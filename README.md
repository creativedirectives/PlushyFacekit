# PlushyFaceKit

Blender 5.0 addon for generating plushy character face parts for Meta Quest 3 Mixed Reality.

## What it does
Procedurally generates face components (eyes, nose, mouth) with animations,
UV unwrapped and exported as FBX for Unity import.

## Parts
- **Eyes**: Circle style with blink animation (crescent moon close shape)
- **Nose**: Oval (soft button style)
- **Mouth**: Crescent smile with tongue geometry and eating animation

## Usage
1. Open Blender 5.0
2. Go to Scripting tab
3. Open `scripts/PlushyFaceKit.py`
4. Edit `CONFIG` dict at top to choose styles
5. Press Alt+P to run

## CONFIG options
```python
CONFIG = {
    "eye_style":   "almond",    # "almond" | "circle"
    "nose_style":  "oval",      # "oval"   | "triangle"
    "mouth_style": "crescent",  # "crescent" | "line" | "lips"
    "export":      False,       # True = auto FBX export on run
}
```

## Export settings (Unity-correct)
- axis_forward = '-Y'
- axis_up = 'Z'
- bake_space_transform = False

## Project structure
```
PlushyFaceKit/
├── blender/        .blend source files
├── exports/        FBX files for Unity
├── scripts/        Python addon scripts
└── README.md
```
