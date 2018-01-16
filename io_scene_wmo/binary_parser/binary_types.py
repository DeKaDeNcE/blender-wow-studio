from struct import pack, unpack
from collections import deque, Iterable
from types import LambdaType

non_compatible_type_exception_str = "Provided type is not generic or container or does not define custom __read__() and __write__() methods."

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
        self.__size__ = size
        self.default_value = default_value

    def __call__(self):
        return self.default_value

    def __read__(self, f):
        return unpack(self.format, f.read(self.__size__))

    def __write__(self, f, value):
        f.write(pack(self.format, value))

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

    def __read__(self, f):
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

    def __write__(self, f, string):
        f.write(string.encode(self.encoding))

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
        return cls(item)


class static_array(metaclass=ArrayMeta):
    __slots__ = ('len', 'type')

    def __init__(self, len):
        self.len = len

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

    def __call__(self, *args, **kwargs):
        self.type = args[0]()
        return tuple(self.type() if isinstance(self.type, LambdaType) else self.type for _ in range(self.len))



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
                new_args.append(lambda: arg(*args, **call_kwargs))

            else:
                new_args.append(arg)

        new_kwargs = {}
        if kwargs is not None:
            for key, value in kwargs.items():
                if isinstance(value, template_T):
                    new_kwargs[key] = value.resolve_template_type(*args, **call_kwargs)

                elif isinstance(value, TemplateExpressionQueue):
                    new_kwargs[key] = lambda: value(*args, **call_kwargs)

                else:
                    new_kwargs[key] = value

            return lambda: type_(*new_args, **call_kwargs)

        else:
            return lambda: type_(*new_args)

    def __or__(self, other):
        return self, other

# structures
class StructMeta(TypeMeta):
    def __new__(cls, name, bases, dict):

        struct_fields = []
        for base in bases:
            if issubclass(base, Struct):
                struct_fields.extend(base.__fields__)
        struct_fields.extend(dict.get('__fields__'))

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

        dict['__fields__'] = new_fields

        slots = []

        for field in new_fields:
            slots.append(field[1])

        if new_fields:
            dict['__slots__'] = slots

        return type.__new__(cls, name, bases, dict)


class Struct(metaclass=StructMeta):
    __fields__ = []
    __slots__ = ()
    bound_containers = []

    def __init__(self, *args, **kwargs):

        for i, field_pair in enumerate(self.__fields__):
            field_type, field_name = field_pair
            type_ = field_type

            if isinstance(field_type, template_T):
                type_ = field_type.resolve_template_type(*args, **kwargs)
                self.__fields__[i] = (type_, self.__fields__[i][1])

            elif isinstance(field_type, TemplateExpressionQueue):
                type_ = field_type(*args, **kwargs)

                setattr(self, field_name, type_())

            if isinstance(type_, (GenericType, string_t, LambdaType, static_array)):
                setattr(self, field_name, type_())
            else:
                setattr(self, field_name, type_(*args, **kwargs))

    def __read__(self, f):

        for field_type, field_name in self.__fields__:
            if isinstance(field_type, (GenericType, string_t)):
                setattr(self, field_name, field_type.__read__(f))
            elif isinstance(field_type, (static_array)):
                setattr(self, field_name, field_type.__read__(f, self))
            else:
                getattr(self, field_name).__read__(f)

    def __write__(self, f):

        self.update_bound_container_data()

        for field_type, field_name in self.__fields__:

            if isinstance(field_type, (GenericType, string_t, tuple_t, array_t)):
                field_type.__write__(f, getattr(self, field_name))
            else:
                getattr(self, field_name).__write__(f)

    def update_bound_container_data(self):
        # update dependent length variables in the structure
        for cntr, name in self.bound_containers:
            setattr(self, cntr.bound_value, len(getattr(self, name)))

    @property
    def __size__(self):
        total_size = 0
        for field_type, field_name in self.__fields__:
            total_size += field_type.__size__
        return total_size


def typeof(struct, field):
    is_class = isinstance(struct, type)
    if (not is_class and not isinstance(struct, Struct)) or (is_class and not issubclass(struct, Struct)):
        raise TypeError("typeof(object, attribute) requires a statically typed structure.")

    for field_type, field_name in struct.__fields__:
        if field_name == field:
            return struct.__template_types__[field_name] if isinstance(field_type, template_T) \
                else field_type if not isinstance(field_type, TemplateExpressionQueue) else TemplateExpressionQueue

    raise AttributeError("Struct {} does not define field {}."
                         .format(struct.__class__ if is_class else struct.__class__.__name__, field))


def sizeof(struct):
    if not isinstance(struct, Struct):
        raise TypeError("sizeof(object) requires an instance of a statically typed structure.")
    return struct.__size__


if __name__ == '__main__':

    class SampleStruct(Struct):
        __fields__ = (
            template_T['a'] | 'test',
        )
    class SampleStruct2(Struct):
        __fields__ = (
            float64 | 'big_radius',
            SampleStruct << {'a': int8} | 'structure',
            static_array[3] << (SampleStruct << {'a': float32}) | 'test',
        )


    struct = SampleStruct2()

    print(type(struct.test[0].test))


