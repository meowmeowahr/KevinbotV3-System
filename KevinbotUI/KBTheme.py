import qdarktheme
import enum


class Themes(enum.Enum):
    KBDef = 0


class Modes(enum.Enum):
    Dark = 0
    Light = 1


def load(widget, theme=Themes.KBDef, mode=Modes.Dark):
    if theme == Themes.KBDef:
        if mode == Modes.Dark:
            widget.setStyleSheet(qdarktheme.load_stylesheet("dark"))
        elif mode == Modes.Light:
            widget.setStyleSheet(qdarktheme.load_stylesheet("light"))
