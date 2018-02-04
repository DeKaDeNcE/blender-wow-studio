from struct import pack, unpack
from collections import deque, Iterable, OrderedDict
from itertools import product
from functools import partial
from copy import copy


def _lshift(self, other):
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
        args.append(other)

    if kwargs is not None:
        return TemplateExpressionQueue(self, *args, **kwargs)
    else:
        return TemplateExpressionQueue(self, *args)


#############################################################
######                 Generic types                   ######
#############################################################

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

    def __read__(self, f, dummy=None):
        return unpack(self.format, f.read(self.size))[0]

    def __write__(self, f, value):
        f.write(pack(self.format, value))

    def __size__(self, dummy):
        return self.size

    def __or__(self, other):
        return (self, other[0], other[1]) if type(other) is tuple else (self, other, self.default_value)

    def __call__(self, *args, **kwargs):
        return self.default_value

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


class StringMeta(type):
    def __getitem__(self, item):
        if type(item) is int:
            return string_t(item)
        else:
            raise TypeError("Strings accept only integers as length identifiers.")


class string_t(metaclass=StringMeta):
    default_value = ''

    def __init__(self, len=0, encoding='utf-8'):
        self.encoding = encoding
        self.len = len

    def __call__(self, *args, **kwargs):
        return self.default_value

    def __read__(self, f, dummy=None):
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
        return (self, other[0], other[1]) if type(other) is tuple else (self, other, self.default_value)


class TypeMeta(type):
    def __or__(cls, other):
        return (cls, other[0], other[1]) if type(other) is tuple else (cls, other, None)

    def __lshift__(cls, other):
        return _lshift(cls, other)


#############################################################
######                  Templates                      ######
#############################################################

class TemplateTMeta(TypeMeta):
    def __getitem__(cls, item):
        instance = cls()
        instance.id = item
        return instance


class template_T(metaclass=TemplateTMeta):
    __slots__ = ('id',)

    def resolve_template_type(self, *args, **kwargs):
        if type(self.id) is str:
            type_ = kwargs.get(self.id)
            if not type_:
                raise KeyError("Template key <<{}>> was not passed to structure constructor.".format(self.id))
        elif type(self.id) is int:
            try:
                type_ = args[self.id]
            except IndexError:
                raise IndexError("Template builder is expecting {} or more positional arguments."
                                 .format(self.id + 1))
        else:
            raise TypeError("Templates can only be resolved using positional arguments or keywords.")

        return type_

    def __or__(self, other):
        if type(other) is tuple:
            raise SyntaxError("Template expressions do not support default values.")
        return self, other, None

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


class TemplateTypeCache:
    # make class a singleton
    _instance = None
    cache = {}

    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_, *args, **kwargs)
        return class_._instance

    def setdefault(self, cls, *args, **kwargs):
        hashable_kwargs = frozenset(kwargs)
        t_type = self.cache.get((cls, args, hashable_kwargs))

        if t_type is None:
            t_type = copy(cls)
            t_type.__fields__ = copy(cls.__fields__)

            for f_name, f_pair in t_type.__fields__.items():
                f_type, f_default = f_pair

                if type(f_type) is template_T:
                    if type(f_type.id) is int:
                        try:
                            f_type = args[f_type.id]
                        except IndexError:
                            raise SyntaxError("No template key passed for field \"{}\".".format(f_name))

                    elif type(f_type.id) is str:
                        try:
                            f_type = kwargs[f_type.id]
                        except KeyError:
                            raise SyntaxError("No template key passed for field \"{}\".".format(f_name))

                    else:
                        raise SyntaxError("Invalid template identifier {}".format(f_type.id))

                    t_type.__fields__[f_name] = f_type, None

                elif type(f_type) is TemplateExpressionQueue:
                    type_cache = TemplateTypeCache()

                    partial_ = f_type(*args, **kwargs)
                    keywords = partial_.keywords
                    f_type = type_cache.setdefault(partial_.func, partial_.args, keywords)

                    t_type.__fields__[f_name] = f_type, None

            # self.cache[cls, tuple(args), hashable_kwargs] = t_type

        return t_type


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
        if type(type_) is template_T:
            type_ = self.cls.resolve_template_type(*args, **call_kwargs)

        new_args = []
        for arg in self.args:
            if type(arg) is template_T:
                new_args.append(arg.resolve_template_type(*args, **call_kwargs))

            elif type(arg) is TemplateExpressionQueue:
                new_args.append(partial(arg, *args, **call_kwargs))

            else:
                new_args.append(arg)

        new_kwargs = {}
        if kwargs is not None:
            for key, value in kwargs.items():
                val_type = type(value)
                if val_type is template_T:
                    new_kwargs[key] = value.resolve_template_type(*args, **call_kwargs)

                elif val_type is TemplateExpressionQueue:
                    new_kwargs[key] = partial(value, *args, **call_kwargs)

                else:
                    new_kwargs[key] = value

            return partial(type_, *new_args, **call_kwargs)

        else:
            return partial(type_, *new_args)

    def __or__(self, other):
        if type(other) is tuple:
            raise SyntaxError("Template expressions do not support default values.")
        return self, other, None


