from collections import namedtuple

import bpy

from ....utils.misc import draw_spoiler
from .doodad_set import WMO_PT_doodad_set, WoWWMODoodadSetProperptyGroup
from .fog import WMO_PT_fog
from .group import WMO_PT_wmo_group
from .light import WMO_PT_light
from .material import WMO_PT_material, update_flags, update_shader
from .portal import WMO_PT_portal
from .utils import WMO_UL_root_components_template_list, update_current_object, update_doodad_pointer
from .... import ui_icons


######################
###### UI Lists ######
######################

class WMO_UL_root_components_doodadset_list(WMO_UL_root_components_template_list):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):

        if self.layout_type in {'DEFAULT', 'COMPACT'}:

            row = layout.row(align=True)
            sub_col = row.column()
            sub_col.scale_x = 0.5

            s_row = sub_col.row(align=True)

            s_row.label(text="#{}".format(index), icon='WORLD' if item.pointer.name == '$SetDefaultGlobal' else 'GROUP')
            s_row.prop(item.pointer, 'name', emboss=False)

        elif self.layout_type in {'GRID'}:
            pass


class WMO_UL_root_components_groups_list(WMO_UL_root_components_template_list):

    icon = ui_icons['WOW_STUDIO_WMO']


class WMO_UL_root_components_fogs_list(WMO_UL_root_components_template_list):

    icon = ui_icons['WOW_STUDIO_FOG']

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):

        if self.layout_type in {'DEFAULT', 'COMPACT'}:

            row = layout.row(align=True)
            sub_col = row.column()
            sub_col.scale_x = 0.5

            s_row = sub_col.row(align=True)

            if isinstance(self.icon, int):
                s_row.label(text="#{} ".format(index), icon_value=self.icon)

            elif isinstance(self.icon, str):
                s_row.label(text="#{} ".format(index), icon=self.icon)

            if item.pointer:
                s_row.label(text=item.pointer.name)

        elif self.layout_type in {'GRID'}:
            pass


class WMO_UL_root_components_portal_list(WMO_UL_root_components_template_list):

    icon = ui_icons['WOW_STUDIO_CONVERT_PORTAL']


class WMO_UL_root_components_materials_list(WMO_UL_root_components_template_list):

    icon = 'MATERIAL_DATA'

class WMO_UL_root_components_lights_list(WMO_UL_root_components_template_list):

    icon = 'LIGHT'


_ui_lists = {
    'groups': 'WMO_UL_root_components_groups_list',
    'fogs': 'WMO_UL_root_components_fogs_list',
    'portals': 'WMO_UL_root_components_portal_list',
    'materials': 'WMO_UL_root_components_materials_list',
    'lights': 'WMO_UL_root_components_lights_list',
    'doodad_sets': 'WMO_UL_root_components_doodadset_list'
}

_ui_lists_classes = (
    WMO_UL_root_components_groups_list,
    WMO_UL_root_components_fogs_list,
    WMO_UL_root_components_portal_list,
    WMO_UL_root_components_materials_list,
    WMO_UL_root_components_lights_list,
    WMO_UL_root_components_doodadset_list
)

_obj_props = ['wow_wmo_portal',
              'wow_wmo_fog',
              'wow_wmo_group',
              'wow_wmo_liquid',
              'wow_wmo_doodad_set',
              'wow_wmo_light'
              ]


def is_obj_unused(obj):
    for prop in _obj_props:
        if getattr(obj, prop).enabled:
            return False

    return True


#####################
##### Operators #####
#####################

