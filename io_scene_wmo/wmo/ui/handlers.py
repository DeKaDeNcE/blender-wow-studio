import bpy
from bpy.app.handlers import persistent
from ...utils.misc import show_message_box


_obj_props = (
              ('wow_wmo_group', 'groups'),
              ('wow_wmo_portal', 'portals'),
              ('wow_wmo_fog', 'fogs'),
              ('wow_wmo_light', 'lights'),
              ('wow_wmo_doodad_set', 'doodad_sets'),
              ('wow_wmo_doodad', 'doodads')
             )


def _remove_col_items(scene, col_name):
    col = getattr(scene.wow_wmo_root_components, col_name)
    for i, obj in enumerate(col):
        if obj.pointer and obj.pointer.name not in scene.objects:
            col.remove(i)
            break
    else:
        return

    _remove_col_items(scene, col_name)


def _remove_col_items_doodads(scene):
    col = scene.wow_wmo_root_components.doodad_sets

    # prevent infinite recursion
    if not len(col):
        return

    for d_set in col:
        for i, doodad in enumerate(d_set.doodads):
            if doodad.pointer and doodad.pointer.name not in scene.objects:
                d_set.doodads.remove(i)
                break

        else:
            return

    _remove_col_items_doodads(scene)

def _add_col_items(scene):
    for i, obj in enumerate(scene.objects):
        for prop, col_name in _obj_props:
            prop_group = getattr(obj, prop)

            if col_name == 'doodads':

                if prop_group.enabled:

                    # identify if doodad is not in any doodad set
                    for d_set in scene.wow_wmo_root_components.doodad_sets:
                        index = d_set.doodads.find(obj.name)

                        if index >= 0:
                            # check if doodad is parented to the correct set
                            if obj.parent != d_set.pointer:
                                obj.parent = d_set.pointer
                            break

                    else:
                        # attempt adding to active doodad set
                        if len(scene.wow_wmo_root_components.doodad_sets):
                            cur_set_index = scene.wow_wmo_root_components.cur_doodad_set
                            act_set = scene.wow_wmo_root_components.doodad_sets[cur_set_index]
                            slot = act_set.doodads.add()
                            slot.pointer = obj

                        else:
                            bpy.data.objects.remove(obj, do_unlink=True)

                else:
                    continue

            elif prop_group.enabled:

                col = getattr(scene.wow_wmo_root_components, col_name)

                if col.find(obj.name) < 0:
                    prop_group.enabled = False
                    slot = col.add()
                    slot.pointer = obj

DEPSGRAPH_UPDATE_LOCK = False

banned_ops = (
    "OBJECT_OT_transform_apply",
    "OBJECT_OT_transforms_to_deltas",
    "OBJECT_OT_origin_set",
    "TRANSFORM_OT_mirror",
    "OBJECT_OT_visual_transform_apply"
)


@persistent
def on_depsgraph_update(_):
    global DEPSGRAPH_UPDATE_LOCK
    if DEPSGRAPH_UPDATE_LOCK:
        return

    delete = False
    is_duplicated = False

    for update in bpy.context.view_layer.depsgraph.updates:

        try:
            if isinstance(update.id, bpy.types.Object) and update.id.type == 'MESH' and update.id.wow_wmo_doodad.enabled:
                obj = bpy.data.objects[update.id.name, update.id.library]
                DEPSGRAPH_UPDATE_LOCK = True

                # handle object copies
                if obj.active_material.users > 1:
                    for i, mat in enumerate(obj.data.materials):
                        mat = mat.copy()
                        obj.data.materials[i] = mat
                        is_duplicated = True

                if is_duplicated:
                    continue

                # enforce object mode
                if obj.mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode='OBJECT')

                # remove modifiers
                if len(obj.modifiers):
                    obj.modifiers.clear()

                # delete if object was processed by a specific operator
                if bpy.context.window_manager.operators[-1].bl_idname in banned_ops:
                    delete = True
                    bpy.data.objects.remove(obj, do_unlink=True)

                if update.is_updated_transform:
                    # check if object is scaled evenly
                    max_scale = 0.0
                    for j in range(3):
                        if obj.scale[j] > max_scale:
                            max_scale = obj.scale[j]

                    obj.scale = (max_scale, max_scale, max_scale)

            elif isinstance(update.id, bpy.types.Scene):
                n_objs = len(bpy.context.scene.objects)

                if n_objs == bpy.wbs_n_scene_objects:
                    continue

                if n_objs < bpy.wbs_n_scene_objects:
                    bpy.wbs_n_scene_objects = n_objs

                    _remove_col_items(bpy.context.scene, 'groups')
                    _remove_col_items(bpy.context.scene, 'portals')
                    _remove_col_items(bpy.context.scene, 'fogs')
                    _remove_col_items(bpy.context.scene, 'lights')
                    _remove_col_items(bpy.context.scene, 'doodad_sets')
                    _remove_col_items_doodads(bpy.context.scene)

                else:
                    bpy.wbs_n_scene_objects = n_objs
                    _add_col_items(bpy.context.scene)

        finally:
            DEPSGRAPH_UPDATE_LOCK = False



    if delete:
        show_message_box('One or more doodads were deleted due to mesh changes. Editing doodads is not allowed.'
                         , "WoW Blender Studio Error"
                         , icon='ERROR')


def register():
    bpy.wbs_n_scene_objects = 0
    bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update)


def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(on_depsgraph_update)
    del bpy.wbs_n_scene_objects

