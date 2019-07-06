import math
import operator
import os
import struct
import subprocess
import traceback

import bpy
import bmesh
import mathutils


from mathutils import Vector
from math import cos, sin, tan, radians

from .enums import *
from .panels.toolbar import switch_doodad_set, get_doodad_sets
from . import handlers
from ..render import load_wmo_shader_dependencies, update_wmo_mat_node_tree
from ..utils.fogs import create_fog_object
from ..utils.doodads import import_doodad_model, import_doodad
from ..utils.wmv import wmv_get_last_wmo, wmv_get_last_m2
from ...ui import get_addon_prefs
from ...utils.misc import load_game_data


###############################
## WMO operators
###############################

class WMO_OT_destroy_property(bpy.types.Operator):
    bl_idname = "scene.wow_wmo_destroy_wow_property"
    bl_label = "Disable Property"
    bl_options = {'UNDO', 'REGISTER', 'INTERNAL'}

    prop_group:  bpy.props.StringProperty()

    prop_map = {
        'wow_wmo_group': 'groups',
        'wow_wmo_light': 'lights',
        'wow_wmo_material': 'materials',
        'wow_wmo_fog': 'fogs',
        'wow_wmo_portal': 'portals',
        'wow_wmo_doodad': 'doodads'
    }

    @classmethod
    def poll(cls, context):
        return context.scene.wow_scene.type == 'WMO' and hasattr(context, 'object') and context.object

    def execute(self, context):

        getattr(context.object, self.prop_group).enabled = False

        col = getattr(bpy.context.scene.wow_wmo_root_components, self.prop_map[self.prop_group])

        idx = col.find(context.object.name)

        if idx >= 0:
            col.remove(idx)
            bpy.context.scene.wow_wmo_root_components.is_update_critical = True

        return {'FINISHED'}


class WMO_OT_generate_materials(bpy.types.Operator):
    bl_idname = "scene.wow_wmo_generate_materials"
    bl_label = "Generate WMO Textures"
    bl_description = "Generate WMO materials."
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.scene.wow_scene.type == 'WMO'

    def execute(self, context):
        load_wmo_shader_dependencies(True)
        for mat in bpy.data.materials:
            update_wmo_mat_node_tree(mat)

        return {'FINISHED'}


class WMO_OT_reload_textures_from_cache(bpy.types.Operator):
    bl_idname = "scene.wow_wmo_reload_textures_from_cache"
    bl_label = "Reload WMO textures"
    bl_description = "Reload textures from WoW cache."
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.scene.wow_scene.type == 'WMO'

    def execute(self, context):

        game_data = load_game_data()
        addon_prefs = get_addon_prefs()
        texture_dir = addon_prefs.cache_dir_path

        for material in bpy.data.materials:
            if not material.wow_wmo_material.enabled:
                continue

            for tex_slot in material.texture_slots:

                if tex_slot and tex_slot.texture and tex_slot.texture.type == 'IMAGE':
                    game_data.extract_textures_as_png(texture_dir, [material.wow_wmo_material.texture1])

                    image = bpy.data.images.load(
                        os.path.join(texture_dir, os.path.splitext(material.wow_wmo_material.texture1)[0] + '.png'),
                        check_existing=True)
                    tex_slot.texture.image = image
                    tex_slot.texture.image.gl_load()
                    tex_slot.texture.image.update()

        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return {'FINISHED'}


class WMO_OT_fix_material_duplicates(bpy.types.Operator):
    bl_idname = "scene.wow_fix_material_duplicates"
    bl_label = "Fix material duplicates"
    bl_description = "Fix duplicated materials in WMO groups."
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        material_duplicates = {}

        get_attributes = operator.attrgetter(
            'Shader', 'TerrainType', 'BlendingMode',
            'Texture1', 'EmissiveColor', 'Flags',
            'Texture2', 'DiffColor')

        for material in bpy.data.materials:

            name = material.name.split('.png')[0]
            if '.png' in material.name:
                name += '.png'
            material_duplicates.setdefault(name, []).append(material.name)

        duplicate_count = 0
        for source, duplicates in material_duplicates.items():
            source_props = bpy.data.materials[source].wow_wmo_material

            for duplicate in duplicates:
                dupli_props = bpy.data.materials[duplicate].wow_wmo_material
                if source != duplicate \
                and source_props.Shader == dupli_props.Shader \
                and source_props.TerrainType == dupli_props.TerrainType \
                and source_props.BlendingMode == dupli_props.BlendingMode \
                and source_props.Texture1 == dupli_props.Texture1 \
                and source_props.EmissiveColor[:] == dupli_props.EmissiveColor[:] \
                and source_props.Flags == dupli_props.Flags \
                and source_props.Texture2 == dupli_props.Texture2 \
                and source_props.DiffColor[:] == dupli_props.DiffColor[:]:
                    bpy.ops.view3d.replace_material(matorg=duplicate, matrep=source)
                    duplicate_count += 1

        self.report({'INFO'}, "Cleared {} duplicated materials".format(duplicate_count))

        return {'FINISHED'}


