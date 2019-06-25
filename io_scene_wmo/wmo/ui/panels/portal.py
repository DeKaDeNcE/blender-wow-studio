import bpy
from ..enums import *


class WMO_PT_portal(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "WMO Portal"

    def draw_header(self, context):
        row = self.layout.row()
        row.alignment = 'RIGHT'
        op = row.operator('scene.wow_wmo_destroy_wow_property', text='', icon='X', emboss=False)
        op.prop_group = 'wow_wmo_portal'

        if bpy.context.scene.wow_wmo_root_components.portals.find(context.object.name) < 0:
            row.label(text='', icon='ERROR')

    def draw(self, context):
        layout = self.layout

        column = layout.column()
        column.prop(context.object.wow_wmo_portal, "first")
        column.prop(context.object.wow_wmo_portal, "second")

        col = layout.column()

        col.separator()
        col.label(text="Relation direction:")
        col.prop(context.object.wow_wmo_portal, "algorithm", expand=True)

        layout.enabled = context.object.wowF_wmo_portal.enabled

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
                and context.object is not None
                and context.object.data is not None
                and context.object.type == 'MESH'
                and context.object.wow_wmo_portal.enabled
                )


def portal_validator(self, context):
    if self.second and not self.second.wow_wmo_group.enabled:
        self.second = None

    if self.first and not self.first.wow_wmo_group.enabled:
        self.first = None


class WowPortalPlanePropertyGroup(bpy.types.PropertyGroup):

    enabled:  bpy.props.BoolProperty()

    first:  bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="First group",
        poll=lambda self, obj: obj.wow_wmo_group.enabled and self.Second != obj and obj.name in bpy.context.scene.objects,
        update=portal_validator
    )

    second:  bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Second group",
        poll=lambda self, obj: obj.wow_wmo_group.enabled and self.First != obj and obj.name in bpy.context.scene.objects,
        update=portal_validator
    )

    portal_id:  bpy.props.IntProperty(
        name="Portal's ID",
        description="Portal ID"
        )

    algorithm:  bpy.props.EnumProperty(
        items=portal_dir_alg_enum,
        default="0"
        )


def register():
    bpy.types.Object.wow_wmo_portal = bpy.props.PointerProperty(type=WowPortalPlanePropertyGroup)


def unregister():
    del bpy.types.Object.wow_wmo_portal

