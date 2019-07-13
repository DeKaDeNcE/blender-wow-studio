import bpy


class M2_PT_transparency_panel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_label = "M2 Transparency"

    def draw(self, context):
        layout = self.layout

        col = layout.column()

        row = col.row()
        sub_col1 = row.column()
        sub_col1.template_list("WowM2Transparency_TransparencyList", "", context.scene, "wow_m2_transparency",
                               context.scene, "wow_m2_cur_transparency_index")

        sub_col2 = row.column().column(align=True)
        sub_col2.operator("scene.wow_m2_transparency_add_value", text='', icon='ADD')
        sub_col2.operator("scene.wow_m2_transparency_remove_value", text='', icon='REMOVE')

    @classmethod
    def poll(cls, context):
        return context.scene is not None and context.scene.wow_scene.type == 'M2'


class M2_UL_transparency_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        self.use_filter_show = False

        if self.layout_type in {'DEFAULT', 'COMPACT'}:

            row = layout.row(align=True)
            cur_trans_prop_group = context.scene.wow_m2_transparency[index]
            row.prop(cur_trans_prop_group, "name", text="", icon='RESTRICT_VIEW_OFF', emboss=False)
            row.prop(cur_trans_prop_group, "value", text="")

        elif self.layout_type in {'GRID'}:
            pass


class M2_OT_transparency_value_add(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_transparency_add_value'
    bl_label = 'Add WoW transparency'
    bl_description = 'Add WoW transparency'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        value = context.scene.wow_m2_transparency.add()
        context.scene.wow_m2_cur_transparency_index = len(context.scene.wow_m2_transparency) - 1
        value.name = 'Transparency_{}'.format(context.scene.wow_m2_cur_transparency_index)

        return {'FINISHED'}


class M2_OT_transparency_value_remove(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_transparency_remove_value'
    bl_label = 'Remove WoW transparency'
    bl_description = 'Remove WoW transparency'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        context.scene.wow_m2_transparency.remove(context.scene.wow_m2_cur_transparency_index)

        return {'FINISHED'}


def update_transparency_change(self, context):
    for mat in bpy.data.materials:
        if mat.use_nodes and mat.texture_slots[mat.active_texture_index].texture.wow_m2_texture.transparency == self.name:
            mat.node_tree.nodes['Math'].inputs[1].default_value = self.value
            mat.invert_z = mat.invert_z


class WowM2TransprencyPropertyGroup(bpy.types.PropertyGroup):

    value:  bpy.props.FloatProperty(
        name='Transparency',
        description='Defines transparency for M2 material. Can be animated. Multiplied by alpha channel of color block.',
        min=0.0,
        max=1.0,
        default=1.0,
        update=update_transparency_change
    )

    name:  bpy.props.StringProperty(
        name='Transparency name',
        description='Only used for scene organization purposes, ignored on export'
    )


def register():
    bpy.types.Scene.wow_m2_transparency = bpy.props.CollectionProperty(
        name='Transparency',
        type=WowM2TransprencyPropertyGroup
    )

    bpy.types.Scene.wow_m2_cur_transparency_index:  bpy.props.IntProperty()


def unregister():
    del bpy.types.Scene.wow_m2_transparency
    del bpy.types.Scene.wow_m2_cur_transparency_index

