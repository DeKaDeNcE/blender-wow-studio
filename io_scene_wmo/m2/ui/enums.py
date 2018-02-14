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

MESH_PART_IDS = [
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
    pass

