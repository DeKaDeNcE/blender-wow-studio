import bpy
from .internal import load_dependencies_internal, update_wmo_mat_node_tree_internal


def load_wmo_shader_dependencies(reload_shader=False):
    render_engine = bpy.context.scene.render.engine

    if render_engine == 'BLENDER_RENDER':
        load_dependencies_internal(reload_shader)
    else:
        print('\nWARNING: Failed loading shader: materials may not display correctly.'
              '\nIncompatible render engine \"{}"\"'.format(render_engine))


def update_wmo_mat_node_tree(bl_mat):

    render_engine = bpy.context.scene.render.engine

    if render_engine == 'BLENDER_RENDER':
        update_wmo_mat_node_tree_internal(bl_mat)
    else:
        print('\nWARNING: Failed generating node tree: material \"{}\" may not display correctly.'
              '\nIncompatible render engine \"{}"\"'.format(bl_mat.name, render_engine))