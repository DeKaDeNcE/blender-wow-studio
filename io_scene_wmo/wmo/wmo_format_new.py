from ..binary_parser.binary_types import *
from ..m2_new.wow_common_types import *


class MVER(Struct):
    _fields_ = (
            string_t(4) | 'magic',
            uint32 | 'size',
            uint32 | 'version',
    )

"""
WMO Root File
"""

class MOHD(Struct):
    """WMO root file header"""
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
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


class MOTX(Struct):
    """List of all texture files used in a WMO"""
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        StringTable | 'string_table'
    )


class WMOMaterial(Struct):
    """WMO Material structure"""
    _fields_ = (
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


class MOUV(Struct):
    """Map Object UV Legion+"""
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        array[template_T['len']] << C2Vector | 'translation_speed',
    )


class MOGN(Struct):
    """Names of all referenced WMO groups"""
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        StringBlock | 'group_names',
    )


class WMOGroupInfo(Struct):
    """WMO Group Info Structure"""
    _fields_ = (
        uint32 | 'offset',
        uint32 | 'size',
        uint32 | 'flags',
        CAaBox | 'bounding_box',
        int32 | 'name_offset'
    )

class MOGI(Struct):
    """List of all group infos"""
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        array[template_T['n_groups']] << WMOGroupInfo | 'group_infos',
    )


class MOSB(Struct):
    """Path to a skybox .M2 model (optional)"""
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        string_t | 'skybox_filename',
    )

class MOPV(Struct):
    """List of all portal vertices positions"""
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        array[template_T['n_portal_vertices']] << C3Vector | 'portal_vertices',
    )

class WMOPortal(Struct):
    """WMO Portal structure"""
    _fields_ = (
        uint16 | 'start_vertex',
        uint16 | 'count',
        C4Plane | 'plane'
    )

class MOPT(Struct):
    """List of all portal structures"""
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[this_size('size')] << WMOPortal | 'portals',
    )

class WMOPortalRelation(Struct):
    """WMO Portal Relation structure"""
    _fields_ = (
        uint16 | 'portal_index',
        uint16 | 'group_index',
        int16 | 'side',
        uint16 | 'padding'
    )

class MOPR(Struct):
    """List of all WMO Portal Relation structures"""
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[this_size('size')] << WMOPortalRelation | 'portal_relations',
    )

class MOVV(Struct):
    """List of visible block vertices locations"""
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[this_size('size')] << C3Vector | 'visible_block_vertices',
    )

class VisibleBlock(Struct):
    """Visible block structure"""
    _fields_ = (
        uint16 | 'first_vertex',
        uint16 | 'count'
    )

class MOVB(Struct):
    """List of all visible blocks"""
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[this_size('size')] << VisibleBlock | 'visible_blocks'
    )

class WMOLight(Struct):
    """WMO Light structure"""
    _fields_ = (
        uint8 | 'type',
        uint8 | 'use_attenuation',
        uint16 | 'padding',
        CImVector | 'color',
        C3Vector | 'position',
        float32 | 'intensity',
        float32 | 'attenuation_start',
        float32 | 'attenuation_end',
        array[4] << float32 | 'unk'
    )

class MOLT(Struct):
    """List of all WMO Light structures"""
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[this_size('size')] << WMOLight | 'lights',
    )

class WMODoodadSet(Struct):
    """WMO Doodad Set structure"""
    _fields_ = (
        string_t | 'name',  # TODO: implement len for strings
        uint32 | 'start_index',
        uint32 | 'count',
        uint32 | 'padding'
    )

class MODS(Struct):
    """List of all WMO Doodad Set structures"""
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[this_size('size')] << WMODoodadSet | 'doodad_sets'
    )

class MODN(Struct):
    """List of all doodad names (paths)"""
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        StringBlock | 'doodad_names',
    )

class WMODoodadDefinition(Struct):
    """WMO Doodad Definition structure"""
    _fields_ = (
        uint32 | 'flags',
        C3Vector | 'position',
        C4Quaternion | 'orientation',
        float32 | 'scale',
        CImVector | 'color'
    )

class MODD(Struct):
    """List of all doodad definitions"""
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[this_size('size')] << WMODoodadDefinition | 'doodad_definitions',
    )

class WMOFog(Struct):
    """WMO Fog structure"""
    _fields_ = (
        uint32 | 'flags',
        C3Vector | 'pos',
        float32 | 'smaller_radius',
        float32 | 'larger_radius',
        float32 | 'end',
        float32 | 'start_scalar',
        CImVector | 'color'
    )

class MFOG(Struct):
    """List of all WMO fogs"""
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[this_size('size')] << WMOFog | 'fogs',
    )

class MCVP(Struct):
    """List of convex volume planes (used for transport objects)"""
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[this_size('size')] << C4Plane | 'convex_volume_planes',
    )

