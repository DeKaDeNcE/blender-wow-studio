import bpy
import gpu

import mathutils

from typing import Union
from bgl import *

from ...wbs_kernel.wbs_kernel import CWMODrawingBatch
from ...wbs_kernel.wbs_kernel import OpenGLUtils
from .shaders import WMOShaderPermutations, EGxBLend
from .drawing_material import WMODrawingMaterial
from ..drawing_elements import ElementTypes
from ..utils import render_debug
from ..bgl_ext import glCheckError


class WMODrawingBatch:
    c_batch: CWMODrawingBatch

    # control
    mesh_type: int = ElementTypes.WmoMesh
    shader: gpu.types.GPUShader
    bl_batch_vert_shader_id: int
    bl_batch_frag_shader_id: int

    # uniform data
    draw_material: Union[CWMODrawingBatch, None]

    def __init__(self
                 , c_batch: 'CWMODrawingBatch'
                 , draw_obj: 'WMODrawingObject'
                 , context: bpy.types.Context):

        self.c_batch = c_batch
        self.context = context
        self.draw_obj = draw_obj

        self.tag_free = False

        self.mat_id = self.c_batch.get_mat_id()

        try:
            self.draw_material = self.draw_obj.draw_mgr.draw_materials.get(
                self.draw_obj.bl_obj.data.materials[self.mat_id].name)

        except IndexError:
            self.draw_material = None

        self.create_vao()

        self.draw_obj.draw_mgr.draw_elements.add_batch(self)

        render_debug('Instantiated drawing batch for object \"{}\"'.format(draw_obj.bl_obj.name))

    @property
    def is_transparent(self) -> bool:
        return False

    @property
    def priority_plane(self) -> int:
        return 0

    @property
    def layer(self) -> int:
        return 0

    @property
    def is_skybox(self) -> bool:
        return False

    @property
    def bb_center(self) -> mathutils.Vector:
        return mathutils.Vector(self.c_batch.bb_center)

    @property
    def sort_radius(self) -> float:
        return self.c_batch.sort_radius

    @property
    def sort_distance(self):

        perspective_mat = self.draw_obj.draw_mgr.region_3d.perspective_matrix
        bb_center = self.draw_obj.bl_obj.matrix_world @ self.bb_center

        value = (perspective_mat.to_translation() - bb_center).length

        if self.draw_material.is_inverted or self.draw_material.is_transformed:
            result_point = bb_center * (1.0 / value) if value > 0.00000023841858 else bb_center

            sort_dist = perspective_mat.to_translation().length * self.sort_radius

            result_point *= sort_dist

            value = (bb_center - result_point).length \
                if self.draw_material.is_inverted else (bb_center + result_point).length

        return value

    def create_vao(self):
        self.shader = self.determine_valid_shader()
        self.c_batch.set_program(self.shader.program)
        self.c_batch.create_vao()
        glCheckError('Create VAO')

    def ensure_context(self):
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

    def determine_valid_shader(self) -> gpu.types.GPUShader:

        shaders = WMOShaderPermutations()

        if self.draw_material:

            shader_rec = WMOShaderPermutations.get_shader_combo(int(self.draw_material.bl_material.wow_wmo_material.shader))
            self.bl_batch_vert_shader_id = shader_rec.vertex_shader
            self.bl_batch_frag_shader_id = shader_rec.pixel_shader

            return shaders.get_shader_by_id(self.bl_batch_vert_shader_id,
                                            self.bl_batch_frag_shader_id)
        else:
            return shaders.default_shader

    def draw(self):

        render_debug('Drawing batch for object \"{}\"'.format(self.draw_obj.bl_obj.name))

        bl_obj = self.draw_obj.bl_obj

        if not bl_obj.visible_get():
            return

        if self.tag_free:
            return

        if self.draw_material:
            self.draw_wmo_batch()
        else:
            self.draw_fallback()

    def draw_fallback(self):

        glCheckError('drawfallback pre')

        self.shader = self.determine_valid_shader()
        self.shader.bind()
        self.c_batch.set_program(self.shader.program)

        self.shader.uniform_float('uViewProjectionMatrix', self.draw_obj.draw_mgr.region_3d.perspective_matrix)

        self.shader.uniform_float('uPlacementMatrix', self.draw_obj.bl_obj.matrix_world)
        self.shader.uniform_float('uSunDirAndFogStart', self.draw_obj.draw_mgr.sun_dir_and_fog_start)
        self.shader.uniform_float('uSunColorAndFogEnd', self.draw_obj.draw_mgr.sun_color_and_fog_end)
        self.shader.uniform_float('uAmbientLight', self.draw_obj.draw_mgr.ambient_light)
        self.shader.uniform_float('uFogColorAndAlphaTest', (*self.draw_obj.draw_mgr.fog_color, 1.0 / 255.0))
        self.shader.uniform_int('UnFogged_IsAffectedByLight_LightCount', (False, True, 0))

        glEnable(GL_DEPTH_TEST)

        self.c_batch.draw()

        glDisable(GL_DEPTH_TEST)

        gpu.shader.unbind()

        glCheckError('draw fallback post')

    def draw_wmo_batch(self):

        glCheckError('draw')

        #render_debug('Drawing batch for object \"{}\"'.format(self.draw_obj.bl_obj.name))

        color_name = self.draw_material.bl_material.wow_m2_material.color
        transparency_name = self.draw_material.bl_material.wow_m2_material.transparency
        color = self.context.scene.wow_m2_colors[color_name].color if color_name else (1.0, 1.0, 1.0, 1.0)

        if transparency_name:
            transparency_rec = self.context.scene.wow_m2_transparency.get(transparency_name)
            transparency = transparency_rec.value if transparency_rec else 1.0
        else:
            transparency = 1.0

        combined_color = (*color[:3], color[3] * transparency)

        u_alpha_test = 128.0 / 255.0 * combined_color[3] \
            if self.draw_material.blend_mode.index == EGxBLend.AlphaKey.index else 1.0 / 255.0  # Maybe move this to shader logic?

        self._set_active_textures()

        self.shader = self.determine_valid_shader()
        self.shader.bind()
        glCheckError('Pre-link program')
        self.c_batch.set_program(self.shader.program)
        glCheckError('Post-link program')

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
        # OpenGLUtils.glBlendFuncSeparate(self.draw_material.blend_mode.src_color,
        #                                 self.draw_material.blend_mode.dest_color,
        #                                 self.draw_material.blend_mode.src_alpha,
        #                                 self.draw_material.blend_mode.dest_alpha)

        self.shader.uniform_float('uViewProjectionMatrix', self.draw_obj.draw_mgr.region_3d.perspective_matrix)

        self.shader.uniform_float('uPlacementMatrix', self.draw_obj.bl_obj.matrix_world)
        self.shader.uniform_float('uSunDirAndFogStart', self.draw_obj.draw_mgr.sun_dir_and_fog_start)
        self.shader.uniform_float('uSunColorAndFogEnd', self.draw_obj.draw_mgr.sun_color_and_fog_end)
        self.shader.uniform_float('uAmbientLight', self.draw_obj.draw_mgr.ambient_light)
        self.shader.uniform_float('uFogColorAndAlphaTest', (*self.draw_obj.draw_mgr.fog_color, u_alpha_test))
        self.shader.uniform_int('UnFogged_IsAffectedByLight_LightCount', (self.draw_material.is_unfogged,
                                                                          not self.draw_material.is_unlit, 0))

        try:
            self.shader.uniform_int('uTexture', 0)
        except ValueError:
            pass

        try:
            self.shader.uniform_int('uTexture2', 1)
        except ValueError:
            pass

        try:
            self.shader.uniform_int('uTexture3', 2)
        except ValueError:
            pass

        try:
            self.shader.uniform_int('uTexture4', 3)
        except ValueError:
            pass

        self.shader.uniform_float('color_Transparency', combined_color)

        self.c_batch.draw()

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

        glCheckError('draw end')

    def free(self):

        if self.tag_free:
            return

        self.tag_free = True
        self.draw_obj.draw_mgr.draw_elements.remove_batch(self)
