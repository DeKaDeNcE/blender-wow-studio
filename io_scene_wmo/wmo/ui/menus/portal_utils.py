from bpy.types import Menu
from .... import ui_icons


class VIEW3D_MT_wmo_portal_actions(Menu):
    bl_label = "Portal Actions"

    def draw(self, context):

        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("scene.wow_set_portal_dir_alg", text='Set portal direction',
                     icon_value=ui_icons['WOW_STUDIO_APPLY_DIRECTION'])
        pie.operator("scene.wow_bake_portal_relations", text='Bake portal relations',
                     icon_value=ui_icons['WOW_STUDIO_APPLY_RELATIONS'])