class WMO_OT_import_adt_scene(bpy.types.Operator):
    bl_idname = "scene.wow_import_adt_scene"
    bl_label = "Import M2s and WMOs from ADT"
    bl_description = "Import M2s and WMOs from ADT"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        return True

    dir_path:  bpy.props.StringProperty(
        name="",
        description="Choose a directory with ADTs:",
        default="",
        maxlen=1024,
        subtype='DIR_PATH')

    doodads_on:  bpy.props.BoolProperty(
        name="As doodads",
        description="Import M2 models as doodads",
        default=True
    )

    group_objects:  bpy.props.BoolProperty(
        name="Group objects",
        description="Add imported objects to a new group",
        default=True
    )

    move_to_center:  bpy.props.BoolProperty(
        name="Move to center",
        description="Move imported objects to center of coordinates",
        default=True
    )

    def execute(self, context):

        game_data = load_game_data()

        if not game_data or not game_data.files:
            self.report({'ERROR'}, "Failed to import model. Connect to game client first.")
            return {'CANCELLED'}

        addon_prefs = get_addon_prefs()

        dir = bpy.path.abspath(self.dir_path)
        if not dir:
            return {'FINISHED'}

        fileinfo_path = addon_prefs.fileinfo_path

        instance_cache = {}
        uid_cache = set()

        group_name = None
        if self.group_objects:
            i = 0
            while True:
                name = "ADTImport_" + str(i)
                if name not in bpy.context.scene.objects:
                    group_name = name
                    break
                i += 1

            bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
            parent = bpy.context.view_layer.objects.active
            parent.name = group_name

        for filename in os.listdir(dir):

            m2_paths = []
            wmo_paths = []

            m2_instances = {}
            wmo_instances = {}

            if filename.endswith(".adt"):
                filepath = os.path.join(dir, filename)
                subprocess.call([fileinfo_path, filepath])

                with open(os.path.splitext(filepath)[0] + ".txt", 'r') as f:

                    cur_chunk = ""
                    for line in f.readlines():
                        parsed_line = line.replace('\t', ' ')
                        data = parsed_line.split()

                        if not data:
                            continue

                        if data[0] in {'MMDX', 'MWMO', 'MDDF', 'MODF'}:
                            cur_chunk = data[0]
                        else:
                            if cur_chunk == 'MMDX':

                                m2_path = data[1]
                                i = 2
                                while not m2_path.endswith(".m2"):
                                    m2_path += " {}".format(data[i])
                                    i += 1

                                m2_paths.append(m2_path)

                            elif cur_chunk == 'MWMO':

                                wmo_path = data[1]
                                i = 2
                                while not wmo_path.endswith(".wmo"):
                                    wmo_path += " {}".format(data[i])
                                    i += 1

                                wmo_paths.append(wmo_path)

                            elif cur_chunk == 'MDDF':
                                entry = data[2:]
                                entry.insert(0, data[0])
                                m2_instances[data[1]] = entry
                            elif cur_chunk == 'MODF':
                                entry = data[2:]
                                entry.insert(0, data[0])
                                wmo_instances[data[1]] = entry

            # import M2s
            for uid, instance in m2_instances.items():

                if uid in uid_cache:
                    continue
                uid_cache.add(uid)

                doodad_path = m2_paths[int(instance[0])]
                cached_obj = instance_cache.get(doodad_path)

                if cached_obj:
                    obj = cached_obj.copy()
                    obj.data = cached_obj.data.copy()
                    bpy.context.collection.objects.link(obj)

                else:
                    proto_scene = (bpy.data.scenes.get('$WMODoodadPrototypes') or bpy.data.scenes.new(
                        name='$WMODoodadPrototypes'))
                    try:
                        obj = import_doodad_model(addon_prefs.cache_dir_path, doodad_path, proto_scene)
                    except:
                        bpy.ops.mesh.primitive_cube_add()
                        obj = bpy.context.view_layer.objects.active
                        obj.name = 'ERR_' + os.path.splitext(os.path.basename(doodad_path))[0]
                        traceback.print_exc()
                        print("\nFailed to import model: <<{}>>. Placeholder is imported instead.".format(doodad_path))

                    instance_cache[doodad_path] = obj

                obj.name += ".m2"
                obj.location = ((-float(instance[1])), (float(instance[3])), float(instance[2]))
                obj.rotation_euler = (math.radians(float(instance[6])),
                                      math.radians(float(instance[4])),
                                      math.radians(float(instance[5]) + 90))
                obj.scale = tuple((float(instance[7]) / 1024.0 for _ in range(3)))

                if self.doodads_on:
                    obj.wow_wmo_doodad.enabled = True
                    obj.wow_wmo_doodad.path = doodad_path

                if self.group_objects:
                    obj.parent = parent

            # import WMOs
            from .. import import_wmo
            for uid, instance in wmo_instances.items():

                if uid in uid_cache:
                    continue
                uid_cache.add(uid)

                wmo_path = wmo_paths[int(instance[0])]

                if os.name != 'nt':
                    wmo_path = wmo_path.replace('\\', '/')

                cached_obj = instance_cache.get(wmo_path)

                if not cached_obj:
                    try:
                        game_data.extract_file(dir, wmo_path)
                        root_path = os.path.join(dir, wmo_path)

                        with open(root_path, 'rb') as f:
                            f.seek(24)
                            n_groups = struct.unpack('I', f.read(4))[0]

                        group_paths = ["{}_{}.wmo".format(wmo_path[:-4], str(i).zfill(3)) for i in range(n_groups)]

                        game_data.extract_files(dir, group_paths)

                        obj = import_wmo.import_wmo_to_blender_scene(root_path, True, True, True)

                        # clean up unnecessary files and directories
                        os.remove(root_path)
                        for group_path in group_paths:
                            os.remove(os.path.join(dir, group_path))

                    except:
                        bpy.ops.mesh.primitive_cube_add()
                        obj = bpy.context.view_layer.objects.active
                        obj.name = os.path.basename(wmo_path) + ".wmo"
                        traceback.print_exc()
                        print("\nFailed to import model: <<{}>>. Placeholder is imported instead.".format(wmo_path))

                    instance_cache[wmo_path] = obj

                else:
                    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
                    obj = bpy.context.view_layer.objects.active
                    obj.name = os.path.basename(wmo_path) + ".wmo"

                    for child in cached_obj.children:
                        nobj = child.copy()
                        if nobj.data:
                            nobj.data = child.data.copy()
                        bpy.context.collection.objects.link(nobj)

                        nobj.parent = obj

                obj.location = ((-float(instance[1])), (float(instance[3])), float(instance[2]))
                obj.rotation_euler = (math.radians(float(instance[6])),
                                      math.radians(float(instance[4])),
                                      math.radians(float(instance[5]) + 90))

                if self.group_objects:
                    obj.parent = parent

        if self.move_to_center:
            selected = bpy.context.selected_objects
            bpy.ops.object.select_all(action='DESELECT')

            for obj in parent.children:
                obj.select_set(True)

            bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')
            bpy.ops.view3d.snap_cursor_to_selected()

            bpy.ops.transform.translate(value=tuple(-x for x in bpy.context.space_data.cursor.location))

            bpy.ops.object.select_all(action='DESELECT')

            for obj in selected:
                obj.select_set(True)

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class WMO_OT_import_last_wmo_from_wmv(bpy.types.Operator):
    bl_idname = "scene.wow_import_last_wmo_from_wmv"
    bl_label = "Load last WMO from WMV"
    bl_description = "Load last WMO from WMV"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):

        game_data = load_game_data()

        if not game_data or not game_data.files:
            self.report({'ERROR'}, "Failed to import model. Connect to game client first.")
            return {'CANCELLED'}

        addon_prefs = get_addon_prefs()
        cache_dir = addon_prefs.cache_dir_path

        wmo_path = wmv_get_last_wmo()

        if not wmo_path:
            self.report({'ERROR'}, """WoW Model Viewer log contains no WMO entries.
            Make sure to use compatible WMV version or open a .wmo there.""")
            return {'CANCELLED'}

        try:
            game_data.extract_file(cache_dir, wmo_path)

            if os.name != 'nt':
                root_path = os.path.join(cache_dir, wmo_path.replace('\\', '/'))
            else:
                root_path = os.path.join(cache_dir, wmo_path)

            with open(root_path, 'rb') as f:
                f.seek(24)
                n_groups = struct.unpack('I', f.read(4))[0]

            group_paths = ["{}_{}.wmo".format(wmo_path[:-4], str(i).zfill(3)) for i in range(n_groups)]

            game_data.extract_files(cache_dir, group_paths)

            from .. import import_wmo
            obj = import_wmo.import_wmo_to_blender_scene(root_path, True, True, True, True)

            # clean up unnecessary files and directories
            os.remove(root_path)
            for group_path in group_paths:
                os.remove(os.path.join(cache_dir, *group_path.split('\\')))

        except:
            traceback.print_exc()
            self.report({'ERROR'}, "Failed to import model.")
            return {'CANCELLED'}

        self.report({'INFO'}, "Done importing WMO object to scene.")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    class WMO_OT_wmv_import_doodad(bpy.types.Operator):
        bl_idname = 'scene.wow_wmo_import_doodad_from_wmv'
        bl_label = 'Import last M2 from WMV'
        bl_description = 'Import last M2 from WoW Model Viewer'
        bl_options = {'REGISTER', 'UNDO'}

        def execute(self, context):

            m2_path = wmv_get_last_m2()
            cache_path = get_addon_prefs().cache_dir_path

            root = context.scene.wow_wmo_root_components

            if not len(root.doodad_sets) or len(root.doodad_sets) < root.cur_doodad_set:
                self.report({'ERROR'}, "Failed to import doodad. No active doodad set is selected.")
                return {'CANCELLED'}

            doodad_set_obj = root.doodad_sets[root.cur_doodad_set].pointer

            if not m2_path:
                self.report({'ERROR'}, "WoW Model Viewer log contains no model entries."
                                       "Make sure to use compatible WMV version or open an .m2 there.")
                return {'CANCELLED'}

            obj = import_doodad(m2_path, cache_path)
            obj.parent = doodad_set_obj
            bpy.context.collection.objects.link(obj)

            return {'FINISHED'}


