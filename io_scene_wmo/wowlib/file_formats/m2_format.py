from wow_common_types import *

VERSION = 264

class M2Versions:
    CLASSIC = 256
    TBC = 263
    WOTLK = 264
    CATA = 272
    MOP = 272
    WOD = 273 # ?
    LEGION = 274
    # BFA - ?

#############################################################
######                 M2 Common Types                 ######
#############################################################

class M2Bounds(Struct):
    __fields__ = (
        CAaBox | 'extent',
        float32 | 'radius'
    )


class M2Array(Struct):
    __slots__ = ("elements", "e_read", "e_write", "type")
    __fields__ = (
        uint32 | 'n_elements',
        uint32 | 'ofs_elements'
    )

    def __init__(self, type_t, *args, **kwargs):
        self.type = type_t

        if type(type_) in (GenericType, string_t):
            self.e_read = lambda f: type_t.__read__(f)
            self.e_write = lambda f, e: type_t.__write__(f, e)
        else:
            self.e_read = lambda f: type_t().__read__(f)
            self.e_write = lambda f, e: e.__write__(f)

        self.elements = []

    def __read__(self, f):
        super().__read__(f)
        pos = f.tell()
        f.seek(self.ofs_elements)
        self.elements = [self.e_read(f) for _ in range(self.n_elements)]
        f.seek(pos)

    def __write__(self, f):
        self.n_elements = len(self.elements)
        self.ofs_elements = request_offset(self.n_elements, sizeof(self.type))
        super().__write__(f)
        pos = f.tell()
        f.seek(self.ofs_elements)
        for element in self.elements:
            self.e_write(f, element)
        f.seek(pos)


class M2SplineKey(Struct):
    __fields__ = (
        template_T[0] | 'value',
        template_T[0] | 'in_tan',
        template_T[0] | 'out_tan'
    )

class M2Range(Struct):
    __fields__ = (
        uint32 | 'minimum',
        uint32 | 'maximum'
    )

class M2Track(Struct):
    __fields__ = (
        uint16 | 'interpolation_type',
        uint16 | 'global_sequence',
        if_(VERSION < M2Versions.WOTLK),
            M2Array << M2Range,
            M2Array << uint32 | 'timestamps',
        else_,
            M2Array << (M2Array << uint32) | 'timestamps',
        endif_,

        if_(VERSION < M2Versions.WOTLK),
            M2Array << template_T[0] | 'values',
        else_,
            M2Array << (M2Array << template_T[0]) | 'values',
        endif_
    )

#############################################################
######                  M2 Chunks                      ######
#############################################################

# The following section applies to Legion+

class PFID(Struct):
    __fields__ = (
        string_t[4] | ('magic', 'DIFP'),
        uint32 | ('size', 4),
        uint32 | 'phys_file_id'
    )

class SFID(Struct):
    pass

class Chunk(Struct):
    __fields__ = ()
    def __write__(self, f):
        self.size = self.__size__() - 8
        super().__write__(f)

class AnimFileID(Struct):
    __fields__ = (
        uint16 | 'anim_id',
        uint16 | 'sub_anim_id',
        uint32 | 'file_id'
    )

class AFID(Chunk):
    __fields__ = (
        string_t[4] | ('magic', 'DIFA'),
        uint32 | 'size',
        dynamic_array[this.size / 8] << AnimFileID | 'anim_file_ids'
    )



#############################################################
######                  M2 Header                      ######
#############################################################

