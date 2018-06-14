import bpy
from ..enums import *


class WowM2BonePanel(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "bone"
    bl_label = "M2 Bone"

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.edit_bone.WowM2Bone, "KeyBoneID")
        col.separator()
        col.prop(context.edit_bone.WowM2Bone, "Flags")

    @classmethod
    def poll(cls, context):
        return (context.scene is not None
                and context.scene.WowScene.Type == 'M2'
                and context.edit_bone is not None)


class WowM2BonePropertyGroup(bpy.types.PropertyGroup):
    KeyBoneID = bpy.props.EnumProperty(
        name="Keybone",
        description="WoW bone keybone ID",
        items=get_keybone_ids
    )

    Flags = bpy.props.EnumProperty(
        name="Bone flags",
        description="WoW bone flags",
        items=BONE_FLAGS,
        options={"ENUM_FLAG"}
    )


def register():
    bpy.types.EditBone.WowM2Bone = bpy.props.PointerProperty(type=WowM2BonePropertyGroup)


def unregister():
   del bpy.types.EditBone.WowM2Bone