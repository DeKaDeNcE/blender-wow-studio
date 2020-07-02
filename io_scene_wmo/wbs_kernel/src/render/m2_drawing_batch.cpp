#include "m2_drawing_batch.hpp"
#include <render/m2_drawing_mesh.hpp>

#include <iostream>

using namespace wbs_kernel;

M2DrawingBatch::M2DrawingBatch(M2DrawingMesh *draw_mesh, short mat_id, bool is_nonindexed)
{
  this->draw_mesh = draw_mesh;
  this->mat_id = mat_id;
  this->is_nonindexed = is_nonindexed;
}

void M2DrawingBatch::set_tri_start(int triangle_start)
{
  this->tri_start = triangle_start;
}


void M2DrawingBatch::create_vao()
{
  glGenVertexArrays(1, &this->vao);
  glBindVertexArray(this->vao);

  int vertices_co_pos = glGetAttribLocation(this->shader_program, "aPosition");

  glBindBuffer(GL_ARRAY_BUFFER, this->draw_mesh->vbo);

  glVertexAttribPointer(vertices_co_pos, 3, GL_FLOAT, GL_FALSE, 3 * sizeof(GLfloat), (void*)(0));

  glEnableVertexAttribArray(vertices_co_pos);

  int normals_pos = glGetAttribLocation(this->shader_program, "aNormal");
  glBindBuffer(GL_ARRAY_BUFFER, this->draw_mesh->vbo_normals);
  glVertexAttribPointer(normals_pos, 3, GL_FLOAT, GL_FALSE, 3 * sizeof(GLfloat), (void*)(0));
  glEnableVertexAttribArray(normals_pos);

  int texcoord_pos = glGetAttribLocation(this->shader_program, "aTexCoord");

  if (texcoord_pos >= 0)
  {
    glBindBuffer(GL_ARRAY_BUFFER, this->draw_mesh->vbo_tex_coords);
    glVertexAttribPointer(texcoord_pos, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(GLfloat), (void *) (0));
    glEnableVertexAttribArray(texcoord_pos);
  }
  int tex_coord_2_loc = glGetAttribLocation(this->shader_program, "aTexCoord2");

  if (tex_coord_2_loc >= 0)
  {
    glBindBuffer(GL_ARRAY_BUFFER, this->draw_mesh->vbo_tex_coords2);
    glVertexAttribPointer(tex_coord_2_loc, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(GLfloat), (void*)(0));
    glEnableVertexAttribArray(tex_coord_2_loc);
  }

  glBindVertexArray(0);

}

void M2DrawingBatch::set_program(int shader_program)
{
  this->shader_program = shader_program;
}

void M2DrawingBatch::draw()
{

  glDisable(GL_PRIMITIVE_RESTART);

  glUseProgram(this->shader_program);
  glBindVertexArray(this->vao);

  if (this->is_nonindexed)
  {
    glDrawArrays(GL_TRIANGLES, this->tri_start * 3, this->n_tris * 3);
  }
  else
  {
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, this->draw_mesh->ibo);
    glDrawElements(GL_TRIANGLES, this->n_tris * 3, GL_UNSIGNED_INT, (void *) (this->tri_start * 3 * sizeof(GLuint)));
  }

  glEnable(GL_PRIMITIVE_RESTART);

  glBindVertexArray(0);
}


int M2DrawingBatch::get_mat_id()
{
  return this->mat_id;
}

void M2DrawingBatch::set_n_tris(int n_triangles)
{
  this->n_tris = n_triangles;
}

int M2DrawingBatch::get_n_tris()
{
  return this->n_tris;
}

int M2DrawingBatch::get_tri_start()
{
  return this->tri_start;
}


M2DrawingBatch::~M2DrawingBatch()
{
  //std::cout << "Destroyed CM2DrawingBatch from C++" << std::endl;
  glDeleteVertexArrays(1, &this->vao);
}

float* M2DrawingBatch::get_bb_center()
{
  return this->bb_center;
}

float M2DrawingBatch::get_sort_radius()
{
  return this->sort_radius;
}


