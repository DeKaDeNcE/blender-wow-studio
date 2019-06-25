import bpy
import time

from math import sqrt
from mathutils import Vector

from .wmo_group import *
from ..pywowlib.file_formats.wmo_format_root import *
from ..pywowlib.file_formats.wmo_format_group import *

from ..ui import get_addon_prefs


class WMOFile:
    """ World of Warcraft WMO """

    def __init__(self, filepath):
        self.filepath = filepath
        self.groups = []
        self.bl_scene_objects = BlenderSceneObjects()
        self.material_lookup = {}
        self.texture_lookup = {}
        self.display_name = os.path.basename(os.path.splitext(filepath)[0])
        self.parent = None

        self.mver = MVER()
        self.mohd = MOHD()
        self.motx = MOTX()
        self.momt = MOMT()
        self.mogn = MOGN()
        self.mogi = MOGI()
        self.mosb = MOSB()
        self.mopv = MOPV()
        self.mopt = MOPT()
        self.mopr = MOPR()
        self.movv = MOVV()
        self.movb = MOVB()
        self.molt = MOLT()
        self.mods = MODS()
        self.modn = MODN()
        self.modd = MODD()
        self.mfog = MFOG()
        self.mcvp = MCVP()

    def read(self):
        """ Read WMO data from files into memory """

        start_time = time.time()

        with open(self.filepath, "rb") as f:

            # check if file is a WMO root or a WMO group, or unknown
            f.seek(12)
            hdr = ChunkHeader()
            hdr.read(f)
            f.seek(0)

            if hdr.magic == "DHOM":
                self.mver.read(f)
                self.mohd.read(f)
                self.motx.read(f)
                self.momt.read(f)
                self.mogn.read(f)
                self.mogi.read(f)
                self.mosb.read(f)
                self.mopv.read(f)
                self.mopt.read(f)
                self.mopr.read(f)
                self.movv.read(f)
                self.movb.read(f)
                self.molt.read(f)
                self.mods.read(f)
                self.modn.read(f)
                self.modd.read(f)
                self.mfog.read(f)

                if f.tell() != os.fstat(f.fileno()).st_size:
                    self.mcvp.read(f)

                print("\nDone reading root file: <<" + os.path.basename(f.name) + ">>")
                root_name = os.path.splitext(self.filepath)[0]

                for i in range(self.mohd.n_groups):
                    group_name = root_name + "_" + str(i).zfill(3) + ".wmo"

                    if not os.path.isfile(group_name):
                        raise FileNotFoundError("\nNot all referenced WMO groups are present in the directory.\a")

                    group = WMOGroupFile(self)
                    group.read(open(group_name, 'rb'))
                    self.groups.append(group)

            elif hdr.magic == "PGOM":
                raise NotImplementedError("\nImport of separate WMO group files is not supported. "
                                          "Please import the root file.\a")

            else:
                raise Exception("\nFile is not a WMO file or corrupted.\a")

            print("\nDone reading WMO. \nTotal reading time: ",
                  time.strftime("%M minutes %S seconds.", time.gmtime(time.time() - start_time)))

    def write(self):
        """ Write WMO data from memory into files """

        start_time = time.time()

        with open(self.filepath, 'wb') as f:
            print("\n\n=== Writing root file ===")

            self.mver.write(f)
            self.mohd.write(f)
            self.motx.write(f)
            self.momt.write(f)
            self.mogn.write(f)
            self.mogi.write(f)
            self.mosb.write(f)
            self.mopv.write(f)
            self.mopt.write(f)
            self.mopr.write(f)
            self.movv.write(f)
            self.movb.write(f)
            self.molt.write(f)
            self.mods.write(f)
            self.modn.write(f)
            self.modd.write(f)
            self.mfog.write(f)

            print("\nDone writing root file: <<" + os.path.basename(f.name) + ">>")

        print("\n\n=== Writing group files ===")
        for index, group in enumerate(self.groups):
            with open(os.path.splitext(self.filepath)[0] + "_" + str(index).zfill(3) + ".wmo", 'wb') as f:
                group.write(f)

        print("\nDone writing WMO. \nTotal writing time: ",
              time.strftime("%M minutes %S seconds.\a", time.gmtime(time.time() - start_time)))

    def compare_materials(self, material):
        """ Compare two WoW material properties """

        wow_mat1 = material.wow_wmo_material

        for material2, index in self.material_lookup.items():

            wow_mat2 = material2.wow_wmo_material

            if wow_mat1.shader == wow_mat2.shader \
            and wow_mat1.terrain_type == wow_mat2.terrain_type \
            and wow_mat1.blending_mode == wow_mat2.blending_mode \
            and wow_mat1.texture1 == wow_mat2.texture1 \
            and wow_mat1.emissive_color == wow_mat2.emissive_color \
            and wow_mat1.flags == wow_mat2.flags \
            and wow_mat1.texture2 == wow_mat2.texture2 \
            and wow_mat1.diff_color == wow_mat2.diff_color:
                return index

        return None

    def add_material(self, mat):
        """ Add material if not already added, then return index in root file """

        mat_index = self.compare_materials(mat)

        if mat_index is not None:
            return mat_index

        else:
            # else add it then return index
            if not mat.wow_wmo_material.enabled:
                self.material_lookup[mat] = 0xFF
                return 0xFF
            else:
                self.material_lookup[mat] = len(self.momt.materials)

                wow_mat = WMOMaterial()

                wow_mat.shader = int(mat.wow_wmo_material.shader)
                wow_mat.blend_mode = int(mat.wow_wmo_material.blending_mode)
                wow_mat.terrain_type = int(mat.wow_wmo_material.terrain_type)

                if mat.wow_wmo_material.texture1 in self.texture_lookup:
                    wow_mat.texture1_ofs = self.texture_lookup[mat.wow_wmo_material.texture1]
                else:
                    self.texture_lookup[mat.wow_wmo_material.texture1] = self.motx.add_string(mat.wow_wmo_material.texture1)
                    wow_mat.texture1_ofs = self.texture_lookup[mat.wow_wmo_material.texture1]

                wow_mat.emissive_color = (int(mat.wow_wmo_material.emissive_color[0] * 255),
                                          int(mat.wow_wmo_material.emissive_color[1] * 255),
                                          int(mat.wow_wmo_material.emissive_color[2] * 255),
                                          int(mat.wow_wmo_material.emissive_color[3] * 255))

                wow_mat.TextureFlags1 = 0

                if mat.wow_wmo_material.texture2 in self.texture_lookup:
                    wow_mat.texture2_ofs = self.texture_lookup[mat.wow_wmo_material.texture2]
                else:
                    self.texture_lookup[mat.wow_wmo_material.texture2] = self.motx.add_string(mat.wow_wmo_material.texture2)
                    wow_mat.texture2_ofs = self.texture_lookup[mat.wow_wmo_material.texture2]

                wow_mat.diff_color = (int(mat.wow_wmo_material.diff_color[0] * 255),
                                      int(mat.wow_wmo_material.diff_color[1] * 255),
                                      int(mat.wow_wmo_material.diff_color[2] * 255),
                                      int(mat.wow_wmo_material.diff_color[3] * 255))

                for flag in mat.wow_wmo_material.flags:
                    wow_mat.flags |= int(flag)

                self.momt.materials.append(wow_mat)

                return self.material_lookup[mat]

    def add_group_info(self, flags, bounding_box, name, desc):
        """ Add group info, then return offset of name and desc in a tuple """
        group_info = GroupInfo()

        group_info.flags = flags  # 8
        group_info.bounding_box_corner1 = bounding_box[0].copy()
        group_info.bounding_box_corner2 = bounding_box[1].copy()
        group_info.name_ofs = self.mogn.add_string(name)  # 0xFFFFFFFF

        desc_ofs = self.mogn.add_string(desc)

        self.mogi.infos.append(group_info)

        return group_info.name_ofs, desc_ofs

    def load_materials(self):
        """ Load materials from WoW WMO root file """
        self.material_lookup = {}

        addon_prefs = get_addon_prefs()

        images = []
        image_names = []

        # Add ghost material
        mat = bpy.data.materials.get("WowMaterial_ghost")
        if not mat:
            mat = bpy.data.materials.new("WowMaterial_ghost")
            mat.diffuse_color = (0.2, 0.5, 0.5, 1.0)
            mat.diffuse_intensity = 1.0
            mat.alpha = 0.15
            mat.transparency_method = 'Z_TRANSPARENCY'
            mat.use_transparency = True

        self.material_lookup[0xFF] = mat

        for index, wmo_material in enumerate(self.momt.materials):
            texture1 = self.motx.get_string(wmo_material.texture1_ofs)
            material_name = os.path.basename(texture1)[:-4] + '.png'

            mat = bpy.data.materials.new(material_name)
            self.material_lookup[index] = mat

            mat.wow_wmo_material.enabled = True
            mat.wow_wmo_material.shader = str(wmo_material.shader)
            mat.wow_wmo_material.blending_mode = str(wmo_material.blend_mode)
            mat.wow_wmo_material.texture1 = texture1
            mat.wow_wmo_material.emissive_color = [x / 255 for x in wmo_material.emissive_color[0:4]]
            mat.wow_wmo_material.texture2 = self.motx.get_string(wmo_material.texture2_ofs)
            mat.wow_wmo_material.diff_color = [x / 255 for x in wmo_material.diff_color[0:4]]
            mat.wow_wmo_material.terrain_type = str(wmo_material.terrain_type)

            mat_flags = set()
            bit = 1
            while bit <= 0x80:
                if wmo_material.flags & bit:
                    mat_flags.add(str(bit))
                bit <<= 1
            mat.wow_wmo_material.flags = mat_flags

            # set texture slot and load texture

            if mat.wow_wmo_material.texture1:
                tex1_slot = mat.texture_slots.create(2)
                tex1_slot.uv_layer = "UVMap"
                tex1_slot.texture_coords = 'UV'

                tex1_name = material_name + "_Tex_01"
                tex1 = bpy.data.textures.new(tex1_name, 'IMAGE')
                tex1_slot.texture = tex1

                try:
                    tex1_img_filename = os.path.splitext(mat.wow_wmo_material.texture1)[0] + '.png'

                    if os.name != 'nt':
                        tex1_img_filename = tex1_img_filename.replace('\\', '/')

                    img1_loaded = False

                    # check if image already loaded
                    for iImg in range(len(images)):
                        if image_names[iImg] == tex1_img_filename:
                            tex1.image = images[iImg]
                            img1_loaded = True
                            break

                    # if image is not loaded, do it
                    if not img1_loaded:
                        tex1_img = bpy.data.images.load(os.path.join(addon_prefs.cache_dir_path, tex1_img_filename))
                        tex1.image = tex1_img
                        images.append(tex1_img)
                        image_names.append(tex1_img_filename)
                        mat.active_texture = tex1_img

                except:
                    pass

            # set texture slot and load texture
            if mat.wow_wmo_material.texture2:
                tex2_slot = mat.texture_slots.create(1)
                tex2_slot.uv_layer = "UVMap"
                tex2_slot.texture_coords = 'UV'

                tex2_name = material_name + "_Tex_02"
                tex2 = bpy.data.textures.new(tex2_name, 'IMAGE')
                tex2_slot.texture = tex2

                try:
                    tex2_img_filename = os.path.splitext(mat.wow_wmo_material.texture2)[0] + '.png'

                    if os.name != 'nt':
                        tex2_img_filename = tex2_img_filename.replace('\\', '/')

                    img2_loaded = False

                    # check if image already loaded
                    for iImg in range(len(images)):
                        if image_names[iImg] == tex2_img_filename:
                            tex2.image = images[iImg]
                            img2_loaded = True
                            break

                    # if image is not loaded, do it
                    if not img2_loaded:
                        tex2_img = bpy.data.images.load(os.path.join(addon_prefs.cache_dir_path, tex2_img_filename))
                        tex2.image = tex2_img
                        images.append(tex2_img)
                        image_names.append(tex2_img_filename)
                except:
                    pass

    def load_lights(self):
        """ Load WoW WMO MOLT lights """
        for i in range(len(self.molt.lights)):
            l = self.molt.lights[i]

            bl_light_types = ['POINT', 'SPOT', 'SUN', 'POINT']

            try:
                l_type = bl_light_types[l.light_type]
            except IndexError:
                raise Exception("Light type unknown : {} (light nbr : {})".format(str(l.LightType), str(i)))

            light_name = self.display_name + "_Light_" + str(i).zfill(2)
            light = bpy.data.lamps.new(light_name, l_type)
            light.color = (l.color[2] / 255, l.color[1] / 255, l.color[0] / 255)
            light.energy = l.intensity

            if l.light_type in {0, 1}:
                light.falloff_type = 'INVERSE_LINEAR'
                light.distance = l.unknown4 / 2
                light.use_sphere = True

            light.wow_wmo_light.enabled = True
            light.wow_wmo_light.light_type = str(l.light_type)
            light.wow_wmo_light.type = bool(l.type)
            light.wow_wmo_light.use_attenuation = bool(l.use_attenuation)
            light.wow_wmo_light.padding = bool(l.padding)
            light.wow_wmo_light.type = bool(l.type)
            light.wow_wmo_light.color = light.color
            light.wow_wmo_light.color_alpha = l.color[3] / 255
            light.wow_wmo_light.intensity = l.intensity
            light.wow_wmo_light.attenuation_start = l.attenuation_start
            light.wow_wmo_light.attenuation_end = l.attenuation_end

            obj = bpy.data.objects.new(light_name, light)
            obj.location = self.molt.lights[i].position

            bpy.context.scene.objects.link(obj)

            if self.parent:
                obj.parent = self.parent

    def load_fogs(self):
        """ Load WoW WMO fog objects """
        for i in range(len(self.mfog.fogs)):

            f = self.mfog.fogs[i]

            bpy.ops.mesh.primitive_uv_sphere_add()
            fog = bpy.context.scene.objects.active

            if not f.big_radius:
                fog.hide = False

            fog.name = self.display_name + "_Fog_" + str(i).zfill(2)

            # applying real object transformation
            fog.location = f.position
            bpy.ops.transform.resize(value=(f.big_radius, f.big_radius, f.big_radius))  # 0.5 is the default sphere radius

            bpy.ops.object.shade_smooth()
            fog.draw_type = 'SOLID'
            fog.show_transparent = True
            fog.show_name = True
            fog.color = (f.color1[2] / 255, f.color1[1] / 255, f.color1[0] / 255, 0.0)

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
            if f.flags & 0x01:
                fog.wow_wmo_fog.ignore_radius = True
            if f.flags & 0x10:
                fog.wow_wmo_fog.unknown = True

            if f.small_radius != 0:
                fog.wow_wmo_fog.inner_radius = int(f.small_radius / f.big_radius * 100)
            else:
                fog.wow_wmo_fog.inner_radius = 0

            fog.wow_wmo_fog.end_dist = f.end_dist
            fog.wow_wmo_fog.start_factor = f.start_factor
            fog.wow_wmo_fog.color1 = (f.color1[2] / 255, f.color1[1] / 255, f.color1[0] / 255)
            fog.wow_wmo_fog.end_dist2 = f.end_dist
            fog.wow_wmo_fog.start_factor2 = f.start_factor2
            fog.wow_wmo_fog.color2 = (f.color2[2] / 255, f.color2[1] / 255, f.color2[0] / 255)

            if self.parent:
                fog.parent = self.parent

    def load_doodads(self, dir=None, game_data=None):
        """ Load doodad sets to scene. Two modes are supported: data storing and actual import."""
        scene = bpy.context.scene
        if game_data and dir:
            obj_map = {}

            for doodad_set in self.mods.sets:

                bpy.ops.object.empty_add(type='SPHERE', location=(0, 0, 0))
                anchor = bpy.context.scene.objects.active
                anchor.name = doodad_set.name
                anchor.hide = True
                anchor.hide_select = True
                anchor.lock_location = (True, True, True)
                anchor.lock_rotation = (True, True, True)
                anchor.lock_scale = (True, True, True)

                if self.parent:
                    anchor.parent = self.parent

                for i in range(doodad_set.start_doodad, doodad_set.start_doodad + doodad_set.n_doodads):
                    doodad = self.modd.definitions[i]
                    doodad_path = os.path.splitext(self.modn.get_string(doodad.name_ofs))[0] + ".m2"

                    obj = obj_map.get(doodad_path)

                    if not obj:
                        try:
                            obj = m2.m2_to_blender_mesh(dir, doodad_path, game_data)
                        except Exception as e:
                            bpy.ops.mesh.primitive_cube_add()
                            obj = bpy.context.scene.objects.active
                            obj.name = 'ERR_' + os.path.splitext(os.path.basename(doodad_path))[0]
                            print("\n{}\nFailed to import model: <<{}>>. Placeholder is imported instead.".format(e, doodad_path))

                        obj.wow_wmo_doodad.enabled = True
                        obj.wow_wmo_doodad.path = doodad_path

                        obj_map[doodad_path] = obj
                        nobj = obj
                    else:
                        nobj = obj.copy()
                        scene.objects.link(nobj)

                    nobj.wow_wmo_doodad.color = (doodad.color[2] / 255,
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

        else:
            string_filter = []

            scene.wow_wmo_root.mods_sets.clear()
            scene.wow_wmo_root.modn_string_table.clear()
            scene.wow_wmo_root.modd_definitions.clear()

            for doodad_set in self.mods.sets:
                property_set = scene.wow_wmo_root.mods_sets.add()
                property_set.name = doodad_set.name
                property_set.start_doodad = doodad_set.start_doodad
                property_set.n_doodads = doodad_set.n_doodads
                property_set.padding = doodad_set.padding

            for doodad_definition in self.modd.definitions:
                property_definition = scene.wow_wmo_root.modd_definitions.add()
                property_definition.name_ofs = doodad_definition.name_ofs
                property_definition.flags = doodad_definition.flags
                property_definition.position = doodad_definition.position

                property_definition.rotation = (doodad_definition.rotation[0],
                                                doodad_definition.rotation[1],
                                                doodad_definition.rotation[2])

                property_definition.tilt = doodad_definition.rotation[3]
                property_definition.scale = doodad_definition.scale

                property_definition.color = (doodad_definition.color[0],
                                             doodad_definition.color[1],
                                             doodad_definition.color[2])

                property_definition.color_alpha = doodad_definition.color[3]

                if property_definition.name_ofs not in string_filter:
                    path = scene.wow_wmo_root.modn_string_table.add()
                    path.ofs = property_definition.name_ofs
                    path.string = self.modn.get_string(property_definition.name_ofs)
                    string_filter.append(property_definition.name_ofs)

    def load_portals(self):
        """ Load WoW WMO portal planes """
        vert_count = 0
        for index, portal in enumerate(self.mopt.infos):
            portal_name = self.display_name + "_Portal_" + str(index).zfill(3)

            verts = []
            face = []
            faces = []

            for j in range(portal.n_vertices):
                if len(face) < 4:
                    verts.append(self.mopv.portal_vertices[vert_count])
                    face.append(j)
                vert_count += 1

            faces.append(face)

            mesh = bpy.data.meshes.new(portal_name)

            obj = bpy.data.objects.new(portal_name, mesh)

            obj.wow_wmo_portal.enabled = True
            first_relationship = True

            for relation in self.mopr.relations:
                if relation.portal_index == index:
                    group_name = self.mogn.get_string(self.groups[relation.group_index].mogp.group_name_ofs)
                    if first_relationship:
                        obj.wow_wmo_portal.first = bpy.context.scene.objects[group_name]
                        first_relationship = False
                    else:
                        obj.wow_wmo_portal.second = bpy.context.scene.objects[group_name]
                        break

            mesh.from_pydata(verts, [], faces)
            bpy.context.scene.objects.link(obj)

            if self.parent:
                obj.parent = self.parent

    def load_properties(self):
        """ Load global WoW WMO properties """
        properties = bpy.context.scene.wow_wmo_root
        properties.ambient_color = [float(self.mohd.ambient_color[2] / 255),
                                    float(self.mohd.ambient_color[1] / 255),
                                    float(self.mohd.ambient_color[0]) / 255,
                                    float(self.mohd.ambient_color[3]) / 255]

        flags = set()
        if self.mohd.flags & 0x1:
            flags.add("0")
        if self.mohd.flags & 0x2:
            flags.add("2")
        if self.mohd.flags & 0x8:
            flags.add("1")

        properties.flags = flags
        properties.skybox_path = self.mosb.skybox
        properties.wmo_id = self.mohd.id

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
        corner1 = self.mogi.infos[0].bounding_box_corner1
        corner2 = self.mogi.infos[0].bounding_box_corner2

        for gi in self.mogi.infos:
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

    def save_doodad_sets(self):
        """ Save doodads data from Blender scene to WMO root """
        start_time = time.time()

        if len(self.bl_scene_objects.doodad_sets):
            doodad_paths = {}

            has_global = False

            for set_name, doodads in self.bl_scene_objects.doodad_sets:
                print("\nSaving doodadset: <<{}>>".format(set_name))

                doodad_set = DoodadSet()
                doodad_set.name = set_name
                doodad_set.start_doodad = len(self.modd.definitions)

                for doodad in doodads:
                    doodad_def = DoodadDefinition()

                    path = os.path.splitext(doodad.wow_wmo_doodad.path)[0] + ".MDX"

                    doodad_def.name_ofs = doodad_paths.get(path)
                    if not doodad_def.name_ofs:
                        doodad_def.name_ofs = self.modn.add_string(path)
                        doodad_paths[path] = doodad_def.name_ofs

                    doodad_def.position = doodad.matrix_world @ Vector((0, 0, 0))

                    doodad.rotation_mode = 'QUATERNION'

                    doodad_def.rotation = (doodad.rotation_quaternion[1],
                                           doodad.rotation_quaternion[2],
                                           doodad.rotation_quaternion[3],
                                           doodad.rotation_quaternion[0])

                    doodad_def.scale = doodad.scale[0]

                    doodad_def.color = (int(doodad.wow_wmo_doodad.color[2] * 255),
                                        int(doodad.wow_wmo_doodad.color[1] * 255),
                                        int(doodad.wow_wmo_doodad.color[0] * 255),
                                        int(doodad.wow_wmo_doodad.color[3] * 255))

                    for flag in doodad.wow_wmo_doodad.flags:
                        doodad_def.flags |= int(flag)

                    self.modd.definitions.append(doodad_def)

                doodad_set.n_doodads = len(self.modd.definitions) - doodad_set.start_doodad

                if set_name == "Set_$DefaultGlobal":
                    self.mods.sets.insert(0, doodad_set)
                    has_global = True
                else:
                    self.mods.sets.append(doodad_set)

                    print("Done saving doodadset: <<{}>>".format(set_name))

            if not has_global:
                doodad_set = DoodadSet()
                doodad_set.name = "Set_$DefaultGlobal"
                doodad_set.start_doodad = 0
                doodad_set.n_doodads = 0
                self.mods.sets.insert(0, doodad_set)

        elif len(bpy.context.scene.wow_wmo_root.mods_sets):
            print("\nSaving preserved doodadset data")
            scene = bpy.context.scene
            ofs_map = {}

            for property_set in scene.wow_wmo_root.mods_sets:
                doodad_set = DoodadSet()
                doodad_set.name = property_set.name
                doodad_set.StartDoodad = property_set.start_doodad
                doodad_set.nDoodads = property_set.n_doodads
                doodad_set.padding = property_set.padding

                self.mods.sets.append(doodad_set)

            for modn_string in scene.wow_wmo_root.modn_string_table:
                ofs_map[modn_string.ofs] = self.modn.add_string(modn_string.string)

            for property_def in scene.wow_wmo_root.modd_definitions:
                doodad_def = DoodadDefinition()
                doodad_def.name_ofs = ofs_map.get(property_def.name_ofs)
                doodad_def.flags = property_def.flags
                doodad_def.position = property_def.position

                doodad_def.rotation = [property_def.rotation[0],
                                       property_def.rotation[1],
                                       property_def.rotation[2],
                                       0.0]

                doodad_def.rotation[3] = property_def.tilt
                doodad_def.scale = property_def.scale

                doodad_def.color = [int(property_def.color[0]),
                                    int(property_def.color[1]),
                                    int(property_def.color[2]),
                                    0]

                doodad_def.color[3] = int(property_def.color_alpha)

                self.modd.definitions.append(doodad_def)

        print("\nDone saving doodad sets. "
              "\nTotal saving time: ", time.strftime("%M minutes %S seconds", time.gmtime(time.time() - start_time)))

    def save_lights(self):
        start_time = time.time()
        print("\nSaving lights")

        for obj in self.bl_scene_objects.lights:
            mesh = obj.data

            light = Light()
            light.light_type = int(mesh.wow_wmo_light.light_type)

            if light.light_type in {0, 1}:
                light.unknown4 = mesh.distance * 2

            light.type = mesh.wow_wmo_light.type
            light.use_attenuation = mesh.wow_wmo_light.use_attenuation
            light.padding = mesh.wow_wmo_light.padding

            light.color = (int(mesh.wow_wmo_light.color[2] * 255),
                           int(mesh.wow_wmo_light.color[1] * 255),
                           int(mesh.wow_wmo_light.color[0] * 255),
                           int(mesh.wow_wmo_light.color_alpha * 255))

            light.position = obj.location
            light.intensity = mesh.wow_wmo_light.intensity
            light.attenuation_start = mesh.wow_wmo_light.attenuation_start
            light.attenuation_end = mesh.wow_wmo_light.attenuation_end
            self.molt.lights.append(light)

        print("\nDone saving lights. "
              "\nTotal saving time: ", time.strftime("%M minutes %S seconds", time.gmtime(time.time() - start_time)))

    def save_liquids(self):
        start_time = time.time()

        for liquid_obj in self.bl_scene_objects.liquids:
            print("\nSaving liquid: <<{}>>".format(liquid_obj.name))

            if not liquid_obj.wow_wmo_liquid.wmo_group:
                print("WARNING: Failed saving liquid: <<{}>>".format(liquid_obj.name))
                continue
            group_obj = liquid_obj.wow_wmo_liquid.wmo_group

            group_index = group_obj.wow_wmo_group.group_id
            group = self.groups[group_index]

            group.save_liquid(liquid_obj)

            print("Done saving liquid: <<{}>>".format(liquid_obj.name))

        print("\nDone saving liquids. "
              "\nTotal saving time: ", time.strftime("%M minutes %S seconds", time.gmtime(time.time() - start_time)))

    def save_portals(self):
        start_time = time.time()
        print("\nSaving portals")

        saved_portals_ids = []

        self.mopt.infos = len(self.bl_scene_objects.portals) * [None]

        for group_obj in self.bl_scene_objects.groups:

            portal_relations = group_obj.wow_wmo_group.relations.portals
            group_index = group_obj.wow_wmo_group.group_id
            group = self.groups[group_index]
            group.mogp.PortalStart = len(self.mopr.relations)

            for relation in portal_relations:
                portal_obj = bpy.context.scene.objects[relation.id]
                portal_index = portal_obj.wow_wmo_portal.portal_id

                if portal_index not in saved_portals_ids:
                    print("\nSaving portal: <<{}>>".format(portal_obj.name))

                    portal_mesh = portal_obj.data
                    portal_info = PortalInfo()
                    portal_info.start_vertex = len(self.mopv.portal_vertices)
                    v = []

                    for poly in portal_mesh.polygons:
                        for loop_index in poly.loop_indices:
                            vertex_pos = portal_mesh.vertices[portal_mesh.loops[loop_index].vertex_index].co \
                                         @ portal_obj.matrix_world
                            self.mopv.portal_vertices.append(vertex_pos)
                            v.append(vertex_pos)

                    v_A = v[0][1] * v[1][2] - v[1][1] * v[0][2] - v[0][1] * v[2][2] + v[2][1] * v[0][2] + v[1][1] * v[2][2] - \
                          v[2][1] * v[1][2]
                    v_B = -v[0][0] * v[1][2] + v[2][0] * v[1][2] + v[1][0] * v[0][2] - v[2][0] * v[0][2] - v[1][0] * v[2][2] + \
                          v[0][0] * v[2][2]
                    v_C = v[2][0] * v[0][1] - v[1][0] * v[0][1] - v[0][0] * v[2][1] + v[1][0] * v[2][1] - v[2][0] * v[1][1] + \
                          v[0][0] * v[1][1]
                    v_D = -v[0][0] * v[1][1] * v[2][2] + v[0][0] * v[2][1] * v[1][2] + v[1][0] * v[0][1] * v[2][2] - v[1][0] * \
                          v[2][1] * v[0][2] - v[2][0] * v[0][1] * v[1][2] + v[2][0] * v[1][1] * v[0][2]

                    portal_info.unknown = v_D / sqrt(v_A * v_A + v_B * v_B + v_C * v_C)
                    portal_info.n_vertices = len(self.mopv.portal_vertices) - portal_info.start_vertex
                    portal_info.normal = tuple(portal_mesh.polygons[0].normal)

                    self.mopt.infos[portal_index] = portal_info
                    saved_portals_ids.append(portal_index)

                    print("Done saving portal: <<{}>>".format(portal_obj.name))

                first = self.bl_scene_objects.portals[portal_index].wow_wmo_portal.first
                second = self.bl_scene_objects.portals[portal_index].wow_wmo_portal.second

                # calculating portal relation
                relation = PortalRelation()
                relation.portal_index = portal_index
                relation.group_index = second.wow_wmo_group.group_id if first.name == group_obj.name else first.wow_wmo_group.group_id
                relation.side = group.get_portal_direction(portal_obj, group_obj)

                self.mopr.relations.append(relation)

            group.mogp.PortalCount = len(self.mopr.relations) - group.mogp.PortalStart

        print("\nDone saving portals. "
              "\nTotal saving time: ", time.strftime("%M minutes %S seconds", time.gmtime(time.time() - start_time)))

    def save_fogs(self):
        start_time = time.time()
        print("\nSaving fogs")

        for fog_obj in self.bl_scene_objects.fogs:
            print("\nSaving fog: <<{}>>".format(fog_obj.name))
            fog = Fog()

            fog.big_radius = fog_obj.dimensions[2] / 2
            fog.small_radius = fog.big_radius * (fog_obj.wow_wmo_fog.inner_radius / 100)

            fog.color1 = (int(fog_obj.wow_wmo_fog.color1[2] * 255),
                          int(fog_obj.wow_wmo_fog.color1[1] * 255),
                          int(fog_obj.wow_wmo_fog.color1[0] * 255),
                          0xFF)

            fog.color2 = (int(fog_obj.wow_wmo_fog.color2[2] * 255),
                          int(fog_obj.wow_wmo_fog.color2[1] * 255),
                          int(fog_obj.wow_wmo_fog.color2[0] * 255),
                          0xFF)

            fog.end_dist = fog_obj.wow_wmo_fog.end_dist
            fog.end_dist2 = fog_obj.wow_wmo_fog.end_dist2
            fog.position = fog_obj.location
            fog.start_factor = fog_obj.wow_wmo_fog.start_factor
            fog.StarFactor2 = fog_obj.wow_wmo_fog.start_factor2

            if fog_obj.wow_wmo_fog.ignore_radius:
                fog.flags |= 0x01
            if fog_obj.wow_wmo_fog.unknown:
                fog.flags |= 0x10

            self.mfog.fogs.append(fog)

            print("Done saving fog: <<{}>>".format(fog_obj.name))

        print("\nDone saving fogs. "
              "\nTotal saving time: ", time.strftime("%M minutes %S seconds", time.gmtime(time.time() - start_time)))

    def save_root_header(self):
        print("\nSaving root header")

        scene = bpy.context.scene

        self.mver.version = 17

        # setting up default fog with default blizzlike values.
        if not len(self.mfog.fogs):
            empty_fog = Fog()
            empty_fog.color1 = (0xFF, 0xFF, 0xFF, 0xFF)
            empty_fog.color2 = (0x00, 0x00, 0x00, 0xFF)
            empty_fog.end_dist = 444.4445
            empty_fog.end_dist2 = 222.2222
            empty_fog.start_factor = 0.25
            empty_fog.start_factor2 = -0.5
            self.mfog.fogs.append(empty_fog)

        bb = self.get_global_bounding_box()
        self.mohd.bounding_box_corner1 = bb[0]
        self.mohd.bounding_box_corner2 = bb[1]

        # DBC foreign keys
        self.mohd.id = scene.wow_wmo_root.wmo_id
        self.mosb.skybox = scene.wow_wmo_root.skybox_path

        self.mohd.ambient_color = [int(scene.wow_wmo_root.ambient_color[2] * 255),
                                   int(scene.wow_wmo_root.ambient_color[1] * 255),
                                   int(scene.wow_wmo_root.ambient_color[0] * 255),
                                   int(scene.wow_wmo_root.ambient_color[3] * 255)]

        self.mohd.n_materials = len(self.momt.materials)
        self.mohd.n_groups = len(self.mogi.infos)
        self.mohd.n_portals = len(self.mopt.infos)
        self.mohd.n_models = self.modn.string_table.decode("ascii").count('.MDX')
        self.mohd.n_lights = len(self.molt.lights)
        self.mohd.n_doodads = len(self.modd.definitions)
        self.mohd.n_sets = len(self.mods.sets)

        flags = scene.wow_wmo_root.flags
        if "0" in flags:
            self.mohd.flags |= 0x01
        if "2" in flags:
            self.mohd.flags |= 0x02
        if "1" in flags:
            self.mohd.flags |= 0x08

        self.mohd.flags |= 0x4

        print("Done saving root header")


class BlenderSceneObjects:

    def __init__(self):
        self.groups = []
        self.portals = []
        self.fogs = []
        self.lights = []
        self.liquids = []
        self.doodad_sets = []

    @staticmethod
    def find_nearest_object(obj_, objects):
        """Get closest object to another object"""

        dist = sys.float_info.max
        result = None
        for obj in objects:
            obj_location_relative = obj.matrix_world.inverted() @ obj.location
            hit = obj_.closest_point_on_mesh(obj_location_relative)
            hit_dist = (obj.location - obj.matrix_world @ hit[1]).length
            if hit_dist < dist:
                dist = hit_dist
                result = obj

        return result

    def build_references(self, export_selected):
        """ Build WMO references in Blender scene """

        start_time = time.time()

        empties = []

        for obj in bpy.context.scene.objects:
            if not obj.wow_wmo_doodad.enabled and not obj.type == 'EMPTY':
                if obj.hide or export_selected and not obj.select:
                    continue
                else:
                    bpy.context.scene.objects.active = obj
                    bpy.ops.object.mode_set(mode='OBJECT')

            obj.select_set(False)

            if obj.type == 'MESH':

                if obj.wow_wmo_group.enabled:
                    self.groups.append(obj)
                    obj.wow_wmo_group.group_id = len(self.groups) - 1

                elif obj.wow_wmo_portal.enabled:
                    self.portals.append(obj)
                    obj.wow_wmo_portal.portal_id = len(self.portals) - 1

                    group_objects = (obj.wow_wmo_portal.first, obj.wow_wmo_portal.second)

                    for group_obj in group_objects:
                        if group_obj and group_obj.name in bpy.context.scene.objects:
                            rel = group_obj.wow_wmo_group.relations.portals.add()
                            rel.id = obj.name
                        else:
                            raise KeyError("Portal <<{}>> points to a non-existing object.".format(obj.name))

                elif obj.wow_wmo_fog.enabled:
                    self.fogs.append(obj)
                    obj.wow_wmo_fog.fog_id = len(self.fogs) - 1

                elif obj.wow_wmo_liquid.enabled:
                    self.liquids.append(obj)
                    group = obj.wow_wmo_liquid.wmo_group

                    if group:
                        group.wow_wmo_group.relations.liquid = obj.name
                    else:
                        print("\nWARNING: liquid <<{}>> points to a non-existing object.".format(obj.wow_wmo_liquid.wmo_group))
                        continue

            elif obj.type == 'LAMP' and obj.data.wow_wmo_light.enabled:
                self.lights.append(obj)

            elif obj.type == 'EMPTY':
                empties.append(obj)

        print("\nDone building references. "
              "\nTotal building time: ",
              time.strftime("%M minutes %S seconds", time.gmtime(time.time() - start_time)))

        start_time = time.time()

        # sorting doodads into sets
        doodad_counter = 0
        for empty in empties:

            doodad_set = (empty.name, [])

            for doodad in empty.children:
                if doodad.wow_wmo_doodad.enabled:
                    group = BlenderSceneObjects.find_nearest_object(doodad, self.groups)

                    if group:
                        rel = group.wow_wmo_group.relations.doodads.add()
                        rel.id = doodad_counter
                        doodad_counter += 1

                        doodad_set[1].append(doodad)

            if doodad_set[1]:
                self.doodad_sets.append(doodad_set)

        # setting light references
        for index, light in enumerate(self.lights):
            group = BlenderSceneObjects.find_nearest_object(light, self.groups)
            if group:
                rel = group.wow_wmo_group.relations.lights.add()
                rel.id = index

        print("\nDone assigning doodads and lights to groups. "
              "\nTotal time: ",
              time.strftime("%M minutes %S seconds", time.gmtime(time.time() - start_time)))

    def clear_references(self):
        for group in self.groups:
            group.wow_wmo_group.relations.doodads.clear()
            group.wow_wmo_group.relations.lights.clear()
            group.wow_wmo_group.relations.portals.clear()
            group.wow_wmo_group.relations.liquid = ""