###############################
## Doodad operators
###############################

class WMO_OT_wmv_import_doodad_from_wmv(bpy.types.Operator):
    bl_idname = 'scene.wow_wmo_import_doodad_from_wmv'
    bl_label = 'Import last M2 from WMV'
    bl_description = 'Import last M2 from WoW Model Viewer'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        m2_path = wmv_get_last_m2()
        cache_path = get_addon_prefs().cache_dir_path

        root = context.scene.wow_wmo_root_components

        if not len(root.doodad_sets) or len(root.doodad_sets) < root.cur_doodad_set:
            self.report({'ERROR'}, "Failed to import doodad. No active doodad set is selected.")
            return {'CANCELLED'}

        doodad_set_obj = root.doodad_sets[root.cur_doodad_set].pointer

        if not m2_path:
            self.report({'ERROR'}, "WoW Model Viewer log contains no model entries."
                                   "Make sure to use compatible WMV version or open an .m2 there.")
            return {'CANCELLED'}

        obj = import_doodad(m2_path, cache_path)
        obj.parent = doodad_set_obj
        bpy.context.collection.objects.link(obj)

        return {'FINISHED'}

class WMO_OT_doodads_bake_color(bpy.types.Operator):
    bl_idname = "scene.wow_doodads_bake_color"
    bl_label = "Bake doodads color"
    bl_description = "Bake doodads colors from nearby vertex color values"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        return True

    tree_map = {}

    @staticmethod
    def find_nearest_object(obj_, objects):
        """Get closest object to another object"""

        dist = 32767
        result = None
        for obj in objects:
            obj_location_relative = obj.matrix_world.inverted() @ obj_.location
            hit = obj.closest_point_on_mesh(obj_location_relative)
            hit_dist = (obj_location_relative - hit[1]).length
            if hit_dist < dist:
                dist = hit_dist
                result = obj

        return result

    @staticmethod
    def get_object_radius(obj):
        corner_min = [32767, 32767, 32767]
        corner_max = [0, 0, 0]

        mesh = obj.data

        for vertex in mesh.vertices:
            for i in range(3):
                corner_min[i] = min(corner_min[i], vertex.co[i])
                corner_max[i] = max(corner_max[i], vertex.co[i])
        result = (mathutils.Vector(corner_min) - mathutils.Vector(corner_max))
        return (abs(result.x) + abs(result.y) + abs(result.z)) / 3

    def gen_doodad_color(self, obj, group):

        mesh = group.data

        if not mesh.vertex_colors:
            return 0.5, 0.5, 0.5, 1.0

        radius = self.get_object_radius(obj)
        colors = []

        kd_tree = self.tree_map.get(group.name)
        if not kd_tree:
            kd_tree = mathutils.kdtree.KDTree(len(mesh.polygons))

            for index, poly in enumerate(mesh.polygons):
                kd_tree.insert(group.matrix_world @ poly.center, index)

            kd_tree.balance()
            self.tree_map[group.name] = kd_tree

        polygons = kd_tree.find_range(obj.location, radius)

        if not polygons:
            polygons.append(kd_tree.find(obj.location))

        for poly in polygons:
            for loop_index in mesh.polygons[poly[1]].loop_indices:
                colors.append(mesh.vertex_colors[mesh.vertex_colors.active_index].data[loop_index].color)

        if not colors:
            return 0.5, 0.5, 0.5, 1.0

        final_color = mathutils.Vector((0x00, 0x00, 0x00))
        for color in colors:
            final_color += mathutils.Vector(color)

        return tuple(final_color / len(colors)) + (1.0,)

    def execute(self, context):

        window_manager = context.window_manager
        doodad_counter = 0
        len_objects = len(bpy.context.selected_objects)

        groups = [obj for obj in bpy.context.scene.objects if obj.wow_wmo_group.enabled]

        window_manager.progress_begin(0, 100)
        for index, obj in enumerate(bpy.context.selected_objects):
            if obj.wow_wmo_doodad.enabled:
                obj.color = self.gen_doodad_color(obj, self.find_nearest_object(obj, groups))
                print("\nBaking color to doodad instance <<{}>>".format(obj.name))
                doodad_counter += 1
                window_manager.progress_update(int(index / len_objects * 100))

        window_manager.progress_end()

        if doodad_counter:
            self.report({'INFO'}, "Done baking colors to {} doodad instances.".format(doodad_counter))
        else:
            self.report({'ERROR'}, "No doodad instances found among selected objects.")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class WMO_OT_doodadset_add(bpy.types.Operator):
    bl_idname = 'scene.wow_doodad_set_add'
    bl_label = 'Add doodad set'
    bl_description = 'Add models to doodadset'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    Action:  bpy.props.EnumProperty(
        name="Operator action",
        description="Choose operator action",
        items=[
            ("ADD", "Add to existing set", "", 'PLUGIN', 0),
            ("CUSTOM", "Create new set", "", 'ADD', 1),
            ("GLOBAL", "Create new global set", "", 'WORLD', 2),
        ]
    )

    Set:  bpy.props.EnumProperty(
        name="",
        description="Select doodad set",
        items=get_doodad_sets,
        update=switch_doodad_set
    )

    Name:  bpy.props.StringProperty(
        name=""
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        col.label(text="Action")
        col.prop(self, "Action", expand=True)

        if self.Action == "ADD":
            text = "Select set:"
            col.label(text=text)
            col.prop(self, "Set")
        elif self.Action == "CUSTOM":
            text = "Enter set name:"
            col.label(text=text)
            col.prop(self, "Name")

    def execute(self, context):

        selected_objs = []
        for obj in bpy.context.scene.objects:
            if obj.select_get() and obj.wow_wmo_doodad.enabled:
                selected_objs.append(obj)

        if self.Action == "ADD":
            if self.Set != "None":
                for obj in selected_objs:
                    obj.parent = bpy.context.scene.objects[self.Set]

                self.report({'INFO'}, "Successfully added doodads to doodad set")

            else:
                self.report({'WARNING'}, "Select a doodad set to link objects to first")

        elif self.Action == "CUSTOM":
            if self.Name:
                bpy.ops.object.empty_add(type='SPHERE', location=(0, 0, 0))
                obj = bpy.context.view_layer.objects.active
                obj.name = self.Name
                obj.hide_viewport = True
                obj.hide_select = True
                obj.lock_location = (True, True, True)
                obj.lock_rotation = (True, True, True)
                obj.lock_scale = (True, True, True)

                for object in selected_objs:
                    object.parent = obj

                self.report({'INFO'}, "Successfully created new doodadset and added doodads to it")

            else:
                self.report({'WARNING'}, "Enter name of the doodadset")

        elif self.Action == "GLOBAL":
            if not bpy.context.scene.objects.get("Set_$DefaultGlobal"):
                bpy.ops.object.empty_add(type='SPHERE', location=(0, 0, 0))
                obj = bpy.context.view_layer.objects.active
                obj.name = "Set_$DefaultGlobal"
                obj.hide_viewport = True
                obj.hide_select = True
                obj.lock_location = (True, True, True)
                obj.lock_rotation = (True, True, True)
                obj.lock_scale = (True, True, True)

                for object in selected_objs:
                    object.parent = obj

                self.report({'INFO'}, "Successfully created global doodadset and added doodads to it")

            else:
                self.report({'WARNING'}, "There can only be one global doodadset")

        switch_doodad_set(bpy.context.scene, None)

        return {'FINISHED'}

class WMO_OT_doodadset_color(bpy.types.Operator):
    bl_idname = 'scene.wow_doodad_set_color'
    bl_label = 'Set Doodad Color'
    bl_description = "Set color to selected doodads"
    bl_options = {'REGISTER', 'UNDO'}

    Color:  bpy.props.FloatVectorProperty(
        name='Color',
        description='Color applied to doodads',
        subtype='COLOR',
        size=4
    )

    def draw(self, context):
        self.layout.column().prop(self, "Color")

    def execute(self, context):

        if not bpy.context.selected_objects:
            self.report({'ERROR'}, "No objects selected.")
            return {'FINISHED'}

        success = False
        for obj in bpy.context.selected_objects:
            if obj.wow_wmo_doodad.enabled:
                obj.wow_wmo_doodad.color = self.Color
                success = True

        if success:
            self.report({'INFO'}, "Successfully assigned color to selected doodads.")
        else:
            self.report({'ERROR'}, "No doodads found among selected objects.")

        return {'FINISHED'}


class WMO_OT_doodadset_template_action(bpy.types.Operator):
    bl_idname = 'scene.wow_doodad_set_template_action'
    bl_label = 'Template action'
    bl_description = 'Apply an action to all instances of selected object on the scene'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    Action:  bpy.props.EnumProperty(
        items=[
            ('SELECT', "Select", "Rotate all instances of selected doodads", 'PMARKER_ACT', 0),
            ('REPLACE', "Replace", "Replace all instances of selected doodads with last M2 from WMV", 'FILE_REFRESH', 1),
            ('RESIZE', "Resize", "Resize all instances of selected doodads", 'FULLSCREEN_ENTER', 2),
            ('DELETE', "Delete", "Delete all instances of selected doodads", 'CANCEL', 3),
            ('ROTATE', "Rotate", "Rotate all instances of selected doodads", 'LOOP_FORWARDS', 4)],
        default='SELECT'
    )

    Scale:  bpy.props.FloatProperty(
        name="Scale",
        description="Scale applied to doodads",
        min=0.01,
        max=20,
        default=1
    )

    Rotation:  bpy.props.FloatVectorProperty(
        name="Rotation",
        default=(0, 0, 0, 0),
        size=4
    )

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        col = self.layout.column()

        col.prop(self, "Action", expand=True)

        if self.Action == 'RESIZE':
            col.prop(self, "Scale")
        elif self.Action == 'ROTATE':
            col.prop(self, "Rotation")

    def execute(self, context):

        target = None
        active = bpy.context.view_layer.objects.active

        if active and active.wow_wmo_doodad:
            target = active.wow_wmo_doodad.path
        else:
            self.report({'ERROR'}, "Template functions require an active object.")
            return {'CANCELLED'}

        selected_only = False
        if len(bpy.context.selected_objects) > 1:
            selected_only = True

        selected_objects = bpy.context.selected_objects.copy()
        objects_to_select = []

        success = False

        if target:

            new_obj = None

            if self.Action == 'REPLACE':
                if not bpy.data.is_saved:
                    self.report({'ERROR'}, "Saved your blendfile first.")
                    return {'FINISHED'}

                if not hasattr(bpy, "wow_game_data"):
                    self.report({'ERROR'}, "Connect to game data first.")
                    return {'FINISHED'}

                bpy.ops.scene.wow_wmo_import_doodad_from_wmv()
                new_obj = bpy.context.view_layer.objects.active

            for obj in bpy.context.scene.objects:
                is_selected = obj in selected_objects if selected_only else True

                if obj.wow_wmo_doodad.path == target and is_selected:

                    if self.Action == 'REPLACE':

                        location = obj.location
                        rotation = obj.rotation_quaternion
                        scale = obj.scale
                        parent = obj.parent
                        color = obj.wow_wmo_doodad.color
                        flags = obj.wow_wmo_doodad.flags

                        bpy.data.objects.remove(obj, do_unlink=True)

                        obj = new_obj.copy()
                        bpy.context.collection.objects.link(obj)
                        bpy.context.view_layer.objects.active = obj

                        obj.location = location
                        obj.rotation_mode = 'QUATERNION'
                        obj.rotation_quaternion = rotation
                        obj.scale = scale
                        obj.parent = parent
                        obj.wow_wmo_doodad.color = color
                        obj.wow_wmo_doodad.flags = flags
                        objects_to_select.append(obj)

                    elif self.Action == 'RESIZE':

                        obj.scale *= self.Scale
                        obj.select_set(True)

                    elif self.Action == 'DELETE':

                        bpy.data.objects.remove(obj, do_unlink=True)

                    elif self.Action == 'ROTATE':
                        obj.rotation_mode = 'QUATERNION'
                        for i, _ in enumerate(self.Rotation):
                            obj.rotation_quaternion[i] += self.Rotation[i]

                    elif self.Action == 'SELECT':
                        obj.select_set(True)

                    success = True

                for ob in objects_to_select:
                    ob.select_set(True)

            if new_obj:
                bpy.data.objects.remove(new_obj, do_unlink=True)

            if success:
                self.report({'INFO'}, "Template action applied.")

            return {'FINISHED'}

        else:
            self.report({'ERROR'}, "No doodad is selected.")
            return {'FINISHED'}


###############################
## Water operators
###############################

class WMO_OT_add_liquid_flag(bpy.types.Operator):
    bl_idname = 'scene.wow_mliq_change_flags'
    bl_label = 'Change liquid flags'
    bl_description = 'Change WoW liquid flags'

    Action:  bpy.props.EnumProperty(
        name="",
        description="Select flag action",
        items=[("ADD", "", ""),
               ("ADD_ALL", "", ""),
               ("CLEAR", "", ""),
               ("CLEAR_ALL", "", "")
               ]
    )

    def execute(self, context):
        water = bpy.context.view_layer.objects.active
        if water.wow_wmo_liquid.enabled:
            mesh = water.data

            if self.Action == "ADD":
                for polygon in mesh.polygons:
                    if polygon.select:
                        for loop_index in polygon.loop_indices:
                            mesh.vertex_colors[mesh.vertex_colors.active_index].data[loop_index].color = (0, 0, 255)
            elif self.Action == "ADD_ALL":
                for polygon in mesh.polygons:
                    for loop_index in polygon.loop_indices:
                        mesh.vertex_colors[mesh.vertex_colors.active_index].data[loop_index].color = (0, 0, 255)
            elif self.Action == "CLEAR":
                for polygon in mesh.polygons:
                    if polygon.select:
                        for loop_index in polygon.loop_indices:
                            mesh.vertex_colors[mesh.vertex_colors.active_index].data[loop_index].color = (255, 255, 255)
            elif self.Action == "CLEAR_ALL":
                for polygon in mesh.polygons:
                    for loop_index in polygon.loop_indices:
                        mesh.vertex_colors[mesh.vertex_colors.active_index].data[loop_index].color = (255, 255, 255)

        else:
            self.report({'ERROR'}, "Selected object is not World of Warcraft liquid")

        return {'FINISHED'}



def angled_vertex(origin: Vector, pos: Vector, angle: float, orientation: float) -> float:
    return origin.z + ((pos.x - origin.x) * cos(orientation) + (pos.y - origin.y) * sin(orientation)) * tan(angle)

def get_median_point(bm: bmesh.types.BMesh) -> Vector:

    selected_vertices = [v for v in bm.verts if v.select]

    f = 1 / len(selected_vertices)

    median = Vector((0, 0, 0))

    for vert in selected_vertices:
        median += vert.co * f

    return median

def align_vertices(bm : bmesh.types.BMesh, mesh : bpy.types.Mesh, median : Vector, angle : float, orientation : float):
    for vert in bm.verts:
        if vert.select:
            vert.co[2] = angled_vertex(median, vert.co, radians(angle), radians(orientation))

    bmesh.update_edit_mesh(mesh, loop_triangles=True, destructive=True)

class WMO_OT_edit_liquid(bpy.types.Operator):
    bl_idname = "wow.liquid_edit_mode"
    bl_label = "Edit WoW Liquid"

    def __init__(self):
        self.init_loc = 0.0
        self.move_initiated = False
        self.rotation_initiated = False
        self.bm = None
        self.speed_modifier = 1.0

        self.orientation = 0.0
        self.angle = 0.0

        self.median = Vector((0, 0, 0))
        self.color_type = 'TEXTURE'

    def __del__(self):
        pass

    def modal(self, context, event):

        if context.object.mode != 'EDIT':
            return {'PASS_THROUGH'}

        mesh = context.object.data

        if event.type == 'MIDDLEMOUSE':
            return {'PASS_THROUGH'}

        if event.type in {'C', 'B', 'A', 'RIGHTMOUSE'} \
                and not self.move_initiated \
                and not self.rotation_initiated:
            return {'PASS_THROUGH'}


        elif event.type == 'G' and not self.rotation_initiated:
            self.move_initiated = True
            self.init_loc = event.mouse_x


        elif event.type == 'R' and not self.move_initiated:
            self.rotation_initiated = True
            self.median = get_median_point(self.bm)
            self.orientation = 0.0
            self.angle = 0.0


        elif event.type == 'F' and event.shift:

            median = get_median_point(self.bm)

            for vert in self.bm.verts:
                if vert.select:
                    vert.co[2] = median[2]

            bmesh.update_edit_mesh(mesh, loop_triangles=True, destructive=True)


        elif event.type == 'MOUSEMOVE':

            if self.move_initiated:
                for vert in self.bm.verts:
                    if vert.select:
                        vert.co[2] = mesh.vertices[vert.index].co[2] + (event.mouse_x - self.init_loc) / 100

                bmesh.update_edit_mesh(mesh, loop_triangles=True, destructive=True)

            return {'PASS_THROUGH'}

        elif event.type == 'WHEELUPMOUSE':

            if self.rotation_initiated:

                if event.shift:
                    self.angle = min(self.angle + 5, 89.9)
                    align_vertices(self.bm, context.object.data, self.median, self.angle, self.orientation)

                elif event.alt:
                    self.orientation += 10

                    if self.orientation > 360:
                        self.orientation -= 360

                    align_vertices(self.bm, context.object.data, self.median, self.angle, self.orientation)

            else:
                return {'PASS_THROUGH'}


        elif event.type == 'WHEELDOWNMOUSE':

            if self.rotation_initiated:
                if event.shift:
                    self.angle = max(self.angle - 5, -89.9)
                    align_vertices(self.bm, context.object.data, self.median, self.angle, self.orientation)

                elif event.alt:
                    self.orientation -= 10

                    if self.orientation < 0:
                        self.orientation = 360 - self.orientation

                    align_vertices(self.bm, context.object.data, self.median, self.angle, self.orientation)

            else:
                return {'PASS_THROUGH'}


        elif event.type in {'LEFTMOUSE', 'RIGHTMOUSE'}:  # Confirm
            self.move_initiated = False
            self.rotation_initiated = False

        elif event.type in {'ESC', 'TAB'}:  # Cancel
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.context.scene.display.shading.color_type = self.color_type
            handlers.DEPSGRAPH_UPDATE_LOCK = False
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        handlers.DEPSGRAPH_UPDATE_LOCK = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")         # force a benign select tool

        # create a bmesh to operate on
        self.bm = bmesh.from_edit_mesh(context.object.data)
        self.bm.verts.ensure_lookup_table()

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


###############################
## Object operators
###############################

class WMO_OT_bake_portal_relations(bpy.types.Operator):
    bl_idname = 'scene.wow_bake_portal_relations'
    bl_label = 'Bake portal relations'
    bl_description = 'Bake portal relations'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        def find_nearest_objects_pair(object, objects):

            pairs = []

            for obj in objects:
                hit = obj.closest_point_on_mesh(
                    obj.matrix_world.inverted() @ (object.matrix_world @ object.data.polygons[0].center))
                hit_dist = (obj.matrix_world @ hit[1] - object.matrix_world @ object.data.polygons[0].center).length
                pairs.append((obj, hit_dist))

            pairs.sort(key=lambda x: x[1])

            return pairs[0][0], pairs[1][0]

        if not bpy.context.selected_objects:
            self.report({'ERROR'}, "No objects selected.")
            return {'FINISHED'}

        success = False

        groups = tuple(x for x in bpy.context.scene.objects if x.wow_wmo_group.enabled and not x.hide_viewport)

        for obj in bpy.context.selected_objects:
            if obj.wow_wmo_portal.enabled:
                direction = find_nearest_objects_pair(obj, groups)
                obj.wow_wmo_portal.first = direction[0] if direction[0] else ""
                obj.wow_wmo_portal.second = direction[1] if direction[1] else ""
                success = True

        if success:
            self.report({'INFO'}, "Done baking portal relations.")
        else:
            self.report({'ERROR'}, "No portal objects found among selected objects.")

        return {'FINISHED'}


class WMO_OT_add_scale(bpy.types.Operator):
    bl_idname = 'scene.wow_add_scale_reference'
    bl_label = 'Add scale'
    bl_description = 'Add a WoW scale prop'
    bl_options = {'REGISTER', 'UNDO'}

    ScaleType:  bpy.props.EnumProperty(
        name="Scale Type",
        description="Select scale reference type",
        items=[('HUMAN', "Human Scale (average)", ""),
               ('TAUREN', "Tauren Scale (thickest)", ""),
               ('TROLL', "Troll Scale (tallest)", ""),
               ('GNOME', "Gnome Scale (smallest)", "")
               ],
        default='HUMAN'
    )

    def execute(self, context):
        if self.ScaleType == 'HUMAN':
            bpy.ops.object.add(type='LATTICE')
            scale_obj = bpy.context.object
            scale_obj.name = "Human Scale"
            scale_obj.dimensions = (0.582, 0.892, 1.989)

        elif self.ScaleType == 'TAUREN':
            bpy.ops.object.add(type='LATTICE')
            scale_obj = bpy.context.object
            scale_obj.name = "Tauren Scale"
            scale_obj.dimensions = (1.663, 1.539, 2.246)

        elif self.ScaleType == 'TROLL':
            bpy.ops.object.add(type='LATTICE')
            scale_obj = bpy.context.object
            scale_obj.name = "Troll Scale"
            scale_obj.dimensions = (1.116, 1.291, 2.367)

        elif self.ScaleType == 'GNOME':
            bpy.ops.object.add(type='LATTICE')
            scale_obj = bpy.context.object
            scale_obj.name = "Gnome Scale"
            scale_obj.dimensions = (0.362, 0.758, 0.991)

        self.report({'INFO'}, "Successfully added " + self.ScaleType + " scale")
        return {'FINISHED'}


class WMO_OT_add_water(bpy.types.Operator):
    bl_idname = 'scene.wow_add_water'
    bl_label = 'Add water'
    bl_description = 'Add a WoW water plane'
    bl_options = {'REGISTER', 'UNDO'}

    xPlanes:  bpy.props.IntProperty(
        name="X subdivisions:",
        description="Amount of WoW liquid planes in a row. One plane is 4.1666625 in its radius.",
        default=10,
        min=1
    )

    yPlanes:  bpy.props.IntProperty(
        name="Y subdivisions:",
        description="Amount of WoW liquid planes in a column. One plane is 4.1666625 in its radius.",
        default=10,
        min=1
    )

    def execute(self, context):
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=self.xPlanes + 1,
                                        y_subdivisions=self.yPlanes + 1,
                                        radius=4.1666625 / 2
                                        )
        water = bpy.context.view_layer.objects.active
        bpy.ops.transform.resize(value=(self.xPlanes, self.yPlanes, 1.0))

        water.name += "_Liquid"

        mesh = water.data

        bit = 1
        while bit <= 0x80:
            mesh.vertex_colors.new("flag_" + hex(bit))
            bit <<= 1

        water.wow_wmo_liquid.enabled = True

        water.hide_viewport = False if "4" in bpy.context.scene.wow_visibility else True

        self.report({'INFO'}, "Successfully сreated WoW liquid: " + water.name)
        return {'FINISHED'}


