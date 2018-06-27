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



    '''
    wmo = WMOFile(filepath)
    wmo.read()

    print("\n\n### Importing WMO components ###")

    if load_textures:
        game_data = load_game_data()

        if load_textures:
            addon_prefs = get_addon_prefs()
            print("\n\n### Extracting textures ###")
            game_data.extract_textures_as_png(addon_prefs.cache_dir_path, wmo.motx.get_all_strings())

    # group objects if required
    parent = None
    if group_objects:
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        parent = bpy.context.scene.objects.active
        parent.name = wmo.display_name + ".wmo"
        wmo.parent = parent

    # load all materials in root file
    wmo.load_materials()

    # load all WMO components
    wmo.load_lights()
    wmo.load_properties()
    wmo.load_fogs()

    print("\n\n### Importing WMO groups ###")

    for group in wmo.groups:
        obj_name = wmo.mogn.get_string(group.mogp.group_name_ofs)
        print("\nImporting group <<{}>>".format(obj_name))
        if not obj_name == 'antiportal':
            group.load_object(obj_name, import_doodads)

    wmo.load_portals()

    print("\n\n### Importing WMO doodad sets ###")

    if import_doodads and game_data.files:
        addon_prefs = get_addon_prefs()
        wmo.load_doodads(addon_prefs.cache_dir_path, game_data)
    else:
        wmo.load_doodads()

    print("\nDone importing WMO. \nTotal import time: ",
          time.strftime("%M minutes %S seconds.\a", time.gmtime(time.time() - start_time)))

    return parent
    
    '''
