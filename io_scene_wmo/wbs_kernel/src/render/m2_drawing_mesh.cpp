#include <render/m2_drawing_mesh.hpp>

extern "C"
{
#include <BKE_mesh.h>
#include <DNA_meshdata_types.h>
#include <BKE_mesh_mapping.h>
#include <BKE_mesh_runtime.h>
}

#include <cmath>
#include <cassert>
#include <iostream>
#include <algorithm>
#include <cstring>
#include <limits>

#include <glm/glm.hpp>


using namespace wbs_kernel;

M2DrawingMesh::M2DrawingMesh(uintptr_t mesh_pointer)
{
  this->mesh = reinterpret_cast<Mesh*>(mesh_pointer);

  // generate VBO and IBO
  glGenBuffers(1, &this->vbo);
  glGenBuffers(1, &this->ibo);
  glGenBuffers(1, &this->vbo_normals);
  glGenBuffers(1, &this->vbo_tex_coords);
  glGenBuffers(1, &this->vbo_tex_coords2);
}

// Simplified version for UVs only
void* M2DrawingMesh::CustomData_get_n(const CustomData* data, int type, int index, int n)
{
  int layer_index;

  //BLI_assert(index >= 0 && n >= 0);

  /* get the layer index of the first layer of type */
  layer_index = data->typemap[type];
  if (layer_index == -1) {
    return nullptr;
  }

  const size_t offset = (size_t)index * sizeof(MLoopUV);
  return POINTER_OFFSET(data->layers[layer_index + n].data, offset);
}

int M2DrawingMesh::CustomData_get_named_layer_index(const CustomData *data, int type, const char *name)
{
  int i;

  for (i = 0; i < data->totlayer; i++) {
    if (data->layers[i].type == type) {
      if (strcmp(data->layers[i].name, name)) {
        return i;
      }
    }
  }

  return -1;
}

void M2DrawingMesh::init_looptris()
{
  this->batch_length = std::vector<int>(this->mesh->totcol ? this->mesh->totcol : 1, 0);
  this->loop_tris = std::vector<MLoopTri*>(this->mesh->runtime.looptris.len);

  for (int i = 0; i < this->mesh->runtime.looptris.len; ++i)
  {
    MLoopTri* loop_tri = this->mesh->runtime.looptris.array + i;
    this->loop_tris[i] = loop_tri;
    this->batch_length[this->mesh->mpoly[loop_tri->poly].mat_nr]++;
  }

  std::sort(loop_tris.begin(), loop_tris.end(), [this](MLoopTri* p_a, MLoopTri* p_b)
  {
    return this->mesh->mpoly[p_a->poly].mat_nr < this->mesh->mpoly[p_b->poly].mat_nr;
  });
}

