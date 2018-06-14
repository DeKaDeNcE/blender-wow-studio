import bpy


class WowM2TextureTransformControllerPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "M2 Texture Transform"

    def draw_header(self, context):
        self.layout.prop(context.object.wow_m2_uv_transform, "enabled", text="")

    def draw(self, context):
        pass

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.WowScene.Type == 'M2'
                and context.object is not None
                and context.object.type == 'EMPTY'
                and not (context.object.wow_m2_event.enabled
                         or context.object.wow_m2_attachment.enabled
                         or context.object.wow_m2_camera.enabled)
        )


class WowM2TextureTransformControllerPropertyGroup(bpy.types.PropertyGroup):

    enabled = bpy.props.BoolProperty(
        name='Enabled',
        description='Enable this object to be WoW M2 texture transform controller',
        default=False
    )


def register():
    bpy.types.Object.wow_m2_uv_transform = bpy.props.PointerProperty(type=WowM2TextureTransformControllerPropertyGroup)


def unregister():
    del bpy.types.Object.wow_m2_uv_transform
