import hashlib
import os
import traceback

import bpy

from .render import update_wmo_mat_node_tree, load_wmo_shader_dependencies
from .utils.fogs import create_fog_object
from .utils.materials import load_texture, add_ghost_material
from .utils.doodads import import_doodad_model
from .wmo_scene_group import BlenderWMOSceneGroup
from ..ui import get_addon_prefs
from ..utils.misc import find_nearest_object, ProgressReport


class BlenderWMOMaterialRenderFlags:
    Unlit = 0x1
    SIDN = 0x2
    IsTwoLayered = 0x4
    IsOpaque = 0x10


class BlenderWMOScene:
    """ This class is used for assembling a Blender scene from a WNO file or saving the scene back to it."""

    def __init__(self, wmo, prefs):
        self.wmo = wmo
        self.settings = prefs
        self.material_lookup = {}

        self.bl_groups = []
        self.bl_portals = []
        self.bl_fogs = []
        self.bl_lights = []
        self.bl_liquids = []
        self.bl_doodad_sets = []

    def build_references(self, export_selected, export_method):
        """ Build WMO references in Blender scene """

        root_comps = bpy.context.scene.wow_wmo_root_components

        # process groups
        for i, slot in enumerate(root_comps.groups):

            if export_method == 'PARTIAL':
                if not slot.pointer.export:
                    continue

            elif (export_selected and not slot.pointer.select_get()) or slot.pointer.hide_viewport:
                continue

            slot.pointer.wow_wmo_group.group_id = i
            self.bl_groups.append((i, slot.pointer))

        # process portals
        for i, slot in enumerate(root_comps.portals):
            self.bl_portals.append((i, slot.pointer))
            slot.pointer.wow_wmo_portal.portal_id = i

        # process fogs
        for i, slot in enumerate(root_comps.fogs):
            self.bl_fogs.append((i, slot.pointer))
            slot.pointer.wow_wmo_fog.fog_id = i

        # process lights
        self.bl_lights = [slot.pointer for slot in root_comps.lights]

        empties = []
        scene_objects = bpy.context.scene.objects if not export_selected else bpy.context.selected_objects

        for obj in filter(lambda o: not obj.wow_wmo_doodad.enabled and not o.hide_viewport, scene_objects):

            if obj.type == 'MESH':

                if obj.wow_wmo_group.enabled:
                    self.bl_groups.append(obj)
                    obj.wow_wmo_group.group_id = len(self.bl_groups) - 1

                elif obj.wow_wmo_portal.enabled:
                    self.bl_portals.append(obj)
                    obj.wow_wmo_portal.portal_id = len(self.bl_portals) - 1

                    group_objects = (obj.wow_wmo_portal.first, obj.wow_wmo_portal.second)

                    for group_obj in group_objects:
                        if group_obj and group_obj.name in bpy.context.scene.objects:
                            rel = group_obj.wow_wmo_group.relations.portals.add()
                            rel.id = obj.name
                        else:
                            raise KeyError("Portal <<{}>> points to a non-existing object.".format(obj.name))

                elif obj.wow_wmo_fog.enabled:
                    self.bl_fogs.append(obj)
                    obj.wow_wmo_fog.fog_id = len(self.bl_fogs) - 1

                elif obj.wow_wmo_liquid.enabled:
                    self.bl_liquids.append(obj)
                    group = obj.wow_wmo_liquid.wmo_group

                    if group:
                        group.wow_wmo_group.relations.liquid = obj.name
                    else:
                        print("\nWARNING: liquid <<{}>> points to a non-existing object.".format(
                            obj.wow_wmo_liquid.wmo_group))
                        continue

            elif obj.type == 'LIGHT' and obj.data.wow_wmo_light.enabled:
                self.bl_lights.append(obj)

            elif obj.type == 'EMPTY':
                empties.append(obj)

        # sorting doodads into sets
        doodad_counter = 0
        for empty in empties:

            doodad_set = (empty.name, [])

            for doodad in empty.children:
                if doodad.wow_wmo_doodad.enabled:
                    group = find_nearest_object(doodad, self.groups)

                    if group:
                        rel = group.wow_wmo_group.relations.doodads.add()
                        rel.id = doodad_counter
                        doodad_counter += 1

                        doodad_set[1].append(doodad)

            if doodad_set[1]:
                self.bl_doodad_sets.append(doodad_set)

        # setting light references
        for index, light in enumerate(self.bl_lights):
            group = find_nearest_object(light, self.groups)
            if group:
                rel = group.wow_wmo_group.relations.lights.add()
                rel.id = index

    def clear_references(self):
        for group in self.groups:
            group.wow_wmo_group.relations.doodads.clear()
            group.wow_wmo_group.relations.lights.clear()
            group.wow_wmo_group.relations.portals.clear()
            group.wow_wmo_group.relations.liquid = ""

    def load_materials(self, texture_dir=None):
        """ Load materials from WoW WMO root file """

        addon_prefs = get_addon_prefs()

        if texture_dir is None:
            texture_dir = addon_prefs.cache_dir_path

        self.material_lookup = { 0xFF : add_ghost_material() }

        load_wmo_shader_dependencies(reload_shader=True)

        textures = {}

        for index, wmo_material in ProgressReport(list(enumerate(self.wmo.momt.materials)), msg='Importing materials'):
            texture1 = self.wmo.motx.get_string(wmo_material.texture1_ofs)
            texture2 = self.wmo.motx.get_string(wmo_material.texture2_ofs)
            material_name = os.path.basename(texture1)[:-4] + '.png'

            mat = bpy.data.materials.new(material_name)
            self.material_lookup[index] = mat

            mat.wow_wmo_material.enabled = True

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
                    mat.use_textures[0] = False
                except:
                    pass

            if texture2:

                try:
                    tex = load_texture(textures, texture2, texture_dir)
                    mat.wow_wmo_material.diff_texture_2 = tex
                    mat.use_textures[1] = False
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

    def load_lights(self):
        """ Load WoW WMO MOLT lights """

        for i, wmo_light in ProgressReport(list(enumerate(self.wmo.molt.lights)), msg='Importing lights'):

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

        for i, wmo_fog in ProgressReport(list(enumerate(self.wmo.mfog.fogs)), msg='Importing fogs'):

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

    def load_doodads(self, assets_dir=None):

        cache_path = self.settings.cache_dir_path
        doodad_prototypes = {}

        scene = bpy.context.scene

        progress = ProgressReport(self.wmo.modd.definitions, msg='Importing doodads')
        for doodad_set in self.wmo.mods.sets:

            anchor = bpy.data.objects.new(doodad_set.name, None)
            anchor.empty_display_type = 'SPHERE'

            anchor.wow_wmo_doodad_set.enabled = True
            slot = scene.wow_wmo_root_components.doodad_sets.add()
            slot.pointer = anchor

            bpy.context.collection.objects.link(anchor)
            anchor.name = doodad_set.name
            anchor.hide_viewport = True
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
                    nobj = import_doodad_model(cache_path, doodad_path)
                    doodad_prototypes[path_hash] = nobj
                else:
                    nobj = proto_obj.copy()
                    nobj.data = nobj.data.copy()

                    for j, mat in enumerate(nobj.data.materials):
                        nobj.data.materials[j] = mat.copy()

                nobj.parent = anchor
                bpy.context.collection.objects.link(nobj)
                bpy.context.view_layer.objects.active = nobj

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
                nobj.hide_viewport = True
                slot = scene.wow_wmo_root_components.doodad_sets[-1].doodads.add()
                slot.pointer = nobj

                progress.progress_step()

        progress.progress_end()

    def load_portals(self):
        """ Load WoW WMO portal planes """

        vert_count = 0
        for index, portal in ProgressReport(list(enumerate(self.wmo.mopt.infos)), msg='Importing portals'):
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

        for group in ProgressReport(self.wmo.groups, msg='Importing groups'):
            bl_group = BlenderWMOSceneGroup(self, group)
            self.bl_groups.append(bl_group)

            if not bl_group.name == 'antiportal':
                bl_group.load_object()





