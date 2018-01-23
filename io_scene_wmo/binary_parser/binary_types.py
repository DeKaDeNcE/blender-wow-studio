from struct import pack, unpack
from collections import deque, Iterable
from itertools import product
from functools import partial

generic_type_dict = {
    'b': "int8",
    'B': "uint8",
    'h': "int16",
    'H': "uint16",
    'i': "int32",
    'I': "uint32",
    'q': "int64",
    'Q': "uint64",
    'f': "float",
    's': "char",
    '?': "bool"
}

class GenericType:
    def __init__(self, format, size, default_value=0):
        self.format = format
        self.size = size
        self.default_value = default_value

    def __call__(self):
        return self.default_value

    def _read_(self, f):
        return unpack(self.format, f.read(self.size))

    def _write_(self, f, value):
        f.write(pack(self.format, value))

    def _size_(self):
        return self.size

    def __or__(self, other):
        return self, other

    def __repr__(self):
        return "<GenericType: {}>".format(generic_type_dict[self.format])


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

class string_t:
    default_value = ''

    def __init__(self, len=0, encoding='utf-8'):
        self.encoding = encoding
        self.len = len

    def __call__(self):
        return self.default_value

    def _read_(self, f):
        if self.len == 0:
            string = ''
            while True:
                char = f.read(1)
                if char != 0:
                    string += char
                else:
                    break
            string.decode(self.encoding)
            return string
        else:
            return f.read(self.len).decode(self.encoding)

    def _write_(self, f, string):
        f.write(string.encode(self.encoding))

    def __or__(self, other):
        return self, other

# preprocessor-like conditions
class if_:
    def __init__(self, exp):
        self.value = bool(exp)

class elif_:
    def __init__(self, exp):
        self.value = bool(exp)

class else_: pass
class endif_: pass

# parent of all supported complex types
class TypeMeta(type):
    def __or__(cls, other):
        return cls, other

    def __lshift__(cls, other):
        args = []
        kwargs = None
        if type(other) is dict:
            kwargs = other
        elif isinstance(other, Iterable):
            for element in other:
                if type(element) is not dict:
                    if kwargs is None:
                        args.append(element)
                    else:
                        raise SyntaxError("Positional argument follows a keyword argument.")
                else:
                    kwargs = element
        else:
            args.append(other)

        if kwargs is not None:
            return TemplateExpressionQueue(cls, *args, **kwargs)
        else:
            return TemplateExpressionQueue(cls, *args)

class Type(metaclass=TypeMeta): pass


# containers
class ArrayMeta(type):
    def __getitem__(cls, item):
        if not cls.is_bound:
            if type(item) is not int:
                raise TypeError('Static array can only accept ints as length identifiers. Use dynamic array instead.')
            elif item == 0:
                raise ValueError('Static array cannot have 0-length dimensions.')

        if type(item) is int and item < 0:
            raise ValueError('Length cannot be negative.')

        return cls(item)


class this_size:
    __slots__ = ('size_attr', 'extra_bytes')
    def __init__(self, size_attr, extra_bytes=0):
        self.size_attr = size_attr
        self.extra_bytes = extra_bytes

class this_exp:
    __slots__ = ('exp')
    def __init__(self, exp):
        self.exp = exp

