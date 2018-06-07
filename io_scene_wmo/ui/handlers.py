import bpy

from bpy.app.handlers import persistent
from ..utils import load_game_data


@persistent
def _load_game_data(scene):
    load_game_data()

@persistent
def recompile_node_trees(dummy):
    for mat in bpy.data.materials:
        mat.invert_z = False


def register_handlers():
    bpy.app.handlers.load_post.append(_load_game_data)
    bpy.app.handlers.frame_change_pre.append(recompile_node_trees)


def unregister_handlers():
    bpy.app.handlers.load_post.remove(_load_game_data)
    bpy.app.handlers.frame_change_pre.remove(recompile_node_trees)



