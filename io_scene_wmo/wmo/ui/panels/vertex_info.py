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

        self.layout.prop_search(context.object.wow_wmo_vertex_info, "batch_type_a", context.object,
                                "vertex_groups", text="Batch type A vertex group"
                                )

        self.layout.prop_search(context.object.wow_wmo_vertex_info, "batch_type_b",
                                context.object, "vertex_groups", text="Batch type B vertex group"
                                )

        self.layout.prop_search(context.object.wow_wmo_vertex_info, "lightmap",
                                context.object, "vertex_groups", text="Lightmap"
                                )

        self.layout.prop_search(context.object.wow_wmo_vertex_info, "blendmap", context.object,
                                "vertex_groups", text="Blendmap"
                                )

        self.layout.prop_search(context.object.wow_wmo_vertex_info, "second_uv", context.object.data,
                                "uv_textures", text="Second UV"
                                )

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
                and context.object is not None
                and context.object.data is not None
                and isinstance(context.object.data,bpy.types.Mesh)
                and context.object.wow_wmo_group.enabled
                )


class WowVertexInfoPropertyGroup(bpy.types.PropertyGroup):

    vertex_group = bpy.props.StringProperty()

    node_size = bpy.props.IntProperty(
        name="Node max size",
        description="Max count of faces for a node in bsp tree",
        default=2500, min=1,
        soft_max=5000
        )

    batch_type_a = bpy.props.StringProperty()
    batch_type_b = bpy.props.StringProperty()
    lightmap = bpy.props.StringProperty()
    blendmap = bpy.props.StringProperty()
    second_uv = bpy.props.StringProperty()


def register():
    bpy.types.Object.wow_wmo_vertex_info = bpy.props.PointerProperty(type=WowVertexInfoPropertyGroup)


def unregister():
    del bpy.types.Object.wow_wmo_vertex_info
