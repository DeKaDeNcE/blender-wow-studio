from bpy.types import Menu


class VIEW3D_MT_wmo_doodad_actions(Menu):
    bl_label = "Doodad Actions"

    def draw(self, context):

        layout = self.layout
        pie = layout.menu_pie()

        pie.operator("scene.wow_doodads_bake_color", text='Bake Color', icon='SHADING_RENDERED')
        pie.operator("scene.wow_doodad_set_color", text='Set Color', icon='SHADING_SOLID')

        op = pie.operator("scene.wow_doodad_set_template_action", text='Template Select', icon='PMARKER_ACT')
        op.action = 'SELECT'

        op = pie.operator("scene.wow_doodad_set_template_action", text='Template Replace', icon='FILE_REFRESH')
        op.action = 'REPLACE'

        op = pie.operator("scene.wow_doodad_set_template_action", text='Template Delete', icon='CANCEL')
        op.action = 'DELETE'

        op = pie.operator("scene.wow_doodad_set_template_action", text='Template Rotate', icon='LOOP_FORWARDS')
        op.action = 'ROTATE'

        op = pie.operator("scene.wow_doodad_set_template_action", text='Template Resize', icon='FULLSCREEN_ENTER')
        op.action = 'RESIZE'
