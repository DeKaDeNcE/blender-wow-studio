from pywowlib.wmo_file import WMOFile

if __name__ == '__main__':
    root = WMOFile(0, filepath='D:\\WoWModding\World of Warcraft 3.3.5a\\Data\\'
                               'patch-Q.MPQ\\world\\wmo\\Azeroth\\Buildings\\Chapel\\RedridgeChapel.wmo')

    root.read()