class WMO_OT_add_fog(bpy.types.Operator):
    bl_idname = 'scene.wow_add_fog'
    bl_label = 'Add fog'
    bl_description = 'Add a WoW fog object to the scene'

    def execute(self, context):

        fog = create_fog_object()

        self.report({'INFO'}, "Successfully сreated WoW fog: " + fog.name)
        return {'FINISHED'}


class WMO_OT_invert_portals(bpy.types.Operator):
    bl_idname = 'scene.wow_set_portal_dir_alg'
    bl_label = 'Set portal direction algorithm'
    bl_description = 'Set portal direction calculation algorithm.'
    bl_options = {'REGISTER', 'UNDO'}

    Algorithm:  bpy.props.EnumProperty(
        items=portal_dir_alg_enum,
        default="0"
    )

    def execute(self, context):
        success = False
        for ob in bpy.context.selected_objects:
            if ob.wow_wmo_portal.enabled:
                ob.wow_wmo_portal.algorithm = self.Algorithm
                success = True

        if success:
            self.report({'INFO'}, "Successfully inverted selected portals")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No portals found among selected objects")
            return {'CANCELLED'}


class WMO_OT_fill_textures(bpy.types.Operator):
    bl_idname = 'scene.wow_fill_textures'
    bl_label = 'Fill textures'
    bl_description = """Fill Texture 1 field of WoW materials with paths from applied image. """
    bl_options = {'REGISTER'}

    def execute(self, context):

        game_data = load_game_data()
        for ob in bpy.context.selected_objects:
            mesh = ob.data
            for material in mesh.materials:

                img = None
                for i in range(3):
                    try:
                        img = material.texture_slots[3 - i].texture.image
                    except:
                        pass

                if img and not material.wow_wmo_material.texture1:

                    path = (os.path.splitext(bpy.path.abspath(img.filepath))[0] + ".blp", "")
                    rest_path = ""

                    while True:
                        path = os.path.split(path[0])

                        if not path[1]:
                            print("\nTexture <<{}>> not found.".format(img.filepath))
                            break

                        rest_path = os.path.join(path[1], rest_path)
                        rest_path = rest_path[:-1] if rest_path.endswith('\\') else rest_path

                        if os.name != 'nt':
                            rest_path_n = rest_path.replace('/', '\\')
                        else:
                            rest_path_n = rest_path

                        rest_path_n = rest_path_n[:-1] if rest_path_n.endswith('\\') else rest_path_n

                        if game_data.has_file(rest_path_n)[0]:
                            material.wow_wmo_material.texture1 = rest_path_n
                            break

            self.report({'INFO'}, "Done filling texture paths")

        return {'FINISHED'}


