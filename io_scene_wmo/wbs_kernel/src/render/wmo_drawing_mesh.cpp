#include <render/wmo_drawing_mesh.hpp>

extern "C"
{
#include <BKE_mesh.h>
#include <BKE_mesh_mapping.h>
#include <BKE_mesh_runtime.h>
}

#include <cmath>
#include <cassert>
#include <iostream>
#include <algorithm>
#include <cstring>
#include <limits>

#include "glm/glm.hpp"


using namespace wbs_kernel;

std::unordered_map<int, int> WMODrawingMesh::cd_sizemap = {
                                                            { 16, sizeof(MLoopUV) },
                                                            { 17, sizeof(MLoopCol) }
                                                          };

WMODrawingMesh::WMODrawingMesh(uintptr_t mesh_pointer)
{
  this->mesh = reinterpret_cast<Mesh*>(mesh_pointer);
}

// Simplified version for UVs and vertex colors only
void* WMODrawingMesh::CustomData_get_n(const CustomData* data, int type, int index, int n)
{
  int layer_index;

  //BLI_assert(index >= 0 && n >= 0);

  /* get the layer index of the first layer of type */
  layer_index = data->typemap[type];
  if (layer_index == -1) {
    return nullptr;
  }

  const size_t offset = (size_t)index * WMODrawingMesh::cd_sizemap[type];
  return POINTER_OFFSET(data->layers[layer_index + n].data, offset);
}

int WMODrawingMesh::CustomData_get_named_layer_index(const CustomData *data, int type, const char *name)
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

void WMODrawingMesh::init_looptris()
{
  this->loop_tris = std::vector<MLoopTri*>(this->mesh->runtime.looptris.len);

  std::vector<int> color_layers = this->get_color_layers();

  for (int i = 0; i < this->mesh->runtime.looptris.len; ++i)
  {
    MLoopTri* loop_tri = this->mesh->runtime.looptris.array + i;
    this->loop_tris[i] = loop_tri;

    WMOBatchTypes batch_type = this->get_batch_type(loop_tri, color_layers);

    std::pair<int, int> batch_length_key = {static_cast<int>(batch_type), this->mesh->mpoly[loop_tri->poly].mat_nr};
    this->batch_length[batch_length_key]++;
    this->batch_map[loop_tri] = batch_type;
  }

  std::sort(loop_tris.begin(), loop_tris.end(), [this, color_layers](MLoopTri* p_a, MLoopTri* p_b)
  {
    WMOBatchTypes batch_type_a = this->batch_map[p_a];
    WMOBatchTypes batch_type_b = this->batch_map[p_b];

    if (batch_type_a != batch_type_b)
    {
      return batch_type_a < batch_type_b;
    }

    return this->mesh->mpoly[p_a->poly].mat_nr < this->mesh->mpoly[p_b->poly].mat_nr;
  });
}

std::vector<int> WMODrawingMesh::get_uv_layers()
{
  return std::vector<int>  (WMODrawingMesh::CustomData_get_named_layer_index(&this->mesh->ldata,
                                                             CustomDataType::CD_MLOOPUV, "UVMap"),
                            WMODrawingMesh::CustomData_get_named_layer_index(&this->mesh->ldata,
                                                             CustomDataType::CD_MLOOPUV, "UVMap.001"));
}

std::vector<int> WMODrawingMesh::get_color_layers()
{
   auto color_layers = std::vector<int> {WMODrawingMesh::CustomData_get_named_layer_index(&this->mesh->ldata,
                                                         CustomDataType::CD_MLOOPCOL, "Col"),
                                         WMODrawingMesh::CustomData_get_named_layer_index(&this->mesh->ldata,
                                                         CustomDataType::CD_MLOOPCOL, "BatchmapTrans"),
                                         WMODrawingMesh::CustomData_get_named_layer_index(&this->mesh->ldata,
                                                         CustomDataType::CD_MLOOPCOL, "BatchmapInt"),
                                         WMODrawingMesh::CustomData_get_named_layer_index(&this->mesh->ldata,
                                                         CustomDataType::CD_MLOOPCOL, "Blendmap"),
                                         WMODrawingMesh::CustomData_get_named_layer_index(&this->mesh->ldata,
                                                         CustomDataType::CD_MLOOPCOL, "Lightmap")};

   return color_layers;
}

