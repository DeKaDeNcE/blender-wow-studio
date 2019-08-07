import bpy
from ..enums import *
from ....utils.callbacks import delay_execution, on_release


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

        col.separator()
        col.label(text='Render settings', icon='RESTRICT_RENDER_OFF')
        col.prop(context.scene.wow_wmo_root, "ext_ambient_color")
        col.prop(context.scene.wow_wmo_root, "ext_dir_color")
        col.prop(context.scene.wow_wmo_root, "sidn_scalar")

        if context.scene.render.engine in ('CYCLES', 'BLENDER_EEVEE'):
            col.label(text='Sun Direciton:')
            col.prop(context.scene.wow_wmo_root, "sun_direction", text='')

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


@on_release()
def update_ext_ambient_color(self, context):
    properties = bpy.data.node_groups.get('MO_Properties')
    if properties:
        properties.nodes['extLightAmbientColor'].outputs[0].default_value = self.ext_ambient_color


@on_release()
def update_ext_dir_color(self, context):
    properties = bpy.data.node_groups.get('MO_Properties')
    if properties:
        properties.nodes['extLightDirColor'].outputs[0].default_value = self.ext_dir_color


@on_release()
def update_sidn_scalar(self, context):
    properties = bpy.data.node_groups.get('MO_Properties')
    if properties:
        properties.nodes['SIDNScalar'].outputs[0].default_value = self.sidn_scalar


@on_release()
def update_sun_direction(self, context):
    properties = bpy.data.node_groups.get('MO_Properties')
    if properties:
        properties.nodes['SunDirection'].inputs[1].default_value = self.sun_direction


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

    # render controls
    ext_ambient_color:  bpy.props.FloatVectorProperty(
        name="Ext. Ambient Color",
        subtype='COLOR',
        default=(0.138, 0.223, 0.323, 1),
        size=4,
        min=0.0,
        max=1.0,
        update=update_ext_ambient_color
        )

    ext_dir_color:  bpy.props.FloatVectorProperty(
        name="Ext. Dir Color",
        subtype='COLOR',
        default=(0.991, 0.246, 0, 1),
        size=4,
        min=0.0,
        max=1.0,
        update=update_ext_dir_color
    )

    sidn_scalar:  bpy.props.FloatProperty(
        name='SIDN intensity',
        description='Controls intensity of night glow in materials',
        min=0.0,
        max=1.0,
        update=update_sidn_scalar
    )

    sun_direction:  bpy.props.FloatVectorProperty(
        name='Sun Direction',
        description='Defines the direction of the sun',
        default=(0.2, 0.7, 0.6),
        size=3,
        subtype='DIRECTION',
        update=update_sun_direction
    )


def register():
    bpy.types.Scene.wow_wmo_root = bpy.props.PointerProperty(type=WowRootPropertyGroup)


def unregister():
    del bpy.types.Scene.wow_wmo_root

