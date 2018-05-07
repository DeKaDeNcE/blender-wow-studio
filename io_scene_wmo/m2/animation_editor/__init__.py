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
        col.label =


class WowM2AnmationPropertyGroup(bpy.types.PropertyGroup):

    Objects = bpy.props.CollectionProperty(

    )




def register_wow_m2_animation_editor_properties():
    bpy.types.Scene.WowM2Animations = bpy.props.CollectionProperty(
        type=WowM2AnmationPropertyGroup,
        name="Animations",
        description="WoW M2 animation sequences"
    )


def unregister_wow_m2_animation_editor_properties():
    bpy.types.Scene.WowM2Animations = None


def register_animation_editor():
    register_wow_m2_animation_editor_properties()


def unregister_animation_editor():
    unregister_wow_m2_animation_editor_properties()