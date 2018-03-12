from ...io_utils.types import uint32
from ... import CLIENT_VERSION, WoWVersions


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

    @staticmethod
    def write(f, string, str_block_ofs):
        pos = f.tell()
        f.seek(0, 2)
        str_pos = f.tell()
        f.write((string + '\0').encode('utf-8'))
        f.seek(pos)
        uint32.write(str_pos - str_block_ofs)


class DBCLangString:
    def __init__(self):
        if CLIENT_VERSION < WoWVersions.CATA:
            self.enUS = ''
            self.koKR = ''
            self.frFR = ''
            self.deDE = ''
            self.enCN = ''  # also zhCN
            self.enTW = ''  # also zhTW
            self.esES = ''
            self.esMX = ''

            if CLIENT_VERSION >= WoWVersions.TBC:
                self.ruRU = ''
                self.jaJP = ''
                self.ptPT = ''  # also ptBR
                self.itIT = ''
                self.unknown_12 = ''
                self.unknown_13 = ''
                self.unknown_14 = ''
                self.unknown_15 = ''

        else:
            self.client_locale = ''

        self.flags = 0

    def read(self, f, str_block_ofs):
        if CLIENT_VERSION < WoWVersions.CATA:
            self.enUS = DBCString.read(f, str_block_ofs)
            self.koKR = DBCString.read(f, str_block_ofs)
            self.frFR = DBCString.read(f, str_block_ofs)
            self.deDE = DBCString.read(f, str_block_ofs)
            self.enCN = DBCString.read(f, str_block_ofs)
            self.enTW = DBCString.read(f, str_block_ofs)
            self.esES = DBCString.read(f, str_block_ofs)
            self.esMX = DBCString.read(f, str_block_ofs)

            if CLIENT_VERSION >= WoWVersions.TBC:
                self.ruRU = DBCString.read(f, str_block_ofs)
                self.jaJP = DBCString.read(f, str_block_ofs)
                self.ptPT = DBCString.read(f, str_block_ofs)
                self.itIT = DBCString.read(f, str_block_ofs)
                self.unknown_12 = DBCString.read(f, str_block_ofs)
                self.unknown_13 = DBCString.read(f, str_block_ofs)
                self.unknown_14 = DBCString.read(f, str_block_ofs)
                self.unknown_15 = DBCString.read(f, str_block_ofs)

        else:
            self.client_locale = DBCString.read(f, str_block_ofs)

        self.flags = uint32.read(f)

        return self

    def write(self, f, str_block_ofs):
        if CLIENT_VERSION < WoWVersions.CATA:
            DBCString.write(f, self.enUS, str_block_ofs)
            DBCString.write(f, self.koKR, str_block_ofs)
            DBCString.write(f, self.frFR, str_block_ofs)
            DBCString.write(f, self.deDE, str_block_ofs)
            DBCString.write(f, self.enCN, str_block_ofs)
            DBCString.write(f, self.enTW, str_block_ofs)
            DBCString.write(f, self.esES, str_block_ofs)
            DBCString.write(f, self.esMX, str_block_ofs)

            if CLIENT_VERSION >= WoWVersions.TBC:
                DBCString.write(f, self.ruRU, str_block_ofs)
                DBCString.write(f, self.jaJP, str_block_ofs)
                DBCString.write(f, self.ptPT, str_block_ofs)
                DBCString.write(f, self.itIT, str_block_ofs)
                DBCString.write(f, self.unknown_12, str_block_ofs)
                DBCString.write(f, self.unknown_13, str_block_ofs)
                DBCString.write(f, self.unknown_14, str_block_ofs)
                DBCString.write(f, self.unknown_15, str_block_ofs)

        else:
            DBCString.write(f, self.client_locale, str_block_ofs)

        uint32.write(f, self.flags)

        return self

