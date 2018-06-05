import bpy
import os

from ..pywowlib.m2_file import M2File
from .m2_scene import BlenderM2Scene

from ..ui import get_addon_prefs
from ..utils import load_game_data


def import_m2(version, file, load_textures):  # TODO: implement multiversioning

    # get global variables
    addon_preferences = get_addon_prefs()

    if type(file) is str:
        m2_file = M2File(version, filepath=file)
        m2 = m2_file.root
        m2.filepath = file  # TODO: HACK

        if load_textures:

            game_data = load_game_data()

            print("\n\n### Extracting textures ###")
            textures = [m2_texture.filename.value for m2_texture in m2.textures if not m2_texture.type]
            game_data.extract_textures_as_png(addon_preferences.cache_dir_path, textures)

        print("\n\n### Importing M2 model ###")

        bl_m2 = BlenderM2Scene(m2_file, addon_preferences)

        bl_m2.load_materials(addon_preferences.cache_dir_path)
        bl_m2.load_armature()
        bl_m2.load_animations()
        bl_m2.load_geosets()
        bl_m2.load_texture_transforms()
        bl_m2.load_collision()
        bl_m2.load_attachments()
        bl_m2.load_lights()
        bl_m2.load_events()

    else:
        pass

