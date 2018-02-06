def parse_bitfield(bitfield, ui_enum_prop, last_flag=0x1000):

    flags = set()
    bit = 1
    while bit <= last_flag:
        if bitfield & bit:
            flags.add(str(bit))
        bit <<= 1
    ui_enum_prop = flags


def get_material_viewport_image(material):
    """ Get viewport image assigned to a material """
    img = material.texture_slots[0].texture.image
    return img
