import bpy

from ....utils.node_builder import NodeTreeBuilder


def update_m2_mat_node_tree_cycles(bl_mat):

    # get textures
    img_1 = bl_mat.wow_m2_material.texture_1 if bl_mat.wow_m2_material.texture_1 else None

    bl_mat.use_nodes = True
    uv = bl_mat.node_tree.nodes.new('ShaderNodeUVMap')
    uv.uv_map = 'UVMap'
    bsdf = bl_mat.node_tree.nodes["Principled BSDF"]
    tex_image = bl_mat.node_tree.nodes.new('ShaderNodeTexImage')

    if img_1:
        tex_image.image = img_1

    bl_mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])
    bl_mat.node_tree.links.new(uv.outputs['UV'], tex_image.inputs['Vector'])
