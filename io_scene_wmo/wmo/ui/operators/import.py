import bpy
import os
import traceback
import struct

from ... import import_wmo
from ...utils.wmv import wmv_get_last_wmo
from ....ui import get_addon_prefs
from ....utils.misc import load_game_data


class WMO_OT_import_last_wmo_from_wmv(bpy.types.Operator):
    bl_idname = "scene.wow_import_last_wmo_from_wmv"
    bl_label = "Load last WMO from WMV"
    bl_description = "Load last WMO from WMV"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):

        game_data = load_game_data()

        if not game_data or not game_data.files:
            self.report({'ERROR'}, "Failed to import model. Connect to game client first.")
            return {'CANCELLED'}

        addon_prefs = get_addon_prefs()
        cache_dir = addon_prefs.cache_dir_path

        wmo_path = wmv_get_last_wmo()

        if not wmo_path:
            self.report({'ERROR'}, """WoW Model Viewer log contains no WMO entries.
            Make sure to use compatible WMV version or open a .wmo there.""")
            return {'CANCELLED'}

        try:
            game_data.extract_file(cache_dir, wmo_path)

            if os.name != 'nt':
                root_path = os.path.join(cache_dir, wmo_path.replace('\\', '/'))
            else:
                root_path = os.path.join(cache_dir, wmo_path)

            with open(root_path, 'rb') as f:
                f.seek(24)
                n_groups = struct.unpack('I', f.read(4))[0]

            group_paths = ["{}_{}.wmo".format(wmo_path[:-4], str(i).zfill(3)) for i in range(n_groups)]

            game_data.extract_files(cache_dir, group_paths)

            import_wmo.import_wmo_to_blender_scene(root_path, True)

            # clean up unnecessary files and directories
            os.remove(root_path)
            for group_path in group_paths:
                os.remove(os.path.join(cache_dir, *group_path.split('\\')))

        except:
            traceback.print_exc()
            self.report({'ERROR'}, "Failed to import model.")
            return {'CANCELLED'}

        self.report({'INFO'}, "Done importing WMO object to scene.")
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)
