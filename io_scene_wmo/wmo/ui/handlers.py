import bpy
from bpy.app.handlers import persistent
from ...utils.misc import show_message_box

__reload_order_index__ = 0

_obj_props = [('wow_wmo_group', 'groups'),
              ('wow_wmo_portal', 'portals'),
              ('wow_wmo_fog', 'fogs'),
              ('wow_wmo_light', 'lights'),
              ('wow_wmo_doodad_set', 'doodad_sets'),
              ('wow_wmo_doodad', 'doodads')
             ]


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


@persistent
def sync_wmo_root_components_collections(scene):
    n_objs = len(scene.objects)

    if n_objs == bpy.n_scene_objects:
        return

    if n_objs < bpy.n_scene_objects:
        bpy.n_scene_objects = n_objs

        _remove_col_items(scene, 'groups')
        _remove_col_items(scene, 'portals')
        _remove_col_items(scene, 'fogs')
        _remove_col_items(scene, 'lights')
        _remove_col_items(scene, 'doodad_sets')
        _remove_col_items_doodads(scene)

    else:
        bpy.n_scene_objects = n_objs

        for i, obj in enumerate(scene.objects):
            for prop, col_name in _obj_props:
                prop_group = getattr(obj, prop)

                if col_name == 'doodads':

                    if prop_group.enabled:

                        # identify if doodad is not in any doodad set
                        for d_set in scene.wow_wmo_root_components.doodad_sets:
                            index = d_set.doodads.find(obj.name)
                            if index >= 0:
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


depsgraph_lock = False
@persistent
def protect_doodad_mesh(_):
    depsgraph = bpy.context.view_layer.depsgraph
    global depsgraph_lock
    delete = False
    is_duplicated = False

    if depsgraph_lock:
        return

    for update in depsgraph.updates:

        if isinstance(update.id, bpy.types.Object) and update.id.type == 'MESH' and update.id.wow_wmo_doodad.enabled:
            depsgraph_lock = True
            obj = bpy.data.objects[update.id.name]

            for i, mat in enumerate(obj.data.materials):
                if mat.users > 1:
                    mat = mat.copy()
                    obj.data.materials[i] = mat

                    is_duplicated = True

                    for j in range(3):
                        mat.node_tree.animation_data.drivers[j].driver.variables[0].targets[0].id = obj

            if is_duplicated:
                continue

            if obj.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')

            if len(obj.modifiers):
                obj.modifiers.clear()

            if update.is_updated_geometry:
                delete = True
                bpy.data.objects.remove(obj, do_unlink=True)


    if delete:
        show_message_box('One or more doodads were deleted due to mesh changes. Editing doodads is not allowed.'
                         , "WoW Blender Studio Error"
                         , icon='ERROR')

    depsgraph_lock = False

def register():
    bpy.n_scene_objects = 0
    bpy.app.handlers.depsgraph_update_post.append(sync_wmo_root_components_collections)
    bpy.app.handlers.depsgraph_update_pre.append(protect_doodad_mesh)


def unregister():
    bpy.app.handlers.depsgraph_update_pre.remove(protect_doodad_mesh)
    bpy.app.handlers.depsgraph_update_post.remove(sync_wmo_root_components_collections)

