import re
import os
import bpy
import time
import subprocess
from .storm import MPQFile


class WoWFileData:
    def __init__(self, wow_path, blp_path):
        self.wow_path = wow_path
        self.files = self.open_game_resources(self.wow_path)
        self.converter = BLPConverter(blp_path) if blp_path else None

    def __del__(self):
        print("\nUnloading game data...")

    def has_file(self, filepath):
        """ Check if the file is available in WoW filesystem """
        for storage, type in self.files:
            if type:
                file = filepath in storage
            else:
                abs_path = os.path.join(storage, filepath)
                file = os.path.exists(abs_path) and os.path.isfile(abs_path)

            if file:
                return storage, type

        return None, None

    def read_file(self, filepath):
        """ Read the latest version of the file from loaded archives and directories. """

        storage, type = self.has_file(filepath)
        if storage:
            if type:
                file = storage.open(filepath).read()
            else:
                file = open(os.path.join(storage, filepath), "rb").read()

        else:
            raise KeyError("\nRequested file <<{}>> not found in WoW filesystem.".format(filepath))

        return file

    def extract_file(self, dir, filepath):
        """ Extract the latest version of the file from loaded archives to provided working directory. """

        file = self.read_file(filepath)

        abs_path = os.path.join(dir, filepath)
        local_dir = os.path.dirname(abs_path)

        if not os.path.exists(local_dir):
            os.makedirs(local_dir)

        f = open(abs_path, 'wb')
        f.write(file or b'')
        f.close()

    def extract_files(self, dir, filenames):
        """ Extract the latest version of the files from loaded archives to provided working directory. """

        for filename in filenames:
            self.extract_file(dir, filename)

    def extract_textures_as_png(self, dir, filenames):
        """ Read the latest version of the texture files from loaded archives and directories and
        extract them to current working directory as PNG images. """
        if self.converter:
            blp_paths = []

            for filename in filenames:
                abs_path = os.path.join(dir, filename)
                if not os.path.exists(os.path.splitext(abs_path)[0] + ".png"):

                    try:
                        self.extract_file(dir, filename)
                    except KeyError:
                        print("PNG texture extraction: <<{}>> not found in WoW filesystem.".format(filename))
                        continue

                    blp_paths.append(abs_path)

            self.converter.convert(blp_paths)

            for blp_path in blp_paths:
                if os.path.exists(blp_path):
                    os.remove(blp_path)

        else:
            raise FileNotFoundError("\nPNG texture extraction failed. No converter executable specified or found.")

    @staticmethod
    def list_game_data_paths(path):
        """List files and directories in a directory that correspond to WoW patch naming rules."""
        dir_files = []
        for f in os.listdir(path):
            cur_path = os.path.join(path, f)

            if os.path.isfile(cur_path) \
            and os.path.splitext(f)[1].lower() == '.mpq' \
            or not os.path.isfile(cur_path) \
            and re.match(r'patch-\w.mpq', f.lower()):
                dir_files.append(cur_path)

        map(lambda x: x.lower(), dir_files)

        dir_files.sort(key=lambda s: os.path.splitext(s)[0])

        return dir_files

    @staticmethod
    def is_wow_path_valid(wow_path):
        """Check if a given path is a path to WoW client."""
        if wow_path and os.path.exists(os.path.join(wow_path, "Wow.exe")):
            return True

        return False

    @staticmethod
    def open_game_resources(wow_path):
        """Open game resources and store links to them in memory"""

        print("\nProcessing available game resources of client: " + wow_path)
        start_time = time.time()

        if WoWFileData.is_wow_path_valid(wow_path):
            data_packages = WoWFileData.list_game_data_paths(os.path.join(wow_path, "Data\\"))
            resource_map = []

            for package in data_packages:
                if os.path.isfile(package):
                    resource_map.append((MPQFile(package), True))
                    print("\nLoaded MPQ: " + os.path.basename(package))
                else:
                    resource_map.append((package, False))
                    print("\nLoaded folder patch: " + os.path.basename(package))

            print("\nDone initializing data packages.")
            print("Total loading time: ", time.strftime("%M minutes %S seconds", time.gmtime(time.time() - start_time)))
            return resource_map
        else:
            print("\nPath to World of Warcraft is empty or invalid. Failed to load game data.")
            return None


class BLPConverter:
    def __init__(self, tool_path):
        if os.path.exists(tool_path):
            if os.name == 'nt' and not tool_path.endswith('.exe'):
                raise Exception("\nBLPConverter not found. Applications must have a .exe extension on Windows.")
            self.tool_path = tool_path
            print("\nFound BLP Converter executable: " + tool_path)
        else:
            raise Exception("\nNo BLPConverter found at given path: " + tool_path)

    def convert(self, filepaths, always_replace = False):
        init_length = len(self.tool_path) + 4
        init_command = self.tool_path
        cur_length = 0
        cur_args = []

        for filepath in filepaths:
            if always_replace or not os.path.exists(os.path.splitext(filepath)[0] + ".png"):
                length = len(filepath)

                if 2047 - (cur_length + init_length) < length + 2:
                    final_command = [init_command, "-out png"]
                    final_command.extend(cur_args)
                    if subprocess.call(final_command):
                        raise Exception("\nBLP convertion failed.")
                    cur_length = 0
                    cur_args = []

                cur_length += length + 3
                cur_args.append(filepath)

        if cur_length:
            final_command = [init_command, "-out png"]
            final_command.extend(cur_args)
            if subprocess.call(final_command):
                raise Exception("\nBLP convertion failed.")


class WOW_FILESYSTEM_LOAD_OP(bpy.types.Operator):
    bl_idname = 'scene.load_wow_filesystem'
    bl_label = 'Load WoW filesystem'
    bl_description = 'Establish connection to World of Warcraft client files'
    bl_options = {'REGISTER'}

    def execute(self, context):

        if hasattr(bpy, "wow_game_data"):

            delattr(bpy, "wow_game_data")
            self.report({'INFO'}, "WoW game data is unloaded.")

        else:

            preferences = bpy.context.user_preferences.addons.get("io_scene_wmo").preferences

            bpy.wow_game_data = WoWFileData(preferences.wow_path, preferences.blp_path)

            if not bpy.wow_game_data.files:
                self.report({'ERROR'}, "WoW game data is not loaded. Check settings.")
                return {'CANCELLED'}

            self.report({'INFO'}, "WoW game data is loaded.")

        return {'FINISHED'}
