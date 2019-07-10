import bpy


def create_fog_object(name='Fog', radius=1.0, location=None, color=(1.0, 1.0, 1.0, 1.0)):

    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius
                                         , location=bpy.context.scene.cursor.location if location is None else location
                                         )


    fog = bpy.context.view_layer.objects.active
    fog.name = name

    # applying real object transformation
    bpy.ops.object.shade_smooth()

    mesh = fog.data
    material = bpy.data.materials.new(name=name)
    mesh.materials.append(material)

    material.use_nodes = True
    node_tree = material.node_tree

    for node in node_tree.nodes:
        node_tree.nodes.remove(node)

    output = material.node_tree.nodes.new('ShaderNodeOutputMaterial')
    diffuse = material.node_tree.nodes.new('ShaderNodeBsdfDiffuse')
    transparent = material.node_tree.nodes.new('ShaderNodeBsdfTransparent')
    mix = material.node_tree.nodes.new('ShaderNodeMixShader')

    node_tree.links.new(output.inputs['Surface'], mix.outputs['Shader'])
    node_tree.links.new(mix.inputs[1], transparent.outputs['BSDF'])
    node_tree.links.new(mix.inputs[2], diffuse.outputs['BSDF'])

    mix.inputs['Fac'].default_value = 0.3
    diffuse.inputs['Color'].default_value = color

    slot = bpy.context.scene.wow_wmo_root_elements.fogs.add()
    slot.pointer = fog

    fog.hide_viewport = False if "3" in bpy.context.scene.wow_visibility else True

    return fog