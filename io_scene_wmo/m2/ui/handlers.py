import bpy
from bpy.app.handlers import persistent


# @persistent
def live_update_materials(dummy):
    for mat_slot in bpy.context.scene.WowM2MaterialsToUpdate:
        if mat_slot.material.LiveUpdate:
            mat_slot.material.invert_z = mat_slot.material.invert_z


def register_m2_handlers():
    bpy.app.handlers.frame_change_pre.append(live_update_materials)


def unregister_m2_handlers():
    bpy.app.handlers.frame_change_pre.remove(live_update_materials)