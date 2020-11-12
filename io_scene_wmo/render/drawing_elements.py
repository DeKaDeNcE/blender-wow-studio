import traceback

from enum import IntEnum
from copy import copy
from typing import List
from functools import cmp_to_key, partial


class ElementTypes(IntEnum):
    GeneralMesh = 0
    AdtMesh = 1
    WmoMesh = 2
    OccludingQuery = 3
    M2Mesh = 4
    ParticleMesh = 5


class DrawingElements:

    def __init__(self):
        self.batches: List['M2DrawingBatch'] = []

    def add_batch(self, batch):
        self.batches.append(batch)

    def remove_batch(self, batch):
        self.batches.remove(batch)

    def draw(self):
        batches = copy(self.batches)

        try:
            sorted_indices = sorted(list(range(len(self.batches))), key=cmp_to_key(partial(self.sort_elements, self)))
        except IndexError:
            print('Skipping frame! Iterator invalidated!')
            self.draw()
            #traceback.print_exc()
            return

        #print("Began drawing")
        for batch_index in sorted_indices:
            batch = batches[batch_index]

            if batch.tag_free:
                continue

            try:
                batch.draw()
                #print(batch.draw_obj.bl_obj_name, batch.sort_distance)
            except:
                batch.free()
                print('Debug: Freeing batch from DrawingElements!')
                traceback.print_exc()
                self.draw()

    @staticmethod
    def sort_elements(self, a, b):

        batch_a = self.batches[a]
        batch_b = self.batches[b]

        #print("Comparing:", batch_a.draw_obj.bl_obj_name, batch_b.draw_obj.bl_obj_name)

        if not batch_a.draw_material:
            return -1

        if not batch_b.draw_material:
            return 1

        if batch_a.is_transparent > batch_b.is_transparent:
            return 1

        if batch_a.is_transparent < batch_b.is_transparent:
            return -1

        if batch_a.mesh_type > batch_b.mesh_type:
            return 1

        if batch_a.mesh_type < batch_b.mesh_type:
            return -1

        if batch_a.is_skybox > batch_b.is_skybox:
            return -1

        if batch_a.is_skybox < batch_b.is_skybox:
            return 1

        if batch_a.mesh_type == ElementTypes.M2Mesh and batch_a.is_transparent and batch_b.is_transparent:
            if batch_a.priority_plane != batch_b.priority_plane:
                return -1 if batch_b.priority_plane > batch_a.priority_plane else 1

            if batch_a.sort_distance > batch_b.sort_distance:
                return -1

            if batch_a.sort_distance < batch_b.sort_distance:
                return 1

            if batch_b.layer != batch_a.layer:
                return -1 if batch_b.layer < batch_a.layer else 1

        if batch_a.mesh_type == ElementTypes.ParticleMesh and batch_b.mesh_type == ElementTypes.ParticleMesh:
            if batch_a.priority_plane != batch_b.priority_plane:
                return -1 if batch_b.priority_plane > batch_a.priority_plane else 1

            if batch_a.sort_distance > batch_b.sort_distance:
                return -1
            if batch_a.sort_distance < batch_b.sort_distance:
                return 1

        if batch_a.draw_material.blend_mode.index != batch_b.draw_material.blend_mode.index:
            return -1 if batch_a.draw_material.blend_mode.index < batch_b.draw_material.blend_mode.index else 1

        '''
        min_tex_count = min(batch_a.texture_count, batch_b.texture_count)
        for i in range(min_tex_count):
            if batch_a.m_texture[i] != batch_b.m_texture[i]:
                return batch_a.m_texture[i] < batch_b.m_texture[i]

        if batch_a.texture_count != batch_b.texture_count:
            return batch_a.texture_count < batch_b.texture_count

        '''

        """
        if batch_a.m_start != batch_b.m_start:
            return batch_a.m_start < batch_b.m_start

        if batch_a.m_end != batch_b.m_end:
            return batch_a.m_end < batch_b.m_end

        """

        return 1 if a > b else -1


