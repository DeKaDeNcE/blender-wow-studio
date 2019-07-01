import bpy
import os
import sys
import time

from mathutils import Vector

from ..pywowlib.archives.wow_filesystem import WoWFileData
from .. import PACKAGE_NAME


def find_nearest_object(obj_, objects):
    """Get closest object to another object"""

    dist = sys.float_info.max
    result = None
    for obj in objects:
        obj_location_relative = obj.matrix_world.inverted() @ obj.location
        hit = obj_.closest_point_on_mesh(obj_location_relative)
        hit_dist = (obj.location - obj.matrix_world @ hit[1]).length
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


def load_game_data():
    if not hasattr(bpy, 'wow_game_data'):

        addon_preferences = bpy.context.preferences.addons[PACKAGE_NAME].preferences
        bpy.wow_game_data = WoWFileData(addon_preferences.wow_path, addon_preferences.project_dir_path)

        if not bpy.wow_game_data.files:
            raise UserWarning("WoW game data is not loaded. Check settings.")

    return bpy.wow_game_data


def resolve_texture_path(filepath):
    filepath = os.path.splitext(bpy.path.abspath(filepath))[0] + ".blp"
    prefs = bpy.context.preferences.addons[__package__].preferences

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

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)


class ProgressReport:
    def __init__(self, iterable, msg):
        self.iterable = iterable
        self.n_steps = len(iterable)
        self.step = 0
        self.msg = msg
        self.cur_msg = ''
        self.start_time = time.time()

    def __iter__(self):
        return self

    def __next__(self):
        if not self.step:
            self.start_time = time.time()

        if self.step == len(self.iterable):
            self.progress_end()
            raise StopIteration

        ret = self.iterable[self.step]
        self.step += 1
        self.update_progress()

        return ret

    def update_progress(self):
        old_len = len(self.cur_msg)
        percent = int(self.step / self.n_steps * 100) if self.n_steps else 100
        progress = percent / 100.0
        length = 40
        block = int(round(length * progress))
        self.cur_msg = "\r{}: [{}] {}% <{} / {}>".format(self.msg, "#"*block + "-"*(length-block),
                                                         percent, self.step, self.n_steps)
        sys.stdout.write("{}{}".format(self.cur_msg, ' ' * (old_len - len(self.cur_msg))))
        sys.stdout.flush()

    def progress_end(self):
        self.update_progress()
        old_len = len(self.cur_msg)
        e_time = time.strftime("%M min. %S sec.", time.gmtime(time.time() - self.start_time))
        msg = "{0}: done in {1} <{2} / {2}>".format(self.msg, e_time, self.n_steps)
        sys.stdout.write("\r{}{}\n".format(msg, ' ' * abs(old_len - len(msg))))
        sys.stdout.flush()

    def progress_step(self):
        """ Manually step through progress. Should be used when ProgressReport is not used as an iterator"""
        return next(self)


class BiDirectionalDict:
    __slots__ = ('forward', 'reversed')

    def __init__(self):
        self.forward = {}
        self.reversed = {}

    @staticmethod
    def _parse_subscription_args(item):
        if isinstance(item, int):
            index, is_reversed = item, False

        elif isinstance(item, tuple):
            if len(item) != 2:
                raise IndexError('\nBiDirectionalDict expects either an int key or a tuple of (index, is_reversed)')

            index, is_reversed = item

        else:
            raise TypeError('\nBiDirectionalDict expects either an int key or a tuple of (index, is_reversed)')

        return index, is_reversed

    def __getitem__(self, key):
        index, is_reversed = self._parse_subscription_args(key)
        _dict = self.forward if not is_reversed else self.reversed
        return _dict[index]

    def __setitem__(self, key, value):
        index, is_reversed = self._parse_subscription_args(key)
        left, right = (self.reversed, self.forward) if is_reversed else (self.forward, self.reversed)

        if value in right:
            del right[value]

        left[index] = value
        right[value] = index

    def get(self, key, is_reversed=False, default=None):
        _dict = self.forward if not is_reversed else self.reversed
        return _dict.get(key, default)

    def setdefault(self, key, is_reversed=False, default=None):
        result = self.get(key, is_reversed)

        if result is None:
            self[key, is_reversed] = default
            return default

        return result






