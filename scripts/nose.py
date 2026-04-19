"""
nose.py — PlushyFaceKit
  build_oval_nose(config)     — soft button oval, UV sphere base
  build_triangle_nose(config) — rounded triangle, 3-vert circle base
"""
import bpy
import bmesh
import math
from utils import make_mat, to_edit, to_object


def build_oval_nose(config):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=10, ring_count=7, radius=1.0, location=(0, 0, -0.55)
    )
    nose = bpy.context.active_object
    nose.name = "PlushyNose"
    nose.scale = (0.22, 0.15, 0.13)
    bpy.ops.object.transform_apply(scale=True)

    # Flatten back face, puff front slightly
    to_edit()
    bm = bmesh.from_edit_mesh(nose.data)
    for v in bm.verts:
        if v.co.y < -0.10:
            v.co.y = -0.11
        if v.co.y > 0.08:
            v.co.y += 0.015
    bmesh.update_edit_mesh(nose.data)
    to_object()

    nose.data.materials.clear()
    nose.data.materials.append(make_mat("nose_mat", (0.08, 0.04, 0.02)))

    to_edit()
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
    to_object()

    print("OK oval nose built.")
    return nose, None


def build_triangle_nose(config):
    bpy.ops.mesh.primitive_circle_add(vertices=3, radius=0.22, location=(0, 0, -0.55))
    nose = bpy.context.active_object
    nose.name = "PlushyNose"
    nose.rotation_euler[2] = math.radians(180)
    nose.rotation_euler[0] = math.radians(90)
    bpy.ops.object.transform_apply(rotation=True)
    nose.scale = (1.2, 1.0, 0.85)
    bpy.ops.object.transform_apply(scale=True)

    to_edit()
    bpy.ops.mesh.edge_face_add()
    bpy.ops.mesh.inset(thickness=0.03, depth=0.0)
    bpy.ops.mesh.inset(thickness=0.02, depth=0.02)

    bm = bmesh.from_edit_mesh(nose.data)
    nose.data.materials.clear()
    nose.data.materials.append(make_mat("nose_mat",       (0.06, 0.03, 0.01)))
    nose.data.materials.append(make_mat("nose_inner_mat", (0.12, 0.06, 0.03)))
    areas = sorted(set(round(f.calc_area(), 5) for f in bm.faces))
    for face in bm.faces:
        face.material_index = 0 if round(face.calc_area(), 5) == areas[-1] else 1
    bmesh.update_edit_mesh(nose.data)
    to_object()

    sub = nose.modifiers.new(name="Subdivision", type="SUBSURF")
    sub.levels = 2

    to_edit()
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
    to_object()

    print("OK triangle nose built.")
    return nose, None