class WMO_OT_root_components_components_change(bpy.types.Operator):
    bl_idname = 'scene.wow_wmo_root_components_change'
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

                    slot = bpy.context.scene.wow_wmo_root_components.groups.add()
                    slot.pointer = obj

                else:
                    bpy.context.scene.wow_wmo_root_components.groups.add()

            elif self.col_name in 'portals':
                bpy.context.scene.wow_wmo_root_components.portals.add()

            elif self.col_name == 'lights':
                slot = bpy.context.scene.wow_wmo_root_components.lights.add()

                if self.add_action == 'NEW':
                    light = bpy.data.objects.new(name='LIGHT', object_data=bpy.data.lights.new('LIGHT', type='POINT'))
                    bpy.context.collection.objects.link(light)
                    light.location = bpy.context.scene.cursor.location
                    slot.pointer = light

            elif self.col_name == 'fogs':
                bpy.ops.scene.wow_add_fog()

            elif self.col_name == 'materials':

                slot = bpy.context.scene.wow_wmo_root_components.materials.add()

                if self.add_action == 'NEW':
                    new_mat = bpy.data.materials.new('Material')
                    slot.pointer = new_mat

            elif self.col_name == 'doodad_sets':
                act_obj = bpy.context.view_layer.objects.active
                bpy.ops.object.empty_add(type='ARROWS', location=(0, 0,0))

                d_set = bpy.context.view_layer.objects.active
                bpy.context.view_layer.objects.active = act_obj

                d_set.hide_select = True
                d_set.hide_viewport = True
                d_set.wow_wmo_doodad_set.enabled = True

                if not len(bpy.context.scene.wow_wmo_root_components.doodad_sets):
                    d_set.name = '$SetDefaultGlobal'
                else:
                    d_set.name = 'Doodad_Set'

                slot = bpy.context.scene.wow_wmo_root_components.doodad_sets.add()
                slot.pointer = d_set

        elif self.action == 'REMOVE':

            col = getattr(context.scene.wow_wmo_root_components, self.col_name)
            cur_idx = getattr(context.scene.wow_wmo_root_components, self.cur_idx_name)

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
            context.scene.wow_wmo_root_components.is_update_critical = True

        else:
            self.report({'ERROR'}, 'Unsupported token')
            return {'CANCELLED'}

        return {'FINISHED'}


#####################
##### Panels #####
#####################

class WMO_PT_root_components_groups(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_label = "WMO Groups"

    def draw(self, context):
        layout = self.layout
        draw_list(context, layout, 'cur_group', 'groups')

        root_comps = context.scene.wow_wmo_root_components
        groups = root_comps.groups
        cur_group = root_comps.cur_group

        ctx_override = namedtuple('ctx_override', ('object', 'scene', 'layout'))

        if len(groups) > cur_group:
            obj = groups[cur_group].pointer
            if obj:
                spoiler = draw_spoiler(layout, root_comps, 'is_group_props_expanded',
                                       'Properties', icon='PREFERENCES')
                if spoiler:
                    ctx = ctx_override(obj, context.scene, spoiler)
                    WMO_PT_wmo_group.draw(ctx, ctx)
                    spoiler.enabled = True

        layout.prop(root_comps, 'is_update_critical')  # temporary

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
        )


class WMO_PT_root_components_fogs(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_label = "WMO Fogs"

    def draw(self, context):
        layout = self.layout
        draw_list(context, layout, 'cur_fog', 'fogs')

        root_comps = context.scene.wow_wmo_root_components
        fogs = root_comps.fogs
        cur_fog = root_comps.cur_fog

        ctx_override = namedtuple('ctx_override', ('object', 'scene', 'layout'))

        if len(fogs) > cur_fog:
            obj = fogs[cur_fog].pointer
            if obj:
                spoiler = draw_spoiler(layout, root_comps, 'is_fog_props_expanded',
                                       'Properties', icon='PREFERENCES')
                if spoiler:
                    ctx = ctx_override(obj, context.scene, spoiler)
                    WMO_PT_fog.draw(ctx, ctx)
                    spoiler.enabled = True

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
        )


