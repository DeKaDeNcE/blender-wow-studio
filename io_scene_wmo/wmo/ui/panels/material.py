import bpy
from ..enums import *


class WowMaterialPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    bl_label = "WoW Material"

    def draw_header(self, context):
        layout = self.layout
        self.layout.prop(context.material.WowMaterial, "Enabled")

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.material.WowMaterial, "Shader")
        col.prop(context.material.WowMaterial, "TerrainType")
        col.prop(context.material.WowMaterial, "BlendingMode")

        col.separator()
        col.prop(context.material.WowMaterial, "Texture1")
        col.prop(context.material.WowMaterial, "Texture2")

        col.separator()
        col.label("Flags:")
        col.prop(context.material.WowMaterial, "Flags")

        layout.prop(context.material.WowMaterial, "EmissiveColor")
        layout.prop(context.material.WowMaterial, "DiffColor")
        layout.enabled = context.material.WowMaterial.Enabled

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.WowScene.Type == 'WMO'
                and context.material is not None
        )


class WowMaterialPropertyGroup(bpy.types.PropertyGroup):

    Enabled = bpy.props.BoolProperty(
        name="",
        description="Enable WoW material properties"
        )

    Flags = bpy.props.EnumProperty(
        name="Material flags",
        description="WoW material flags",
        items=material_flag_enum,
        options={"ENUM_FLAG"}
        )

    Shader = bpy.props.EnumProperty(
        items=shader_enum,
        name="Shader",
        description="WoW shader assigned to this material"
        )

    BlendingMode = bpy.props.EnumProperty(
        items=blending_enum,
        name="Blending",
        description="WoW material blending mode"
        )

    Texture1 = bpy.props.StringProperty(
        name="Texture 1",
        description="Diffuse texture"
        )

    EmissiveColor = bpy.props.FloatVectorProperty(
        name="Emissive Color",
        subtype='COLOR',
        default=(1,1,1,1),
        size=4,
        min=0.0,
        max=1.0
        )

    Texture2 = bpy.props.StringProperty(
        name="Texture 2",
        description="Environment texture"
        )

    DiffColor = bpy.props.FloatVectorProperty(
        name="Diffuse Color",
        subtype='COLOR',
        default=(1,1,1,1),
        size=4,
        min=0.0,
        max=1.0
        )

    TerrainType = bpy.props.EnumProperty(
        items=terrain_type_enum,
        name="Terrain Type",
        description="Terrain type assigned to this material. Used for producing correct footstep sounds."
        )


def register():
    bpy.types.Material.WowMaterial = bpy.props.PointerProperty(type=WowMaterialPropertyGroup)


def unregister():
    bpy.types.Material.WowMaterial = None
