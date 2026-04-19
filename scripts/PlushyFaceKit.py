"""
Plushy Face Kit — Blender 5.0.1
Stage 1: Modular script — run from Scripting tab (Alt+P)
Parts: Eyes (almond/circle), Nose (triangle/oval), Mouth (line/lips)
Author: Built with Claude + Dontavius
"""

import bpy
import bmesh
import math
from mathutils import Vector

# ──────────────────────────────────────────────────────────
# CONFIG — edit these before running
# ──────────────────────────────────────────────────────────

CONFIG = {
    "eye_style":       "almond",   # "almond" | "circle"
    "nose_style":      "oval",     # "oval"   | "triangle"
    "mouth_style":     "crescent", # "crescent" | "line" | "lips"
    "lips_heart":      True,       # True = heart inset + lipstick on lips
    "generate_eyes":   True,
    "generate_nose":   True,
    "generate_mouth":  True,
    "export":          False,      # set True to auto-export FBX on run
    "export_path":     "C:/Users/Dontavius/Desktop/PlushyFaceKit.fbx",
}

# ──────────────────────────────────────────────────────────
# UTILITIES  (match original eye script exactly)
# ──────────────────────────────────────────────────────────

def deselect_all():
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")

def set_active(obj):
    deselect_all()
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

def to_object():
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

def to_edit():
    bpy.ops.object.mode_set(mode="EDIT")

def to_pose():
    bpy.ops.object.mode_set(mode="POSE")

def make_mat(name, rgb, roughness=0.95, specular=0.0):
    m = bpy.data.materials.new(name=name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = specular
    return m

def apply_smooth_interp(action):
    """Apply bezier ease-in-out to all fcurve keyframes in an action."""
    if not action:
        return
    try:
        for layer in action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for fc in cb.fcurves:
                        for kp in fc.keyframe_points:
                            kp.interpolation = "BEZIER"
                            kp.easing = "EASE_IN_OUT"
    except Exception:
        # Fallback for older action API
        try:
            for fc in action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "BEZIER"
                    kp.easing = "EASE_IN_OUT"
        except Exception:
            pass

# ──────────────────────────────────────────────────────────
# CLEANUP
# ──────────────────────────────────────────────────────────

def cleanup():
    to_object()
    kill = [
        "Eyes", "irig",
        "PlushyNose",
        "PlushyMouth", "mouth_rig",
        "empty iris l", "empty iris r",
        "empty eye close l", "empty eye close r",
        "Cube",
    ]
    for obj in list(bpy.data.objects):
        base = obj.name.rstrip("0123456789").rstrip(".")
        if base in kill or obj.name in kill:
            bpy.data.objects.remove(obj, do_unlink=True)

    kill_mats = [
        "eye stroke", "eye inside left", "eye inside right",
        "nose_mat", "mouth_mat", "lip_mat", "lipstick_mat",
    ]
    for name in kill_mats:
        m = bpy.data.materials.get(name)
        if m:
            bpy.data.materials.remove(m, do_unlink=True)

    for mesh in list(bpy.data.meshes):
        if any(mesh.name.startswith(p) for p in ["Eyes","Circle","PlushyNose","PlushyMouth"]):
            bpy.data.meshes.remove(mesh, do_unlink=True)

    for arm in list(bpy.data.armatures):
        if arm.name.startswith("irig") or arm.name.startswith("mouth_rig"):
            bpy.data.armatures.remove(arm, do_unlink=True)

    for action in list(bpy.data.actions):
        if any(action.name.startswith(p) for p in ["BlinkAction","MouthAction"]):
            bpy.data.actions.remove(action, do_unlink=True)

    print("OK Cleaned up.")

# ──────────────────────────────────────────────────────────
# EYES — SHARED RIG (used by both almond and circle)
# ──────────────────────────────────────────────────────────

def _create_eye_rig():
    deselect_all()
    bpy.ops.object.armature_add(location=(0, 0, 0))
    arm = bpy.context.active_object
    arm.name = "irig"
    arm.data.name = "irig"
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

def _bind_eye_mesh(eye, arm):
    to_object()
    deselect_all()
    eye.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type="ARMATURE_NAME")
    set_active(eye)
    for gn in ["eye.in.l","eye.out.l","eye.mid.l","eye.in.r","eye.out.r","eye.mid.r"]:
        if gn not in eye.vertex_groups:
            eye.vertex_groups.new(name=gn)
    to_edit()
    bm = bmesh.from_edit_mesh(eye.data)
    assignments = {}
    for v in bm.verts:
        x = v.co.x
        ax = abs(x)
        side = "l" if x < 0 else "r"
        if ax < 0.25:
            grp = f"eye.in.{side}"
        elif ax > 0.78:
            grp = f"eye.out.{side}"
        else:
            grp = f"eye.mid.{side}"
        assignments.setdefault(grp, []).append(v.index)
    to_object()
    for grp, indices in assignments.items():
        vg = eye.vertex_groups.get(grp)
        if vg:
            vg.add(indices, 1.0, "REPLACE")
    arm_mod = next((m for m in eye.modifiers if m.type == "ARMATURE"), None)
    if arm_mod:
        bpy.ops.object.modifier_move_to_index(modifier=arm_mod.name, index=0)

