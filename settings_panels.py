from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from KevinbotUI import SwitchControl
import theme_control
import json
import os

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
SETTINGS_PATH = os.path.join(CURRENT_DIR, 'settings.json')

settings = json.load(open(SETTINGS_PATH, 'r'))

def save_json():
    with open(SETTINGS_PATH, 'w') as f:
        json.dump(settings, f, indent=4)

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


class SysInfoPanel(QWidget):
    
    name = "System Info"
    
    def __init__(self, parent):
        super().__init__()
        
        self.setObjectName("Kevinbot3_SettingsPanel_Panel")
        self.root_layout = QVBoxLayout()
        self.setLayout(self.root_layout)

        self.label = QLabel(self.name)
        self.label.setStyleSheet("font-weight: bold;")
        self.label.setAlignment(Qt.AlignCenter)
        self.root_layout.addWidget(self.label)

        self.root_layout.addStretch()

        self.layout = QGridLayout()
        self.root_layout.addLayout(self.layout)

        self.update_interval_label = QLabel("Update interval (seconds):")
        self.layout.addWidget(self.update_interval_label, 0, 0)

        self.update_interval_spinbox = QSpinBox()
        self.update_interval_spinbox.setMinimum(1)
        self.update_interval_spinbox.setMaximum(5)
        self.update_interval_spinbox.setMinimumWidth(64)
        self.update_interval_spinbox.setValue(settings["sysinfo"]["interval"])
        self.update_interval_spinbox.valueChanged.connect(self.update_interval_changed)
        self.layout.addWidget(self.update_interval_spinbox, 0, 1)

        self.root_layout.addStretch()

    def update_interval_changed(self):
        settings["sysinfo"]["interval"] = self.update_interval_spinbox.value()
        save_json()