import bpy
from ..enums import *


class WoWRootPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_label = "WoW Root"

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.scene.WoWRoot, "Flags")
        col.separator()

        if "2" in context.scene.WoWRoot.Flags:
            col.prop(context.scene.WoWRoot, "AmbientColor")

        col.separator()

        col.prop(context.scene.WoWRoot, "SkyboxPath")
        col.prop(context.scene.WoWRoot, "WMOid")

    @classmethod
    def poll(cls, context):
        return context.scene is not None and context.scene.WowScene.Type == 'WMO'


class MODS_Set(bpy.types.PropertyGroup):
    Name = bpy.props.StringProperty()
    StartDoodad = bpy.props.IntProperty()
    nDoodads = bpy.props.IntProperty()
    Padding = bpy.props.IntProperty()


class MODN_String(bpy.types.PropertyGroup):
    Ofs = bpy.props.IntProperty()
    String = bpy.props.StringProperty()


class MODD_Definition(bpy.types.PropertyGroup):
    NameOfs = bpy.props.IntProperty()
    Flags = bpy.props.IntProperty()
    Position = bpy.props.FloatVectorProperty()
    Rotation = bpy.props.FloatVectorProperty()
    Tilt = bpy.props.FloatProperty()
    Scale = bpy.props.FloatProperty()
    Color = bpy.props.FloatVectorProperty()
    ColorAlpha = bpy.props.FloatProperty()


class WowRootPropertyGroup(bpy.types.PropertyGroup):

    MODS_Sets = bpy.props.CollectionProperty(type=MODS_Set)
    MODN_StringTable = bpy.props.CollectionProperty(type=MODN_String)
    MODD_Definitions = bpy.props.CollectionProperty(type=MODD_Definition)

    Flags = bpy.props.EnumProperty(
        name="Root flags",
        description="WoW WMO root flags",
        items=root_flags_enum,
        options={"ENUM_FLAG"}
        )

    AmbientColor = bpy.props.FloatVectorProperty(
        name="Ambient Color",
        subtype='COLOR',
        default=(1, 1, 1, 1),
        size=4,
        min=0.0,
        max=1.0
        )

    SkyboxPath = bpy.props.StringProperty(
        name="SkyboxPath",
        description="Skybox for WMO (.MDX)",
        default='',
        )

    WMOid = bpy.props.IntProperty(
        name="WMO DBC ID",
        description="Used in WMOAreaTable (optional)",
        default=0,
        )


def register():
    bpy.types.Scene.WoWRoot = bpy.props.PointerProperty(type=WowRootPropertyGroup)


def unregister():
    bpy.types.Scene.WoWRoot = None