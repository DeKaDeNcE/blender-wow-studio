from . import panels

panels_list = [
    'geoset',
    'material',
    'texture',
    'attachment',
    'event',
    'camera',
    'texture_transform',
    'particle',
    'colors',
    'light',
    'bone',
    'transparency'
]


def register_m2_panels():
    for panel_name in panels_list:
        getattr(panels, panel_name).register()


def unregister_m2_panels():
    for panel_name in panels_list:
        getattr(panels, panel_name).unregister()