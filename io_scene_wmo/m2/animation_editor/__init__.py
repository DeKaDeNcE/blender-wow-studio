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
        return wm.invoke_props_dialog(self, width=820)

    def draw(self, context):
        layout = self.layout
        split = layout.split(percentage=0.5)

        # Top row - collections: animations, objects
        # Animations column

        col = split.column()
        col.label('Animations:', icon='CLIP')

        row = col.row()
        sub_col1 = row.column()
        sub_col1.template_list("AnimationEditor_AnimationList", "", context.scene, "wow_m2_animations", context.scene,
                               "wow_m2_cur_anim_index")
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
            cur_anim_track = context.scene.wow_m2_animations[context.scene.wow_m2_cur_anim_index]

        except IndexError:
            pass

        cur_anim_pair = None

        if cur_anim_track and context.scene.wow_m2_cur_anim_index >= 0:

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
        else:
            col.label('No sequence selected.', icon='ERROR')

        # Lower row of top layout: active item editing properties
        split = layout.split(percentage=0.5)
        col = split.column()

        if cur_anim_track and context.scene.wow_m2_cur_anim_index >= 0:
            row = col.row()
            row_split = row.split(percentage=0.935)
            row_split = row_split.row(align=True)
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

            row = row_split.row(align=True)
            row.operator("scene.wow_m2_animation_editor_seq_deselect", text='', icon='ARMATURE_DATA')

            if cur_anim_pair:

                col = split.column()

                row_split = col.row().split(percentage=0.93)
                row = row_split.row(align=True)
                row_split = row.split(percentage=0.30)
                row_split.row().label('Object' if cur_anim_pair.Type == 'OBJECT' else 'Scene')
                row = row_split.row(align=True)
                row.prop(cur_anim_pair, "Type", text="", expand=True)

                if cur_anim_pair.Type == 'OBJECT':
                    row.prop(cur_anim_pair, "Object", text='')

                    if cur_anim_pair.Object:
                        row.row().operator("scene.wow_m2_animation_editor_select_object",
                                            text='', icon='ZOOM_SELECTED').name = cur_anim_pair.Object.name
                    else:
                        sub_row = row.row()
                        sub_row.enabled = False
                        sub_row.label("", icon='ZOOM_SELECTED')
                else:
                    row.prop(cur_anim_pair, "Scene", text='')

                row_split = col.row().split(percentage=0.93)
                row = row_split.row(align=True)
                col = row.column()
                col.scale_x = 0.54
                col.label("Action:")

                col = row.column(align=True)
                col.scale_x = 1.0 if cur_anim_pair.Action else 1.55
                col.template_ID(cur_anim_pair, "Action", new="scene.wow_m2_animation_editor_action_add",
                                unlink="scene.wow_m2_animation_editor_action_unlink")

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
            row = col.row(align=True)
            row.enabled = cur_anim_track.IsAlias
            row.label('', icon='FILE_TICK' if cur_anim_track.AliasNext < len(context.scene.wow_m2_animations) else 'ERROR')
            row.prop(cur_anim_track, 'AliasNext', text="Next alias")
            row.operator("scene.wow_m2_animation_editor_go_to_index", text="", icon='ZOOM_SELECTED').anim_index = \
                cur_anim_track.AliasNext

            col = split.column()
            col.enabled = not cur_anim_track.IsGlobalSequence
            col.label(text='Flags:')
            col.separator()
            col.prop(cur_anim_track, 'Flags', text="Flags")
            col.separator()

    def check(self, context):  # redraw the popup window
        return True


class AnimationEditor_IDSearch(bpy.types.Operator):
    bl_idname = "scene.wow_m2_animation_id_search"
    bl_label = "Search animation ID"
    bl_description = "Select WoW M2 animation ID"
    bl_options = {'REGISTER', 'INTERNAL'}
    bl_property = "AnimationID"

    AnimationID = bpy.props.EnumProperty(items=get_anim_ids)

    def execute(self, context):

        context.scene.wow_m2_animations[bpy.context.scene.wow_m2_cur_anim_index].AnimationID = self.AnimationID

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

