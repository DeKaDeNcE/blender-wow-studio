import bpy
import os


def load_texture(textures : dict, filename : str, texture_dir : str) -> bpy.types.Texture:
    new_filename = os.path.splitext(filename)[0] + '.png'

    if os.name != 'nt':
        new_filename = new_filename.replace('\\', '/')

    tex1_name = os.path.basename(new_filename)

    texture = None

    # check if texture is already loaded
    for tex_name, tex in textures.items():
        if tex_name == filename:
            texture = tex
            break

    # if image is not loaded, do it
    if not texture:
        texture = bpy.data.textures.new(tex1_name, 'IMAGE')
        texture.wow_wmo_texture.path = filename
        tex_img = bpy.data.images.load(os.path.join(texture_dir, new_filename))
        texture.image = tex_img

        textures[filename] = texture

    return texture


def add_ghost_material() -> bpy.types.Material:
    """ Add ghost material """

    mat = bpy.data.materials.get("WowMaterial_ghost")
    if not mat:
        mat = bpy.data.materials.new("WowMaterial_ghost")
        mat.diffuse_color = (0.2, 0.5, 0.5, 1.0)

    return mat
