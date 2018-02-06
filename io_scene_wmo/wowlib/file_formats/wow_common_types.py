from struct import pack, unpack
from functools import partial


#############################################################
######                 Parsing helpers                 ######
#############################################################

class GenericType:
    __slots__ = ('format', 'size', 'default_value')

    def __init__(self, format, size, default_value=0):
        self.format = format
        self.size = size
        self.default_value = 0

    def read(self, f, n=1):
        if type(n) is not int:
            raise TypeError('Length can only be represented by an integer value.')

        if n <= 0:
            raise TypeError('Length should be an integer value above 0.')

        if n == 1:
            ret = unpack(self.format, f.read(self.size))
        else:
            ret = unpack(str(n) + self.format, f.read(self.size * n))
        return ret[0] if len(ret) == 1 else ret

    def write(self, f, value, n=1):
        if type(n) is not int:
            raise TypeError('Length can only be represented by an integer value.')

        if n <= 0:
            raise TypeError('Length should be an integer value above 0.')

        if n == 1:
            f.write(pack(self.format, value))
        else:
            f.write(pack(str(n) + self.format, *value))

    def __call__(self, *args, **kwargs):
        return self.default_value


class Template(type):
    def __lshift__(cls, other):
        args = []
        kwargs = None

        if type(other) is tuple:
            for arg in other:
                if type(arg) is not dict:
                    if kwargs is None:
                        args.append(arg)
                    else:
                        raise SyntaxError("Keyword argument followed by a positional argument.")
                else:
                    if kwargs is not None:
                        raise SyntaxError("Only one set of keyword arguments is supported.")
                    kwargs = arg

        elif type(other) is dict:
            kwargs = other

        else:
            return partial(cls, other)

        if kwargs is not None:
            return partial(cls, *args, **kwargs)
        else:
            return partial(cls, *args)


class Array(metaclass=Template):
    __slots__ = ('type', 'length', 'values')

    def __init__(self, type_, length):
        self.type = type_
        self.length = length
        self.values = [type_ for _ in range(length)]

    def read(self, f):
        type_ = type(self.type)

        if type_ is GenericType:
            self.values = [self.type.read(f) for _ in range(self.length)]
        else:
            for val in self.values:
                val.read(f)

        return self

    def write(self, f):
        type_ = type(self.type)

        if type_ is GenericType:
            for val in self.values:
                self.type.write(f, val)
        else:
            for val in self.values:
                val.write(f)

        return self


###### Common binary types ######

int8 = GenericType('b', 1)
uint8 = GenericType('B', 1)
int16 = GenericType('h', 2)
uint16 = GenericType('H', 2)
int32 = GenericType('i', 4)
uint32 = GenericType('I', 4)
int64 = GenericType('q', 8)
uint64 = GenericType('Q', 8)
float32 = GenericType('f', 4, 0.0)
float64 = GenericType('f', 8, 0.0)
char = GenericType('s', 1, '')
boolean = GenericType('?', 1, False)
vec3D = GenericType('fff', 12, (0.0, 0.0, 0.0))
vec2D = GenericType('ff', 8, (0.0, 0.0))
quat = GenericType('ffff', 16, (0.0, 0.0, 0.0, 0.0))
string = char


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


