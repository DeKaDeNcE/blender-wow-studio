import bpy
import bmesh
import traceback

from bpy.types import Menu
from functools import partial

from ....ui import get_addon_prefs
from ....utils.misc import load_game_data
from ...utils.wmv import wmv_get_last_texture
from ...utils.materials import load_texture
from ...render import update_wmo_mat_node_tree


class WMO_OT_assign_material(bpy.types.Operator):
    bl_idname = "mesh.wow_assign_material"
    bl_label = "Assign material"
    bl_description = "Assign selected material to selected polygons"
    bl_options = {'UNDO', 'REGISTER', 'INTERNAL'}

    mat_name: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'MESH' and context.object.mode == 'EDIT'

    def execute(self, context):

        try:
            obj = context.object
            mesh = obj.data

            mat = bpy.data.materials[self.mat_name]

            mat_index = -1

            for i, m in enumerate(mesh.materials):
                if m is mat:
                    mat_index = i
                    break

            if mat_index < 0:
                mat_index = len(mesh.materials)
                mesh.materials.append(mat)

            bm = bmesh.from_edit_mesh(mesh)

            for face in bm.faces:
                if face.select:
                    face.material_index = mat_index

            bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)

            for poly in mesh.polygons:
                poly.material_index = mat_index

        except:
            traceback.print_exc()
            self.report({'ERROR'}, "Setting material failed.")
            return {'CANCELLED'}

        return {'FINISHED'}


class WMO_OT_import_texture_from_wmv(bpy.types.Operator):
    bl_idname = "mesh.wow_import_texture_wmv"
    bl_label = "Import texture from WoWModelViewer"
    bl_description = "Import a texture file from WMV and create material for it."
    bl_options = {'UNDO', 'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'MESH' and context.object.mode == 'EDIT'

    def execute(self, context):

        addon_prefs = get_addon_prefs()
        game_data = load_game_data()

        if not game_data:
            self.report({'ERROR'}, "Importing texture failed. Game data was not loaded.")
            return {'CANCELLED'}

        path = wmv_get_last_texture()

        if not path:
            self.report({'ERROR'}, "WMV log does not contain any texture paths.")
            return {'CANCELLED'}

        game_data.extract_textures_as_png(addon_prefs.cache_dir_path, (path,))
        texture = load_texture({}, path, addon_prefs.cache_dir_path)

        mat = bpy.data.materials.new(name=path.split('\\')[-1][:-4] + '.PNG')
        mat.wow_wmo_material.diff_texture_1 = texture
        update_wmo_mat_node_tree(mat)

        slot = context.scene.wow_wmo_root_components.materials.add()
        slot.pointer = mat
        mat.wow_wmo_material.enabled = True

        bpy.ops.mesh.wow_assign_material(mat_name=mat.name)

        return {'FINISHED'}


class VIEW3D_MT_select_texture(Menu):
    bl_label = "Select texture"

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'MESH' and context.object.mode == 'EDIT'


    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        box = pie.box()
        box.label(text='Select texture', icon='VIEWZOOM')
        row = box.row()
        row.scale_x = 0.5
        row.scale_y = 0.5
        row.template_ID_preview(context.scene, 'wow_cur_image', hide_buttons=True, rows=5, cols=5)

        pie.operator("mesh.wow_import_texture_wmv", text='Import from WMV', icon='ADD')


def timer(override):
    bpy.ops.wm.call_menu_pie(override, name="VIEW3D_PIE_select_materials")


def set_image(self, value):
    if self.wow_cur_image:
        self.wow_cur_image_old = self.wow_cur_image
        self.wow_cur_image = None

        win = bpy.context.window
        scr = win.screen
        areas3d = [area for area in scr.areas if area.type == 'VIEW_3D']
        region = [region for region in areas3d[0].regions if region.type == 'WINDOW']

        override = {'window': win,
                    'screen': scr,
                    'area': areas3d[0],
                    'region': region,
                    'scene': bpy.context.scene,
                    }

        bpy.app.timers.register(partial(timer, override), first_interval=0.0)


def get_more_materials_list(self, context):
    scene = bpy.context.scene
    materials = list([mat for mat in scene.wow_wmo_root_components.materials if
                      mat.pointer and mat.pointer.wow_wmo_material.diff_texture_1 == scene.wow_cur_image_old])

    return list([(mat.name, mat.name, mat.name, 'MATERIAL', i) for i, mat in enumerate(materials[5:])]) if len(
        materials) > 6 else []


def update_more_materials(self, context):
    if self.more_materials:
        bpy.ops.mesh.wow_assign_material(mat_name=self.more_materials)


class VIEW3D_MT_select_material(Menu):
    bl_label = "Select materials"

    def draw(self, context):
        scene = bpy.context.scene
        layout = self.layout
        pie = layout.menu_pie()

        materials = list([mat for mat in scene.wow_wmo_root_components.materials if
                          mat.pointer and mat.pointer.wow_wmo_material.diff_texture_1 == scene.wow_cur_image_old])

        if len(materials) > 6:
            for mat in materials[:5]:
                op = pie.operator("mesh.wow_assign_material", text=mat.pointer.name, icon='MATERIAL')
                op.mat_name = mat.pointer.name

            box = pie.box()
            box.prop(scene, "more_materials", text='More', icon='MATERIAL')

        else:
            for mat in materials:
                op = pie.operator("mesh.wow_assign_material", text=mat.pointer.name, icon='MATERIAL')
                op.mat_name = mat.pointer.name

addon_keymaps = []
def register():
    bpy.types.Scene.wow_cur_image = bpy.props.PointerProperty(type=bpy.types.Image, update=set_image)
    bpy.types.Scene.wow_cur_image_old = bpy.props.PointerProperty(type=bpy.types.Image)

    bpy.types.Scene.more_materials = bpy.props.EnumProperty(  name='More'
                                                            , items=get_more_materials_list
                                                            , update=update_more_materials
                                                           )

    # handle the keymap
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D', region_type='WINDOW')
    kmi = km.keymap_items.new("wm.call_menu_pie", type='Q', value='PRESS', shift=True)
    kmi.properties.name = "VIEW3D_MT_select_texture"
    addon_keymaps.append((km, kmi))

def unregister():
    del bpy.types.Scene.more_materials
    del bpy.types.Scene.wow_cur_image_old
    del bpy.types.Scene.wow_cur_image

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

