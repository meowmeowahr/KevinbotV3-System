"""
Kevinbot SysInfo
A simple app to view hardware and software information

Author: Kevin Ahr
"""

from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *
from KevinbotUI import AboutBox
import json
import sys
import os

import psutil
import platform
import cpuinfo
import socket
import getpass

if platform.system() == 'Windows':
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("_")

__version__ = 'v0.1.0'
__author__ = 'Kevin Ahr'

ENABLE_BATT = False

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
SETTINGS_PATH = os.path.join(CURRENT_DIR, 'settings.json')

settings = json.load(open(SETTINGS_PATH, 'r'))


def save_settings():
    with open(SETTINGS_PATH, 'w') as f:
        json.dump(settings, f, indent=4)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kevinbot System Information")
        self.setMinimumSize(800, 600)
        self.setWindowIcon(QIcon(os.path.join(CURRENT_DIR, "icons/", "sysinfo-icon.svg")))

        self.item_widgets = []
        self.item_count = 0

        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_widget.setLayout(self.main_layout)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        QScroller.grabGesture(self.scroll, QScroller.LeftMouseButtonGesture);
        self.main_layout.addWidget(self.scroll)

        self.widget = QWidget()
        self.scroll.setWidget(self.widget)
        
        self.layout = QVBoxLayout()
        self.widget.setLayout(self.layout)

        self.setCentralWidget(self.main_widget)

        # menu
        self.menu_bar = QMenuBar()
        self.setMenuBar(self.menu_bar)

        # file menu
        self.file_menu = self.menu_bar.addMenu("File")
        self.file_menu.addAction("Quit", self.close)

        # edit menu
        self.edit_menu = self.menu_bar.addMenu("Edit")
        self.settings_action = self.edit_menu.addAction("Settings", self.open_settings)

        self.about_box = AboutBox(__author__, "Kevinbot SysInfo", __version__, os.path.join(CURRENT_DIR, "icons/", "sysinfo-icon.svg"), os.path.join(CURRENT_DIR, "icons/sysinfo-icon.svg"))
        
        # help menu
        self.help_menu = self.menu_bar.addMenu("Help")
        self.help_menu.addAction("About", self.about_box.show)

        self.cpu_label = QLabel("CPU:")
        self.cpu_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.cpu_label.setFixedHeight(30)

        self.cores_label = QLabel("Cores: {}".format(psutil.cpu_count(logical=True)))
        self.cores_label.setStyleSheet("font-size: 13px;")
        self.cores_label.setFixedHeight(20)

        self.logical_label = QLabel("Logical: {}".format(psutil.cpu_count(logical=False)))
        self.logical_label.setStyleSheet("font-size: 13px;")
        self.logical_label.setFixedHeight(20)

        self.model_label = QLabel("Model: {}".format(cpuinfo.get_cpu_info()['brand_raw']))
        self.model_label.setStyleSheet("font-size: 13px;")
        self.model_label.setFixedHeight(20)

        self.usage_label = QLabel("Usage: {}%".format(psutil.cpu_percent()))
        self.usage_label.setStyleSheet("font-size: 13px;")
        self.usage_label.setFixedHeight(20)

        self.item_count += 1
        self.add_item("#4fec88", "#44a22f", [self.cpu_label, self.cores_label, self.logical_label, self.model_label, self.usage_label], self.item_count-1, icon=os.path.join(CURRENT_DIR, "icons/cpu.svg"))


        self.mem_label = QLabel("Memory:")
        self.mem_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.mem_label.setFixedHeight(30)

        self.total_label = QLabel("Total: {}GB".format(round(psutil.virtual_memory().total / 1024 / 1024 / 1024, 2)))
        self.total_label.setStyleSheet("font-size: 13px;")
        self.total_label.setFixedHeight(20)

        self.available_label = QLabel("Available: {}GB".format(round(psutil.virtual_memory().available / 1024 / 1024 / 1024, 2)))
        self.available_label.setStyleSheet("font-size: 13px;")
        self.available_label.setFixedHeight(20)
        
        self.used_label = QLabel("Used: {}GB ({}%)".format(round(psutil.virtual_memory().used / 1024 / 1024 / 1024, 2), psutil.virtual_memory().percent))
        self.used_label.setStyleSheet("font-size: 13px;")
        self.used_label.setFixedHeight(20)

        self.item_count += 1
        self.add_item("#36a7f2", "#6fddff", [self.mem_label, self.total_label, self.available_label, self.used_label], self.item_count-1, icon=os.path.join(CURRENT_DIR, "icons/memory.svg"))

        self.disk_label = QLabel("Disks / Partitions:")
        self.disk_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.disk_label.setFixedHeight(30)

        # spreadsheet of disks and partitions
        self.disk_list = QTableWidget()
        self.disk_list.setStyleSheet("font-size: 13px;")
        self.disk_list.setFixedHeight(100)
        self.disk_list.verticalHeader().setVisible(False)

        self.disk_list.setColumnCount(6)
        self.disk_list.setRowCount(len(psutil.disk_partitions()))
        self.disk_list.setHorizontalHeaderLabels(["Device", "Mountpoint", "FS", "Total", "Free", "Used"])

        for i in range(self.disk_list.columnCount()):
            self.disk_list.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)


        for i, disk in enumerate(psutil.disk_partitions()):
            self.disk_list.setItem(i, 0, QTableWidgetItem(disk.device))
            self.disk_list.setItem(i, 1, QTableWidgetItem(disk.mountpoint))
            self.disk_list.setItem(i, 2, QTableWidgetItem(disk.fstype))
            self.disk_list.setItem(i, 3, QTableWidgetItem(str(round(psutil.disk_usage(disk.mountpoint).total / 1024 / 1024 / 1024, 2))))
            self.disk_list.setItem(i, 4, QTableWidgetItem("{}GB".format(round(psutil.disk_usage(disk.mountpoint).free / 1024 / 1024 / 1024, 2))))
            self.disk_list.setItem(i, 5, QTableWidgetItem("{}GB ({}%)".format(round(psutil.disk_usage(disk.mountpoint).used / 1024 / 1024 / 1024, 2), psutil.disk_usage(disk.mountpoint).percent)))
        for i in range(self.disk_list.rowCount()):
            self.disk_list.setRowHeight(i, 20)
            for j in range(self.disk_list.columnCount()):
                self.disk_list.item(i, j).setTextAlignment(Qt.AlignCenter)
                self.disk_list.item(i, j).setFlags(Qt.ItemIsEnabled)


        self.item_count += 1
        self.add_item("#f2a736", "#ffd86f", [self.disk_label, self.disk_list], self.item_count-1, icon=os.path.join(CURRENT_DIR, "icons/harddisk.svg"))

        self.network_label = QLabel("Network:")
        self.network_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.network_label.setFixedHeight(30)

        self.ip_label = QLabel("IP: {}".format(socket.gethostbyname(socket.gethostname())))
        self.ip_label.setStyleSheet("font-size: 13px;")
        self.ip_label.setFixedHeight(20)

        self.hostname_label = QLabel("Hostname: {}".format(socket.gethostname()))
        self.hostname_label.setStyleSheet("font-size: 13px;")
        self.hostname_label.setFixedHeight(20)

        self.network_list = QTableWidget()
        self.network_list.setStyleSheet("font-size: 13px;")
        self.network_list.verticalHeader().setVisible(False)

        self.network_list.setColumnCount(5)
        self.network_list.setRowCount(len(psutil.net_io_counters(pernic=True)))
        self.network_list.setHorizontalHeaderLabels(["Interface", "Bytes Sent", "Bytes Received", "Packets Sent", "Packets Received"])

        for i in range(self.network_list.columnCount()):
            self.network_list.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)

        for i, interface in enumerate(psutil.net_io_counters(pernic=True)):
            self.network_list.setItem(i, 0, QTableWidgetItem(interface))
            self.network_list.setItem(i, 1, QTableWidgetItem(str(round(psutil.net_io_counters(pernic=True)[interface].bytes_sent / 1024 / 1024, 2))))
            self.network_list.setItem(i, 2, QTableWidgetItem(str(round(psutil.net_io_counters(pernic=True)[interface].bytes_recv / 1024 / 1024, 2))))
            self.network_list.setItem(i, 3, QTableWidgetItem(str(psutil.net_io_counters(pernic=True)[interface].packets_sent)))
            self.network_list.setItem(i, 4, QTableWidgetItem(str(psutil.net_io_counters(pernic=True)[interface].packets_recv)))

        for i in range(self.network_list.rowCount()):
            self.network_list.setRowHeight(i, 20)
            for j in range(self.network_list.columnCount()):
                self.network_list.item(i, j).setTextAlignment(Qt.AlignCenter)
                self.network_list.item(i, j).setFlags(Qt.ItemIsEnabled)

        self.item_count += 1
        self.add_item("#f5e837", "#ffc91e", [self.network_label, self.ip_label, self.hostname_label, self.network_list], self.item_count-1, max_height=500, icon=os.path.join(CURRENT_DIR, "icons/network.svg"), min_height=300)
        

        if ENABLE_BATT:
            try:
                # battery item
                self.battery_label = QLabel("Battery:")
                self.battery_label.setStyleSheet("font-size: 15px; font-weight: bold;")
                self.battery_label.setFixedHeight(30)

                self.battery_time_label = QLabel("Time left: {}s".format(psutil.sensors_battery().secsleft))
                self.battery_time_label.setStyleSheet("font-size: 13px;")
                self.battery_time_label.setFixedHeight(20)

                self.battery_percent_label = QLabel("Percent: {}%".format(psutil.sensors_battery().percent))
                self.battery_percent_label.setStyleSheet("font-size: 13px;")
                self.battery_percent_label.setFixedHeight(20)

                self.battery_power_label = QLabel("Power: {}".format(psutil.sensors_battery().power_plugged))
                self.battery_power_label.setStyleSheet("font-size: 13px;")
                self.battery_power_label.setFixedHeight(20)

                self.item_count += 1
                self.add_item("#f43204", "#fb1385", [self.battery_label, self.battery_time_label, self.battery_percent_label, self.battery_power_label], self.item_count-1, icon=os.path.join(CURRENT_DIR, "icons/battery.svg"))

            except Exception as e:
                self.item_widgets.append("Battery not found")

        # python info
        self.python_label = QLabel("Python:")
        self.python_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.python_label.setFixedHeight(30)

        self.python_version_label = QLabel("Version: {}".format(platform.python_version()))
        self.python_version_label.setStyleSheet("font-size: 13px;")
        self.python_version_label.setFixedHeight(20)

        self.python_architecture_label = QLabel("Architecture: {}".format(platform.architecture()[0]))
        self.python_architecture_label.setStyleSheet("font-size: 13px;")
        self.python_architecture_label.setFixedHeight(20)

        self.python_machine_label = QLabel("Machine: {}".format(platform.machine()))
        self.python_machine_label.setStyleSheet("font-size: 13px;")
        self.python_machine_label.setFixedHeight(20)
        

        self.item_count += 1
        self.add_item("#3F2B96", "#A8C0FF", [self.python_label, self.python_version_label, self.python_architecture_label, self.python_machine_label], self.item_count-1, icon=os.path.join(CURRENT_DIR, "icons/python.svg"))


        # system info
        self.system_label = QLabel("System:")
        self.system_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.system_label.setFixedHeight(30)

        self.system_version_label = QLabel("OS: {}".format(platform.platform()))
        self.system_version_label.setStyleSheet("font-size: 13px;")
        self.system_version_label.setFixedHeight(20)

        self.system_machine_label = QLabel("Machine: {}".format(platform.machine()))
        self.system_machine_label.setStyleSheet("font-size: 13px;")
        self.system_machine_label.setFixedHeight(20)

        self.system_release_label = QLabel("Release: {}".format(platform.release()))
        self.system_release_label.setStyleSheet("font-size: 13px;")
        self.system_release_label.setFixedHeight(20)

        self.system_version_info_label = QLabel("Version info: {}".format(platform.version()))
        self.system_version_info_label.setStyleSheet("font-size: 13px;")
        self.system_version_info_label.setFixedHeight(20)

        self.item_count += 1
        self.add_item("#d53768", "#daa353", [self.system_label, self.system_version_label, self.system_release_label, self.system_machine_label, self.system_version_info_label], self.item_count-1, icon=os.path.join(CURRENT_DIR, "icons/computer.svg"))


        # user info
        self.user_label = QLabel("User:")
        self.user_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.user_label.setFixedHeight(30)

        self.user_name_label = QLabel("Name: {}".format(getpass.getuser()))
        self.user_name_label.setStyleSheet("font-size: 13px;")
        self.user_name_label.setFixedHeight(20)

        self.user_home_label = QLabel("Home: {}".format(os.path.expanduser('~')))
        self.user_home_label.setStyleSheet("font-size: 13px;")
        self.user_home_label.setFixedHeight(20)

        self.user_shell_label = QLabel("Shell: {}".format(os.getenv('SHELL')))
        self.user_shell_label.setStyleSheet("font-size: 13px;")
        self.user_shell_label.setFixedHeight(20) 

        self.item_count += 1
        self.add_item("#fbfc9b", "#c87c06", [self.user_label, self.user_name_label, self.user_home_label, self.user_shell_label], self.item_count-1, icon=os.path.join(CURRENT_DIR, "icons/system-users.svg"))

        # set a timer to update values every second
        self.timer = QTimer()
        self.timer.setInterval(settings["sysinfo"]["interval"] * 1000)
        self.timer.timeout.connect(self.updateValues)
        self.timer.start()

        self.show()

    def updateValues(self):
        self.cores_label.setText("Cores: {}".format(psutil.cpu_count(logical=True)))
        self.logical_label.setText("Logical: {}".format(psutil.cpu_count(logical=False)))
        self.usage_label.setText("Usage: {}%".format(psutil.cpu_percent()))
        self.total_label.setText("Total: {}GB".format(round(psutil.virtual_memory().total / 1024 / 1024 / 1024, 2)))
        self.available_label.setText("Available: {}GB".format(round(psutil.virtual_memory().available / 1024 / 1024 / 1024, 2)))
        self.used_label.setText("Used: {}GB ({}%)".format(round(psutil.virtual_memory().used / 1024 / 1024 / 1024, 2), psutil.virtual_memory().percent))
        for i in range(self.disk_list.rowCount()):
            self.disk_list.item(i, 3).setText("{}GB".format(round(psutil.disk_usage(self.disk_list.item(i, 1).text()).total / 1024 / 1024 / 1024, 2)))
            self.disk_list.item(i, 4).setText("{}GB".format(round(psutil.disk_usage(self.disk_list.item(i, 1).text()).free / 1024 / 1024 / 1024, 2)))
            self.disk_list.item(i, 5).setText("{}GB ({}%)".format(round(psutil.disk_usage(self.disk_list.item(i, 1).text()).used / 1024 / 1024 / 1024, 2), psutil.disk_usage(self.disk_list.item(i, 1).text()).percent))

        for i in range(self.network_list.rowCount()):
            self.network_list.item(i, 1).setText("{}".format(round(psutil.net_io_counters(pernic=True)[self.network_list.item(i, 0).text()].bytes_sent, 2)))
            self.network_list.item(i, 2).setText("{}".format(round(psutil.net_io_counters(pernic=True)[self.network_list.item(i, 0).text()].bytes_recv, 2)))
            self.network_list.item(i, 3).setText(str(psutil.net_io_counters(pernic=True)[self.network_list.item(i, 0).text()].packets_sent))
            self.network_list.item(i, 4).setText(str(psutil.net_io_counters(pernic=True)[self.network_list.item(i, 0).text()].packets_recv))

        if ENABLE_BATT:
            try:
                self.battery_time_label.setText("Time left: {}s".format(psutil.sensors_battery().secsleft))
                self.battery_percent_label.setText("Percent: {}%".format(psutil.sensors_battery().percent))
                self.battery_power_label.setText("Power: {}".format(psutil.sensors_battery().power_plugged))
            except Exception as e:
                print("Can't get battery info: {}, maybe you are not using a laptop".format(e))
            

    def add_item(self, color1: str, color2: str, items: list, index: int, max_height: int = 200, min_height: int = 0, icon: str = None):
        self.item_widgets.insert(index, QFrame())
        self.item_widgets[index].setFrameShape(QFrame.Shape.Panel)
        self.layout.addWidget(self.item_widgets[index])

        self.item_widgets[index].setMaximumHeight(max_height)
        self.item_widgets[index].setMinimumHeight(min_height)

        layout = QHBoxLayout()
        layout.setContentsMargins(4,4,4,4)
        self.item_widgets[index].setLayout(layout)

        color_box = QFrame()
        color_box.setFixedWidth(100)
        color_box.setStyleSheet(f"background-color: qlineargradient( x1:0 y1:0, x2:1 y2:0, stop:0 {color1}, stop:1 {color2}); border-radius: 4px")
        layout.addWidget(color_box)

        infolay = QVBoxLayout()
        layout.addLayout(infolay)

        if icon:
            # add icon on frame
            color_layout = QHBoxLayout()
            color_layout.setContentsMargins(0,0,0,0)
            color_box.setLayout(color_layout)
            icon_label = QLabel()
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setPixmap(QPixmap(icon))
            color_layout.addWidget(icon_label)

        for item in items:
            infolay.addWidget(item)

    def open_settings(self):
        self.settings_window = SettingsWindow()
        self.settings_window.show()


class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")
        self.setWindowIcon(QIcon(os.path.join(CURRENT_DIR, "icons/sysinfo-icon.svg")))

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.update_interval_label = QLabel("Update interval (seconds):")
        self.layout.addWidget(self.update_interval_label, 0, 0)

        self.update_interval_spinbox = QSpinBox()
        self.update_interval_spinbox.setMinimum(1)
        self.update_interval_spinbox.setMaximum(5)
        self.update_interval_spinbox.setValue(settings["sysinfo"]["interval"])
        self.update_interval_spinbox.valueChanged.connect(self.update_interval_changed)
        self.layout.addWidget(self.update_interval_spinbox, 0, 1)

    def update_interval_changed(self):
        settings["sysinfo"]["interval"] = self.update_interval_spinbox.value()
        win.timer.setInterval(settings["sysinfo"]["interval"] * 1000)
        save_settings()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Kevinbot System Information")
    win = MainWindow()
    sys.exit(app.exec())