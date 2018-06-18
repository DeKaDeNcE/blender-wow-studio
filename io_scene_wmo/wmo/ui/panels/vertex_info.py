import bpy


class WowVertexInfoPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    bl_label = "WoW Vertex Info"

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        self.layout.prop_search(context.object.WowVertexInfo, "VertexGroup",
                                context.object, "vertex_groups", text="Collision vertex group"
                                )

        self.layout.prop(context.object.WowVertexInfo, "NodeSize", slider=True)

        self.layout.prop_search(context.object.WowVertexInfo, "BatchTypeA", context.object,
                                "vertex_groups", text="Batch type A vertex group"
                                )

        self.layout.prop_search(context.object.WowVertexInfo, "BatchTypeB",
                                context.object, "vertex_groups", text="Batch type B vertex group"
                                )

        self.layout.prop_search(context.object.WowVertexInfo, "Lightmap",
                                context.object, "vertex_groups", text="Lightmap"
                                )

        self.layout.prop_search(context.object.WowVertexInfo, "Blendmap", context.object,
                                "vertex_groups", text="Blendmap"
                                )

        self.layout.prop_search(context.object.WowVertexInfo, "SecondUV", context.object.data,
                                "uv_textures", text="Second UV"
                                )

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.WowScene.Type == 'WMO'
                and context.object is not None
                and context.object.data is not None
                and isinstance(context.object.data,bpy.types.Mesh)
                and context.object.WowWMOGroup.Enabled
                )


class WowVertexInfoPropertyGroup(bpy.types.PropertyGroup):
    VertexGroup = bpy.props.StringProperty()

    NodeSize = bpy.props.IntProperty(
        name="Node max size",
        description="Max count of faces for a node in bsp tree",
        default=2500, min=1,
        soft_max=5000
        )

    BatchTypeA = bpy.props.StringProperty()
    BatchTypeB = bpy.props.StringProperty()
    Lightmap = bpy.props.StringProperty()
    Blendmap = bpy.props.StringProperty()
    SecondUV = bpy.props.StringProperty()


def register():
    bpy.types.Object.WowVertexInfo = bpy.props.PointerProperty(type=WowVertexInfoPropertyGroup)


def unregister():
    bpy.types.Object.WowVertexInfo = None