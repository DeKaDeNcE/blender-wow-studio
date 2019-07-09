import bpy

from collections import namedtuple

from .... import ui_icons
from .utils import update_current_object, update_doodad_pointer, WMO_UL_root_components_template_list
from .doodad import WMO_PT_doodad


class WMO_OT_doodad_set_components_change(bpy.types.Operator):
    bl_idname = 'scene.wow_wmo_doodad_set_components_change'
    bl_label = 'Add / Remove'
    bl_description = 'Add / Remove'
    bl_options = {'REGISTER', 'INTERNAL', 'UNDO'}

    action:  bpy.props.StringProperty(default='ADD', options={'HIDDEN'})

    def execute(self, context):

        root_comps = context.scene.wow_wmo_root_components

        if self.action == 'ADD':
            bpy.ops.scene.wow_wmo_import_doodad_from_wmv()
            obj = bpy.context.view_layer.objects.active
            obj.parent = root_comps.doodad_sets[root_comps.cur_doodad_set].pointer


        else:
            d_set = root_comps.doodad_sets[root_comps.cur_doodad_set]

            if d_set.cur_doodad < len(d_set.doodads):
                d_set.doodads[d_set.cur_doodad].pointer.parent = None
                d_set.doodads.remove(d_set.cur_doodad)

        return {'FINISHED'}


class WMO_UL_doodad_set_doodad_list(WMO_UL_root_components_template_list, bpy.types.UIList):
    icon = ui_icons['WOW_STUDIO_M2']

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):

        if self.layout_type in {'DEFAULT', 'COMPACT'}:

            row = layout.row(align=True)
            sub_col = row.column()
            sub_col.scale_x = 0.3

            sub_col.label(text="#{}".format(index), icon='WORLD' if item.pointer.name == '$SetDefaultGlobal' else 'GROUP')

            sub_col = row.column()
            sub_col.prop(item.pointer, 'name', emboss=False, text='')

        elif self.layout_type in {'GRID'}:
            pass


class WMO_PT_doodad_set(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "WMO Doodad Set"

    def draw(self, context):
        layout = self.layout

        root_comps = context.scene.wow_wmo_root_components
        d_set = root_comps.doodad_sets[root_comps.cur_doodad_set]
        row = layout.row()
        sub_col1 = row.column()
        sub_col1.template_list('WMO_UL_doodad_set_doodad_list', "", d_set, 'doodads', d_set, 'cur_doodad')
        sub_col_parent = row.column()
        sub_col2 = sub_col_parent.column(align=True)

        op = sub_col2.operator("scene.wow_wmo_doodad_set_components_change", text='', icon='ADD')
        op.action = 'ADD'

        op = sub_col2.operator("scene.wow_wmo_doodad_set_components_change", text='', icon='REMOVE')
        op.action = 'REMOVE'

        if len(d_set.doodads):
            doodad = d_set.doodads[d_set.cur_doodad]

            ctx_override = namedtuple('ctx_override', ('layout', 'object'))

            if doodad:
                box = sub_col1.box()
                col = box.column()
                col.label(text='Doodad Properties', icon='PREFERENCES')
                ctx = ctx_override(col, doodad.pointer)
                WMO_PT_doodad.draw(ctx, ctx)

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
                and context.object is not None
                and context.object.wow_wmo_doodad_set.enabled
        )


class DoodadPointerPropertyGroup(bpy.types.PropertyGroup):

    pointer:  bpy.props.PointerProperty(type=bpy.types.Object, update=update_doodad_pointer)

    name:  bpy.props.StringProperty()


class WoWWMODoodadSetProperptyGroup(bpy.types.PropertyGroup):

    enabled:  bpy.props.BoolProperty()

    cur_doodad:  bpy.props.IntProperty(
        update=lambda self, ctx: update_current_object(self, ctx, 'doodads', 'cur_doodad')
    )

    doodads:  bpy.props.CollectionProperty(type=DoodadPointerPropertyGroup)

    pointer:  bpy.props.PointerProperty(type=bpy.types.Object, update=update_doodad_pointer)

    name:  bpy.props.StringProperty()


def register():
    bpy.types.Object.wow_wmo_doodad_set = bpy.props.PointerProperty(type=WoWWMODoodadSetProperptyGroup)


def unregister():
    del bpy.types.Object.wow_wmo_doodad_set
