from collections import namedtuple

import bpy

from .doodad_set import WMO_PT_doodad_set, WoWWMODoodadSetProperptyGroup
from .fog import WMO_PT_fog
from .group import WMO_PT_wmo_group
from .light import WMO_PT_light
from .material import WMO_PT_material, update_flags, update_shader
from .portal import WMO_PT_portal
from .utils import WMO_UL_root_elements_template_list, update_current_object, update_doodad_pointer
from .... import ui_icons


######################
###### UI Lists ######
######################

class WMO_UL_root_elements_doodadset_list(WMO_UL_root_elements_template_list, bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):

        if self.layout_type in {'DEFAULT', 'COMPACT'}:

            row = layout.row()
            sub_col = row.column()
            sub_col.scale_x = 0.3

            sub_col.label(text="#{}".format(index), icon='WORLD' if item.pointer.name == '$SetDefaultGlobal' else 'GROUP')

            sub_col = row.column()
            sub_col.prop(item.pointer, 'name', emboss=False, text='')

        elif self.layout_type in {'GRID'}:
            pass


class WMO_UL_root_elements_groups_list(WMO_UL_root_elements_template_list, bpy.types.UIList):

    icon = ui_icons['WOW_STUDIO_WMO']


class WMO_UL_root_elements_fogs_list(WMO_UL_root_elements_template_list, bpy.types.UIList):

    icon = ui_icons['WOW_STUDIO_FOG']

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):

        if self.layout_type in {'DEFAULT', 'COMPACT'}:

            row = layout.row()
            sub_col = row.column()
            sub_col.scale_x = 0.3

            if isinstance(self.icon, int):
                sub_col.label(text="#{} ".format(index), icon_value=self.icon)

            elif isinstance(self.icon, str):
                sub_col.label(text="#{} ".format(index), icon=self.icon)

            sub_col = row.column()
            sub_col.prop(item.pointer, 'name', emboss=False, text='')

        elif self.layout_type in {'GRID'}:
            pass


class WMO_UL_root_elements_portal_list(WMO_UL_root_elements_template_list, bpy.types.UIList):

    icon = ui_icons['WOW_STUDIO_CONVERT_PORTAL']


class WMO_UL_root_elements_materials_list(WMO_UL_root_elements_template_list, bpy.types.UIList):

    icon = 'MATERIAL_DYNAMIC'



class WMO_UL_root_elements_lights_list(WMO_UL_root_elements_template_list, bpy.types.UIList):

    icon = 'LIGHT'


_ui_lists = {
    'groups': 'WMO_UL_root_elements_groups_list',
    'fogs': 'WMO_UL_root_elements_fogs_list',
    'portals': 'WMO_UL_root_elements_portal_list',
    'materials': 'WMO_UL_root_elements_materials_list',
    'lights': 'WMO_UL_root_elements_lights_list',
    'doodad_sets': 'WMO_UL_root_elements_doodadset_list'
}

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
##### Panels #####
#####################

wmo_widget_items = (
                    ("GROUPS", "", "WMO Groups", ui_icons['WOW_STUDIO_WMO'], 0),
                    ("FOGS", "", "WMO Fogs", ui_icons['WOW_STUDIO_FOG'], 1),
                    ("MATERIALS", "", "WMO Materials", 'MATERIAL', 2),
                    ("PORTALS", "", "WMO Portals", ui_icons['WOW_STUDIO_CONVERT_PORTAL'], 3),
                    ("LIGHTS", "", "WMO Lights",'LIGHT', 4),
                    ("DOODADS", "", "WMO Doodad Sets", ui_icons['WOW_STUDIO_M2'], 5)
                   )

wmo_widget_labels = {item[0] : item[2] for item in wmo_widget_items}


