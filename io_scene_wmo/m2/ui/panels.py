import bpy

from .enums import *


###############################
## Material
###############################

class WowM2MaterialPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    bl_label = "M2 Material"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label('Flags:')
        col.prop(context.material.WowM2Material, "Flags")
        col.separator()
        col.label('Render Flags:')
        col.prop(context.material.WowM2Material, "RenderFlags")
        col.separator()
        col.prop(context.material.WowM2Material, "BlendingMode")
        col.prop(context.material.WowM2Material, "Shader")

    @classmethod
    def poll(cls, context):
        return context.material is not None


class WowM2MaterialPropertyGroup(bpy.types.PropertyGroup):

    Flags = bpy.props.EnumProperty(
        name="Material flags",
        description="WoW  M2 material flags",
        items=TEX_UNIT_FLAGS,
        options={"ENUM_FLAG"}
        )

    RenderFlags = bpy.props.EnumProperty(
        name="Render flags",
        description="WoW  M2 render flags",
        items=RENDER_FLAGS,
        options={"ENUM_FLAG"}
        )

    Shader = bpy.props.EnumProperty(
        items=SHADERS,
        name="Shader",
        description="WoW shader assigned to this material"
        )

    BlendingMode = bpy.props.EnumProperty(
        items=BLENDING_MODES,
        name="Blending",
        description="WoW material blending mode"
        )


def register_wow_m2_material_properties():
    bpy.types.Material.WowM2Material = bpy.props.PointerProperty(type=WowM2MaterialPropertyGroup)


def unregister_wow_m2_material_properties():
    bpy.types.Material.WowM2Material = None


###############################
## Vertex Info
###############################

class M2GeosetPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "WoW M2 Geoset"

    def draw(self, context):
        self.layout.prop(context.object.WowM2Geoset, "CollisionMesh")

        if not context.object.WowM2Geoset.CollisionMesh:
            self.layout.prop(context.object.WowM2Geoset, "MeshPartID")

    @classmethod
    def poll(cls, context):
        return (context.object is not None
                and context.object.data is not None
                and isinstance(context.object.data, bpy.types.Mesh)
                )


class WowM2GeosetPropertyGroup(bpy.types.PropertyGroup):
    CollisionMesh = bpy.props.BoolProperty(
        name='Collision mesh',
        default=False
    )

    MeshPartID = bpy.props.IntProperty(
        name="Geoset ID",
        description="Mesh part ID of this geoset",
        min=0,
        max=2500
    )


def register_wow_m2_geoset_properties():
    bpy.types.Object.WowM2Geoset = bpy.props.PointerProperty(type=WowM2GeosetPropertyGroup)


def unregister_wow_m2_geoset_properties():
    bpy.types.Object.WowM2Geoset = None


###############################
## Texture
###############################

class WowM2TexturePanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "texture"
    bl_label = "M2 Texture"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.texture.WowM2Texture, "Flags")
        col.separator()
        col.prop(context.texture.WowM2Texture, "TextureType")

    @classmethod
    def poll(cls, context):
        return context.texture is not None


class WowM2TexturePropertyGroup(bpy.types.PropertyGroup):

    Flags = bpy.props.EnumProperty(
        name="Texture flags",
        description="WoW  M2 texture flags",
        items=TEXTURE_FLAGS,
        options={"ENUM_FLAG"},
        default={'1', '2'}
        )

    TextureType = bpy.props.EnumProperty(
        name="Texture type",
        description="WoW  M2 texture type",
        items=TEXTURE_TYPES
        )


def register_wow_m2_texture_properties():
    bpy.types.ImageTexture.WowM2Texture = bpy.props.PointerProperty(type=WowM2TexturePropertyGroup)


def unregister_wow_m2_texture_properties():
    bpy.types.ImageTexture.WowM2Texture = None


###############################
## Light
###############################

class WowM2LightPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    bl_label = "M2 Light"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.object.data.WowM2Light, "Type")
        col.prop(context.object.data.WowM2Light, "AmbientColor")
        col.prop(context.object.data.WowM2Light, "AmbientIntensity")
        col.prop(context.object.data.WowM2Light, "DiffuseColor")
        col.prop(context.object.data.WowM2Light, "DiffuseIntensity")
        col.prop(context.object.data.WowM2Light, "AttenuationStart")
        col.prop(context.object.data.WowM2Light, "AttenuationEnd")
        col.prop(context.object.data.WowM2Light, "Enabled")

    @classmethod
    def poll(cls, context):
        return context.object is not None \
            and context.object.type == 'LAMP'


def update_lamp_type(self, context):
    context.object.data.type = 'POINT' if int(context.object.WowM2Light.Type) else 'SPOT'


class WowM2LightPropertyGroup(bpy.types.PropertyGroup):
    Type = bpy.props.EnumProperty(
        name="Type",
        description="WoW  M2 light type",
        items=[('0', 'Directional', 'Login screen only'), ('1', 'Point', '')],
        default='1',
        update=update_lamp_type
        )

    AmbientColor = bpy.props.FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        default=(1, 1, 1),
        min=0.0,
        max=1.0
    )

    AmbientIntensity = bpy.props.FloatProperty(
        name="Ambient intensity",
        description="Ambient intensity of the light",
        default=1.0,
        min=0.0,
        max=1.0
    )

    DiffuseColor = bpy.props.FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        default=(1, 1, 1),
        min=0.0,
        max=1.0
    )

    DiffuseIntensity = bpy.props.FloatProperty(
        name="Diffuse intensity",
        description="Diffuse intensity of the light",
        default=1.0,
        min=0.0,
        max=1.0
    )

    AttenuationStart = bpy.props.FloatProperty(
        name="Attenuation start",
        description="Start of attenuation",
        min=0.0    # TODO: max / default?
    )

    AttenuationEnd = bpy.props.FloatProperty(
        name="Attenuation end",
        description="End of attenuation",
        min=0.0  # TODO: max / default?
    )

    Enabled = bpy.props.BoolProperty(
        name='Enabled',
        default=True
    )


def register_wow_m2_light_properties():
    bpy.types.Lamp.WowM2Light = bpy.props.PointerProperty(type=WowM2LightPropertyGroup)


def unregister_wow_m2_light_properties():
    bpy.types.Lamp.WowM2Light = None


def register():
    register_wow_m2_material_properties()
    register_wow_m2_geoset_properties()
    register_wow_m2_texture_properties()
    register_wow_m2_light_properties()


def unregister():
    unregister_wow_m2_material_properties()
    unregister_wow_m2_geoset_properties()
    unregister_wow_m2_texture_properties()
    unregister_wow_m2_light_properties()