class M2Header(Struct):
    __fields__ = (
        string_t[4] | ('magic', 'MD20' if VERSION < M2Versions.LEGION else 'MD21'),
        uint32 | ('version', VERSION),
        M2Array << char | 'name',
        M2GlobalFlags | 'global_flags',
        M2Array << M2Loop | 'global_loops',
        M2Array << M2Sequence | 'sequences',
        M2Array << uint16 | 'sequence_lookups',

        if_(VERSION <= M2Versions.TBC),
            M2Array << uint32 | 'playable_animation_lookup',     # type is unk
        endif_,
        
        M2Array << M2CompBone | 'bones',                         # 0x100 bones max
        M2Array << uint16 | 'key_bone_lookup',
        M2Array << M2Vertex | 'vertices',

        if_(VERSION <= M2Versions.TBC),
            M2Array << M2SkinProfile | 'skin_profiles',
        else_,
            uint32 | 'num_skin_profiles',
        endif_,

        M2Array << M2Color | 'colors',                             # Color and alpha animations definitions.
        M2Array << M2Texture | 'textures',
        M2Array << M2TextureWeight | 'texture_weights',            # Transparency of textures.

        if_(VERSION <= M2Versions.TBC),
            M2Array << uin16 | 'unknown',                          # type is unk
        endif_,

        M2Array << M2TextureTransform | 'texture_transforms',
        M2Array << uint16 | 'replacable_texture_lookup',
        M2Array << M2Material | 'materials',                       # Blending modes / render flags.
        M2Array << uint16 | 'bone_lookup_table',
        M2Array << uint16 | 'texture_lookup_table',
        M2Array << uint16 | 'tex_unit_lookup_table',               # ≥ Cata: unused
        M2Array << uint16 | 'transparency_lookup_table',
        M2Array << uint16 | 'texture_transforms_lookup_table',

        CAaBox | 'bounding_box',                                   # min/max( [1].z, 2.0277779f ) - 0.16f seems to be the maximum camera height
        float3 | 'bounding_sphere_radius',                         # detail doodad draw dist = clamp (bounding_sphere_radius * detailDoodadDensityFade * detailDoodadDist, …)
        CAaBox | 'collision_box',
        float32 | 'collision_sphere_radius',

        M2Array << uint16 | 'collision_triangles',
        M2Array << C3Vector | 'collision_vertices',
        M2Array << C3Vector | 'collision_normals',
        M2Array << M2Attachment | 'attachments',                   # position of equipped weapons or effects
        M2Array << uint16 | 'attachment_lookup_table',
        M2Array << M2Event | 'events',                             # Used for playing sounds when dying and a lot else.
        M2Array << M2Light | 'lights',                             # Lights are mainly used in loginscreens but in wands and some doodads too.
        M2Array << M2Camera | 'cameras',                           # The cameras are present in most models for having a model in the character tab. 
        M2Array << uint16 | 'camera_lookup_table',
        M2Array << M2Ribbon | 'ribbon_emitters',                   # Things swirling around. See the CoT-entrance for light-trails.
        M2Array << M2Particle | 'particle_emitters',

        # TODO: implement on-demand fields
        '''
        #if ≥ Wrath                                              # TODO: verify version
        if (flag_use_texture_combiner_combos)
        {
            M2Array << uint16 | textureCombinerCombos,           # When set, textures blending is overriden by the associated array.
        }
        #endif
        '''
    )

class M2GlobalFlags(Bitfield):
    __fields__ = (
        "flag_tilt_x",
        "flag_tilt_y",
        if_(VERSION >= M2Versions.WOTLK), # verify version
            "flag_use_texture_combiner_combos",
            unk,
            if_(VERSION >= M2Versions.MOP),
                'flag_load_phys_data',
                unk,
                if_(VERSION >= M2Versions.WOD),
                    unk, # denon hunter tatoo glow
                    "flag_camera_related", #TODO: verify version
                    if_(VERSION >= M2Versions.LEGION), # not sure
                        "flag_new_particle_record",

    )

#############################################################
######              Animation sequences                ######
#############################################################

