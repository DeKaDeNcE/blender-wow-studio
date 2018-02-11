import os

from .file_formats.m2_format import M2Header, M2Versions
from .file_formats.skin_format import M2SkinProfile


class M2File:
    def __init__(self, version, filepath=None):
        self.version = version

        if filepath:
            self.filepath = filepath
            with open(filepath, 'rb') as f:
                self.root = M2Header()
                self.root.read(f)
                self.skin_profiles = []

                if version >= M2Versions.WOTLK:
                    raw_path = os.path.splitext(filepath)[0]
                    for i in range(self.root.num_skin_profiles):
                        with open("{}{}.skin".format(raw_path, str(i).zfill(2)), 'rb') as skin_file:
                            self.skin_profiles.append(M2SkinProfile().read(skin_file))

                else:
                    self.skin_profiles = self.root.skin_profiles

        else:
            self.filepath = None
            self.root = M2Header()
            self.skin_profiles = [M2SkinProfile()]

    def write(self, filepath):
        with open(filepath, 'rb') as f:
            if self.version < M2Versions.WOTLK:
                self.root.skin_profiles = self.skin_profiles
            else:
                raw_path = os.path.splitext(filepath)[0]
                for i, skin in enumerate(self.skin_profiles):
                    with open("{}{}.skin".format(raw_path, str(i).zfill(2)), 'wb') as skin_file:
                        skin.write(skin_file)

            self.root.write(f)

            # TODO: anim, skel and phys













