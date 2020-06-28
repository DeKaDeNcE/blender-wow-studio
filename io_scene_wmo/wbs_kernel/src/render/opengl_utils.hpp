#ifndef WBS_KERNEL_OPENGL_UTILS_HPP
#define WBS_KERNEL_OPENGL_UTILS_HPP

#include <glew.h>

namespace wbs_kernel
{
  class COpenGLUtils
  {
  public:
    static void glew_init();
    static void set_blend_func(int srcRGB, int dstRGB, int srcAlpha, int dstAlpha);
  };

}

#endif //WBS_KERNEL_OPENGL_UTILS_HPP
