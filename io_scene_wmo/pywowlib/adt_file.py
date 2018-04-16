from .file_formats.adt_chunks import *
from io import BufferedReader


class ADTFile:
    def __init__(self, file=None):

        self.mver = MVER()
        self.mhdr = MHDR()
        self.mhdr = MHDR()
        self.mcin = MCIN()
        self.mtex = MTEX()
        self.mmdx = MMDX()
        self.mmid = 

        if file:
            if type(file) is BufferedReader:
                self.read(file)

            elif type(file) is str:
                with open(file, 'rb') as f:
                    self.read(f)

            else:
                raise NotImplementedError('\nFile argument must be either a filepath string or io.BufferedReader')




