import bpy
import bmesh
import os

from math import cos, sin, tan, radians
from time import time

from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras import view3d_utils

from ....addon_common.cookiecutter.cookiecutter import CookieCutter
from ....addon_common.common import ui
from ....addon_common.common.utils import delay_exec
from ....addon_common.common.drawing import Drawing
from ....addon_common.common.boundvar import BoundInt, BoundFloat, BoundBool
from ....addon_common.common.ui_styling import load_defaultstylings
from ....addon_common.common.globals import Globals

from ..handlers import DepsgraphLock
from .. import handlers



def angled_vertex(origin: Vector, pos: Vector, angle: float, orientation: float) -> float:
    return origin.z + ((pos.x - origin.x) * cos(orientation) + (pos.y - origin.y) * sin(orientation)) * tan(angle)


def get_median_point(bm: bmesh.types.BMesh) -> Vector:

    selected_vertices = [v for v in bm.verts if v.select]

    f = 1 / len(selected_vertices)

    median = Vector((0, 0, 0))

    for vert in selected_vertices:
        median += vert.co * f

    return median


def align_vertices(bm : bmesh.types.BMesh, mesh : bpy.types.Mesh, median : Vector, angle : float, orientation : float):
    for vert in bm.verts:
        if vert.select:
            vert.co[2] = angled_vertex(median, vert.co, radians(angle), radians(orientation))

    bmesh.update_edit_mesh(mesh, loop_triangles=True, destructive=True)


def reload_stylings():
    load_defaultstylings()
    path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'ui', 'ui.css')
    try:
        Globals.ui_draw.load_stylesheet(path)
    except AssertionError as e:
        # TODO: show proper dialog to user here!!
        print('could not load stylesheet "%s"' % path)
        print(e)
    Globals.ui_document.body.dirty('Reloaded stylings', children=True)
    Globals.ui_document.body.dirty_styling()
    Globals.ui_document.body.dirty_flow()


event_keymap = {
    'ONE' : 0,
    'TWO' : 1,
    'THREE': 2,
    'FOUR': 3,
    'FIVE': 4,
    'SIX': 5,
    'SEVEN': 6,
    'EIGHT': 7,
    'NUMPAD_1': 0,
    'NUMPAD_2': 1,
    'NUMPAD_3': 2,
    'NUMPAD_4': 3,
    'NUMPAD_5': 4,
    'NUMPAD_6': 5,
    'NUMPAD_7': 6,
    'NUMPAD_8': 7,
}

# some settings container
options = {}
options["variable_1"] = 10.0
options["variable_3"] = True


