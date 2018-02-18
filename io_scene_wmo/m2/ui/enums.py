import bpy
from ...pywowlib.enums.m2_enums import M2SkinMeshPartID, M2KeyBones, M2AttachmentTypes
from ...utils import load_game_data
from ... import ui_icons


###############################
## Enumerated constants
###############################

SHADERS = [
    ('0', "Diffuse", ""), ('1', "Specular", ""), ('2', "Metal", ""),
    ('3', "Env", ""), ('4', "Opaque", ""), ('5', "EnvMetal", ""),
    ('6', "TwoLayerDiffuse", ""), ('7', "TwoLayerEnvMetal", ""), ('8', "TwoLayerTerrain", ""),
    ('9', "DiffuseEmissive", ""), ('10', "Tangent", ""), ('11', "MaskedEnvMetal", ""),
    ('12', "EnvMetalEmissive", ""), ('13', "TwoLayerDiffuseOpaque", ""), ('14', "TwoLayerDiffuseEmissive", "")
]

TEX_UNIT_FLAGS = [
    ("1", "Invert", "", 'MOD_DATA_TRANSFER', 0x1),
    ("2", "Transform", "", 'SCULPTMODE_HLT', 0x2),
    ("4", "Projected Texture", "", 'MOD_UVPROJECT', 0x4),
    ("8", "Unknown", "", 'QUESTION', 0x8),
    ("16", "Batch Compatible", "", 'SETTINGS', 0x10),
    ("32", "Projected Texture 2", "", 'MOD_UVPROJECT', 0x20),
    ("64", "Use Texture Weights", "", 'WPAINT_HLT', 0x40)
]

RENDER_FLAGS = [
    ("1", "Unlit", "Disable lighting", 'SNAP_VOLUME', 0x1),
    ("2", "Unfogged", "Disable fog", ui_icons['MAT_UNFOGGED'], 0x2),
    ("4", "Two-sided", "Render from both sides", 'MOD_UVPROJECT', 0x4),
    ("8", "Depth-Test", "Unknown", 'SPACE3', 0x8),
    ("16", "Depth-Write", "Unknown", 'SPACE2', 0x10)
]

BLENDING_MODES = [
    ("0", "Opaque", "Blending disabled", 'MESH_CUBE', 1),
    ("1", "AlphaTesting", "All pixels are fully opaque or transparent, leading to aliasing (“jaggies”)", 'MOD_BEVEL', 2),
    ("2", "AlphaBlending", "All pixels can support full transparency range. Sometimes thus can produce some rendering issues", 'MOD_CAST', 3),
    ("3", "Add", "Takes the pixels of the Material and adds them to the pixels of the background. This means that there is no darkening; since all pixel values are added together, blacks will just render as transparent", 'FORCE_TEXTURE', 4),
    ("4", "AddAlpha", "This Blend Mode works by taking in an Opacity value or texture and applying it to the surface such that black areas are completely transparent, white areas are completely opaque, and the varying shades of gradation between result in corresponding transparency levels", 'TPAINT_HLT', 5),
    ("5", "Modulate", "The Modulate Blend Mode simply multiplies the value of the Material against the pixels of the background", 'FACESEL', 6),
    ("6", "DeeeprunTram", "Probably is used in particles. Needs to be researched", 'MOD_PARTICLES', 7)
]

TEXTURE_TYPES = [
    ("0", "None", "Texture given in filename", 'PMARKER', 1),
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
    ("18", "Guild Emblem", "", 'PMARKER', 19)

]

TEXTURE_FLAGS = [
    ("1", "Wrap X", "Texture wrap X", 'TRIA_RIGHT', 0x1),
    ("2", "Wrap Y", "Texture wrap Y", 'TRIA_UP', 0x2),
]

BONE_FLAGS = [
    ("4", "Unknown", "", 'PMARKER', 0x4),
    ("8", "Spherical Billboard", "", 'PMARKER', 0x8),
    ("16", "Cylindrical Billboard Lock X", "", 'PMARKER', 0x10),
    ("32", "Cylindrical Billboard Lock Y", "", 'PMARKER', 0x20),
    ("64", "Cylindrical Billboard Lock Z", "", 'PMARKER', 0x40),
    ("512", "Transformed", "", 'PMARKER', 0x200),
    ("1024", "Kinematic Bone", "", 'PMARKER', 0x400),
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
    ("Hands", "BE Hands", "Hands for Blood Elf / Night Elf (Legion+)", 'PMARKER', 23)
]

