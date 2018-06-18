import bpy


class WoWDoodadPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "WoW Doodad"

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        layout.prop(context.object.WoWDoodad, "Path")
        layout.prop(context.object.WoWDoodad, "Color")

        col = layout.column()
        col.label("Flags:")
        col.prop(context.object.WoWDoodad, "Flags")
        layout.enabled = context.object.WoWDoodad.Enabled

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.WowScene.Type == 'WMO'
                and context.object is not None
                and context.object.WoWDoodad.Enabled
                and isinstance(context.object.data, bpy.types.Mesh))


class WoWDoodadPropertyGroup(bpy.types.PropertyGroup):

    Path = bpy.props.StringProperty()

    Color = bpy.props.FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        size=4,
        default=(1,1,1,1),
        min=0.0,
        max=1.0
        )

    Flags = bpy.props.EnumProperty(
        name ="Doodad flags",
        description ="WoW doodad instance flags",
        items =[
                ("1" , "Accept Projected Tex.", ""),
                ("2", "Adjust lighting", ""),
                ("4", "Unknown", ""),
                ("8", "Unknown", "")],
        options={"ENUM_FLAG"}
        )

    Enabled = bpy.props.BoolProperty(
        name="",
        description="Enable WoW Doodad properties"
        )


def register():
    bpy.types.Object.WoWDoodad = bpy.props.PointerProperty(type=WoWDoodadPropertyGroup)


def unregister():
    bpy.types.Object.WoWDoodad = None
