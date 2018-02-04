from enum import IntEnum
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
    __slots__ = ("elements", "type")
    __fields__ = (
        uint32 | 'n_elements',
        uint32 | 'ofs_elements'
    )

    def __init__(self, *args, **kwargs):
        type_t = args[0]
        super(M2Array, self).__init__(*args, **kwargs)
        self.type = type_t
        self.elements = []

    def __read__(self, f):
        super(M2Array, self).__read__(f)
        pos = f.tell()
        f.seek(self.ofs_elements)

        type_ = type(self.type)
        if type(self.type) in (GenericType, string_t):
            self.elements = [self.type.__read__(f) for _ in range(self.n_elements)]
        elif type_ is partial:
            for _ in range(self.n_elements):
                struct = self.type()()
                struct.__read__(f)
                self.elements.append(struct)
        else:
            for _ in range(self.n_elements):
                struct = self.type()
                struct.__read__(f)
                self.elements.append(struct)

        f.seek(pos)

    def __write__(self, f):
        self.n_elements = len(self.elements)
        self.ofs_elements = request_offset(self.n_elements, sizeof(self.type))

        super(M2Array, self).__write__(f)
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


class M2TrackBase(Struct):
    __fields__ = (
        uint16 | 'interpolation_type',
        uint16 | 'global_sequence',
        if_(VERSION < M2Versions.WOTLK),
            M2Array << M2Range,
            M2Array << uint32 | 'timestamps',
        else_,
            M2Array << (M2Array << uint32) | 'timestamps',
        endif_,
    )


class M2Track(M2TrackBase):
    __fields__ = (
        if_(VERSION < M2Versions.WOTLK),
            M2Array << template_T[0] | 'values',
        else_,
            M2Array << (M2Array << template_T[0]) | 'values',
        endif_
    )


class FBlock(Struct):
    __fields__ = (
        # TODO: get back here
    )


class Vector_2fp_6_9(Struct):
    __fields__ = (
        fixed_point << (uint16, 6, 9) | 'x',
        fixed_point << (uint16, 6, 9) | 'y'
    )


class M2Box(Struct):
    __fields__ = (
        C3Vector | 'model_rotation_speed_min',
        C3Vector | 'model_rotation_speed_max'
    )

#############################################################
######                  M2 Chunks                      ######
#############################################################
# The following section applies to Legion+

'''
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
    
'''


#############################################################
######              Animation sequences                ######
#############################################################

class M2SequenceFlags:
    blended_animation_auto = 0x1             # Sets 0x80 when loaded. (M2Init)
    load_low_priority_sequence = 0x10        # apparently set during runtime in CM2Shared::LoadLowPrioritySequence for all entries of a loaded sequence (including aliases)
    looped_animation = 0x20                  # primary bone sequence -- If set, the animation data is in the .m2 file. If not set, the animation data is in an .anim file.
    is_alias = 0x40                          # has next / is alias (To find the animation data, the client skips these by following aliasNext until an animation without 0x40 is found.)
    blended_animation = 0x80                 # Blended animation (if either side of a transition has 0x80, lerp between end->start states, unless end==start by comparing bone values)
    sequence_stored_in_model = 0x100         # sequence stored in model ?
    some_legion_flag = 0x800                 # seen in Legion 24500


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
        uint32 | "flags",                    # See below.
        int16 | "frequency",                 # This is used to determine how often the animation is played. For all animations of the same type, this adds up to 0x7FFF (32767).
        uint16 | "padding",
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
            M2Track << C4Quaternion | "rotation",   # compressed values, default is (32767,32767,32767,65535) == (0,0,0,1) == identity TODO: M2CompQuat
        endif_,
        M2Track << C3Vector | "scale",
        C3Vector | "pivot",                      # The pivot point of that bone.
    )


class M2CompBoneFlags:
    spherical_billboard = 0x8,
    cylindrical_billboard_lock_x = 0x10,
    cylindrical_billboard_lock_y = 0x20,
    cylindrical_billboard_lock_z = 0x40,
    transformed = 0x200,
    kinematic_bone = 0x400,                       # MoP+: allow physics to influence this bone
    helmet_anim_scaled = 0x1000,                  # set blend_modificator to helmetAnimScalingRec.m_amount for this bone


