# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8-80 compliant>


bl_info = {
    "name": "WoW Blender Studio",
    "author": "Skarn",
    "version": (3, 0),
    "blender": (2, 79, 0),
    "description": "Import-Export WoW WMO",
    "category": "Import-Export"
}

import bpy
from .addon_updater_ops import register as register_updater
from .addon_updater_ops import unregister as unregister_updater
from bpy.props import StringProperty, BoolProperty
from .ui import register_ui, unregister_ui

# load and reload submodules
##################################
from .developer_utils import setup_addon_modules
setup_addon_modules(__path__, __name__, True)


class WMOPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    wow_path = StringProperty(
        name="WoW Client Path",
        subtype='DIR_PATH'
    )

    fileinfo_path = StringProperty(
        name="Path to fileinfo.exe",
        subtype='FILE_PATH'
    )

    wmv_path = StringProperty(
        name="WoW Model Viewer Log Path",
        subtype='FILE_PATH'
    )

    blp_path = StringProperty(
        name="BLP Converter Path",
        subtype='FILE_PATH'
    )

    use_cache_dir = BoolProperty(
        name="Use cache directory",
        description="Use custom cache directory for storing textures and other exported content",
        default=True
    )

    cache_dir_path = StringProperty(
        name="Cache Directory Path",
        description="Any folder that can be used to store exporter content",
        subtype="DIR_PATH"
    )

    # addon updater preferences
    auto_check_update = bpy.props.BoolProperty(
        name = "Auto-check for Update",
        description = "If enabled, auto-check for updates using an interval",
        default = True,
        )

    updater_intrval_months = bpy.props.IntProperty(
        name='Months',
        description = "Number of months between checking for updates",
        default=0,
        min=0
        )
    updater_intrval_days = bpy.props.IntProperty(
        name='Days',
        description = "Number of days between checking for updates",
        default=7,
        min=0,
        )
    updater_intrval_hours = bpy.props.IntProperty(
        name='Hours',
        description = "Number of hours between checking for updates",
        default=0,
        min=0,
        max=23
        )
    updater_intrval_minutes = bpy.props.IntProperty(
        name='Minutes',
        description = "Number of minutes between checking for updates",
        default=0,
        min=0,
        max=59
        )

    def draw(self, context):
        self.layout.prop(self, "wow_path")
        self.layout.prop(self, "wmv_path")
        self.layout.prop(self, "blp_path")
        self.layout.prop(self, "fileinfo_path")

        self.layout.prop(self, "use_cache_dir")
        row = self.layout.row()
        row.prop(self, "cache_dir_path")
        if not context.user_preferences.addons['io_scene_wmo'].preferences.use_cache_dir:
            row.enabled = False
        addon_updater_ops.update_settings_ui(self, context)


menu_import = lambda self, ctx: self.layout.operator("import_mesh.wmo", text="WoW WMO (.wmo)")
menu_export = lambda self, ctx: self.layout.operator("import_mesh.wmo", text="WoW WMO (.wmo)")


def register():
    register_updater(bl_info)
    bpy.utils.register_module(__name__)
    register_ui()
    bpy.types.INFO_MT_file_import.append(menu_import)
    bpy.types.INFO_MT_file_export.append(menu_export)


def unregister():
    bpy.utils.unregister_module(__name__)
    unregister_ui()
    bpy.types.INFO_MT_file_import.remove(menu_import)
    bpy.types.INFO_MT_file_export.remove(menu_export)
    unregister_updater()


if __name__ == "__main__":
    register()
