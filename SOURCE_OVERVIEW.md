# Pixel Zombie Siege - Source Code Overview

Tai lieu nay mo ta cau truc ma nguon cua project Pixel Zombie Siege, giup doc code nhanh hon va co the dung trong README hoac bao cao mon hoc.

## 1. Tong Quan Kien Truc

Pixel Zombie Siege la game top-down 2D zombie survival viet bang Python va Pygame. Project hien duoc to chuc theo huong "mot core gameplay lon + cac manager tach rieng" de giu game chay on dinh trong khi van de mo rong UI, map, save, pathfinding va build EXE.

Luồng chính:

```text
main.py
  -> khoi tao pygame, Game, Player, MapManager, UIManager, SaveManager
  -> xu ly input/menu/prepare/gameplay
  -> update player, zombie, bullet, structure, effect, wave
  -> render map, entity, effect, HUD, hotbar, panel
```

Các manager phụ:

```text
UIManager      -> ve menu, prepare screen, HUD, hotbar, stats panel
MapManager     -> load/render map, collision grid, spawn point, buildable grid
SaveManager    -> save setting, high score, meta progression
path_utils     -> xu ly duong dan asset/save khi chay source hoac EXE
```

## 2. File Chinh

### `main.py`

Day la file trung tam cua game. File nay chua phan lon logic gameplay:

- Khoi tao cua so, fullscreen/adaptive resolution.
- Vong lap chinh cua game.
- State menu, option, prepare screen, gameplay, game over.
- Player movement, shooting, reload, dash, auto-fire.
- Weapon progression, bullet, laser, shotgun pellet, railgun.
- Zombie AI: Walker, Runner, Spitter, Boomer, Stalker, Titan.
- Wave system, spawn queue, difficulty scaling.
- Building system: turret, fence, gate, trap, mine, steel wall.
- Collision, dynamic obstacle, pathfinding cache.
- Effect: damage number, gold number, muzzle flash, blood decal, shockwave, warning circle.
- Audio: load sound/music, mixer channel theo nhom.

Các class quan trọng trong `main.py`:

```text
Game        -> dieu phoi toan bo game
Player      -> nguoi choi, weapon, stat, level, perk
Weapon      -> thong so sung, ammo, reload, fire rate
Bullet      -> dan thuong va projectile
Zombie      -> AI, pathfinding, tan cong, skill tung loai zombie
Structure   -> cong trinh phong thu: turret/fence/gate/trap
FloatingText, Particle, Shockwave, WarningCircle -> effect nhe
```

### `ui_manager.py`

Quan ly phan ve UI de giam viec ve truc tiep trong `main.py`.

Nhiem vu:

- Ve main menu.
- Ve option menu.
- Ve prepare screen.
- Ve HUD trong tran.
- Ve hotbar.
- Ve stats panel.
- Ve button, panel, progress bar, icon placeholder.
- Scale UI theo kich thuoc man hinh.

Các method đáng chú ý:

```text
draw_main_menu(...)
draw_options_menu(...)
draw_prepare_screen(...)
draw_hud(...)
draw_hotbar(...)
draw_stats_panel(...)
draw_button(...)
draw_panel(...)
draw_progress_bar(...)
```

### `map_manager.py`

Quan ly map va chuan bi cho Tiled Map Editor.

Nhiem vu:

- Load map builtin neu khong co JSON.
- Load Tiled JSON trong `assets/maps/`.
- Render cac layer theo thu tu.
- Quan ly collision grid.
- Quan ly buildable grid.
- Quan ly player spawn, zombie spawn, boss spawn.
- Cap nhat dynamic obstacle tu cong trinh.

Các method quan trọng:

```text
load_builtin_map(map_name)
load_tiled_map(map_name)
render(screen, camera)
is_blocked(tile_x, tile_y)
is_buildable(tile_x, tile_y)
get_player_spawn()
get_zombie_spawns()
get_boss_spawns()
world_to_tile(x, y)
tile_to_world(tile_x, tile_y)
update_dynamic_obstacles(buildings)
```

### `save_manager.py`

Quan ly save file va high score.

Nhiem vu:

- Tao save mac dinh khi chua co file.
- Load/save JSON.
- Backup save bi loi/corrupt.
- Luu settings, high score, progression, achievement.
- Ho tro duong dan save an toan khi build EXE.

### `path_utils.py`

Chua helper duong dan:

- `resource_path(relative_path)`: lay dung duong dan asset khi chay source hoac PyInstaller.
- `get_base_path()`: xac dinh thu muc goc.
- `user_data_path(filename)`: luu file nguoi dung vao AppData khi chay EXE.

### `tools/balance_audit.py`

Cong cu ho tro can bang gameplay:

- Tinh DPS uoc luong tung vu khi.
- In bang weapon progression.
- Ho tro tao/cap nhat `BALANCE_NOTES.md`.

### `tools/generate_synth_audio.py`

Tao audio placeholder/synth cho sung, zombie, music va cac hieu ung co ban neu thieu asset that.

### `test_gate_and_fence.py`

Test nho cho he thong fence/gate:

