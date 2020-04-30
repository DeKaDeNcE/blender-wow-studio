import bpy

from ....utils.node_builder import NodeTreeBuilder


def update_wmo_mat_node_tree_cycles(bl_mat):

    bl_mat.use_nodes = True
    tree = bl_mat.node_tree
    links = tree.links

    tree_builder = NodeTreeBuilder(tree)

    # get textures
    img_1 = bl_mat.wow_wmo_material.diff_texture_1 if bl_mat.wow_wmo_material.diff_texture_1 else None
    img_2 = bl_mat.wow_wmo_material.diff_texture_2 if bl_mat.wow_wmo_material.diff_texture_2 else None

    # create nodes

    ng_wmo_shader = bpy.data.node_groups['MO_WMOShader']

    blendmap = tree_builder.add_node('ShaderNodeAttribute', 'Blendmap', 0, 0)
    blendmap.attribute_name = 'Blendmap'

    uvmap = tree_builder.add_node('ShaderNodeUVMap', 'UVMap', 0, 1)
    uvmap.uv_map = 'UVMap'

    uvmap2 = tree_builder.add_node('ShaderNodeUVMap', 'UVMap', 0, 2)
    uvmap2.uv_map = 'UVMap.001'

    emissive_color = tree_builder.add_node('ShaderNodeRGB', 'EmissiveColor', 1, 0)

    diffuse_tex1 = tree_builder.add_node('ShaderNodeTexImage', 'DiffuseTexture1', 1, 1)
    if img_1:
        diffuse_tex1.image = img_1

    diffuse_tex2 = tree_builder.add_node('ShaderNodeTexImage', 'DiffuseTexture2', 1, 2)
    if img_2:
        diffuse_tex2.image = img_2

    shader = tree_builder.add_node('ShaderNodeGroup', 'WMO Shader', 2, 1)
    shader.node_tree = ng_wmo_shader

    output = tree_builder.add_node('ShaderNodeOutputMaterial', 'Output', 3, 1)


    # set node links

    links.new(blendmap.outputs['Color'], shader.inputs['Blendmap'])
    links.new(uvmap.outputs['UV'], diffuse_tex1.inputs['Vector'])
    links.new(uvmap2.outputs['UV'], diffuse_tex2.inputs['Vector'])
    links.new(emissive_color.outputs['Color'], shader.inputs['EmissiveColor'])
    links.new(diffuse_tex1.outputs['Color'], shader.inputs['DiffuseTexture1'])
    links.new(diffuse_tex1.outputs['Alpha'], shader.inputs['Alpha1'])
    links.new(diffuse_tex2.outputs['Color'], shader.inputs['DiffuseTexture2'])
    links.new(diffuse_tex2.outputs['Alpha'], shader.inputs['Alpha2'])
    links.new(shader.outputs['Shader'], output.inputs['Surface'])