class static_array(metaclass=ArrayMeta):
    __slots__ = ('dimensions', 'type', 'type_size')
    is_bound = False

    @staticmethod
    def generate_ndimensional_iterable(lengths, type, iterable):
        if len(lengths) > 1:
            dimension = iterable(static_array.generate_ndimensional_iterable(lengths[1:], type, iterable)
                                 for _ in range(lengths[0]))
        else:
            dimension = iterable(type() if callable(type) else type for _ in range(lengths[0]))

        return dimension

    def __init__(self, length):
        self.dimensions = [length,]

    def __getitem__(self, length):
        if not self.is_bound:
            if type(length) is not int:
                raise TypeError('Static array can only accept integers as length identifiers. Use dynamic array instead.')
            elif length == 0:
                raise ValueError('Static array cannot have 0-length dimensions.')

        if self.dimensions[-1] == 0:
            raise TypeError('Zero-length dimension cannot contain any further elements.')

        if type(length) is int and length < 0:
            raise ValueError('Length cannot be negative.')

        self.dimensions.append(length)
        return self

    def __or__(self, other):
        return self, other

    def __lshift__(self, other):
        args = []
        kwargs = None
        if type(other) is dict:
            kwargs = other
        elif isinstance(other, Iterable):
            for element in other:
                if type(element) is not dict:
                    if kwargs is None:
                        args.append(element)
                    else:
                        raise SyntaxError("Positional argument follows a keyword argument.")
                else:
                    kwargs = element
        else:
            args.append(other)

        if kwargs is not None:
            return TemplateExpressionQueue(self, *args, **kwargs)
        else:
            return TemplateExpressionQueue(self, *args)

    def _read_(self, f, attribute_pair):
        cls, attr = attribute_pair
        this = cls
        itrbl = getattr(cls, attr)
        dimensions = self.dimensions
        if self.is_bound:
            for i, dm in enumerate(self.dimensions):
                dm_type = type(dm)
                if dm_type is str:
                    dimensions[i] = getattr(cls, dm)
                elif dm_type is int:
                    pass
                elif dm_type is this_size:
                    dimensions[i] = getattr(this, dm_type.size_attr) * self.type_size - dm_type.extra_bytes
                elif dm_type is this_exp:
                    dimensions[i] = eval(dm_type.exp)
                else:
                    raise TypeError('Unknown dynamic_array length identifier. Must be structure field name or int.')

        if isinstance(self.type, (GenericType, string_t)):
            return static_array.generate_ndimensional_iterable(dimensions,
                                                               self.type,
                                                               list if self.is_bound else tuple)

        for indices in product(*[range(s) for s in dimensions]):
            item = itrbl
            for idx in indices:
                item = item[idx]
            item._read_(f)

        return itrbl

    def _write_(self, f, attribute_pair):
        cls, attr = attribute_pair
        itrbl = getattr(cls, attr)
        if self.is_bound:
            for i, dm in enumerate(self.dimensions):
                dm_type = type(dm)
                if dm_type is str:
                    dm_itrbl = itrbl
                    for j in range(i + 1):
                        dm_itrbl = dm_itrbl[j]

                    setattr(cls, dm, len(dm_itrbl))

                elif dm_type is int:
                    pass

                elif dm_type is this_size:
                    setattr(cls, dm_type.size_attr, self._size_() - dm_type.extra_bytes)

                elif dm_type is this_exp:
                    pass

                else:
                    raise TypeError('Unknown dynamic_array length identifier. Must be structure field name or int.')

        for indices in product(*[range(s) for s in self.dimensions]):
            item = itrbl
            for idx in indices:
                item = item[idx]

            self.type._write_(f, item) if isinstance(self.type, (GenericType, string_t)) else item._write_(f)

    def __call__(self, *args, **kwargs):
        arg = args[0]
        self.type = arg() if callable(arg) else arg
        type_ = self.type() if callable(self.type) else self.type

        try:
            self.type_size = self.type._size_() if isinstance(type_, (GenericType, string_t)) else type_._size_()
        except AttributeError:
            raise TypeError("All used types should define _size_ method.")

        return self.generate_ndimensional_iterable(self.dimensions, self.type, tuple)

    def _size_(self):
        length = self.dimensions[0]
        for dim in self.dimensions[1:]:
            length *= dim

        return self.type_size * length


class dynamic_array(static_array):
    __slots__ = ('dimensions', 'type')
    is_bound = True


# templates
class typename_t_meta(TypeMeta):
    def __getitem__(cls, item):
        instance = cls()
        instance.id = item
        return instance


class template_T(metaclass=typename_t_meta):
    __slots__ = ('id',)

    def resolve_template_type(self, *args, **kwargs):
        if isinstance(self.id, str):
            type_ = kwargs.get(self.id)
            if not type_:
                raise KeyError("Template key <<{}>> was not passed to structure constructor.".format(self.id))
        elif isinstance(self.id, int):
            try:
                type_ = args[self.id]
            except IndexError:
                raise IndexError("Template builder is expecting {} or more positional arguments."
                                 .format(self.id + 1))
        else:
            raise TypeError("Templates can only be resolved using positional arguments or keywords.")

        return type_

    def __or__(self, other):
        return self, other

    def __lshift__(self, other):
        args = []
        kwargs = None
        if type(other) is dict:
            kwargs = other
        elif isinstance(other, Iterable):
            for element in other:
                if type(element) is not dict:
                    if kwargs is None:
                        args.append(element)
                    else:
                        raise SyntaxError("Positional argument follows a keyword argument.")
                else:
                    kwargs = element
        else:
            args.append(other)

        if kwargs is not None:
            return TemplateExpressionQueue(self, *args, **kwargs)
        else:
            return TemplateExpressionQueue(self, *args)


class TemplateExpressionQueue:
    __slots__ = ('cls', 'args', 'kwargs')

    def __init__(self, cls, *args, **kwargs):
        self.cls = cls
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        call_kwargs = self.kwargs

        for key, value in kwargs.items():
            if key not in call_kwargs:
                call_kwargs[key] = value

        type_ = self.cls
        if isinstance(type_, template_T):
            type_ = self.cls.resolve_template_type(*args, **call_kwargs)

        new_args = []
        for arg in self.args:
            if isinstance(arg, template_T):
                new_args.append(arg.resolve_template_type(*args, **call_kwargs))

            elif isinstance(arg, TemplateExpressionQueue):
                new_args.append(partial(arg, *args, **call_kwargs))

            else:
                new_args.append(arg)

        new_kwargs = {}
        if kwargs is not None:
            for key, value in kwargs.items():
                if isinstance(value, template_T):
                    new_kwargs[key] = value.resolve_template_type(*args, **call_kwargs)

                elif isinstance(value, TemplateExpressionQueue):
                    new_kwargs[key] = partial(value, *args, **call_kwargs)

                else:
                    new_kwargs[key] = value

            return partial(type_, *new_args, **call_kwargs)

        else:
            return partial(type_, *new_args)

    def __or__(self, other):
        return self, other

