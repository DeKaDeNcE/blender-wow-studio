import bpy
import os


def load_texture(textures : dict, filename : str, texture_dir : str) -> bpy.types.Image:
    new_filename = os.path.splitext(filename)[0] + '.png'

    if os.name != 'nt':
        new_filename = new_filename.replace('\\', '/')

    texture = textures.get(filename)

    # if image is not loaded, do it
    if not texture:
        tex_img = bpy.data.images.load(os.path.join(texture_dir, new_filename))
        tex_img.wow_wmo_texture.path = filename
        tex_img.name = os.path.basename(new_filename)
        texture = tex_img

        textures[filename] = texture

    return texture


def add_ghost_material() -> bpy.types.Material:
    """ Add ghost material """

    mat = bpy.data.materials.get("WowMaterial_ghost")
    if not mat:
        mat = bpy.data.materials.new("WowMaterial_ghost")
        mat.diffuse_color = (0.2, 0.5, 0.5, 1.0)

    return mat
