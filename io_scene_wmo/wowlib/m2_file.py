from file_formats.m2_format import M2Header
from file_formats.skin_format import M2SkinProfile

if __name__ == '__main__':
    for _ in range(10):
        with open("C:\\Users\\sshum\\Desktop\\ArthasLichKing\\ArthasLichKing_Unarmed00.skin", 'rb') as f:
            skin = M2SkinProfile()
            skin.read(f)
            print(skin)