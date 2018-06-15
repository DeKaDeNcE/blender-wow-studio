import bpy
from math import ceil
from ....utils import wrap_text


class CameraErrors:
    INVALID_OBJ = 0
    DUPLICATE_OBJ = 1
    BAD_GEOMETRY = 2


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


def validate_camera_path(m2_camera):
    errors = []

    checked_curve_objs = []
    for i, curve in enumerate(m2_camera.animation_curves):

        # check if the used curve is None or invalid
        if curve.object is None or curve.object.name not in bpy.context.scene.objects:
            errors.append(("Curve slot #{} is invalid.".format(i), CameraErrors.INVALID_OBJ))
            continue

        # check if the same path is used twice
        if curve.object in checked_curve_objs:
            errors.append(("Curve \"{}\" is used more than once.".format(curve.object.name), CameraErrors.DUPLICATE_OBJ))

        checked_curve_objs.append(curve.object)

        # check curve's geometry validity
        if len(curve.object.data.splines) > 1:
            errors.append(("Curve \"{}\" contains more than 1 spline.".format(curve.object.name),
                           CameraErrors.BAD_GEOMETRY))
            continue

        if len(curve.object.data.splines[0].bezier_points) > 2:
            errors.append(("Curve \"{}\" contains more than 2 bezier points.".format(curve.object.name),
                           CameraErrors.BAD_GEOMETRY))
            continue

        next_index = i + 1
        if len(m2_camera.animation_curves) > next_index:
            next_segment = m2_camera.animation_curves[next_index]

            if not next_segment.object \
            or not len(next_segment.object.data.splines) \
            or not len(next_segment.object.data.splines[0].bezier_points):
                continue

            last_point = curve.object.data.splines[0].bezier_points[1]
            next_point = next_segment.object.data.splines[0].bezier_points[0]

            if last_point.co != next_point.co \
            or last_point.handle_left != next_point.handle_left \
            or last_point.handle_right != next_point.handle_right:
                errors.append(("Curve \"{}\" does not connect to next segment properly.".format(curve.object.name),
                               CameraErrors.BAD_GEOMETRY))

    return errors


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

        split = col.row().split(percentage=0.94)
        row_split = split.row(align=True)
        row_split.operator("object.wow_m2_camera_curve_compose", text='Compose curve', icon='RNDCURVE')
        row_split.operator("object.wow_m2_camera_curve_decompose", text='Decompose curve', icon='CURVE_PATH')
        split.row()

        # draw error box
        errors = sorted(validate_camera_path(context.object.wow_m2_camera), key=lambda x: x[1])
        if errors:
            col.separator()
            col.label('Errors:')
            box = col.box()

            for error_msg, error_code in errors:
                sub_box = box.box()
                lines = wrap_text(ceil(bpy.context.area.width / 9), error_msg)
                sub_box.row(align=True).label(lines[0], icon='ERROR')

                for i in range(1, len(lines)):
                    sub_box.row(align=True).label(lines[i])

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
    bl_label = 'Add curve segment'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        context.object.wow_m2_camera.animation_curves.add()
        context.object.wow_m2_camera.cur_anim_curve_index = len(context.object.wow_m2_camera.animation_curves) - 1

        return {'FINISHED'}


class WowM2Camera_CurveRemove(bpy.types.Operator):
    bl_idname = 'object.wow_m2_camera_curve_remove'
    bl_label = 'Remove curve segment'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        context.object.wow_m2_camera.animation_curves.remove(context.object.wow_m2_camera.cur_anim_curve_index)

        return {'FINISHED'}


class WowM2Camera_CurveMove(bpy.types.Operator):
    bl_idname = 'object.wow_m2_camera_curve_move'
    bl_label = 'Move curve segment'
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


