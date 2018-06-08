import bpy
from bpy.app.handlers import persistent


@persistent
def live_update_materials(dummy):
    try:
        anim = bpy.context.scene.wow_m2_animations[bpy.context.scene.wow_m2_cur_anim_index]
        if anim.LiveUpdate:
            for mat in bpy.data.materials:
                if mat.wow_m2_material.LiveUpdate:
                    mat.invert_z = mat.invert_z
    except IndexError:
        pass


def register_m2_handlers():
    bpy.app.handlers.frame_change_pre.append(live_update_materials)


def unregister_m2_handlers():
    bpy.app.handlers.frame_change_pre.remove(live_update_materials)