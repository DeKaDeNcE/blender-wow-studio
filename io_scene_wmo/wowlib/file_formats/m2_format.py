from .wow_common_types import *

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
            if_(VERSION >= M2Versions.MOP,
                'flag_load_phys_data',
                unk,
                if_(VERSION >= M2Versions.WOD),
                    unk, # denon hunter tatoo glow
                    "flag_camera_related", #TODO: verify version
                    if_(VERSION >= M2Versions.LEGION), # not sure
                        "flag_new_particle_record",

    )

