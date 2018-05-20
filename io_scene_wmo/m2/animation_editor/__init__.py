import bpy

from ..ui.enums import get_anim_ids, ANIMATION_FLAGS


###############################
## User Interface
###############################

#### Pop-up dialog ####

class AnimationEditorDialog(bpy.types.Operator):
    bl_idname = 'scene.wow_animation_editor_toggle'
    bl_label = 'WoW M2 Animation Editor'

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=700)

    def draw(self, context):
        layout = self.layout
        split = layout.split(percentage=0.5)

        # Top row - collections: animations, objects, nla_tracks
        # Animations column

        col = split.column()
        col.label('Animations:', icon='CLIP')
        row = col.row()
        sub_col1 = row.column()
        sub_col1.template_list("AnimationEditor_AnimationList", "", context.scene, "WowM2Animations", context.scene,
                               "WowM2CurAnimIndex")
        sub_col2 = row.column(align=True)
        sub_col2.operator("scene.wow_m2_animation_editor_seq_add", text='', icon='ZOOMIN')
        sub_col2.operator("scene.wow_m2_animation_editor_seq_remove", text='', icon='ZOOMOUT')

        # Objects column

        col = split.column()
        col.label('Objects:', icon='OBJECT_DATA')

        cur_anim_track = None

        try:
            cur_anim_track = context.scene.WowM2Animations[context.scene.WowM2CurAnimIndex]

        except IndexError:
            col.label('No sequence selected.', icon='ERROR')

        cur_anim_pair = None

        if cur_anim_track:

            row = col.row()
            sub_col1 = row.column()

            sub_col1.template_list("AnimationEditor_SequenceObjectList", "", cur_anim_track, "AnimPairs",
                                   cur_anim_track, "ActiveObjectIndex")
            sub_col2 = row.column(align=True)
            sub_col2.operator("scene.wow_m2_animation_editor_object_add", text='', icon='ZOOMIN')
            sub_col2.operator("scene.wow_m2_animation_editor_object_remove", text='', icon='ZOOMOUT')

            try:
                cur_anim_pair = cur_anim_track.AnimPairs[cur_anim_track.ActiveObjectIndex]
            except IndexError:
                pass

        # Lower row of top layout: active item editing properties

        if cur_anim_track:
            split = layout.split(percentage=0.5)
            col = split.column()
            row = col.row()
            row_split = row.split(percentage=0.88)
            row_split.prop(cur_anim_track, "PlaybackSpeed", text='Speed')

            if cur_anim_pair:

                col = split.column()

                row = col.row()
                row_split = row.split(percentage=0.88)
                row_split.prop(cur_anim_pair, "Object", text='Object')

                row = col.row()
                row_split = row.split(percentage=0.88)
                row_split.prop(cur_anim_pair, "Action", text='Action')

            else:
                # Draw a placeholder row layout to avoid constant window resize

                col = split.column()

                row = col.row()
                row_split = row.split(percentage=0.88)
                row_split.label("Object: no object selected")

                row = col.row()
                row_split = row.split(percentage=0.88)
                row_split.label("Action: no action available")

            # Lower row: animation and blender playback properties

            row = layout.row()
            row.separator()

            split = layout.split(percentage=0.5)

            col = split.column()
            col.label("Animation properties", icon='UI')
            col.separator()
            col.prop(cur_anim_track, 'IsGlobalSequence', text='Global sequence')

            col = col.column()
            col.enabled = not cur_anim_track.IsGlobalSequence

            col.label(text='Animation ID:')
            row = col.row(align=True)
            row.prop(cur_anim_track, 'AnimationID', text="")
            row.operator("scene.wow_m2_animation_id_search", text="", icon='VIEWZOOM')
            col.label(text='Flags:')
            col.prop(cur_anim_track, 'Flags', text="Flags")
            col.prop(cur_anim_track, 'Movespeed', text="Move speed")
            col.prop(cur_anim_track, 'BlendTime', text="Blend time")
            col.prop(cur_anim_track, 'Frequency', text="Frequency")

            col.label(text='Random repeat:')
            col.prop(cur_anim_track, 'ReplayMin', text="Min")
            col.prop(cur_anim_track, 'ReplayMax', text="Max")

            col.label(text='Relations:')

            row = col.row(align=True)
            row.prop(cur_anim_track, 'VariationNext', text="Next")
            row.operator("scene.wow_m2_animation_switch_active_action", text="", icon='ZOOM_SELECTED').attr_name = 'VariationNext'

            row = col.row(align=True)
            row.prop(cur_anim_track, 'AliasNext', text="Next alias")
            row.operator("scene.wow_m2_animation_switch_active_action", text="", icon='ZOOM_SELECTED').attr_name = 'AliasNext'

            col = split.column()
            col.label('Playback properties', icon='TRIA_RIGHT_BAR')
            col.separator()

    def check(self, context): # redraw the popup window
        return True


#### UI List layouts ####

# Animation List

class AnimationEditor_AnimationList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            anim_ids = get_anim_ids(None, None)
            row = layout.row()
            row.label(anim_ids[int(item.AnimationID)][1] if not item.IsGlobalSequence else 'GlobalSeq', icon='SEQUENCE') # todo: Global sequence counter.
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
            row = layout.row()
            if item.Object:
                row.label(item.Object.name, icon='OBJECT_DATA')
            else:
                row.label("Empty slot", icon='MATCUBE')

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
            sequence.AnimPairs.remove(sequence.ActiveObjectIndex)

        except IndexError:
            self.report({'ERROR'}, "No animation sequence selected")
            return {'CANCELLED'}

        return {'FINISHED'}


