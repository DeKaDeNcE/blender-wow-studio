import bpy
import bgl

from .drawing_manager import DrawingManager
from .utils import render_debug
from .bgl_ext import create_framebuffer, glCheckError
from ..wbs_kernel.wbs_kernel import OpenGLUtils


class WoWRenderEngine(bpy.types.RenderEngine):
    # These three members are used by blender to set up the
    # RenderEngine; define its internal name, visible name and capabilities.
    bl_idname = "WOW"
    bl_label = "WoW"
    bl_use_preview = False
    bl_use_eevee_viewport = True

    # Init is called whenever a new render engine instance is created. Multiple
    # instances may exist at the same time, for example for a viewport and final
    # render.
    def __init__(self):

        self.glew_init = False
        self.first_time = True
        self.draw_manager = DrawingManager(bpy.context)

        render_debug('Instantiated render engine.')

    # When the render engine instance is destroy, this is called. Clean up any
    # render engine data here, for example stopping running render threads.
    def __del__(self):
        render_debug('Freed render engine.')

    # This is the method called by Blender for both final renders (F12) and
    # small preview for materials, world and lights.
    def render(self, depsgraph):
        scene = depsgraph.scene
        scale = scene.render.resolution_percentage / 100.0
        self.size_x = int(scene.render.resolution_x * scale)
        self.size_y = int(scene.render.resolution_y * scale)

        # Fill the render result with a flat color. The framebuffer is
        # defined as a list of pixels, each pixel itself being a list of
        # R,G,B,A values.
        if self.is_preview:
            color = [0.1, 0.2, 0.1, 1.0]
        else:
            color = [0.2, 0.1, 0.1, 1.0]

        pixel_count = self.size_x * self.size_y
        rect = [color] * pixel_count

        # Here we write the pixel values to the RenderResult
        result = self.begin_result(0, 0, self.size_x, self.size_y)
        layer = result.layers[0].passes["Combined"]
        layer.rect = rect
        self.end_result(result)

    # For viewport renders, this method gets called once at the start and
    # whenever the scene or 3D viewport changes. This method is where data
    # should be read from Blender in the same thread. Typically a render
    # thread will be started to do the work while keeping Blender responsive.
    def view_update(self, context, depsgraph):
        # depsgraph = context.evaluated_depsgraph_get()

        if not self.glew_init:
            OpenGLUtils.init_glew()
            self.glew_init = True

        region = context.region
        view3d = context.space_data
        scene = depsgraph.scene

        # Get viewport dimensions
        dimensions = region.width, region.height

        if self.first_time:
            self.first_time = False
            self.draw_manager.init_datablocks(depsgraph)
        else:
            self.draw_manager.update_render_data(depsgraph)

        '''
        # Loop over all object instances in the scene.
        if first_time or depsgraph.id_type_updated('OBJECT'):
            for instance in depsgraph.object_instances:
                pass
                
        '''

        render_debug('Num unfreed materials: {}\n'
                     'Num unfreed drawing objects: {}\n'
                     'Num unfreed batches: {}\n'.format(
            len(self.draw_manager.draw_materials),
            len(self.draw_manager.m2_objects),
            len(self.draw_manager.draw_elements.batches))
        )

    # For viewport renders, this method is called whenever Blender redraws
    # the 3D viewport. The renderer is expected to quickly draw the render
    # with OpenGL, and not perform other expensive work.
    # Blender will draw overlays for selection and editing on top of the
    # rendered image automatically.

    def view_draw(self, context, depsgraph):

        # buf = bgl.Buffer(bgl.GL_INT, 1)
        # bgl.glGetIntegerv(bgl.GL_FRAMEBUFFER_BINDING, buf)
        # cur_fbo = buf.to_list()[0]
        # del buf
        #
        # region = context.region
        # view3d = context.space_data
        # scene = depsgraph.scene
        #
        # # Get viewport dimensions
        # width, height = region.width, region.height
        #
        # bgl.glBindFramebuffer(bgl.GL_FRAMEBUFFER, self.fbo_id)

        #bgl.glEnable(bgl.GL_BLEND)
        #bgl.glBlendFunc(bgl.GL_ONE, bgl.GL_ONE_MINUS_SRC_ALPHA)
        #self.bind_display_space_shader(context.scene)

        self.draw_manager.draw()

        bgl.glColorMask(False, False, False, True)
        bgl.glClearColor(0, 0, 0, 1.0)
        bgl.glClear(bgl.GL_COLOR_BUFFER_BIT)

        #self.unbind_display_space_shader()
        #bgl.glDisable(bgl.GL_BLEND)

        # glCheckError('post-draw-all')
        #
        # bgl.glBindFramebuffer(bgl.GL_DRAW_FRAMEBUFFER, cur_fbo)
        # bgl.glDrawBuffer(bgl.GL_BACK)
        #
        # bgl.glBindFramebuffer(bgl.GL_READ_FRAMEBUFFER, self.fbo_id)
        # bgl.glReadBuffer(bgl.GL_COLOR_ATTACHMENT0)
        #
        # glCheckError('bind fbos')
        #
        # bgl.glBlitFramebuffer(
        #                   0, 0, width, height,
        #                   0, 0, width, height,
        #                   bgl.GL_COLOR_BUFFER_BIT | bgl.GL_DEPTH_BUFFER_BIT,
        #                   bgl.GL_NEAREST)
        #
        # glCheckError('blit')
        #
        # bgl.glBindFramebuffer(bgl.GL_FRAMEBUFFER, cur_fbo)


# RenderEngines also need to tell UI Panels that they are compatible with.
# We recommend to enable all panels marked as BLENDER_RENDER, and then
# exclude any panels that are replaced by custom panels registered by the
# render engine, or that are not supported.
def get_panels():
    exclude_panels = {
    }

    panels = []
    for panel in bpy.types.Panel.__subclasses__():
        if hasattr(panel, 'COMPAT_ENGINES'): # and 'BLENDER_RENDER' in panel.COMPAT_ENGINES:
            if panel.__name__ not in exclude_panels:
                panels.append(panel)

    return panels


def register():
    # Register the RenderEngine
    bpy.utils.register_class(WoWRenderEngine)

    for panel in get_panels():
        panel.COMPAT_ENGINES.add('WOW')


def unregister():
    bpy.utils.unregister_class(WoWRenderEngine)

    for panel in get_panels():
        if 'WOW' in panel.COMPAT_ENGINES:
            panel.COMPAT_ENGINES.remove('WOW')


if __name__ == "__main__":
    register()