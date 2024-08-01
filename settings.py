# Kevinbot Settings Manager

import json
from typing import Any, Dict, List, Literal


class _SysInfo:
    def __init__(self, data: Dict[str, Any]):
        self.interval: int = data.get("interval", 2)


class _Settings:
    def __init__(self, data: Dict[str, Any]):
        self.page: int = data.get("page", 4)


class _Logging:
    def __init__(self, data: Dict[str, Any]):
        self.level: int = data.get("level", 0)


class _ServoMappings:
    def __init__(self, data: Dict[str, Any]):
        self.arms: dict | None = data.get("arms")
        self.head: dict | None = data.get("head")


class _Servos:
    def __init__(self, data: Dict[str, Any]):
        self.mappings: _ServoMappings | None = data.get("mappings")


class _Battery:
    def __init__(self, data: Dict[str, Any]):
        self.enable_two: bool = data.get("enable_two", True)
        self.cutoff_voltages: List[float] = data.get("cutoff_voltages", [8.0, 16.8])
        self.warn_voltages: List[float] = data.get("warn_voltages", [10.5, 17.2])
        self.warn_sound: Literal["repeat", "once", "never"] | str = data.get("warn_sound", "once")


class _LightingSection:
    def __init__(self, data: Dict[str, Any]):
        self.update: int = data.get("update", 200)
        self.brightness: int = data.get("brightness", 120)


class _Lighting:
    def __init__(self, data: Dict[str, Any]):
        self.head: _LightingSection | None = _LightingSection(data.get("head"))
        self.body: _LightingSection | None = _LightingSection(data.get("body"))
        self.base: _LightingSection | None = _LightingSection(data.get("base"))


class _MQTT:
    def __init__(self, data: Dict[str, Any]):
        self.port: int = data.get("port", 1883)
        self.address: str = data.get("address", "localhost")


class _Serial:
    def __init__(self, data: Dict[str, Any]):
        self.p2_baud: int = data.get("p2-baud", 624000)
        self.p2_port: str = data.get("p2-port", "/dev/ttyAMA2")
        self.xb_baud: int = data.get("xb-baud", 460800)
        self.xb_port: str = data.get("xb-port", "/dev/ttyAMA0")
        self.head_baud: int = data.get("head-baud", 115200)
        self.head_port: str = data.get("head-port", "/dev/ttyUSB0")


class _Com:
    def __init__(self, data: Dict[str, Any]):
        self.tick: str = data.get("tick", "1s")
        self.topic_batt1: str = data.get("topic-batt1", "kevinbot/battery/batt1")
        self.topic_batt2: str = data.get("topic-batt2", "kevinbot/battery/batt2")
        self.topic_sys_uptime: str = data.get("topic-sys-uptime", "kevinbot/uptimes/os")
        self.topic_core_uptime: str = data.get("topic-core-uptime", "kevinbot/uptimes/core")
        self.topic_enabled: str = data.get("topic-enabled", "kevinbot/enabled")
        self.data_max: int = data.get("data_max", 50)


class _MPU:
    def __init__(self, data: Dict[str, Any]):
        self.enabled: bool = data.get("enabled", True)
        self.address: int = data.get("address", 104)
        self.update_speed: float = data.get("update-speed", 0.1)
        self.topic_roll: str = data.get("topic-roll", "kevinbot/mpu/roll")
        self.topic_pitch: str = data.get("topic-pitch", "kevinbot/mpu/pitch")
        self.topic_yaw: str = data.get("topic-yaw", "kevinbot/mpu/yaw")


class _BME:
    def __init__(self, data: Dict[str, Any]):
        self.update_speed: float = data.get("update-speed", 0.1)
        self.topic_temp: str = data.get("topic-temp", "kevinbot/bme/temperature")
        self.topic_humidity: str = data.get("topic-humidity", "kevinbot/bme/humidity")
        self.topic_pressure: str = data.get("topic-pressure", "kevinbot/bme/pressure")


class _Services:
    def __init__(self, data: Dict[str, Any]):
        self.mqtt: _MQTT = _MQTT(data.get("mqtt", {}))
        self.serial: _Serial = _Serial(data.get("serial", {}))
        self.com: _Com = _Com(data.get("com", {}))
        self.mpu: _MPU = _MPU(data.get("mpu", {}))
        self.bme: _BME = _BME(data.get("bme", {}))


class SettingsManager:
    def __init__(self, filepath: str = 'settings.json'):
        self.services: _Services | None = None
        self.servo: _Servos | None = None
        self.battery: _Battery | None = None
        self.lighting: _Lighting | None = None
        self.logging: _Logging | None = None
        self.settings_gui: _Settings | None = None
        self.sysinfo: _SysInfo | None = None
        self.filepath = filepath

        self.load()

    def _get_data(self):
        return {
            "sysinfo": self.sysinfo.__dict__,
            "settings": self.settings_gui.__dict__,
            "logging": self.logging.__dict__,
            "servos": self.servo.__dict__,
            "battery": self.battery.__dict__,
            "lighting": self.lighting.__dict__,
            "services": {
                "mqtt": self.services.mqtt.__dict__,
                "serial": self.services.serial.__dict__,
                "com": self.services.com.__dict__,
                "mpu": self.services.mpu.__dict__,
                "bme": self.services.bme.__dict__
            }
        }

    def load(self) -> None:
        try:
            with open(self.filepath, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {}
        self.sysinfo = _SysInfo(data.get("sysinfo", {}))
        self.settings_gui = _Settings(data.get("settings", {}))
        self.logging = _Logging(data.get("logging", {}))
        self.servo = _Servos(data.get("servos", {}))
        self.battery = _Battery(data.get("battery", {}))
        self.lighting = _Lighting(data.get("lighting", {}))
        self.services = _Services(data.get("services", {}))

    def save(self) -> None:
        with open(self.filepath, 'w') as file:
            json.dump(self._get_data(), file, indent=4)

    def __repr__(self):
        return f"{super().__repr__()}\n\n{json.dumps(self._get_data(), indent=2)}"


if __name__ == "__main__":
    settings = SettingsManager("settings.json")
    print(settings)
