import bpy


class WMO_OT_destroy_property(bpy.types.Operator):
    bl_idname = "scene.wow_wmo_destroy_wow_property"
    bl_label = "Disable Property"
    bl_options = {'UNDO', 'REGISTER', 'INTERNAL'}

    prop_group:  bpy.props.StringProperty()

    prop_map = {
        'wow_wmo_group': 'groups',
        'wow_wmo_light': 'lights',
        'wow_wmo_material': 'materials',
        'wow_wmo_fog': 'fogs',
        'wow_wmo_portal': 'portals',
        'wow_wmo_doodad': 'doodads'
    }

    @classmethod
    def poll(cls, context):
        return context.scene.wow_scene.type == 'WMO' and hasattr(context, 'object') and context.object

    def execute(self, context):

        getattr(context.object, self.prop_group).enabled = False

        col = getattr(bpy.context.scene.wow_wmo_root_components, self.prop_map[self.prop_group])

        idx = col.find(context.object.name)

        if idx >= 0:
            col.remove(idx)
            bpy.context.scene.wow_wmo_root_components.is_update_critical = True

        return {'FINISHED'}
