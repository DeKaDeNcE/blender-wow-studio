import os
import gpu
import bpy
import traceback
import mathutils
import struct
import numpy as np
from math import radians
from mathutils import Matrix, Vector

from tqdm import tqdm
from enum import IntEnum
from ctypes import c_uint, c_uint8
from typing import List, Dict, Tuple
from ..utils.misc import singleton, Sequence

from bgl import *
from gpu_extras.batch import batch_for_shader

from collections import namedtuple


class M2PixelShader(IntEnum):
    # Wotlk deprecated shaders
    Combiners_Decal = -1
    Combiners_Add = -2
    Combiners_Mod2x = -3
    Combiners_Fade = -4,
    Combiners_Opaque_Add = -5
    Combiners_Opaque_AddNA = -6
    Combiners_Add_Mod = -7
    Combiners_Mod2x_Mod2x = -8

    # Legion modern shaders
    Combiners_Opaque = 0
    Combiners_Mod = 1
    Combiners_Opaque_Mod = 2
    Combiners_Opaque_Mod2x = 3
    Combiners_Opaque_Mod2xNA = 4
    Combiners_Opaque_Opaque = 5
    Combiners_Mod_Mod = 6
    Combiners_Mod_Mod2x = 7
    Combiners_Mod_Add = 8
    Combiners_Mod_Mod2xNA = 9
    Combiners_Mod_AddNA = 10
    Combiners_Mod_Opaque = 11
    Combiners_Opaque_Mod2xNA_Alpha = 12
    Combiners_Opaque_AddAlpha = 13
    Combiners_Opaque_AddAlpha_Alpha = 14
    Combiners_Opaque_Mod2xNA_Alpha_Add = 15
    Combiners_Mod_AddAlpha = 16
    Combiners_Mod_AddAlpha_Alpha = 17
    Combiners_Opaque_Alpha_Alpha = 18
    Combiners_Opaque_Mod2xNA_Alpha_3s = 19
    Combiners_Opaque_AddAlpha_Wgt = 20
    Combiners_Mod_Add_Alpha = 21
    Combiners_Opaque_ModNA_Alpha = 22
    Combiners_Mod_AddAlpha_Wgt = 23
    Combiners_Opaque_Mod_Add_Wgt = 24
    Combiners_Opaque_Mod2xNA_Alpha_UnshAlpha = 25
    Combiners_Mod_Dual_Crossfade = 26
    Combiners_Opaque_Mod2xNA_Alpha_Alpha = 27
    Combiners_Mod_Masked_Dual_Crossfade = 28
    Combiners_Opaque_Alpha = 29
    Guild = 30
    Guild_NoBorder = 31
    Guild_Opaque = 32
    Combiners_Mod_Depth = 33
    Illum = 34
    Combiners_Mod_Mod_Mod_Const = 35


class M2VertexShader(IntEnum):
    Diffuse_T1 = 0
    Diffuse_Env = 1
    Diffuse_T1_T2 = 2
    Diffuse_T1_Env = 3
    Diffuse_Env_T1 = 4
    Diffuse_Env_Env = 5
    Diffuse_T1_Env_T1 = 6
    Diffuse_T1_T1 = 7
    Diffuse_T1_T1_T1 = 8
    Diffuse_EdgeFade_T1 = 9
    Diffuse_T2 = 10
    Diffuse_T1_Env_T2 = 11
    Diffuse_EdgeFade_T1_T2 = 12
    Diffuse_EdgeFade_Env = 13
    Diffuse_T1_T2_T1 = 14
    Diffuse_T1_T2_T3 = 15
    Color_T1_T2_T3 = 16
    BW_Diffuse_T1 = 17
    BW_Diffuse_T1_T2 = 18


EGxBlendRecord = namedtuple('EGxBlendRecord',
                            ['blending_enabled', 'src_color', 'dest_color', 'src_alpha', 'dest_alpha'])


