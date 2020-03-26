import bpy
from ..enums import *


class M2_PT_geoset_panel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "M2 Geoset"

    def draw(self, context):
        self.layout.prop(context.object.wow_m2_geoset, "collision_mesh")

        if not context.object.wow_m2_geoset.collision_mesh:
            self.layout.prop(context.object.wow_m2_geoset, "mesh_part_group")
            self.layout.prop(context.object.wow_m2_geoset, "mesh_part_id")

            row = self.layout.row(align=True)
            row.prop(context.object.wow_m2_geoset, "uv_transform")
            row.operator("scene.wow_m2_geoset_add_texture_transform", text='', icon='RNA_ADD')

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'M2'
                and context.object is not None
                and context.object.data is not None
                and isinstance(context.object.data, bpy.types.Mesh))


def update_geoset_uv_transform(self, context):
    c_obj = context.object.wow_m2_geoset.uv_transform

    uv_transform = context.object.modifiers.get('M2TexTransform')

    if c_obj:
        if not c_obj.wow_m2_uv_transform.enabled:
            context.object.wow_m2_geoset.uv_transform = None

        if not uv_transform:
            bpy.ops.object.modifier_add(type='UV_WARP')
            uv_transform = context.object.modifiers[-1]
            uv_transform.name = 'M2TexTransform'
            uv_transform.object_from = context.object
            uv_transform.object_to = c_obj
            uv_transform.uv_layer = 'UVMap'
        else:
            uv_transform.object_to = c_obj

    elif uv_transform:
        context.object.modifiers.remove(uv_transform)


class WowM2GeosetPropertyGroup(bpy.types.PropertyGroup):
    collision_mesh:  bpy.props.BoolProperty(
        name='Collision mesh',
        default=False
    )

    mesh_part_group:  bpy.props.EnumProperty(
        name="Geoset group",
        description="Group of this geoset",
        items=MESH_PART_TYPES
    )

    mesh_part_id:  bpy.props.EnumProperty(
        name="Geoset ID",
        description="Mesh part ID of this geoset",
        items=mesh_part_id_menu
    )

    uv_transform:  bpy.props.PointerProperty(
        name="UV Transform",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.wow_m2_uv_transform.enabled,
        update=update_geoset_uv_transform
    )


class M2_OT_add_texture_transform(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_geoset_add_texture_transform'
    bl_label = 'Add new UV transform controller'
    bl_options = {'REGISTER', 'INTERNAL'}

    anim_index:  bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        bpy.ops.object.empty_add(type='SINGLE_ARROW', location=(0, 0, 0))
        c_obj = bpy.context.view_layer.objects.active
        c_obj.name = "TT_Controller"
        c_obj.wow_m2_uv_transform.enabled = True
        c_obj = bpy.context.view_layer.objects.active
        c_obj.rotation_mode = 'QUATERNION'
        c_obj.empty_display_size = 0.5
        c_obj.animation_data_create()
        c_obj.animation_data.action_blend_type = 'ADD'

        obj.wow_m2_geoset.uv_transform = c_obj
        bpy.context.view_layer.objects.active = obj

        return {'FINISHED'}


def register():
    bpy.types.Object.wow_m2_geoset = bpy.props.PointerProperty(type=WowM2GeosetPropertyGroup)


def unregister():
    del bpy.types.Object.wow_m2_geoset