class WMO_OT_quick_collision(bpy.types.Operator):
    bl_idname = 'scene.wow_quick_collision'
    bl_label = 'Generate basic collision for selected objects'
    bl_description = 'Generate WoW collision equal to geometry of the selected objects'
    bl_options = {'REGISTER', 'UNDO'}

    NodeSize:  bpy.props.IntProperty(
        name="Node max size",
        description="Max count of faces for a node in bsp tree",
        default=2500,
        min=1,
        soft_max=5000
    )

    CleanUp:  bpy.props.BoolProperty(
        name="Clean up",
        description="Remove unreferenced vertex groups",
        default=False
    )

    def execute(self, context):

        success = False
        for ob in bpy.context.selected_objects:
            if ob.wow_wmo_group.enabled:
                bpy.context.view_layer.objects.active = ob

                if self.CleanUp:
                    for vertex_group in ob.vertex_groups:
                        if vertex_group.name != ob.wow_wmo_vertex_info.vertex_group \
                                and vertex_group.name != ob.wow_wmo_vertex_info.batch_type_a \
                                and vertex_group.name != ob.wow_wmo_vertex_info.batch_type_b \
                                and vertex_group.name != ob.wow_wmo_vertex_info.lightmap \
                                and vertex_group.name != ob.wow_wmo_vertex_info.blendmap \
                                and vertex_group.name != ob.wow_wmo_vertex_info.second_uv:
                            ob.vertex_groups.remove(vertex_group)

                if ob.vertex_groups.get(ob.wow_wmo_vertex_info.vertex_group):
                    bpy.ops.object.vertex_group_set_active(group=ob.wow_wmo_vertex_info.vertex_group)
                else:
                    new_vertex_group = ob.vertex_groups.new(name="Collision")
                    bpy.ops.object.vertex_group_set_active(group=new_vertex_group.name)
                    ob.wow_wmo_vertex_info.vertex_group = new_vertex_group.name

                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.object.vertex_group_assign()
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                ob.wow_wmo_vertex_info.node_size = self.NodeSize

                success = True

        if success:
            self.report({'INFO'}, "Successfully generated automatic collision for selected WMO groups")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No WMO group objects found among selected objects")
            return {'CANCELLED'}


