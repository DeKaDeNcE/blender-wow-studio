import os

from .file_formats.m2_format import *
from .file_formats.skin_format import M2SkinProfile, M2SkinSubmesh, M2SkinTextureUnit
from ..pywowlib.io_utils.types import uint32, vec3D


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
                    # load skins

                    raw_path = os.path.splitext(filepath)[0]
                    for i in range(self.root.num_skin_profiles):
                        with open("{}{}.skin".format(raw_path, str(i).zfill(2)), 'rb') as skin_file:
                            self.skins.append(M2SkinProfile().read(skin_file))

                    # load anim files
                    for i, sequence in enumerate(self.root.sequences):

                        # handle alias animations
                        real_anim = sequence
                        a_idx = i
                        while real_anim.flags & 0x40 and real_anim.alias_next != a_idx:
                            a_idx = real_anim.alias_next
                            real_anim = self.root.sequences[real_anim.alias_next]

                        if not sequence.flags & 0x130:
                            anim_path = "{}{}-{}.anim".format(os.path.splitext(filepath)[0],
                                                              str(real_anim.id).zfill(4),
                                                              str(sequence.variation_index).zfill(2))

                            # TODO: implement game-data loading
                            anim_file = open(anim_path, 'rb')

                            for bone in self.root.bones:
                                if bone.rotation.timestamps.n_elements > a_idx:
                                    frames = bone.rotation.timestamps[a_idx]
                                    track = bone.rotation.values[a_idx]

                                    anim_file.seek(frames.ofs_elements)
                                    bone.rotation.timestamps[i].values = \
                                        [uint32.read(anim_file) for _ in range(frames.n_elements)]

                                    anim_file.seek(track.ofs_elements)
                                    bone.rotation.values[i].values = \
                                        [M2CompQuaternion().read(anim_file) for _ in range(track.n_elements)]

                                if bone.translation.timestamps.n_elements > a_idx:
                                    frames = bone.translation.timestamps[a_idx]
                                    track = bone.translation.values[a_idx]

                                    anim_file.seek(frames.ofs_elements)
                                    bone.translation.timestamps[i].values = \
                                        [uint32.read(anim_file) for _ in range(frames.n_elements)]

                                    anim_file.seek(track.ofs_elements)
                                    bone.translation.values[i].values = \
                                        [vec3D.read(anim_file) for _ in range(track.n_elements)]

                                if bone.scale.timestamps.n_elements > a_idx:
                                    frames = bone.scale.timestamps[a_idx]
                                    track = bone.scale.values[a_idx]

                                    anim_file.seek(frames.ofs_elements)
                                    bone.scale.timestamps[i].values = \
                                        [uint32.read(anim_file) for _ in range(frames.n_elements)]

                                    anim_file.seek(track.ofs_elements)
                                    bone.scale.values[i].values = \
                                        [vec3D.read(anim_file) for _ in range(track.n_elements)]

                else:
                    self.skins = self.root.skin_profiles

        else:
            self.filepath = None
            self.root = M2Header()
            self.skins = [M2SkinProfile()]

    def write(self, filepath):
        with open(filepath, 'wb') as f:
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
        vertex.tex_coords = tuple(tex_coords)

        skin = self.skins[0]

        # handle optional properties
        if tex_coords2:
            vertex.tex_coords2 = tex_coords2

        if bone_weights:
            vertex.bone_weights = bone_weights

        if bone_indices:
            vertex.bone_indices = bone_indices
            skin.bone_indices.append(bone_indices)

        vertex_index = self.root.vertices.add(vertex)
        skin.vertex_indices.append(vertex_index)
        return vertex_index

    def add_geoset(self, vertices, normals, uv, uv2, tris, origin, mesh_part_id, b_weights=None, b_indices=None):
        submesh = M2SkinSubmesh()
        texture_unit = M2SkinTextureUnit()
        skin = self.skins[0]

        # add vertices
        start_index = len(self.root.vertices)
        for i, vertex_pos in enumerate(vertices):
            args = [vertex_pos, normals[i], uv[i]]  # fill essentials
            if b_weights:
                args.append(b_weights[i])

            if b_indices:
                args.append(b_indices[i])

            if uv2:
                args.append(uv2[i])

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

        geoset_index = skin.submeshes.add(submesh)
        texture_unit.geoset_index = geoset_index
        skin.texture_units.append(texture_unit)

        return geoset_index

    def add_material_to_geoset(self, geoset_id, render_flags, blending, flags, shader_id, tex_id):  # TODO: Add extra params & cata +
        skin = self.skins[0]
        tex_unit = skin.texture_units[geoset_id]
        tex_unit.flags = flags
        tex_unit.shader_id = shader_id
        tex_unit.texture_count = 1 # TODO: multitexturing
        tex_unit.texture_combo_index = tex_id
        # tex_unit.color_index = color_id

        # check if we already have that render flag else create it
        for i, material in enumerate(self.root.materials):
            if material.flags == render_flags and material.blending_mode == blending:
                tex_unit.material_index = i
                break
        else:
            m2_mat = M2Material()
            m2_mat.flags = render_flags
            m2_mat.blending_mode = blending
            tex_unit.material_index = self.root.materials.add(m2_mat)

    def add_texture(self, path, flags, tex_type):

        # check if this texture was already added
        for i, tex in enumerate(self.root.textures):
            if tex.path == path and tex.flags == flags and tex.type == tex_type:
                return i

        texture = M2Texture()
        texture.path = path
        texture.flags = flags
        texture.type = tex_type

        tex_id = self.root.textures.add(texture)
        self.root.texture_lookup_table.append(tex_id)

        return tex_id

    def add_bone(self, pivot, key_bone_id, flags, parent_bone):
        m2_bone = M2CompBone()
        m2_bone.key_bone_id = key_bone_id
        m2_bone.flags = flags
        m2_bone.parent_bone = parent_bone
        m2_bone.pivot = tuple(pivot)

        bone_id = self.root.bones.add(m2_bone)
        self.root.bone_lookup_table.append(bone_id)

        return bone_id

    def add_dummy_anim_set(self, origin):
        bone = self.root.bones.new()
        bone.pivot = tuple(origin)

    def add_anim(self, a_id, var_id, time_bounds, movespeed, flags, frequency, replay, bl_time, bounds, var_next=None, alias_next=None):
        seq = M2Sequence()
        seq_id = self.root.sequences.add(seq)
        self.root.sequence_lookup.append(seq_id)

        # It is presumed that framerate is always 24 fps.
        if self.version <= M2Versions.TBC:
            seq.start_timestamp, seq.end_timestamp = time_bounds
        else:
            seq.duration = (time_bounds[1] - time_bounds[0]) / 24

        seq.id = a_id
        seq.variation_index = var_id
        seq.variation_next = var_next if var_next else -1
        seq.alias_next = alias_next if alias_next else seq_id
        seq.flags = flags
        seq.frequency = frequency
        seq.movespeed = movespeed
        seq.replay.minimum, seq.replay.maximum = replay
        seq.bounds.extent, seq.bounds.radius = bounds

        if self.version <= M2Versions.WOD:
            seq.blend_time = bl_time
        else:
            seq.blend_time_in, seq.blend_time_out = bl_time

        return seq_id








        






















