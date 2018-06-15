import bpy


def poll_camera_path_curve(self, obj):
    return obj.type == 'CURVE' and len(obj.data.splines) == 1 and len(obj.data.splines[0].bezier_points)


def update_camera_path_curve(self, context):
    # double check is needed because pippete selector ignores polling
    if self.object:
        self.name = self.object.name

        if not poll_camera_path_curve(None, self.object):
            self.object = None
            self.name = ""


def update_empty_draw_type(self, context):
    context.object.empty_draw_type = 'CONE'


def update_scene_animation(self, context):
    context.scene.wow_m2_cur_anim_index = context.scene.wow_m2_cur_anim_index


class WowM2CameraPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "M2 Camera"

    def draw_header(self, context):
        if context.object.type == 'EMPTY':
            self.layout.prop(context.object.wow_m2_camera, 'enabled', text='')

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        if context.object.type == 'CAMERA':
            col.prop(context.object.wow_m2_camera, 'type')
            col.separator()
        else:
            layout.enabled = context.object.wow_m2_camera.enabled
            self.bl_label = 'M2 Camera Target'

        col.label('Path curves:')
        row = col.row()
        sub_col1 = row.column()
        sub_col1.template_list("WowM2Camera_CurveList", "", context.object.wow_m2_camera, "animation_curves",
                               context.object.wow_m2_camera, "cur_anim_curve_index")

        sub_col_parent = row.column()
        sub_col2 = sub_col_parent.column(align=True)
        sub_col2.operator("object.wow_m2_camera_curve_add", text='', icon='ZOOMIN')
        sub_col2.operator("object.wow_m2_camera_curve_remove", text='', icon='ZOOMOUT')

        sub_col_parent.separator()

        sub_col3 = sub_col_parent.column(align=True)
        sub_col3.operator("object.wow_m2_camera_curve_move", text='', icon='TRIA_UP').direction = 'UP'
        sub_col3.operator("object.wow_m2_camera_curve_move", text='', icon='TRIA_DOWN').direction = 'DOWN'

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.WowScene.Type == 'M2'
                and context.object is not None
                and context.object.type == 'CAMERA' or (
                    context.object.type == 'EMPTY'
                    and not (context.object.wow_m2_attachment.enabled
                             or context.object.wow_m2_uv_transform.enabled
                             or context.object.wow_m2_event.enabled)
                )
        )


class WowM2CameraPathPropertyGroup(bpy.types.PropertyGroup):

    object = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name='Curve',
        description='Bezier curve with only one spline with 2 bezier points, defining camera path for a frame range.',
        poll=poll_camera_path_curve,
        update=update_camera_path_curve

    )

    duration = bpy.props.FloatProperty(
        name='Duration',
        description="Duration in frames of the camera travelling along this path segment.",
        min=0,
        update=update_scene_animation
    )

    # for internal use only
    name = bpy.props.StringProperty()


class WowM2CameraPropertyGroup(bpy.types.PropertyGroup):

    enabled = bpy.props.BoolProperty(
        name='Enabled',
        description='Enable this empty to be a camera target controller.',
        default=False,
        update=update_empty_draw_type
    )

    type = bpy.props.EnumProperty(
        name='Type',
        description='Type of this camera',
        items=[("0", "Portrait", "", 'OUTLINER_OB_ARMATURE', 0),
               ("1", "Character info", "", 'MOD_ARMATURE', 1),
               ("-1", "Flyby", "", 'FORCE_BOID', -1)]
    )

    animation_curves = bpy.props.CollectionProperty(type=WowM2CameraPathPropertyGroup)
    cur_anim_curve_index = bpy.props.IntProperty()


class WowM2Camera_CurveList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        self.use_filter_show = False

        if self.layout_type in {'DEFAULT', 'COMPACT'}:

            row = layout.row(align=True)
            row1 = row.row(align=True)
            row1.scale_x = 0.5
            row1.label("#{}".format(index), icon='CURVE_BEZCURVE')
            row.prop(item, "object", text="")
            row.prop(item, "duration")

        elif self.layout_type in {'GRID'}:
            pass


class WowM2Camera_CurveAdd(bpy.types.Operator):
    bl_idname = 'object.wow_m2_camera_curve_add'
    bl_label = 'Add WoW animation'
    bl_description = 'Add WoW animation sequence'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        context.object.wow_m2_camera.animation_curves.add()
        context.object.wow_m2_camera.cur_anim_curve_index = len(context.object.wow_m2_camera.animation_curves) - 1

        return {'FINISHED'}


class WowM2Camera_CurveRemove(bpy.types.Operator):
    bl_idname = 'object.wow_m2_camera_curve_remove'
    bl_label = 'Remove WoW animation'
    bl_description = 'Remove WoW animation sequence'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        context.object.wow_m2_camera.animation_curves.remove(context.object.wow_m2_camera.cur_anim_curve_index)

        return {'FINISHED'}


class WowM2Camera_CurveMove(bpy.types.Operator):
    bl_idname = 'object.wow_m2_camera_curve_move'
    bl_label = 'Move WoW animation'
    bl_description = 'Move WoW animation sequence'
    bl_options = {'REGISTER', 'INTERNAL'}

    direction = bpy.props.StringProperty()

    def execute(self, context):

        if self.direction == 'UP':
            context.object.wow_m2_camera.animation_curves.move(context.object.wow_m2_camera.cur_anim_curve_index,
                                                               context.object.wow_m2_camera.cur_anim_curve_index - 1)
            context.object.wow_m2_camera.cur_anim_curve_index -= 1

        elif self.direction == 'DOWN':
            context.object.wow_m2_camera.animation_curves.move(context.object.wow_m2_camera.cur_anim_curve_index,
                                                               context.object.wow_m2_camera.cur_anim_curve_index + 1)
            context.object.wow_m2_camera.cur_anim_curve_index += 1

        else:
            raise NotImplementedError("Only UP and DOWN movement in the UI list in supported.")

        return {'FINISHED'}


def register():
    bpy.types.Object.wow_m2_camera = bpy.props.PointerProperty(type=WowM2CameraPropertyGroup)


def unregister():
    del bpy.types.Object.wow_m2_camera
