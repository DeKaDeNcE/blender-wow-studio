import bpy
from ..enums import *
from ...render import load_wmo_shader_dependencies, update_wmo_mat_node_tree


class WowMaterialPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    bl_label = "WMO Material"

    def draw_header(self, context):
        self.layout.prop(context.material.wow_wmo_material, "enabled")

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.material.wow_wmo_material, "shader")
        col.prop(context.material.wow_wmo_material, "terrain_type")
        col.prop(context.material.wow_wmo_material, "blending_mode")

        col.separator()
        col.prop(context.material.wow_wmo_material, "diff_texture_1")
        col.prop(context.material.wow_wmo_material, "diff_texture_2")

        col.separator()
        col.label("Flags:")
        col.prop(context.material.wow_wmo_material, "flags")

        layout.prop(context.material.wow_wmo_material, "emissive_color")
        layout.prop(context.material.wow_wmo_material, "diff_color")
        layout.enabled = context.material.wow_wmo_material.enabled

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
                and context.material is not None
        )


def update_flags(self, context):
    if hasattr(context, 'material'):
        if '1' in self.flags:
            context.material.pass_index |= 0x1  # BlenderWMOMaterialRenderFlags.Unlit
        else:
            context.material.pass_index &= ~0x1

        if '16' in self.flags:
            context.material.pass_index |= 0x2  # BlenderWMOMaterialRenderFlags.SIDN
        else:
            context.material.pass_index &= ~0x2


def update_shader(self, context):
    if hasattr(context, 'material'):
        if int(self.shader) in (3, 5, 6, 7, 8, 9, 11, 12, 13, 15):
            context.material.pass_index |= 0x4  # BlenderWMOMaterialRenderFlags.IsTwoLayered
        else:
            context.material.pass_index &= ~0x4


def update_diff_texture_1(self, context):
    if not hasattr(context, 'material') \
            or not context.material.use_nodes \
            or ('DiffuseTexture1' not in context.material.node_tree.nodes):
        return

    if bpy.context.scene.render.engine == 'BLENDER_RENDER':
        context.material.node_tree.nodes['DiffuseTexture1'].texture = self.diff_texture_1
    elif bpy.context.scene.render.engine == 'CYCLES' and self.diff_texture_1:
        context.material.node_tree.nodes['DiffuseTexture1'].image = self.diff_texture_1.image


def update_diff_texture_2(self, context):
    if not hasattr(context, 'material') \
            or not context.material.use_nodes \
            or ('DiffuseTexture2' not in context.material.node_tree.nodes):
        return

    if bpy.context.scene.render.engine == 'BLENDER_RENDER':
        context.material.node_tree.nodes['DiffuseTexture2'].texture = self.diff_texture_2
    elif bpy.context.scene.render.engine == 'CYCLES' and self.diff_texture_2:
        context.material.node_tree.nodes['DiffuseTexture2'].image = self.diff_texture_2.image


def update_emissive_color(self, context):
    if not hasattr(context, 'material') \
            or not context.material.use_nodes \
            or ('EmissiveColor' not in context.material.node_tree.nodes):
        return

    context.material.node_tree.nodes['EmissiveColor'].outputs[0].default_value = self.emissive_color


def update_wmo_material_enabled(self, context):
    if not hasattr(context, 'material') or not context.material:
        return

    if self.enabled:
        update_wmo_mat_node_tree(context.material)

    elif context.materials.use_nodes:
        tree = context.material.node_tree

        for n in tree.nodes:
            tree.nodes.remove(n)

        context.material.use_nodes = False


class WowMaterialPropertyGroup(bpy.types.PropertyGroup):

    enabled = bpy.props.BoolProperty(
        name="",
        description="Enable WoW material properties",
        update=update_wmo_material_enabled)

    flags = bpy.props.EnumProperty(
        name="Material flags",
        description="WoW material flags",
        items=material_flag_enum,
        options={"ENUM_FLAG"},
        update=update_flags
        )

    shader = bpy.props.EnumProperty(
        items=shader_enum,
        name="Shader",
        description="WoW shader assigned to this material",
        update=update_shader
        )

    blending_mode = bpy.props.EnumProperty(
        items=blending_enum,
        name="Blending",
        description="WoW material blending mode"
        )

    emissive_color = bpy.props.FloatVectorProperty(
        name="Emissive Color",
        subtype='COLOR',
        default=(1,1,1,1),
        size=4,
        min=0.0,
        max=1.0,
        update=update_emissive_color
        )

    diff_color = bpy.props.FloatVectorProperty(
        name="Diffuse Color",
        subtype='COLOR',
        default=(1, 1, 1, 1),
        size=4,
        min=0.0,
        max=1.0
        )

    terrain_type = bpy.props.EnumProperty(
        items=terrain_type_enum,
        name="Terrain Type",
        description="Terrain type assigned to this material. Used for producing correct footstep sounds."
        )

    diff_texture_1 = bpy.props.PointerProperty(
        type=bpy.types.Texture,
        name='Texture 1',
        update=update_diff_texture_1
    )

    diff_texture_2 = bpy.props.PointerProperty(
        type=bpy.types.Texture,
        name='Texture 2',
        update=update_diff_texture_2
    )


def register():
    bpy.types.Material.wow_wmo_material = bpy.props.PointerProperty(type=WowMaterialPropertyGroup)


def unregister():
    del bpy.types.Material.wow_wmo_material