def _add_eye_shape_keys(eye):
    set_active(eye)
    bpy.ops.object.shape_key_add(from_mix=False)
    eye.data.shape_keys.key_blocks[0].name = "Basis"

    def add_key(name, x_sign):
        bpy.ops.object.shape_key_add(from_mix=False)
        idx = len(eye.data.shape_keys.key_blocks) - 1
        eye.data.shape_keys.key_blocks[idx].name = name
        eye.active_shape_key_index = idx
        to_edit()
        bm = bmesh.from_edit_mesh(eye.data)
        verts = [v for v in bm.verts if (v.co.x * x_sign) > 0.05]
        if verts:
            cz = sum(v.co.z for v in verts) / len(verts)
            for v in verts:
                v.co.z = cz + (v.co.z - cz) * 0.04
        bmesh.update_edit_mesh(eye.data)
        to_object()

    add_key("eye close left",  -1)
    add_key("eye close right", +1)
    eye.active_shape_key_index = 0

def _add_eye_drivers(eye, arm):
    sk = eye.data.shape_keys
    if not sk:
        return
    for key_name, bone_name in [("eye close left","eye.close.l"),("eye close right","eye.close.r")]:
        kb = sk.key_blocks.get(key_name)
        if not kb:
            continue
        try:
            kb.driver_remove("value")
        except Exception:
            pass
        fc  = kb.driver_add("value")
        drv = fc.driver
        drv.type       = "SCRIPTED"
        drv.expression = "max(0.0, min(1.0, (var - 0.32) * 3.5))"
        var             = drv.variables.new()
        var.name        = "var"
        var.type        = "TRANSFORMS"
        tgt             = var.targets[0]
        tgt.id          = arm
        tgt.bone_target = bone_name
        tgt.transform_type  = "LOC_Z"
        tgt.transform_space = "WORLD_SPACE"

def _create_eye_empties(arm):
    specs = [
        ("empty iris l",      (-0.60,0,0.10), "pupil.l"),
        ("empty iris r",      ( 0.60,0,0.10), "pupil.r"),
        ("empty eye close l", (-0.60,0,0.35), "eye.close.l"),
        ("empty eye close r", ( 0.60,0,0.35), "eye.close.r"),
    ]
    empties = {}
    for name, loc, bone_name in specs:
        bpy.ops.object.empty_add(type="PLAIN_AXES", location=loc)
        emp = bpy.context.active_object
        emp.name = name
        emp.scale = (0.05,0.05,0.05)
        bpy.ops.object.transform_apply(scale=True)
        empties[name] = emp
        if bone_name in arm.data.bones:
            to_object()
            deselect_all()
            emp.select_set(True)
            arm.select_set(True)
            bpy.context.view_layer.objects.active = arm
            arm.data.bones.active = arm.data.bones[bone_name]
            bpy.ops.object.parent_set(type="BONE")
    to_object()
    return empties

