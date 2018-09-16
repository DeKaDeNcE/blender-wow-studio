import os
import bpy

from pathlib import Path
from .internal import update_wmo_mat_node_tree_internal
from .cycles import update_wmo_mat_node_tree_cycles


node_groups = [
    'MO_ApplyLighting',
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
    'MO_SetLighting'
 ]


def load_wmo_shader_dependencies(reload_shader=False):
    render_engine = bpy.context.scene.render.engine

    # remove old node groups
    if reload_shader:
        for ng_name in node_groups:
            if ng_name in bpy.data.node_groups:
                bpy.data.node_groups.remove(bpy.data.node_groups[ng_name])

    if render_engine == 'BLENDER_RENDER':
        lib_path = os.path.join(str(Path(__file__).parent), 'internal', 'wotlk_default.blend')
    elif render_engine == 'CYCLES':
        lib_path = os.path.join(str(Path(__file__).parent), 'cycles', 'wotlk_default.blend')
    else:
        print('\nWARNING: Failed loading shader: materials may not display correctly.'
              '\nIncompatible render engine \"{}"\"'.format(render_engine))
        return

    with bpy.data.libraries.load(lib_path) as (data_from, data_to):
        data_to.node_groups = [node_group for node_group in data_from.node_groups if node_group in node_groups]


def update_wmo_mat_node_tree(bl_mat):

    render_engine = bpy.context.scene.render.engine

    if render_engine == 'BLENDER_RENDER':
        update_wmo_mat_node_tree_internal(bl_mat)

    elif render_engine == 'CYCLES':
        update_wmo_mat_node_tree_cycles(bl_mat)
        bpy.context.scene.wow_wmo_root.sun_direction = bpy.context.scene.wow_wmo_root.sun_direction

    else:
        print('\nWARNING: Failed generating node tree: material \"{}\" may not display correctly.'
              '\nIncompatible render engine \"{}"\"'.format(bl_mat.name, render_engine))

    # sync scene lighting properties
    bpy.context.scene.wow_wmo_root.ext_ambient_color = bpy.context.scene.wow_wmo_root.ext_ambient_color
    bpy.context.scene.wow_wmo_root.ext_dir_color = bpy.context.scene.wow_wmo_root.ext_dir_color
    bpy.context.scene.wow_wmo_root.sidn_scalar = bpy.context.scene.wow_wmo_root.sidn_scalar
