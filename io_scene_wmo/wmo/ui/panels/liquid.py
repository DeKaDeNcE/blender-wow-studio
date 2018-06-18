import bpy
from ..enums import *


class WowLiquidPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "WoW Liquid"

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        self.layout.prop(context.object.WowLiquid, "LiquidType")
        self.layout.prop(context.object.WowLiquid, "Color")
        self.layout.prop(context.object.WowLiquid, "WMOGroup")

        layout.enabled = context.object.WowLiquid.Enabled

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.WowScene.Type == 'WMO'
                and context.object is not None
                and context.object.data is not None
                and isinstance(context.object.data,bpy.types.Mesh)
                and context.object.WowLiquid.Enabled
                )


def liquid_validator(self, context):
    if self.WMOGroup and not self.WMOGroup.WowWMOGroup.Enabled:
        self.WMOGroup = None


def liquid_poll(self, obj):
    if not obj.WowWMOGroup.Enabled and obj.name in bpy.context.scene.objects:
        return False

    for ob in bpy.context.scene.objects:
        if ob.WowLiquid.Enabled and ob.WowLiquid.WMOGroup is obj:
            return False

    return True


class WowLiquidPropertyGroup(bpy.types.PropertyGroup):

    Enabled = bpy.props.BoolProperty(
        name="",
        description="Enable wow liquid properties",
        default=False
        )

    Color = bpy.props.FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        default=(0.08, 0.08, 0.08, 1),
        size=4,
        min=0.0,
        max=1.0
        )

    LiquidType = bpy.props.EnumProperty(
        items=liquid_type_enum,
        name="Liquid Type",
        description="Type of the liquid present in this WMO group"
        )

    WMOGroup = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="WMO Group",
        poll=liquid_poll,
        update=liquid_validator
    )


def register():
    bpy.types.Object.WowLiquid = bpy.props.PointerProperty(type=WowLiquidPropertyGroup)


def unregister():
    bpy.types.Object.WowLiquid = None