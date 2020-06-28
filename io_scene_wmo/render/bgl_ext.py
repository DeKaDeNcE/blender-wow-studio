import traceback

from bgl import *


def glCheckError(title):
    err = glGetError()
    if err == GL_NO_ERROR:
        return

    derrs = {
        GL_INVALID_ENUM: 'invalid enum',
        GL_INVALID_VALUE: 'invalid value',
        GL_INVALID_OPERATION: 'invalid operation',
        GL_OUT_OF_MEMORY: 'out of memory',
        GL_INVALID_FRAMEBUFFER_OPERATION: 'invalid framebuffer operation',
    }
    if err in derrs:
        print('ERROR (%s): %s' % (title, derrs[err]))
    else:
        print('ERROR (%s): code %d' % (title, err))
    traceback.print_stack()


def check_framebuffer_status(target):
    status = glCheckFramebufferStatus(target)

    if status ==  GL_FRAMEBUFFER_COMPLETE:
        return True
    elif status == GL_FRAMEBUFFER_UNDEFINED:
        print("framebuffer not complete: GL_FRAMEBUFFER_UNDEFINED - returned if the specified framebuffer is the default read or draw framebuffer, but the default framebuffer does not exist.")
    elif status == GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT:
        print("framebuffer not complete: GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT - returned if any of the framebuffer attachment points are framebuffer incomplete.")
    elif status == GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT:
        print("framebuffer not complete: GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT - returned if the framebuffer does not have at least one image attached to it.")
    elif status == GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER:
        print("framebuffer not complete: GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER - returned if the value of GL_FRAMEBUFFER_ATTACHMENT_OBJECT_TYPE is GL_NONE for any color attachment point named by GL_DRAW_BUFFERi.")
    elif status ==  GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER:
        print("framebuffer not complete: GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER - returned if GL_READ_BUFFER is not GL_NONE and the value of GL_FRAMEBUFFER_ATTACHMENT_OBJECT_TYPE is GL_NONE for the color attachment point named by GL_READ_BUFFER.")
    elif status ==  GL_FRAMEBUFFER_UNSUPPORTED:
        print("framebuffer not complete: GL_FRAMEBUFFER_UNSUPPORTED - returned if the combination of internal formats of the attached images violates an implementation-dependent set of restrictions.")
    elif status ==  GL_FRAMEBUFFER_INCOMPLETE_MULTISAMPLE:
        print("framebuffer not complete: GL_FRAMEBUFFER_INCOMPLETE_MULTISAMPLE - returned if the value of GL_RENDERBUFFER_SAMPLES is not the same for all attached renderbuffers; if the value of GL_TEXTURE_SAMPLES is the not same for all attached textures; or, if the attached images are a mix of renderbuffers and      textures, the value of GL_RENDERBUFFER_SAMPLES does not match the value of GL_TEXTURE_SAMPLES. also returned if the value of GL_TEXTURE_FIXED_SAMPLE_LOCATIONS i     s not the same for all attached textures; or, if the attached images are a mix of renderbuffers and textures, the value of GL_TEXTURE_FIXED_SAMPLE_LOCATIONS is not GL_TRUE for all attached textures.")
    elif status ==  GL_FRAMEBUFFER_INCOMPLETE_LAYER_TARGETS:
        print("framebuffer not complete: GL_FRAMEBUFFER_INCOMPLETE_LAYER_TARGETS - returned if any framebuffer attachment is layered, and any populated attachment is not layered, or if all populated color attachments are not from textures of the same target.")
    else:
        print("framebuffer not complete: status 0x%x (unknown)" % (status,))

    return False


def create_image(width, height, target=GL_RGBA):
    """create an empty image, dimensions pow2"""
    if target == GL_RGBA:
        target, internal_format, dimension  = GL_RGBA, GL_RGB, 3
    else:
        target, internal_format, dimension = GL_DEPTH_COMPONENT32, GL_DEPTH_COMPONENT, 1

    null_buffer = Buffer(GL_BYTE, [(width + 1) * (height + 1) * dimension])

    id_buf = Buffer(GL_INT, 1)
    glGenTextures(1, id_buf)

    tex_id = id_buf.to_list()[0]
    glBindTexture(GL_TEXTURE_2D, tex_id)

    glTexImage2D(GL_TEXTURE_2D, 0, target, width, height, 0, internal_format, GL_UNSIGNED_BYTE, null_buffer)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    if target == GL_DEPTH_COMPONENT32:
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_COMPARE_MODE, GL_NONE)

    glCopyTexImage2D(GL_TEXTURE_2D, 0, target, 0, 0, width, height, 0)

    glBindTexture(GL_TEXTURE_2D, 0)

    del null_buffer

    return tex_id


def delete_image(tex_id):
    """clear created image"""
    id_buf = Buffer(GL_INT, 1)
    id_buf.to_list()[0] = tex_id

    if glIsTexture(tex_id):
        glDeleteTextures(1, id_buf)


def create_framebuffer(width, height, target=GL_RGBA):
    """create an empty framebuffer"""
    id_buf = Buffer(GL_INT, 1)

    glGenFramebuffers(1, id_buf)
    fbo_id = id_buf.to_list()[0]

    if fbo_id == 0:
        print("Framebuffer error on creation")
        return -1

    tex_id = create_image(width, height)

    glBindFramebuffer(GL_FRAMEBUFFER, fbo_id)
    glFramebufferTexture(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, tex_id, 0)

    glGenRenderbuffers(1, id_buf)
    depth_id = id_buf.to_list()[0]

    glBindRenderbuffer(GL_RENDERBUFFER, depth_id)
    glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT32, width, height)

    # attach the depth buffer
    glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, depth_id)

    #glDrawBuffers(fbo_id, GL_COLOR_ATTACHMENT0)

    if not check_framebuffer_status(GL_DRAW_FRAMEBUFFER):
        delete_framebuffer(fbo_id)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        return -1

    glBindFramebuffer(GL_FRAMEBUFFER, 0)
    return fbo_id

def delete_framebuffer(fbo_id):
    """clear created framebuffer"""
    id_buf = Buffer(GL_INT, 1)
    id_buf.to_list()[0] = fbo_id

    if glIsFramebuffer(fbo_id):
        glDeleteFramebuffers(1, id_buf)