int M2DrawingMesh::create_vertex_map()
{
  this->init_looptris();
  this->vertex_map.clear();
  this->vertex_map.reserve(this->mesh->totvert);

  std::vector<int> uv_layers = {M2DrawingMesh::CustomData_get_named_layer_index(&this->mesh->ldata,
                                                                 CustomDataType::CD_MLOOPUV, "UVMap"),
                                M2DrawingMesh::CustomData_get_named_layer_index(&this->mesh->ldata,
                                                                 CustomDataType::CD_MLOOPUV, "UVMap.001")};

  int v_index_global_counter = 0;

  this->n_materials = 0;
  int cur_mat_id = -1;

  int loop_tri_counter = 0;
  for (auto& loop_tri : loop_tris)
  {
    MPoly* poly = &this->mesh->mpoly[loop_tri->poly];

    if (cur_mat_id != poly->mat_nr)
    {
      cur_mat_id = poly->mat_nr;
      this->n_materials++;
    }

    for (unsigned int loop_index : loop_tri->tri)
    {
      MLoop* loop = &this->mesh->mloop[loop_index];

      // check if we already registered the vertex of that index

      bool has_matching_dupli = false;
      auto it = vertex_map.find(loop->v);
      if(it != vertex_map.end())
      {
        // check if registered dupli vertices have matching attributes
        for (auto & iter : it->second)
        {
          auto& uv_layers_data = std::get<2>(iter);

          if (std::get<1>(iter) == poly->mat_nr)
          {
            bool is_uv_shared = true;
            for (int j = 0; j < 2; ++j)
            {
              int uv_layer_index = uv_layers[j];

              if (uv_layer_index < 0)
              {
                continue;
              }

              auto uv_loop = static_cast<MLoopUV *>(M2DrawingMesh::CustomData_get_n(&this->mesh->ldata, CD_MLOOPUV,
                                                                                    loop_index, uv_layer_index));

              float uv_diff[2];
              uv_diff[0] = std::fabs(uv_layers_data[j].first) - std::fabs(uv_loop->uv[0]);
              uv_diff[1] = std::fabs(uv_layers_data[j].second) - std::fabs(uv_loop->uv[1]);

              if ((std::fabs(uv_diff[0]) > STD_UV_CONNECT_LIMIT) && std::fabs(uv_diff[1]) > STD_UV_CONNECT_LIMIT)
              {
                is_uv_shared = false;
                break;
              }

            }

            if (is_uv_shared)
            {
              auto& loop_tri_users = std::get<3>(iter);
              loop_tri_users.push_back(loop_tri_counter);
              has_matching_dupli = true;
              break;
            }
          }
        }
      }

      // do not add new vertex dupli if we found a matching one already
      if (has_matching_dupli)
      {
        continue;
      }

      // handle registering new duplicate vertex
      std::tuple<int, int, std::vector<std::pair<float, float>>, std::vector<int>> vertex_dupli =
          {0, 0, std::vector<std::pair<float, float>>{static_cast<size_t>(2)}, std::vector<int>{}};

      std::get<0>(vertex_dupli) = v_index_global_counter;
      std::get<1>(vertex_dupli) = poly->mat_nr;

      auto& uv_layers_data = std::get<2>(vertex_dupli);

      for (int j = 0; j < 2; ++j)
      {
        int uv_layer_index = uv_layers[j];

        if (uv_layer_index < 0)
        {
          uv_layers_data[j] = std::pair<float, float>(0.0f, 0.0f);
        }
        else
        {
          auto uv_loop = static_cast<MLoopUV*>(M2DrawingMesh::CustomData_get_n(&this->mesh->ldata, CD_MLOOPUV,
                                                                               loop_index, j));
          uv_layers_data[j] = std::pair<float, float>(uv_loop->uv[0], uv_loop->uv[1]);
        }

      }

      auto& loop_tri_users = std::get<3>(vertex_dupli);
      loop_tri_users.push_back(loop_tri_counter);

      v_index_global_counter++;

      vertex_map[loop->v].push_back(std::move(vertex_dupli));

    }

    loop_tri_counter++;
  }

  return v_index_global_counter;

}

void M2DrawingMesh::update_mesh_pointer(uintptr_t mesh_pointer)
{
  this->mesh = reinterpret_cast<Mesh*>(mesh_pointer);
}

bool M2DrawingMesh::validate_batches(int n_vertices_new)
{
  if (this->drawing_batches.size()
      && (this->n_vertices == n_vertices_new
          && this->n_triangles == this->mesh->runtime.looptris.len
          && this->bl_n_materials == this->mesh->totcol))
  {
    for (auto& batch : this->drawing_batches)
    {
      if (this->batch_length[batch->get_mat_id()] != batch->get_n_tris())
      {
        return false;
      }
    }

  }
  else
  {
    return false;
  }

  return true;
}


