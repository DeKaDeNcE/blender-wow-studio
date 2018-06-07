import bpy

from bpy.app.handlers import persistent
from ..utils import load_game_data

from ..m2.ui.handlers import register_m2_handlers, unregister_m2_handlers


@persistent
def _load_game_data(scene):
    load_game_data()


def register_handlers():
    bpy.app.handlers.load_post.append(_load_game_data)
    register_m2_handlers()


def unregister_handlers():
    bpy.app.handlers.load_post.remove(_load_game_data)
    unregister_m2_handlers()



