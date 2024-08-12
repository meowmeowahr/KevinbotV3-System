import datetime
import logging
import os
import subprocess
import sys
import threading
import time
import traceback
import uuid
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import Any, Final, List

import serial
from command_queue import CommandQueue
from command_queue.commands import FunctionCommand
from loguru import logger
from paho.mqtt import client as mqtt_client

from remote_interface import RemoteInterface, RemoteCommand
from robot_commands import (
    SpeechCommand,
    RemoteHandshakeCommand,
    RobotRequestEnableCommand,
    RobotRequestEstopCommand,
    CoreSerialCommand,
    WavCommand,
    RemoteEnableCommand,
)
from settings import SettingsManager

__version__ = "1.0.0"

CLI_ID: Final = f"kevinbot-com-service-{uuid.uuid4()}"
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
SETTINGS_PATH = os.path.join(CURRENT_DIR, "settings.json")
settings = SettingsManager(SETTINGS_PATH)


@dataclass
class CurrentStateManager:
    enabled: bool = False
    error: int = 0
    speech_engine: str = "espeak"
    last_alive_msg: datetime.datetime = dataclass_field(
        default_factory=lambda: datetime.datetime.now()
    )
    core_alive: bool = True
    core_uptime: int = 0
    core_uptime_ms: int = 0
    battery_notifications_displayed: list[bool] = dataclass_field(
        default_factory=lambda: [False, False]
    )
    battery_sound_played: list[bool] = dataclass_field(
        default_factory=lambda: [False, False]
    )
    connected_remotes: list[str] = dataclass_field(default_factory=list)
    arm_servos: dict = dataclass_field(default_factory=dict)
    head_servos: dict = dataclass_field(default_factory=dict)
    sensors: dict = dataclass_field(
        default_factory=lambda: {
            "batts": [-1, -1],
            "temps": [-1, -1, -1],
            "mpu": [-1, -1, -1],
            "bme": [-1, -1, -1],
        }
    )
    lighting_head_update: int = dataclass_field(
        default_factory=lambda: settings.lighting.head.update
    )
    lighting_head_brightness: int = dataclass_field(
        default_factory=lambda: settings.lighting.head.brightness
    )
    lighting_body_update: int = dataclass_field(
        default_factory=lambda: settings.lighting.body.update
    )
    lighting_body_brightness: int = dataclass_field(
        default_factory=lambda: settings.lighting.body.brightness
    )
    lighting_base_update: int = dataclass_field(
        default_factory=lambda: settings.lighting.base.update
    )
    lighting_base_brightness: int = dataclass_field(
        default_factory=lambda: settings.lighting.base.brightness
    )


def map_range(value, in_min, in_max, out_min, out_max):
    return out_min + (((value - in_min) / (in_max - in_min)) * (out_max - out_min))


def split_string(s: str, n: int):
    return [s[i: i + n] for i in range(0, len(s), n)]


def get_uptime():
    with open("/proc/uptime", "r") as f:
        uptime_seconds = float(f.readline().split()[0])

    return uptime_seconds


def data_to_core(data: str):
    p2_ser.write(data.encode("utf-8"))


def set_enabled(ena: bool):
    current_state.enabled = ena


