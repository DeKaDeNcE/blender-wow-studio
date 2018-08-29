import bpy
from .internal import load_dependencies_internal, update_wmo_mat_node_tree_internal
from .cycles import load_dependencies_cycles, update_wmo_mat_node_tree_cycles

def load_wmo_shader_dependencies(reload_shader=False):
    render_engine = bpy.context.scene.render.engine

    if render_engine == 'BLENDER_RENDER':
        load_dependencies_internal(reload_shader)
    elif render_engine == 'CYCLES':
        load_dependencies_cycles(reload_shader)
    else:
        print('\nWARNING: Failed loading shader: materials may not display correctly.'
              '\nIncompatible render engine \"{}"\"'.format(render_engine))


def update_wmo_mat_node_tree(bl_mat):

    render_engine = bpy.context.scene.render.engine

    if render_engine == 'BLENDER_RENDER':
        update_wmo_mat_node_tree_internal(bl_mat)

    elif render_engine == 'CYCLES':
        update_wmo_mat_node_tree_cycles(bl_mat)

    else:
        print('\nWARNING: Failed generating node tree: material \"{}\" may not display correctly.'
              '\nIncompatible render engine \"{}"\"'.format(bl_mat.name, render_engine))