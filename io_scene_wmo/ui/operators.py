import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy_extras.io_utils import ExportHelper

from ..pywowlib.archives.wow_filesystem import WoWFileData
from ..wmo.import_wmo import import_wmo_to_blender_scene
from ..wmo.export_wmo import export_wmo_from_blender_scene
from ..m2.import_m2 import import_m2
from ..m2.export_m2 import export_m2
from . import get_addon_prefs

#############################################################
######                 Common operators                ######
#############################################################


class WBS_OT_texture_transparency_toggle(bpy.types.Operator):
    bl_idname = 'wow.toggle_image_alpha'
    bl_label = 'Toggle texture transparency'
    bl_description = 'Toggle texture transparency (useful for working in solid mode)'
    bl_options = {'REGISTER'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.label(text="This will overwrite alpha settings for images. Continue?")

    def execute(self, context):

        for image in bpy.data.images:
            if image.library is not None:
                continue
            image.alpha_mode = 'NONE' if image.alpha_mode in ('PREMUL', 'CHANNEL_PACKED', 'STRAIGHT') else 'STRAIGHT'

        return {'FINISHED'}


class WBS_OT_reload_game_data(bpy.types.Operator):
    bl_idname = 'scene.reload_wow_filesystem'
    bl_label = 'Reoad WoW filesystem'
    bl_description = 'Re-establish connection to World of Warcraft client files'
    bl_options = {'REGISTER'}

    def execute(self, context):

        if hasattr(bpy, "wow_game_data"):
            for storage, type_ in bpy.wow_game_data.files:
                if type_:
                    storage.close()

            delattr(bpy, "wow_game_data")

        addon_preferences = get_addon_prefs()
        bpy.wow_game_data = WoWFileData(addon_preferences.wow_path, addon_preferences.project_dir_path)

        if not bpy.wow_game_data.files:
            self.report({'ERROR'}, "WoW game data is not loaded. Check settings.")
            return {'CANCELLED'}

        self.report({'INFO'}, "WoW game data is reloaded.")

        return {'FINISHED'}


#############################################################
######             Import/Export Operators             ######
#############################################################


class WBS_OT_wmo_import(bpy.types.Operator):
    """Load WMO mesh data"""
    bl_idname = "import_mesh.wmo"
    bl_label = "Import WMO"
    bl_options = {'UNDO', 'REGISTER'}

    filepath: StringProperty(
        subtype='FILE_PATH',
        )

    filter_glob: StringProperty(
        default="*.wmo",
        options={'HIDDEN'}
        )

    import_lights: BoolProperty(
        name="Import lights",
        description="Import WMO lights to scene",
        default=True,
        )

    import_doodads: BoolProperty(
        name="Import doodads",
        description='Import WMO doodads to scene',
        default=True
    )

    import_fogs: BoolProperty(
        name="Import fogs",
        description="Import WMO fogs to scene",
        default=True,
        )

    group_objects: BoolProperty(
        name="Group objects",
        description="Group all objects of this WMO on import",
        default=False,
        )

    def execute(self, context):
        import_wmo_to_blender_scene(self.filepath, self.import_doodads, self.import_lights,
                                    self.import_fogs, self.group_objects)
        context.scene.wow_scene.type = 'WMO'
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class WBS_OT_wmo_export(bpy.types.Operator, ExportHelper):
    """Save WMO mesh data"""
    bl_idname = "export_mesh.wmo"
    bl_label = "Export WMO"
    bl_options = {'PRESET', 'REGISTER'}

    filename_ext = ".wmo"

    filter_glob: StringProperty(
        default="*.wmo",
        options={'HIDDEN'}
    )

    export_method: EnumProperty(
        name='Export Method',
        description='Partial export if the scene was exported before and was not critically modified',
        items=[('FULL', 'Full', ''),
               ('PARTIAL', 'Partial', '')
               ]
    )

    export_selected: BoolProperty(
        name="Export selected objects",
        description="Export only selected objects on the scene",
        default=False,
        )


    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'export_method', text='', expand=True)

        if self.export_method == 'FULL':
            layout.prop(self, 'export_selected')


    def execute(self, context):
        if context.scene and context.scene.wow_scene.type == 'WMO':

            if self.export_method == 'PARTIAL' and context.scene.wow_wmo_root_elements.is_update_critical:
                self.report({'ERROR'}, 'Partial export is not available. The changes are critical.')
                return {'CANCELLED'}

            export_wmo_from_blender_scene(self.filepath, self.export_selected, self.export_method)
            return {'FINISHED'}

        self.report({'ERROR'}, 'Invalid scene type.')
        return {'CANCELLED'}


class WBS_OT_m2_import(bpy.types.Operator):
    """Load M2 data"""
    bl_idname = "import_mesh.m2"
    bl_label = "Import M2"
    bl_options = {'UNDO', 'REGISTER'}

    filepath: StringProperty(
        subtype='FILE_PATH',
        )

    filter_glob: StringProperty(
        default="*.m2",
        options={'HIDDEN'}
        )

    load_textures: BoolProperty(
        name="Fetch textures",
        description="Automatically fetch textures from game data",
        default=True,
        )

    def execute(self, context):
        import_m2(int(context.scene.wow_scene.version), self.filepath, self.load_textures)
        context.scene.wow_scene.type = 'M2'
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class WBS_OT_m2_export(bpy.types.Operator, ExportHelper):
    """Save M2 mesh data"""
    bl_idname = "export_mesh.m2"
    bl_label = "Export M2"
    bl_options = {'PRESET', 'REGISTER'}

    filename_ext = ".m2"

    filter_glob: StringProperty(
        default="*.m2",
        options={'HIDDEN'}
    )

    export_selected: BoolProperty(
        name="Export selected objects",
        description="Export only selected objects on the scene",
        default=False,
        )

    version: EnumProperty(
        name="Version",
        description="Version of World of Warcraft",
        items=[('264', 'WOTLK', "")],
        default='264'
    )

    autofill_textures: BoolProperty(
        name="Fill texture paths",
        description="Automatically assign texture paths based on texture filenames",
        default=True
        )

    def execute(self, context):
        if context.scene and context.scene.wow_scene.type == 'M2':
            export_m2(int(context.scene.wow_scene.version), self.filepath, self.export_selected, self.autofill_textures)
            return {'FINISHED'}

        self.report({'ERROR'}, 'Invalid scene type.')
