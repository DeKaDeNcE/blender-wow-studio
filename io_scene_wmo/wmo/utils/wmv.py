from typing import Union

from ...ui import get_addon_prefs


def wmv_get_last_wmo() -> Union[None, str]:
    """Get the path of last WMO model from WoWModelViewer or similar log."""

    addon_preferences = get_addon_prefs()
    if addon_preferences.wmv_path:

        lines = open(addon_preferences.wmv_path).readlines()

        for line in reversed(lines):
            if 'Loading WMO' in line:
                return line[22:].rstrip("\n")

def wmv_get_last_m2() -> Union[None, str]:
    """Get the path of last M2 model from WoWModelViewer or similar log."""

    addon_preferences = get_addon_prefs()
    if addon_preferences.wmv_path:

        lines = open(addon_preferences.wmv_path).readlines()

        for line in reversed(lines):
            if 'Loading model:' in line:
                return line[25:].split(",", 1)[0].rstrip("\n")


def wmv_get_last_texture() -> Union[None, str]:
    """Get the path of last texture from WoWModelViewer or similar log."""

    addon_preferences = get_addon_prefs()
    if addon_preferences.wmv_path:

        lines = open(addon_preferences.wmv_path).readlines()

        for line in reversed(lines):
            if 'Loading texture' in line:
                return line[27:].rstrip("\n")