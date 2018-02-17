import bpy
import bpy.utils.previews
import os

icon_file_dict = None
ui_icons = {}


def register_icon_manager():
    global icon_file_dict

    icon_file_dict = bpy.utils.previews.new()

    global ui_icons

    icons_dir = os.path.join(os.path.dirname(__file__), "icons")

    for file in os.listdir(icons_dir):
        icon_file_dict.load(os.path.splitext(file)[0].upper(), os.path.join(icons_dir, file), 'IMAGE')

    for name, icon_file in icon_file_dict.items():
        ui_icons[name] = icon_file.icon_id


def unregister_icon_manager():
    bpy.utils.previews.remove(icon_file_dict)


def get_ui_icons():
    global ui_icons
    return ui_icons