import bpy

from ..m2.ui.panels import register as register_m2_ui
from ..m2.ui.panels import unregister as unregister_m2_ui
from ..wmo.ui.panels import register as register_wmo_ui
from ..wmo.ui.panels import unregister as unregister_wmo_ui


def render_gamedata_toggle(self, context):
    game_data_loaded = hasattr(bpy, "wow_game_data") and bpy.wow_game_data.files

    layout = self.layout
    row = layout.row(align=True)
    icon = 'COLOR_GREEN' if game_data_loaded else 'COLOR_RED'
    text = "Disconnect WoW" if game_data_loaded else "Connect WoW"
    row.operator("scene.load_wow_filesystem", text=text, icon=icon)


def register_ui():
    register_m2_ui()
    register_wmo_ui()
    bpy.types.INFO_HT_header.append(render_gamedata_toggle)


def unregister_ui():
    unregister_m2_ui()
    unregister_wmo_ui()
    bpy.types.INFO_HT_header.append(render_gamedata_toggle)