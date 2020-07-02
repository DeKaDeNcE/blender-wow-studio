from libc.stdint cimport uintptr_t, uint32_t
from libcpp.vector cimport vector
from libcpp cimport bool


cdef extern from "render/m2_drawing_mesh.hpp" namespace "wbs_kernel":
    cdef cppclass M2DrawingMesh:
        M2DrawingMesh(uintptr_t mesh_pointer) except +
        void update_mesh_pointer(uintptr_t mesh_pointer) except +
        bool update_geometry(bool is_indexed) except +
        void allocate_buffers(uint32_t n_vertices_new, uint32_t n_triangles_new) except +
        void init_opengl_buffers() except +
        void run_buffer_updates() except +
        vector[M2DrawingBatch*]* get_drawing_batches() except +


cdef extern from "render/m2_drawing_batch.hpp" namespace "wbs_kernel":
    cdef cppclass M2DrawingBatch:

        M2DrawingBatch(M2DrawingMesh *draw_mesh, short mat_id) except +
        void set_tri_start(int triangle_start) except +
        void set_n_tris(int n_triangles) except +
        int get_n_tris() except +
        int get_tri_start() except +
        void create_vao() except +
        void set_program(int shader_program) except +
        void draw() except +
        int get_mat_id() except +
        float* get_bb_center() except +
        float get_sort_radius() except +


cdef extern from "render/opengl_utils.hpp" namespace "wbs_kernel":

    cdef cppclass COpenGLUtils:

        @staticmethod
        void glew_init() except +

        @staticmethod
        void set_blend_func(int srcRGB, int dstRGB, int srcAlpha, int dstAlpha) except +

