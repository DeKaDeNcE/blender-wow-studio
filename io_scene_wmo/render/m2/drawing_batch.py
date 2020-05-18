import bpy
import sys
import bmesh
import inspect
import gpu
import struct
import numpy as np
import mathutils

from typing import Tuple, List, Set
from bgl import *
from gpu_extras.batch import batch_for_shader

from .shaders import M2ShaderPermutations, EGxBLend
from .drawing_material import M2DrawingMaterial
from ..drawing_elements import ElementTypes
from ..utils import render_debug
from ..bgl_ext import glCheckError


class M2DrawingBatch:
    __slots__ = (
        'bl_obj_name',
        'bl_mesh_name',
        'draw_obj',
        'vertices',
        'normals',
        'indices',
        'tex_coords',
        'tex_coords2',
        'bones',
        'bone_weights',
        'bone_influences',
        'batch',
        'shader',
        'draw_material',
        'texture_1',
        'texture_2',
        'texture_3',
        'texture_4',
        'context',
        'sort_radius',
        'bl_batch_vert_shader_id',
        'bl_batch_frag_shader_id',
        'tag_free'
    )

    # vertex attributes
    vertices: np.array
    normals: np.array
    indices: np.array
    tex_coords: np.array
    tex_coords2: np.array
    bones: np.array
    bone_weights: np.array

    # control
    mesh_type: int = ElementTypes.M2Mesh
    shader: gpu.types.GPUShader
    batch: gpu.types.GPUBatch
    bl_batch_vert_shader_id: int
    bl_batch_frag_shader_id: int

    # uniform data
    draw_material: M2DrawingMaterial

    def __init__(self
                 , obj: bpy.types.Object
                 , draw_obj: 'M2DrawingObject'
                 , context: bpy.types.Context):

        self.context = context
        self.bl_obj_name = obj.name
        self.bl_mesh_name = obj.data.name
        self.draw_obj = draw_obj

        self.bone_influences = 0
        self.sort_radius = 0.0
        self.tag_free = False

        # handle materials
        draw_material, users = self.draw_obj.drawing_mgr.drawing_materials.get(self.bl_obj.active_material.name,
                                                                               (None, None))

        if draw_material:
            self.draw_material = draw_material
            users.append(self)
        else:
            # TODO: default material

            self.draw_material = M2DrawingMaterial(self.bl_obj.active_material, self.draw_obj.drawing_mgr)
            self.draw_obj.drawing_mgr.drawing_materials[self.bl_obj.active_material.name] = self.draw_material, [self, ]

        # prepare batch
        batch, users = self.draw_obj.drawing_mgr.batch_cache.get(self.bl_mesh_name, (None, None))

        if batch:
            other_draw_batch = users[-1]
            self.batch = batch
            self.bone_influences = other_draw_batch.bone_influences
            self.sort_radius = other_draw_batch.sort_radius
            self.shader = other_draw_batch.shader
            users.append(self)
        else:
            self._update_batch_geometry(self.bl_obj)
            self.shader = self.determine_valid_shader()
            self.batch = self._create_batch()
            self.draw_obj.drawing_mgr.batch_cache[self.bl_mesh_name] = batch, [self, ]
            self._free_batch_geometry()

        self.draw_obj.drawing_mgr.drawing_elements.add_batch(self)

        render_debug('Instantiated drawing batch for object \"{}\" and mesh \"{}\"'.format(self.bl_obj_name,
                                                                                           self.bl_mesh_name))

    @property
    def bl_obj(self):
        try:
            return bpy.data.objects[self.bl_obj_name]
        except KeyError:
            self.free()

    @property
    def is_transparent(self):
        return (self.draw_material.blend_mode.index > EGxBLend.AlphaKey.index) \
               or not self.draw_material.depth_write

    @property
    def priority_plane(self):
        return self.draw_material.bl_material.wow_m2_material.priority_plane

    @property
    def layer(self):
        return self.draw_material.bl_material.wow_m2_material.layer

    @property
    def is_skybox(self):
        return self.draw_obj.is_skybox

    @property
    def m2_draw_obj_idx(self):
        return list(self.draw_obj.drawing_mgr.m2_objects.keys()).index(self.draw_obj.bl_rig_name)

    @property
    def bb_center(self):
        return 0.125 * sum((mathutils.Vector(b) for b in self.bl_obj.bound_box), mathutils.Vector())

    @property
    def sort_distance(self):

        perspective_mat = self.draw_obj.drawing_mgr.region_3d.perspective_matrix
        bb_center = self.bl_obj.matrix_world @ self.bb_center

        value = (perspective_mat.to_translation() - bb_center).length

        if self.draw_material.is_inverted or self.draw_material.is_transformed:
            result_point = bb_center * (1.0 / value) if value > 0.00000023841858 else bb_center

            sort_dist = perspective_mat.to_translation().length * self.sort_radius

            result_point *= sort_dist

            value = (bb_center - result_point).length \
                if self.draw_material.is_inverted else (bb_center + result_point).length

        return value

    def ensure_context(self):
        obj_test = self.bl_obj
        mat_test = self.draw_material.bl_material

        if not mat_test:
            self.tag_free = True

        return self.tag_free

    def _set_active_textures(self):

        gl_texture_slots = (
            GL_TEXTURE0,
            GL_TEXTURE1,
            GL_TEXTURE2,
            GL_TEXTURE3
        )

        for i, gl_slot in enumerate(gl_texture_slots):
            bind_code = self.draw_material.get_bindcode(i)

            if bind_code:
                glActiveTexture(gl_slot)
                glBindTexture(GL_TEXTURE_2D, bind_code)

    def recreate_batch(self):
        self.free_textures()
        self.bind_textures()
        self._update_batch_geometry(self.bl_obj)
        self.shader = self.determine_valid_shader()
        self.batch = self._create_batch()

    def determine_valid_shader(self) -> gpu.types.GPUShader:

        self.bl_batch_vert_shader_id = int(self.draw_material.bl_material.wow_m2_material.vertex_shader)
        self.bl_batch_frag_shader_id = int(self.draw_material.bl_material.wow_m2_material.fragment_shader)

        return M2ShaderPermutations().get_shader_by_id(self.bl_batch_vert_shader_id,
                                                       self.bl_batch_frag_shader_id,
                                                       self.bone_influences)

    def draw(self):

        if self.tag_free:
            return

        color_name = self.draw_material.bl_material.wow_m2_material.color
        transparency_name = self.draw_material.bl_material.wow_m2_material.transparency
        color = self.context.scene.wow_m2_colors[color_name].color if color_name else (1.0, 1.0, 1.0, 1.0)
        transparency = self.context.scene.wow_m2_transparency[transparency_name].value if transparency_name else 1.0
        combined_color = (*color[:3], color[3] * transparency)

        u_alpha_test = 128.0 / 255.0 * combined_color[3] \
            if self.draw_material.blend_mode.index == EGxBLend.AlphaKey.index else 1.0 / 255.0  # Maybe move this to shader logic?

        self._set_active_textures()

        self.shader = self.determine_valid_shader()
        self.shader.bind()

        # draw

        if self.draw_material.depth_culling:
            glEnable(GL_DEPTH_TEST)

        glDepthMask(GL_TRUE if self.draw_material.depth_write else GL_FALSE)

        if self.draw_material.backface_culling:
            glEnable(GL_CULL_FACE)

        if self.draw_material.blend_mode.blending_enabled:
            glEnable(GL_BLEND)

        if self.is_skybox:
            glDepthRange(0.998, 1.0)

        glBlendFunc(self.draw_material.blend_mode.src_color, self.draw_material.blend_mode.dest_color)

        tex1_matrix_flattened = [j[i] for i in range(4)
                                 for j in self.bl_obj.wow_m2_geoset.uv_transform_1.matrix_world] \
                                if self.bl_obj.wow_m2_geoset.uv_transform_1 \
                                else [j[i] for i in range(4) for j in mathutils.Matrix.Identity(4)]

        tex2_matrix_flattened = [j[i] for i in range(4)
                                 for j in self.bl_obj.wow_m2_geoset.uv_transform_2.matrix_world] \
                                if self.bl_obj.wow_m2_geoset.uv_transform_2 \
                                else [j[i] for i in range(4) for j in mathutils.Matrix.Identity(4)]

        self.shader.uniform_float('uViewProjectionMatrix', self.draw_obj.drawing_mgr.region_3d.perspective_matrix)

        self.shader.uniform_float('uPlacementMatrix',
                                  self.draw_obj.bl_rig.matrix_world if self.draw_obj.has_bones
                                                                    else mathutils.Matrix.Identity(4))

        self.shader.uniform_float('uPlacementMatrixLocal', self.bl_obj.matrix_world)
        self.shader.uniform_float('uSunDirAndFogStart', self.draw_obj.drawing_mgr.sun_dir_and_fog_start)
        self.shader.uniform_float('uSunColorAndFogEnd', self.draw_obj.drawing_mgr.sun_color_and_fog_end)
        self.shader.uniform_float('uAmbientLight', self.draw_obj.drawing_mgr.ambient_light)
        self.shader.uniform_float('uFogColorAndAlphaTest', (*self.draw_obj.drawing_mgr.fog_color, u_alpha_test))
        self.shader.uniform_int('UnFogged_IsAffectedByLight_LightCount', (self.draw_material.is_unfogged,
                                                                          self.draw_material.is_unlit, 0))
        self.shader.uniform_int('uTexture', 0)
        self.shader.uniform_int('uTexture2', 1)
        self.shader.uniform_int('uTexture3', 2)
        self.shader.uniform_int('uTexture4', 3)

        self.shader.uniform_float('color_Transparency', combined_color)
        self.shader.uniform_vector_float(self.shader.uniform_from_name('uTextMat'),
                                         struct.pack('16f', *tex1_matrix_flattened)
                                         + struct.pack('16f', *tex2_matrix_flattened), 16, 2)

        if self.bone_influences:
            self.shader.uniform_vector_float(self.shader.uniform_from_name('uBoneMatrices'),
                                             self.draw_obj.bone_matrices, 16, len(self.draw_obj.bl_rig.pose.bones))

        self.batch.draw(self.shader)

        if self.is_skybox:
            glDepthRange(0, 0.996)

        if self.draw_material.blend_mode.blending_enabled:
            glDisable(GL_BLEND)

        if self.draw_material.backface_culling:
            glDisable(GL_CULL_FACE)

        glDepthMask(GL_FALSE if self.draw_material.depth_write else GL_TRUE)

        if self.draw_material.depth_culling:
            glDisable(GL_DEPTH_TEST)

        gpu.shader.unbind()
        #glCheckError('draw')

    def _update_batch_geometry_editable(self, obj: bpy.types.Object):
        mesh = obj.data

        # create bmesh
        bm = bmesh.new()
        bm.from_mesh(obj.data)

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

        # handle texture coordinates
        uv = bm.loops.layers.uv.get('UVMap')

        if not uv:
            raise Exception('Error: no UV Layer named "UVMap" is found. Failed rendering model.')

        uv2 = bm.loops.layers.uv.get('UVMap.001') if self.draw_material.texture_count >= 2 else None

        faces_set = set(faces)
        batches = {}

        len_vertex_array = 0
        while faces_set:
            face = next(iter(faces_set))

            linked_faces, vertex_index_set = self.get_linked_faces(face, uv, uv2)
            len_vertex_array += len(vertex_index_set)

            batches.setdefault(face.material_index, []).append(linked_faces)
            faces_set -= set(linked_faces)

        # create vertex attribute arrays
        self.normals = np.empty((len_vertex_array, 3), 'f')
        self.vertices = np.empty((len_vertex_array, 3), 'f')
        self.indices = np.empty((len(faces), 3), 'i')
        self.tex_coords = np.empty((len_vertex_array, 2), 'f')
        self.tex_coords2 = np.zeros((len_vertex_array, 2), 'f')
        self.bones = np.zeros((len_vertex_array, 4), 'f')
        self.bone_weights = np.zeros((len_vertex_array, 4), 'f')

        bb_center = self.bb_center
        vert_base_index = 0
        face_base_index = 0
        for mat_index, batch_groups in batches.items():

            for batch_group in batch_groups:
                vertex_map = {}
                vertex_index_counter = 0

                for i, face in enumerate(batch_group):
                    face_indices = [0, 0, 0]

                    for j, vertex in enumerate(face.verts):

                        # vertex attributes
                        local_v_index = vertex_map.get(vertex.index)

                        if local_v_index is None:
                            vertex_map[vertex.index] = vertex_index_counter
                            local_v_index = vertex_index_counter
                            vertex_index_counter += 1

                        global_v_index = vert_base_index + local_v_index
                        self.vertices[global_v_index] = vertex.co.to_tuple()
                        self.normals[global_v_index] = vertex.normal.to_tuple()
                        self.tex_coords[global_v_index] = face.loops[j][uv].uv

                        if uv2:
                            self.tex_coords2[global_v_index] = face.loops[j][uv2].uv

                        # bones
                        self.bone_influences = 0
                        if self.draw_obj.has_bones:

                            mesh_vertex = mesh.vertices[vertex.index]

                            v_bone_influences = 0
                            counter = 0
                            for group_info in mesh_vertex.groups:
                                bone_id = self.draw_obj.bl_rig.pose.bones.find(
                                    obj.vertex_groups[group_info.group].name)
                                weight = group_info.weight

                                if bone_id < 0 or not weight:
                                    continue

                                v_bone_influences += 1

                                self.bones[global_v_index][counter] = bone_id
                                self.bone_weights[global_v_index][counter] = weight

                                counter += 1

                            assert counter < 5

                            if not counter:
                                self.bone_weights[global_v_index][0] = 1.0

                            self.bone_influences = max(self.bone_influences, v_bone_influences)

                        # calc sort radius
                        self.sort_radius = max(self.sort_radius, (vertex.co - bb_center).length)

                        # save face indices
                        face_indices[j] = global_v_index

                    self.indices[face_base_index + i] = face_indices

                face_base_index += len(batch_group)
                vert_base_index += vertex_index_counter

    def _update_batch_geometry(self, obj: bpy.types.Object):
        mesh = obj.data
        mesh.calc_loop_triangles()

        # create vertex attribute arrays
        self.normals = np.empty((len(mesh.vertices), 3), 'f')
        self.vertices = np.empty((len(mesh.vertices), 3), 'f')
        self.indices = np.empty((len(mesh.loop_triangles), 3), 'i')
        self.tex_coords = np.empty((len(mesh.vertices), 2), 'f')
        self.tex_coords2 = np.zeros((len(mesh.vertices), 2), 'f')
        self.bones = np.zeros((len(mesh.vertices), 4), 'f')
        self.bone_weights = np.zeros((len(mesh.vertices), 4), 'f')

        # handle geometry
        mesh.vertices.foreach_get("normal", np.reshape(self.normals, len(mesh.vertices) * 3))
        mesh.vertices.foreach_get("co", np.reshape(self.vertices, len(mesh.vertices) * 3))
        mesh.loop_triangles.foreach_get("vertices", np.reshape(self.indices, len(mesh.loop_triangles) * 3))

        # handle texture coordinates
        uv_layer = mesh.uv_layers.get('UVMap')

        if not uv_layer:
            raise Exception('Error: no UV Layer named "UVMap" is found. Failed rendering model.')

        uv_layer1 = mesh.uv_layers.get('UVMap.001') if self.draw_material.texture_count >= 2 else None

        if uv_layer1:
            for loop in mesh.loops:
                self.tex_coords[loop.vertex_index] = uv_layer.data[loop.index].uv
                self.tex_coords2[loop.vertex_index] = uv_layer1.data[loop.index].uv
        else:
            for loop in mesh.loops:
                self.tex_coords[loop.vertex_index] = uv_layer.data[loop.index].uv

        # handle bone data
        bb_center = self.bb_center

        self.bone_influences = 0

        if self.draw_obj.has_bones:
            for vertex in mesh.vertices:

                v_bone_influences = 0
                counter = 0
                for group_info in vertex.groups:
                    bone_id = self.draw_obj.bl_rig.pose.bones.find(obj.vertex_groups[group_info.group].name)
                    weight = group_info.weight

                    if bone_id < 0 or not weight:
                        continue

                    v_bone_influences += 1

                    self.bones[vertex.index][counter] = bone_id
                    self.bone_weights[vertex.index][counter] = weight

                    counter += 1

                assert counter < 5

                if not counter:
                    self.bone_weights[vertex.index][0] = 1.0

                self.bone_influences = max(self.bone_influences, v_bone_influences)

            # calc sort radius
            self.sort_radius = max(self.sort_radius, (vertex.co - bb_center).length)

    @staticmethod
    def get_linked_faces(b_face
                         , uv
                         , uv2
                         , stack=len(inspect.stack())
                         , vert_index_set=set()) -> Tuple[List[bmesh.types.BMFace], Set[int]]:
        # check if face was already processed
        if b_face.tag:
            return [], vert_index_set

        f_linked = [b_face]
        mat_idx = b_face.material_index
        b_face.tag = True

        # store vertex indices used by that face
        for vert in b_face.verts:
            vert_index_set.add(vert.index)

        # Select edges that link two faces
        for link_edge in b_face.edges:
            # check if edge is shared with another face
            if not len(link_edge.link_faces) == 2:
                continue

            # prevent recursion stack overflow
            if stack >= sys.getrecursionlimit() - 1:
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

                # call this function recursively on this face if all checks are passed
                linked, vert_index_set = M2DrawingBatch.get_linked_faces(link_face, uv, uv2,
                                                                         stack=stack + 1, vert_index_set=vert_index_set)
                f_linked.extend(linked)

        return f_linked, vert_index_set

    def _get_valid_attributes(self) -> dict:

        attributes = {
            "aPosition": self.vertices,
            "aNormal": self.normals,
            "aTexCoord": self.tex_coords,
        }

        if self.draw_material.texture_count >= 2 \
                and self.bl_batch_vert_shader_id in {2, 10, 11, 12, 14, 15, 16}:
            attributes["aTexCoord2"] = self.tex_coords2

        if self.bone_influences:
            attributes["aBones"] = self.bones
            attributes["aBoneWeights"] = self.bone_weights

        return attributes

    def _create_batch(self) -> gpu.types.GPUBatch:
        return batch_for_shader(self.shader, 'TRIS', self._get_valid_attributes(), indices=self.indices)

    def _free_batch_geometry(self):
        self.vertices = None
        self.normals = None
        self.tex_coords = None
        self.tex_coords2 = None
        self.bones = None
        self.bone_weights = None

    def free(self):
        if self.tag_free:
            return

        self.tag_free = True

        batch, users = self.draw_obj.drawing_mgr.batch_cache.get(self.bl_mesh_name)

        if len(users) == 1:
            del self.draw_obj.drawing_mgr.batch_cache[self.bl_mesh_name]
        else:
            users.remove(self)

        draw_mat, users = self.draw_obj.drawing_mgr.drawing_materials.get(self.draw_material.bl_material_name)

        if len(users) == 1:
            del self.draw_obj.drawing_mgr.drawing_materials[self.draw_material.bl_material_name]
        else:
            users.remove(self)

        del self.draw_obj.batches[self.bl_obj_name]
        self.draw_obj.drawing_mgr.drawing_elements.remove_batch(self)

        render_debug('Freed drawing batch for object \"{}\" and mesh \"{}\"'.format(self.bl_obj_name,
                                                                                    self.bl_mesh_name))
