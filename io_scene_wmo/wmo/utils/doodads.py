import io
import os
import traceback

import bpy

from ...utils.misc import load_game_data
from ...utils.node_builder import NodeTreeBuilder
from ...pywowlib.io_utils.types import *




# This file is implementing basic M2 geometry parsing in prodedural style for the sake of performance.
class Submesh:
    __slots__ = (
        "start_vertex",
        "n_vertices",
        "start_triangle",
        "n_triangles",
        "texture_id",
        "blend_mode"
    )

    def __init__(self, f):
        skip(f, 4)
        self.start_vertex = uint16.read(f)
        self.n_vertices = uint16.read(f)
        self.start_triangle = uint16.read(f)
        self.n_triangles = uint16.read(f)
        self.texture_id = None
        self.blend_mode = 0

        skip(f, 36)


def skip(f, n_bytes):
    f.seek(f.tell() + n_bytes)


def import_doodad_model(asset_dir : str, filepath : str) -> bpy.types.Object:
    """Import World of Warcraft M2 model to scene."""

    game_data = load_game_data()

    m2_path = os.path.splitext(filepath)[0] + ".m2"
    skin_path = os.path.splitext(filepath)[0] + "00.skin"

    m2_name = os.path.basename(os.path.splitext(m2_path)[0])

    try:
        m2_file = io.BytesIO(game_data.read_file(m2_path))
    except KeyError:
        raise FileNotFoundError("\nModel <<{}>> not found in WoW file system.".format(filepath))

    try:
        skin_file = io.BytesIO(game_data.read_file(skin_path))
    except KeyError:
        raise FileNotFoundError("\nSkin file for model <<{}>> not found in WoW file system.".format(filepath))

    ###### M2 file parsing ######

    f = m2_file
    magic = f.read(4).decode("utf-8")
    while magic not in ('MD20', 'MD21'):
        skip(f, uint32.read(f))
        magic = f.read(4).decode("utf-8")

    # read flags
    f.seek(16)
    global_flags = uint32.read(f)

    # read vertex positions
    f.seek(60)
    n_vertices = uint32.read(f)
    f.seek(uint32.read(f))

    vertices = [(0.0, 0.0, 0.0)] * n_vertices
    normals = [(0.0, 0.0, 0.0)] * n_vertices
    uv_coords = [(0.0, 0.0)] * n_vertices

    for i in range(n_vertices):
        vertices[i] = float32.read(f, 3)
        skip(f, 8)
        normals[i] = float32.read(f, 3)
        uv_coords[i] = float32.read(f, 2)
        skip(f, 8)

    # read render flags and blending modes
    f.seek(112)
    n_render_flags = uint32.read(f)
    f.seek(uint32.read(f))

    blend_modes = []  # skip render flags for now
    for _ in range(n_render_flags):
        skip(f, 2)
        blend_modes.append(uint16.read(f))

    # read texture lookup
    f.seek(128)
    n_tex_lookups = uint32.read(f)
    f.seek(uint32.read(f))
    texture_lookup_table = [uint16.read(f) for _ in range(n_tex_lookups)]

    # read texture names
    f.seek(80)
    n_textures = uint32.read(f)
    f.seek(uint32.read(f))

    texture_paths = []
    for _ in range(n_textures):
        skip(f, 8)
        len_tex = uint32.read(f)
        ofs_tex = uint32.read(f)

        if not len_tex:
            texture_paths.append(None)
            continue

        pos = f.tell()
        f.seek(ofs_tex)
        texture_paths.append(f.read(len_tex).decode('utf-8').rstrip('\0'))
        f.seek(pos)

    # read blend mode overrides
    if global_flags & 0x08:
        f.seek(304)
        n_blendmode_overrides = uint32.read(f)
        f.seek(uint32.read(f))

        blend_mode_overrides = []
        for _ in range(n_blendmode_overrides):
            blend_mode_overrides.append(uint16.read(f))

    ###### Skin ######

    f = skin_file
    padding = 0

    # indices
    try:
        magic = f.read(4).decode("utf-8")
    except UnicodeDecodeError:
        padding = 4
        f.seek(0)

    n_indices = uint32.read(f)
    f.seek(uint32.read(f))
    indices = unpack('{}H'.format(n_indices), f.read(2 * n_indices))

    # triangles
    f.seek(12 - padding)
    n_triangles = uint32.read(f) // 3
    f.seek(uint32.read(f))
    triangles = [(0, 0, 0)] * n_triangles
    for i in range(n_triangles):
        triangles[i] = unpack('HHH', f.read(6))

    # submeshes
    f.seek(28 - padding)
    n_submeshes = uint32.read(f)
    f.seek(uint32.read(f))
    submeshes = [Submesh(f) for _ in range(n_submeshes)]

    # texture units
    f.seek(36 - padding)
    n_tex_units = uint32.read(f)
    f.seek(uint32.read(f))
    for _ in range(n_tex_units):
        skip(f, 2)
        shader_id = uint16.read(f)
        submesh_id = uint16.read(f)

        if submeshes[submesh_id].texture_id is not None:
            skip(f, 18)
            continue

        skip(f, 4)
        render_flag_index = uint16.read(f)
        skip(f, 4)
        submeshes[submesh_id].texture_id = uint16.read(f)
        skip(f, 6)

        # determine blending mode
        if global_flags & 0x08 and shader_id < len(blend_mode_overrides):
            submeshes[submesh_id].blend_mode = blend_mode_overrides[shader_id]
        else:
            submeshes[submesh_id].blend_mode = blend_modes[render_flag_index]


    ###### Build blender object ######
    faces = [[0, 0, 0]] * n_triangles

    for i, tri in enumerate(triangles):
        face = []
        for index in tri:
            face.append(indices[index])

        faces[i] = face

    # create mesh
    mesh = bpy.data.meshes.new(m2_name)
    mesh.from_pydata(vertices, [], faces)

    for poly in mesh.polygons:
        poly.use_smooth = True

    # set normals
    for index, vertex in enumerate(mesh.vertices):
        vertex.normal = normals[index]

    # set uv
    uv_layer1 = mesh.uv_layers.new(name="UVMap")
    for i in range(len(uv_layer1.data)):
        uv = uv_coords[mesh.loops[i].vertex_index]
        uv_layer1.data[i].uv = (uv[0], 1 - uv[1])

    # unpack and convert textures
    game_data.extract_textures_as_png(asset_dir, texture_paths)

    # create object
    nobj = bpy.data.objects.new(m2_name, mesh)
    nobj.wow_wmo_doodad.path = filepath
    nobj.wow_wmo_doodad.enabled = True
    nobj.wow_wmo_doodad.self_pointer = nobj

    # set textures
    for i, submesh in enumerate(submeshes):
        tex_path = os.path.splitext(texture_paths[texture_lookup_table[submesh.texture_id]])[0] + '.png'

        # add support for unix filesystems
        if os.name != 'nt':
            tex_path = tex_path.replace('\\', '/')

        img = None

        try:
            img = bpy.data.images.load(os.path.join(asset_dir, tex_path), check_existing=True)
        except RuntimeError:
            traceback.print_exc()
            print("\nFailed to load texture: <<{}>>. File is missing or corrupted.".format(tex_path))

        if img:
            for j in range(submesh.start_triangle // 3, (submesh.start_triangle + submesh.n_triangles) // 3):
                mesh.polygons[j].material_index = i

        mat = bpy.data.materials.new(name="{}_{}".format(m2_name, i))

        mat.use_nodes = True

        node_tree = mat.node_tree
        tree_builder = NodeTreeBuilder(node_tree)

        tex_image = tree_builder.add_node('ShaderNodeTexImage', "Texture", 0, 0)
        tex_image.image = img

        doodad_color = tree_builder.add_node('ShaderNodeRGB', "DoodadColor", 0, 2)

        mix_rgb = tree_builder.add_node('ShaderNodeMixRGB', "ApplyColor", 1, 1)
        mix_rgb.inputs['Fac'].default_value = 1.0
        mix_rgb.blend_type = 'MULTIPLY'

        transparent_bsdf = tree_builder.add_node('ShaderNodeBsdfTransparent', "Transparent", 2, 0)
        bsdf = tree_builder.add_node('ShaderNodeBsdfDiffuse', "Diffuse", 2, 2)

        mix_shader = tree_builder.add_node('ShaderNodeMixShader', "MixShader", 3, 0)
        mix_shader.inputs['Fac'].default_value = 1.0

        output = tree_builder.add_node('ShaderNodeOutputMaterial', "Output", 4, 1)

        mat.node_tree.links.new(tex_image.outputs['Color'], mix_rgb.inputs['Color1'])

        if submesh.blend_mode not in (0, 3):
            mat.node_tree.links.new(tex_image.outputs['Alpha'], mix_shader.inputs['Fac'])

        mat.node_tree.links.new(doodad_color.outputs['Color'], mix_rgb.inputs['Color2'])
        mat.node_tree.links.new(mix_rgb.outputs['Color'], bsdf.inputs['Color'])
        mat.node_tree.links.new(bsdf.outputs['BSDF'], mix_shader.inputs[2])
        mat.node_tree.links.new(transparent_bsdf.outputs['BSDF'], mix_shader.inputs[1])
        mat.node_tree.links.new(mix_shader.outputs['Shader'], output.inputs['Surface'])


        # configure blending
        if submesh.blend_mode == 0:
            mat.blend_method = 'OPAQUE'
        elif submesh.blend_mode == 1:
            mat.blend_method = 'CLIP'
            mat.alpha_threshold = 0.9
        elif submesh.blend_mode == 2:
            mat.blend_method = 'BLEND'
        elif submesh.blend_mode in (3, 4):
            mat.blend_method = 'ADD'
        elif submesh.blend_mode == 5:
            mat.blend_method = 'MULTIPLY'
        else:
            mat.blend_method = 'BLEND'

        mesh.materials.append(mat)

    return nobj

def import_doodad(m2_path : str, cache_path : str) -> bpy.types.Object:

    try:
        obj = import_doodad_model(cache_path, m2_path)
    except:
        obj = import_doodad_model(cache_path, 'Spells\\Errorcube.m2')
        traceback.print_exc()
        print("\nFailed to import model: <<{}>>. Placeholder is imported instead.".format(m2_path))

    obj.name = os.path.splitext(m2_path.split('\\')[-1])[0]

    return obj