def update_animation_collection(self, context):

    anim_ids = get_anim_ids(None, None)
    index_cache = {}

    for i, anim in enumerate(bpy.context.scene.wow_m2_animations):
        anim_id = int(anim.AnimationID) if not anim.IsGlobalSequence else -1
        last_idx = index_cache.get(anim_id)

        if last_idx is not None:
            anim.ChainIndex = last_idx + 1
            index_cache[anim_id] += 1
        else:
            anim.ChainIndex = 0
            index_cache[anim_id] = 0

        if not anim.IsGlobalSequence:
            if not anim.IsAlias:
                anim.Name = "#{} {} ({})".format(i, anim_ids[int(anim.AnimationID)][1], anim.ChainIndex)
            else:
                anim.Name = "#{} {} ({}) -> #{}".format(i, anim_ids[int(anim.AnimationID)][1],
                                                        anim.ChainIndex, anim.AliasNext)
        else:
            anim.Name = "#{} Global Sequence ({})".format(i, anim.ChainIndex)


class AnimationEditor_AnimationList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        self.use_filter_show = True

        if self.layout_type in {'DEFAULT', 'COMPACT'}:

            row = layout.row()
            row.label(item.Name, icon='SEQUENCE')

            if not item.IsGlobalSequence:
                if item.IsAlias and len(data.wow_m2_animations) < item.AliasNext:
                    row.label("", icon='ERROR')
                row.prop(item, "IsPrimarySequence", emboss=False, text="",
                         icon='POSE_HLT' if item.IsPrimarySequence else 'OUTLINER_DATA_POSE')
                row.prop(item, "IsAlias", emboss=False, text="",
                         icon='GHOST_ENABLED' if item.IsAlias else 'GHOST_DISABLED')
            else:
                row.prop(item, 'StashToNLA', emboss=False, text="",
                         icon='RESTRICT_RENDER_OFF' if item.StashToNLA else 'RESTRICT_RENDER_ON')

            row.prop(item, "LiveUpdate", emboss=False, text="", icon='PMARKER_SEL' if item.LiveUpdate else 'PMARKER')

        elif self.layout_type in {'GRID'}:
            pass

    def filter_items(self, context, data, propname):

        col = getattr(data, propname)
        filter_name = self.filter_name.lower()

        flt_flags = [self.bitflag_filter_item
                     if any(filter_name in filter_set for filter_set in (str(i), item.Name.lower()))
                     else 0 for i, item in enumerate(col, 1)
                     ]

        if self.use_filter_sort_alpha:
            flt_neworder = [x[1] for x in sorted(
                zip(
                    [x[0] for x in sorted(enumerate(col),
                                          key=lambda x: x[1].Name.split()[1] + x[1].Name.split()[2])], range(len(col))
                )
            )
            ]
        else:
            flt_neworder = []

        return flt_flags, flt_neworder


