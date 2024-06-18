from qtpy.QtWidgets import *
from qtpy.QtCore import *
from qtpy.QtGui import *
from KevinbotUI import KBTheme
from settings_panels import ThemePanel, SysInfoPanel, CommsPanel, ServicesPanel, settings, save_json
import os
import sys
import qtawesome as qta
import theme_control

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

HOME_WIDGET_INDEX = 0
THEME_PANEL_INDEX = 1
SYSINFO_PANEL_INDEX = 2
COMMS_PANEL_INDEX = 3
SERVICES_PANEL_INDEX = 4


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kevinbot Settings")
        self.setWindowIcon(QIcon.fromTheme("utilities-tweak-tool"))
        self.setObjectName("Kevinbot3_Settings_Window")

        self.widget = QWidget()
        self.setCentralWidget(self.widget)

        self.main_layout = QHBoxLayout()
        self.widget.setLayout(self.main_layout)

        self.scroll = QScrollArea()

        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)

        self.scroll_widget = QWidget()
        self.scroll.setWidget(self.scroll_widget)

        self.item_layout = QVBoxLayout()

        # items
        
        self.theme_button = QToolButton()
        self.theme_button.setObjectName("Kevinbot3_Settings_Panel_Button")
        self.theme_button.setText(" " + ThemePanel.name)
        self.theme_button.setIconSize(QSize(24, 24))
        self.theme_button.setFixedWidth(180)
        self.theme_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.theme_button.clicked.connect(lambda: self.set_page(THEME_PANEL_INDEX))
        self.item_layout.addWidget(self.theme_button)

        self.comms_button = QToolButton()
        self.comms_button.setObjectName("Kevinbot3_Settings_Panel_Button")
        self.comms_button.setText(" " + CommsPanel.name)
        self.comms_button.setIconSize(QSize(24, 24))
        self.comms_button.setFixedWidth(180)
        self.comms_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.comms_button.clicked.connect(lambda: self.set_page(COMMS_PANEL_INDEX))
        self.item_layout.addWidget(self.comms_button)

        self.services_button = QToolButton()
        self.services_button.setObjectName("Kevinbot3_Settings_Panel_Button")
        self.services_button.setText(" " + ServicesPanel.name)
        self.services_button.setIconSize(QSize(24, 24))
        self.services_button.setFixedWidth(180)
        self.services_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.services_button.clicked.connect(lambda: self.set_page(SERVICES_PANEL_INDEX))
        self.item_layout.addWidget(self.services_button)

        self.sysinfo_button = QToolButton()
        self.sysinfo_button.setObjectName("Kevinbot3_Settings_Panel_Button")
        self.sysinfo_button.setText(" " + SysInfoPanel.name)
        self.sysinfo_button.setIconSize(QSize(24, 24))
        self.sysinfo_button.setFixedWidth(180)
        self.sysinfo_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.sysinfo_button.clicked.connect(lambda: self.set_page(SYSINFO_PANEL_INDEX))
        self.item_layout.addWidget(self.sysinfo_button)

        self.scroll_widget.setLayout(self.item_layout)

        self.scroll.setFixedWidth(QSize(self.scroll.sizeHint()).width())

        self.main_layout.addWidget(self.scroll)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("Kevinbot3_Settings_StackedWidget")
        self.main_layout.addWidget(self.stacked_widget)

        self.home_widget = QWidget()
        self.home_widget.setObjectName("Kevinbot3_Settings_Widget")
        self.stacked_widget.insertWidget(HOME_WIDGET_INDEX, self.home_widget)

        self.home_layout = QVBoxLayout()
        self.home_widget.setLayout(self.home_layout)

        self.home_top_layout = QHBoxLayout()
        self.home_layout.addLayout(self.home_top_layout)

        self.settings_grid_layout = QGridLayout()
        self.home_layout.addLayout(self.settings_grid_layout)

        self.theme_panel = ThemePanel(self)
        self.theme_panel.theme_select_switch.stateChanged.connect(self.update_icons)
        self.stacked_widget.insertWidget(THEME_PANEL_INDEX, self.theme_panel)
        
        self.sysinfo_panel = SysInfoPanel(self)
        self.stacked_widget.insertWidget(SYSINFO_PANEL_INDEX, self.sysinfo_panel)

        self.comms_panel = CommsPanel(self)
        self.stacked_widget.insertWidget(COMMS_PANEL_INDEX, self.comms_panel)

        self.services_panel = ServicesPanel(self)
        self.stacked_widget.insertWidget(SERVICES_PANEL_INDEX, self.services_panel)

        self.update_icons()
        self.stacked_widget.setCurrentIndex(settings["settings"]["page"])
        self.show()

    def update_icons(self):
        self.ensurePolished()
        if theme_control.get_dark():
            KBTheme.load(self, app, mode=KBTheme.Modes.Dark)
        else:
            KBTheme.load(self, app, mode=KBTheme.Modes.Light)
        self.ensurePolished()

        self.theme_button.setIcon(QIcon(qta.icon("fa5s.paint-roller", color=self.palette().buttonText().color().name())))
        self.sysinfo_button.setIcon(QIcon(qta.icon("fa5s.microchip", color=self.palette().buttonText().color().name())))
        self.comms_button.setIcon(QIcon(qta.icon("mdi.transit-connection-variant", color=self.palette().buttonText().color().name())))
        self.services_button.setIcon(QIcon(qta.icon("mdi.cogs", color=self.palette().buttonText().color().name())))

    def set_page(self, page: int):
        self.stacked_widget.setCurrentIndex(page)
        settings["settings"]["page"] = page
        save_json()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Kevinbot v3 Settings")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