#############################################################
######                    Arrays                       ######
#############################################################

class ArrayMeta(type):
    def __getitem__(cls, item):
        type_ = type(item)
        int_only = False

        if not cls.is_dynamic:
            if type_ is not int:
                raise TypeError('Static array can only accept ints as length identifiers. Use dynamic array instead.')
            elif item == 0:
                raise ValueError('Static array cannot have 0-length dimensions.')

        if type_ is int:
            if item < 0:
                raise ValueError('Length cannot be negative.')
            int_only = True

        return cls(item, int_only)


class ThisMeta(type):
    def __getattribute__(cls, name):
        return cls(name)


class this(metaclass=ThisMeta):
    __slots__ = ('exp',)

    def __init__(self, attr):
        self.exp = "struct.{}".format(attr)

    def __add__(self, other):
        self.exp = "({} + {})".format(self.exp, other.exp if type(other) is this else other)
        return self

    def __sub__(self, other):
        self.exp = "({} - {})".format(self.exp, other.exp if type(other) is this else other)
        return self

    def __mul__(self, other):
        self.exp = "({} * {})".format(self.exp, other.exp if type(other) is this else other)
        return self

    def __div__(self, other):
        self.exp = "({} // {})".format(self.exp, other.exp if type(other) is this else other)
        return self


