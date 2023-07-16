from typing import Dict, Any, Final, List

import datetime
import os
import time
import subprocess
import threading
import logging
import sys
import uuid

import playsound
import pyttsx3
import serial
from paho.mqtt import client as mqtt_client

from xbee import XBee

from system_options import (
    settings,
    TOPIC_HUMI,
    TOPIC_PRESSURE,
    TOPIC_TEMP,
    TOPIC_YAW,
    TOPIC_PITCH,
    TOPIC_ROLL,
    P2_SERIAL_PORT,
    XB_SERIAL_PORT,
    HEAD_SERIAL_PORT,
    P2_BAUD_RATE,
    XB_BAUD_RATE,
    HEAD_BAUD_RATE,
    BATT_LOW_VOLT,
    USING_BATT_2,
    BROKER,
    PORT)

__version__ = "1.0.0"

CLI_ID: Final = f'kevinbot-com-service-{uuid.uuid4()}'

speech_engine = "espeak"
connected_remotes = []

last_alive_msg = datetime.datetime.now()
is_alive = True

sensors: Dict[Any, Any] = {"batts": [-1, -1],
                           "mpu": [0, 0, 0], "bme": [0, 0, 0]}

shown_batt1_notif = False
shown_batt2_notif = False

enabled = False


def map_range(value, in_min, in_max, out_min, out_max):
    return out_min + (((value - in_min) / (in_max - in_min))
                      * (out_max - out_min))


def speak_festival(text):
    os.system('echo "{}" | festival --tts'.format(text.replace("Kevinbot",
                                                               "Kevinbought")))


def get_uptime():
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])

    return uptime_seconds


def data_to_remote(data):
    xbee.send("tx", dest_addr=b'\x00\x00',
              data=bytes("{}".format(data), 'utf-8'))


def recv_loop():
    global shown_batt1_notif, shown_batt2_notif
    global sensors, enabled

    while True:
        try:
            line: List[Any] = p2_ser.readline().decode().strip("\n").split("=")

            data_to_remote("{}={}\r".format(line[0], line[1]))

            if line[0] == "batt_volts":
                line[1] = line[1].split(",")

                sensors["batts"][0] = float(line[1][0]) / 10
                sensors["batts"][1] = float(line[1][1]) / 10
                if client:
                    client.publish(
                        settings["services"]["com"]["topic-batt1"],
                        sensors["batts"][0])
                    client.publish(
                        settings["services"]["com"]["topic-batt2"],
                        sensors["batts"][1])

                if int(line[1][0]) < BATT_LOW_VOLT:
                    playsound.playsound(os.path.join(os.curdir,
                                                     "sounds/low-battery.mp3"))
                    if not shown_batt1_notif:
                        subprocess.run(["notify-send", "Kevinbot System",
                                        f"Battery #1 is critically low. \
                                        \nVoltage: {float(line[1][0]) / 10}V",
                                        "-u", "critical", "-t", "0"])
                        shown_batt1_notif = True

                if int(line[1][1]) < BATT_LOW_VOLT and USING_BATT_2:
                    playsound.playsound(os.path.join(os.curdir,
                                                     "sounds/low-battery.mp3"))
                    if not shown_batt2_notif:
                        subprocess.run(["notify-send", "Kevinbot System",
                                        f"Battery #2 is critically low. \
                                        \nVoltage: {float(line[1][1]) / 10}V",
                                        "-u", "critical", "-t", "0"])
                        shown_batt2_notif = True
            elif line[0] == "robot.disable":
                enabled = not line[1].lower() in ["true", "t"]
                logging.info(f"Enabled: {enabled}")
            if line[0] == "alive":
                # System Tick
                publish(settings["services"]["com"]
                        ["topic-core-uptime"], line[1])
                if settings["services"]["com"]["tick"].lower() == "core":
                    tick()
        except (IndexError, ValueError):
            # data is corrupt
            pass


def head_recv_loop():
    while True:
        data = head_ser.readline().decode("UTF-8")
        if data.startswith("eye_settings."):
            data_to_remote(data)


def tick():
    data_to_remote(f"os_uptime={round(get_uptime())}")
    publish(settings["services"]["com"]["topic-sys-uptime"], get_uptime())
    publish(settings["services"]["com"]["topic-enabled"], enabled)


