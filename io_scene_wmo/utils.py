import bpy

from io import BytesIO
from .pywowlib.archives.mpq.wow import WoWFileData
from .pywowlib.wdbx.wdbc import DBFilesClient, DBCFile
from .pywowlib.wdbx.definitions.wotlk import AnimationData


def parse_bitfield(bitfield, last_flag=0x1000):

    flags = set()
    bit = 1
    while bit <= last_flag:
        if bitfield & bit:
            flags.add(str(bit))
        bit <<= 1

    return flags


def get_material_viewport_image(material):
    """ Get viewport image assigned to a material """
    for i in range(3):
        try:
            img = material.texture_slots[3 - i].texture.image
            return img
        except:
            pass
    return None


def load_game_data():
    if not hasattr(bpy, 'wow_game_data'):
        addon_preferences = bpy.context.user_preferences.addons[__package__].preferences
        bpy.wow_game_data = WoWFileData(addon_preferences.wow_path, addon_preferences.blp_path)

        if not bpy.wow_game_data.files:
            raise ChildProcessError("WoW game data is not loaded. Check settings.")

        bpy.db_files_client = DBFilesClient()

        # list of all DB tables that we need to load
        anim_data_dbc = DBCFile(AnimationData, 'AnimationData')
        anim_data_dbc.read(BytesIO(bpy.wow_game_data.read_file('DBFilesClient\\AnimationData.dbc')))
        bpy.db_files_client.add(anim_data_dbc)

    return bpy.wow_game_data
