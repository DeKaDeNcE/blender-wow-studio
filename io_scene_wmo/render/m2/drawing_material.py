import bpy

from .shaders import EGxBlendRecord, M2BlendingModeToEGxBlend


class M2DrawingMaterial:
    __slots__ = (
        'bl_material_name',
        'blend_mode',
        'depth_write',
        'depth_culling',
        'backface_culling',
        'is_unlit',
        'is_unfogged',
        'is_inverted',
        'is_transformed',
        'texture_count'
    )

    blend_mode: EGxBlendRecord
    depth_write: bool
    depth_culling: bool
    backface_culling: bool
    is_unlit: bool
    is_unfogged: bool
    is_inverted: bool
    is_transformed: bool
    texture_count: int

    def __init__(self, material: bpy.types.Material):
        self.bl_material_name = material.name
        self.update_uniform_data()

    @property
    def bl_material(self):
        try:
            return bpy.data.materials[self.bl_material_name]
        except KeyError:
            return None

    def update_uniform_data(self):

        bl_material = self.bl_material

        if not bl_material:
            return

        self.blend_mode =       M2BlendingModeToEGxBlend[int(self.bl_material.wow_m2_material.blending_mode)]
        self.depth_write =      '16' not in bl_material.wow_m2_material.render_flags
        self.depth_culling =    '8' not in bl_material.wow_m2_material.render_flags
        self.backface_culling = '4' not in bl_material.wow_m2_material.render_flags
        self.is_unlit =         '1' in bl_material.wow_m2_material.render_flags
        self.is_unfogged =      '2' in bl_material.wow_m2_material.render_flags

        self.is_inverted =      '1' in bl_material.wow_m2_material.flags
        self.is_transformed =   '2' in bl_material.wow_m2_material.flags

        self.texture_count = 0

        if bl_material.wow_m2_material.texture_1:
            self.texture_count += 1

        if bl_material.wow_m2_material.texture_2:
            self.texture_count += 1

        if bl_material.wow_m2_material.texture_3:
            self.texture_count += 1

        if bl_material.wow_m2_material.texture_4:
            self.texture_count += 1
