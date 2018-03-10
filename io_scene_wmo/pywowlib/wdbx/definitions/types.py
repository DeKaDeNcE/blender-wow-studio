from ...io_utils.types import uint32


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