def recv_loop():
    while True:
        try:
            data = p2_ser.readline().decode().strip("\n")
        except UnicodeError as e:
            data = ""
            logger.error(f"Got {repr(e)} when processing data")

        line: List[Any] = data.split("=")
        logger.log("DATA", f"Data from Kevinbot Core - {data}")

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
                    settings.services.com.topic_batts,
                    ",".join(map(str, current_state.sensors["batts"])),
                )

            if int(line[1][0]) < settings.battery.warn_voltages[0]:
                if settings.battery.warn_sound == "repeat":
                    command_queue.add_command(WavCommand("sounds/low-battery.wav"))
                elif settings.battery.warn_sound == "never":
                    pass
                else:
                    if not current_state.battery_sound_played[0]:
                        command_queue.add_command(WavCommand("sounds/low-battery.wav"))
                        current_state.battery_sound_played[0] = True
                if not current_state.battery_notifications_displayed[0]:
                    subprocess.run(
                        [
                            "notify-send",
                            "Kevinbot System",
                            f"Battery #1 is low. \
                                    \nVoltage: {float(line[1][0]) / 10}V",
                            "-u",
                            "critical",
                            "-t",
                            "0",
                        ]
                    )
                    current_state.battery_notifications_displayed[0] = True

            if (
                    int(line[1][1]) < settings.battery.warn_voltages[1]
                    and settings.battery.enable_two
            ):
                if settings.battery.warn_sound == "repeat":
                    command_queue.add_command(WavCommand("sounds/low-battery.wav"))
                elif settings.battery.warn_sound == "never":
                    pass
                else:
                    if not current_state.battery_sound_played[1]:
                        command_queue.add_command(WavCommand("sounds/low-battery.wav"))
                        current_state.battery_sound_played[1] = True

                if not current_state.battery_notifications_displayed[1]:
                    subprocess.run(
                        [
                            "notify-send",
                            "Kevinbot System",
                            f"Battery #2 is low. \
                                    \nVoltage: {float(line[1][1]) / 10}V",
                            "-u",
                            "critical",
                            "-t",
                            "0",
                        ]
                    )
                    current_state.battery_notifications_displayed[1] = True

            remote.send(data)
        elif line[0] == "core.enabled":
            # command_queue.add_command(RobotRequestEnableCommand(line[1].lower() in ["true", "t"],
            #                                                     p2_ser,
            #                                                     remote,
            #                                                     current_state))
            command_queue.add_command(
                RemoteEnableCommand(line[1].lower() in ["true", "t"], remote)
            )
            command_queue.add_command(
                FunctionCommand(lambda: set_enabled(line[1].lower() in ["true", "t"]))
            )
            command_queue.add_command(WavCommand("sounds/enable.wav"))
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
            remote.send(data)
        elif line[0] == "connection.requesthandshake":
            logger.warning("Handshake requested")
            perform_core_handshake()
            command_queue.add_command(
                RobotRequestEnableCommand(False, p2_ser, remote, current_state)
            )
            command_queue.add_command(FunctionCommand(lambda: set_enabled(False)))
            command_queue.add_command(WavCommand("sounds/enable.wav"))
        elif line[0] == "sensors.temps":
            bad = False
            for item in line[1].split(","):
                if not item.isdigit():
                    logger.warning("Got bad data from sensors.temps")
                    bad = True
                    break
            if bad:
                continue

            current_state.sensors["temps"] = list(
                map(lambda x: int(x) / 100, line[1].split(","))
            )
            remote.send(
                f"sensors.temps={','.join(list(map(str, current_state.sensors['temps'])))}"
            )
        elif line[0] == "sensors.bme":
            bad = False
            for item in line[1].split(","):
                if not item.isdigit():
                    logger.warning("Got bad data from sensors.bme")
                    bad = True
                    break
            if bad:
                continue
            current_state.sensors["bme"] = list(map(int, line[1].split(",")))
            remote.send(
                f"sensors.bme={','.join(list(map(str, current_state.sensors['bme'])))}"
            )


def head_recv_loop():
    while True:
        data = head_ser.readline().decode("UTF-8").strip("\r\n")
        if data.startswith("eyeSettings."):
            remote.send(data)
        elif data == "handshake.request":
            head_ser.write(b"getSettings=true\n")
            head_ser.write(b"handshake.complete\n")


def tick():
    remote.send(f"system.uptime={round(get_uptime())}")
    p2_ser.write("core.tick\n".encode("utf-8"))
    publish(settings.services.com.topic_sys_uptime, get_uptime())
    publish(settings.services.com.topic_enabled, current_state.enabled)


