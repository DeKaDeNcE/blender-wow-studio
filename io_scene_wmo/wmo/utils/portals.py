import bpy
import mathutils
import sys

from math import pi
from ...pywowlib.file_formats.wmo_format_root import PortalRelation


def calculate_portal_direction( group_obj : bpy.types.Object
                              , portal_obj : bpy.types.Object
                              , bound_relation : PortalRelation
                              , bound_relation_side : int
                              ) -> int:
    mesh = group_obj.data
    portal_mesh = portal_obj.data
    normal = portal_obj.data.polygons[0].normal

    for poly in mesh.polygons:
        poly_normal = mathutils.Vector(poly.normal)
        g_center = group_obj.matrix_world @ poly.center + poly_normal * sys.float_info.epsilon

        dist = normal[0] * g_center[0] + normal[1] * g_center[1] \
               + normal[2] * g_center[2] - portal_mesh.polygons[0].normal[0] \
                                           * portal_mesh.vertices[portal_mesh.polygons[0].vertices[0]].co[0] \
               - portal_mesh.polygons[0].normal[1] \
                 * portal_mesh.vertices[portal_mesh.polygons[0].vertices[0]].co[1] \
               - portal_mesh.polygons[0].normal[2] \
                 * portal_mesh.vertices[portal_mesh.polygons[0].vertices[0]].co[2]

        if dist == 0:
            continue

        for portal_poly in portal_mesh.polygons:

            direction = portal_poly.center - g_center
            length = mathutils.Vector(direction).length
            direction.normalize()

            angle = mathutils.Vector(direction).angle(poly.normal, None)

            if angle is None or angle >= pi * 0.5:
                continue

            ray_cast_result = bpy.context.scene.ray_cast(g_center, direction)

            if not ray_cast_result[0] \
                    or ray_cast_result[4].name == portal_obj.name \
                    or mathutils.Vector(
                        (ray_cast_result[1][0] - g_center[0], ray_cast_result[1][1] - g_center[1],
                         ray_cast_result[1][2] - g_center[2])).length > length:
                result = 1 if dist > 0 else -1

                if bound_relation_side == 0:
                    bound_relation.Side = -result

                return result

    return 0
