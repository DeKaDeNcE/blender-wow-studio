from enum import IntEnum


class ADTChunkFlags(IntEnum):
    HAS_MCSH = 0x1
    IMPASS = 0x2
    LQ_RIVER = 0x4
    LQ_OCEAN = 0x8
    LQ_MAGMA = 0x10
    LQ_SLIME = 0x20
    HAS_MCCV = 0x40c
    UNKNOWN = 0x80
    DO_NOT_FIX_ALPHA_MAP = 0x8000
    HIGH_RES_HOLES = 0x10000



