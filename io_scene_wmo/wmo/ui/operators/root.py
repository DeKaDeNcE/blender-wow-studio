import bpy

from ..panels.root_elements import is_obj_unused


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

        col = getattr(bpy.context.scene.wow_wmo_root_elements, self.prop_map[self.prop_group])

        idx = col.find(context.object.name)

        if idx >= 0:
            col.remove(idx)
            bpy.context.scene.wow_wmo_root_elements.is_update_critical = True

        return {'FINISHED'}


class WMO_OT_root_elements_components_change(bpy.types.Operator):
    bl_idname = 'scene.wow_wmo_root_elements_change'
    bl_label = 'Add / Remove'
    bl_description = 'Add / Remove'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    col_name:  bpy.props.StringProperty(options={'HIDDEN'})
    cur_idx_name:  bpy.props.StringProperty(options={'HIDDEN'})
    action:  bpy.props.StringProperty(default='ADD', options={'HIDDEN'})
    add_action:  bpy.props.EnumProperty(
        items=[('EMPTY', 'Empty', ''),
               ('NEW', 'New', '')],
        default='EMPTY',
        options={'HIDDEN'}
    )

    def execute(self, context):

        if self.action == 'ADD':

            if self.col_name != 'materials' \
            and bpy.context.view_layer.objects.active \
            and bpy.context.view_layer.objects.active.mode != 'OBJECT':
                self.report({'ERROR'}, "Object mode must be active.")
                return {'CANCELLED'}

            if self.col_name == 'groups':

                obj = bpy.context.view_layer.objects.active

                if obj and obj.select_get():

                    if obj.type != 'MESH':
                        self.report({'ERROR'}, "Object must be a mesh")
                        return {'CANCELLED'}

                    if not is_obj_unused(obj):

                        if not obj.wow_wmo_group.enabled:
                            self.report({'ERROR'}, "Object is already used")
                            return {'CANCELLED'}

                        else:
                            win = bpy.context.window
                            scr = win.screen
                            areas3d = [area for area in scr.areas if area.type == 'VIEW_3D']
                            region = [region for region in areas3d[0].regions if region.type == 'WINDOW']

                            override = {'window': win,
                                        'screen': scr,
                                        'area': areas3d[0],
                                        'region': region[0],
                                        'scene': bpy.context.scene,
                                        'object': obj
                                        }

                            bpy.ops.scene.wow_wmo_destroy_wow_property(override, prop_group='wow_wmo_group')
                            self.report({'INFO'}, "Group was overriden")

                    slot = bpy.context.scene.wow_wmo_root_elements.groups.add()
                    slot.pointer = obj

                else:
                    bpy.context.scene.wow_wmo_root_elements.groups.add()

            elif self.col_name in 'portals':
                bpy.context.scene.wow_wmo_root_elements.portals.add()

            elif self.col_name == 'lights':
                slot = bpy.context.scene.wow_wmo_root_elements.lights.add()

                if self.add_action == 'NEW':
                    light = bpy.data.objects.new(name='LIGHT', object_data=bpy.data.lights.new('LIGHT', type='POINT'))
                    bpy.context.collection.objects.link(light)
                    light.location = bpy.context.scene.cursor.location
                    slot.pointer = light

            elif self.col_name == 'fogs':
                bpy.ops.scene.wow_add_fog()

            elif self.col_name == 'materials':

                slot = bpy.context.scene.wow_wmo_root_elements.materials.add()

                if self.add_action == 'NEW':
                    new_mat = bpy.data.materials.new('Material')
                    slot.pointer = new_mat

            elif self.col_name == 'doodad_sets':
                act_obj = bpy.context.view_layer.objects.active
                bpy.ops.object.empty_add(type='ARROWS', location=(0, 0,0))

                d_set = bpy.context.view_layer.objects.active
                bpy.context.view_layer.objects.active = act_obj

                d_set.hide_select = True
                d_set.hide_set(True)
                d_set.wow_wmo_doodad_set.enabled = True

                if not len(bpy.context.scene.wow_wmo_root_elements.doodad_sets):
                    d_set.name = '$SetDefaultGlobal'
                else:
                    d_set.name = 'Doodad_Set'

                slot = bpy.context.scene.wow_wmo_root_elements.doodad_sets.add()
                slot.pointer = d_set

        elif self.action == 'REMOVE':

            col = getattr(context.scene.wow_wmo_root_elements, self.col_name)
            cur_idx = getattr(context.scene.wow_wmo_root_elements, self.cur_idx_name)

            if len(col) <= cur_idx:
                return {'FINISHED'}

            item = col[cur_idx].pointer

            if item:
                if self.col_name == 'groups':
                    item.wow_wmo_group.enabled = False

                elif self.col_name == 'portals':
                    item.wow_wmo_portal.enabled = False

                elif self.col_name == 'fogs':
                    item.wow_wmo_fog.enabled = False

                elif self.col_name == 'lights':
                    item.wow_wmo_light.enabled = False

                elif self.col_name == 'materials':
                    item.wow_wmo_material.enabled = False

                elif self.col_name == 'doodad_sets':
                    item.wow_wmo_doodad_set.enabled = False

            col.remove(cur_idx)
            context.scene.wow_wmo_root_elements.is_update_critical = True

        else:
            self.report({'ERROR'}, 'Unsupported token')
            return {'CANCELLED'}

        return {'FINISHED'}
