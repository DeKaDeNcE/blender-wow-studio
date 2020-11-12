import os
import gpu

from typing import Tuple, Dict, Any

from ..utils.misc import singleton, Sequence


class ShaderPermutationsFormat:
    M2 = 0,
    WMO = 1,
    ADT = 2


class ShaderPermutationsManager:

    shader_source_path: str
    extra_defines: Dict[str, Any]

    def __init__(self):
        self.shader_permutations: Dict = {}
        self.shader_source: str
        self.default_shader: gpu.types.GPUShader

        rel_path = 'shaders\\glsl330\\{}.glsl'.format(self.shader_source_path) if os.name == 'nt'\
            else 'shaders/glsl330/{}.glsl'.format(self.shader_source_path)

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), rel_path)) as f:
            self.shader_source = "".join(f.readlines())

        rel_path = 'shaders\\glsl330\\default.glsl' if os.name == 'nt' else 'shaders/glsl330/default.glsl'

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),  rel_path)) as f:
            shader_source_fallback = "".join(f.readlines())

            vert_shader_string_perm = "#define COMPILING_VS {}\n" \
                                      "{}".format(1, shader_source_fallback)
            frag_shader_string_perm = "#define COMPILING_FS {}\n" \
                                      "{}".format(1, shader_source_fallback)

            self.default_shader = gpu.types.GPUShader(vert_shader_string_perm, frag_shader_string_perm)

    def _compile_shader_permutation(self
                                    , vert_shader_id: int
                                    , frag_shader_id: int) -> gpu.types.GPUShader:

        vert_shader_string_perm = "#define COMPILING_VS {}\n" \
                                  "#define VERTEXSHADER {}\n" \
                                  "{}".format(1, vert_shader_id, self.shader_source)
        frag_shader_string_perm = "#define COMPILING_FS {}\n" \
                                  "#define FRAGMENTSHADER {}\n" \
                                  "{}".format(1, frag_shader_id, self.shader_source)

        shader = gpu.types.GPUShader(vert_shader_string_perm, frag_shader_string_perm)
        self.shader_permutations[vert_shader_id, frag_shader_id] = shader

        return shader

    def get_shader_by_id(self
                         , vert_shader_id: int
                         , frag_shader_id: int) -> gpu.types.GPUShader:

        shader = self.shader_permutations.get((vert_shader_id, frag_shader_id))

        if not shader:
            shader = self._compile_shader_permutation(vert_shader_id, frag_shader_id)

        return shader
