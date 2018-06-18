import bpy
from ..enums import *


class WowWMOGroupPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "WoW WMO Group"

    def draw_header(self, context):
        self.layout.prop(context.object.WowWMOGroup, "Enabled")

    def draw(self, context):
        col = self.layout.column()
        col.prop(context.object.WowWMOGroup, "GroupDesc")

        col.separator()
        col.label("Flags:")
        col.prop(context.object.WowWMOGroup, "PlaceType")
        col.prop(context.object.WowWMOGroup, "Flags")

        col.separator()
        col.label("Fogs:")
        col.prop(context.object.WowWMOGroup, "Fog1")
        col.prop(context.object.WowWMOGroup, "Fog2")
        col.prop(context.object.WowWMOGroup, "Fog3")
        col.prop(context.object.WowWMOGroup, "Fog4")

        col.separator()
        col.prop(context.object.WowWMOGroup, "GroupDBCid")
        col.prop(context.object.WowWMOGroup, "LiquidType")

        self.layout.enabled = context.object.WowWMOGroup.Enabled

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.WowScene.Type == 'WMO'
                and context.object is not None
                and context.object.data is not None
                and isinstance(context.object.data,bpy.types.Mesh)
                and not context.object.WowPortalPlane.Enabled
                and not context.object.WowLiquid.Enabled
                and not context.object.WowFog.Enabled
                and not context.object.WoWDoodad.Enabled
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
    Portals = bpy.props.CollectionProperty(type=WowWMOPortalRel)
    Lights = bpy.props.CollectionProperty(type=WowWMOLightRel)
    Liquid = bpy.props.StringProperty()
    Doodads = bpy.props.CollectionProperty(type=WowWMODoodadRel)


def fog_validator(self, context):
    if self.Fog1 and (not self.Fog1.WowFog.Enabled or self.Fog1.name not in bpy.context.scene.objects):
        self.Fog1 = None

    if self.Fog2 and (not self.Fog2.WowFog.Enabled or self.Fog2.name not in bpy.context.scene.objects):
        self.Fog2 = None

    if self.Fog3 and (not self.Fog3.WowFog.Enabled or self.Fog3.name not in bpy.context.scene.objects):
        self.Fog3 = None

    if self.Fog4 and (not self.Fog4.WowFog.Enabled or self.Fog4.name not in bpy.context.scene.objects):
        self.Fog4 = None


class WowWMOGroupPropertyGroup(bpy.types.PropertyGroup):

    GroupDesc = bpy.props.StringProperty(name="Description")

    Enabled = bpy.props.BoolProperty(
        name="",
        description="Enable wow WMO group properties"
        )

    Flags = bpy.props.EnumProperty(
        items=group_flag_enum,
        options={'ENUM_FLAG'}
        )

    PlaceType = bpy.props.EnumProperty(
        items=place_type_enum,
        name="Place Type",
        description="Group is indoor or outdoor"
        )

    GroupID = bpy.props.IntProperty(
        name="",
        description="Group identifier used for export"
        )

    GroupDBCid = bpy.props.IntProperty(
        name="DBC Group ID",
        description="WMO Group ID in DBC file"
        )

    LiquidType = bpy.props.EnumProperty(
        items=liquid_type_enum,
        name="LiquidType",
        description="Fill this WMO group with selected liquid."
        )

    Fog1 = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Fog #1",
        poll=lambda self, obj: obj.WowFog.Enabled and obj.name in bpy.context.scene.objects,
        update=fog_validator
    )

    Fog2 = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Fog #2",
        poll=lambda self, obj: obj.WowFog.Enabled and obj.name in bpy.context.scene.objects,
        update=fog_validator
    )

    Fog3 = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Fog #3",
        poll=lambda self, obj: obj.WowFog.Enabled and obj.name in bpy.context.scene.objects,
        update=fog_validator
    )

    Fog4 = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Fog #4",
        poll=lambda self, obj: obj.WowFog.Enabled and obj.name in bpy.context.scene.objects,
        update=fog_validator
    )


    MODR = bpy.props.CollectionProperty(type=WowWMOMODRStore)


    Relations = bpy.props.PointerProperty(type=WowWMOGroupRelations)


def register():
    bpy.types.Object.WowWMOGroup = bpy.props.PointerProperty(type=WowWMOGroupPropertyGroup)


def unregister():
    bpy.types.Object.WowWMOGroup = None