"""
mouth.py — PlushyFaceKit
  build_crescent_mouth(config)  — wide arc smile + tongue geometry (MAIN)
  build_line_mouth(config)      — simple line/oval mouth
  build_lips_mouth(config)      — lips with optional heart + lipstick

Tongue design notes:
  - Basis shape key = all verts collapsed to center → invisible when closed
  - "tongue out" shape key = full oval → only visible when mouth opens
  - Unity: set tongue material Render Queue = mouth queue + 1
"""
import bpy
import bmesh
import math
from utils import make_mat, set_active, to_edit, to_object, apply_smooth_interp


# ── SHARED ANIMATION ──────────────────────────────────────────────────────────

def _keyframe_eating(mouth_obj, tongue_obj=None):
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end   = 250

    open_key = mouth_obj.data.shape_keys.key_blocks.get("mouth open")
    if not open_key:
        return

    mouth_chew = [
        (1,0.0),(60,0.0),(66,1.0),(73,0.35),
        (80,0.90),(87,0.30),(94,0.80),(101,0.20),(108,0.0),(250,0.0),
    ]
    for frame, val in mouth_chew:
        open_key.value = val
        open_key.keyframe_insert(data_path="value", frame=frame)

    if tongue_obj:
        tongue_key = tongue_obj.data.shape_keys.key_blocks.get("tongue out")
        if tongue_key:
            tongue_sched = [
                (1,0.0),(65,0.0),(70,1.0),(73,0.40),
                (80,0.95),(87,0.35),(94,0.85),(101,0.15),(107,0.0),(250,0.0),
            ]
            for frame, val in tongue_sched:
                tongue_key.value = val
                tongue_key.keyframe_insert(data_path="value", frame=frame)

    sk = mouth_obj.data.shape_keys
    if sk.animation_data and sk.animation_data.action:
        apply_smooth_interp(sk.animation_data.action)
    scene.frame_set(1)
    print("  OK eating animation keyframed.")


# ── CRESCENT MOUTH + TONGUE ───────────────────────────────────────────────────

