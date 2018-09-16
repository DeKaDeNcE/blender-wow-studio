import bpy


def update_wmo_mat_node_tree_internal(bl_mat):

    # setup material node tree
    bl_mat.use_nodes = True
    bl_mat.use_shadeless = True
    tree = bl_mat.node_tree
    links = tree.links

    # clear default nodes
    for n in tree.nodes:
        tree.nodes.remove(n)

    # get textures
    tex_1 = bl_mat.wow_wmo_material.diff_texture_1
    tex_2 = bl_mat.wow_wmo_material.diff_texture_2

    # create nodes

    ng_apply_vertex_color = bpy.data.node_groups['MO_ApplyVertexColor']
    ng_object_flags = bpy.data.node_groups['MO_ObjectFlags']
    ng_mix_textures = bpy.data.node_groups['MO_MixTextures']
    ng_properties = bpy.data.node_groups['MO_Properties']
    ng_mat_flags = bpy.data.node_groups['MO_MaterialFlags']

    g_info_main = tree.nodes.new('ShaderNodeGeometry')
    g_info_main.label = 'GeometryInfoMain'
    g_info_main.location = -1979.28, 1202.12
    g_info_main.uv_layer = 'UVMap'
    g_info_main.color_layer = 'Col'

    g_info_second_layer = tree.nodes.new('ShaderNodeGeometry')
    g_info_second_layer.label = 'GeometryInfoSecondLayer'
    g_info_second_layer.location = -1979.28, 834.877
    g_info_second_layer.uv_layer = 'UVMap.001'
    g_info_second_layer.color_layer = 'Blendmap'

    diffuse_tex1 = tree.nodes.new('ShaderNodeTexture')
    diffuse_tex1.label = 'DiffuseTexture1'
    diffuse_tex1.name = diffuse_tex1.label
    diffuse_tex1.location = -1696.0, 1202.12
    diffuse_tex1.texture = tex_1

    diffuse_tex2 = tree.nodes.new('ShaderNodeTexture')
    diffuse_tex2.label = 'DiffuseTexture2'
    diffuse_tex2.name = diffuse_tex2.label
    diffuse_tex2.location = -1696.0, 834.877

    if tex_2:
        diffuse_tex2.texture = tex_2

    lightmap = tree.nodes.new('ShaderNodeGeometry')
    lightmap.label = 'Lightmap'
    lightmap.location = -1698.83, 486.141
    lightmap.color_layer = 'Lightmap'

    mix_textures = tree.nodes.new('ShaderNodeGroup')
    mix_textures.label = 'MixTextures'
    mix_textures.location = -1346, 834
    mix_textures.node_tree = ng_mix_textures

    object_flags = tree.nodes.new('ShaderNodeGroup')
    object_flags.label = 'ObjectFlags'
    object_flags.location = -1346, 618
    object_flags.node_tree = ng_object_flags

    emissive_color = tree.nodes.new('ShaderNodeRGB')
    emissive_color.label = 'EmissiveColor'
    emissive_color.name = emissive_color.label
    emissive_color.location = -1097, 1202

    properties = tree.nodes.new('ShaderNodeGroup')
    properties.location = -1100.0, 1460
    properties.node_tree = ng_properties

    ecol_gamma = tree.nodes.new('ShaderNodeGamma')
    ecol_gamma.location = -900, 1120
    ecol_gamma.inputs[1].default_value = 1 / 2.2

    apply_sidn_scalar = tree.nodes.new('ShaderNodeMixRGB')
    apply_sidn_scalar.location = -620, 1200
    apply_sidn_scalar.blend_type = 'MULTIPLY'
    apply_sidn_scalar.inputs[0].default_value = 1

    mat_flags = tree.nodes.new('ShaderNodeGroup')
    mat_flags.location = -620.0, 1000
    mat_flags.node_tree = ng_mat_flags

    use_sidn_mix = tree.nodes.new('ShaderNodeMixRGB')
    use_sidn_mix.location = -400, 1100
    use_sidn_mix.inputs[1].default_value = (0, 0, 0, 1)

    material_node = tree.nodes.new('ShaderNodeMaterial')
    material_node.location = -1100.9, 984.342
    material_node.material = bl_mat

    mix_lightmap = tree.nodes.new('ShaderNodeMixRGB')
    mix_lightmap.location = -1095, 485
    mix_lightmap.blend_type = 'MIX'
    mix_lightmap.inputs[1].default_value = (0, 0, 0, 1)

    batchmap_a = tree.nodes.new('ShaderNodeGeometry')
    batchmap_a.label = 'BatchmapTrans'
    batchmap_a.location = -826.845, 485
    batchmap_a.color_layer = 'BatchmapTrans'

    batchmap_b = tree.nodes.new('ShaderNodeGeometry')
    batchmap_b.label = 'BatchmapInt'
    batchmap_b.location = -580.904, 485
    batchmap_b.color_layer = 'BatchmapInt'

    apply_vertex_color = tree.nodes.new('ShaderNodeGroup')
    apply_vertex_color.label = 'ApplyVertexColor'
    apply_vertex_color.location = -120, 800
    apply_vertex_color.node_tree = ng_apply_vertex_color

    output = tree.nodes.new('ShaderNodeOutput')
    output.location = 220, 800

    # set node links

    links.new(g_info_main.outputs[4], diffuse_tex1.inputs[0])
    links.new(g_info_main.outputs[6], apply_vertex_color.inputs[2])

    links.new(g_info_second_layer.outputs[4], diffuse_tex2.inputs[0])
    links.new(g_info_second_layer.outputs[6], mix_textures.inputs[2])

    links.new(diffuse_tex1.outputs[1], mix_textures.inputs[0])
    links.new(diffuse_tex2.outputs[1], mix_textures.inputs[1])

    links.new(lightmap.outputs[6], mix_lightmap.inputs[2])

    links.new(mix_textures.outputs[0], material_node.inputs[0])

    links.new(object_flags.outputs[7], mix_lightmap.inputs[0])

    links.new(emissive_color.outputs[0], ecol_gamma.inputs[0])

    links.new(properties.outputs[6], apply_sidn_scalar.inputs[1])

    links.new(ecol_gamma.outputs[0], apply_sidn_scalar.inputs[2])

    links.new(apply_sidn_scalar.outputs[0], use_sidn_mix.inputs[2])
    links.new(mat_flags.outputs[1], use_sidn_mix.inputs[0])
    links.new(use_sidn_mix.outputs[0], apply_vertex_color.inputs[3])

    links.new(material_node.outputs[0], apply_vertex_color.inputs[0])
    links.new(material_node.outputs[1], output.inputs[1])

    links.new(mix_lightmap.outputs[0], apply_vertex_color.inputs[1])

    links.new(batchmap_a.outputs[6], apply_vertex_color.inputs[5])
    links.new(batchmap_b.outputs[6], apply_vertex_color.inputs[4])

    links.new(apply_vertex_color.outputs[0], output.inputs[0])










