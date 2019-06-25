import bpy

from ..m2.ui import register_m2_panels, unregister_m2_panels
from ..wmo.ui import register_wmo_panels, unregister_wmo_panels
from .handlers import register_handlers, unregister_handlers
from .panels import register_panels, unregister_panels


def get_addon_prefs():
    return bpy.context.preferences.addons[__package__[:-3]].preferences


def register_ui():
    register_handlers()
    register_m2_panels()
    register_wmo_panels()
    register_panels()


def unregister_ui():
    unregister_handlers()
    unregister_m2_panels()
    unregister_wmo_panels()
    unregister_panels()