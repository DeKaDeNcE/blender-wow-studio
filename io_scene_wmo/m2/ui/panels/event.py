import bpy
from ..enums import *


class WowM2EventPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "M2 Event"

    def draw_header(self, context):
        self.layout.prop(context.object.wow_m2_event, "Enabled", text="")

    def draw(self, context):
        layout = self.layout
        layout.enabled = context.object.wow_m2_event.Enabled

        col = layout.column()
        col.prop(context.object.wow_m2_event, 'Token')
        col.prop(context.object.wow_m2_event, 'Enabled')

        event_name = M2EventTokens.get_event_name(context.object.wow_m2_event.Token)
        if event_name in ('PlayEmoteSound', 'DoodadSoundUnknown', 'DoodadSoundOneShot', 'GOPlaySoundKitCustom'):
            col.label(text='SoundEntryID')
            col.prop(context.object.wow_m2_event, 'Data')
        elif event_name == 'GOAddShake':
            col.label(text='SpellEffectCameraShakesID')
            col.prop(context.object.wow_m2_event, 'Data')

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.WowScene.Type == 'M2'
                and context.object is not None
                and context.object.type == 'EMPTY'
                and not (context.object.wow_m2_attachment.Enabled
                         or context.object.wow_m2_uv_transform.Enabled
                         or context.object.wow_m2_camera.enabled)
        )


class WowM2EventPropertyGroup(bpy.types.PropertyGroup):

    Enabled = bpy.props.BoolProperty(
        name='Enabled',
        description='Enabled this object to be a WoW M2 event',
        default=False
    )

    Token = bpy.props.EnumProperty(
        name='Token',
        description='This token defines the purpose of the event',
        items=get_event_names
    )

    Data = bpy.props.IntProperty(
        name='Data',
        description='Data passed when this event is fired',
        min=0
    )

    Fire = bpy.props.BoolProperty(
        name='Enabled',
        description='Enable this event in this specific animation keyframe',
        default=False
    )


def register():
    bpy.types.Object.wow_m2_event = bpy.props.PointerProperty(type=WowM2EventPropertyGroup)


def unregister():
    del bpy.types.Object.wow_m2_event
