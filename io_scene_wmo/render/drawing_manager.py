import bpy
from typing import List, Tuple, Dict
from mathutils import Vector

from .m2.shaders import M2ShaderPermutations
from .m2.drawing_object import M2DrawingObject
from .m2.drawing_batch import M2DrawingBatch

from profilehooks import profile

from bgl import *


class DrawingManager:

    def __init__(self, context, handler_mode=False):
        self.context: bpy.types.Context = context
        self.shaders = M2ShaderPermutations()
        self.m2_objects: Dict[str, M2DrawingObject] = {}
        self.bound_textures: Dict[bpy.types.Image, Tuple[int, List[M2DrawingBatch]]] = {}

        if handler_mode:
            self.handle = bpy.types.SpaceView3D.draw_handler_add(self._draw_callback, (self,), 'WINDOW', 'POST_VIEW')

        # get active viewport
        self.region_3d: bpy.types.SpaceView3D = bpy.context.space_data.region_3d
        self.region: bpy.types.Region = self._get_active_region()

        # initialized via methods
        self.depth_tex_bindcode: int
        self.depth_tex_id_buf: Buffer
        self.depth_buf: Buffer

        # uniform data
        sun_dir = Vector(context.scene.wow_render_settings.sun_direction)
        sun_dir.negate()
        self.sun_dir_and_fog_start = (*sun_dir[:3], 10)
        self.sun_color_and_fog_end = (*context.scene.wow_render_settings.ext_dir_color[:3], 50)
        self.ambient_light = context.scene.wow_render_settings.ext_ambient_color
        self.fog_color = (0.1, 0.5, 0)

    @profile
    def update_render_data(self, depsgraph: bpy.types.Depsgraph):

        for update in depsgraph.updates:

            if isinstance(update.id, bpy.types.Scene):
                sun_dir = Vector(self.context.scene.wow_render_settings.sun_direction)
                sun_dir.negate()
                self.sun_dir_and_fog_start = (*sun_dir[:3], 10)
                self.sun_color_and_fog_end = (*self.context.scene.wow_render_settings.ext_dir_color[:3], 50)
                self.ambient_light = self.context.scene.wow_render_settings.ext_ambient_color
                self.fog_color = (0.1, 0.5, 0)

            if isinstance(update.id, bpy.types.Object):

                if update.id.type == 'ARMATURE':

                    draw_obj = self.m2_objects.get(update.id.name)

                    if update.is_updated_geometry:
                        draw_obj.update_bone_matrices()

    def queue_for_drawing(self, obj: bpy.types.Object):
        if obj.type != 'ARMATURE':
            raise Exception('Error: M2 should be represented as armature object. Failed to queue for drawing.')

        self.m2_objects[obj.name] = M2DrawingObject(obj, self, self.context)

    @profile
    def draw(self):

        #self._render_depth_opengl()

        self.region_3d = bpy.context.space_data.region_3d
        self.region = self._get_active_region()

        for m2 in self.m2_objects.values():
            m2.draw()

        #self.render_depth_texture()

        #self._destroy_depthbuffer_texture()

    def render_depth_texture(self) -> bpy.types.Image:
        """ Render scene depth_tex_bindcode into texture """

        width, height = self.region.width, self.region.height

        image_name = "depth_tex_bindcode"
        if not image_name in bpy.data.images:
            bpy.data.images.new(image_name, width, height)

        zfar = 1000.0
        znear = 1.0

        def linearize(depth):
            return (*([(-zfar * znear / (depth * (zfar - znear) - zfar)) / zfar] * 3), 1.0)

        image = bpy.data.images[image_name]
        image.scale(width, height)

        image.pixels = [y for x in [linearize(v) for v in self.depth_buf] for y in x]

        return image

    def _m2_draw_obj_from_bl_obj(self, obj: bpy.types.Object):
        for m2 in self.m2_objects:
            if m2.rig.name == obj.name:  # TODO: get rid of string comparison
                return m2

    @staticmethod
    def _get_active_region() -> bpy.types.Region:

        for region in bpy.context.area.regions:
            if region.type == 'WINDOW':
                return region

    def _render_depth_opengl(self):

        width, height = self.region.width, self.region.height

        self.depth_tex_id_buf = Buffer(GL_INT, 1)

        glGenTextures(1, self.depth_tex_id_buf)

        self.depth_tex_bindcode = self.depth_tex_id_buf.to_list()[0]

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.depth_tex_bindcode)

        self.depth_buf = Buffer(GL_FLOAT, width * height)
        glReadPixels(0, 0, width, height, GL_DEPTH_COMPONENT, GL_FLOAT, self.depth_buf)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, width, height,
                     0, GL_DEPTH_COMPONENT, GL_FLOAT, self.depth_buf)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER,
                        GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                        GL_NEAREST)

        glBindTexture(GL_TEXTURE_2D, self.depth_tex_bindcode)

        return self.depth_tex_bindcode

    def _destroy_depthbuffer_texture(self):
        glDeleteTextures(1, self.depth_tex_id_buf)

    @staticmethod
    def _draw_callback(self):
        self.draw()

    def __contains__(self, item):

        for draw_obj in self.m2_objects:
            if draw_obj.rig == item:
                return True

        return False

    def __del__(self):
        if hasattr(self, 'handle'):
            bpy.types.SpaceView3D.draw_handler_remove(self.handle, 'WINDOW')