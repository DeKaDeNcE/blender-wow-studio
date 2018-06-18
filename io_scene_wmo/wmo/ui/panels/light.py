import bpy
from ..enums import *


class WowLightPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    bl_label = "WMO Light"

    def draw_header(self, context):
        self.layout.prop(context.object.data.wow_wmo_light, "enabled")

    def draw(self, context):
        layout = self.layout
        self.layout.prop(context.object.data.wow_wmo_light, "light_type")
        self.layout.prop(context.object.data.wow_wmo_light, "use_attenuation")
        self.layout.prop(context.object.data.wow_wmo_light, "color")
        self.layout.prop(context.object.data.wow_wmo_light, "intensity")
        self.layout.prop(context.object.data.wow_wmo_light, "attenuation_start")
        self.layout.prop(context.object.data.wow_wmo_light, "attenuation_end")
        layout.enabled = context.object.data.wow_wmo_light.enabled

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
                and context.object is not None
                and context.object.data is not None
                and isinstance(context.object.data, bpy.types.Lamp)
                )


class WowLightPropertyGroup(bpy.types.PropertyGroup):

    enabled = bpy.props.BoolProperty(
        name="",
        description="Enable wow light properties"
        )

    light_type = bpy.props.EnumProperty(
        items=light_type_enum,
        name="Type",
        description="Type of the lamp"
        )

    type = bpy.props.BoolProperty(
        name="Type",
        description="Unknown"
        )

    use_attenuation = bpy.props.BoolProperty(
        name="Use attenuation",
        description="True if lamp use attenuation"
        )

    padding = bpy.props.BoolProperty(
        name="Padding",
        description="True if lamp use padding"
        )

    color = bpy.props.FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        default=(1, 1, 1),
        min=0.0,
        max=1.0
        )

    intensity = bpy.props.FloatProperty(
        name="Intensity",
        description="Intensity of the lamp"
        )

    color_alpha = bpy.props.FloatProperty(
        name="ColorAlpha",
        description="Color alpha",
        default=1,
        min=0.0,
        max=1.0
        )

    attenuation_start = bpy.props.FloatProperty(
        name="Attenuation start",
        description="Distance at which light intensity starts to decrease"
        )

    attenuation_end = bpy.props.FloatProperty(
        name="Attenuation end",
        description="Distance at which light intensity reach 0"
        )


def register():
    bpy.types.Lamp.wow_wmo_light = bpy.props.PointerProperty(type=WowLightPropertyGroup)


def unregister():
    del bpy.types.Lamp.wow_wmo_light


