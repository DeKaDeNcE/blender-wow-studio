import bpy

def get_addon_prefs():
    return bpy.context.preferences.addons[__package__[:-3]].preferences

