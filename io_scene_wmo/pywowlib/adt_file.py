from .file_formats.adt_chunks import *
from io import BufferedReader


class ADTFile:
    def __init__(self, file=None):

        self.version = MVER()
        self.header = MHDR()
        self.textures = MTEX()
        self.model_filenames = []
        self.map_object_filenames = []
        self.model_instances = MDDF()
        self.map_object_instances = MODF()
        self.chunks = [[MCNK() for _ in range(16)] for _ in range(16)]

        if file:
            if type(file) is BufferedReader:
                self.read(file)

            elif type(file) is str:
                with open(file, 'rb') as f:
                    self.read(f)

            else:
                raise NotImplementedError('\nFile argument must be either a filepath string or io.BufferedReader')




