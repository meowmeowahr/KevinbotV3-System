import json
import os
import platform
import socket
import string
from typing import Any

import psutil
from qtpy.QtCore import Qt, QSize
from qtpy.QtGui import QPalette, QColor, QPixmap
from qtpy.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QScrollArea,
    QToolBox,
    QCheckBox,
    QLineEdit,
    QComboBox,
    QSpinBox)

import theme_control
from KevinbotUI import SwitchControl
from system_options import SETTING_COMBOS

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
SETTINGS_PATH = os.path.join(CURRENT_DIR, 'settings.json')

settings = json.load(open(SETTINGS_PATH, 'r'))


def save_json():
    with open(SETTINGS_PATH, 'w') as f:
        json.dump(settings, f, indent=4)


def detect_model() -> str:
    with open('/proc/device-tree/model') as f:
        model = "".join(filter(lambda x: x in string.printable, f.read()))
    return model


class _SysInfoItem(QWidget):
    def __init__(self, name, data):
        super().__init__()

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.name_label = QLabel(name)
        self.layout.addWidget(self.name_label)

        self.layout.addStretch()

        self.data_label = QLabel(str(data))
        self.data_label.setStyleSheet("font-weight: bold;")
        self.data_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.layout.addWidget(self.data_label)


class ThemePanel(QWidget):

    name = "Theme"

    def __init__(self, parent: Any):
        super().__init__()

        self.parent = parent

        self.setObjectName("Kevinbot3_SettingsPanel_Panel")
        self.root_layout = QHBoxLayout()
        self.setLayout(self.root_layout)

        self.theme_layout = QVBoxLayout()
        self.root_layout.addLayout(self.theme_layout)

        self.label = QLabel(self.name)
        self.label.setStyleSheet("font-weight: bold;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.theme_layout.addWidget(self.label)

        self.theme_layout.addStretch()

        self.theme_select_layout = QHBoxLayout()
        self.theme_layout.addLayout(self.theme_select_layout)

        self.theme_select_label = QLabel("Dark Mode:")
        self.theme_select_layout.addWidget(self.theme_select_label)

        self.ensurePolished()
        self.theme_select_switch = SwitchControl()
        self.theme_select_switch.set_active_color(
            QColor(self.palette().color(QPalette.ColorRole.Highlight)))
        self.theme_select_switch.set_bg_color(
            QColor(self.palette().color(QPalette.ColorRole.Dark)))
        self.theme_select_switch.stateChanged.connect(
            self.theme_select_changed)
        self.theme_select_layout.addWidget(self.theme_select_switch)

        self.theme_layout.addStretch()

        if theme_control.get_dark():
            self.theme_select_switch.setChecked(True)
            self.theme_select_switch.start_animation(True)
        else:
            self.theme_select_switch.setChecked(False)
            self.theme_select_switch.start_animation(False)

    def theme_select_changed(self):
        theme_control.set_theme(self.theme_select_switch.isChecked())
        self.theme_select_switch.set_active_color(
            QColor(self.palette().color(QPalette.ColorRole.Highlight)))
        self.theme_select_switch.set_bg_color(
            QColor(self.palette().color(QPalette.ColorRole.Dark)))
        self.parent.update_icons()


class SysInfoPanel(QScrollArea):

    name = "System Info"

    def __init__(self, _):
        super().__init__()

        self.setObjectName("Kevinbot3_SettingsPanel_Panel")
        self.setWidgetResizable(True)

        self.widget = QWidget()
        self.setWidget(self.widget)

        self.root_layout = QVBoxLayout()
        self.widget.setLayout(self.root_layout)

        self.label = QLabel(self.name)
        self.label.setStyleSheet("font-weight: bold;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.root_layout.addWidget(self.label)

        self.root_layout.addStretch()

        self.layout = QVBoxLayout()
        self.root_layout.addLayout(self.layout)

        self.logo_layout = QHBoxLayout()
        self.kevinbot_logo = QLabel()
        self.kevinbot_logo.setObjectName("Kevinbot3_Settings_Kevinbot_Logo")
        self.kevinbot_logo.setPixmap(
            QPixmap(
                os.path.join(
                    CURRENT_DIR,
                    "icons/kevinbot.svg")))
        self.kevinbot_logo.setScaledContents(True)
        self.kevinbot_logo.setFixedSize(QSize(96, 96))
        self.logo_layout.addWidget(self.kevinbot_logo)

        self.layout.addLayout(self.logo_layout)

        self.name = QLabel("Kevinbot v3")
        self.name.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.name)

        self.h_line = QFrame()
        self.h_line.setFrameShape(QFrame.Shape.HLine)
        self.layout.addWidget(self.h_line)

        self.hostname = _SysInfoItem("Hostname", socket.gethostname())
        self.layout.addWidget(self.hostname)

        self.h_line = QFrame()
        self.h_line.setFrameShape(QFrame.Shape.HLine)
        self.layout.addWidget(self.h_line)

        self.kernel = _SysInfoItem("Kernel Version", platform.release())
        self.layout.addWidget(self.kernel)

        self.h_line = QFrame()
        self.h_line.setFrameShape(QFrame.Shape.HLine)
        self.layout.addWidget(self.h_line)

        self.board = _SysInfoItem("Board", detect_model())
        self.layout.addWidget(self.board)

        self.h_line = QFrame()
        self.h_line.setFrameShape(QFrame.Shape.HLine)
        self.layout.addWidget(self.h_line)

        self.memory = _SysInfoItem(
            "Memory", str(
                round(
                    psutil.virtual_memory().total / 1024 / 1024 / 1024, 2))
            + "GB Total")
        self.layout.addWidget(self.memory)

        self.root_layout.addStretch()


class CommsPanel(QScrollArea):
    name = "Communication"

    def __init__(self, _):
        super().__init__()

        self.setObjectName("Kevinbot3_SettingsPanel_Panel")
        self.setWidgetResizable(True)

        self.widget = QWidget()
        self.setWidget(self.widget)

        self.root_layout = QVBoxLayout()
        self.widget.setLayout(self.root_layout)

        self.label = QLabel(self.name)
        self.label.setStyleSheet("font-weight: bold;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.root_layout.addWidget(self.label)

        self.layout = QVBoxLayout()
        self.root_layout.addLayout(self.layout)

        self.toolbox = QToolBox()
        self.layout.addWidget(self.toolbox)

        self.baud_item = QWidget()
        self.baud_layout = QVBoxLayout()
        self.baud_item.setLayout(self.baud_layout)

        self.core_baud_layout = QHBoxLayout()
        self.baud_layout.addLayout(self.core_baud_layout)

        self.core_baud_label = QLabel("Core Baud")
        self.core_baud_layout.addWidget(self.core_baud_label)

        self.core_baud_combo = QComboBox()
        self.core_baud_combo.addItems(list(map(str, SETTING_COMBOS["bauds"])))
        self.core_baud_combo.setCurrentText(
            str(settings["services"]["serial"]["p2-baud"]))
        self.core_baud_combo.currentTextChanged.connect(self.update_core_baud)
        self.core_baud_layout.addWidget(self.core_baud_combo)

        self.xbee_baud_layout = QHBoxLayout()
        self.baud_layout.addLayout(self.xbee_baud_layout)

        self.xbee_baud_label = QLabel("XBee Baud")
        self.xbee_baud_layout.addWidget(self.xbee_baud_label)

        self.xbee_baud_combo = QComboBox()
        self.xbee_baud_combo.addItems(list(map(str, SETTING_COMBOS["bauds"])))
        self.xbee_baud_combo.setCurrentText(
            str(settings["services"]["serial"]["xb-baud"]))
        self.xbee_baud_combo.currentTextChanged.connect(self.update_xbee_baud)
        self.xbee_baud_layout.addWidget(self.xbee_baud_combo)

        self.head_baud_layout = QHBoxLayout()
        self.baud_layout.addLayout(self.head_baud_layout)

        self.head_baud_label = QLabel("Head Baud")
        self.head_baud_layout.addWidget(self.head_baud_label)

        self.head_baud_combo = QComboBox()
        self.head_baud_combo.addItems(list(map(str, SETTING_COMBOS["bauds"])))
        self.head_baud_combo.setCurrentText(
            str(settings["services"]["serial"]["head-baud"]))
        self.head_baud_combo.currentTextChanged.connect(self.update_head_baud)
        self.head_baud_layout.addWidget(self.head_baud_combo)

        self.toolbox.addItem(self.baud_item, "Baud Rates")

        self.ports_item = QWidget()
        self.ports_layout = QVBoxLayout()
        self.ports_item.setLayout(self.ports_layout)

        self.core_port_layout = QHBoxLayout()
        self.ports_layout.addLayout(self.core_port_layout)

        self.core_port_label = QLabel("Core Port")
        self.core_port_layout.addWidget(self.core_port_label)

        self.core_port_edit = QLineEdit()
        self.core_port_edit.setMaximumWidth(180)
        self.core_port_edit.setText(
            str(settings["services"]["serial"]["p2-port"]))
        self.core_port_edit.textChanged.connect(self.update_core_port)
        self.core_port_layout.addWidget(self.core_port_edit)

        self.xbee_port_layout = QHBoxLayout()
        self.ports_layout.addLayout(self.xbee_port_layout)

        self.xbee_port_label = QLabel("XBee Port")
        self.xbee_port_layout.addWidget(self.xbee_port_label)

        self.xbee_port_edit = QLineEdit()
        self.xbee_port_edit.setMaximumWidth(180)
        self.xbee_port_edit.setText(
            str(settings["services"]["serial"]["xb-port"]))
        self.xbee_port_edit.textChanged.connect(self.update_xbee_port)
        self.xbee_port_layout.addWidget(self.xbee_port_edit)

        self.head_port_layout = QHBoxLayout()
        self.ports_layout.addLayout(self.head_port_layout)

        self.head_port_label = QLabel("Head Port")
        self.head_port_layout.addWidget(self.head_port_label)

        self.head_port_edit = QLineEdit()
        self.head_port_edit.setMaximumWidth(180)
        self.head_port_edit.setText(
            str(settings["services"]["serial"]["head-port"]))
        self.head_port_edit.textChanged.connect(self.update_head_port)
        self.head_port_layout.addWidget(self.head_port_edit)

        self.toolbox.addItem(self.ports_item, "Serial Ports")

        self.restart_warning = QLabel(
            "A restart is required for these settings to update")
        self.layout.addWidget(self.restart_warning)

    @staticmethod
    def update_core_baud(baud: str):
        settings["services"]["serial"]["p2-baud"] = int(baud)
        save_json()

    @staticmethod
    def update_xbee_baud(baud: str):
        settings["services"]["serial"]["xb-baud"] = int(baud)
        save_json()

    @staticmethod
    def update_head_baud(baud: str):
        settings["services"]["serial"]["head-baud"] = int(baud)
        save_json()

    @staticmethod
    def update_core_port(port: str):
        settings["services"]["serial"]["p2-port"] = port
        save_json()

    @staticmethod
    def update_xbee_port(port: str):
        settings["services"]["serial"]["xb-port"] = port
        save_json()

    @staticmethod
    def update_head_port(port: str):
        settings["services"]["serial"]["head-port"] = port
        save_json()


class ServicesPanel(QScrollArea):
    name = "Services"

    def __init__(self, _):
        super().__init__()

        self.setObjectName("Kevinbot3_SettingsPanel_Panel")
        self.setWidgetResizable(True)

        self.widget = QWidget()
        self.setWidget(self.widget)

        self.root_layout = QVBoxLayout()
        self.widget.setLayout(self.root_layout)

        self.label = QLabel(self.name)
        self.label.setStyleSheet("font-weight: bold;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.root_layout.addWidget(self.label)

        self.layout = QVBoxLayout()
        self.root_layout.addLayout(self.layout)

        self.toolbox = QToolBox()
        self.layout.addWidget(self.toolbox)

        self.com_item = QWidget()
        self.com_layout = QVBoxLayout()
        self.com_item.setLayout(self.com_layout)

        self.batt_layout = QHBoxLayout()
        self.com_layout.addLayout(self.batt_layout)

        self.batt_label = QLabel("Battery MQTT Topic")
        self.batt_layout.addWidget(self.batt_label)

        self.batt_edit = QLineEdit()
        self.batt_edit.setMaximumWidth(180)
        self.batt_edit.setText(str(settings["services"]["com"]["topic-batts"]))
        self.batt_edit.textChanged.connect(self.update_batt)
        self.batt_layout.addWidget(self.batt_edit)

        self.uptime_os_layout = QHBoxLayout()
        self.com_layout.addLayout(self.uptime_os_layout)

        self.uptime_os_label = QLabel("Sys Uptime MQTT Topic")
        self.uptime_os_layout.addWidget(self.uptime_os_label)

        self.uptime_os_edit = QLineEdit()
        self.uptime_os_edit.setMaximumWidth(180)
        self.uptime_os_edit.setText(
            str(settings["services"]["com"]["topic-sys-uptime"]))
        self.uptime_os_edit.textChanged.connect(self.update_uptime_os)
        self.uptime_os_layout.addWidget(self.uptime_os_edit)

        self.uptime_core_layout = QHBoxLayout()
        self.com_layout.addLayout(self.uptime_core_layout)

        self.uptime_core_label = QLabel("Core Uptime MQTT Topic")
        self.uptime_core_layout.addWidget(self.uptime_core_label)

        self.uptime_core_edit = QLineEdit()
        self.uptime_core_edit.setMaximumWidth(180)
        self.uptime_core_edit.setText(
            str(settings["services"]["com"]["topic-core-uptime"]))
        self.uptime_core_edit.textChanged.connect(self.update_uptime_core)
        self.uptime_core_layout.addWidget(self.uptime_core_edit)

        self.tick_layout = QHBoxLayout()
        self.com_layout.addLayout(self.tick_layout)

        self.tick_label = QLabel("Tick Speed")
        self.tick_layout.addWidget(self.tick_label)

        self.tick_combo = QComboBox()
        self.tick_combo.addItems(list(map(str, SETTING_COMBOS["ticks"])))
        self.tick_combo.setCurrentText(
            str(settings["services"]["com"]["tick"]))
        self.tick_combo.currentTextChanged.connect(self.update_tick)
        self.tick_layout.addWidget(self.tick_combo)

        self.toolbox.addItem(self.com_item, "Communication Service")

        self.mpu_item = QWidget()
        self.mpu_layout = QVBoxLayout()
        self.mpu_item.setLayout(self.mpu_layout)

        self.mpu_enable = QCheckBox("Enable")
        self.mpu_enable.setChecked(settings["services"]["mpu"]["enabled"])
        self.mpu_enable.stateChanged.connect(self.update_mpu_ena)
        self.mpu_layout.addWidget(self.mpu_enable)

        self.mpu_addr_layout = QHBoxLayout()
        self.mpu_layout.addLayout(self.mpu_addr_layout)

        self.mpu_addr_label = QLabel("Address")
        self.mpu_addr_layout.addWidget(self.mpu_addr_label)

        self.mpu_addr_spin = QSpinBox()
        self.mpu_addr_spin.setDisplayIntegerBase(16)
        self.mpu_addr_spin.setPrefix("0x")
        self.mpu_addr_spin.setRange(0x00, 0x7f)
        self.mpu_addr_spin.setAccelerated(True)
        self.mpu_addr_spin.setValue(settings["services"]["mpu"]["address"])
        self.mpu_addr_spin.valueChanged.connect(self.update_mpu_addr)
        self.mpu_addr_layout.addWidget(self.mpu_addr_spin)

        self.toolbox.addItem(self.mpu_item, "MPU9250 Service")

        self.restart_warning = QLabel(
            "A restart is required for these settings to update")
        self.layout.addWidget(self.restart_warning)

    @staticmethod
    def update_batt(topic: str):
        settings["services"]["com"]["topic-batts"] = topic
        save_json()

    @staticmethod
    def update_uptime_os(topic: str):
        settings["services"]["com"]["topic-sys-uptime"] = topic
        save_json()

    @staticmethod
    def update_uptime_core(topic: str):
        settings["services"]["com"]["topic-core-uptime"] = topic
        save_json()

    @staticmethod
    def update_tick(value: str):
        settings["services"]["com"]["tick"] = value
        save_json()

    @staticmethod
    def update_mpu_ena(value: str):
        settings["services"]["mpu"]["enabled"] = bool(value)
        save_json()

    @staticmethod
    def update_mpu_addr(value: str):
        settings["services"]["mpu"]["address"] = value
        save_json()
