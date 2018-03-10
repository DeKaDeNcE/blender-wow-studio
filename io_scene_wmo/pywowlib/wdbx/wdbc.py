from ..io_utils.types import *
from collections import namedtuple
from io import BytesIO
from .definitions import wotlk
from .definitions.types import DBCString


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


class DBCFile:
    def __init__(self, name):
        definition = getattr(wotlk, name)
        if not definition:
            raise FileNotFoundError('No definition for DB <<{}>> found.'.format(name))

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

    def read_from_gamedata(self, game_data):
        f = BytesIO(game_data.read_file('DBFilesClient\\{}.dbc'.format(self.name)))
        self.read(f)

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