def transmit_full_remote_list():
    mesh = [
               f"KEVINBOTV3|{__version__}|kevinbot.kevinbot"
           ] + current_state.connected_remotes
    data = split_string(",".join(mesh), settings.services.com.data_max)

    for count, part in enumerate(data):
        remote.send(f"system.remotes.list:{count}:" f"{len(data) - 1}={data[count]}")


def remote_recv(data):
    try:
        if "rf_data" not in data:
            return

        data = data["rf_data"].decode().strip("\r\n").split("=", 1)
        command = RemoteCommand(data[0])
        if len(data) > 1:
            value = data[1]
        else:
            value = ""

        if data[0].startswith("eyes."):
            print(data)
            head_ser.write(
                (data[0].split(".")[1] + "=" + data[1] + "\n").encode("UTF-8")
            )
        elif command == RemoteCommand.SpeechSpeak:
            if current_state.enabled:
                command_queue.add_command(
                    SpeechCommand(value, current_state.speech_engine)
                )
        elif command == RemoteCommand.ArmPositions:
            previous_servos = current_state.arm_servos.copy()
            positions = list(map(int, value.split(",")))
            for port, position in zip(arm_ports, positions):
                current_state.arm_servos[port] = position
            # get differences between previous and current positions
            new_positions = {
                key: current_state.arm_servos[key]
                for key in current_state.arm_servos
                if key not in previous_servos
                   or previous_servos[key] != current_state.arm_servos[key]
            }
            for change in new_positions:
                p2_ser.write(
                    f"""s={change},{map_range(new_positions[change], 0, 255,
                                                       *settings.servo.mappings.arm_limits.get(str(change),
                                                                                               [0, 180]))}\n""".encode(
                        "utf-8"
                    )
                )
            p2_ser.flush()
        elif command == RemoteCommand.HeadXPosition:
            try:
                int(value)
            except ValueError:
                logger.warning(f"Got non-int value for head.position.x(0)")
                return

            x_position = map_range(
                int(value),
                0,
                255,
                *settings.servo.mappings.head_limits.get("x", [0, 180]),
            )
            current_state.head_servos["x"] = x_position

            p2_ser.write(
                f"s={settings.servo.mappings.head.get('x', 14)},{round(x_position)}\n".encode(
                    "utf-8"
                )
            )
        elif command == RemoteCommand.HeadYPosition:
            try:
                int(value)
            except ValueError:
                logger.warning(f"Got non-int value for head.position.y(0)")
                return

            y_position = map_range(
                int(value),
                0,
                255,
                *settings.servo.mappings.head_limits.get("y", [0, 180]),
            )
            current_state.head_servos["y"] = y_position

            p2_ser.write(
                f"s={settings.servo.mappings.head.get('y', 15)},{round(y_position)}\n".encode(
                    "utf-8"
                )
            )
        elif command == RemoteCommand.LightingHeadEffect:
            command_queue.add_command(
                CoreSerialCommand(
                    p2_ser, f"{RemoteCommand.LightingHeadEffect.value}={value}\n"
                )
            )
        elif command == RemoteCommand.LightingHeadColor1:
            command_queue.add_command(
                CoreSerialCommand(
                    p2_ser, f"{RemoteCommand.LightingHeadColor1.value}={value}\n"
                )
            )
        elif command == RemoteCommand.LightingHeadColor2:
            command_queue.add_command(
                CoreSerialCommand(
                    p2_ser, f"{RemoteCommand.LightingHeadColor2.value}={value}\n"
                )
            )
        elif command == RemoteCommand.LightingHeadUpdateSpeed:
            current_state.lighting_head_update = int(value)
            command_queue.add_command(
                CoreSerialCommand(
                    p2_ser, f"{RemoteCommand.LightingHeadUpdateSpeed.value}={value}\n"
                )
            )
        elif command == RemoteCommand.LightingHeadBright:
            current_state.lighting_head_brightness = int(value)
            command_queue.add_command(
                CoreSerialCommand(
                    p2_ser, f"{RemoteCommand.LightingHeadBright.value}={value}\n"
                )
            )
        elif command == RemoteCommand.LightingBodyEffect:
            command_queue.add_command(
                CoreSerialCommand(
                    p2_ser, f"{RemoteCommand.LightingBodyEffect.value}={value}\n"
                )
            )
        elif command == RemoteCommand.LightingBodyColor1:
            command_queue.add_command(
                CoreSerialCommand(
                    p2_ser, f"{RemoteCommand.LightingBodyColor1.value}={value}\n"
                )
            )
        elif command == RemoteCommand.LightingBodyColor2:
            command_queue.add_command(
                CoreSerialCommand(
                    p2_ser, f"{RemoteCommand.LightingBodyColor2.value}={value}\n"
                )
            )
        elif command == RemoteCommand.LightingBodyUpdateSpeed:
            current_state.lighting_body_update = int(value)
            command_queue.add_command(
                CoreSerialCommand(
                    p2_ser, f"{RemoteCommand.LightingBodyUpdateSpeed.value}={value}\n"
                )
            )
        elif command == RemoteCommand.LightingBodyBright:
            current_state.lighting_body_brightness = int(value)
            command_queue.add_command(
                CoreSerialCommand(
                    p2_ser, f"{RemoteCommand.LightingBodyBright.value}={value}\n"
                )
            )
        elif command == RemoteCommand.LightingBaseEffect:
            command_queue.add_command(
                CoreSerialCommand(
                    p2_ser, f"{RemoteCommand.LightingBaseEffect.value}={value}\n"
                )
            )
        elif command == RemoteCommand.LightingBaseColor1:
            command_queue.add_command(
                CoreSerialCommand(
                    p2_ser, f"{RemoteCommand.LightingBaseColor1.value}={value}\n"
                )
            )
        elif command == RemoteCommand.LightingBaseColor2:
            command_queue.add_command(
                CoreSerialCommand(
                    p2_ser, f"{RemoteCommand.LightingBaseColor2.value}={value}\n"
                )
            )
        elif command == RemoteCommand.LightingBaseUpdateSpeed:
            current_state.lighting_base_update = int(value)
            command_queue.add_command(
                CoreSerialCommand(
                    p2_ser, f"{RemoteCommand.LightingBaseUpdateSpeed.value}={value}\n"
                )
            )
        elif command == RemoteCommand.LightingBaseBright:
            current_state.lighting_base_brightness = int(value)
            command_queue.add_command(
                CoreSerialCommand(
                    p2_ser, f"{RemoteCommand.LightingBaseBright.value}={value}\n"
                )
            )
        elif command == RemoteCommand.LightingCameraBrightness:
            command_queue.add_command(
                CoreSerialCommand(p2_ser, f"lighting.cam.bright={value}\n")
            )
        elif command == RemoteCommand.SpeechEngine:
            current_state.speech_engine = value
        elif command == RemoteCommand.RequestEstop:
            command_queue.add_command(
                RobotRequestEstopCommand(p2_ser, remote, current_state)
            )
            command_queue.add_command(WavCommand("sounds/estop.wav"))
        elif command == RemoteCommand.RequestEnable:
            enabled = value.lower() in ["true", "t"]
            command_queue.add_command(
                RobotRequestEnableCommand(enabled, p2_ser, remote, current_state)
            )
            command_queue.add_command(FunctionCommand(lambda: set_enabled(enabled)))
            command_queue.add_command(WavCommand("sounds/enable.wav"))
        elif command == RemoteCommand.RemoteListAdd:
            if value not in current_state.connected_remotes:
                current_state.connected_remotes.append(value)
                logger.info(f"Wireless device connected: {value}")
                logger.info(f"Total devices: {current_state.connected_remotes}")
            command_queue.add_command(
                RemoteHandshakeCommand(
                    remote, value.split("|")[0], __version__, current_state
                )
            )
        elif command == RemoteCommand.RemoteListRemove:
            if value in current_state.connected_remotes:
                current_state.connected_remotes.remove(value)
                logger.info(f"Wireless device disconnected: {value}")
            logger.info(f"Total devices: {current_state.connected_remotes}")
        elif command == RemoteCommand.RemoteListFetch:
            transmit_full_remote_list()
        elif command == RemoteCommand.Ping:
            if value.split(",")[0] == "KEVINBOTV3":
                command_queue.add_command(WavCommand("sounds/device-notify.wav"))
                logger.info(f"Ping from {data[1].split(',')[1]}")
                subprocess.run(
                    ["notify-send", "Ping!", f"Ping from {data[1].split(',')[1]}"]
                )

        # print("time", [t-times[0] for t in times])
    except Exception as e:
        command_queue.add_command(
            RobotRequestEnableCommand(False, p2_ser, remote, current_state)
        )
        command_queue.add_command(FunctionCommand(lambda: set_enabled(False)))
        command_queue.add_command(WavCommand("sounds/enable.wav"))
        logger.error(f"Exception in Remote Loop: {e}")
        traceback.print_exc()


