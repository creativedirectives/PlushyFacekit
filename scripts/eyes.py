"""
eyes.py — PlushyFaceKit
Two eye style options. Both share all helpers from eye_shared.py.

  build_circle_eyes(config)   — 16-vert smooth circle
  build_hexagon_eyes(config)  — 6-vert hexagon, points east/west (◇ horizontal)
                                subdivision softens into a wide organic oval
"""
import bpy
from utils      import set_active, to_object, to_pose
from eye_shared import (
    _build_eye_base,
    _create_eye_rig,
    _bind_eye_mesh,
    _add_crescent_keys,
    _build_uv_eye_shader,
    _create_blink_anim,
)


def _finish_eye(eye, arm):
    """Shared final steps after mesh is built — same for every style."""
    _add_crescent_keys(eye)
    _bind_eye_mesh(eye, arm)
    _build_uv_eye_shader("left")
    _build_uv_eye_shader("right")
    _create_blink_anim(eye)
    set_active(arm)
    to_pose()


def build_circle_eyes(config):
    """
    Smooth round eyes — 16-vert circle base.
    Subdivision gives clean circular silhouette.
    """
    arm = _create_eye_rig()
    eye = _build_eye_base(vertices=16, radius=0.35, z_rotate_deg=0)
    _finish_eye(eye, arm)
    print("OK circle eyes built.")
    return eye, arm


def build_hexagon_eyes(config):
    """
    Wide expressive eyes — 6-vert hexagon, z_rotate=0 puts sharp points
    east and west (◇ orientation). Subdivision rounds the corners into
    a soft elongated shape — distinct contrast to the circle style.
    """
    arm = _create_eye_rig()
    eye = _build_eye_base(vertices=6, radius=0.35, z_rotate_deg=0)
    _finish_eye(eye, arm)
    print("OK hexagon eyes built.")
    return eye, arm
