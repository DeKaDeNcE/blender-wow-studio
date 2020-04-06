import bpy

from ....third_party.tqdm import tqdm


class WMO_OT_add_scale(bpy.types.Operator):
    bl_idname = 'scene.wow_add_scale_reference'
    bl_label = 'Add scale'
    bl_description = 'Add a WoW scale prop'
    bl_options = {'REGISTER', 'UNDO'}

    scale_type:  bpy.props.EnumProperty(
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
        if self.scale_type == 'HUMAN':
            bpy.ops.object.add(type='LATTICE')
            scale_obj = bpy.context.object
            scale_obj.name = "Human Scale"
            scale_obj.dimensions = (0.582, 0.892, 1.989)

        elif self.scale_type == 'TAUREN':
            bpy.ops.object.add(type='LATTICE')
            scale_obj = bpy.context.object
            scale_obj.name = "Tauren Scale"
            scale_obj.dimensions = (1.663, 1.539, 2.246)

        elif self.scale_type == 'TROLL':
            bpy.ops.object.add(type='LATTICE')
            scale_obj = bpy.context.object
            scale_obj.name = "Troll Scale"
            scale_obj.dimensions = (1.116, 1.291, 2.367)

        elif self.scale_type == 'GNOME':
            bpy.ops.object.add(type='LATTICE')
            scale_obj = bpy.context.object
            scale_obj.name = "Gnome Scale"
            scale_obj.dimensions = (0.362, 0.758, 0.991)

        self.report({'INFO'}, "Successfully added " + self.scale_type + " scale")
        return {'FINISHED'}


class WMO_OT_quick_collision(bpy.types.Operator):
    bl_idname = 'scene.wow_quick_collision'
    bl_label = 'Generate collision'
    bl_description = 'Generate WoW collision equal to geometry of the selected objects'
    bl_options = {'REGISTER', 'UNDO'}

    leaf_size:  bpy.props.IntProperty(
        name="Node max size",
        description="Max count of faces for a node in bsp tree",
        default=2500,
        min=1,
        soft_max=5000
    )

    clean_up:  bpy.props.BoolProperty(
        name="Clean up",
        description="Remove unreferenced vertex groups",
        default=False
    )

    def execute(self, context):

        success = False
        selected_objects = bpy.context.selected_objects[:]
        bpy.ops.object.select_all(action='DESELECT')
        for ob in tqdm(selected_objects, desc='Generating collision', ascii=True):

            if ob.wow_wmo_group.enabled:

                bpy.context.view_layer.objects.active = ob

                if self.clean_up:
                    for vertex_group in ob.vertex_groups:
                        if vertex_group.name != ob.wow_wmo_vertex_info.vertex_group:
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
                ob.wow_wmo_vertex_info.node_size = self.leaf_size

                success = True

        if success:
            self.report({'INFO'}, "Successfully generated automatic collision for selected WMO groups")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No WMO group objects found among selected objects")
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