#############################################################
######              Geometry and rendering             ######
#############################################################

###### Vertices ######

class M2Vertex(Struct):
    __fields__ = (
        C3Vector | 'pos',
        array[4] << uint8 | 'bone_weights',
        array[4] << uint8 | 'bone_indices',
        C3Vector | 'normal',
        array[2] << C2Vector | 'tex_coords'  # two textures, depending on shader used
    )


###### Render flags ######

class M2RenderFlags:
    Unlit = 0x1
    Unfogged = 0x2
    TwoSided = 0x8
    DepthWrite = 0x10
    ShadowBatch1 = 0x40
    ShadowBatch2 = 0x80
    UnkWoD = 0x400
    PreventAlpha = 0x800


class M2BlendingModes:
    Opaque = 0
    Mod = 1
    Decal = 2
    Add = 3
    Mod2X = 4
    Fade = 5
    DeeprunTram = 6
    WoD = 7


class M2Material(Struct):
    __fields__ = (
        uint16 | 'flags',
        uint16 | 'blending_mode'  # apparently a bitfield
    )


###### Colors and transparency ######

class M2Color(Struct):
    __fields__ = (
        M2Track << C3Vector | 'color',  # vertex colors in rgb order
        M2Track << fixed16 | 'alpha'    # 0 - transparent, 0x7FFF - opaque. NonInterp
    )


class M2TextureWeight(Struct):
    __fields__ = (
        M2Track << fixed16 | 'weight',
    )


###### Colors and transparency ######

class M2Texture(Struct):
    __fields__ = (
        uint32 | 'type',
        uint32 | 'flags',
        M2Array << char | 'filename'  # TODO: implement it different for strings
    )


class M2TextureTypes(IntEnum):
    NONE = 0                # Texture given in filename
    SKIN = 1                # Skin Body + clothes
    OBJECT_SKIN = 2         # Object Skin -- Item, Capes ("Item\ObjectComponents\Cape\*.blp")
    WEAPON_BLADE = 3        # Weapon Blade -- Used on several models but not used in the client as far as I see. Armor Reflect?
    WEAPON_HANDLE = 4       # Weapon Handle
    ENVIRONMENT = 5         # (OBSOLETE) Environment (Please remove from source art)
    CHAR_HAIR = 6           # Skin Body + clothes
    CHAR_FACIAL_HAIR = 7    # (OBSOLETE) Character Facial Hair (Please remove from source art)
    SKIN_EXTRA = 8          # Skin Extra
    UI_SKIN = 9             # UI Skin -- Used on inventory art M2s (1): inventoryartgeometry.m2 and inventoryartgeometryold.m2
    TAUREN_MANE = 10        # (OBSOLETE) Tauren Mane (Please remove from source art) -- Only used in quillboarpinata.m2. I can't even find something referencing that file. Oo Is it used?
    MONSTER_1 = 11          # Monster Skin 1 -- Skin for creatures or gameobjects #1
    MONSTER_2 = 12          # Monster Skin 2 -- Skin for creatures or gameobjects #2
    MONSTER_3 = 13          # Monster Skin 3 -- Skin for creatures or gameobjects #3
    ITEM_ICON = 14          # Item Icon -- Used on inventory art M2s (2): ui-button.m2 and forcedbackpackitem.m2 (CSimpleModel_ReplaceIconTexture("texture"))

    # Cata+
    GUILD_BG_COLOR = 15
    GUILD_EMBLEM_COLOR = 16
    GUILD_BORDER_COLOR = 17
    GUILD_EMBLEM = 18


class M2TextureFlags:
    T_WRAP_X = 0x1
    T_WRAP_Y = 0x2


#############################################################
######                    Effects                      ######
#############################################################

class M2TextureTransform(Struct):
    __fields__ = (
        M2Track << C3Vector | 'translation',
        M2Track << C4Quaternion | 'rotation',   # rotation center is texture center (0.5, 0.5, 0.5)
        M2Track << C3Vector | 'scaling'
    )


