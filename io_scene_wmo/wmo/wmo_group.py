import os
import hashlib
import bpy
import bmesh
import mathutils

from math import floor, ceil, pi
from .bsp_tree import *
from ..pywowlib.file_formats.wmo_format_group import *
from ..pywowlib.file_formats.wmo_format_root import MVER


class WMOGroupFile:
    def __init__(self, root):

        self.root = root

        self.mver = MVER()
        self.mogp = MOGP()
        self.mopy = MOPY()
        self.movi = MOVI()
        self.movt = MOVT()
        self.monr = MONR()
        self.motv = MOTV()
        self.moba = MOBA()
        self.molr = MOLR()
        self.modr = MODR()
        self.mobn = MOBN()
        self.mobr = MOBR()
        self.mocv = MOCV()
        self.mliq = MLIQ()
        self.motv2 = MOTV()
        self.mocv2 = MOCV()

    def read(self, f):
        """ Read WoW WMO group file """

        self.mver.read(f)
        self.mogp.read(f)
        self.mopy.read(f)
        self.movi.read(f)
        self.movt.read(f)
        self.monr.read(f)
        self.motv.read(f)
        self.moba.read(f)

        if self.mogp.flags & MOGPFlags.HasLight:
            self.molr.read(f)

        if self.mogp.flags & MOGPFlags.HasDoodads:
            self.modr.read(f)

        if self.mogp.flags & MOGPFlags.HasCollision:
            self.mobn.read(f)
            self.mobr.read(f)

        if self.mogp.flags & MOGPFlags.HasVertexColor:
            self.mocv.read(f)

        if self.mogp.flags & MOGPFlags.HasWater:
            if self.mogp.liquid_type in {3, 4, 7, 8, 11, 12}:
                self.mliq.liquid_material = False
            self.mliq.read(f)

        if self.mogp.flags & MOGPFlags.HasTwoMOTV:
            self.motv2.read(f)

        if self.mogp.flags & MOGPFlags.HasTwoMOCV:
            self.mocv2.read(f)

    def write(self, f):
        """ Write a saved WoW WMO group to a file """
        print("\nWriting file: <<" +  os.path.basename(f.name) + ">>")

        self.mver.write(f)

        f.seek(0x58)
        self.mopy.write(f)
        self.movi.write(f)
        self.movt.write(f)
        self.monr.write(f)
        self.motv.write(f)
        self.moba.write(f)

        if self.molr:
            self.molr.write(f)

        if self.modr:
            self.modr.write(f)

        self.mobn.write(f)
        self.mobr.write(f)

        if self.mocv:
            self.mocv.write(f)

        if self.mliq:
            self.mliq.write(f)

        if self.motv2:
            self.motv2.write(f)

        if self.mocv2:
            self.mocv2.write(f)

        # get file size
        f.seek(0, 2)
        self.mogp.header.Size = f.tell() - 20

        # write header
        f.seek(0xC)
        self.mogp.write(f)

    @staticmethod
    def get_avg(list_):
        """ Get single average normal vector from a split normal """
        normal = [0.0, 0.0, 0.0]

        for n in list_:
            for i in range(0, 3):
                normal[i] += n[i]

        for i in range(0, 3):
            normal[i] /= len(list_)

        return normal

    @staticmethod
    def comp_colors(color1, color2):
        """ Compare two colors """

        for i in range(0, 3):
            if color1[i] != color2[i]:
                return False
        return True

    @staticmethod
    def get_batch_type(b_face, vg_batch_map_index, vg_batch_map):
        """ Find which MOBA batch type a passed bmesh face belongs two """

        # assume batch C if no batch map provided
        if vg_batch_map is None:
            return 2

        count_a = 0
        count_b = 0

        for vertex in b_face.verts:
            dvert = vertex[vg_batch_map]

            if vg_batch_map_index in dvert:
                weight = dvert[vg_batch_map_index]

                if weight != 0:
                    count_a += 1
                else:
                    count_b += 1

        if count_a == 3:
            return 0
        elif count_b == 3:
            return 1
        else:
            return 2

    @staticmethod
    def get_material_viewport_image(material):
        """ Get viewport image assigned to a material """
        for i in range(3):
            try:
                img = material.texture_slots[3 - i].texture.image
                return img
            except:
                pass
        return None

    @staticmethod
    def get_linked_faces(b_face, face_batch_type, uv, uv2, batch_map, batch_map_index, stack=0):
        # check if face was already processed
        if b_face.tag:
            return []

        f_linked = [b_face]
        mat_idx = b_face.material_index
        b_face.tag = True

        # Select edges that link two faces
        for link_edge in b_face.edges:
            # check if edge is shared with another face
            if not len(link_edge.link_faces) == 2:
                continue

            # prevent recursion stack overflow
            if stack > sys.getrecursionlimit() - 1:
                break

            for link_face in link_edge.link_faces:
                # check if face was already processed and if it shares the same material
                if link_face.tag or link_face.material_index != mat_idx:
                    continue

                # check if face is located within same UV island.
                linked_uvs = 0
                for loop in b_face.loops:

                    for l_loop in loop.vert.link_loops:
                        if l_loop.face is link_face:
                            if l_loop[uv].uv == loop[uv].uv:
                                linked_uvs += 1
                            if uv2 and l_loop[uv2].uv == loop[uv2].uv:
                                linked_uvs += 1

                if (not uv2 and linked_uvs < 2) or (uv2 and linked_uvs < 4):
                    continue

                # check if face is located within the same batch
                batch_type = WMOGroupFile.get_batch_type(link_face, batch_map_index, batch_map)

                if batch_type != face_batch_type:
                    continue

                # call this function recursively on this face if all checks are passed
                f_linked.extend(WMOGroupFile.get_linked_faces(link_face, batch_type, uv, uv2, batch_map,
                                                              batch_map_index, stack=stack + 1))

        return f_linked

    def from_wmo_liquid_type(self, basic_liquid_type):
        """ Convert simplified WMO liquid type IDs to real LiquidType.dbc IDs """
        real_liquid_type = 0

        if basic_liquid_type < 20:
            if basic_liquid_type == 0:
                real_liquid_type = 14 if self.mogp.flags & 0x80000 else 13
            elif basic_liquid_type == 1:
                real_liquid_type = 14
            elif basic_liquid_type == 2:
                real_liquid_type = 19
            elif basic_liquid_type == 15:
                real_liquid_type = 17
            elif basic_liquid_type == 3:
                real_liquid_type = 20
        else:
            real_liquid_type = basic_liquid_type + 1

        return real_liquid_type

    # return array of vertice and array of faces in a tuple
    def load_liquids(self, group_name, pos):
        """ Load liquid plane of the WMO group. Should only be called if MLIQ is present. """

        # load vertices
        vertices = []
        for y in range(0, self.mliq.y_verts):
            y_pos = self.mliq.position[1] + y * 4.1666625
            for x in range(0 , self.mliq.x_verts):
                x_pos = self.mliq.position[0] + x * 4.1666625
                vertices.append((x_pos, y_pos, self.mliq.vertex_map[y * self.mliq.x_verts + x].height[0]))

        # calculate faces
        indices = []
        for y in range(self.mliq.y_tiles):
            for x in range(self.mliq.x_tiles):
                indices.append(y * self.mliq.x_verts + x)
                indices.append(y * self.mliq.x_verts + x + 1)
                indices.append((y + 1) * self.mliq.x_verts + x)
                indices.append((y + 1) * self.mliq.x_verts + x + 1)

        faces = []

        for i in range(0, len(indices), 4):
            faces.append((indices[i], indices[i + 1], indices[i + 3], indices[i + 2]))

        # create mesh and object
        name = group_name + "_Liquid"
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        # create mesh from python data
        mesh.from_pydata(vertices,[],faces)
        mesh.update(calc_edges=True)
        mesh.validate()

        # create uv map if liquid is lava
        if self.mogp.liquid_type in {3, 4, 7, 8, 11, 12}:
            uv_map = {}

            for vertex in mesh.vertices:
                uv_map[vertex.index] = (self.mliq.vertex_map[vertex.index].u,
                                        self.mliq.vertex_map[vertex.index].v)

            mesh.uv_textures.new("UVMap")
            uv_layer1 = mesh.uv_layers[0]

            for poly in mesh.polygons:
                for loop_index in poly.loop_indices:
                        uv_layer1.data[loop_index].uv = (uv_map.get(mesh.loops[loop_index].vertex_index)[0],
                                                         - uv_map.get(mesh.loops[loop_index].vertex_index)[1])

        # setting flags in a hacky way using vertex colors
        bit = 1
        while bit <= 0x80:
            vc_layer = mesh.vertex_colors.new("flag_" + hex(bit))
            for poly in mesh.polygons:
                tile_flag = self.mliq.tile_flags[poly.index]
                for loop in poly.loop_indices:
                    if tile_flag & bit:
                        vc_layer.data[loop].color = (0, 0, 255)
            bit <<= 1

        # set mesh location
        obj.location = pos
        bpy.context.scene.objects.link(obj)

        bpy.context.scene.objects.active = obj

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=True)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        obj.lock_scale = [True, True, True]
        obj.lock_rotation[2] = True

        obj.wow_wmo_liquid.enabled = True

        # getting Liquid Type ID
        if self.root.mohd.flags & 0x4:
            real_liquid_type = self.mogp.liquid_type
        else:
            real_liquid_type = self.from_wmo_liquid_type(self.mogp.liquid_type)

        obj.wow_wmo_liquid.color = self.root.material_lookup[self.mliq.material_id].wow_wmo_material.diff_color
        obj.wow_wmo_liquid.liquid_type = str(real_liquid_type)
        try:
            obj.wow_wmo_liquid.wmo_group = bpy.context.scene.objects[group_name]
        except KeyError:
            raise KeyError("Liquid {} points to a non-existing WMO group".format(obj.name))

        if self.root.parent:
            obj.parent = self.root.parent

    # Return faces indices
    def get_bsp_node_indices(self, i_node, nodes, faces, indices):
        """ Get indices of a WMO BSP tree nodes """
        # last node in branch
        node_indices = []
        if nodes[i_node].plane_type & BSPPlaneType.Leaf:
            for i in range(nodes[i_node].first_face, nodes[i_node].first_face + nodes[i_node].num_faces):
                node_indices.append(faces[i])

        if nodes[i_node].children[0] != -1:
            node_indices.extend(self.get_bsp_node_indices(nodes[i_node].children[0], nodes, faces, indices))

        if nodes[i_node].children[1] != -1:
            node_indices.extend(self.get_bsp_node_indices(nodes[i_node].children[1], nodes, faces, indices))

        return node_indices

    def get_collision_indices(self):
        """ Get indices of a WMO BSP tree nodes that have collision """
        node_indices = self.get_bsp_node_indices(0, self.mobn.nodes, self.mobr.faces, self.movi.indices)
        indices = []
        for i in node_indices:
            if not self.mopy.triangle_materials[i].flags & 0x04:
                indices.append(self.movi.indices[i * 3])
                indices.append(self.movi.indices[i * 3 + 1])
                indices.append(self.movi.indices[i * 3 + 2])

        return indices

    # Create mesh from file data
    def load_object(self, obj_name, editable_doodads):
        """ Load WoW WMO group as an object to the Blender scene """

        vertices = self.movt.vertices
        normals = self.monr.normals
        tex_coords = self.motv.tex_coords
        faces = [self.movi.indices[i:i + 3] for i in range(0, len(self.movi.indices), 3)]

        # create mesh
        mesh = bpy.data.meshes.new(obj_name)
        mesh.from_pydata(vertices, [], faces)

        # create object
        scn = bpy.context.scene

        for o in scn.objects:
            o.select = False

        nobj = bpy.data.objects.new(obj_name, mesh)
        scn.objects.link(nobj)

        for poly in mesh.polygons:
            poly.use_smooth = True

        # set normals
        for i in range(len(normals)):
            mesh.vertices[i].normal = normals[i]

        custom_normals = [(0.0, 0.0, 0.0)] * len(mesh.loops)
        mesh.use_auto_smooth = True
        for i, loop in enumerate(mesh.loops):
            mesh.vertices[loop.vertex_index].normal = normals[loop.vertex_index]
            custom_normals[i] = normals[loop.vertex_index]

        mesh.normals_split_custom_set(custom_normals)

        # set vertex color
        if self.mogp.flags & MOGPFlags.HasVertexColor:
            flag_set = nobj.wow_wmo_group.flags
            flag_set.add('0')
            nobj.wow_wmo_group.flags = flag_set
            vert_color_layer1 = mesh.vertex_colors.new("Col")

            # loops and vertex_color are in the same order, so we use it to find vertex index
            for i in range(len(mesh.loops)):

                vert_color_layer1.data[i].color = (self.mocv.vert_colors[mesh.loops[i].vertex_index][2] / 255,
                                                   self.mocv.vert_colors[mesh.loops[i].vertex_index][1] / 255,
                                                   self.mocv.vert_colors[mesh.loops[i].vertex_index][0] / 255)

        if self.mogp.flags & MOGPFlags.HasTwoMOCV:
            blendmap = nobj.vertex_groups.new("Blendmap")
            nobj.wow_wmo_vertex_info.blendmap = blendmap.name
            blendmap.add(self.movi.indices, 1.0, 'ADD')

            for vertex in mesh.vertices:
                vertex.groups[blendmap.index].weight = self.mocv2.vert_colors[vertex.index][3] / 255

        # set uv
        uv1 = mesh.uv_textures.new("UVMap")
        uv_layer1 = mesh.uv_layers[0]
        for i in range(len(uv_layer1.data)):
            uv = tex_coords[mesh.loops[i].vertex_index]
            uv_layer1.data[i].uv = (uv[0], 1 - uv[1])

        if self.mogp.flags & MOGPFlags.HasTwoMOTV:
            uv2 = mesh.uv_textures.new("UVMap_2")
            nobj.wow_wmo_vertex_info.second_uv = uv2.name
            uv_layer2 = mesh.uv_layers[1]

            for j in range(len(uv_layer2.data)):
                uv = self.motv2.tex_coords[mesh.loops[j].vertex_index]
                uv_layer2.data[j].uv = (uv[0], 1 - uv[1])

        # map root material ID to index in mesh materials
        material_indices = {}
        material_viewport_textures = {}

        # create batch vertex groups

        batch_map = None

        if self.mogp.n_batches_a != 0 or self.mogp.n_batches_b != 0:
            batch_map = nobj.vertex_groups.new("BatchMap")
            nobj.wow_wmo_vertex_info.batch_map = batch_map.name

        batch_material_map = {}

        # add materials
        for i in range(len(self.moba.batches)):

            material = mesh.materials.get(self.root.material_lookup[self.moba.batches[i].material_id].name)

            if not material:
                mat_id = len(mesh.materials)
                material_indices[self.moba.batches[i].material_id] = mat_id
                material = self.root.material_lookup[self.moba.batches[i].material_id]

                image = self.get_material_viewport_image(material)
                material_viewport_textures[mat_id] = image

                if not len(material.texture_slots) and image:
                    texture = bpy.data.textures.new(os.path.split(image.filepath)[1], 'IMAGE')
                    texture.image = image
                    texture_slot = material.texture_slots.add()
                    texture_slot.texture = texture

                mesh.materials.append(self.root.material_lookup[self.moba.batches[i].material_id])

                material.wow_wmo_material.enabled = True

            if i < self.mogp.n_batches_a:
                batch = self.moba.batches[i]
                indices = self.movi.indices[batch.start_triangle : batch.start_triangle + batch.n_triangles]
                batch_map.add(indices, 0.0, 'ADD')

                # add lightmap information for batch A
                if self.mocv.vert_colors:
                    for index in indices:
                        mesh.vertices[index].groups[batch_map.index].weight = self.mocv.vert_colors[index][3] / 255

            elif i < self.mogp.n_batches_b:
                batch = self.moba.batches[i]
                indices = self.movi.indices[batch.start_triangle : batch.start_triangle + batch.n_triangles]
                batch_map.add(indices, 0.0, 'ADD')

            batch_material_map[
                (self.moba.batches[i].start_triangle // 3,
                (self.moba.batches[i].start_triangle + self.moba.batches[i].n_triangles) // 3)
                ] = self.moba.batches[i].material_id

        # add ghost material
        for i in self.mopy.triangle_materials:
            if i.material_id == 0xFF:
                mat_ghost__id = len(mesh.materials)
                mesh.materials.append(self.root.material_lookup[0xFF])
                material_viewport_textures[mat_ghost__id] = None
                material_indices[0xFF] = mat_ghost__id
                break

        # set faces material
        for i in range(len(mesh.polygons)):
            mat_id = self.mopy.triangle_materials[i].material_id

            mesh.polygons[i].material_index = material_indices[mat_id]

            # set texture displayed in viewport
            img = material_viewport_textures[material_indices[mat_id]]
            if img is not None:
                uv1.data[i].image = img

        # DEBUG BSP
        """for iNode in range(len(self.mobn.Nodes)):
            bsp_node_indices = self.GetBSPNodeIndices(iNode, self.mobn.Nodes, self.mobr.Faces, self.movi.Indices)
            bsp_node_vg = nobj.vertex_groups.new("debug_bsp")

            #for i in bsp_n1_indices:
            #    bsp_n1_GroupIndices.append(i)

            bsp_node_vg.add(bsp_node_indices, 1.0, 'ADD')"""
        # DEBUG BSP

        # add collision vertex group
        collision_indices = self.get_collision_indices()

        if collision_indices:
            collision_vg = nobj.vertex_groups.new("Collision")
            collision_vg.add(collision_indices, 1.0, 'ADD')
            nobj.wow_wmo_vertex_info.vertex_group = collision_vg.name

        # add WMO group properties
        nobj.wow_wmo_group.enabled = True
        nobj.wow_wmo_group.description = self.root.mogn.get_string(self.mogp.desc_group_name_ofs)
        nobj.wow_wmo_group.group_dbc_id = int(self.mogp.group_id)

        objects = bpy.context.scene.objects
        nobj.wow_wmo_group.fog1 = objects[self.root.display_name + "_Fog_" + str(self.mogp.fog_indices[0]).zfill(2)]
        nobj.wow_wmo_group.fog2 = objects[self.root.display_name + "_Fog_" + str(self.mogp.fog_indices[1]).zfill(2)]
        nobj.wow_wmo_group.fog3 = objects[self.root.display_name + "_Fog_" + str(self.mogp.fog_indices[2]).zfill(2)]
        nobj.wow_wmo_group.fog4 = objects[self.root.display_name + "_Fog_" + str(self.mogp.fog_indices[3]).zfill(2)]

        if self.mogp.flags & MOGPFlags.HasWater:
            self.load_liquids(nobj.name, nobj.location)

        else:
            # getting Liquid Type ID

            if self.root.mohd.flags & 0x4:
                real_liquid_type = self.mogp.liquid_type
            else:
                real_liquid_type = self.from_wmo_liquid_type(self.mogp.liquid_type)
                real_liquid_type = 0 if real_liquid_type == 17 else real_liquid_type

            nobj.wow_wmo_group.liquid_type = str(real_liquid_type)

        if not editable_doodads and self.mogp.flags & MOGPFlags.HasDoodads:
            if self.modr.doodad_refs:
                for i in range(len(self.modr.doodad_refs)):
                    doodad = nobj.wow_wmo_group.modr.add()
                    doodad.value = self.modr.doodad_refs[i]

        if self.mogp.flags & MOGPFlags.Indoor:
            nobj.wow_wmo_group.place_type = str(0x2000)
        else:
            nobj.wow_wmo_group.place_type = str(0x8)

        flag_set = nobj.wow_wmo_group.flags

        if self.mogp.flags & MOGPFlags.DoNotUseLocalLighting:
            flag_set.add('1')

        if self.mogp.flags & MOGPFlags.AlwaysDraw:
            flag_set.add('2')

        if self.mogp.flags & MOGPFlags.IsMountAllowed:
            flag_set.add('3')

        if self.mogp.flags & MOGPFlags.HasSkybox:
            flag_set.add('4')

        nobj.wow_wmo_group.flags = flag_set

        mesh.validate(clean_customdata=False)
        mesh.update()

        nobj.select = True

        if scn.objects.active is None or scn.objects.active.mode == 'OBJECT':
            scn.objects.active = nobj

        if self.root.parent:
            nobj.parent = self.root.parent

    def get_portal_direction(self, portal_obj, group_obj):
        """ Get the direction of MOPR portal relation given a portal object and a target group """

        def try_calculate_direction():

            mesh = group_obj.data
            portal_mesh = portal_obj.data
            normal = portal_obj.data.polygons[0].normal

            for poly in mesh.polygons:
                poly_normal = mathutils.Vector(poly.normal)
                g_center = group_obj.matrix_world * poly.center + poly_normal * sys.float_info.epsilon

                dist = normal[0] * g_center[0] + normal[1] * g_center[1] \
                     + normal[2] * g_center[2] - portal_mesh.polygons[0].normal[0] \
                     * portal_mesh.vertices[portal_mesh.polygons[0].vertices[0]].co[0] \
                     - portal_mesh.polygons[0].normal[1] \
                     * portal_mesh.vertices[portal_mesh.polygons[0].vertices[0]].co[1] \
                     - portal_mesh.polygons[0].normal[2] \
                     * portal_mesh.vertices[portal_mesh.polygons[0].vertices[0]].co[2]

                if dist == 0:
                    continue

                for portal_poly in portal_mesh.polygons:

                    direction = portal_poly.center - g_center
                    length = mathutils.Vector(direction).length
                    direction.normalize()

                    angle = mathutils.Vector(direction).angle(poly.normal, None)

                    if angle is None or angle >= pi * 0.5:
                        continue

                    ray_cast_result = bpy.context.scene.ray_cast(g_center, direction)

                    if not ray_cast_result[0] \
                    or ray_cast_result[4].name == portal_obj.name \
                    or mathutils.Vector(
                        (ray_cast_result[1][0] - g_center[0], ray_cast_result[1][1] - g_center[1],
                         ray_cast_result[1][2] - g_center[2])).length > length:
                        result = 1 if dist > 0 else -1

                        if bound_relation_side == 0:
                            bound_relation.Side = -result

                        return result

            return 0

        bpy.context.scene.objects.active = portal_obj

        # check if this portal was already processed
        bound_relation_side = None
        bound_relation = None
        for relation in self.root.mopr.relations:
            if relation.portal_index == portal_obj.wow_wmo_portal.portal_id:
                bound_relation_side = relation.side
                bound_relation = relation

        if bound_relation_side:
            return -bound_relation_side

        if portal_obj.wow_wmo_portal.algorithm != '0':
            return 1 if portal_obj.wow_wmo_portal.algorithm == '1' else -1

        # reveal hidden geometry
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        portal_obj.select = True
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        portal_obj.select = False

        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')

        result = try_calculate_direction()

        if result:
            return result

        # triangulate the proxy portal
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.quads_convert_to_tris()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        result = try_calculate_direction()

        if result:
            return result

        if bound_relation_side is None:
            print("\nFailed to calculate direction for portal <<{}>>. "
                  "Calculation from another side will be attempted.".format(portal_obj.name))
        else:
            print("\nFailed to calculate direction from the opposite side for portal <<{}>> "
                  "You may consider setting up the direction manually.".format(portal_obj.name))

        return 0

    def save_liquid(self, ob):
        mesh = ob.data

        # apply mesh transformations
        active = bpy.context.scene.objects.active
        bpy.context.scene.objects.active = ob
        ob.select = True
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        ob.select = False
        bpy.context.scene.objects.active = active

        start_vertex = 0
        sum = 0
        for vertex in mesh.vertices:
            cur_sum = vertex.co[0] + vertex.co[1]

            if cur_sum < sum:
                start_vertex = vertex.index
                sum = cur_sum

        self.mliq.x_tiles = round(ob.dimensions[0] / 4.1666625)
        self.mliq.y_tiles = round(ob.dimensions[1] / 4.1666625)
        self.mliq.x_verts = self.mliq.x_tiles + 1
        self.mliq.y_verts = self.mliq.y_tiles + 1
        self.mliq.position = mesh.vertices[start_vertex].co

        self.mogp.flags |= 0x1000 # do we really need that?
        self.mogp.liquid_type = int(ob.wow_wmo_liquid.liquid_type)

        # creating liquid material

        material = bpy.data.materials.new(ob.name)
        material.wow_wmo_material.enabled = True
        material.wow_wmo_material.diff_color = ob.wow_wmo_liquid.color

        types_1 = {3, 7, 11}
        types_2 = {4, 8, 12}

        material.wow_wmo_material.texture1 = "DUNGEONS\\TEXTURES\\STORMWIND\\GRAY12.BLP"

        if self.mogp.liquid_type in types_1:
            material.wow_wmo_material.texture1 = "DUNGEONS\\TEXTURES\\METAL\\BM_BRSPIRE_CATWALK01.BLP"

        elif self.mogp.liquid_type in types_2:
            material.wow_wmo_material.texture1 = "DUNGEONS\\TEXTURES\\FLOOR\\JLO_UNDEADZIGG_SLIMEFLOOR.BLP"

        self.mliq.material_id = self.root.add_material(material)

        if self.mogp.liquid_type in types_1 or self.mogp.liquid_type in types_2:

            if mesh.uv_layers.active:

                uv_map = {}

                for poly in mesh.polygons:
                    for loop_index in poly.loop_indices:
                        if mesh.loops[loop_index].vertex_index not in uv_map:
                            uv_map[mesh.loops[loop_index].vertex_index] = mesh.uv_layers.active.data[loop_index].uv

                for i in range(self.mliq.x_verts * self.mliq.y_verts):
                    vertex = MagmaVertex()

                    vertex.u = int(uv_map.get(mesh.vertices[i].index)[0])
                    vertex.v = int(uv_map.get(mesh.vertices[i].index)[1])

                    vertex.height = mesh.vertices[i].co[2]
                    self.mliq.vertex_map.append(vertex)
            else:
                raise Exception("\nSlime and magma (lava) liquids require a UV map to be created.")

        else:

            for j in range(self.mliq.x_verts * self.mliq.y_verts):
                vertex = WaterVertex()

                vertex.height = mesh.vertices[j].co[2]
                self.mliq.vertex_map.append(vertex)

        for poly in mesh.polygons:
                tile_flag = 0
                blue = [0.0, 0.0, 1.0]

                bit = 1
                while bit <= 0x80:
                    vc_layer = mesh.vertex_colors["flag_" + hex(bit)]

                    if self.comp_colors(vc_layer.data[poly.loop_indices[0]].color, blue):
                        tile_flag |= bit
                    bit <<= 1

                self.mliq.tile_flags.append(tile_flag)

    def save(self, original_obj, obj, autofill_textures):
        """ Save WoW WMO group data for future export """
        print("\nSaving group: <<{}>>".format(obj.name[:-4]))

        bpy.context.scene.objects.active = obj
        mesh = obj.data

        if mesh.has_custom_normals:
            mesh.calc_normals_split()

        # create bmesh
        bm = bmesh.new()
        bm.from_object(obj, bpy.context.scene)

        # triangulate bmesh
        bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method=0, ngon_method=0)

        vertices = bm.verts
        edges = bm.edges
        faces = bm.faces

        vertices.ensure_lookup_table()
        edges.ensure_lookup_table()
        faces.ensure_lookup_table()

        # untag faces
        for face in faces:
            face.tag = False

        deform = bm.verts.layers.deform.active
        uv = bm.loops.layers.uv.active
        uv2 = bm.loops.layers.uv.get(obj.wow_wmo_vertex_info.second_uv)

        obj_blend_map = obj.vertex_groups.get(obj.wow_wmo_vertex_info.blendmap)
        vg_blend_map_index = obj_blend_map.index if obj_blend_map else 0

        obj_collision_vg = obj.vertex_groups.get(obj.wow_wmo_vertex_info.vertex_group)
        vg_collision_index = obj_collision_vg.index if obj_collision_vg else 0

        obj_batch_map = obj.vertex_groups.get(obj.wow_wmo_vertex_info.batch_map)
        vg_batch_map_index = obj_batch_map.index if obj_batch_map else 0

        vertex_colors = bm.loops.layers.color.active
        use_vertex_color = '0' in obj.wow_wmo_group.flags \
                               or (obj.wow_wmo_group.place_type == '8192' and '1' not in obj.wow_wmo_group.flags)

        if obj_blend_map:
            self.root.mohd.flags |= 0x2

        faces_set = set(faces)
        batches = {}

        while faces_set:
            face = next(iter(faces_set))
            batch_type = WMOGroupFile.get_batch_type(face, vg_batch_map_index, deform)
            linked_faces = WMOGroupFile.get_linked_faces(face, batch_type, uv, uv2, deform, vg_batch_map_index)
            batches.setdefault((face.material_index, batch_type), []).append(linked_faces)
            faces_set -= set(linked_faces)

        batches = sorted(batches.items(), key=lambda x: (x[0][1], x[0][0]))

        self.mver.version = 17

        start_triangle = 0
        start_vertex = 0
        next_v_index_local = 0
        for batch_info, batch_groups in batches:
            mat_index, batch_type = batch_info

            for batch_group in batch_groups:
                n_faces = len(batch_group)
                n_vertices = n_faces * 3

                batch = Batch()
                batch.start_triangle = start_triangle
                batch.n_triangles = n_vertices
                batch.start_vertex = start_vertex
                batch.last_vertex = start_vertex + n_vertices - 1
                batch.material_id = self.root.add_material(mesh.materials[mat_index])
                batch.bounding_box = [32767, 32767, 32767, -32768, -32768, -32768]

                # increment start indices for the next batch
                start_triangle = start_triangle + batch.n_triangles
                start_vertex = batch.last_vertex + 1

                # do not write collision only batches as actual batches, because they are not
                if batch.material_id != 0xFF:
                    self.moba.batches.append(batch)

                if batch_type == 0:
                    self.mogp.n_batches_a += 1
                elif batch_type == 1:
                    self.mogp.n_batches_b += 1
                elif batch_type == 2:
                    self.mogp.n_batches_c += 1

                # actually save geometry
                vertex_map = {}
                for i, face in enumerate(batch_group):

                    tri_mat = TriangleMaterial()
                    tri_mat.material_id = batch.material_id

                    collision_counter = 0
                    for j, vertex in enumerate(face.verts):
                        vert_info = vertex_map.get(vertex.index)
                        dvert = vertex[deform]

                        if vert_info is None:

                            # determine if vertex is collideable
                            is_collideable = obj_collision_vg and (vg_collision_index in dvert)

                            if is_collideable:
                                collision_counter += 1

                            vertex_map[vertex.index] = next_v_index_local, is_collideable
                            v_index_local = next_v_index_local
                            next_v_index_local += 1

                            # handle basic geometry elements
                            self.movt.vertices.append(vertex.co.to_tuple())
                            self.monr.normals.append(vertex.normal.to_tuple())
                            self.motv.tex_coords.append((face.loops[j][uv].uv[0],
                                                         1.0 - face.loops[j][uv].uv[1]))

                            # handle second UV map layer
                            if uv2:
                                self.motv2.tex_coords.append((face.loops[j][uv].uv[0],
                                                             1.0 - face.loops[j][uv2].uv[1]))

                            # handler vertex color
                            if use_vertex_color:
                                if vertex_colors:
                                    vertex_color = [0x7F, 0x7F, 0x7F, 0x00]
                                    vcol = face.loops[j][vertex_colors]

                                    for k in range(3):
                                        vertex_color[k] = round(vcol[3 - k - 1] * 255)

                                    # in batch A it is guaranteed that blendmap exists
                                    if batch_type == 0:
                                        attenuation = round(dvert[vg_batch_map_index] * 255)

                                        if attenuation > 0:
                                            tri_mat.flags |= 0x1  # TODO: actually check what this does

                                        vertex_color[3] = attenuation

                                    self.mocv.vert_colors.append(vertex_color)
                                else:
                                    # set correct default values for vertex
                                    self.mocv.vert_colors.append([0x7F, 0x7F, 0x7F, 0x00]
                                                                 if batch_type == 2 else [0x7F, 0x7F, 0x7F, 0xFF])

                            if obj_blend_map:
                                if vg_blend_map_index in dvert:
                                    blend_factor = round(dvert[vg_blend_map_index] * 255)
                                else:
                                    blend_factor = 1

                                self.mocv2.vert_colors.append((0, 0, 0, blend_factor))

                            self.movi.indices.append(v_index_local)
                            # tri_indices[j] = v_index_local

                            # calculate bounding box
                            for k in range(2):
                                for l in range(3):
                                    idx = k * 3 + l
                                    batch.bounding_box[idx] = min(batch.bounding_box[idx], int(floor(vertex.co[l]))) \
                                        if k == 0 else max(batch.bounding_box[idx], int(ceil(vertex.co[l])))

                        else:
                            v_index_local, is_collideable = vert_info

                            if is_collideable:
                                collision_counter += 1

                            self.movi.indices.append(v_index_local)

                    tri_mat.flags = 0x8 if tri_mat.material_id == 0xFF else 0x20
                    tri_mat.flags |= 0x40 if collision_counter == 3 else 0x4 | 0x8

                    self.mopy.triangle_materials.append(tri_mat)

        # free bmesh
        bm.free()

        # write header
        self.mogp.bounding_box_corner1 = [32767.0, 32767.0, 32767.0]
        self.mogp.bounding_box_corner2 = [-32768.0, -32768.0, -32768.0]

        for vtx in self.movt.vertices:
            for j in range(0, 3):
                self.mogp.bounding_box_corner1[j] = min(self.mogp.bounding_box_corner1[j], vtx[j])
                self.mogp.bounding_box_corner2[j] = max(self.mogp.bounding_box_corner2[j], vtx[j])

        self.mogp.flags |= MOGPFlags.HasCollision  # /!\ MUST HAVE 0x1 FLAG ELSE THE GAME CRASH !
        if '0' in obj.wow_wmo_group.flags:
            self.mogp.flags |= MOGPFlags.HasVertexColor
        if '4' in obj.wow_wmo_group.flags:
            self.mogp.flags |= MOGPFlags.HasSkybox
        if '1' in obj.wow_wmo_group.flags:
            self.mogp.flags |= MOGPFlags.DoNotUseLocalLighting
        if '2' in obj.wow_wmo_group.flags:
            self.mogp.flags |= MOGPFlags.AlwaysDraw
        if '3' in obj.wow_wmo_group.flags:
            self.mogp.flags |= MOGPFlags.IsMountAllowed

        self.mogp.flags |= int(obj.wow_wmo_group.place_type)

        has_lights = False

        fogs = (obj.wow_wmo_group.fog1,
                obj.wow_wmo_group.fog2,
                obj.wow_wmo_group.fog3,
                obj.wow_wmo_group.fog4)

        lamps = obj.wow_wmo_group.relations.lights

        # set fog references
        self.mogp.fog_indices = (fogs[0].wow_wmo_fog.fog_id if fogs[0] else 0,
                                 fogs[1].wow_wmo_fog.fog_id if fogs[0] else 0,
                                 fogs[2].wow_wmo_fog.fog_id if fogs[0] else 0,
                                 fogs[3].wow_wmo_fog.fog_id if fogs[0] else 0)
        # save lamps
        if lamps:
            has_lights = True
            for lamp in lamps:
                self.molr.LightRefs.append(lamp.id)

        self.mogp.group_id = int(obj.wow_wmo_group.group_dbc_id)
        group_info = self.root.add_group_info(self.mogp.flags,
                                              [self.mogp.bounding_box_corner1, self.mogp.bounding_box_corner2],
                                              original_obj.name,
                                              obj.wow_wmo_group.description)

        self.mogp.group_name_ofs = group_info[0]
        self.mogp.desc_group_name_ofs = group_info[1]

        if len(obj.wow_wmo_group.modr):
            for doodad in obj.wow_wmo_group.modr:
                self.modr.doodad_refs.append(doodad.value)
            self.mogp.flags |= MOGPFlags.HasDoodads
        elif obj.wow_wmo_group.relations.doodads:
            for doodad in obj.wow_wmo_group.relations.doodads:
                self.modr.doodad_refs.append(doodad.id)
            self.mogp.flags |= MOGPFlags.HasDoodads
        else:
            self.modr = None

        bsp_tree = BSPTree()
        bsp_tree.GenerateBSP(self.movt.vertices, self.movi.indices, obj.wow_wmo_vertex_info.node_size)

        self.mobn.nodes = bsp_tree.Nodes
        self.mobr.faces = bsp_tree.Faces

        if '0' not in obj.wow_wmo_group.flags:
            if obj.wow_wmo_group.place_type == '8192':
                if '1' in obj.wow_wmo_group.flags \
                and not len(mesh.vertex_colors):
                    self.mocv = None
                else:
                    self.mogp.flags |= MOGPFlags.HasVertexColor
            else:
                self.mocv = None

        if not self.mogp.flags & MOGPFlags.HasWater:
            self.mliq = None
            self.mogp.flags |= MOGPFlags.IsNotOcean # check if this is necessary
            self.root.mohd.flags |= 0x4
            self.mogp.liquid_type = int(obj.wow_wmo_group.liquid_type)

        if not has_lights:
            self.molr = None
        else:
            self.mogp.flags |= MOGPFlags.HasLight

        # write second MOTV and MOCV
        if uv2 is None:
            self.motv2 = None

        if obj_blend_map is None:
            self.mocv2 = None

        print("\nDone saving group: <<{}>>".format(obj.name[:-4]))



