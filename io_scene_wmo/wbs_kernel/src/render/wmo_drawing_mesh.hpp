#ifndef WBS_KERNEL_RENDER_WMO_EDITABLE_HPP
#define WBS_KERNEL_RENDER_WMO_EDITABLE_HPP

#include <wmo_drawing_batch.hpp>

#include <unordered_map>
#include <cstdint>
#include <vector>
#include <array>
#include <tuple>
#include <functional>

#define GLEW_STATIC
#include <glew.h>

extern "C"
{
#include <DNA_mesh_types.h>
#include <BKE_customdata.h>
#include <DNA_meshdata_types.h>
};


namespace wbs_kernel
{

  struct pair_hash
  {
      template <class T1, class T2>
      std::size_t operator() (const std::pair<T1, T2> &pair) const
      {
          return std::hash<T1>()(pair.first) ^ std::hash<T2>()(pair.second);
      }
  };

  enum class WMOBatchTypes
  {
    Transitional = 0,
    Interior = 1,
    Exterior = 2
  };

  class WMODrawingMesh
  {

  // Members
  public:
    // OpenGL buffers
    GLuint vbo;
    GLuint ibo;

    GLuint vbo_normals;
    GLuint vbo_tex_coords;
    GLuint vbo_tex_coords2;
    GLuint vbo_mccv;
    GLuint vbo_mccv2;

    static std::unordered_map<int, int> cd_sizemap;

  private:
    Mesh* mesh;

    float* vertices_co = nullptr;
    float* normals = nullptr;
    float* tex_coords = nullptr;
    float* tex_coords2 = nullptr;
    float* mccv = nullptr;
    float* mccv2 = nullptr;

    int* tri_indices = nullptr;
    //int* bone_indices = nullptr;

    // loop triangles sorted by material index
    std::vector<MLoopTri*> loop_tris;

    // mapping of vertex duplication within mesh, used to construct VBO/IBO etc.

    std::unordered_map<int, std::vector<std::tuple<int, int, std::vector<std::pair<float, float>>, std::vector<std::array<unsigned char, 3>>, std::vector<int>, int>>> vertex_map;
    std::unordered_map<std::pair<int, int>, int, pair_hash> batch_length;
    std::unordered_map<MLoopTri*, WMOBatchTypes> batch_map;

    // drawing batches of this mesh
    std::vector<WMODrawingBatch*> drawing_batches;

    uint32_t n_vertices = 0;
    uint32_t n_triangles = 0;
    int n_materials = 0;
    int bl_n_materials = 0;

    bool is_indexed;
    bool is_initialized = false;
    bool is_batching_valid;

// Methods
  public:
    WMODrawingMesh(uintptr_t mesh_pointer);
    void update_mesh_pointer(uintptr_t mesh_pointer);
    bool update_geometry(bool use_indexed);
    void run_buffer_updates();
    std::vector<WMODrawingBatch*>* get_drawing_batches();
    ~WMODrawingMesh();

  private:
    int create_vertex_map();
    bool update_geometry_indexed();
    bool update_geometry_nonindexed();
    void init_looptris();
    bool validate_batches(int n_vertices_new);
    void allocate_buffers(uint32_t n_vertices_new, uint32_t n_triangles_new);
    void generate_opengl_buffers();
    void init_opengl_buffers();
    void update_opengl_buffers();
    static unsigned char color_get_avg(unsigned char r, unsigned char g, unsigned char b);
    inline std::vector<int> get_uv_layers();
    inline std::vector<int> get_color_layers();
    WMOBatchTypes get_batch_type(MLoopTri* loop_tri, std::vector<int>& color_layers);

    // Blender
    static void* CustomData_get_n(const CustomData* data, int type, int index, int n);
    static int CustomData_get_named_layer_index(const CustomData *data, int type, const char *name);
  };
}


#endif //WBS_KERNEL_RENDER_WMO_EDITABLE_HPP