class M2Ribbon(Struct):
    __fields__ = (
        uint32 | 'ribbon_id',                        # Always (as I have seen): -1.
        uint32 | 'bone_index',                       # A bone to attach to.
        C3Vector | 'position',                       # And a position, relative to that bone.
        M2Array << uint16 | 'texture_indices',       # into textures
        M2Array << uint16 | 'material_indices',      # into materials
        M2Track << C3Vector | 'color_track',
        M2Track << fixed16 | 'alpha_track',          # And an alpha value in a short, where: 0 - transparent, 0x7FFF - opaque.
        M2Track << float32 | 'height_above_track',
        M2Track << float32 | 'height_below_track',   # do not set to same!
        float32 | 'edges_per_second',                # this defines how smooth the ribbon is. A low value may produce a lot of edges.
        float32 | 'edge_lifetime',                   # the length aka Lifespan. in seconds
        float32 | 'gravity',                         # use arcsin(val) to get the emission angle in degree
        uint16 | 'texture_rows',                     # tiles in texture
        uint16 | 'texture_cols',
        M2Track << uint16 | 'tex_slot_track',
        M2Track << uint8 | 'visibility_track',

        if_(VERSION >= M2Versions.WOTLK),            # TODO: verify version
            int16 | 'priority_plane',
            uint16 | 'padding',
        endif_
    )


