import bpy

from functools import partial

from bpy.app.handlers import persistent
from ..render import BlenderWMOObjectRenderFlags
from ...utils.misc import show_message_box

class DepsgraphLock:
    def __enter__(self):
        global DEPSGRAPH_UPDATE_LOCK
        DEPSGRAPH_UPDATE_LOCK = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        global DEPSGRAPH_UPDATE_LOCK
        DEPSGRAPH_UPDATE_LOCK = False

_obj_props = (
              ('wow_wmo_group', 'groups'),
              ('wow_wmo_portal', 'portals'),
              ('wow_wmo_fog', 'fogs'),
              ('wow_wmo_light', 'lights'),
              ('wow_wmo_doodad_set', 'doodad_sets'),
              ('wow_wmo_doodad', 'doodads')
             )


def _remove_col_items(scene, col_name):
    col = getattr(scene.wow_wmo_root_elements, col_name)
    for i, obj in enumerate(col):
        if obj.pointer and obj.pointer.name not in scene.objects:
            col.remove(i)
            break
    else:
        return

    _remove_col_items(scene, col_name)


def _remove_col_items_doodads(scene):
    col = scene.wow_wmo_root_elements.doodad_sets

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
                    for d_set in scene.wow_wmo_root_elements.doodad_sets:
                        index = d_set.doodads.find(obj.name)

                        if index >= 0:
                            # check if doodad is parented to the correct set
                            if obj.parent != d_set.pointer:
                                obj.parent = d_set.pointer
                            break

                    else:
                        # attempt adding to active doodad set
                        if len(scene.wow_wmo_root_elements.doodad_sets):
                            cur_set_index = scene.wow_wmo_root_elements.cur_doodad_set
                            act_set = scene.wow_wmo_root_elements.doodad_sets[cur_set_index]
                            slot = act_set.doodads.add()
                            slot.pointer = obj

                        else:
                            bpy.data.objects.remove(obj, do_unlink=True)

                else:
                    continue

            elif prop_group.enabled:

                col = getattr(scene.wow_wmo_root_elements, col_name)

                if col.find(obj.name) < 0:
                    prop_group.enabled = False
                    slot = col.add()
                    slot.pointer = obj

def _liquid_edit_mode_timer(context):
    bpy.ops.wow.liquid_edit_mode(context, 'INVOKE_DEFAULT')

DEPSGRAPH_UPDATE_LOCK = False

banned_ops = (
    "OBJECT_OT_transform_apply",
    "OBJECT_OT_transforms_to_deltas",
    "OBJECT_OT_origin_set",
    "TRANSFORM_OT_mirror",
    "OBJECT_OT_visual_transform_apply"
)

liquid_banned_ops_edit_mode = (
    "TRANSFORM_OT_mirror",
    "MESH_OT_delete",
    "MESH_OT_duplicate_move",
    "MESH_OT_extrude_region",
    "MESH_OT_extrude_verts_indiv",
    "MESH_OT_split",
    "MESH_OT_symmetrize",
    "MESH_OT_sort_elements",
    "MESH_OT_delete_loose",
    "MESH_OT_decimate",
    "MESH_OT_dissolve_degenerate",
    "MESH_OT_dissolve_limited",
    "MESH_OT_face_make_planar",
    "MESH_OT_face_make_planar",
    "MESH_OT_vert_connect_nonplanar",
    "MESH_OT_vert_connect_concave",
    "MESH_OT_bevel",
    "MESH_OT_merge"
)

wmo_render_flag_map = {
    'Lightmap': BlenderWMOObjectRenderFlags.HasLightmap,
    'BatchmapInt': BlenderWMOObjectRenderFlags.HasBatchB,
    'BatchmapTrans': BlenderWMOObjectRenderFlags.HasBatchA,
    'Blendmap': BlenderWMOObjectRenderFlags.HasBlendmap
}