class EGxBLend(metaclass=Sequence):
    Opaque = EGxBlendRecord(False, GL_ONE, GL_ZERO, GL_ONE, GL_ZERO)
    AlphaKey = EGxBlendRecord(False, GL_ONE, GL_ZERO, GL_ONE, GL_ZERO)
    Alpha = EGxBlendRecord(True, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ONE_MINUS_SRC_ALPHA)
    Add = EGxBlendRecord(True, GL_SRC_ALPHA, GL_ONE, GL_ZERO, GL_ONE)
    Mod = EGxBlendRecord(True, GL_DST_COLOR, GL_ZERO, GL_DST_ALPHA, GL_ZERO)
    Mod2x = EGxBlendRecord(True, GL_DST_COLOR, GL_SRC_COLOR, GL_DST_ALPHA, GL_SRC_ALPHA)
    ModAdd = EGxBlendRecord(True, GL_DST_COLOR, GL_ONE, GL_DST_ALPHA, GL_ONE)
    InvSrcAlphaAdd = EGxBlendRecord(True, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ONE_MINUS_SRC_ALPHA, GL_ONE)
    InvSrcAlphaOpaque = EGxBlendRecord(True, GL_ONE_MINUS_SRC_ALPHA, GL_ZERO, GL_ONE_MINUS_SRC_ALPHA, GL_ZERO)
    SrcAlphaOpaque = EGxBlendRecord(True, GL_SRC_ALPHA, GL_ZERO, GL_SRC_ALPHA, GL_ZERO)
    NoAlphaAdd = EGxBlendRecord(True, GL_ONE, GL_ONE, GL_ZERO, GL_ONE)
    ConstantAlpha = EGxBlendRecord(True, GL_CONSTANT_ALPHA, GL_ONE_MINUS_CONSTANT_ALPHA, GL_CONSTANT_ALPHA,
                                   GL_ONE_MINUS_CONSTANT_ALPHA)
    Screen = EGxBlendRecord(True, GL_ONE_MINUS_DST_COLOR, GL_ONE, GL_ONE, GL_ZERO)
    BlendAdd = EGxBlendRecord(True, GL_ONE, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ONE_MINUS_SRC_ALPHA)


class M2BlendingModeToEGxBlend(metaclass=Sequence):

    Blend_Opaque = EGxBLend.Opaque
    Blend_AlphaKey = EGxBLend.AlphaKey
    Blend_Alpha = EGxBLend.Alpha
    Blend_NoAlphaAdd = EGxBLend.NoAlphaAdd
    Blend_Add = EGxBLend.Add
    Blend_Mod = EGxBLend.Mod
    Blend_Mod2x = EGxBLend.Mod2x
    Blend_BlendAdd = EGxBLend.BlendAdd


M2ShaderTableRecord = namedtuple('M2ShaderTableRecord',['pixel_shader', 'vertex_shader'])


