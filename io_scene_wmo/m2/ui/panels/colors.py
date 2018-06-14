import bpy


class WowM2ColorsPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_label = "M2 Colors"

    def draw(self, context):
        layout = self.layout

        col = layout.column()

        row = col.row()
        sub_col1 = row.column()
        sub_col1.template_list("WowM2Colors_ColorList", "", context.scene, "wow_m2_colors", context.scene,
                               "WowM2CurColorIndex")

        sub_col2 = row.column().column(align=True)
        sub_col2.operator("scene.wow_m2_colors_add_color", text='', icon='ZOOMIN')
        sub_col2.operator("scene.wow_m2_colors_remove_color", text='', icon='ZOOMOUT')

    @classmethod
    def poll(cls, context):
        return context.scene is not None and context.scene.WowScene.Type == 'M2'


class WowM2Colors_ColorList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        self.use_filter_show = False

        if self.layout_type in {'DEFAULT', 'COMPACT'}:

            row = layout.row(align=True)
            cur_color_prop_group = context.scene.wow_m2_colors[index]
            row.prop(cur_color_prop_group, "name", text="", icon='COLOR', emboss=False)
            row.prop(cur_color_prop_group, "Color", text="")

        elif self.layout_type in {'GRID'}:
            pass


class WowM2Colors_ColorAdd(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_colors_add_color'
    bl_label = 'Add WoW color'
    bl_description = 'Add WoW color'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        color = context.scene.wow_m2_colors.add()
        context.scene.WowM2CurColorIndex = len(context.scene.wow_m2_colors) - 1
        color.name = 'Color_{}'.format(context.scene.WowM2CurColorIndex)

        return {'FINISHED'}


class WowM2Colors_ColorRemove(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_colors_remove_color'
    bl_label = 'Remove WoW color'
    bl_description = 'Remove WoW color'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        context.scene.wow_m2_colors.remove(context.scene.WowM2CurColorIndex)

        return {'FINISHED'}


def update_color_change(self, context):
    for mat in bpy.data.materials:
        if mat.use_nodes and mat.texture_slots[mat.active_texture_index].texture.wow_m2_texture.Color == self.name:
            mat.node_tree.nodes['ColorRamp'].color_ramp.elements[0].color = self.Color
            mat.invert_z = mat.invert_z


class WowM2ColorPropertyGroup(bpy.types.PropertyGroup):

    Color = bpy.props.FloatVectorProperty(
        name='Color',
        description='The color applied to WoW material. Can be animated. Alpha defines model transparency and is multiplied with transparency value',
        subtype='COLOR',
        size=4,
        default=(1.0, 1.0, 1.0, 1.0),
        min=0.0,
        max=1.0,
        update=update_color_change
    )

    name = bpy.props.StringProperty(
        name='Color name',
        description='Only used for scene organization purposes, ignored on export'
    )


def register():
    bpy.types.Scene.wow_m2_colors = bpy.props.CollectionProperty(
        name='Colors',
        type=WowM2ColorPropertyGroup
    )

    bpy.types.Scene.WowM2CurColorIndex = bpy.props.IntProperty()


def unregister():
    del bpy.types.Scene.wow_m2_colors
    del bpy.types.Scene.WowM2CurColorIndex