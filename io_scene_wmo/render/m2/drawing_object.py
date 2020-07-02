import traceback
import bpy
import numpy as np

from mathutils import Matrix
from typing import List

from .drawing_batch import M2DrawingBatch
from ..utils import render_debug
from ...wbs_kernel.wbs_kernel import CM2DrawingMesh, CM2DrawingBatch
from ..bgl_ext import glCheckError


class M2DrawingObject:

    batches: List[CM2DrawingBatch]

    def __init__(self
                 , bl_obj: bpy.types.Object
                 , drawing_mgr: 'M2DrawingManager'
                 , context: bpy.types.Context
                 , is_skybox: bool = False):

        self.context = context
        self.draw_mgr = drawing_mgr
        self.bl_obj_name = bl_obj.name
        self.is_skybox = is_skybox
        self.is_dirty = True
        self.is_batching_valid = False

        self.mesh_ptr = bl_obj.data.as_pointer()
        self.c_mesh = CM2DrawingMesh(self.mesh_ptr)
        self.batches = []
        bl_obj.data.calc_loop_triangles()
        render_debug('Initialized drawing object \"{}\"'.format(self.bl_obj_name))

        self.update_geometry()

    def update_geometry(self, bl_obj: bpy.types.Object = None):
        if bl_obj:
            self.c_mesh.update_mesh_pointer(bl_obj.data.as_pointer())
            bl_obj.data.calc_loop_triangles()

        self.is_batching_valid = self.c_mesh.update_geometry(not(self.context.screen.is_animation_playing or self.bl_obj.mode != 'OBJECT'))

        self.is_dirty = True

    def update_geometry_opengl(self, bl_obj: bpy.types.Object = None):

        self.c_mesh.update_buffers()

        if not self.is_batching_valid:

            for batch in self.batches:
                batch.free()

            self.batches = \
                [M2DrawingBatch(c_batch, self, self.context) for c_batch in self.c_mesh.get_drawing_batches()]

        self.is_dirty = False

    @property
    def bl_obj(self):

        try:
            return bpy.data.objects[self.bl_obj_name]
        except KeyError:
            self.free()

    def free(self):

        for batch in self.batches:
            batch.free()

        del self.draw_mgr.m2_objects[self.bl_obj_name]

        render_debug('Freed drawing object \"{}\"'.format(self.bl_obj_name))

    '''
    def update_bone_matrices(self):
        rig = self.bl_rig
        for i, pbone in enumerate(rig.pose.bones):
            self.bone_matrices[i] = [j[i] for i in range(4) for j in pbone.matrix_channel]

    def create_batches_from_armature(self, rig: bpy.types.Object):

        for obj in filter(lambda x: x.type == 'MESH', rig.children):

            # Limit bone influences to 4. TODO: rework to be non-destructive!
            """
            if obj.vertex_groups:
                active_obj = bpy.context.view_layer.objects.active
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.vertex_group_limit_total()
                bpy.context.view_layer.objects.active = active_obj
                
            """

            self.create_batch_from_object(obj)

    def create_batch_from_object(self, obj: bpy.types.Object):
        self.batches[obj.name] = M2DrawingBatch(obj, self, self.context)
        
    '''