def _setup_eye_shader(eye, empties, side="left"):
    sl  = "l" if side == "left" else "r"
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

    out  = N("ShaderNodeOutputMaterial", 900, 0)
    bsdf = N("ShaderNodeBsdfPrincipled",  650, 0)
    bsdf.inputs["Roughness"].default_value = 0.15
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.5
    lk(bsdf.outputs["BSDF"], out.inputs["Surface"])

    tc_iris = N("ShaderNodeTexCoord", -800, 300)
    iris_emp = empties.get(f"empty iris {sl}")
    if iris_emp:
        tc_iris.object = iris_emp

    vm_len = N("ShaderNodeVectorMath", -580, 300)
    vm_len.operation = "LENGTH"
    lk(tc_iris.outputs["Object"], vm_len.inputs[0])

    # Pupil → iris ring → white sclera
    cr_pupil = N("ShaderNodeValToRGB", -360, 400)
    cr_pupil.color_ramp.interpolation = "EASE"
    cr_pupil.color_ramp.elements[0].position = 0.0
    cr_pupil.color_ramp.elements[0].color    = (0.0, 0.0, 0.0, 1.0)
    cr_pupil.color_ramp.elements[1].position = 0.22
    cr_pupil.color_ramp.elements[1].color    = (0.0, 0.0, 0.0, 1.0)
    el_iris   = cr_pupil.color_ramp.elements.new(0.30)
    el_iris.color = (0.15, 0.40, 0.85, 1.0)
    el_sclera = cr_pupil.color_ramp.elements.new(0.42)
    el_sclera.color = (0.95, 0.95, 0.95, 1.0)
    lk(vm_len.outputs["Value"], cr_pupil.inputs["Fac"])

    # Specular bubble highlight — offset circle
    vm_sub = N("ShaderNodeVectorMath", -800, 0)
    vm_sub.operation = "SUBTRACT"
    vm_sub.inputs[1].default_value = (0.12, 0.0, -0.10)
    lk(tc_iris.outputs["Object"], vm_sub.inputs[0])

    vm_bubble = N("ShaderNodeVectorMath", -580, 0)
    vm_bubble.operation = "LENGTH"
    lk(vm_sub.outputs["Vector"], vm_bubble.inputs[0])

    cr_bubble = N("ShaderNodeValToRGB", -360, 0)
    cr_bubble.color_ramp.interpolation = "EASE"
    cr_bubble.color_ramp.elements[0].position = 0.0
    cr_bubble.color_ramp.elements[0].color    = (1.0, 1.0, 1.0, 1.0)
    cr_bubble.color_ramp.elements[1].position = 0.10
    cr_bubble.color_ramp.elements[1].color    = (0.0, 0.0, 0.0, 1.0)
    lk(vm_bubble.outputs["Value"], cr_bubble.inputs["Fac"])

    # Blink mask
    tc_close = N("ShaderNodeTexCoord", -800, -300)
    close_emp = empties.get(f"empty eye close {sl}")
    if close_emp:
        tc_close.object = close_emp

    sep = N("ShaderNodeSeparateXYZ", -580, -300)
    lk(tc_close.outputs["Object"], sep.inputs["Vector"])

    cr_blink = N("ShaderNodeValToRGB", -360, -300)
    cr_blink.color_ramp.elements[0].color    = (0.0, 0.0, 0.0, 1.0)
    cr_blink.color_ramp.elements[1].position = 0.18
    cr_blink.color_ramp.elements[1].color    = (1.0, 1.0, 1.0, 1.0)
    lk(sep.outputs["Z"], cr_blink.inputs["Fac"])

    # Screen blend: bubble over base
    mix_bubble = N("ShaderNodeMixRGB", -80, 200)
    mix_bubble.blend_type = "SCREEN"
    mix_bubble.inputs["Fac"].default_value = 0.85
    lk(cr_pupil.outputs["Color"],  mix_bubble.inputs["Color1"])
    lk(cr_bubble.outputs["Color"], mix_bubble.inputs["Color2"])

    # Blink multiply
    mix_blink = N("ShaderNodeMixRGB", 200, 100)
    mix_blink.blend_type = "MULTIPLY"
    mix_blink.inputs["Fac"].default_value = 1.0
    lk(mix_bubble.outputs["Color"], mix_blink.inputs["Color1"])
    lk(cr_blink.outputs["Color"],   mix_blink.inputs["Color2"])

    lk(mix_blink.outputs["Color"], bsdf.inputs["Base Color"])
    print(f"  OK Shader: eye inside {side}")


def _create_blink_animation(eye):
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

# ── ALMOND EYES (your original hexagon style) ─────────────

