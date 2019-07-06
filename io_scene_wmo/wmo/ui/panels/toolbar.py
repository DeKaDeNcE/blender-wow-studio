import bpy
from ..enums import *

__reload_order_index__ = 0


def update_wow_visibility(self, context):
    values = self.wow_visibility

    for obj in self.objects:
        if 'wow_hide' not in obj:
            obj['wow_hide'] = obj.hide_viewport

        if obj['wow_hide'] != obj.hide_viewport:
            continue

        if obj.type == "MESH":
            if obj.wow_wmo_group.enabled:
                if obj.wow_wmo_group.place_type == '8':
                    obj.hide_viewport = '0' not in values
                else:
                    obj.hide_viewport = '1' not in values

                if obj.wow_wmo_group.collision_mesh:
                    col = obj.wow_wmo_group.collision_mesh

                    if 'wow_hide' not in col:
                        col['wow_hide'] = col.hide_viewport

                    if col['wow_hide'] != col.hide_viewport:
                        continue

                    col.hide_viewport = '6' not in values
                    col['wow_hide'] = col.hide_viewport

            elif obj.wow_wmo_portal.enabled:
                obj.hide_viewport = '2' not in values
            elif obj.wow_wmo_fog.enabled:
                obj.hide_viewport = '3' not in values
            elif obj.wow_wmo_liquid.enabled:
                obj.hide_viewport = '4' not in values
        elif obj.type == "LAMP" and obj.data.wow_wmo_light.enabled:
            obj.hide_viewport = '5' not in values

        obj['wow_hide'] = obj.hide_viewport


def update_liquid_flags(self, context):
    value = self.wow_liquid_flags

    water = bpy.context.view_layer.objects.active
    mesh = water.data
    if water.wow_wmo_liquid.enabled:
        layer = mesh.vertex_colors.get("flag_" + value)

        if layer:
            layer.active = True
            mesh.use_paint_mask = True
        else:
            layer = mesh.vertex_colors.new("flag_" + value)
            layer.active = True


def get_doodad_sets(self, context):
    has_global = False
    doodad_set_objects = set()
    doodad_sets = []

    for obj in bpy.context.scene.objects:
        if obj.wow_wmo_doodad.enabled and obj.parent:
            if obj.parent.name != "Set_$DefaultGlobal":
                doodad_set_objects.add(obj.parent)
            else:
                has_global = True

    for index, obj in enumerate(sorted(doodad_set_objects, key=lambda x: x.name), 1 + has_global):
        doodad_sets.append((obj.name, obj.name, "", 'SCENE_DATA', index))

    doodad_sets.insert(0, ("None", "No set", "", 'X', 0))
    if has_global:
        doodad_sets.insert(1, ("Set_$DefaultGlobal", "Set_$DefaultGlobal", "", 'WORLD', 1))

    return doodad_sets


def switch_doodad_set(self, context):
    set = self.wow_doodad_visibility

    for obj in bpy.context.scene.objects:
        if obj.wow_wmo_doodad.enabled:
            if obj.parent:
                name = obj.parent.name
                obj.hide_viewport = set == "None" or name != set and name != "Set_$DefaultGlobal"
            else:
                obj.hide_viewport = True


