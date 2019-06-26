import bpy

__reload_order_index__ = -1

###############################
## Camera Animation Driver Utils
###############################

def update_frame_range(obj):
    last_frame = 0

    for segment in obj.wow_m2_camera.animation_curves:
        first_frame = last_frame
        last_frame = first_frame + segment.duration
        segment.frame_start, segment.frame_end = first_frame, last_frame


def in_path_segment(constraint, obj, frame):
    segment = constraint.target
    if not segment:
        '''
        raise Exception('\nConstraint \"{}\" does not have a target or the target is invalid.'
                        ' Path animation cannot be evaluated.'.format(constraint.name))
        '''
        pass

    frame_start = 0
    frame_end = 0

    for curve in obj.wow_m2_camera.animation_curves:
        frame_start = frame_end
        frame_end = frame_start + curve.duration

        if segment == curve.object:
            break

    return frame_start <= frame < frame_end


def calc_segment_offset(constraint, obj, frame):
    segment = constraint.target
    if not segment:
        '''
        raise Exception('\nConstraint \"{}\" does not have a target or the target is invalid.'
                        ' Path animation cannot be evaluated.'.format(constraint.name))
        '''
        pass

    frame_end = 0

    for curve in obj.wow_m2_camera.animation_curves:
        frame_start = frame_end
        frame_end = frame_start + curve.duration

        if segment == curve.object:
            if not curve.duration:
                return 0

            return (frame - frame_start) / curve.duration

    return 0


def register():
    bpy.app.driver_namespace["in_path_segment"] = in_path_segment
    bpy.app.driver_namespace["calc_segment_offset"] = calc_segment_offset





