#ifndef WBS_KERNEL_M2_DRAWING_BATCH_HPP
#define WBS_KERNEL_M2_DRAWING_BATCH_HPP

#define GLEW_STATIC
#include <glew.h>


namespace wbs_kernel
{
  class M2DrawingMesh;

  class M2DrawingBatch
  {
  // Members
  private:
    M2DrawingMesh* draw_mesh;
    int mat_id;
    int tri_start = 0;
    int n_tris = 0;
    bool is_nonindexed = false;

    GLuint vao;
    GLuint shader_program;

  public:
    float sort_radius = 0.0f;
    float bb_center[3] = {0.0f, 0.0f, 0.0f};

  // Methods
  public:
    M2DrawingBatch(M2DrawingMesh *draw_mesh, short mat_id, bool is_nonindexed = false);

    void set_tri_start(int triangle_start);
    void set_n_tris(int n_triangles);
    int get_n_tris();
    int get_tri_start();
    void create_vao();
    void draw();
    void set_program(int shader_program);
    int get_mat_id();
    float* get_bb_center();
    float get_sort_radius();
    ~M2DrawingBatch();

  };

}

#endif //WBS_KERNEL_M2_DRAWING_BATCH_HPP
