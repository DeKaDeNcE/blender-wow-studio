import bpy
from ..enums import *


class WowM2MaterialPanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    bl_label = "M2 Material"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label('Render settings:')
        col.prop(context.material.wow_m2_material, "LiveUpdate")
        col.separator()
        col.label('Flags:')
        col.prop(context.material.wow_m2_material, "Flags")
        col.separator()
        col.label('Render Flags:')
        col.prop(context.material.wow_m2_material, "RenderFlags")
        col.separator()
        col.prop(context.material.wow_m2_material, "BlendingMode")
        col.prop(context.material.wow_m2_material, "Shader")

    @classmethod
    def poll(cls, context):
        return(context.scene is not None
               and context.scene.WowScene.Type == 'M2'
               and context.material is not None)


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

    # Blender animation playback settings

    LiveUpdate = bpy.props.BoolProperty(
        name='Live update',
        description='Automatically update this material on scene frame changes, if global live update is on. May decrease FPS.',
        default=False
    )


def register():
    bpy.types.Material.wow_m2_material = bpy.props.PointerProperty(type=WowM2MaterialPropertyGroup)


def unregister():
    del bpy.types.Material.wow_m2_material
