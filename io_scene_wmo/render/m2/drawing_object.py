import traceback
import bpy
import numpy as np

from typing import List

from .drawing_batch import M2DrawingBatch


class M2DrawingObject:
    __slots__ = (
        'drawing_mgr',
        'rig',
        'batches',
        'bone_matrices',
        'placement_matrix',
        'context'
    )

    def __init__(self
                 , rig: bpy.types.Object
                 , drawing_mgr: 'M2DrawingManager'
                 , context: bpy.types.Context):

        self.context = context

        if rig.type != 'ARMATURE':
            raise Exception('Error: object \"{}\" is not an armature object.'.format(rig.name))

        self.drawing_mgr = drawing_mgr
        self.rig = rig
        self.batches: Dict[M2DrawingBatch] = []

        # uniform data
        self.bone_matrices = np.empty((len(self.rig.pose.bones), 16), 'f')

        self.create_batches_from_armature(rig)
        self.update_bone_matrices()

    def update_bone_matrices(self):
        # update bone transform matrices
        for i, pbone in enumerate(self.rig.pose.bones):
            self.bone_matrices[i] = [j[i] for i in range(4) for j in self.rig.convert_space(pose_bone=pbone,
                                                                                            matrix=pbone.matrix_channel,
                                                                                            from_space='POSE',
                                                                                            to_space='WORLD')]

    def draw(self):
        broken_batches = []

        for batch in self.batches:

            try:
                batch.draw()
            except:
                broken_batches.append(batch)
                traceback.print_exc()

        for batch in broken_batches:
            batch.free_textures()
            self.batches.remove(batch)

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