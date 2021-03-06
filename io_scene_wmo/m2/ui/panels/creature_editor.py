import os

import bpy

from ....utils.misc import load_game_data


###############################
## Items callbacks
###############################

def get_creature_model_data(self, context):
    game_data = load_game_data()
    creature_model_data_db = game_data.db_files_client.CreatureModelData

    cr_model_data_entries = [('None', 'None', '')]
    model_path = os.path.splitext(context.scene.wow_scene.game_path.lower())[0]
    for record in creature_model_data_db.records:
        if os.path.splitext(record.ModelPath.lower())[0] == model_path:
            cr_model_data_entries.append((str(record.ID), 'ModelDataEntry_{}'.format(record.ID), ""))
    return cr_model_data_entries


def get_creature_display_infos(self, context):
    game_data = load_game_data()
    creature_display_info_db = game_data.db_files_client.CreatureDisplayInfo

    cr_display_infos = [('None', 'None', '')]
    cr_model_data = int(context.scene.wow_m2_creature.CreatureModelData)
    for record in creature_display_info_db.records:
        if record.Model == cr_model_data:
            cr_display_infos.append((str(record.ID), 'CreatureDisplayInfoEntry_{}'.format(record.ID), ""))

    return cr_display_infos


def get_char_races(self, context):
    game_data = load_game_data()
    chr_races_db = game_data.db_files_client.ChrRaces

    return [(str(record.ID), record.clientFileString, '') for record in chr_races_db.records]


###############################
## Update callbacks
###############################

def load_display_info_properties(self, context):
    game_data = load_game_data()
    creature_display_info_db = game_data.db_files_client.CreatureDisplayInfo
    record = creature_display_info_db[int(context.scene.wow_m2_creature.CreatureDisplayInfo)]

    context.scene.wow_m2_creature.DisplaySound = record.Sound
    context.scene.wow_m2_creature.DisplayScale = record.Scale
    context.scene.wow_m2_creature.DisplayTexture1 = record.Texture1
    context.scene.wow_m2_creature.DisplayTexture2 = record.Texture2
    context.scene.wow_m2_creature.DisplayTexture3 = record.Texture3
    context.scene.wow_m2_creature.DisplayPortraitTextureName = record.PortraitTextureName
    context.scene.wow_m2_creature.ExtraDisplayInformation = record.ExtraDisplayInformation


def load_display_extra_properties(self, context):
    game_data = load_game_data()
    creature_display_info_extra_db = game_data.db_files_client.CreatureDisplayInfoExtra
    record = creature_display_info_extra_db[int(context.scene.wow_m2_creature.ExtraDisplayInformation)]

    if record:
        context.scene.wow_m2_creature.DisplayExtraRace = str(record.Race)
        context.scene.wow_m2_creature.DisplayExtraGender = str(record.Gender)
        context.scene.wow_m2_creature.DisplayExtraSkinColor = record.SkinColor
        context.scene.wow_m2_creature.DisplayExtraFaceType = record.FaceType
        context.scene.wow_m2_creature.DisplayExtraHairType = record.HairType
        context.scene.wow_m2_creature.DisplayExtraHairStyle = record.HairStyle
        context.scene.wow_m2_creature.DisplayExtraBeardStyle = record.BeardStyle
        context.scene.wow_m2_creature.DisplayExtraHelm = record.Helm
        context.scene.wow_m2_creature.DisplayExtraShoulder = record.Shoulder
        context.scene.wow_m2_creature.DisplayExtraShirt = record.Shirt
        context.scene.wow_m2_creature.DisplayExtraCuirass = record.Cuirass
        context.scene.wow_m2_creature.DisplayExtraBelt = record.Belt
        context.scene.wow_m2_creature.DisplayExtraLegs = record.Legs
        context.scene.wow_m2_creature.DisplayExtraBoots = record.Boots
        context.scene.wow_m2_creature.DisplayExtraWrist = record.Wrist
        context.scene.wow_m2_creature.DisplayExtraGloves = record.Gloves
        context.scene.wow_m2_creature.DisplayExtraTabard = record.Tabard
        context.scene.wow_m2_creature.DisplayExtraCape = record.Cape
        context.scene.wow_m2_creature.DisplayExtraCanEquip = record.CanEquip
        context.scene.wow_m2_creature.DisplayExtraTexture = record.Texture

    elif int(context.scene.wow_m2_creature.ExtraDisplayInformation):
        context.scene.wow_m2_creature.ExtraDisplayInformation = 0


