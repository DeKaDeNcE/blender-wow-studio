import bpy


class WMO_PT_doodad(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "WMO Doodad"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.object.wow_wmo_doodad, "path")
        layout.prop(context.object, "color")

        col = layout.column()
        col.label("Flags:")
        col.prop(context.object.wow_wmo_doodad, "flags")
        layout.enabled = context.object.wow_wmo_doodad.enabled

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
                and context.object is not None
                and context.object.wow_wmo_doodad.enabled
                and context.object.data.library is not None
                and (context.object.type == 'MESH'
                     or context.object.type == 'EMPTY')
        )


class WoWDoodadPropertyGroup(bpy.types.PropertyGroup):

    enabled:  bpy.props.BoolProperty()

    path:  bpy.props.StringProperty()

    color:  bpy.props.FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        size=4,
        default=(1, 1, 1, 1),
        min=0.0,
        max=1.0
    )

    flags:  bpy.props.EnumProperty(
        name="Doodad flags",
        description="WoW doodad instance flags",
        items=[("1", "Accept Projected Tex.", ""),
               ("2", "Adjust lighting", ""),
               ("4", "Unknown", ""),
               ("8", "Unknown", "")],
        options={"ENUM_FLAG"}
    )


def register():
    bpy.types.Object.wow_wmo_doodad:  bpy.props.PointerProperty(type=WoWDoodadPropertyGroup)


def unregister():
    bpy.types.Object.wow_wmo_doodad = None