class M2Sequence(Struct):
    __fields__ = (
        uint16 | "id",                       # Animation id in AnimationData.dbc
        uint16 | "variation_index",          # Sub-animation id: Which number in a row of animations this one is.
        if_(VERSION <= M2Versions.TBC),
            uint32 | "start_timestamp",
            uint32 | "end_timestamp",
        else_,
            uint32 | "duration",             # The length of this animation sequence in milliseconds.
        endif_,

        float32 | "movespeed",               # This is the speed the character moves with in this animation.
        M2SequenceFlags << uint32 | "flags", # See below.
        int16 | "frequency",                 # This is used to determine how often the animation is played. For all animations of the same type, this adds up to 0x7FFF (32767).
        uint16 | "_padding",
        M2Range | "replay",                  # May both be 0 to not repeat. Client will pick a random number of repetitions within bounds if given.
        
        if_(VERSION < M2Versions.WOD),
            uint32 | "blend_time",
        else_,
            uint16 | "blend_time_in",        # The client blends (lerp) animation states between animations where the end and start values differ. This specifies how long that blending takes. Values: 0, 50, 100, 150, 200, 250, 300, 350, 500.
            uint16 | "blend_time_out",       # The client blends between this sequence and the next sequence for blendTimeOut milliseconds.
        endif_,
                                             # For both blendTimeIn and blendTimeOut, the client plays both sequences simultaneously while interpolating between their animation transforms.
        M2Bounds | "bounds",
        int16 | "variation_next",            # id of the following animation of this AnimationID, points to an Index or is -1 if none.
        uint16 | "alias_next",               # id in the list of animations. Used to find actual animation if this sequence is an alias (flags & 0x40)
    )

class M2SequenceFlags:
        blended_animation_auto = 0x1         # Sets 0x80 when loaded. (M2Init)                
        load_low_priority_sequence = 0x10    # apparently set during runtime in CM2Shared::LoadLowPrioritySequence for all entries of a loaded sequence (including aliases)
        looped_animation = 0x20              # primary bone sequence -- If set, the animation data is in the .m2 file. If not set, the animation data is in an .anim file.
        is_alias = 0x40                      # has next / is alias (To find the animation data, the client skips these by following aliasNext until an animation without 0x40 is found.)
        blended_animation = 0x80             # Blended animation (if either side of a transition has 0x80, lerp between end->start states, unless end==start by comparing bone values)
        sequence_stored_in_model = 0x100     # sequence stored in model ?
        some_legion_flag = 0x800             # seen in Legion 24500 models

# TODO: animation lookup
# TODO: playable animation lookup (<= TBC)

#############################################################
######                     Bones                       ######
#############################################################

class M2CompBone(Struct):
    __fields__ = (
        int32 | "key_bone_id",                    # Back-reference to the key bone lookup table. -1 if this is no key bone.
        uint32 | "flags",                 
        int16 | "parent_bone",                    # Parent bone ID or -1 if there is none.
        uint16 | "submesh_id",
        
        # union
        uint16 | "u_dist_to_furth_desc",
        uint16 | "u_zration_of_chain",    
        # uint32 | boneNameCRC",                  # these are for debugging only. their bone names match those in key bone lookup.
        # unionend

        M2Track << C3Vector | "translation",
        if_(VERSION <= M2Versions.CLASSIC),
            M2Track << C4Quaternion | "rotation",
        else_,
            M2Track << M2CompQuat | "rotation",   # compressed values, default is (32767,32767,32767,65535) == (0,0,0,1) == identity
        endif_,
        M2Track << C3Vector | "scale",
        C3Vector |  "pivot",                      # The pivot point of that bone.
    )

class M2CompBoneFlags:
    spherical_billboard = 0x8,
    cylindrical_billboard_lock_x = 0x10,
    cylindrical_billboard_lock_y = 0x20,
    cylindrical_billboard_lock_z = 0x40,
    transformed = 0x200,
    kinematic_bone = 0x400,                       # MoP+: allow physics to influence this bone
    helmet_anim_scaled = 0x1000,                  # set blend_modificator to helmetAnimScalingRec.m_amount for this bone
