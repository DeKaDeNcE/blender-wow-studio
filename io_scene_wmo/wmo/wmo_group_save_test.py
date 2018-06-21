import bpy
import bmesh
import sys


def get_linked_faces(f, uv, uv2, stack=0):
    if f.tag:
        return []

    f_linked = [f]
    mat_idx = f.material_index
    f.tag = True

    # Select edges that link two faces
    for link_edge in f.edges:
        if not len(link_edge.link_faces) == 2:
            continue

        for link_face in link_edge.link_faces:
            if not link_face.tag:
                continue

            # check if faces share the same material
            if link_face.material_index == mat_idx:

                # check if face is located within same UV island.
                linked_uvs = 0
                for loop in f.loops:

                    for l_loop in loop.vert.link_loops:
                        if l_loop.face is link_face \
                        and l_loop[uv].uv == loop[uv].uv \
                        and l_loop[uv2].uv == loop[uv2].uv:
                            linked_uvs += 1

                if linked_uvs >= 2 and stack < sys.getrecursionlimit() - 1:
                    f_linked.extend(get_linked_faces(link_face, uv, stack=stack + 1))

    return f_linked


def sort_geometry(obj):
    mesh = obj.data

    # create bmesh
    bm = bmesh.new()
    bm.from_object(obj, bpy.context.scene)

    # triangulate bmesh
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method=0, ngon_method=0)

    vertices = bm.verts
    edges = bm.edges
    faces = bm.faces

    vertices.ensure_lookup_table()
    edges.ensure_lookup_table()
    faces.ensure_lookup_table()

    # untag faces
    for face in faces:
        face.tag = False

    faces_set = set(faces)
    mat_batches = {}
    uv = bm.loops.layers.uv[0]
    uv2 = bm.loops.layers.uv[1]

    while faces_set:
        face = next(iter(faces_set))
        linked_faces = get_linked_faces(face, uv, uv2)
        mat_batches.setdefault(face.material_index, []).append(list(linked_faces))
        faces_set -= set(linked_faces)

    # bm.free()

    return mat_batches, bm


if __name__ == '__main__':
    mat_batches, bm = sort_geometry(bpy.context.object)
    for face in mat_batches[4][4]:
        bpy.context.object.data.polygons[face.index].select = True

    bm.free()