class GFID(Struct):
    """Required when WMO is loaded from fileID (Legion+)"""
    _fields_ = (
        #TODO: get back here
    )


"""
WMO Group File
"""

class MOGP(Struct):
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        uint32 | 'group_name',
        uint32 | 'descriptive_group_name',
        uint32 | 'flags',
        CAaBox | 'bounding_box',
        uint16 | 'portal_start',
        uint16 | 'portal_count',
        uint16 | 'trans_batch_count',
        uint16 | 'int_batch_count',
        uint16 | 'ext_batch_count',
        uint16 | 'padding',
        array[4] << uint8 | 'fog_ids',
        uint32 | 'group_liquid',
        uint32 | 'unique_id',
        uint32 | 'flags2',
        uint32 | 'unk'
    )

class TriangleMaterial(Struct):
    _fields_ = (
        uint8 | 'flags',
        uint8 | 'material_id'
    )

    # TODO: implement poll methods here

class MOPY(Struct):
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[template_T['n_triangles']] << TriangleMaterial | 'polygons',
    )

class MOVI(Struct):
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[this_size['size']] << uint16 | 'triangle_vertex_indices',
    )

class MOVT(Struct):
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[this_size['size']] << C3Vector | 'vertex_coordinates',
    )

class MONR(Struct):
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[this_size['size']] << C3Vector | 'normals',
    )

class MOTV(Struct):
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[this_size['size']] << C2Vector | 'texture_coordinates',
    )

class RenderBatch(Struct):
    _fields_ = (
        if_(VERSION < Versions.Legion),
        array[6] << int16 | 'bounding_box',
        else_,
        array[10] << uint8 | 'unk',
        uint16 | 'material_id_large',
        endif_,

        uint32 | 'start_index',
        uint16 | 'count',
        uint16 | 'min_index',
        uint16 | 'max_index',
        uint8 | 'flag' if VERSION < Versions.Legion else 'use_material_id_large',
        uint8 | 'material_id',
    )

class MOBA(Struct):
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[this_size('size')] << RenderBatch | 'batches',
    )

class MOLR(Struct):
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[this_size('size')] << uint16 | 'light_references',

    )

class MODR(Struct):
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[this_size('size')] << uint16 | 'doodad_references',

    )

class BSPNode(Struct):
    _fields_ = (
        uint16 | 'flags',
        int16 | 'neg_child',
        int16 | 'pos_child',
        uint16 | 'n_faces',
        uint32 | 'face_start',
        float32 | 'plane_dist'
    )

class MOBN(Struct):
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[this_size('size')] << BSPNode | 'bsp_nodes',

    )


class MOBR(Struct):
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[this_size('size')] << uint16 | 'node_face_indices',

    )


class MOCV(Struct):
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[this_size('size')] << CImVector | 'color_vertices',

    )

class WMOWaterVert(Struct):
    _fields_ = (
        uint8 | 'flow1',
        uint8 | 'flow2',
        uint8 | 'flow1Pct',
        uint8 | 'filler',
        float32 | 'height'
    )

class WMOMagmaVert(Struct):
    _fields_ = (
        int16 | 'u',
        int16 | 'v',
        float32 | 'height'
    )

class MLIQ(Struct):
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        uint32 | 'n_x_vertices',
        uint32 | 'n_y_vertices',
        uint32 | 'n_x_tiles',
        uint32 | 'n_y_tiles',
        array[3] << float32 | 'base_coordinates',
        uint16 | 'material_id',
        dynamic_array['n_x_vertices']['n_y_vertices'] << template_T['vertex_type'],
        dynamic_array['n_x_tiles']['n_y_tiles'] << uint8 | 'tile_flags'

    )

class MORI(Struct):
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[this_size('size')] << uint16 | 'triangle_strip_indices',
    )

class MORB(Struct):
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        uint32 | 'start_index',
        uint16 | 'index_count',
        uint16 | 'padding'
    )

class MOBS(Struct):
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[this_size('size')][24] << char | 'unk',
    )

# WoD+
class MDAL(Struct):
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        CArgb | 'replacement_for_header_color',
    )

# WoD+
class MOPL(Struct):
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[this_size('size')] << C4Plane | 'terrain_cutting_planes',
    )

#Legion+
class MOLS(Struct):
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[this_size('size')][56] << char | 'unk',
    )

#Legion+
class WMOPointLight(Struct):
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        uint32 | 'unk',
        CImVector | 'color',
        C3Vector | 'pos',
        float32 | 'intensity',
        float32 | 'attenuation_start',
        float32 | 'attenuation_end',
        float32 | 'unk1',
        uint32 | 'unk2',
        uint32 | 'unk3'
    )

class MOLP(Struct):
    _fields_ = (
        string_t(4) | 'magic',
        uint32 | 'size',
        dynamic_array[this_size('size')] << WMOPointLight | 'point_lights',
    )