class WMO_PT_root_components_portals(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_label = "WMO Portals"

    def draw(self, context):
        layout = self.layout
        draw_list(context, layout, 'cur_portal', 'portals')

        root_comps = context.scene.wow_wmo_root_components
        portals = root_comps.portals
        cur_portal = root_comps.cur_portal

        ctx_override = namedtuple('ctx_override', ('object', 'scene', 'layout'))

        if len(portals) > cur_portal:
            obj = portals[cur_portal].pointer
            if obj:
                spoiler = draw_spoiler(layout, root_comps, 'is_portal_props_expanded',
                                       'Properties', icon='PREFERENCES')
                if spoiler:
                    ctx = ctx_override(obj, context.scene, spoiler)
                    WMO_PT_portal.draw(ctx, ctx)
                    spoiler.enabled = True

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
        )


class WMO_PT_root_components_lights(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_label = "WMO Lights"

    def draw(self, context):
        layout = self.layout
        draw_list(context, layout, 'cur_light', 'lights')

        root_comps = context.scene.wow_wmo_root_components
        portals = root_comps.lights
        cur_portal = root_comps.cur_light

        ctx_override = namedtuple('ctx_override', ('object', 'scene', 'layout'))

        if len(portals) > cur_portal:
            obj = portals[cur_portal].pointer
            if obj:
                spoiler = draw_spoiler(layout, root_comps, 'is_light_props_expanded',
                                       'Properties', icon='PREFERENCES')
                if spoiler:
                    ctx = ctx_override(obj, context.scene, spoiler)
                    WMO_PT_light.draw(ctx, ctx)
                    spoiler.enabled = True

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
        )


class WBS_PT_root_components_materials(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_label = "WMO Materials"

    def draw(self, context):
        layout = self.layout
        draw_list(context, layout, 'cur_material', 'materials')

        root_comps = context.scene.wow_wmo_root_components
        materials = root_comps.materials
        cur_material = root_comps.cur_material

        ctx_override = namedtuple('ctx_override', ('material', 'scene', 'layout'))

        if len(materials) > cur_material:
            mat = materials[cur_material].pointer
            if mat:
                spoiler = draw_spoiler(layout, root_comps, 'is_material_props_expanded',
                                       'Properties', icon='PREFERENCES')
                if spoiler:
                    ctx = ctx_override(mat, context.scene, spoiler)
                    WMO_PT_material.draw(ctx, ctx)
                    spoiler.enabled = True

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
        )


class WMO_PT_doodadsets_panel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_label = "WMO Doodad Sets"

    def draw(self, context):
        layout = self.layout
        draw_list(context, layout, 'cur_doodad_set', 'doodad_sets')

        root_comps = context.scene.wow_wmo_root_components
        doodad_sets = root_comps.doodad_sets
        cur_set = root_comps.cur_doodad_set

        if len(doodad_sets) > cur_set:
            doodad_set = doodad_sets[cur_set]
            spoiler = draw_spoiler(layout, root_comps, 'is_doodad_set_props_expanded', 'Doodads', icon='PREFERENCES')

            if spoiler:
                spoiler.enabled = True

                ctx_override = namedtuple('ctx_override', ('object', 'scene', 'layout'))

                ctx = ctx_override(doodad_set.pointer, context.scene, spoiler)
                WMO_PT_doodad_set.draw(ctx, ctx)

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
        )


def draw_list(context, col, cur_idx_name, col_name):

    row = col.row()
    sub_col1 = row.column()
    sub_col1.template_list(_ui_lists[col_name], "",
                           context.scene.wow_wmo_root_components,
                           col_name, context.scene.wow_wmo_root_components, cur_idx_name)
    sub_col_parent = row.column()
    sub_col2 = sub_col_parent.column(align=True)

    if col_name in ('materials', 'lights', 'doodad_sets'):
        op = sub_col2.operator("scene.wow_wmo_root_components_change", text='', icon='ADD')
        op.action, op.add_action, op.col_name, op.cur_idx_name = 'ADD', 'NEW', col_name, cur_idx_name

    if col_name not in ('doodad_sets', 'doodads'):
        op = sub_col2.operator("scene.wow_wmo_root_components_change", text='', icon='COLLECTION_NEW')
        op.action, op.add_action, op.col_name, op.cur_idx_name = 'ADD', 'EMPTY', col_name, cur_idx_name

    op = sub_col2.operator("scene.wow_wmo_root_components_change", text='', icon='REMOVE')
    op.action, op.col_name, op.cur_idx_name = 'REMOVE', col_name, cur_idx_name


