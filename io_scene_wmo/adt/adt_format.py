from ..binary_parser.binary_types import *


class MVER(Struct):
    __fields__ = (
        uint32_t | 'version'
    )

class MHDR(Struct):
    __fields__ = (
        uint32_t | 'flags',
    )
