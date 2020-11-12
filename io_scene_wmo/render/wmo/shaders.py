import os
import gpu

from enum import IntEnum
from ctypes import c_uint, c_uint8
from collections import namedtuple
from typing import Dict, Tuple

from ...utils.misc import singleton, Sequence
from ..shaders import ShaderPermutationsManager
from bgl import *


class WMOPixelShader(IntEnum):
    NoShader = -1,
    MapObjDiffuse = 0,
    MapObjSpecular = 1,
    MapObjMetal = 2,
    MapObjEnv = 3,
    MapObjOpaque = 4,
    MapObjEnvMetal = 5,
    MapObjTwoLayerDiffuse = 6, # MapObjComposite
    MapObjTwoLayerEnvMetal = 7,
    MapObjTwoLayerTerrain = 8,
    MapObjDiffuseEmissive = 9,
    MapObjMaskedEnvMetal = 10,
    MapObjEnvMetalEmissive = 11,
    MapObjTwoLayerDiffuseOpaque = 12,
    MapObjTwoLayerDiffuseEmissive = 13,
    MapObjAdditiveMaskedEnvMetal = 14,
    MapObjTwoLayerDiffuseMod2x = 15,
    MapObjTwoLayerDiffuseMod2xNA = 16,
    MapObjTwoLayerDiffuseAlpha = 17,
    MapObjLod = 18,
    MapObjParallax = 19


class WMOVertexShader(IntEnum):
    NoShader = -1,
    MapObjDiffuse_T1 = 0,
    MapObjDiffuse_T1_Refl = 1,
    MapObjDiffuse_T1_Env_T2 = 2,
    MapObjSpecular_T1 = 3,
    MapObjDiffuse_Comp = 4,
    MapObjDiffuse_Comp_Refl = 5,
    MapObjDiffuse_Comp_Terrain = 6,
    MapObjDiffuse_CompAlpha = 7,
    MapObjParallax = 8,


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


class WMOBlendingModeToEGxBlend(metaclass=Sequence):

    Blend_Opaque = EGxBLend.Opaque
    Blend_AlphaKey = EGxBLend.AlphaKey
    Blend_Alpha = EGxBLend.Alpha
    Blend_NoAlphaAdd = EGxBLend.NoAlphaAdd
    Blend_Add = EGxBLend.Add
    Blend_Mod = EGxBLend.Mod
    Blend_Mod2x = EGxBLend.Mod2x
    Blend_BlendAdd = EGxBLend.BlendAdd


WMOShaderTableRecord = namedtuple('WMOShaderTableRecord', ['pixel_shader', 'vertex_shader'])


class WMOShaderTable(metaclass=Sequence):
    MapObjDiffuse = WMOShaderTableRecord(WMOPixelShader.MapObjDiffuse, WMOVertexShader.MapObjDiffuse_T1)

    MapObjSpecular = WMOShaderTableRecord(WMOPixelShader.MapObjSpecular, WMOVertexShader.MapObjSpecular_T1)

    MapObjMetal = WMOShaderTableRecord(WMOPixelShader.MapObjMetal, WMOVertexShader.MapObjSpecular_T1)

    MapObjEnv = WMOShaderTableRecord(WMOPixelShader.MapObjEnv, WMOVertexShader.MapObjDiffuse_T1_Refl)

    MapObjOpaque = WMOShaderTableRecord(WMOPixelShader.MapObjOpaque, WMOVertexShader.MapObjDiffuse_T1)

    MapObjEnvMetal = WMOShaderTableRecord(WMOPixelShader.MapObjEnvMetal, WMOVertexShader.MapObjDiffuse_T1_Refl)

    MapObjTwoLayerDiffuse = WMOShaderTableRecord(WMOPixelShader.MapObjTwoLayerDiffuse,
                                                 WMOVertexShader.MapObjDiffuse_Comp)

    MapObjTwoLayerEnvMetal = WMOShaderTableRecord(WMOPixelShader.MapObjTwoLayerEnvMetal,
                                                  WMOVertexShader.MapObjDiffuse_T1)

    TwoLayerTerrain = WMOShaderTableRecord(WMOPixelShader.MapObjTwoLayerTerrain,
                                           WMOVertexShader.MapObjDiffuse_Comp_Terrain)

    MapObjDiffuseEmissive = WMOShaderTableRecord(WMOPixelShader.MapObjDiffuseEmissive,
                                                 WMOVertexShader.MapObjDiffuse_Comp)

    waterWindow = WMOShaderTableRecord(WMOPixelShader.NoShader,
                                       WMOVertexShader.NoShader)

    MapObjMaskedEnvMetal = WMOShaderTableRecord(WMOPixelShader.MapObjMaskedEnvMetal,
                                                WMOVertexShader.MapObjDiffuse_T1_Env_T2)

    MapObjEnvMetalEmissive = WMOShaderTableRecord(WMOPixelShader.MapObjEnvMetalEmissive,
                                                  WMOVertexShader.MapObjDiffuse_T1_Env_T2)

    TwoLayerDiffuseOpaque = WMOShaderTableRecord(WMOPixelShader.MapObjTwoLayerDiffuseOpaque,
                                                 WMOVertexShader.MapObjDiffuse_Comp)

    submarineWindow = WMOShaderTableRecord(WMOPixelShader.NoShader, WMOVertexShader.NoShader)

    TwoLayerDiffuseEmissive = WMOShaderTableRecord(WMOPixelShader.MapObjTwoLayerDiffuseEmissive,
                                                   WMOVertexShader.MapObjDiffuse_Comp)

    MapObjDiffuseTerrain = WMOShaderTableRecord(WMOPixelShader.MapObjDiffuse,
                                                WMOVertexShader.MapObjDiffuse_T1)

    MapObjAdditiveMaskedEnvMetal = WMOShaderTableRecord(WMOPixelShader.MapObjAdditiveMaskedEnvMetal,
                                                        WMOVertexShader.MapObjDiffuse_T1_Env_T2)

    MapObjTwoLayerDiffuseMod2x = WMOShaderTableRecord(WMOPixelShader.MapObjTwoLayerDiffuseMod2x,
                                                      WMOVertexShader.MapObjDiffuse_CompAlpha)

    MapObjTwoLayerDiffuseMod2xNA = WMOShaderTableRecord(WMOPixelShader.MapObjTwoLayerDiffuseMod2xNA,
                                                        WMOVertexShader.MapObjDiffuse_Comp)

    MapObjTwoLayerDiffuseAlpha = WMOShaderTableRecord(WMOPixelShader.MapObjTwoLayerDiffuseAlpha,
                                                      WMOVertexShader.MapObjDiffuse_CompAlpha)

    MapObjLod = WMOShaderTableRecord(WMOPixelShader.MapObjLod,
                                     WMOVertexShader.MapObjDiffuse_T1)

    MapObjParallax = WMOShaderTableRecord(WMOPixelShader.MapObjParallax,
                                          WMOVertexShader.MapObjParallax)

@singleton
class WMOShaderPermutations(ShaderPermutationsManager):

    shader_source_path = 'wmo_shader'

    @staticmethod
    def get_shader_combo_index(vertex_shader_id: int, pixel_shader_id: int):

        for record in WMOShaderTable:
            if record.value.vertex_shader == vertex_shader_id and record.value.pixel_shader == pixel_shader_id:
                return record.index

    def get_shader_combo(self, id: int):
        # TODO: ugly

        count = 0
        for i, record in enumerate(WMOShaderTable):

            if i == count:
                return record

            count += 1

