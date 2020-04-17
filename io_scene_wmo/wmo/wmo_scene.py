import hashlib
import bpy
import bmesh

from mathutils import Vector
from bmesh.types import BMVert

from math import sqrt, atan2, pi
from typing import Dict, List

from .render import update_wmo_mat_node_tree, load_wmo_shader_dependencies, BlenderWMOMaterialRenderFlags
from .utils.fogs import create_fog_object
from .utils.materials import load_texture, add_ghost_material
from .utils.doodads import import_doodad
from .wmo_scene_group import BlenderWMOSceneGroup
from ..ui import get_addon_prefs
from ..utils.misc import find_nearest_object

from ..pywowlib.file_formats.wmo_format_root import GroupInfo, PortalInfo, PortalRelation, Fog
from ..pywowlib.wmo_file import WMOFile

from ..third_party.tqdm import tqdm


class BlenderWMOScene:
    """ This class is used for assembling a Blender scene from a WNO file or saving the scene back to it."""

    def __init__(self, wmo : WMOFile, prefs):
        self.wmo : WMOFile = wmo
        self.settings = prefs

        self.bl_materials   : Dict[int, bpy.types.Material]  = {}
        self.bl_groups      : List[BlenderWMOSceneGroup]     = []
        self.bl_portals     : List[bpy.types.Object]         = []
        self.bl_fogs        : List[bpy.types.Object]         = []
        self.bl_lights      : List[bpy.types.Object]         = []
        self.bl_liquids     : List[bpy.types.Object]         = []
        self.bl_doodad_sets : Dict[str, bpy.types.Object]    = {}

    def load_materials(self, texture_dir=None):
        """ Load materials from WoW WMO root file """

        addon_prefs = get_addon_prefs()

        if texture_dir is None:
            texture_dir = addon_prefs.cache_dir_path

        self.bl_materials = {0xFF : add_ghost_material()}

        if 'MO_WMOShader' not in bpy.data.node_groups:
            load_wmo_shader_dependencies(reload_shader=True)

        textures = {}

        for index, wmo_material in tqdm(list(enumerate(self.wmo.momt.materials)), desc='Importing materials', ascii=True):
            texture1 = self.wmo.motx.get_string(wmo_material.texture1_ofs)
            texture2 = self.wmo.motx.get_string(wmo_material.texture2_ofs)

            mat = bpy.data.materials.new(texture1.split('\\')[-1][:-4] + '.png')
            mat.wow_wmo_material.self_pointer = mat

            self.bl_materials[index] = mat

            try:
                mat.wow_wmo_material.shader = str(wmo_material.shader)
            except TypeError:
                print("Incorrect shader id \"{}\". Most likely badly retro-ported WMO.".format(str(wmo_material.shader)))
                mat.wow_wmo_material.shader = "0"

            mat.wow_wmo_material.blending_mode = str(wmo_material.blend_mode)
            mat.wow_wmo_material.emissive_color = [pow(x / 255, 2.2) for x in wmo_material.emissive_color]
            mat.wow_wmo_material.diff_color = [pow(x / 255, 2.2) for x in wmo_material.diff_color]
            mat.wow_wmo_material.terrain_type = str(wmo_material.terrain_type)

            mat_flags = set()
            bit = 1
            while bit <= 0x80:
                if wmo_material.flags & bit:
                    mat_flags.add(str(bit))
                bit <<= 1
            mat.wow_wmo_material.flags = mat_flags

            # create texture slots and load textures

            if texture1:
                try:
                    tex = load_texture(textures, texture1, texture_dir)
                    mat.wow_wmo_material.diff_texture_1 = tex
                except:
                    pass

            if texture2:

                try:
                    tex = load_texture(textures, texture2, texture_dir)
                    mat.wow_wmo_material.diff_texture_2 = tex
                except:
                    pass

            update_wmo_mat_node_tree(mat)

            # set render flags
            pass_index = 0

            if wmo_material.flags & 0x1:
                pass_index |= BlenderWMOMaterialRenderFlags.Unlit

            if wmo_material.flags & 0x10:
                pass_index |= BlenderWMOMaterialRenderFlags.SIDN

            if wmo_material.shader in (3, 5, 6, 7, 8, 9, 11, 12, 13, 15):
                pass_index |= BlenderWMOMaterialRenderFlags.IsTwoLayered

            if wmo_material.blend_mode in (0, 8, 9):
                pass_index |= BlenderWMOMaterialRenderFlags.IsOpaque

            # configure blending
            if wmo_material.blend_mode in (0, 8, 9):
                mat.blend_method = 'OPAQUE'
            elif wmo_material.blend_mode == 1:
                mat.blend_method = 'CLIP'
                mat.alpha_threshold = 0.9
            elif wmo_material.blend_mode in (3, 7, 10):
                mat.blend_method = 'ADD'
            elif wmo_material.blend_mode in (4, 5):
                mat.blend_method = 'MULTIPLY'
            else:
                mat.blend_method = 'BLEND'

            mat.pass_index = pass_index

            slot = bpy.context.scene.wow_wmo_root_elements.materials.add()
            slot.pointer = mat

    def load_lights(self):
        """ Load WoW WMO MOLT lights """

        for i, wmo_light in tqdm(list(enumerate(self.wmo.molt.lights)), desc='Importing lights', ascii=True):

            bl_light_types = ['POINT', 'SPOT', 'SUN', 'POINT']

            try:
                l_type = bl_light_types[wmo_light.light_type]
            except IndexError:
                raise Exception("Light type unknown : {} (light nbr : {})".format(str(wmo_light.LightType), str(i)))

            light_name = "{}_Light_{}".format(self.wmo.display_name, str(i).zfill(2))

            light = bpy.data.lights.new(light_name, l_type)
            obj = bpy.data.objects.new(light_name, light)
            obj.location = self.wmo.molt.lights[i].position

            light.color = (wmo_light.color[2] / 255, wmo_light.color[1] / 255, wmo_light.color[0] / 255)
            light.energy = wmo_light.intensity

            if wmo_light.light_type in {0, 1}:
                light.falloff_type = 'INVERSE_LINEAR'
                light.distance = wmo_light.unknown4 / 2

            obj.wow_wmo_light.enabled = True
            obj.wow_wmo_light.light_type = str(wmo_light.light_type)
            obj.wow_wmo_light.type = bool(wmo_light.type)
            obj.wow_wmo_light.use_attenuation = bool(wmo_light.use_attenuation)
            obj.wow_wmo_light.padding = bool(wmo_light.padding)
            obj.wow_wmo_light.type = bool(wmo_light.type)
            obj.wow_wmo_light.color = light.color
            obj.wow_wmo_light.color_alpha = wmo_light.color[3] / 255
            obj.wow_wmo_light.intensity = wmo_light.intensity
            obj.wow_wmo_light.attenuation_start = wmo_light.attenuation_start
            obj.wow_wmo_light.attenuation_end = wmo_light.attenuation_end

            bpy.context.collection.objects.link(obj)

            self.bl_lights.append(light)

    def load_fogs(self):
        """ Load fogs from WMO Root File"""

        for i, wmo_fog in tqdm(list(enumerate(self.wmo.mfog.fogs)), desc='Importing fogs', ascii=True):

            fog_obj = create_fog_object(  name="{}_Fog_{}".format(self.wmo.display_name, str(i).zfill(2))
                                        , location=wmo_fog.position
                                        , radius=wmo_fog.big_radius
                                        , color=(wmo_fog.color1[2] / 255,
                                                 wmo_fog.color1[1] / 255,
                                                 wmo_fog.color1[0] / 255,
                                                 0.0
                                                )
                                        )

            # applying object properties

            fog_obj.wow_wmo_fog.enabled = True
            fog_obj.wow_wmo_fog.ignore_radius = wmo_fog.flags & 0x01
            fog_obj.wow_wmo_fog.unknown = wmo_fog.flags & 0x10

            if wmo_fog.small_radius != 0:
                fog_obj.wow_wmo_fog.inner_radius = int(wmo_fog.small_radius / wmo_fog.big_radius * 100)
            else:
                fog_obj.wow_wmo_fog.inner_radius = 0

            fog_obj.wow_wmo_fog.end_dist = wmo_fog.end_dist
            fog_obj.wow_wmo_fog.start_factor = wmo_fog.start_factor
            fog_obj.wow_wmo_fog.color1 = (wmo_fog.color1[2] / 255, wmo_fog.color1[1] / 255, wmo_fog.color1[0] / 255)
            fog_obj.wow_wmo_fog.end_dist2 = wmo_fog.end_dist
            fog_obj.wow_wmo_fog.start_factor2 = wmo_fog.start_factor2
            fog_obj.wow_wmo_fog.color2 = (wmo_fog.color2[2] / 255, wmo_fog.color2[1] / 255, wmo_fog.color2[0] / 255)

            self.bl_fogs.append(fog_obj)

    def load_doodads(self):

        cache_path = self.settings.cache_dir_path
        doodad_prototypes = {}

        scene = bpy.context.scene

        with tqdm(self.wmo.modd.definitions, desc='Importing doodads', ascii=True) as progress:
            for doodad_set in self.wmo.mods.sets:

                anchor = bpy.data.objects.new(doodad_set.name, None)
                anchor.empty_display_type = 'SPHERE'

                anchor.wow_wmo_doodad_set.enabled = True
                slot = scene.wow_wmo_root_elements.doodad_sets.add()
                slot.pointer = anchor

                bpy.context.collection.objects.link(anchor)
                anchor.name = doodad_set.name
                anchor.hide_set(True)
                anchor.hide_select = True
                anchor.lock_location = (True, True, True)
                anchor.lock_rotation = (True, True, True)
                anchor.lock_scale = (True, True, True)

                for i in range(doodad_set.start_doodad, doodad_set.start_doodad + doodad_set.n_doodads):
                    doodad = self.wmo.modd.definitions[i]

                    doodad_path = self.wmo.modn.get_string(doodad.name_ofs)
                    path_hash = str(hashlib.md5(doodad_path.encode('utf-8')).hexdigest())

                    proto_obj = doodad_prototypes.get(path_hash)

                    if not proto_obj:
                        nobj = import_doodad(doodad_path, cache_path)
                        doodad_prototypes[path_hash] = nobj
                    else:
                        nobj = proto_obj.copy()
                        nobj.data = nobj.data.copy()

                        for j, mat in enumerate(nobj.data.materials):
                            nobj.data.materials[j] = mat.copy()

                    nobj.parent = anchor
                    bpy.context.collection.objects.link(nobj)
                    bpy.context.view_layer.objects.active = nobj

                    nobj.wow_wmo_doodad.self_pointer = nobj
                    nobj.wow_wmo_doodad.color = (pow(doodad.color[2] / 255, 2.2),
                                                 pow(doodad.color[1] / 255, 2.2),
                                                 pow(doodad.color[0] / 255, 2.2),
                                                 pow(doodad.color[3] / 255, 2.2)
                                                )

                    flags = []
                    bit = 1
                    while bit <= 0x8:
                        if doodad.flags & bit:
                            flags.append(str(bit))
                        bit <<= 1

                    nobj.wow_wmo_doodad.flags = set(flags)

                    # place the object correctly on the scene
                    nobj.location = doodad.position
                    nobj.scale = (doodad.scale, doodad.scale, doodad.scale)

                    nobj.rotation_mode = 'QUATERNION'
                    nobj.rotation_quaternion = (doodad.rotation[3],
                                                doodad.rotation[0],
                                                doodad.rotation[1],
                                                doodad.rotation[2])
                    nobj.hide_set(True)
                    slot = scene.wow_wmo_root_elements.doodad_sets[-1].doodads.add()
                    slot.pointer = nobj

                    progress.update(1)

    def load_portals(self):
        """ Load WoW WMO portal planes """

        vert_count = 0
        for index, portal in tqdm(list(enumerate(self.wmo.mopt.infos)), desc='Importing portals', ascii=True):
            portal_name = "{}_Portal_{}".format(self.wmo.display_name, str(index).zfill(3))

            verts = []
            face = []
            faces = []

            for j in range(portal.n_vertices):
                if len(face) < 4:
                    verts.append(self.wmo.mopv.portal_vertices[vert_count])
                    face.append(j)
                vert_count += 1

            faces.append(face)

            mesh = bpy.data.meshes.new(portal_name)

            obj = bpy.data.objects.new(portal_name, mesh)

            obj.wow_wmo_portal.enabled = True
            first_relationship = True

            for relation in self.wmo.mopr.relations:
                if relation.portal_index == index:
                    group_name = self.wmo.mogn.get_string(
                        self.bl_groups[relation.group_index].wmo_group.mogp.group_name_ofs)

                    if first_relationship:
                        obj.wow_wmo_portal.first = bpy.context.scene.objects[group_name]
                        first_relationship = False
                    else:
                        obj.wow_wmo_portal.second = bpy.context.scene.objects[group_name]
                        break

            mesh.from_pydata(verts, [], faces)
            bpy.context.collection.objects.link(obj)

            self.bl_portals.append(obj)

    def load_properties(self):
        """ Load global WoW WMO properties """
        properties = bpy.context.scene.wow_wmo_root
        properties.ambient_color = (pow(self.wmo.mohd.ambient_color[2] / 255, 2.2),
                                    pow(self.wmo.mohd.ambient_color[1] / 255, 2.2),
                                    pow(self.wmo.mohd.ambient_color[0] / 255, 2.2),
                                    pow(self.wmo.mohd.ambient_color[3] / 255, 2.2))

        flags = set()
        if self.wmo.mohd.flags & 0x1:
            flags.add("0")
        if self.wmo.mohd.flags & 0x2:
            flags.add("2")
        if self.wmo.mohd.flags & 0x8:
            flags.add("1")

        properties.flags = flags
        properties.skybox_path = self.wmo.mosb.skybox
        properties.wmo_id = self.wmo.mohd.id

    def load_groups(self):

        for group in tqdm(self.wmo.groups, desc='Importing groups', ascii=True):
            bl_group = BlenderWMOSceneGroup(self, group)
            self.bl_groups.append(bl_group)

            if not bl_group.name == 'antiportal':
                bl_group.load_object()

    def build_references(self, export_selected, export_method):
        """ Build WMO references in Blender scene """

        root_elements = bpy.context.scene.wow_wmo_root_elements

        # process materials
        for i, slot in enumerate(root_elements.materials):
            if not slot.pointer:
                raise ReferenceError('\nError saving WMO. Material slot does not point to a valid material.')

            self.bl_materials[i] = slot.pointer

        # process groups
        group_objects = []
        for i, slot in enumerate(root_elements.groups):

            if (export_selected and not slot.pointer.select_get()) or slot.pointer.hide_get():
                continue

            slot.pointer.wow_wmo_group.group_id = i

            slot.pointer.wow_wmo_group.relations.doodads.clear()
            slot.pointer.wow_wmo_group.relations.lights.clear()
            slot.pointer.wow_wmo_group.relations.portals.clear()

            group = self.wmo.add_group()
            self.bl_groups.append(BlenderWMOSceneGroup(self, group, obj=slot.pointer))
            group_objects.append(slot.pointer)

            group.export = not (export_method == 'PARTIAL' and not slot.export)

        # process portals
        for i, slot in enumerate(root_elements.portals):
            self.bl_portals.append(slot.pointer)
            slot.pointer.wow_wmo_portal.portal_id = i

            if not slot.pointer.wow_wmo_portal.first or not slot.pointer.wow_wmo_portal.second:
                raise ReferenceError('\nError saving WMO. '
                                     'Portal \"{}\" points to a non-existing group.'.format(slot.pointer.name))

            rel = slot.pointer.wow_wmo_portal.first.wow_wmo_group.relations.portals.add()
            rel.id = slot.pointer.name  # TODO: store pointer instead?

            rel = slot.pointer.wow_wmo_portal.second.wow_wmo_group.relations.portals.add()
            rel.id = slot.pointer.name  # TODO: store pointer instead?

        # process fogs
        for i, slot in enumerate(root_elements.fogs):
            self.bl_fogs.append(slot.pointer)
            slot.pointer.wow_wmo_fog.fog_id = i

        # process lights
        for i, slot in enumerate(root_elements.lights):
            group = find_nearest_object(slot.pointer, group_objects)
            rel = group.wow_wmo_group.relations.lights.add()
            rel.id = i

            self.bl_lights.append(slot.pointer)

        # process doodads
        doodad_counter = 0
        for i, slot in enumerate(root_elements.doodad_sets):

            doodads = []
            for doodad in slot.doodads:
                group = find_nearest_object(doodad.pointer, group_objects)
                rel = group.wow_wmo_group.relations.doodads.add()
                rel.id = doodad_counter
                doodad_counter += 1

                doodads.append(doodad.pointer)

            self.bl_doodad_sets[slot.name] = doodads

    def save_materials(self):
        """ Add material if not already added, then return index in root file """

        for i, mat_slot in tqdm( enumerate(bpy.context.scene.wow_wmo_root_elements.materials)
                                         , desc='Saving materials'
                                         , ascii=True
                                         ):

            mat = mat_slot.pointer

            if not mat.wow_wmo_material.diff_texture_1:
                raise ReferenceError('\nError saving WMO. Material \"{}\" must have a diffuse texture.'.format(mat.name))

            diff_texture_1 = mat.wow_wmo_material.diff_texture_1.wow_wmo_texture.path

            diff_texture_2 = mat.wow_wmo_material.diff_texture_2.wow_wmo_texture.path if mat.wow_wmo_material.diff_texture_2 else ""

            flags = 0

            for flag in mat.wow_wmo_material.flags:
                flags |= int(flag)

            self.wmo.add_material(  diff_texture_1
                                  , diff_texture_2
                                  , int(mat.wow_wmo_material.shader)
                                  , int(mat.wow_wmo_material.blending_mode)
                                  , int(mat.wow_wmo_material.terrain_type)
                                  , flags
                                  , ( int(mat.wow_wmo_material.emissive_color[0] * 255),
                                      int(mat.wow_wmo_material.emissive_color[1] * 255),
                                      int(mat.wow_wmo_material.emissive_color[2] * 255),
                                      int(mat.wow_wmo_material.emissive_color[3] * 255)
                                    )
                                  , ( int(mat.wow_wmo_material.diff_color[0] * 255),
                                      int(mat.wow_wmo_material.diff_color[1] * 255),
                                      int(mat.wow_wmo_material.diff_color[2] * 255),
                                      int(mat.wow_wmo_material.diff_color[3] * 255)
                                    )
                                 )

    def add_group_info(self, flags, bounding_box, name, desc):
        """ Add group info, then return offset of name and desc in a tuple """
        group_info = GroupInfo()

        group_info.flags = flags  # 8
        group_info.bounding_box_corner1 = bounding_box[0].copy()
        group_info.bounding_box_corner2 = bounding_box[1].copy()
        group_info.name_ofs = self.wmo.mogn.add_string(name)  # 0xFFFFFFFF

        desc_ofs = self.wmo.mogn.add_string(desc)

        self.wmo.mogi.infos.append(group_info)

        return group_info.name_ofs, desc_ofs

    def save_doodad_sets(self):
        """ Save doodads data from Blender scene to WMO root """

        has_global = False

        if len(self.bl_doodad_sets):

            for set_name, doodads in tqdm(self.bl_doodad_sets.items(), desc='Saving doodad sets', ascii=True):

                self.wmo.add_doodad_set(set_name, len(doodads))

                for doodad in doodads:

                    path = doodad.wow_wmo_doodad.path

                    position = (doodad.matrix_world @ Vector((0, 0, 0))).to_tuple()

                    doodad.rotation_mode = 'QUATERNION'
                    rotation = (doodad.rotation_quaternion[1],
                                doodad.rotation_quaternion[2],
                                doodad.rotation_quaternion[3],
                                doodad.rotation_quaternion[0])

                    scale = doodad.scale[0]

                    doodad_color = [int(pow(channel, 10 / 22) * 255) for channel in doodad.wow_wmo_doodad.color]
                    doodad_color = (doodad_color[2], doodad_color[1], doodad_color[0], doodad_color[3])

                    flags = 0
                    for flag in doodad.wow_wmo_doodad.flags:
                        flags |= int(flag)

                    self.wmo.add_doodad(path, position, rotation, scale, doodad_color, flags)

            if set_name == "Set_$DefaultGlobal":
                has_global = True

        if not has_global:
            self.wmo.add_doodad_set("Set_$DefaultGlobal", 0)

    def save_lights(self):

        for obj in tqdm(self.bl_lights, desc='Saving lights', ascii=True):

            light_type = int(obj.wow_wmo_light.light_type)

            unk1 = obj.data.distance * 2

            unk2 = obj.wow_wmo_light.type
            use_attenuation = obj.wow_wmo_light.use_attenuation
            padding = obj.wow_wmo_light.padding

            color = (int(obj.wow_wmo_light.color[2] * 255),
                     int(obj.wow_wmo_light.color[1] * 255),
                     int(obj.wow_wmo_light.color[0] * 255),
                     int(obj.wow_wmo_light.color_alpha * 255))

            position = obj.location.to_tuple()
            intensity = obj.wow_wmo_light.intensity
            attenuation_start = obj.wow_wmo_light.attenuation_start
            attenuation_end = obj.wow_wmo_light.attenuation_end

            self.wmo.add_light(light_type, unk1, unk2, use_attenuation, padding, color,
                               position, intensity, attenuation_start, attenuation_end)

    @staticmethod
    def get_angle(vec_a: Vector, vec_b: Vector, vec_n: Vector) -> float:
        return atan2(
            -(vec_a.x * vec_b.y * vec_n.z + vec_b.x * vec_n.y * vec_a.z + vec_n.x * vec_a.y * vec_b.z
              - vec_a.z * vec_b.y * vec_n.x - vec_b.z * vec_n.y * vec_a.x - vec_n.z * vec_a.y * vec_b.x),
            -(vec_a.x * vec_b.x + vec_a.y * vec_b.y + vec_a.z * vec_b.z)) + pi

    @staticmethod
    def traverse(  cur_vtx: BMVert
                 , nodes_to_hit: List
                 , nodes_hit: List
                 , origin: BMVert) -> List:

        for edge in cur_vtx.link_edges:

            other = edge.other_vert(cur_vtx)

            if other == origin:
                if not nodes_to_hit:
                    return nodes_hit
                else:
                    continue

            if other in nodes_hit:
                continue

            nodes_to_hit_new = nodes_to_hit.copy()
            nodes_to_hit_new.remove(other)

            nodes_hit_new = nodes_hit.copy()
            nodes_hit_new.append(other)

            result = BlenderWMOScene.traverse(other, nodes_to_hit_new, nodes_hit_new, origin)

            if result:
                return result

        return []

    @staticmethod
    def sort_portal_vertices(vertices: List[BMVert], normal: Vector) -> List[BMVert]:

        pos_n = Vector((0, 0, 0))
        origin = None

        for vtx in vertices:
            if len(vtx.link_edges) == 2 and origin is None:
                origin = vtx
            pos_n += vtx.co

        pos_n /= len(vertices)
        vtx_a = origin.link_edges[0].other_vert(origin)
        vtx_b = origin.link_edges[1].other_vert(origin)
        vector_o = origin.co - pos_n
        next_vtx = vtx_b if BlenderWMOScene.get_angle(vtx_a.co - pos_n, vector_o, normal) \
                            < BlenderWMOScene.get_angle(vtx_b.co - pos_n, vector_o, normal) else vtx_a

        # traversing mesh
        nodes_to_hit = list(vertices).copy()
        nodes_to_hit.remove(origin)
        nodes_to_hit.remove(next_vtx)

        nodes_hit = [origin, next_vtx]
        result = BlenderWMOScene.traverse(next_vtx, nodes_to_hit, nodes_hit, origin)

        return result

    def save_portals(self):

        saved_portals_ids = []

        self.wmo.mopt.infos = len(self.bl_portals) * [PortalInfo()]

        for bl_group in tqdm(self.bl_groups, desc='Saving portals', ascii=True):

            group_obj = bl_group.bl_object
            portal_relations = group_obj.wow_wmo_group.relations.portals
            bl_group.wmo_group.mogp.portal_start = len(self.wmo.mopr.relations)

            for relation in portal_relations:
                portal_obj = bpy.context.scene.objects[relation.id]
                portal_index = portal_obj.wow_wmo_portal.portal_id

                if portal_index not in saved_portals_ids:

                    portal_mesh = portal_obj.data
                    portal_info = PortalInfo()
                    portal_info.start_vertex = len(self.wmo.mopv.portal_vertices)
                    v = []

                    bm = bmesh.new()
                    bm.from_mesh(portal_mesh)

                    portal_verts = self.sort_portal_vertices(bm.verts, portal_mesh.polygons[0].normal)

                    for vertex in portal_verts:
                        vertex_pos = portal_obj.matrix_world @ vertex.co
                        self.wmo.mopv.portal_vertices.append(vertex_pos.to_tuple())
                        v.append(vertex_pos)

                    bm.free()

                    v_A = v[0][1] * v[1][2] - v[1][1] * v[0][2] - v[0][1] * v[2][2] + v[2][1] * v[0][2] + v[1][1] * \
                          v[2][2] - \
                          v[2][1] * v[1][2]
                    v_B = -v[0][0] * v[1][2] + v[2][0] * v[1][2] + v[1][0] * v[0][2] - v[2][0] * v[0][2] - v[1][0] * \
                          v[2][2] + \
                          v[0][0] * v[2][2]
                    v_C = v[2][0] * v[0][1] - v[1][0] * v[0][1] - v[0][0] * v[2][1] + v[1][0] * v[2][1] - v[2][0] * \
                          v[1][1] + \
                          v[0][0] * v[1][1]
                    v_D = -v[0][0] * v[1][1] * v[2][2] + v[0][0] * v[2][1] * v[1][2] + v[1][0] * v[0][1] * v[2][2] - \
                          v[1][0] * \
                          v[2][1] * v[0][2] - v[2][0] * v[0][1] * v[1][2] + v[2][0] * v[1][1] * v[0][2]

                    portal_info.unknown = v_D / sqrt(v_A * v_A + v_B * v_B + v_C * v_C)
                    portal_info.n_vertices = len(self.wmo.mopv.portal_vertices) - portal_info.start_vertex
                    portal_info.normal = tuple(portal_mesh.polygons[0].normal)

                    self.wmo.mopt.infos[portal_index] = portal_info
                    saved_portals_ids.append(portal_index)

                first = self.bl_portals[portal_index].wow_wmo_portal.first
                second = self.bl_portals[portal_index].wow_wmo_portal.second

                # calculating portal relation
                relation = PortalRelation()
                relation.portal_index = portal_index
                relation.group_index = second.wow_wmo_group.group_id if first.name == group_obj.name \
                                                                     else first.wow_wmo_group.group_id

                relation.side = bl_group.get_portal_direction(portal_obj, group_obj)

                self.wmo.mopr.relations.append(relation)

            bl_group.wmo_group.mogp.portal_count = len(self.wmo.mopr.relations) - bl_group.wmo_group.mogp.portal_start

    def save_groups(self):

        for bl_group in tqdm(self.bl_groups, desc='Saving groups', ascii=True):

            if bl_group.wmo_group.export:
                bl_group.save()

    def save_fogs(self):

        for fog_obj in tqdm(self.bl_fogs, desc='Saving fogs', ascii=True):

            big_radius = fog_obj.dimensions[2] / 2
            small_radius = big_radius * (fog_obj.wow_wmo_fog.inner_radius / 100)

            color1 = (int(fog_obj.wow_wmo_fog.color1[2] * 255),
                          int(fog_obj.wow_wmo_fog.color1[1] * 255),
                          int(fog_obj.wow_wmo_fog.color1[0] * 255),
                          0xFF)

            color2 = (int(fog_obj.wow_wmo_fog.color2[2] * 255),
                          int(fog_obj.wow_wmo_fog.color2[1] * 255),
                          int(fog_obj.wow_wmo_fog.color2[0] * 255),
                          0xFF)

            end_dist = fog_obj.wow_wmo_fog.end_dist
            end_dist2 = fog_obj.wow_wmo_fog.end_dist2
            position = fog_obj.location.to_tuple()
            start_factor = fog_obj.wow_wmo_fog.start_factor
            start_factor2 = fog_obj.wow_wmo_fog.start_factor2

            flags = 0
            if fog_obj.wow_wmo_fog.ignore_radius:
                flags |= 0x01
            if fog_obj.wow_wmo_fog.unknown:
                flags |= 0x10

            self.wmo.add_fog(big_radius, small_radius, color1, color2, end_dist, end_dist2, position,
                             start_factor, start_factor2, flags)

    def save_root_header(self):

        scene = bpy.context.scene

        self.wmo.mver.version = 17

        # setting up default fog with default blizzlike values.
        if not len(self.wmo.mfog.fogs):
            empty_fog = Fog()
            empty_fog.color1 = (0xFF, 0xFF, 0xFF, 0xFF)
            empty_fog.color2 = (0x00, 0x00, 0x00, 0xFF)
            empty_fog.end_dist = 444.4445
            empty_fog.end_dist2 = 222.2222
            empty_fog.start_factor = 0.25
            empty_fog.start_factor2 = -0.5
            self.wmo.mfog.fogs.append(empty_fog)

        bb = self.wmo.get_global_bounding_box()
        self.wmo.mohd.bounding_box_corner1 = bb[0]
        self.wmo.mohd.bounding_box_corner2 = bb[1]

        # DBC foreign keys
        self.wmo.mohd.id = scene.wow_wmo_root.wmo_id
        self.wmo.mosb.skybox = scene.wow_wmo_root.skybox_path

        self.wmo.mohd.ambient_color = [int(scene.wow_wmo_root.ambient_color[2] * 255),
                                       int(scene.wow_wmo_root.ambient_color[1] * 255),
                                       int(scene.wow_wmo_root.ambient_color[0] * 255),
                                       int(scene.wow_wmo_root.ambient_color[3] * 255)]

        self.wmo.mohd.n_materials = len(self.wmo.momt.materials)
        self.wmo.mohd.n_groups = len(self.wmo.mogi.infos)
        self.wmo.mohd.n_portals = len(self.wmo.mopt.infos)
        self.wmo.mohd.n_models = self.wmo.modn.string_table.decode("ascii").count('.MDX')
        self.wmo.mohd.n_lights = len(self.wmo.molt.lights)
        self.wmo.mohd.n_doodads = len(self.wmo.modd.definitions)
        self.wmo.mohd.n_sets = len(self.wmo.mods.sets)

        flags = scene.wow_wmo_root.flags
        if "0" in flags:
            self.wmo.mohd.flags |= 0x01
        if "2" in flags:
            self.wmo.mohd.flags |= 0x02
        if "1" in flags:
            self.wmo.mohd.flags |= 0x08

        self.wmo.mohd.flags |= 0x4






