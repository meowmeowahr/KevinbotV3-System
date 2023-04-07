import os
import configparser

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

LXSESSION_CONFIG = "/home/kevinbot/.config/lxsession/LXDE-pi/desktop.conf"

lxsession_parser = configparser.ConfigParser()
lxsession_parser.optionxform = str
lxsession_parser.read(LXSESSION_CONFIG)

LIGHT_CONFIG = os.path.join(CURRENT_DIR, "system-configs", "desktop-light.conf")
DARK_CONFIG = os.path.join(CURRENT_DIR, "system-configs", "desktop-dark.conf")


def set_theme(dark: bool):
    if dark:
        lxsession_parser.set("GTK", "sNet/ThemeName", "Arc-Dark")
        lxsession_parser.set("GTK", "sNet/IconThemeName", "Papirus-Dark")
        with open(LXSESSION_CONFIG, 'w') as fp:
            lxsession_parser.write(fp)
    else:
        lxsession_parser.set("GTK", "sNet/ThemeName", "Arc-Lighter")
        lxsession_parser.set("GTK", "sNet/IconThemeName", "Papirus-Light")
        with open(LXSESSION_CONFIG, 'w') as fp:
            lxsession_parser.write(fp)


def get_dark():
    try:
        if lxsession_parser.get("GTK", "sNet/ThemeName") == "Arc-Dark":
            return True
        elif lxsession_parser.get("GTK", "sNet/ThemeName") == "Arc-Lighter":
            return False
        else:
            return -1
    except configparser.NoSectionError:
        return -1
