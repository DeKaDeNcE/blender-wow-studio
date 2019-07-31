import bpy
from ..enums import *


class WMO_OT_add_scale(bpy.types.Operator):
    bl_idname = 'scene.wow_add_scale_reference'
    bl_label = 'Add scale'
    bl_description = 'Add a WoW scale prop'
    bl_options = {'REGISTER', 'UNDO'}

    ScaleType:  bpy.props.EnumProperty(
        name="Scale Type",
        description="Select scale reference type",
        items=[('HUMAN', "Human Scale (average)", ""),
               ('TAUREN', "Tauren Scale (thickest)", ""),
               ('TROLL', "Troll Scale (tallest)", ""),
               ('GNOME', "Gnome Scale (smallest)", "")
               ],
        default='HUMAN'
    )

    def execute(self, context):
        if self.ScaleType == 'HUMAN':
            bpy.ops.object.add(type='LATTICE')
            scale_obj = bpy.context.object
            scale_obj.name = "Human Scale"
            scale_obj.dimensions = (0.582, 0.892, 1.989)

        elif self.ScaleType == 'TAUREN':
            bpy.ops.object.add(type='LATTICE')
            scale_obj = bpy.context.object
            scale_obj.name = "Tauren Scale"
            scale_obj.dimensions = (1.663, 1.539, 2.246)

        elif self.ScaleType == 'TROLL':
            bpy.ops.object.add(type='LATTICE')
            scale_obj = bpy.context.object
            scale_obj.name = "Troll Scale"
            scale_obj.dimensions = (1.116, 1.291, 2.367)

        elif self.ScaleType == 'GNOME':
            bpy.ops.object.add(type='LATTICE')
            scale_obj = bpy.context.object
            scale_obj.name = "Gnome Scale"
            scale_obj.dimensions = (0.362, 0.758, 0.991)

        self.report({'INFO'}, "Successfully added " + self.ScaleType + " scale")
        return {'FINISHED'}


class WMO_OT_quick_collision(bpy.types.Operator):
    bl_idname = 'scene.wow_quick_collision'
    bl_label = 'Generate basic collision for selected objects'
    bl_description = 'Generate WoW collision equal to geometry of the selected objects'
    bl_options = {'REGISTER', 'UNDO'}

    NodeSize:  bpy.props.IntProperty(
        name="Node max size",
        description="Max count of faces for a node in bsp tree",
        default=2500,
        min=1,
        soft_max=5000
    )

    CleanUp:  bpy.props.BoolProperty(
        name="Clean up",
        description="Remove unreferenced vertex groups",
        default=False
    )

    def execute(self, context):

        success = False
        for ob in bpy.context.selected_objects:
            if ob.wow_wmo_group.enabled:
                bpy.context.view_layer.objects.active = ob

                if self.CleanUp:
                    for vertex_group in ob.vertex_groups:
                        if vertex_group.name != ob.wow_wmo_vertex_info.vertex_group \
                                and vertex_group.name != ob.wow_wmo_vertex_info.batch_type_a \
                                and vertex_group.name != ob.wow_wmo_vertex_info.batch_type_b \
                                and vertex_group.name != ob.wow_wmo_vertex_info.lightmap \
                                and vertex_group.name != ob.wow_wmo_vertex_info.blendmap \
                                and vertex_group.name != ob.wow_wmo_vertex_info.second_uv:
                            ob.vertex_groups.remove(vertex_group)

                if ob.vertex_groups.get(ob.wow_wmo_vertex_info.vertex_group):
                    bpy.ops.object.vertex_group_set_active(group=ob.wow_wmo_vertex_info.vertex_group)
                else:
                    new_vertex_group = ob.vertex_groups.new(name="Collision")
                    bpy.ops.object.vertex_group_set_active(group=new_vertex_group.name)
                    ob.wow_wmo_vertex_info.vertex_group = new_vertex_group.name

                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.object.vertex_group_assign()
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                ob.wow_wmo_vertex_info.node_size = self.NodeSize

                success = True

        if success:
            self.report({'INFO'}, "Successfully generated automatic collision for selected WMO groups")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No WMO group objects found among selected objects")
            return {'CANCELLED'}