###########################
##### Property Groups #####
###########################

def update_object_pointer(self, context, prop, obj_type):

    if self.pointer:

        # handle replacing pointer value
        if self.pointer_old:
            getattr(self.pointer_old, prop).enabled = False
            self.pointer_old = None

        # check if object is another type
        if not is_obj_unused(self.pointer) or self.pointer.type != obj_type:
            self.pointer = None
            return

        getattr(self.pointer, prop).enabled = True
        self.pointer_old = self.pointer
        self.name = self.pointer.name

    elif self.pointer_old:
        # handle deletion
        getattr(self.pointer_old, prop).enabled = False
        self.pointer_old = None
        self.name = ""


def update_group_pointer(self, context):
    update_object_pointer(self, context, 'wow_wmo_group', 'MESH')

    # force pass index recalculation
    if self.pointer:
        act_obj = context.view_layer.objects.active
        context.view_layer.objects.active = self.pointer

        self.pointer.wow_wmo_group.flags = self.pointer.wow_wmo_group.flags
        self.pointer.wow_wmo_group.place_type = self.pointer.wow_wmo_group.place_type

        context.view_layer.objects.active = act_obj


def update_material_pointer(self, context):

    if self.pointer:

        # handle replacing pointer value
        if self.pointer_old:
            self.pointer_old.wow_wmo_material.enabled = False
            self.pointer_old = None

        # check if material is used
        if self.pointer.wow_wmo_material.enabled:
            self.pointer = None
            return

        self.pointer.wow_wmo_material.enabled = True
        self.pointer_old = self.pointer
        self.name = self.pointer.name

        # force pass index recalculation

        ctx_override = namedtuple('ctx_override', ('material',))
        ctx = ctx_override(self.pointer)
        update_shader(self.pointer.wow_wmo_material, ctx)
        update_flags(self.pointer.wow_wmo_material, ctx)

    elif self.pointer_old:
        # handle deletion
        self.pointer_old.wow_wmo_material.enabled = False
        self.pointer_old = None
        self.name = ""


class GroupPointerPropertyGroup(bpy.types.PropertyGroup):

    pointer:  bpy.props.PointerProperty(
        name='WMO Group',
        type=bpy.types.Object,
        poll=lambda self, obj: is_obj_unused(obj) and obj.type == 'MESH',
        update=update_group_pointer
    )

    pointer_old:  bpy.props.PointerProperty(type=bpy.types.Object)

    name:  bpy.props.StringProperty()

    export:  bpy.props.BoolProperty(
        name='Export group',
        description='Mark this group for export'
    )


class FogPointerPropertyGroup(bpy.types.PropertyGroup):

    pointer:  bpy.props.PointerProperty(
        name='WMO Fog',
        type=bpy.types.Object,
        poll=lambda self, obj: is_obj_unused(obj) and obj.type == 'MESH',
        update=lambda self, ctx: update_object_pointer(self, ctx, 'wow_wmo_fog', 'MESH')
    )

    pointer_old:  bpy.props.PointerProperty(type=bpy.types.Object)

    name:  bpy.props.StringProperty()


class LightPointerPropertyGroup(bpy.types.PropertyGroup):

    pointer:  bpy.props.PointerProperty(
        name='WMO Light',
        type=bpy.types.Object,
        poll=lambda self, obj: is_obj_unused(obj) and obj.type == 'LIGHT',
        update=lambda self, ctx: update_object_pointer(self, ctx, 'wow_wmo_light', 'LIGHT')
    )

    pointer_old:  bpy.props.PointerProperty(type=bpy.types.Object)

    name:  bpy.props.StringProperty()


