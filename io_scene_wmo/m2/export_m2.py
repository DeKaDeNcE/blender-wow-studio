from ..pywowlib.m2_file import M2File
from .m2_scene import BlenderM2Scene

from ..ui import get_addon_prefs


def export_m2(filepath, version, selected_only, fill_texpath):
    addon_prefs = get_addon_prefs()

    m2 = M2File(version)
    bl_m2 = BlenderM2Scene(M2File, addon_prefs)



