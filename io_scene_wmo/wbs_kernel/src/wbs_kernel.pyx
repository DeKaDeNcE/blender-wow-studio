cimport wbs_kernel
from cython.operator cimport dereference

from typing import List

cdef class CM2DrawingMesh:
    cdef M2DrawingMesh* draw_mesh
    cdef vector[M2DrawingBatch*]* batches

    def __cinit__(self, uintptr_t mesh_pointer):
       self.draw_mesh = new M2DrawingMesh(mesh_pointer)
       self.batches = NULL

    def update_geometry(self, bool is_indexed=True):
        return self.draw_mesh.update_geometry(is_indexed)

    def update_mesh_pointer(self, uintptr_t mesh_pointer):
        self.draw_mesh.update_mesh_pointer(mesh_pointer) 

    def get_drawing_batches(self) -> List[CM2DrawingBatch]:
        self.batches = self.draw_mesh.get_drawing_batches()

        batches = [CM2DrawingBatch(<uintptr_t>batch_ptr) for batch_ptr in dereference(self.batches)]

        return batches

    def update_buffers(self):
        self.draw_mesh.run_buffer_updates()

    def __dealloc__(self):
       del self.draw_mesh


cdef class CM2DrawingBatch:
    cdef M2DrawingBatch* draw_batch

    def __cinit__(self, uintptr_t draw_batch_ptr):
       self.draw_batch = <M2DrawingBatch*>draw_batch_ptr

    def set_program(self, int shader_program):
        self.draw_batch.set_program(shader_program)

    def create_vao(self):
        self.draw_batch.create_vao()

    def get_mat_id(self):
        return self.draw_batch.get_mat_id()

    def draw(self):
        self.draw_batch.draw()

    @property
    def bb_center(self):
        cdef float* bb_center = self.draw_batch.get_bb_center()
        return bb_center[0], bb_center[1], bb_center[2]

    @property
    def sort_radius(self):
        return self.draw_batch.get_sort_radius()

cdef class OpenGLUtils:

    @staticmethod
    def init_glew():
        COpenGLUtils.glew_init()

    @staticmethod
    def glBlendFuncSeparate(int srcRGB, int dstRGB, int srcAlpha, int dstAlpha):
         COpenGLUtils.set_blend_func(srcRGB, dstRGB, srcAlpha, dstAlpha)



