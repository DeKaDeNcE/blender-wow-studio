import bpy
from collections import namedtuple
from ....utils import draw_spoiler
from .... import ui_icons
from .material import WowMaterialPropertyGroup, WowMaterialPanel
from .group import WowWMOGroupPanel
from .portal import WowPortalPlanePanel
from .fog import WowFogPanel
from .light import WowLightPanel


class RootComponents_TemplateList(bpy.types.UIList):

    icon = 'OBJECT_DATA'

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):

        if self.layout_type in {'DEFAULT', 'COMPACT'}:

            row = layout.row()
            sub_col = row.column()

            if isinstance(self.icon, int):
                sub_col.label("#{} ".format(index), icon_value=self.icon)

            elif isinstance(self.icon, str):
                sub_col.label("#{} ".format(index), icon=self.icon)

            sub_col.scale_x = 0.5
            row.prop(item, 'pointer', emboss=True, text='')

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


class RootComponents_GroupsList(RootComponents_TemplateList):

    icon = ui_icons['WOW_STUDIO_WMO']


class RootComponents_FogsList(RootComponents_TemplateList):

    icon = ui_icons['WOW_STUDIO_FOG']


class RootComponents_PortalsList(RootComponents_TemplateList):

    icon = ui_icons['WOW_STUDIO_CONVERT_PORTAL']


class RootComponents_MaterialsList(RootComponents_TemplateList):

    icon = 'MATERIAL_DATA'

class RootComponents_LightsList(RootComponents_TemplateList):

    icon = 'LAMP'


_ui_lists = {
    'groups': 'RootComponents_GroupsList',
    'fogs': 'RootComponents_FogsList',
    'portals': 'RootComponents_PortalsList',
    'materials': 'RootComponents_MaterialsList',
    'lights': 'RootComponents_LightsList'
}


_obj_props = ['wow_wmo_portal',
              'wow_wmo_fog',
              'wow_wmo_group',
              'wow_wmo_liquid'
              ]


def is_obj_unused(obj):
    for prop in _obj_props:
        if getattr(obj, prop).enabled:
            return False

    return True


class RootComponents_ComponentChange(bpy.types.Operator):
    bl_idname = 'scene.wow_wmo_root_components_change'
    bl_label = 'Add / Remove'
    bl_description = 'Add / Remove'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    col_name = bpy.props.StringProperty()
    cur_idx_name = bpy.props.StringProperty()
    action = bpy.props.StringProperty(default='ADD')
    material_action = bpy.props.EnumProperty(
        name='Create new material slot',
        items=[('EMPTY', 'Empty', ''),
               ('NEW', 'New', '')],
        default='EMPTY'
    )

    def draw(self, context):
        layout = self.layout
        if self.action == 'ADD' and self.col_name == 'materials':

            row = layout.row()
            row.prop(self, 'material_action', expand=True)

    def invoke(self, context, event):
        if self.action == 'ADD':
            if self.col_name == 'materials':
                wm = context.window_manager
                return wm.invoke_props_dialog(self)

    def execute(self, context):
        if self.action == 'ADD':
            if self.col_name == 'groups':

                obj = bpy.context.scene.objects.active

                if obj and obj.select:

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

            elif self.col_name in ('portals', 'lights'):
                getattr(bpy.context.scene.wow_wmo_root_components, self.col_name).add()

            elif self.col_name == 'fogs':
                bpy.ops.scene.wow_add_fog()

            elif self.col_name == 'materials':

                slot = bpy.context.scene.wow_wmo_root_components.materials.add()

                if self.material_action == 'NEW':
                    new_mat = bpy.data.materials.new('Material')
                    slot.pointer = new_mat

        elif self.action == 'REMOVE':

            col = getattr(context.scene.wow_wmo_root_components, self.col_name)
            cur_idx = getattr(context.scene.wow_wmo_root_components, self.cur_idx_name)

            if not len(col):
                return {'FINISHED'}

            item = col[cur_idx].pointer

            if item:
                if self.col_name == 'groups':
                    item.wow_wmo_group.enabled = False

                elif self.col_name == 'portals':
                    item.wow_wmo_portal.enabled = False

                elif self.col_name == 'fogs':
                    item.wow_wmo_fog.enabled = False

                elif self.col_name == 'materials':
                    item.wow_wmo_material.enabled = False

            col.remove(cur_idx)

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


class RootComponents_LightsPanel(bpy.types.Panel):
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
                                       'Properties', icon='SCRIPTWIN')
                if spoiler:
                    ctx = ctx_override(obj, context.scene, spoiler)
                    WowLightPanel.draw(ctx, ctx)
                    spoiler.enabled = True

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
        )


