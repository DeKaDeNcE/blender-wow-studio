from ...utils.misc import load_game_data
from ... import ui_icons
from ...pywowlib.enums.m2_enums import *

__reload_order_index__ = -1

###############################
## Enumerated constants
###############################

VERTEX_SHADERS = [
    ("0", "Diffuse_T1", ""),
    ("1", "Diffuse_Env", ""),
    ("2", "Diffuse_T1_T2", ""),
    ("3", "Diffuse_T1_Env", ""),
    ("4", "Diffuse_Env_T1", ""),
    ("5", "Diffuse_Env_Env", ""),
    ("6", "Diffuse_T1_Env_T1", ""),
    ("7", "Diffuse_T1_T1", ""),
    ("8", "Diffuse_T1_T1_T1", ""),
    ("9", "Diffuse_EdgeFade_T1", ""),
    ("10", "Diffuse_T2", ""),
    ("11", "Diffuse_T1_Env_T2", ""),
    ("12", "Diffuse_EdgeFade_T1_T2", ""),
    ("13", "Diffuse_EdgeFade_Env", ""),
    ("14", "Diffuse_T1_T2_T1", ""),
    ("15", "Diffuse_T1_T2_T3", ""),
    ("16", "Color_T1_T2_T3", ""),
    ("17", "BW_Diffuse_T1", ""),
    ("18", "BW_Diffuse_T1_T2", "")
]


FRAGMENT_SHADERS = [
    ("0", "Combiners_Opaque", ""),
    ("1", "Combiners_Mod", ""),
    ("2", "Combiners_Opaque_Mod", ""),
    ("3", "Combiners_Opaque_Mod2x", ""),
    ("4", "Combiners_Opaque_Mod2xNA", ""),
    ("5", "Combiners_Opaque_Opaque", ""),
    ("6", "Combiners_Mod_Mod", ""),
    ("7", "Combiners_Mod_Mod2x", ""),
    ("8", "Combiners_Mod_Add", ""),
    ("9", "Combiners_Mod_Mod2xNA", ""),
    ("10", "Combiners_Mod_AddNA", ""),
    ("11", "Combiners_Mod_Opaque", ""),
    ("12", "Combiners_Opaque_Mod2xNA_Alpha", ""),
    ("13", "Combiners_Opaque_AddAlpha", ""),
    ("14", "Combiners_Opaque_AddAlpha_Alpha", ""),
    ("15", "Combiners_Opaque_Mod2xNA_Alpha_Add", ""),
    ("16", "Combiners_Mod_AddAlpha", ""),
    ("17", "Combiners_Mod_AddAlpha_Alpha", ""),
    ("18", "Combiners_Opaque_Alpha_Alpha", ""),
    ("19", "Combiners_Opaque_Mod2xNA_Alpha_3s", ""),
    ("20", "Combiners_Opaque_AddAlpha_Wgt", ""),
    ("21", "Combiners_Mod_Add_Alpha", ""),
    ("22", "Combiners_Opaque_ModNA_Alpha", ""),
    ("23", "Combiners_Mod_AddAlpha_Wgt", ""),
    ("24", "Combiners_Opaque_Mod_Add_Wgt", ""),
    ("25", "Combiners_Opaque_Mod2xNA_Alpha_UnshAlpha", ""),
    ("26", "Combiners_Mod_Dual_Crossfade", ""),
    ("27", "Combiners_Opaque_Mod2xNA_Alpha_Alpha", ""),
    ("28", "Combiners_Mod_Masked_Dual_Crossfade", ""),
    ("29", "Combiners_Opaque_Alpha", ""),
    ("30", "Guild", ""),
    ("31", "Guild_NoBorder", ""),
    ("32", "Guild_Opaque", ""),
    ("33", "Combiners_Mod_Depth", ""),
    ("34", "Illum", ""),
    ("35", "Combiners_Mod_Mod_Mod_Const", "")
]