class M2Particle(Struct):
    __fields__ = (
        uint32 | 'particle_id',                                                     # Always (as I have seen): -1.
        uint32 | 'flags',                                                           # See Below
        C3Vector | 'position',                                                      # The position. Relative to the following bone.
        uint16 | 'bone',                                                            # The bone its attached to.
        uint16 | 'texture',                                                         # And the textures that are used. For multi-textured particles actually three ids
        M2Array << int8 | 'geometry_model_filename',                                # if given, this emitter spawns models
        M2Array << int8 | 'recursion_model_filename',                               # if given, this emitter is an alias for the (maximum 4) emitters of the given model

        if_(VERSION >= M2Versions.TBC),
            uint8 | 'blending_type',                                                # A blending type for the particle. See Below
            uint8 | 'emitter_type',                                                 # 1 - Plane (rectangle), 2 - Sphere, 3 - Spline, 4 - Bone
            uint16 | 'particle_color_index',                                        # This one is used for ParticleColor.dbc. See below.
        else_,
            uint16 | 'blending_type',                                               # A blending type for the particle. See Below
            uint16 | 'emitter_type',                                                # 1 - Plane (rectangle), 2 - Sphere, 3 - Spline, 4 - Bone
        endif_,

        if_(VERSION >= M2Versions.CATA),
            array[2] << (fixed_point << uint8, 2, 5) | 'multi_texture_paramX',
        else_,
            uint8 | 'particle_type',                                                # Found below.
            uint8 | 'head_or_tail',                                                 # 0 - Head, 1 - Tail, 2 - Both
        endif_,

        uint16 | 'texture_tile_rotation',                                           # Rotation for the texture tile. (Values: -1,0,1) -- priorityPlane
        uint16 | 'texture_dimensions_rows',                                         # for tiled textures
        uint16 | 'texture_dimensions_columns',
        M2Track << float32 | 'emission_speed',                                      # Base velocity at which particles are emitted.
        M2Track << float32 | 'speed_variation',                                     # Random variation in particle emission speed. (range: 0 to 1)
        M2Track << float32 | 'vertical_range',                                      # Drifting away vertically. (range: 0 to pi) For plane generators, this is the maximum polar angle of the initial velocity;
                                                                                    # 0 makes the velocity straight up (+z). For sphere generators, this is the maximum elevation of the initial position; 0 makes the initial position entirely in the x-y plane (z=0).
        M2Track << float32 | 'horizontal_range',                                    # They can do it horizontally too! (range: 0 to 2*pi) For plane generators, this is the maximum azimuth angle of the initial velocity;
                                                                                    # 0 makes the velocity have no sideways (y-axis) component.  For sphere generators, this is the maximum azimuth angle of the initial position.

        M2Track << float32 | 'gravity',                                             # Not necessarily a float; see below.
        M2Track << float32 | 'lifespan',

        if_(VERSION >= M2Versions.WOTLK),
            float32 | 'lifespan_vary',                                              # An individual particle's lifespan is added to by lifespanVary * random(-1, 1)
        endif_,

        M2Track << float32 | 'emission_rate',

        if_(VERSION >= M2Versions.WOTLK),
            float32 | 'emission_rate_vary',                                         # This adds to the base emissionRate value the same way as lifespanVary. The random value is different every update.
        endif_,

        M2Track << float32 | 'emission_area_length',                                # For plane generators, this is the width of the plane in the x-axis. For sphere generators, this is the minimum radius.
        M2Track << float32 | 'emission_area_width',                                 # For plane generators, this is the width of the plane in the y-axis. For sphere generators, this is the maximum radius.
        M2Track << float32 | 'z_source',                                            # When greater than 0, the initial velocity of the particle is (particle.position - C3Vector(0, 0, zSource)).Normalize()

        if_(VERSION >= M2Versions.WOTLK),
            FBlock << C3Vector | 'color_track',                                     # Most likely they all have 3 timestamps for {start, middle, end}.
            FBlock << fixed16 | 'alpha_track',
            FBlock << C2Vector | 'scale_track',
            C2Vector | 'scale_vary',                                                # A percentage amount to randomly vary the scale of each particle
            FBlock << uint16 | 'head_cell_track',                                   # Some kind of intensity values seen: 0,16,17,32 (if set to different it will have high intensity)
            FBlock << uint16 | 'tail_cell_track',
        else_,
            float32 | 'mid_point',                                                  # Middle point in lifespan (0 to 1).
            array[3] << CImVector | 'color_values',
            array[4] << float32 | 'scale_values',
            array[2] << uint16 | 'head_cell_begin',
            uint16 | ('between1', 1),
            array[2] << uint16 | 'head_cell_end',
            uint16 | ('between2', 1),
            array[4] << int16 | 'tiles',                                            # Indices into the tiles on the texture ? Or tailCell maybe ?
        endif_,

        float32 | 'tail_length',                                                    # TailCellTime?
        float32 | 'twinkle_speed',                                                  # has something to do with the spread
        float32 | 'twinkle_percent',                                                # has something to do with the spread
        CRange | 'twinkle_scale',
        float32 | 'burst_multiplier',                                               # ivelScale
        float32 | 'drag',                                                           # For a non-zero values, instead of travelling linearly the particles seem to slow down sooner. Speed is multiplied by exp( -drag * t ).

        if_(VERSION >= M2Versions.WOTLK),
            float32 | 'basespin',                                                   # Initial rotation of the particle quad
            float32 | 'base_spin_vary',
            float32 | 'spin',                                                       # Rotation of the particle quad per second
            float32 | 'spin_vary',
        else_,
            float32 | 'spin',                                                       # 0.0 for none, 1.0 to rotate the particle 360 degrees throughout its lifetime.
        endif_,

        M2Box | 'tumble',
        C3Vector | 'wind_vector',
        float32 | 'wind_time',

        float32 | 'follow_speed1',
        float32 | 'follow_scale1',
        float32 | 'follow_speed2',
        float32 | 'follow_scale2',
        M2Array << C3Vector | 'spline_points',                                      # Set only for spline praticle emitter. Contains array of points for spline
        M2Track << uint8 | 'enabled_in',                                            # (boolean) Appears to be used sparely now, probably there's a flag that links particles to animation sets where they are enabled.

        if_(VERSION >= M2Versions.CATA),
            array[2] << Vector_2fp_6_9 | 'multi_texture_param0',
            array[2] << Vector_2fp_6_9 | 'multi_texture_param1',
        endif_
    )


