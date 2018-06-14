import bpy


class WowM2AnimationsPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_label = "M2 Animations"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.template_list("AnimationEditor_AnimationList", "", context.scene, "wow_m2_animations", context.scene,
                          "wow_m2_cur_anim_index")

        try:
            cur_anim_track = context.scene.wow_m2_animations[context.scene.wow_m2_cur_anim_index]

            row = col.row()
            row_split = row.split().row(align=True)
            row_split.prop(cur_anim_track, "playback_speed", text='Speed')

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

            col.separator()

        except IndexError:
            pass

        col.operator('scene.wow_animation_editor_toggle', text='Edit animations', icon='CLIP')

    @classmethod
    def poll(cls, context):
        return context.scene is not None and context.scene.WowScene.Type == 'M2'
