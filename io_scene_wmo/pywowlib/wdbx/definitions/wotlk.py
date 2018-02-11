from collections import OrderedDict
from ..wdbc import DBCString
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


