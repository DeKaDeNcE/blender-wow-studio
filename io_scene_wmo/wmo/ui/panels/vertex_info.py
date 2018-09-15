import bpy


class WowVertexInfoPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    bl_label = "WMO Vertex Info"

    def draw(self, context):
        self.layout.prop_search(context.object.wow_wmo_vertex_info, "vertex_group",
                                context.object, "vertex_groups", text="Collision vertex group"
                                )

        self.layout.prop(context.object.wow_wmo_vertex_info, "node_size", slider=True)
        self.layout.prop(context.object.wow_wmo_vertex_info, "has_batch_int")
        self.layout.prop(context.object.wow_wmo_vertex_info, "has_batch_trans")
        self.layout.prop(context.object.wow_wmo_vertex_info, "has_blend_map")

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
                and context.object is not None
                and context.object.data is not None
                and isinstance(context.object.data,bpy.types.Mesh)
                and context.object.wow_wmo_group.enabled
                )


def update_has_batch_int(self, context):
    if self.has_batch_int:
        context.object.pass_index |= 0x8
    else:
        context.object.pass_index &= ~0x8


def update_has_batch_trans(self, context):
    if self.has_batch_trans:
        context.object.pass_index |= 0x10
    else:
        context.object.pass_index &= ~0x10


def update_has_blend_map(self, context):
    if self.has_blend_map:
        context.object.pass_index |= 0x40
    else:
        context.object.pass_index &= ~0x40


class WowVertexInfoPropertyGroup(bpy.types.PropertyGroup):

    vertex_group = bpy.props.StringProperty()

    node_size = bpy.props.IntProperty(
        name="Node max size",
        description="Max count of faces for a node in bsp tree",
        default=2500, min=1,
        soft_max=5000
        )

    has_batch_int = bpy.props.BoolProperty(
        name='Use Interior Batches',
        default=False,
        update=update_has_batch_int
    )

    has_batch_trans = bpy.props.BoolProperty(
        name='Use Trans Batches',
        default=False,
        update=update_has_batch_trans
    )

    has_blend_map = bpy.props.BoolProperty(
        name='Has Blend Map',
        default=False,
        update=update_has_blend_map
    )


def register():
    bpy.types.Object.wow_wmo_vertex_info = bpy.props.PointerProperty(type=WowVertexInfoPropertyGroup)


def unregister():
    del bpy.types.Object.wow_wmo_vertex_info
