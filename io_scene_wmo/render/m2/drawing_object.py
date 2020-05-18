import traceback
import bpy
import numpy as np

from mathutils import Matrix
from typing import Dict

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
        'is_skybox',
        'has_bones'
    )

    def __init__(self
                 , rig: bpy.types.Object
                 , drawing_mgr: 'M2DrawingManager'
                 , context: bpy.types.Context
                 , is_skybox: bool = False
                 , has_bones: bool = True):

        self.context = context
        self.drawing_mgr = drawing_mgr
        self.bl_rig_name = rig.name
        self.is_skybox = is_skybox
        self.batches: Dict[str, M2DrawingBatch] = {}
        self.has_bones = has_bones

        # uniform data
        if has_bones:
            self.bone_matrices = np.empty((len(rig.pose.bones), 16), 'f')
            self.update_bone_matrices()
        else:
            self.bone_matrices = np.zeros((1, 16), 'f')
            self.bone_matrices[0] = [j[i] for i in range(4) for j in Matrix.Identity(4)]

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

            self.create_batch_from_object(obj)

    def create_batch_from_object(self, obj: bpy.types.Object):
        self.batches[obj.name] = M2DrawingBatch(obj, self, self.context)

    def free(self):

        for batch in list(self.batches.values()):
            batch.free()

        del self.batches
        del self.drawing_mgr.m2_objects[self.bl_rig_name]

        render_debug('Freed drawing object \"{}\"'.format(self.bl_rig_name))

    def __contains__(self, item):
        return item in self.batches