ANIMATION_FLAGS = [
    ("1", "Init Blend", "Sets Blended flag on M2 init", 'PMARKER', 0x1),
    ("2", "Unknown", "", 'QUESTION', 0x2),
    ("4", "Unknown", "", 'QUESTION', 0x4),
    ("8", "Unknown", "", 'QUESTION', 0x8),
    ("16", "Unknown", "apparently set during runtime in CM2Shared::LoadLowPrioritySequence for all entries of a loaded sequence (including aliases)", 'QUESTION', 0x10),
    ("32", "Primary Sequence", " If set, the animation data is in the .m2 file, else in an .anim file", 'MOD_WIREFRAME', 0x20),
    ("64", "Is Alias", "To find the animation data, the client skips these by following aliasNext until an animation without 0x40 is found.", 'TRIA_RIGHT', 0x40),
    ("128", "Blended animation", "", 'TRIA_RIGHT', 0x80),
    ("256", "Unknown", "Sequence stored in model?", 'QUESTION', 0x100),
    ("512", "Unknown", "", 'QUESTION', 0x200),
    ("512", "Unknown", "", 'QUESTION', 0x400),
    ("512", "Unknown", "Seen in Legion 24500 models", 'QUESTION', 0x800)
]


def generate_enumerated_list(irange, name):
    return list([(str(i), "{}_{}".format(name, i), "") for i in irange])


def mesh_part_id_menu(self, context):

    geoset_group = self.MeshPartGroup
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
                ("803", "Ruffled", "Ruffled wristbands")]

    elif geoset_group == 'Kneepads':
        return [("901", "None (DNE)", "No kneepads"),
                ("902", "Long", "Long kneepads"),
                ("903", "Short", "Short kneepads")]

    elif geoset_group == 'Chest':
        return [("1001", "None (DNE)", "No chest"),
                ("1002", "Plate", "Downside of a plate chest")]

    elif geoset_group == 'Pants':
        return [("1101", "Regular", "Regular pants"),
                ("1102", "Skirt", "Short skirt"),
                ("1104", "Armored", "Armored pants")]

    elif geoset_group == 'Tabard':
        return [("1201", "None (DNE)", "No tabard"),
                ("1202", "Tabard", "Tabard")]

    elif geoset_group == 'Legs':
        return [("1301", "Trousers", ""),
               ("1302", "Dress", "")]

    elif geoset_group == 'Cloak':
        return [("1501", "Scarf", "Shortest cloak"),
                ("1502", "Knight", "Usually the longest cloak"),
                ("1503", "Normal", ""),
                ("1504", "Double-tail", ""),
                ("1505", "Small", ""),
                ("1506", "Small double-tail", "")]

    elif geoset_group == 'Eyeglows':
        return [("1701", "None (DNE)", "No eyeglow"),
                ("1702", "Racial", "Racial eyeglow"),
                ("1703", "DK", "Death Knight eyeglow")]

    elif geoset_group == 'Belt':
        return [("1801", "None (DNE)", "No belt / bellypack"),
                ("1802", "Bulky", "Bulky belt")]

    elif geoset_group == 'Feet':
        return [("2001", "None (DNE)", "No feet"),
                ("2002", "Feet", "Feet")]

    elif geoset_group == 'Hands':
        return [("2301", "BE / NE Hands", 'Hands for Blood Elf / Night Elf')]

    else:
        return [('0', 'No subtype', "")]


def get_keybone_ids(self, context):
    keybone_ids = [('-1', 'Not a keybone', '')]
    keybone_ids.extend([(str(field.value), field.name, '') for field in M2KeyBones])

    return keybone_ids


def get_anim_ids(self, context):
    load_game_data()
    return [(str(record.ID), record.Name, '') for record in bpy.db_files_client.AnimationData.records]


def get_attachment_types(self, context):
    return [(str(field.value), field.name, "") for field in M2AttachmentTypes]



