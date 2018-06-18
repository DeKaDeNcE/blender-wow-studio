import bpy
from ..enums import *


class WoWRootPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_label = "WMO Root"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.scene.wow_wmo_root, "flags")
        col.separator()

        if "2" in context.scene.wow_wmo_root.flags:
            col.prop(context.scene.wow_wmo_root, "ambient_color")

        col.separator()

        col.prop(context.scene.wow_wmo_root, "skybox_path")
        col.prop(context.scene.wow_wmo_root, "wmo_id")

    @classmethod
    def poll(cls, context):
        return context.scene is not None and context.scene.wow_scene.type == 'WMO'


class MODS_Set(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty()
    start_doodad = bpy.props.IntProperty()
    n_doodads = bpy.props.IntProperty()
    padding = bpy.props.IntProperty()


class MODN_String(bpy.types.PropertyGroup):
    ofs = bpy.props.IntProperty()
    string = bpy.props.StringProperty()


class MODD_Definition(bpy.types.PropertyGroup):
    name_ofs = bpy.props.IntProperty()
    flags = bpy.props.IntProperty()
    position = bpy.props.FloatVectorProperty()
    rotation = bpy.props.FloatVectorProperty()
    tilt = bpy.props.FloatProperty()
    scale = bpy.props.FloatProperty()
    color = bpy.props.FloatVectorProperty()
    color_alpha = bpy.props.FloatProperty()


class WowRootPropertyGroup(bpy.types.PropertyGroup):

    mods_sets = bpy.props.CollectionProperty(type=MODS_Set)
    modn_string_table = bpy.props.CollectionProperty(type=MODN_String)
    modd_definitions = bpy.props.CollectionProperty(type=MODD_Definition)

    flags = bpy.props.EnumProperty(
        name="Root flags",
        description="WoW WMO root flags",
        items=root_flags_enum,
        options={"ENUM_FLAG"}
        )

    ambient_color = bpy.props.FloatVectorProperty(
        name="Ambient Color",
        subtype='COLOR',
        default=(1, 1, 1, 1),
        size=4,
        min=0.0,
        max=1.0
        )

    skybox_path = bpy.props.StringProperty(
        name="Skybox Path",
        description="Skybox for WMO (.MDX)",
        default='',
        )

    wmo_id = bpy.props.IntProperty(
        name="DBC ID",
        description="Used in WMOAreaTable (optional)",
        default=0,
        )


def register():
    bpy.types.Scene.wow_wmo_root = bpy.props.PointerProperty(type=WowRootPropertyGroup)


def unregister():
    del bpy.types.Scene.wow_wmo_root