WMOBatchTypes WMODrawingMesh::get_batch_type(MLoopTri* loop_tri, std::vector<int>& color_layers)
{
  // determine alleged tri batch type, batch trans overrides batch int. If not these, consider batch ext.
  int color_layer_index;
  bool is_batch_trans = true;
  bool is_batch_int = true;

  for (unsigned int loop_index : loop_tri->tri)
  {
    // check trans batch
    color_layer_index = color_layers[1];

    if (color_layer_index >= 0)
    {
      auto color_loop = static_cast<MLoopCol*>(WMODrawingMesh::CustomData_get_n(&this->mesh->ldata, CD_MLOOPCOL,
                                                                                loop_index, color_layer_index));
      if (color_loop->r > 0 || color_loop->g > 0 || color_loop->b > 0)
      {
        is_batch_trans = false;
      }

    }
    else
    {
      is_batch_trans = false;
    }

    // check int batch
    color_layer_index = color_layers[2];

    if (color_layer_index >= 0)
    {
      auto color_loop = static_cast<MLoopCol*>(WMODrawingMesh::CustomData_get_n(&this->mesh->ldata, CD_MLOOPCOL,
                                                                                loop_index, color_layer_index));
      if (color_loop->r > 0 || color_loop->g > 0 || color_loop->b > 0)
      {
        is_batch_int = false;
      }

    }
    else
    {
      is_batch_int = false;
    }

  }

  // determine final batch type
  WMOBatchTypes batch_type = WMOBatchTypes::Exterior;

  if (is_batch_trans)
  {
    batch_type = WMOBatchTypes::Transitional;
  }
  else if (is_batch_int)
  {
     batch_type = WMOBatchTypes::Interior;
  }

  return batch_type;
}