@persistent
def on_depsgraph_update(_):
    global DEPSGRAPH_UPDATE_LOCK
    if DEPSGRAPH_UPDATE_LOCK:
        return

    delete = False
    is_duplicated = False

    for update in bpy.context.view_layer.depsgraph.updates:

        try:
            if isinstance(update.id, bpy.types.Object) and update.id.type == 'MESH':
                if update.id.wow_wmo_doodad.enabled:
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
                    if bpy.context.window_manager.operators \
                    and bpy.context.window_manager.operators[-1].bl_idname in banned_ops:
                        delete = True
                        bpy.data.objects.remove(obj, do_unlink=True)

                    if update.is_updated_transform:
                        # check if object is scaled evenly
                        max_scale = 0.0
                        for j in range(3):
                            if obj.scale[j] > max_scale:
                                max_scale = obj.scale[j]

                        obj.scale = (max_scale, max_scale, max_scale)

                elif update.id.wow_wmo_liquid.enabled:
                    obj = bpy.data.objects[update.id.name, update.id.library]

                    with DepsgraphLock():
                        if obj.mode == 'EDIT':
                            win = bpy.context.window
                            scr = win.screen
                            areas3d = [area for area in scr.areas if area.type == 'VIEW_3D']
                            region = [region for region in areas3d[0].regions if region.type == 'WINDOW']
                            space = [space for space in areas3d[0].regions if space.type == 'VIEW_3D']

                            override = {'window': win,
                                        'screen': scr,
                                        'area': areas3d[0],
                                        'region': region,
                                        'scene': bpy.context.scene,
                                        'workspace': bpy.context.workspace,
                                        'space_data': space
                                        }

                            # we need a timer here to prevent operator recognizing tab event as exit
                            bpy.app.timers.register(partial(_liquid_edit_mode_timer, override), first_interval=0.1)

                        # enforce object mode or sculpt mode
                        elif obj.mode not in ('OBJECT', 'SCULPT'):
                            bpy.context.view_layer.objects.active = obj
                            bpy.ops.object.mode_set(mode='OBJECT')


                        # enforce Z plane for sculpting brushes
                        if obj.mode == 'SCULPT':
                            for brush in bpy.data.brushes:
                                brush.sculpt_plane = 'Z'

                        obj.scale = (1, 1, 1)
                        obj.rotation_mode = 'XYZ'
                        obj.rotation_euler = (0, 0, 0)

                        # remove modifiers
                        if len(obj.modifiers):
                            obj.modifiers.clear()

                elif update.id.wow_wmo_fog.enabled:
                    obj = bpy.data.objects[update.id.name, update.id.library]

                    with DepsgraphLock():
                        # enforce object mode
                        if obj.mode != 'OBJECT':
                            bpy.context.view_layer.objects.active = obj
                            bpy.ops.object.mode_set(mode='OBJECT')

                elif update.id.wow_wmo_group.enabled:
                    obj = bpy.data.objects[update.id.name, update.id.library]
                    mesh = obj.data

                    for col_name, flag in wmo_render_flag_map.items():
                        col = mesh.vertex_colors.get(col_name)

                        if col:
                            obj.pass_index |= flag
                        else:
                            obj.pass_index &= ~flag


            elif isinstance(update.id, bpy.types.Scene):

                # sync collection active items
                act_obj = bpy.context.view_layer.objects.active

                root_comps = bpy.context.scene.wow_wmo_root_elements
                if act_obj:
                    if act_obj.wow_wmo_group.enabled:
                        slot_idx = root_comps.groups.find(act_obj.name)
                        root_comps.cur_group = slot_idx

                    elif act_obj.wow_wmo_fog.enabled:
                        slot_idx = root_comps.fogs.find(act_obj.name)
                        root_comps.cur_fog = slot_idx

                    elif act_obj.wow_wmo_light.enabled:
                        slot_idx = root_comps.lights.find(act_obj.name)
                        root_comps.cur_light = slot_idx

                    elif act_obj.wow_wmo_portal.enabled:
                        slot_idx = root_comps.portals.find(act_obj.name)
                        root_comps.cur_portal = slot_idx

                    elif act_obj.wow_wmo_doodad.enabled:
                        d_set = root_comps.doodad_sets[root_comps.cur_doodad_set]

                        if d_set.pointer:
                            slot_idx = d_set.doodads.find(act_obj.name)

                            if slot_idx >= 0:
                                d_set.cur_doodad = slot_idx

                # fill collections
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
    bpy.types.Object.wow_subject_to_removal = bpy.props.BoolProperty(default=False)
    bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update)


def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(on_depsgraph_update)
    del bpy.wbs_n_scene_objects
    del bpy.types.Object.wow_subject_to_removal