SHADERS = [
    ('0', 'Combiners_Opaque_Mod2xNA_Alpha_Diffuse_T1_Env', ''),
    ('1', 'Combiners_Opaque_AddAlpha_Diffuse_T1_Env', ''),
    ('2', 'Combiners_Opaque_AddAlpha_Alpha_Diffuse_T1_Env', ''),
    ('3', 'Combiners_Opaque_Mod2xNA_Alpha_Add_Diffuse_T1_Env_T1', ''),
    ('4', 'Combiners_Mod_AddAlpha_Diffuse_T1_Env', ''),
    ('5', 'Combiners_Opaque_AddAlpha_Diffuse_T1_T1', ''),
    ('6', 'Combiners_Mod_AddAlpha_Diffuse_T1_T1', ''),
    ('7', 'Combiners_Mod_AddAlpha_Alpha_Diffuse_T1_Env', ''),
    ('8', 'Combiners_Opaque_Alpha_Alpha_Diffuse_T1_Env', ''),
    ('9', 'Combiners_Opaque_Mod2xNA_Alpha_3s_Diffuse_T1_Env_T1', ''),
    ('10', 'Combiners_Opaque_AddAlpha_Wgt_Diffuse_T1_T1', ''),
    ('11', 'Combiners_Mod_Add_Alpha_Diffuse_T1_Env', ''),
    ('12', 'Combiners_Opaque_ModNA_Alpha_Diffuse_T1_Env', ''),
    ('13', 'Combiners_Mod_AddAlpha_Wgt_Diffuse_T1_Env', ''),
    ('14', 'Combiners_Mod_AddAlpha_Wgt_Diffuse_T1_T1', ''),
    ('15', 'Combiners_Opaque_AddAlpha_Wgt_Diffuse_T1_T2', ''),
    ('16', 'Combiners_Opaque_Mod_Add_Wgt_Diffuse_T1_Env', ''),
    ('17', 'Combiners_Opaque_Mod2xNA_Alpha_UnshAlpha1', ''),
    ('18', 'Combiners_Mod_Dual_Crossfade_Diffuse_T1', ''),
    ('19', 'Combiners_Mod_Depth_Diffuse_EdgeFade_T1', ''),
    ('20', 'Combiners_Opaque_Mod2xNA_Alpha_Alpha_Diffuse_T1_Env_T2', ''),
    ('21', 'Combiners_Mod_Mod_Diffuse_EdgeFade_T1_T2', ''),
    ('22', 'Combiners_Mod_Masked_Dual_Crossfade_Diffuse_T1_T2', ''),
    ('23', 'Combiners_Opaque_Alpha_Diffuse_T1_T1', ''),
    ('24', 'Combiners_Opaque_Mod2xNA_Alpha_UnshAlpha2', ''),
    ('25', 'Combiners_Mod_Depth_Diffuse_EdgeFade_Env', ''),
    ('26', 'Guild_Diffuse_T1_T2_T1', ''),
    ('27', 'Guild_NoBorder_Diffuse_T1_T2', ''),
    ('28', 'Guild_Opaque_Diffuse_T1_T2_T1', ''),
    ('29', 'Illum_Diffuse_T1_T1', ''),
    ('30', 'Combiners_Mod_Mod_Mod_Const_Diffuse_T1_T2_T3', ''),
    ('31', 'Combiners_Mod_Mod_Mod_Const_Color_T1_T2_T3', ''),
    ('32', 'Combiners_Opaque_Diffuse_T1', ''),
    ('33', 'Combiners_Mod_Mod2x_Diffuse_EdgeFade_T1_T2', ''),
]

TEX_UNIT_FLAGS = [
    ("1", "Invert", "", 'MOD_DATA_TRANSFER', 0x1),
    ("2", "Transform", "", 'SCULPTMODE_HLT', 0x2),
    ("4", "Projected Texture", "", 'MOD_UVPROJECT', 0x4),
    ("8", "Unknown", "", 'QUESTION', 0x8),
    ("16", "Batch Compatible", "", 'SETTINGS', 0x10),
    ("32", "Projected Texture 2", "", 'MOD_UVPROJECT', 0x20),
    ("64", "Use Texture Weights", "", 'WPAINT_HLT', 0x40),
    ("128", "Unknown", "", 'QUESTION', 0x80),
]

RENDER_FLAGS = [
    ("1", "Unlit", "Disable lighting", 'SNAP_VOLUME', 0x1),
    ("2", "Unfogged", "Disable fog", 'MOD_FLUID', 0x2),
    ("4", "Two-sided", "Render from both sides", 'MOD_UVPROJECT', 0x4),
    ("8", "Depth-Test", "Unknown", 'SPACE3', 0x8),
    ("16", "Depth-Write", "Unknown", 'SPACE2', 0x10),
    ("64", "Shadow Batch 1", "seen in WoD", 'QUESTION', 0x40),
    ("128", "Shadow Batch 2", "seen in WoD", 'QUESTION', 0x80),
    ("256", "Unknown", "seen in well_vortex01.m2", 'QUESTION', 0x100),
    ("1024", "Unknown", "see in WoD", 'QUESTION', 0x400),
    ("2048", "Prevent Alpha ", "revent alpha for custom elements. if set, use (fully) opaque or transparent. (litSphere, shadowMonk) (MoP+)", 'SPACE2', 0x800)
]

