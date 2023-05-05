"""
Kevinbot v3 Hardware Service
By: Kevin Ahr
"""

import json
import os
import ast
import traceback
import time

import serial
from xbee import XBee

import colorama

import device_manager
import hardware_utils

# paths
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
SETTINGS_PATH = os.path.join(CURRENT_DIR, 'settings.json')

# settings.json
settings = json.load(open(SETTINGS_PATH, 'r'))

# Device Table Manager
dev_man = device_manager.DeviceManager()

# Color printing
colorama.init()

# variables
connected_remotes = {}


# device communication
def xbee_callback(message):
    # noinspection PyBroadException
    try:
        text_data = message["rf_data"].decode("utf-8").strip("\r\n")
        data = text_data.split("=", maxsplit=1)
        if data[0] == "core.speech":
            dev_man.attach_callback(device_manager.CallbackTypes.ModData, None)
            dev_man.set_value(data[0], data[1])
            dev_man.attach_callback(device_manager.CallbackTypes.ModData, tx_cv)
        elif data[0] == "core.speech-engine":
            dev_man.attach_callback(device_manager.CallbackTypes.ModData, None)
            dev_man.set_value(data[0], data[1])
            dev_man.attach_callback(device_manager.CallbackTypes.ModData, tx_cv)
        elif data[0] == "core.remote.status":
            status, remote = data[1].split(":", maxsplit=1)
            connected_remotes[remote] = status
            print(connected_remotes)

        # value-less commands
        elif data[0] == "stop":
            time.sleep(0.02)
            raw_send("stop")
        elif data[0] == "get_json":
            data = str(dev_man.json_export())
            split_data = [data[i:i+settings["services"]["data_max"]] for i in range(0, len(data), settings["services"]["data_max"])]
            data_to_remote(f"tables.len={len(split_data)-1}")
            for index, part in enumerate(split_data):
                data_to_remote(f"tables.part=\"{part}\"")

        elif data[0] == "pint":
            raw_send(f"{data[0]}={data[1]}")

        elif "color" in data[0]:
            if len(data) == 2:
                dev_man.set_value(data[0], data[1])
                if dev_man.get_value("enabled") is False:
                    disable_actions()

        else:
            if len(data) == 2:
                dev_man.set_value(data[0], hardware_utils.convert_values(data[1]))
                if dev_man.get_value("enabled") is False:
                    disable_actions()
    except Exception:
        print(colorama.Fore.RED + "An error has occurred in XBEE_CALLBACK" + colorama.Style.RESET_ALL)
        traceback.print_exc()


def main_loop():
    while True:
        data = core_serial.readline()
        data = data.decode('utf-8').strip("\r\n").split("=", maxsplit=1)
        print(data)

        if data[0] == "alive":  # The alive command is used as a timer to send device tables
            dev_man.attach_callback(device_manager.CallbackTypes.ModData, None)
            dev_man.set_value("core_secs", int(data[1]))
            dev_man.attach_callback(device_manager.CallbackTypes.ModData, tx_cv)

            for key in dev_man.pairs:
                data_to_remote(f"rx.{key}={dev_man.pairs[key]}")
        if data[0] == "batt_volts":
            dev_man.attach_callback(device_manager.CallbackTypes.ModData, None)
            dev_man.set_value("batt_volt1", int(int(data[1].split(",")[0])))
            dev_man.set_value("batt_volt2", int(int(data[1].split(",")[1])))
            dev_man.attach_callback(device_manager.CallbackTypes.ModData, tx_cv)

            data_to_remote(f"batt_volts={data[1]}")


core_serial = serial.Serial(settings["services"]["serial"]["p2-port"],
                            baudrate=settings["services"]["serial"]["p2-baud"])

xbee_serial = serial.Serial(settings["services"]["serial"]["xb-port"],
                            baudrate=settings["services"]["serial"]["xb-baud"])
xbee = XBee(xbee_serial, escaped=True, callback=xbee_callback)


# Hardware Keys
def add_keys():
    dev_man.add_pair(("left_motor", 1500))
    dev_man.add_pair(("right_motor", 1500))
    dev_man.add_pair(("head_x", 1500))
    dev_man.add_pair(("head_y", 1500))

    dev_man.add_pair(("head_color1", "#000000"))
    dev_man.add_pair(("head_color2", "#000000"))
    dev_man.add_pair(("head_effect", "color1"))
    dev_man.add_pair(("head_effect_brightness", 120))
    dev_man.add_pair(("head_update", 200))

    dev_man.add_pair(("body_color1", "#000000"))
    dev_man.add_pair(("body_color2", "#000000"))
    dev_man.add_pair(("body_effect_brightness", 120))
    dev_man.add_pair(("body_effect", "color1"))
    dev_man.add_pair(("body_update", 200))

    dev_man.add_pair(("base_color1", "#000000"))
    dev_man.add_pair(("base_color2", "#000000"))
    dev_man.add_pair(("base_effect_brightness", "#000000"))
    dev_man.add_pair(("base_effect", "color1"))
    dev_man.add_pair(("base_update", 200))

    dev_man.add_pair(("cam_brightness", 1))

    dev_man.add_pair(("robot_version", device_manager.UNKNOWN_VALUE))
    dev_man.add_pair(("core_millis", 0))
    dev_man.add_pair(("core_secs", 0))
    dev_man.add_pair(("core_clock", device_manager.UNKNOWN_VALUE))

    dev_man.add_pair(("batt_volt1", 120))
    dev_man.add_pair(("batt_volt2", 120))

    dev_man.add_pair(("enabled", False))

    dev_man.add_pair(("core.speech", ""))
    dev_man.add_pair(("core.speech-engine", "espeak"))


def convert_cv(key: str) -> str:
    value = dev_man.get_value(key)
    if key in hardware_utils.CONVERSION_TABLE:
        new_key = hardware_utils.CONVERSION_TABLE[key]
    else:
        new_key = key

    return f"{new_key}={value}"


def tx_cv(key: str, _: any) -> None:
    """ Send command=value data to the Kevinbot Hardware Controller """

    if dev_man.get_value("enabled") is True:
        core_serial.write(convert_cv(key).encode("utf-8"))
        print(f"Sent: {convert_cv(key)}")

def raw_send(data: str) -> None:
    print(f"Sent: {data}")
    core_serial.write(data.encode("utf-8"))


def data_to_remote(data):
    xbee.send("tx", dest_addr=b'\x00\x00', data=data.encode('utf-8'))


def disable_actions():
    raw_send("stop")
    dev_man.attach_callback(device_manager.CallbackTypes.ModData, None)
    dev_man.set_value("left_motor", 1500)
    dev_man.set_value("right_motor", 1500)
    dev_man.attach_callback(device_manager.CallbackTypes.ModData, tx_cv)


if __name__ == "__main__":
    dev_man.attach_callback(device_manager.CallbackTypes.ModData, tx_cv)
    add_keys()
    dev_man.print_data()

    main_loop()