class M2ShaderTable(metaclass=Sequence):
    Combiners_Opaque_Mod2xNA_Alpha_Diffuse_T1_Env = M2ShaderTableRecord(
        M2PixelShader.Combiners_Opaque_Mod2xNA_Alpha,           M2VertexShader.Diffuse_T1_Env)

    Combiners_Opaque_AddAlpha_Diffuse_T1_Env = M2ShaderTableRecord(
        M2PixelShader.Combiners_Opaque_AddAlpha,                M2VertexShader.Diffuse_T1_Env)

    Combiners_Opaque_AddAlpha_Alpha_Diffuse_T1_Env = M2ShaderTableRecord(
        M2PixelShader.Combiners_Opaque_AddAlpha_Alpha,          M2VertexShader.Diffuse_T1_Env)

    Combiners_Opaque_Mod2xNA_Alpha_Add_Diffuse_T1_Env_T1 = M2ShaderTableRecord(
        M2PixelShader.Combiners_Opaque_Mod2xNA_Alpha_Add,       M2VertexShader.Diffuse_T1_Env_T1)

    Combiners_Mod_AddAlpha_Diffuse_T1_Env = M2ShaderTableRecord(
        M2PixelShader.Combiners_Mod_AddAlpha,                   M2VertexShader.Diffuse_T1_Env)

    Combiners_Opaque_AddAlpha_Diffuse_T1_T1 = M2ShaderTableRecord(
        M2PixelShader.Combiners_Opaque_AddAlpha,                M2VertexShader.Diffuse_T1_T1)

    Combiners_Mod_AddAlpha_Diffuse_T1_T1 = M2ShaderTableRecord(
        M2PixelShader.Combiners_Mod_AddAlpha,                   M2VertexShader.Diffuse_T1_T1)

    Combiners_Mod_AddAlpha_Alpha_Diffuse_T1_Env = M2ShaderTableRecord(
        M2PixelShader.Combiners_Mod_AddAlpha_Alpha,             M2VertexShader.Diffuse_T1_Env)

    Combiners_Opaque_Alpha_Alpha_Diffuse_T1_Env = M2ShaderTableRecord(
        M2PixelShader.Combiners_Opaque_Alpha_Alpha,             M2VertexShader.Diffuse_T1_Env)

    Combiners_Opaque_Mod2xNA_Alpha_3s_Diffuse_T1_Env_T1 = M2ShaderTableRecord(
        M2PixelShader.Combiners_Opaque_Mod2xNA_Alpha_3s,        M2VertexShader.Diffuse_T1_Env_T1)

    Combiners_Opaque_AddAlpha_Wgt_Diffuse_T1_T1 = M2ShaderTableRecord(
        M2PixelShader.Combiners_Opaque_AddAlpha_Wgt,            M2VertexShader.Diffuse_T1_T1)

    Combiners_Mod_Add_Alpha_Diffuse_T1_Env = M2ShaderTableRecord(
        M2PixelShader.Combiners_Mod_Add_Alpha,                  M2VertexShader.Diffuse_T1_Env)

    Combiners_Opaque_ModNA_Alpha_Diffuse_T1_Env = M2ShaderTableRecord(
        M2PixelShader.Combiners_Opaque_ModNA_Alpha,             M2VertexShader.Diffuse_T1_Env)

    Combiners_Mod_AddAlpha_Wgt_Diffuse_T1_Env = M2ShaderTableRecord(
        M2PixelShader.Combiners_Mod_AddAlpha_Wgt,               M2VertexShader.Diffuse_T1_Env)

    Combiners_Mod_AddAlpha_Wgt_Diffuse_T1_T1 = M2ShaderTableRecord(
        M2PixelShader.Combiners_Mod_AddAlpha_Wgt,               M2VertexShader.Diffuse_T1_T1)

    Combiners_Opaque_AddAlpha_Wgt_Diffuse_T1_T2 = M2ShaderTableRecord(
        M2PixelShader.Combiners_Opaque_AddAlpha_Wgt,            M2VertexShader.Diffuse_T1_T2)

    Combiners_Opaque_Mod_Add_Wgt_Diffuse_T1_Env = M2ShaderTableRecord(
        M2PixelShader.Combiners_Opaque_Mod_Add_Wgt,             M2VertexShader.Diffuse_T1_Env)

    Combiners_Opaque_Mod2xNA_Alpha_UnshAlpha1 = M2ShaderTableRecord(
        M2PixelShader.Combiners_Opaque_Mod2xNA_Alpha_UnshAlpha, M2VertexShader.Diffuse_T1_Env_T1)

    Combiners_Mod_Dual_Crossfade_Diffuse_T1 = M2ShaderTableRecord(
        M2PixelShader.Combiners_Mod_Dual_Crossfade,             M2VertexShader.Diffuse_T1)

    Combiners_Mod_Depth_Diffuse_EdgeFade_T1 = M2ShaderTableRecord(
        M2PixelShader.Combiners_Mod_Depth,                      M2VertexShader.Diffuse_EdgeFade_T1)

    Combiners_Opaque_Mod2xNA_Alpha_Alpha_Diffuse_T1_Env_T2 = M2ShaderTableRecord(
        M2PixelShader.Combiners_Opaque_Mod2xNA_Alpha_Alpha,     M2VertexShader.Diffuse_T1_Env_T2)

    Combiners_Mod_Mod_Diffuse_EdgeFade_T1_T2 = M2ShaderTableRecord(M2PixelShader.Combiners_Mod_Mod,                        M2VertexShader.Diffuse_EdgeFade_T1_T2)

    Combiners_Mod_Masked_Dual_Crossfade_Diffuse_T1_T2 = M2ShaderTableRecord(
        M2PixelShader.Combiners_Mod_Masked_Dual_Crossfade,      M2VertexShader.Diffuse_T1_T2)

    Combiners_Opaque_Alpha_Diffuse_T1_T1 = M2ShaderTableRecord(
        M2PixelShader.Combiners_Opaque_Alpha,                   M2VertexShader.Diffuse_T1_T1)

    Combiners_Opaque_Mod2xNA_Alpha_UnshAlpha2 = M2ShaderTableRecord(
        M2PixelShader.Combiners_Opaque_Mod2xNA_Alpha_UnshAlpha, M2VertexShader.Diffuse_T1_Env_T2)

    Combiners_Mod_Depth_Diffuse_EdgeFade_Env = M2ShaderTableRecord(
        M2PixelShader.Combiners_Mod_Depth,                      M2VertexShader.Diffuse_EdgeFade_Env)

    Guild_Diffuse_T1_T2_T1 = M2ShaderTableRecord(
        M2PixelShader.Guild,                                    M2VertexShader.Diffuse_T1_T2_T1)

    Guild_NoBorder_Diffuse_T1_T2 = M2ShaderTableRecord(
        M2PixelShader.Guild_NoBorder,                           M2VertexShader.Diffuse_T1_T2)

    Guild_Opaque_Diffuse_T1_T2_T1 = M2ShaderTableRecord(
        M2PixelShader.Guild_Opaque,                             M2VertexShader.Diffuse_T1_T2_T1)

    Illum_Diffuse_T1_T1 = M2ShaderTableRecord(
        M2PixelShader.Illum,                                    M2VertexShader.Diffuse_T1_T1)

    Combiners_Mod_Mod_Mod_Const_Diffuse_T1_T2_T3 = M2ShaderTableRecord(
        M2PixelShader.Combiners_Mod_Mod_Mod_Const,              M2VertexShader.Diffuse_T1_T2_T3)

    Combiners_Mod_Mod_Mod_Const_Color_T1_T2_T3 = M2ShaderTableRecord(
        M2PixelShader.Combiners_Mod_Mod_Mod_Const,              M2VertexShader.Color_T1_T2_T3)

    Combiners_Opaque_Diffuse_T1 = M2ShaderTableRecord(
        M2PixelShader.Combiners_Opaque,                         M2VertexShader.Diffuse_T1)

    Combiners_Mod_Mod2x_Diffuse_EdgeFade_T1_T2 = M2ShaderTableRecord(
        M2PixelShader.Combiners_Mod_Mod2x,                      M2VertexShader.Diffuse_EdgeFade_T1_T2)


