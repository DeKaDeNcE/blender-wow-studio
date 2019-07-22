import bpy
import bmesh

from math import cos, sin, tan, radians
from time import time

from mathutils import Vector

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


class WMO_OT_edit_liquid(bpy.types.Operator):
    bl_idname = "wow.liquid_edit_mode"
    bl_label = "Edit WoW Liquid"

    def __init__(self):
        self.init_loc = 0.0
        self.move_initiated = False
        self.rotation_initiated = False
        self.bm = None
        self.speed_modifier = 1.0

        self.orientation = 0.0
        self.angle = 0.0

        self.median = Vector((0, 0, 0))
        self.color_type = 'TEXTURE'
        self.shading_type = 'SOLID'

        self.selected_verts = {}
        self.viewports = []
        self.init_time = time()

    def __del__(self):
        pass

    def modal(self, context, event):
        context.area.tag_redraw()

        if context.object.mode != 'EDIT':
            return {'PASS_THROUGH'}

        mesh = context.object.data

        if event.type in {'MIDDLEMOUSE', 'NUMPAD_PERIOD'}:
            return {'PASS_THROUGH'}

        if event.type in {'C', 'B', 'A', 'RIGHTMOUSE'} \
                and not self.move_initiated \
                and not self.rotation_initiated:
            return {'PASS_THROUGH'}

        elif event.type == 'G' and not self.rotation_initiated:
            bpy.context.window.cursor_modal_set('MOVE_X')
            self.report({'INFO'}, "Changing height")
            self.move_initiated = True
            self.init_loc = event.mouse_x

            self.selected_verts = {vert : vert.co[2] for vert in self.bm.verts if vert.select}

        elif event.type == 'R' and not self.move_initiated:
            bpy.context.window.cursor_modal_set('SCROLL_Y')
            self.report({'INFO'}, "Rotating vertices. Shift + Scroll - tilt | Alt + Scroll - rotate")
            self.selected_verts = {vert: vert.co[2] for vert in self.bm.verts if vert.select}
            self.rotation_initiated = True
            self.median = get_median_point(self.bm)
            self.orientation = 0.0
            self.angle = 0.0

        elif event.type == 'E' and event.shift:

            median = get_median_point(self.bm)

            for vert in self.bm.verts:
                if vert.select:
                    vert.co[2] = median[2]

            bmesh.update_edit_mesh(mesh, loop_triangles=True, destructive=True)
            self.report({'INFO'}, "Equalized vertex height")

        elif event.type == 'MOUSEMOVE':

            if self.move_initiated:
                fac = 10 if event.shift else 30
                for vert, height in self.selected_verts.items():
                    vert.co[2] = height + (event.mouse_x - self.init_loc) / fac

                bmesh.update_edit_mesh(mesh, loop_triangles=True, destructive=True)

            return {'PASS_THROUGH'}

        elif event.type == 'WHEELUPMOUSE':

            if self.rotation_initiated:

                if event.shift:
                    self.angle = min(self.angle + 5, 89.9)
                    align_vertices(self.bm, context.object.data, self.median, self.angle, self.orientation)

                elif event.alt:
                    self.orientation += 10

                    if self.orientation > 360:
                        self.orientation -= 360

                    align_vertices(self.bm, context.object.data, self.median, self.angle, self.orientation)

            else:
                return {'PASS_THROUGH'}

        elif event.type == 'WHEELDOWNMOUSE':

            if self.rotation_initiated:
                if event.shift:
                    self.angle = max(self.angle - 5, -89.9)
                    align_vertices(self.bm, context.object.data, self.median, self.angle, self.orientation)

                elif event.alt:
                    self.orientation -= 10

                    if self.orientation < 0:
                        self.orientation = 360 - self.orientation

                    align_vertices(self.bm, context.object.data, self.median, self.angle, self.orientation)

            else:
                return {'PASS_THROUGH'}

        # handle flag editing

        elif event.type in event_keymap.keys():

            flag_number = event_keymap[event.type]
            mesh = context.object.data
            layer = mesh.vertex_colors.get("flag_{}".format(flag_number))
            layer.active = True

        elif event.type == 'F' and (event.shift or event.ctrl):
            layer = self.bm.loops.layers.color.active
            color = (0, 0, 255, 255) if event.shift else (255, 255, 255, 255)

            for face in self.bm.faces:
                if face.select:
                    for loop in face.loops:
                        loop[layer] = color

            bmesh.update_edit_mesh(mesh, loop_triangles=True, destructive=True)
            self.report({'INFO'}, "Flag set" if event.shift else "Flag unset")

        elif event.type in {'LEFTMOUSE'}:  # Confirm
            bpy.context.window.cursor_modal_restore()

            if self.move_initiated or self.rotation_initiated:
                self.report({'INFO'}, "Applied")
                self.move_initiated = False
                self.rotation_initiated = False

        elif event.type in {'RIGHTMOUSE'}:
            bpy.context.window.cursor_set('DEFAULT')

            if self.move_initiated or self.rotation_initiated:
                self.report({'INFO'}, "Cancelled")
                self.move_initiated = False
                self.rotation_initiated = False

            for vert, height in self.selected_verts.items():
                vert.co[2] = height

                bmesh.update_edit_mesh(mesh, loop_triangles=True, destructive=True)

        elif event.type in {'ESC', 'TAB'} and (time() - self.init_time) > 0.5:  # Cancel
            bpy.ops.object.mode_set(mode='OBJECT')

            for viewport in self.viewports:
                viewport.spaces[0].shading.type = self.shading_type
                viewport.spaces[0].shading.color_type = self.color_type

            handlers.DEPSGRAPH_UPDATE_LOCK = False
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):

        if context.object.mode == 'EDIT':
            handlers.DEPSGRAPH_UPDATE_LOCK = True

            bpy.ops.mesh.select_mode(bpy.context.copy(), type='VERT', action='ENABLE', use_extend=True)
            bpy.ops.mesh.select_mode(bpy.context.copy(), type='EDGE', action='ENABLE', use_extend=True)
            bpy.ops.mesh.select_mode(bpy.context.copy(), type='FACE', action='ENABLE', use_extend=True)

            bpy.ops.wm.tool_set_by_id(bpy.context.copy(), name="builtin.select_box")         # force a benign select tool

            # create a bmesh to operate on
            self.bm = bmesh.from_edit_mesh(context.object.data)
            self.bm.verts.ensure_lookup_table()

            self.viewports = [a for a in context.screen.areas if a.type == 'VIEW_3D']

            context.window_manager.modal_handler_add(self)

            for viewport in self.viewports:
                self.color_type = viewport.spaces[0].shading.color_type
                self.shading_type = viewport.spaces[0].shading.type
                viewport.spaces[0].shading.type = 'SOLID'
                viewport.spaces[0].shading.color_type = 'VERTEX'

            return {'RUNNING_MODAL'}

        else:
            return {'CANCELLED'}


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

            water.hide_viewport = False if "4" in bpy.context.scene.wow_visibility else True

        self.report({'INFO'}, "Successfully сreated WoW liquid: {}".format(water.name))
        return {'FINISHED'}