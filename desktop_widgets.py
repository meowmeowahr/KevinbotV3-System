import datetime
import os
import uuid
from typing import Any

import qtawesome as qta
from qtpy.QtCore import Qt, QSize, QTimer
from qtpy.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout, QPushButton,
                            QLabel, QBoxLayout)

import theme_control
from KevinbotUI import KBTheme
from kevinbot_qt_mqtt import MqttClient
from settings import SettingsManager

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
SETTINGS_PATH = os.path.join(CURRENT_DIR, 'settings.json')
settings = SettingsManager(SETTINGS_PATH)


class BaseWidget(QFrame):
    def __init__(self, add=False, data: dict[str, Any] | None = None, mqtt_client: MqttClient | None = None):
        super().__init__()
        if data is None:
            data: dict[str, Any] = {"type": "base", "uuid": str(uuid.uuid4())}
        self.mqtt_client = mqtt_client
        self.data = data
        self.add = add

        self.ensurePolished()
        if theme_control.get_dark():
            self.fg_color = Qt.GlobalColor.white
            KBTheme.load(self, mode=KBTheme.Modes.Dark)
        else:
            self.fg_color = Qt.GlobalColor.black
            KBTheme.load(self, mode=KBTheme.Modes.Light)

        self._root_layout = QVBoxLayout()
        self.setLayout(self._root_layout)
        self.setFrameShape(self.Shape.Box)

        self.top_bar = QHBoxLayout()
        self._root_layout.addLayout(self.top_bar)

        self.title = QLabel("Base Widget")
        self.top_bar.addWidget(self.title)

        self.top_bar.addStretch()

        if add:
            self.add_button = QPushButton()
            self.add_button.setIcon(qta.icon("mdi.plus", color=self.fg_color))
            self.add_button.setFixedSize(QSize(24, 24))
            self.add_button.setIconSize(QSize(24, 24))
            self.top_bar.addWidget(self.add_button)
        else:
            self.up_button = QPushButton()
            self.up_button.setIcon(qta.icon("mdi.arrow-up",
                                            color=self.fg_color))
            self.up_button.setFixedSize(QSize(24, 24))
            self.up_button.setIconSize(QSize(24, 24))
            self.top_bar.addWidget(self.up_button)

            self.down_button = QPushButton()
            self.down_button.setIcon(qta.icon("mdi.arrow-down",
                                              color=self.fg_color))
            self.down_button.setFixedSize(QSize(24, 24))
            self.down_button.setIconSize(QSize(24, 24))
            self.top_bar.addWidget(self.down_button)

            self.remove_button = QPushButton()
            self.remove_button.setIcon(qta.icon("mdi.close",
                                                color=self.fg_color))
            self.remove_button.setFixedSize(QSize(24, 24))
            self.remove_button.setIconSize(QSize(24, 24))
            self.top_bar.addWidget(self.remove_button)

        self._root_layout.addStretch()

    def set_title(self, title: str):
        self.title.setText(title)

    def set_data(self, data: any):
        self.data = data

    def add_layout(self, layout: QBoxLayout):
        self._root_layout.addLayout(layout)
        self._root_layout.addStretch()


class ClockWidget(BaseWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data["type"] = "clock"

        if self.add:
            self.set_title("12-Hour Clock")
        else:
            self.set_title("Clock")

        self.setFixedHeight(200)

        self.layout = QVBoxLayout()
        self.add_layout(self.layout)

        self.time = QLabel("??:?? ??")
        self.time.setStyleSheet("font-size: 48px;")
        self.time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.time)

        self.date = QLabel("??????")
        self.date.setStyleSheet("font-size: 24px;")
        self.date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.date)

        if not self.add:
            self.timer = QTimer()
            self.timer.setInterval(1000)
            self.timer.timeout.connect(self.update_time)
            self.timer.start()

    def update_time(self):
        self.time.setText(datetime.datetime.now().strftime("%I:%M %p").upper())
        self.date.setText(datetime.datetime.now()
                          .strftime("%d, %b %Y").upper())


class Clock24Widget(BaseWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data["type"] = "clock24"

        if self.add:
            self.set_title("24-Hour Clock")
        else:
            self.set_title("Clock")

        self.setFixedHeight(200)

        self.layout = QVBoxLayout()
        self.add_layout(self.layout)

        self.time = QLabel("??:??:??")
        self.time.setStyleSheet("font-size: 48px;")
        self.time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.time)

        self.date = QLabel("??????")
        self.date.setStyleSheet("font-size: 24px;")
        self.date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.date)

        if not self.add:
            self.timer = QTimer()
            self.timer.setInterval(500)
            self.timer.timeout.connect(self.update_time)
            self.timer.start()

    def update_time(self):
        self.time.setText(datetime.datetime.now().strftime("%H:%M:%S").upper())
        self.date.setText(datetime.datetime.now()
                          .strftime("%d, %b %Y").upper())


