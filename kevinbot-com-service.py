import logging
import traceback
from typing import Any, Final, List
from dataclasses import dataclass
from dataclasses import field as dataclass_field

import datetime
import os
import time
import subprocess
import threading
import sys
import uuid

from loguru import logger

import playsound
import pyttsx3
import serial
from paho.mqtt import client as mqtt_client

from xbee import XBee

from settings import SettingsManager

__version__ = "1.0.0"

CLI_ID: Final = f'kevinbot-com-service-{uuid.uuid4()}'
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
SETTINGS_PATH = os.path.join(CURRENT_DIR, 'settings.json')
settings = SettingsManager(SETTINGS_PATH)


@dataclass
class CurrentStateManager:
    enabled: bool = False
    error: int = 0
    speech_engine: str = "espeak"
    last_alive_msg: datetime.datetime = dataclass_field(default_factory=lambda: datetime.datetime.now())
    core_alive: bool = True
    core_uptime: int = 0
    core_uptime_ms: int = 0
    battery_notifications_displayed: list[bool] = dataclass_field(default_factory=lambda: [False, False])
    connected_remotes: list[str] = dataclass_field(default_factory=list)
    sensors: dict = dataclass_field(default_factory=lambda: {
        "batts": [-1, -1],
        "mpu": [0, 0, 0],
        "bme": [0, 0, 0]
    })


def map_range(value, in_min, in_max, out_min, out_max):
    return out_min + (((value - in_min) / (in_max - in_min))
                      * (out_max - out_min))


def split_string(s: str, n: int):
    return [s[i:i+n] for i in range(0, len(s), n)]


def speak_festival(text):
    os.system('echo "{}" | festival --tts'.format(text.replace("Kevinbot",
                                                               "Kevinbought")))


def get_uptime():
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])

    return uptime_seconds


def data_to_remote(data: str):
    xbee.send("tx", dest_addr=b'\x00\x00',
              data=bytes("{}".format(data), 'utf-8'))


def data_to_core(data: str):
    p2_ser.write(data.encode("utf-8"))


def recv_loop():
    while True:
        try:
            data = p2_ser.readline().decode().strip("\n")
        except UnicodeError as e:
            data = ""
            logger.error(f"Got {repr(e)} when processing data")

        line: List[Any] = data.split("=")
        logger.trace(f"Data from Kevinbot Core - {data}")

        if line[0] == "bms.voltages":
            line[1] = line[1].split(",")

            if not line[1][0].isdigit():
                logger.warning(f"Got non-digit value for bms.voltages(0), {line[1][0]}")
                continue
            elif not line[1][1].isdigit():
                logger.warning(f"Got non-digit value for bms.voltages(1), {line[1][1]}")
                continue

            current_state.sensors["batts"][0] = float(line[1][0]) / 10
            current_state.sensors["batts"][1] = float(line[1][1]) / 10
            if client:
                client.publish(
                    settings.services.com.topic_batt1,
                    current_state.sensors["batts"][0])
                client.publish(
                    settings.services.com.topic_batt2,
                    current_state.sensors["batts"][1])

            if int(line[1][0]) < settings.battery.warn_voltages[0]:
                playsound.playsound(os.path.join(os.curdir,
                                                 "sounds/low-battery.mp3"), False)
                if not current_state.battery_notifications_displayed[0]:
                    subprocess.run(["notify-send", "Kevinbot System",
                                    f"Battery #1 is critically low. \
                                    \nVoltage: {float(line[1][0]) / 10}V",
                                    "-u", "critical", "-t", "0"])
                    current_state.battery_notifications_displayed[0] = True

            if int(line[1][1]) < settings.battery.warn_voltages[1] and settings.battery.enable_two:
                playsound.playsound(os.path.join(os.curdir,
                                                 "sounds/low-battery.mp3"), block=False)
                if not current_state.battery_notifications_displayed[1]:
                    subprocess.run(["notify-send", "Kevinbot System",
                                    f"Battery #2 is critically low. \
                                    \nVoltage: {float(line[1][1]) / 10}V",
                                    "-u", "critical", "-t", "0"])
                    current_state.battery_notifications_displayed[1] = True

            data_to_remote(data)
        elif line[0] == "system.enable":
            request_system_enable(line[1].lower() in ["true", "t"])
        elif line[0] == "core.error":
            if not line[1].isdigit():
                logger.warning(f"Got non-digit value for core.error(0), {line[1]}")
                continue
            current_state.error = int(line[1])
        elif line[0] == "core.uptime":
            if not line[1].isdigit():
                logger.warning(f"Got non-digit value for core.uptime(0), {line[1]}")
                continue

            current_state.core_uptime = int(line[1])
            data_to_remote(data)
        elif line[0] == "connection.requesthandshake":
            logger.warning("Handshake requested")
            perform_core_handshake()
            request_system_enable(False)

        # TODO: Re-tx data to remote