class WMO_OT_to_group(bpy.types.Operator):
    bl_idname = 'scene.wow_selected_objects_to_group'
    bl_label = 'Selected objects to WMO group'
    bl_description = 'Transfer all selected objects to WoW WMO groups'
    bl_options = {'REGISTER', 'UNDO'}

    GroupName:  bpy.props.StringProperty(name="Name")
    description:  bpy.props.StringProperty(name="Description")

    place_type:  bpy.props.EnumProperty(
        items=place_type_enum,
        name="Place Type",
        description="Group is indoor or outdoor"
    )

    Flags:  bpy.props.EnumProperty(
        items=group_flag_enum,
        options={'ENUM_FLAG'}
    )

    GroupDBCid:  bpy.props.IntProperty(
        name="DBC Group ID",
        description="WMO Group ID in DBC file"
    )

    LiquidType:  bpy.props.EnumProperty(
        items=liquid_type_enum,
        name="LiquidType",
        description="Fill this WMO group with selected liquid."
    )

    def execute(self, context):

        scene = bpy.context.scene

        success = False
        for ob in bpy.context.selected_objects:
            if ob.type == 'MESH':
                ob.wow_wmo_liquid.enabled = False
                ob.wow_wmo_fog.enabled = False
                ob.wow_wmo_portal.enabled = False
                ob.wow_wmo_group.enabled = True
                ob.wow_wmo_group.place_type = self.place_type
                ob.wow_wmo_group.GroupName = self.GroupName
                ob.wow_wmo_group.description = self.description
                ob.wow_wmo_group.flags = self.Flags
                ob.wow_wmo_group.group_dbc_id = self.GroupDBCid
                ob.wow_wmo_group.liquid_type = self.LiquidType

                if self.place_type == "8" and "0" in scene.wow_visibility \
                        or self.place_type == "8192" and "1" in scene.wow_visibility:
                    ob.hide_set(False)
                else:
                    ob.hide_set(True)
                success = True

        if success:
            self.report({'INFO'}, "Successfully converted select objects to WMO groups")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No mesh objects found among selected objects")
            return {'CANCELLED'}


class WMO_OT_to_wow_material(bpy.types.Operator):
    bl_idname = 'scene.wow_selected_objects_to_wow_material'
    bl_label = 'Materials of selected objects to WoW Material'
    bl_description = 'Transfer all materials of selected objects to WoW material'
    bl_options = {'REGISTER', 'UNDO'}

    Flags:  bpy.props.EnumProperty(
        name="Material flags",
        description="WoW material flags",
        items=material_flag_enum,
        options={"ENUM_FLAG"}
    )

    Shader:  bpy.props.EnumProperty(
        items=shader_enum,
        name="Shader",
        description="WoW shader assigned to this material"
    )

    BlendingMode:  bpy.props.EnumProperty(
        items=blending_enum,
        name="Blending",
        description="WoW material blending mode"
    )

    Texture1:  bpy.props.StringProperty(
        name="Texture 1",
        description="Diffuse texture"
    )

    EmissiveColor:  bpy.props.FloatVectorProperty(
        name="Emissive Color",
        subtype='COLOR',
        default=(1, 1, 1, 1),
        size=4,
        min=0.0,
        max=1.0
    )

    Texture2:  bpy.props.StringProperty(
        name="Texture 2",
        description="Environment texture"
    )

    DiffColor:  bpy.props.FloatVectorProperty(
        name="Diffuse Color",
        subtype='COLOR',
        default=(1, 1, 1, 1),
        size=4,
        min=0.0,
        max=1.0
    )

    TerrainType:  bpy.props.EnumProperty(
        items=terrain_type_enum,
        name="Terrain Type",
        description="Terrain type assigned to this material. Used for producing correct footstep sounds."
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "Shader")
        col.prop(self, "TerrainType")
        col.prop(self, "BlendingMode")

        col.separator()
        col.label(text="Flags:")
        col.prop(self, "Flags")

        col.separator()
        col.prop(self, "Texture1")
        col.prop(self, "Texture2")

        layout.prop(self, "EmissiveColor")
        layout.prop(self, "DiffColor")

    def execute(self, context):
        success = False
        for ob in bpy.context.selected_objects:
            if ob.wow_wmo_group.enabled:
                for material in ob.data.materials:
                    material.wow_wmo_material.enabled = True
                    material.wow_wmo_material.shader = self.Shader
                    material.wow_wmo_material.blending_mode = self.BlendingMode
                    material.wow_wmo_material.terrain_type = self.TerrainType
                    material.wow_wmo_material.flags = self.Flags
                    material.wow_wmo_material.emissive_color = self.EmissiveColor
                    material.wow_wmo_material.diff_color = self.DiffColor
                success = True

        if success:
            self.report({'INFO'}, "Successfully enabled all materials in the selected WMO groups as WMO materials")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No WMO group objects found among selected objects")
            return {'FINISHED'}