@singleton
class M2ShaderPermutations:

    def __init__(self):
        self.shader_permutations: Dict[Tuple[int, int, int], gpu.types.GPUShader] = {}

        rel_path = 'shaders\\glsl330\\m2_shader.glsl' if os.name == 'nt' else 'shaders/glsl330/m2_shader.glsl'

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), rel_path)) as f:
            shader_string = "".join(f.readlines())

        for record in tqdm(M2ShaderTable, desc='Compiling M2 shader permutations'):

            for i in range(5):
                vert_shader_string_perm = "#define COMPILING_VS {}\n" \
                                          "#define BONEINFLUENCES {}\n" \
                                          "#define VERTEXSHADER {}\n" \
                                          "{}".format(1, i, record.value.vertex_shader, shader_string)
                frag_shader_string_perm = "#define COMPILING_FS {}\n" \
                                          "#define BONEINFLUENCES {}\n" \
                                          "#define FRAGMENTSHADER {}\n" \
                                          "{}".format(1, i, record.value.pixel_shader, shader_string)

                self.shader_permutations[record.value.vertex_shader, record.value.pixel_shader, i] = \
                    gpu.types.GPUShader(vert_shader_string_perm, frag_shader_string_perm)

    def get_shader_by_id(self
                         , vert_shader_id: int
                         , frag_shader_id: int
                         , bone_influences: int) -> gpu.types.GPUShader:

        return self.shader_permutations[vert_shader_id, frag_shader_id, bone_influences]

    def get_shader_by_m2_id(self
                            , texture_count: int
                            , m2_batch_shader_id: int
                            , bone_influences: int) -> gpu.types.GPUShader:

        vert_shader_id = self._get_vertex_shader_id(texture_count, m2_batch_shader_id)
        frag_shader_id = self._get_pixel_shader_id(texture_count, m2_batch_shader_id)

        #print(vert_shader_id, frag_shader_id)

        return self.shader_permutations[vert_shader_id, frag_shader_id, bone_influences]

    @staticmethod
    def _get_vertex_shader_id(texture_count: int, shader_id: int) -> int:

        if shader_id < 0:
            vertex_shader_id = shader_id & 0x7FFF

            if c_uint(vertex_shader_id).value >= 0x22:
                raise ValueError("Wrong shader ID for vertex shader")

            result = c_uint(M2ShaderTable[vertex_shader_id].vertex_shader).value

        elif texture_count == 1:
            if (shader_id & 0x80) != 0:
                result = 1
            else:
                result = 10
                if not (shader_id & 0x4000):
                    result = 0

        elif (shader_id & 0x80) != 0:
            result = ((shader_id & 8) >> 3) | 4

        else:
            result = 3
            if not (shader_id & 8):
                result = 5 * c_uint((shader_id & 0x4000) == 0).value + 2

        return result

    @staticmethod
    def _get_pixel_shader_id(texture_count: int, shader_id: int):

        array1 = [
            M2PixelShader.Combiners_Mod_Mod2x,
            M2PixelShader.Combiners_Mod_Mod,
            M2PixelShader.Combiners_Mod_Mod2xNA,
            M2PixelShader.Combiners_Mod_AddNA,
            M2PixelShader.Combiners_Mod_Opaque,
            M2PixelShader.Combiners_Mod_Mod,
            M2PixelShader.Combiners_Mod_Mod,
            M2PixelShader.Combiners_Mod_Add
        ]

        array2 = [
            M2PixelShader.Combiners_Opaque_Mod2x,
            M2PixelShader.Combiners_Opaque_Mod,
            M2PixelShader.Combiners_Opaque_Mod2xNA,
            M2PixelShader.Combiners_Opaque_AddAlpha_Alpha,
            M2PixelShader.Combiners_Opaque_Opaque,
            M2PixelShader.Combiners_Opaque_Mod,
            M2PixelShader.Combiners_Opaque_Mod,
            M2PixelShader.Combiners_Opaque_AddAlpha_Alpha
        ]

        if shader_id < 0:

            pixel_shader_id = shader_id & 0x7FFF
            if c_uint(pixel_shader_id).value >= 0x22:
                raise ValueError("Wrong shader ID for pixel shader")

            result = c_uint(M2ShaderTable[shader_id & 0x7FFF].pixel_shader).value

        elif texture_count == 1:

            result = int((shader_id & 0x70) != 0)
        else:

            cur_array = array2
            if shader_id & 0x70:
                cur_array = array1

            result = cur_array[(c_uint8(shader_id).value ^ 4) & 7]

        return result


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
        'bind_code1'
    )

    def __init__(self, obj: bpy.types.Object, draw_obj: 'M2DrawingObject'):
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
        self.material: bpy.types.Material
        self.texture: bpy.types.Image = None
        self.bind_code1 = 0

        self._update_batch_geometry(self.bl_obj)
        self.shader = self.determine_valid_shader()
        self.batch = self._create_batch()
        self.bind_textures()

    def bind_textures(self):
        self.material = self.bl_obj.data.materials[0]
        self.texture = self.material.wow_m2_material.texture

        bind_code, users = self.draw_obj.drawing_mgr.bound_textures.get(self.texture, (None, None))

        if bind_code is None and self.texture:
            self.texture.gl_load()
            bind_code = self.texture.bindcode
            self.draw_obj.drawing_mgr.bound_textures[self.texture] = bind_code, [self, ]

        elif self not in users:
            users.append(self)

        self.bind_code1 = bind_code

    def _set_active_textures(self):
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.bind_code1)

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

        self._set_active_textures()

        color_name = self.texture.wow_m2_texture.color
        transparency_name = self.texture.wow_m2_texture.transparency

        color = bpy.context.scene.wow_m2_colors[color_name].color if color_name else (1.0, 1.0, 1.0, 1.0)
        transparency = bpy.context.scene.wow_m2_transparency[transparency_name].value if transparency_name else 1.0

        combined_color = (*color[:3], color[3] * transparency)

        m2_blend_mode = int(self.material.wow_m2_material.blending_mode)
        blend_record = M2BlendingModeToEGxBlend[m2_blend_mode]

        blend_enabled = blend_record.blending_enabled
        depth_write = '16' not in self.material.wow_m2_material.render_flags
        depth_culling = '8' not in self.material.wow_m2_material.render_flags
        backface_culling = '4' not in self.material.wow_m2_material.render_flags
        is_unlit = int('1' in self.material.wow_m2_material.render_flags)
        is_unfogged = int('2' in self.material.wow_m2_material.render_flags)

        if m2_blend_mode == 1: # Alpha Key
            u_alpha_test = 128.0 / 255.0 * combined_color[3]  # Maybe move this to shader logic?
        else:
            u_alpha_test = 1.0 / 255.0

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

        # get active viewport
        r3d = bpy.data.screens[5].areas[5].spaces[0].region_3d

        sun_dir = mathutils.Vector(bpy.context.scene.wow_render_settings.sun_direction)
        sun_dir.negate()

        tex1_matrix_flattened = [j[i] for i in range(4)
                                 for j in bpy.context.scene.objects['TT_Controller.003'].matrix_world] \
                                if self.bl_obj.wow_m2_geoset.uv_transform \
                                else [j[i] for i in range(4) for j in mathutils.Matrix.Identity(4)]

        tex2_matrix_flattened = [j[i] for i in range(4) for j in mathutils.Matrix.Identity(4)]

        self.shader.uniform_float('uViewProjectionMatrix', r3d.perspective_matrix)
        self.shader.uniform_float('uPlacementMatrix', self.bl_obj.matrix_world)
        self.shader.uniform_float('uSunDirAndFogStart', (*sun_dir[:3], 10))
        self.shader.uniform_float('uSunColorAndFogEnd', (*bpy.context.scene.wow_render_settings.ext_dir_color[:3], 50))
        self.shader.uniform_float('uAmbientLight', bpy.context.scene.wow_render_settings.ext_ambient_color)
        self.shader.uniform_float('uFogColorAndAlphaTest', (1, 0, 0, u_alpha_test))
        self.shader.uniform_int('UnFogged_IsAffectedByLight_LightCount', (is_unfogged, is_unlit, 0))
        self.shader.uniform_int('uTexture', 0)
        self.shader.uniform_float('color_Transparency', combined_color)
        self.shader.uniform_vector_float(self.shader.uniform_from_name('uTextMat'),
                                         struct.pack('16f', *tex1_matrix_flattened)
                                         + struct.pack('16f', *tex2_matrix_flattened), 16, 2)

        if self.bone_influences:
            self.shader.uniform_vector_float(self.shader.uniform_from_name('uBoneMatrices'),
                                             self.draw_obj.bone_matrices, 16, len(self.bl_rig.pose.bones))

        glCheckError('uniform')
        self.batch.draw(self.shader)
        glCheckError('draw')

        if blend_enabled:
            glDisable(GL_BLEND)

        if backface_culling:
            glDisable(GL_CULL_FACE)

        if depth_write:
            glDepthMask(GL_FALSE)

        if depth_culling:
            glDisable(GL_DEPTH_TEST)

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