def build_almond_eyes(config):
    bpy.ops.mesh.primitive_circle_add(vertices=6, radius=0.35, location=(-0.6,0,0.1))
    eye = bpy.context.active_object
    eye.name = "Eyes"
    eye.rotation_euler[2] = math.radians(30)
    eye.rotation_euler[0] = math.radians(90)
    bpy.ops.object.transform_apply(rotation=True)

    eye.data.materials.append(make_mat("eye stroke",       (0.0,0.0,0.0)))
    eye.data.materials.append(make_mat("eye inside left",  (1.0,1.0,1.0)))
    eye.data.materials.append(make_mat("eye inside right", (1.0,1.0,1.0)))

    to_edit()
    bpy.ops.mesh.edge_face_add()
    bpy.ops.mesh.inset(thickness=0.045, depth=0)
    bpy.ops.mesh.inset(thickness=0.045, depth=0)
    bm = bmesh.from_edit_mesh(eye.data)
    min_area = min(f.calc_area() for f in bm.faces)
    for face in bm.faces:
        face.material_index = 1 if face.calc_area() <= min_area * 1.15 else 0
    bmesh.update_edit_mesh(eye.data)
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.symmetrize(direction="NEGATIVE_X")
    bm = bmesh.from_edit_mesh(eye.data)
    min_area = min(f.calc_area() for f in bm.faces)
    for face in bm.faces:
        if face.calc_area() <= min_area * 1.15 and face.calc_center_median().x > 0.1:
            face.material_index = 2
    bmesh.update_edit_mesh(eye.data)
    to_object()

    sub = eye.modifiers.new(name="Subdivision", type="SUBSURF")
    sub.levels = 3
    sub.render_levels = 3

    _add_eye_shape_keys(eye)
    arm = _create_eye_rig()
    _bind_eye_mesh(eye, arm)
    empties = _create_eye_empties(arm)
    set_active(eye)
    _setup_eye_shader(eye, empties, "left")
    _setup_eye_shader(eye, empties, "right")
    _add_eye_drivers(eye, arm)
    _create_blink_animation(eye)
    set_active(arm)
    to_pose()
    print("OK Almond eyes built.")
    return eye, arm

# ── CIRCLE EYES ────────────────────────────────────────────

def build_circle_eyes(config):
    # Circle = 12-vert circle, perfectly round
    bpy.ops.mesh.primitive_circle_add(vertices=12, radius=0.32, location=(-0.6,0,0.1))
    eye = bpy.context.active_object
    eye.name = "Eyes"
    eye.rotation_euler[0] = math.radians(90)
    bpy.ops.object.transform_apply(rotation=True)

    eye.data.materials.append(make_mat("eye stroke",       (0.0,0.0,0.0)))
    eye.data.materials.append(make_mat("eye inside left",  (1.0,1.0,1.0)))
    eye.data.materials.append(make_mat("eye inside right", (1.0,1.0,1.0)))

    to_edit()
    bpy.ops.mesh.edge_face_add()
    bpy.ops.mesh.inset(thickness=0.04, depth=0)
    bpy.ops.mesh.inset(thickness=0.04, depth=0)
    bm = bmesh.from_edit_mesh(eye.data)
    min_area = min(f.calc_area() for f in bm.faces)
    for face in bm.faces:
        face.material_index = 1 if face.calc_area() <= min_area * 1.15 else 0
    bmesh.update_edit_mesh(eye.data)
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.symmetrize(direction="NEGATIVE_X")
    bm = bmesh.from_edit_mesh(eye.data)
    min_area = min(f.calc_area() for f in bm.faces)
    for face in bm.faces:
        if face.calc_area() <= min_area * 1.15 and face.calc_center_median().x > 0.1:
            face.material_index = 2
    bmesh.update_edit_mesh(eye.data)
    to_object()

    sub = eye.modifiers.new(name="Subdivision", type="SUBSURF")
    sub.levels = 3
    sub.render_levels = 3

    _add_eye_shape_keys(eye)
    arm = _create_eye_rig()
    _bind_eye_mesh(eye, arm)
    empties = _create_eye_empties(arm)
    set_active(eye)
    _setup_eye_shader(eye, empties, "left")
    _setup_eye_shader(eye, empties, "right")
    _add_eye_drivers(eye, arm)
    _create_blink_animation(eye)
    set_active(arm)
    to_pose()
    print("OK Circle eyes built.")
    return eye, arm

# ──────────────────────────────────────────────────────────
# NOSE
# ──────────────────────────────────────────────────────────

