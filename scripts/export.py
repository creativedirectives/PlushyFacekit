"""
export.py — PlushyFaceKit
FBX export with correct Unity axis settings.
  axis_forward = '-Y'  → Blender -Y maps to Unity +Z (no manual rotation needed)
  axis_up      = 'Z'   → Blender  Z maps to Unity +Y
  bake_space_transform = False  → avoids compound 180° flip bug
"""
import bpy
from utils import to_object


def export_face_kit(config):
    path = config.get("export_path", "")
    if not path:
        print("WARN export: no export_path set in CONFIG.")
        return

    to_object()
    bpy.ops.object.select_all(action="SELECT")

    bpy.ops.export_scene.fbx(
        filepath=path,
        use_selection=True,
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        bake_space_transform=False,
        mesh_smooth_type="FACE",
        use_mesh_modifiers=True,
        add_leaf_bones=False,
        path_mode="COPY",
        axis_forward="-Y",
        axis_up="Z",
    )
    print(f"OK exported: {path}")