def head_recv_loop():
    while True:
        data = head_ser.readline().decode("UTF-8")
        if data.startswith("eye_settings."):
            data_to_remote(data)


def tick():
    data_to_remote(f"os_uptime={round(get_uptime())}")
    p2_ser.write("system.tick\n".encode("utf-8"))
    publish(settings.services.com.topic_sys_uptime, get_uptime())
    publish(settings.services.com.topic_enabled, current_state.enabled)


def begin_remote_handshake(uid: str):
    logger.info(f"Remote ({uid}) handshake started")
    data_to_remote(f"handshake.start={uid}")
    data_to_remote(f"core.enabled={current_state.enabled}")
    data_to_remote(f"core.speech-engine={current_state.speech_engine}")
    transmit_full_remote_list()
    data_to_remote(f"handshake.end={uid}")
    logger.success(f"Remote ({uid}) handshake ended")


def e_stop(power_off: bool = False):
    data_to_core("system.estop\n")
    data_to_remote("system.estop")
    request_system_enable(False)
    if power_off:
        time.sleep(1)
        subprocess.run(["systemctl", "poweroff"])


def request_system_e_stop():
    e_stop(False)


def request_system_enable(ena: bool, sound: bool = True):
    if current_state.error:
        data_to_remote(f"core.enablefailed={int(ena)}")
        return

    if not ena == current_state.enabled:
        current_state.enabled = ena
        logger.info(f"Enabled: {current_state.enabled}")
        data_to_core(f"system.enabled={int(ena)}\n")
        print("core", f"system.enabled={int(ena)}\n")

        if not ena:
            # On disable
            p2_ser.write("head_effect=color1\n".encode("utf-8"))
            p2_ser.write("body_effect=color1\n".encode("utf-8"))
            p2_ser.write("base_effect=color1\n".encode("utf-8"))
            p2_ser.write("head_color1=000000\n".encode("utf-8"))
            p2_ser.write("body_color1=000000\n".encode("utf-8"))
            p2_ser.write("base_color1=000000\n".encode("utf-8"))

        data_to_remote(f"core.enabled={current_state.enabled}")
        if sound:
            playsound.playsound(os.path.join(os.curdir,
                                             "sounds/enable.wav"), False)


def transmit_full_remote_list():
    mesh = [f"KEVINBOTV3|{__version__}|kevinbot.kevinbot"] + current_state.connected_remotes
    data = split_string(",".join(mesh), settings.services.com.data_max)

    for count, part in enumerate(data):
        data_to_remote(f"core.full_mesh:{count}:"
                       f"{len(data) - 1}={data[count]}")


def remote_recv_loop():
    while True:
        try:
            data = xbee.wait_read_frame()

            if data["id"] == "status":
                logger.warning("Got XBee Status msg: %s", data["status"])

            raw = data['rf_data'].decode().strip("\r\n")
            data = data['rf_data'].decode().strip("\r\n").split('=', 1)

            print(data)

            if data[0].startswith("eye."):
                head_ser.write(
                    (raw.split(
                        ".",
                        maxsplit=1)[1] +
                     "\n").encode("UTF-8"))
            elif data[0] == "core.speech":
                data_to_remote("remote.disableui=True")
                if current_state.speech_engine == "festival":
                    speak_festival(data[1].strip("\r\n"))
                elif current_state.speech_engine == "espeak":
                    espeak_engine.say(data[1].strip("\r\n"))
                    espeak_engine.runAndWait()
                    print("here")
                data_to_remote("remote.disableui=False")
            elif data[0] == "core.speech-engine":
                current_state.speech_engine = data[1].strip("\r\n")
            elif data[0] == "request.estop":
                request_system_e_stop()
            elif data[0] == "request.enabled":
                enabled = data[1].lower() in ["true", "t"]
                request_system_enable(enabled)
            elif data[0] == "core.remotes.add":
                if not data[1] in current_state.connected_remotes:
                    current_state.connected_remotes.append(data[1])
                    logger.info(f"Wireless device connected: {data[1]}")
                    logger.info(f"Total devices: {current_state.connected_remotes}")
                begin_remote_handshake(data[1].split("|")[0])
            elif data[0] == "core.remotes.remove":
                if data[1] in current_state.connected_remotes:
                    current_state.connected_remotes.remove(data[1])
                    logger.info(f"Wireless device disconnected: {data[1]}")
                logger.info(f"Total devices: {current_state.connected_remotes}")
            elif data[0] == "core.remotes.get_full":
                transmit_full_remote_list()
            elif data[0] == "core.ping":
                if data[1].split(",")[0] == "KEVINBOTV3":
                    threading.Thread(
                        target=playsound.playsound,
                        args=(
                            os.path.join(
                                os.curdir,
                                "sounds/device-notify.wav"),
                        ),
                        daemon=True).start()
                    logger.info(f"Ping from {data[1].split(',')[1]}")
                    subprocess.run(
                        ["notify-send", "Ping!",
                         f"Ping from {data[1].split(',')[1]}"])
            else:
                data_to_core(f"{data[0]}={data[1]}\n")
        except Exception as e:
            request_system_enable(False)
            logger.error(f"Exception in Remote Loop: {e}")
            traceback.print_exc()


