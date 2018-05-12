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
        row = col.row()
        sub_col1 = row.column()
        sub_col1.template_list("AnimationList", "", context.scene, "WowM2Animations", context.scene, "WowM2CurAnimIndex")
        sub_col2 = row.column(align=True)
        sub_col2.operator("scene.wow_m2_animation_editor_seq_add", text='', icon='ZOOMIN')
        sub_col2.operator("scene.wow_m2_animation_editor_seq_remove", text='', icon='ZOOMOUT')

    def check(self, context):
        return True


class AnimationList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon_value=icon)
        elif self.layout_type in {'GRID'}:
            pass


class AnimationEditorSequenceAdd(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_animation_editor_seq_add'
    bl_label = 'Add WoW animation'
    bl_description = 'Add Wow animation sequence'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        sequence = context.scene.WowM2Animations.add()

        return {'FINISHED'}


class AnimationEditorSequenceRemove(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_animation_editor_seq_remove'
    bl_label = 'Remove WoW animation'
    bl_description = 'Remove Wow animation sequence'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):

        context.scene.WowM2Animations.remove(context.scene.WowM2CurAnimIndex)

        return {'FINISHED'}


class WowM2AnimationEditorNLATrackPropertyGroup(bpy.types.PropertyGroup):

    Name = bpy.props.StringProperty()


class WowM2AnimationEditorAnimationPairsPropertyGroup(bpy.types.PropertyGroup):

    @staticmethod
    def poll_object(self, obj):
        # TODO: safer polling

        sequence = bpy.context.scene.WowM2Animations[bpy.context.scene.WowM2CurAnimIndex]

        for anim_pair in sequence.AnimPairs:
            if anim_pair.Object == obj:
                return False


        return True

    @staticmethod
    def update_object(self, context):
        # TODO: safety checks

        sequence = bpy.context.scene.WowM2Animations[bpy.context.scene.WowM2CurAnimIndex]

    Object = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Object",
        description="Object to animate in this animation sequence",
        poll=poll_object,
        update=update_object
    )

    NLATracks = bpy.props.CollectionProperty(
        type=WowM2AnimationEditorNLATrackPropertyGroup,
        name="NLA Tracks",
        description="NLA Tracks to use in this animation sequence"
    )


class WowM2AnimationEditorPropertyGroup(bpy.types.PropertyGroup):

    AnimPairs = bpy.props.CollectionProperty(type=WowM2AnimationEditorAnimationPairsPropertyGroup)


def register_wow_m2_animation_editor_properties():
    bpy.types.Scene.WowM2Animations = bpy.props.CollectionProperty(
        type=WowM2AnimationEditorPropertyGroup,
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