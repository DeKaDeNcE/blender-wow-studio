from ...pywowlib.enums.m2_enums import M2SkinMeshPartID

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
    ("1", "Invert", "", 'PMARKER', 0x1),
    ("2", "Transform", "", 'FORCE_TURBULENCE', 0x2),
    ("4", "Projected Texture", "", 'ARROW_LEFTRIGHT', 0x4),
    ("8", "Unknown", "", 'ARROW_LEFTRIGHT', 0x8),
    ("16", "Batch Compatible", "", 'PMARKER_SEL', 0x10),
    ("32", "Projected Texture 2", "", 'PMARKER_ACT', 0x20),
    ("64", "Use Texture Weights", "", 'PMARKER_ACT', 0x40)
]

RENDER_FLAGS = [
    ("1", "Unlit", "Disable lighting", 'PMARKER', 0x1),
    ("2", "Unfogged", "Disable fog", 'FORCE_TURBULENCE', 0x2),
    ("4", "Two-sided", "Render from both sides", 'ARROW_LEFTRIGHT', 0x4),
    ("8", "Depth-Test", "Unknown", 'PMARKER_SEL', 0x8),
    ("16", "Depth-Write", "Unknown", 'PMARKER_ACT', 0x10)
]

BLENDING_MODES = [
    ("0", "Opaque", "Blending disabled", 'PMARKER', 1),
    ("1", "Mod", "Unknown", 'PMARKER', 2),
    ("2", "Decal", "Unknown", 'FORCE_TURBULENCE', 3),
    ("3", "Add", "Unknown", 'ARROW_LEFTRIGHT', 4),
    ("4", "Mod2x", "Unknown", 'PMARKER_SEL', 5),
    ("5", "Fade", "Unknown", 'PMARKER_ACT', 6),
    ("6", "Deeeprun Tram", "Unknown", 'PMARKER_ACT', 7)
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
    ("1", "Wrap X", "Texture wrap X", 'PMARKER', 0x1),
    ("2", "Wrap Y", "Texture wrap Y", 'FORCE_TURBULENCE', 0x2),
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
    ("Trousers", "Trousers", "Trousers geosets", 'PMARKER', 15),
    ("Unknown2", "Unknown 2", "", 'PMARKER', 16),
    ("Cloak", "Cloak", "Cloak geosets", 'PMARKER', 17),
    ("Unknown3", "Unknown 3", "", 'PMARKER', 18),
    ("Eyeglows", "Eyeglows geosets", "", 'PMARKER', 19),
    ("Belt", "Belt", "Belt / Bellypack geosets", 'PMARKER', 20),
    ("Trail", "Trail", "Trail geosets / Undead bones (Legion+)", 'PMARKER', 21),
    ("Feet", "Feet", "Feet geosets", 'PMARKER', 22),
    ("Hands", "BE Hands", "Hands for Blood Elf / Night Elf (Legion+)", 'PMARKER', 23)
]


def mesh_part_id_menu(self, context):
    geoset_group = context.object.WowM2Geoset.MeshPartID
    if geoset_group == 'Skin':
        return [('0', 'No subtype', "")]

    elif geoset_group == 'Hair':
        return [(str(i), "{}_{}".format('Hairstyle', i), "") for i in M2SkinMeshPartID.Hairstyle.value]

    elif geoset_group == 'Facial1':
        return [(str(i), "{}_{}".format('Facial', i), "") for i in M2SkinMeshPartID.Facial1.value]

    elif geoset_group == 'Facial2':
        return [(str(i), "{}_{}".format('Facial', i), "") for i in M2SkinMeshPartID.Facial2.value]

    elif geoset_group == 'Facial3':
        return [(str(i), "{}_{}".format('Facial', i), "") for i in M2SkinMeshPartID.Facial3.value]

    elif geoset_group == 'Glove':  # TODO: describe
        return [(str(i), "{}_{}".format('Glove', i), "") for i in M2SkinMeshPartID.Glove.value]

    elif geoset_group == 'Boots':
        return [(str(i), "{}_{}".format('Boots', i), "") for i in M2SkinMeshPartID.Boots.value]

    elif geoset_group in ('Unknown1', 'Unknown2', 'Unknown3'):
        return [('0', 'No subtype', "")]

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
                ("1002", "Chest", "Purpose is unknown")]

    elif geoset_group == 'Pants':
        return [("1101", "Regular", "Regular pants"),
                ("1102", "Skirt", "Short skirt"),
                ("1103", "Armored", "Armored pants")]

    elif geoset_group == 'Tabard':
        return [("1201", "None (DNE)", "No tabard"),
                ("1202", "Tabard", "Tabard")]

    elif geoset_group == 'Trousers':
        return [("1301", "Legs", "Legs"),
               ("1302", "Dress", "Tabard")]

    elif geoset_group == 'Cloak':
        return [(str(i), "{}_{}".format('Cloak', i), "") for i in M2SkinMeshPartID.Cloak.value]

    elif geoset_group == 'Eyeglows':
        return [("1701", "None (DNE)", "No eyeglow"),
                ("1702", "Racial", "Racial eyeglow"),
                ("1703", "DK", "Death Knight eyeglow")]

    elif geoset_group == 'Belt':
        return [("1801", "None (DNE)", "No belt / bellypack"),
                ("1802", "Bulky", "Bulky belt")]

    elif geoset_group == 'Tail':
        return [('0', 'No subtype', "")]

    elif geoset_group == 'Feet':
        return [("2001", "None (DNE)", "No feet"),
                ("2002", "Feet", "Feet")]

    elif geoset_group == 'Hands':
        return [("1", "BE / NE Hands", 'Hands for Blood Elf / Night Elf')]

    else:
        return [('0', 'No subtype', "")]







