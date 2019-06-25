import bpy
from ..enums import *


class WMO_PT_liquid(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "WMO Liquid"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.object.wow_wmo_liquid, "liquid_type")
        layout.prop(context.object.wow_wmo_liquid, "color")
        layout.prop(context.object.wow_wmo_liquid, "wmo_group")

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
                and context.object is not None
                and context.object.data is not None
                and context.object.type == 'MESH'
                and context.object.wow_wmo_liquid.enabled
                )


def liquid_validator(self, context):
    if self.wmo_group and not self.wmo_group.wow_wmo_group.enabled:
        self.wmo_group = None


def liquid_poll(self, obj):
    if not obj.wow_wmo_group.enabled and obj.name in bpy.context.scene.objects:
        return False

    for ob in bpy.context.scene.objects:
        if ob.wow_wmo_liquid.enabled and ob.wow_wmo_liquid.wmo_group is obj:
            return False

    return True


class WowLiquidPropertyGroup(bpy.types.PropertyGroup):

    enabled:  bpy.props.BoolProperty()

    color:  bpy.props.FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        default=(0.08, 0.08, 0.08, 1),
        size=4,
        min=0.0,
        max=1.0
        )

    liquid_type:  bpy.props.EnumProperty(
        items=liquid_type_enum,
        name="Liquid Type",
        description="Type of the liquid present in this WMO group"
        )

    wmo_group:  bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="WMO Group",
        poll=liquid_poll,
        update=liquid_validator
    )


def register():
    bpy.types.Object.wow_wmo_liquid:  bpy.props.PointerProperty(type=WowLiquidPropertyGroup)


def unregister():
    del bpy.types.Object.wow_wmo_liquid