class EnaWidget(BaseWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data["type"] = "enable"
        self.set_title("Robot Status")

        if self.mqtt_client:
            self.mqtt_client.subscribe(settings.services.com.topic_enabled)
            self.mqtt_client.messageSignal.connect(self.message_slot)

        if "speed" not in self.data:
            self.data["speed"] = 400

        self.enabled = False
        self.light_on = False

        self.setFixedHeight(180)

        self.layout = QVBoxLayout()
        self.add_layout(self.layout)

        self.pulser = QFrame()
        self.pulser.setFixedHeight(64)
        self.pulser.setStyleSheet("background-color: #4CAF50;")
        self.layout.addWidget(self.pulser)

        self.text = QLabel("Disabled")
        self.text.setStyleSheet("font-size: 32px; font-weight: bold")
        self.text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.text)

        if not self.add:
            self.timer = QTimer()
            self.timer.setInterval(self.data["speed"])
            self.timer.timeout.connect(self.pulse)
            self.timer.start()

    def pulse(self):
        if self.enabled:
            self.text.setText("Enabled")
            self.light_on = not self.light_on
            if self.light_on:
                self.pulser.setStyleSheet("background-color: #E53935;")
            else:
                self.pulser.setStyleSheet("background-color: #212121;")
        else:
            self.text.setText("Disabled")
            self.pulser.setStyleSheet("background-color: #4CAF50;")

    def message_slot(self, topic: str, payload: str):
        if settings.services.com.topic_enabled in topic:
            self.enabled = payload.lower() == "true"


class BattWidget(BaseWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.batt1_voltage = 0
        self.batt2_voltage = 0

        self.data["type"] = "batt"
        self.set_title("Battery Status")

        if self.mqtt_client:
            self.mqtt_client.subscribe(settings.services.com.topic_batts)
            self.mqtt_client.messageSignal.connect(self.message_slot)

        if "update" not in self.data:
            self.data["update"] = 2000

        self.setFixedHeight(120)

        self.layout = QVBoxLayout()
        self.add_layout(self.layout)

        if settings.battery.enable_two:
            self.b1 = QLabel("Battery #1 Voltage: ??")
            self.layout.addWidget(self.b1)

            self.b2 = QLabel("Battery #2 Voltage: ??")
            self.layout.addWidget(self.b2)
        else:
            self.b1 = QLabel("Battery Voltage: ??")
            self.layout.addWidget(self.b1)

    def message_slot(self, topic: str, payload: str):
        if settings.services.com.topic_batts in topic:
            self.batt1_voltage, self.batt2_voltage = map(float, payload.split(",", maxsplit=1))

        if settings.battery.enable_two:
            self.b1.setText(f"Battery #1 Voltage: \
                            <b>{self.batt1_voltage}v</b>")
            self.b2.setText(f"Battery #2 Voltage: \
                            <b>{self.batt2_voltage}v</b>")
        else:
            self.b1.setText(f"Battery Voltage: \
                            <b>{self.batt1_voltage}v</b>")


class EmptyWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(80)

        self.data = uuid.uuid4()

        self.ensurePolished()
        if theme_control.get_dark():
            self.fg_color = Qt.GlobalColor.white
            KBTheme.load(self, mode=KBTheme.Modes.Dark)
        else:
            self.fg_color = Qt.GlobalColor.black
            KBTheme.load(self, mode=KBTheme.Modes.Light)

        self._root_layout = QVBoxLayout()
        self.setLayout(self._root_layout)
        self.setFrameShape(self.Shape.Box)

        self.label = QLabel("There are no widgets in the dock")
        self._root_layout.addWidget(self.label)

    def set_title(self, title: str):
        self.label.setText(title)

    def set_data(self, data: any):
        self.data = data


class AddButton(QPushButton):
    def __init__(self):
        super().__init__()

        self.ensurePolished()
        if theme_control.get_dark():
            self.fg_color = Qt.GlobalColor.white
            KBTheme.load(self, mode=KBTheme.Modes.Dark)
        else:
            self.fg_color = Qt.GlobalColor.black
            KBTheme.load(self, mode=KBTheme.Modes.Light)

        self.setIcon(qta.icon("mdi.widgets", color=self.fg_color))
