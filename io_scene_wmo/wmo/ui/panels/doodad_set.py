import bpy
from .... import ui_icons
from .root_components import update_current_object, update_doodad_pointer, RootComponents_TemplateList


def draw_list(context, col, cur_idx_name, col_name):

    row = col.row()
    sub_col1 = row.column()
    sub_col1.template_list('DoodadSet_DoodadList', "",
                           context.object.wow_wmo_doodad_set,
                           'doodads', context.object.wow_wmo_doodad_set, 'cur_doodad')
    sub_col_parent = row.column()
    sub_col2 = sub_col_parent.column(align=True)

    op = sub_col2.operator("scene.wow_wmo_root_components_change", text='', icon='GO_LEFT')
    op.action, op.add_action, op.col_name, op.cur_idx_name = 'ADD', 'NEW', col_name, cur_idx_name

    op = sub_col2.operator("scene.wow_wmo_root_components_change", text='', icon='ZOOMOUT')
    op.action, op.col_name, op.cur_idx_name = 'REMOVE', col_name, cur_idx_name


class DoodadSet_DoodadList(RootComponents_TemplateList):
    icon = ui_icons['WOW_STUDIO_M2']


class WoWDoodadSetPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "WMO Doodad Set"

    def draw(self, context):
        layout = self.layout
        draw_list(context, layout, 'cur_doodad', 'doodads')

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
                and context.object is not None
                and context.object.wow_wmo_doodad_set.enabled
        )


class DoodadPointerPropertyGroup(bpy.types.PropertyGroup):

    pointer = bpy.props.PointerProperty(type=bpy.types.Object, update=update_doodad_pointer)

    name = bpy.props.StringProperty()


class WoWWMODoodadSetProperptyGroup(bpy.types.PropertyGroup):

    enabled = bpy.props.BoolProperty()

    cur_doodad = bpy.props.IntProperty(
        update=lambda self, ctx: update_current_object(self, ctx, 'doodads', 'cur_doodad')
    )

    doodads = bpy.props.CollectionProperty(type=DoodadPointerPropertyGroup)


def register():
    bpy.types.Object.wow_wmo_doodad_set = bpy.props.PointerProperty(type=WoWWMODoodadSetProperptyGroup)


def unregister():
    del bpy.types.Object.wow_wmo_doodad_set
