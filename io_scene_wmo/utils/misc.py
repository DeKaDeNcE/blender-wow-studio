import bpy
import os
import sys

from mathutils import Vector
from collections import namedtuple

from ..pywowlib import WoWVersionManager
from ..pywowlib.archives.wow_filesystem import WoWFileData
from .. import PACKAGE_NAME


SequenceRecord = namedtuple('SequenceRecord', ['name', 'value', 'index'])


class Sequence(type):

    def __new__(mcs, name, bases, dct):

        dct['__fields__'] = list(dct.keys())[2:]
        dct['_iter'] = 0

        return super().__new__(mcs, name, bases, dct)

    def __getitem__(self, item):
        return getattr(self, self.__fields__[item])

    def __iter__(self):
        return self

    def __next__(self):

        if self._iter == len(self.__fields__):
            self._iter = 0
            raise StopIteration
        
        item = SequenceRecord(self.__fields__[self._iter], getattr(self, self.__fields__[self._iter]), self._iter)
        self._iter += 1
        return item

    def index(self, item):
        return self.__fields__.index(item)

def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance


def find_nearest_object(obj_, objects):
    """Get closest object to another object"""

    dist = sys.float_info.max
    result = None

    for obj in objects:
        obj_location_relative = obj.matrix_world.inverted() @ obj_.location
        hit = obj.closest_point_on_mesh(obj_location_relative)
        hit_dist = (obj_location_relative - hit[1]).length
        if hit_dist < dist:
            dist = hit_dist
            result = obj

    return result


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


def load_game_data() -> WoWFileData:

    WoWVersionManager().set_client_version(int(bpy.context.scene.wow_scene.version))

    if not hasattr(bpy, 'wow_game_data'):

        addon_preferences = bpy.context.preferences.addons[PACKAGE_NAME].preferences
        bpy.wow_game_data = WoWFileData(addon_preferences.wow_path, addon_preferences.project_dir_path)

        if not bpy.wow_game_data.files:
            raise UserWarning("WoW game data is not loaded. Check settings.")

    return bpy.wow_game_data


def resolve_texture_path(filepath: str) -> str:
    filepath = os.path.splitext(bpy.path.abspath(filepath))[0] + ".blp"
    prefs = bpy.context.preferences.addons[PACKAGE_NAME].preferences

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
            print("\nTexture \"{}\" not found.".format(path))
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
    loc = bpy.context.scene.cursor.location

    origin_loc = None
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            ctx = bpy.context.copy()
            ctx['area'] = area
            ctx['region'] = area.regions[-1]
            bpy.ops.view3d.snap_cursor_to_selected(ctx)
            origin_loc = bpy.context.scene.cursor.location

    bpy.context.scene.cursor.location = loc

    return origin_loc


def get_obj_boundbox_center(obj):
    return obj.matrix_world @ (0.125 * sum((Vector(b) for b in obj.bound_box), Vector()))


def get_obj_radius(obj, bb_center):
    mesh = obj.data
    radius = 0.0
    for vertex in mesh.vertices:
        dist = (vertex.co - bb_center).length
        if dist > radius:
            radius = dist

    return radius


def get_obj_boundbox_world(obj):
    return tuple(obj.matrix_world @ Vector(obj.bound_box[0])), tuple(obj.matrix_world @ Vector(obj.bound_box[6]))


def get_objs_boundbox_world(objects):
    corner1 = [32768, 32768, 32768]
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


def simplify_numbers(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])


def wrap_text(width, text):

    lines = []

    arr = text.split()
    length_sum = 0

    str_sum = ""

    for var in arr:
        length_sum += len(var) + 1
        if length_sum <= width:
            str_sum += " " + var
        else:
            lines.append(str_sum)
            length_sum = 0
            str_sum = var

    if length_sum != 0:
        lines.append(str_sum)

    # lines.append(" " + arr[len(arr) - 1])

    return lines


def draw_spoiler(layout, data, toggle_prop_name, name="", data1=None, layout_enabled=None, icon=None, align=True):
    """ Draw a spoiler-like layout in Blender UI """

    is_expanded = getattr(data, toggle_prop_name)

    body = layout.box()

    header = body.box()
    header_row = header.row(align=True)
    header_row.prop(data, toggle_prop_name, emboss=False, text='', icon='TRIA_DOWN' if is_expanded else 'TRIA_RIGHT')

    if data1 and layout_enabled:
        if icon:
            header_row.label(text='', icon=icon)
        header_row.prop(data1, layout_enabled, text=name)
    else:
        header_row.label(text='       ' + name if align else name, icon=icon)

    if is_expanded:

        content = body.column()

        if data1 and layout_enabled:
            content.enabled = getattr(data1, layout_enabled)

        return content


def show_message_box(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)







