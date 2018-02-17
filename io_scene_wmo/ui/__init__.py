import bpy
import os
import bpy.utils.previews

from ..m2.ui.panels import register as register_m2_ui
from ..m2.ui.panels import unregister as unregister_m2_ui
from ..wmo.ui.panels import register as register_wmo_ui
from ..wmo.ui.panels import unregister as unregister_wmo_ui
from .handlers import register_handlers, unregister_handlers


def get_addon_prefs():
    return bpy.context.user_preferences.addons[__package__[:-3]].preferences


def render_gamedata_toggle(self, context):
    game_data_loaded = hasattr(bpy, "wow_game_data") and bpy.wow_game_data.files

    global ui_icons
    
    layout = self.layout
    row = layout.row(align=True)
    icon = ui_icons['RELOAD'] if game_data_loaded else 'COLOR_RED'
    text = "Reload WoW" if game_data_loaded else "Connect WoW"
    row.operator("scene.reload_wow_filesystem", text=text, icon_value=icon)


menu_import_wmo = lambda self, ctx: self.layout.operator("import_mesh.wmo", text="WoW WMO (.wmo)")
menu_export_wmo = lambda self, ctx: self.layout.operator("export_mesh.wmo", text="WoW WMO (.wmo)")
menu_import_m2 = lambda self, ctx: self.layout.operator("import_mesh.m2", text="WoW M2 (.m2)")

icon_file_dict = bpy.utils.previews.new()
ui_icons = {}

def register_ui():
    global ui_icons
    
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")

    for file in os.listdir(icons_dir):
        icon_file_dict.load(os.path.splitext(file)[0].upper(), os.path.join(icons_dir, file), 'IMAGE')

    for name, icon_file in icon_file_dict.items():
        ui_icons[name] = icon_file.icon_id

    register_handlers()
    register_m2_ui()
    register_wmo_ui()
    bpy.types.INFO_HT_header.append(render_gamedata_toggle)
    bpy.types.INFO_MT_file_import.append(menu_import_wmo)
    bpy.types.INFO_MT_file_import.append(menu_import_m2)
    bpy.types.INFO_MT_file_export.append(menu_export_wmo)


def unregister_ui():
    unregister_handlers()
    unregister_m2_ui()
    unregister_wmo_ui()
    bpy.types.INFO_MT_file_import.remove(menu_import_wmo)
    bpy.types.INFO_MT_file_import.remove(menu_import_m2)
    bpy.types.INFO_MT_file_export.remove(menu_export_wmo)
    bpy.types.INFO_HT_header.remove(render_gamedata_toggle)
    bpy.utils.previews.remove(icon_file_dict)