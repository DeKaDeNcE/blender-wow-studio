from struct import pack, unpack
from functools import partial


#############################################################
######                 Parsing helpers                 ######
#############################################################

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
