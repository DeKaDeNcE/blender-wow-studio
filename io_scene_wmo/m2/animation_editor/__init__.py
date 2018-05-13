import bpy


###############################
## User Interface
###############################

#### Pop-up dialog ####

class AnimationEditorDialog(bpy.types.Operator):
    bl_idname = 'scene.wow_animation_editor_toggle'
    bl_label = 'Wow M2 Animation Editor'

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=600)

    def draw(self, context):
        layout = self.layout
        split = layout.split(percentage=0.33)

        col = split.column()
        col.label('Animations:', icon='RENDER_ANIMATION')
        row = col.row()
        sub_col1 = row.column()
        sub_col1.template_list("AnimationEditor_AnimationList", "", context.scene, "WowM2Animations", context.scene,
                               "WowM2CurAnimIndex")
        sub_col2 = row.column(align=True)
        sub_col2.operator("scene.wow_m2_animation_editor_seq_add", text='', icon='ZOOMIN')
        sub_col2.operator("scene.wow_m2_animation_editor_seq_remove", text='', icon='ZOOMOUT')

        col = split.column()
        col.label('Objects:', icon='OBJECT_DATA')

        try:
            cur_anim_track = context.scene.WowM2Animations[context.scene.WowM2CurAnimIndex]

        except IndexError:
            col.label('No sequence selected.', icon='ERROR')

        if cur_anim_track:

            row = col.row()
            sub_col1 = row.column()
            sub_col1.template_list("AnimationEditor_SequenceObjectList", "", cur_anim_track, "AnimPairs",
                                   cur_anim_track, "ActiveObjectIndex")
            sub_col2 = row.column(align=True)
            sub_col2.operator("scene.wow_m2_animation_editor_seq_add", text='', icon='ZOOMIN')
            sub_col2.operator("scene.wow_m2_animation_editor_seq_remove", text='', icon='ZOOMOUT')

            col = split.column()
            col.label('NLA Tracks:', icon='NLA')

            try:
                cur_anim_pair = cur_anim_track[cur_anim_track.ActiveObjectIndex]
            except IndexError:
                col.label('No object selected.', icon='ERROR')

            if cur_anim_pair.Object is not None:

                row = col.row()
                sub_col1 = row.column()
                sub_col1.template_list("AnimationEditor_ObjectNLATrackList", "", cur_anim_pair, "NLATracks",
                                       cur_anim_pair, "ActiveTrack")
                sub_col2 = row.column(align=True)
                sub_col2.operator("scene.wow_m2_animation_editor_seq_add", text='', icon='ZOOMIN')
                sub_col2.operator("scene.wow_m2_animation_editor_seq_remove", text='', icon='ZOOMOUT')

            else:
                col.label('Active object slot is empty.', icon='ERROR')


        else:

            col = split.column()
            col.label('NLA Tracks:', icon='NLA')
            col.label('No object selected.', icon='ERROR')


    def check(self, context): # redraw the popup window
        return True


#### UI List layouts ####

# Animation List

class AnimationEditor_AnimationList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon_value=icon)
        elif self.layout_type in {'GRID'}:
            pass


class AnimationEditor_SequenceAdd(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_animation_editor_seq_add'
    bl_label = 'Add WoW animation'
    bl_description = 'Add Wow animation sequence'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        sequence = context.scene.WowM2Animations.add()

        return {'FINISHED'}


class AnimationEditor_SequenceRemove(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_animation_editor_seq_remove'
    bl_label = 'Remove WoW animation'
    bl_description = 'Remove Wow animation sequence'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):

        context.scene.WowM2Animations.remove(context.scene.WowM2CurAnimIndex)

        return {'FINISHED'}


# Object list


class AnimationEditor_SequenceObjectList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon_value=icon)
        elif self.layout_type in {'GRID'}:
            pass

class AnimationEditor_ObjectAdd(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_animation_editor_object_add'
    bl_label = 'Add object'
    bl_description = 'Add new object to selected animation sequence'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):

        scene = context.scene

        try:
            sequence = scene.WowM2Animations[scene.WowM2CurAnimIndex]
            sequence.AnimPairs.add()

        except IndexError:
            self.report({'ERROR'}, "No animation sequence selected")
            return {'CANCELLED'}

        return {'FINISHED'}

class AnimationEditor_ObjectRemove(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_animation_editor_object_remove'
    bl_label = 'Remove object'
    bl_description = 'Remove object from selected animation sequence'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):

        scene = context.scene

        try:
            sequence = scene.WowM2Animations[scene.WowM2CurAnimIndex]
            sequence.AnimPairs.remove()

        except IndexError:
            self.report({'ERROR'}, "No animation sequence selected")
            return {'CANCELLED'}

        return {'FINISHED'}


# NLA Track list


class AnimationEditor_ObjectNLATrackList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon_value=icon)
        elif self.layout_type in {'GRID'}:
            pass


class AnimationEditor_NLATrackSlotAdd(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_animation_editor_nla_track_add'
    bl_label = 'Add NLA track slot'
    bl_description = 'Add NLA track slot to selected object'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        scene = context.scene

        try:
            sequence = scene.WowM2Animations[scene.WowM2CurAnimIndex]

            try:
                anim_pair = sequence.AnimPairs[sequence.ActiveObjectIndex]

                if anim_pair.Object is None:
                    self.report({'ERROR'}, "Active object slot is empty")
                    return {'CANCELLED'}

                nla_track = anim_pair.NLATracks.add()


            except IndexError:
                self.report({'ERROR'}, "No object selected in this sequence")
                return {'CANCELLED'}

        except IndexError:
            self.report({'ERROR'}, "No animation sequence selected")
            return {'CANCELLED'}

        return {'FINISHED'}


class AnimationEditor_NLATrackSlotRemove(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_animation_editor_seq_remove'
    bl_label = 'Remove WoW animation'
    bl_description = 'Remove Wow animation sequence'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):

        scene = context.scene

        try:
            sequence = scene.WowM2Animations[scene.WowM2CurAnimIndex]

            try:
                anim_pair = sequence.AnimPairs[sequence.ActiveObjectIndex]

                if anim_pair.Object is None:
                    self.report({'ERROR'}, "Active object slot is empty")
                    return {'CANCELLED'}

                nla_track = anim_pair.NLATracks.add()


            except IndexError:
                self.report({'ERROR'}, "No object selected in this sequence")
                return {'CANCELLED'}

        except IndexError:
            self.report({'ERROR'}, "No animation sequence selected")
            return {'CANCELLED'}

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

    ActiveTrack = bpy.props.IntProperty()


class WowM2AnimationEditorPropertyGroup(bpy.types.PropertyGroup):

    AnimPairs = bpy.props.CollectionProperty(type=WowM2AnimationEditorAnimationPairsPropertyGroup)

    ActiveObjectIndex = bpy.props.IntProperty()


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