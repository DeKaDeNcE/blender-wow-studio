import bpy

CLOSE_TO_ZERO = 5e-324


def skybox_follow_viewport_camera():

    viewport = bpy.app.driver_namespace.get('wow_viewport')

    if not viewport:
        return CLOSE_TO_ZERO

    if bpy.context.view_layer.objects.active:
        bpy.context.view_layer.objects.active.location = viewport.view_matrix.inverted().translation

    return 0.0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001


#def register():
   # bpy.app.timers.register(skybox_follow_viewport_camera, persistent=True)


#def unregister():
  #  bpy.app.timers.unregister(skybox_follow_viewport_camera)