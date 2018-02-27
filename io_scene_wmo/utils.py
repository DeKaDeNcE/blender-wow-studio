import bpy
import os

from io import BytesIO
from .pywowlib.archives.mpq.wow import WoWFileData
from .pywowlib.wdbx.wdbc import DBFilesClient, DBCFile
from .pywowlib.wdbx.definitions.wotlk import AnimationData


def parse_bitfield(bitfield, last_flag=0x1000):

    flags = set()
    bit = 1
    while bit <= last_flag:
        if bitfield & bit:
            flags.add(str(bit))
        bit <<= 1

    return flags


def construct_bitfield(flag_set):

    bitfiled = 0

    for flag in flag_set:
        bitfiled |= int(flag)

    return bitfiled


def get_material_viewport_image(material):
    """ Get viewport image assigned to a material """
    for i in range(3):
        try:
            img = material.texture_slots[3 - i].texture.image
            return img
        except:
            pass
    return None


def load_game_data():
    if not hasattr(bpy, 'wow_game_data'):
        addon_preferences = bpy.context.user_preferences.addons[__package__].preferences
        bpy.wow_game_data = WoWFileData(addon_preferences.wow_path, addon_preferences.blp_path)

        if not bpy.wow_game_data.files:
            raise ChildProcessError("WoW game data is not loaded. Check settings.")

        bpy.db_files_client = DBFilesClient()

        # list of all DB tables that we need to load
        anim_data_dbc = DBCFile(AnimationData, 'AnimationData')
        anim_data_dbc.read(BytesIO(bpy.wow_game_data.read_file('DBFilesClient\\AnimationData.dbc')))
        bpy.db_files_client.add(anim_data_dbc)

    return bpy.wow_game_data


def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance


def resolve_texture_path(filepath):
    filepath = os.path.splitext(bpy.path.abspath(filepath))[0] + ".blp"
    prefs = bpy.context.user_preferences.addons[__package__].preferences

    # TODO: project folder
    if prefs.use_cache_dir and prefs.cache_dir_path:
        rel_path = os.path.relpath(filepath, start=prefs.cache_dir_path)
        test_path = os.path.join(prefs.cache_dir_path, rel_path)
        if os.path.exists(test_path) and os.path.isfile(test_path):
            return rel_path.replace('/', '\\')

    game_data = load_game_data()

    path = (filepath, "")
    rest_path = ""

    while True:
        path = os.path.split(path[0])

        if not path[1]:
            print("\nTexture <<{}>> not found.".format(path))
            break

        rest_path = os.path.join(path[1], rest_path)
        rest_path = rest_path[:-1] if rest_path.endswith('\\') else rest_path

        if os.name != 'nt':
            rest_path_n = rest_path.replace('/', '\\')
        else:
            rest_path_n = rest_path

        rest_path_n = rest_path_n[:-1] if rest_path_n.endswith('\\') else rest_path_n

        if game_data.has_file(rest_path_n)[0]:
            return rest_path_n


def get_origin_position():
    loc = bpy.context.scene.cursor_location

    origin_loc = None
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            ctx = bpy.context.copy()
            ctx['area'] = area
            ctx['region'] = area.regions[-1]
            bpy.ops.view3d.snap_cursor_to_selected(ctx)
            origin_loc = bpy.context.scene.cursor_location

    bpy.context.scene.cursor_location = loc

    return origin_loc







