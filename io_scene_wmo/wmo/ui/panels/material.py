import bpy
from ..enums import *
from ...render import update_wmo_mat_node_tree
from ....utils.callbacks import on_release


class WMO_PT_material(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    bl_label = "WMO Material"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        col = layout.column()
        col.prop(context.material.wow_wmo_material, "shader")
        col.prop(context.material.wow_wmo_material, "terrain_type")
        col.prop(context.material.wow_wmo_material, "blending_mode")

        col.separator()

        box = col.box()
        box.prop(context.material.wow_wmo_material, "diff_texture_1")

        if context.material.wow_wmo_material.diff_texture_1:
            box.prop(context.material.wow_wmo_material.diff_texture_1.wow_wmo_texture, "path")

        box = col.box()
        box.prop(context.material.wow_wmo_material, "diff_texture_2")

        if context.material.wow_wmo_material.diff_texture_2:
            box.prop(context.material.wow_wmo_material.diff_texture_2.wow_wmo_texture, "path")

        col.separator()
        col.prop(context.material.wow_wmo_material, "flags")

        layout.prop(context.material.wow_wmo_material, "emissive_color")
        layout.prop(context.material.wow_wmo_material, "diff_color")
        layout.enabled = context.material.wow_wmo_material.enabled

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
                and context.material is not None
                and context.material.wow_wmo_material.enabled
        )


def update_flags(self, context):
    material = self.self_pointer

    if '1' in self.flags:
        material.pass_index |= 0x1  # BlenderWMOMaterialRenderFlags.Unlit
    else:
        material.pass_index &= ~0x1

    if '16' in self.flags:
        material.pass_index |= 0x2  # BlenderWMOMaterialRenderFlags.SIDN
    else:
        material.pass_index &= ~0x2


def update_shader(self, context):
    material = self.self_pointer

    if int(self.shader) in (3, 5, 6, 7, 8, 9, 11, 12, 13, 15):
        material.pass_index |= 0x4  # BlenderWMOMaterialRenderFlags.IsTwoLayered
    else:
        material.pass_index &= ~0x4

def update_blending_mode(self, context):
    material = self.self_pointer

    blend_mode = int(self.blending_mode)
    if blend_mode in (0, 8, 9):
        material.pass_index |= 0x10 # BlenderWMOMaterialRenderFlags.IsOpaque
    else:
        material.pass_index &= ~0x10

    if blend_mode in (0, 8, 9):
        material.blend_method = 'OPAQUE'
    elif blend_mode == 1:
        material.blend_method = 'CLIP'
        material.alpha_threshold = 0.9
    elif blend_mode in (3, 7, 10):
        material.blend_method = 'ADD'
    elif blend_mode in (4, 5):
        material.blend_method = 'MULTIPLY'
    else:
        material.blend_method = 'BLEND'

def update_diff_texture_1(self, context):
    if not self.self_pointer.use_nodes or ('DiffuseTexture1' not in self.self_pointer.node_tree.nodes):
        return

    if bpy.context.scene.render.engine in ('CYCLES', 'BLENDER_EEVEE') and self.diff_texture_1:
        self.self_pointer.node_tree.nodes['DiffuseTexture1'].image = self.diff_texture_1


def update_diff_texture_2(self, context):
    if not self.self_pointer.use_nodes or ('DiffuseTexture2' not in self.self_pointer.node_tree.nodes):
        return

    if bpy.context.scene.render.engine in ('CYCLES', 'BLENDER_EEVEE') and self.diff_texture_2:
        self.self_pointer.node_tree.nodes['DiffuseTexture2'].image = self.diff_texture_2

@on_release()
def update_emissive_color(self, context):
    if not self.self_pointer.use_nodes or ('EmissiveColor' not in self.self_pointer.node_tree.nodes):
        return

    self.self_pointer.node_tree.nodes['EmissiveColor'].outputs[0].default_value = self.emissive_color


def update_wmo_material_enabled(self, context):

    if self.enabled:
        update_wmo_mat_node_tree(self.self_pointer)


class WowMaterialPropertyGroup(bpy.types.PropertyGroup):

    enabled:  bpy.props.BoolProperty()

    flags:  bpy.props.EnumProperty(
        name="Material Flags",
        description="WoW material flags",
        items=material_flag_enum,
        options={"ENUM_FLAG"},
        update=update_flags
        )

    shader:  bpy.props.EnumProperty(
        items=shader_enum,
        name="Shader",
        description="WoW shader assigned to this material",
        update=update_shader
        )

    blending_mode:  bpy.props.EnumProperty(
        items=blending_enum,
        name="Blending",
        description="WoW material blending mode",
        update=update_blending_mode
        )

    emissive_color:  bpy.props.FloatVectorProperty(
        name="Emissive Color",
        subtype='COLOR',
        default=(1,1,1,1),
        size=4,
        min=0.0,
        max=1.0,
        update=update_emissive_color
        )

    diff_color:  bpy.props.FloatVectorProperty(
        name="Diffuse Color",
        subtype='COLOR',
        default=(1, 1, 1, 1),
        size=4,
        min=0.0,
        max=1.0
        )

    terrain_type:  bpy.props.EnumProperty(
        items=terrain_type_enum,
        name="Terrain Type",
        description="Terrain type assigned to this material. Used for producing correct footstep sounds."
        )

    diff_texture_1:  bpy.props.PointerProperty(
        type=bpy.types.Image,
        name='Texture 1',
        update=update_diff_texture_1
    )

    diff_texture_2:  bpy.props.PointerProperty(
        type=bpy.types.Image,
        name='Texture 2',
        update=update_diff_texture_2
    )

    # internal

    self_pointer: bpy.props.PointerProperty(type=bpy.types.Material)


def register():
    bpy.types.Material.wow_wmo_material = bpy.props.PointerProperty(type=WowMaterialPropertyGroup)


def unregister():
    del bpy.types.Material.wow_wmo_material
