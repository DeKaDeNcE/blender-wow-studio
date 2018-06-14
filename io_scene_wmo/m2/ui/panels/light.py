import bpy


class WowM2LightPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    bl_label = "M2 Light"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.object.data.WowM2Light, "Type")
        col.prop(context.object.data.WowM2Light, "AmbientColor")
        col.prop(context.object.data.WowM2Light, "AmbientIntensity")
        col.prop(context.object.data.WowM2Light, "DiffuseColor")
        col.prop(context.object.data.WowM2Light, "DiffuseIntensity")
        col.prop(context.object.data.WowM2Light, "AttenuationStart")
        col.prop(context.object.data.WowM2Light, "AttenuationEnd")
        col.prop(context.object.data.WowM2Light, "Enabled")

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.WowScene.Type == 'M2'
                and context.object is not None
                and context.object.type == 'LAMP')


def update_lamp_type(self, context):
    context.object.data.type = 'POINT' if int(context.object.data.WowM2Light.Type) else 'SPOT'


class WowM2LightPropertyGroup(bpy.types.PropertyGroup):
    Type = bpy.props.EnumProperty(
        name="Type",
        description="WoW  M2 light type",
        items=[('0', 'Directional', 'Login screen only'), ('1', 'Point', '')],
        default='1',
        update=update_lamp_type
    )

    AmbientColor = bpy.props.FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        default=(1, 1, 1),
        min=0.0,
        max=1.0
    )

    AmbientIntensity = bpy.props.FloatProperty(
        name="Ambient intensity",
        description="Ambient intensity of the light",
        default=1.0,
        min=0.0,
        max=1.0
    )

    DiffuseColor = bpy.props.FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        default=(1, 1, 1),
        min=0.0,
        max=1.0
    )

    DiffuseIntensity = bpy.props.FloatProperty(
        name="Diffuse intensity",
        description="Diffuse intensity of the light",
        default=1.0,
        min=0.0,
        max=1.0
    )

    AttenuationStart = bpy.props.FloatProperty(
        name="Attenuation start",
        description="Start of attenuation",
        min=0.0  # TODO: max / default?
    )

    AttenuationEnd = bpy.props.FloatProperty(
        name="Attenuation end",
        description="End of attenuation",
        min=0.0  # TODO: max / default?
    )

    Enabled = bpy.props.BoolProperty(
        name='Enabled',
        default=True
    )


def register():
    bpy.types.Lamp.WowM2Light = bpy.props.PointerProperty(type=WowM2LightPropertyGroup)


def unregister():
    del bpy.types.Lamp.WowM2Light
