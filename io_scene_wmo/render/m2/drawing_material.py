import bpy

from .shaders import EGxBlendRecord, M2BlendingModeToEGxBlend


class M2DrawingMaterial:
    __slots__ = (
        'bl_material',
        'blend_mode',
        'depth_write',
        'depth_culling',
        'backface_culling',
        'is_unlit',
        'is_unfogged',
        'is_inverted',
        'is_transformed'
    )

    blend_mode: EGxBlendRecord
    depth_write: bool
    depth_culling: bool
    backface_culling: bool
    is_unlit: bool
    is_unfogged: bool
    is_inverted: bool
    is_transformed: bool

    def __init__(self, material: bpy.types.Material):
        self.bl_material = material
        self.update_uniform_data()

    def update_uniform_data(self):
        self.blend_mode =       M2BlendingModeToEGxBlend[int(self.bl_material.wow_m2_material.blending_mode)]
        self.depth_write =      '16' not in self.bl_material.wow_m2_material.render_flags
        self.depth_culling =    '8' not in self.bl_material.wow_m2_material.render_flags
        self.backface_culling = '4' not in self.bl_material.wow_m2_material.render_flags
        self.is_unlit =         '1' in self.bl_material.wow_m2_material.render_flags
        self.is_unfogged =      '2' in self.bl_material.wow_m2_material.render_flags

        self.is_inverted =      '1' in self.bl_material.wow_m2_material.flags
        self.is_transformed =   '2' in self.bl_material.wow_m2_material.flags