int WMODrawingMesh::create_vertex_map()
{
  this->init_looptris();
  this->vertex_map.clear();
  this->vertex_map.reserve(this->mesh->totvert);

  std::vector<int> uv_layers = this->get_uv_layers();
  std::vector<int> color_layers = this->get_color_layers();
  std::vector<int> data_color_layers = {0, 3, 4};

  int v_index_global_counter = 0;

  this->n_materials = 0;
  int cur_mat_id = -1;

  int loop_tri_counter = 0;
  for (auto& loop_tri : this->loop_tris)
  {
    MPoly* poly = &this->mesh->mpoly[loop_tri->poly];

    if (cur_mat_id != poly->mat_nr)
    {
      cur_mat_id = poly->mat_nr;
      this->n_materials++;
    }

    WMOBatchTypes batch_type = this->get_batch_type(loop_tri, color_layers);

    // process triangle loops
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
          auto& color_layers_data = std::get<3>(iter);

          if (std::get<1>(iter) == poly->mat_nr)
          {
            bool is_uv_shared = true;
            bool is_color_shared = true;

            // compare UVs
            for (int j = 0; j < 2; ++j)
            {
              int uv_layer_index = uv_layers[j];

              if (uv_layer_index < 0)
              {
                continue;
              }

              auto uv_loop = static_cast<MLoopUV*>(WMODrawingMesh::CustomData_get_n(&this->mesh->ldata, CD_MLOOPUV,
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

            // compare colors
            for (auto layer_index : data_color_layers)
            {
              int color_layer_index = color_layers[layer_index];

              if (color_layer_index < 0)
              {
                continue;
              }

              auto color_loop = static_cast<MLoopCol*>(WMODrawingMesh::CustomData_get_n(&this->mesh->ldata, CD_MLOOPCOL,
                                                                                        loop_index, color_layer_index));

              std::array<unsigned char, 3> cur_color = {color_loop->r, color_loop->g, color_loop->b};
              for (int k = 0; k < 3; ++k)
              {
                if (color_layers_data[layer_index][k] != cur_color[k])
                {
                    is_color_shared = false;
                    break;
                }
              }

            }

            if (is_uv_shared && is_color_shared && static_cast<int>(batch_type) == std::get<5>(iter))
            {
              auto& loop_tri_users = std::get<4>(iter);
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
      std::tuple<int, int, std::vector<std::pair<float, float>>, std::vector<std::array<unsigned char, 3>>,
                 std::vector<int>, int> vertex_dupli =
          {0, 0, std::vector<std::pair<float, float>>{static_cast<size_t>(2)}, {{0, 0, 0}}, std::vector<int>{}, 0};

      std::get<0>(vertex_dupli) = v_index_global_counter;
      std::get<1>(vertex_dupli) = poly->mat_nr;
      std::get<5>(vertex_dupli) = static_cast<int>(batch_type);

      // handle UVs
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
          auto uv_loop = static_cast<MLoopUV*>(WMODrawingMesh::CustomData_get_n(&this->mesh->ldata, CD_MLOOPUV,
                                                                                loop_index, j));
          uv_layers_data[j] = std::pair<float, float>(uv_loop->uv[0], uv_loop->uv[1]);
        }

      }

      // handle colors
      auto& color_layers_data = std::get<3>(vertex_dupli);

      for (int j = 0; j < 6; ++j)
      {
        int color_layer_index = color_layers[j];

        if (color_layer_index < 0)
        {
          color_layers_data[j] = std::array<unsigned char, 3>{{0, 0, 0}};
        }
        else
        {
          auto color_loop = static_cast<MLoopCol*>(WMODrawingMesh::CustomData_get_n(&this->mesh->ldata, CD_MLOOPCOL,
                                                                                    loop_index, j));
          color_layers_data[j] = std::array<unsigned char, 3>{{color_loop->r, color_loop->g, color_loop->b}};
        }

      }

      auto& loop_tri_users = std::get<4>(vertex_dupli);
      loop_tri_users.push_back(loop_tri_counter);

      v_index_global_counter++;

      vertex_map[loop->v].push_back(std::move(vertex_dupli));

    }

    loop_tri_counter++;
  }

  return v_index_global_counter;

}

void WMODrawingMesh::update_mesh_pointer(uintptr_t mesh_pointer)
{
  this->mesh = reinterpret_cast<Mesh*>(mesh_pointer);
}

bool WMODrawingMesh::validate_batches(int n_vertices_new)
{
  if (this->drawing_batches.size()
      && (this->n_vertices == n_vertices_new
          && this->n_triangles == this->mesh->runtime.looptris.len
          && this->bl_n_materials == this->mesh->totcol))
  {
    for (auto& batch : this->drawing_batches)
    {
      std::pair<int, int> batch_length_key = {static_cast<int>(batch->type), batch->get_mat_id()};
      if (this->batch_length[batch_length_key] != batch->get_n_tris())
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


bool WMODrawingMesh::update_geometry_nonindexed()
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
  WMODrawingBatch* cur_batch = nullptr;

  std::vector<int> uv_layers = this->get_uv_layers();
  std::vector<int> color_layers = this->get_color_layers();



  std::vector<float*> uv_buffers = {this->tex_coords, this->tex_coords2};

  glm::vec3 bound_box[2];

  int global_tri_index = 0;
  int global_vertex_index = 0;
  for (auto loop_tri : this->loop_tris)
  {
    MPoly *poly = &this->mesh->mpoly[loop_tri->poly];

    WMOBatchTypes batch_type = this->batch_map[loop_tri];

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

      cur_batch = new WMODrawingBatch(this, poly->mat_nr, true, batch_type);
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

      // UVs
      for (int j = 0; j < 2; ++j)
      {
        for (int k = 0; k < 2; ++k)
        {
          uv_buffers[j][global_vertex_index * 2 + k] =
              uv_layers[j] < 0 ? 0.0f : static_cast<MLoopUV*>(WMODrawingMesh::CustomData_get_n(&this->mesh->ldata,
                                                                              CD_MLOOPUV, loop_index, j))->uv[k];
        }

      }

      /*
      // Colors
      auto& colors = std::get<3>(*dupli_vertex_params);

      // vertex color
      for (int j = 0; j < 3; ++j)
      {
       this->mccv[global_vertex_index * 3 + j] = static_cast<float>(colors[0][j]) / 255.0f;
      }

      // lightmap
      this->mccv[global_vertex_index * 3 + 3] =
        static_cast<float>(WMODrawingMesh::color_get_avg(colors[5][0], colors[5][1], colors[5][2])) / 255.0f;

      // blendmap
      this->mccv2[global_vertex_index * 3 + 3] =
        static_cast<float>(WMODrawingMesh::color_get_avg(colors[4][0], colors[4][1], colors4][2])) / 255.0f

      */

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

bool WMODrawingMesh::update_geometry(bool use_indexed)
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

bool WMODrawingMesh::update_geometry_indexed()
{
  int n_vertices_new = this->create_vertex_map();
  this->is_batching_valid = this->is_indexed ? this->validate_batches(n_vertices_new) : false;
  this->is_indexed = true;

  this->bl_n_materials = this->mesh->totcol;

  this->allocate_buffers(n_vertices_new, static_cast<uint32_t>(this->mesh->runtime.looptris.len));

  int mat_idx = -1;
  int cur_batch_type = -1;
  int global_tri_index = 0;

  if (!this->is_batching_valid)
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
  WMODrawingBatch* cur_batch = nullptr;

  for (auto loop_tri : this->loop_tris)
  {
    MPoly *poly = &this->mesh->mpoly[loop_tri->poly];

    WMOBatchTypes batch_type = this->batch_map[loop_tri];

    if (!is_batching_valid && mat_idx != poly->mat_nr && cur_batch_type != static_cast<int>(batch_type))
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

      cur_batch = new WMODrawingBatch(this, poly->mat_nr, false, batch_type);
      cur_batch->set_tri_start(global_tri_index);
      mat_idx = poly->mat_nr;
      cur_batch_type = static_cast<int>(batch_type);

      bound_box[0] = glm::vec3(std::numeric_limits<float>::max());
      bound_box[1] = glm::vec3(std::numeric_limits<float>::min());
    }

    int tri_index_counter = 0;
    for (unsigned int loop_index : loop_tri->tri)
    {
      MLoop *loop = &this->mesh->mloop[loop_index];

      // find vertex duplis using this blender vertex, and find the dupli using this loop
      auto vertex_duplis = this->vertex_map[loop->v];

      std::tuple<int, int, std::vector<std::pair<float, float>>, std::vector<std::array<unsigned char, 3>>, std::vector<int>, int>* dupli_vertex_params = nullptr;
      for (auto& vertex_dupli : vertex_duplis)
      {
        for (int dupli_tri_user : std::get<4>(vertex_dupli))
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

      auto& colors = std::get<3>(*dupli_vertex_params);

      // vertex color
      for (int j = 0; j < 3; ++j)
      {
       this->mccv[global_vertex_index * 3 + j] = static_cast<float>(colors[0][j]) / 255.0f;
      }

      // lightmap
      this->mccv[global_vertex_index * 3 + 3] =
        static_cast<float>(WMODrawingMesh::color_get_avg(colors[4][0], colors[4][1], colors[4][2])) / 255.0f;

      // blendmap
      this->mccv2[global_vertex_index * 3 + 3] =
        static_cast<float>(WMODrawingMesh::color_get_avg(colors[3][0], colors[3][1], colors[3][2])) / 255.0f;

      tri_index_counter++;
    }

    global_tri_index++;
  }

  // handle last batch

  if (!this->is_batching_valid)
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
  }

  return is_batching_valid;
}

void WMODrawingMesh::run_buffer_updates()
{

  if (!this->is_batching_valid)
  {
    this->init_opengl_buffers();
  }
  else
  {
     this->update_opengl_buffers();
  }
}

void WMODrawingMesh::allocate_buffers(uint32_t n_vertices_new, uint32_t n_triangles_new)
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
    this->mccv = new float[n_vertices_new * 3];
    this->mccv2 = new float[n_vertices_new * 3];
  }
  else if (this->n_vertices < n_vertices_new)
  {
    // reallocate vertex attribute arrays
    delete[] this->vertices_co;
    delete[] this->normals;
    delete[] this->tex_coords;
    delete[] this->tex_coords2;
    delete[] this->mccv;
    delete[] this->mccv2;

    this->vertices_co = new float[n_vertices_new * 3];
    this->normals = new float[n_vertices_new * 3];
    this->tex_coords = new float[n_vertices_new * 2];
    this->tex_coords2 = new float[n_vertices_new * 2];
    this->mccv = new float[n_vertices_new * 3];
    this->mccv2 = new float[n_vertices_new * 3];
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

void WMODrawingMesh::generate_opengl_buffers()
{
  // generate VBO and IBO
  glGenBuffers(1, &this->vbo);
  glGenBuffers(1, &this->ibo);
  glGenBuffers(1, &this->vbo_normals);
  glGenBuffers(1, &this->vbo_tex_coords);
  glGenBuffers(1, &this->vbo_tex_coords2);
  glGenBuffers(1, &this->vbo_mccv);
  glGenBuffers(1, &this->vbo_mccv2);
}

void WMODrawingMesh::init_opengl_buffers()
{
  if (!this->is_initialized)
  {
    this->generate_opengl_buffers();
    this->is_initialized = true;
  }

  glBindBuffer(GL_ARRAY_BUFFER, this->vbo);
  glBufferData(GL_ARRAY_BUFFER, this->n_vertices * 3 * sizeof(float), this->vertices_co, GL_DYNAMIC_DRAW);

  glBindBuffer(GL_ARRAY_BUFFER, this->vbo_normals);
  glBufferData(GL_ARRAY_BUFFER, this->n_vertices * 3 * sizeof(float), this->normals, GL_DYNAMIC_DRAW);

  glBindBuffer(GL_ARRAY_BUFFER, this->vbo_tex_coords);
  glBufferData(GL_ARRAY_BUFFER, this->n_vertices * 2 * sizeof(float), this->tex_coords, GL_DYNAMIC_DRAW);

  glBindBuffer(GL_ARRAY_BUFFER, this->vbo_tex_coords2);
  glBufferData(GL_ARRAY_BUFFER, this->n_vertices * 2 * sizeof(float), this->tex_coords2, GL_DYNAMIC_DRAW);

  glBindBuffer(GL_ARRAY_BUFFER, this->vbo_mccv);
  glBufferData(GL_ARRAY_BUFFER, this->n_vertices * 3 * sizeof(float), this->mccv, GL_DYNAMIC_DRAW);

  glBindBuffer(GL_ARRAY_BUFFER, this->vbo_mccv2);
  glBufferData(GL_ARRAY_BUFFER, this->n_vertices * 3 * sizeof(float), this->mccv2, GL_DYNAMIC_DRAW);

  if (this->is_indexed)
  {
   glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, this->ibo);
   glBufferData(GL_ELEMENT_ARRAY_BUFFER, this->n_triangles * 3 * sizeof(int), this->tri_indices, GL_DYNAMIC_DRAW);
  }

}

void WMODrawingMesh::update_opengl_buffers()
{
  glBindBuffer(GL_ARRAY_BUFFER, this->vbo);
  glBufferSubData(GL_ARRAY_BUFFER, 0, this->n_vertices * 3 * sizeof(float), this->vertices_co);

  glBindBuffer(GL_ARRAY_BUFFER, this->vbo_normals);
  glBufferSubData(GL_ARRAY_BUFFER, 0, this->n_vertices * 3 * sizeof(float), this->normals);

  glBindBuffer(GL_ARRAY_BUFFER, this->vbo_tex_coords);
  glBufferSubData(GL_ARRAY_BUFFER, 0, this->n_vertices * 2 * sizeof(float), this->tex_coords);

  glBindBuffer(GL_ARRAY_BUFFER, this->vbo_tex_coords2);
  glBufferSubData(GL_ARRAY_BUFFER, 0, this->n_vertices * 2 * sizeof(float), this->tex_coords2);

  glBindBuffer(GL_ARRAY_BUFFER, this->vbo_mccv);
  glBufferSubData(GL_ARRAY_BUFFER, 0, this->n_vertices * 3 * sizeof(float), this->mccv);

  glBindBuffer(GL_ARRAY_BUFFER, this->vbo_mccv2);
  glBufferSubData(GL_ARRAY_BUFFER, 0, this->n_vertices * 3 * sizeof(float), this->mccv2);

}

std::vector<WMODrawingBatch*>* WMODrawingMesh::get_drawing_batches()
{
  return &this->drawing_batches;
}

unsigned char WMODrawingMesh::color_get_avg(unsigned char r, unsigned char g, unsigned char b)
{
    return (r + g + b) / 3;
}

WMODrawingMesh::~WMODrawingMesh()
{
  glDeleteBuffers(1, &this->vbo);
  glDeleteBuffers(1, &this->vbo_normals);
  glDeleteBuffers(1, &this->vbo_tex_coords);
  glDeleteBuffers(1, &this->vbo_tex_coords2);
  glDeleteBuffers(1, &this->vbo_mccv);
  glDeleteBuffers(1, &this->vbo_mccv2);

  delete[] this->vertices_co;
  delete[] this->tri_indices;
  delete[] this->normals;
  delete[] this->tex_coords;
  delete[] this->tex_coords2;
  delete[] this->mccv;
  delete[] this->mccv2;

  for (auto batch_ptr : this->drawing_batches)
  {
    delete batch_ptr;
  }
}




