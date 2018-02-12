import bpy

###############################
## Constants
###############################

SHADERS = [
    ('0', "Diffuse", ""),
    ('1', "Specular", ""),
    ('2', "Metal", ""),
    ('3', "Env", ""),
    ('4', "Opaque", ""),
    ('5', "EnvMetal", ""),
    ('6', "TwoLayerDiffuse", ""),
    ('7', "TwoLayerEnvMetal", ""),
    ('8', "TwoLayerTerrain", ""),
    ('9', "DiffuseEmissive", ""),
    ('10', "Tangent", ""),
    ('11', "MaskedEnvMetal", ""),
    ('12', "EnvMetalEmissive", ""),
    ('13', "TwoLayerDiffuseOpaque", ""),
    ('14', "TwoLayerDiffuseEmissive", "")
]

TEX_UNIT_FLAGS = [
    ("1", "Unlit", "Disable lighting", 'PMARKER', 0x1),
    ("2", "Unfogged", "Disable fog", 'FORCE_TURBULENCE', 0x2),
    ("4", "Two-sided", "Render from both sides", 'ARROW_LEFTRIGHT', 0x4),
    ("8", "Depth-Test", "Unknown", 'PMARKER_SEL', 0x8),
    ("16", "Depth-Write", "Unknown", 'PMARKER_ACT', 0x10)
]

BLENDING_MODES = [
    ("0", "Opaque", "Blending disabled", 'PMARKER', 1),
    ("1", "Mod", "", 'PMARKER', 2),
    ("2", "Decal", "", 'FORCE_TURBULENCE', 3),
    ("3", "Add", "", 'ARROW_LEFTRIGHT', 4),
    ("4", "Mod2x", "", 'PMARKER_SEL', 5),
    ("5", "Fade", "", 'PMARKER_ACT', 6),
    ("6", "Deeeprun Tram", "", 'PMARKER_ACT', 7)
]


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
        col.prop(context.material.WowM2Material, "RenderFlags")
        col.prop(context.material.WowM2Material, "BlendingMode")
        col.prop(context.material.WowM2Material, "Shader")



    @classmethod
    def poll(cls, context):
        return context.material is not None


class WowM2MaterialPropertyGroup(bpy.types.PropertyGroup):

    RenderFlags = bpy.props.EnumProperty(
        name="Material flags",
        description="WoW  M2 material flags",
        items=TEX_UNIT_FLAGS,
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

class M2CollisionMesh(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "WoW M2 Collision"

    def draw(self, context):
        self.layout.prop(context.object.WowM2VertexInfo, "CollisionOnly")

    @classmethod
    def poll(cls, context):
        return (context.object is not None
                and context.object.data is not None
                and isinstance(context.object.data, bpy.types.Mesh)
                )


class WowM2MeshPropertyGroup(bpy.types.PropertyGroup):
    CollisionMesh = bpy.props.BoolProperty(default=False, name='Collision mesh')


def register_wow_m2_mesh_properties():
    bpy.types.Object.WowM2VertexInfo = bpy.props.PointerProperty(type=WowM2MeshPropertyGroup)


def unregister_wow_m2_mesh_properties():
    bpy.types.Object.WowM2VertexInfo = None


def register():
    register_wow_m2_material_properties()
    register_wow_m2_mesh_properties()


def unregister():
    unregister_wow_m2_material_properties()
    unregister_wow_m2_mesh_properties()


