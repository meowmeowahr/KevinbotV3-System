from qtpy.QtWidgets import QApplication

import qdarktheme
import enum
import qtawesome as qta


class Themes(enum.Enum):
    KBDef = 0


class Modes(enum.Enum):
    Dark = 0
    Light = 1


def load(widget, app: QApplication | None = None, theme=Themes.KBDef, mode=Modes.Dark):
    if theme == Themes.KBDef:
        if mode == Modes.Dark:
            widget.setStyleSheet(qdarktheme.load_stylesheet("dark"))
            if app:
                qta.dark(app)
        elif mode == Modes.Light:
            widget.setStyleSheet(qdarktheme.load_stylesheet("light"))
            if app:
                qta.light(app)
