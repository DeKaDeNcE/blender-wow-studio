#ifndef WBS_KERNEL_RENDER_M2_EDITABLE_HPP
#define WBS_KERNEL_RENDER_M2_EDITABLE_HPP

#include <m2_drawing_batch.hpp>

#include <unordered_map>
#include <cstdint>
#include <vector>
#include <tuple>

#define GLEW_STATIC
#include <glew.h>

extern "C"
{
#include <DNA_mesh_types.h>
#include <BKE_customdata.h>
};


namespace wbs_kernel
{
  class M2DrawingMesh
  {

  // Members
  public:
    // OpenGL buffers
    GLuint vbo;
    GLuint ibo;

    GLuint vbo_normals;
    GLuint vbo_tex_coords;
    GLuint vbo_tex_coords2;

  private:
    Mesh* mesh;

    float* vertices_co = nullptr;
    float* normals = nullptr;
    float* tex_coords = nullptr;
    float* tex_coords2 = nullptr;
    //float* weights = nullptr;

    int* tri_indices = nullptr;
    //int* bone_indices = nullptr;

    // loop triangles sorted by material index
    std::vector<MLoopTri*> loop_tris;

    // mapping of vertex duplication within mesh, used to construct VBO/IBO etc.
    std::unordered_map<int, std::vector<std::tuple<int, int, std::vector<std::pair<float, float>>, std::vector<int>>>> vertex_map;
    std::vector<int> batch_length;

    // drawing batches of this mesh
    std::vector<M2DrawingBatch*> drawing_batches;

    uint32_t n_vertices = 0;
    uint32_t n_triangles = 0;
    int n_materials = 0;
    int bl_n_materials = 0;

    bool is_indexed;

  // Methods
  public:
    M2DrawingMesh(uintptr_t mesh_pointer);
    void update_mesh_pointer(uintptr_t mesh_pointer);
    bool update_geometry(bool use_indexed);
    std::vector<M2DrawingBatch*>* get_drawing_batches();
    ~M2DrawingMesh();

  private:
    int create_vertex_map();
    bool update_geometry_indexed();
    bool update_geometry_nonindexed();
    void init_looptris();
    bool validate_batches(int n_vertices_new);
    void allocate_buffers(uint32_t n_vertices_new, uint32_t n_triangles_new);
    void init_opengl_buffers();
    void update_opengl_buffers();

    // Blender
    static void* CustomData_get_n(const CustomData* data, int type, int index, int n);
    static int CustomData_get_named_layer_index(const CustomData *data, int type, const char *name);
  };
}


#endif //WBS_KERNEL_RENDER_M2_EDITABLE_HPP
