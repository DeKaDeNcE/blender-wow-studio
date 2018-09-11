import bpy
from collections import namedtuple
from ....utils import draw_spoiler
from .material import WowMaterialPropertyGroup, WowMaterialPanel
from .group import WowWMOGroupPanel
from .portal import WowPortalPlanePanel
from .fog import WowFogPanel


class RootComponents_TemplateList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):

        if self.layout_type in {'DEFAULT', 'COMPACT'}:

            row = layout.row()
            row.label("#{} {}".format(index, item.pointer.name if item.pointer else 'Empty slot'))
            row.prop(item, "pointer", text=item.name)

        elif self.layout_type in {'GRID'}:
            pass

    def filter_items(self, context, data, propname):

        col = getattr(data, propname)
        filter_name = self.filter_name.lower()

        flt_flags = [self.bitflag_filter_item
                     if any(filter_name in filter_set for filter_set in (str(i), (item.pointer.name if item.pointer else 'Empty slot').lower()))
                     else 0 for i, item in enumerate(col, 1)
                     ]

        if self.use_filter_sort_alpha:
            flt_neworder = [x[1] for x in sorted(
                zip(
                    [x[0] for x in sorted(enumerate(col),
                                          key=lambda x: x[1].name.split()[1] + x[1].name.split()[2])], range(len(col))
                )
            )
            ]
        else:
            flt_neworder = []

        return flt_flags, flt_neworder


class RootComponents_ComponentAdd(bpy.types.Operator):
    bl_idname = 'scene.wow_wmo_root_components_change'
    bl_label = 'Add'
    bl_options = {'REGISTER', 'INTERNAL'}

    col_name = bpy.props.StringProperty()
    cur_idx_name = bpy.props.StringProperty()
    action = bpy.props.StringProperty(default='ADD')

    def execute(self, context):
        if self.action == 'ADD':
            col = getattr(context.scene.wow_wmo_root_components, self.col_name)
            col.add()
            setattr(context.scene.wow_wmo_root_components, self.cur_idx_name, len(col) - 1)

        elif self.action == 'REMOVE':
            col = getattr(context.scene.wow_wmo_root_components, self.col_name)
            col.remove(getattr(context.scene.wow_wmo_root_components, self.cur_idx_name))
        else:
            self.report({'ERROR'}, 'Unsupported token')
            return {'CANCELLED'}

        return {'FINISHED'}


class RootComponents_GroupsPanel(bpy.types.Panel):
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
                                       'Properties', icon='SCRIPTWIN')
                if spoiler:
                    ctx = ctx_override(obj, context.scene, spoiler)
                    WowWMOGroupPanel.draw(ctx, ctx)
                    spoiler.enabled = True

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
        )


class RootComponents_FogsPanel(bpy.types.Panel):
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
                                       'Properties', icon='SCRIPTWIN')
                if spoiler:
                    ctx = ctx_override(obj, context.scene, spoiler)
                    WowFogPanel.draw(ctx, ctx)
                    spoiler.enabled = True

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
        )


class RootComponents_PortalsPanel(bpy.types.Panel):
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
                                       'Properties', icon='SCRIPTWIN')
                if spoiler:
                    ctx = ctx_override(obj, context.scene, spoiler)
                    WowPortalPlanePanel.draw(ctx, ctx)
                    spoiler.enabled = True

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
        )


class RootComponents_MaterialssPanel(bpy.types.Panel):
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
            mat = materials[cur_material]
            if mat:
                spoiler = draw_spoiler(layout, root_comps, 'is_material_props_expanded',
                                       'Properties', icon='SCRIPTWIN')
                if spoiler:
                    ctx = ctx_override(mat, context.scene, spoiler)
                    WowMaterialPanel.draw(ctx, ctx)
                    spoiler.enabled = True

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
        )


def draw_list(context, col, cur_idx_name, col_name):
    row = col.row()
    sub_col1 = row.column()
    sub_col1.template_list('RootComponents_TemplateList', "",
                           context.scene.wow_wmo_root_components,
                           col_name, context.scene.wow_wmo_root_components, cur_idx_name)
    sub_col_parent = row.column()
    sub_col2 = sub_col_parent.column(align=True)
    op = sub_col2.operator("scene.wow_wmo_root_components_change", text='', icon='ZOOMIN')
    op.action, op.col_name, op.cur_idx_name = 'ADD', col_name, cur_idx_name
    op = sub_col2.operator("scene.wow_wmo_root_components_change", text='', icon='ZOOMOUT')
    op.action, op.col_name, op.cur_idx_name = 'REMOVE', col_name, cur_idx_name


class ObjectPointerPropertyGroup(bpy.types.PropertyGroup):

    pointer = bpy.props.PointerProperty(type=bpy.types.Object)


class MaterialPointerPropertyGroup(bpy.types.PropertyGroup):

    pointer = bpy.props.PointerProperty(type=bpy.types.Material)
    wow_wmo_material = bpy.props.PointerProperty(type=WowMaterialPropertyGroup)


class WoWWMO_RootComponents(bpy.types.PropertyGroup):

    groups = bpy.props.CollectionProperty(type=ObjectPointerPropertyGroup)
    cur_group = bpy.props.IntProperty()
    is_group_props_expanded = bpy.props.BoolProperty()

    fogs = bpy.props.CollectionProperty(type=ObjectPointerPropertyGroup)
    cur_fog = bpy.props.IntProperty()
    is_fog_props_expanded = bpy.props.BoolProperty()

    portals = bpy.props.CollectionProperty(type=ObjectPointerPropertyGroup)
    cur_portal = bpy.props.IntProperty()
    is_portal_props_expanded = bpy.props.BoolProperty()

    materials = bpy.props.CollectionProperty(type=MaterialPointerPropertyGroup)
    cur_material = bpy.props.IntProperty()
    is_material_props_expanded = bpy.props.BoolProperty()


def register():
    bpy.types.Scene.wow_wmo_root_components = bpy.props.PointerProperty(type=WoWWMO_RootComponents)


def unregister():
    del bpy.types.Scene.wow_wmo_root_components

