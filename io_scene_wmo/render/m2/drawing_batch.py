import bpy
import gpu
import struct
import numpy as np
import mathutils

from typing import Tuple, List
from bgl import *
from gpu_extras.batch import batch_for_shader

from .shaders import M2ShaderPermutations, M2BlendingModeToEGxBlend, EGxBlendRecord
from ..bgl_ext import glCheckError


class M2DrawingBatch:
    __slots__ = (
        'bl_obj',
        'bl_rig',
        'draw_obj',
        'texture_count',
        'vertices',
        'normals',
        'indices',
        'tex_coords',
        'tex_coords2',
        'bones',
        'bone_weights',
        'bone_influences',
        'batch',
        'batch_shader_id',
        'shader',
        'material',
        'texture',
        'context'
    )

    def __init__(self
                 , obj: bpy.types.Object
                 , draw_obj: 'M2DrawingObject'
                 , context: bpy.types.Context):

        self.context = context
        self.bl_obj = obj
        self.bl_rig = draw_obj.rig
        self.draw_obj = draw_obj

        self.texture_count = 1
        self.bone_influences = 0
        self.batch_shader_id = 0

        self.vertices: np.array
        self.normals: np.array
        self.indices: np.array
        self.tex_coords: np.array
        self.tex_coords2: np.array
        self.bones: np.array
        self.bone_weights: np.array
        self.shader: gpu.types.GPUShader
        self.batch: gpu.types.GPUBatch

        # uniform data
        self.material: bpy.types.Material
        self.texture: bpy.types.Image

        self._update_batch_geometry(self.bl_obj)
        self.shader = self.determine_valid_shader()
        self.batch = self._create_batch()
        self.bind_textures()

    def bind_textures(self, rebind=False):
        self.material = self.bl_obj.data.materials[0]
        self.texture = self.material.wow_m2_material.texture

        bind_code, users = self.draw_obj.drawing_mgr.bound_textures.get(self.texture, (None, None))

        if rebind:

            if bind_code is not None and self.texture:
                self.texture.gl_load()
                bind_code = self.texture.bindcode
                self.draw_obj.drawing_mgr.bound_textures[self.texture] = bind_code, [self, ]
            elif self not in users:

                self.texture.gl_load()
                bind_code = self.texture.bindcode
                users.append(self)
                self.draw_obj.drawing_mgr.bound_textures[self.texture] = bind_code, users

        if bind_code is None and self.texture:
            self.texture.gl_load()
            bind_code = self.texture.bindcode
            self.draw_obj.drawing_mgr.bound_textures[self.texture] = bind_code, [self, ]

        elif self not in users:
            users.append(self)

    def _set_active_textures(self):

        if self.texture.bindcode == 0:
            self.bind_textures(rebind=True)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture.bindcode)

    def free_textures(self):

        bind_code, users = self.draw_obj.drawing_mgr.bound_textures.get(self.texture, (None, None))

        if bind_code:
            if len(users) == 1:
                self.texture.gl_free()
                del self.draw_obj.drawing_mgr.bound_textures[self.texture]
            else:
                users.remove(self)

    def recreate_batch(self):
        self.free_textures()
        self.bind_textures()
        self._update_batch_geometry(self.bl_obj)
        self.shader = self.determine_valid_shader()
        self.batch = self._create_batch()

    def determine_valid_shader(self) -> gpu.types.GPUShader:

        # TODO: update texture count here

        self.batch_shader_id = self.bl_obj.data.materials[0].wow_m2_material.shader

        return M2ShaderPermutations().get_shader_by_m2_id(self.texture_count, self.batch_shader_id,
                                                          self.bone_influences)

    def draw(self):

        color_name = self.texture.wow_m2_texture.color
        transparency_name = self.texture.wow_m2_texture.transparency
        color = self.context.scene.wow_m2_colors[color_name].color if color_name else (1.0, 1.0, 1.0, 1.0)
        transparency = self.context.scene.wow_m2_transparency[transparency_name].value if transparency_name else 1.0
        combined_color = (*color[:3], color[3] * transparency)

        m2_blend_mode = int(self.material.wow_m2_material.blending_mode)
        blend_record = M2BlendingModeToEGxBlend[m2_blend_mode]
        blend_enabled = blend_record.blending_enabled
        depth_write = '16' not in self.material.wow_m2_material.render_flags
        depth_culling = '8' not in self.material.wow_m2_material.render_flags
        backface_culling = '4' not in self.material.wow_m2_material.render_flags
        is_unlit = int('1' in self.material.wow_m2_material.render_flags)
        is_unfogged = int('2' in self.material.wow_m2_material.render_flags)
        u_alpha_test = 128.0 / 255.0 * combined_color[3] \
            if m2_blend_mode == 1 else 1.0 / 255.0  # Maybe move this to shader logic?

        self._set_active_textures()

        self.shader = self.determine_valid_shader()
        self.shader.bind()

        # draw

        if depth_culling:
            glEnable(GL_DEPTH_TEST)

        if depth_write:
            glDepthMask(GL_TRUE)

        if backface_culling:
            glEnable(GL_CULL_FACE)

        if blend_enabled:
            glEnable(GL_BLEND)

        glBlendFunc(blend_record.src_color, blend_record.dest_color)

        tex1_matrix_flattened = [j[i] for i in range(4)
                                 for j in self.bl_obj.wow_m2_geoset.uv_transform.matrix_world] \
                                if self.bl_obj.wow_m2_geoset.uv_transform \
                                else [j[i] for i in range(4) for j in mathutils.Matrix.Identity(4)]

        tex2_matrix_flattened = [j[i] for i in range(4) for j in mathutils.Matrix.Identity(4)]

        self.shader.uniform_float('uViewProjectionMatrix', self.draw_obj.drawing_mgr.region_3d.perspective_matrix)
        self.shader.uniform_float('uPlacementMatrix', self.bl_obj.matrix_local)
        self.shader.uniform_float('uSunDirAndFogStart', self.draw_obj.drawing_mgr.sun_dir_and_fog_start)
        self.shader.uniform_float('uSunColorAndFogEnd', self.draw_obj.drawing_mgr.sun_color_and_fog_end)
        self.shader.uniform_float('uAmbientLight', self.draw_obj.drawing_mgr.ambient_light)
        self.shader.uniform_float('uFogColorAndAlphaTest', (*self.draw_obj.drawing_mgr.fog_color, u_alpha_test))
        self.shader.uniform_int('UnFogged_IsAffectedByLight_LightCount', (is_unfogged, is_unlit, 0))
        self.shader.uniform_int('uTexture', 0)

        self.shader.uniform_float('color_Transparency', combined_color)
        self.shader.uniform_vector_float(self.shader.uniform_from_name('uTextMat'),
                                         struct.pack('16f', *tex1_matrix_flattened)
                                         + struct.pack('16f', *tex2_matrix_flattened), 16, 2)

        if self.bone_influences:
            self.shader.uniform_vector_float(self.shader.uniform_from_name('uBoneMatrices'),
                                             self.draw_obj.bone_matrices, 16, len(self.bl_rig.pose.bones))

        self.batch.draw(self.shader)

        if blend_enabled:
            glDisable(GL_BLEND)

        if backface_culling:
            glDisable(GL_CULL_FACE)

        if depth_write:
            glDepthMask(GL_FALSE)

        if depth_culling:
            glDisable(GL_DEPTH_TEST)

        gpu.shader.unbind()
        glCheckError('draw')

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

        uv_layer1 = mesh.uv_layers.get('UVMap.001') if self.texture_count >= 2 else None

        if uv_layer1:
            for loop in mesh.loops:
                self.tex_coords[loop.vertex_index] = uv_layer.data[loop.index].uv
                self.tex_coords2[loop.vertex_index] = uv_layer1.data[loop.index].uv
        else:
            for loop in mesh.loops:
                self.tex_coords[loop.vertex_index] = uv_layer.data[loop.index].uv

        # handle bone data
        self.bone_influences = 0
        for vertex in mesh.vertices:

            v_bone_influences = 0
            counter = 0
            for group_info in vertex.groups:
                bone_id = self.bl_rig.pose.bones.find(obj.vertex_groups[group_info.group].name)
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

    def _get_valid_attributes(self) -> dict:

        attributes = {
            "aPosition": self.vertices,
            "aNormal": self.normals,
            "aTexCoord": self.tex_coords,
        }

        if self.texture_count >= 2:
            attributes["aTexCoord2"] = self.tex_coords2

        if self.bone_influences:
            attributes["aBones"] = self.bones
            attributes["aBoneWeights"] = self.bone_weights

        return attributes

    def _create_batch(self) -> gpu.types.GPUBatch:
        return batch_for_shader(self.shader, 'TRIS', self._get_valid_attributes(), indices=self.indices)
