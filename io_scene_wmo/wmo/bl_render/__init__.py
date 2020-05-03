import os
import bpy

from pathlib import Path
from .cycles import update_wmo_mat_node_tree_cycles


class BlenderWMOObjectRenderFlags:
    IsOutdoor = 0x1
    IsIndoor = 0x2
    NoLocalLight = 0x4
    HasBatchB = 0x8
    HasBatchA = 0x10
    HasVertexColor = 0x20
    HasBlendmap = 0x40
    HasLightmap = 0x80

class BlenderWMOMaterialRenderFlags:
    Unlit = 0x1
    SIDN = 0x2
    IsTwoLayered = 0x4
    IsOpaque = 0x10

node_groups = [
    'MO_ApplyLighting',
    'MO_ApplyLightingTrans',
    'MO_ApplyLightingGeneric',
    'MO_Equal',
    'MO_IsFlagInBitmask',
    'MO_IsInBatchMap',
    'MO_MaterialFlags',
    'MO_MixBatches',
    'MO_MixTextures',
    'MO_ObjectFlags',
    'MO_Properties',
    'MO_ApplyVertexColor',
    'MO_FixVertexColorAlpha',
    'MO_SaturateUpper',
    'MO_SetLighting',
    'MO_ShaderMix',
    'MO_WMOShader'
 ]


def load_wmo_shader_dependencies(reload_shader=False):
    render_engine = bpy.context.scene.render.engine

    # remove old node groups
    if reload_shader:
        for ng_name in node_groups:
            if ng_name in bpy.data.node_groups:
                bpy.data.node_groups.remove(bpy.data.node_groups[ng_name])

    missing_nodes = [ng_name for ng_name in node_groups if ng_name not in bpy.data.node_groups]

    if render_engine in ('CYCLES', 'BLENDER_EEVEE'):
        lib_path = os.path.join(str(Path(__file__).parent), 'cycles', 'wotlk_default.blend')
    else:
        print('\nWARNING: Failed loading shader: materials may not display correctly.'
              '\nIncompatible render engine \""{}"\"'.format(render_engine))
        return

    with bpy.data.libraries.load(lib_path) as (data_from, data_to):
        data_to.node_groups = [node_group for node_group in data_from.node_groups if node_group in missing_nodes]


def update_wmo_mat_node_tree(bl_mat):

    render_engine = bpy.context.scene.render.engine

    if render_engine in ('CYCLES', 'BLENDER_EEVEE'):
        update_wmo_mat_node_tree_cycles(bl_mat)
        bpy.context.scene.wow_render_settings.sun_direction = bpy.context.scene.wow_render_settings.sun_direction

    else:
        print('\nWARNING: Failed generating node tree: material \"{}\" may not display correctly.'
              '\nIncompatible render engine \""{}"\"'.format(bl_mat.name, render_engine))

    # sync scene lighting properties
    bpy.context.scene.wow_render_settings.ext_ambient_color= bpy.context.scene.wow_render_settings.ext_ambient_color
    bpy.context.scene.wow_render_settings.ext_dir_color = bpy.context.scene.wow_render_settings.ext_dir_color
    bpy.context.scene.wow_render_settings.sidn_scalar = bpy.context.scene.wow_render_settings.sidn_scalar