class WMO_OT_texface_to_material(bpy.types.Operator):
    bl_idname = 'scene.wow_texface_to_material'
    bl_label = 'Texface to material'
    bl_description = 'Generate materials out of texfaces in selected objects'

    def execute(self, context):
        if bpy.context.selected_objects[0]:
            bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
        bpy.ops.view3d.material_remove()
        bpy.ops.view3d.texface_to_material()

        self.report({'INFO'}, "Successfully generated materials from face textures")
        return {'FINISHED'}


class WMO_OT_to_wmo_portal(bpy.types.Operator):
    bl_idname = 'scene.wow_selected_objects_to_portals'
    bl_label = 'Selected objects to WMO portals'
    bl_description = 'Transfer all selected objects to WoW WMO portals'
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout
        column = layout.column()

    def execute(self, context):
        success = False
        for ob in bpy.context.selected_objects:
            if ob.type == 'MESH':
                ob.wow_wmo_group.enabled = False
                ob.wow_wmo_liquid.enabled = False
                ob.wow_wmo_fog.enabled = False
                ob.wow_wmo_portal.enabled = True

                ob.hide_viewport = False if "2" in bpy.context.scene.wow_visibility else True
                success = True

        if success:
            self.report({'INFO'}, "Successfully converted select objects to portals")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No mesh objects found among selected objects")
            return {'CANCELLED'}


