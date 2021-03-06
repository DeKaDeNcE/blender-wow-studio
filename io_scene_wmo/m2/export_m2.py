from ..pywowlib.m2_file import M2File
from .m2_scene import BlenderM2Scene

from ..ui import get_addon_prefs


def export_m2(version, filepath, selected_only, fill_textures):
    addon_prefs = get_addon_prefs()

    m2 = M2File(version)
    bl_m2 = BlenderM2Scene(m2, addon_prefs)
    bl_m2.save_properties(filepath, selected_only)
    bl_m2.save_bones(selected_only)
    bl_m2.save_geosets(selected_only, fill_textures)
    bl_m2.save_collision(selected_only)

    m2.write(filepath)




