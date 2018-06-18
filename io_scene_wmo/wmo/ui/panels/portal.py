import bpy
from ..enums import *


class WowPortalPlanePanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "WoW Portal Plane"

    def draw_header(self, context):
        layout = self.layout
        self.layout.prop(context.object.WowPortalPlane, "Enabled")

    def draw(self, context):
        layout = self.layout

        column = layout.column()
        column.prop(context.object.WowPortalPlane, "First")
        column.prop(context.object.WowPortalPlane, "Second")

        col = layout.column()

        col.separator()
        col.label("Relation direction:")
        col.prop(context.object.WowPortalPlane, "Algorithm", expand=True)

        layout.enabled = context.object.WowPortalPlane.Enabled

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.WowScene.Type == 'WMO'
                and context.object is not None
                and context.object.data is not None
                and isinstance(context.object.data,bpy.types.Mesh)
                and not context.object.WowWMOGroup.Enabled
                and not context.object.WowLiquid.Enabled
                and not context.object.WowFog.Enabled
                and not context.object.WoWDoodad.Enabled
                )


def portal_validator(self, context):
    if self.Second and not self.Second.WowWMOGroup.Enabled:
        self.Second = None

    if self.First and not self.First.WowWMOGroup.Enabled:
        self.First = None


class WowPortalPlanePropertyGroup(bpy.types.PropertyGroup):

    Enabled = bpy.props.BoolProperty(
        name="",
        description="Enable wow WMO group properties"
        )

    First = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="First group",
        poll=lambda self, obj: obj.WowWMOGroup.Enabled and self.Second != obj and obj.name in bpy.context.scene.objects,
        update=portal_validator
    )

    Second = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Second group",
        poll=lambda self, obj: obj.WowWMOGroup.Enabled and self.First != obj and obj.name in bpy.context.scene.objects,
        update=portal_validator
    )

    PortalID = bpy.props.IntProperty(
        name="Portal's ID",
        description="Portal ID"
        )

    Algorithm = bpy.props.EnumProperty(
        items=portal_dir_alg_enum,
        default="0"
        )


def register():
    bpy.types.Object.WowPortalPlane = bpy.props.PointerProperty(type=WowPortalPlanePropertyGroup)


def unregister():
    bpy.types.Object.WowPortalPlane = None