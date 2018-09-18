import bpy
from bpy.app.handlers import persistent

__reload_order_index__ = 0

_obj_props = [('wow_wmo_group', 'groups'),
              ('wow_wmo_portal', 'portals'),
              ('wow_wmo_fog', 'fogs'),
              ('wow_wmo_light', 'lights')
             ]


@persistent
def sync_wmo_root_components_collections(scene):
    n_objs = len(scene.objects)

    if n_objs == bpy.n_scene_objects:
        return

    if n_objs < bpy.n_scene_objects:
        for i, obj in enumerate(scene.wow_wmo_root_components.groups):
            if obj.pointer and obj.pointer.name not in scene.objects:
                scene.wow_wmo_root_components.groups.remove(i)

        for i, obj in enumerate(scene.wow_wmo_root_components.portals):
            if obj.pointer and obj.pointer.name not in scene.objects:
                scene.wow_wmo_root_components.portals.remove(i)

        for i, obj in enumerate(scene.wow_wmo_root_components.fogs):
            if obj.pointer and obj.pointer.name not in scene.objects:
                scene.wow_wmo_root_components.fogs.remove(i)

        for i, obj in enumerate(scene.wow_wmo_root_components.lights):
            if obj.pointer and obj.pointer.name not in scene.objects:
                scene.wow_wmo_root_components.lights.remove(i)

    else:
        for i, obj in enumerate(scene.objects):
            for prop, col_name in _obj_props:
                col = getattr(scene.wow_wmo_root_components, col_name)
                prop_group = getattr(obj, prop)
                if prop_group.enabled and col.find(obj.name) < 0:
                    prop_group.enabled = False
                    slot = col.add()
                    slot.pointer = obj

    bpy.n_scene_objects = n_objs


def register_wmo_handlers():
    bpy.n_scene_objects = 0
    bpy.app.handlers.scene_update_post.append(sync_wmo_root_components_collections)


def unregister_wmo_handlers():
    bpy.app.handlers.scene_update_post.remove(sync_wmo_root_components_collections)

