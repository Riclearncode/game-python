# Build EXE - Pixel Zombie Siege

This project can be packaged for Windows with PyInstaller. The recommended build is `onedir` because the game uses assets, audio, maps and save files.

## Requirements

Install dependencies from the project root:

```powershell
py -m pip install -r requirements.txt
```

## Build With PowerShell

```powershell
.\build_exe.ps1
```

## Build With CMD

```bat
build_exe.bat
```

The output executable will be:

```text
dist\PixelZombieSiege\PixelZombieSiege.exe
```

## Bundled Assets

The build scripts include:

```text
assets\
```

This covers current audio, menu images, maps and tilesets because they live under the `assets` directory.

## Save File Location

When running from source, save data is stored at:

```text
save\save_data.json
```

When running the EXE, save data is stored outside the bundled app folder:

```text
%APPDATA%\PixelZombieSiege\save_data.json
```

This avoids writing into PyInstaller temporary folders and keeps the high score/settings after updating the EXE.

## Path Helpers

The project uses `path_utils.py`:

- `resource_path(relative_path)` for bundled read-only resources.
- `user_data_path(filename)` for save/high score data.
- `get_base_path()` for source vs PyInstaller resource lookup.

Use `resource_path()` whenever code loads files from `assets/`.
Use `user_data_path()` whenever code writes player data.

## Manual EXE Test Checklist

1. Run `dist\PixelZombieSiege\PixelZombieSiege.exe`.
2. Main menu appears.
3. Start opens the difficulty/map/class flow.
4. Enter a run.
5. Audio and menu background load if assets exist.
6. Finish or restart a run so high score can save.
7. Reopen the EXE and confirm high score/settings persist.

## Optional Onefile Build

`onedir` is easier to debug and is recommended. If you later want `onefile`, keep using `resource_path()` and keep save files in `%APPDATA%`.