class array(metaclass=ArrayMeta):
    __slots__ = ('dimensions', 'type', 'type_size', 'int_only')
    is_dynamic = False

    def __init__(self, length, int_only):
        self.int_only = int_only
        self.dimensions = [length, ]

    def __getitem__(self, length):
        if not self.is_dynamic:
            if type(length) is not int:
                raise TypeError(
                    'Static array can only accept integers as length identifiers. Use dynamic array instead.')
            elif length == 0:
                raise ValueError('Static array cannot have 0-length dimensions.')

        if self.dimensions[-1] == 0:
            raise TypeError('Zero-length dimension cannot contain any further elements.')

        if type(length) is int:
            if length < 0:
                raise ValueError('Length cannot be negative.')
        else:
            self.int_only = False

        self.dimensions.append(length)
        return self

    def __or__(self, other):
        return self, other, None

    @staticmethod
    def gen_ndim_itrbl(lengths, type, iterable):
        if len(lengths) > 1:
            dimension = iterable(array.gen_ndim_itrbl(lengths[1:], type, iterable)
                                 for _ in range(lengths[0]))
        else:
            dimension = iterable(type() if callable(type) else type for _ in range(lengths[0]))

        return dimension

    def _get_real_dimensions(self, struct):
        real_dimensions = []
        for dim in self.dimensions:
            type_ = type(dim)

            if type_ is int:
                real_dimensions.append(dim)
            elif type_ is str:
                real_dimensions.append(getattr(struct, dim))
            elif type_ is this:
                real_dimensions.append(eval(dim.exp))

        return real_dimensions

    def __lshift__(self, other):
        self.type = other
        return self

    def __call__(self, struct, *args, **kwargs):
        type_t = type(self.type)
        if type_t is template_T:
            self.type = self.type.resolve_template_type(*args, **kwargs)

        elif type_t is TemplateExpressionQueue:
            self.type = TemplateExpressionQueue(*args, **kwargs)

        try:
            self.type_size = self.type().__size__() if type(self.type) not in (
            GenericType, string_t) else self.type.__size__(True)
        except AttributeError:
            raise TypeError("All used types should define __size__() method.")

        if isinstance(type_t, array):
            raise TypeError("Nested arrays are not supported. Use dimensions instead.")

        if not self.is_dynamic or self.int_only:
            return array.gen_ndim_itrbl(self.dimensions, self.type, tuple)
        else:
            dimensions = self._get_real_dimensions(struct)
            for dim in dimensions:
                if type(dim) is not int or dim <= 0:
                    return []

            return array.gen_ndim_itrbl(dimensions, self.type, list)

    def _get_length(self, attribute_pair=None):
        if not self.is_dynamic or self.int_only:
            length = self.dimensions[0]
            for dim in self.dimensions[1:]:
                length *= dim
        else:
            array = getattr(*attribute_pair)
            if not array:
                return 0
            cur_dim = array[0]
            length = len(cur_dim)

            for _ in range(len(self.dimensions) - 1):
                cur_dim = cur_dim[0]
                length *= len(cur_dim)

        return length

    def __read__(self, f, attribute_pair):
        struct, attr = attribute_pair
        type_ = type(self.type)

        dimensions = self.dimensions if not self.is_dynamic or self.int_only else self._get_real_dimensions(struct)

        new_array = array.gen_ndim_itrbl(dimensions, self.type, list)
        if type_ in (GenericType, string_t):

            if len(dimensions) > 1:
                for indices in product(*[range(s) for s in dimensions]):
                    item = new_array
                    n_indices = len(indices)
                    for i, idx in enumerate(indices):
                        item = item[idx]

                        if i == n_indices - 1:
                            item[idx] = self.type.__read__(f)

            else:
                for element in new_array:
                    element

        else:
            for indices in product(*[range(s) for s in dimensions]):
                item = new_array
                for i, idx in enumerate(indices):
                    item = item[idx]

                item.__read__(f)

        setattr(struct, attr, new_array if self.is_dynamic else tuple(new_array))

    def __write__(self, f, attribute_pair):
        struct, attr = attribute_pair
        array = getattr(*attribute_pair)
        type_ = type(self.type)

        dimensions = self.dimensions if not self.is_dynamic or self.int_only else self._get_real_dimensions(struct)

        write_type = lambda item: self.type.__write__(f, item) if type_ in (GenericType, string_t) else item.__write__(
            f)

        for indices in product(*[range(s) for s in dimensions]):
            item = array
            for i, idx in enumerate(indices):
                item = item[idx]
            write_type(item)

    def __size__(self, attribute_pair):

        length = self._get_length(attribute_pair)
        return length * self.type_size


class dynamic_array(array):
    is_dynamic = True


#############################################################
######                  Structure                      ######
#############################################################

# preprocessor-like conditions
class if_:
    def __init__(self, exp):
        self.value = bool(exp)


class elif_:
    def __init__(self, exp):
        self.value = bool(exp)


class else_: pass


class endif_: pass


