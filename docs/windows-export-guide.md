# Windows Export Guide

## Purpose

This project includes a Godot Windows export preset, but this ZIP does not include a verified Windows executable. Export must be performed from a local Godot installation with export templates installed.

## Steps

1. Install Godot 4.x.
2. Install Godot export templates.
3. Open the `game/` folder as the project.
4. Confirm `game/export_presets.cfg` exists.
5. In Godot, choose Project → Export.
6. Select the Windows Desktop preset.
7. Export to:

```text
../builds/windows/PeaceOS_CrisisRoom_v0.2.exe
```

8. Package the `.exe` and `.pck` if Godot exports them separately.
9. Create a release ZIP:

```text
PeaceOS_CrisisRoom_v0.2_Windows.zip
```

## Success Condition

A non-Godot user can unzip the package, double-click the executable, and play.