class WMO_PT_tools_object_mode_display(bpy.types.Panel):
    bl_label = 'Display'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = 'objectmode'
    bl_category = 'WMO'

    def draw(self, context):
        layout = self.layout.split()
        col = layout.column(align=True)
        col_row = col.row()
        col_row.column(align=True).prop(context.scene, "wow_visibility")
        col_col = col_row.column(align=True)
        col_col.operator("scene.wow_wmo_select_entity", text='', icon='VIEWZOOM').entity = 'Outdoor'
        col_col.operator("scene.wow_wmo_select_entity", text='', icon='VIEWZOOM').entity = 'Indoor'
        col_col.operator("scene.wow_wmo_select_entity", text='', icon='VIEWZOOM').entity = 'wow_wmo_portal'
        col_col.operator("scene.wow_wmo_select_entity", text='', icon='VIEWZOOM').entity = 'wow_wmo_fog'
        col_col.operator("scene.wow_wmo_select_entity", text='', icon='VIEWZOOM').entity = 'wow_wmo_liquid'
        col_col.operator("scene.wow_wmo_select_entity", text='', icon='VIEWZOOM').entity = 'wow_wmo_light'
        col_col.operator("scene.wow_wmo_select_entity", text='', icon='VIEWZOOM').entity = 'Collision'

        if not bpy.context.scene.wow_wmo_root.mods_sets:
            box2_row2 = col.row()
            box2_row2.prop(context.scene, "wow_doodad_visibility", expand=False)
            box2_row2.operator("scene.wow_wmo_select_entity", text='', icon='VIEWZOOM').entity = 'wow_wmo_doodad'

    @classmethod
    def poll(cls, context):
        return context.scene is not None and context.scene.wow_scene.type == 'WMO'


class WMO_PT_tools_panel_object_mode_add_to_scene(bpy.types.Panel):
    bl_label = 'Add to scene'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = 'objectmode'
    bl_category = 'WMO'

    def draw(self, context):
        layout = self.layout.split()

        has_sets = True if bpy.context.scene.wow_wmo_root.mods_sets else False
        game_data_loaded = hasattr(bpy, "wow_game_data") and bpy.wow_game_data.files

        col = layout.column(align=True)

        box1 = col.box().column(align=True)
        box1_col = box1.column(align=True)
        box1_row1 = box1_col.row(align=True)
        box1_row1.operator("scene.wow_add_fog", text='Fog', icon_value=ui_icons['WOW_STUDIO_FOG_ADD'])
        box1_row1.operator("scene.wow_add_water", text='Water', icon_value=ui_icons['WOW_STUDIO_WATER_ADD'])
        box1_row2 = box1_col.row(align=True)
        box1_row3 = box1_col.row(align=True)
        if game_data_loaded:
            if not has_sets:
                box1_row2.operator("scene.wow_wmo_import_doodad_from_wmv", text='M2',
                                   icon_value=ui_icons['WOW_STUDIO_DOODADS_ADD'])
                box1_row2.operator("scene.wow_import_last_wmo_from_wmv", text='WMO',
                                   icon_value=ui_icons['WOW_STUDIO_WMO_ADD'])
            box1_row3.operator("scene.wow_import_adt_scene", text='ADT', icon_value=ui_icons['WOW_STUDIO_ADT_ADD'])
            box1_row3.operator("scene.wow_add_scale_reference", text='Scale',
                               icon_value=ui_icons['WOW_STUDIO_SCALE_ADD'])

        else:
            box1_col.operator("scene.wow_add_scale_reference", text='Scale',
                              icon_value=ui_icons['WOW_STUDIO_SCALE_ADD'])

    @classmethod
    def poll(cls, context):
        return context.scene is not None and context.scene.wow_scene.type == 'WMO'


class WMO_PT_tools_object_mode_actions(bpy.types.Panel):
    bl_label = 'Actions'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = 'objectmode'
    bl_category = 'WMO'

    def draw(self, context):
        layout = self.layout.split()
        col = layout.column(align=True)

        col.label(text="Global:")
        col.operator("scene.wow_fix_material_duplicates", text='Fix material duplicates', icon='ASSET_MANAGER')
        col.operator("scene.wow_wmo_generate_materials", text='Generate materials', icon='MATERIAL')

        if bpy.context.selected_objects:
            box = col.box()
            box.label(text="Selected:")
            box.menu("WMO_MT_convert_operators", text="Convert selected")
            box.label(text="Apply:")
            box_col = box.column(align=True)
            box_col.operator("scene.wow_quick_collision", text='Quick collision', icon='STYLUS_PRESSURE')
            box_col.operator("scene.wow_fill_textures", text='Fill texture paths', icon='FILE_IMAGE')
            box_col.operator("scene.wow_set_portal_dir_alg", text='Set portal dir.',
                             icon_value=ui_icons['WOW_STUDIO_APPLY_DIRECTION'])
            box_col.operator("scene.wow_bake_portal_relations", text='Bake portal rels.',
                             icon_value=ui_icons['WOW_STUDIO_APPLY_RELATIONS'])

            if context.object and context.object.wow_wmo_liquid.enabled:
                box_col.operator("wow.liquid_edit_mode", text='Edit liquid')

    @classmethod
    def poll(cls, context):
        return context.scene is not None and context.scene.wow_scene.type == 'WMO'