class WMO_PT_root_elements(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_label = "WMO Components"

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO')

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.prop(context.scene.wow_wmo_root_elements, 'cur_widget', expand=True)
        row.label(text=wmo_widget_labels[context.scene.wow_wmo_root_elements.cur_widget])
        col = layout.column()

        cur_widget = context.scene.wow_wmo_root_elements.cur_widget

        if cur_widget == 'GROUPS':
            draw_wmo_groups_panel(col, context)
        elif cur_widget == 'MATERIALS':
            draw_wmo_materials_panel(col, context)
        elif cur_widget == 'PORTALS':
            draw_wmo_portals_panel(col, context)
        elif cur_widget == 'DOODADS':
            draw_wmo_doodad_sets_panel(col, context)
        elif cur_widget == 'FOGS':
            draw_wmo_fogs_panel(col, context)
        elif cur_widget == 'LIGHTS':
            draw_wmo_lights_panel(col, context)
        else:
            pass # invalid identifier


def draw_wmo_groups_panel(layout, context):
    layout = draw_list(context, layout, 'cur_group', 'groups')

    root_comps = context.scene.wow_wmo_root_elements
    groups = root_comps.groups
    cur_group = root_comps.cur_group

    ctx_override = namedtuple('ctx_override', ('object', 'scene', 'layout'))

    if len(groups) > cur_group:
        obj = groups[cur_group].pointer
        if obj:
            box = layout.box()
            box.label(text='Properties', icon='PREFERENCES')

            ctx = ctx_override(obj, context.scene, box)
            WMO_PT_wmo_group.draw(ctx, ctx)

    layout.prop(root_comps, 'is_update_critical')  # temporary


def draw_wmo_fogs_panel(layout, context):
    layout = draw_list(context, layout, 'cur_fog', 'fogs')

    root_comps = context.scene.wow_wmo_root_elements
    fogs = root_comps.fogs
    cur_fog = root_comps.cur_fog

    ctx_override = namedtuple('ctx_override', ('object', 'scene', 'layout'))

    if len(fogs) > cur_fog:
        obj = fogs[cur_fog].pointer
        if obj:
            box = layout.box()
            box.label(text='Properties', icon='PREFERENCES')

            ctx = ctx_override(obj, context.scene, box)
            WMO_PT_fog.draw(ctx, ctx)


def draw_wmo_portals_panel(layout, context):
    layout = draw_list(context, layout, 'cur_portal', 'portals')

    root_comps = context.scene.wow_wmo_root_elements
    portals = root_comps.portals
    cur_portal = root_comps.cur_portal

    ctx_override = namedtuple('ctx_override', ('object', 'scene', 'layout'))

    if len(portals) > cur_portal:
        obj = portals[cur_portal].pointer
        if obj:
            box = layout.box()
            box.label(text='Properties', icon='PREFERENCES')

            ctx = ctx_override(obj, context.scene, box)
            WMO_PT_portal.draw(ctx, ctx)


def draw_wmo_lights_panel(layout, context):
    layout = draw_list(context, layout, 'cur_light', 'lights')

    root_comps = context.scene.wow_wmo_root_elements
    portals = root_comps.lights
    cur_portal = root_comps.cur_light

    ctx_override = namedtuple('ctx_override', ('object', 'scene', 'layout'))

    if len(portals) > cur_portal:
        obj = portals[cur_portal].pointer
        if obj:
            box = layout.box()
            box.label(text='Properties', icon='PREFERENCES')

            ctx = ctx_override(obj, context.scene, box)
            WMO_PT_light.draw(ctx, ctx)



def draw_wmo_materials_panel(layout, context):
    layout = draw_list(context, layout, 'cur_material', 'materials')

    if bpy.context.view_layer.objects.active and bpy.context.view_layer.objects.active.mode == 'EDIT':
        row = layout.row(align=True)
        row.operator("object.material_slot_assign", text="Assign")
        row.operator("object.material_slot_select", text="Select")
        row.operator("object.material_slot_deselect", text="Deselect")

    root_comps = context.scene.wow_wmo_root_elements
    materials = root_comps.materials
    cur_material = root_comps.cur_material

    ctx_override = namedtuple('ctx_override', ('material', 'scene', 'layout'))

    if len(materials) > cur_material:
        mat = materials[cur_material].pointer
        if mat:
            box = layout.box()
            box.label(text='Properties', icon='PREFERENCES')

            ctx = ctx_override(mat, context.scene, box)
            WMO_PT_material.draw(ctx, ctx)


def draw_wmo_doodad_sets_panel(layout, context):
    layout = draw_list(context, layout, 'cur_doodad_set', 'doodad_sets')

    root_comps = context.scene.wow_wmo_root_elements
    doodad_sets = root_comps.doodad_sets
    cur_set = root_comps.cur_doodad_set

    if len(doodad_sets) > cur_set:
        doodad_set = doodad_sets[cur_set]
        ctx_override = namedtuple('ctx_override', ('object', 'scene', 'layout'))

        box = layout.box()
        box.label(text='Doodads', icon_value=ui_icons['WOW_STUDIO_M2'])

        ctx = ctx_override(doodad_set.pointer, context.scene, box)
        WMO_PT_doodad_set.draw(ctx, ctx)


def draw_list(context, col, cur_idx_name, col_name):

    row = col.row()
    sub_col1 = row.column()
    sub_col1.template_list(_ui_lists[col_name], "",
                           context.scene.wow_wmo_root_elements,
                           col_name, context.scene.wow_wmo_root_elements, cur_idx_name)
    sub_col_parent = row.column()
    sub_col2 = sub_col_parent.column(align=True)

    if col_name in ('materials', 'lights', 'doodad_sets'):
        op = sub_col2.operator("scene.wow_wmo_root_elements_change", text='', icon='ADD')
        op.action, op.add_action, op.col_name, op.cur_idx_name = 'ADD', 'NEW', col_name, cur_idx_name

    if col_name not in ('doodad_sets', 'doodads'):
        op = sub_col2.operator("scene.wow_wmo_root_elements_change", text='', icon='COLLECTION_NEW')
        op.action, op.add_action, op.col_name, op.cur_idx_name = 'ADD', 'EMPTY', col_name, cur_idx_name

    op = sub_col2.operator("scene.wow_wmo_root_elements_change", text='', icon='REMOVE')
    op.action, op.col_name, op.cur_idx_name = 'REMOVE', col_name, cur_idx_name

    return sub_col1


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
        self.pointer.wow_wmo_material.self_pointer = self.pointer
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
                child.hide_set(False)

        else:
            for child in d_set.pointer.children:
                child.hide_set(True)


def update_current_material(self, context):

    mat = self.materials[self.cur_material].pointer
    obj = bpy.context.view_layer.objects.active

    if mat and obj and obj.type == 'MESH' and mat.name in obj.data.materials:
        obj.active_material_index = obj.data.materials.find(mat.name)


class DoodadProtoPointerPropertyGroup(bpy.types.PropertyGroup):

    pointer:  bpy.props.PointerProperty(type=bpy.types.Object, update=update_doodad_pointer)

    name:  bpy.props.StringProperty()


class WoWWMO_RootComponents(bpy.types.PropertyGroup):

    is_update_critical:  bpy.props.BoolProperty(default=False)

    cur_widget: bpy.props.EnumProperty(
        name='WMO Components',
        items=wmo_widget_items
    )

    groups:  bpy.props.CollectionProperty(type=GroupPointerPropertyGroup)
    cur_group:  bpy.props.IntProperty(update=lambda self, ctx: update_current_object(self, ctx, 'groups', 'cur_group'))

    fogs:  bpy.props.CollectionProperty(type=FogPointerPropertyGroup)
    cur_fog:  bpy.props.IntProperty(update=lambda self, ctx: update_current_object(self, ctx, 'fogs', 'cur_fog'))

    portals:  bpy.props.CollectionProperty(type=PortalPointerPropertyGroup)
    cur_portal:  bpy.props.IntProperty(update=lambda self, ctx: update_current_object(self, ctx, 'portals', 'cur_portal'))

    lights:  bpy.props.CollectionProperty(type=LightPointerPropertyGroup)
    cur_light:  bpy.props.IntProperty(update=lambda self, ctx: update_current_object(self, ctx, 'lights', 'cur_light'))

    doodad_sets:  bpy.props.CollectionProperty(type=WoWWMODoodadSetProperptyGroup)
    cur_doodad_set:  bpy.props.IntProperty(update=update_current_doodad_set)

    materials:  bpy.props.CollectionProperty(type=MaterialPointerPropertyGroup)
    cur_material:  bpy.props.IntProperty(update=update_current_material)


def register():
    bpy.types.Scene.wow_wmo_root_elements = bpy.props.PointerProperty(type=WoWWMO_RootComponents)


def unregister():
    del bpy.types.Scene.wow_wmo_root_elements