class AnimationEditor_SequenceAdd(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_animation_editor_seq_add'
    bl_label = 'Add WoW animation'
    bl_description = 'Add WoW animation sequence'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        context.scene.wow_m2_animations.add()
        context.scene.wow_m2_cur_anim_index = len(context.scene.wow_m2_animations) - 1
        update_animation_collection(None, None)

        return {'FINISHED'}


class AnimationEditor_SequenceRemove(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_animation_editor_seq_remove'
    bl_label = 'Remove WoW animation'
    bl_description = 'Remove WoW animation sequence'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        context.scene.wow_m2_animations.remove(context.scene.wow_m2_cur_anim_index)
        update_animation_collection(None, None)

        return {'FINISHED'}


class AnimationEditor_SequenceMove(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_animation_editor_seq_move'
    bl_label = 'Move WoW animation'
    bl_description = 'Move WoW animation sequence'
    bl_options = {'REGISTER', 'INTERNAL'}

    direction = bpy.props.StringProperty()

    def execute(self, context):

        if self.direction == 'UP':
            context.scene.wow_m2_animations.move(context.scene.wow_m2_cur_anim_index, context.scene.wow_m2_cur_anim_index - 1)
            context.scene.wow_m2_cur_anim_index -= 1
        elif self.direction == 'DOWN':
            context.scene.wow_m2_animations.move(context.scene.wow_m2_cur_anim_index, context.scene.wow_m2_cur_anim_index + 1)
            context.scene.wow_m2_cur_anim_index += 1
        else:
            raise NotImplementedError("Only UP and DOWN movement in the UI list in supported.")

        update_animation_collection(None, None)

        return {'FINISHED'}


class AnimationEditor_SequenceDeselect(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_animation_editor_seq_deselect'
    bl_label = 'Get back to rest pose'
    bl_description = 'Deselect WoW animation sequence'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):

        context.scene.wow_m2_cur_anim_index = -1

        for obj in context.scene.objects:
            if obj.animation_data:
                obj.animation_data.action = None

            # TODO: set to rest pose here

        return {'FINISHED'}


class AnimationEditor_GoToAnimation(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_animation_editor_go_to_index'
    bl_label = 'Go to this WoW animation'
    bl_options = {'REGISTER', 'INTERNAL'}

    anim_index = bpy.props.IntProperty()

    def execute(self, context):
        if self.anim_index < len(context.scene.wow_m2_animations):
            context.scene.wow_m2_cur_anim_index = self.anim_index

            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Invalid animation index")
            return {'CANCELLED'}


# Object list
class AnimationEditor_SequenceObjectList(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        self.use_filter_show = True

        ob = data
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row()
            if item.Type == 'OBJECT' and item.Object:

                icon = 'OBJECT_DATA'

                if item.Object.type == 'ARMATURE':
                    icon = 'OUTLINER_OB_ARMATURE'
                elif item.Object.type == 'LAMP':
                    icon = 'LAMP_SUN',
                elif item.Object.type == 'CAMERA':
                    icon = 'RESTRICT_RENDER_OFF'
                elif item.Object.type == 'EMPTY':
                    if item.Object.wow_m2_attachment.Enabled:
                        icon = 'CONSTRAINT'
                    elif item.Object.wow_m2_event.Enabled:
                        icon = 'PLUGIN'
                    elif item.Object.wow_m2_camera.enabled:
                        icon = 'BBOX'
                    elif item.Object.wow_m2_uv_transform.Enabled:
                        icon = 'ASSET_MANAGER'

                row.label(item.Object.name, icon=icon)
            elif item.Type == 'SCENE' and item.Scene:
                row.label(item.Scene.name, icon='SCENE_DATA')
            else:
                row.label("Empty slot", icon='MATCUBE')

        elif self.layout_type in {'GRID'}:
            pass

    def filter_items(self, context, data, propname):

        col = getattr(data, propname)
        filter_name = self.filter_name.lower()

        flt_flags = [self.bitflag_filter_item
                     if any(filter_name in filter_set for filter_set in (str(i), item.Object.name.lower()
                                                                         if item.Object else 'Empty slot'))
                     else 0 for i, item in enumerate(col, 1)
                     ]

        if self.use_filter_sort_alpha:
            flt_neworder = [x[1] for x in sorted(
                zip([x[0] for x in sorted(enumerate(col),key=lambda x: x[1].Object.name
                                          if x[1].Object else 'Empty slot')], range(len(col)))
            )
            ]
        else:
            flt_neworder = []

        return flt_flags, flt_neworder


class AnimationEditor_ObjectAdd(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_animation_editor_object_add'
    bl_label = 'Add object'
    bl_description = 'Add new object to selected animation sequence'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):

        scene = context.scene

        try:
            sequence = scene.wow_m2_animations[scene.wow_m2_cur_anim_index]
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
            sequence = scene.wow_m2_animations[scene.wow_m2_cur_anim_index]
            sequence.AnimPairs.remove(sequence.ActiveObjectIndex)

        except IndexError:
            self.report({'ERROR'}, "No animation sequence selected")
            return {'CANCELLED'}

        return {'FINISHED'}


class AnimationEditor_ObjectSelect(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_animation_editor_select_object'
    bl_label = 'Select object'
    bl_options = {'REGISTER', 'INTERNAL'}

    name = bpy.props.StringProperty()

    def execute(self, context):
        bpy.data.objects[self.name].select = True
        return {'FINISHED'}


class AnimationEditor_ActionAdd(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_animation_editor_action_add'
    bl_label = 'Add new action'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        scene = context.scene
        sequence = scene.wow_m2_animations[scene.wow_m2_cur_anim_index]
        anim_pair = sequence.AnimPairs[sequence.ActiveObjectIndex]
        anim_pair.Action = bpy.data.actions.new(name="")
        anim_pair.Action.use_fake_user = True

        return {'FINISHED'}


class AnimationEditor_ActionUnlink(bpy.types.Operator):
    bl_idname = 'scene.wow_m2_animation_editor_action_unlink'
    bl_label = 'Unlink action'
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        sequence = context.scene.wow_m2_animations[context.scene.wow_m2_cur_anim_index]
        anim_pair = sequence.AnimPairs[sequence.ActiveObjectIndex]
        return anim_pair.Action is not None

    def execute(self, context):
        scene = context.scene
        sequence = scene.wow_m2_animations[scene.wow_m2_cur_anim_index]
        anim_pair = sequence.AnimPairs[sequence.ActiveObjectIndex]
        anim_pair.Action = None
        return {'FINISHED'}

###############################
## Property groups
###############################


def poll_object(self, obj):
    # TODO: safer polling

    if obj.name not in bpy.context.scene.objects:
        return False

    sequence = bpy.context.scene.wow_m2_animations[bpy.context.scene.wow_m2_cur_anim_index]

    for anim_pair in sequence.AnimPairs:
        if anim_pair.Object == obj:
            return False

    if obj.type not in ('CAMERA', 'ARMATURE', 'LAMP', 'EMPTY'):
        return False

    if obj.type == 'EMPTY' and not (obj.wow_m2_uv_transform.Enabled
                                    or obj.wow_m2_attachment.Enabled
                                    or obj.wow_m2_event.Enabled
                                    or obj.wow_m2_camera.enabled):
        return False

    return True


def poll_scene(self, scene):

    if scene.name != bpy.context.scene.name:
        return False

    sequence = bpy.context.scene.wow_m2_animations[bpy.context.scene.wow_m2_cur_anim_index]

    for anim_pair in sequence.AnimPairs:
        if anim_pair.Scene == scene:
            return False

    return True


def update_object(self, context):

    sequence = bpy.context.scene.wow_m2_animations[bpy.context.scene.wow_m2_cur_anim_index]
    anim_pair = sequence.AnimPairs[sequence.ActiveObjectIndex]

    if anim_pair.Object:
        anim_pair.Object.animation_data_create()
        anim_pair.Object.animation_data.action_blend_type = 'ADD'


def update_scene(self, context):
    sequence = bpy.context.scene.wow_m2_animations[bpy.context.scene.wow_m2_cur_anim_index]
    anim_pair = sequence.AnimPairs[sequence.ActiveObjectIndex]

    if anim_pair.Scene:
        anim_pair.Scene.animation_data_create()
        anim_pair.Scene.animation_data.action_blend_type = 'ADD'


def update_action(self, context):
    sequence = bpy.context.scene.wow_m2_animations[bpy.context.scene.wow_m2_cur_anim_index]
    anim_pair = sequence.AnimPairs[sequence.ActiveObjectIndex]
    if anim_pair.Type == 'OBJECT' and anim_pair.Object and anim_pair.Object.animation_data:
        anim_pair.Object.animation_data.action = anim_pair.Action
    elif anim_pair.Type == 'SCENE' and anim_pair.Scene and anim_pair.Scene.animation_data:
        anim_pair.Scene.animation_data.action = anim_pair.Action


def update_anim_pair_type(self, context):
    sequence = bpy.context.scene.wow_m2_animations[bpy.context.scene.wow_m2_cur_anim_index]
    anim_pair = sequence.AnimPairs[sequence.ActiveObjectIndex]
    if anim_pair.Type == 'OBJECT':
        anim_pair.Scene = None
    else:
        anim_pair.Object = None


class WowM2AnimationEditorAnimationPairsPropertyGroup(bpy.types.PropertyGroup):

    Type = bpy.props.EnumProperty(
        name="Type",
        description="Defines whether object or scene is animated",
        items=[('OBJECT', "Object", "", 'OBJECT_DATA', 0),
               ('SCENE', "Scene", "", 'SCENE_DATA', 1)],
        default='OBJECT',
        update=update_anim_pair_type
    )

    Object = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Object",
        description="Object to animate in this animation sequence",
        poll=poll_object,
        update=update_object
    )

    Scene = bpy.props.PointerProperty(
        type=bpy.types.Scene,
        name="Scene",
        description="Scene to animate in this animation sequence",
        poll=poll_scene,
        update=update_scene
    )

    Action = bpy.props.PointerProperty(
        type=bpy.types.Action,
        name="Action",
        description="Action to use in this animation sequence",
        update=update_action
    )


def update_playback_speed(self, context):
    sequence = bpy.context.scene.wow_m2_animations[bpy.context.scene.wow_m2_cur_anim_index]
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

    update_animation_collection(None, None)


def update_stash_to_nla(self, context):
    if self.StashToNLA and not context.scene.wow_m2_animations[context.scene.wow_m2_cur_anim_index] == self:
        for anim_pair in self.AnimPairs:
            if (anim_pair.Object or anim_pair.Scene) and anim_pair.Action:
                obj = anim_pair.Object if anim_pair.Type == 'OBJECT' else anim_pair.Scene

                nla_track = obj.animation_data.nla_tracks.get(anim_pair.Action.name)

                if not nla_track:
                    nla_track = obj.animation_data.nla_tracks.new()
                    nla_track.is_solo = False
                    nla_track.lock = True
                    nla_track.mute = False

                nla_track.name = anim_pair.Action.name

                for strip in nla_track.strips:
                    nla_track.strips.remove(strip)

                strip = nla_track.strips.new(name=anim_pair.Action.name, start=0, action=anim_pair.Action)
                strip.blend_type = 'ADD'

                if obj.animation_data.action:
                    strip.frame_end = obj.animation_data.action.frame_range[1]
    else:
        for anim_pair in self.AnimPairs:
            if (anim_pair.Object or anim_pair.Scene) and anim_pair.Action:
                obj = anim_pair.Object if anim_pair.Type == 'OBJECT' else anim_pair.Scene
                nla_track = obj.animation_data.nla_tracks.get(anim_pair.Action.name)

                if nla_track:
                    obj.animation_data.nla_tracks.remove(nla_track)

    update_scene_frame_range()


class WowM2AnimationEditorPropertyGroup(bpy.types.PropertyGroup):

    # Collection

    AnimPairs = bpy.props.CollectionProperty(type=WowM2AnimationEditorAnimationPairsPropertyGroup)

    ActiveObjectIndex = bpy.props.IntProperty(update=update_animation_collection)

    ChainIndex = bpy.props.IntProperty()

    Name = bpy.props.StringProperty()

    # Playback properties

    PlaybackSpeed = bpy.props.FloatProperty(
        name="Speed",
        description="Playback speed of this animation. Does not affect in-game playback speed.",
        min=0.1,
        max=120,
        default=1.0,
        update=update_playback_speed
    )

    StashToNLA = bpy.props.BoolProperty(
        name='Enable persistent playing',
        description='Enable persistent playing of this global sequences, no matter what animation is chosen',
        update=update_stash_to_nla
    )

    LiveUpdate = bpy.props.BoolProperty(
        name='Live update',
        description='Automatically update materials that have live update turned on. May decrease FPS.'
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
        items=get_anim_ids,
        update=update_animation_collection
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

    AliasNext = bpy.props.IntProperty(
        name='Alias',
        description='Index of animation used as a alias for this one',
        min=0,
        update=update_animation_collection
    )


def update_scene_frame_range():
    frame_end = 0

    for obj in bpy.context.scene.objects:
        if obj.animation_data and not obj.wow_m2_event.Enabled:  # TODO: wtf?

            # set scene frame range based on action length
            if obj.animation_data.action and obj.animation_data.action.frame_range[1] > frame_end:
                frame_end = obj.animation_data.action.frame_range[1]

            # set scene frame range based on camera animation length
            if obj.type == 'CAMERA' or (obj.type == 'EMPTY' and obj.wow_m2_camera.enanled):

                max_frame = 0
                for curve in obj.wow_m2_camera.animation_curves:
                    max_frame += curve.duration

                if max_frame > frame_end:
                    frame_end = max_frame

            for nla_track in obj.animation_data.nla_tracks:
                if not nla_track.mute:
                    for strip in nla_track.strips:
                        if strip.frame_end > frame_end:
                            frame_end = strip.frame_end

    # set scene frame range based on scene action length
    if bpy.context.scene.animation_data and bpy.context.scene.animation_data.action:
        if bpy.context.scene.animation_data.action.frame_range[1] > frame_end:
            frame_end = bpy.context.scene.animation_data.action.frame_range[1]

    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = frame_end

    # update NLA tracks length
    for anim in bpy.context.scene.wow_m2_animations:
        if anim.IsGlobalSequence and anim.StashToNLA:
            for anim_pair in anim.AnimPairs:
                if anim_pair.Object and anim_pair.Action:
                    nla_track = anim_pair.Object.animation_data.nla_tracks.get(anim_pair.Action.name)

                    if nla_track and len(nla_track.strips):
                        nla_track.strips[-1].frame_end = bpy.context.scene.frame_end


def update_animation(self, context):
    try:
        sequence = context.scene.wow_m2_animations[bpy.context.scene.wow_m2_cur_anim_index]
    except IndexError:
        return

    context.scene.render.fps_base = sequence.PlaybackSpeed

    for obj in context.scene.objects:
        if obj.animation_data:
            obj.animation_data.action = None

            if obj.type == 'ARMATURE':
                for bone in obj.pose.bones:
                    bone.location = (0, 0, 0)
                    bone.rotation_mode = 'QUATERNION'
                    bone.rotation_quaternion = (1, 0, 0, 0)
                    bone.scale = (1, 1, 1)

    for color in context.scene.wow_m2_colors:
        color.Color = (0.5, 0.5, 0.5, 1.0)

    for trans in context.scene.wow_m2_transparency:
        trans.Value = 1.0

    if bpy.context.scene.animation_data:
        bpy.context.scene.animation_data.action = None

    global_seqs = []

    for i, anim in enumerate(context.scene.wow_m2_animations):

        if i == context.scene.wow_m2_cur_anim_index:
            for anim_pair in anim.AnimPairs:
                if anim_pair.Type == 'OBJECT':
                    anim_pair.Object.animation_data.action = anim_pair.Action
                else:
                    anim_pair.Scene.animation_data.action = anim_pair.Action

        if anim.IsGlobalSequence:
            global_seqs.append(anim)

    update_scene_frame_range()

    for seq in global_seqs:
        update_stash_to_nla(seq, bpy.context)


def register_wow_m2_animation_editor_properties():

    bpy.types.Scene.wow_m2_animations = bpy.props.CollectionProperty(
        type=WowM2AnimationEditorPropertyGroup,
        name="Animations",
        description="WoW M2 animation sequences"
    )

    bpy.types.Scene.wow_m2_cur_anim_index = bpy.props.IntProperty(
        name='M2 Animation',
        description='Current WoW M2 animation',
        update=update_animation
    )


def unregister_wow_m2_animation_editor_properties():
    del bpy.types.Scene.wow_m2_animations
    del bpy.types.Scene.wow_m2_cur_anim_index


def register_animation_editor():
    register_wow_m2_animation_editor_properties()


def unregister_animation_editor():
    unregister_wow_m2_animation_editor_properties()