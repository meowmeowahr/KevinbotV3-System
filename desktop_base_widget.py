from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QVBoxLayout, QPushButton,
                             QLabel)
from PyQt5.QtCore import Qt, QSize
import qtawesome as qta

from KevinbotUI import KBTheme
import theme_control

import uuid


class BaseWidget(QFrame):
    def __init__(self, add=False):
        super().__init__()
        self.data = {"type": "base", "uuid": str(uuid.uuid4())}

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

    def setTitle(self, title: str):
        self.title.setText(title)

    def setData(self, data: any):
        self.data = data


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

    def setTitle(self, title: str):
        self.label.setText(title)

    def setData(self, data: any):
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
