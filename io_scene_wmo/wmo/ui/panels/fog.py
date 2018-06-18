import bpy


class WowFogPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "WoW Fog"

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        layout.enabled = context.object.WowFog.Enabled
        self.layout.prop(context.object.WowFog, "IgnoreRadius")
        self.layout.prop(context.object.WowFog, "Unknown")
        self.layout.prop(context.object.WowFog, "InnerRadius")
        self.layout.prop(context.object.WowFog, "EndDist")
        self.layout.prop(context.object.WowFog, "StartFactor")
        self.layout.prop(context.object.WowFog, "Color1")
        self.layout.prop(context.object.WowFog, "EndDist2")
        self.layout.prop(context.object.WowFog, "StartFactor2")
        self.layout.prop(context.object.WowFog, "Color2")

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.WowScene.Type == 'WMO'
                and context.object is not None
                and context.object.data is not None
                and isinstance(context.object.data,bpy.types.Mesh)
                and context.object.WowFog.Enabled
                )


def update_fog_color(self, context):
    bpy.context.scene.objects.active.color = (self.Color1[0], self.Color1[1], self.Color1[2], 0.5)


class WowFogPropertyGroup(bpy.types.PropertyGroup):

    Enabled = bpy.props.BoolProperty(
        name="",
        description="Enable WoW WMO fog properties"
        )

    FogID = bpy.props.IntProperty(
        name="WMO Group ID",
        description="Used internally for exporting",
        default= 0,
        )

    IgnoreRadius = bpy.props.BoolProperty(
        name="Ignore Radius",
        description="Ignore radius in CWorldView::QueryCameraFog",
        default = False
        )

    Unknown = bpy.props.BoolProperty(
        name="Unknown Flag",
        description="Check that in if you know what it is",
        default = False
        )

    InnerRadius = bpy.props.FloatProperty(
        name="Inner Radius (%)",
        description="A radius of fog starting to fade",
        default=100.0,
        min=0.0,
        max=100.0
        )

    EndDist = bpy.props.FloatProperty(
        name="Farclip",
        description="Fog farclip",
        default=70.0,
        min=0.0,
        max=2048.0
        )

    StartFactor = bpy.props.FloatProperty(
        name="Nearclip",
        description="Fog nearclip",
        default=0.1,
        min=0.0,
        max=1.0
        )

    Color1 = bpy.props.FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        default=(1,1,1),
        min=0.0,
        max=1.0,
        update=update_fog_color
        )

    EndDist2 = bpy.props.FloatProperty(
        name="Underwater farclip",
        description="Underwater fog farclip",
        default=70.0,
        min=0.0,
        max=250.0
        )

    StartFactor2 = bpy.props.FloatProperty(
        name="Underwater nearclip",
        description="Underwater fog nearclip",
        default=0.1,
        min=0.0,
        max=1.0
        )

    Color2 = bpy.props.FloatVectorProperty(
        name="Underwater Color",
        subtype='COLOR',
        default=(1,1,1),
        min=0.0,
        max=1.0
        )


def register():
    bpy.types.Object.WowFog = bpy.props.PointerProperty(type=WowFogPropertyGroup)


def unregister():
    bpy.types.Object.WowFog = None
