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
    "version": (4, 0),
    "blender": (2, 80, 0),
    "description": "Import-Export WoW WMO",
    "category": "Import-Export"
}

import os
import sys
import traceback
import bpy
import bpy.utils.previews
from bpy.props import StringProperty
from . import auto_load

PACKAGE_NAME = __package__

# include custom lib vendoring dir
parent_dir = os.path.abspath(os.path.dirname(__file__))
vendor_dir = os.path.join(parent_dir, 'third_party')

sys.path.append(vendor_dir)

# load custom icons
ui_icons = {}
pcoll = None

pcoll = bpy.utils.previews.new()

icons_dir = os.path.join(os.path.dirname(__file__), "ui", "icons")

for file in os.listdir(icons_dir):
    pcoll.load(os.path.splitext(file)[0].upper(), os.path.join(icons_dir, file), 'IMAGE')

for name, icon_file in pcoll.items():
    ui_icons[name] = icon_file.icon_id


class WMOPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    wow_path: StringProperty(
        name="WoW Client Path",
        subtype='DIR_PATH'
    )

    fileinfo_path: StringProperty(
        name="Path to fileinfo.exe",
        subtype='FILE_PATH'
    )

    wmv_path: StringProperty(
        name="WoW Model Viewer Log Path",
        subtype='FILE_PATH'
    )

    cache_dir_path: StringProperty(
        name="Cache Directory Path",
        description="Any folder that can be used to store exporter content",
        subtype="DIR_PATH"
    )

    project_dir_path: StringProperty(
        name="Project Directory Path",
        description="A directory blender saves WoW files to and treats as top-priority patch.",
        subtype="DIR_PATH"
    )

    def draw(self, context):
        self.layout.prop(self, "wow_path")
        self.layout.prop(self, "wmv_path")
        self.layout.prop(self, "fileinfo_path")
        self.layout.prop(self, "cache_dir_path")
        self.layout.prop(self, "project_dir_path")


auto_load.init()

def register():
    bpy.utils.register_class(WMOPreferences)

    try:
        auto_load.register()
        print("Registered WoW Blender Studio")

    except:
        traceback.print_exc()

def unregister():
    try:
        auto_load.unregister()
        print("Registered WoW Blender Studio")

    except:
        traceback.print_exc()

    global pcoll
    bpy.utils.previews.remove(pcoll)
    bpy.utils.unregister_class(WMOPreferences)


if __name__ == "__main__":
    register()