def build_oval_nose(config):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=7, radius=1.0, location=(0,0,-0.55))
    nose = bpy.context.active_object
    nose.name = "PlushyNose"
    nose.scale = (0.22, 0.15, 0.13)
    bpy.ops.object.transform_apply(scale=True)

    # Flatten back, puff front
    to_edit()
    bm = bmesh.from_edit_mesh(nose.data)
    for v in bm.verts:
        if v.co.y < -0.10:
            v.co.y = -0.11
        if v.co.y > 0.08:
            v.co.y += 0.015
    bmesh.update_edit_mesh(nose.data)
    to_object()

    nose.data.materials.append(make_mat("nose_mat", (0.08,0.04,0.02)))

    to_edit()
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
    to_object()

    print("OK Oval nose built.")
    return nose, None

def build_triangle_nose(config):
    # 3-vert circle = triangle base
    bpy.ops.mesh.primitive_circle_add(vertices=3, radius=0.22, location=(0,0,-0.55))
    nose = bpy.context.active_object
    nose.name = "PlushyNose"
    # Rotate so flat edge is on top (like a real animal nose triangle)
    nose.rotation_euler[2] = math.radians(180)
    nose.rotation_euler[0] = math.radians(90)
    bpy.ops.object.transform_apply(rotation=True)

    # Scale: wider than tall
    nose.scale = (1.2, 1.0, 0.85)
    bpy.ops.object.transform_apply(scale=True)

    to_edit()
    bpy.ops.mesh.edge_face_add()
    # Two insets: outer stroke border, then inner fill
    bpy.ops.mesh.inset(thickness=0.03, depth=0.0)
    bpy.ops.mesh.inset(thickness=0.02, depth=0.02)  # depth=puff

    bm = bmesh.from_edit_mesh(nose.data)
    nose.data.materials.append(make_mat("nose_mat",        (0.06,0.03,0.01)))
    nose.data.materials.append(make_mat("nose_inner_mat",  (0.12,0.06,0.03)))
    areas = sorted(set(round(f.calc_area(),5) for f in bm.faces))
    for face in bm.faces:
        a = round(face.calc_area(),5)
        face.material_index = 0 if a == areas[-1] else 1
    bmesh.update_edit_mesh(nose.data)
    to_object()

    # Subdivision for softness
    sub = nose.modifiers.new(name="Subdivision", type="SUBSURF")
    sub.levels = 2

    to_edit()
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
    to_object()

    print("OK Triangle nose built.")
    return nose, None

# ──────────────────────────────────────────────────────────
# MOUTH
# ──────────────────────────────────────────────────────────

def _add_mouth_eating_animation(mouth_obj):
    """Eating chew cycle: frames 60-120. Blink-compatible timeline."""
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end   = 250
    sk = mouth_obj.data.shape_keys
    if not sk:
        return

    # Open shape key drives the eating animation
    open_key = sk.key_blocks.get("mouth open")
    if not open_key:
        return

    # Chew schedule: open → partial → open → partial → open → close
    chew = [
        (1,   0.0),
        (60,  0.0),   # start closed
        (66,  1.0),   # open wide
        (73,  0.35),  # partial close
        (80,  0.85),  # open again
        (87,  0.30),  # partial close
        (94,  0.75),  # open
        (101, 0.20),  # partial close
        (108, 0.0),   # fully closed
        (250, 0.0),
    ]
    for frame, value in chew:
        open_key.value = value
        open_key.keyframe_insert(data_path="value", frame=frame)

    if sk.animation_data and sk.animation_data.action:
        apply_smooth_interp(sk.animation_data.action)
    scene.frame_set(1)
    print("OK Eating animation keyframed.")

