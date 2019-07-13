import bpy
from ..enums import *


class M2_PT_event_panel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "M2 Event"

    def draw_header(self, context):
        self.layout.prop(context.object.wow_m2_event, "enabled", text="")

    def draw(self, context):
        layout = self.layout
        layout.enabled = context.object.wow_m2_event.enabled

        col = layout.column()
        col.prop(context.object.wow_m2_event, 'token')
        col.prop(context.object.wow_m2_event, 'enabled')

        event_name = M2EventTokens.get_event_name(context.object.wow_m2_event.token)
        if event_name in ('PlayEmoteSound', 'DoodadSoundUnknown', 'DoodadSoundOneShot', 'GOPlaySoundKitCustom'):
            col.label(text='SoundEntryID')
            col.prop(context.object.wow_m2_event, 'data')
        elif event_name == 'GOAddShake':
            col.label(text='SpellEffectCameraShakesID')
            col.prop(context.object.wow_m2_event, 'data')

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'M2'
                and context.object is not None
                and context.object.type == 'EMPTY'
                and not (context.object.wow_m2_attachment.enabled
                         or context.object.wow_m2_uv_transform.enabled
                         or context.object.wow_m2_camera.enabled)
        )


class WowM2EventPropertyGroup(bpy.types.PropertyGroup):

    enabled:  bpy.props.BoolProperty(
        name='Enabled',
        description='Enabled this object to be a WoW M2 event',
        default=False
    )

    token:  bpy.props.EnumProperty(
        name='Token',
        description='This token defines the purpose of the event',
        items=get_event_names
    )

    data:  bpy.props.IntProperty(
        name='Data',
        description='Data passed when this event is fired',
        min=0
    )

    fire:  bpy.props.BoolProperty(
        name='Enabled',
        description='Enable this event in this specific animation keyframe',
        default=False
    )


def register():
    bpy.types.Object.wow_m2_event = bpy.props.PointerProperty(type=WowM2EventPropertyGroup)


def unregister():
    del bpy.types.Object.wow_m2_event
