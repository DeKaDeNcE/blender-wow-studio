import os
import bpy

from .cycles import update_m2_mat_node_tree_cycles


def update_m2_mat_node_tree(bl_mat):

    render_engine = bpy.context.scene.render.engine

    if render_engine in ('CYCLES', 'BLENDER_EEVEE'):
        update_m2_mat_node_tree_cycles(bl_mat)

    else:
        print('\nWARNING: Failed generating node tree: material \"{}\" may not display correctly.'
              '\nIncompatible render engine \""{}"\"'.format(bl_mat.name, render_engine))