def build_line_mouth(config):
    """Simple curved line mouth — opens/closes and has eating animation."""
    # Build from a circle scaled very wide and flat = smile shape
    bpy.ops.mesh.primitive_circle_add(vertices=16, radius=0.38, location=(0,0,-1.05))
    mouth = bpy.context.active_object
    mouth.name = "PlushyMouth"
    mouth.rotation_euler[0] = math.radians(90)
    # Scale into a wide flat oval (the closed mouth shape)
    mouth.scale = (1.0, 1.0, 0.22)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    to_edit()
    bpy.ops.mesh.edge_face_add()
    bpy.ops.mesh.inset(thickness=0.025, depth=0)

    # Assign materials: outer stroke, inner dark (mouth interior)
    mouth.data.materials.append(make_mat("mouth_mat",          (0.05,0.02,0.01)))
    mouth.data.materials.append(make_mat("mouth_interior_mat", (0.02,0.01,0.01)))
    bm = bmesh.from_edit_mesh(mouth.data)
    min_area = min(f.calc_area() for f in bm.faces)
    for face in bm.faces:
        face.material_index = 1 if face.calc_area() <= min_area * 1.15 else 0
    bmesh.update_edit_mesh(mouth.data)
    to_object()

    sub = mouth.modifiers.new(name="Subdivision", type="SUBSURF")
    sub.levels = 2

    # UV unwrap
    to_edit()
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
    to_object()

    # Shape keys
    set_active(mouth)
    bpy.ops.object.shape_key_add(from_mix=False)
    mouth.data.shape_keys.key_blocks[0].name = "Basis"

    # Open shape key: push top verts up, bottom verts down
    bpy.ops.object.shape_key_add(from_mix=False)
    mouth.data.shape_keys.key_blocks[1].name = "mouth open"
    mouth.active_shape_key_index = 1
    to_edit()
    bm = bmesh.from_edit_mesh(mouth.data)
    center_z = sum(v.co.z for v in bm.verts) / len(bm.verts)
    for v in bm.verts:
        if v.co.z > center_z:
            v.co.z += 0.14  # upper lip up
        else:
            v.co.z -= 0.10  # lower lip down
    bmesh.update_edit_mesh(mouth.data)
    to_object()
    mouth.active_shape_key_index = 0

    _add_mouth_eating_animation(mouth)

    print("OK Line mouth built.")
    return mouth, None

def build_lips_mouth(config):
    """Lips mouth — upper M-shape, lower fuller oval. Optional heart + lipstick."""
    lips_heart = config.get("lips_heart", False)

    # ── Lower lip: wide flat oval ──
    bpy.ops.mesh.primitive_circle_add(vertices=12, radius=0.36, location=(0,0,-1.10))
    lower = bpy.context.active_object
    lower.name = "PlushyMouth"
    lower.rotation_euler[0] = math.radians(90)
    lower.scale = (1.0, 1.0, 0.30)
    bpy.ops.object.transform_apply(rotation=True, scale=True)

    lip_color = (0.65, 0.20, 0.20)
    lipstick_color = (0.80, 0.05, 0.10)

    lower.data.materials.append(make_mat("lip_mat",      lip_color,      roughness=0.80))
    lower.data.materials.append(make_mat("mouth_mat",    (0.02,0.01,0.01)))
    if lips_heart:
        lower.data.materials.append(make_mat("lipstick_mat", lipstick_color, roughness=0.55, specular=0.3))

    to_edit()
    bpy.ops.mesh.edge_face_add()
    bpy.ops.mesh.inset(thickness=0.03, depth=0)

    bm = bmesh.from_edit_mesh(lower.data)
    min_area = min(f.calc_area() for f in bm.faces)
    for face in bm.faces:
        face.material_index = 0 if face.calc_area() > min_area * 1.15 else 1
    bmesh.update_edit_mesh(lower.data)
    to_object()

    # ── Upper lip: add verts above lower lip with M-shape dip ──
    to_edit()
    bm = bmesh.from_edit_mesh(lower.data)
    # Find top verts of the outer ring (highest Z)
    top_verts = sorted(bm.verts, key=lambda v: v.co.z, reverse=True)[:6]
    # Cupid bow dip: push center top verts down slightly
    cx = 0.0
    for v in top_verts:
        dist_from_center = abs(v.co.x - cx)
        if dist_from_center < 0.12:
            v.co.z -= 0.06   # dip at center = cupid bow
        else:
            v.co.z += 0.04   # peaks on either side
    bmesh.update_edit_mesh(lower.data)
    to_object()

    # Heart inset on upper lip
    if lips_heart:
        to_edit()
        bm = bmesh.from_edit_mesh(lower.data)
        # Select only top faces
        for face in bm.faces:
            face.select = face.calc_center_median().z > 0.0
        bmesh.update_edit_mesh(lower.data)
        bpy.ops.mesh.inset(thickness=0.05, depth=0.01)
        bm = bmesh.from_edit_mesh(lower.data)
        for face in bm.faces:
            if face.select:
                face.material_index = 2  # lipstick_mat
        bmesh.update_edit_mesh(lower.data)
        to_object()

    sub = lower.modifiers.new(name="Subdivision", type="SUBSURF")
    sub.levels = 2

    to_edit()
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.02)
    to_object()

    # Shape keys
    set_active(lower)
    bpy.ops.object.shape_key_add(from_mix=False)
    lower.data.shape_keys.key_blocks[0].name = "Basis"

    bpy.ops.object.shape_key_add(from_mix=False)
    lower.data.shape_keys.key_blocks[1].name = "mouth open"
    lower.active_shape_key_index = 1
    to_edit()
    bm = bmesh.from_edit_mesh(lower.data)
    center_z = sum(v.co.z for v in bm.verts) / len(bm.verts)
    for v in bm.verts:
        if v.co.z > center_z:
            v.co.z += 0.12
        else:
            v.co.z -= 0.09
    bmesh.update_edit_mesh(lower.data)
    to_object()
    lower.active_shape_key_index = 0

    _add_mouth_eating_animation(lower)

    print(f"OK Lips mouth built (heart={'yes' if lips_heart else 'no'}).")
    return lower, None


