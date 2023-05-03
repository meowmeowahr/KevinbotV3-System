"""
Kevinbot v3 Device Manager
By: Kevin Ahr
"""

from enum import Enum
import json

UNKNOWN_VALUE = None


class CallbackTypes(Enum):
    NewPair = 0
    DelPair = 1
    ModData = 2


class DeviceManager:
    def __init__(self) -> None:
        self.__device_pairs = {}

        self.__new_callback = None
        self.__del_callback = None
        self.__mod_callback = None

    def json_import(self, data: dict) -> None:
        if not isinstance(data, (tuple, list)):
            raise ValueError(f"Expected dict, got {type(data)}")

        self.__device_pairs = data

    def json_export(self) -> dict:
        return json.dumps(self.__device_pairs)

    def print_data(self) -> None:
        """ Print out all pairs in a pretty format """

        longest_key = len(max(self.__device_pairs, key=len))
        print("KEY", " " * (longest_key - 2), "|", "VALUE")
        for key in self.__device_pairs:
            print(key, " " * (longest_key + 1 - len(key)), "|", self.__device_pairs[key])

    def attach_callback(self, event: CallbackTypes, callback) -> None:
        if event == CallbackTypes.NewPair:
            self.__new_callback = callback
        elif event == CallbackTypes.DelPair:
            self.__del_callback = callback
        elif event == CallbackTypes.ModData:
            self.__mod_callback = callback

    def add_pair(self, pair: [tuple, list]) -> None:
        if not isinstance(pair, (tuple, list)):
            raise ValueError(f"Expected tuple or list, got {type(pair)}")

        self.__device_pairs[pair[0]] = pair[1]

        if self.__new_callback:
            self.__new_callback(pair[0], pair[1])

    def del_pair(self, key: str) -> None:
        del self.__device_pairs[key]

        if self.__del_callback:
            self.__del_callback(key)

    def get_value_type(self, key: str) -> type:
        return type(self.__device_pairs[key])

    def get_value(self, key: str):
        return self.__device_pairs[key]

    def set_value(self, key: str, value) -> None:
        if not (type(self.__device_pairs[key]) == type(value) or value == UNKNOWN_VALUE):
            raise ValueError(f"Can't set a a value of {type(self.__device_pairs[key])} to {type(value)}")

        if key not in self.__device_pairs:
            raise RuntimeWarning(f"Key {key} does not exist in the table")

        self.__device_pairs[key] = value

        if self.__mod_callback:
            self.__mod_callback(key, value)

    @property
    def pairs(self):
        return self.__device_pairs

    @property
    def pair_count(self) -> int:
        return len(self.__device_pairs)