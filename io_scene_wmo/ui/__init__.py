import bpy

from ..m2.ui.panels import register as register_m2_ui
from ..m2.ui.panels import unregister as unregister_m2_ui
from ..wmo.ui.panels import register as register_wmo_ui
from ..wmo.ui.panels import unregister as unregister_wmo_ui


def get_addon_prefs():
    return bpy.context.user_preferences.addons[__package__[:-3]].preferences


def render_gamedata_toggle(self, context):
    game_data_loaded = hasattr(bpy, "wow_game_data") and bpy.wow_game_data.files

    layout = self.layout
    row = layout.row(align=True)
    icon = 'COLOR_GREEN' if game_data_loaded else 'COLOR_RED'
    text = "Disconnect WoW" if game_data_loaded else "Connect WoW"
    row.operator("scene.load_wow_filesystem", text=text, icon=icon)


menu_import_wmo = lambda self, ctx: self.layout.operator("import_mesh.wmo", text="WoW WMO (.wmo)")
menu_export_wmo = lambda self, ctx: self.layout.operator("export_mesh.wmo", text="WoW WMO (.wmo)")
menu_import_m2 = lambda self, ctx: self.layout.operator("import_mesh.m2", text="WoW M2 (.m2)")


def register_ui():
    register_m2_ui()
    register_wmo_ui()
    bpy.types.INFO_HT_header.append(render_gamedata_toggle)
    bpy.types.INFO_MT_file_import.append(menu_import_wmo)
    bpy.types.INFO_MT_file_import.append(menu_import_m2)
    bpy.types.INFO_MT_file_export.append(menu_export_wmo)


def unregister_ui():
    unregister_m2_ui()
    unregister_wmo_ui()
    bpy.types.INFO_MT_file_import.remove(menu_import_wmo)
    bpy.types.INFO_MT_file_import.remove(menu_import_m2)
    bpy.types.INFO_MT_file_export.remove(menu_export_wmo)
    bpy.types.INFO_HT_header.remove(render_gamedata_toggle)