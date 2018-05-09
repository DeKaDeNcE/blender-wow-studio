import bpy


###############################
## User Interface
###############################

class AnimationEditorDialog(bpy.types.Operator):
    bl_idname = 'scene.wow_animation_editor_toggle'
    bl_label = 'Wow M2 Animation Editor'

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label('Animations:')
        sub_col1 = col.column()
        sub_col1.template_list("AnimationList", "", context.scene, "WowM2Animations", context.scene, "WowM2CurAnimIndex")
        sub_col2 = col.column()
        sub_col2.operator("scene.wow_wmo_select_entity", text='', icon='VIEWZOOM').Entity = 'Outdoor'


class AnimationList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon_value=icon)
        elif self.layout_type in {'GRID'}:
            pass


class WowM2AnmationPropertyGroup(bpy.types.PropertyGroup):

    Objects = bpy.props.IntProperty()


def register_wow_m2_animation_editor_properties():
    bpy.types.Scene.WowM2Animations = bpy.props.CollectionProperty(
        type=WowM2AnmationPropertyGroup,
        name="Animations",
        description="WoW M2 animation sequences"
    )

    bpy.types.Scene.WowM2CurAnimIndex = bpy.props.IntProperty()


def unregister_wow_m2_animation_editor_properties():
    del bpy.types.Scene.WowM2Animations
    del bpy.types.Scene.WowM2CurAnimIndex


def register_animation_editor():
    register_wow_m2_animation_editor_properties()


def unregister_animation_editor():
    unregister_wow_m2_animation_editor_properties()