def on_connect(cli, userdata, flags, rc):
    if rc == 0:
        logger.success("Connected to MQTT Broker")
    else:
        logger.critical(f"Failed to connect, return code {rc}")
        sys.exit()


def on_message(cli, userdata, msg):
    if settings.services.mpu.topic_roll in msg.topic:
        current_state.sensors["mpu"][0] = float(msg.payload.decode())
    elif settings.services.mpu.topic_pitch in msg.topic:
        current_state.sensors["mpu"][1] = float(msg.payload.decode())
    elif settings.services.mpu.topic_yaw in msg.topic:
        current_state.sensors["mpu"][2] = float(msg.payload.decode())
        data_to_remote(
            f"imu={current_state.sensors['mpu'][0]},"
            f"{current_state.sensors['mpu'][1]},"
            f"{current_state.sensors['mpu'][2]}")
    elif settings.services.bme.topic_temp in msg.topic:
        current_state.sensors["bme"][0] = float(msg.payload.decode())
    elif settings.services.bme.topic_humidity in msg.topic:
        current_state.sensors["bme"][1] = float(msg.payload.decode())
    elif settings.services.bme.topic_pressure in msg.topic:
        current_state.sensors["bme"][2] = float(msg.payload.decode())
        data_to_remote(f"bme={current_state.sensors['bme'][0]},"
                       f"{round(float(current_state.sensors['bme'][0]) * 1.8 + 32, 2)},"
                       f"{current_state.sensors['bme'][1]},{current_state.sensors['bme'][2]}")


def publish(topic, msg):
    result = client.publish(topic, msg)
    status = result[0]
    if status != 0:
        logger.error(f"Failed to send message to topic {topic}")


def tick_loop():
    if settings.services.com.tick.lower() == "core":
        return

    while True:
        time.sleep(float(settings.services.com.tick.lower().strip("s")))
        tick()


def perform_core_handshake():
    while True:
        p2_ser.write("connection.isready=0\n".encode("utf-8"))
        line = p2_ser.readline().decode("utf-8").strip("\n")
        if line == "ready":
            # Start connection handshake
            logger.info("Beginning core connection handshake")
            p2_ser.write("connection.start\n".encode("utf-8"))
            p2_ser.write("core.errors.clear\n".encode("utf-8"))
            p2_ser.write("connection.ok\n".encode("utf-8"))
            logger.success("Core is connected")
            logger.info("Reset battery notifications")
            current_state.battery_notifications_displayed = [False, False]
            break
        time.sleep(0.1)


if __name__ == "__main__":
    # banner
    try:
        import pyfiglet

        print("\033[94m", end=None)
        print(pyfiglet.Figlet().renderText("Kevinbot COM"))
    except ImportError:
        print("\033[94mKevinbot COM")
        pyfiglet = None
    print("\033[0m", end=None)

    current_state = CurrentStateManager()

    # logging
    logger.remove()
    logger.add(sys.stderr, level=settings.logging.level)
    logging.basicConfig(level=settings.logging.level)

    # serial
    xb_ser = serial.Serial(settings.services.serial.xb_port, baudrate=settings.services.serial.xb_baud)
    xbee = XBee(xb_ser, escaped=False)

    p2_ser = serial.Serial(settings.services.serial.p2_port, baudrate=settings.services.serial.p2_baud)

    head_ser = serial.Serial(settings.services.serial.head_port, baudrate=settings.services.serial.head_baud)

    # speech
    espeak_engine = pyttsx3.init("espeak")

    # mqtt
    client = mqtt_client.Client(CLI_ID)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(settings.services.mqtt.address, settings.services.mqtt.port)
    client.subscribe(settings.services.mpu.topic_roll)
    client.subscribe(settings.services.mpu.topic_pitch)
    client.subscribe(settings.services.mpu.topic_yaw)
    client.subscribe(settings.services.bme.topic_temp)
    client.subscribe(settings.services.bme.topic_humidity)
    client.subscribe(settings.services.bme.topic_pressure)

    # hold up until core is ready
    logger.info("Waiting for core connection")
    perform_core_handshake()

    # threads

    recv_thread = threading.Thread(target=recv_loop, daemon=True)
    recv_thread.start()

    head_recv_thread = threading.Thread(target=head_recv_loop, daemon=True)
    head_recv_thread.start()

    remote_recv_thread = threading.Thread(target=remote_recv_loop, daemon=True)
    remote_recv_thread.start()

    tick_thread = threading.Thread(target=tick_loop, daemon=True)
    tick_thread.start()

    # init
    data_to_remote("core.service.init=kevinbot.com")
    data_to_remote("core.enabled=False")

    logger.success("Comms are up!")

    client.loop_forever()