# ──────────────────────────────────────────────────────────
# MOUTH — CRESCENT (smile shape)
# ──────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────
# MOUTH — CRESCENT + TONGUE
# ──────────────────────────────────────────────────────────

def build_crescent_mouth(config):
    """
    Wide crescent smile with red tongue geometry inside.
    Tongue is a separate mesh parented to the mouth.
    Unity note: set tongue Render Queue +1 above mouth so it draws on top.
    """
    def arc_pts(half_w, dip, n):
        cy = (half_w**2 - dip**2) / (2.0 * dip)
        r  = math.sqrt(half_w**2 + cy**2)
        al = math.atan2(-cy, -half_w)
        ar = math.atan2(-cy,  half_w)
        pts = []
        for i in range(n + 1):
            t = i / n
            a = al + t * (ar - al)
            pts.append((r * math.cos(a), 0.0, cy + r * math.sin(a)))
        return pts, cy, r

    n      = 20
    half_w = 0.52
    dip_o  = 0.32
    dip_i  = 0.06
    m_z    = -1.05

    outer_pts, cy_o, r_o = arc_pts(half_w, dip_o, n)
    inner_pts, cy_i, r_i = arc_pts(half_w, dip_i, n)
    z_off = m_z - (cy_o - r_o)
    outer_pts = [(x, y, z + z_off) for x,y,z in outer_pts]
    inner_pts = [(x, y, z + z_off) for x,y,z in inner_pts]

    # Mouth mesh
    mesh_data = bpy.data.meshes.new("PlushyMouth")
    obj = bpy.data.objects.new("PlushyMouth", mesh_data)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    bm = bmesh.new()
    outer_v = [bm.verts.new(p) for p in outer_pts]
    inner_v = [bm.verts.new(p) for p in reversed(inner_pts)][1:-1]
    bm.faces.new(outer_v + inner_v)
    bm.to_mesh(mesh_data)
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

    obj.data.materials.append(make_mat("mouth_stroke",  (0.02, 0.01, 0.01)))
    obj.data.materials.append(make_mat("mouth_cavity",  (0.02, 0.01, 0.01)))

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
        if v.co.z < mid_z:
            v.co.z -= 0.14
        else:
            v.co.z += 0.05
    bmesh.update_edit_mesh(obj.data)
    to_object()
    obj.active_shape_key_index = 0

    # ── TONGUE ──────────────────────────────────────────────
    # Flat oval mesh, parented to mouth, positioned inside cavity.
    # y=0.08 puts it in front of the mouth plane.
    # Unity: set tongue Render Queue to mouth_queue + 1.
    t_z = -0.97
    t_y =  0.08

    tmesh = bpy.data.meshes.new("Tongue")
    tongue = bpy.data.objects.new("Tongue", tmesh)
    bpy.context.collection.objects.link(tongue)
    bpy.context.view_layer.objects.active = tongue

    bm_t = bmesh.new()
    nt = 20
    for i in range(nt):
        a = (2 * math.pi * i) / nt
        bm_t.verts.new((0.32 * math.cos(a), t_y, t_z + 0.10 * math.sin(a)))
    bm_t.verts.ensure_lookup_table()
    face = bm_t.faces.new(bm_t.verts)
    bmesh.ops.recalc_face_normals(bm_t, faces=[face])
    bm_t.to_mesh(tmesh)
    bm_t.free()

    sub_t = tongue.modifiers.new("Subdivision", type="SUBSURF")
    sub_t.levels = 2

    mat_t = bpy.data.materials.new("tongue_mat")
    mat_t.use_nodes = True
    bt = mat_t.node_tree.nodes.get("Principled BSDF")
    bt.inputs["Base Color"].default_value = (0.85, 0.04, 0.06, 1.0)
    bt.inputs["Roughness"].default_value  = 0.35
    if "Specular IOR Level" in bt.inputs:
        bt.inputs["Specular IOR Level"].default_value = 0.8
    tongue.data.materials.append(mat_t)

    # Shape keys — tongue
    bpy.ops.object.shape_key_add(from_mix=False)
    tongue.data.shape_keys.key_blocks[0].name = "Basis"
    bpy.ops.object.shape_key_add(from_mix=False)
    tongue.data.shape_keys.key_blocks[1].name = "tongue out"
    tongue.active_shape_key_index = 1
    to_edit()
    bm_t2 = bmesh.from_edit_mesh(tongue.data)
    for v in bm_t2.verts:
        v.co.z -= 0.02
        v.co.y += 0.02
    bmesh.update_edit_mesh(tongue.data)
    to_object()
    tongue.active_shape_key_index = 0
    tongue.parent = obj

    # ── EATING + TONGUE ANIMATION ────────────────────────────
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end   = 250

    open_key   = obj.data.shape_keys.key_blocks.get("mouth open")
    tongue_key = tongue.data.shape_keys.key_blocks.get("tongue out")

    mouth_chew = [
        (1,0.0),(60,0.0),(66,1.0),(73,0.35),
        (80,0.90),(87,0.30),(94,0.80),(101,0.20),(108,0.0),(250,0.0),
    ]
    tongue_sched = [
        (1,0.0),(67,0.0),(72,1.0),(80,0.5),
        (87,0.8),(101,0.3),(108,0.0),(250,0.0),
    ]
    for frame, val in mouth_chew:
        open_key.value = val
        open_key.keyframe_insert(data_path="value", frame=frame)
    for frame, val in tongue_sched:
        tongue_key.value = val
        tongue_key.keyframe_insert(data_path="value", frame=frame)

    if obj.data.shape_keys.animation_data and obj.data.shape_keys.animation_data.action:
        apply_smooth_interp(obj.data.shape_keys.animation_data.action)

    scene.frame_set(1)
    print("OK Crescent mouth + tongue built.")
    print("   Unity tip: set tongue Render Queue = mouth queue + 1")
    return obj, None


