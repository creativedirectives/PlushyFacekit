"""
eyes.py — PlushyFaceKit
Public eye builders. Both call shared helpers — zero duplication.

  build_almond_eyes(config)  — 6-vert hexagon base, 30deg rotation
  build_circle_eyes(config)  — 16-vert circle base, no rotation
"""
import bpy
from utils import set_active, to_object, to_pose
from eye_shared import (
    _build_eye_base,
    _create_eye_rig,
    _bind_eye_mesh,
    _add_crescent_keys,
    _build_uv_eye_shader,
    _create_blink_anim,
)


def _finish_eye(eye, arm):
    """Shared final steps after mesh is built."""
    _add_crescent_keys(eye)
    _bind_eye_mesh(eye, arm)
    _build_uv_eye_shader("left")
    _build_uv_eye_shader("right")
    _create_blink_anim(eye)
    set_active(arm)
    to_pose()


def build_almond_eyes(config):
    """Hexagon (6-vert) base — gives a softer almond/oval silhouette."""
    eye = _build_eye_base(vertices=6, radius=0.35, z_rotate_deg=30)

    arm = _create_eye_rig()
    _finish_eye(eye, arm)
    print("OK almond eyes built.")
    return eye, arm


def build_circle_eyes(config):
    """Circle (16-vert) base — perfectly round eye."""
    eye = _build_eye_base(vertices=16, radius=0.35, z_rotate_deg=0)

    arm = _create_eye_rig()
    _finish_eye(eye, arm)
    print("OK circle eyes built.")
    return eye, arm
