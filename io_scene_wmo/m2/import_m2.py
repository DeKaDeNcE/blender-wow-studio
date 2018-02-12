import bpy
import os
from io import BytesIO
from ..pywowlib.m2_file import M2File
from ..pywowlib.enums.m2_enums import M2SkinMeshPartID, M2AttachmentTypes
from ..pywowlib.wdbx.wdbc import DBCFile
from ..pywowlib.wdbx.definitions.wotlk import AnimationData
from ..pywowlib.io_utils.types import uint32, vec3D
from ..pywowlib.file_formats.m2_format import M2CompQuaternion

from ..utils import parse_bitfield
from mathutils import Vector


class BlenderM2Scene:
    def __init__(self, m2, skins, prefs):
        self.m2 = m2
        self.skins = skins
        self.materials = {}
        self.geosets = []
        self.rig = None
        self.collision_mesh = None
        self.settings = prefs

    def load_materials(self, texture_dir):
        # TODO: multitexturing
        skin = self.skins[0]  # assuming first skin is the most detailed one

        for tex_unit in skin.texture_units:
            texture = self.m2.textures[self.m2.texture_lookup_table[tex_unit.texture_combo_index]].filename.value
            texture_png = os.path.splitext(texture)[0] + '.png'
            m2_mat = self.m2.materials[tex_unit.material_index]

            # creating material
            blender_mat = bpy.data.materials.new(os.path.basename(texture_png))

            tex1_slot = blender_mat.texture_slots.create(0)
            tex1_slot.uv_layer = "UVMap"
            tex1_slot.texture_coords = 'UV'

            tex1_name = blender_mat.name + "_Tex_02"
            tex1 = bpy.data.textures.new(tex1_name, 'IMAGE')
            tex1_slot.texture = tex1

            # loading images
            if os.name != 'nt': texture_png = texture_png.replace('\\', '/')  # reverse slahes for unix

            try:
                tex1_img = bpy.data.images.load(os.path.join(texture_dir, texture_png))
                tex1.image = tex1_img
                blender_mat.active_texture = tex1
            except RuntimeError:
                pass

            ''' NEEDS UI
            # filling material settings
            parse_bitfield(tex_unit.flags, blender_mat.WowM2Material.Flags, 0x80)  # texture unit flags
            parse_bitfield(m2_mat.flags, blender_mat.WowM2Material.RenderFlags, 0x800)  # render flags

            blender_mat.WowM2Material.BlendingMode = m2_mat.blending_mode  # TODO: ? bitfield
            blender_mat.WowM2Material.Shader = tex_unit.shader_id
            '''

            # TODO: other settings

            self.materials[tex_unit.skin_section_index] = blender_mat

    def load_armature(self):
        if not len(self.m2.bones):
            print("\nNo armature found to import.")
            return

        print("\nImporting armature")

        # Create armature
        armature = bpy.data.armatures.new('{}_Armature'.format(self.m2.name.value))
        rig = bpy.data.objects.new(self.m2.name.value, armature)
        rig.location = (0, 0, 0)
        self.rig = rig

        # Link the object to the scene
        scene = bpy.context.scene
        scene.objects.link(rig)
        scene.objects.active = rig
        scene.update()

        bpy.ops.object.mode_set(mode='EDIT')

        for i, bone in enumerate(self.m2.bones):  # add bones to armature.
            bl_edit_bone = armature.edit_bones.new(bone.name)
            bl_edit_bone.head = Vector(bone.pivot)

            bl_edit_bone.tail.x = bl_edit_bone.head.x + 0.1 # TODO: mess with bones parenting even more
            bl_edit_bone.tail.y = bl_edit_bone.head.y
            bl_edit_bone.tail.z = bl_edit_bone.head.z

        for i, bone in enumerate(self.m2.bones):  # link children to parents
            if bone.parent_bone >= 0:
                bl_edit_bone = armature.edit_bones[bone.name]
                parent = armature.edit_bones[self.m2.bones[bone.parent_bone].name]
                bl_edit_bone.parent = parent

        bpy.context.scene.update()  # update scene.
        bpy.ops.object.mode_set(mode='OBJECT')  # return to object mode.

        skin = self.skins[0]

        for i, smesh in enumerate(skin.submeshes):
            bl_obj = self.geosets[i]
            bl_obj.parent = rig

            # bind armature to geometry
            bpy.context.scene.objects.active = bl_obj
            bpy.ops.object.modifier_add(type='ARMATURE')
            bpy.context.object.modifiers["Armature"].object = rig

            vgroups = {}
            for j in range(smesh.vertex_start, smesh.vertex_start + smesh.vertex_count):
                m2_vertex = self.m2.vertices[skin.vertex_indices[j]]
                for b_index, bone_index in enumerate(filter(lambda x: x > 0, m2_vertex.bone_indices)):
                    vgroups.setdefault(self.m2.bones[bone_index].name, []).append((j - smesh.vertex_start, m2_vertex.bone_weights[b_index] / 255))

            for name in vgroups.keys():
                if len(vgroups[name]) > 0:
                    grp = bl_obj.vertex_groups.new(name)
                    for (v, w) in vgroups[name]:
                        grp.add([v], w, 'REPLACE')

    def load_animations(self):
        if not len(self.m2.sequences):
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

        game_data = getattr(bpy, "wow_game_data", None)
        if not game_data:
            bpy.ops.scene.load_wow_filesystem()

        anim_data_dbc = DBCFile(AnimationData)
        anim_data_dbc.read(BytesIO(game_data.read_file('DBFilesClient\\AnimationData.dbc')))

        for i, sequence in enumerate(self.m2.sequences):
            field_name = None
            if anim_data_dbc:
                field_name = anim_data_dbc.get_field(sequence.id, 'Name')

            name = '{}_UnkAnim'.format(str(i).zfill(3)) if not field_name \
                else "{}_{}_({})".format(str(i).zfill(3), field_name, sequence.variation_index)

            action = bpy.data.actions.new(name=name)
            action.use_fake_user = True  # TODO: check if this is the best solution
            rig.animation_data.action = action

            done_rot = False
            done_trans = False
            done_scale = False

            anim_file = None
            if not sequence.flags & 0x130:
                anim_path = "{}{}-{}.anim".format(os.path.splitext(self.m2.filepath)[0],
                                                  str(sequence.id).zfill(4), str(sequence.variation_index).zfill(2))

                # TODO: implement game-data loading
                anim_file = open(anim_path, 'rb')

            for bone in self.m2.bones:  # TODO <= TBC

                bl_bone = rig.pose.bones[bone.name]

                if bone.rotation.timestamps.n_elements > i:
                    rotation_frames = bone.rotation.timestamps[i]
                    rotation_track = bone.rotation.values[i]
                else:
                    rotation_frames = []
                    rotation_track = []

                if bone.translation.timestamps.n_elements > i:
                    translation_frames = bone.translation.timestamps[i]
                    translation_track = bone.translation.values[i]
                else:
                    translation_frames = []
                    translation_track = []

                if bone.scale.timestamps.n_elements > i:
                    scale_frames = bone.scale.timestamps[i]
                    scale_track = bone.scale.values[i]
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

        rig.animation_data.action = bpy.data.actions[0]
        bpy.context.scene.frame_set(0)

        bpy.ops.object.mode_set(mode='OBJECT')

    def load_geosets(self):
        if not len(self.m2.vertices):
            print("\nNo mesh geometry found to import.")
            return

        else:
            print("\nImporting geosets.")

        skin = self.skins[0]

        for smesh_i, smesh in enumerate(skin.submeshes):

            vertices = [self.m2.vertices[skin.vertex_indices[i]].pos
                        for i in range(smesh.vertex_start, smesh.vertex_start + smesh.vertex_count)]

            normals = [self.m2.vertices[skin.vertex_indices[i]].normal
                       for i in range(smesh.vertex_start, smesh.vertex_start + smesh.vertex_count)]

            tex_coords = [self.m2.vertices[skin.vertex_indices[i]].tex_coords
                          for i in range(smesh.vertex_start, smesh.vertex_start + smesh.vertex_count)]

            triangles = [[skin.triangle_indices[i + j] - smesh.vertex_start for j in range(3)]
                         for i in range(smesh.index_start, smesh.index_start + smesh.index_count, 3)]

            # create mesh
            mesh = bpy.data.meshes.new(self.m2.name.value)
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

            self.geosets.append(obj)

    def load_attachments(self):
        # TODO: store attachment type
        # TODO: unknown field

        for i, attachment in enumerate(self.m2.attachments):
            bpy.ops.object.empty_add(type='SPHERE', location=(0, 0, 0))
            obj = bpy.context.scene.objects.active
            obj.scale = (0.094431, 0.094431, 0.094431)
            bpy.ops.object.constraint_add(type='CHILD_OF')
            constraint = obj.constraints[-1]
            constraint.target = self.rig
            obj.parent = self.rig
            bone = self.m2.bones[attachment.bone]
            constraint.subtarget = bone.name

            bl_edit_bone = self.rig.data.bones[bone.name]
            obj.location = bl_edit_bone.matrix_local.inverted() * Vector(attachment.position)

            obj.name = M2AttachmentTypes.get_attachment_name(attachment.id, i)
            bl_edit_bone.name = obj.name

    def load_lights(self):
        # TODO: animate values after UI is implemented
        for i, light in enumerate(self.m2.lights):
            bpy.ops.object.lamp_add(type='POINT' if light.type else 'SPOT', location=(0, 0, 0))
            obj = bpy.context.scene.objects.active

            if self.rig:
                obj.parent = self.rig

            if light.bone >= 0:
                bpy.ops.object.constraint_add(type='CHILD_OF')
                constraint = obj.constraints[-1]
                constraint.target = self.rig
                bone = self.m2.bones[light.bone]
                constraint.subtarget = bone.name

    def load_collision(self):

        if not len(self.m2.collision_vertices):
            print("\nNo collision mesh found to import.")
            return
        else:
            print("\nImporting collision mesh.")

        vertices = [vertex.values for vertex in self.m2.collision_vertices]
        triangles = [self.m2.collision_triangles[i:i+3] for i in range(0, len(self.m2.collision_triangles), 3)]

        # create mesh
        mesh = bpy.data.meshes.new(self.m2.name.value)
        mesh.from_pydata(vertices, [], triangles)

        for poly in mesh.polygons:
            poly.use_smooth = True

        # create object
        obj = bpy.data.objects.new('Collision', mesh)
        bpy.context.scene.objects.link(obj)
        obj.hide = True

        # TODO: add UI
        # TODO: add transparent material


