import os
import gpu

from enum import IntEnum
from ctypes import c_uint, c_uint8
from collections import namedtuple
from typing import Dict, Tuple

from ...utils.misc import singleton, Sequence
from ..shaders import ShaderPermutationsManager
from bgl import *


class M2PixelShader(IntEnum):
    # Wotlk deprecated shaders
    '''
    Combiners_Decal = -1
    Combiners_Add = -2
    Combiners_Mod2x = -3
    Combiners_Fade = -4,
    Combiners_Opaque_Add = -5
    Combiners_Opaque_AddNA = -6
    Combiners_Add_Mod = -7
    Combiners_Mod2x_Mod2x = -8
    '''

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
                            ['blending_enabled', 'src_color', 'dest_color', 'src_alpha', 'dest_alpha', 'index'])


class EGxBLend(metaclass=Sequence):
    Opaque = EGxBlendRecord(False, GL_ONE, GL_ZERO, GL_ONE, GL_ZERO, 0)
    AlphaKey = EGxBlendRecord(False, GL_ONE, GL_ZERO, GL_ONE, GL_ZERO, 1)
    Alpha = EGxBlendRecord(True, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ONE_MINUS_SRC_ALPHA, 2)
    Add = EGxBlendRecord(True, GL_SRC_ALPHA, GL_ONE, GL_ZERO, GL_ONE, 3)
    Mod = EGxBlendRecord(True, GL_DST_COLOR, GL_ZERO, GL_DST_ALPHA, GL_ZERO, 4)
    Mod2x = EGxBlendRecord(True, GL_DST_COLOR, GL_SRC_COLOR, GL_DST_ALPHA, GL_SRC_ALPHA, 5)
    ModAdd = EGxBlendRecord(True, GL_DST_COLOR, GL_ONE, GL_DST_ALPHA, GL_ONE, 6)
    InvSrcAlphaAdd = EGxBlendRecord(True, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, 7)
    InvSrcAlphaOpaque = EGxBlendRecord(True, GL_ONE_MINUS_SRC_ALPHA, GL_ZERO, GL_ONE_MINUS_SRC_ALPHA, GL_ZERO, 8)
    SrcAlphaOpaque = EGxBlendRecord(True, GL_SRC_ALPHA, GL_ZERO, GL_SRC_ALPHA, GL_ZERO, 9)
    NoAlphaAdd = EGxBlendRecord(True, GL_ONE, GL_ONE, GL_ZERO, GL_ONE, 10)
    ConstantAlpha = EGxBlendRecord(True, GL_CONSTANT_ALPHA, GL_ONE_MINUS_CONSTANT_ALPHA, GL_CONSTANT_ALPHA,
                                   GL_ONE_MINUS_CONSTANT_ALPHA, 11)
    Screen = EGxBlendRecord(True, GL_ONE_MINUS_DST_COLOR, GL_ONE, GL_ONE, GL_ZERO, 12)
    BlendAdd = EGxBlendRecord(True, GL_ONE, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ONE_MINUS_SRC_ALPHA, 13)


class M2BlendingModeToEGxBlend(metaclass=Sequence):

    Blend_Opaque = EGxBLend.Opaque
    Blend_AlphaKey = EGxBLend.AlphaKey
    Blend_Alpha = EGxBLend.Alpha
    Blend_NoAlphaAdd = EGxBLend.NoAlphaAdd
    Blend_Add = EGxBLend.Add
    Blend_Mod = EGxBLend.Mod
    Blend_Mod2x = EGxBLend.Mod2x
    Blend_BlendAdd = EGxBLend.BlendAdd


M2ShaderTableRecord = namedtuple('M2ShaderTableRecord', ['pixel_shader', 'vertex_shader'])


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

    Combiners_Mod_Mod_Diffuse_EdgeFade_T1_T2 = M2ShaderTableRecord(
        M2PixelShader.Combiners_Mod_Mod,                        M2VertexShader.Diffuse_EdgeFade_T1_T2)

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
class M2ShaderPermutations(ShaderPermutationsManager):

    shader_source_path = 'm2_shader'

    @staticmethod
    def get_vertex_shader_id(texture_count: int, shader_id: int) -> int:

        if shader_id < 0:  # all shaders with negative shader id
            vertex_shader_id = shader_id & 0x7FFF

            if c_uint(vertex_shader_id).value >= 0x22:
                raise ValueError("Wrong shader ID for vertex shader")

            result = c_uint(M2ShaderTable[vertex_shader_id].vertex_shader).value

            # reverse: vertex_shader_id | 0x80000000 for int32) (do with ctypes)

        elif texture_count == 1:  # 0, 1, 10
            if (shader_id & 0x80) != 0:
                result = 1
            else:
                result = 10
                if not (shader_id & 0x4000):
                    result = 0

        elif (shader_id & 0x80) != 0:  # 4, 5
            result = ((shader_id & 8) >> 3) | 4

        else:  # 3, 7, 8
            result = 3
            if not (shader_id & 8):
                result = 5 * c_uint((shader_id & 0x4000) == 0).value + 2

        return result

    @staticmethod
    def get_pixel_shader_id(texture_count: int, shader_id: int):

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

        if shader_id < 0:  # all shaders with negative shader id

            pixel_shader_id = shader_id & 0x7FFF
            if c_uint(pixel_shader_id).value >= 0x22:
                raise ValueError("Wrong shader ID for pixel shader")

            result = c_uint(M2ShaderTable[pixel_shader_id].pixel_shader).value

            # reverse: pixel_shader_id | 0x80000000 for int32) (do with ctypes)

        elif texture_count == 1:  # 0, 1

            result = int((shader_id & 0x70) != 0)
        else:

            cur_array = array2
            if shader_id & 0x70:
                cur_array = array1

            result = cur_array[(c_uint8(shader_id).value ^ 4) & 7].value

        return result

    @staticmethod
    def get_shader_combo_index(vertex_shader_id: int, pixel_shader_id: int):

        for record in M2ShaderTable:
            if record.value.vertex_shader == vertex_shader_id and record.value.pixel_shader == pixel_shader_id:
                return record.index

