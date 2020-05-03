import bpy
from ..enums import *
from ....utils.callbacks import on_release


class WMO_PT_root(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_label = "WMO Root"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

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


@on_release()
def update_flags(self, context):
    properties = bpy.data.node_groups.get('MO_Properties')
    if properties:
        properties.nodes['IsRenderPathUnified'].outputs[0].default_value = int('2' in self.flags)
        properties.nodes['DoNotFixColorVertexAlpha'].outputs[0].default_value = int('1' in self.flags)


@on_release()
def update_ambient_color(self, context):
    properties = bpy.data.node_groups.get('MO_Properties')
    if properties:
        properties.nodes['IntAmbientColor'].outputs[0].default_value = self.ambient_color


class WowRootPropertyGroup(bpy.types.PropertyGroup):


    flags:  bpy.props.EnumProperty(
        name="Root flags",
        description="WoW WMO root flags",
        items=root_flags_enum,
        options={"ENUM_FLAG"},
        update=update_flags
        )

    ambient_color:  bpy.props.FloatVectorProperty(
        name="Ambient Color",
        subtype='COLOR',
        default=(1, 1, 1, 1),
        size=4,
        min=0.0,
        max=1.0,
        update=update_ambient_color
        )

    skybox_path:  bpy.props.StringProperty(
        name="Skybox Path",
        description="Skybox for WMO (.MDX)",
        default='',
        )

    wmo_id:  bpy.props.IntProperty(
        name="DBC ID",
        description="Used in WMOAreaTable (optional)",
        default=0,
        )


def register():
    bpy.types.Scene.wow_wmo_root = bpy.props.PointerProperty(type=WowRootPropertyGroup)


def unregister():
    del bpy.types.Scene.wow_wmo_root

