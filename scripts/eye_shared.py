"""
eye_shared.py — PlushyFaceKit
All private eye helpers shared by almond and circle builders.
  _build_eye_base()      — create primitive, fill, inset, mirror, flatten
  _create_eye_rig()      — bone hierarchy
  _bind_eye_mesh()       — vertex groups + armature modifier
  _add_crescent_keys()   — shape keys that close into a sine arc (crescent blink)
  _build_uv_eye_shader() — UV-based emission shader: pupil/iris/sclera/bubble
  _create_blink_anim()   — keyframe the blink schedule
"""
import bpy
import bmesh
import math
from mathutils import Vector
from utils import deselect_all, set_active, to_object, to_edit, apply_smooth_interp


# ── PRIMITIVE BASE ────────────────────────────────────────────────────────────

def _build_eye_base(vertices, radius, z_rotate_deg):
    """
    Build a single flat eye circle (left side only at x=-0.6).
    Returns the eye object with flat mesh, mirrored to right side,
    UV unwrapped, both inner faces assigned to mat 1/2.
    """
    bpy.ops.mesh.primitive_circle_add(
        vertices=vertices, radius=radius, location=(-0.6, 0, 0.1)
    )
    eye = bpy.context.active_object
    eye.name = "Eyes"

    if z_rotate_deg:
        eye.rotation_euler[2] = math.radians(z_rotate_deg)
    eye.rotation_euler[0] = math.radians(90)
    bpy.ops.object.transform_apply(rotation=True)

    # Fill + single inset for border ring
    to_edit()
    bpy.ops.mesh.edge_face_add()
    bpy.ops.mesh.inset(thickness=0.045, depth=0)

    # Flatten completely — no Y depth, no dome shadow
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.transform.resize(value=(1, 0, 1), orient_type="GLOBAL")

    # Mirror to right eye FIRST
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.symmetrize(direction="NEGATIVE_X")
    to_object()

    # Add material slots BEFORE assigning indices (clear() resets indices to 0)
    eye.data.materials.clear()
    from utils import make_mat
    eye.data.materials.append(make_mat("eye stroke",       (0.0, 0.0, 0.0)))
    eye.data.materials.append(make_mat("eye inside left",  (1.0, 1.0, 1.0)))
    eye.data.materials.append(make_mat("eye inside right", (1.0, 1.0, 1.0)))

    # Now assign by VERTEX COUNT — inner filled polygon has the most verts
    to_edit()
    bm = bmesh.from_edit_mesh(eye.data)
    max_verts = max(len(f.verts) for f in bm.faces)
    for f in bm.faces:
        if len(f.verts) >= max_verts * 0.8:
            f.material_index = 1 if f.calc_center_median().x <= 0 else 2
        else:
            f.material_index = 0
    bmesh.update_edit_mesh(eye.data)

    # UV unwrap each eye as its own island
    bpy.ops.mesh.select_all(action="DESELECT")
    bm = bmesh.from_edit_mesh(eye.data)
    for f in bm.faces:
        f.select = f.calc_center_median().x <= 0
    bmesh.update_edit_mesh(eye.data)
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.0)

    bpy.ops.mesh.select_all(action="DESELECT")
    bm = bmesh.from_edit_mesh(eye.data)
    for f in bm.faces:
        f.select = f.calc_center_median().x > 0
    bmesh.update_edit_mesh(eye.data)
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.0)

    to_object()

    sub = eye.modifiers.new(name="Subdivision", type="SUBSURF")
    sub.levels       = 2
    sub.render_levels = 2

    return eye


# ── RIG ───────────────────────────────────────────────────────────────────────

def _create_eye_rig():
    deselect_all()
    bpy.ops.object.armature_add(location=(0, 0, 0))
    arm = bpy.context.active_object
    arm.name = arm.data.name = "irig"
    arm.show_in_front = True

    to_edit()
    ebs = arm.data.edit_bones
    for b in list(ebs):
        ebs.remove(b)

    def bone(name, head, tail, deform=False, parent=None):
        b = ebs.new(name)
        b.head = Vector(head)
        b.tail = Vector(tail)
        b.use_deform = deform
        if parent:
            b.parent = ebs[parent]
        return b

    bone("eye root",    (0,    0, 0.0), (0,    0, 0.20))
    bone("eye.root.l",  (-0.6, 0, 0.1), (-0.6, 0, 0.30), parent="eye root")
    bone("eye.root.r",  ( 0.6, 0, 0.1), ( 0.6, 0, 0.30), parent="eye root")
    bone("pupil.l",     (-0.60,0,0.10), (-0.60,0,0.22), parent="eye.root.l")
    bone("eye.close.l", (-0.60,0,0.32), (-0.60,0,0.44), parent="eye.root.l")
    bone("eye.in.l",    (-0.35,0,0.10), (-0.25,0,0.10), deform=True, parent="eye.root.l")
    bone("eye.out.l",   (-0.85,0,0.10), (-0.95,0,0.10), deform=True, parent="eye.root.l")
    bone("eye.mid.l",   (-0.60,0,0.30), (-0.60,0,0.40), deform=True, parent="eye.root.l")
    bone("pupil.r",     ( 0.60,0,0.10), ( 0.60,0,0.22), parent="eye.root.r")
    bone("eye.close.r", ( 0.60,0,0.32), ( 0.60,0,0.44), parent="eye.root.r")
    bone("eye.in.r",    ( 0.35,0,0.10), ( 0.25,0,0.10), deform=True, parent="eye.root.r")
    bone("eye.out.r",   ( 0.85,0,0.10), ( 0.95,0,0.10), deform=True, parent="eye.root.r")
    bone("eye.mid.r",   ( 0.60,0,0.30), ( 0.60,0,0.40), deform=True, parent="eye.root.r")
    to_object()
    return arm


