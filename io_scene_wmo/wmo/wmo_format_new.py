from ..binary_parser.binary_types import *
from ..m2_new.wow_common_types import *

class Chunk(Struct):
    __fields__ = ()
    #TODO: get back here


class MVER_chunk(Chunk):
    __fields__ = (
        uint32_t | 'version'
    )

class MOHD_chunk(Chunk):
    __fields__ = (
        uint32_t | 'n_materials',
        uint32_t | 'n_groups',
        uint32_t | 'n_portals',
        uint32_t | 'n_lights',
        uint32_t | 'n_models',
        uint32_t | 'n_doodads',
        uint32_t | 'n_sets',
        BGRA | 'ambient_color',
        uint32_t | 'id',
        C3Vector << float32_t | 'bounding_box_corner_1',
        C3Vector << float32_t | 'bounding_box_corner_2',
        uint32_t | 'flags'
    )

class MOTX_chunk(Chunk):
    __fields__ = (
        StringTable | 'string_table'
    )

class WMO_Material(Struct):
    __fields__ = (
        uint32_t | 'flags',
        uint32_t | 'shader',
        uint32_t | 'blend_mode',
        uint32_t | 'texture1_ofs',
        BGRA | 'emissive_color',
        BGRA | 'sidn_emissive_color',
        uint32_t | 'texture2_ofs',
        BGRA | 'diff_color',
        uint32_t | 'terrain_type',
        uint32_t | 'texture3_ofs',
        BGRA | 'color_3',
        uint32_t | 'tex_3_flags',
    )