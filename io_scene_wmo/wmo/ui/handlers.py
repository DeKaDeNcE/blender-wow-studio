import bpy
from bpy.app.handlers import persistent

__reload_order_index__ = 0

_obj_props = [('wow_wmo_group', 'groups'),
              ('wow_wmo_portal', 'portals'),
              ('wow_wmo_fog', 'fogs'),
              ('wow_wmo_light', 'lights')
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

    else:
        bpy.n_scene_objects = n_objs

        for i, obj in enumerate(scene.objects):
            for prop, col_name in _obj_props:
                col = getattr(scene.wow_wmo_root_components, col_name)
                prop_group = getattr(obj, prop)
                if prop_group.enabled and col.find(obj.name) < 0:
                    prop_group.enabled = False
                    slot = col.add()
                    slot.pointer = obj


def register_wmo_handlers():
    bpy.n_scene_objects = 0
    bpy.app.handlers.scene_update_post.append(sync_wmo_root_components_collections)


def unregister_wmo_handlers():
    bpy.app.handlers.scene_update_post.remove(sync_wmo_root_components_collections)

