import bpy
from ..enums import *


class M2_PT_texture_panel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "image"
    bl_label = "M2 Texture"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.edit_image.wow_m2_texture, "flags")
        col.separator()
        col.prop(context.edit_image.wow_m2_texture, "texture_type")
        col.separator()
        col.prop(context.edit_image.wow_m2_texture, "path", text='Path')

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'M2'
                and context.image is not None)


class WowM2TexturePropertyGroup(bpy.types.PropertyGroup):

    flags:  bpy.props.EnumProperty(
        name="Texture flags",
        description="WoW  M2 texture flags",
        items=TEXTURE_FLAGS,
        options={"ENUM_FLAG"},
        default={'1', '2'}
        )

    texture_type:  bpy.props.EnumProperty(
        name="Texture type",
        description="WoW  M2 texture type",
        items=TEXTURE_TYPES
        )

    path:  bpy.props.StringProperty(
        name='Path',
        description='Path to .blp file in wow file system.'
    )

def register():
    bpy.types.Image.wow_m2_texture = bpy.props.PointerProperty(type=WowM2TexturePropertyGroup)


def unregister():
    del bpy.types.Image.wow_m2_texture