- Gate co trang thai mo/dong.
- Fence/gate co tac dong den pathfinding.
- Dam bao logic phong thu khong bi crash.

## 3. Thu Muc Asset

```text
assets/
  menu_background.png
  maps/
    warehouse.json
    crossfire_yard.json
    split_ruins.json
    tiled_loader_test.json
  tilesets/
    warehouse_tiles.png
    crossfire_yard_tiles.png
    split_ruins_tiles.png
  audio/
    synth/
    kenney_rpg/
    opengameart/
```

Map JSON duoc load boi `MapManager`. Neu file map hoac tileset bi thieu, game dung fallback/placeholder de khong crash.

## 4. Luong Gameplay

### Khoi dong game

```text
py main.py
  -> Game.__init__()
  -> load settings/save
  -> load assets/audio/map
  -> vao main menu
```

### Chon tran

```text
Main Menu
  -> Start
  -> chon difficulty
  -> chon map
  -> chon character
  -> init run
```

### Trong tran

```text
handle_events()
update(dt)
  -> update_player
  -> update_wave
  -> update_zombies
  -> update_structures
  -> update_bullets/effects
draw()
  -> render map
  -> render entity/effect
  -> render HUD/UI
```

## 5. AI Va Pathfinding

Project dung nhieu cach tim duong theo tung loai zombie:

- Walker: flow-field BFS dung chung de toi uu so luong lon.
- Runner: A* va flank de gay ap luc.
- Spitter: giu khoang cach, uu tien vi tri co the ban acid.
- Boomer: dash vao player hoac cum cong trinh, co explosion AOE.
- Stalker: flank va ne line-of-fire neu co the.
- Titan: clearance A*, phase theo HP, charge, stomp, summon, leap khi bi ket.

Collision/pathfinding lay du lieu tu:

```text
MapManager collision grid
  + dynamic obstacles tu fence/gate/turret/steel wall
  + path cache trong Game
```

## 6. He Thong Xay Dung

Cong trinh chinh:

- Turret co ban.
- Fence.
- Gate.
- Spike trap.
- Mine.
- Steel wall.
- Machine turret.
- Laser turret.
- Slow turret.

Logic dat cong trinh nam trong:

```text
Game.can_place_building(...)
Game.place_structure(...)
Structure.update(...)
Structure.draw(...)
MapManager.update_dynamic_obstacles(...)
```

Hien tai fence/gate/steel wall duoc dat tu do hon, nhung van khong cho dat len:

- Tuong/collision map.
- Spawn point quan trong.
- Player dang dung.
- Zombie dang chiem o.
- Cong trinh khac.

## 7. Weapon Progression

Weapon stat duoc gom theo tier trong `WEAPON_DEFS` cua `main.py`.

Các chỉ số chính:

- `damage`
- `fire_rate`
- `magazine`
- `reload_time`
- `bullet_speed`
- `range`
- `spread`
- `pellets`
- `pierce`
- `spin_up`
- `cost`

HUD va upgrade UI doc tu weapon hien tai cua player, nen khi them weapon moi can cap nhat bang weapon definition va sound/effect fallback neu can.

## 8. UI/HUD

UI hien tai chia thanh:

- Main menu.
- Option menu.
- Prepare screen.
- HUD gameplay.
- Hotbar.
- Stats panel.
- Algorithm demo overlay.
- Game over/high score.

Hotbar dang uu tien cac hanh dong hay dung:

- Upgrade.
- Turret.
- Fence.
- Gate.
- Reload.
- Repair.
- Dash.
- Auto fire.
- Info.

Các nút ít dùng hoặc nâng cao có thể vẫn giữ logic/phím trong `main.py`, nhưng không nhất thiết luôn hien tren hotbar.

## 9. Build EXE

Project co script build:

```powershell
.\build_exe.ps1
```

hoac:

```bat
build_exe.bat
```

Huong dan chi tiet nam trong `BUILD_EXE.md`.

## 10. Cach Test Nhanh

Compile:

```powershell
py -m py_compile main.py ui_manager.py map_manager.py save_manager.py path_utils.py tools\balance_audit.py test_gate_and_fence.py
```

Smoke test:

```powershell
py main.py --smoke
```

Test gameplay thu cong:

1. Mo game bang `py main.py`.
2. Vao Start.
3. Chon difficulty, map, character.
4. Vao tran.
5. Test ban, reload, nhat vang, upgrade.
6. Test dat turret/fence/gate.
7. Bat Algorithm Demo bang `F1` neu can demo pathfinding.

## 11. Diem Nen Tach Tiep

Neu tiep tuc refactor, nen tach dan cac he sau khoi `main.py`:

- `weapon_system.py`: weapon definition, ammo, reload, shooting.
- `zombie_system.py`: zombie stats, AI, skill.
- `building_system.py`: structure stats, build validation, repair.
- `effect_manager.py`: particle, floating text, shockwave, decal.
- `audio_manager.py`: load/play sound, music switching.
- `wave_manager.py`: spawn queue, wave reward, difficulty scaling.

Muc tieu la giu `main.py` chi con vai tro dieu phoi vong lap va ket noi cac manager.