# ── BIND ─────────────────────────────────────────────────────────────────────

def _bind_eye_mesh(eye, arm):
    to_object()
    deselect_all()
    eye.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type="ARMATURE_NAME")

    set_active(eye)
    groups = ["eye.in.l","eye.out.l","eye.mid.l","eye.in.r","eye.out.r","eye.mid.r"]
    for gn in groups:
        if gn not in eye.vertex_groups:
            eye.vertex_groups.new(name=gn)

    to_edit()
    bm = bmesh.from_edit_mesh(eye.data)
    assignments = {}
    for v in bm.verts:
        x, ax = v.co.x, abs(v.co.x)
        side  = "l" if x < 0 else "r"
        grp   = (f"eye.in.{side}"  if ax < 0.25 else
                 f"eye.out.{side}" if ax > 0.78 else
                 f"eye.mid.{side}")
        assignments.setdefault(grp, []).append(v.index)
    to_object()

    for grp, idxs in assignments.items():
        vg = eye.vertex_groups.get(grp)
        if vg:
            vg.add(idxs, 1.0, "REPLACE")

    arm_mod = next((m for m in eye.modifiers if m.type == "ARMATURE"), None)
    if arm_mod:
        bpy.ops.object.modifier_move_to_index(modifier=arm_mod.name, index=0)


# ── CRESCENT SHAPE KEYS ───────────────────────────────────────────────────────

def _add_crescent_keys(eye):
    """
    Blink closes into a horizontal sine-arc crescent.
    Each eye side's verts compress to a curved line — not a flat squish.
    """
    set_active(eye)
    bpy.ops.object.shape_key_add(from_mix=False)
    eye.data.shape_keys.key_blocks[0].name = "Basis"

    eye_defs = [
        ("eye close left",  -0.6,  -1),
        ("eye close right",  0.6,   1),
    ]
    r           = 0.35
    crescent_h  = 0.07

    for key_name, cx, x_sign in eye_defs:
        bpy.ops.object.shape_key_add(from_mix=False)
        idx = len(eye.data.shape_keys.key_blocks) - 1
        eye.data.shape_keys.key_blocks[idx].name = key_name
        eye.active_shape_key_index = idx

        to_edit()
        bm = bmesh.from_edit_mesh(eye.data)
        for v in bm.verts:
            if (x_sign < 0 and v.co.x > -0.1) or (x_sign > 0 and v.co.x < 0.1):
                continue
            x_norm = max(-1.0, min(1.0, (v.co.x - cx) / r))
            v.co.z = 0.1 + crescent_h * math.sin(math.pi * (x_norm + 1) / 2)
        bmesh.update_edit_mesh(eye.data)
        to_object()

    eye.active_shape_key_index = 0
    print("  OK crescent shape keys added.")


# ── UV EMISSION SHADER ────────────────────────────────────────────────────────

