import bpy


class WMO_PT_liquid(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "WMO Liquid"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        layout.prop(context.object.wow_wmo_liquid, "color")

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
                and context.object is not None
                and context.object.data is not None
                and context.object.type == 'MESH'
                and context.object.wow_wmo_liquid.enabled
                )


class WowLiquidPropertyGroup(bpy.types.PropertyGroup):

    enabled:  bpy.props.BoolProperty()

    color:  bpy.props.FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        default=(0.08, 0.08, 0.08, 1),
        size=4,
        min=0.0,
        max=1.0
        )



def register():
    bpy.types.Object.wow_wmo_liquid = bpy.props.PointerProperty(type=WowLiquidPropertyGroup)


def unregister():
    del bpy.types.Object.wow_wmo_liquid
