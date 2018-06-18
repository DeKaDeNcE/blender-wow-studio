import bpy
from ..enums import *


class WowLightPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    bl_label = "WoW light"

    def draw_header(self, context):
        self.layout.prop(context.object.data.WowLight, "Enabled")

    def draw(self, context):
        layout = self.layout
        self.layout.prop(context.object.data.WowLight, "LightType")
        self.layout.prop(context.object.data.WowLight, "UseAttenuation")
        self.layout.prop(context.object.data.WowLight, "Color")
        self.layout.prop(context.object.data.WowLight, "Intensity")
        self.layout.prop(context.object.data.WowLight, "AttenuationStart")
        self.layout.prop(context.object.data.WowLight, "AttenuationEnd")
        layout.enabled = context.object.data.WowLight.Enabled

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.WowScene.Type == 'WMO'
                and context.object is not None
                and context.object.data is not None
                and isinstance(context.object.data, bpy.types.Lamp)
                )


class WowLightPropertyGroup(bpy.types.PropertyGroup):

    Enabled = bpy.props.BoolProperty(
        name="",
        description="Enable wow light properties"
        )

    LightType = bpy.props.EnumProperty(
        items=light_type_enum,
        name="Type",
        description="Type of the lamp"
        )

    Type = bpy.props.BoolProperty(
        name="Type",
        description="Unknown"
        )

    UseAttenuation = bpy.props.BoolProperty(
        name="Use attenuation",
        description="True if lamp use attenuation"
        )

    Padding = bpy.props.BoolProperty(
        name="Padding",
        description="True if lamp use Padding"
        )

    Color = bpy.props.FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        default=(1, 1, 1),
        min=0.0,
        max=1.0
        )

    Intensity = bpy.props.FloatProperty(
        name="Intensity",
        description="Intensity of the lamp"
        )

    ColorAlpha = bpy.props.FloatProperty(
        name="ColorAlpha",
        description="Color alpha",
        default=1,
        min=0.0,
        max=1.0
        )

    AttenuationStart = bpy.props.FloatProperty(
        name="Attenuation start",
        description="Distance at which light intensity starts to decrease"
        )

    AttenuationEnd = bpy.props.FloatProperty(
        name="Attenuation end",
        description="Distance at which light intensity reach 0"
        )


def register():
    bpy.types.Lamp.WowLight = bpy.props.PointerProperty(type=WowLightPropertyGroup)


def unregister():
    bpy.types.Lamp.WowLight = None

