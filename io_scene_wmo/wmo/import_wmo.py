import bpy
import time
from .wmo_scene import BlenderWMOScene
from ..pywowlib.wmo_file import WMOFile
from ..pywowlib import CLIENT_VERSION

from ..ui import get_addon_prefs
from ..utils import load_game_data, ProgressReport


def import_wmo_to_blender_scene(filepath, load_textures, import_doodads, import_lights, import_fogs, group_objects):
    """ Read and import WoW WMO object to Blender scene"""

    start_time = time.time()

    print("\nImporting WMO")

    addon_prefs = get_addon_prefs()
    game_data = load_game_data()

    wmo = WMOFile(CLIENT_VERSION, filepath=filepath)
    wmo.read()
    wmo_scene = BlenderWMOScene(wmo=wmo, prefs=addon_prefs)

    # extract textures to cache folder
    game_data.extract_textures_as_png(addon_prefs.cache_dir_path, wmo.motx.get_all_strings())

    # load all WMO components
    wmo_scene.load_materials()
    wmo_scene.load_lights()
    wmo_scene.load_properties()
    wmo_scene.load_fogs()
    wmo_scene.load_groups()
    wmo_scene.load_portals()
    wmo_scene.load_doodads(assets_dir=addon_prefs.cache_dir_path)

    print("\nDone importing WMO. \nTotal import time: ",
          time.strftime("%M minutes %S seconds.\a", time.gmtime(time.time() - start_time)))