bool M2DrawingMesh::update_geometry_nonindexed()
{
  this->init_looptris();

  bool is_batching_valid = this->is_indexed ? false : this->validate_batches(this->mesh->runtime.looptris.len * 3);
  this->is_indexed = false;

  this->bl_n_materials = this->mesh->totcol;

  this->allocate_buffers(this->mesh->runtime.looptris.len * 3, static_cast<uint32_t>(this->mesh->runtime.looptris.len));

  if (!is_batching_valid)
  {
    for (auto batch_ptr : this->drawing_batches)
    {
      delete batch_ptr;
    }

    this->drawing_batches.clear();
    this->drawing_batches.reserve(this->mesh->totcol);
  }

  int mat_idx = -1;
  int batch_counter = 0;
  M2DrawingBatch* cur_batch = nullptr;

  std::vector<int> uv_layers = {M2DrawingMesh::CustomData_get_named_layer_index(&this->mesh->ldata,
                                                                 CustomDataType::CD_MLOOPUV, "UVMap"),
                                M2DrawingMesh::CustomData_get_named_layer_index(&this->mesh->ldata,
                                                                 CustomDataType::CD_MLOOPUV, "UVMap.001")};

  std::vector<float*> uv_buffers = {this->tex_coords, this->tex_coords2};

  glm::vec3 bound_box[2];

  int global_tri_index = 0;
  int global_vertex_index = 0;
  for (auto loop_tri : this->loop_tris)
  {
    MPoly *poly = &this->mesh->mpoly[loop_tri->poly];

    if (!is_batching_valid && mat_idx != poly->mat_nr)
    {
      if (cur_batch != nullptr)
      {
        cur_batch->set_n_tris(global_tri_index - cur_batch->get_tri_start());
        this->drawing_batches[poly->mat_nr] = cur_batch;

        glm::vec3 bb_center = 0.5f * (bound_box[0] + bound_box[1]);
        cur_batch->bb_center[0] = bb_center.x;
        cur_batch->bb_center[1] = bb_center.y;
        cur_batch->bb_center[2] = bb_center.z;
        cur_batch->sort_radius = (bound_box[0] - bb_center).length();

        batch_counter++;
      }

      cur_batch = new M2DrawingBatch(this, poly->mat_nr, true);
      cur_batch->set_tri_start(global_tri_index);
      mat_idx = poly->mat_nr;

      bound_box[0] = glm::vec3(std::numeric_limits<float>::max());
      bound_box[1] = glm::vec3(std::numeric_limits<float>::min());
    }

    int tri_index_counter = 0;
    for (unsigned int loop_index : loop_tri->tri)
    {
      MLoop *loop = &this->mesh->mloop[loop_index];

      for (int j = 0; j < 3; ++j)
      {
        this->vertices_co[global_vertex_index * 3 + j] = this->mesh->mvert[loop->v].co[j];
        this->normals[global_vertex_index * 3 + j] = this->mesh->mvert[loop->v].no[j];
      }

      for (int j = 0; j < 2; ++j)
      {
        for (int k = 0; k < 2; ++k)
        {
          uv_buffers[j][global_vertex_index * 2 + k] =
              uv_layers[j] < 0 ? 0.0f : static_cast<MLoopUV*>(M2DrawingMesh::CustomData_get_n(&this->mesh->ldata,
                                                                              CD_MLOOPUV, loop_index, j))->uv[k];
        }

      }

      tri_index_counter++;

      global_vertex_index++;
    }

    global_tri_index++;
  }

  // handle last batch

  if (!is_batching_valid)
  {
    if (cur_batch != nullptr)
    {
      cur_batch->set_n_tris(global_tri_index - cur_batch->get_tri_start());

      glm::vec3 bb_center = 0.5f * (bound_box[0] + bound_box[1]);
      cur_batch->bb_center[0] = bb_center.x;
      cur_batch->bb_center[1] = bb_center.y;
      cur_batch->bb_center[2] = bb_center.z;
      cur_batch->sort_radius = (bound_box[0] - bb_center).length();

      this->drawing_batches.push_back(cur_batch);
    }

    this->init_opengl_buffers();
  }
  else
  {
    this->update_opengl_buffers();
  }


  return is_batching_valid;
}

bool M2DrawingMesh::update_geometry(bool use_indexed)
{
  if (use_indexed)
  {
    return this->update_geometry_indexed();
  }
  else
  {
    return this->update_geometry_nonindexed();
  }
}

