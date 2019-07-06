import bpy
import bmesh
import traceback
import os

from bpy.types import Menu
from functools import partial

from ....ui import get_addon_prefs
from ....utils.misc import load_game_data
from ...utils.wmv import wmv_get_last_texture
from ...utils.materials import load_texture
from ...render import update_wmo_mat_node_tree, load_wmo_shader_dependencies


class WMO_OT_assign_material(bpy.types.Operator):
    bl_idname = "mesh.wow_assign_material"
    bl_label = "Assign material"
    bl_description = "Assign selected material to selected polygons"
    bl_options = {'UNDO', 'REGISTER', 'INTERNAL'}

    mat_name: bpy.props.StringProperty(default='Material')
    action: bpy.props.EnumProperty(
        name='Action',
        items=(('NAME', "", ""),
               ('NEW', "", "")),
        default='NAME'
    )

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'MESH' and context.object.mode == 'EDIT'

    def execute(self, context):

        try:
            obj = context.object
            mesh = obj.data

            mat = bpy.data.materials[self.mat_name] if self.action == 'NAME' else bpy.data.materials.new(self.mat_name)

            if self.action == 'NEW':
                texture = context.scene.wow_last_selected_images[-1].pointer
                mat.wow_wmo_material.path = texture.wow_wmo_texture.path
                mat.wow_wmo_material.diff_texture_1 = texture

                load_wmo_shader_dependencies()
                update_wmo_mat_node_tree(mat)

                slot = context.scene.wow_wmo_root_components.materials.add()
                slot.pointer = mat
                mat.wow_wmo_material.enabled = True

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

        except:
            traceback.print_exc()
            self.report({'ERROR'}, "Setting material failed.")
            return {'CANCELLED'}

        return {'FINISHED'}


class WMO_OT_import_texture_from_filepath(bpy.types.Operator):
    bl_idname = "mesh.wow_import_texture_filepath"
    bl_label = "Import texture from filepath"
    bl_description = "Import a texture file from filepath and create material for it."
    bl_options = {'UNDO', 'REGISTER', 'INTERNAL'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'MESH' and context.object.mode == 'EDIT'

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):

        game_data = load_game_data()

        if not game_data:
            self.report({'ERROR'}, "Importing texture failed. Game data was not loaded.")
            return {'CANCELLED'}

        path = game_data.traverse_file_path(bpy.path.abspath(self.filepath))

        if not path:
            self.report({'INFO'}, "Texture was not found in WoW file system. Set the path in material manually.")

        texture = bpy.data.images.load(bpy.path.abspath(self.filepath))
        texture.wow_wmo_texture.path = path if path else self.filepath
        texture.name = os.path.basename(self.filepath)

        mat = bpy.data.materials.new(name=texture.name)
        mat.wow_wmo_material.diff_texture_1 = texture

        load_wmo_shader_dependencies()
        update_wmo_mat_node_tree(mat)

        slot = context.scene.wow_wmo_root_components.materials.add()
        slot.pointer = mat
        mat.wow_wmo_material.enabled = True

        global display_material_select_pie
        display_material_select_pie = False
        context.scene.wow_cur_image = texture
        display_material_select_pie = True

        bpy.ops.mesh.wow_assign_material(mat_name=mat.name, action='NAME')

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

        load_wmo_shader_dependencies()
        update_wmo_mat_node_tree(mat)

        slot = context.scene.wow_wmo_root_components.materials.add()
        slot.pointer = mat
        mat.wow_wmo_material.enabled = True

        global display_material_select_pie
        display_material_select_pie = False
        context.scene.wow_cur_image = texture
        display_material_select_pie = True

        bpy.ops.mesh.wow_assign_material(mat_name=mat.name, action='NAME')

        return {'FINISHED'}


