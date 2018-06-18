from . import panels

panels_list = [
    'doodad',
    'fog',
    'group',
    'light',
    'liquid',
    'material',
    'portal',
    'root',
    'toolbar',
    'vertex_info'
]


def register_wmo_panels():
    for panel_name in panels_list:
        getattr(panels, panel_name).register()


def unregister_wmo_panels():
    for panel_name in panels_list:
        getattr(panels, panel_name).unregister()

