import bpy
from ..enums import *


class M2_PT_attachment_panel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "M2 Attachment"

    def draw_header(self, context):
        self.layout.prop(context.object.wow_m2_attachment, "enabled", text="")

    def draw(self, context):
        layout = self.layout
        layout.enabled = context.object.wow_m2_attachment.enabled

        col = layout.column()
        col.prop(context.object.wow_m2_attachment, 'type', text="Type")
        col.prop(context.object.wow_m2_attachment, 'animate', text="Animate")

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'M2'
                and context.object is not None
                and context.object.type == 'EMPTY'
                and not (context.object.wow_m2_event.enabled
                         or context.object.wow_m2_uv_transform.enabled
                         or context.object.wow_m2_camera.enabled)
        )


class WowM2AttachmentPropertyGroup(bpy.types.PropertyGroup):

    enabled:  bpy.props.BoolProperty(
        name='Enabled',
        description='Enabled this object to be a WoW M2 attachment point',
        default=False
    )

    type:  bpy.props.EnumProperty(
        name="Type",
        description="WoW Attachment Type",
        items=get_attachment_types
    )

    animate:  bpy.props.BoolProperty(
        name='Animate',
        description='Animate attached object at this keyframe',
        default=True
    )


def register():
    bpy.types.Object.wow_m2_attachment:  bpy.props.PointerProperty(type=WowM2AttachmentPropertyGroup)


def unregister():
    del bpy.types.Object.wow_m2_attachment
