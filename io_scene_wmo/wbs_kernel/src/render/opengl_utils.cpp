#include "opengl_utils.hpp"

#include <stdio.h>

using namespace wbs_kernel;

void COpenGLUtils::glew_init()
{
  GLenum err = glewInit();
  if (GLEW_OK != err)
  {
    /* Problem: glewInit failed, something is seriously wrong. */
    fprintf(stderr, "Error: %s\n", glewGetErrorString(err));
  }
}

void COpenGLUtils::set_blend_func(int srcRGB, int dstRGB, int srcAlpha, int dstAlpha)
{
  glBlendFuncSeparate(srcRGB, dstRGB, srcAlpha, dstAlpha);
}