class StructMeta(TypeMeta):
    """Code launched on creation of the Struct object"""

    def __new__(cls, name, bases, dict):

        # inherit fields from parent structs
        struct_fields = []
        for base in bases:
            if issubclass(base, Struct):
                struct_fields.extend([(values[0], key, values[1]) for key, values in base.__fields__.items()])
        struct_fields.extend(dict.get('__fields__'))

        # create ordered dict for final fields
        new_fields = OrderedDict()

        # implement preprocessor-like directives
        exec_controller = deque()

        for element in struct_fields:
            if type(element) is if_:
                exec_controller.append(element.value)

            elif type(element) is elif_:
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

            elif (not exec_controller or exec_controller[-1]) and type(element) is tuple:

                f_type, f_name, f_default = element

                # safety check
                if f_name in new_fields.keys():
                    raise NameError("Field name \"{}\" was already used before in this struct.".format(f_name))

                new_fields[f_name] = f_type, f_default

        dict['__fields__'] = new_fields

        if new_fields:
            user_slots = dict.get('__slots__')
            final_slots = tuple(new_fields.keys()) + ('__rfields__', ) 
            if user_slots:
                final_slots += tuple(user_slots) if type(user_slots) in (tuple, list) else (user_slots,)
            dict['__slots__'] = final_slots

        return type.__new__(cls, name, bases, dict)


class Struct(metaclass=StructMeta):
    __slots__ = ()
    __fields__ = []

    def __init__(self, *args, **kwargs):
        self.__rfields__ = copy(self.__fields__)

        for f_name, f_pair in self.__rfields__.items():
            f_type, f_default = f_pair
            type_ = type(f_type)

            if type_ is template_T:
                f_type = f_type.resolve_template_type(*args, **kwargs)
                self.__rfields__[f_name] = (f_type, None)

            elif type_ is TemplateExpressionQueue:
                self.__rfields__[f_name] = (f_type.cls, None)
                f_type = f_type(*args, **kwargs)

            elif type_ in (array, dynamic_array):
                setattr(self, f_name, f_type(self, *args, **kwargs))
                continue

            setattr(self, f_name, f_default if f_default is not None else f_type(*args, **kwargs))

    def __read__(self, f):
        for f_name, f_pair in self.__rfields__.items():
            f_type, f_default = f_pair

            if type(f_type) in (GenericType, string_t, array, dynamic_array):
                test = f.tell()
                setattr(self, f_name, f_type.__read__(f, (self, f_name)))
            else:
                getattr(self, f_name).__read__(f)

        return self

    def __write__(self, f):
        for f_name, f_pair in self.__rfields__.items():
            f_type, f_default = f_pair

            if type(f_type) in (GenericType, string_t, array, dynamic_array):
                f_type.__write__(f, getattr(self, f_name))
            else:
                getattr(self, f_name).__write__(f)

        return self

    def __size__(self):
        size = 0

        for f_name, f_pair in self.__rfields__.items():
            f_type, f_default = f_pair
            if type(f_type) in (GenericType, string_t, array, dynamic_array):
                size += f_type.__size__((self, f_name))
            else:
                size += getattr(self, f_name).__size__()

        return size


def sizeof(struct):
    return struct.__size__()


def typeof(struct, attr):
    try:
        f_type, f_default = struct.__rfields__[attr]
    except KeyError:
        raise AttributeError('Field \'{}\' not found in struct \'{}\'.'.format(attr, struct))
    return f_type


if __name__ == '__main__':
    class SampleStruct(Struct):
        __fields__ = (
            template_T[0] | 'test',
        )


    class SampleStruct2(Struct):
        __slots__ = ('test_slot', 'a')
        __fields__ = (
            template_T['a'] | 'test',
            SampleStruct << int8 | 'test_cache',
            template_T['a'] | 'test_template',
            int32 | ('test_default', 5),
            int64 | ('test_this', 2),
            array[1][2] << (SampleStruct << int8) | 'array',
            dynamic_array[1][2] << int64 | 'd_array',
            dynamic_array[this.test_this * this.test_default][this.test_this] << template_T['a'] | 'da_array'
        )


    from timeit import timeit

    # print(timeit(lambda: SampleStruct2(a=int8, b=int16)))

    struct = SampleStruct2(a=int8, b=int16)
    struct.test_slot = 1
    print(struct.test_slot)

