import bpy
import mathutils
import bmesh

from math import pi, ceil, floor

from ..pywowlib.file_formats.wmo_format_group import MOGPFlags, LiquidVertex, TriangleMaterial, Batch
from ..pywowlib.wmo_file import WMOGroupFile
from .bsp_tree import *
from .render import BlenderWMOObjectRenderFlags


class BlenderWMOSceneGroup:
    def __init__(self, wmo_scene, wmo_group, obj=None):
        self.wmo_group : WMOGroupFile = wmo_group
        self.wmo_scene = wmo_scene
        self.bl_object : bpy.types.Object = obj
        self.name = wmo_scene.wmo.mogn.get_string(wmo_group.mogp.group_name_ofs)

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

        for i in range(3):
            if color1[i] != color2[i]:
                return False
        return True

    @staticmethod
    def comp_colors_key(color1):
        for i in range(len(color1)):
            if color1[i] > 0:
                return True
        return False


    @staticmethod
    def get_batch_type(b_face, batch_map_trans, batch_map_int):
        """ Find which MOBA batch type a passed bmesh face belongs two """

        if not batch_map_trans and not batch_map_int:
            return 2

        trans_count = 0
        int_count = 0

        n_verts = len(b_face.loops)

        for loop in b_face.loops:
            if batch_map_trans and BlenderWMOSceneGroup.comp_colors_key(loop[batch_map_trans]):
                trans_count += 1

            if batch_map_int and BlenderWMOSceneGroup.comp_colors_key(loop[batch_map_int]):
                int_count += 1

        if trans_count == n_verts:
            return 0
        elif int_count == n_verts:
            return 1
        else:
            return 2


    @staticmethod
    def get_material_viewport_image(material):
        """ Get viewport image assigned to a material """

        if material.wow_wmo_material.diff_texture_1:
            return material.wow_wmo_material.diff_texture_1

    @staticmethod
    def get_linked_faces(b_face, face_batch_type, uv, uv2, batch_map_trans, batch_map_int, stack=0):
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
                batch_type = BlenderWMOSceneGroup.get_batch_type(link_face, batch_map_trans, batch_map_int)

                if batch_type != face_batch_type:
                    continue

                # call this function recursively on this face if all checks are passed
                f_linked.extend(BlenderWMOSceneGroup.get_linked_faces(link_face, batch_type, uv, uv2, batch_map_trans,
                                                                      batch_map_int, stack=stack + 1))

        return f_linked

    def from_wmo_liquid_type(self, basic_liquid_type):
        """ Convert simplified WMO liquid type IDs to real LiquidType.dbc IDs """
        real_liquid_type = 0

        if basic_liquid_type < 20:
            if basic_liquid_type == 0:
                real_liquid_type = 14 if self.wmo_group.mogp.flags & 0x80000 else 13
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

        group = self.wmo_group

        # load vertices
        vertices = []
        for y in range(0, group.mliq.y_verts):
            y_pos = group.mliq.position[1] + y * 4.1666625
            for x in range(0, group.mliq.x_verts):
                x_pos = group.mliq.position[0] + x * 4.1666625
                vertices.append((x_pos, y_pos, group.mliq.vertex_map[y * group.mliq.x_verts + x].height))

        # calculate faces
        indices = []
        for y in range(group.mliq.y_tiles):
            for x in range(group.mliq.x_tiles):
                indices.append(y * group.mliq.x_verts + x)
                indices.append(y * group.mliq.x_verts + x + 1)
                indices.append((y + 1) * group.mliq.x_verts + x)
                indices.append((y + 1) * group.mliq.x_verts + x + 1)

        faces = []

        for i in range(0, len(indices), 4):
            faces.append((indices[i], indices[i + 1], indices[i + 3], indices[i + 2]))

        # create mesh and object
        name = group_name + "_Liquid"
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        # create mesh from python data
        mesh.from_pydata(vertices, [], faces)
        mesh.update(calc_edges=True)
        mesh.validate()

        # create uv map if liquid is lava
        if group.mogp.liquid_type in {3, 4, 7, 8, 11, 12}:
            uv_map = {}

            for vertex in mesh.vertices:
                uv_map[vertex.index] = (group.mliq.vertex_map[vertex.index].u,
                                        group.mliq.vertex_map[vertex.index].v)

            mesh.uv_layers.new(name="UVMap")
            uv_layer1 = mesh.uv_layers[0]

            for poly in mesh.polygons:
                for loop_index in poly.loop_indices:
                    uv_layer1.data[loop_index].uv = (uv_map.get(mesh.loops[loop_index].vertex_index)[0],
                                                     - uv_map.get(mesh.loops[loop_index].vertex_index)[1])

        # setting flags in a hacky way using vertex colors
        bit = 1
        counter = 0
        while bit <= 0x80:
            vc_layer = mesh.vertex_colors.new(name="flag_" + str(counter))
            counter += 1

            for poly in mesh.polygons:
                tile_flag = group.mliq.tile_flags[poly.index]
                for loop in poly.loop_indices:
                    if tile_flag & bit:
                        vc_layer.data[loop].color = (0, 0, 255, 255)
            bit <<= 1

        # set mesh location
        obj.location = pos
        bpy.context.collection.objects.link(obj)

        bpy.context.view_layer.objects.active = obj

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=True)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        obj.lock_scale = [True, True, True]
        obj.lock_rotation[2] = True

        obj.wow_wmo_liquid.enabled = True

        # getting Liquid Type ID
        if self.wmo_scene.wmo.mohd.flags & 0x4:
            real_liquid_type = group.mogp.liquid_type
        else:
            real_liquid_type = self.from_wmo_liquid_type(group.mogp.liquid_type)

        obj.wow_wmo_liquid.color = self.wmo_scene.bl_materials[group.mliq.material_id].wow_wmo_material.diff_color

        wmo_group_obj = bpy.context.scene.objects[group_name]
        wmo_group_obj.wow_wmo_group.liquid_type = str(real_liquid_type)
        wmo_group_obj.wow_wmo_group.liquid_mesh = obj

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

        group = self.wmo_group
        node_indices = self.get_bsp_node_indices(0, group.mobn.nodes, group.mobr.faces, group.movi.indices)
        indices = []
        for i in node_indices:
            if not group.mopy.triangle_materials[i].flags & 0x04:
                indices.append(group.movi.indices[i * 3])
                indices.append(group.movi.indices[i * 3 + 1])
                indices.append(group.movi.indices[i * 3 + 2])

        return indices

    def load_object(self):
        """ Load WoW WMO group as an object to the Blender scene """

        group = self.wmo_group

        vertices = group.movt.vertices
        normals = group.monr.normals
        tex_coords = group.motv.tex_coords
        faces = [group.movi.indices[i:i + 3] for i in range(0, len(group.movi.indices), 3)]

        # create mesh
        mesh = bpy.data.meshes.new(self.name)
        mesh.from_pydata(vertices, [], faces)

        # create object
        scn = bpy.context.scene

        nobj = bpy.data.objects.new(self.name, mesh)
        scn.collection.objects.link(nobj)

        collision_face_ids = []
        for i, poly in enumerate(mesh.polygons):
            poly.use_smooth = True

            if group.mopy.triangle_materials[i].material_id == 0xFF:
                collision_face_ids.append(i)

        # set normals
        for i in range(len(normals)):
            mesh.vertices[i].normal = normals[i]

        custom_normals = [(0.0, 0.0, 0.0)] * len(mesh.loops)
        mesh.use_auto_smooth = True
        for i, loop in enumerate(mesh.loops):
            mesh.vertices[loop.vertex_index].normal = normals[loop.vertex_index]
            custom_normals[i] = normals[loop.vertex_index]

        mesh.normals_split_custom_set(custom_normals)

        pass_index = 0

        # set vertex color
        vertex_color_layer = None
        lightmap = None
        if group.mogp.flags & MOGPFlags.HasVertexColor:
            flag_set = nobj.wow_wmo_group.flags
            flag_set.add('0')
            nobj.wow_wmo_group.flags = flag_set
            vertex_color_layer = mesh.vertex_colors.new(name="Col")
            lightmap = mesh.vertex_colors.new(name="Lightmap")

            pass_index |= BlenderWMOObjectRenderFlags.HasVertexColor
            pass_index |= BlenderWMOObjectRenderFlags.HasLightmap

        blendmap = None
        if group.mogp.flags & MOGPFlags.HasTwoMOCV:
            blendmap = mesh.vertex_colors.new(name="Blendmap")

            pass_index |= BlenderWMOObjectRenderFlags.HasBlendmap

        # set uv
        uv1 = mesh.uv_layers.new(name="UVMap")
        uv_layer1 = mesh.uv_layers[0]

        for i in range(len(uv_layer1.data)):
            # set uv1
            uv = tex_coords[mesh.loops[i].vertex_index]
            uv_layer1.data[i].uv = (uv[0], 1 - uv[1])

        uv_layer2 = None
        if group.mogp.flags & MOGPFlags.HasTwoMOTV:
            uv2 = mesh.uv_layers.new(name="UVMap.001")
            nobj.wow_wmo_vertex_info.second_uv = uv2.name
            uv_layer2 = mesh.uv_layers[1]

        # map wmo material ID to index in mesh materials
        material_indices = {}
        material_viewport_textures = {}

        # create batch vertex groups

        batch_map_a = None
        batch_map_b = None

        if group.mogp.n_batches_a != 0:
            batch_map_a = mesh.vertex_colors.new(name="BatchmapTrans")
            pass_index |= BlenderWMOObjectRenderFlags.HasBatchA

        if group.mogp.n_batches_b != 0:
            batch_map_b = mesh.vertex_colors.new(name="BatchmapInt")
            pass_index |= BlenderWMOObjectRenderFlags.HasBatchB

        # nobj.wow_wmo_vertex_info.batch_map = batch_map.name

        batch_material_map = {}

        batch_a_range = range(0, group.moba.batches[group.mogp.n_batches_a - 1].last_vertex + 1
        if group.mogp.n_batches_a else 0)

        batch_b_range = range(len(batch_a_range) - 1,
                              group.moba.batches[group.mogp.n_batches_a + group.mogp.n_batches_b - 1].last_vertex + 1
                              if group.mogp.n_batches_b else len(batch_a_range) - 1)

        # add materials
        for i, batch in enumerate(group.moba.batches):

            material = self.wmo_scene.bl_materials[group.moba.batches[i].material_id]

            mat_index_local = material_indices.get(batch.material_id)

            if mat_index_local is None:
                mat_id = len(mesh.materials)
                material_indices[batch.material_id] = mat_id

                image = self.get_material_viewport_image(material)
                material_viewport_textures[mat_id] = image
                mesh.materials.append(material)
                mat_index_local = mat_id

            for poly in mesh.polygons[batch.start_triangle // 3: (batch.start_triangle + batch.n_triangles) // 3]:

                poly.material_index = mat_index_local

            batch_material_map[(batch.start_triangle // 3,
                                (batch.start_triangle + group.moba.batches[i].n_triangles) // 3)] = batch.material_id

        # add ghost material
        for i in group.mopy.triangle_materials:
            if i.material_id == 0xFF:
                mat_ghost__id = len(mesh.materials)
                mesh.materials.append(self.wmo_scene.bl_materials[0xFF])
                material_viewport_textures[mat_ghost__id] = None
                material_indices[0xFF] = mat_ghost__id
                break

        # set layer data
        for i, loop in enumerate(mesh.loops):

            if vertex_color_layer is not None:
                mesh.vertex_colors['Col'].data[i].color = (group.mocv.vert_colors[loop.vertex_index][2] / 255,
                                                           group.mocv.vert_colors[loop.vertex_index][1] / 255,
                                                           group.mocv.vert_colors[loop.vertex_index][0] / 255,
                                                           1.0)

                mesh.vertex_colors['Lightmap'].data[i].color = (group.mocv.vert_colors[loop.vertex_index][3] / 255,
                                                                group.mocv.vert_colors[loop.vertex_index][3] / 255,
                                                                group.mocv.vert_colors[loop.vertex_index][3] / 255,
                                                                1.0)

            if blendmap is not None:
                mocv_layer = group.mocv2 if group.mogp.flags & MOGPFlags.HasVertexColor else group.mocv
                mesh.vertex_colors['Blendmap'].data[i].color = (mocv_layer.vert_colors[loop.vertex_index][3] / 255,
                                                                mocv_layer.vert_colors[loop.vertex_index][3] / 255,
                                                                mocv_layer.vert_colors[loop.vertex_index][3] / 255,
                                                                1.0)

            if uv_layer2 is not None:
                uv = group.motv2.tex_coords[loop.vertex_index]
                uv_layer2.data[i].uv = (uv[0], 1 - uv[1])

            if batch_map_a:
                mesh.vertex_colors['BatchmapTrans'].data[i].color = (1, 1, 1, 1) if loop.vertex_index in batch_a_range else (0, 0, 0, 0)

            if batch_map_b:
                mesh.vertex_colors['BatchmapInt'].data[i].color = (1, 1, 1, 1) if loop.vertex_index in batch_b_range else (0, 0, 0, 0)
        '''
        # set faces material
        for i in range(len(mesh.polygons)):
            mat_id = group.mopy.triangle_materials[i].material_id
 
            mesh.polygons[i].material_index = material_indices[mat_id]
 
            # set texture displayed in viewport
            img = material_viewport_textures[material_indices[mat_id]]
            if img is not None:
                uv1.data[i].image = img
 
        '''

        # DEBUG BSP
        """for iNode in range(len(group.mobn.Nodes)):
            bsp_node_indices = group.GetBSPNodeIndices(iNode, group.mobn.Nodes, group.mobr.Faces, group.movi.Indices)
            bsp_node_vg = nobj.vertex_groups.new("debug_bsp")
 
            #for i in bsp_n1_indices:
            #    bsp_n1_GroupIndices.append(i)
 
            bsp_node_vg.add(bsp_node_indices, 1.0, 'ADD')"""
        # DEBUG BSP

        # add collision vertex group
        collision_indices = self.get_collision_indices()

        if collision_indices:
            collision_vg = nobj.vertex_groups.new(name="Collision")
            collision_vg.add(collision_indices, 1.0, 'ADD')
            nobj.wow_wmo_vertex_info.vertex_group = collision_vg.name

        # add WMO group properties
        nobj.wow_wmo_group.enabled = True
        nobj.wow_wmo_group.description = self.wmo_scene.wmo.mogn.get_string(group.mogp.desc_group_name_ofs)
        nobj.wow_wmo_group.group_dbc_id = int(group.mogp.group_id)

        nobj.wow_wmo_group.fog1 = self.wmo_scene.bl_fogs[group.mogp.fog_indices[0]]
        nobj.wow_wmo_group.fog2 = self.wmo_scene.bl_fogs[group.mogp.fog_indices[1]]
        nobj.wow_wmo_group.fog3 = self.wmo_scene.bl_fogs[group.mogp.fog_indices[2]]
        nobj.wow_wmo_group.fog4 = self.wmo_scene.bl_fogs[group.mogp.fog_indices[3]]

        if group.mogp.flags & MOGPFlags.HasWater:
            self.load_liquids(nobj.name, nobj.location)

        else:
            # getting Liquid Type ID

            if self.wmo_scene.wmo.mohd.flags & 0x4:
                real_liquid_type = group.mogp.liquid_type
            else:
                real_liquid_type = self.from_wmo_liquid_type(group.mogp.liquid_type)
                real_liquid_type = 0 if real_liquid_type == 17 else real_liquid_type

            nobj.wow_wmo_group.liquid_type = str(real_liquid_type)

        if group.mogp.flags & MOGPFlags.Indoor:
            nobj.wow_wmo_group.place_type = str(0x2000)
            pass_index |= BlenderWMOObjectRenderFlags.IsIndoor
        else:
            nobj.wow_wmo_group.place_type = str(0x8)
            pass_index |= BlenderWMOObjectRenderFlags.IsOutdoor

        flag_set = nobj.wow_wmo_group.flags

        if group.mogp.flags & MOGPFlags.DoNotUseLocalLighting:
            flag_set.add('1')
            pass_index |= BlenderWMOObjectRenderFlags.NoLocalLight

        if group.mogp.flags & MOGPFlags.AlwaysDraw:
            flag_set.add('2')

        if group.mogp.flags & MOGPFlags.IsMountAllowed:
            flag_set.add('3')

        if group.mogp.flags & MOGPFlags.HasSkybox:
            flag_set.add('4')

        nobj.wow_wmo_group.flags = flag_set
        nobj.pass_index = pass_index

        # remove collision faces from mesh\
        if collision_face_ids:

            bm_col = bmesh.new()

            bm = bmesh.new()
            bm.from_mesh(mesh)

            bm.faces.ensure_lookup_table()
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            bm_collision_faces = [bm.faces[i] for i in collision_face_ids]

            # create collision mesh
            vert_map = {}
            for face in bm_collision_faces:
                face_verts = [None, None, None]
                for j, vert in enumerate(face.verts):

                    n_vert = vert_map.get(vert.index)
                    if not n_vert:
                        n_vert = bm_col.verts.new(vert.co)
                        vert_map[vert.index] = n_vert

                    face_verts[j] = n_vert

                try:
                    bm_col.faces.new(face_verts)
                except ValueError:
                    pass
                    # print('\nWARNING: Duplicated face was removed from collision geometry.')

            c_mesh = bpy.data.meshes.new(name=self.name + '_Collision')
            bm_col.to_mesh(c_mesh)
            bm_col.free()

            # remove collision faces from original mesh
            bmesh.ops.delete(bm, geom=bm_collision_faces, context='FACES')
            bm.to_mesh(mesh)
            mesh.update()
            bpy.context.view_layer.update()
            bm.free()

            c_obj = bpy.data.objects.new(c_mesh.name, c_mesh)
            scn.collection.objects.link(c_obj)
            nobj.wow_wmo_group.collision_mesh = c_obj

    def get_portal_direction(self, portal_obj, group_obj):
        """ Get the direction of MOPR portal relation given a portal object and a target group """

        def try_calculate_direction():

            mesh = group_obj.data
            portal_mesh = portal_obj.data
            normal = portal_obj.data.polygons[0].normal

            for poly in mesh.polygons:
                poly_normal = mathutils.Vector(poly.normal)
                g_center = group_obj.matrix_world @ poly.center + poly_normal * sys.float_info.epsilon

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

                    ray_cast_result = bpy.context.scene.ray_cast(bpy.context.view_layer, g_center, direction)

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

        bpy.ops.object.select_all(action='DESELECT')

        bpy.context.view_layer.objects.active = portal_obj

        # check if this portal was already processed
        bound_relation_side = None
        bound_relation = None
        for relation in self.wmo_scene.wmo.mopr.relations:
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

        portal_obj.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        portal_obj.select_set(False)

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
            print("\nFailed to calculate direction for portal \"{}\". "
                  "Calculation from another side will be attempted.".format(portal_obj.name))
        else:
            print("\nFailed to calculate direction from the opposite side for portal \"{}\" "
                  "You may consider setting up the direction manually.".format(portal_obj.name))

        return 0

    def save_liquid(self, ob):

        group = self.wmo_group

        mesh = ob.data

        # apply mesh transformations
        active = bpy.context.view_layer.objects.active
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        ob.select_set(False)
        bpy.context.view_layer.objects.active = active

        start_vertex = 0
        sum = 0
        for vertex in mesh.vertices:
            cur_sum = vertex.co[0] + vertex.co[1]

            if cur_sum < sum:
                start_vertex = vertex.index
                sum = cur_sum

        group.mliq.x_tiles = round(ob.dimensions[0] / 4.1666625)
        group.mliq.y_tiles = round(ob.dimensions[1] / 4.1666625)
        group.mliq.x_verts = group.mliq.x_tiles + 1
        group.mliq.y_verts = group.mliq.y_tiles + 1
        group.mliq.position = mesh.vertices[start_vertex].co.to_tuple()

        group.mogp.flags |= 0x1000  # do we really need that?

        types_1 = {3, 7, 11}
        types_2 = {4, 8, 12}

        texture1 = "DUNGEONS\\TEXTURES\\STORMWIND\\GRAY12.BLP"

        if group.mogp.liquid_type in types_1:
            texture1 = "DUNGEONS\\TEXTURES\\METAL\\BM_BRSPIRE_CATWALK01.BLP"

        elif group.mogp.liquid_type in types_2:
            texture1 = "DUNGEONS\\TEXTURES\\FLOOR\\JLO_UNDEADZIGG_SLIMEFLOOR.BLP"

        diff_color = (int(ob.wow_wmo_liquid.color[0] * 255),
                      int(ob.wow_wmo_liquid.color[1] * 255),
                      int(ob.wow_wmo_liquid.color[2] * 255),
                      int(ob.wow_wmo_liquid.color[3] * 255)
                     )

        group.mliq.material_id = self.wmo_scene.wmo.add_material(texture1, diff_color=diff_color)

        if group.mogp.liquid_type in types_1 or group.mogp.liquid_type in types_2:

            if mesh.uv_layers.active:

                uv_map = {}

                for poly in mesh.polygons:
                    for loop_index in poly.loop_indices:
                        if mesh.loops[loop_index].vertex_index not in uv_map:
                            uv_map[mesh.loops[loop_index].vertex_index] = mesh.uv_layers.active.data[loop_index].uv

                for i in range(group.mliq.x_verts * group.mliq.y_verts):
                    vertex = LiquidVertex()
                    vertex.is_water = False

                    vertex.u = int(uv_map.get(mesh.vertices[i].index)[0])
                    vertex.v = int(uv_map.get(mesh.vertices[i].index)[1])

                    vertex.height = mesh.vertices[i].co[2]
                    group.mliq.vertex_map.append(vertex)
            else:
                raise Exception("\nError saving WMO. Slime and magma (lava) liquids require a UV map to be created.")

        else:

            for j in range(group.mliq.x_verts * group.mliq.y_verts):
                vertex = LiquidVertex()

                vertex.height = mesh.vertices[j].co[2]
                group.mliq.vertex_map.append(vertex)

        for poly in mesh.polygons:
            tile_flag = 0
            blue = [0.0, 0.0, 1.0]

            counter = 0
            bit = 1
            while bit <= 0x80:
                vc_layer = mesh.vertex_colors["flag_{}".format(counter)]

                if self.comp_colors(vc_layer.data[poly.loop_indices[0]].color, blue):
                    tile_flag |= bit
                bit <<= 1

                counter += 1

            group.mliq.tile_flags.append(tile_flag)

    def save(self):
        """ Save WoW WMO group data for future export """

        obj = self.bl_object

        group = self.wmo_group
        scene = bpy.context.scene

        bpy.context.view_layer.objects.active = obj
        mesh = obj.data

        if mesh.has_custom_normals:
            mesh.calc_normals_split()

        # create bmesh
        bm = bmesh.new()
        bm.from_object(obj, bpy.context.evaluated_depsgraph_get())

        # triangulate bmesh
        bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')

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
        uv2 = bm.loops.layers.uv.get('UVMap.001')

        obj_collision_vg = None
        vg_collision_index = 0

        if obj.wow_wmo_vertex_info.vertex_group:
            obj_collision_vg = obj.vertex_groups.get(obj.wow_wmo_vertex_info.vertex_group)
            vg_collision_index = obj_collision_vg.index

        obj_blend_map = bm.loops.layers.color.get('Blendmap')
        obj_batch_map_trans = bm.loops.layers.color.get('BatchmapTrans')
        obj_batch_map_int = bm.loops.layers.color.get('BatchmapInt')
        obj_light_map = bm.loops.layers.color.get('Lightmap')
        vertex_colors = bm.loops.layers.color.get('Col')

        use_vertex_color = '0' in obj.wow_wmo_group.flags \
                           or (obj.wow_wmo_group.place_type == '8192' and '1' not in obj.wow_wmo_group.flags)

        if obj_blend_map:
            self.wmo_scene.wmo.mohd.flags |= 0x2

        if obj.wow_wmo_group.collision_mesh:
            col_mesh = obj.wow_wmo_group.collision_mesh.data.copy()

            for poly in col_mesh.polygons:
                poly.material_index = 0xFF

            bm.from_mesh(col_mesh)
            bm.verts.ensure_lookup_table()
            bm.faces.ensure_lookup_table()

        faces_set = set(faces)
        batches = {}

        while faces_set:
            face = next(iter(faces_set))
            batch_type = BlenderWMOSceneGroup.get_batch_type(face, obj_batch_map_trans, obj_batch_map_int)

            linked_faces = BlenderWMOSceneGroup.get_linked_faces(face, batch_type, uv, uv2,
                                                                 obj_batch_map_trans, obj_batch_map_int)

            is_batch = face.material_index < len(mesh.materials)

            batches.setdefault((face.material_index if is_batch else 0xFF, batch_type), []).append(linked_faces)
            faces_set -= set(linked_faces)

        batches = sorted(batches.items(), key=lambda x: (x[0][1], x[0][0]))

        group.mver.version = 17

        start_triangle = 0
        start_vertex = 0
        next_v_index_local = 0
        for batch_info, batch_groups in batches:
            mat_index, batch_type = batch_info

            for batch_group in batch_groups:
                n_faces = len(batch_group)
                n_vertices = n_faces * 3
                mat_id = scene.wow_wmo_root_elements.materials.find(
                    mesh.materials[mat_index].name) if mat_index != 0xFF else mat_index

                batch = Batch()
                batch.start_triangle = start_triangle
                batch.n_triangles = n_vertices
                batch.start_vertex = start_vertex
                batch.last_vertex = start_vertex + n_vertices - 1
                batch.material_id = mat_id
                batch.bounding_box = [32767, 32767, 32767, -32768, -32768, -32768]

                # increment start indices for the next batch
                start_triangle = start_triangle + batch.n_triangles
                start_vertex = batch.last_vertex + 1

                # do not write collision only batches as actual batches, because they are not
                if batch.material_id != 0xFF:
                    group.moba.batches.append(batch)

                    if batch_type == 0:
                        group.mogp.n_batches_a += 1
                    elif batch_type == 1:
                        group.mogp.n_batches_b += 1
                    elif batch_type == 2:
                        group.mogp.n_batches_c += 1

                # actually save geometry
                vertex_map = {}
                for i, face in enumerate(batch_group):

                    tri_mat = TriangleMaterial()
                    tri_mat.material_id = batch.material_id

                    collision_counter = 0
                    for j, vertex in enumerate(face.verts):
                        vert_info = vertex_map.get(vertex.index)

                        dvert = vertex[deform] if deform else None

                        if vert_info is None:

                            # determine if vertex is collideable
                            is_collideable = (obj_collision_vg and (vg_collision_index in dvert)) or tri_mat.material_id == 0xFF

                            if is_collideable:
                                collision_counter += 1

                            vertex_map[vertex.index] = next_v_index_local, is_collideable
                            v_index_local = next_v_index_local
                            next_v_index_local += 1

                            # handle basic geometry elements
                            group.movt.vertices.append((obj.matrix_world @ vertex.co).to_tuple())
                            group.monr.normals.append(vertex.normal.to_tuple())
                            group.motv.tex_coords.append((face.loops[j][uv].uv[0],
                                                         1.0 - face.loops[j][uv].uv[1]))

                            # handle second UV map layer
                            if uv2:
                                group.motv2.tex_coords.append((face.loops[j][uv].uv[0],
                                                              1.0 - face.loops[j][uv2].uv[1]))

                            # handle vertex color
                            if use_vertex_color:
                                if vertex_colors and batch.material_id != 0xFF:
                                    vertex_color = [0x7F, 0x7F, 0x7F, 0x00]
                                    vcol = face.loops[j][vertex_colors]

                                    for k in range(3):
                                        vertex_color[k] = round(vcol[3 - k - 1] * 255)

                                    if obj_light_map:
                                        attenuation = round(face.loops[j][obj_light_map][0] * 255) if obj_light_map else 0

                                        if attenuation > 0:
                                            tri_mat.flags |= 0x1  # TODO: actually check what this does

                                        vertex_color[3] = attenuation

                                    group.mocv.vert_colors.append(vertex_color)
                                else:
                                    # set correct default values for vertex
                                    group.mocv.vert_colors.append([0x7F, 0x7F, 0x7F, 0x00])

                            if obj_blend_map:

                                blend_factor = round(face.loops[j][obj_blend_map][0] * 255) if obj_blend_map else 1
                                group.mocv2.vert_colors.append((0, 0, 0, blend_factor))

                            group.movi.indices.append(v_index_local)
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

                            group.movi.indices.append(v_index_local)

                    tri_mat.flags = 0x8 if tri_mat.material_id == 0xFF else 0x20
                    tri_mat.flags |= 0x40 if collision_counter == 3 else 0x4 | 0x8

                    group.mopy.triangle_materials.append(tri_mat)

        # free bmesh
        bm.free()

        # write header
        group.mogp.bounding_box_corner1 = [32767.0, 32767.0, 32767.0]
        group.mogp.bounding_box_corner2 = [-32768.0, -32768.0, -32768.0]

        for vtx in group.movt.vertices:
            for j in range(0, 3):
                group.mogp.bounding_box_corner1[j] = min(group.mogp.bounding_box_corner1[j], vtx[j])
                group.mogp.bounding_box_corner2[j] = max(group.mogp.bounding_box_corner2[j], vtx[j])

        group.mogp.flags |= MOGPFlags.HasCollision  # /!\ MUST HAVE 0x1 FLAG ELSE THE GAME CRASH !
        if '0' in obj.wow_wmo_group.flags:
            group.mogp.flags |= MOGPFlags.HasVertexColor
        if '4' in obj.wow_wmo_group.flags:
            group.mogp.flags |= MOGPFlags.HasSkybox
        if '1' in obj.wow_wmo_group.flags:
            group.mogp.flags |= MOGPFlags.DoNotUseLocalLighting
        if '2' in obj.wow_wmo_group.flags:
            group.mogp.flags |= MOGPFlags.AlwaysDraw
        if '3' in obj.wow_wmo_group.flags:
            group.mogp.flags |= MOGPFlags.IsMountAllowed

        group.mogp.flags |= int(obj.wow_wmo_group.place_type)

        has_lights = False

        fogs = (obj.wow_wmo_group.fog1,
                obj.wow_wmo_group.fog2,
                obj.wow_wmo_group.fog3,
                obj.wow_wmo_group.fog4)

        lamps = obj.wow_wmo_group.relations.lights

        # set fog references
        group.mogp.fog_indices = (fogs[0].wow_wmo_fog.fog_id if fogs[0] else 0,
                                 fogs[1].wow_wmo_fog.fog_id if fogs[0] else 0,
                                 fogs[2].wow_wmo_fog.fog_id if fogs[0] else 0,
                                 fogs[3].wow_wmo_fog.fog_id if fogs[0] else 0)
        # save lamps
        if lamps:
            has_lights = True
            for lamp in lamps:
                group.molr.LightRefs.append(lamp.id)

        group.mogp.group_id = int(obj.wow_wmo_group.group_dbc_id)
        group_info = self.wmo_scene.add_group_info(group.mogp.flags,
                                                  [group.mogp.bounding_box_corner1, group.mogp.bounding_box_corner2],
                                                  obj.name,
                                                  obj.wow_wmo_group.description)

        group.mogp.group_name_ofs = group_info[0]
        group.mogp.desc_group_name_ofs = group_info[1]

        if len(obj.wow_wmo_group.modr):
            for doodad in obj.wow_wmo_group.modr:
                group.modr.doodad_refs.append(doodad.value)
            group.mogp.flags |= MOGPFlags.HasDoodads
        elif obj.wow_wmo_group.relations.doodads:
            for doodad in obj.wow_wmo_group.relations.doodads:
                group.modr.doodad_refs.append(doodad.id)
            group.mogp.flags |= MOGPFlags.HasDoodads
        else:
            group.modr = None

        bsp_tree = BSPTree()
        bsp_tree.GenerateBSP(group.movt.vertices, group.movi.indices, obj.wow_wmo_vertex_info.node_size)

        group.mobn.nodes = bsp_tree.Nodes
        group.mobr.faces = bsp_tree.Faces

        if '0' not in obj.wow_wmo_group.flags:
            if obj.wow_wmo_group.place_type == '8192':
                if '1' in obj.wow_wmo_group.flags \
                        and not len(mesh.vertex_colors):
                    group.mocv = None
                else:
                    group.mogp.flags |= MOGPFlags.HasVertexColor
            else:
                group.mocv = None

        if obj.wow_wmo_group.liquid_mesh:
            self.save_liquid(obj.wow_wmo_group.liquid_mesh)
        else:
            group.mliq = None
            group.mogp.flags |= MOGPFlags.IsNotOcean  # check if this is necessary
            group.root.mohd.flags |= 0x4

        group.mogp.liquid_type = int(obj.wow_wmo_group.liquid_type)

        if not has_lights:
            group.molr = None
        else:
            group.mogp.flags |= MOGPFlags.HasLight

        # write second MOTV and MOCV
        if uv2 is None:
            group.motv2 = None

        if obj_blend_map is None:
            group.mocv2 = None



