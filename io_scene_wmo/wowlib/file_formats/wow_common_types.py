from binary_parser.binary_types import *


class C2Vector(Struct):
    """A two component float vector."""
    __fields__ = (
        float32 | 'x',
        float32 | 'y'
    )


class C2iVector(Struct):
    """A two component int vector."""
    __fields__ = (
        int32 | 'x',
        int32 | 'y'
    )


class C3Vector(Struct):
    """A three component float vector."""
    __fields__ = (
        float32 | 'x',
        float32 | 'y',
        float32 | 'z'
    )


class C3iVector(Struct):
    """A three component int vector."""
    __fields__ = (
        int32 | 'x',
        int32 | 'y',
        int32 | 'z'
    )


class C4Vector(Struct):
    """A four component float vector."""
    __fields__ = (
        float32 | 'x',
        float32 | 'y',
        float32 | 'z',
        float32 | 'w',
    )
    
    
class C4iVector(Struct):
    """A four component int vector."""
    __fields__ = (
        int32 | 'x',
        int32 | 'y',
        int32 | 'z',
        int32 | 'w'
    )


class C33Matrix(Struct):
    """A three by three matrix."""
    __fields__ = (
        array[3] << C3Vector | 'columns',
    )


class C34Matrix(Struct):
    """A three by four matrix."""
    __fields__ = (
        array[4] << C3Vector | 'columns',
    )


class C44Matrix(Struct):
    """A four by four matrix."""
    __fields__ = (
        array[4] << C4Vector | 'columns',
    )


class C4Plane(Struct):
    """A 3D plane defined by four floats."""
    __fields__ = (
        C3Vector | 'normal',
        float32 | 'distance'
    )


class C4Quaternion(Struct):
    """A quaternion."""
    __fields__ = (
        float32 | 'x',
        float32 | 'y',
        float32 | 'z',
        float32 | 'w',
    )


class CRange(Struct):
    """A one dimensional float range defined by the bounds."""
    __fields__ = (
        float32 | 'min',
        float32 | 'max'
    )


class CiRange(Struct):
    """A one dimensional int range defined by the bounds."""
    __fields__ = (
        int32 | 'min',
        int32 | 'max'
    )


class CAaBox(Struct):
    """An axis aligned box described by the minimum and maximum point."""
    __fields__ = (
        C3Vector | 'min',
        C3Vector | 'max'
    )


class CAaSphere(Struct):
    """An axis aligned sphere described by position and radius."""
    __fields__ = (
        C3Vector | 'position',
        float32 | 'radius'
    )


class CArgb(Struct):
    """A color given in values of red, green, blue and alpha."""
    __fields__ = (
        uint8 | 'r',
        uint8 | 'g',
        uint8 | 'b',
        uint8 | 'a'    
    )


class CImVector(Struct):
    """A color given in values of blue, green, red and alpha."""
    __fields__ = (
        uint8 | 'b',
        uint8 | 'g',
        uint8 | 'r',
        uint8 | 'a'
    )


class C3sVector(Struct):
    """A three component vector of shorts."""
    __fields__ = (
        int16 | 'x',
        int16 | 'y',
        int16 | 'z'
    )


class C3Segment(Struct):
    __fields__ = (
        C3Vector | 'start',
        C3Vector | 'end'
    )


class CFacet(Struct):
    __fields__ = (
        C4Plane | 'plane',
        array[3] << C3Vector | 'vertices'
    )


class C3Ray(Struct):
    """A ray defined by an origin and direction."""
    __fields__ = (
        C3Vector | 'origin',
        C3Vector | 'dir'
    )


class CRect(Struct):
    __fields__ = (
        float32 | 'top',
        float32 | 'miny',
        float32 | 'left',
        float32 | 'minx',
        float32 | 'bottom',
        float32 | 'maxy',
        float32 | 'right',
        float32 | 'maxx',
    )


class CiRect(Struct):
    __fields__ = (
        int32 | 'top',
        int32 | 'miny',
        int32 | 'left',
        int32 | 'minx',
        int32 | 'bottom',
        int32 | 'maxy',
        int32 | 'right',
        int32 | 'maxx',
    )


class fixed_point(Struct):
    """A fixed point real number, opposed to a floating point."""
    __fields__ = (
        # TODO: BITFIELDS
    )
    

# A fixed point number without integer part.
fixed16 = int16