class WMO_OT_to_group(bpy.types.Operator):
    bl_idname = 'scene.wow_selected_objects_to_group'
    bl_label = 'Selected objects to WMO group'
    bl_description = 'Transfer all selected objects to WoW WMO groups'
    bl_options = {'REGISTER', 'UNDO'}

    GroupName:  bpy.props.StringProperty(name="Name")
    description:  bpy.props.StringProperty(name="Description")

    place_type:  bpy.props.EnumProperty(
        items=place_type_enum,
        name="Place Type",
        description="Group is indoor or outdoor"
    )

    Flags:  bpy.props.EnumProperty(
        items=group_flag_enum,
        options={'ENUM_FLAG'}
    )

    GroupDBCid:  bpy.props.IntProperty(
        name="DBC Group ID",
        description="WMO Group ID in DBC file"
    )

    LiquidType:  bpy.props.EnumProperty(
        items=liquid_type_enum,
        name="LiquidType",
        description="Fill this WMO group with selected liquid."
    )

    def execute(self, context):

        scene = bpy.context.scene

        success = False
        for ob in bpy.context.selected_objects:
            if ob.type == 'MESH':
                ob.wow_wmo_liquid.enabled = False
                ob.wow_wmo_fog.enabled = False
                ob.wow_wmo_portal.enabled = False
                ob.wow_wmo_group.enabled = True
                ob.wow_wmo_group.place_type = self.place_type
                ob.wow_wmo_group.GroupName = self.GroupName
                ob.wow_wmo_group.description = self.description
                ob.wow_wmo_group.flags = self.Flags
                ob.wow_wmo_group.group_dbc_id = self.GroupDBCid
                ob.wow_wmo_group.liquid_type = self.LiquidType

                if self.place_type == "8" and "0" in scene.wow_visibility \
                        or self.place_type == "8192" and "1" in scene.wow_visibility:
                    ob.hide_viewport = False
                else:
                    ob.hide_viewport = True
                success = True

        if success:
            self.report({'INFO'}, "Successfully converted select objects to WMO groups")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No mesh objects found among selected objects")
            return {'CANCELLED'}


