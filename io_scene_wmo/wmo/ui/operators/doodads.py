import bpy
import mathutils

from ..panels.toolbar import switch_doodad_set, get_doodad_sets
from ...utils.doodads import import_doodad
from ...utils.wmv import wmv_get_last_m2
from ....ui import get_addon_prefs
from ....utils.misc import find_nearest_object
from ....third_party.tqdm import tqdm


class WMO_OT_wmv_import_doodad_from_wmv(bpy.types.Operator):
    bl_idname = 'scene.wow_wmo_import_doodad_from_wmv'
    bl_label = 'Import last M2 from WMV'
    bl_description = 'Import last M2 from WoW Model Viewer'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        m2_path = wmv_get_last_m2()
        cache_path = get_addon_prefs().cache_dir_path

        root = context.scene.wow_wmo_root_elements

        if not len(root.doodad_sets) or len(root.doodad_sets) < root.cur_doodad_set:
            self.report({'ERROR'}, "Failed to import doodad. No active doodad set is selected.")
            return {'CANCELLED'}

        doodad_set_obj = root.doodad_sets[root.cur_doodad_set].pointer

        if not m2_path:
            self.report({'ERROR'}, "WoW Model Viewer log contains no model entries."
                                   "Make sure to use compatible WMV version or open an .m2 there.")
            return {'CANCELLED'}

        obj = import_doodad(m2_path, cache_path)
        obj.parent = doodad_set_obj
        obj.location = context.scene.cursor.location

        bpy.context.collection.objects.link(obj)
        context.view_layer.objects.active = obj

        return {'FINISHED'}


class WMO_OT_doodads_bake_color(bpy.types.Operator):
    bl_idname = "scene.wow_doodads_bake_color"
    bl_label = "Bake doodads color"
    bl_description = "Bake doodads colors from nearby vertex color values"
    bl_options = {'UNDO', 'REGISTER'}

    tree_map = {}

    @staticmethod
    def get_object_radius(obj):
        corner_min = [32767, 32767, 32767]
        corner_max = [0, 0, 0]

        mesh = obj.data

        for vertex in mesh.vertices:
            for i in range(3):
                corner_min[i] = min(corner_min[i], vertex.co[i])
                corner_max[i] = max(corner_max[i], vertex.co[i])
        result = (mathutils.Vector(corner_min) - mathutils.Vector(corner_max))
        return (abs(result.x) + abs(result.y) + abs(result.z)) / 3

    def gen_doodad_color(self, obj, group):

        mesh = group.data

        if 'Col' not in mesh.vertex_colors:
            return 0.5, 0.5, 0.5, 1.0

        radius = self.get_object_radius(obj)
        colors = []

        kd_tree = self.tree_map.get(group.name)
        if not kd_tree:
            kd_tree = mathutils.kdtree.KDTree(len(mesh.polygons))

            for index, poly in enumerate(mesh.polygons):
                kd_tree.insert(group.matrix_world @ poly.center, index)

            kd_tree.balance()
            self.tree_map[group.name] = kd_tree

        polygons = kd_tree.find_range(obj.location, radius)

        if not polygons:
            polygons.append(kd_tree.find(obj.location))

        for poly in polygons:
            for loop_index in mesh.polygons[poly[1]].loop_indices:
                colors.append(mesh.vertex_colors['Col'].data[loop_index].color)

        if not colors:
            return 0.5, 0.5, 0.5, 1.0

        final_color = mathutils.Vector((0, 0, 0, 0))

        for color in colors:
            final_color += mathutils.Vector(color)

        final_color = final_color / len(colors)

        flags = bpy.context.scene.wow_wmo_root.flags

        if "2" in flags and group.wow_wmo_group.place_type == '8192':
            final_color += mathutils.Vector(tuple([c / 2 for c in bpy.context.scene.wow_wmo_root.ambient_color]))

        return final_color

    def execute(self, context):

        doodad_counter = 0

        groups = [obj for obj in bpy.context.scene.objects if obj.wow_wmo_group.enabled]

        for index, obj in enumerate(tqdm(bpy.context.selected_objects, desc='Baking doodad colors', ascii=True)):
            if obj.wow_wmo_doodad.enabled:

                group = find_nearest_object(obj, groups)

                if '0' not in group.wow_wmo_group.flags or not group.data.vertex_colors.get('Col'):
                    continue

                vertex_color = self.gen_doodad_color(obj, group)

                color = [pow(x, 2.2) for x in vertex_color]
                obj.wow_wmo_doodad.color = color

                doodad_counter += 1

        if doodad_counter:
            self.report({'INFO'}, "Done baking colors to {} doodad instances.".format(doodad_counter))
        else:
            self.report({'ERROR'}, "No doodad instances found among selected objects.")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)



