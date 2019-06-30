import hashlib
import io
import os
import traceback

import bpy

from ..utils.misc import load_game_data
from ..utils.node_builder import NodeTreeBuilder
from ..pywowlib.io_utils.types import *
from ..ui import get_addon_prefs


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
        self.texture_id = 0
        self.blend_mode = 0

        skip(f, 36)


def skip(f, n_bytes):
    f.seek(f.tell() + n_bytes)


def import_doodad(asset_dir, filepath):
    """Import World of Warcraft M2 model to scene."""

    m2_name = str(hashlib.md5(filepath.encode('utf-8')).hexdigest())

    game_data = load_game_data()

    m2_path = os.path.splitext(filepath)[0] + ".m2"
    skin_path = os.path.splitext(filepath)[0] + "00.skin"

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

    # read blend mode overrides
    if global_flags & 0x08:
        f.seek(304)
        n_blendmode_overrides = uint32.read(f)
        f.seek(uint32.read(f))

        blend_mode_overrides = []
        for _ in range(n_blendmode_overrides):
            blend_mode_overrides.append(uint16.read(f))

    # texture units
    f.seek(36 - padding)
    n_tex_units = uint32.read(f)
    f.seek(uint32.read(f))
    for _ in range(n_tex_units):
        skip(f, 2)
        shader_id = uint16.read(f)
        submesh_id = uint16.read(f)
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
    nobj.use_fake_user = True
    nobj.wow_wmo_doodad.enabled = True
    nobj.wow_wmo_doodad.path = filepath

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


def wmv_get_last_m2():
    """Get the path of last M2 model from WoWModelViewer or similar log."""

    addon_preferences = get_addon_prefs()
    if addon_preferences.wmv_path:

        lines = open(addon_preferences.wmv_path).readlines()

        for line in reversed(lines):
            if 'Loading model:' in line:
                return line[25:].split(",", 1)[0].rstrip("\n")


class WowWMOImportDoodadWMV(bpy.types.Operator):
    bl_idname = 'scene.wow_wmo_import_doodad_from_wmv'
    bl_label = 'Import last M2 from WMV'
    bl_description = 'Import last M2 from WoW Model Viewer'
    bl_options = {'REGISTER'}

    def execute(self, context):

        cache_path = get_addon_prefs().cache_dir_path
        m2_path = wmv_get_last_m2()

        if not m2_path:
            self.report({'ERROR'}, """WoW Model Viewer log contains no model entries.
            Make sure to use compatible WMV version or open an .m2 there.""")
            return {'CANCELLED'}

        doodad_path_noext = os.path.splitext(m2_path)[0]
        doodad_path_noext_uni = doodad_path_noext.replace('\\', '/')

        doodad_path = doodad_path_noext + ".m2"
        doodad_path_blend = doodad_path_noext_uni + '.blend'
        doodad_basename = os.path.basename(doodad_path_noext_uni)
        path_local = doodad_path_blend if os.name != 'nt' else doodad_path_noext + '.blend'
        library_path = os.path.join(cache_path, path_local)

        path_hash = str(hashlib.md5(doodad_path.encode('utf-8')).hexdigest())

        doodad_col = bpy.context.scene.wow_wmo_root_components.doodads_proto
        p_obj = doodad_col.get(path_hash)

        if not p_obj:

            if not os.path.exists(library_path):
                library_dir = os.path.split(library_path)[0]
                if not os.path.exists(library_dir):
                    os.makedirs(library_dir)

                try:
                    p_obj = import_doodad(cache_path, doodad_path)
                except:

                    p_obj = import_doodad(cache_path, 'Spells\\Errorcube.m2')
                    p_obj.wow_wmo_doodad.enabled = True
                    p_obj.wow_wmo_doodad.path = doodad_path
                    p_obj.name = path_hash
                    traceback.print_exc()
                    print("\nFailed to import model: <<{}>>. Placeholder is imported instead.".format(doodad_path))

                bpy.data.libraries.write(library_path, {p_obj}, fake_user=True)
                bpy.data.objects.remove(p_obj)

        with bpy.data.libraries.load(library_path, link=True) as (data_from, data_to):
            data_to.objects = [ob_name for ob_name in data_from.objects if ob_name == path_hash]

        p_obj = data_to.objects[0]

        slot = doodad_col.add()
        slot.pointer = p_obj

        obj = bpy.data.objects.new(doodad_basename, p_obj.data)
        bpy.context.collection.objects.link(obj)

        obj.wow_wmo_doodad.enabled = True
        obj.wow_wmo_doodad.path = m2_path

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        return {'FINISHED'}
