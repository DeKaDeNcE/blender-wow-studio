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
        col.label(text='Shader control:')
        col.prop(context.material.wow_m2_material, "blending_mode")
        col.prop(context.material.wow_m2_material, "vertex_shader")
        col.prop(context.material.wow_m2_material, "fragment_shader")
        col.separator()
        col.label(text='Sorting control:')
        col.prop(context.material.wow_m2_material, "priority_plane")
        col.prop(context.material.wow_m2_material, "layer")
        col.separator()
        col.label(text='Textures')
        col.prop(context.material.wow_m2_material, "texture_1")
        col.prop(context.material.wow_m2_material, "texture_2")
        col.prop(context.material.wow_m2_material, "texture_3")
        col.prop(context.material.wow_m2_material, "texture_4")
        col.separator()
        col.prop_search(context.material.wow_m2_material, "color",
                        context.scene, "wow_m2_colors", text='Color', icon='COLOR')
        col.prop_search(context.material.wow_m2_material, "transparency",
                        context.scene, "wow_m2_transparency", text='Transparency', icon='RESTRICT_VIEW_OFF')

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

    vertex_shader:  bpy.props.EnumProperty(
        items=VERTEX_SHADERS,
        name="Vertex Shader",
        description="WoW vertex shader assigned to this material",
        default='0'
        )

    fragment_shader:  bpy.props.EnumProperty(
        items=FRAGMENT_SHADERS,
        name="Fragment Shader",
        description="WoW fragment shader assigned to this material",
        default='0'
        )

    #shader: bpy.props.IntProperty(name='Shader')

    blending_mode:  bpy.props.EnumProperty(
        items=BLENDING_MODES,
        name="Blending",
        description="WoW material blending mode"
        )

    texture_1: bpy.props.PointerProperty(
        type=bpy.types.Image
    )

    texture_2: bpy.props.PointerProperty(
        type=bpy.types.Image
    )

    texture_3: bpy.props.PointerProperty(
        type=bpy.types.Image
    )

    texture_4: bpy.props.PointerProperty(
        type=bpy.types.Image
    )

    layer: bpy.props.IntProperty(
        min=0,
        max=7
    )

    priority_plane: bpy.props.IntProperty()

    color: bpy.props.StringProperty(
        name='Color',
        description='Color track linked to this texture.'
    )

    transparency: bpy.props.StringProperty(
        name='Transparency',
        description='Transparency track linked to this texture.'
    )

    # Blender animation playback settings

    live_update:  bpy.props.BoolProperty(
        name='Live update',
        description='Automatically update this material on scene frame changes, if global live update is on. May decrease FPS.',
        default=False
    )


def register():
    bpy.types.Material.wow_m2_material = bpy.props.PointerProperty(type=WowM2MaterialPropertyGroup)


def unregister():
    del bpy.types.Material.wow_m2_material
