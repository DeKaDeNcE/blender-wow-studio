from file_formats.m2_format import M2Header

if __name__ == '__main__':
    for _ in range(10):
        with open("C:\\Users\\sshum\\Desktop\\ArthasLichKing\\ArthasLichKing.M2", 'rb') as f:
            m2 = M2Header()
            m2.__read__(f)
            print(m2)