class M2ParticleFlags(IntEnum):
    EffectedByLight = 0x1               # Particles are affected by lighting;
    UseWorldMatrix = 0x8                # Particles travel "up" in world space, rather than model.
    DoNotTrail = 0x10                   # Do not Trail
    Unlightning = 0x20                  # Unlightning
    UseModelMatrix = 0x80               # Particles in Model Space
    SpawnPosRandom = 0x200              # spawn position randomized in some way?
    PinParticle = 0x400                 # Pinned Particles, their quad enlarges from their creation position to where they expand.
    XYQuad = 0x1000                     # XYQuad Particles. They align to XY axis facing Z axis direction.
    ClampToGround = 0x2000              # clamp to ground
    ChooseRandomTexture = 0x10000       # ChooseRandomTexture
    OutwardParticle = 0x20000           # "Outward" particles, most emitters have this and their particles move away from the origin, when they don't the particles start at origin+(speed*life) and move towards the origin.
    Unknown = 0x40000                   # unknown. In a large proportion of particles this seems to be simply the opposite of the above flag, but in some (e.g. voidgod.m2 or wingedlionmount.m2) both flags are true.
    ScaleVaryXY = 0x80000               # If set, ScaleVary affects x and y independently; if not set, ScaleVary.x affects x and y uniformly, and ScaleVary.y is not used.
    RandFlipBookStart = 0x200000        # Random FlipBookStart
    IgnoreDistance = 0x400000           # Ignores Distance (or 0x4000000?!, CMapObjDef::SetDoodadEmittersIgnoresDistance has this one)
    CompressGravity = 0x800000          # gravity values are compressed vectors instead of z-axis values (see Compressed Particle Gravity below)
    BoneGenerator = 0x1000000           # bone generator = bone, not joint
    DoNotThrottleEmission = 0x4000000   # do not throttle emission rate based on distance
    UseMultiTexturing = 0x10000000      # Particle uses multi-texturing (could be one of the other WoD-specific flags), see multi-textured section.


#############################################################
######                  Miscellaneous                  ######
#############################################################

###### Lights ######

class M2Light(Struct):
    __fields__ = (
        uint16 | ('type', 1),                             # Types are listed below.
        int16 | 'bone',                                   # -1 if not attached to a bone
        C3Vector | 'position',                            # relative to bone, if given
        M2Track << C3Vector | 'ambient_color',
        M2Track << float32 | 'ambient_intensity',         # defaults to 1.0
        M2Track << C3Vector | 'diffuse_color',
        M2Track << float32 | 'diffuse_intensity',
        M2Track << float32 | 'attenuation_start',
        M2Track << float32 | 'attenuation_end',
        M2Track << uint8 | 'visibility'                   # enabled?
    )


class M2LightTypes:
    Directional = 0     # Directional light type is not used (at least in 3.3.5) outside login screen, and doesn't seem to be taken into account in world.
    Point = 1


###### Cameras ######

class M2Camera(Struct):
    __fields__ = (
        uint32 | 'type',                                            # 0: portrait, 1: characterinfo; -1: else (flyby etc.); referenced backwards in the lookup table.
        if_(VERSION < M2Versions.CATA),
            float32 | 'fov',                                        # Diagonal FOV in radians. See below for conversion.
        endif_,
        float32 | 'far_clip',
        float32 | 'near_clip',
        M2Track << (M2SplineKey << C3Vector) | 'positions',         # positions; // How the camera's position moves. Should be 3*3 floats.
        C3Vector | 'position_base',
        M2Track << (M2SplineKey << C3Vector) | 'target_position',   # How the target moves. Should be 3*3 floats.
        C3Vector | 'target_position_base',
        M2Track << (M2SplineKey << float32) | 'roll',               # The camera can have some roll-effect. Its 0 to 2*Pi.
        if_(VERSION >= M2Versions.CATA),
            M2Track << (M2SplineKey << float32) | 'fov',            # Diagonal FOV in radians. float vfov = dfov / sqrt(1.0 + pow(aspect, 2.0));
        endif_,
    )


###### Attachments ######

