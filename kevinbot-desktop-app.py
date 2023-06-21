import sys
import os
import json
import functools

from PyQt5.QtWidgets import (QApplication, QMainWindow, QDialog, QWidget,
                             QVBoxLayout, QLabel, QScrollArea)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QMoveEvent

from KevinbotUI import KBTheme
import theme_control
import desktop_base_widget

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
SETTINGS_PATH = os.path.join(CURRENT_DIR, 'widgets.json')

settings = json.load(open(SETTINGS_PATH, 'r'))

WIDGET_TYPES = {
    "base": desktop_base_widget.BaseWidget,
    "clock": desktop_base_widget.ClockWidget,
    "clock24": desktop_base_widget.Clock24Widget,
    "enable": desktop_base_widget.EnaWidget}


def save_json():
    with open(SETTINGS_PATH, 'w') as f:
        json.dump(settings, f, indent=4)


def reload_settings():
    settings["order"] = []

    for n in range(dock.main_layout.count()):
        settings["order"].append(dock.main_layout.itemAt(n).widget().data)
    save_json()


class DockWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setWindowOpacity(0.8)
        self.setFixedWidth(280)

        self.reposition_timer = QTimer()

        self.screen = app.primaryScreen()
        self.screen.geometryChanged.connect(lambda: self.reposition_timer.
                                            singleShot(1200, self.reposition))

        self.widget = QWidget()
        self.setCentralWidget(self.widget)

        self.root_layout = QVBoxLayout()
        self.widget.setLayout(self.root_layout)

        self.add_button = desktop_base_widget.AddButton()
        self.add_button.setText("Add a Widget")
        self.add_button.clicked.connect(self.add_widget)
        self.root_layout.addWidget(self.add_button)

        self.root_layout.addStretch()

        self.main_layout = QVBoxLayout()
        self.root_layout.addLayout(self.main_layout)

        self.extras_layout = QVBoxLayout()
        self.root_layout.addLayout(self.extras_layout)

        self.root_layout.addStretch()

        for item in settings["order"]:
            widget = WIDGET_TYPES[item["type"]](data=item)
            widget.up_button.clicked.connect(
                functools.partial(self.move_widget_up, widget))
            widget.down_button.clicked.connect(
                functools.partial(self.move_widget_down, widget))
            widget.remove_button.clicked.connect(
                functools.partial(self.widget_del, widget))
            self.main_layout.addWidget(widget)

        self.empty_widget = desktop_base_widget.EmptyWidget()
        self.empty_widget.setVisible(self.main_layout.count() == 0)
        self.extras_layout.addWidget(self.empty_widget)

        self.reposition()
        self.show()

    def move_widget_up(self, w):
        index = self.main_layout.indexOf(w)
        self.main_layout.removeWidget(w)

        if index == 0:
            self.main_layout.insertWidget(self.main_layout.count(), w)
        else:
            self.main_layout.insertWidget(index - 1, w)

        reload_settings()

    def move_widget_down(self, w):
        index = self.main_layout.indexOf(w)
        self.main_layout.removeWidget(w)

        if index == self.main_layout.count():
            self.main_layout.insertWidget(0, w)
        else:
            self.main_layout.insertWidget(index + 1, w)

        reload_settings()

    def widget_del(self, w):
        if self.main_layout.count() == 1:
            self.empty_widget.setVisible(True)

        self.main_layout.removeWidget(w)
        w.deleteLater()
        reload_settings()

    def add_widget(self):
        add_win = AddWindow(self)
        add_win.exec()

    def moveEvent(self, a0: QMoveEvent) -> None:
        self.reposition()
        a0.accept()

    def reposition(self):
        self.setFixedHeight(self.screen.availableGeometry().height())
        self.move(self.screen.availableGeometry().width() - self.width(), 0)


class AddWindow(QDialog):
    def __init__(self, parent=None):
        super(AddWindow, self).__init__(parent)
        self.setWindowTitle("Add Widget")
        self.setModal(True)

        self.ensurePolished()
        if theme_control.get_dark():
            self.fg_color = Qt.GlobalColor.white
            KBTheme.load(self, mode=KBTheme.Modes.Dark)
        else:
            self.fg_color = Qt.GlobalColor.black
            KBTheme.load(self, mode=KBTheme.Modes.Light)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.title = QLabel("Select a Widget")
        self.layout.addWidget(self.title)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.layout.addWidget(self.scroll)

        self.scroll_widget = QWidget()
        self.scroll.setWidget(self.scroll_widget)

        self.scroll_layout = QVBoxLayout()
        self.scroll_widget.setLayout(self.scroll_layout)

        self.add_base_widget = desktop_base_widget.BaseWidget(add=True)
        self.add_base_widget.add_button.clicked.connect(lambda: self.add_widget(desktop_base_widget.BaseWidget()))
        self.scroll_layout.addWidget(self.add_base_widget)

        self.add_clock_widget = desktop_base_widget.ClockWidget(add=True)
        self.add_clock_widget.add_button.clicked.connect(lambda: self.add_widget(desktop_base_widget.ClockWidget()))
        self.scroll_layout.addWidget(self.add_clock_widget)

        self.add_clock24_widget = desktop_base_widget.Clock24Widget(add=True)
        self.add_clock24_widget.add_button.clicked.connect(lambda: self.add_widget(desktop_base_widget.Clock24Widget()))
        self.scroll_layout.addWidget(self.add_clock24_widget)

        self.add_enable_status_widget = desktop_base_widget.EnaWidget(add=True)
        self.add_enable_status_widget.add_button.clicked.connect(lambda:
                                                                 self.add_widget(desktop_base_widget.EnaWidget()))
        self.scroll_layout.addWidget(self.add_enable_status_widget)

        self.show()

    def add_widget(self, widget: QWidget):
        widget.up_button.clicked.connect(
            functools.partial(dock.move_widget_up, widget))
        widget.down_button.clicked.connect(
            functools.partial(dock.move_widget_down, widget))
        widget.remove_button.clicked.connect(
            functools.partial(dock.widget_del, widget))
        dock.main_layout.addWidget(widget)
        dock.empty_widget.setVisible(False)
        reload_settings()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dock = DockWindow()
    sys.exit(app.exec())
