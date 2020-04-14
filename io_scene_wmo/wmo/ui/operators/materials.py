import bpy
import bmesh

from ...render import load_wmo_shader_dependencies, update_wmo_mat_node_tree
from ....utils.misc import resolve_texture_path
from ...ui.handlers import DepsgraphLock


class WMO_OT_generate_materials(bpy.types.Operator):
    bl_idname = "scene.wow_wmo_generate_materials"
    bl_label = "Generate WMO Materials"
    bl_description = "Generate WMO materials."
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.scene.wow_scene.type == 'WMO'

    def execute(self, context):
        if 'MO_WMOShader' not in bpy.data.node_groups:
            load_wmo_shader_dependencies(True)

        materials = bpy.data.materials

        if context.selected_objects:
            materials = []
            for obj in context.selected_objects:
                if not obj.wow_wmo_group.enabled:
                    continue

                materials.extend(obj.data.materials)

        for mat in materials:

            tex = None
            if mat.use_nodes:

                for node in mat.node_tree.nodes:
                    if node.bl_idname == 'ShaderNodeTexImage':
                        tex = node.image
                        break

            update_wmo_mat_node_tree(mat)

            with DepsgraphLock():

                if mat.name not in context.scene.wow_wmo_root_elements.materials:
                    mat.wow_wmo_material.self_pointer = mat

                    mat.wow_wmo_material.diff_texture_1 = tex

                    slot = context.scene.wow_wmo_root_elements.materials.add()
                    slot.pointer = mat

        return {'FINISHED'}


class WMO_OT_material_assign(bpy.types.Operator):
    bl_idname = "object.wow_wmo_material_assign"
    bl_label = "Assign WMO Material"
    bl_description = "Assign WMO material to selected faces."
    bl_options = {'UNDO', 'REGISTER', 'INTERNAL'}

    def execute(self, context):

        mesh = context.view_layer.objects.active.data
        bm = bmesh.from_edit_mesh(mesh)
        mat = context.scene.wow_wmo_root_elements.materials[context.scene.wow_wmo_root_elements.cur_material]

        if not mat.pointer:
            self.report({'ERROR'}, "Cannot assign an empty material")
            return {'CANCELLED'}

        mat_index = mesh.materials.find(mat.pointer.name)

        if mat_index < 0:
            mat_index = len(mesh.materials)
            mesh.materials.append(mat.pointer)

        for face in bm.faces:
            if not face.select:
                continue

            face.material_index = mat_index

        bmesh.update_edit_mesh(mesh)

        return {'FINISHED'}


class WMO_OT_material_select(bpy.types.Operator):
    bl_idname = "object.wow_wmo_material_select"
    bl_label = "Select WMO Material"
    bl_description = "Select WMO material to selected faces."
    bl_options = {'UNDO', 'REGISTER', 'INTERNAL'}

    def execute(self, context):

        mesh = context.view_layer.objects.active.data
        bm = bmesh.from_edit_mesh(mesh)
        mat = context.scene.wow_wmo_root_elements.materials[context.scene.wow_wmo_root_elements.cur_material]

        if not mat.pointer:
            self.report({'ERROR'}, "Cannot select an empty material")
            return {'CANCELLED'}

        mat_index = mesh.materials.find(mat.pointer.name)

        for face in bm.faces:
            if face.material_index == mat_index:
                face.select = True

        bmesh.update_edit_mesh(mesh)

        return {'FINISHED'}


class WMO_OT_material_deselect(bpy.types.Operator):
    bl_idname = "object.wow_wmo_material_deselect"
    bl_label = "Deselect WMO Material"
    bl_description = "Deselect WMO material to selected faces."
    bl_options = {'UNDO', 'REGISTER', 'INTERNAL'}

    def execute(self, context):

        mesh = context.view_layer.objects.active.data
        bm = bmesh.from_edit_mesh(mesh)
        mat = context.scene.wow_wmo_root_elements.materials[context.scene.wow_wmo_root_elements.cur_material]

        if not mat.pointer:
            self.report({'ERROR'}, "Cannot deselect an empty material")
            return {'CANCELLED'}

        mat_index = mesh.materials.find(mat.pointer.name)

        for face in bm.faces:
            if face.material_index == mat_index:
                face.select = False

        bmesh.update_edit_mesh(mesh)

        return {'FINISHED'}


class WMO_OT_fill_textures(bpy.types.Operator):
    bl_idname = 'scene.wow_fill_textures'
    bl_label = 'Fill textures'
    bl_description = "Fill Texture 1 field of WoW materials with paths from applied image"
    bl_options = {'REGISTER'}

    def execute(self, context):

        for ob in filter(lambda o: o.wow_wmo_group.enabled, bpy.context.selected_objects):
            mesh = ob.data
            for material in mesh.materials:
                if not material.wow_wmo_material.enabled:
                    continue

                texture = material.wow_wmo_material.diff_texture_1

                if not texture or texture.type != 'IMAGE':
                    continue

                texture.wow_wmo_texture.path = resolve_texture_path(texture.filepath)

        self.report({'INFO'}, "Done filling texture paths")

        return {'FINISHED'}