def import_m2(version, file, load_textures):  # TODO: implement multiversioning

    # get global variables
    game_data = getattr(bpy, "wow_game_data", None)
    prefs = bpy.context.user_preferences.addons.get("io_scene_wmo").preferences
    texture_dir = prefs.cache_dir_path if prefs.use_cache_dir else os.path.dirname(file)

    if type(file) is str:
        m2_file = M2File(version, filepath=file)
        m2 = m2_file.root
        m2.filepath = file  # TODO: HACK
        skins = m2_file.skin_profiles

        if load_textures:
            if not game_data:
                print("\n\n### Loading game data ###")
                bpy.ops.scene.load_wow_filesystem()
                game_data = bpy.wow_game_data

            if game_data.files:
                print("\n\n### Extracting textures ###")
                textures = [m2_texture.filename.value for m2_texture in m2.textures if not m2_texture.type]
                game_data.extract_textures_as_png(texture_dir, textures)

        print("\n\n### Importing M2 model ###")

        bl_m2 = BlenderM2Scene(m2, skins, prefs)

        bl_m2.load_materials(texture_dir)
        bl_m2.load_geosets()
        bl_m2.load_armature()
        bl_m2.load_animations()
        bl_m2.load_attachments()
        bl_m2.load_collision()
        bl_m2.load_lights()

    else:
        pass