def build_crescent_mouth(config):
    """
    Wide crescent smile (two circle arcs) with collapsed-basis tongue.
    """

    def arc_pts(half_w, dip, n):
        cy = (half_w**2 - dip**2) / (2.0 * dip)
        r  = math.sqrt(half_w**2 + cy**2)
        al = math.atan2(-cy, -half_w)
        ar = math.atan2(-cy,  half_w)
        return [(r * math.cos(al + i/n * (ar-al)), 0.0,
                 cy + r * math.sin(al + i/n * (ar-al))) for i in range(n+1)], cy, r

    n, half_w, dip_o, dip_i, m_z = 20, 0.52, 0.32, 0.06, -1.05
    outer_pts, cy_o, r_o = arc_pts(half_w, dip_o, n)
    inner_pts, cy_i, r_i = arc_pts(half_w, dip_i, n)
    z_off = m_z - (cy_o - r_o)
    outer_pts = [(x, y, z+z_off) for x,y,z in outer_pts]
    inner_pts = [(x, y, z+z_off) for x,y,z in inner_pts]

    # Mouth mesh
    md = bpy.data.meshes.new("PlushyMouth")
    obj = bpy.data.objects.new("PlushyMouth", md)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    bm = bmesh.new()
    ov = [bm.verts.new(p) for p in outer_pts]
    iv = [bm.verts.new(p) for p in reversed(inner_pts)][1:-1]
    bm.faces.new(ov + iv)
    bm.to_mesh(md)
    bm.free()

    to_edit()
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.inset(thickness=0.035, depth=0.0)
    bm2 = bmesh.from_edit_mesh(obj.data)
    max_a = max(f.calc_area() for f in bm2.faces)
    for f in bm2.faces:
        f.material_index = 0 if f.calc_area() >= max_a * 0.85 else 1
    bmesh.update_edit_mesh(obj.data)
    to_object()

    obj.data.materials.clear()
    obj.data.materials.append(make_mat("mouth_stroke", (0.02, 0.01, 0.01)))
    obj.data.materials.append(make_mat("mouth_cavity", (0.02, 0.01, 0.01)))

    sub = obj.modifiers.new(name="Subdivision", type="SUBSURF")
    sub.levels = 2

    to_edit()
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
    to_object()

    # Shape keys — mouth
    set_active(obj)
    bpy.ops.object.shape_key_add(from_mix=False)
    obj.data.shape_keys.key_blocks[0].name = "Basis"
    bpy.ops.object.shape_key_add(from_mix=False)
    obj.data.shape_keys.key_blocks[1].name = "mouth open"
    obj.active_shape_key_index = 1
    to_edit()
    bm3 = bmesh.from_edit_mesh(obj.data)
    all_z = [v.co.z for v in bm3.verts]
    mid_z = (max(all_z) + min(all_z)) / 2
    for v in bm3.verts:
        v.co.z += (-0.14 if v.co.z < mid_z else 0.05)
    bmesh.update_edit_mesh(obj.data)
    to_object()
    obj.active_shape_key_index = 0

    # Tongue — Basis = collapsed (invisible), "tongue out" = full oval
    t_z, t_y = -0.97, 0.01
    tmesh  = bpy.data.meshes.new("Tongue")
    tongue = bpy.data.objects.new("Tongue", tmesh)
    bpy.context.collection.objects.link(tongue)
    bpy.context.view_layer.objects.active = tongue

    bmt = bmesh.new()
    nt  = 20
    for i in range(nt):           # Basis: all verts at center = zero surface area
        bmt.verts.new((0.0, t_y, t_z))
    bmt.verts.ensure_lookup_table()
    face = bmt.faces.new(bmt.verts)
    bmesh.ops.recalc_face_normals(bmt, faces=[face])
    bmt.to_mesh(tmesh)
    bmt.free()

    tongue.data.materials.clear()
    mat_t = bpy.data.materials.new("tongue_mat")
    mat_t.use_nodes = True
    bt = mat_t.node_tree.nodes.get("Principled BSDF")
    bt.inputs["Base Color"].default_value = (0.85, 0.04, 0.06, 1.0)
    bt.inputs["Roughness"].default_value  = 0.35
    if "Specular IOR Level" in bt.inputs:
        bt.inputs["Specular IOR Level"].default_value = 0.8
    tongue.data.materials.append(mat_t)

    sub_t = tongue.modifiers.new("Subdivision", type="SUBSURF")
    sub_t.levels = 2

    # Shape keys — tongue out expands to full oval
    bpy.ops.object.shape_key_add(from_mix=False)
    tongue.data.shape_keys.key_blocks[0].name = "Basis"
    bpy.ops.object.shape_key_add(from_mix=False)
    tongue.data.shape_keys.key_blocks[1].name = "tongue out"
    tongue.active_shape_key_index = 1
    to_edit()
    bmt2 = bmesh.from_edit_mesh(tongue.data)
    bmt2.verts.ensure_lookup_table()
    for i, v in enumerate(bmt2.verts):
        a = (2 * math.pi * i) / nt
        v.co.x = 0.30 * math.cos(a)
        v.co.z = t_z + 0.09 * math.sin(a)
    bmesh.update_edit_mesh(tongue.data)
    to_object()
    tongue.active_shape_key_index = 0
    tongue.parent = obj

    _keyframe_eating(obj, tongue)
    print("OK crescent mouth + tongue built.")
    print("   Unity: tongue Render Queue = mouth queue + 1")
    return obj, None


# ── LINE MOUTH ────────────────────────────────────────────────────────────────

def build_line_mouth(config):
    bpy.ops.mesh.primitive_circle_add(vertices=16, radius=0.38, location=(0, 0, -1.05))
    mouth = bpy.context.active_object
    mouth.name = "PlushyMouth"
    mouth.rotation_euler[0] = math.radians(90)
    mouth.scale = (1.0, 1.0, 0.22)
    bpy.ops.object.transform_apply(rotation=True, scale=True)

    to_edit()
    bpy.ops.mesh.edge_face_add()
    bpy.ops.mesh.inset(thickness=0.025, depth=0)
    bm = bmesh.from_edit_mesh(mouth.data)
    min_a = min(f.calc_area() for f in bm.faces)
    for f in bm.faces:
        f.material_index = 1 if f.calc_area() <= min_a * 1.15 else 0
    bmesh.update_edit_mesh(mouth.data)
    to_object()

    mouth.data.materials.clear()
    mouth.data.materials.append(make_mat("mouth_stroke",       (0.05, 0.02, 0.01)))
    mouth.data.materials.append(make_mat("mouth_interior_mat", (0.02, 0.01, 0.01)))

    sub = mouth.modifiers.new(name="Subdivision", type="SUBSURF")
    sub.levels = 2

    to_edit()
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
    to_object()

    set_active(mouth)
    bpy.ops.object.shape_key_add(from_mix=False)
    mouth.data.shape_keys.key_blocks[0].name = "Basis"
    bpy.ops.object.shape_key_add(from_mix=False)
    mouth.data.shape_keys.key_blocks[1].name = "mouth open"
    mouth.active_shape_key_index = 1
    to_edit()
    bm2 = bmesh.from_edit_mesh(mouth.data)
    cz = sum(v.co.z for v in bm2.verts) / len(bm2.verts)
    for v in bm2.verts:
        v.co.z += (0.14 if v.co.z > cz else -0.10)
    bmesh.update_edit_mesh(mouth.data)
    to_object()
    mouth.active_shape_key_index = 0

    _keyframe_eating(mouth)
    print("OK line mouth built.")
    return mouth, None


