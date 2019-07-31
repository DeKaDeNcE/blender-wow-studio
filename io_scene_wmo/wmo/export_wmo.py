import bpy
import time

from ..pywowlib.wmo_file import WMOFile, WMOGroupFile
from ..pywowlib import CLIENT_VERSION

from .wmo_scene import BlenderWMOScene

from ..ui import get_addon_prefs


def export_wmo_from_blender_scene(filepath, export_selected, export_method):
    """ Export WoW WMO object from Blender scene to files """

    start_time = time.time()

    wmo = WMOFile(CLIENT_VERSION, filepath)
    bl_scene = BlenderWMOScene(wmo, get_addon_prefs())

    bl_scene.build_references(export_selected, export_method)

    bl_scene.save_doodad_sets()
    bl_scene.save_lights()
    bl_scene.save_fogs()
    bl_scene.save_portals()
    bl_scene.save_groups()
    bl_scene.save_root_header()

    wmo.write()

    print("\nExport finished successfully. "
          "\nTotal export time: ", time.strftime("%M minutes %S seconds\a", time.gmtime(time.time() - start_time)))
