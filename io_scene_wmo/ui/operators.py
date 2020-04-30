import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy_extras.io_utils import ExportHelper

from ..wmo.import_wmo import import_wmo_to_blender_scene
from ..wmo.export_wmo import export_wmo_from_blender_scene
from ..m2.import_m2 import import_m2
from ..m2.export_m2 import export_m2
from ..utils.misc import load_game_data

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
            if bpy.wow_game_data.files:
                for storage, type_ in bpy.wow_game_data.files:
                    if type_:
                        storage.close()

            delattr(bpy, "wow_game_data")

        load_game_data()

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
        version = int(context.scene.wow_scene.version)

        import_wmo_to_blender_scene(self.filepath, version)
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
        items=[('FULL', 'Full', 'Full'),
               ('PARTIAL', 'Partial', 'Partial')
               ]
    )

    export_selected: BoolProperty(
        name="Export selected objects",
        description="Export only selected objects on the scene",
        default=False,
        )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'export_method', expand=True)

        if self.export_method == 'FULL':
            layout.prop(self, 'export_selected')

    def execute(self, context):
        if context.scene and context.scene.wow_scene.type == 'WMO':

            if self.export_method == 'PARTIAL' and context.scene.wow_wmo_root_elements.is_update_critical:
                self.report({'ERROR'}, 'Partial export is not available. The changes are critical.')
                return {'CANCELLED'}

            version = int(context.scene.wow_scene.version)

            export_wmo_from_blender_scene(self.filepath, version, self.export_selected, self.export_method)
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

    def execute(self, context):
        import_m2(int(context.scene.wow_scene.version), self.filepath, True)
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


from ..addon_common.cookiecutter.cookiecutter import CookieCutter
from ..addon_common.common import ui

