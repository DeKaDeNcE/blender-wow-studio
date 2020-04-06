from bpy.types import Menu


class VIEW3D_MT_wmo_group_actions(Menu):
    bl_label = "Group Actions"

    def draw(self, context):

        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("scene.wow_wmo_generate_materials", text='Generate materials', icon='MATERIAL_DATA')
        pie.operator("scene.wow_fill_textures", text='Fill texture paths', icon='SEQ_SPLITVIEW')
        pie.operator("scene.wow_quick_collision", text='Quick collision', icon='MOD_TRIANGULATE')
