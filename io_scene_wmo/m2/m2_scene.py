import bpy
import os
from mathutils import Vector

from ..pywowlib.enums.m2_enums import M2SkinMeshPartID, M2AttachmentTypes, M2EventTokens
from ..pywowlib.io_utils.types import uint32, vec3D
from ..pywowlib.file_formats.m2_format import M2CompQuaternion
from ..utils import parse_bitfield, construct_bitfield, load_game_data


class BlenderM2Scene:
    def __init__(self, m2, prefs):
        self.m2 = m2
        self.materials = {}
        self.geosets = []
        self.animations = []
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

            self.materials[tex_unit.skin_section_index] = blender_mat

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

        skin = self.m2.skins[0]

        for i, smesh in enumerate(skin.submeshes):
            bl_obj = self.geosets[i]
            bl_obj.parent = rig

            # bind armature to geometry
            bpy.context.scene.objects.active = bl_obj
            bpy.ops.object.modifier_add(type='ARMATURE')
            bpy.context.object.modifiers["Armature"].object = rig

            vgroups = {}
            for j in range(smesh.vertex_start, smesh.vertex_start + smesh.vertex_count):
                m2_vertex = self.m2.root.vertices[skin.vertex_indices[j]]
                for b_index, bone_index in enumerate(filter(lambda x: x > 0, m2_vertex.bone_indices)):
                    vgroups.setdefault(self.m2.root.bones[bone_index].name, []).append((j - smesh.vertex_start, m2_vertex.bone_weights[b_index] / 255))

            for name in vgroups.keys():
                if len(vgroups[name]) > 0:
                    grp = bl_obj.vertex_groups.new(name)
                    for (v, w) in vgroups[name]:
                        grp.add([v], w, 'REPLACE')

    def load_animations(self):
        if not len(self.m2.root.sequences):
            print("\nNo animation data found to import.")
            return
        else:
            print("\nImporting animations.")

        if not self.rig:
            print("\nArmature is not present on the scene. Skipping animation import. M2 is most likely corrupted.")
            return

        rig = self.rig
        rig.animation_data_create()
        bpy.context.scene.objects.active = rig
        bpy.ops.object.mode_set(mode='POSE')

        load_game_data()
        anim_data_dbc = bpy.db_files_client.AnimationData

        # import animation sequences
        for i, sequence in enumerate(self.m2.root.sequences):
            field_name = anim_data_dbc.get_field(sequence.id, 'Name')

            name = '{}_UnkAnim'.format(str(i).zfill(3)) if not field_name \
                else "{}_{}_({})".format(str(i).zfill(3), field_name, sequence.variation_index)

            action = bpy.data.actions.new(name=name)
            action.use_fake_user = True  # TODO: check if this is the best solution
            rig.animation_data.action = action
            self.animations.append(action)

            done_rot = False
            done_trans = False
            done_scale = False

            # handles alias animations
            real_anim = sequence
            anim_idx = i
            while real_anim.flags & 0x40 and real_anim.alias_next != anim_idx:
                anim_idx = real_anim.alias_next
                real_anim = self.m2.root.sequences[real_anim.alias_next]

            anim_file = None
            if not sequence.flags & 0x130:
                anim_path = "{}{}-{}.anim".format(os.path.splitext(self.m2.root.filepath)[0],
                                                  str(real_anim.id).zfill(4), str(sequence.variation_index).zfill(2))

                # TODO: implement game-data loading
                anim_file = open(anim_path, 'rb')

            for bone in self.m2.root.bones:  # TODO <= TBC

                bl_bone = rig.pose.bones[bone.name]

                if bone.rotation.timestamps.n_elements > anim_idx:
                    rotation_frames = bone.rotation.timestamps[anim_idx]
                    rotation_track = bone.rotation.values[anim_idx]
                else:
                    rotation_frames = []
                    rotation_track = []

                if bone.translation.timestamps.n_elements > anim_idx:
                    translation_frames = bone.translation.timestamps[anim_idx]
                    translation_track = bone.translation.values[anim_idx]
                else:
                    translation_frames = []
                    translation_track = []

                if bone.scale.timestamps.n_elements > anim_idx:
                    scale_frames = bone.scale.timestamps[anim_idx]
                    scale_track = bone.scale.values[anim_idx]
                else:
                    scale_frames = []
                    scale_track = []

                if anim_file:
                    if len(rotation_frames):
                        anim_file.seek(rotation_frames.ofs_elements)
                        rotation_frames.values = [uint32.read(anim_file) for _ in range(rotation_frames.n_elements)]

                        anim_file.seek(rotation_track.ofs_elements)
                        rotation_track.values = [M2CompQuaternion().read(anim_file) for _ in range(rotation_track.n_elements)]

                    if len(translation_frames):
                        anim_file.seek(translation_frames.ofs_elements)
                        translation_frames.values = [uint32.read(anim_file) for _ in range(translation_frames.n_elements)]

                        anim_file.seek(translation_track.ofs_elements)
                        translation_track.values = [vec3D.read(anim_file) for _ in range(translation_track.n_elements)]

                    if len(scale_frames):
                        anim_file.seek(scale_frames.ofs_elements)
                        scale_frames.values = [uint32.read(anim_file) for _ in range(scale_frames.n_elements)]

                        anim_file.seek(scale_track.ofs_elements)
                        scale_track.values = [vec3D.read(anim_file) for _ in range(scale_track.n_elements)]

                for j, frame in enumerate(rotation_frames):
                    bpy.context.scene.frame_set(frame * 0.0266666)
                    bl_bone.rotation_quaternion = rotation_track[j].to_quaternion()
                    bl_bone.keyframe_insert(data_path='rotation_quaternion', group=bone.name)
                    done_rot = True

                for j, frame in enumerate(translation_frames):
                    bpy.context.scene.frame_set(frame * 0.0266666)
                    bl_bone.location = bl_bone.bone.matrix_local.inverted() * (Vector(bone.pivot) +
                                                                               Vector(translation_track[j]))
                    bl_bone.keyframe_insert(data_path='location')
                    done_trans = True

                for j, frame in enumerate(scale_frames):
                    bpy.context.scene.frame_set(frame * 0.0266666)
                    bl_bone.scale = scale_track[j]
                    bl_bone.keyframe_insert(data_path='scale')
                    done_scale = True

                if not done_rot:
                    bpy.context.scene.frame_set(0)
                    bl_bone.keyframe_insert(data_path='rotation_quaternion')
                if not done_trans:
                    bpy.context.scene.frame_set(0)
                    bl_bone.keyframe_insert(data_path='location')
                if not done_scale:
                    bpy.context.scene.frame_set(0)
                    bl_bone.keyframe_insert(data_path='scale')

        rig.animation_data.action = self.animations[0]
        bpy.context.scene.frame_set(0)

        bpy.ops.object.mode_set(mode='OBJECT')

        # set animation properties
        for i, action in enumerate(self.animations):
            m2_sequence = self.m2.root.sequences[i]

            action.WowM2Animation.AnimationID = str(m2_sequence.id)
            action.WowM2Animation.Flags = parse_bitfield(m2_sequence.flags, 0x800)
            action.WowM2Animation.Movespeed = m2_sequence.movespeed
            action.WowM2Animation.Frequency = m2_sequence.frequency
            action.WowM2Animation.ReplayMin = m2_sequence.replay.minimum
            action.WowM2Animation.ReplayMax = m2_sequence.replay.maximum
            action.WowM2Animation.BlendTime = m2_sequence.blend_time

            if m2_sequence.variation_next > 0:
                action.WowM2Animation.VariationNext = bpy.data.actions[m2_sequence.variation_next]

            if m2_sequence.alias_next != i:
                action.WowM2Animation.AliasNext = bpy.data.actions[m2_sequence.alias_next]

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
            material = self.materials[smesh_i]
            mesh.materials.append(material)

            for i, poly in enumerate(mesh.polygons):
                uv1.data[i].image = material.active_texture.image
                poly.material_index = 0

            # get object name
            name = M2SkinMeshPartID.get_mesh_part_name(smesh.skin_section_id)
            obj = bpy.data.objects.new(name if name else 'Geoset', mesh)
            bpy.context.scene.objects.link(obj)

            obj.WowM2Geoset.MeshPartGroup = name
            obj.WowM2Geoset.MeshPartID = str(smesh.skin_section_id)

            self.geosets.append(obj)

    def load_attachments(self):
        # TODO: unknown field

        for i, attachment in enumerate(self.m2.root.attachments):
            bpy.ops.object.empty_add(type='SPHERE', location=(0, 0, 0))
            obj = bpy.context.scene.objects.active
            obj.scale = (0.094431, 0.094431, 0.094431)
            bpy.ops.object.constraint_add(type='CHILD_OF')
            constraint = obj.constraints[-1]
            constraint.target = self.rig
            obj.parent = self.rig
            bone = self.m2.root.bones[attachment.bone]
            constraint.subtarget = bone.name

            bl_edit_bone = self.rig.data.bones[bone.name]
            obj.location = bl_edit_bone.matrix_local.inverted() * Vector(attachment.position)

            obj.name = M2AttachmentTypes.get_attachment_name(attachment.id, i)
            obj.WowM2Attachment.Type = str(attachment.id)
            bl_edit_bone.name = obj.name

    def load_lights(self):

        def animate_light_properties(obj, prop_path, m2_track):
            panel, prop = prop_path.split('.')
            obj.animation_data_create()

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

            # import animated values
            animate_light_properties(obj, 'WowM2Light.AmbientColor', light.ambient_color)
            animate_light_properties(obj, 'WowM2Light.AmbientIntensity', light.ambient_intensity)
            animate_light_properties(obj, 'WowM2Light.DiffuseColor', light.diffuse_color)
            animate_light_properties(obj, 'WowM2Light.DiffuseIntensity', light.diffuse_intensity)
            animate_light_properties(obj, 'WowM2Light.AttenuationStart', light.attenuation_start)
            animate_light_properties(obj, 'WowM2Light.AttenuationEnd', light.attenuation_end)
            animate_light_properties(obj, 'WowM2Light.Enabled', light.visibility)

    def load_events(self):
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
            obj.name = M2EventTokens.get_event_name(event.identifier)
            obj.WowM2Event.Token = event.identifier
            obj.WowM2Event.Data = event.data

            # animate event firing
            obj.animation_data_create()

            for i, action in enumerate(self.animations):
                obj.animation_data.action = action

                try:
                    frames = event.enabled.timestamps[i]
                except IndexError:
                    break

                for j, frame in enumerate(frames):
                    bpy.context.scene.frame_set(frame * 0.0266666)

                    obj.WowM2Event.Enabled = True

                    obj.keyframe_insert(data_path='["WowM2Event"]["Enabled"]')

            obj.animation_data.action = self.animations[0]

    def load_particles(self):
        if not len(self.m2.root.particles):
            print("\nNo particles found to import.")
            return
        else:
            print("\nImport particles.")

    def load_collision(self):

        if not len(self.m2.root.collision_vertices):
            print("\nNo collision mesh found to import.")
            return
        else:
            print("\nImporting collision mesh.")

        vertices = [vertex.values for vertex in self.m2.root.collision_vertices]
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

    def save_bones(self, selected_only):
        rigs = list(filter(lambda ob: ob.type == 'ARMATURE' and not ob.hide, bpy.context.scene.objects))

        if len(rigs) > 1:
            raise Exception('Error: M2 exporter does not support more than one armature. Hide or remove the extra one.')

        for rig in rigs:
            self.rig = rig
            bpy.context.scene.objects.active = rig
            bpy.ops.object.mode_set(mode='EDIT')

            armature = rig.data

            for bone in armature.edit_bones:
                m2_bone = self.m2.root.bones.new()
                m2_bone.key_bone_id = bone.WowM2Bone.KeyBoneID
                m2_bone.flags = construct_bitfield(bone.WowM2Bone.Flags)
                m2_bone.parent_bone = armature.edit_bones.index(bone.parent) if bone.parent else -1
                m2_bone.pivot = bone.head

            break

        else:
            # Add an empty bone, if the model is not animated
            if selected_only:
                bpy.ops.view3d.snap_cursor_to_selected()
                self.m2.add_dummy_bone(bpy.context.scene.cursor_location.to_tuple())
            else:
                bpy.ops.object.select_all(action='SELECT')
                bpy.ops.view3d.snap_cursor_to_selected()
                self.m2.add_dummy_bone(bpy.context.scene.cursor_location.to_tuple())
                bpy.ops.object.select_all(action='DESELECT')

    def save_geosets(self, selected_only):
        objects = bpy.context.selected_objects if selected_only else bpy.context.scene.objects
        if not objects:
            raise Exception('Error: no mesh found on the scene or selected.')

        # deselect all objects before saving geosets
        bpy.ops.object.select_all(action='DESELECT')

        proxy_objects = []
        for obj in filter(lambda ob: not ob.WowM2Geoset.CollisionMesh and obj.type == 'MESH' and not obj.hide, objects):

            new_obj = obj.copy()
            new_obj.data = obj.data.copy()

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
            tex_coords = [mesh.uv_layers.active.data[loop.vertex_index].uv for loop in mesh.loops]
            tris = [poly.vertices for poly in mesh.polygons]

            tex_coords2 = []
            if len(mesh.uv_layers) >= 2:
                tex_coords2 = [mesh.uv_layers[1].data[loop.vertex_index].uv for loop in mesh.loops]

            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')  # TODO: find a better way to do this
            bpy.ops.view3d.snap_cursor_to_selected()
            origin = bpy.context.scene.cursor_location

            self.m2.add_geoset(vertices, normals, tex_coords, tex_coords2, tris, origin, )  # TODO: bone stuff

        for obj in proxy_objects:
            bpy.data.objects.remove(obj, do_unlink=True)