'''
Created on Dec 30, 2019

@author: Patrick
'''
'''
Copyright (C) 2018 CG Cookie
https://github.com/CGCookie/retopoflow
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import bpy
from ..addon_common.cookiecutter.cookiecutter import CookieCutter

from ..addon_common.common import ui
from ..addon_common.common.drawing import Drawing

from ..addon_common.common.boundvar import BoundInt, BoundFloat, BoundBool

# some settings container
options = {}
options["variable_1"] = 10.0
options["variable_3"] = True


# override this pass through to allow anything in 3dview to pass through
def in_region(reg, x, y):
    # first, check outside of area
    if x < reg.x: return False
    if y < reg.y: return False
    if x > reg.x + reg.width: return False
    if y > reg.y + reg.height: return False

    return True


class CookieCutter_UITest(CookieCutter, bpy.types.Operator):
    bl_idname = "view3d.cookiecutter_ui_test"
    bl_label = "CookieCutter UI Test (Example)"

    default_keymap = {
        'commit': 'RET',
        'cancel': 'ESC',
        'test': 'LEFTMOUSE'
    }

    # for this, checkout "polystrips_props.py'
    @property
    def variable_2_gs(self):
        return getattr(self, '_var_cut_count_value', 0)

    @variable_2_gs.setter
    def variable_2_gs(self, v):
        if self.variable_2 == v: return
        self.variable_2 = v
        # if self.variable_2.disabled: return

    ### Redefine/OVerride of defaults methods from CookieCutter ###
    def start(self):
        opts = {
            'pos': 9,
            'movable': True,
            'bgcolor': (0.2, 0.2, 0.2, 0.8),
            'padding': 0,
        }

        # some data storage, simple single variables for now
        # later, more coplex dictionaries or container class
        self.variable_1 = BoundFloat('''options['variable_1']''', min_value=0.5, max_value=15.5)
        self.variable_2 = BoundInt('''self.variable_2_gs''', min_value=0, max_value=10)
        self.variable_3 = BoundBool('''options['variable_3']''')

        self.setup_ui()

    # def update(self):
    # self.ui_action.set_label('Press: %s' % (','.join(self.actions.now_pressed.keys()),))

    def end_commit(self):
        pass

    def end_cancel(self):
        pass

    def end(self):  # happens after end_commit or end_cancel
        pass

    def should_pass_through(self, context, event):
        print(context.region.type)
        print(context.area.type)

        if context.area.type != "VIEW_3D":
            return True

        # first, check outside of area
        outside = False
        if event.mouse_x < context.area.x: outside = True
        if event.mouse_y < context.area.y: outside = True
        if event.mouse_x > context.area.x + context.area.width: outside = True
        if event.mouse_y > context.area.y + context.area.height: outside = True

        if outside:
            print('outside the 3DView area')
            return True

        # make sure we are in the window region, not the header, tools or UI
        for reg in context.area.regions:
            if in_region(reg, event.mouse_x, event.mouse_y) and reg.type != "WINDOW":
                print('in wrong region')
                return True


        return False

    ######## End Redefinitions from CookieCutter Class ###

    # typically, we would definte these somewhere else
    def tool_action(self):
        print('tool action')
        return

    def setup_ui(self):

        # go ahead and open these files
        # addon_common.common.ui
        # addon_common.cookiecutter.cookiecutter_ui

        # know that every CookieCutter instance has self.document upon startup
        # most of our ui elements are going to be children of self.document.body

        # we generate our UI elements using the methods in ui.py

        # we need to read ui_core, particulalry UI_Element

        # collapsible, and framed_dialog
        # first, know

        self.ui_main = ui.framed_dialog(label='ui.framed_dialog',
                                        resiable=None,
                                        resiable_x=True,
                                        resizable_y=False,
                                        closeable=True,
                                        moveable=True,
                                        hide_on_close=True,
                                        parent=self.document.body)

        # tools
        ui_tools = ui.div(id="tools", parent=self.ui_main)
        ui.button(label='ui.button', title='self.tool_action() method linked to button', parent=ui_tools,
                  on_mouseclick=self.tool_action)

        # create a collapsille container to hold a few variables
        container = ui.collapsible('ui.collapse container', parent=self.ui_main)

        i1 = ui.labeled_input_text(label='Sui.labeled_input_text',
                                   title='float property to BoundFLoat',
                                   value=self.variable_1)

        i2 = ui.labeled_input_text(label='ui.labled_input_text',
                                   title='integer property to BoundInt',
                                   value=self.variable_2)

        i3 = ui.input_checkbox(
            label='ui.input_checkbox',
            title='True/False property to BoundBool')

        container.builder([i1, i2, i3])

    @CookieCutter.FSM_State('main')
    def modal_main(self):
        Drawing.set_cursor('DEFAULT')

        if self.actions.pressed('test'):
            self.actions.pass_through = False
            print('aaaaaaaaaand action \n\n')
            return 'test'

        if self.actions.pressed('cancel'):
            print('cancelled')
            self.done(cancel=True)
            return 'cancel'

        if self.actions.pressed('commit'):
            print('committed')
            self.done()
            return 'finished'

    @CookieCutter.FSM_State('test')
    def modal_grab(self):
        Drawing.set_cursor('CROSSHAIR')

        self.actions.unuse('navigate')
        if self.actions.mousemove:
            print('action mousemove!')
            self.report({'INFO'}, "Applied")
            return 'test'  # can return nothing and stay in this state?

        if self.actions.released('test'):
            # self.lbl.set_label('finish action')
            print('finish action')
            return 'main'

    # there are no drawing methods for this example
    # this is all buttons and input wundows


class M2DrawingTest(bpy.types.Operator):
    bl_idname = "wm.render_test"
    bl_label = "M2 Render Test"

    def execute(self, context):

        import importlib
        from .. import render
        importlib.reload(render)

        dm = render.M2DrawingManager()
        dm.queue_for_drawing(bpy.context.view_layer.objects.active)

        return {'FINISHED'}