class WMO_OT_select_texture_from_recent(bpy.types.Operator):
    bl_idname = "mesh.wow_select_texture_from_recent"
    bl_label = "Select texture"
    bl_description = "Select recently used texture"
    bl_options = {'REGISTER', 'INTERNAL'}

    index: bpy.props.IntProperty()

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'MESH' and context.object.mode == 'EDIT'

    def execute(self, context):

        context.scene.wow_cur_image = context.scene.wow_last_selected_images[self.index].pointer

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

        if len(context.scene.wow_last_selected_images):
            box = pie.box()
            row = box.row()
            for i, texture in enumerate(context.scene.wow_last_selected_images):
                col = row.column()
                col.template_icon(row.icon(texture.pointer), scale=5.0)
                op = col.operator("mesh.wow_select_texture_from_recent", text='', icon='ADD')
                op.index = i

        pie.operator("mesh.wow_import_texture_wmv", text='Import from WMV', icon='ADD')
        pie.operator("mesh.wow_import_texture_filepath", text='Import from file', icon='ADD')


def timer(override):
    bpy.ops.wm.call_menu_pie(override, name="VIEW3D_MT_select_material")


def handle_last_selected_images(scene):
    # clear invalid items
    while True:
        for i, tex in enumerate(scene.wow_last_selected_images):
            if not tex.pointer:
                scene.wow_last_selected_images.remove(i)
                break
        else:
            break

    # avoid duplicates and truncate the collection
    for i, tex in enumerate(scene.wow_last_selected_images):

        if tex.pointer == scene.wow_cur_image:
            scene.wow_last_selected_images.remove(i)
            break
    else:
        if len(scene.wow_last_selected_images) > 5:
            scene.wow_last_selected_images.remove(0)

    slot = scene.wow_last_selected_images.add()
    slot.pointer = scene.wow_cur_image
    scene.wow_cur_image = None

display_material_select_pie = True
def set_image(self, value):
    if self.wow_cur_image:
        global display_material_select_pie

        handle_last_selected_images(self)

        if display_material_select_pie:
            bpy.app.timers.register(partial(timer, bpy.context.copy()), first_interval=0.0)


def get_more_materials_list(self, context):
    scene = bpy.context.scene
    materials = list([mat for mat in scene.wow_wmo_root_components.materials
                      if mat.pointer
                      and mat.pointer.wow_wmo_material.diff_texture_1 == scene.wow_last_selected_images[-1].pointer])

    return list([(mat.name, mat.name, mat.name, 'MATERIAL', i) for i, mat in enumerate(materials[5:])]) if len(
        materials) > 6 else []


def update_more_materials(self, context):
    if self.more_materials:
        bpy.ops.mesh.wow_assign_material(mat_name=self.more_materials, action='NAME')


class VIEW3D_MT_select_material(Menu):
    bl_label = "Select material"

    def draw(self, context):

        scene = bpy.context.scene
        layout = self.layout
        pie = layout.menu_pie()

        op = pie.operator("mesh.wow_assign_material", text='New material', icon='ADD')
        op.action = 'NEW'

        materials = list([mat for mat in scene.wow_wmo_root_components.materials
                          if mat.pointer
                          and mat.pointer.wow_wmo_material.diff_texture_1 == scene.wow_last_selected_images[-1].pointer])

        if len(materials) > 6:
            for mat in materials[:5]:
                op = pie.operator("mesh.wow_assign_material", text=mat.pointer.name, icon='MATERIAL')
                op.mat_name = mat.pointer.name
                op.action = 'NAME'

            box = pie.box()
            box.prop(scene, "more_materials", text='More', icon='MATERIAL')

        else:
            for mat in materials:
                op = pie.operator("mesh.wow_assign_material", text=mat.pointer.name, icon='MATERIAL')
                op.mat_name = mat.pointer.name
                op.action = 'NAME'


class ImagePointerPropertyGroup(bpy.types.PropertyGroup):

    pointer: bpy.props.PointerProperty(type=bpy.types.Image)

addon_keymaps = []
def register():
    bpy.types.Scene.wow_cur_image = bpy.props.PointerProperty(type=bpy.types.Image, update=set_image)
    bpy.types.Scene.wow_last_selected_images = bpy.props.CollectionProperty(type=ImagePointerPropertyGroup)

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
    del bpy.types.Scene.wow_last_selected_images
    del bpy.types.Scene.wow_cur_image

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

