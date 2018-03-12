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

    cr_display_infos = []
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

        if context.scene.WowM2Creature.CreatureModelData != 'None':
            col1 = col.column()
            col1.label('Display Info:')
            col1.prop(context.scene.WowM2Creature, 'CreatureDisplayInfo', text='')
            box = col1.box()
            col1 = box.column()
            col1.prop(context.scene.WowM2Creature, 'DisplaySound')

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


def register_wow_m2_creature_editor_properties():
    bpy.types.Scene.WowM2Creature = bpy.props.PointerProperty(type=WowM2CreaturePropertyGroup)


def unregister_wow_m2_creature_editor_properties():
    bpy.types.Scene.WowM2Creature = None


def register_creature_editor():
    register_wow_m2_creature_editor_properties()


def unregister_creature_editor():
    unregister_wow_m2_creature_editor_properties()
