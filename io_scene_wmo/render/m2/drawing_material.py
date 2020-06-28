import bpy

from .shaders import EGxBlendRecord, M2BlendingModeToEGxBlend


class M2DrawingMaterial:
    __slots__ = (
        'draw_mgr',
        'bl_material_name',
        'blend_mode',
        'depth_write',
        'depth_culling',
        'backface_culling',
        'is_unlit',
        'is_unfogged',
        'is_inverted',
        'is_transformed',
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
        self.bl_material_name = material.name

        self.update_uniform_data()

    @property
    def bl_material(self):
        try:
            return bpy.data.materials[self.bl_material_name]
        except KeyError:
            return None

    def get_texture(self, tex_index: int):
        mat = self.bl_material

        if mat:
            return getattr(mat.wow_m2_material, 'texture_{}'.format(tex_index + 1))

    @property
    def texture_count(self):
        mat = self.bl_material
        counter = 0

        if mat:
            for i in range(4):
                tex = getattr(mat.wow_m2_material, 'texture_{}'.format(i + 1))
                if tex:
                    counter += 1

        return counter

    def update_uniform_data(self):

        bl_material = self.bl_material

        if not bl_material:
            return

        self.blend_mode = M2BlendingModeToEGxBlend[int(self.bl_material.wow_m2_material.blending_mode)]
        self.depth_write = '16' not in bl_material.wow_m2_material.render_flags
        self.depth_culling = '8' not in bl_material.wow_m2_material.render_flags
        self.backface_culling = '4' not in bl_material.wow_m2_material.render_flags
        self.is_unlit = '1' in bl_material.wow_m2_material.render_flags
        self.is_unfogged = '2' in bl_material.wow_m2_material.render_flags

        self.is_inverted = '1' in bl_material.wow_m2_material.flags
        self.is_transformed = '2' in bl_material.wow_m2_material.flags

    def get_bindcode(self, tex_index: int) -> int:

        texture = self.get_texture(tex_index)

        if texture:
            if not texture.bindcode:
                texture.gl_load()

            return texture.bindcode

        return 0