class WMO_OT_edit_liquid(CookieCutter, bpy.types.Operator):
    bl_idname = "wow.liquid_edit_mode"
    bl_label = "Edit WoW Liquid"

    default_keymap = {
        'cancel': {'ESC', 'TAB'},
        'grab': 'G',
        'rotate': 'R',
        'equalize': 'E',
        'flag': 'F',
        'paint': {'LEFTMOUSE', 'SHIFT+LEFTMOUSE'}
    }

    @property
    def variable_2_gs(self):
        return getattr(self, '_var_cut_count_value', 0)

    @variable_2_gs.setter
    def variable_2_gs(self, v):
        if self.variable_2 == v: return
        self.variable_2 = v
        # if self.variable_2.disabled: return

    def start(self):
        self.init_loc = 0.0
        self.speed_modifier = 1.0

        self.orientation = 0.0
        self.angle = 0.0

        self.median = Vector((0, 0, 0))
        self.color_type = 'TEXTURE'
        self.shading_type = 'SOLID'

        self.selected_verts = {}
        self.viewports = []
        self.init_time = time()

        self.obj = self.context.object
        self.mesh = self.context.object.data

        self.active_tool = 'select'

        handlers.DEPSGRAPH_UPDATE_LOCK = True

        bpy.ops.mesh.select_mode(bpy.context.copy(), type='VERT', action='ENABLE', use_extend=True)
        bpy.ops.mesh.select_mode(bpy.context.copy(), type='EDGE', action='ENABLE', use_extend=True)
        bpy.ops.mesh.select_mode(bpy.context.copy(), type='FACE', action='ENABLE', use_extend=True)

        bpy.ops.wm.tool_set_by_id(bpy.context.copy(), name="builtin.select_box")  # force a benign select tool

        # create a bmesh to operate on
        self.bm = bmesh.from_edit_mesh(self.context.object.data)
        self.bm.verts.ensure_lookup_table()

        # create BVH tree for ray_casting
        self.bvh_tree = BVHTree.FromBMesh(self.bm)

        # store viewports
        self.viewports = [a for a in self.context.screen.areas if a.type == 'VIEW_3D']

        for viewport in self.viewports:
            self.color_type = viewport.spaces[0].shading.color_type
            self.shading_type = viewport.spaces[0].shading.type
            viewport.spaces[0].shading.type = 'SOLID'
            viewport.spaces[0].shading.color_type = 'VERTEX'

        # setup UI variables

        self.tools = {
            "select": ("Select", "", ""),
            "grab": ("Raise / Lower (G)", "close.png", "Raise \ Lower"),
            "rotate": ("Rotate (R)", "legion.png", ""),
            "equalize": ("Equalize (E)", "", ""),
            "flag": ("Edit flags (F)", "contours_32.png", ""),

        }

        self.variable_1 = BoundFloat('''options['variable_1']''', min_value=0.5, max_value=15.5)
        self.variable_2 = BoundInt('''self.variable_2_gs''', min_value=0, max_value=10)
        self.variable_3 = BoundBool('''options['variable_3']''')

        self.blender_ui_set()
        self.setup_ui()

    def blender_ui_set(self):
        self.viewaa_simplify()
        self.manipulator_hide()
        self._space.show_gizmo = True
        self.panels_hide()
        self.region_darken()

    def update_ui(self):
        self.ui_main.dirty('update', parent=True, children=True)

    def select_tool(self, action):

        tool_id = "tool-{}".format(action)

        e = self.document.body.getElementById('tool-{}'.format(tool_id))
        if e: e.checked = True

        self.active_tool = action

        self.update_ui()

    def setup_ui(self):

        reload_stylings()

        self.ui_main = ui.framed_dialog(label='Liquid Editor',
                                        resiable=None,
                                        resiable_x=True,
                                        resizable_y=False,
                                        closeable=False,
                                        moveable=True,
                                        hide_on_close=True,
                                        parent=self.document.body)

        # tools
        ui_tools = ui.div(id="tools", parent=self.ui_main)

        def add_tool(action="", name="", icon="", title=""):
            nonlocal ui_tools
            nonlocal self
            # must be a fn so that local vars are unique and correctly captured
            lbl, img = name, icon

            radio = ui.input_radio(id='tool-{}'.format(action), value=lbl.lower(), title=title, name="tool",
                                   classes="tool", checked=False, parent=ui_tools)
            radio.add_eventListener('on_input', delay_exec('''if radio.checked: self.select_tool("{}")'''.format(action)))
            ui.img(src=img, parent=radio, title=title)
            ui.label(innerText=lbl, parent=radio, title=title)

        for key, value in self.tools.items(): add_tool(action=key, name=value[0], icon=value[1], title=value[2])

        ui.button(label='ui.button', title='self.tool_action() method linked to button', parent=ui_tools,
                  on_mouseclick=self.tool_action)

        # create a collapsille container to hold a few variables
        container = ui.collapsible('ui.collapse container', parent=self.ui_main)

        i1 = ui.labeled_input_text(label='Sui.labeled_input_text',
                                   title='float property to BoundFLoat',
                                   value=self.variable_1)

        i2 = ui.labeled_input_text(label='ui.labled_input_text',
                                   title='integer property to BoundInt',
                                   value=self.variable_2)

        i3 = ui.input_checkbox(
            label='ui.input_checkbox',
            title='True/False property to BoundBool')

        container.builder([i1, i2, i3])

    def should_pass_through(self, context, event):

        # allow selection events to pass through
        return True if event.type in {'A', 'B', 'C'} else False

    def tool_action(self):
        print('tool action')
        return

    def activate_tool(self, name):
        self.active_tool = name
        e = self.document.body.getElementById('tool-{}'.format(self.active_tool))
        if e: e.checked = True


    def update_bmesh(self):
        self.bm = bmesh.from_edit_mesh(self.context.object.data)
        self.bm.verts.ensure_lookup_table()

    @CookieCutter.FSM_State('main', 'enter')
    def enter_main(self):
        self.update_bmesh()

    @CookieCutter.FSM_State('main')
    def modal_main(self):

        self.context.area.tag_redraw()
        Drawing.set_cursor('DEFAULT')

        if self.actions.pressed('grab') or self.active_tool == 'grab':
            self.activate_tool('grab')

            Drawing.set_cursor('MOVE_X')
            self.init_loc = self.event.mouse_x
            self.selected_verts = {vert: vert.co[2] for vert in self.bm.verts if vert.select}

            return 'grab'

        elif self.actions.pressed('rotate') or self.active_tool == 'rotate':
            self.activate_tool('rotate')

            self.report({'INFO'}, "Rotating vertices. Shift + Scroll - tilt | Alt + Scroll - rotate")

            self.selected_verts = {vert: vert.co[2] for vert in self.bm.verts if vert.select}
            self.median = get_median_point(self.bm)
            self.orientation = 0.0
            self.angle = 0.0

            return 'rotate'

        elif self.actions.pressed('equalize') or self.active_tool == 'equalize':

            self.activate_tool('equalize')
            return 'equalize'

        elif self.actions.pressed('flag') or self.active_tool == 'flag':

            self.activate_tool('flag')
            return 'flag'

        elif self.actions.pressed('cancel') and (time() - self.init_time) > 0.5:

            bpy.ops.object.mode_set(mode='OBJECT')

            for viewport in self.viewports:
                viewport.spaces[0].shading.type = self.shading_type
                viewport.spaces[0].shading.color_type = self.color_type

            handlers.DEPSGRAPH_UPDATE_LOCK = False

            self.done(cancel=False)
            return 'finished'

        else:
            self.activate_tool('select')

    @CookieCutter.FSM_State('grab')
    def modal_grab(self):

        if self.active_tool != 'grab':
            return 'main'
        else:
            self.activate_tool('grab')

        # alter vertex height
        if self.actions.mousemove:

            fac = 10 if self.actions.shift else 30
            for vert, height in self.selected_verts.items():
                vert.co[2] = height + (self.event.mouse_x - self.init_loc) / fac

            bmesh.update_edit_mesh(self.mesh, loop_triangles=True, destructive=True)

        # accept
        if self.actions.event_type == 'LEFTMOUSE':
            self.active_tool = 'select'
            return 'main'

        # cancel
        elif self.actions.event_type == 'RIGHTMOUSE':

            for vert, height in self.selected_verts.items():
                vert.co[2] = height

                bmesh.update_edit_mesh(self.mesh, loop_triangles=True, destructive=True)

            self.active_tool = 'select'

            return 'main'

        # switch state
        for action in self.default_keymap.keys():

            if self.actions.pressed(action):
                self.update_bmesh()
                self.active_tool = action
                return action

        return 'grab'

    @CookieCutter.FSM_State('rotate')
    def modal_rotate(self):

        if self.active_tool != 'rotate':
            return 'main'

        Drawing.set_cursor('SCROLL_Y')

        if self.actions.event_type == 'WHEELUPMOUSE':

            if self.actions.shift:
                self.angle = min(self.angle + 5, 89.9)
                align_vertices(self.bm, self.context.object.data, self.median, self.angle, self.orientation)

            elif self.actions.alt:
                self.orientation += 10

                if self.orientation > 360:
                    self.orientation -= 360

                align_vertices(self.bm, self.context.object.data, self.median, self.angle, self.orientation)

        elif self.actions.event_type == 'WHEELDOWNMOUSE':

            if self.actions.shift:
                self.angle = max(self.angle - 5, -89.9)
                align_vertices(self.bm, self.context.object.data, self.median, self.angle, self.orientation)

            elif self.actions.alt:
                self.orientation -= 10

                if self.orientation < 0:
                    self.orientation = 360 - self.orientation

                align_vertices(self.bm, self.context.object.data, self.median, self.angle, self.orientation)

        # accept
        if self.actions.event_type == 'LEFTMOUSE':
            self.active_tool = 'select'
            return 'main'

        # cancel
        elif self.actions.event_type == 'RIGHTMOUSE':

            for vert, height in self.selected_verts.items():
                vert.co[2] = height

                bmesh.update_edit_mesh(self.mesh, loop_triangles=True, destructive=True)

            self.active_tool = 'select'

            return 'main'

        return 'rotate'

    @CookieCutter.FSM_State('equalize')
    def equalize(self):

        median = get_median_point(self.bm)

        for vert in self.bm.verts:
            if vert.select:
                vert.co[2] = median[2]

        bmesh.update_edit_mesh(self.mesh, loop_triangles=True, destructive=True)
        self.report({'INFO'}, "Equalized vertex height")

        self.active_tool = 'select'

        return 'main'

    @CookieCutter.FSM_State('flag')
    def modal_flag(self):

        if self.active_tool != 'flag':
            return 'main'

        Drawing.set_cursor('PAINT_BRUSH')

        if self.actions.event_type in event_keymap.keys():

            flag_number = event_keymap.get(self.actions.event_type, 0)
            layer = self.mesh.vertex_colors.get("flag_{}".format(flag_number))
            layer.active = True

        layer = self.bm.loops.layers.color.active
        color = (0, 0, 255, 255) if not self.actions.shift else (255, 255, 255, 255)

        if self.actions.event_type == 'K':

            for face in self.bm.faces:
                if face.select:
                    for loop in face.loops:
                        loop[layer] = color

            bmesh.update_edit_mesh(self.mesh, loop_triangles=True, destructive=True)
            self.report({'INFO'}, "Flag unset" if self.actions.shift else "Flag set")

        if not self.actions.released('paint'):

            # TODO: radius brush

            # get the context arguments
            region = self.context.region
            rv3d = self.context.region_data
            coord = self.event.mouse_region_x, self.event.mouse_region_y

            # get the ray from the viewport and mouse
            view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
            ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)

            ray_target = ray_origin + view_vector

            ray_origin_obj = self.obj.matrix_world.inverted() @ ray_origin
            ray_target_obj = self.obj.matrix_world.inverted() @ ray_target

            ray_direction_obj = ray_target_obj - ray_origin_obj

            # cast the ray

            location, normal, face_index, distance = self.bvh_tree.ray_cast(ray_origin_obj, ray_direction_obj)

            if face_index is not None:
                color = (0, 0, 255, 255) if not self.actions.shift else (255, 255, 255, 255)

                face = self.bm.faces[face_index]

                for loop in face.loops:
                    loop[layer] = color

                bmesh.update_edit_mesh(self.mesh, loop_triangles=True, destructive=True)

        if self.actions.event_type == 'RIGHTMOUSE':
            self.active_tool = 'select'
            return 'main'
        else:
          return 'flag'