class WowM2Camera_CurveCompose(bpy.types.Operator):
    bl_idname = 'object.wow_m2_camera_curve_compose'
    bl_label = 'Compose curve'
    bl_description = 'Convert current curves to a single curve'
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):

        if validate_camera_path(context.object.wow_m2_camera):  # checking for errors
            self.report({'ERROR'}, 'M2 curve path contains errors.')
            return {'CANCELLED'}

        camera_props = context.object.wow_m2_camera

        curve = bpy.data.curves.new(name='BakedCurve', type='CURVE')
        curve_obj = bpy.data.objects.new(name='BakedCurve', object_data=curve)
        bpy.context.scene.objects.link(curve_obj)
        curve.dimensions = '3D'
        curve.resolution_u = 64

        spline = curve.splines.new('BEZIER')
        spline.resolution_u = 64
        spline.bezier_points.add(count=len(camera_props.animation_curves))

        curve_first_point = spline.bezier_points[0]
        segment_first_point = camera_props.animation_curves[0].object.data.splines[0].bezier_points[0]

        curve_first_point.co = segment_first_point.co
        curve_first_point.handle_right = segment_first_point.handle_right
        curve_first_point.handle_left = segment_first_point.handle_left

        for i, segment in enumerate(camera_props.animation_curves):
            segment_point = segment.object.data.splines[0].bezier_points[1]
            curve_point = spline.bezier_points[i + 1]
            curve_point.co = segment_point.co
            curve_point.handle_right = segment_point.handle_right
            curve_point.handle_left = segment_point.handle_left

        return {'FINISHED'}


class WowM2Camera_CurveDecompose(bpy.types.Operator):
    bl_idname = 'object.wow_m2_camera_curve_decompose'
    bl_label = 'Decompose curve'
    bl_description = 'Convert a single curves to timed curve segments'
    bl_options = {'REGISTER', 'INTERNAL'}

    curve_obj = bpy.props.StringProperty(
        name='Curve',
        description='Curve object to be decomposed to timed curve segments'
    )

    preserve_timing = bpy.props.BoolProperty(
        name='Preserve Timing',
        description='Align decomposed curve segments to already existing timed slots.',
        default=True
    )

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop_search(self, 'curve_obj', context.scene, 'objects', icon='OBJECT_DATA')
        layout.prop(self, 'preserve_timing')

    def execute(self, context):

        try:
            curve_obj = bpy.data.objects[self.curve_obj]
        except KeyError:
            self.report({'ERROR'}, 'No curve object is selected.')
            return {'FINISHED'}

        if curve_obj.type != 'CURVE':
            self.report({'ERROR'}, 'Select a bezier curve object instead.')
            return {'FINISHED'}

        if not curve_obj.data.splines or len(curve_obj.data.splines[0].bezier_points) < 2:
            self.report({'ERROR'}, 'Badly formed curve.')
            return {'FINISHED'}

        if not curve_obj.data.splines[0].type == 'BEZIER':
            self.report({'ERROR'}, 'Select a bezier curve object instead.')
            return {'FINISHED'}

        camera_props = context.object.wow_m2_camera

        # remove old referenced segment objects
        for segment in camera_props.animation_curves:

            old_segment = segment.object
            segment.object = None
            bpy.data.objects.remove(old_segment, do_unlink=True)

        # remove slots based on user's choice
        if not self.preserve_timing:
            camera_props.animation_curves.clear()

        # create segment curves
        new_segments = []
        points = curve_obj.data.splines[0].bezier_points
        for i in range(1, len(points)):
            first_point = points[i - 1]
            last_point = points[i]

            name = "{}_BakedSegment".format(curve_obj.name)
            curve = bpy.data.curves.new(name=name, type='CURVE')
            new_obj = bpy.data.objects.new(name=name, object_data=curve)
            bpy.context.scene.objects.link(new_obj)

            curve.dimensions = '3D'
            curve.resolution_u = 64

            spline = curve.splines.new('BEZIER')
            spline.resolution_u = 64
            spline.bezier_points.add(count=1)

            seg_first_point = spline.bezier_points[0]
            seg_last_point = spline.bezier_points[1]

            seg_first_point.co = first_point.co
            seg_first_point.handle_right = first_point.handle_right
            seg_first_point.handle_left = first_point.handle_left

            seg_last_point.co = last_point.co
            seg_last_point.handle_right = last_point.handle_right
            seg_last_point.handle_left = last_point.handle_left

            new_segments.append(new_obj)

        # fill in overlapping slots
        segments_overlap = 0
        for i, segment in enumerate(camera_props.animation_curves):
            segment.object = new_segments[i]
            segments_overlap += 1

        # create new slots for extra segments
        for i in range(segments_overlap, len(new_segments) - segments_overlap):
            segment = camera_props.animation_curves.add()
            segment.object = new_segments[i]

        return {'FINISHED'}


def register():
    bpy.types.Object.wow_m2_camera = bpy.props.PointerProperty(type=WowM2CameraPropertyGroup)


def unregister():
    del bpy.types.Object.wow_m2_camera
