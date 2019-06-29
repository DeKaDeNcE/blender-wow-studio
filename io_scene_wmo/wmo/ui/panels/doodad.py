import bpy
from .. import handlers


class WMO_PT_doodad(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "WMO Doodad"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.prop(context.object.wow_wmo_doodad, "path")
        layout.prop(context.object.wow_wmo_doodad, "color")

        col = layout.column()
        col.prop(context.object.wow_wmo_doodad, "flags")
        layout.enabled = context.object.wow_wmo_doodad.enabled

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
                and context.object is not None
                and context.object.wow_wmo_doodad.enabled
                and (context.object.type == 'MESH'
                     or context.object.type == 'EMPTY')
        )


def update_doodad_color(self, context):
    mesh = context.object.data

    handlers.depsgraph_lock = True
    for mat in mesh.materials:
        mat.node_tree.nodes['DoodadColor'].outputs[0].default_value = self.color

    handlers.depsgraph_lock = False

class WoWDoodadPropertyGroup(bpy.types.PropertyGroup):

    enabled:  bpy.props.BoolProperty()

    path:  bpy.props.StringProperty(name="Path")

    color:  bpy.props.FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        size=4,
        default=(1, 1, 1, 1),
        min=0.0,
        max=1.0,
        update=update_doodad_color
    )

    flags:  bpy.props.EnumProperty(
        name="Flags",
        description="WoW doodad instance flags",
        items=[("1", "Accept Projected Tex.", ""),
               ("2", "Adjust lighting", ""),
               ("4", "Unknown", ""),
               ("8", "Unknown", "")],
        options={"ENUM_FLAG"}
    )


def register():
    bpy.types.Object.wow_wmo_doodad = bpy.props.PointerProperty(type=WoWDoodadPropertyGroup)


def unregister():
    bpy.types.Object.wow_wmo_doodad = None