def remote_recv_loop():
    global speech_engine
    global enabled
    global connected_remotes

    while True:
        try:
            data = xbee.wait_read_frame()

            if (not data['rf_data'].decode().startswith('core')) and enabled:
                p2_ser.write(data['rf_data'])

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
                if speech_engine == "festival":
                    speak_festival(data[1].strip("\r\n"))
                elif speech_engine == "espeak":
                    espeak_engine.say(data[1].strip("\r\n"))
                    espeak_engine.runAndWait()
            elif data[0] == "core.speech-engine":
                speech_engine = data[1].strip("\r\n")
            elif data[0] == "robot.disable":
                enabled = not data[1].lower() in ["true", "t"]
                p2_ser.write("stop".encode("UTF-8"))
            elif data[0] == "enabled":
                enabled = data[1].lower() in ["true", "t"]
                logging.info(f"Enabled: {enabled}")
            elif data[0] == "core.remotes.add":
                if not data[1] in connected_remotes:
                    connected_remotes.append(data[1])
                    logging.info(f"Wireless device connected: {data[1]}")
                    logging.info(f"Total devices: {connected_remotes}")
                data_to_remote(f"core.enabled={enabled}")
                data_to_remote(f"core.speech-engine={speech_engine}")
            elif data[0] == "core.remotes.remove":
                if data[1] in connected_remotes:
                    connected_remotes.remove(data[1])
                    logging.info(f"Wireless device disconnected: {data[1]}")
                logging.info(f"Total devices: {connected_remotes}")
            elif data[0] == "core.remotes.get_full":
                mesh = [f"KEVINBOTV3|{__version__}|kevinbot.kevinbot"]
                mesh = ",".join(mesh + connected_remotes)
                mesh = [mesh[i:i + settings["services"]["data_max"]]
                        for i in range(0, len(mesh),
                                       settings["services"]["data_max"])]
                for count, part in enumerate(mesh):
                    data_to_remote(f"core.full_mesh:{count}:"
                                   f"{len(mesh)-1}={mesh[count]}")
                    print(f"core.full_mesh:{count}:"
                          f"{len(mesh)-1}={','.join(mesh)}")
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
                    logging.info(f"Ping from {data[1].split(',')[1]}")
                    subprocess.run(
                        ["notify-send", "Ping!",
                         f"Ping from {data[1].split(',')[1]}"])
            elif data[0] == "shutdown":
                subprocess.run(["systemctl", "poweroff"])
        except Exception as e:
            data_to_remote("robot.disable=True")
            disable()
            logging.error(f"Exception in Remote Loop: {e}")


def disable():
    p2_ser.write("stop".encode("UTF-8"))


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT Broker")
    else:
        logging.critical(f"Failed to connect, return code {rc}")
        sys.exit()


def on_message(client, userdata, msg):
    global sensors

    if TOPIC_ROLL in msg.topic:
        sensors["mpu"][0] = float(msg.payload.decode())
    elif TOPIC_PITCH in msg.topic:
        sensors["mpu"][1] = float(msg.payload.decode())
    elif TOPIC_YAW in msg.topic:
        sensors["mpu"][2] = float(msg.payload.decode())
        data_to_remote(
            f"imu={sensors['mpu'][0]},{sensors['mpu'][1]},{sensors['mpu'][2]}")
    elif TOPIC_TEMP in msg.topic:
        sensors["bme"][0] = float(msg.payload.decode())
    elif TOPIC_HUMI in msg.topic:
        sensors["bme"][1] = float(msg.payload.decode())
    elif TOPIC_PRESSURE in msg.topic:
        sensors["bme"][2] = float(msg.payload.decode())
        data_to_remote(f"bme={sensors['bme'][0]},"
                       f"{round(float(sensors['bme'][0]) * 1.8 + 32, 2)},"
                       f"{sensors['bme'][1]},{sensors['bme'][2]}")


def publish(topic, msg):
    result = client.publish(topic, msg)
    status = result[0]
    if status != 0:
        logging.error(f"Failed to send message to topic {topic}")


def tick_loop():
    if settings["services"]["com"]["tick"].lower() == "core":
        return

    while True:
        time.sleep(float(settings["services"]["com"]
                   ["tick"].lower().strip("s")))
        tick()


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

    # logging
    logging.basicConfig(level=settings["logging"]["level"])

    # serial
    xb_ser = serial.Serial(XB_SERIAL_PORT, baudrate=XB_BAUD_RATE)
    xbee = XBee(xb_ser, escaped=False)

    p2_ser = serial.Serial(P2_SERIAL_PORT, baudrate=P2_BAUD_RATE)

    head_ser = serial.Serial(HEAD_SERIAL_PORT, baudrate=HEAD_BAUD_RATE)

    # speech
    espeak_engine = pyttsx3.init("espeak")

    # threads
    client = None

    recv_thread = threading.Thread(target=recv_loop, daemon=True)
    recv_thread.start()

    head_recv_thread = threading.Thread(target=head_recv_loop, daemon=True)
    head_recv_thread.start()

    remote_recv_thread = threading.Thread(target=remote_recv_loop, daemon=True)
    remote_recv_thread.start()

    tick_thread = threading.Thread(target=tick_loop, daemon=True)
    tick_thread.start()

    # mqtt
    client = mqtt_client.Client(CLI_ID)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT)
    client.subscribe(TOPIC_ROLL)
    client.subscribe(TOPIC_PITCH)
    client.subscribe(TOPIC_YAW)
    client.subscribe(TOPIC_TEMP)
    client.subscribe(TOPIC_HUMI)
    client.subscribe(TOPIC_PRESSURE)

    # init
    data_to_remote("core.service.init=kevinbot.com")
    data_to_remote("core.enabled=False")

    client.loop_forever()
