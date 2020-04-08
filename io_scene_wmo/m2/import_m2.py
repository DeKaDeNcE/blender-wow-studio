import os

from ..utils.misc import load_game_data
from .m2_scene import BlenderM2Scene
from ..pywowlib.m2_file import M2File
from ..ui import get_addon_prefs


def import_m2(version, filepath):  # TODO: implement multiversioning

    # get global variables
    addon_preferences = get_addon_prefs()

    try:
        game_data = load_game_data()

    except UserWarning:
        game_data = None

    m2_file = M2File(version, filepath=filepath)
    m2 = m2_file.root
    m2.filepath = filepath  # TODO: HACK

    if addon_preferences.cache_dir_path and game_data:

        if version
        textures = [m2_texture.filename.value for m2_texture in m2.textures
                    if not m2_texture.type and m2_texture.filename.value]
        game_data.extract_textures_as_png(addon_preferences.cache_dir_path, textures)

    print("\n\n### Importing M2 model ###")

    bl_m2 = BlenderM2Scene(m2_file, addon_preferences)

    bl_m2.load_armature()
    bl_m2.load_animations()
    bl_m2.load_colors()
    bl_m2.load_transparency()
    bl_m2.load_materials(addon_preferences.cache_dir_path, os.path.dirname(filepath))
    bl_m2.load_geosets()
    bl_m2.load_texture_transforms()
    bl_m2.load_collision()
    bl_m2.load_attachments()
    bl_m2.load_lights()
    bl_m2.load_events()
    bl_m2.load_cameras()


