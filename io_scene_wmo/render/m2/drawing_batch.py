import bpy
import gpu
import struct
import numpy as np
import mathutils

from typing import Tuple, List
from bgl import *
from gpu_extras.batch import batch_for_shader

from .shaders import M2ShaderPermutations, EGxBLend
from .drawing_material import M2DrawingMaterial
from ..drawing_elements import DrawingElements, ElementTypes
from ..bgl_ext import glCheckError


class M2DrawingBatch:
    __slots__ = (
        'bl_obj_name',
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
        'draw_material',
        'texture',
        'context',
        'sort_radius'
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

    # uniform data
    draw_material: M2DrawingMaterial
    texture: bpy.types.Image

    def __init__(self
                 , obj: bpy.types.Object
                 , draw_obj: 'M2DrawingObject'
                 , context: bpy.types.Context):

        self.context = context
        self.bl_obj_name = obj.name
        self.draw_obj = draw_obj

        self.texture_count = 1
        self.bone_influences = 0
        self.batch_shader_id = 0
        self.sort_radius = 0.0

        # handle materials
        draw_material = self.draw_obj.drawing_mgr.drawing_materials.get(self.bl_obj.active_material.name)

        if draw_material:
            self.draw_material = draw_material
        else:
            self.draw_material = M2DrawingMaterial(self.bl_obj.active_material)
            self.draw_obj.drawing_mgr.drawing_materials[self.bl_obj.active_material.name] = self.draw_material  # TODO: handle 0 materials

        # prepare batch
        self._update_batch_geometry(self.bl_obj)
        self.shader = self.determine_valid_shader()
        self.batch = self._create_batch()
        self.bind_textures()

        DrawingElements().add_batch(self)

    @property
    def bl_obj(self):
        return bpy.data.objects[self.bl_obj_name]

    @property
    def is_transparent(self):
        return (self.draw_material.blend_mode > EGxBLend.AlphaKey) or not self.draw_material.depth_write

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
        return self.draw_obj.drawing_mgr.m2_objects.index(self.draw_obj)

    @property
    def bb_center(self):
        return 0.125 * sum((mathutils.Vector(b) for b in self.bl_obj.bound_box), mathutils.Vector())

    @property
    def sort_distance(self):

        bb_center = self.draw_obj.drawing_mgr.region_3d.perspective_matrix @ self.bb_center

        value = bb_center.length

        if self.draw_material.is_inverted and self.draw_material.is_transformed:
            result_point = bb_center * (1.0 / value) if value > 0.00000023841858 else bb_center

            sort_dist = self.draw_obj.drawing_mgr.region_3d.perspective_matrix.to_translation().length \
                        * self.sort_radius

            result_point *= sort_dist

            value = (bb_center - result_point).length \
                if self.draw_material.is_inverted else (bb_center + result_point).length

        return value

    def bind_textures(self, rebind=False):

        self.texture = self.draw_material.bl_material.wow_m2_material.texture  # TODO: proper updates

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

        u_alpha_test = 128.0 / 255.0 * combined_color[3] \
            if self.draw_material.blend_mode.index == EGxBLend.AlphaKey.index else 1.0 / 255.0  # Maybe move this to shader logic?

        self._set_active_textures()

        self.shader = self.determine_valid_shader()
        self.shader.bind()

        # draw

        if self.draw_material.depth_culling:
            glEnable(GL_DEPTH_TEST)

        if self.draw_material.depth_write:
            glDepthMask(GL_TRUE)

        if self.draw_material.backface_culling:
            glEnable(GL_CULL_FACE)

        if self.draw_material.blend_mode.blending_enabled:
            glEnable(GL_BLEND)

        glBlendFunc(self.draw_material.blend_mode.src_color, self.draw_material.blend_mode.dest_color)

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
        self.shader.uniform_int('UnFogged_IsAffectedByLight_LightCount', (self.draw_material.is_unfogged,
                                                                          self.draw_material.is_unlit, 0))
        self.shader.uniform_int('uTexture', 0)

        self.shader.uniform_float('color_Transparency', combined_color)
        self.shader.uniform_vector_float(self.shader.uniform_from_name('uTextMat'),
                                         struct.pack('16f', *tex1_matrix_flattened)
                                         + struct.pack('16f', *tex2_matrix_flattened), 16, 2)

        if self.bone_influences:
            self.shader.uniform_vector_float(self.shader.uniform_from_name('uBoneMatrices'),
                                             self.draw_obj.bone_matrices, 16, len(self.draw_obj.bl_rig.pose.bones))

        self.batch.draw(self.shader)

        if self.draw_material.blend_mode.blending_enabled:
            glDisable(GL_BLEND)

        if self.draw_material.backface_culling:
            glDisable(GL_CULL_FACE)

        if self.draw_material.depth_write:
            glDepthMask(GL_FALSE)

        if self.draw_material.depth_culling:
            glDisable(GL_DEPTH_TEST)

        gpu.shader.unbind()
        #glCheckError('draw')

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
        bb_center = self.bb_center
        self.bone_influences = 0
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
