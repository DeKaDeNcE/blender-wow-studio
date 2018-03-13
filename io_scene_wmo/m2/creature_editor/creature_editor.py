import bpy
import os

from ...utils import load_game_data


###############################
## Items callbacks
###############################

def get_creature_model_data(self, context):
    game_data = load_game_data()
    creature_model_data_db = game_data.db_files_client.CreatureModelData

    cr_model_data_entries = [('None', 'None', '')]
    model_path = os.path.splitext(context.scene.WowScene.GamePath.lower())[0]
    for record in creature_model_data_db.records:
        if os.path.splitext(record.ModelPath.lower())[0] == model_path:
            cr_model_data_entries.append((str(record.ID), 'ModelDataEntry_{}'.format(record.ID), ""))
    return cr_model_data_entries


def get_creature_display_infos(self, context):
    game_data = load_game_data()
    creature_display_info_db = game_data.db_files_client.CreatureDisplayInfo

    cr_display_infos = [('None', 'None', '')]
    cr_model_data = int(context.scene.WowM2Creature.CreatureModelData)
    for record in creature_display_info_db.records:
        if record.Model == cr_model_data:
            cr_display_infos.append((str(record.ID), 'CreatureDisplayInfoEntry_{}'.format(record.ID), ""))

    return cr_display_infos


###############################
## Update callbacks
###############################

def load_display_info_properties(self, context):
    game_data = load_game_data()
    creature_display_info_db = game_data.db_files_client.CreatureDisplayInfo
    record = creature_display_info_db[int(context.scene.WowM2Creature.CreatureDisplayInfo)]

    context.scene.WowM2Creature.DisplaySound = record.Sound
    context.scene.WowM2Creature.DisplayScale = record.Scale
    context.scene.WowM2Creature.DisplayTexture1 = record.Texture1
    context.scene.WowM2Creature.DisplayTexture2 = record.Texture2
    context.scene.WowM2Creature.DisplayTexture3 = record.Texture3
    context.scene.WowM2Creature.PortraitTextureName = record.PortraitTextureName


class WoWM2CreatureEditorPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = 'objectmode'
    bl_category = 'M2 Extra'
    bl_label = 'Creature Editor'

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        if not context.scene.WowScene.GamePath:
            col.label('Model path is unknown.', icon='ERROR')
            return

        col.label('Model data:')
        col.prop(context.scene.WowM2Creature, 'CreatureModelData', text='')
        col.separator()

        if context.scene.WowM2Creature.CreatureModelData != 'None':
            col1 = col.column()
            col1.label('Display Info:')
            col1.prop(context.scene.WowM2Creature, 'CreatureDisplayInfo', text='')

            if context.scene.WowM2Creature.CreatureDisplayInfo != 'None':
                col1.label('Settings:', icon='SETTINGS')
                box = col1.box()
                col1 = box.column()
                col1.prop(context.scene.WowM2Creature, 'DisplaySound')
                col1.prop(context.scene.WowM2Creature, 'DisplayScale')

                col1.separator()
                col1.operator('scene.wow_creature_load_textures',
                              text='Load all textures',
                              icon='APPEND_BLEND').LoadAll = True

                row = col1.row(align=True)
                row.prop(context.scene.WowM2Creature, 'DisplayTexture1')
                op = row.operator('scene.wow_creature_load_textures', text='', icon='APPEND_BLEND')
                op.LoadAll = False
                op.Path = context.scene.WowM2Creature.DisplayTexture1
                op.TexNum = 11

                row = col1.row(align=True)
                row.prop(context.scene.WowM2Creature, 'DisplayTexture2')
                op = row.operator('scene.wow_creature_load_textures', text='', icon='APPEND_BLEND')
                op.LoadAll = False
                op.Path = context.scene.WowM2Creature.DisplayTexture2
                op.TexNum = 12

                row = col1.row(align=True)
                row.prop(context.scene.WowM2Creature, 'DisplayTexture3')
                op = row.operator('scene.wow_creature_load_textures', text='', icon='APPEND_BLEND')
                op.LoadAll = False
                op.Path = context.scene.WowM2Creature.DisplayTexture3
                op.TexNum = 13

                col1.prop(context.scene.WowM2Creature, 'PortraitTextureName')

        else:
            col.label('No display info found.', icon='PMARKER_ACT')

    @classmethod
    def poll(cls, context):
        return context.scene is not None and context.scene.WowScene.Type == 'M2'


