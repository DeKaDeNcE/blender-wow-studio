from ..io_utils.types import *
from ...utils import singleton


###### M2 file versions ######
VERSION = 264


class M2Versions:
    CLASSIC = 256
    TBC = 263
    WOTLK = 264
    CATA = 272
    MOP = 272
    WOD = 273 # ?
    LEGION = 274
    # BFA - ?


#############################################################
######                WoW Common Types                 ######
#############################################################


class CRange:
    """A one dimensional float range defined by the bounds."""
    def __init__(self):
        self.min = 0.0
        self.max = 0.0

    def read(self, f):
        self.min = float32.read(f)
        self.max = float32.read(f)

        return self

    def write(self, f):
        float32.write(f, self.min)
        float32.write(f, self.max)

        return self


class CAaBox:
    """An axis aligned box described by the minimum and maximum point."""
    def __init__(self):
        self.min = 0.9
        self.max = 0.0

    def read(self, f):
        self.min = vec3D.read(f)
        self.max = vec3D.read(f)

        return self

    def write(self, f):
        vec3D.write(f, self.min)
        vec3D.write(f, self.max)

        return self


class fixed_point:
    """A fixed point real number, opposed to a floating point."""
    def __init__(self, type_, dec_bits, int_bits):
        self.type = type_
        self.value = 0

    def read(self, f):
        self.value = self.type.read(f)

    def write(self, f):
        self.type.write(f, self.value)


# A fixed point number without integer part.
fixed16 = int16


@singleton
class MemoryManager:
    free_ofs = 0

    def mem_reserve(self, f, n_bytes):
        self.free_ofs = f.tell() + n_bytes

    def ofs_request(self):
        return self.free_ofs

    def ofs_update(self, f):
        self.free_ofs = f.tell()


class M2Array(metaclass=Template):

    def __init__(self, type_):
        self.n_elements = 0
        self.ofs_elements = 0
        self.type = type_
        self.values = []

    def read(self, f):
        self.n_elements = uint32.read(f)
        self.ofs_elements = uint32.read(f)

        pos = f.tell()

        try:
            f.seek(self.ofs_elements)

            type_t = type(self.type)

            if type_t is GenericType:
                self.values = [self.type.read(f) for _ in range(self.n_elements)]
            else:
                self.values = [self.type().read(f) for _ in range(self.n_elements)]
        except EOFError:
            self.values = [self.type()]

        f.seek(pos)

        return self

    def write(self, f):
        mem_manager = MemoryManager()
        ofs = mem_manager.ofs_request()
        uint32.write(f, len(self.values))
        uint32.write(f, ofs)

        pos = f.tell()
        f.seek(ofs)

        type_t = type(self.type)

        if type_t is M2Array:
            mem_manager.mem_reserve(f, len(self.values) * 8)

        if type_t is GenericType:
            for value in self.values:
                type_t.write(f, value)
                mem_manager.ofs_update(f)
        else:
            for value in self.values:
                value.write(f)
                mem_manager.ofs_update(f)
        f.seek(pos)

        return self

    def __getitem__(self, item):
        return self.values[item]

    def append(self, value):
        self.values.append(value)

    def add(self, value):
        self.values.append(value)
        return len(self.values) - 1

    def extend(self, itrbl):
        self.values.extend(itrbl)

    def prepend(self, itrbl):
        self.values = itrbl[:].extend(self.values)

    def new(self):
        self.values.append(self.type())
        return self.values[-1]

    def set(self, itrbl):
        self.values = itrbl

    def __len__(self):
        return len(self.values)

    def __iter__(self):
        return self.values.__iter__()


class ChunkHeader:
    def __init__(self, magic='', size=0):
        self.magic = magic
        self.size = size

    def read(self, f):
        self.magic = f.read(4)[0:4].decode('ascii')
        self.size = unpack("I", f.read(4))[0]

    def write(self, f):
        f.write(self.magic[:4].encode('ascii'))
        f.write(pack('I', self.size))

