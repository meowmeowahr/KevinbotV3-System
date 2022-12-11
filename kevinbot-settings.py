from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from KevinbotUI import AboutBox
from settings_panels import ThemePanel, SysInfoPanel
import os
import sys
import socket

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

HOME_WIDGET_INDEX   = 0
THEME_PANEL_INDEX   = 1
SYSINFO_PANEL_INDEX = 2


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kevinbot Settings")
        self.setWindowIcon(QIcon.fromTheme("utilities-tweak-tool"))
        self.setObjectName("Kevinbot3_Settings_Window")

        self.main_widget = QStackedWidget()
        self.main_widget.setObjectName("Kevinbot3_Settings_StackedWidget")
        self.setCentralWidget(self.main_widget)

        self.home_widget = QWidget()
        self.home_widget.setObjectName("Kevinbot3_Settings_Widget")
        self.main_widget.insertWidget(HOME_WIDGET_INDEX, self.home_widget)

        self.home_layout = QVBoxLayout()
        self.home_widget.setLayout(self.home_layout)

        self.home_top_layout = QHBoxLayout()
        self.home_layout.addLayout(self.home_top_layout)

        self.kevinbot_logo = QLabel()
        self.kevinbot_logo.setObjectName("Kevinbot3_Settings_Kevinbot_Logo")
        self.kevinbot_logo.setPixmap(QPixmap(os.path.join(CURRENT_DIR, "icons/kevinbot.svg")))
        self.kevinbot_logo.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.kevinbot_logo.setScaledContents(True)
        self.kevinbot_logo.setFixedSize(QSize(96, 96))
        self.home_top_layout.addWidget(self.kevinbot_logo)

        self.home_top_layout.addStretch()

        self.home_top_name_layout = QVBoxLayout()
        self.home_top_layout.addLayout(self.home_top_name_layout)

        self.home_top_layout.addStretch()

        self.home_top_name_layout.addStretch()

        self.name = QLabel("Kevinbot v3")
        self.name.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.home_top_name_layout.addWidget(self.name)

        self.hostname = QLabel(socket.gethostname())
        self.home_top_name_layout.addWidget(self.hostname)

        self.home_top_name_layout.addStretch()

        self.settings_grid_layout = QGridLayout()
        self.home_layout.addLayout(self.settings_grid_layout)

        self.theme_button = QToolButton()
        self.theme_button.setObjectName("Kevinbot3_Settings_Panel_Button")
        self.theme_button.setText(ThemePanel.name)
        self.theme_button.setIcon(QIcon(os.path.join(CURRENT_DIR, "icons/theme.svg")))
        self.theme_button.setIconSize(QSize(64, 64))
        self.theme_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.theme_button.setFixedSize(QSize(96, 96))
        self.settings_grid_layout.addWidget(self.theme_button, 0, 0)
        
        self.sysinfo_button = QToolButton()
        self.sysinfo_button.setObjectName("Kevinbot3_Settings_Panel_Button")
        self.sysinfo_button.setText(SysInfoPanel.name)
        self.sysinfo_button.setIcon(QIcon(os.path.join(CURRENT_DIR, "icons/cpu.svg")))
        self.sysinfo_button.setIconSize(QSize(64, 64))
        self.sysinfo_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.sysinfo_button.setFixedSize(QSize(96, 96))
        self.settings_grid_layout.addWidget(self.sysinfo_button, 0, 1)

        self.theme_panel = ThemePanel(self.main_widget, HOME_WIDGET_INDEX)
        self.main_widget.insertWidget(THEME_PANEL_INDEX, self.theme_panel)
        self.theme_button.clicked.connect(lambda: self.main_widget.setCurrentIndex(THEME_PANEL_INDEX))
        
        self.sysinfo_panel = SysInfoPanel(self.main_widget, HOME_WIDGET_INDEX)
        self.main_widget.insertWidget(SYSINFO_PANEL_INDEX, self.sysinfo_panel)
        self.sysinfo_button.clicked.connect(lambda: self.main_widget.setCurrentIndex(SYSINFO_PANEL_INDEX))

        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Kevinbot v3 Settings")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())        