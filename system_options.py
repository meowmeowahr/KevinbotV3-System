import json
import os
from typing import Final

CURRENT_DIR: Final = os.path.dirname(os.path.realpath(__file__))
SETTINGS_PATH: Final = os.path.join(CURRENT_DIR, "settings.json")

settings = json.load(open(SETTINGS_PATH, "r"))

XB_SERIAL_PORT = settings["services"]["serial"]["xb-port"]
XB_BAUD_RATE = settings["services"]["serial"]["xb-baud"]

P2_SERIAL_PORT = settings["services"]["serial"]["p2-port"]
P2_BAUD_RATE = settings["services"]["serial"]["p2-baud"]

HEAD_SERIAL_PORT = settings["services"]["serial"]["head-port"]
HEAD_BAUD_RATE = settings["services"]["serial"]["head-baud"]

BROKER = settings["services"]["mqtt"]["address"]
PORT = settings["services"]["mqtt"]["port"]
TOPIC_IMU = settings["services"]["mpu"]["topic-imu"]

USING_BATT_2 = settings["battery"]["enable_two"]
BATT_LOW_VOLT = 90

SETTING_COMBOS = {
    "bauds": [4800, 9600, 19200, 38400, 57600, 115200, 230400, 460800, 624000, 921600],
    "ticks": ["CORE", "0.1s", "0.25s", "0.4s", "0.6s", "0.8s", "1s", "1.5s", "2s"],
}