BLENDING_MODES = [
    ("0", "Opaque", "Blending disabled", 'MESH_CUBE', 1),
    ("1", "AlphaKey", "All pixels are fully opaque or transparent, leading to aliasing (“jaggies”)", 'MOD_BEVEL', 2),
    ("2", "Alpha", "All pixels can support full transparency range. Sometimes thus can produce some rendering issues", 'MOD_CAST', 3),
    ("3", "NoAlphaAdd", "Takes the pixels of the Material and adds them to the pixels of the background. This means that there is no darkening; since all pixel values are added together, blacks will just render as transparent", 'FORCE_TEXTURE', 4),
    ("4", "Add", "This Blend Mode works by taking in an Opacity value or texture and applying it to the surface such that black areas are completely transparent, white areas are completely opaque, and the varying shades of gradation between result in corresponding transparency levels", 'TPAINT_HLT', 5),
    ("5", "Mod", "The Modulate Blend Mode simply multiplies the value of the Material against the pixels of the background", 'FACESEL', 6),
    ("6", "Mod2X", "Probably is used in particles. Needs to be researched", 'MOD_PARTICLES', 7),
    ("7", "BlendAdd", "Probably is used in particles. Needs to be researched", 'MOD_PARTICLES', 8)
]

TEXTURE_TYPES = [
    ("0", "Hardcoded", "Texture given in filename", 'PMARKER', 1),
    ("1", "Skin", "Body and clothes", 'PMARKER', 2),
    ("2", "Object Skin", "Items, Capes", 'PMARKER', 3),
    ("3", "Weapon Blade", "Armor reflect", 'PMARKER', 4),
    ("4", "Weapon Handle", "Weapon Handle", 'PMARKER', 5),
    ("5", "Environment", "Environment (OBSOLETE)", 'PMARKER', 5),
    ("6", "Hair", "Character hair", 'PMARKER', 7),
    ("7", "Facial Hair", "Character facial hair", 'PMARKER', 8),
    ("8", "Skin Extra", "Skin Extra", 'PMARKER', 9),
    ("9", "UI Skin", "UI Skin (inventory models)", 'PMARKER', 10),
    ("10", "Tauren Mane", "Tauren Mane (OBSOLETE)", 'PMARKER', 11),
    ("11", "Monster 1", "Monster Skin 1", 'PMARKER', 12),
    ("12", "Monster 2", "Monster Skin 2", 'PMARKER', 13),
    ("13", "Monster 3", "Monster Skin 3", 'PMARKER', 14),
    ("14", "Item Icon", "Item icon", 'PMARKER', 15),
    ("15", "Guild Background Color", "", 'PMARKER', 16),
    ("16", "Guild Emblem Color", "", 'PMARKER', 17),
    ("17", "Guild Border Color", "", 'PMARKER', 18),
    ("18", "Guild Emblem", "", 'PMARKER', 19),
    ("19", "Eyes", "", 'PMARKER', 20),
    ("20", "Accessory", "", 'PMARKER', 21),
    ("21", "Secondary Skin", "", 'PMARKER', 22),
    ("22", "Secondary Hair", "", 'PMARKER', 23),
    ("23", "Unknown: 23", "", 'PMARKER', 24),
    ("24", "Unknown: 24", "", 'PMARKER', 25)

]

TEXTURE_FLAGS = [
    ("1", "Wrap X", "Texture wrap X", 'TRIA_RIGHT', 0x1),
    ("2", "Wrap Y", "Texture wrap Y", 'TRIA_UP', 0x2)
]

BONE_FLAGS = [
    ("1", "Ignore Parent Translate", "", 'PMARKER', 0x1),
    ("2", "Ignore Parent Scale", "", 'PMARKER', 0x2),
    ("4", "Ignore Parent Rotation", "", 'PMARKER', 0x4),
    ("8", "Spherical Billboard", "", 'PMARKER', 0x8),
    ("16", "Cylindrical Billboard Lock X", "", 'PMARKER', 0x10),
    ("32", "Cylindrical Billboard Lock Y", "", 'PMARKER', 0x20),
    ("64", "Cylindrical Billboard Lock Z", "", 'PMARKER', 0x40),
    ("512", "Transformed", "", 'PMARKER', 0x200),
    ("1024", "Kinematic Bone", "MoP+. Allow physics to influence this bone", 'PMARKER', 0x400),
    ("4096", "Helmet Anim Scaled", "", 'PMARKER', 0x1000),
]

