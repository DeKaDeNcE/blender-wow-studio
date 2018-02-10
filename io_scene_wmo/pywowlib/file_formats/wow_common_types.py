from ..io_utils.types import *

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


class M2Array(metaclass=Template):

    def __init__(self, type_):
        self.type = type_
        self.values = []

    def read(self, f):
        n_elements = uint32.read(f)
        ofs_elements = uint32.read(f)

        pos = f.tell()
        f.seek(ofs_elements)

        type_t = type(self.type)

        if type_t is GenericType:
            self.values = [self.type.read(f) for _ in range(n_elements)]
        else:
            self.values = [self.type().read(f) for _ in range(n_elements)]
        f.seek(pos)

        return self

    def write(self, f):
        ofs = request_offset()
        uint32.write(f, len(self.values))
        uint32.write(f, ofs)

        type_t = type(self.type)

        pos = f.tell()
        f.seek(ofs)

        if type_t is GenericType:
            for value in self.values:
                type_t.write(f, value)
        else:
            for value in self.values:
                value.write(f)
        f.seek(pos)

        return self

    def __getitem__(self, item):
        return self.values[item]

    def append(self, value):
        self.values.append(value)

    def extend(self, itrbl):
        self.values.extend(itrbl)

    def prepend(self, itrbl):
        self.values = itrbl[:].extend(self.values)

    def set(self, itrbl):
        self.values = itrbl

    def __len__(self):
        return len(self.values)

    def __iter__(self):
        return self.values.__iter__()