class M2DrawingObject:
    __slots__ = (
        'drawing_mgr',
        'rig',
        'batches',
        'bone_matrices'
    )

    def __init__(self, rig: bpy.types.Object, drawing_mgr: 'M2DrawingManager'):

        if rig.type != 'ARMATURE':
            raise Exception('Error: object \"{}\" is not an armature object.'.format(rig.name))

        self.drawing_mgr = drawing_mgr
        self.rig = rig
        self.batches: List[M2DrawingBatch] = []
        self.bone_matrices = np.empty((len(self.rig.pose.bones), 16), 'f')

        self.create_batches_from_armature(rig)

    def draw(self):

        for i, pbone in enumerate(self.rig.pose.bones):

            '''
            rest_bone_mat = self.bl_rig.data.bones[pbone.name].matrix_local
            mat = (self.bl_rig.matrix_world @ rest_bone_mat).inverted() @ (self.bl_rig.matrix_world @ pbone.matrix)
            '''

            self.bone_matrices[i] = [j[i] for i in range(4) for j in self.rig.convert_space(pose_bone=pbone,
                                                                                            matrix=pbone.matrix_channel,
                                                                                            from_space='POSE',
                                                                                            to_space='WORLD')]
        broken_batches = []

        for batch in self.batches:

            try:
                batch.draw()
            except:
                broken_batches.append(batch)
                traceback.print_exc()

        for batch in broken_batches:
            batch.free_textures()
            self.batches.remove(batch)

    def create_batches_from_armature(self, rig: bpy.types.Object):

        for obj in filter(lambda x: x.type == 'MESH', rig.children):

            # Limit bone influences to 4. TODO: rework to be non-destructive!
            if obj.vertex_groups:
                active_obj = bpy.context.view_layer.objects.active
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.vertex_group_limit_total()
                bpy.context.view_layer.objects.active = active_obj

            self._create_batch_from_object(obj)

    def _create_batch_from_object(self, obj: bpy.types.Object):
        self.batches.append(M2DrawingBatch(obj, self))


