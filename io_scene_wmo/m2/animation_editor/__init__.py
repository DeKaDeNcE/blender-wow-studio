import bpy

from ..ui.enums import get_anim_ids, ANIMATION_FLAGS

###############################
## User Interface
###############################

#### Pop-up dialog ####

class AnimationEditorDialog(bpy.types.Operator):
    bl_idname = 'scene.wow_animation_editor_toggle'
    bl_label = 'WoW M2 Animation Editor'

    is_playing_anim = False

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
        sub_col_parent = row.column()
        sub_col2 = sub_col_parent.column(align=True)
        sub_col2.operator("scene.wow_m2_animation_editor_seq_add", text='', icon='ZOOMIN')
        sub_col2.operator("scene.wow_m2_animation_editor_seq_remove", text='', icon='ZOOMOUT')

        sub_col_parent.separator()

        sub_col3 = sub_col_parent.column(align=True)
        sub_col3.operator("scene.wow_m2_animation_editor_seq_move", text='', icon='TRIA_UP').direction = 'UP'
        sub_col3.operator("scene.wow_m2_animation_editor_seq_move", text='', icon='TRIA_DOWN').direction = 'DOWN'

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
        split = layout.split(percentage=0.5)
        col = split.column()

        if cur_anim_track:
            row = col.row()
            row_split = row.split(percentage=0.88)
            row_split.prop(cur_anim_track, "PlaybackSpeed", text='Speed')

            if context.scene.sync_mode == 'AUDIO_SYNC' and context.user_preferences.system.audio_device == 'JACK':
                sub = row_split.row(align=True)
                sub.scale_x = 2.0
                sub.operator("screen.animation_play", text="", icon='PLAY')

            row = row_split.row(align=True)
            if not context.screen.is_animation_playing:
                if context.scene.sync_mode == 'AUDIO_SYNC' and context.user_preferences.system.audio_device == 'JACK':
                    sub = row.row(align=True)
                    sub.scale_x = 2.0
                    sub.operator("screen.animation_play", text="", icon='PLAY')
                else:
                    row.operator("screen.animation_play", text="", icon='PLAY_REVERSE').reverse = True
                    row.operator("screen.animation_play", text="", icon='PLAY')
            else:
                sub = row.row(align=True)
                sub.scale_x = 2.0
                sub.operator("screen.animation_play", text="", icon='PAUSE')

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
            layout.row().label("Animation properties", icon='UI')

            split = layout.split(percentage=0.5)

            col = split.column()
            col.separator()
            col.prop(cur_anim_track, 'IsGlobalSequence', text='Global sequence')

            col = col.column()
            col.enabled = not cur_anim_track.IsGlobalSequence

            row = col.row(align=True)
            row.label("Animation ID: ")
            anim_ids = get_anim_ids(None, None)
            row.operator("scene.wow_m2_animation_id_search", text=anim_ids[int(cur_anim_track.AnimationID)][1],
                         icon='VIEWZOOM')
            col.prop(cur_anim_track, 'Movespeed', text="Move speed")
            col.prop(cur_anim_track, 'BlendTime', text="Blend time")
            col.prop(cur_anim_track, 'Frequency', text="Frequency")

            col.label(text='Random repeat:')
            col.prop(cur_anim_track, 'ReplayMin', text="Min")
            col.prop(cur_anim_track, 'ReplayMax', text="Max")

            col.label(text='Relations:')
            col.prop(cur_anim_track, 'VariationNext', text="Next")
            col.prop(cur_anim_track, 'AliasNext', text="Next alias")

            col = split.column()
            col.enabled = not cur_anim_track.IsGlobalSequence
            col.label(text='Flags:')
            col.separator()
            col.prop(cur_anim_track, 'Flags', text="Flags")
            col.separator()

    def check(self, context): # redraw the popup window
        return True


class WowM2AnimationIDSearch(bpy.types.Operator):
    bl_idname = "scene.wow_m2_animation_id_search"
    bl_label = "Search animation ID"
    bl_description = "Select WoW M2 animation ID"
    bl_options = {'REGISTER', 'INTERNAL'}
    bl_property = "AnimationID"

    AnimationID = bpy.props.EnumProperty(items=get_anim_ids)

    def execute(self, context):

        context.scene.WowM2Animations[bpy.context.scene.WowM2CurAnimIndex].AnimationID = self.AnimationID

        # refresh UI after setting the property
        for region in context.area.regions:
            if region.type == "UI":
                region.tag_redraw()

        self.report({'INFO'}, "Animation ID set successfully.")
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


#### UI List layouts ####

# Animation List

def update_animation_colletion():

    index_cache = {}

    for anim in reversed(bpy.context.scene.WowM2Animations):
        anim_id = int(anim.AnimationID) if not anim.IsGlobalSequence else -1
        last_idx = index_cache.get(anim_id)

        if last_idx is not None:
            anim.ChainIndex = last_idx + 1
            index_cache[anim_id] += 1
        else:
            anim.ChainIndex = 0
            index_cache[anim_id] = 0


