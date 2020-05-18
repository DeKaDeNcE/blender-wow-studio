import bpy
import gpu
import traceback
from typing import List, Tuple, Dict, Union
from mathutils import Vector

from .m2.shaders import M2ShaderPermutations
from .m2.drawing_object import M2DrawingObject
from .m2.drawing_batch import M2DrawingBatch
from .m2.drawing_material import M2DrawingMaterial
from .drawing_elements import DrawingElements
from .utils import render_debug

from profilehooks import profile

from bgl import *


class DrawingManager:

    sun_dir_and_fog_start: Tuple[float, float, float, float]
    sun_color_and_fog_end: Tuple[float, float, float, float]
    ambient_light: Tuple[float, float, float]
    fog_color: Tuple[float, float, float]

    def __init__(self, context, handler_mode=False):
        self.context: bpy.types.Context = context
        self.shaders = M2ShaderPermutations()
        self.m2_objects: Dict[str, M2DrawingObject] = {}
        self.bound_textures: Dict[str, Tuple[int, List[M2DrawingMaterial]]] = {}
        self.drawing_materials: Dict[str, Tuple[M2DrawingMaterial, List[M2DrawingBatch]]] = {}
        self.drawing_elements = DrawingElements()
        self.batch_cache: Dict[str, Tuple[gpu.types.GPUBatch, List[M2DrawingBatch]]] = {}

        if handler_mode:
            self.handle = bpy.types.SpaceView3D.draw_handler_add(self._draw_callback, (self,), 'WINDOW', 'POST_VIEW')

        # get active viewport
        self.region_3d: bpy.types.SpaceView3D = bpy.context.space_data.region_3d
        self.region: bpy.types.Region = self._get_active_region()

        # depth pass
        self.depth_tex_id_buf = Buffer(GL_INT, 1)
        glGenTextures(1, self.depth_tex_id_buf)
        self.depth_tex_bindcode = self.depth_tex_id_buf.to_list()[0]
        self.depth_buf = Buffer(GL_FLOAT, self.region.width * self.region.height)

        # uniform data
        self._update_global_uniforms()

        render_debug('Instantiated drawing manager.')

    def _update_global_uniforms(self):
        sun_dir = Vector(self.context.scene.wow_render_settings.sun_direction)
        sun_dir.negate()
        self.sun_dir_and_fog_start = (*sun_dir[:3], self.context.scene.wow_render_settings.fog_start)
        self.sun_color_and_fog_end = (*self.context.scene.wow_render_settings.ext_dir_color[:3],
                                      self.context.scene.wow_render_settings.fog_end)
        self.ambient_light = self.context.scene.wow_render_settings.ext_ambient_color
        self.fog_color = self.context.scene.wow_render_settings.fog_color

    @profile
    def update_render_data(self, depsgraph: bpy.types.Depsgraph):

        try:

            for update in depsgraph.updates:

                if isinstance(update.id, bpy.types.Scene):
                    self._update_global_uniforms()

                elif isinstance(update.id, bpy.types.Object):

                    if update.id.type == 'ARMATURE':
                        self._m2_handle_armature_update(update)

                    elif update.id.type == 'MESH':
                        self._m2_handle_mesh_update(update)

                elif isinstance(update.id, bpy.types.Material):

                    render_debug('Detected update for material \"{}\"'.format(update.id.name))
                    draw_mat, _ = self.drawing_materials.get(update.id.name, (None, None))

                    if draw_mat:
                        draw_mat.update_uniform_data()

            self._m2_remove_invalid_children()

        except:
            render_debug('Exception occured on depsgraph update of render data. Traceback is below.')
            traceback.print_exc()  # DEBUG

    def _m2_handle_armature_update(self, update: bpy.types.DepsgraphUpdate):
        render_debug('Detected update for armature \"{}\"'.format(update.id.name))

        draw_obj = self.m2_objects.get(update.id.name)

        if not draw_obj:
            draw_obj = self.queue_for_drawing(update.id.original)

        if update.is_updated_geometry and update.id.original.children:
            draw_obj.update_bone_matrices()

    def _m2_handle_mesh_update(self, update: bpy.types.DepsgraphUpdate):
        render_debug('Detected update for mesh \"{}\"'.format(update.id.name))

        if update.id.original.parent and update.id.original.parent.type == 'ARMATURE':

            draw_obj = self.m2_objects.get(update.id.original.parent.name)

            if draw_obj and update.id.original.name not in draw_obj:
                draw_obj.create_batch_from_object(update.id.original)

                old_draw_obj = self.m2_objects.get(update.id.original.name)

                if old_draw_obj:
                    old_draw_obj.free()

        elif not update.id.original.parent or (update.id.original.parent
                                               and update.id.original.parent.type not in {'ARMATURE', 'EMPTY'}):

            self.queue_for_drawing(update.id.original, is_armature=False)

    def _m2_remove_invalid_children(self):

        for m2 in self.m2_objects.values():
            for batch in list(m2.batches.values()):
                rig = m2.bl_rig
                if batch.bl_obj not in self.recurse_children(rig) and not batch.bl_obj == rig:
                    batch.free()

    @staticmethod
    def recurse_children(obj: bpy.types.Object) -> List[bpy.types.Object]:
        children = []

        for child in obj.children:
            children.append(child)
            children.extend(DrawingManager.recurse_children(child))

        return children

    def queue_for_drawing(self, obj: bpy.types.Object, is_armature: bool = True) -> Union[M2DrawingObject, None]:
        try:

            if is_armature:

                if obj.type != 'ARMATURE':
                    raise Exception('Error: M2 should be represented as armature object. Failed to queue for drawing.')

                draw_obj = M2DrawingObject(obj, self, self.context)
                draw_obj.create_batches_from_armature(obj)
            else:
                draw_obj = M2DrawingObject(obj, self, self.context, has_bones=False)
                draw_obj.create_batch_from_object(obj)

        except IndexError:
            traceback.print_exc()  # DEBUG
            return None

        self.m2_objects[obj.name] = draw_obj

        return draw_obj

    @profile
    def draw(self):

        self.region_3d = bpy.context.space_data.region_3d
        self.region = self._get_active_region()

        self.drawing_elements.draw()

        #self._render_depth_opengl()
        #self.render_depth_texture()

        #self._destroy_depthbuffer_texture()

    def _linearize(self, depth):
        znear = self.region_3d.clip_start
        zfar = self.region_3d.clip_end

        return (*([(-zfar * znear / (depth * (zfar - znear) - zfar)) / zfar] * 3), 1.0)

    def render_depth_texture(self):
        """ Render scene depth_tex_bindcode into texture """

        width, height = self.region.width, self.region.height

        image_name = "DepthBuffer"
        if image_name not in bpy.data.images:
            image = bpy.data.images.new(image_name, width, height)
        else:
            return

        image.scale(width, height)

        image.pixels = [y for x in [self._linearize(v) for v in self.depth_buf] for y in x]

    @staticmethod
    def _get_active_region() -> bpy.types.Region:

        for region in bpy.context.area.regions:
            if region.type == 'WINDOW':
                return region

    def _render_depth_opengl(self):

        width, height = self.region.width, self.region.height

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.depth_tex_bindcode)

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

    def free(self):
        for draw_obj in list(self.m2_objects.values()):
            draw_obj.free()

        render_debug('Freed drawing manager.')

    def __contains__(self, item):

        for draw_obj in self.m2_objects.values():
            if draw_obj.rig == item:
                return True

        return False

    def __del__(self):
        if hasattr(self, 'handle'):
            bpy.types.SpaceView3D.draw_handler_remove(self.handle, 'WINDOW')