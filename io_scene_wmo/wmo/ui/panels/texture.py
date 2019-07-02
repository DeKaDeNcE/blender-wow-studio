import bpy


class WMO_PT_texture(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "image"
    bl_label = "WMO Texture"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        col = layout.column()
        col.prop(context.edit_image.wow_wmo_texture, "path")

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
                and context.image is not None
        )


class WowWMOTexturePropertyGroup(bpy.types.PropertyGroup):

    path:  bpy.props.StringProperty(
        name="Texture 1",
        description="Diffuse texture"
        )


def register():
    bpy.types.Image.wow_wmo_texture = bpy.props.PointerProperty(type=WowWMOTexturePropertyGroup)


def unregister():
    del bpy.types.Image.wow_wmo_texture
