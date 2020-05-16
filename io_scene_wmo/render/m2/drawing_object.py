import traceback
import bpy
import numpy as np

from copy import copy
from typing import List

from .drawing_batch import M2DrawingBatch
from ..utils import render_debug


class M2DrawingObject:
    __slots__ = (
        'drawing_mgr',
        'bl_rig_name',
        'batches',
        'bone_matrices',
        'placement_matrix',
        'context',
        'is_skybox'
    )

    def __init__(self
                 , rig: bpy.types.Object
                 , drawing_mgr: 'M2DrawingManager'
                 , context: bpy.types.Context
                 , is_skybox: bool = False):

        self.context = context

        if rig.type != 'ARMATURE':
            raise Exception('Error: object \"{}\" is not an armature object.'.format(rig.name))

        self.drawing_mgr = drawing_mgr
        self.bl_rig_name = rig.name
        self.is_skybox = is_skybox
        self.batches: List[M2DrawingBatch] = []

        # uniform data
        self.bone_matrices = np.empty((len(rig.pose.bones), 16), 'f')

        self.update_bone_matrices()
        self.create_batches_from_armature(rig)

        render_debug('Instantiated drawing object \"{}\"'.format(self.bl_rig_name))

    @property
    def bl_rig(self):

        try:
            return bpy.data.objects[self.bl_rig_name]
        except KeyError:
            self.free()

    def update_bone_matrices(self):
        rig = self.bl_rig
        for i, pbone in enumerate(rig.pose.bones):
            self.bone_matrices[i] = [j[i] for i in range(4) for j in pbone.matrix_channel]

    def create_batches_from_armature(self, rig: bpy.types.Object):

        for obj in filter(lambda x: x.type == 'MESH', rig.children):

            # Limit bone influences to 4. TODO: rework to be non-destructive!
            '''
            if obj.vertex_groups:
                active_obj = bpy.context.view_layer.objects.active
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.vertex_group_limit_total()
                bpy.context.view_layer.objects.active = active_obj
                
            '''

            self._create_batch_from_object(obj)

    def _create_batch_from_object(self, obj: bpy.types.Object):
        self.batches.append(M2DrawingBatch(obj, self, self.context))

    def free(self):

        for batch in copy(self.batches):
            batch.free()

        del self.batches
        del self.drawing_mgr.m2_objects[self.bl_rig_name]

        render_debug('Freed drawing object \"{}\"'.format(self.bl_rig_name))