# structures
class StructMeta(TypeMeta):
    def __new__(cls, name, bases, dict):

        struct_fields = []
        for base in bases:
            if issubclass(base, Struct):
                struct_fields.extend(base._fields_)
        struct_fields.extend(dict.get('_fields_'))

        new_fields = []
        exec_controller = deque()

        for element in struct_fields:
            if isinstance(element, if_):
                exec_controller.append(element.value)

            elif isinstance(element, elif_):
                try:
                    exec_controller[-1] = element.value
                except IndexError:
                    raise SyntaxError("elif_ should follow an if_ instruction.")

            elif element is else_:
                try:
                    exec_controller[-1] = not exec_controller[-1]
                except IndexError:
                    raise SyntaxError("else_ should follow an if_ instruction.")

            elif element is endif_:
                try:
                    exec_controller.pop()
                except IndexError:
                    raise SyntaxError("endif_ can only be used to close a condition.")

            elif (not exec_controller or exec_controller[-1]) and isinstance(element, tuple) and len(element) == 2:

                for field_type, field_name in new_fields:
                    if field_name == element[1]:
                        raise NameError("Field name \"{}\" was already used before in this struct.".format(element[1]))
                new_fields.append(element)

        if exec_controller:
            raise SyntaxError("At least one condition is not closed with endif_.")

        dict['_fields_'] = new_fields

        slots = ['_rfields_',]

        for field in new_fields:
            slots.append(field[1])

        if new_fields:
            dict['__slots__'] = slots

        return type.__new__(cls, name, bases, dict)


class Struct(metaclass=StructMeta):
    __slots__ = ()
    _fields_ = []
    bound_containers = []

    def __init__(self, *args, **kwargs):
        self._rfields_ = self._fields_[:]

        for i, field_pair in enumerate(self._fields_):
            field_type, field_name = field_pair
            type_ = field_type

            if isinstance(field_type, template_T):
                type_ = field_type.resolve_template_type(*args, **kwargs)
                self._rfields_[i] = (type_, self._fields_[i][1])

            elif isinstance(field_type, TemplateExpressionQueue):
                type_ = field_type(*args, **kwargs)
                self._rfields_[i] = (field_type.cls, self._fields_[i][1])

                setattr(self, field_name, type_())
                continue

            if isinstance(type_, (GenericType, string_t)):
                setattr(self, field_name, type_())
            else:
                setattr(self, field_name, type_(*args, **kwargs))

    def _read_(self, f):

        for field_type, field_name in self._rfields_:
            if isinstance(field_type, (GenericType, string_t)):
                setattr(self, field_name, field_type._read_(f))
            elif isinstance(field_type, (static_array, dynamic_array)):
                setattr(self, field_name, field_type._read_(f, (self, field_name)))
            else:
                getattr(self, field_name)._read_(f)

    def _write_(self, f):

        for field_type, field_name in self._rfields_:

            if isinstance(field_type, (GenericType, string_t)):
                field_type._write_(f, getattr(self, field_name))
            elif isinstance(field_type, (static_array, dynamic_array)):
                field_type._write_(f, (self, field_name))
            else:
                getattr(self, field_name)._write_(f)

    def _size_(self):
        size = 0
        try:
            for field_type, field_name in self._rfields_:
                size += field_type._size_() \
                        if isinstance(field_type, (GenericType, string_t, static_array, dynamic_array)) else \
                        getattr(self, field_name)._size_()
        except AttributeError:
            raise TypeError("All used types should define _size_ method.")

        return size


def sizeof(struct):
    return struct._size_()

def typeof(struct, attr):
    try:
        for field_type, field_name in struct._rfields_:
            if field_name == attr:
                return field_type
    except AttributeError:
        raise TypeError('typeof() function works only for Struct objects.')

    raise AttributeError('Field \'{}\' not found in struct \'{}\'.'.format(attr, struct))


if __name__ == '__main__':

    class SampleStruct(Struct):
        _fields_ = (
            template_T[0] | 'test',
        )

    class SampleStruct2(Struct):
        _fields_ = (
            SampleStruct << template_T['a'] | 'test',
            SampleStruct << template_T['b'] | 'test1',
            template_T['a'] | 'test3',
            static_array[1][2] << (SampleStruct << int8) | 'array',
        )

    struct = SampleStruct2(a=int16, b=int32, c=SampleStruct(int8))







