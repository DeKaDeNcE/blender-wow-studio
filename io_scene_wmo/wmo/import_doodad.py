import bpy
import os
import io
import traceback
import hashlib
from struct import unpack

from ..ui import get_addon_prefs
from ..utils import load_game_data


# This file is implementing basic M2 geometry parsing in prodedural style for the sake of performance.
class Submesh:
    __slots__ = (
        "start_vertex",
        "n_vertices",
        "start_triangle",
        "n_triangles",
        "texture_id"
    )

    def __init__(self, f):
        skip(f, 4)
        self.start_vertex = unpack('H', f.read(2))[0]
        self.n_vertices = unpack('H', f.read(2))[0]
        self.start_triangle = unpack('H', f.read(2))[0]
        self.n_triangles = unpack('H', f.read(2))[0]
        self.texture_id = 0

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
        skip(f, unpack('I', f.read(4))[0])
        magic = f.read(4).decode("utf-8")

    # read vertex positions
    skip(f, 56)
    n_vertices = unpack('I', f.read(4))[0]
    f.seek(unpack('I', f.read(4))[0])

    vertices = [(0.0, 0.0, 0.0)] * n_vertices
    normals = [(0.0, 0.0, 0.0)] * n_vertices
    uv_coords = [(0.0, 0.0)] * n_vertices

    for i in range(n_vertices):
        vertices[i] = unpack('fff', f.read(12))
        skip(f, 8)
        normals[i] = unpack('fff', f.read(12))
        uv_coords[i] = unpack('ff', f.read(8))
        skip(f, 8)

    # read texture lookup
    f.seek(128)
    n_tex_lookups = unpack('I', f.read(4))[0]
    f.seek(unpack('I', f.read(4))[0])
    texture_lookup_table = [unpack('H', f.read(2))[0] for _ in range(n_tex_lookups)]

    # read texture names
    f.seek(80)
    n_textures = unpack('I', f.read(4))[0]
    f.seek(unpack('I', f.read(4))[0])

    texture_paths = []
    for _ in range(n_textures):
        skip(f, 8)
        len_tex = unpack('I', f.read(4))[0]
        ofs_tex = unpack('I', f.read(4))[0]

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

    n_indices = unpack('I', f.read(4))[0]
    f.seek(unpack('I', f.read(4))[0])
    indices = unpack('{}H'.format(n_indices), f.read(2 * n_indices))

    # triangles
    f.seek(12 - padding)
    n_triangles = unpack('I', f.read(4))[0] // 3
    f.seek(unpack('I', f.read(4))[0])
    triangles = [(0, 0, 0)] * n_triangles
    for i in range(n_triangles):
        triangles[i] = unpack('HHH', f.read(6))

    # submeshes
    f.seek(28 - padding)
    n_submeshes = unpack('I', f.read(4))[0]
    f.seek(unpack('I', f.read(4))[0])
    submeshes = [Submesh(f) for _ in range(n_submeshes)]

    # texture units
    f.seek(36 - padding)
    n_tex_units = unpack('I', f.read(4))[0]
    f.seek(unpack('I', f.read(4))[0])
    for _ in range(n_tex_units):
        skip(f, 4)
        submesh_id = unpack('H', f.read(2))[0]
        skip(f, 10)
        submeshes[submesh_id].texture_id = unpack('H', f.read(2))[0]
        skip(f, 6)

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
    uv1 = mesh.uv_textures.new("UVMap")
    uv_layer1 = mesh.uv_layers[0]
    for i in range(len(uv_layer1.data)):
        uv = uv_coords[mesh.loops[i].vertex_index]
        uv_layer1.data[i].uv = (uv[0], 1 - uv[1])

    # unpack and convert textures
    game_data.extract_textures_as_png(asset_dir, texture_paths)

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

        # set material for rendering
        mat = bpy.data.materials.new("{}_{}".format(m2_name, i))
        mesh.materials.append(mat)
        mat.use_object_color = True
        mat.use_shadeless = True

        texture = bpy.data.textures.new(mat.name, type='IMAGE')
        texture.image = img
        tex_slot = mat.texture_slots.add()
        tex_slot.texture = texture

        if img:
            for j in range(submesh.start_triangle // 3, (submesh.start_triangle + submesh.n_triangles) // 3):
                uv1.data[j].image = img
                mesh.polygons[j].material_index = i

    nobj = bpy.data.objects.new(m2_name, mesh)
    nobj.use_fake_user = True
    nobj.wow_wmo_doodad.enabled = True
    nobj.wow_wmo_doodad.path = filepath

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

        game_data = load_game_data()

        if not game_data or not game_data.files:
            self.report({'ERROR'}, "Failed to import model. Connect to game client first.")
            return {'CANCELLED'}

        addon_preferences = get_addon_prefs()
        m2_path = wmv_get_last_m2()

        if not m2_path:
            self.report({'ERROR'}, """WoW Model Viewer log contains no model entries.
            Make sure to use compatible WMV version or open an .m2 there.""")
            return {'CANCELLED'}

        proto_scene = (bpy.data.scenes.get('$WMODoodadPrototypes') or bpy.data.scenes.new(name='$WMODoodadPrototypes'))
        try:
            obj = import_doodad(addon_preferences.cache_dir_path, m2_path, proto_scene)
        except:
            bpy.ops.mesh.primitive_cube_add()
            obj = bpy.context.scene.objects.active
            traceback.print_exc()
            self.report({'WARNING'}, "Failed to import model. Placeholder is imported instead.")
        else:
            self.report({'INFO'}, "Imported model: {}".format(m2_path))

        if bpy.context.scene.objects.active and bpy.context.scene.objects.active.select:
            obj.location = bpy.context.scene.objects.active.location
        else:
            obj.location = bpy.context.scene.cursor_location

        obj.wow_wmo_doodad.enabled = True
        obj.wow_wmo_doodad.path = m2_path

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.objects.active = obj
        obj.select = True

        return {'FINISHED'}
