from ..binary_parser.binary_types import *


class MVER(Struct):
    __fields__ = (
            uint32 | 'version'
    )

class MHDR(Struct):
    __fields__ = (
        uint32 | 'flags',
    )
