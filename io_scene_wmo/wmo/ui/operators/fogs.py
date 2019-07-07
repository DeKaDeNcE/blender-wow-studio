import bpy

from ...utils.fogs import create_fog_object

class WMO_OT_add_fog(bpy.types.Operator):
    bl_idname = 'scene.wow_add_fog'
    bl_label = 'Add fog'
    bl_description = 'Add a WoW fog object to the scene'

    def execute(self, context):

        fog = create_fog_object()

        self.report({'INFO'}, "Successfully сreated WoW fog: " + fog.name)
        return {'FINISHED'}