class WMO_PT_tools_object_mode_doodads(bpy.types.Panel):
    bl_label = 'Doodads'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = 'objectmode'
    bl_category = 'WMO'

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
                and not bpy.context.scene.wow_wmo_root.mods_sets and bpy.context.selected_objects)

    def draw(self, context):
        layout = self.layout.split()
        col = layout.column(align=True)

        has_sets = True if bpy.context.scene.wow_wmo_root.mods_sets else False
        box = col.box()
        box_col2 = box.column(align=True)

        if not has_sets:
            box_col2.operator("scene.wow_doodad_set_add", text='Add to doodadset', icon='ADD')
            box_col2.operator("scene.wow_doodads_bake_color", text='Bake color', icon='GROUP_VCOL')
            box_col2.operator("scene.wow_doodad_set_color", text='Set color', icon='COLOR')
            box_col2.operator("scene.wow_doodad_set_template_action", text='Template action', icon='FORCE_MAGNETIC')
        else:
            box_col2.operator("scene.wow_clear_preserved_doodad_sets", text='Clear doodad sets', icon='CANCEL')


class WMO_MT_convert_operators(bpy.types.Menu):
    bl_label = "Convert"
    bl_options = {'REGISTER'}

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.operator("scene.wow_selected_objects_to_group", text='To WMO group', icon='OBJECT_DATA')
        col.operator("scene.wow_selected_objects_to_wow_material", text='To WMO material', icon='SMOOTH')
        col.operator("scene.wow_selected_objects_to_portals", text='To WMO portal', icon='MOD_MIRROR')
        col.operator("scene.wow_texface_to_material", text='Texface to material', icon='TEXTURE_DATA')

    @classmethod
    def poll(cls, context):
        return context.scene is not None and context.scene.wow_scene.type == 'WMO'


class WMO_MT_mesh_wow_components_add(bpy.types.Menu):
    bl_label = "WoW"
    bl_options = {'REGISTER'}

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.operator("scene.wow_add_fog", text='Fog', icon_value=ui_icons['WOW_STUDIO_FOG_ADD'])
        col.operator("scene.wow_add_water", text='Water', icon_value=ui_icons['WOW_STUDIO_WATER_ADD'])
        col.operator("scene.wow_add_scale_reference", text='Scale', icon_value=ui_icons['WOW_STUDIO_SCALE_ADD'])

        if hasattr(bpy, "wow_game_data") and bpy.wow_game_data.files:
            col.operator("scene.wow_wmo_import_doodad_from_wmv", text='M2',
                         icon_value=ui_icons['WOW_STUDIO_DOODADS_ADD'])
            col.operator("scene.wow_import_last_wmo_from_wmv", text='WMO', icon_value=ui_icons['WOW_STUDIO_WMO_ADD'])
            col.operator("scene.wow_import_adt_scene", text='ADT', icon_value=ui_icons['WOW_STUDIO_ADT_ADD'])

    @classmethod
    def poll(cls, context):
        return context.scene is not None and context.scene.wow_scene.type == 'WMO'


def wow_components_add_menu_item(self, context):
    self.layout.menu("WMO_MT_mesh_wow_components_add", icon_value=ui_icons['WOW_STUDIO_WOW_ADD'])


