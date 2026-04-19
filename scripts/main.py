"""
PlushyFaceKit — main.py
Run this from Blender Scripting tab (Alt+P).
Edit CONFIG below to choose styles, then run.
"""

# ── LOAD MODULES ─────────────────────────────────────────────────────────────
# Blender scripting tab runs as __main__ so we use exec-based imports.
import importlib, sys, os, bpy

_scripts = os.path.join(os.path.expanduser("~"), "Desktop", "PlushyFaceKit", "scripts")
if _scripts not in sys.path:
    sys.path.insert(0, _scripts)

# Direct imports (flat, no package — works from Scripting tab)
import utils;    importlib.reload(utils)
import cleanup;  importlib.reload(cleanup)
import eye_shared; importlib.reload(eye_shared)
import eyes;     importlib.reload(eyes)
import nose;     importlib.reload(nose)
import mouth;    importlib.reload(mouth)
import export as exporter; importlib.reload(exporter)

# ── CONFIG ────────────────────────────────────────────────────────────────────
CONFIG = {
    "eye_style":    "circle",      # "circle" | "hexagon"
    "nose_style":   "oval",        # "oval"   | "triangle"
    "mouth_style":  "crescent",    # "crescent" | "line" | "lips"
    "lips_heart":   True,
    "generate_eyes":  True,
    "generate_nose":  True,
    "generate_mouth": True,
    "export":       False,
    "export_path":  "C:/Users/Dontavius/Desktop/PlushyFaceKit/exports/PlushyFaceKit.fbx",
}

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "="*55)
    print("  PlushyFaceKit — building...")
    print("="*55)

    cleanup.cleanup()

    cube = bpy.data.objects.get("Cube")
    if cube:
        bpy.data.objects.remove(cube, do_unlink=True)

    if CONFIG["generate_eyes"]:
        if CONFIG["eye_style"] == "hexagon":
            eyes.build_hexagon_eyes(CONFIG)
        else:
            eyes.build_circle_eyes(CONFIG)

    if CONFIG["generate_nose"]:
        if CONFIG["nose_style"] == "triangle":
            nose.build_triangle_nose(CONFIG)
        else:
            nose.build_oval_nose(CONFIG)

    if CONFIG["generate_mouth"]:
        if CONFIG["mouth_style"] == "lips":
            mouth.build_lips_mouth(CONFIG)
        elif CONFIG["mouth_style"] == "line":
            mouth.build_line_mouth(CONFIG)
        else:
            mouth.build_crescent_mouth(CONFIG)

    if CONFIG["export"]:
        exporter.export_face_kit(CONFIG)

    bpy.context.scene.frame_set(1)

    print("\n" + "="*55)
    print("  DONE!")
    print(f"  eyes    → {CONFIG['eye_style']}")
    print(f"  nose    → {CONFIG['nose_style']}")
    print(f"  mouth   → {CONFIG['mouth_style']}")
    print("  SPACEBAR = preview animations")
    print("="*55 + "\n")

main()
