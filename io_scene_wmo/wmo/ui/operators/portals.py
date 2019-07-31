import bpy
from ..enums import portal_dir_alg_enum


class WMO_OT_bake_portal_relations(bpy.types.Operator):
    bl_idname = 'scene.wow_bake_portal_relations'
    bl_label = 'Bake portal relations'
    bl_description = 'Bake portal relations'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        def find_nearest_objects_pair(object, objects):

            pairs = []

            for obj in objects:
                hit = obj.closest_point_on_mesh(
                    obj.matrix_world.inverted() @ (object.matrix_world @ object.data.polygons[0].center))
                hit_dist = (obj.matrix_world @ hit[1] - object.matrix_world @ object.data.polygons[0].center).length
                pairs.append((obj, hit_dist))

            pairs.sort(key=lambda x: x[1])

            return pairs[0][0], pairs[1][0]

        if not bpy.context.selected_objects:
            self.report({'ERROR'}, "No objects selected.")
            return {'FINISHED'}

        success = False

        groups = tuple(x for x in bpy.context.scene.objects if x.wow_wmo_group.enabled and not x.hide_get())

        for obj in bpy.context.selected_objects:
            if obj.wow_wmo_portal.enabled:
                direction = find_nearest_objects_pair(obj, groups)
                obj.wow_wmo_portal.first = direction[0] if direction[0] else ""
                obj.wow_wmo_portal.second = direction[1] if direction[1] else ""
                success = True

        if success:
            self.report({'INFO'}, "Done baking portal relations.")
        else:
            self.report({'ERROR'}, "No portal objects found among selected objects.")

        return {'FINISHED'}


class WMO_OT_invert_portals(bpy.types.Operator):
    bl_idname = 'scene.wow_set_portal_dir_alg'
    bl_label = 'Set portal direction algorithm'
    bl_description = 'Set portal direction calculation algorithm.'
    bl_options = {'REGISTER', 'UNDO'}

    Algorithm:  bpy.props.EnumProperty(
        items=portal_dir_alg_enum,
        default="0"
    )

    def execute(self, context):
        success = False
        for ob in bpy.context.selected_objects:
            if ob.wow_wmo_portal.enabled:
                ob.wow_wmo_portal.algorithm = self.Algorithm
                success = True

        if success:
            self.report({'INFO'}, "Successfully inverted selected portals")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No portals found among selected objects")
            return {'CANCELLED'}