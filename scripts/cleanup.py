"""
cleanup.py — PlushyFaceKit
Removes ALL objects, materials, meshes, armatures created by the kit.
Safe to re-run — won't crash if objects don't exist.
"""
import bpy
from utils import to_object

# Every object name the kit ever creates
KILL_OBJECTS = {
    "Eyes", "irig",
    "PlushyNose",
    "PlushyMouth", "Tongue", "mouth_rig",
    "empty iris l", "empty iris r",
    "empty eye close l", "empty eye close r",
    "Cube",
}

# Every material name the kit ever creates
KILL_MATERIALS = {
    "eye stroke", "eye inside left", "eye inside right",
    "nose_mat", "nose_inner_mat",
    "mouth_stroke", "mouth_cavity", "mouth_mat",
    "mouth_interior_mat", "lip_mat", "lipstick_mat",
    "tongue_mat",
}

# Mesh name prefixes the kit creates
KILL_MESH_PREFIXES = ("Eyes", "Circle", "PlushyNose", "PlushyMouth", "Tongue")

# Armature name prefixes
KILL_ARM_PREFIXES  = ("irig", "mouth_rig")

# Action name prefixes
KILL_ACTION_PREFIXES = ("BlinkAction", "MouthAction")


def cleanup():
    to_object()

    # Objects (also catches .001 .002 duplicates)
    for obj in list(bpy.data.objects):
        base = obj.name.rstrip("0123456789").rstrip(".")
        if base in KILL_OBJECTS or obj.name in KILL_OBJECTS:
            bpy.data.objects.remove(obj, do_unlink=True)

    # Materials
    for name in KILL_MATERIALS:
        m = bpy.data.materials.get(name)
        if m:
            bpy.data.materials.remove(m, do_unlink=True)

    # Meshes
    for mesh in list(bpy.data.meshes):
        if any(mesh.name.startswith(p) for p in KILL_MESH_PREFIXES):
            bpy.data.meshes.remove(mesh, do_unlink=True)

    # Armatures
    for arm in list(bpy.data.armatures):
        if any(arm.name.startswith(p) for p in KILL_ARM_PREFIXES):
            bpy.data.armatures.remove(arm, do_unlink=True)

    # Actions
    for action in list(bpy.data.actions):
        if any(action.name.startswith(p) for p in KILL_ACTION_PREFIXES):
            bpy.data.actions.remove(action, do_unlink=True)

    print("OK cleanup: scene cleared.")