def on_connect(_, __, ___, rc):
    if rc == 0:
        logger.success("Connected to MQTT Broker")
    else:
        logger.critical(f"Failed to connect, return code {rc}")
        sys.exit()


def on_message(_, __, msg):
    if settings.services.mpu.topic_imu in msg.topic:
        current_state.sensors["mpu"] = list(map(float, msg.payload.decode().split(",")))
        remote.send(
            f"sensors.imu={current_state.sensors['mpu'][0]},"
            f"{current_state.sensors['mpu'][1]},"
            f"{current_state.sensors['mpu'][2]}"
        )
    elif settings.services.bme.topic_temp in msg.topic:
        current_state.sensors["bme"][0] = float(msg.payload.decode())
    elif settings.services.bme.topic_humidity in msg.topic:
        current_state.sensors["bme"][1] = float(msg.payload.decode())
    elif settings.services.bme.topic_pressure in msg.topic:
        current_state.sensors["bme"][2] = float(msg.payload.decode())
        remote.send(
            f"bme={current_state.sensors['bme'][0]},"
            f"{round(float(current_state.sensors['bme'][0]) * 1.8 + 32, 2)},"
            f"{current_state.sensors['bme'][1]},{current_state.sensors['bme'][2]}"
        )


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
            current_state.error = 0
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
    logger.level("DATA", no=4, color="<magenta>", icon="<>")
    logger.add(sys.stderr, level=settings.logging.level)
    logging.basicConfig(level=settings.logging.level)

    # serial
    remote = RemoteInterface(
        settings.services.serial.xb_port,
        settings.services.serial.xb_baud,
        escaped=True,
        callback=remote_recv,
    )
    p2_ser = serial.Serial(
        settings.services.serial.p2_port, baudrate=settings.services.serial.p2_baud
    )
    head_ser = serial.Serial(
        settings.services.serial.head_port, baudrate=settings.services.serial.head_baud
    )

    # arms
    arm_ports = []
    for servo_port in range(len(settings.servo.mappings.arms)):
        arm_ports.append(settings.servo.mappings.arms[str(servo_port)])

    # mqtt
    client = mqtt_client.Client(CLI_ID)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(settings.services.mqtt.address, settings.services.mqtt.port)
    client.subscribe(settings.services.mpu.topic_imu)
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

    tick_thread = threading.Thread(target=tick_loop, daemon=True)
    tick_thread.start()

    # command queue
    command_queue = CommandQueue()
    command_queue.run_in_background(100)

    # init
    remote.send("core.service.init=kevinbot.com")
    remote.send("core.enabled=False")

    logger.success("Comms are up!")

    client.loop_forever()