###############################
## User Interface
###############################

#### Pop-up dialog ####

class M2_OT_creature_editor_dialog(bpy.types.Operator):
    bl_idname = 'scene.wow_creature_editor_toggle'
    bl_label = 'WoW M2 Creature Editor'

    @classmethod
    def poll(cls, context):
        return context.scene is not None and context.scene.wow_scene.type == 'M2'

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        split = layout.split(factor=0.5)
        col = split.column()
        col1 = split.column()

        if not context.scene.wow_scene.game_path:
            col.label(text='Model path is unknown.', icon='ERROR')
            return

        col.label(text='Model data:')
        col.prop(context.scene.wow_m2_creature, 'CreatureModelData', text='')
        col.separator()

        if context.scene.wow_m2_creature.CreatureModelData != 'None':
            col1.label(text='Display Info:')
            col1.prop(context.scene.wow_m2_creature, 'CreatureDisplayInfo', text='')

            if context.scene.wow_m2_creature.CreatureDisplayInfo != 'None':
                col1.label(text='Settings:', icon='SETTINGS')
                box = col1.box()
                box.prop(context.scene.wow_m2_creature, 'DisplaySound')
                box.prop(context.scene.wow_m2_creature, 'DisplayScale')

                box.separator()
                box.operator('scene.wow_creature_load_textures',
                             text='Load all textures',
                             icon='APPEND_BLEND').LoadAll = True

                row = box.row(align=True)
                row.prop(context.scene.wow_m2_creature, 'DisplayTexture1')
                op = row.operator('scene.wow_creature_load_textures', text='', icon='APPEND_BLEND')
                op.LoadAll = False
                op.Path = context.scene.wow_m2_creature.DisplayTexture1
                op.TexNum = 11

                row = box.row(align=True)
                row.prop(context.scene.wow_m2_creature, 'DisplayTexture2')
                op = row.operator('scene.wow_creature_load_textures', text='', icon='APPEND_BLEND')
                op.LoadAll = False
                op.Path = context.scene.wow_m2_creature.DisplayTexture2
                op.TexNum = 12

                row = box.row(align=True)
                row.prop(context.scene.wow_m2_creature, 'DisplayTexture3')
                op = row.operator('scene.wow_creature_load_textures', text='', icon='APPEND_BLEND')
                op.LoadAll = False
                op.Path = context.scene.wow_m2_creature.DisplayTexture3
                op.TexNum = 13

                box.prop(context.scene.wow_m2_creature, 'DisplayPortraitTextureName')
                box.prop(context.scene.wow_m2_creature, 'ExtraDisplayInformation')

                if context.scene.wow_m2_creature.ExtraDisplayInformation != 0:
                    box.label(text='Settings:', icon='SETTINGS')
                    box1 = box.box()

                    box1.prop(context.scene.wow_m2_creature, 'DisplayExtraCanEquip')
                    box1.prop(context.scene.wow_m2_creature, 'DisplayExtraTexture')
                    box1.prop(context.scene.wow_m2_creature, 'DisplayExtraRace')
                    box1.prop(context.scene.wow_m2_creature, 'DisplayExtraGender')
                    box1.prop(context.scene.wow_m2_creature, 'DisplayExtraSkinColor')
                    box1.prop(context.scene.wow_m2_creature, 'DisplayExtraFaceType')
                    box1.prop(context.scene.wow_m2_creature, 'DisplayExtraHairType')
                    box1.prop(context.scene.wow_m2_creature, 'DisplayExtraHairStyle')
                    box1.prop(context.scene.wow_m2_creature, 'DisplayExtraBeardStyle')

                    box1.label(text='Equipment:')
                    row = box1.row()
                    row.prop(context.scene.wow_m2_creature, 'DisplayExtraHelm')
                    row = box1.row()
                    row.prop(context.scene.wow_m2_creature, 'DisplayExtraShoulder')
                    row = box1.row()
                    row.prop(context.scene.wow_m2_creature, 'DisplayExtraShirt')
                    row = box1.row()
                    row.prop(context.scene.wow_m2_creature, 'DisplayExtraCuirass')
                    row = box1.row()
                    row.prop(context.scene.wow_m2_creature, 'DisplayExtraBelt')
                    row = box1.row()
                    row.prop(context.scene.wow_m2_creature, 'DisplayExtraLegs')
                    row = box1.row()
                    row.prop(context.scene.wow_m2_creature, 'DisplayExtraBoots')
                    row = box1.row()
                    row.prop(context.scene.wow_m2_creature, 'DisplayExtraWrist')
                    row = box1.row()
                    row.prop(context.scene.wow_m2_creature, 'DisplayExtraGloves')
                    row = box1.row()
                    row.prop(context.scene.wow_m2_creature, 'DisplayExtraTabard')
                    row = box1.row()
                    row.prop(context.scene.wow_m2_creature, 'DisplayExtraCape')

        else:
            col.label(text='No display info found.', icon='PMARKER_ACT')

    def check(self, context):  # redraw the popup window
        return True


