import bpy
from ..enums import *


class M2_PT_material_panel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    bl_label = "M2 Material"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text='Render settings:')
        col.prop(context.material.wow_m2_material, "live_update")
        col.separator()
        col.label(text='Flags:')
        col.prop(context.material.wow_m2_material, "flags")
        col.separator()
        col.label(text='Render flags:')
        col.prop(context.material.wow_m2_material, "render_flags")
        col.separator()
        col.prop(context.material.wow_m2_material, "blending_mode")
        col.prop(context.material.wow_m2_material, "shader")

    @classmethod
    def poll(cls, context):
        return(context.scene is not None
               and context.scene.wow_scene.type == 'M2'
               and context.material is not None)


class WowM2MaterialPropertyGroup(bpy.types.PropertyGroup):

    flags:  bpy.props.EnumProperty(
        name="Material flags",
        description="WoW  M2 material flags",
        items=TEX_UNIT_FLAGS,
        options={"ENUM_FLAG"}
        )

    render_flags:  bpy.props.EnumProperty(
        name="Render flags",
        description="WoW  M2 render flags",
        items=RENDER_FLAGS,
        options={"ENUM_FLAG"}
        )

    shader:  bpy.props.EnumProperty(
        items=SHADERS,
        name="shader",
        description="WoW shader assigned to this material"
        )

    blending_mode:  bpy.props.EnumProperty(
        items=BLENDING_MODES,
        name="Blending",
        description="WoW material blending mode"
        )

    # Blender animation playback settings

    live_update:  bpy.props.BoolProperty(
        name='Live update',
        description='Automatically update this material on scene frame changes, if global live update is on. May decrease FPS.',
        default=False
    )


def register():
    bpy.types.Material.wow_m2_material:  bpy.props.PointerProperty(type=WowM2MaterialPropertyGroup)


def unregister():
    del bpy.types.Material.wow_m2_material