class WMO_PT_tools_liquid_flags(bpy.types.Panel):
    bl_label = 'Liquid Flags'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = 'vertexpaint'
    bl_category = 'WMO'

    def draw(self, context):
        layout = self.layout.split()

        col = layout.column()

        col.label(text="Flags")
        col.prop(context.scene, "wow_liquid_flags", expand=True)

        col.label(text="Actions")
        col.operator("scene.wow_mliq_change_flags", text='Add flag', icon='MOD_SOFT').Action = "ADD"
        col.operator("scene.wow_mliq_change_flags", text='Fill all', icon='OUTLINER_OB_LATTICE').Action = "ADD_ALL"
        col.operator("scene.wow_mliq_change_flags", text='Clear flag', icon='LATTICE_DATA').Action = "CLEAR"
        col.operator("scene.wow_mliq_change_flags", text='Clear all', icon='MOD_LATTICE').Action = "CLEAR_ALL"

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
                and context.object is not None
                and context.object.data is not None
                and isinstance(context.object.data, bpy.types.Mesh)
                and context.object.wow_wmo_liquid.enabled
                )


def render_viewport_toggles_right(self, context):
    if context.scene.wow_scene.type == 'WMO':
        layout = self.layout
        row = layout.row(align=True)
        row.popover(  panel="WMO_PT_tools_object_mode_display"
                    , text=''
                    , icon_value=ui_icons['WOW_STUDIO_WMO']
                   )


def register():
    bpy.types.Scene.wow_visibility = bpy.props.EnumProperty(
        items=[
            ('0', "Outdoor", "Display outdoor groups", 'OBJECT_DATA', 0x1),
            ('1', "Indoor", "Display indoor groups", 'MOD_SUBSURF', 0x2),
            ('2', "Portals", "Display portals", ui_icons['WOW_STUDIO_CONVERT_PORTAL'], 0x4),
            ('3', "Fogs", "Display fogs", ui_icons['WOW_STUDIO_FOG'], 0x8),
            ('4', "Liquids", "Display liquids", 'MOD_WAVE', 0x10),
            ('5', "Lights", "Display lights", 'OUTLINER_OB_LAMP', 0x20),
            ('6', "Collision", "Display collision", 'STYLUS_PRESSURE', 0x40)],
        options={'ENUM_FLAG'},
        default={'0', '1', '2', '3', '4', '5', '6'},
        update=update_wow_visibility
    )

    bpy.types.Scene.wow_liquid_flags = bpy.props.EnumProperty(
        items=[
            ('0x1', "Flag 0x01", "Switch to this flag", 'MOD_SOFT', 0),
            ('0x2', "Flag 0x02", "Switch to this flag", 'MOD_SOFT', 1),
            ('0x4', "Flag 0x04", "Switch to this flag", 'MOD_SOFT', 2),
            ('0x8', "Invisible", "Switch to this flag", 'RESTRICT_VIEW_OFF', 3),
            ('0x10', "Flag 0x10", "Switch to this flag", 'MOD_SOFT', 4),
            ('0x20', "Flag 0x20", "Switch to this flag", 'MOD_SOFT', 5),
            ('0x40', "Flag 0x40", "Switch to this flag", 'MOD_SOFT', 6),
            ('0x80', "Flag 0x80", "Switch to this flag", 'MOD_SOFT', 7)],
        default='0x1',
        update=update_liquid_flags
    )

    bpy.types.Scene.wow_doodad_visibility = bpy.props.EnumProperty(
        name="",
        description="Switch doodad sets",
        items=get_doodad_sets,
        update=switch_doodad_set
    )

    bpy.types.VIEW3D_MT_add.prepend(wow_components_add_menu_item)
    bpy.types.VIEW3D_HT_header.append(render_viewport_toggles_right)


def unregister():
    del bpy.types.Scene.wow_visibility
    del bpy.types.Scene.wow_liquid_flags
    del bpy.types.Scene.wow_doodad_visibility

    bpy.types.VIEW3D_MT_add.remove(wow_components_add_menu_item)
    bpy.types.VIEW3D_MT_add.remove(render_viewport_toggles_right)