MESH_PART_TYPES = [
    ("Skin", "Skin", "Character body geoset", 'PMARKER', 1),
    ("Hair", "Hair", "Character hair geosets", 'PMARKER', 2),
    ("Facial1", "Facial1", "Usually beard geosets", 'PMARKER', 3),
    ("Facial2", "Facial2", "Usually mustache geosets", 'PMARKER', 4),
    ("Facial3", "Facial3", "Usually sideburns geosets", 'PMARKER', 5),
    ("Glove", "Glove", "Glove geosets", 'PMARKER', 6),
    ("Boots", "Boots", "Boots geosets", 'PMARKER', 7),
    ("Unknown", "Unknown", "", 'PMARKER', 8),
    ("Ears", "Ears", "Ears geosets", 'PMARKER', 9),
    ("Wristbands", "Wristbands", "Wristbands / Sleeves geosets", 'PMARKER', 10),
    ("Kneepads", "Kneepads", "Kneepad geosets", 'PMARKER', 11),
    ("Chest", "Chest", "Chest geosets", 'PMARKER', 12),
    ("Pants", "Pants", "Pants geosets", 'PMARKER', 13),
    ("Tabard", "Tabard", "Tabard geosets", 'PMARKER', 14),
    ("Legs", "Trousers", "Trousers geosets", 'PMARKER', 15),
    ("Unknown2", "Unknown 2", "", 'PMARKER', 16),
    ("Cloak", "Cloak", "Cloak geosets", 'PMARKER', 17),
    ("Unknown3", "Unknown 3", "", 'PMARKER', 18),
    ("Eyeglows", "Eyeglows", "Eyeglows geosets", 'PMARKER', 19),
    ("Belt", "Belt", "Belt / Bellypack geosets", 'PMARKER', 20),
    ("Trail", "Trail", "Trail geosets / Undead bones (Legion+)", 'PMARKER', 21),
    ("Feet", "Feet", "Feet geosets", 'PMARKER', 22),
    ("Hands", "BE Hands", "Hands for Blood Elf / Night Elf (Legion+)", 'PMARKER', 23),
    ("Head", "Head", "", 'PMARKER', 24),
    ("Torso", "Torso", "", 'PMARKER', 25),
    ("Shoulders", "Shoulders", "", 'PMARKER', 26),
    ("Helmet", "Helmet", "", 'PMARKER', 27),
    ("Unknown4", "Unknown4", "", 'PMARKER', 28),
]

ANIMATION_FLAGS = [
    ("1", "Init Blend", "Sets Blended flag on M2 init", 'PMARKER', 0x1),
    ("2", "Unknown", "", 'QUESTION', 0x2),
    ("4", "Unknown", "", 'QUESTION', 0x4),
    ("8", "Unknown", "", 'QUESTION', 0x8),
    ("16", "Unknown", "apparently set during runtime in CM2Shared::LoadLowPrioritySequence for all entries of a loaded sequence (including aliases)", 'QUESTION', 0x10),
    ("32", "Primary Sequence", "If set, the animation data is in the .m2 file, else in an .anim file", 'MOD_WIREFRAME', 0x20),
    ("64", "Is Alias", "To find the animation data, the client skips these by following aliasNext until an animation without 0x40 is found.", 'TRIA_RIGHT', 0x40),
    ("128", "Blended animation", "", 'TRIA_RIGHT', 0x80),
    ("256", "Unknown", "Sequence stored in model?", 'QUESTION', 0x100),
    ("512", "Unknown", "", 'QUESTION', 0x200),
    ("1024", "Unknown", "", 'QUESTION', 0x400),
    ("2048", "Unknown", "Seen in Legion 24500 models", 'QUESTION', 0x800)
]


def generate_enumerated_list(irange, name):
    return list([(str(i), "{}_{}".format(name, i), "") for i in irange])