class M2Attachment(Struct):
    __fields__ = (
        uint32 | 'id',                              # Referenced in the lookup-block below.
        uint16 | 'bone',                            # attachment base
        uint16 | 'unknown',                         # see BogBeast.m2 in vanilla for a model having values here
        C3Vector | 'position',                      # relative to bone; Often this value is the same as bone's pivot point
        M2Track << boolean | 'animate_attached'     # whether or not the attached model is animated when this model is. only a bool is used. default is true.
    )


###### Events ######

class M2Event(Struct):
    __fields__ = (
        uint32 | 'identifier',
        uint32 | 'data',
        uint32 | 'bone',
        C3Vector | 'position',
        M2TrackBase | 'enabled'
    )


#############################################################
######                  M2 Header                      ######
#############################################################


class M2Header(Struct):
    __fields__ = (
        string_t[4] | ('magic', 'MD20' if VERSION < M2Versions.LEGION else 'MD21'),
        uint32 | ('version', VERSION),
        M2Array << char | 'name',
        uint32 | 'global_flags',
        M2Array << uint32 | 'global_loops',
        M2Array << M2Sequence | 'sequences',
        M2Array << uint16 | 'sequence_lookups',

        if_(VERSION <= M2Versions.TBC),
            M2Array << uint32 | 'playable_animation_lookup',                                # type is unk
        endif_,

        M2Array << M2CompBone | 'bones',                                                    # 0x100 bones max

        M2Array << uint16 | 'key_bone_lookup',
        M2Array << M2Vertex | 'vertices',

        if_(VERSION <= M2Versions.TBC),
            M2Array << uint32 | 'skin_profiles',                                            # SkinProfile
        else_,
            uint32 | 'num_skin_profiles',
        endif_,

        M2Array << M2Color | 'colors',                                                      # Color and alpha animations definitions.
        M2Array << M2Texture | 'textures',
        M2Array << M2TextureWeight | 'texture_weights',                                     # Transparency of textures.

        if_(VERSION <= M2Versions.TBC),
            M2Array << uint16 | 'unknown',                                                  # type is unk
        endif_,

        M2Array << M2TextureTransform | 'texture_transforms',
        M2Array << uint16 | 'replacable_texture_lookup',
        M2Array << M2Material | 'materials',                                                # Blending modes / render flags.
        M2Array << uint16 | 'bone_lookup_table',
        M2Array << uint16 | 'texture_lookup_table',
        M2Array << uint16 | 'tex_unit_lookup_table',                                        # ≥ Cata: unused
        M2Array << uint16 | 'transparency_lookup_table',
        M2Array << uint16 | 'texture_transforms_lookup_table',



        CAaBox | 'bounding_box',                                                            # min/max( [1].z, 2.0277779f ) - 0.16f seems to be the maximum camera height
        float32 | 'bounding_sphere_radius',
                                                                                            # detail doodad draw dist = clamp (bounding_sphere_radius * detailDoodadDensityFade * detailDoodadDist, …)
        CAaBox | 'collision_box',
        float32 | 'collision_sphere_radius',

        M2Array << uint16 | 'collision_triangles',
        M2Array << C3Vector | 'collision_vertices',
        M2Array << C3Vector | 'collision_normals',
        M2Array << M2Attachment | 'attachments',                                            # position of equipped weapons or effects

        M2Array << uint16 | 'attachment_lookup_table',
        M2Array << M2Event | 'events',                                                      # Used for playing sounds when dying and a lot else.
        M2Array << M2Light | 'lights',                                                      # Lights are mainly used in loginscreens but in wands and some doodads too.
        M2Array << M2Camera | 'cameras',

                                                                                            # The cameras are present in most models for having a model in the character tab.
        M2Array << uint16 | 'camera_lookup_table',
        M2Array << M2Ribbon | 'ribbon_emitters',                                            # Things swirling around. See the CoT-entrance for light-trails.

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


class M2GlobalFlags(IntEnum):
    TILT_X = 0x1
    TILT_Y = 0x2
    UseTextureCombiner_Combos = 0x8
    LoadPhysData = 0x20
    UNK = 0x80
    CameraRelated = 0x100




