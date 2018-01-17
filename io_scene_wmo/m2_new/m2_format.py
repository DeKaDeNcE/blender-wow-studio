import struct

from .wow_common_types import *
from ..binary_parser.binary_types import *
from mathutils import Vector
from functools import partial

VERSION = 264


##### Types #####

class M2CompQuaternion(Struct):
    __fields__ = (
        uint16 | 'x',
        uint16 | 'y',
        uint16 | 'z',
        uint16 | 'w',
    )

    #TODO: Divide by 0x7FFFF

    def __init__(self, tuple=(0, 0, 0, 1)):
        super().__init__()
        self.x = tuple[0]
        self.y = tuple[1]
        self.z = tuple[2]
        self.w = tuple[3]

    def to_bl_quaternion(self):
        return Quaternion((self.w, self.x, self.y, self.z))

    @classmethod
    def from_bl_quaternion(cls, qtrn):
        return cls((qtrn[1], qtrn[2], qtrn[3], qtrn[0]))


class M2Bounds(Struct):
    __fields__ = (
        CAaBox | 'extent',
        float32 | 'radius'
    )

class M2InterpolationRange(Struct):
    __fields__ = (
        uint32 | 'start',
        uint32 | 'end'
    )

class M2Array:
    def __init__(self, type):
        self.type = type
        self.data = []

    def read(self, f):
        number = struct.unpack('I', f.read(4))[0]
        offset = struct.unpack('I', f.read(4))[0]

        old_pos = f.tell()
        f.seek(offset)
        for _ in range(number):
            data_block = self.type()
            data_block.__read__f)
            self.data.append(data_block)
        f.seek(old_pos)

    def write(self, f):
        f.write(struct.pack('I', len(self.data)))
        f.write(struct.pack('I'))

        old_pos = f.tell()
        f.seek(data_ofs)
        for data_block in self.data:
            data_block.__write__(f)
        new_pos = f.tell() - old_pos
        f.seek(old_pos)

        return new_pos


class M2Track(Struct):
    __fields__ = (
        uint16 | 'interpolation_type',
        uint16 | 'global_sequence_index',
        if_(VERSION < M2Versions.WOTLK),
        M2Array << (pair << uint32) | 'interpolation_ranges',
        M2Array << uint32 | 'timestamps',
        M2Array << template_T | 'values',
        else_,
        M2Array << (M2Array << uint32) | 'timestamps',
        M2Array << (M2Array << template_T) | 'values',
        endif_
    )


class M2FakeTrack(Struct):
    __fields__ = (
        M2Array << uint32 | 'timestamps',
        M2Array << uint32 | 'values'
    )


class M2Loop(Struct):
    ''' A list of timestamps that act as upper limits for global sequence ranges. '''
    __fields__ = {
        'timestamps': uint32
    }


# TODO find out what this one is for.
class M2SplineKey:
    def __init__(self):
        self.value = None
        self.in_tan = None
        self.out_tan = None

class M2Box(Struct):
    __fields__ = (
        C3Vector | 'model_rotation_speed_min',
        C3Vector | 'model_rotation_speed_max'
    )


##### Versions #####

class M2Versions:
    CLASSIC = 256  # and lower
    TBC = 263  # 260-263
    WOTLK = 264
    CATA = 272  # 265-272
    MOP = 272
    WOD = 273  # ????
    LEGION = 274


##### Chunks #####

class PFID_Chunk(Struct):
    __fields__ = {
        'header': ChunkHeader,
        'phys_file_id': uint32
    }

    def write(self, f):
        self.header.magic = 'DIFP'
        self.header.size = 4
        super().write(f)

class SFID_Chunk(Struct):
    __fields__ = {
        'header': ChunkHeader
    }

    def __init__(self, n_views, n_lod_bands):
        super().__init__()
        self.__fields__['']

    def __init__(self):
        self.header = ChunkHeader()
        self.skin_file_data_ids = []
        self.lod_skin_file_data_ids = []

    def read(self, f, n_views, n_lod_bands):
        self.header.read(f)
        for _ in range(n_views):
            self.skin_file_data_ids.append(struct.unpack('I', f.read(4))[0])

        for _ in range(n_lod_bands):
            self.lod_skin_file_data_ids.append(struct.unpack('I', f.read(4))[0])

    def write(self, f):
        self.header.magic = 'DIFS'
        self.header.size = (len(self.skin_file_data_ids) + len(self.lod_skin_file_data_ids)) * 4
        self.header.write(f)

        for skin_file_data_id in self.skin_file_data_ids:
            f.write(struct.pack('I', skin_file_data_id))

        for lod_skin_file_data_id in self.lod_skin_file_data_ids:
            f.write(struct.pack('I', lod_skin_file_data_id))


