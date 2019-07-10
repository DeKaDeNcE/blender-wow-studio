import bpy

from collections import namedtuple

from ..enums import *
from .liquid import WMO_PT_liquid

class WMO_PT_wmo_group(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "WMO Group"

    def draw_header(self, context):
        row = self.layout.row()
        row.alignment = 'RIGHT'
        op = row.operator('scene.wow_wmo_destroy_wow_property', text='', icon='X', emboss=False)
        op.prop_group = 'wow_wmo_group'

        if bpy.context.scene.wow_wmo_root_elements.groups.find(context.object.name) < 0:
            row.label(text='', icon='ERROR')
            row.alert = True

    def draw(self, context):
        self.layout.use_property_split = True

        col = self.layout.column()
        col.prop(context.object.wow_wmo_group, "description")

        col.separator()
        col.prop(context.object.wow_wmo_group, "place_type")
        col.prop(context.object.wow_wmo_group, "flags")

        col.separator()
        box = col.box()
        box.prop(context.object.wow_wmo_group, "fog1")
        box.prop(context.object.wow_wmo_group, "fog2")
        box.prop(context.object.wow_wmo_group, "fog3")
        box.prop(context.object.wow_wmo_group, "fog4")

        col.separator()
        col.prop(context.object.wow_wmo_group, "group_dbc_id")
        col.prop(context.object.wow_wmo_group, "liquid_type")

        box = col.box()
        box.prop(context.object.wow_wmo_group, "liquid_mesh")

        if context.object.wow_wmo_group.liquid_mesh:
            ctx_override = namedtuple('ctx_override', ('layout', 'object'))
            ctx = ctx_override(box, context.object.wow_wmo_group.liquid_mesh)
            WMO_PT_liquid.draw(ctx, ctx)

        col.prop(context.object.wow_wmo_group, "collision_mesh")

        self.layout.enabled = context.object.wow_wmo_group.enabled

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
                and context.object is not None
                and context.object.data is not None
                and context.object.type == 'MESH'
                and context.object.wow_wmo_group.enabled
                )


class WowWMOMODRStore(bpy.types.PropertyGroup):
    value:  bpy.props.IntProperty(name="Doodads Ref")


class WowWMOPortalRel(bpy.types.PropertyGroup):
    id:  bpy.props.StringProperty()


class WowWMOLightRel(bpy.types.PropertyGroup):
    id:  bpy.props.IntProperty()


class WowWMODoodadRel(bpy.types.PropertyGroup):
    id:  bpy.props.IntProperty()


class WowWMOGroupRelations(bpy.types.PropertyGroup):
    """Used for export internally"""
    portals:  bpy.props.CollectionProperty(type=WowWMOPortalRel)
    lights:  bpy.props.CollectionProperty(type=WowWMOLightRel)
    liquid:  bpy.props.StringProperty()
    doodads:  bpy.props.CollectionProperty(type=WowWMODoodadRel)


def fog_validator(self, context):
    if self.fog1 and (not self.fog1.wow_wmo_fog.enabled or self.fog1.name not in bpy.context.scene.objects):
        self.fog1 = None

    if self.fog2 and (not self.fog2.wow_wmo_fog.enabled or self.fog2.name not in bpy.context.scene.objects):
        self.fog2 = None

    if self.fog3 and (not self.fog3.wow_wmo_fog.enabled or self.fog3.name not in bpy.context.scene.objects):
        self.fog3 = None

    if self.fog4 and (not self.fog4.wow_wmo_fog.enabled or self.fog4.name not in bpy.context.scene.objects):
        self.fog4 = None


def collision_validator(self, context):
    if self.collision_mesh.type != 'MESH':
        self.collision_mesh = None


def update_place_type(self, context):

    obj = context.object

    if not obj:
        obj = context.view_layer.objects.active

    if not obj:
        return

    if self.place_type == '8':
        obj.pass_index |= 0x1 # BlenderWMOObjectRenderFlags.IsOutdoor
        obj.pass_index &= ~0x2 # BlenderWMOObjectRenderFlags.IsIndoor
    else:
        obj.pass_index &= ~0x1
        obj.pass_index |= 0x2


def update_flags(self, context):

    obj = context.object

    if not obj:
        obj = context.view_layer.objects.active

    if not obj:
        return

    if '0' in self.flags:
        obj.pass_index |= 0x20  # BlenderWMOObjectRenderFlags.HasVertexColor
    else:
        obj.pass_index &= ~0x20

    if '1' in self.flags:
        obj.pass_index |= 0x4  # BlenderWMOObjectRenderFlags.NoLocalLight
    else:
        obj.pass_index &= ~0x4

def is_liquid_unused(obj):

    root_elements = bpy.context.scene.wow_wmo_root_elements

    for group in root_elements.groups:
        if group.pointer and group.pointer.wow_wmo_group.liquid_mesh == obj:
            return False

    return True

class WowWMOGroupPropertyGroup(bpy.types.PropertyGroup):

    description:  bpy.props.StringProperty(name="Description")

    enabled:  bpy.props.BoolProperty(
        name="",
        description="Enable wow WMO group properties"
        )

    flags:  bpy.props.EnumProperty(
        items=group_flag_enum,
        options={'ENUM_FLAG'},
        update=update_flags
        )

    place_type:  bpy.props.EnumProperty(
        items=place_type_enum,
        name="Place Type",
        description="Group is indoor or outdoor",
        update=update_place_type
        )

    group_id:  bpy.props.IntProperty(
        name="",
        description="Group identifier used for export"
        )

    group_dbc_id:  bpy.props.IntProperty(
        name="DBC Group ID",
        description="WMO Group ID in DBC file"
        )

    liquid_type:  bpy.props.EnumProperty(
        items=liquid_type_enum,
        name="LiquidType",
        description="Fill this WMO group with selected liquid."
        )

    fog1:  bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Fog #1",
        poll=lambda self, obj: obj.wow_wmo_fog.enabled and obj.name in bpy.context.scene.objects,
        update=fog_validator
    )

    fog2:  bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Fog #2",
        poll=lambda self, obj: obj.wow_wmo_fog.enabled and obj.name in bpy.context.scene.objects,
        update=fog_validator
    )

    fog3:  bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Fog #3",
        poll=lambda self, obj: obj.wow_wmo_fog.enabled and obj.name in bpy.context.scene.objects,
        update=fog_validator
    )

    fog4:  bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Fog #4",
        poll=lambda self, obj: obj.wow_wmo_fog.enabled and obj.name in bpy.context.scene.objects,
        update=fog_validator
    )

    collision_mesh:  bpy.props.PointerProperty(
        type=bpy.types.Object,
        name='Collision',
        description='Invisible collision geometry of this group',
        poll=lambda self, obj: obj.type == 'MESH',
        update=collision_validator
    )

    liquid_mesh: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name='Liquid',
        description='Liquid plane linked to this group',
        poll=lambda self, obj: obj.type == 'MESH' and obj.wow_wmo_liquid.enabled and is_liquid_unused(obj)
    )

    modr:  bpy.props.CollectionProperty(type=WowWMOMODRStore)

    relations:  bpy.props.PointerProperty(type=WowWMOGroupRelations)


def register():
    bpy.types.Object.wow_wmo_group = bpy.props.PointerProperty(type=WowWMOGroupPropertyGroup)


def unregister():
    del bpy.types.Object.wow_wmo_group
