import subprocess

from loguru import logger


def get_current_xfce4_theme():
    try:
        # Get the current theme
        result = subprocess.run(
            ["xfconf-query", "--channel", "xsettings", "--property", "/Net/ThemeName"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"An error occurred: {e}")
        return None


def set_current_xfce4_theme(theme_name):
    try:
        # Set the theme
        subprocess.run(
            [
                "xfconf-query",
                "--channel",
                "xsettings",
                "--property",
                "/Net/ThemeName",
                "--set",
                theme_name,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info(f"Theme set to: {theme_name}")
    except subprocess.CalledProcessError as e:
        logger.error(f"An error occurred: {e}")


def set_libadwaita_theme(theme_preference):
    try:
        if theme_preference not in ["prefer-dark", "default"]:
            raise ValueError(
                "Invalid theme preference. Use 'prefer-dark' or 'default'."
            )

        # Set the libadwaita theme preference
        subprocess.run(
            [
                "gsettings",
                "set",
                "org.gnome.desktop.interface",
                "color-scheme",
                theme_preference,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info(f"Libadwaita theme set to: {theme_preference}")
    except subprocess.CalledProcessError as e:
        logger.error(f"An error occurred: {e}")


def set_xfwm_theme(theme_name):
    try:
        # Set the XFWM theme
        subprocess.run(
            [
                "xfconf-query",
                "--channel",
                "xfwm4",
                "--property",
                "/general/theme",
                "--set",
                theme_name,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info(f"XFWM theme set to: {theme_name}")
    except subprocess.CalledProcessError as e:
        logger.error(f"An error occurred: {e}")


def set_xfce_wallpaper(image_path):
    try:
        # Get all last-image properties using xfconf-query
        result = subprocess.run(
            ["xfconf-query", "--channel", "xfce4-desktop", "--list"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Filter properties with grep
        last_image_properties = [
            line for line in result.stdout.splitlines() if "last-image" in line
        ]

        if not last_image_properties:
            logger.warning("No last-image properties found.")
            return

        # Set the wallpaper for each last-image property
        for prop in last_image_properties:
            subprocess.run(
                [
                    "xfconf-query",
                    "--channel",
                    "xfce4-desktop",
                    "--property",
                    prop,
                    "--set",
                    image_path,
                ],
                check=True,
            )
            logger.info(f"Wallpaper set to: {image_path} for property: {prop}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to set wallpaper: {e}")


def get_dark():
    return get_current_xfce4_theme() == "Arc-Dark"


def set_theme(dark: bool):
    if dark:
        set_current_xfce4_theme("Arc-Dark")
        set_libadwaita_theme("prefer-dark")
        set_xfwm_theme("Arc-Dark")
    else:
        set_current_xfce4_theme("Arc")
        set_libadwaita_theme("default")
        set_xfwm_theme("Arc")