class WowM2CreaturePropertyGroup(bpy.types.PropertyGroup):

    # DBs

    CreatureModelData:  bpy.props.EnumProperty(
        name='Model data',
        description='CreatureModelData.db entry',
        items=get_creature_model_data
    )

    CreatureDisplayInfo:  bpy.props.EnumProperty(
        name='Creature display',
        description='CreatureDisplayInfo.db entry',
        items=get_creature_display_infos,
        update=load_display_info_properties
    )

    ExtraDisplayInformation:  bpy.props.IntProperty(
        name='Display extra',
        description='Applies only to NPCs with character model (hair/facial feature/... and equipment settings). Not used for creatures.',
        default=0,
        min=0,
        update=load_display_extra_properties
    )

    # Creature display info

    DisplaySound:  bpy.props.IntProperty(
        name='Sound',
        description='If 0 - CreatureModelData information is used. Otherwise, overrides generic model settings for this displayID.',
        default=0,
        min=0
    )

    DisplayScale:  bpy.props.FloatProperty(
        name='Scale',
        description='Default scale. Stacks (by multiplying) with other scale settings (in creature_template, applied auras...).',
        default=1.0,
        min=0.0
    )

    DisplayTexture1:  bpy.props.StringProperty(
        name='Texture 1',
        description='First creature skin texture. Texture must be in the same folder as the model.',
    )

    DisplayTexture2:  bpy.props.StringProperty(
        name='Texture 2',
        description='Second creature skin texture. Texture must be in the same folder as the model.',
    )

    DisplayTexture3:  bpy.props.StringProperty(
        name='Texture 3',
        description='Third creature skin texture. Texture must be in the same folder as the model.',
    )

    DisplayPortraitTextureName:  bpy.props.StringProperty(
        name='Portrait Texture',
        description='Holding an icon like INV_Misc_Food_59. Only on a few.',
    )

    # Creature display info extra

    DisplayExtraRace:  bpy.props.EnumProperty(
        name='Race',
        description='The race this NPC belongs to',
        items=get_char_races
    )

    DisplayExtraGender:  bpy.props.EnumProperty(
        name='Gender',
        description='0 for Male, 1 for Female',
        items=[('0', 'Male', ''),
               ('1', 'Female', '')]
    )

    DisplayExtraSkinColor:  bpy.props.IntProperty(
        name='Skin Color',
        default=0,
        min=0
    )

    DisplayExtraFaceType:  bpy.props.IntProperty(
        name='Face type',
        default=0,
        min=0
    )

    DisplayExtraHairType:  bpy.props.IntProperty(
        name='Hair type',
        default=0,
        min=0
    )

    DisplayExtraHairStyle:  bpy.props.IntProperty(
        name='Hairstyle',
        default=0,
        min=0
    )

    DisplayExtraBeardStyle:  bpy.props.IntProperty(
        name='Beard',
        default=0,
        min=0
    )

    DisplayExtraHelm:  bpy.props.IntProperty(
        name='Helm',
        default=0,
        min=0
    )

    DisplayExtraShoulder:  bpy.props.IntProperty(
        name='Shoulder',
        default=0,
        min=0
    )

    DisplayExtraShirt:  bpy.props.IntProperty(
        name='Shirt',
        default=0,
        min=0
    )

    DisplayExtraCuirass:  bpy.props.IntProperty(
        name='Cuirass',
        default=0,
        min=0
    )

    DisplayExtraBelt:  bpy.props.IntProperty(
        name='Belt',
        default=0,
        min=0
    )

    DisplayExtraLegs:  bpy.props.IntProperty(
        name='Legs',
        default=0,
        min=0
    )

    DisplayExtraBoots:  bpy.props.IntProperty(
        name='Boots',
        default=0,
        min=0
    )

    DisplayExtraWrist:  bpy.props.IntProperty(
        name='Wrist',
        default=0,
        min=0
    )

    DisplayExtraGloves:  bpy.props.IntProperty(
        name='Gloves',
        default=0,
        min=0
    )

    DisplayExtraTabard:  bpy.props.IntProperty(
        name='Tabard',
        default=0,
        min=0
    )

    DisplayExtraCape:  bpy.props.IntProperty(
        name='Cape',
        default=0,
        min=0
    )

    DisplayExtraCanEquip:  bpy.props.BoolProperty(
        name='Can equip',
        default=True,
    )

    DisplayExtraTexture:  bpy.props.StringProperty(
        name='Texture'
    )



