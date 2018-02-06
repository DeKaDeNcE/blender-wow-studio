import bpy
import os
from ..wowlib.m2_file import M2File, M2Externals
from ..utils import parse_bitfield, get_material_viewport_image


class BlenderM2Scene:
    def __init__(self, m2, skins, prefs):
        self.m2 = m2
        self.skins = skins
        self.materials = {}
        self.geosets = {}
        self.collision_mesh = None
        self.settings = prefs

    def load_materials(self, texture_dir):
        # TODO: multitexturing
        skin = self.skins[0]  # assuming first skin is the most detailed one

        for tex_unit in skin.texture_units:
            texture = self.m2.textures[self.m2.texture_lookup_table[tex_unit.texture_combo_index]]
            texture_png = os.path.splitext(texture)[0] + '.png'
            m2_mat = self.m2.materials[tex_unit.material_index]

            # creating material
            blender_mat = bpy.data.materials.new(os.path.basename(texture_png))

            tex1_slot = blender_mat.texture_slots.create(1)
            tex1_slot.uv_layer = "UVMap"
            tex1_slot.texture_coords = 'UV'

            tex1_name = blender_mat.name + "_Tex_02"
            tex1 = bpy.data.textures.new(tex1_name, 'IMAGE')
            tex1_slot.texture = tex1

            # loading images
            if os.name != 'nt': texture_png = texture_png.replace('\\', '/')  # reverse slahes for unix

            try:
                tex1_img = bpy.data.images.load(os.path.join(texture_dir, texture_png))
                tex1.image = tex1_img
                blender_mat.active_texture = tex1_img
            except RuntimeError:
                pass

            ''' NEEDS UI
            # filling material settings
            parse_bitfield(tex_unit.flags, blender_mat.WowM2Material.Flags, 0x80)  # texture unit flags
            parse_bitfield(m2_mat.flags, blender_mat.WowM2Material.RenderFlags, 0x800)  # render flags

            blender_mat.WowM2Material.BlendingMode = m2_mat.blending_mode  # TODO: ? bitfield
            blender_mat.WowM2Material.Shader = tex_unit.shader_id
            '''

            # TODO: other settings

            self.materials[tex_unit.skin_section_index] = blender_mat

    def load_geosets(self):
        if not len(self.m2.vertices):
            print("\nNo mesh geometry found to import.")
            return

        skin = self.skins[0]
        skin_tris = [skin.triangle_indices[i:i+2] for i in range(len(skin.triangle_indices))]

        for smesh_i, smesh in enumerate(skin.submeshes):
            smesh_tris = [skin_tris[i] for i in range(smesh.start_triangle // 3,
                                                      smesh.start_triangle + smesh.n_triangles // 3)]

            vertices = []
            normals = []
            tex_coords = []

            final_tris = []

            for tri in smesh_tris:
                final_tri = tuple([i - smesh.start_triangle for i in tri])
                for index in tri:
                    vertex = self.m2.vertices[skin.vertex_indices[index]]
                    vertices.append(vertex.position)
                    normals.append(vertex.normal)
                    tex_coords.append(vertex.tex_coords)
                    # TODO: bone stuff, tex_coords2

                final_tris.append(final_tri)

            # create mesh
            mesh = bpy.data.meshes.new(self.m2.name.value)
            mesh.from_pydata(vertices, [], final_tris)

            for poly in mesh.polygons:
                poly.use_smooth = True

            # set normals
            for index, vertex in enumerate(mesh.vertices):
                vertex.normal = normals[index]

            # set uv
            uv1 = mesh.uv_textures.new("UVMap")
            uv_layer1 = mesh.uv_layers[0]
            for i in range(len(uv_layer1.data)):
                uv = tex_coords[mesh.loops[i].vertex_index]
                uv_layer1.data[i].uv = (uv[0], 1 - uv[1])

            # set textures and materials
            material = self.materials[smesh_i]
            mesh.materials.append(material)

            img = get_material_viewport_image(material)
            for i, poly in enumerate(mesh.polygons):
                uv1.active.data[i] = img
                poly.material_index = 0


def import_m2(version, file):  # TODO: implement multiversioning

    # get global variables
    game_data = getattr(bpy, "wow_game_data", None)
    prefs = bpy.context.user_preferences.addons.get("io_scene_wmo").preferences
    texture_dir = prefs.cache_dir_path if prefs.use_cache_dir else os.path.dirname(file)

    if type(file) is str:
        m2_file = M2File(version, filepath=file)
        m2 = m2_file.root
        skins = m2_file.skin_profiles

        if not game_data:
            print("\n\n### Loading game data ###")
            bpy.ops.scene.load_wow_filesystem()
            game_data = bpy.wow_game_data

        if game_data.files:
            print("\n\n### Extracting textures ###")
            textures = m2.textures.values
            game_data.extract_textures_as_png(texture_dir, textures)

        print("\n\n### Importing M2 model ###")

        bl_m2 = BlenderM2Scene(m2, skins, prefs)

        bl_m2.load_materials(texture_dir)
        bl_m2.load_geosets()

    else:
        pass







