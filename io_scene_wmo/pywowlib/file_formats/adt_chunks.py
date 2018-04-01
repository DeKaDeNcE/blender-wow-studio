from .wow_common_types import *
from .. import CLIENT_VERSION, WoWVersions

TILE_SIZE = 5533.333333333
MAP_SIZE_MIN = -17066.66656
MAP_SIZE_MAX = 17066.66657


class MVER:
    def __init__(self):
        self.header = ChunkHeader('REVM', 4)
        self.version = 0

    def read(self, f):
        self.header.read(f)
        self.version = uint32.read(f)

    def write(self, f):
        self.header.write(f)
        uint32.write(self.header)


class MHDR:
    def __init__(self):
        self.header = ChunkHeader('RDHM', 54)

    def read(self, f):
        self.header.read(f)

    def write(self, f):
        self.header.write(f)

    class MCIN:
        def __init__(self):
            self.header = ChunkHeader('NICM', 16)
            self.offset = 0
            self.size = 0

        def read(self, f):
            self.header.read(f)
            self.offset = uint32.read(f)
            self.size = uint32.read(f)
            f.skip(8)

        def write(self, f):
            self.header.write(f)
            uint32.write(f, self.header)
            uint32.write(f, self.size)
            f.skip(8)


class MTEX(StringBlockChunk):
    magic = 'XTEM'


class MMDX(StringBlockChunk):
    magic = 'XDMM'


class MMID:
    def __init__(self):
        self.header = ChunkHeader('DIMM')
        self.offsets = []

    def read(self, f):
        self.header.read(f)

        for _ in range(self.header.size // 4):
            self.offsets.append(uint32.read(f))

    def write(self, f):
        self.header.size = len(self.offsets) * 4
        self.header.write(f)

        for offset in self.offsets:
            uint32.write(offset)


class MWMO(StringBlockChunk):
    magic = 'OMWM'


class MWID:
    def __init__(self):
        self.header = ChunkHeader('DIWM')
        self.offsets = []

    def read(self, f):
        self.header.read(f)

        for _ in range(self.header.size // 4):
            self.offsets.append(uint32.read(f))

    def write(self, f):
        self.header.size = len(self.offsets) * 4
        self.header.write(f)

        for offset in self.offsets:
            uint32.write(offset)


class ADTDoodadDefinition:
    def __init__(self):
        self.name_id = 0
        self.unique_id = 0
        self.position = (0, 0, 0)
        self.rotation = (0, 0, 0)
        self.scale = 0
        self.flags = 0

    def read(self, f):
        self.name_id = uint32.read(f)
        self.unique_id = uint32.read(f)
        self.position = vec3D.read(f)
        self.rotation = vec3D.read(f)
        self.scale = uint16.read(f)
        self.flags = uint16.read(f)

        return self

    def write(self, f):
        uint32.write(f, self.name_id)
        uint32.write(f, self.unique_id)
        vec3D.write(f, self.position)
        vec3D.write(f, self.rotation)
        uint16.write(f, self.scale)
        uint16.write(f, self.flags)

        return self


class MDDF:
    def __init__(self):
        self.header = ChunkHeader('FDDM')
        self.doodad_instances = []

    def read(self, f):
        self.header.read(f)
        for _ in range(self.header.size // 36):
            self.doodad_instances.append(ADTDoodadDefinition().read(f))

    def write(self, f):
        self.header.size = len(self.doodad_instances) * 36
        self.header.write(f)

        for doodad in self.doodad_instances:
            doodad.write(f)


class ADTWMODefinition:
    def __init__(self):
        self.name_id = 0
        self.unique_id = 0
        self.position = (0.0, 0.0, 0.0)
        self.rotation = (0.0, 0.0, 0.0)
        self.extents = CAaBox()
        self.flags = 0
        self.doodad_set = 0
        self.name_set = 0
        self.scale = 0

    def read(self, f):
        self.name_id = uint32.read(f)
        self.unique_id = uint32.read(f)
        self.position = vec3D.read(f)
        self.rotation = vec3D.read(f)
        self.extents.read(f)
        self.flags = uint16.read(f)
        self.doodad_set = uint16.read(f)
        self.name_set = uint16.read(f)
        self.scale = uint16.read(f)

    def write(self, f):
        uint32.write(f, self.name_id)
        uint32.write(f, self.unique_id)
        vec3D.write(f, self.position)
        vec3D.write(f, self.rotation)
        self.extents.write(f)
        uint16.write(f, self.flags)
        uint16.write(f, self.doodad_set)
        uint16.write(f, self.name_set)
        uint16.write(f, self.scale)


class MODF:
    def __init__(self):
        self.header = ChunkHeader('FDOM')
        self.wmo_instances = []

    def read(self, f):
        self.header.read(f)
        for _ in range(self.header.size // 64):
            wmo_instance = ADTWMODefinition()
            wmo_instance.read(f)
            self.wmo_instances.append(wmo_instance)

    def write(self, f):
        self.header.size = len(self.wmo_instances) * 64
        self.header.write(f)

        for wmo_instance in self.wmo_instances:
            wmo_instance.write(f)


class MCNK:
    def __init__(self):
        self.header = ChunkHeader('KNCM')
        self.index_x = 0
        self.index_y = 0
        self.n_layers = 0
        self.n_doodad_refs = 0

        if CLIENT_VERSION >= WoWVersions.MOP:
            self.hole_high_res = 0
        else:
            self.ofs_height = 0
            self.ofs_normal = 0

        self.ofs_layer = 0
        self.ofs_refs = 0
        self.ofs_alpha = 0
        self.size_alpha = 0
        self.ofs_shadow = 0
        self.size_shadow = 0
        self.area_id = 0
        self.n_map_obj_refs = 0
        self.holes_low_res = 0
        self.unknown_but_used = 0
        self.low_quality_texture_map = []


class MCVT:
    def __init__(self):
        self.header = ChunkHeader('TVCM')
        self.height = [0.0] * 145

    def read(self, f):
        self.header.read(f)
        self.height = [float32.read(f) for _ in range(145)]

    def write(self, f):
        self.header.write(f)
        for value in self.height: float32.write(value)


class MCLV:
    def __init__(self):
        self.header = ChunkHeader('VLCM')
        self.colors = [(255, 255, 255, 255)] * 145

    def read(self, f):
        self.header.read(f)
        self.colors = [uint8.read(f, 4) for _ in range(145)]

    def write(self, f):
        self.header.write(f)
        for value in self.colors: uint8.write(f, value, 4)


class MCCV:
    def __init__(self):
        self.header = ChunkHeader('VCCM')
        self.colors = [(255, 255, 255, 255)] * 145

    def read(self, f):
        self.header.read(f)
        self.colors = [uint8.read(f, 4) for _ in range(145)]

    def write(self, f):
        self.header.write(f)
        for value in self.colors: uint8.write(f, value, 4)


class MCNR:
    def __init__(self):
        self.header = ChunkHeader('RNCM')
        self.entries = 
































