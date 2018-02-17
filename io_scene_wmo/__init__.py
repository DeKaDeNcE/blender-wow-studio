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
from bpy.props import StringProperty, BoolProperty
from .ui import register_ui, unregister_ui
from .ui.icon_manager import get_ui_icons

get_ui_icons()

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

    def draw(self, context):
        self.layout.prop(self, "wow_path")
        self.layout.prop(self, "wmv_path")
        self.layout.prop(self, "blp_path")
        self.layout.prop(self, "fileinfo_path")

        self.layout.prop(self, "use_cache_dir")
        row = self.layout.row()
        row.prop(self, "cache_dir_path")
        if not context.user_preferences.addons[__package__].preferences.use_cache_dir:
            row.enabled = False


def register():
    bpy.utils.register_module(__name__)
    register_ui()


def unregister():
    bpy.utils.unregister_module(__name__)
    unregister_ui()


if __name__ == "__main__":
    register()