bool M2DrawingMesh::update_geometry_indexed()
{
  int n_vertices_new = this->create_vertex_map();
  bool is_batching_valid = this->is_indexed ? this->validate_batches(n_vertices_new) : false;
  this->is_indexed = true;

  this->bl_n_materials = this->mesh->totcol;

  this->allocate_buffers(n_vertices_new, static_cast<uint32_t>(this->mesh->runtime.looptris.len));

  int mat_idx = -1;
  int global_tri_index = 0;

  if (!is_batching_valid)
  {
    for (auto batch_ptr : this->drawing_batches)
    {
      delete batch_ptr;
    }

    this->drawing_batches.clear();
    this->drawing_batches.reserve(this->mesh->totcol);
  }

  glm::vec3 bound_box[2];

  int batch_counter = 0;
  M2DrawingBatch* cur_batch = nullptr;

  for (auto loop_tri : this->loop_tris)
  {
    MPoly *poly = &this->mesh->mpoly[loop_tri->poly];

    if (!is_batching_valid && mat_idx != poly->mat_nr)
    {
      if (cur_batch != nullptr)
      {
        cur_batch->set_n_tris(global_tri_index - cur_batch->get_tri_start());
        this->drawing_batches[poly->mat_nr] = cur_batch;

        glm::vec3 bb_center = 0.5f * (bound_box[0] + bound_box[1]);
        cur_batch->bb_center[0] = bb_center.x;
        cur_batch->bb_center[1] = bb_center.y;
        cur_batch->bb_center[2] = bb_center.z;
        cur_batch->sort_radius = (bound_box[0] - bb_center).length();
        batch_counter++;
      }

      cur_batch = new M2DrawingBatch(this, poly->mat_nr);
      cur_batch->set_tri_start(global_tri_index);
      mat_idx = poly->mat_nr;

      bound_box[0] = glm::vec3(std::numeric_limits<float>::max());
      bound_box[1] = glm::vec3(std::numeric_limits<float>::min());
    }

    int tri_index_counter = 0;
    for (unsigned int loop_index : loop_tri->tri)
    {
      MLoop *loop = &this->mesh->mloop[loop_index];

      // find vertex duplis using this blender vertex, and find the dupli using this loop
      auto vertex_duplis = this->vertex_map[loop->v];

      std::tuple<int, int, std::vector<std::pair<float, float>>, std::vector<int>>* dupli_vertex_params = nullptr;
      for (auto& vertex_dupli : vertex_duplis)
      {
        for (int dupli_tri_user : std::get<3>(vertex_dupli))
        {
          if (dupli_tri_user == global_tri_index)
          {
            dupli_vertex_params = &vertex_dupli;
            break;
          }
        }
      }

      assert(dupli_vertex_params != nullptr && "Vertex is not referenced by this tri.");

      int global_vertex_index = std::get<0>(*dupli_vertex_params);

      // fill the buffers
      this->tri_indices[global_tri_index * 3 + tri_index_counter] = global_vertex_index;

      for (int j = 0; j < 3; ++j)
      {
        this->vertices_co[global_vertex_index * 3 + j] = this->mesh->mvert[loop->v].co[j];
        this->normals[global_vertex_index * 3 + j] = this->mesh->mvert[loop->v].no[j];

        // bounding box calculations
        bound_box[0][j] = std::min(bound_box[0][j], this->mesh->mvert[loop->v].co[j]);
        bound_box[1][j] = std::max(bound_box[1][j], this->mesh->mvert[loop->v].co[j]);
      }

      auto& uv = std::get<2>(*dupli_vertex_params)[0];
      auto& uv1 = std::get<2>(*dupli_vertex_params)[1];

      this->tex_coords[global_vertex_index * 2] = uv.first;
      this->tex_coords[global_vertex_index * 2 + 1] = uv.second;

      this->tex_coords2[global_vertex_index * 2] = uv1.first;
      this->tex_coords2[global_vertex_index * 2 + 1] = uv1.second;

      tri_index_counter++;
    }

    global_tri_index++;
  }

  // handle last batch

  if (!is_batching_valid)
  {
    if (cur_batch != nullptr)
    {
      cur_batch->set_n_tris(global_tri_index - cur_batch->get_tri_start());
      glm::vec3 bb_center = 0.5f * (bound_box[0] + bound_box[1]);
      cur_batch->bb_center[0] = bb_center.x;
      cur_batch->bb_center[1] = bb_center.y;
      cur_batch->bb_center[2] = bb_center.z;
      cur_batch->sort_radius = (bound_box[0] - bb_center).length();

      this->drawing_batches.push_back(cur_batch);
    }

    this->init_opengl_buffers();
  }
  else
  {
    this->update_opengl_buffers();
  }

  return is_batching_valid;
}