class WMO_OT_add_liquid(bpy.types.Operator):
    bl_idname = 'scene.wow_add_liquid'
    bl_label = 'Add liquid'
    bl_description = 'Add a WoW liquid plane'
    bl_options = {'REGISTER', 'UNDO'}

    x_planes:  bpy.props.IntProperty(
        name="X subdivisions:",
        description="Amount of WoW liquid planes in a row. One plane is 4.1666625 in its radius.",
        default=10,
        min=1
    )

    y_planes:  bpy.props.IntProperty(
        name="Y subdivisions:",
        description="Amount of WoW liquid planes in a column. One plane is 4.1666625 in its radius.",
        default=10,
        min=1
    )

    def execute(self, context):
        with DepsgraphLock():
            bpy.ops.mesh.primitive_grid_add(x_subdivisions=self.x_planes + 1,
                                            y_subdivisions=self.y_planes + 1,
                                            size=4.1666625
                                            )
            water = bpy.context.view_layer.objects.active
            bpy.ops.transform.resize(value=(self.x_planes, self.y_planes, 1.0))
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

            water.name += "_Liquid"

            mesh = water.data

            bit = 1
            counter = 0
            while bit <= 0x80:
                mesh.vertex_colors.new(name="flag_{}".format(counter))

                counter += 1
                bit <<= 1

            water.wow_wmo_liquid.enabled = True

            water.hide_set(False if "4" in bpy.context.scene.wow_visibility else True)

        self.report({'INFO'}, "Successfully сreated WoW liquid: {}".format(water.name))
        return {'FINISHED'}