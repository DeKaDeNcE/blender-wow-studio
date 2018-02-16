from ..io_utils.types import *
from collections import namedtuple


class DBCHeader:

    def __init__(self):
        self.magic = 'WDBC'
        self.record_count = 0
        self.field_count = 0
        self.record_size = 0
        self.string_block_size = 0

    def read(self, f):
        self.magic = string.read(f, 4)
        self.record_count = uint32.read(f)
        self.field_count = uint32.read(f)
        self.record_size = uint32.read(f)
        self.string_block_size = uint32.read(f)

        return self

    def write(self, f):
        string.write(f, self.magic)
        uint32.write(f, self.record_count)
        uint32.write(f, self.field_count)
        uint32.write(f, self.record_size)
        uint32.write(f, self.string_block_size)

        return self


class DBCString:
    @staticmethod
    def read(f, str_block_ofs):
        ofs = uint32.read(f)
        pos = f.tell()
        f.seek(ofs + str_block_ofs)

        strng = b''
        while True:
            char = f.read(1)
            if char != b'\0':
                strng += char
            else:
                break
        f.seek(pos)

        return strng.decode('utf-8')

    '''
    @staticmethod
    def write(f, strng):
        f.write((strng + '\0').encode('utf-8'))
    '''


class DBCFile:
    def __init__(self, definition, name):
        self.header = DBCHeader()
        self.name = name
        self.field_names = namedtuple('RecordGen', [name for name in definition.keys()])
        self.field_types = tuple([type_ for type_ in definition.values()])
        self.records = []

    def read(self, f):
        self.header.read(f)
        str_block_ofs = 20 + self.header.record_count * self.header.record_size
        for _ in range(self.header.record_count):
            self.records.append(self.field_names(*[f_type.read(f, str_block_ofs) if f_type is DBCString else f_type.read(f) for f_type in self.field_types]))

    def get_field(self, id, name):
        for record in self.records:
            if record.ID == id:
                return getattr(record, name)


class DBFilesClient:
    def __init__(self):
        self.tables = {}

    def __getattr__(self, item):
        return self.tables[item]

    def add(self, wdb):
        self.tables[wdb.name] = wdb

