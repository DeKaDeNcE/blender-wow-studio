import bpy


class WowM2LightPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    bl_label = "M2 Light"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.object.data.wow_m2_light, "type")
        col.prop(context.object.data.wow_m2_light, "ambient_color")
        col.prop(context.object.data.wow_m2_light, "ambient_intensity")
        col.prop(context.object.data.wow_m2_light, "diffuse_color")
        col.prop(context.object.data.wow_m2_light, "diffuse_intensity")
        col.prop(context.object.data.wow_m2_light, "attenuation_start")
        col.prop(context.object.data.wow_m2_light, "attenuation_end")
        col.prop(context.object.data.wow_m2_light, "visibility")

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.WowScene.type == 'M2'
                and context.object is not None
                and context.object.type == 'LAMP')


def update_lamp_type(self, context):
    context.object.data.type = 'POINT' if int(context.object.data.wow_m2_light.type) else 'SPOT'


class WowM2LightPropertyGroup(bpy.types.PropertyGroup):
    type = bpy.props.EnumProperty(
        name="type",
        description="WoW  M2 light type",
        items=[('0', 'Directional', 'Login screen only'), ('1', 'Point', '')],
        default='1',
        update=update_lamp_type
    )

    ambient_color = bpy.props.FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        default=(1, 1, 1),
        min=0.0,
        max=1.0
    )

    ambient_intensity = bpy.props.FloatProperty(
        name="Ambient intensity",
        description="Ambient intensity of the light",
        default=1.0,
        min=0.0,
        max=1.0
    )

    diffuse_color = bpy.props.FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        default=(1, 1, 1),
        min=0.0,
        max=1.0
    )

    diffuse_intensity = bpy.props.FloatProperty(
        name="Diffuse intensity",
        description="Diffuse intensity of the light",
        default=1.0,
        min=0.0,
        max=1.0
    )

    attenuation_start = bpy.props.FloatProperty(
        name="Attenuation start",
        description="Start of attenuation",
        min=0.0  # TODO: max / default?
    )

    attenuation_end = bpy.props.FloatProperty(
        name="Attenuation end",
        description="End of attenuation",
        min=0.0  # TODO: max / default?
    )

    visibility = bpy.props.BoolProperty(
        name='enabled',
        default=True
    )


def register():
    bpy.types.Lamp.wow_m2_light = bpy.props.PointerProperty(type=WowM2LightPropertyGroup)


def unregister():
    del bpy.types.Lamp.wow_m2_light
