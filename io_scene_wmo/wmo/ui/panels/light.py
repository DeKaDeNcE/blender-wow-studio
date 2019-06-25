import bpy
from ..enums import *


class WMO_PT_light(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    bl_label = "WMO Light"

    def draw_header(self, context):
        row = self.layout.row()
        row.alignment = 'RIGHT'
        op = row.operator('scene.wow_wmo_destroy_wow_property', text='', icon='X', emboss=False)
        op.prop_group = 'wow_wmo_light'

        if bpy.context.scene.wow_wmo_root_components.lights.find(context.object.name) < 0:
            row.label(text='', icon='ERROR')

    def draw(self, context):
        self.layout.prop(context.object.wow_wmo_light, "light_type")
        self.layout.prop(context.object.wow_wmo_light, "use_attenuation")
        self.layout.prop(context.object.wow_wmo_light, "color")
        self.layout.prop(context.object.wow_wmo_light, "intensity")
        self.layout.prop(context.object.wow_wmo_light, "attenuation_start")
        self.layout.prop(context.object.wow_wmo_light, "attenuation_end")

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
                and context.object is not None
                and context.object.data is not None
                and context.object.type == 'LAMP'
                and context.object.wow_wmo_light.enabled
                )


class WowLightPropertyGroup(bpy.types.PropertyGroup):

    enabled:  bpy.props.BoolProperty()

    light_type:  bpy.props.EnumProperty(
        items=light_type_enum,
        name="Type",
        description="Type of the lamp"
        )

    type:  bpy.props.BoolProperty(
        name="Type",
        description="Unknown"
        )

    use_attenuation:  bpy.props.BoolProperty(
        name="Use attenuation",
        description="True if lamp use attenuation"
        )

    padding:  bpy.props.BoolProperty(
        name="Padding",
        description="True if lamp use padding"
        )

    color:  bpy.props.FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        default=(1, 1, 1),
        min=0.0,
        max=1.0
        )

    intensity:  bpy.props.FloatProperty(
        name="Intensity",
        description="Intensity of the lamp"
        )

    color_alpha:  bpy.props.FloatProperty(
        name="ColorAlpha",
        description="Color alpha",
        default=1,
        min=0.0,
        max=1.0
        )

    attenuation_start:  bpy.props.FloatProperty(
        name="Attenuation start",
        description="Distance at which light intensity starts to decrease"
        )

    attenuation_end:  bpy.props.FloatProperty(
        name="Attenuation end",
        description="Distance at which light intensity reach 0"
        )


def register():
    bpy.types.Object.wow_wmo_light = bpy.props.PointerProperty(type=WowLightPropertyGroup)


def unregister():
    del bpy.types.Object.wow_wmo_light


