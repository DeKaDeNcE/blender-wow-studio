import bpy
import traceback
import os
import hashlib

from .wmo_scene_group import BlenderWMOSceneGroup
from ..ui import get_addon_prefs
from .import_doodad import import_doodad
from ..utils import find_nearest_object, ProgressReport
from .render import update_wmo_mat_node_tree, load_wmo_shader_dependencies


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

    def build_references(self, export_selected):
        """ Build WMO references in Blender scene """

        empties = []
        scene_objects = bpy.context.scene.objects if not export_selected else bpy.context.selected_objects

        for obj in filter(lambda o: not obj.wow_wmo_doodad.enabled and not o.hide, scene_objects):

            if obj.type == 'MESH':

                if obj.wow_wmo_group.enabled:
                    self.groups.append(obj)
                    obj.wow_wmo_group.group_id = len(self.groups) - 1

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

            elif obj.type == 'LAMP' and obj.data.wow_wmo_light.enabled:
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

        def _load_texture(textures, filename, texture_dir):

            new_filename = os.path.splitext(filename)[0] + '.png'

            if os.name != 'nt':
                new_filename = new_filename.replace('\\', '/')

            tex1_name = os.path.basename(new_filename)

            texture = None

            # check if texture is already loaded
            for tex_name, tex in textures.items():
                if tex_name == filename:
                    texture = tex
                    break

            # if image is not loaded, do it
            if not texture:
                texture = bpy.data.textures.new(tex1_name, 'IMAGE')
                texture.wow_wmo_texture.path = filename
                tex1_img = bpy.data.images.load(os.path.join(texture_dir, new_filename))
                texture.image = tex1_img

                textures[filename] = texture

            return texture

        addon_prefs = get_addon_prefs()

        if texture_dir is None:
            texture_dir = addon_prefs.cache_dir_path

        self.material_lookup = {}

        # Add ghost material
        mat = bpy.data.materials.get("WowMaterial_ghost")
        if not mat:
            mat = bpy.data.materials.new("WowMaterial_ghost")
            mat.diffuse_color = (0.2, 0.5, 1.0)
            mat.diffuse_intensity = 1.0
            mat.alpha = 0.15
            mat.transparency_method = 'Z_TRANSPARENCY'
            mat.use_transparency = True

        self.material_lookup[0xFF] = mat

        load_wmo_shader_dependencies(reload_shader=True)

        textures = {}

        for index, wmo_material in ProgressReport(list(enumerate(self.wmo.momt.materials)), msg='Importing materials'):
            texture1 = self.wmo.motx.get_string(wmo_material.texture1_ofs)
            texture2 = self.wmo.motx.get_string(wmo_material.texture2_ofs)
            material_name = os.path.basename(texture1)[:-4] + '.png'

            mat = bpy.data.materials.new(material_name)
            self.material_lookup[index] = mat

            mat.wow_wmo_material.enabled = True
            mat.wow_wmo_material.shader = str(wmo_material.shader)
            mat.wow_wmo_material.blending_mode = str(wmo_material.blend_mode)
            mat.wow_wmo_material.emissive_color = [pow(x / 255, 1 / 2.2) for x in wmo_material.emissive_color]
            mat.wow_wmo_material.diff_color = [pow(x / 255, 1 / 2.2) for x in wmo_material.diff_color]
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
                tex_slot = mat.texture_slots.create(0)
                tex_slot.uv_layer = "UVMap"
                tex_slot.texture_coords = 'UV'

                try:
                    tex = _load_texture(textures, texture1, texture_dir)
                    tex_slot.texture = tex
                    mat.wow_wmo_material.diff_texture_1 = tex
                except:
                    pass

            if texture2:
                tex_slot = mat.texture_slots.create(0)
                tex_slot.uv_layer = "UVMap"
                tex_slot.texture_coords = 'UV'

                try:
                    tex = _load_texture(textures, texture2, texture_dir)
                    tex_slot.texture = tex
                    mat.wow_wmo_material.diff_texture_2 = tex
                except:
                    pass

            update_wmo_mat_node_tree(mat)

    def load_lights(self):
        """ Load WoW WMO MOLT lights """

        for i, wmo_light in ProgressReport(list(enumerate(self.wmo.molt.lights)), msg='Importing lights'):

            bl_light_types = ['POINT', 'SPOT', 'SUN', 'POINT']

            try:
                l_type = bl_light_types[wmo_light.light_type]
            except IndexError:
                raise Exception("Light type unknown : {} (light nbr : {})".format(str(wmo_light.LightType), str(i)))

            light_name = "{}_Light_{}".format(self.wmo.display_name, str(i).zfill(2))
            light = bpy.data.lamps.new(light_name, l_type)
            light.color = (wmo_light.color[2] / 255, wmo_light.color[1] / 255, wmo_light.color[0] / 255)
            light.energy = wmo_light.intensity

            if wmo_light.light_type in {0, 1}:
                light.falloff_type = 'INVERSE_LINEAR'
                light.distance = wmo_light.unknown4 / 2
                light.use_sphere = True

            light.wow_wmo_light.enabled = True
            light.wow_wmo_light.light_type = str(wmo_light.light_type)
            light.wow_wmo_light.type = bool(wmo_light.type)
            light.wow_wmo_light.use_attenuation = bool(wmo_light.use_attenuation)
            light.wow_wmo_light.padding = bool(wmo_light.padding)
            light.wow_wmo_light.type = bool(wmo_light.type)
            light.wow_wmo_light.color = light.color
            light.wow_wmo_light.color_alpha = wmo_light.color[3] / 255
            light.wow_wmo_light.intensity = wmo_light.intensity
            light.wow_wmo_light.attenuation_start = wmo_light.attenuation_start
            light.wow_wmo_light.attenuation_end = wmo_light.attenuation_end

            obj = bpy.data.objects.new(light_name, light)
            obj.location = self.wmo.molt.lights[i].position

            bpy.context.scene.objects.link(obj)

            self.bl_lights.append(light)

    def load_fogs(self):
        """ Load fogs from WMO Root File"""

        for i, wmo_fog in ProgressReport(list(enumerate(self.wmo.mfog.fogs)), msg='Importing fogs'):
            bpy.ops.mesh.primitive_uv_sphere_add()
            fog = bpy.context.scene.objects.active

            if not wmo_fog.big_radius:
                fog.hide = False

            fog.name = "{}_Fog_{}".format(self.wmo.display_name, str(i).zfill(2))

            # applying real object transformation
            fog.location = wmo_fog.position
            bpy.ops.transform.resize(value=(wmo_fog.big_radius, wmo_fog.big_radius, wmo_fog.big_radius))  # 0.5 is the default sphere radius

            bpy.ops.object.shade_smooth()
            fog.draw_type = 'SOLID'
            fog.show_transparent = True
            fog.show_name = True
            fog.color = (wmo_fog.color1[2] / 255, wmo_fog.color1[1] / 255, wmo_fog.color1[0] / 255, 0.0)

            mesh = fog.data

            material = bpy.data.materials.new(name=fog.name)

            if mesh.materials:
                mesh.materials[0] = material
            else:
                mesh.materials.append(material)

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.object.material_slot_assign()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')

            mesh.materials[0].use_object_color = True
            mesh.materials[0].use_transparency = True
            mesh.materials[0].alpha = 0.35

            # applying object properties

            fog.wow_wmo_fog.enabled = True
            if wmo_fog.flags & 0x01:
                fog.wow_wmo_fog.ignore_radius = True
            if wmo_fog.flags & 0x10:
                fog.wow_wmo_fog.unknown = True

            if wmo_fog.small_radius != 0:
                fog.wow_wmo_fog.inner_radius = int(wmo_fog.small_radius / wmo_fog.big_radius * 100)
            else:
                fog.wow_wmo_fog.inner_radius = 0

            fog.wow_wmo_fog.end_dist = wmo_fog.end_dist
            fog.wow_wmo_fog.start_factor = wmo_fog.start_factor
            fog.wow_wmo_fog.color1 = (wmo_fog.color1[2] / 255, wmo_fog.color1[1] / 255, wmo_fog.color1[0] / 255)
            fog.wow_wmo_fog.end_dist2 = wmo_fog.end_dist
            fog.wow_wmo_fog.start_factor2 = wmo_fog.start_factor2
            fog.wow_wmo_fog.color2 = (wmo_fog.color2[2] / 255, wmo_fog.color2[1] / 255, wmo_fog.color2[0] / 255)

            self.bl_fogs.append(fog)

    def load_doodads(self, assets_dir=None):

        cache_path = self.settings.cache_dir_path

        for doodad_name in ProgressReport(self.wmo.modn.get_all_strings(), msg='Importing doodad prototypes'):
            doodad_path_noext = os.path.splitext(doodad_name)[0]
            doodad_path = doodad_path_noext + ".m2"
            library_path = os.path.join(cache_path, doodad_path_noext + '.blend')

            path_hash = str(hashlib.md5(doodad_path.encode('utf-8')).hexdigest())

            obj = bpy.data.objects.get(path_hash)

            if not obj:

                if not os.path.exists(library_path):
                    library_dir = os.path.split(library_path)[0]
                    if not os.path.exists(library_dir):
                        os.makedirs(library_dir)

                    try:
                        p_obj = import_doodad(assets_dir, doodad_path)
                    except:
                        p_obj = import_doodad(assets_dir, 'Spells\\Errorcube.m2')
                        p_obj.wow_wmo_doodad.path = doodad_path
                        p_obj.name = path_hash
                        traceback.print_exc()
                        print("\nFailed to import model: <<{}>>. Placeholder is imported instead.".format(doodad_path))

                    bpy.data.libraries.write(library_path, {p_obj}, fake_user=True)
                    bpy.data.objects.remove(p_obj)

                with bpy.data.libraries.load(library_path, link=True) as (data_from, data_to):
                    data_to.objects = [ob_name for ob_name in data_from.objects if ob_name == path_hash]

                obj = data_to.objects[0]

                assert obj is not None

            elif obj.library is None:
                raise Exception('\nNon-library doodad data-block collision ({})'.format(path_hash))

        scene = bpy.context.scene

        progress = ProgressReport(self.wmo.modd.definitions, msg='Importing doodads')
        for doodad_set in self.wmo.mods.sets:

            anchor = bpy.data.objects.new(doodad_set.name, None)
            anchor.empty_draw_type = 'SPHERE'
            bpy.context.scene.objects.link(anchor)
            anchor.name = doodad_set.name
            anchor.hide = True
            anchor.hide_select = True
            anchor.lock_location = (True, True, True)
            anchor.lock_rotation = (True, True, True)
            anchor.lock_scale = (True, True, True)

            for i in range(doodad_set.start_doodad, doodad_set.start_doodad + doodad_set.n_doodads):
                doodad = self.wmo.modd.definitions[i]

                doodad_path_noext = os.path.splitext(self.wmo.modn.get_string(doodad.name_ofs))[0]
                doodad_path = doodad_path_noext + ".m2"
                doodad_basename = os.path.basename(doodad_path_noext)
                path_hash = str(hashlib.md5(doodad_path.encode('utf-8')).hexdigest())

                proto_obj = bpy.data.objects.get(path_hash)

                if not proto_obj:
                    raise FileNotFoundError('\nWMO is referencing non-existing doodad.')

                nobj = bpy.data.objects.new(doodad_basename, proto_obj.data)
                scene.objects.link(nobj)

                nobj.wow_wmo_doodad.enabled = True
                nobj.wow_wmo_doodad.path = doodad_path
                nobj.color = (doodad.color[2] / 255,
                              doodad.color[1] / 255,
                              doodad.color[0] / 255,
                              doodad.color[3] / 255)

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
                nobj.parent = anchor
                nobj.hide = True

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
            bpy.context.scene.objects.link(obj)

            self.bl_portals.append(obj)

    def load_properties(self):
        """ Load global WoW WMO properties """
        properties = bpy.context.scene.wow_wmo_root
        properties.ambient_color = [self.wmo.mohd.ambient_color[2] / 255,
                                    self.wmo.mohd.ambient_color[1] / 255,
                                    self.wmo.mohd.ambient_color[0] / 255,
                                    self.wmo.mohd.ambient_color[3] / 255]

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

    @staticmethod
    def get_object_bounding_box(obj):
        """ Calculate bounding box of an object """
        corner1 = [0.0, 0.0, 0.0]
        corner2 = [0.0, 0.0, 0.0]

        for v in obj.bound_box:
            if v[0] < corner1[0]:
                corner1[0] = v[0]
            if v[1] < corner1[1]:
                corner1[1] = v[1]
            if v[2] < corner1[2]:
                corner1[2] = v[2]

            if v[0] > corner2[0]:
                corner2[0] = v[0]
            if v[1] > corner2[1]:
                corner2[1] = v[1]
            if v[2] > corner2[2]:
                corner2[2] = v[2]

        return corner1, corner2

    def get_global_bounding_box(self):
        """ Calculate bounding box of an entire scene """
        corner1 = self.wmo.mogi.infos[0].bounding_box_corner1
        corner2 = self.wmo.mogi.infos[0].bounding_box_corner2

        for gi in self.wmo.mogi.infos:
            v = gi.bounding_box_corner1
            if v[0] < corner1[0]:
                corner1[0] = v[0]
            if v[1] < corner1[1]:
                corner1[1] = v[1]
            if v[2] < corner1[2]:
                corner1[2] = v[2]

            v = gi.bounding_box_corner2
            if v[0] > corner2[0]:
                corner2[0] = v[0]
            if v[1] > corner2[1]:
                corner2[1] = v[1]
            if v[2] > corner2[2]:
                corner2[2] = v[2]

        return corner1, corner2