def export_face_kit(config):
    import os
    path = config.get("export_path", "")
    if not path:
        print("WARN No export path set.")
        return

    to_object()
    bpy.ops.object.select_all(action="SELECT")

    bpy.ops.export_scene.fbx(
        filepath=path,
        use_selection=True,
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        bake_space_transform=False,   # OFF — avoids compound rotation error
        mesh_smooth_type="FACE",
        use_mesh_modifiers=True,
        add_leaf_bones=False,
        path_mode="COPY",
        axis_forward="-Y",            # Blender -Y → Unity +Z  ✓
        axis_up="Z",                  # Blender  Z → Unity +Y  ✓
    )
    print(f"OK Exported: {path}")

# ──────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────

def main():
    print("\n" + "="*55)
    print("  Plushy Face Kit — Stage 1")
    print("="*55)

    cleanup()

    cube = bpy.data.objects.get("Cube")
    if cube:
        bpy.data.objects.remove(cube, do_unlink=True)

    # Eyes
    if CONFIG["generate_eyes"]:
        if CONFIG["eye_style"] == "circle":
            build_circle_eyes(CONFIG)
        else:
            build_almond_eyes(CONFIG)

    # Nose
    if CONFIG["generate_nose"]:
        if CONFIG["nose_style"] == "triangle":
            build_triangle_nose(CONFIG)
        else:
            build_oval_nose(CONFIG)

    # Mouth
    if CONFIG["generate_mouth"]:
        if CONFIG["mouth_style"] == "lips":
            build_lips_mouth(CONFIG)
        elif CONFIG["mouth_style"] == "line":
            build_line_mouth(CONFIG)
        else:
            build_crescent_mouth(CONFIG)

    # Export
    if CONFIG["export"]:
        export_face_kit(CONFIG)

    bpy.context.scene.frame_set(1)

    print("\n" + "="*55)
    print("  DONE!")
    print("  SPACEBAR          = play blink + eating animation")
    print("  CONFIG dict       = swap eye/nose/mouth styles")
    print("  export=True       = auto-export FBX for Unity")
    print("="*55 + "\n")

main()
