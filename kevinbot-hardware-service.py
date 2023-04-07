"""
Kevinbot v3 Hardware Service
By: Kevin Ahr
"""

import json
import os

import device_manager
import hardware_utils
import kevinbot_communication

# paths
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
SETTINGS_PATH = os.path.join(CURRENT_DIR, 'settings.json')

# settings.json
settings = json.load(open(SETTINGS_PATH, 'r'))

# Device Table Manager
dev_man = device_manager.DeviceManager()


# device communication
def xbee_callback(message):
    text_data = message["rf_data"].decode("utf-8")
    print(text_data)


kevinbot_communication.init_core(settings["services"]["serial"]["p2-port"], settings["services"]["serial"]["p2-baud"])
kevinbot_communication.init_xbee(settings["services"]["serial"]["xb-port"], settings["services"]["serial"]["xb-baud"],
                                 callback=xbee_callback)


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
    dev_man.add_pair(("core_millis", device_manager.UNKNOWN_VALUE))
    dev_man.add_pair(("core_clock", device_manager.UNKNOWN_VALUE))

    dev_man.add_pair(("enabled", False))


def convert_cv(key: str) -> str:
    value = dev_man.get_value(key)
    if key in hardware_utils.CONVERSION_TABLE:
        new_key = hardware_utils.CONVERSION_TABLE[key]
    else:
        new_key = key

    return f"{new_key}={value}"


def tx_cv(key: str, _: any) -> None:
    """ Send command=value data to the Kevinbot Core """

    print(f"Sent: {convert_cv(key)}")


if __name__ == "__main__":
    dev_man.attach_callback(device_manager.CallbackTypes.ModData, tx_cv)
    add_keys()
    dev_man.print_data()