void M2DrawingMesh::allocate_buffers(uint32_t n_vertices_new, uint32_t n_triangles_new)
{
  // vertex attributes
  // note: we always allocate twice more than needed on each realloc, to avoid reallocating too often
  if (!this->vertices_co)
  {
    // allocate new vertex attribute arrays
    this->vertices_co = new float[n_vertices_new * 3];
    this->normals = new float[n_vertices_new * 3];
    this->tex_coords = new float[n_vertices_new * 2];
    this->tex_coords2 = new float[n_vertices_new * 2];
    //this->weights = new float[n_vertices_new * 4 * 2];
    //this->bone_indices = new int[n_vertices_new * 4 * 2];
  }
  else if (this->n_vertices < n_vertices_new)
  {
    // reallocate vertex attribute arrays
    delete[] this->vertices_co;
    delete[] this->normals;
    delete[] this->tex_coords;
    delete[] this->tex_coords2;
    //delete[] this->weights;
    //delete[] this->bone_indices;

    this->vertices_co = new float[n_vertices_new * 3];
    this->normals = new float[n_vertices_new * 3];
    this->tex_coords = new float[n_vertices_new * 2];
    this->tex_coords2 = new float[n_vertices_new * 2];
    //this->weights = new float[n_vertices_new * 4 * 2];
    //this->bone_indices = new int[n_vertices_new * 4 * 2];
  }

  this->n_vertices = n_vertices_new;

  // index buffer
  if (!this->tri_indices)
  {
    // allocate index array
    this->tri_indices = new int[n_triangles_new * 3];
  }
  else if (this->n_triangles < n_triangles_new)
  {
    // reallocate index array
    delete[] this->tri_indices;
    this->tri_indices = new int[n_triangles_new * 3];
  }

  this->n_triangles = n_triangles_new;


}

void M2DrawingMesh::init_opengl_buffers()
{
  glBindBuffer(GL_ARRAY_BUFFER, this->vbo);
  glBufferData(GL_ARRAY_BUFFER, this->n_vertices * 3 * sizeof(float), this->vertices_co, GL_DYNAMIC_DRAW);

  glBindBuffer(GL_ARRAY_BUFFER, this->vbo_normals);
  glBufferData(GL_ARRAY_BUFFER, this->n_vertices * 3 * sizeof(float), this->normals, GL_DYNAMIC_DRAW);

  glBindBuffer(GL_ARRAY_BUFFER, this->vbo_tex_coords);
  glBufferData(GL_ARRAY_BUFFER, this->n_vertices * 2 * sizeof(float), this->tex_coords, GL_DYNAMIC_DRAW);

  glBindBuffer(GL_ARRAY_BUFFER, this->vbo_tex_coords2);
  glBufferData(GL_ARRAY_BUFFER, this->n_vertices * 2 * sizeof(float), this->tex_coords2, GL_DYNAMIC_DRAW);

  if (this->is_indexed)
  {
   glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, this->ibo);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, this->n_triangles * 3 * sizeof(int), this->tri_indices, GL_DYNAMIC_DRAW);
  }

}

void M2DrawingMesh::update_opengl_buffers()
{
  glBindBuffer(GL_ARRAY_BUFFER, this->vbo);
  glBufferSubData(GL_ARRAY_BUFFER, 0, this->n_vertices * 3 * sizeof(float), this->vertices_co);

  glBindBuffer(GL_ARRAY_BUFFER, this->vbo_normals);
  glBufferSubData(GL_ARRAY_BUFFER, 0, this->n_vertices * 3 * sizeof(float), this->normals);

  glBindBuffer(GL_ARRAY_BUFFER, this->vbo_tex_coords);
  glBufferSubData(GL_ARRAY_BUFFER, 0, this->n_vertices * 2 * sizeof(float), this->tex_coords);

  glBindBuffer(GL_ARRAY_BUFFER, this->vbo_tex_coords2);
  glBufferSubData(GL_ARRAY_BUFFER, 0, this->n_vertices * 2 * sizeof(float), this->tex_coords2);
}

std::vector<M2DrawingBatch*>* M2DrawingMesh::get_drawing_batches()
{
  return &this->drawing_batches;
}

M2DrawingMesh::~M2DrawingMesh()
{
  glDeleteBuffers(1, &this->vbo);
  delete[] this->vertices_co;
  delete[] this->tri_indices;
  delete[] this->normals;
  delete[] this->tex_coords;
  delete[] this->tex_coords2;

  for (auto batch_ptr : this->drawing_batches)
  {
    delete batch_ptr;
  }
}




