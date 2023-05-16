from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from KevinbotUI import SwitchControl
import theme_control
import socket
import json
import psutil
import os
import platform

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
SETTINGS_PATH = os.path.join(CURRENT_DIR, 'settings.json')

settings = json.load(open(SETTINGS_PATH, 'r'))


def save_json():
    with open(SETTINGS_PATH, 'w') as f:
        json.dump(settings, f, indent=4)


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
        self.layout.addWidget(self.data_label)


class ThemePanel(QWidget):
    
    name = "Theme"
    
    def __init__(self, parent):
        super().__init__()

        self.parent = parent

        self.setObjectName("Kevinbot3_SettingsPanel_Panel")
        self.root_layout = QHBoxLayout()
        self.setLayout(self.root_layout)

        self.theme_layout = QVBoxLayout()
        self.root_layout.addLayout(self.theme_layout)

        self.label = QLabel(self.name)
        self.label.setStyleSheet("font-weight: bold;")
        self.label.setAlignment(Qt.AlignCenter)
        self.theme_layout.addWidget(self.label)

        self.theme_layout.addStretch()

        self.theme_select_layout = QHBoxLayout()
        self.theme_layout.addLayout(self.theme_select_layout)

        self.theme_select_label = QLabel("Dark Mode:")
        self.theme_select_layout.addWidget(self.theme_select_label)

        self.theme_select_switch = SwitchControl()
        self.theme_select_switch.set_active_color(QColor(self.palette().color(QPalette.Highlight)))
        self.theme_select_switch.set_bg_color(QColor(self.palette().color(QPalette.ColorRole.Dark)))
        self.theme_select_switch.stateChanged.connect(self.theme_select_changed)
        self.theme_select_layout.addWidget(self.theme_select_switch)

        self.theme_layout.addStretch()

        if theme_control.get_dark():
            self.theme_select_switch.setChecked(True)
            self.theme_select_switch.start_animation(True)
        else:
            self.theme_select_switch.setChecked(False)
            self.theme_select_switch.start_animation(False)

    def theme_select_changed(self, index):
        theme_control.set_theme(self.theme_select_switch.isChecked())
        self.theme_select_switch.set_active_color(QColor(self.palette().color(QPalette.Highlight)))
        self.theme_select_switch.set_bg_color(QColor(self.palette().color(QPalette.ColorRole.Dark)))
        self.parent.update_icons()


class SysInfoPanel(QScrollArea):
    
    name = "System Info"
    
    def __init__(self, parent):
        super().__init__()
        
        self.setObjectName("Kevinbot3_SettingsPanel_Panel")
        self.setWidgetResizable(True)

        self.widget = QWidget()
        self.setWidget(self.widget)

        self.root_layout = QVBoxLayout()
        self.widget.setLayout(self.root_layout)

        self.label = QLabel(self.name)
        self.label.setStyleSheet("font-weight: bold;")
        self.label.setAlignment(Qt.AlignCenter)
        self.root_layout.addWidget(self.label)

        self.root_layout.addStretch()

        self.layout = QVBoxLayout()
        self.root_layout.addLayout(self.layout)

        self.logo_layout = QHBoxLayout()
        self.kevinbot_logo = QLabel()
        self.kevinbot_logo.setObjectName("Kevinbot3_Settings_Kevinbot_Logo")
        self.kevinbot_logo.setPixmap(QPixmap(os.path.join(CURRENT_DIR, "icons/kevinbot.svg")))
        self.kevinbot_logo.setScaledContents(True)
        self.kevinbot_logo.setFixedSize(QSize(96, 96))
        self.logo_layout.addWidget(self.kevinbot_logo)

        self.layout.addLayout(self.logo_layout)

        self.name = QLabel("Kevinbot v3")
        self.name.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.name.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.name)

        self.h_line = QFrame()
        self.h_line.setFrameShape(QFrame.HLine)
        self.layout.addWidget(self.h_line)

        self.hostname = _SysInfoItem("Hostname", socket.gethostname())
        self.layout.addWidget(self.hostname)

        self.h_line = QFrame()
        self.h_line.setFrameShape(QFrame.HLine)
        self.layout.addWidget(self.h_line)

        self.kernel = _SysInfoItem("Kernel Version", platform.release())
        self.layout.addWidget(self.kernel)

        self.h_line = QFrame()
        self.h_line.setFrameShape(QFrame.HLine)
        self.layout.addWidget(self.h_line)

        self.memory = _SysInfoItem("Memory",
                                   str(round(psutil.virtual_memory().total / 1024 / 1024 / 1024, 2)) + "GB Total")
        self.layout.addWidget(self.memory)

        self.root_layout.addStretch()


class CommsPanel(QScrollArea):
    name = "Communication"

    def __init__(self, parent):
        super().__init__()

        self.setObjectName("Kevinbot3_SettingsPanel_Panel")
        self.setWidgetResizable(True)

        self.widget = QWidget()
        self.setWidget(self.widget)

        self.root_layout = QVBoxLayout()
        self.widget.setLayout(self.root_layout)

        self.label = QLabel(self.name)
        self.label.setStyleSheet("font-weight: bold;")
        self.label.setAlignment(Qt.AlignCenter)
        self.root_layout.addWidget(self.label)

        self.root_layout.addStretch()

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
        self.core_baud_combo.addItems(map(str, settings["constants"]["bauds"]))
        self.core_baud_combo.setCurrentText(str(settings["services"]["serial"]["p2-baud"]))
        self.core_baud_combo.currentTextChanged.connect(self.update_core_baud)
        self.core_baud_layout.addWidget(self.core_baud_combo)

        self.toolbox.addItem(self.baud_item, "Baud Rates")

    def update_core_baud(self, baud):
        settings["services"]["serial"]["p2-baud"] = int(baud)
        save_json()
