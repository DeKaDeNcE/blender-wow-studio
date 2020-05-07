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