class WowM2CreaturePropertyGroup(bpy.types.PropertyGroup):

    CreatureModelData = bpy.props.EnumProperty(
        name='Model data',
        description='CreatureModelData.db entry',
        items=get_creature_model_data
    )

    CreatureDisplayInfo = bpy.props.EnumProperty(
        name='Creature display',
        description='CreatureDisplayInfo.db entry',
        items=get_creature_display_infos,
        update=load_display_info_properties
    )

    DisplaySound = bpy.props.IntProperty(
        name='Sound',
        description='If 0 - CreatureModelData information is used. Otherwise, overrides generic model settings for this displayID.',
        default=0,
        min=0
    )

    DisplayScale = bpy.props.FloatProperty(
        name='Scale',
        description='Default scale. Stacks (by multiplying) with other scale settings (in creature_template, applied auras...).',
        default=1.0,
        min=0.0
    )

    DisplayTexture1 = bpy.props.StringProperty(
        name='Texture 1',
        description='First creature skin texture. Texture must be in the same folder as the model.',
    )

    DisplayTexture2 = bpy.props.StringProperty(
        name='Texture 2',
        description='Second creature skin texture. Texture must be in the same folder as the model.',
    )

    DisplayTexture3 = bpy.props.StringProperty(
        name='Texture 3',
        description='Third creature skin texture. Texture must be in the same folder as the model.',
    )

    PortraitTextureName = bpy.props.StringProperty(
        name='Portrait Texture',
        description='Holding an icon like INV_Misc_Food_59. Only on a few.',
    )


###############################
## Operators
###############################

class CreatureEditorLoadTextures(bpy.types.Operator):
    bl_idname = 'scene.wow_creature_load_textures'
    bl_label = 'Load creature skins'
    bl_description = 'Loads skin textures on import .M2'
    bl_options = {'REGISTER', 'INTERNAL'}

    Path = bpy.props.StringProperty()
    TexNum = bpy.props.IntProperty()
    LoadAll = bpy.props.BoolProperty()

    @staticmethod
    def load_skin_texture(context, path, tex_type):
        from ...ui import get_addon_prefs
        cache_dir = get_addon_prefs().cache_dir_path
        game_data = load_game_data()
        game_data.extract_textures_as_png(cache_dir, [path + '.blp'])
        img = None
        try:
            img = bpy.data.images.load(os.path.join(cache_dir, path + '.png'))
        except RuntimeError:
            pass

        if img:
            for obj in filter(lambda o: o.type == 'MESH' and not o.WowM2Geoset.CollisionMesh, context.scene.objects):
                for i, material in enumerate(obj.data.materials):
                    if material.active_texture.WowM2Texture.TextureType == str(tex_type):
                        material.active_texture.image = img

                        uv = obj.data.uv_textures.active
                        for poly in obj.data.polygons:
                            if poly.material_index == i:
                                uv.data[poly.index].image = img

    def execute(self, context):
        if not context.scene.WowScene.GamePath:
            self.report({'ERROR'}, 'Path to model is unknown.')
            return {'CANCELLED'}

        base_path = os.path.dirname(context.scene.WowScene.GamePath)

        if self.LoadAll:
            if context.scene.WowM2Creature.DisplayTexture1:
                self.load_skin_texture(context,
                                       os.path.join(base_path, context.scene.WowM2Creature.DisplayTexture1),
                                       11)

            if context.scene.WowM2Creature.DisplayTexture2:
                self.load_skin_texture(context,
                                       os.path.join(base_path, context.scene.WowM2Creature.DisplayTexture2),
                                       12)

            if context.scene.WowM2Creature.DisplayTexture3:
                self.load_skin_texture(context,
                                       os.path.join(base_path, context.scene.WowM2Creature.DisplayTexture3),
                                       13)

        else:
            if self.Path:
                self.load_skin_texture(context, os.path.join(base_path, self.Path) + '.png', self.TexNum)
            else:
                self.report({'ERROR'}, "No texture to load.")

        self.report({'INFO'}, "Successfully loaded creature skins.")
        return {'FINISHED'}


def register_wow_m2_creature_editor_properties():
    bpy.types.Scene.WowM2Creature = bpy.props.PointerProperty(type=WowM2CreaturePropertyGroup)


def unregister_wow_m2_creature_editor_properties():
    bpy.types.Scene.WowM2Creature = None


def register_creature_editor():
    register_wow_m2_creature_editor_properties()


def unregister_creature_editor():
    unregister_wow_m2_creature_editor_properties()