class M2DrawingManager:

    def __init__(self):
        self.shaders = M2ShaderPermutations()
        self.m2_objects: List[M2DrawingObject] = []
        self.bound_textures: Dict[bpy.types.Image, Tuple[int, List[M2DrawingBatch]]] = {}
        self.handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback, (self,), 'WINDOW','POST_VIEW')

    def queue_for_drawing(self, obj: bpy.types.Object):
        if obj.type != 'ARMATURE':
            raise Exception('Error: M2 should be represented as armature object. Failed to queue for drawing.')

        self.m2_objects.append(M2DrawingObject(obj, self))

    @staticmethod
    def draw_callback(self):

        for m2 in self.m2_objects:
            m2.draw()

    def __del__(self):
        bpy.types.SpaceView3D.draw_handler_remove(self.handle, 'WINDOW')


def glCheckError(title):
    err = glGetError()
    if err == GL_NO_ERROR:
        return

    derrs = {
        GL_INVALID_ENUM: 'invalid enum',
        GL_INVALID_VALUE: 'invalid value',
        GL_INVALID_OPERATION: 'invalid operation',
        GL_OUT_OF_MEMORY: 'out of memory',
        GL_INVALID_FRAMEBUFFER_OPERATION: 'invalid framebuffer operation',
    }
    if err in derrs:
        print('ERROR (%s): %s' % (title, derrs[err]))
    else:
        print('ERROR (%s): code %d' % (title, err))
    traceback.print_stack()




