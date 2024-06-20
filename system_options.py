from typing import Final
import os
import json

CURRENT_DIR: Final = os.path.dirname(os.path.realpath(__file__))
SETTINGS_PATH: Final = os.path.join(CURRENT_DIR, 'settings.json')

settings = json.load(open(SETTINGS_PATH, 'r'))

XB_SERIAL_PORT = settings["services"]["serial"]["xb-port"]
XB_BAUD_RATE = settings["services"]["serial"]["xb-baud"]

P2_SERIAL_PORT = settings["services"]["serial"]["p2-port"]
P2_BAUD_RATE = settings["services"]["serial"]["p2-baud"]

HEAD_SERIAL_PORT = settings["services"]["serial"]["head-port"]
HEAD_BAUD_RATE = settings["services"]["serial"]["head-baud"]

BROKER = settings["services"]["mqtt"]["address"]
PORT = settings["services"]["mqtt"]["port"]
TOPIC_ROLL = settings["services"]["mpu"]["topic-roll"]
TOPIC_PITCH = settings["services"]["mpu"]["topic-pitch"]
TOPIC_YAW = settings["services"]["mpu"]["topic-yaw"]
TOPIC_TEMP = settings["services"]["bme"]["topic-temp"]
TOPIC_HUMI = settings["services"]["bme"]["topic-humidity"]
TOPIC_PRESSURE = settings["services"]["bme"]["topic-pressure"]

USING_BATT_2 = False
BATT_LOW_VOLT = 90

SETTING_COMBOS = {
    "bauds": [
        4800,
        9600,
        19200,
        38400,
        57600,
        115200,
        230400,
        460800,
        624000
    ],
    "ticks": [
        "CORE",
        "0.1s",
        "0.25s",
        "0.4s",
        "0.6s",
        "0.8s",
        "1s",
        "1.5s",
        "2s"
    ]
}