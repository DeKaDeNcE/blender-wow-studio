import bpy
from bpy.app.handlers import persistent
from .drivers import register_m2_driver_utils

__reload_order_index__ = 0


@persistent
def live_update_materials(dummy):
    try:
        anim = bpy.context.scene.wow_m2_animations[bpy.context.scene.wow_m2_cur_anim_index]
        if anim.live_update:
            for mat in bpy.data.materials:
                if mat.wow_m2_material.live_update:
                    mat.invert_z = mat.invert_z
    except IndexError:
        pass


@persistent
def load_handler(dummy):
    register_m2_driver_utils()


def register_m2_handlers():
    bpy.app.handlers.frame_change_pre.append(live_update_materials)
    load_handler(None)
    bpy.app.handlers.load_post.append(load_handler)


def unregister_m2_handlers():
    bpy.app.handlers.frame_change_pre.remove(live_update_materials)
    bpy.app.handlers.load_post.remove(load_handler)