class PortalPointerPropertyGroup(bpy.types.PropertyGroup):

    pointer:  bpy.props.PointerProperty(
        name='WMO Portal',
        type=bpy.types.Object,
        poll=lambda self, obj: is_obj_unused(obj) and obj.type == 'MESH',
        update=lambda self, ctx: update_object_pointer(self, ctx, 'wow_wmo_portal', 'MESH')
    )

    pointer_old:  bpy.props.PointerProperty(type=bpy.types.Object)

    name:  bpy.props.StringProperty()


class MaterialPointerPropertyGroup(bpy.types.PropertyGroup):

    pointer:  bpy.props.PointerProperty(
        name='WMO Material',
        type=bpy.types.Material,
        poll=lambda self, mat: not mat.wow_wmo_material.enabled,
        update=update_material_pointer
    )

    pointer_old:  bpy.props.PointerProperty(type=bpy.types.Material)

    name:  bpy.props.StringProperty()


def update_current_doodad_set(self, context):

    for d_set in self.doodad_sets:
        if d_set.name == self.doodad_sets[self.cur_doodad_set].name:
            for child in d_set.pointer.children:
                child.hide_viewport = False

        else:
            for child in d_set.pointer.children:
                child.hide_viewport = True


class DoodadProtoPointerPropertyGroup(bpy.types.PropertyGroup):

    pointer:  bpy.props.PointerProperty(type=bpy.types.Object, update=update_doodad_pointer)

    name:  bpy.props.StringProperty()


class WoWWMO_RootComponents(bpy.types.PropertyGroup):

    is_update_critical:  bpy.props.BoolProperty(default=False)

    groups:  bpy.props.CollectionProperty(type=GroupPointerPropertyGroup)
    cur_group:  bpy.props.IntProperty(update=lambda self, ctx: update_current_object(self, ctx, 'groups', 'cur_group'))
    is_group_props_expanded:  bpy.props.BoolProperty()

    fogs:  bpy.props.CollectionProperty(type=FogPointerPropertyGroup)
    cur_fog:  bpy.props.IntProperty(update=lambda self, ctx: update_current_object(self, ctx, 'fogs', 'cur_fog'))
    is_fog_props_expanded:  bpy.props.BoolProperty()

    portals:  bpy.props.CollectionProperty(type=PortalPointerPropertyGroup)
    cur_portal:  bpy.props.IntProperty(update=lambda self, ctx: update_current_object(self, ctx, 'portals', 'cur_portal'))
    is_portal_props_expanded:  bpy.props.BoolProperty()

    lights:  bpy.props.CollectionProperty(type=LightPointerPropertyGroup)
    cur_light:  bpy.props.IntProperty(update=lambda self, ctx: update_current_object(self, ctx, 'lights', 'cur_light'))
    is_light_props_expanded:  bpy.props.BoolProperty()

    doodad_sets:  bpy.props.CollectionProperty(type=WoWWMODoodadSetProperptyGroup)
    cur_doodad_set:  bpy.props.IntProperty(update=update_current_doodad_set)
    is_doodad_set_props_expanded:  bpy.props.BoolProperty()

    materials:  bpy.props.CollectionProperty(type=MaterialPointerPropertyGroup)
    cur_material:  bpy.props.IntProperty()
    is_material_props_expanded:  bpy.props.BoolProperty()


def register():
    bpy.types.Scene.wow_wmo_root_components = bpy.props.PointerProperty(type=WoWWMO_RootComponents)

    for cls in _ui_lists_classes:
        bpy.utils.register_class(cls)


def unregister():
    del bpy.types.Scene.wow_wmo_root_components

    for cls in _ui_lists_classes:
        bpy.utils.unregister_class(cls)

