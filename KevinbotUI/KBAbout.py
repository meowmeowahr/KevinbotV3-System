from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *


class AboutBox(QWidget):
    def __init__(
            self,
            author="Unknown",
            appname="Unknown",
            version="Unknown",
            icondir=None,
            bigicon=None,
    ):
        super().__init__()
        self.setWindowTitle("About " + appname)
        self.setWindowIcon(QIcon(icondir))
        self.setObjectName("main")

        self.layout = QVBoxLayout()

        self.icon_layout = QHBoxLayout()
        self.icon_layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addLayout(self.icon_layout)

        self.app_icon = QLabel()
        self.app_icon.setObjectName("app_icon")
        self.app_icon.setPixmap(QPixmap(bigicon))
        self.app_icon.setAlignment(Qt.AlignCenter)
        self.app_icon.setFixedSize(192, 192)
        self.icon_layout.addWidget(self.app_icon)

        self.app_name = QLabel(appname)
        self.app_name.setObjectName("app_name")
        self.app_name.setAlignment(Qt.AlignCenter)
        self.app_name.setStyleSheet("font-size: 22px; font-weight: bold")
        self.layout.addWidget(self.app_name)

        self.app_version = QLabel("Version " + version)
        self.app_version.setObjectName("app_version")
        self.app_version.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.app_version)

        self.app_author = QLabel("Author: " + author)
        self.app_author.setObjectName("app_author")
        self.app_author.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.app_author)

        self.setLayout(self.layout)
