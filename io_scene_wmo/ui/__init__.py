import bpy

from ..m2.ui import register_m2_panels, unregister_m2_panels
from ..m2.ui.panels.creature_editor import register_creature_editor, unregister_creature_editor
from ..m2.ui.panels.animation_editor import register_animation_editor, unregister_animation_editor
from ..wmo.ui.panels import register as register_wmo_ui
from ..wmo.ui.panels import unregister as unregister_wmo_ui
from .handlers import register_handlers, unregister_handlers
from .panels import register_panels, unregister_panels


def get_addon_prefs():
    return bpy.context.user_preferences.addons[__package__[:-3]].preferences


def register_ui():
    register_handlers()
    register_m2_panels()
    register_creature_editor()
    register_animation_editor()
    register_wmo_ui()
    register_panels()


def unregister_ui():
    unregister_handlers()
    unregister_m2_panels()
    unregister_creature_editor()
    unregister_animation_editor()
    unregister_wmo_ui()
    unregister_panels()