class WMO_OT_to_wmo_portal(bpy.types.Operator):
    bl_idname = 'scene.wow_selected_objects_to_portals'
    bl_label = 'Selected objects to WMO portals'
    bl_description = 'Transfer all selected objects to WoW WMO portals'
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout
        column = layout.column()

    def execute(self, context):
        success = False
        for ob in bpy.context.selected_objects:
            if ob.type == 'MESH':
                ob.wow_wmo_group.enabled = False
                ob.wow_wmo_liquid.enabled = False
                ob.wow_wmo_fog.enabled = False
                ob.wow_wmo_portal.enabled = True

                ob.hide_set(False if "2" in bpy.context.scene.wow_visibility else True)
                success = True

        if success:
            self.report({'INFO'}, "Successfully converted select objects to portals")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No mesh objects found among selected objects")
            return {'CANCELLED'}


class WMO_OT_select_entity(bpy.types.Operator):
    bl_idname = 'scene.wow_wmo_select_entity'
    bl_label = 'Select WMO entities'
    bl_description = 'Select all WMO entities of given type'
    bl_options = {'REGISTER', 'INTERNAL'}

    entity:  bpy.props.EnumProperty(
        name="Entity",
        description="Select WMO component entity objects",
        items=[
            ("Outdoor", "Outdoor", ""),
            ("Indoor", "Indoor", ""),
            ("wow_wmo_portal", "Portals", ""),
            ("wow_wmo_liquid", "Liquids", ""),
            ("wow_wmo_fog", "Fogs", ""),
            ("wow_wmo_light", "Lights", ""),
            ("wow_wmo_doodad", "Doodads", ""),
            ("Collision", "Collision", "")
        ]
    )

    def execute(self, context):

        for obj in bpy.context.scene.objects:
            if obj.hide_get():
                continue

            if obj.type == 'MESH':
                if obj.wow_wmo_group.enabled:
                    if self.entity == "Outdoor" and obj.wow_wmo_group.place_type == '8':
                        obj.select_set(True)
                    elif self.entity == "Indoor" and obj.wow_wmo_group.place_type == '8192':
                        obj.select_set(True)

                    if obj.wow_wmo_group.collision_mesh:
                        obj.wow_wmo_group.collision_mesh.select_set(True)

                elif self.entity not in ("wow_wmo_light", "Outdoor", "Indoor", "Collision"):
                    if getattr(obj, self.entity).enabled:
                        obj.select_set(True)

            elif obj.type == 'LIGHT' and self.entity == "wow_wmo_light":
                obj.select_set(True)

        return {'FINISHED'}