# ── LIPS MOUTH ────────────────────────────────────────────────────────────────

def build_lips_mouth(config):
    lips_heart = config.get("lips_heart", False)

    bpy.ops.mesh.primitive_circle_add(vertices=12, radius=0.36, location=(0, 0, -1.10))
    lower = bpy.context.active_object
    lower.name = "PlushyMouth"
    lower.rotation_euler[0] = math.radians(90)
    lower.scale = (1.0, 1.0, 0.30)
    bpy.ops.object.transform_apply(rotation=True, scale=True)

    lower.data.materials.clear()
    lower.data.materials.append(make_mat("lip_mat",   (0.65, 0.20, 0.20), roughness=0.80))
    lower.data.materials.append(make_mat("mouth_mat", (0.02, 0.01, 0.01)))
    if lips_heart:
        lower.data.materials.append(make_mat("lipstick_mat", (0.80, 0.05, 0.10),
                                              roughness=0.55, specular=0.3))

    to_edit()
    bpy.ops.mesh.edge_face_add()
    bpy.ops.mesh.inset(thickness=0.03, depth=0)
    bm = bmesh.from_edit_mesh(lower.data)
    min_a = min(f.calc_area() for f in bm.faces)
    for f in bm.faces:
        f.material_index = 0 if f.calc_area() > min_a * 1.15 else 1
    bmesh.update_edit_mesh(lower.data)
    to_object()

    # Cupid bow
    to_edit()
    bm2 = bmesh.from_edit_mesh(lower.data)
    top_v = sorted(bm2.verts, key=lambda v: v.co.z, reverse=True)[:6]
    for v in top_v:
        v.co.z += (-0.06 if abs(v.co.x) < 0.12 else 0.04)
    bmesh.update_edit_mesh(lower.data)
    to_object()

    if lips_heart:
        to_edit()
        bm3 = bmesh.from_edit_mesh(lower.data)
        for f in bm3.faces:
            f.select = f.calc_center_median().z > 0.0
        bmesh.update_edit_mesh(lower.data)
        bpy.ops.mesh.inset(thickness=0.05, depth=0.01)
        bm3 = bmesh.from_edit_mesh(lower.data)
        for f in bm3.faces:
            if f.select:
                f.material_index = 2
        bmesh.update_edit_mesh(lower.data)
        to_object()

    sub = lower.modifiers.new(name="Subdivision", type="SUBSURF")
    sub.levels = 2

    to_edit()
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
    to_object()

    set_active(lower)
    bpy.ops.object.shape_key_add(from_mix=False)
    lower.data.shape_keys.key_blocks[0].name = "Basis"
    bpy.ops.object.shape_key_add(from_mix=False)
    lower.data.shape_keys.key_blocks[1].name = "mouth open"
    lower.active_shape_key_index = 1
    to_edit()
    bm4 = bmesh.from_edit_mesh(lower.data)
    cz = sum(v.co.z for v in bm4.verts) / len(bm4.verts)
    for v in bm4.verts:
        v.co.z += (0.12 if v.co.z > cz else -0.09)
    bmesh.update_edit_mesh(lower.data)
    to_object()
    lower.active_shape_key_index = 0

    _keyframe_eating(lower)
    print(f"OK lips mouth built (heart={lips_heart}).")
    return lower, None
