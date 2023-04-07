from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from settings_panels import ThemePanel, SysInfoPanel
import os
import sys
import qtawesome as qta
import theme_control

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

HOME_WIDGET_INDEX = 0
THEME_PANEL_INDEX = 1
SYSINFO_PANEL_INDEX = 2


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
        self.theme_button.setFixedWidth(128)
        self.theme_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.theme_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(THEME_PANEL_INDEX))
        self.item_layout.addWidget(self.theme_button)

        self.sysinfo_button = QToolButton()
        self.sysinfo_button.setObjectName("Kevinbot3_Settings_Panel_Button")
        self.sysinfo_button.setText(" " + SysInfoPanel.name)
        self.sysinfo_button.setIconSize(QSize(24, 24))
        self.sysinfo_button.setFixedWidth(128)
        self.sysinfo_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.sysinfo_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(SYSINFO_PANEL_INDEX))
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
        self.stacked_widget.insertWidget(THEME_PANEL_INDEX, self.theme_panel)
        
        self.sysinfo_panel = SysInfoPanel(self)
        self.stacked_widget.insertWidget(SYSINFO_PANEL_INDEX, self.sysinfo_panel)

        self.update_icons()

        self.show()

    def update_icons(self):
        self.ensurePolished()
        if theme_control.get_dark():
            self.fg_color = Qt.GlobalColor.white
        else:
            self.fg_color = Qt.GlobalColor.black

        self.theme_button.setIcon(QIcon(qta.icon("fa5s.paint-roller", color=self.fg_color)))
        self.sysinfo_button.setIcon(QIcon(qta.icon("fa5s.microchip", color=self.fg_color)))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Kevinbot v3 Settings")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
