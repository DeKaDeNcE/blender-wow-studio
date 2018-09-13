import bpy


class WowFogPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "WMO Fog"

    def draw(self, context):
        layout = self.layout
        layout.enabled = context.object.wow_wmo_fog.enabled

        self.layout.prop(context.object.wow_wmo_fog, "ignore_radius")
        self.layout.prop(context.object.wow_wmo_fog, "unknown")
        self.layout.prop(context.object.wow_wmo_fog, "inner_radius")
        self.layout.prop(context.object.wow_wmo_fog, "end_dist")
        self.layout.prop(context.object.wow_wmo_fog, "start_factor")
        self.layout.prop(context.object.wow_wmo_fog, "color1")
        self.layout.prop(context.object.wow_wmo_fog, "end_dist2")
        self.layout.prop(context.object.wow_wmo_fog, "start_factor2")
        self.layout.prop(context.object.wow_wmo_fog, "color2")

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
                and context.object is not None
                and context.object.data is not None
                and isinstance(context.object.data,bpy.types.Mesh)
                and context.object.wow_wmo_fog.enabled
                )


def update_fog_color(self, context):
    bpy.context.scene.objects.active.color = (self.color1[0], self.color1[1], self.color1[2], 0.5)


def update_wmo_fog_enabled(self, context):
    if self.enabled:

        # check if is already added for safety
        for link in context.scene.wow_wmo_root_components.fogs:
            if link.pointer == context.object:
                return

        slot = context.scene.wow_wmo_root_components.fogs.add()
        slot.pointer = context.object

    else:

        for i, link in enumerate(context.scene.wow_wmo_root_components.fogs):
            if link.pointer == context.object:
                context.scene.wow_wmo_root_components.is_update_critical = True
                context.scene.wow_wmo_root_components.fogs.remove(i)


class WowFogPropertyGroup(bpy.types.PropertyGroup):

    enabled = bpy.props.BoolProperty(
        name="",
        description="Enable WoW WMO fog properties",
        update=update_wmo_fog_enabled
    )

    fog_id = bpy.props.IntProperty(
        name="WMO Group ID",
        description="Used internally for exporting",
        default=0,
    )

    ignore_radius = bpy.props.BoolProperty(
        name="Ignore Radius",
        description="Ignore radius in CWorldView::QueryCameraFog",
        default=False
    )

    unknown = bpy.props.BoolProperty(
        name="Unknown Flag",
        description="Check that in if you know what it is",
        default=False
    )

    inner_radius = bpy.props.FloatProperty(
        name="Inner Radius (%)",
        description="A radius of fog starting to fade",
        default=100.0,
        min=0.0,
        max=100.0
    )

    end_dist = bpy.props.FloatProperty(
        name="Farclip",
        description="Fog farclip",
        default=70.0,
        min=0.0,
        max=2048.0
    )

    start_factor = bpy.props.FloatProperty(
        name="Nearclip",
        description="Fog nearclip",
        default=0.1,
        min=0.0,
        max=1.0
    )

    color1 = bpy.props.FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        default=(1, 1, 1),
        min=0.0,
        max=1.0,
        update=update_fog_color
    )

    end_dist2 = bpy.props.FloatProperty(
        name="Underwater farclip",
        description="Underwater fog farclip",
        default=70.0,
        min=0.0,
        max=250.0
    )

    start_factor2 = bpy.props.FloatProperty(
        name="Underwater nearclip",
        description="Underwater fog nearclip",
        default=0.1,
        min=0.0,
        max=1.0
    )

    color2 = bpy.props.FloatVectorProperty(
        name="Underwater Color",
        subtype='COLOR',
        default=(1, 1, 1),
        min=0.0,
        max=1.0
    )


def register():
    bpy.types.Object.wow_wmo_fog = bpy.props.PointerProperty(type=WowFogPropertyGroup)


def unregister():
    del bpy.types.Object.wow_wmo_fog
