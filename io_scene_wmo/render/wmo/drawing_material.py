import bpy

from .shaders import EGxBlendRecord, WMOBlendingModeToEGxBlend


class WMODrawingMaterial:
    __slots__ = (
        'draw_mgr',
        'bl_material_name',
        'blend_mode',
        'backface_culling',
        'is_unlit',
        'is_unfogged',
        'is_exterior_lit',
        'night_glow',
        'is_window',
        'clamp_s',
        'clamp_t',
    )

    blend_mode: EGxBlendRecord
    backface_culling: bool
    is_unlit: bool
    is_unfogged: bool
    is_exterior_lit: bool
    night_glow: bool
    is_window: bool
    clamp_s: bool
    clamp_t: bool

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
            return getattr(mat.wow_wmo_material, 'diff_texture_{}'.format(tex_index + 1))

    @property
    def texture_count(self):
        mat = self.bl_material
        counter = 0

        if mat:
            for i in range(2):
                tex = getattr(mat.wow_wmo_material, 'diff_texture_{}'.format(i + 1))
                if tex:
                    counter += 1

        return counter

    def update_uniform_data(self):

        bl_material = self.bl_material

        if not bl_material:
            return

        self.blend_mode = WMOBlendingModeToEGxBlend[int(self.bl_material.wow_wmo_material.blending_mode)]
        self.backface_culling = '4' not in bl_material.wow_wmo_material.render_flags
        self.is_unlit = '1' in bl_material.wow_wmo_material.render_flags
        self.is_unfogged = '2' in bl_material.wow_wmo_material.render_flags
        self.is_exterior_lit = '8' in bl_material.wow_wmo_material.render_flags
        self.night_glow = '16' in bl_material.wow_wmo_material.render_flags
        self.is_window = '32' in bl_material.wow_wmo_material.render_flags
        self.clamp_s = '64' in bl_material.wow_wmo_material.render_flags
        self.clamp_t = '128' in bl_material.wow_wmo_material.render_flags

    def get_bindcode(self, tex_index: int) -> int:

        texture = self.get_texture(tex_index)

        if texture:
            if not texture.bindcode:
                texture.gl_load()

            return texture.bindcode

        return 0
