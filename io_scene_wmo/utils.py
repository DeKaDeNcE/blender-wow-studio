import bpy
import os

from mathutils import Vector
from .pywowlib.archives.mpq.wow import WoWFileData
from .pywowlib.wdbx.wdbc import DBFilesClient, DBCFile


def parse_bitfield(bitfield, last_flag=0x1000):

    flags = set()
    bit = 1
    while bit <= last_flag:
        if bitfield & bit:
            flags.add(str(bit))
        bit <<= 1

    return flags


def construct_bitfield(flag_set):

    bitfield = 0

    for flag in flag_set:
        bitfield |= int(flag)

    return bitfield


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
        bpy.wow_game_data = WoWFileData(addon_preferences.wow_path,
                                        addon_preferences.project_dir_path,
                                        addon_preferences.blp_path)

        if not bpy.wow_game_data.files:
            raise ChildProcessError("WoW game data is not loaded. Check settings.")

        bpy.db_files_client = DBFilesClient()

        # list of all DB tables that we need to load
        anim_data_dbc = DBCFile('AnimationData')
        anim_data_dbc.read_from_gamedata(bpy.wow_game_data)
        char_sections_dbc = DBCFile('CharSections')
        char_sections_dbc.read_from_gamedata(bpy.wow_game_data)
        creature_display_info_dbc = DBCFile('CreatureDisplayInfo')
        creature_display_info_dbc.read_from_gamedata(bpy.wow_game_data)
        item_display_info_dbc = DBCFile('ItemDisplayInfo')
        item_display_info_dbc.read_from_gamedata(bpy.wow_game_data)

        bpy.db_files_client.add(anim_data_dbc)
        bpy.db_files_client.add(char_sections_dbc)
        bpy.db_files_client.add(creature_display_info_dbc)
        bpy.db_files_client.add(item_display_info_dbc)

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


def get_obj_boundbox_center(obj):
    return obj.matrix_world * (0.125 * sum((Vector(b) for b in obj.bound_box), Vector()))


def get_obj_radius(obj, bb_center):
    mesh = obj.data
    radius = 0.0
    for vertex in mesh.vertices:
        dist = (vertex.co - bb_center).length
        if dist > radius:
            radius = dist

    return radius


def get_obj_boundbox_world(obj):
    return tuple(obj.matrix_world * Vector(obj.bound_box[0])), tuple(obj.matrix_world * Vector(obj.bound_box[6]))


def get_objs_boundbox_world(objects):
    corner1 = [32768, 32768, 32768]     # TODO: verify max boundaries
    corner2 = [-32768, -32768, -32768]

    for obj in objects:
        obj_bb_corner1, obj_bb_corner2 = get_obj_boundbox_world(obj)

        for i, value in enumerate(obj_bb_corner1):
            if value < corner1[i]:
                corner1[i] = value

        for i, value in enumerate(obj_bb_corner2):
            if value > corner2[i]:
                corner2[i] = value

    return tuple(corner1), tuple(corner2)








