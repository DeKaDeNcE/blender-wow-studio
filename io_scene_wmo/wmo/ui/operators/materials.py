import bpy
import os

from ...render import load_wmo_shader_dependencies, update_wmo_mat_node_tree
from ....ui import get_addon_prefs
from ....utils.misc import load_game_data


class WMO_OT_reload_textures_from_cache(bpy.types.Operator):
    bl_idname = "scene.wow_wmo_reload_textures_from_cache"
    bl_label = "Reload WMO textures"
    bl_description = "Reload textures from WoW cache."
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.scene.wow_scene.type == 'WMO'

    def execute(self, context):

        game_data = load_game_data()
        addon_prefs = get_addon_prefs()
        texture_dir = addon_prefs.cache_dir_path

        for material in bpy.data.materials:
            if not material.wow_wmo_material.enabled:
                continue

            for tex_slot in material.texture_slots:

                if tex_slot and tex_slot.texture and tex_slot.texture.type == 'IMAGE':
                    game_data.extract_textures_as_png(texture_dir, [material.wow_wmo_material.texture1])

                    image = bpy.data.images.load(
                        os.path.join(texture_dir, os.path.splitext(material.wow_wmo_material.texture1)[0] + '.png'),
                        check_existing=True)
                    tex_slot.texture.image = image
                    tex_slot.texture.image.gl_load()
                    tex_slot.texture.image.update()

        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return {'FINISHED'}

class WMO_OT_generate_materials(bpy.types.Operator):
    bl_idname = "scene.wow_wmo_generate_materials"
    bl_label = "Generate WMO Textures"
    bl_description = "Generate WMO materials."
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.scene.wow_scene.type == 'WMO'

    def execute(self, context):
        load_wmo_shader_dependencies(True)
        for mat in bpy.data.materials:
            update_wmo_mat_node_tree(mat)

        return {'FINISHED'}


class WMO_OT_fix_material_duplicates(bpy.types.Operator):
    bl_idname = "scene.wow_fix_material_duplicates"
    bl_label = "Fix material duplicates"
    bl_description = "Fix duplicated materials in WMO groups."
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        material_duplicates = {}

        for material in bpy.data.materials:

            name = material.name.split('.png')[0]
            if '.png' in material.name:
                name += '.png'
            material_duplicates.setdefault(name, []).append(material.name)

        duplicate_count = 0
        for source, duplicates in material_duplicates.items():
            source_props = bpy.data.materials[source].wow_wmo_material

            for duplicate in duplicates:
                dupli_props = bpy.data.materials[duplicate].wow_wmo_material
                if source != duplicate \
                and source_props.Shader == dupli_props.Shader \
                and source_props.TerrainType == dupli_props.TerrainType \
                and source_props.BlendingMode == dupli_props.BlendingMode \
                and source_props.Texture1 == dupli_props.Texture1 \
                and source_props.EmissiveColor[:] == dupli_props.EmissiveColor[:] \
                and source_props.Flags == dupli_props.Flags \
                and source_props.Texture2 == dupli_props.Texture2 \
                and source_props.DiffColor[:] == dupli_props.DiffColor[:]:
                    bpy.ops.view3d.replace_material(matorg=duplicate, matrep=source)
                    duplicate_count += 1

        self.report({'INFO'}, "Cleared {} duplicated materials".format(duplicate_count))

        return {'FINISHED'}


class WMO_OT_fill_textures(bpy.types.Operator):
    bl_idname = 'scene.wow_fill_textures'
    bl_label = 'Fill textures'
    bl_description = """Fill Texture 1 field of WoW materials with paths from applied image. """
    bl_options = {'REGISTER'}

    def execute(self, context):

        game_data = load_game_data()
        for ob in bpy.context.selected_objects:
            mesh = ob.data
            for material in mesh.materials:

                img = None
                for i in range(3):
                    try:
                        img = material.texture_slots[3 - i].texture.image
                    except:
                        pass

                if img and not material.wow_wmo_material.texture1:

                    path = (os.path.splitext(bpy.path.abspath(img.filepath))[0] + ".blp", "")
                    rest_path = ""

                    while True:
                        path = os.path.split(path[0])

                        if not path[1]:
                            print("\nTexture <<{}>> not found.".format(img.filepath))
                            break

                        rest_path = os.path.join(path[1], rest_path)
                        rest_path = rest_path[:-1] if rest_path.endswith('\\') else rest_path

                        if os.name != 'nt':
                            rest_path_n = rest_path.replace('/', '\\')
                        else:
                            rest_path_n = rest_path

                        rest_path_n = rest_path_n[:-1] if rest_path_n.endswith('\\') else rest_path_n

                        if game_data.has_file(rest_path_n)[0]:
                            material.wow_wmo_material.texture1 = rest_path_n
                            break

            self.report({'INFO'}, "Done filling texture paths")

        return {'FINISHED'}
