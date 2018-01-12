from ..binary_parser.binary_types import *
from ..m2_new.wow_common_types import *

class Chunk(Struct):
    __fields__ = ()
    #TODO: get back here


class MVER_chunk(Chunk):
    __fields__ = (
            uint32 | 'version'
    )

class MOHD_chunk(Chunk):
    __fields__ = (
        uint32 | 'n_materials',
        uint32 | 'n_groups',
        uint32 | 'n_portals',
        uint32 | 'n_lights',
        uint32 | 'n_models',
        uint32 | 'n_doodads',
        uint32 | 'n_sets',
        BGRA | 'ambient_color',
        uint32 | 'id',
        C3Vector << float32 | 'bounding_box_corner_1',
        C3Vector << float32 | 'bounding_box_corner_2',
        uint32 | 'flags'
    )

class MOTX_chunk(Chunk):
    __fields__ = (
        StringTable | 'string_table'
    )

class WMO_Material(Struct):
    __fields__ = (
        uint32 | 'flags',
        uint32 | 'shader',
        uint32 | 'blend_mode',
        uint32 | 'texture1_ofs',
        BGRA | 'emissive_color',
        BGRA | 'sidn_emissive_color',
        uint32 | 'texture2_ofs',
        BGRA | 'diff_color',
        uint32 | 'terrain_type',
        uint32 | 'texture3_ofs',
        BGRA | 'color_3',
        uint32 | 'tex_3_flags',
    )