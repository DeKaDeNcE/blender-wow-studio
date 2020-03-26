import bpy

from ....utils.node_builder import NodeTreeBuilder


def update_m2_mat_node_tree_cycles(bl_mat):

    # get textures
    img_1 = bl_mat.wow_m2_material.texture if bl_mat.wow_m2_material.texture else None

    bl_mat.use_nodes = True
    bsdf = bl_mat.node_tree.nodes["Principled BSDF"]
    tex_image = bl_mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex_image.image = img_1.image
    bl_mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])