class AnimationEditor_AnimationList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        ob = data
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            anim_ids = get_anim_ids(None, None)

            if not item.IsGlobalSequence:
                anim_name = "{} ({})".format(anim_ids[int(item.AnimationID)][1], item.ChainIndex)
            else:
                anim_name = "Global Sequence ({})".format(item.ChainIndex)

            row = layout.row()
            row.label(anim_name, icon='SEQUENCE')

            if not item.IsGlobalSequence:
                row.prop(item, "IsPrimarySequence", emboss=False, text="", icon='POSE_HLT' if item.IsPrimarySequence else 'OUTLINER_DATA_POSE')
                row.prop(item, "IsAlias", emboss=False, text="", icon='GHOST_ENABLED' if item.IsAlias else 'GHOST_DISABLED')
        elif self.layout_type in {'GRID'}:
            pass


class AnimationEditor_SequenceAdd(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_animation_editor_seq_add'
    bl_label = 'Add WoW animation'
    bl_description = 'Add Wow animation sequence'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        sequence = context.scene.WowM2Animations.add()
        context.scene.WowM2CurAnimIndex = len(context.scene.WowM2Animations) - 1
        update_animation_colletion()

        return {'FINISHED'}


class AnimationEditor_SequenceRemove(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_animation_editor_seq_remove'
    bl_label = 'Remove WoW animation'
    bl_description = 'Remove Wow animation sequence'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):

        context.scene.WowM2Animations.remove(context.scene.WowM2CurAnimIndex)
        update_animation_colletion()

        return {'FINISHED'}


class AnimationEditor_SequenceMove(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_animation_editor_seq_move'
    bl_label = 'Move WoW animation'
    bl_description = 'Move Wow animation sequence'
    bl_options = {'REGISTER', 'INTERNAL'}

    direction = bpy.props.StringProperty()

    def execute(self, context):

        if self.direction == 'UP':
            context.scene.WowM2Animations.move(context.scene.WowM2CurAnimIndex, context.scene.WowM2CurAnimIndex - 1)
            context.scene.WowM2CurAnimIndex -= 1
        elif self.direction == 'DOWN':
            context.scene.WowM2Animations.move(context.scene.WowM2CurAnimIndex, context.scene.WowM2CurAnimIndex + 1)
            context.scene.WowM2CurAnimIndex += 1
        else:
            raise NotImplementedError("Only UP and DOWN movement in the UI list in supported.")

        update_animation_colletion()

        return {'FINISHED'}


# Object list

class AnimationEditor_SequenceObjectList(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            if item.Object:

                icon = 'OBJECT_DATA'

                if item.Object.type == 'ARMATURE':
                    icon = 'OUTLINER_OB_ARMATURE'
                elif item.Object.type == 'LAMP':
                    icon = 'LAMP_SUN',
                elif item.Object.type == 'CAMERA':
                    icon = 'RESTRICT_RENDER_OFF'
                elif item.Object.type == 'EMPTY':
                    if item.Object.empty_draw_type == 'SPHERE':
                        icon = 'CONSTRAINT'
                    elif item.Object.empty_draw_type == 'CUBE':
                        icon = 'PLUGIN'

                row.label(item.Object.name, icon=icon)
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

    if obj.type not in ('CAMERA', 'ARMATURE', 'LAMP', 'EMPTY'):
        return False

    if obj.type == 'EMPTY' and obj.empty_draw_type not in ('SPHERE', 'CUBE'):
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


def update_primary_sequence(self, context):
    flag_set = self.Flags
    is_changed = False

    if self.IsPrimarySequence and '32' not in flag_set:
        flag_set.add('32')
        is_changed = True
    elif not self.IsPrimarySequence and '32' in flag_set:
        flag_set.remove('32')
        is_changed = True

    if is_changed:
        self.Flags = flag_set


def update_animation_flags(self, context):
    self.IsPrimarySequence = '32' in self.Flags
    self.IsAlias = '64' in self.Flags


def update_alias(self, context):
    flag_set = self.Flags
    is_changed = False

    if self.IsAlias and '64' not in flag_set:
        flag_set.add('64')
        is_changed = True
    elif not self.IsAlias and '64' in flag_set:
        flag_set.remove('64')
        is_changed = True

    if is_changed:
        self.Flags = flag_set


class WowM2AnimationEditorPropertyGroup(bpy.types.PropertyGroup):

    # Collection

    AnimPairs = bpy.props.CollectionProperty(type=WowM2AnimationEditorAnimationPairsPropertyGroup)

    ActiveObjectIndex = bpy.props.IntProperty()

    ChainIndex = bpy.props.IntProperty()

    # Playback properties

    PlaybackSpeed = bpy.props.FloatProperty(
        name="Speed",
        description="Playback speed of this animation. Does not affect in-game playback speed.",
        min=0.1,
        max=120,
        default=1.0,
        update=update_playback_speed
    )

    # Layout properties
    IsPrimarySequence = bpy.props.BoolProperty(
        name='Primary sequence',
        description="If set, the animation data is in the .m2 file, else in an .anim file",
        default=True,
        update=update_primary_sequence
    )

    IsAlias = bpy.props.BoolProperty(
        name='Is alias',
        description="The animation uses transformation data from another sequence, changing its action won't affect the in-game track",
        default=False,
        update=update_alias
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
        options={"ENUM_FLAG"},
        update=update_animation_flags
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
    context.scene.frame_end = frame_end + 1


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