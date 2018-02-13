import os

from .file_formats.m2_format import M2Header, M2Versions, M2Vertex
from .file_formats.skin_format import M2SkinProfile, M2SkinSubmesh, M2SkinTextureUnit


class M2File:
    def __init__(self, version, filepath=None):
        self.version = version

        if filepath:
            self.filepath = filepath
            with open(filepath, 'rb') as f:
                self.root = M2Header()
                self.root.read(f)
                self.skins = []

                if version >= M2Versions.WOTLK:
                    raw_path = os.path.splitext(filepath)[0]
                    for i in range(self.root.num_skin_profiles):
                        with open("{}{}.skin".format(raw_path, str(i).zfill(2)), 'rb') as skin_file:
                            self.skins.append(M2SkinProfile().read(skin_file))

                else:
                    self.skins = self.root.skin_profiles

        else:
            self.filepath = None
            self.root = M2Header()
            self.skins = [M2SkinProfile()]

    def write(self, filepath):
        with open(filepath, 'rb') as f:
            if self.version < M2Versions.WOTLK:
                self.root.skin_profiles = self.skins
            else:
                raw_path = os.path.splitext(filepath)[0]
                for i, skin in enumerate(self.skins):
                    with open("{}{}.skin".format(raw_path, str(i).zfill(2)), 'wb') as skin_file:
                        skin.write(skin_file)

            self.root.write(f)

            # TODO: anim, skel and phys

    def add_skin(self):
        skin = M2SkinProfile()
        self.skins.append(skin)
        return skin

    def add_vertex(self, pos, normal, tex_coords, bone_weights=None, bone_indices=None, tex_coords2=None):
        vertex = M2Vertex()
        vertex.pos = tuple(pos)
        vertex.normal = tuple(normal)
        vertex.tex_coords = tex_coords

        # handle optional properties
        if tex_coords2:
            vertex.tex_coords2 = tex_coords2

        if bone_weights:
            vertex.bone_weights = bone_weights

        if bone_indices:
            vertex.bone_indices = bone_indices

        vertex_index = self.root.vertices.add(vertex)

        skin = self.skins[0]
        skin.vertex_indices.append(vertex_index)
        skin.bone_indices.append(bone_indices)
        return vertex_index

    def add_geoset(self, vertices, normals, tex_coords, tris, origin, mesh_part_id,
                   bone_weights=None, bone_indices=None, tex_coords2=None):
        submesh = M2SkinSubmesh()
        texture_unit = M2SkinTextureUnit()
        skin = self.skins[0]

        # add vertices
        start_index = len(self.root.vertices)
        for i, vertex_pos in enumerate(vertices):
            args = [vertex_pos, normals[i], tex_coords[i]]  # fill essentials
            if bone_weights:
                args.append(bone_weights[i])

            if bone_indices:
                args.append(bone_indices[i])

            if tex_coords2:
                args.append(tex_coords2[i])

            self.add_vertex(*args)

        submesh.vertex_start = start_index
        submesh.vertex_count = len(vertices)
        submesh.center_position = origin
        submesh.skin_section_id = mesh_part_id
        submesh.index_start = len(skin.triangle_indices)
        submesh.index_count = len(tris) * 3

        # add triangles
        for i, tri in enumerate(tris):
            for idx in tri:
                skin.triangle_indices.append(start_index + idx)




















