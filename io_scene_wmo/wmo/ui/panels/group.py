import bpy
from ..enums import *


class WowWMOGroupPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "WMO Group"

    def draw_header(self, context):
        self.layout.prop(context.object.wow_wmo_group, "enabled")

    def draw(self, context):
        col = self.layout.column()
        col.prop(context.object.wow_wmo_group, "description")

        col.separator()
        col.label("Flags:")
        col.prop(context.object.wow_wmo_group, "place_type")
        col.prop(context.object.wow_wmo_group, "flags")

        col.separator()
        col.label("Fogs:")
        col.prop(context.object.wow_wmo_group, "fog1")
        col.prop(context.object.wow_wmo_group, "fog2")
        col.prop(context.object.wow_wmo_group, "fog3")
        col.prop(context.object.wow_wmo_group, "fog4")

        col.separator()
        col.prop(context.object.wow_wmo_group, "group_dbc_id")
        col.prop(context.object.wow_wmo_group, "liquid_type")

        self.layout.enabled = context.object.wow_wmo_group.enabled

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
                and context.object is not None
                and context.object.data is not None
                and isinstance(context.object.data,bpy.types.Mesh)
                and not context.object.wow_wmo_portal.enabled
                and not context.object.wow_wmo_liquid.enabled
                and not context.object.wow_wmo_fog.enabled
                and not context.object.wow_wmo_doodad.enabled
                )


class WowWMOMODRStore(bpy.types.PropertyGroup):
    value = bpy.props.IntProperty(name="Doodads Ref")


class WowWMOPortalRel(bpy.types.PropertyGroup):
    id = bpy.props.StringProperty()


class WowWMOLightRel(bpy.types.PropertyGroup):
    id = bpy.props.IntProperty()


class WowWMODoodadRel(bpy.types.PropertyGroup):
    id = bpy.props.IntProperty()


class WowWMOGroupRelations(bpy.types.PropertyGroup):
    """Used for export internally"""
    portals = bpy.props.CollectionProperty(type=WowWMOPortalRel)
    liqhts = bpy.props.CollectionProperty(type=WowWMOLightRel)
    liquid = bpy.props.StringProperty()
    doodads = bpy.props.CollectionProperty(type=WowWMODoodadRel)


def fog_validator(self, context):
    if self.fog1 and (not self.fog1.wow_wmo_fog.enabled or self.fog1.name not in bpy.context.scene.objects):
        self.fog1 = None

    if self.fog2 and (not self.fog2.wow_wmo_fog.enabled or self.fog2.name not in bpy.context.scene.objects):
        self.fog2 = None

    if self.fog3 and (not self.fog3.wow_wmo_fog.enabled or self.fog3.name not in bpy.context.scene.objects):
        self.fog3 = None

    if self.fog4 and (not self.fog4.wow_wmo_fog.enabled or self.fog4.name not in bpy.context.scene.objects):
        self.fog4 = None


class WowWMOGroupPropertyGroup(bpy.types.PropertyGroup):

    description = bpy.props.StringProperty(name="Description")

    enabled = bpy.props.BoolProperty(
        name="",
        description="Enable wow WMO group properties"
        )

    flags = bpy.props.EnumProperty(
        items=group_flag_enum,
        options={'ENUM_FLAG'}
        )

    place_type = bpy.props.EnumProperty(
        items=place_type_enum,
        name="Place Type",
        description="Group is indoor or outdoor"
        )

    group_id = bpy.props.IntProperty(
        name="",
        description="Group identifier used for export"
        )

    group_dbc_id = bpy.props.IntProperty(
        name="DBC Group ID",
        description="WMO Group ID in DBC file"
        )

    liquid_type = bpy.props.EnumProperty(
        items=liquid_type_enum,
        name="LiquidType",
        description="Fill this WMO group with selected liquid."
        )

    fog1 = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Fog #1",
        poll=lambda self, obj: obj.wow_wmo_fog.enabled and obj.name in bpy.context.scene.objects,
        update=fog_validator
    )

    fog2 = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Fog #2",
        poll=lambda self, obj: obj.wow_wmo_fog.enabled and obj.name in bpy.context.scene.objects,
        update=fog_validator
    )

    fog3 = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Fog #3",
        poll=lambda self, obj: obj.wow_wmo_fog.enabled and obj.name in bpy.context.scene.objects,
        update=fog_validator
    )

    fog4 = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Fog #4",
        poll=lambda self, obj: obj.wow_wmo_fog.enabled and obj.name in bpy.context.scene.objects,
        update=fog_validator
    )

    modr = bpy.props.CollectionProperty(type=WowWMOMODRStore)

    relations = bpy.props.PointerProperty(type=WowWMOGroupRelations)


def register():
    bpy.types.Object.wow_wmo_group = bpy.props.PointerProperty(type=WowWMOGroupPropertyGroup)


def unregister():
    del bpy.types.Object.wow_wmo_group
