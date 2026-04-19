"""
utils.py — PlushyFaceKit
Shared helpers used by all modules.
"""
import bpy

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
    b.inputs["Roughness"].default_value  = roughness
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = specular
    return m

def apply_smooth_interp(action):
    """Bezier ease-in-out on all keyframes in an action."""
    if not action:
        return
    try:
        for layer in action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    for fc in cb.fcurves:
                        for kp in fc.keyframe_points:
                            kp.interpolation = "BEZIER"
                            kp.easing        = "EASE_IN_OUT"
    except Exception:
        try:
            for fc in action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "BEZIER"
                    kp.easing        = "EASE_IN_OUT"
        except Exception:
            pass