class AnimFileID(Struct):
    __fields__ = (
        uint8 | 'anim_id',
        uint8 | 'sub_anim_id',
        uint32 | 'file_id'

    )

class AFID_Chunk(Struct):
    __fields__ = (
        ChunkHeader | 'header',

    )

    def __init__(self):
        self.header = ChunkHeader()
        self.anim_file_ids = []

    def read(self, f, n_anim_files):
        self.header.read(f)
        for _ in range(n_anim_files):
            anim_file_id = AnimFileID()
            anim_file_id.read(f)
            self.anim_file_ids.append(anim_file_id)

    def write(self, f):
        self.header.magic = 'DIFA'
        self.header.size = len(self.anim_file_ids) * 8
        self.header.write(f)
        for anim_file_id in self.anim_file_ids:
            anim_file_id.write(f)


class BFID_Chunk:
    def __init__(self):
        self.header = ChunkHeader()
        self.bone_file_data_ids = []

    def read(self, f):
        self.header.read(f)

        for _ in range(self.header.size // 4):
            self.bone_file_data_ids.append(struct.unpack('I', f.read(4))[0])

    def write(self, f):
        self.header.magic = 'DIFB'
        self.header.size = len(self.bone_file_data_ids) * 4
        self.header.write(f)

        for bone_file_data_id in self.bone_file_data_ids:
            f.write(struct.pack('I', bone_file_data_id))


class M2GlobalFlags:
    TILT_X = 0x1
    TILT_Y = 0x2
    UNK_0x4 = 0x4
    # >= WOTLK
    HAS_BLEND_MAPS = 0x8
    UNK_0x10 = 0x10
    # >= MOP
    LOAD_PHYS_DATA = 0x20
    UNK_0x40 = 0x40
    # >= WOD
    UNK_0x80 = 0x80
    CAMERA_RELATED = 0x100
    # >= LEGION
    NEW_PARTICLE_RECORD = 0x200
    UNK_0x400 = 0x400
    UNK_0x800 = 0x800
    UNK_0x1000 = 0x1000
    UNK_0x2000 = 0x2000
    UNK_0x4000 = 0x4000
    UNK_0x8000 = 0x8000


class M2Header(Struct):
    __fields__ = (
        ChunkHeader | 'header',
        uint32 | 'version',
        M2Array << char | 'name',
        uint32 | 'global_flags',
        M2Array << M2Loop | 'global_loops',
        M2Array << M2Sequence | 'sequences',
        M2Array << uint16 | 'sequence_lookup',

        if_(VERSION <= M2Versions.TBC),
        M2Array << uint16 | 'playable_animation_lookup',  # TODO: verify type
        endif_,

        M2Array << M2CompBone | 'bones',
        M2Array << uint16 | 'key_bone_lookup',
        M2Array << M2Vertex | 'vertices',

        if_(VERSION <= M2Versions.TBC),
        M2Array << M2SkinProfile | 'skin_profiles',
        else_,
        uint32 | 'num_skin_profiles',
        endif_,

        M2Array << M2Color | 'colors',
        M2Array << M2Texture | 'textures',
        M2Array << M2TextureWeight | 'texture_weights',

        if_(VERSION <= M2Versions.TBC),
        M2Array << unk | 'unknown',  # TODO: verify type
        endif_,

        M2Array << M2TextureTransform | 'texture_transforms',
        M2Array << uint16 | 'replaceable_texture_lookup',
        M2Array << M2Material | 'materials',
        M2Array << uint16 | 'bone_lookup_table',
        M2Array << uint16 | 'texture_lookup_table',
        M2Array << uint16 | 'tex_unit_lookup_table',  # >= cata unused
        M2Array << uint16 | 'transparency_lookup_table',
        M2Array << uint16 | 'texture_transforms_lookup_table',

        CAaBox | 'bounding_box',
        float32 | 'bounding_sphere_radius',
        CAaBox | 'collision_box',
        float32 | 'collision_sphere_radius',

        M2Array << uint16 | 'collision_triangles',
        M2Array << C3Vector | 'collision_vertices',
        M2Array << C3Vector | 'collision_normals',
        M2Array << M2Attachment | 'attachments',
        M2Array << uint16 | 'attachment_lookup_table',
        M2Array << M2Event | 'events',
        M2Array << M2Light | 'lights',
        M2Array << M2Camera | 'cameras',
        M2Array << uint16 | 'camera_lookup_table',
        M2Array << M2Ribbon | 'ribbon_emitters',

        if_(VERSION <= M2Versions.WOTLK),
        M2Array << M2ParticleOld | 'particle_emitters',
        else_,
        M2Array << M2Particle | 'particle_emitters',
        endif_

        # TODO: implement on-demand structure
    )


#######################
##### Data-blocks #####
#######################

##### Skeleton and animation #####

# == Animation sequences == #

class M2SequenceFlags:
    UNK_0x1 = 0x1  # Sets 0x80 when loaded. (M2Init)
    UNK_0x2 = 0x2
    UNK_0x4 = 0x4
    UNK_0x8 = 0x8
    LOAD_LOW_PRIORITY = 0x10
    LOOP_ANIMATION = 0x20
    HAS_NEXT = 0x40  # client skips the following next sequences until the one with flag 0x40 found
    BLEND_ANIMATION = 0x80  # Blended animation (if either side of a transition has 0x80,
    # lerp between end->start states, unless end==start by comparing bone values)
    STORE_SEQ_IN_MODEL = 0x100


class M2Sequence(Struct):
    __fields__ = (
        uint16 | 'id',
        uint16 | 'variation_index',

        if_(VERSION <= M2Versions.TBC),
        uint32 | 'start_timestamp',
        uint32 | 'end_timestamp',
        else_,
        uint32 | 'duration',
        endif_,

        float32 | 'movespeed',
        uint32 | 'flags',
        int16 | 'frequency',
        uint16 | 'padding',
        M2Range | 'replay',
        uint32 | 'blendtime',
        M2Bounds | 'bounds',
        int16 | 'variation_next',
        uint16 | 'alias_next'
    )

class PlayableAnimationLookupFlags:  # TODO: check if other variations are ever seen
    PLAY_NORMAL = 0
    PLAY_BACKWARDS = 1
    FREEZE = 3


class M2PlayableAnimationIndex(Struct):  # < TBC
    __fields__ = (
        int16 | 'fallback_animation_id',
        int16 | 'flags'
    )

# == Bones == #

class M2CompBoneFlags:
    SPHERICAL_BILLBOARD = 0x8
    CYLINDRICAL_BILLBOARD_LOCK_X = 0x10
    CYLINDRICAL_BILLBOARD_LOCK_Y = 0x20
    CYLINDRICAL_BILLBOARD_LOCK_Z = 0x40
    TRANSFORMED = 0x200
    KINEMATIC_BONE = 0x400
    HELMET_ANIM_SCALED = 0x1000


class M2CompBone(Struct):
    __fields__ = (
        int32 | 'key_bone_id',
        uint32 | 'flags',
        int16 | 'parent_bone',
        uint16 | 'submesh_id',

        if_(VERSION >= M2Versions.TBC),
        uint16 | 'unk',  #TODO: see wiki, IRC 02.07.2017
        uint32 | 'bone_name_crc',

        M2Track << C3Vector | 'translation',
        if_(VERSION >= M2Versions.CLASSIC),
        M2Track << C4Quaternion | 'rotation',
        else_,
        M2Track << M2CompQuaternion | 'rotation',
        endif_,
        M2Track << C3Vector | 'scale',
        C3Vector | 'pivot'
    )

M2KeyBoneNames = [
    "ArmL", "ArmL", "ArmR",
    "ShoulderL", "ShoulderR",
    "SpineLow", "Waist", "Head", "Jaw",
    "IndexFingerR", "MiddleFingerR", "PinkyFingerR", "RingFingerR", "ThumbR",
    "IndexFingerL", "MiddleFingerL", "PinkyFingerL", "RingFingerL", "ThumbL",
    "$BTH", "$CSR", "$CSL",
    "_Breath", "_Name", "_NameMount",
    "$CHD", "$CCH", "Root",
    "Wheel1", "Wheel3", "Wheel4", "Wheel5", "Wheel6", "Wheel7", "Wheel8"
]


##### Geometry and rendering #####

class M2Vertex(Struct):
    __fields__ = (
        C3Vector << float32 | 'pos',
        static_array[4] << uint8 | 'bone_weights',
        static_array[4] << uint8 | 'bone_indices',
        C3Vector << float32 | 'normal',
        static_array[2] << (C2Vector << float32) | 'text_coords'

    )


class M2RenderFlags:
    UNLIT = 0x1
    UNFOGGED = 0x2
    TWO_SIDED = 0x4
    BILLBOARD = 0x8
    NOT_ZBUFFERED = 0x10
    UNK_SHADOW_BATCH_1 = 0x40
    UNK_SHADOW_BATCH_2 = 0x80
    UNK_0x400 = 0x400
    PREVENT_ALPHA = 0x800


class M2BlendingModes:
    MOD = 1
    DECAL = 2
    ADD = 3
    MOD_2X = 4
    FADE = 5
    DEEPRUN_TRAM = 6
    UNK_WOD = 7


class M2Material(Struct):
    __fields__ = (
        uint16 | 'flags',
        uint16 | 'blending_mode'
    )


class M2TextureUnitLookupTable:

    def __init__(self):
        self.texture_units = []

    def read(self, f, size):
        for _ in range(size // 2):
            self.texture_units.append(struct.unpack('H', f.read(2))[0])

    def write(self, f):
        for tex_unit in self.texture_units:
            f.write('H', tex_unit)


# == Colors and transparency == #

class M2Color(Struct):
    __fields__ = (
        M2Track << C3Vector | 'color',
        M2Track << fixed16 | 'alpha'

    )

'''
class M2TextureWeight(Struct):
    __fields__ = (
        M2Track << fixed16 | 'weight'
    )
'''


# == Textures == #

class M2Texture(Struct):
    __fields__ = (
        uint32 | 'type',
        uint32 | 'flags',
        M2Array << char | 'filename' #TODO: implement string type reading

    )


class M2TextureTypes:
    NONE = 0
    SKIN = 1
    OBJECT_SKIN = 2
    WEAPON_BLADE = 3
    WEAPON_HANDLE = 4
    ENVIRONMENT = 5
    CHAR_HAIR = 6
    CHAR_FACIAL_HAIR = 7
    SKIN_EXTRA = 8
    UI_SKIN = 9
    TAUREN_MANE = 10
    MONSTER_1 = 11
    MONSTER_2 = 12
    MONSTER_3 = 13
    ITEM_ICON = 14
    GUILD_BG_COLOR = 15
    GUILD_EMBLEM_COLOR = 16
    GUILD_BORDER_COLOR = 17
    GULD_EMBLEM = 18


# == Effects == #

class M2TextureTransform(Struct):
    __fields__ = (
        M2Track << C3Vector | 'translation',
        M2Track << C4Quaternion | 'rotation',
        M2Track << C3Vector | 'scaling'
    )


class M2RibbonEmitter(Struct):
    __fields__ = (
        uint32 | 'ribbon_id',
        uint32 | 'bone_index',
        C3Vector | 'position',
        M2Array << uint16 | 'texture_indices',
        M2Array << uint16 | 'material_indices',
        M2Track << C3Vector | 'color_track',
        M2Track << fixed16 | 'alpha_track',
        M2Track << float32 | 'height_above_track',
        M2Track << float32 | 'height_below_track',
        float32 | 'edge_lifetime',
        float32 | 'gravity',
        uint16 | 'texture_rows',
        uint16 | 'texture_cols',
        M2Track << uint16 | 'tex_slot_track',
        M2Track << uint8 | 'visibility_track',  #TODO: check template type

        if_(VERSION >= M2Versions.WOTLK),
            int16 | 'priority_plane',
            uint16 | 'padding',
            endif_
    )


class M2ParticleOld(Struct):
    __fields__ = (
        uint32 | 'particle_id',
        uint32 | 'flags',
        C3Vector | 'position',
        uint16 | 'bone',

        if_(VERSION >= M2Versions.CATA),
        #TODO: implement bitfield in binary reader
        else_,
        uint16 | 'texture',

        M2Array << char | 'geometry_model_filename',
        M2Array << char | 'recursion_model_filename',

        if_(VERSION <= M2Versions.TBC),
            uint8 | 'blending_type',
            uint8 | 'emitter_type',
            uint16 | 'particle_color_index',
        else_,
            uint16 | 'blending_type',
            uint16 | 'emitter_type',
        endif_,

        if_(VERSION >= M2Versions.CATA),
        #TODO: implement fixed_point type
        else_,
            uint8 | 'particle_type',
            uint8 | 'head_or_tail',
        endif_,

        uint16 | 'texture_tile_rotation',
        uint16 | 'texture_dimensions_rows',
        uint16 | 'texture_dimensions_columns',
        M2Track << float32 | 'emission_speed',
        M2Track << float32 | 'speed_variation',
        M2Track << float32 | 'vertical_range',
        M2Track << float32 | 'horizontal_range',
        M2Track << float32 | 'gravity',
        M2Track << float32 | 'lifespan',

        if_(VERSION >= M2Versions.WOTLK),
            float32 | 'lifespan_vary',
        endif_,

        M2Track << float32 | 'emission_rate',

        if_(VERSION >= M2Versions.WOTLK),
            float32 | 'emission_rate_vary',
        endif_,

        M2Track << float32 | 'emission_area_length',
        M2Track << float32 | 'emission_area_width',
        M2Track << float32 | 'z_source',

        if_(VERSION >= M2Versions.WOTLK),
            M2FakeTrack << C3Vector | 'color_track',
            M2FakeTrack << C2Vector | 'scale_track',
            C2Vector | 'scale_vary',
            M2FakeTrack << uint16 | 'head_cell_track',
            M2FakeTrack << uint16 | 'tail_cell_track',
        else_,
            float32 | 'mid_point',
        #TODO: implement containers
        endif_,

        float32 | 'tail_length',
        float32 | 'twinkle_speed',
        CRange | 'twinkle_scale',
        float32 | 'burst_multiplier',
        float32 | 'drag',

        if_(VERSION >= M2Versions.WOTLK),
            float32 | 'base_spin',
            float32 | 'base_spin_vary',
            float32 | 'spin',
            float32 | 'spin_vary',
        else_,
            float32 | 'spin',
        endif_,

        M2Box | 'tumble',
        C3Vector | 'wind_vector',
        float32 | 'wind_time',
        float32 | 'follow_speed_1',
        float32 | 'follow_scale1',
        float32 | 'follow_speed_2',
        M2Array << C3Vector | 'spline_points',
        M2Track << uint8 | 'enabled_in'
    )

class M2ParicleOldEmittersTypes:
    RECTANGLE = 1
    SPHERE = 2
    SPLINE = 3
    BONE = 4

class M2BoundingVertices(Struct):
    __fields__ = (
        C3Vector | 'position'
    )

class M2BoundingTriangles(Struct):
    __fields__ = (
            uint16 | 'index'
    )

class M2BoundingNormals(Struct):
    __fields__ = (
        C3Vector | 'normal'
    )

class M2Light(Struct):
    __fields__ = (
        uint16 | 'type',
        int16 | 'bone',
        C3Vector | 'position',
        M2Track << C3Vector | 'ambient_color',
        M2Track << float32 | 'ambient_intensity',
        M2Track << C3Vector | 'diffuse_color',
        M2Track << float32 | 'diffuse_intensity',
        M2Track << float32 | 'attenuation_start',
        M2Track << float32 | 'attenuation_end',
        M2Track << boolean | 'visibility'
    )


class M2Camera(Struct):
    __fields__ = (
        uint32 | 'type',

        if_(VERSION < M2Versions.CATA),
        float32 | 'fov',
        endif_,

        float32 | 'far_clip',
        float32 | 'near_clip',
        M2Track << (M2SplineKey << C3Vector) | 'positions',
        C3Vector | 'position_base',
        M2Track << (M2SplineKey << C3Vector) | 'target_position',
        C3Vector | 'target_position_base',
        M2Track << (M2SplineKey << float32) | 'roll',

        if_(VERSION >= M2Versions.CATA),
        M2Track << (M2SplineKey << float32) | 'fov',
        endif_
    )

class M2Attachment(Struct):
    __fields__ = (
        uint32 | 'id',
        uint16 | 'bone',
        uint16 | 'unknown',
        C3Vector | 'position',
        M2Track << boolean | 'animate_attached'
    )

class M2Events(Struct):
    __fields__ = (
        uint32 | 'identifier',
        uint32 | 'data',
        uint32 | 'bone',
        C3Vector | 'position',
        uint16 | 'interpolation_type',
        uint16 | 'global_sequence'
    )








class M2GlobalSequences:
    def __init__(self):
        self.loops = []

    def read(self, f, n_loops):
        for _ in range(n_loops):
            loop = M2Loop()
            loop.read(f)
            self.loops.append(loop)

    def write(self, f):
        for loop in self.loops:
            loop.write(f)


class M2Data:
    def __init__(self, version):
        self.header = ChunkHeader()
        self.header.magic = '02DM' if version < M2Versions.LEGION else '12DM'

        if version == M2Versions.WOTLK:









