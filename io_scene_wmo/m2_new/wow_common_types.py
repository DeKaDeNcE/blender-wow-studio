import struct
from binary_parser.binary_types import *
from mathutils import Vector, Quaternion


class C2Vector(Struct):
    __fields__ = (
        typename_t['x'] | 'x',
        typename_t['x'] | 'y'
    )

class CAaBox(Struct):
    def __init__(self):
        self.min = Vector((0.0, 0.0, 0.0))
        self.max = Vector((0.0, 0.0, 0.0))

    def read(self, f):
        self.min = Vector(struct.unpack('fff', f.read(12))[0])
        self.max = Vector(struct.unpack('fff', f.read(12))[0])

    def write(self, f):
        f.write(struct.pack('fff', *self.min))
        f.write(struct.pack('fff', *self.max))


class C4Quaternion(Struct):
    def __init__(self, tuple=(0, 0, 0, 0)):
        self.x = tuple[0]
        self.y = tuple[1]
        self.z = tuple[2]
        self.w = tuple[3]

    def to_bl_quaternion(self):
        return Quaternion((self.w, self.x, self.y, self.z))

    @classmethod
    def from_bl_quaternion(cls, qtrn):
        return cls((qtrn[1], qtrn[2], qtrn[3], qtrn[0]))

    def read(self, f):
        self.x = struct.unpack('f', f.read(4))[0]
        self.y = struct.unpack('f', f.read(4))[0]
        self.z = struct.unpack('f', f.read(4))[0]
        self.w = struct.unpack('f', f.read(4))[0]

    def write(self, f):
        f.write(struct.pack('f', self.x))
        f.write(struct.pack('f', self.y))
        f.write(struct.pack('f', self.z))
        f.write(struct.pack('f', self.w))


class Fixed16:
    def __init__(self):
        self.value = 0

    def read(self, f):
        self.value = struct.unpack('H', f.read(2))[0] / 0x7FFF

    def write(self, f):
        f.write(struct.pack('H', int(self.value * 0x7FFF)))


class C2Vector:
    def __init__(self, iterable=(0, 0)):
        self.x = iterable[0]
        self.y = iterable[1]

    def to_bl_vector(self):
        return Vector((self.x, self.y, self.z))

    def read(self, f):
        self.x = struct.unpack('f', f.read(4))[0]
        self.y = struct.unpack('f', f.read(4))[0]

    def write(self, f):
        f.write(struct.pack('f', self.x))
        f.write(struct.pack('f', self.y))


class C3Vector:
    def __init__(self, iterable=(0, 0, 0)):
        self.x = iterable[0]
        self.y = iterable[1]
        self.z = iterable[2]

    def to_bl_vector(self):
        return Vector((self.x, self.y, self.z))

    def read(self, f):
        self.x = struct.unpack('f', f.read(4))[0]
        self.y = struct.unpack('f', f.read(4))[0]
        self.z = struct.unpack('f', f.read(4))[0]

    def write(self, f):
        f.write(struct.pack('f', self.x))
        f.write(struct.pack('f', self.y))
        f.write(struct.pack('f', self.z))


class CImVector:
    """ Used for storing colors in most WoW fileformats """

    def __init__(self, color=(0xFF, 0xFF, 0xFF, 0xFF)):
        self.b = color[2]
        self.g = color[1]
        self.r = color[0]
        self.a = color[3]

    def read(self, f):
        self.b = struct.unpack('B', f.read(1))[0]
        self.g = struct.unpack('B', f.read(1))[0]
        self.r = struct.unpack('B', f.read(1))[0]
        self.a = struct.unpack('B', f.read(1))[0]

    def write(self, f):
        f.write(struct.pack('B', self.b))
        f.write(struct.pack('B', self.g))
        f.write(struct.pack('B', self.r))
        f.write(struct.pack('B', self.a))

    def to_vector(self):
        return Vector((self.b, self.g, self.r, self.a))

    def __add__(self, other):
        if isinstance(other, CImVector):
            return CImVector(self.to_vector() + other.to_vector())
        else:
            raise TypeError("CImVector only supports adding operation with another CImVector.")

    def __sub__(self, other):
        if isinstance(other, CImVector):
            return CImVector(self.to_vector() - other.to_vector())
        else:
            raise TypeError("CImVector only supports subtraction operation with another CImVector.")

    def __mul__(self, other):
        if isinstance(other, CImVector):
            return CImVector((max(x * other[i], 0xFF) for i, x in enumerate(self.to_vector())))
        else:
            raise TypeError("CImVector only supports multiplicatin operation with another CImVector.")

    def __div__(self, other):
        if isinstance(other, CImVector):
            return CImVector((min(x / other[i], 0x00) for i, x in enumerate(self.to_vector())))
        else:
            raise TypeError("CImVector only supports division operation with another CImVector.")

    def __iadd__(self, other):
        if isinstance(other, CImVector):
            return CImVector(self.to_vector() + other.to_vector())
        else:
            raise TypeError("CImVector only supports adding operation with another CImVector.")

    def __isub__(self, other):
        if isinstance(other, CImVector):
            return CImVector(self.to_vector() - other.to_vector())
        else:
            raise TypeError("CImVector only supports subtraction operation with another CImVector.")

    def __imul__(self, other):
        if isinstance(other, CImVector):
            return CImVector((max(x * other[i], 0xFF) for i, x in enumerate(self.to_vector())))
        else:
            raise TypeError("CImVector only supports multiplicatin operation with another CImVector.")

    def __idiv__(self, other):
        if isinstance(other, CImVector):
            return CImVector((min(x / other[i], 0x00) for i, x in enumerate(self.to_vector())))
        else:
            raise TypeError("CImVector only supports division operation with another CImVector.")

    def __str__(self):
        return "({}, {}, {}, {})".format(self.r, self.g, self.b, self.a)


class ChunkHeader:
    def __init__(self, magic='', size=0):
        self.magic = magic
        self.size = size

    def read(self, f):
        self.magic = f.read(4)[0:4].decode('ascii')
        self.size = struct.unpack("I", f.read(4))[0]

    def write(self, f):
        f.write(self.magic[:4].encode('ascii'))
        f.write(struct.pack('I', self.size))