def _build_uv_eye_shader(side="left"):
    """
    Fully procedural from UV coords — no empties, no drift, no dome shadow.
    Draws: dark border ring → white sclera → blue iris → black pupil → bubble.
    """
    mat = bpy.data.materials.get(f"eye inside {side}")
    if not mat:
        return
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    lk = nt.links.new

    def N(t, x, y):
        n = nt.nodes.new(t)
        n.location = (x, y)
        return n

    out  = N("ShaderNodeOutputMaterial", 800, 0)
    emit = N("ShaderNodeEmission",        600, 0)
    emit.inputs["Strength"].default_value = 1.0
    lk(emit.outputs["Emission"], out.inputs["Surface"])

    # UV → center at (0.5, 0.5) → normalized distance 0-1
    uv  = N("ShaderNodeTexCoord",    -800, 100)
    sep = N("ShaderNodeSeparateXYZ", -620, 100)
    lk(uv.outputs["UV"], sep.inputs["Vector"])

    su = N("ShaderNodeMath", -440, 180)
    su.operation = "SUBTRACT"
    su.inputs[1].default_value = 0.5
    lk(sep.outputs["X"], su.inputs[0])

    sv = N("ShaderNodeMath", -440, 50)
    sv.operation = "SUBTRACT"
    sv.inputs[1].default_value = 0.5
    lk(sep.outputs["Y"], sv.inputs[0])

    comb = N("ShaderNodeCombineXYZ", -260, 120)
    lk(su.outputs["Value"], comb.inputs["X"])
    lk(sv.outputs["Value"], comb.inputs["Y"])

    vlen = N("ShaderNodeVectorMath", -80, 120)
    vlen.operation = "LENGTH"
    lk(comb.outputs["Vector"], vlen.inputs[0])

    norm = N("ShaderNodeMath", 80, 120)
    norm.operation = "MULTIPLY"
    norm.inputs[1].default_value = 2.0
    lk(vlen.outputs["Value"], norm.inputs[0])

    # Color ramp: pupil → iris ring → sclera → border ring
    cr = N("ShaderNodeValToRGB", 260, 120)
    cr.color_ramp.interpolation = "EASE"
    cr.color_ramp.elements[0].position = 0.00
    cr.color_ramp.elements[0].color    = (0.0,  0.0,  0.0,  1.0)  # pupil
    cr.color_ramp.elements[1].position = 0.28
    cr.color_ramp.elements[1].color    = (0.0,  0.0,  0.0,  1.0)  # pupil edge
    e1 = cr.color_ramp.elements.new(0.38)
    e1.color = (0.10, 0.35, 0.80, 1.0)                             # iris ring
    e2 = cr.color_ramp.elements.new(0.50)
    e2.color = (1.0,  1.0,  1.0,  1.0)                             # white sclera
    e3 = cr.color_ramp.elements.new(0.82)
    e3.color = (1.0,  1.0,  1.0,  1.0)                             # sclera outer
    e4 = cr.color_ramp.elements.new(0.95)
    e4.color = (0.0,  0.0,  0.0,  1.0)                             # dark border
    lk(norm.outputs["Value"], cr.inputs["Fac"])

    # Specular bubble — offset upper-right in UV space
    su2 = N("ShaderNodeMath", -440, -120)
    su2.operation = "SUBTRACT"
    su2.inputs[1].default_value = 0.63
    lk(sep.outputs["X"], su2.inputs[0])

    sv2 = N("ShaderNodeMath", -440, -220)
    sv2.operation = "SUBTRACT"
    sv2.inputs[1].default_value = 0.65
    lk(sep.outputs["Y"], sv2.inputs[0])

    cb = N("ShaderNodeCombineXYZ", -260, -160)
    lk(su2.outputs["Value"], cb.inputs["X"])
    lk(sv2.outputs["Value"], cb.inputs["Y"])

    vb = N("ShaderNodeVectorMath", -80, -160)
    vb.operation = "LENGTH"
    lk(cb.outputs["Vector"], vb.inputs[0])

    crb = N("ShaderNodeValToRGB", 80, -160)
    crb.color_ramp.interpolation = "EASE"
    crb.color_ramp.elements[0].position = 0.0
    crb.color_ramp.elements[0].color    = (1.0, 1.0, 1.0, 1.0)
    crb.color_ramp.elements[1].position = 0.10
    crb.color_ramp.elements[1].color    = (0.0, 0.0, 0.0, 1.0)
    lk(vb.outputs["Value"], crb.inputs["Fac"])

    # Screen blend: bubble over base
    mx = N("ShaderNodeMixRGB", 480, 0)
    mx.blend_type = "SCREEN"
    mx.inputs["Fac"].default_value = 0.85
    lk(cr.outputs["Color"],  mx.inputs["Color1"])
    lk(crb.outputs["Color"], mx.inputs["Color2"])

    lk(mx.outputs["Color"], emit.inputs["Color"])
    print(f"  OK UV shader: eye inside {side}")


# ── BLINK ANIMATION ───────────────────────────────────────────────────────────

def _create_blink_anim(eye):
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end   = 250
    sk = eye.data.shape_keys
    if not sk:
        return
    schedule = {
        "eye close left":  [(1,0.0),(30,1.0),(45,0.0),(130,1.0),(145,0.0),(250,0.0)],
        "eye close right": [(1,0.0),(30,1.0),(45,0.0),(130,1.0),(145,0.0),(250,0.0)],
    }
    for key_name, frames in schedule.items():
        kb = sk.key_blocks.get(key_name)
        if not kb:
            continue
        for frame, value in frames:
            kb.value = value
            kb.keyframe_insert(data_path="value", frame=frame)
    if sk.animation_data and sk.animation_data.action:
        apply_smooth_interp(sk.animation_data.action)
    scene.frame_set(1)
    print("  OK blink animation keyframed.")
