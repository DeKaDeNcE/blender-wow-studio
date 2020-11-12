import bpy
import gpu

import mathutils

from typing import Union
from bgl import *

from .drawing_elements import ElementTypes
from .utils import render_debug
from .bgl_ext import glCheckError


class DrawingBatch:
    """Abstract base class defining an interface of a drawing batch (drawing element)."""

    c_batch: Union['CM2DrawingBatch', 'CWMODrawingBatch']

    # control
    mesh_type: int = ElementTypes.M2Mesh
    shader: gpu.types.GPUShader
    bl_batch_vert_shader_id: int
    bl_batch_frag_shader_id: int

    # uniform data
    draw_material: Union['M2DrawingMaterial', 'WMODrawingMaterial', None]

    # texture slots

    gl_texture_slots = (
        GL_TEXTURE0,
        GL_TEXTURE1,
        GL_TEXTURE2,
        GL_TEXTURE3
    )

    def __init__(self
                 , c_batch: Union['CM2DrawingBatch', 'CWMODrawingBatch']
                 , draw_obj:  Union['M2DrawingObject', 'WMODrawingObject']
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
        raise NotImplementedError()

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

        for i, gl_slot in enumerate(self.gl_texture_slots):
            bind_code = self.draw_material.get_bindcode(i)

            if bind_code:
                glActiveTexture(gl_slot)
                glBindTexture(GL_TEXTURE_2D, bind_code)

    def determine_valid_shader(self) -> gpu.types.GPUShader:
        raise NotImplementedError()

    def draw(self):

        render_debug('Drawing batch for object \"{}\"'.format(self.draw_obj.bl_obj.name))

        bl_obj = self.draw_obj.bl_obj

        if not bl_obj.visible_get():
            return

        if self.tag_free:
            return

        if self.draw_material:
            self.draw_batch()
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

    def draw_batch(self):
        raise NotImplementedError()

    def free(self):

        if self.tag_free:
            return

        self.tag_free = True
        self.draw_obj.draw_mgr.draw_elements.remove_batch(self)