class WMO_OT_doodad_set_color(bpy.types.Operator):
    bl_idname = 'scene.wow_doodad_set_color'
    bl_label = 'Set Doodad Color'
    bl_description = "Set color to selected doodads"
    bl_options = {'REGISTER', 'UNDO'}

    color:  bpy.props.FloatVectorProperty(
        name='Color',
        description='Color applied to doodads',
        subtype='COLOR',
        size=4
    )

    def draw(self, context):
        self.layout.column().prop(self, "color")

    def execute(self, context):

        if not bpy.context.selected_objects:
            self.report({'ERROR'}, "No objects selected.")
            return {'FINISHED'}

        success = False
        for obj in bpy.context.selected_objects:
            if obj.wow_wmo_doodad.enabled:
                obj.wow_wmo_doodad.color = self.color
                success = True

        if success:
            self.report({'INFO'}, "Successfully assigned color to selected doodads.")
        else:
            self.report({'ERROR'}, "No doodads found among selected objects.")

        return {'FINISHED'}


class WMO_OT_doodadset_template_action(bpy.types.Operator):
    bl_idname = 'scene.wow_doodad_set_template_action'
    bl_label = 'Template action'
    bl_description = 'Apply an action to all instances of selected object on the scene'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    action:  bpy.props.EnumProperty(
        items=[
            ('SELECT', "Select", "Rotate all instances of selected doodads", 'PMARKER_ACT', 0),
            ('REPLACE', "Replace", "Replace all instances of selected doodads with last M2 from WMV", 'FILE_REFRESH', 1),
            ('RESIZE', "Resize", "Resize all instances of selected doodads", 'FULLSCREEN_ENTER', 2),
            ('DELETE', "Delete", "Delete all instances of selected doodads", 'CANCEL', 3),
            ('ROTATE', "Rotate", "Rotate all instances of selected doodads", 'LOOP_FORWARDS', 4)],
        default='SELECT'
    )

    scale:  bpy.props.FloatProperty(
        name="Scale",
        description="Scale applied to doodads",
        min=0.01,
        max=20,
        default=1
    )

    rotation:  bpy.props.FloatVectorProperty(
        name="Rotation",
        default=(0, 0, 0, 0),
        size=4
    )

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        col = self.layout.column()

        col.prop(self, "action", expand=True)

        if self.action == 'RESIZE':
            col.prop(self, "scale")
        elif self.action == 'ROTATE':
            col.prop(self, "rotation")

    def execute(self, context):

        target = None
        active = bpy.context.view_layer.objects.active

        if active and active.wow_wmo_doodad:
            target = active.wow_wmo_doodad.path
        else:
            self.report({'ERROR'}, "Template functions require an active object.")
            return {'CANCELLED'}

        selected_only = False
        if len(bpy.context.selected_objects) > 1:
            selected_only = True

        selected_objects = bpy.context.selected_objects.copy()
        objects_to_select = []

        success = False

        if target:

            new_obj = None

            if self.action == 'REPLACE':
                if not bpy.data.is_saved:
                    self.report({'ERROR'}, "Saved your blendfile first.")
                    return {'FINISHED'}

                if not hasattr(bpy, "wow_game_data"):
                    self.report({'ERROR'}, "Connect to game data first.")
                    return {'FINISHED'}

                bpy.ops.scene.wow_wmo_import_doodad_from_wmv()
                new_obj = bpy.context.view_layer.objects.active

            for obj in bpy.context.scene.objects:
                is_selected = obj in selected_objects if selected_only else True

                if obj.wow_wmo_doodad.path == target and is_selected:

                    if self.action == 'REPLACE':

                        location = obj.location
                        rotation = obj.rotation_quaternion
                        scale = obj.scale
                        parent = obj.parent
                        color = obj.wow_wmo_doodad.color
                        flags = obj.wow_wmo_doodad.flags

                        bpy.data.objects.remove(obj, do_unlink=True)

                        obj = new_obj.copy()
                        bpy.context.collection.objects.link(obj)
                        bpy.context.view_layer.objects.active = obj

                        obj.location = location
                        obj.rotation_mode = 'QUATERNION'
                        obj.rotation_quaternion = rotation
                        obj.scale = scale
                        obj.parent = parent
                        obj.wow_wmo_doodad.color = color
                        obj.wow_wmo_doodad.flags = flags
                        objects_to_select.append(obj)

                    elif self.action == 'RESIZE':

                        obj.scale *= self.scale
                        obj.select_set(True)

                    elif self.action == 'DELETE':

                        bpy.data.objects.remove(obj, do_unlink=True)

                    elif self.action == 'ROTATE':
                        obj.rotation_mode = 'QUATERNION'
                        for i, _ in enumerate(self.rotation):
                            obj.rotation_quaternion[i] += self.rotation[i]

                    elif self.action == 'SELECT':
                        obj.select_set(True)

                    success = True

                for ob in objects_to_select:
                    ob.select_set(True)

            if new_obj:
                bpy.data.objects.remove(new_obj, do_unlink=True)

            if success:
                self.report({'INFO'}, "Template action applied.")

            return {'FINISHED'}

        else:
            self.report({'ERROR'}, "No doodad is selected.")
            return {'FINISHED'}