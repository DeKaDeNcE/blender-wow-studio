import bpy
from ..enums import *


class WowMaterialPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    bl_label = "WMO Material"

    def draw_header(self, context):
        self.layout.prop(context.material.wow_wmo_material, "enabled")

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.material.wow_wmo_material, "shader")
        col.prop(context.material.wow_wmo_material, "terrain_type")
        col.prop(context.material.wow_wmo_material, "blending_mode")

        col.separator()
        col.prop(context.material.wow_wmo_material, "texture1")
        col.prop(context.material.wow_wmo_material, "texture2")

        col.separator()
        col.label("Flags:")
        col.prop(context.material.wow_wmo_material, "flags")

        layout.prop(context.material.wow_wmo_material, "emissive_color")
        layout.prop(context.material.wow_wmo_material, "diff_color")
        layout.enabled = context.material.wow_wmo_material.enabled

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.wow_scene.type == 'WMO'
                and context.material is not None
        )


class WowMaterialPropertyGroup(bpy.types.PropertyGroup):

    enabled = bpy.props.BoolProperty(
        name="",
        description="Enable WoW material properties"
        )

    flags = bpy.props.EnumProperty(
        name="Material flags",
        description="WoW material flags",
        items=material_flag_enum,
        options={"ENUM_FLAG"}
        )

    shader = bpy.props.EnumProperty(
        items=shader_enum,
        name="Shader",
        description="WoW shader assigned to this material"
        )

    blending_mode = bpy.props.EnumProperty(
        items=blending_enum,
        name="Blending",
        description="WoW material blending mode"
        )

    texture1 = bpy.props.StringProperty(
        name="Texture 1",
        description="Diffuse texture"
        )

    emissive_color = bpy.props.FloatVectorProperty(
        name="Emissive Color",
        subtype='COLOR',
        default=(1,1,1,1),
        size=4,
        min=0.0,
        max=1.0
        )

    texture2 = bpy.props.StringProperty(
        name="Texture 2",
        description="Environment texture"
        )

    diff_color = bpy.props.FloatVectorProperty(
        name="Diffuse Color",
        subtype='COLOR',
        default=(1,1,1,1),
        size=4,
        min=0.0,
        max=1.0
        )

    terrain_type = bpy.props.EnumProperty(
        items=terrain_type_enum,
        name="Terrain Type",
        description="Terrain type assigned to this material. Used for producing correct footstep sounds."
        )


def register():
    bpy.types.Material.wow_wmo_material = bpy.props.PointerProperty(type=WowMaterialPropertyGroup)


def unregister():
    del bpy.types.Material.wow_wmo_material
