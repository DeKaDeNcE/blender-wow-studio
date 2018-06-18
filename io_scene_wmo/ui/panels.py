import bpy
from .. import ui_icons


class WowScenePanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_label = "WoW Scene"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.scene.wow_scene, 'type')
        col.prop(context.scene.wow_scene, 'game_path')

    @classmethod
    def poll(cls, context):
        return context.scene is not None


class WowScenePropertyGroup(bpy.types.PropertyGroup):
    type = bpy.props.EnumProperty(
        name='Scene type',
        description='Sets up the UI to work with a specific WoW game format',
        items=(
            ('M2', 'M2', 'M2 model'),
            ('WMO', 'WMO', 'World Map Object (WMO)')    # TODO: verify module availability
            )
        )

    game_path = bpy.props.StringProperty(
        name='Game path',
        description='A path to the model in WoW filesystem.'
    )


def register_wow_scene_properties():
    bpy.types.Scene.wow_scene = bpy.props.PointerProperty(type=WowScenePropertyGroup)


def unregister_wow_scene_properties():
    del bpy.types.Scene.wow_scene


def render_top_bar(self, context):
    layout = self.layout
    row = layout.row(align=True)
    row.label('Scene:')
    row.prop(context.scene.wow_scene, 'type', text='')
    row.operator("scene.reload_wow_filesystem", text="", icon_value=ui_icons['WOW_STUDIO_RELOAD'])


menu_import_wmo = lambda self, ctx: self.layout.operator("import_mesh.wmo", text="WoW WMO (.wmo)")
menu_export_wmo = lambda self, ctx: self.layout.operator("export_mesh.wmo", text="WoW WMO (.wmo)")
menu_import_m2 = lambda self, ctx: self.layout.operator("import_mesh.m2", text="WoW M2 (.m2)")
menu_export_m2 = lambda self, ctx: self.layout.operator("export_mesh.m2", text="WoW M2 (.m2)")


def register_panels():
    register_wow_scene_properties()
    bpy.types.INFO_HT_header.append(render_top_bar)
    bpy.types.INFO_MT_file_import.append(menu_import_wmo)
    bpy.types.INFO_MT_file_import.append(menu_import_m2)
    bpy.types.INFO_MT_file_export.append(menu_export_wmo)
    bpy.types.INFO_MT_file_export.append(menu_export_m2)


def unregister_panels():
    unregister_wow_scene_properties()
    bpy.types.INFO_MT_file_import.remove(menu_import_wmo)
    bpy.types.INFO_MT_file_import.remove(menu_import_m2)
    bpy.types.INFO_MT_file_export.remove(menu_export_wmo)
    bpy.types.INFO_MT_file_export.remove(menu_export_m2)
    bpy.types.INFO_HT_header.remove(render_top_bar)
