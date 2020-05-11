import bpy
from enum import IntEnum
from functools import cmp_to_key

from ..utils.misc import singleton


class ElementTypes(IntEnum):
    GeneralMesh = 0
    AdtMesh = 1
    WmoMesh = 2
    OccludingQuery = 3
    M2Mesh = 4
    ParticleMesh = 5


@singleton
class DrawingElements:

    def __init__(self):
        self.batches = []

    def add_batch(self, batch):
        self.batches.append(batch)

    def draw(self):

        for batch_index in sorted(list(range(len(self.batches))), key=cmp_to_key(self.sort_elements)):
            self.batches[batch_index].draw()

    @staticmethod
    def sort_elements(a, b):

        drawing_elements = DrawingElements()

        batch_a = drawing_elements.batches[a]
        batch_b = drawing_elements.batches[b]

        if batch_a.is_transparent > batch_b.is_transparent:
            return -1

        if batch_a.is_transparent < batch_b.is_transparent:
            return 1

        if batch_a.mesh_type > batch_b.mesh_type:
            return -1

        if batch_a.mesh_type < batch_b.mesh_type:
            return 1

        '''
        if batch_a.render_order != batch_b.render_order:
            if not batch_a.is_transparent:
                return batch_a.render_order < batch_b.render_order
            else:
                return batch_a.render_order > batch_b.render_order
                
        '''

        if batch_a.is_skybox > batch_b.is_skybox:
            return 1

        if batch_a.is_skybox < batch_b.is_skybox:
            return -1

        if batch_a.mesh_type == ElementTypes.M2Mesh and batch_a.is_transparent and batch_b.is_transparent:
            if batch_a.priority_plane != batch_b.priority_plane:
                return batch_b.priority_plane > batch_a.priority_plane

            if batch_a.sort_distance > batch_b.sort_distance:
                return 1

            if batch_a.sort_distance < batch_b.sort_distance:
                return -1

            if batch_a.m2_draw_obj_idx > batch_b.m2_draw_obj_idx:
                return 1

            if batch_a.m2_draw_obj_idx < batch_b.m2_draw_obj_idx:
                return -1

            if batch_b.layer != batch_a.layer:
                return batch_b.layer < batch_a.layer

        if batch_a.mesh_type == ElementTypes.ParticleMesh and batch_b.mesh_type == ElementTypes.ParticleMesh:
            if batch_a.priority_plane != batch_b.priority_plane:
                return batch_b.priority_plane > batch_a.priority_plane

            if batch_a.sort_distance > batch_b.sort_distance:
                return 1
            if batch_a.sort_distance < batch_b.sort_distance:
                return -1

        '''
        if batch_a.m_bindings != batch_b.m_bindings:
            return batch_a.m_bindings > batch_b.m_bindings

        '''

        if batch_a.draw_material.blend_mode.index != batch_b.draw_material.blend_mode.index:
            return batch_a.draw_material.blend_mode.index < batch_b.draw_material.blend_mode.index

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

        return a > b


