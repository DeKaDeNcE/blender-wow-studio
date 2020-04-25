import os

from ..utils.misc import load_game_data
from .m2_scene import BlenderM2Scene
from ..pywowlib.m2_file import M2File, M2Versions
from ..ui import get_addon_prefs


def import_m2(version, filepath, is_local_file=False):

    # get global variables
    addon_preferences = get_addon_prefs()

    try:
        game_data = load_game_data()

    except UserWarning:
        game_data = None

    m2_file = M2File(version, filepath=filepath)
    m2 = m2_file.root
    m2.filepath = filepath  # TODO: HACK

    extract_dir = os.path.dirname(filepath) if is_local_file else addon_preferences.cache_dir_path

    if extract_dir and game_data:

        # extract and read skel
        skel_fdid = m2_file.find_main_skel()

        while skel_fdid:
            skel_path = game_data.extract_file(extract_dir, skel_fdid, 'skel')
            skel_fdid = m2_file.read_skel(skel_path)

        m2_file.process_skels()

        dependencies = m2_file.find_model_dependencies()

        m2_file.texture_path_map = game_data.extract_textures_as_png(extract_dir, dependencies.textures)

        game_data.extract_files(extract_dir, dependencies.anims, 'anim', True)
        skin_filepaths = game_data.extract_files(extract_dir, dependencies.skins, 'skin')

        if version >= M2Versions.WOD:
            game_data.extract_files(extract_dir, dependencies.bones, 'bone', True)
            game_data.extract_files(extract_dir, dependencies.lod_skins, 'skin', True)

    m2_file.read_additional_files(fallback_dir=os.path.dirname(skin_filepaths[0]))
    m2_file.root.assign_bone_names()

    print("\n\n### Importing M2 model ###")

    bl_m2 = BlenderM2Scene(m2_file, addon_preferences)

    bl_m2.load_armature()
    bl_m2.load_animations()
    #bl_m2.load_colors()
    bl_m2.load_transparency()
    bl_m2.load_materials(addon_preferences.cache_dir_path, os.path.dirname(filepath))
    bl_m2.load_geosets()
    bl_m2.load_texture_transforms()
    bl_m2.load_collision()
    bl_m2.load_attachments()
    bl_m2.load_lights()
    bl_m2.load_events()
    #bl_m2.load_cameras()


