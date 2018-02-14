def parse_bitfield(bitfield, last_flag=0x1000):

    flags = set()
    bit = 1
    while bit <= last_flag:
        if bitfield & bit:
            flags.add(str(bit))
        bit <<= 1

    return flags


def get_material_viewport_image(material):
    """ Get viewport image assigned to a material """
    for i in range(3):
        try:
            img = material.texture_slots[3 - i].texture.image
            return img
        except:
            pass
    return None