class RootComponents_MaterialsPanel(bpy.types.Panel):
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
    sub_col1.template_list(_ui_lists[col_name], "",
                           context.scene.wow_wmo_root_components,
                           col_name, context.scene.wow_wmo_root_components, cur_idx_name)
    sub_col_parent = row.column()
    sub_col2 = sub_col_parent.column(align=True)

    row1 = sub_col2.row()
    row1.operator_context = 'INVOKE_DEFAULT' if col_name == 'materials' else 'EXEC_DEFAULT'
    op = row1.operator("scene.wow_wmo_root_components_change", text='', icon='ZOOMIN')
    op.action, op.col_name, op.cur_idx_name = 'ADD', col_name, cur_idx_name
    row1 = sub_col2.row()
    row1.operator_context = 'EXEC_DEFAULT'
    op = row1.operator("scene.wow_wmo_root_components_change", text='', icon='ZOOMOUT')
    op.action, op.col_name, op.cur_idx_name = 'REMOVE', col_name, cur_idx_name


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

    elif self.pointer_old:
        # handle deletion
        self.pointer_old.wow_wmo_material.enabled = False
        self.pointer_old = None
        self.name = ""


class GroupPointerPropertyGroup(bpy.types.PropertyGroup):

    pointer = bpy.props.PointerProperty(
        name='WMO Group',
        type=bpy.types.Object,
        poll=lambda self, obj: is_obj_unused(obj) and obj.type == 'MESH',
        update=lambda self, ctx: update_object_pointer(self, ctx, 'wow_wmo_group', 'MESH')
    )

    pointer_old = bpy.props.PointerProperty(type=bpy.types.Object)

    name = bpy.props.StringProperty()

    is_updated = bpy.props.BoolProperty()


class FogPointerPropertyGroup(bpy.types.PropertyGroup):

    pointer = bpy.props.PointerProperty(
        name='WMO Fog',
        type=bpy.types.Object,
        poll=lambda self, obj: is_obj_unused(obj) and obj.type == 'MESH',
        update=lambda self, ctx: update_object_pointer(self, ctx, 'wow_wmo_fog', 'MESH')
    )

    pointer_old = bpy.props.PointerProperty(type=bpy.types.Object)

    name = bpy.props.StringProperty()


class LightPointerPropertyGroup(bpy.types.PropertyGroup):

    pointer = bpy.props.PointerProperty(
        name='WMO Light',
        type=bpy.types.Object,
        poll=lambda self, obj: is_obj_unused(obj) and obj.type == 'LAMP',
        update=lambda self, ctx: update_object_pointer(self, ctx, 'wow_wmo_light', 'LAMP')
    )

    pointer_old = bpy.props.PointerProperty(type=bpy.types.Object)

    name = bpy.props.StringProperty()


class PortalPointerPropertyGroup(bpy.types.PropertyGroup):

    pointer = bpy.props.PointerProperty(
        name='WMO Portal',
        type=bpy.types.Object,
        poll=lambda self, obj: is_obj_unused(obj) and obj.type == 'MESH',
        update=lambda self, ctx: update_object_pointer(self, ctx, 'wow_wmo_portal', 'MESH')
    )

    pointer_old = bpy.props.PointerProperty(type=bpy.types.Object)

    name = bpy.props.StringProperty()


class MaterialPointerPropertyGroup(bpy.types.PropertyGroup):

    pointer = bpy.props.PointerProperty(
        name='WMO Material',
        type=bpy.types.Material,
        poll=lambda self, mat: not mat.wow_wmo_material.enabled,
        update=update_material_pointer
    )

    pointer_old = bpy.props.PointerProperty(type=bpy.types.Material)

    name = bpy.props.StringProperty()


class WoWWMO_RootComponents(bpy.types.PropertyGroup):

    is_update_critical = bpy.props.BoolProperty(default=False)

    groups = bpy.props.CollectionProperty(type=GroupPointerPropertyGroup)
    cur_group = bpy.props.IntProperty()
    is_group_props_expanded = bpy.props.BoolProperty()

    fogs = bpy.props.CollectionProperty(type=FogPointerPropertyGroup)
    cur_fog = bpy.props.IntProperty()
    is_fog_props_expanded = bpy.props.BoolProperty()

    portals = bpy.props.CollectionProperty(type=PortalPointerPropertyGroup)
    cur_portal = bpy.props.IntProperty()
    is_portal_props_expanded = bpy.props.BoolProperty()

    lights = bpy.props.CollectionProperty(type=LightPointerPropertyGroup)
    cur_light = bpy.props.IntProperty()
    is_light_props_expanded = bpy.props.BoolProperty()

    materials = bpy.props.CollectionProperty(type=MaterialPointerPropertyGroup)
    cur_material = bpy.props.IntProperty()
    is_material_props_expanded = bpy.props.BoolProperty()


def register():
    bpy.types.Scene.wow_wmo_root_components = bpy.props.PointerProperty(type=WoWWMO_RootComponents)


def unregister():
    del bpy.types.Scene.wow_wmo_root_components