def mesh_part_id_menu(self, context):

    geoset_group = self.mesh_part_group
    if geoset_group == 'Skin':
        return [('0', 'No subtype', "")]

    elif geoset_group == 'Hair':
        return generate_enumerated_list(M2SkinMeshPartID.Hair.value, 'Hairstyle')

    elif geoset_group == 'Facial1':
        return generate_enumerated_list(M2SkinMeshPartID.Facial1.value, 'Facial')

    elif geoset_group == 'Facial2':
        return generate_enumerated_list(M2SkinMeshPartID.Facial2.value, 'Facial')

    elif geoset_group == 'Facial3':
        return generate_enumerated_list(M2SkinMeshPartID.Facial3.value, 'Facial')

    elif geoset_group == 'Glove':
        return [("401", "Skin", ""),
                ("402", "Regular", ""),
                ("403", "Jackgloves", ""),
                ("404", "Armored", "")]

    elif geoset_group == 'Boots':
        return [("501", "Skin", ""),
                ("502", "Short", ""),
                ("503", "Jackboots", ""),
                ("504", "Regular", ""),
                ("505", "Plate", "")
                ]

    elif geoset_group == 'Ears':
        return [("701", "None (DNE)", "No ears"),
                ("702", "Ears", "Ears geoset")]

    elif geoset_group == 'Wristbands':
        return [("801", "None (DNE)", "No wristbands"),
                ("802", "Normal", "Normal wristbands"),
                ("803", "Ruffled", "Ruffled wristbands"),
                ("804", "Panda Collar Shirt", "")]

    elif geoset_group == 'Kneepads':
        return [("901", "None (DNE)", "No kneepads"),
                ("902", "Long", "Long kneepads"),
                ("903", "Short", "Short kneepads"),
                ("904", "Panda Pants", "")]

    elif geoset_group == 'Chest':
        return [("1001", "None (DNE)", "No chest"),
                ("1002", "Plate", "Downside of a plate chest"),
                ("1003", "Body 2", ""),
                ("1004", "Body 3", "")]

    elif geoset_group == 'Pants':
        return [("1101", "Regular", "Regular pants"),
                ("1102", "Skirt", "Short skirt"),
                ("1104", "Armored", "Armored pants")]

    elif geoset_group == 'Tabard':
        return [("1201", "None (DNE)", "No tabard"),
                ("1202", "Tabard", "Tabard"),
                ("1203", "Tabard Unk", "SL +")]

    elif geoset_group == 'Legs':
        return [("1301", "Trousers", ""),
                ("1302", "Dress", "")]

    elif geoset_group == 'Cloak':
        return [("1501", "Scarf", "Shortest cloak"),
                ("1502", "Knight", "Usually the longest cloak"),
                ("1503", "Normal", ""),
                ("1504", "Double-tail", ""),
                ("1505", "Small", ""),
                ("1506", "Small double-tail", ""),
                ("1507", "Guild cloak", ""),
                ("1508", "Split", "Long"),
                ("1509", "Tapered", "Long"),
                ("1509", "Notched", "Long"),
                ("1510", "Unknown", "SL+")]

    elif geoset_group == 'Eyeglows':
        return [("1701", "None (DNE)", "No eyeglow"),
                ("1702", "Racial", "Racial eyeglow"),
                ("1703", "DK", "Death Knight eyeglow")]

    elif geoset_group == 'Belt':
        return [("1801", "None (DNE)", "No belt / bellypack"),
                ("1802", "Bulky", "Bulky belt"),
                ("1803", "Panda Cord Belt", "")]

    elif geoset_group == 'Feet':
        return [("2001", "Basic shoes", ""),
                ("2002", "Toes", "")]

    elif geoset_group == 'Head':
        return [("2101", "Show head", "")]

    elif geoset_group == 'Torso':
        return [("2201", "Default", ""),
                ("2202", "Covered torso", "")]

    elif geoset_group == 'Hands':
        return [("2301", "BE / NE Hands", 'Hands for Blood Elf / Night Elf')]

    elif geoset_group == 'Shoulders':
        return [("2201", "Show shoulders", "")]

    elif geoset_group == 'Helmet':
        return [("2202", "Helmet", "")]

    else:
        return [('0', 'No subtype', "")]


def get_keybone_ids(self, context):
    keybone_ids = [('-1', 'Not a keybone', '')]
    keybone_ids.extend([(str(field.value), field.name, '') for field in M2KeyBones])

    return keybone_ids


def get_anim_ids(self, context):
    return [(str(seq_id), name, '') for seq_id, name in M2SequenceNames().items()]


def get_attachment_types(self, context):
    return [(str(field.value), field.name, "") for field in M2AttachmentTypes]


def get_particle_flags(self, context):
    return [(str(field.value), field.name, "", hex(field.value)) for field in M2ParticleFlags]


def get_event_names(self, context):
    return [(field.value, field.name, "") for field in M2EventTokens]