###############################
## Operators
###############################

class M2_OT_creature_editor_load_textures(bpy.types.Operator):
    bl_idname = 'scene.wow_creature_load_textures'
    bl_label = 'Load creature skins'
    bl_description = 'Loads skin textures on import .M2'
    bl_options = {'REGISTER', 'INTERNAL'}

    Path:  bpy.props.StringProperty()
    TexNum:  bpy.props.IntProperty()
    LoadAll:  bpy.props.BoolProperty()

    @staticmethod
    def load_skin_texture(context, path, tex_type):
        from ....ui import get_addon_prefs
        cache_dir = get_addon_prefs().cache_dir_path
        game_data = load_game_data()
        game_data.extract_textures_as_png(cache_dir, [path + '.blp'])
        img = None
        try:
            img = bpy.data.images.load(os.path.join(cache_dir, path + '.png'))
        except RuntimeError:
            pass

        if img:
            for obj in filter(lambda o: o.type == 'MESH' and not o.wow_m2_geoset.collision_mesh, context.scene.objects):
                for i, material in enumerate(obj.data.materials):
                    if material.active_texture.wow_m2_texture.texture_type == str(tex_type):
                        material.active_texture.image = img

                        uv = obj.data.uv_layers.active
                        for poly in obj.data.polygons:
                            if poly.material_index == i:
                                uv.data[poly.index].image = img

    def execute(self, context):
        if not context.scene.wow_scene.game_path:
            self.report({'ERROR'}, 'Path to model is unknown.')
            return {'CANCELLED'}

        base_path = os.path.dirname(context.scene.wow_scene.game_path)

        if self.LoadAll:
            if context.scene.wow_m2_creature.DisplayTexture1:
                self.load_skin_texture(context,
                                       os.path.join(base_path, context.scene.wow_m2_creature.DisplayTexture1),
                                       11)

            if context.scene.wow_m2_creature.DisplayTexture2:
                self.load_skin_texture(context,
                                       os.path.join(base_path, context.scene.wow_m2_creature.DisplayTexture2),
                                       12)

            if context.scene.wow_m2_creature.DisplayTexture3:
                self.load_skin_texture(context,
                                       os.path.join(base_path, context.scene.wow_m2_creature.DisplayTexture3),
                                       13)

        else:
            if self.Path:
                self.load_skin_texture(context, os.path.join(base_path, self.Path), self.TexNum)
            else:
                self.report({'ERROR'}, "No texture to load.")

        self.report({'INFO'}, "Successfully loaded creature skins.")
        return {'FINISHED'}


def register():
    bpy.types.Scene.wow_m2_creature = bpy.props.PointerProperty(type=WowM2CreaturePropertyGroup)


def unregister():
    del bpy.types.Scene.wow_m2_creature