class WMO_OT_to_wow_material(bpy.types.Operator):
    bl_idname = 'scene.wow_selected_objects_to_wow_material'
    bl_label = 'Materials of selected objects to WoW Material'
    bl_description = 'Transfer all materials of selected objects to WoW material'
    bl_options = {'REGISTER', 'UNDO'}

    Flags:  bpy.props.EnumProperty(
        name="Material flags",
        description="WoW material flags",
        items=material_flag_enum,
        options={"ENUM_FLAG"}
    )

    Shader:  bpy.props.EnumProperty(
        items=shader_enum,
        name="Shader",
        description="WoW shader assigned to this material"
    )

    BlendingMode:  bpy.props.EnumProperty(
        items=blending_enum,
        name="Blending",
        description="WoW material blending mode"
    )

    Texture1:  bpy.props.StringProperty(
        name="Texture 1",
        description="Diffuse texture"
    )

    EmissiveColor:  bpy.props.FloatVectorProperty(
        name="Emissive Color",
        subtype='COLOR',
        default=(1, 1, 1, 1),
        size=4,
        min=0.0,
        max=1.0
    )

    Texture2:  bpy.props.StringProperty(
        name="Texture 2",
        description="Environment texture"
    )

    DiffColor:  bpy.props.FloatVectorProperty(
        name="Diffuse Color",
        subtype='COLOR',
        default=(1, 1, 1, 1),
        size=4,
        min=0.0,
        max=1.0
    )

    TerrainType:  bpy.props.EnumProperty(
        items=terrain_type_enum,
        name="Terrain Type",
        description="Terrain type assigned to this material. Used for producing correct footstep sounds."
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "Shader")
        col.prop(self, "TerrainType")
        col.prop(self, "BlendingMode")

        col.separator()
        col.label(text="Flags:")
        col.prop(self, "Flags")

        col.separator()
        col.prop(self, "Texture1")
        col.prop(self, "Texture2")

        layout.prop(self, "EmissiveColor")
        layout.prop(self, "DiffColor")

    def execute(self, context):
        success = False
        for ob in bpy.context.selected_objects:
            if ob.wow_wmo_group.enabled:
                for material in ob.data.materials:
                    material.wow_wmo_material.enabled = True
                    material.wow_wmo_material.shader = self.Shader
                    material.wow_wmo_material.blending_mode = self.BlendingMode
                    material.wow_wmo_material.terrain_type = self.TerrainType
                    material.wow_wmo_material.flags = self.Flags
                    material.wow_wmo_material.emissive_color = self.EmissiveColor
                    material.wow_wmo_material.diff_color = self.DiffColor
                success = True

        if success:
            self.report({'INFO'}, "Successfully enabled all materials in the selected WMO groups as WMO materials")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No WMO group objects found among selected objects")
            return {'FINISHED'}


class WMO_OT_select_entity(bpy.types.Operator):
    bl_idname = 'scene.wow_wmo_select_entity'
    bl_label = 'Select WMO entities'
    bl_description = 'Select all WMO entities of given type'
    bl_options = {'REGISTER', 'INTERNAL'}

    entity:  bpy.props.EnumProperty(
        name="Entity",
        description="Select WMO component entity objects",
        items=[
            ("Outdoor", "Outdoor", ""),
            ("Indoor", "Indoor", ""),
            ("wow_wmo_portal", "Portals", ""),
            ("wow_wmo_liquid", "Liquids", ""),
            ("wow_wmo_fog", "Fogs", ""),
            ("wow_wmo_light", "Lights", ""),
            ("wow_wmo_doodad", "Doodads", ""),
            ("Collision", "Collision", "")
        ]
    )

    def execute(self, context):

        for obj in bpy.context.scene.objects:
            if obj.hide_viewport:
                continue

            if obj.type == 'MESH':
                if obj.wow_wmo_group.enabled:
                    if self.entity == "Outdoor" and obj.wow_wmo_group.place_type == '8':
                        obj.select_set(True)
                    elif self.entity == "Indoor" and obj.wow_wmo_group.place_type == '8192':
                        obj.select_set(True)

                    if obj.wow_wmo_group.collision_mesh:
                        obj.wow_wmo_group.collision_mesh.select_set(True)

                elif self.entity not in ("wow_wmo_light", "Outdoor", "Indoor", "Collision"):
                    if getattr(obj, self.entity).enabled:
                        obj.select_set(True)

            elif obj.type == 'LIGHT' and self.entity == "wow_wmo_light":
                obj.select_set(True)

        return {'FINISHED'}

