import bpy
import os
from mathutils import Vector
from math import sqrt

from ..utils import resolve_texture_path, get_origin_position, get_objs_boundbox_world, get_obj_boundbox_center, get_obj_radius
from ..pywowlib.enums.m2_enums import M2SkinMeshPartID, M2AttachmentTypes, M2EventTokens
from ..utils import parse_bitfield, construct_bitfield, load_game_data
from .ui.enums import mesh_part_id_menu


class BlenderM2Scene:
    """ BlenderM2Scene class is used for assembling a Blender scene from an M2 file or saving the scene back to it."""

    def __init__(self, m2, prefs):
        self.m2 = m2
        self.materials = {}
        self.bone_ids = {}
        self.uv_transforms = {}
        self.geosets = []
        self.animations = []
        self.global_sequences = []
        self.rig = None
        self.collision_mesh = None
        self.settings = prefs

    def load_materials(self, texture_dir):

        # TODO: multitexturing
        skin = self.m2.skins[0]  # assuming first skin is the most detailed one

        for tex_unit in skin.texture_units:
            texture = self.m2.root.textures[self.m2.root.texture_lookup_table[tex_unit.texture_combo_index]]
            tex_path_blp = texture.filename.value
            tex_path_png = os.path.splitext(tex_path_blp)[0] + '.png'
            m2_mat = self.m2.root.materials[tex_unit.material_index]

            # creating material
            blender_mat = bpy.data.materials.new(os.path.basename(tex_path_png))

            tex1_slot = blender_mat.texture_slots.create(0)
            tex1_slot.uv_layer = "UVMap"
            tex1_slot.texture_coords = 'UV'

            tex1_name = blender_mat.name + "_Tex_02"
            tex1 = bpy.data.textures.new(tex1_name, 'IMAGE')
            tex1.WowM2Texture.Flags = parse_bitfield(texture.flags, 0x2)
            tex1.WowM2Texture.TextureType = str(texture.type)
            tex1.WowM2Texture.Path = texture.filename.value

            tex1_slot.texture = tex1

            # loading images
            if os.name != 'nt': tex_path_png = tex_path_png.replace('\\', '/')  # reverse slahes for unix

            try:
                tex1_img = bpy.data.images.load(os.path.join(texture_dir, tex_path_png))
                tex1.image = tex1_img
                blender_mat.active_texture = tex1
            except RuntimeError:
                pass

            # filling material settings
            blender_mat.WowM2Material.Flags = parse_bitfield(tex_unit.flags, 0x80)  # texture unit flags
            blender_mat.WowM2Material.RenderFlags = parse_bitfield(m2_mat.flags, 0x800)  # render flags

            blender_mat.WowM2Material.BlendingMode = str(m2_mat.blending_mode)  # TODO: ? bitfield
            blender_mat.WowM2Material.Shader = str(tex_unit.shader_id)

            # TODO: other settings

            self.materials[tex_unit.skin_section_index] = blender_mat, tex_unit

    def load_armature(self):
        if not len(self.m2.root.bones):
            print("\nNo armature found to import.")
            return

        print("\nImporting armature")

        # Create armature
        armature = bpy.data.armatures.new('{}_Armature'.format(self.m2.root.name.value))
        rig = bpy.data.objects.new(self.m2.root.name.value, armature)
        rig.location = (0, 0, 0)
        self.rig = rig

        # Link the object to the scene
        scene = bpy.context.scene
        scene.objects.link(rig)
        scene.objects.active = rig
        scene.update()

        bpy.ops.object.mode_set(mode='EDIT')

        for i, bone in enumerate(self.m2.root.bones):  # add bones to armature.
            bl_edit_bone = armature.edit_bones.new(bone.name)
            bl_edit_bone.head = Vector(bone.pivot)

            bl_edit_bone.tail.x = bl_edit_bone.head.x + 0.1  # TODO: mess with bones parenting even more
            bl_edit_bone.tail.y = bl_edit_bone.head.y
            bl_edit_bone.tail.z = bl_edit_bone.head.z

            bl_edit_bone.WowM2Bone.Flags = parse_bitfield(bone.flags)
            bl_edit_bone.WowM2Bone.KeyBoneID = str(bone.key_bone_id)

        # link children to parents
        for i, bone in enumerate(self.m2.root.bones):
            if bone.parent_bone >= 0:
                bl_edit_bone = armature.edit_bones[bone.name]
                parent = armature.edit_bones[self.m2.root.bones[bone.parent_bone].name]
                bl_edit_bone.parent = parent

        bpy.context.scene.update()  # update scene.
        bpy.ops.object.mode_set(mode='OBJECT')  # return to object mode.

    def load_animations(self):

        # TODO: pre-wotlk

        def populate_fcurve_trans(f_curves, bone, frames, track):
            # init translation keyframes on the curve
            n_keys = len(frames)
            for trans_fcurve in f_curves: trans_fcurve.keyframe_points.add(n_keys)

            # set translation values for each channel
            for j, timestamp in enumerate(frames):
                trans_vec = bl_bone.bone.matrix_local.inverted() * (Vector(bone.pivot)
                                                                    + Vector(track[j]))

                frame = timestamp * 0.0266666

                for k in range(3):
                    keyframe = f_curves[k].keyframe_points[j]
                    keyframe.co = frame, trans_vec[k]
                    keyframe.interpolation = 'LINEAR' if bone.translation.interpolation_type == 1 else 'CONSTANT'

        def populate_fcurve_rot(f_curves, bone, frames, track):
            # init rotation keyframes on the curve
            n_keys = len(frames)
            for rot_fcurve in f_curves: rot_fcurve.keyframe_points.add(n_keys)

            # set rotation values for each channel
            for j, timestamp in enumerate(frames):
                rot_quat = track[j].to_quaternion()
                frame = timestamp * 0.0266666

                for k in range(4):
                    keyframe = f_curves[k].keyframe_points[j]
                    keyframe.co = frame, rot_quat[k]
                    keyframe.interpolation = 'LINEAR' if bone.rotation.interpolation_type == 1 else 'CONSTANT'

        def populate_fcurve_scale(f_curves, bone, frames, track):
            # init scale keyframes on the curve
            n_keys = len(frames)
            for s_curve in f_curves: s_curve.keyframe_points.add(n_keys)

            # set scale values for each channel
            for j, timestamp in enumerate(frames):
                frame = timestamp * 0.0266666
                for k in range(3):
                    keyframe = f_curves[k].keyframe_points[j]
                    keyframe.co = frame, track[j][k]
                    keyframe.interpolation = 'LINEAR' if bone.scale.interpolation_type == 1 else 'CONSTANT'

        if not len(self.m2.root.sequences) and not len(self.m2.root.global_sequences):
            print("\nNo animation data found to import.")
            return
        else:
            print("\nImporting animations.")

        if not self.rig:
            print("\nArmature is not present on the scene. Skipping animation import. M2 is most likely corrupted.")
            return

        scene = bpy.context.scene
        rig = self.rig
        rig.animation_data_create()
        rig.animation_data.action_blend_type = 'ADD'
        bpy.context.scene.objects.active = rig

        anim_data_dbc = load_game_data().db_files_client.AnimationData

        # import global sequence animations
        for i, sequence in enumerate(self.m2.root.global_sequences):
            seq_index = len(scene.WowM2Animations)
            seq = scene.WowM2Animations.add()
            seq.IsGlobalSequence = True

            # register rig in the sequence
            anim_pair = seq.AnimPairs.add()
            anim_pair.Object = rig

            action = bpy.data.actions.new(name='Global_Sequence_{}'.format(str(i).zfill(3)))
            action.use_fake_user = True
            anim_pair.Action = action

            self.global_sequences.append(seq_index)

        m2_sequences = sorted(enumerate(self.m2.root.sequences), key=lambda item: (item[0], item[1].id, item[1].variation_index))

        # import animation sequence
        for i, pair in enumerate(m2_sequences):
            idx, sequence = pair

            anim = scene.WowM2Animations.add()

            # register rig in the sequence
            anim_pair = anim.AnimPairs.add()
            anim_pair.Object = rig

            field_name = anim_data_dbc.get_field(sequence.id, 'Name')
            name = '{}_UnkAnim'.format(str(i).zfill(3)) if not field_name \
                else "{}_{}_({})".format(str(i).zfill(3), field_name, sequence.variation_index)

            action = bpy.data.actions.new(name=name)
            action.use_fake_user = True

            anim_pair.Action = action

            # add animation properties
            anim.AnimationID = str(sequence.id)
            anim.Flags = parse_bitfield(sequence.flags, 0x800)
            anim.Movespeed = sequence.movespeed
            anim.Frequency = sequence.frequency
            anim.ReplayMin = sequence.replay.minimum
            anim.ReplayMax = sequence.replay.maximum
            anim.BlendTime = sequence.blend_time

            if '64' in anim.Flags:  # check if sequence is an alias
                anim.IsAlias = True

                for j, seq in m2_sequences:
                    if j == sequence.alias_next:
                        anim.AliasNext = j + len(self.m2.root.global_sequences)
                        break

            self.animations.append(idx)

        # import fcurves
        for bone in self.m2.root.bones:
            bl_bone = rig.pose.bones[bone.name]

            is_global_seq_trans = bone.translation.global_sequence >= 0
            is_global_seq_rot = bone.rotation.global_sequence >= 0
            is_global_seq_scale = bone.scale.global_sequence >= 0

            # write global sequence fcurves
            if is_global_seq_trans:
                action = scene.WowM2Animations[self.global_sequences[bone.translation.global_sequence]].AnimPairs[0].Action

                # group channels
                if bone.name not in action.groups:
                    action.groups.new(name=bone.name)

                if bone.translation.timestamps.n_elements:
                    frames = bone.translation.timestamps[0]
                    track = bone.translation.values[0]

                    if frames:
                        t_fcurves = [action.fcurves.new(data_path='pose.bones.["{}"].location'.format(bl_bone.name),
                                                        index=k, action_group=bone.name) for k in range(3)]
                        populate_fcurve_trans(t_fcurves, bone, frames, track)

            if is_global_seq_rot:

                action = scene.WowM2Animations[self.global_sequences[bone.rotation.global_sequence]].AnimPairs[0].Action

                # group channels
                if bone.name not in action.groups:
                    action.groups.new(name=bone.name)

                if bone.rotation.timestamps.n_elements:
                    frames = bone.rotation.timestamps[0]
                    track = bone.rotation.values[0]

                    if frames:
                        r_fcurves = [action.fcurves.new(data_path='pose.bones.["{}"].rotation_quaternion'.format(bl_bone.name),
                                                        index=k, action_group=bone.name) for k in range(4)]
                        populate_fcurve_rot(r_fcurves, bone, frames, track)

            if is_global_seq_scale:
                action = scene.WowM2Animations[self.global_sequences[bone.scale.global_sequence]].AnimPairs[0].Action

                # group channels
                if bone.name not in action.groups:
                    action.groups.new(name=bone.name)

                if bone.scale.timestamps.n_elements:
                    frames = bone.scale.timestamps[0]
                    track = bone.scale.values[0]

                    if frames:
                        s_fcurves = [action.fcurves.new(data_path='pose.bones.["{}"].scale'.format(bl_bone.name),
                                                        index=k, action_group=bone.name) for k in range(3)]
                        populate_fcurve_scale(s_fcurves, bone, frames, track)

            # write regular animation fcurves
            n_global_sequences = len(self.m2.root.global_sequences)
            for i, anim_index in enumerate(self.animations):
                anim = scene.WowM2Animations[i + n_global_sequences]
                action = anim.AnimPairs[0].Action

                # group channels
                if bone.name not in action.groups:
                    action.groups.new(name=bone.name)

                # translate bones
                if not is_global_seq_trans and bone.translation.timestamps.n_elements > anim_index:
                    frames = bone.translation.timestamps[anim_index]
                    track = bone.translation.values[anim_index]

                    if frames:
                        t_fcurves = [action.fcurves.new(data_path='pose.bones.["{}"].location'.format(bl_bone.name),
                                                        index=k, action_group=bone.name) for k in range(3)]
                        populate_fcurve_trans(t_fcurves, bone, frames, track)

                # rotate bones
                if not is_global_seq_rot and bone.rotation.timestamps.n_elements > anim_index:
                    frames = bone.rotation.timestamps[anim_index]
                    track = bone.rotation.values[anim_index]

                    if frames:
                        r_fcurves = [action.fcurves.new(data_path='pose.bones.["{}"].rotation_quaternion'.format(bl_bone.name),
                                                        index=k, action_group=bone.name) for k in range(4)]
                        populate_fcurve_rot(r_fcurves, bone, frames, track)

                # scale bones
                if not is_global_seq_scale and bone.scale.timestamps.n_elements > anim_index:
                    frames = bone.scale.timestamps[anim_index]
                    track = bone.scale.values[anim_index]

                    if frames:
                        s_fcurves = [action.fcurves.new(data_path='pose.bones.["{}"].scale'.format(bl_bone.name),
                                                        index=k, action_group=bone.name) for k in range(3)]
                        populate_fcurve_scale(s_fcurves, bone, frames, track)

    def load_geosets(self):

        if not len(self.m2.root.vertices):
            print("\nNo mesh geometry found to import.")
            return

        else:
            print("\nImporting geosets.")

        skin = self.m2.skins[0]

        for smesh_i, smesh in enumerate(skin.submeshes):

            vertices = [self.m2.root.vertices[skin.vertex_indices[i]].pos
                        for i in range(smesh.vertex_start, smesh.vertex_start + smesh.vertex_count)]

            normals = [self.m2.root.vertices[skin.vertex_indices[i]].normal
                       for i in range(smesh.vertex_start, smesh.vertex_start + smesh.vertex_count)]

            tex_coords = [self.m2.root.vertices[skin.vertex_indices[i]].tex_coords
                          for i in range(smesh.vertex_start, smesh.vertex_start + smesh.vertex_count)]

            triangles = [[skin.triangle_indices[i + j] - smesh.vertex_start for j in range(3)]
                         for i in range(smesh.index_start, smesh.index_start + smesh.index_count, 3)]

            # create mesh
            mesh = bpy.data.meshes.new(self.m2.root.name.value)
            mesh.from_pydata(vertices, [], triangles)

            for poly in mesh.polygons:
                poly.use_smooth = True

            # set normals
            for index, vertex in enumerate(mesh.vertices):
                vertex.normal = normals[index]

            # set uv
            uv1 = mesh.uv_textures.new("UVMap")
            uv_layer1 = mesh.uv_layers[0]
            for i in range(len(uv_layer1.data)):
                uv = tex_coords[mesh.loops[i].vertex_index]
                uv_layer1.data[i].uv = (uv[0], 1 - uv[1])

            # set textures and materials
            material, tex_unit = self.materials[smesh_i]
            mesh.materials.append(material)

            for i, poly in enumerate(mesh.polygons):
                uv1.data[i].image = material.active_texture.image
                poly.material_index = 0  # ???

            # get object name
            name = M2SkinMeshPartID.get_mesh_part_name(smesh.skin_section_id)
            obj = bpy.data.objects.new(name if name else 'Geoset', mesh)
            bpy.context.scene.objects.link(obj)

            obj.WowM2Geoset.MeshPartGroup = name
            obj.WowM2Geoset.MeshPartID = str(smesh.skin_section_id)

            for item in mesh_part_id_menu(obj.WowM2Geoset, None):
                if item[0] == smesh.skin_section_id:
                    obj.name = item[1]

            if self.rig:
                obj.parent = self.rig

                # bind armature to geometry
                bpy.context.scene.objects.active = obj
                bpy.ops.object.modifier_add(type='ARMATURE')
                bpy.context.object.modifiers["Armature"].object = self.rig

                vgroups = {}
                for j in range(smesh.vertex_start, smesh.vertex_start + smesh.vertex_count):
                    m2_vertex = self.m2.root.vertices[skin.vertex_indices[j]]
                    for b_index, bone_index in enumerate(filter(lambda x: x > 0, m2_vertex.bone_indices)):
                        vgroups.setdefault(self.m2.root.bones[bone_index].name, []).append(
                            (j - smesh.vertex_start, m2_vertex.bone_weights[b_index] / 255))

                for name in vgroups.keys():
                    if len(vgroups[name]) > 0:
                        grp = obj.vertex_groups.new(name)
                        for (v, w) in vgroups[name]:
                            grp.add([v], w, 'REPLACE')

            self.geosets.append(obj)

    def load_texture_transforms(self):

        def animate_tex_transform_controller_trans(anim_pair, name, trans_track, anim_index):

            action = anim_pair.Action

            try:
                frames = trans_track.timestamps[anim_index]
                track = trans_track.values[anim_index]
            except IndexError:
                return

            if not len(frames):
                return

            if not action:
                action = bpy.data.actions.new(name=name)
                action.use_fake_user = True
                anim_pair.Action = action

            # create fcurve
            f_curves = [action.fcurves.new(data_path='location', index=k) for k in range(3)]

            # init keyframes on the curve
            for f_curve in f_curves: f_curve.keyframe_points.add(len(frames))

            # set translation values for each channel
            for i, timestamp in enumerate(frames):
                trans_vec = Vector((0, 0, 0)) + Vector(track[i])
                frame = timestamp * 0.0266666

                for j in range(3):
                    keyframe = f_curves[j].keyframe_points[i]
                    keyframe.co = frame, trans_vec[j]
                    keyframe.interpolation = 'LINEAR' if trans_track.interpolation_type == 1 else 'CONSTANT'

        def animate_tex_transform_controller_rot(anim_pair, name, rot_track, anim_index):
            action = anim_pair.Action

            try:
                frames = rot_track.timestamps[anim_index]
                track = rot_track.values[anim_index]
            except IndexError:
                return

            if not len(frames):
                return

            if not action:
                action = bpy.data.actions.new(name=name)
                action.use_fake_user = True
                anim_pair.Action = action

            # create fcurve
            f_curves = [action.fcurves.new(data_path='rotation_quaternion', index=k) for k in range(4)]

            # init keyframes on the curve
            for f_curve in f_curves: f_curve.keyframe_points.add(len(frames))

            # set translation values for each channel
            for i, timestamp in enumerate(frames):
                frame = timestamp * 0.0266666

                rot_quat = (track[i][3], -track[i][1], track[i][0], track[i][2])

                for j in range(4):
                    keyframe = f_curves[j].keyframe_points[i]
                    keyframe.co = frame, rot_quat[j]
                    keyframe.interpolation = 'LINEAR' if rot_track.interpolation_type == 1 else 'CONSTANT'

        def animate_tex_transform_controller_scale(anim_pair, name, scale_track, anim_index):
            action = anim_pair.Action

            try:
                frames = scale_track.timestamps[anim_index]
                track = scale_track.values[anim_index]
            except IndexError:
                return

            if not len(frames):
                return

            if not action:
                action = bpy.data.actions.new(name=name)
                action.use_fake_user = True
                anim_pair.Action = action

            # create fcurve
            f_curves = [action.fcurves.new(data_path='scale', index=k) for k in range(3)]

            # init keyframes on the curve
            for f_curve in f_curves: f_curve.keyframe_points.add(len(frames))

            # set translation values for each channel
            for i, timestamp in enumerate(frames):
                frame = timestamp * 0.0266666

                for j in range(3):
                    keyframe = f_curves[j].keyframe_points[i]
                    keyframe.co = frame, track[i][j]
                    keyframe.interpolation = 'LINEAR' if scale_track.interpolation_type == 1 else 'CONSTANT'

        if not self.geosets:
            print('\nNo geosets found. Skipping texture transform import')
            return
        else:
            print('\nImporting texture transforms')

        skin = self.m2.skins[0]

        for smesh_pair, obj in zip(enumerate(skin.submeshes), self.geosets):
            smesh_i, smesh = smesh_pair

            material, tex_unit = self.materials[smesh_i]
            tex_tranform_index = self.m2.root.texture_transforms_lookup_table[tex_unit.texture_transform_combo_index]

            if tex_tranform_index >= 0:

                c_obj = self.uv_transforms.get(tex_tranform_index)
                tex_transform = self.m2.root.texture_transforms[tex_tranform_index]
                anim_data_dbc = load_game_data().db_files_client.AnimationData
                n_global_sequences = len(self.global_sequences)

                if not c_obj:
                    bpy.ops.object.empty_add(type='SINGLE_ARROW', location=(0, 0, 0))
                    c_obj = bpy.context.scene.objects.active
                    c_obj.name = "TT_Controller"
                    c_obj.WowM2TextureTransform.Enabled = True
                    c_obj = bpy.context.scene.objects.active
                    c_obj.rotation_mode = 'QUATERNION'
                    c_obj.empty_draw_size = 0.5
                    c_obj.animation_data_create()
                    c_obj.animation_data.action_blend_type = 'ADD'

                    self.uv_transforms[tex_tranform_index] = c_obj

                bpy.context.scene.objects.active = obj
                bpy.ops.object.modifier_add(type='UV_WARP')
                uv_transform = bpy.context.object.modifiers[-1]
                uv_transform.name = 'M2TexTransform'
                uv_transform.object_from = obj
                uv_transform.object_to = c_obj
                uv_transform.uv_layer = 'UVMap'

                obj.WowM2Geoset.UVTransform = c_obj

                # load global sequences
                for j, seq_index in enumerate(self.global_sequences):
                    anim = bpy.context.scene.WowM2Animations[seq_index]

                    name = "TT_{}_{}_Global_Sequence_{}".format(tex_tranform_index, obj.name, str(j).zfill(3))

                    cur_index = len(anim.AnimPairs)
                    anim_pair = anim.AnimPairs.add()
                    anim_pair.Object = c_obj

                    if tex_transform.translation.global_sequence == j:
                        animate_tex_transform_controller_trans(anim_pair, name, tex_transform.translation, 0)

                    if tex_transform.rotation.global_sequence == j:
                        animate_tex_transform_controller_rot(anim_pair, name, tex_transform.rotation, 0)

                    if tex_transform.scaling.global_sequence == j:
                        animate_tex_transform_controller_scale(anim_pair, name, tex_transform.scaling, 0)

                    if not anim_pair.Action:
                        anim.AnimPairs.remove(cur_index)

                # load animations
                for j, anim_index in enumerate(self.animations):
                    anim = bpy.context.scene.WowM2Animations[j + n_global_sequences]
                    sequence = self.m2.root.sequences[anim_index]

                    field_name = anim_data_dbc.get_field(sequence.id, 'Name')
                    name = 'TT_{}_{}_{}_UnkAnim'.format(tex_tranform_index, obj.name, str(j).zfill(3)) \
                        if not field_name else "TT_{}_{}_{}_{}_({})".format(tex_tranform_index,
                                                                            obj.name,
                                                                            str(j).zfill(3),
                                                                            field_name,
                                                                            sequence.variation_index)

                    cur_index = len(anim.AnimPairs)
                    anim_pair = anim.AnimPairs.add()
                    anim_pair.Object = c_obj

                    if tex_transform.translation.global_sequence < 0:
                        animate_tex_transform_controller_trans(anim_pair, name, tex_transform.translation, j)

                    if tex_transform.rotation.global_sequence < 0:
                        animate_tex_transform_controller_rot(anim_pair, name, tex_transform.rotation, j)

                    if tex_transform.scaling.global_sequence < 0:
                        animate_tex_transform_controller_scale(anim_pair, name, tex_transform.scaling, j)

                    if not anim_pair.Action:
                        anim.AnimPairs.remove(cur_index)

    def load_attachments(self):
        # TODO: unknown field

        def animate_attachment(attachment, obj, anim, anim_name, frames, track):
            anim_pair = anim.AnimPairs.add()
            anim_pair.Object = obj
            action = anim_pair.Action = bpy.data.actions.new(name=anim_name)
            action.use_fake_user = True
            anim_pair.Action = action

            # create fcurve
            f_curve = action.fcurves.new(data_path='WowM2Attachment.Animate')

            # init translation keyframes on the curve
            f_curve.keyframe_points.add(len(frames))

            # set translation values for each channel
            for k, timestamp in enumerate(frames):
                frame = timestamp * 0.0266666
                keyframe = f_curve.keyframe_points[k]
                keyframe.co = frame, track[k]
                keyframe.interpolation = 'LINEAR' if attachment.animate_attached.interpolation_type == 1 else 'CONSTANT'

        for i, attachment in enumerate(self.m2.root.attachments):
            bpy.ops.object.empty_add(type='SPHERE', location=(0, 0, 0))
            obj = bpy.context.scene.objects.active
            obj.scale = (0.094431, 0.094431, 0.094431)
            obj.empty_draw_size = 0.07
            bpy.ops.object.constraint_add(type='COPY_TRANSFORMS')
            constraint = obj.constraints[-1]
            constraint.target = self.rig
            obj.parent = self.rig
            bone = self.m2.root.bones[attachment.bone]
            constraint.subtarget = bone.name

            bl_edit_bone = self.rig.data.bones[bone.name]
            obj.location = bl_edit_bone.matrix_local.inverted() * Vector(attachment.position)

            obj.name = M2AttachmentTypes.get_attachment_name(attachment.id, i)
            obj.WowM2Attachment.Enabled = True
            obj.WowM2Attachment.Type = str(attachment.id)

            # Animate attachment
            obj.animation_data_create()
            obj.animation_data.action_blend_type = 'ADD'
            anim_data_dbc = load_game_data().db_files_client.AnimationData
            n_global_sequences = len(self.global_sequences)

            # load global sequences
            for j, seq_index in enumerate(self.global_sequences):
                anim = bpy.context.scene.WowM2Animations[seq_index]

                if attachment.animate_attached.global_sequence == j:
                    frames = attachment.animate_attached.timestamps[0]
                    track = attachment.animate_attached.values[0]

                    if not len(frames):
                        continue

                    name = "AT_{}_{}_Global_Sequence_{}".format(i, obj.name, str(j).zfill(3))

                    animate_attachment(attachment, obj, anim, name, frames, track)

            # load animations
            for j, anim_index in enumerate(self.animations):
                anim = bpy.context.scene.WowM2Animations[j + n_global_sequences]
                sequence = self.m2.root.sequences[anim_index]

                if attachment.animate_attached.timestamps.n_elements > anim_index:
                    frames = attachment.animate_attached.timestamps[anim_index]
                    track = attachment.animate_attached.values[anim_index]

                    if not len(frames):
                        continue

                    field_name = anim_data_dbc.get_field(sequence.id, 'Name')
                    name = 'AT_{}_{}_UnkAnim'.format(i, obj.name, str(j).zfill(3)) if not field_name \
                        else "AT_{}_{}_{}_({})".format(i, obj.name, str(j).zfill(3), field_name,
                                                       sequence.variation_index)

                    animate_attachment(attachment, obj, anim, name, frames, track)

    def load_lights(self):

        def animate_light_properties(obj, prop_path, m2_track):
            panel, prop = prop_path.split('.')
            obj.animation_data_create()
            obj.animation_data.action_blend_type = 'ADD'

            for i, action in enumerate(self.animations):
                obj.animation_data.action = action

                try:
                    frames = m2_track.timestamps[i]
                except IndexError:
                    break

                for j, frame in enumerate(frames):
                    bpy.context.scene.frame_set(frame * 0.0266666)

                    setattr(getattr(obj.data, panel), prop, m2_track.values[i][j])

                    obj.data.keyframe_insert(data_path='["{}"]["{}"]'.format(panel, prop))

            obj.animation_data.action = self.animations[0]

        for i, light in enumerate(self.m2.root.lights):
            bpy.ops.object.lamp_add(type='POINT' if light.type else 'SPOT', location=(0, 0, 0))
            obj = bpy.context.scene.objects.active
            obj.data.WowM2Light.Type = str(light.type)

            if self.rig:
                obj.parent = self.rig

            if light.bone >= 0:
                bpy.ops.object.constraint_add(type='CHILD_OF')
                constraint = obj.constraints[-1]
                constraint.target = self.rig
                bone = self.m2.root.bones[light.bone]
                constraint.subtarget = bone.name

                bl_edit_bone = self.rig.data.bones[bone.name]
                obj.location = bl_edit_bone.matrix_local.inverted() * Vector(light.position)

            '''
            # import animated values
            animate_light_properties(obj, 'WowM2Light.AmbientColor', light.ambient_color)
            animate_light_properties(obj, 'WowM2Light.AmbientIntensity', light.ambient_intensity)
            animate_light_properties(obj, 'WowM2Light.DiffuseColor', light.diffuse_color)
            animate_light_properties(obj, 'WowM2Light.DiffuseIntensity', light.diffuse_intensity)
            animate_light_properties(obj, 'WowM2Light.AttenuationStart', light.attenuation_start)
            animate_light_properties(obj, 'WowM2Light.AttenuationEnd', light.attenuation_end)
            animate_light_properties(obj, 'WowM2Light.Enabled', light.visibility)
            '''

    def load_events(self):

        def animate_event(event, obj, anim_name, frames):
            anim_pair = anim.AnimPairs.add()
            anim_pair.Object = obj
            action = anim_pair.Action = bpy.data.actions.new(name=anim_name)
            action.use_fake_user = True
            anim_pair.Action = action

            # create fcurve
            f_curve = action.fcurves.new(data_path='WowM2Event.Fire')

            # init translation keyframes on the curve
            f_curve.keyframe_points.add(len(frames))

            # fire event
            for k, timestamp in enumerate(frames):
                frame = timestamp * 0.0266666
                keyframe = f_curve.keyframe_points[k]
                keyframe.co = frame, True
                keyframe.interpolation = 'LINEAR' if event.enabled.interpolation_type == 1 else 'CONSTANT'

        if not len(self.m2.root.events):
            print("\nNo events found to import.")
            return
        else:
            print("\nImport events.")

        for event in self.m2.root.events:
            bpy.ops.object.empty_add(type='CUBE', location=(0, 0, 0))
            obj = bpy.context.scene.objects.active
            obj.scale = (0.019463, 0.019463, 0.019463)
            bpy.ops.object.constraint_add(type='CHILD_OF')
            constraint = obj.constraints[-1]
            constraint.target = self.rig
            obj.parent = self.rig
            bone = self.m2.root.bones[event.bone]
            constraint.subtarget = bone.name

            bl_edit_bone = self.rig.data.bones[bone.name]
            obj.location = bl_edit_bone.matrix_local.inverted() * Vector(event.position)
            token = M2EventTokens.get_event_name(event.identifier)
            obj.name = "Event_{}".format(token)
            obj.WowM2Event.Enabled = True
            obj.WowM2Event.Token = event.identifier

            if obj.name in ('PlayEmoteSound',
                            'DoodadSoundUnknown',
                            'DoodadSoundOneShot',
                            'GOPlaySoundKitCustom',
                            'GOAddShake'):
                obj.WowM2Event.Data = event.data

            # animate event firing
            obj.animation_data_create()
            obj.animation_data.action_blend_type = 'ADD'
            anim_data_dbc = load_game_data().db_files_client.AnimationData
            n_global_sequences = len(self.global_sequences)

            # load global sequences
            for j, seq_index in enumerate(self.global_sequences):
                anim = bpy.context.scene.WowM2Animations[seq_index]

                if event.enabled.global_sequence == j:
                    frames = event.enabled.timestamps[0]

                    if not len(frames):
                        continue

                    name = 'ET_{}_{}_UnkAnim'.format(token, str(j).zfill(3))

                    animate_event(event, obj, name, frames)

            # load animations
            for j, anim_index in enumerate(self.animations):
                anim = bpy.context.scene.WowM2Animations[j + n_global_sequences]
                sequence = self.m2.root.sequences[anim_index]

                if event.enabled.timestamps.n_elements > anim_index:
                    frames = event.enabled.timestamps[anim_index]

                    if not len(frames):
                        continue

                    field_name = anim_data_dbc.get_field(sequence.id, 'Name')
                    name = 'ET_{}_{}_UnkAnim'.format(token, str(anim_index).zfill(3)) if not field_name \
                        else "ET_{}_{}_{}_({})".format(token, str(anim_index).zfill(3), field_name,
                                                       sequence.variation_index)

                    animate_event(event, obj, name, frames)

    def load_particles(self):
        if not len(self.m2.root.particles):
            print("\nNo particles found to import.")
            return
        else:
            print("\nImport particles.")

        for particle in self.m2.root.particles:
            if particle.emitter_type == 1:
                bpy.ops.mesh.primitive_plane_add(radius=1, location=(0, 0, 0))
                emitter = bpy.context.scene.objects.active
                emitter.dimensions[0] = particle.emission_area_length
                emitter.dimensions[1] = particle.emission_area_width

            elif particle.emitter_type == 2:
                bpy.ops.mesh.primitive_uv_sphere_add(size=particle.emission_area_length, location=(0, 0, 0))
                emitter = bpy.context.scene.objects.active
                # TODO: emission_area_with

            elif particle.emitter_type == 3:
                pass

    def load_collision(self):

        if not len(self.m2.root.collision_vertices):
            print("\nNo collision mesh found to import.")
            return
        else:
            print("\nImporting collision mesh.")

        vertices = [vertex for vertex in self.m2.root.collision_vertices]
        triangles = [self.m2.root.collision_triangles[i:i+3] for i in range(0, len(self.m2.root.collision_triangles), 3)]

        # create mesh
        mesh = bpy.data.meshes.new(self.m2.root.name.value)
        mesh.from_pydata(vertices, [], triangles)

        for poly in mesh.polygons:
            poly.use_smooth = True

        # create object
        obj = bpy.data.objects.new('Collision', mesh)
        bpy.context.scene.objects.link(obj)
        obj.WowM2Geoset.CollisionMesh = True
        obj.hide = True
        # TODO: add transparent material

    def save_properties(self, filepath, selected_only):
        self.m2.root.name.value = os.path.basename(filepath)
        objects = bpy.context.selected_objects if selected_only else bpy.context.scene.objects
        b_min, b_max = get_objs_boundbox_world(filter(lambda ob: not ob.WowM2Geoset.CollisionMesh
                                                                 and ob.type == 'MESH'
                                                                 and not ob.hide, objects))

        self.m2.root.bounding_box.min = b_min
        self.m2.root.bounding_box.max = b_max
        self.m2.root.bounding_sphere_radius = sqrt((b_max[0]-b_min[0]) ** 2
                                                   + (b_max[1]-b_min[2]) ** 2
                                                   + (b_max[2]-b_min[2]) ** 2) / 2

        # TODO: flags, collision bounding box

    def save_bones(self, selected_only):

        def add_bone(bl_bone):
            key_bone_id = int(bl_bone.WowM2Bone.KeyBoneID)
            flags = construct_bitfield(bl_bone.WowM2Bone.Flags)
            parent_bone = self.bone_ids[bl_bone.parent.name] if bl_bone.parent else -1
            pivot = bl_bone.head

            self.bone_ids[bl_bone.name] = self.m2.add_bone(pivot, key_bone_id, flags, parent_bone)

        rigs = list(filter(lambda ob: ob.type == 'ARMATURE' and not ob.hide, bpy.context.scene.objects))

        if len(rigs) > 1:
            raise Exception('Error: M2 exporter does not support more than one armature. Hide or remove the extra one.')

        for rig in rigs:
            self.rig = rig
            bpy.context.scene.objects.active = rig
            bpy.ops.object.mode_set(mode='EDIT')

            armature = rig.data

            # find root bone, check if we only have one root bone
            root_bone = None
            global_bones = []
            for bone in armature.edit_bones:
                if root_bone is not None and bone.parent is None and bone.children:
                    raise Exception('Error: M2 exporter does not support more than one global root bone.')

                if bone.parent is None:
                    if bone.children:
                        root_bone = bone
                        add_bone(root_bone)
                    else:
                        global_bones.append(bone)

            # add global bones
            for bone in global_bones:
                add_bone(bone)

            # find root keybone, write additional bones
            root_keybone = None

            for bone in root_bone.children:

                if bone.WowM2Bone.KeyBoneID == '26':
                    root_keybone = bone
                    continue

                add_bone(bone)
                for child_bone in bone.children_recursive:
                    add_bone(child_bone)

            # write root keybone and its children
            if root_keybone:
                add_bone(root_keybone)
                for bone in root_keybone.children_recursive:
                    add_bone(bone)

            bpy.ops.object.mode_set(mode='OBJECT')

            break

        else:
            # Add an empty bone, if the model is not animated
            if selected_only:
                bpy.ops.object.select_all(action='SELECT')
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
                origin = get_origin_position()
                bpy.ops.object.select_all(action='DESELECT')
            else:
                origin = get_origin_position()

            self.m2.add_dummy_anim_set(origin)

    def save_animations(self):

        # if there are no actions, make a default Stand anim.
        if not len(bpy.data.actions):
            self.m2.add_dummy_anim_set()

        for action in bpy.data.actions:
            seq_id = self.m2.add_anim(
                action.WowM2Animation.AnimationID,
                action.WowM2Animation.VariationNext,
                action.frame_range.to_tuple(),
                action.WowM2Animation.Movespeed,
                construct_bitfield(action.WowM2Animation.Flags),
                action.WowM2Animation.Frequency,
                (action.WowM2Animation.ReplayMin, action.WowM2Animation.ReplayMax),
                action.WowM2Animation.BlendTime,  # TODO: multiversioning
                action.WowM2Animation.VariationNext,
                action.WowM2Animation.AliasNext
            )

            for fcurve in action.fcurves:
                pass

    def save_geosets(self, selected_only, fill_textures):
        objects = bpy.context.selected_objects if selected_only else bpy.context.scene.objects
        if not objects:
            raise Exception('Error: no mesh found on the scene or selected.')

        # deselect all objects before saving geosets
        bpy.ops.object.select_all(action='DESELECT')

        proxy_objects = []
        for obj in filter(lambda ob: not ob.WowM2Geoset.CollisionMesh and ob.type == 'MESH' and not ob.hide, objects):

            new_obj = obj.copy()
            new_obj.data = obj.data.copy()
            proxy_objects.append(new_obj)

            bpy.context.scene.objects.link(new_obj)

            bpy.context.scene.objects.active = new_obj
            mesh = new_obj.data

            # security checks

            if not mesh.uv_layers.active:
                raise Exception("Mesh <<{}>> has no UV map.".format(obj.name))

            if len(mesh.materials) > 1:
                raise Exception("Mesh <<{}>> has more than one material applied.".format(obj.name))

            # apply all modifiers
            if len(obj.modifiers):
                for modifier in obj.modifiers:
                    bpy.ops.object.modifier_apply(modifier=modifier.name)

            # triangulate mesh, delete loose geometry
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.reveal()
            bpy.ops.mesh.quads_convert_to_tris()
            bpy.ops.mesh.delete_loose()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')

            # prepare scene
            ###################################

            # perform edge split
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.seams_from_islands(mark_seams=False, mark_sharp=True)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')

            bpy.ops.object.modifier_add(type='EDGE_SPLIT')
            bpy.context.object.modifiers["EdgeSplit"].use_edge_angle = False
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="EdgeSplit")

            # smooth edges
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.mark_sharp(clear=True)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')

            # export vertices
            vertices = [new_obj.matrix_world * vertex.co for vertex in mesh.vertices]
            normals = [vertex.normal for vertex in mesh.vertices]
            tex_coords = [(0.0, 0.0)] * len(vertices)

            for loop in mesh.loops:
                tex_coords[loop.vertex_index] = (mesh.uv_layers.active.data[loop.index].uv[0],
                                                 1 - mesh.uv_layers.active.data[loop.index].uv[1])

            tris = [poly.vertices for poly in mesh.polygons]

            tex_coords2 = []
            if len(mesh.uv_layers) >= 2:
                tex_coords2 = [mesh.uv_layers[1].data[loop.vertex_index].uv for loop in mesh.loops]

            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
            origin = new_obj.location

            sort_pos = get_obj_boundbox_center(new_obj)
            sort_radius = get_obj_radius(new_obj, sort_pos)

            # collect rig data
            if new_obj.vertex_groups:
                bpy.ops.object.vertex_group_limit_total(limit=4)

            if bpy.data.actions:

                bone_indices = []
                bone_weights = []

                for vertex in mesh.vertices:
                    v_bone_indices = [0, 0, 0, 0]
                    v_bone_weights = [0, 0, 0, 0]

                    for i, group_info in enumerate(vertex.groups):
                        bone_id = self.bone_ids.get(new_obj.vertex_groups[i].name)
                        weight = group_info.weight

                        if bone_id is None:
                            bone_id = 0
                            weight = 0

                        v_bone_indices[i] = bone_id
                        v_bone_weights[i] = int(weight * 255)

                    bone_indices.append(v_bone_indices)
                    bone_weights.append(v_bone_weights)

            else:
                bone_indices = [[0, 0, 0 ,0] for _ in mesh.vertices]
                bone_weights = [[255, 0, 0, 0] for _ in mesh.vertices]

            # add geoset
            g_index = self.m2.add_geoset(vertices, normals, tex_coords, tex_coords2, tris, bone_indices, bone_weights,
                                         origin, sort_pos, sort_radius, int(new_obj.WowM2Geoset.MeshPartID))  # TODO: second UV

            material = mesh.materials[0]
            bl_texture = material.active_texture
            wow_path = bl_texture.WowM2Texture.Path

            if fill_textures and not wow_path:
                wow_path = resolve_texture_path(bl_texture.image.filepath)

            tex_id = self.m2.add_texture(wow_path,
                                         construct_bitfield(bl_texture.WowM2Texture.Flags),
                                         int(bl_texture.WowM2Texture.TextureType)
                                         )

            render_flags = construct_bitfield(material.WowM2Material.RenderFlags)
            flags = construct_bitfield(material.WowM2Material.Flags)
            bl_mode = int(material.WowM2Material.BlendingMode)
            shader_id = int(material.WowM2Material.Shader)

            self.m2.add_material_to_geoset(g_index, render_flags, bl_mode, flags, shader_id, tex_id)

        # remove temporary objects
        for obj in proxy_objects:
            bpy.data.objects.remove(obj, do_unlink=True)

    def save_collision(self, selected_only):
        objects = bpy.context.selected_objects if selected_only else bpy.context.scene.objects
        objects = list(filter(lambda ob: ob.WowM2Geoset.CollisionMesh and ob.type == 'MESH' and not ob.hide, objects))

        proxy_objects = []

        for obj in objects:
            new_obj = obj.copy()
            new_obj.data = obj.data.copy()
            proxy_objects.append(new_obj)

            bpy.context.scene.objects.link(new_obj)

            bpy.context.scene.objects.active = new_obj
            mesh = new_obj.data

            # apply all modifiers
            if len(obj.modifiers):
                for modifier in obj.modifiers:
                    bpy.ops.object.modifier_apply(modifier=modifier.name)

            # triangulate mesh, delete loose geometry
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.reveal()
            bpy.ops.mesh.quads_convert_to_tris()
            bpy.ops.mesh.delete_loose()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')

            # collect geometry data
            vertices = [tuple(new_obj.matrix_world * vertex.co) for vertex in mesh.vertices]
            faces = [tuple([vertex for vertex in poly.vertices]) for poly in mesh.polygons]
            normals = [tuple(poly.normal) for poly in mesh.polygons]

            self.m2.add_collision_mesh(vertices, faces, normals)

        # remove temporary objects
        for obj in proxy_objects:
            bpy.data.objects.remove(obj, do_unlink=True)

        # calculate collision bounding box
        b_min, b_max = get_objs_boundbox_world(objects)
        self.m2.root.collision_box.min = b_min
        self.m2.root.collision_box.max = b_max
        self.m2.root.collision_sphere_radius = sqrt((b_max[0] - b_min[0]) ** 2
                                                    + (b_max[1] - b_min[2]) ** 2
                                                    + (b_max[2] - b_min[2]) ** 2) / 2