###############################
## Property groups
###############################


def poll_object(self, obj):
    # TODO: safer polling

    if obj.name not in bpy.context.scene.objects:
        return False

    sequence = bpy.context.scene.WowM2Animations[bpy.context.scene.WowM2CurAnimIndex]

    for anim_pair in sequence.AnimPairs:
        if anim_pair.Object == obj:
            return False

    return True


def update_object(self, context):
    # TODO: safety checks

    sequence = bpy.context.scene.WowM2Animations[bpy.context.scene.WowM2CurAnimIndex]
    anim_pair = sequence.AnimPairs[sequence.ActiveObjectIndex]
    anim_pair.Object.animation_data_create()


def update_action(self, context):
    sequence = bpy.context.scene.WowM2Animations[bpy.context.scene.WowM2CurAnimIndex]
    anim_pair = sequence.AnimPairs[sequence.ActiveObjectIndex]
    anim_pair.Object.animation_data.action = anim_pair.Action


class WowM2AnimationEditorAnimationPairsPropertyGroup(bpy.types.PropertyGroup):

    Object = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Object",
        description="Object to animate in this animation sequence",
        poll=poll_object,
        update=update_object
    )

    Action = bpy.props.PointerProperty(
        type=bpy.types.Action,
        name="Action",
        description="Action to use in this animation sequence",
        update=update_action
    )


def update_playback_speed(self, context):
    sequence = bpy.context.scene.WowM2Animations[bpy.context.scene.WowM2CurAnimIndex]
    context.scene.render.fps_base = sequence.PlaybackSpeed


class WowM2AnimationEditorPropertyGroup(bpy.types.PropertyGroup):

    # Collection

    AnimPairs = bpy.props.CollectionProperty(type=WowM2AnimationEditorAnimationPairsPropertyGroup)

    ActiveObjectIndex = bpy.props.IntProperty()

    # Playback properties

    PlaybackSpeed = bpy.props.FloatProperty(
        name="Speed",
        description="Playback speed of this animation. Does not affect in-game playback speed.",
        min=0.1,
        max=120,
        default=1.0,
        update=update_playback_speed
    )

    # Actual properties

    IsGlobalSequence = bpy.props.BoolProperty(
        name="Global sequence",
        description='Global sequences are animation loops that are constantly played and blended with current animation',
        default=False
    )

    AnimationID = bpy.props.EnumProperty(
        name="AnimationID",
        description="WoW Animation ID",
        items=get_anim_ids
    )

    Flags = bpy.props.EnumProperty(
        name='Flags',
        description="WoW M2 Animation Flags",
        items=ANIMATION_FLAGS,
        options={"ENUM_FLAG"}
    )

    Movespeed = bpy.props.FloatProperty(
        name="Move speed",
        description="The speed the character moves with in this animation",
        min=0.0,
        default=1.0
    )

    BlendTime = bpy.props.IntProperty(
        name="Blend time",
        description="",
        min=0
    )

    Frequency = bpy.props.IntProperty(
        name="Frequency",
        description="This is used to determine how often the animation is played.",
        min=0,
        max=32767
    )

    AliasNext = bpy.props.PointerProperty(
        type=bpy.types.Action,
        name="Next alias",
        poll=lambda self, action: action != bpy.context.object.animation_data.action
    )

    VariationIndex = bpy.props.IntProperty(
        name="Variation index",
        description="For internal use only",
        min=0
    )

    VariationNext = bpy.props.PointerProperty(
        type=bpy.types.Action,
        name="Next alias"
    )

    ReplayMin = bpy.props.IntProperty(
        name="Replay Min",
        description="Client will pick a random number of repetitions within bounds if given.",
        min=0,
        max=65535
    )

    ReplayMax = bpy.props.IntProperty(
        name="Replay Max",
        description="Client will pick a random number of repetitions within bounds if given.",
        min=0,
        max=65535
    )


def update_animation(self, context):
    sequence = bpy.context.scene.WowM2Animations[bpy.context.scene.WowM2CurAnimIndex]
    context.scene.render.fps_base = sequence.PlaybackSpeed

    frame_end = 0
    for anim_pair in sequence.AnimPairs:
        if anim_pair.Object and anim_pair.Action:
            if anim_pair.Action and anim_pair.Action.frame_range[1] > frame_end:
                frame_end = anim_pair.Action.frame_range[1]

            anim_pair.Object.animation_data.action = anim_pair.Action

    context.scene.frame_start = 0
    context.scene.frame_end = frame_end


def register_wow_m2_animation_editor_properties():
    bpy.types.Scene.WowM2Animations = bpy.props.CollectionProperty(
        type=WowM2AnimationEditorPropertyGroup,
        name="Animations",
        description="WoW M2 animation sequences"
    )

    bpy.types.Scene.WowM2CurAnimIndex = bpy.props.IntProperty(update=update_animation)


def unregister_wow_m2_animation_editor_properties():
    del bpy.types.Scene.WowM2Animations
    del bpy.types.Scene.WowM2CurAnimIndex


def register_animation_editor():
    register_wow_m2_animation_editor_properties()


def unregister_animation_editor():
    unregister_wow_m2_animation_editor_properties()