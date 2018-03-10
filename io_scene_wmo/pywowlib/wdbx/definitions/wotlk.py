from collections import OrderedDict
from .types import DBCString
from ...io_utils.types import *

AnimationData = OrderedDict((
    ('ID', uint32),
    ('Name', DBCString),
    ('WeaponFlags', uint32),
    ('BodyFlags', uint32),
    ('Flags', uint32),
    ('Fallback', uint32),
    ('BehaviorID', uint32),
    ('BehaviorTier', uint32)
))

CharSections = OrderedDict((
    ('ID', uint32),
    ('Race', uint32),
    ('Gender', uint32),
    ('GeneralType', DBCString),
    ('Texture1', DBCString),
    ('Texture2', DBCString),
    ('Texture3', DBCString),
    ('Flags', uint32),
    ('Type', uint32),
    ('Variation', uint32)
))

CreatureDisplayInfo = OrderedDict((
    ('ID', uint32),
    ('Model', uint32),
    ('Sound', uint32),
    ('ExtraDisplayInformation', uint32),
    ('Scale', float32),
    ('Opacity', uint32),
    ('Texture1', DBCString),
    ('Texture2', DBCString),
    ('Texture3', DBCString),
    ('PortraitTextureName', DBCString),
    ('BloodLevel', uint32),
    ('Blood', uint32),
    ('NPCSounds', uint32),
    ('Particles', uint32),
    ('CreatureGeosetData', uint32),
    ('ObjectEffectPackageID', uint32)
))

ItemDisplayInfo = OrderedDict((
    ('ID', uint32),
    ('LeftModel', DBCString),
    ('RightModel', DBCString),
    ('LeftModelTexture', DBCString),
    ('RightModelTexture', DBCString),
    ('Icon1', DBCString),
    ('Icon2', DBCString),
    ('GeosetGroup1', uint32),
    ('GeosetGroup2', uint32),
    ('GeosetGroup3', uint32),
    ('Flags', uint32),
    ('SpellVisualID', uint32),
    ('GroupSoundIndex', uint32),
    ('HelmetGeosetVis1', uint32),
    ('HelmetGeosetVis2', uint32),
    ('UpperArmTexture', DBCString),
    ('LowerArmTexture', DBCString),
    ('HandsTexture', DBCString),
    ('UpperTorsoTexture', DBCString),
    ('LowerTorsoTexture', DBCString),
    ('UpperLegTexture', DBCString),
    ('LowerLegTexture', DBCString),
    ('FootTexture', DBCString),
    ('ItemVisual', uint32),
    ('ParticleColorID', uint32)
))


