# Pixel Zombie Siege - Mô Tả Mã Nguồn

Tài liệu này mô tả cấu trúc mã nguồn của project Pixel Zombie Siege. Nội dung được viết để hỗ trợ đọc code, bảo trì project, viết README hoặc dùng trong báo cáo môn học.

## 1. Tổng Quan Project

Pixel Zombie Siege là game top-down 2D zombie survival viết bằng Python và Pygame. Người chơi sinh tồn theo từng đợt zombie, bắn quái, nhặt vàng, lên cấp, chọn perk, nâng cấp vũ khí và xây công trình phòng thủ như trụ súng, hàng rào, cổng, bẫy.

Project hiện được tổ chức theo hướng:

- `main.py` giữ vai trò lõi gameplay và vòng lặp chính.
- `UIManager` quản lý phần giao diện.
- `MapManager` quản lý map, collision, spawn point và dữ liệu Tiled.
- `SaveManager` quản lý save, setting, high score và meta progression.
- Các file hướng dẫn riêng mô tả map, build EXE, cân bằng và demo thuật toán.

Luồng chạy tổng quát:

```text
main.py
  -> khởi tạo Pygame và Game
  -> load asset, audio, save, map
  -> vào menu chính
  -> chọn độ khó, map, nhân vật
  -> bắt đầu trận
  -> update gameplay theo từng frame
  -> render map, nhân vật, zombie, hiệu ứng và UI
```

## 2. Cấu Trúc File Chính

```text
main.py                  File gameplay chính
ui_manager.py            Quản lý UI, HUD, menu, hotbar
map_manager.py           Quản lý map, Tiled JSON, collision, spawn
save_manager.py          Quản lý save file, high score, progression
path_utils.py            Helper xử lý đường dẫn asset/save khi chạy source hoặc EXE
test_gate_and_fence.py   Test nhanh hệ thống hàng rào/cổng
requirements.txt         Thư viện cần cài
build_exe.ps1            Script build EXE bằng PowerShell
build_exe.bat            Script build EXE bằng batch
```

Các tài liệu phụ:

```text
README.md                Giới thiệu tổng quan project
SOURCE_OVERVIEW.md       Tài liệu mô tả mã nguồn
MAP_GUIDE.md             Quy chuẩn tạo map bằng Tiled
BUILD_EXE.md             Hướng dẫn build EXE
BALANCE_NOTES.md         Ghi chú cân bằng vũ khí/zombie/economy
ALGORITHM_DEMO_GUIDE.md  Hướng dẫn demo thuật toán AI/pathfinding
```

## 3. File `main.py`

`main.py` là file trung tâm của project. File này chứa phần lớn logic gameplay và điều phối các hệ thống khác.

Các nhóm chức năng chính trong `main.py`:

- Khởi tạo cửa sổ game, fullscreen và adaptive resolution.
- Quản lý state: menu chính, option, prepare screen, gameplay, pause, game over.
- Xử lý input bàn phím, chuột và hotbar.
- Quản lý player, súng, đạn, reload, dash, auto-fire.
- Quản lý zombie, AI, skill, pathfinding và Titan Boss.
- Quản lý wave, spawn queue và độ khó.
- Quản lý công trình: turret, hàng rào, cổng, bẫy gai, mìn, tường thép.
- Quản lý score, vàng, XP, level, perk và power-up.
- Quản lý hiệu ứng: muzzle flash, floating text, blood decal, shockwave, warning circle.
- Load và phát âm thanh, nhạc nền, SFX.

Các class quan trọng:

```text
Game
  Điều phối toàn bộ game, vòng lặp update/draw, state, input và kết nối các manager.

Player
  Quản lý người chơi: vị trí, máu, tốc độ, level, XP, weapon, dash, perk.

Weapon
  Quản lý vũ khí: tier, damage, fire rate, magazine, reload, spread, pierce.

Bullet
  Projectile của súng thường, shotgun, rifle, machine gun.

Zombie
  Quản lý từng loại zombie, bao gồm Walker, Runner, Spitter, Boomer, Stalker, Titan.

Structure
  Quản lý công trình phòng thủ như turret, fence, gate, trap, mine.

FloatingText, Particle, BulletTrail, Shockwave, WarningCircle
  Các hiệu ứng hình ảnh nhẹ để game có cảm giác bắn đã tay hơn.
```

## 4. File `ui_manager.py`

`ui_manager.py` gom phần vẽ UI ra khỏi `main.py`, giúp code dễ đọc hơn.

Nhiệm vụ chính:

- Vẽ Main Menu.
- Vẽ Option Menu.
- Vẽ màn chuẩn bị trận.
- Vẽ màn chọn độ khó, map, nhân vật.
- Vẽ HUD trong trận.
- Vẽ hotbar.
- Vẽ bảng chỉ số bằng phím `I`.
- Vẽ nút, panel, progress bar, card, icon placeholder.
- Tự scale theo độ phân giải màn hình.

Các method tiêu biểu:

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

Hotbar hiện ưu tiên các nút dùng thường xuyên:

- `1`: nâng cấp vũ khí.
- `2`: đặt trụ súng.
- `3`: đặt hàng rào.
- `4`: đặt cổng.
- `R`: nạp đạn.
- `E`: sửa công trình.
- `Shift`: lướt.
- `F`: bật/tắt tự động bắn.
- `I`: mở bảng chỉ số.

Các nút ít dùng hoặc nâng cao có thể vẫn giữ logic/phím trong `main.py`, nhưng không luôn hiển thị trên hotbar để tránh rối màn hình.

## 5. File `map_manager.py`

`MapManager` quản lý toàn bộ dữ liệu map và chuẩn bị cho việc import map từ Tiled Map Editor.

Nhiệm vụ chính:

- Load map builtin nếu không có file JSON.
- Load map từ Tiled JSON trong `assets/maps/`.
- Render map theo layer.
- Quản lý collision grid.
- Quản lý buildable grid.
- Quản lý player spawn, zombie spawn, boss spawn.
- Cập nhật dynamic obstacles từ hàng rào, cổng, turret, tường thép.

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

Nếu thiếu file map JSON hoặc tileset image, `MapManager` dùng fallback hoặc placeholder để game không bị crash.

## 6. File `save_manager.py`

`SaveManager` quản lý dữ liệu lưu game dưới dạng JSON.

Dữ liệu lưu gồm:

- Cài đặt ngôn ngữ.
- Âm lượng nhạc và SFX.
- Auto-fire.
- Developer Mode nếu cần.
- High score.
- Wave cao nhất.
- Điểm cao nhất.
- Tổng số zombie đã hạ.
- Tổng vàng đã kiếm.
- Meta progression.
- Achievement và unlock.

Yêu cầu an toàn:

- Nếu chưa có save file thì tự tạo save mặc định.
- Nếu save bị lỗi hoặc corrupt thì backup file cũ và tạo save mới.
- Khi chạy EXE, save không nên lưu trong thư mục tạm của PyInstaller.

## 7. File `path_utils.py`

File này hỗ trợ đường dẫn để game chạy ổn định ở cả hai chế độ:

- Chạy source bằng `py main.py`.
- Chạy bản build EXE bằng PyInstaller.

Các helper chính:

```text
resource_path(relative_path)
  Lấy đúng đường dẫn asset khi chạy source hoặc EXE.

get_base_path()
  Xác định thư mục gốc của game.

user_data_path(filename)
  Lấy đường dẫn lưu dữ liệu người dùng, ưu tiên AppData trên Windows.
```

## 8. Thư Mục Asset

Cấu trúc asset chính:

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

Ý nghĩa:

- `assets/maps/`: chứa map JSON export từ Tiled.
- `assets/tilesets/`: chứa tileset image.
- `assets/audio/`: chứa nhạc nền và SFX.
- `assets/menu_background.png`: ảnh nền menu chính.

## 9. Luồng Gameplay Trong Trận

Mỗi frame, game chạy theo luồng:

```text
handle_events()
  -> đọc input bàn phím/chuột
  -> xử lý click UI, hotbar, xây dựng, pause

update(dt)
  -> update player
  -> update weapon/reload
  -> update wave/spawn
  -> update zombie AI
  -> update bullet/projectile
  -> update structure/turret
  -> update effect
  -> kiểm tra game over

draw()
  -> render map
  -> render blood decal/effect
  -> render item, bullet, zombie, player, structure
  -> render build preview
  -> render HUD/hotbar/panel
```

## 10. AI Và Pathfinding

Game dùng nhiều chiến thuật tìm đường khác nhau tùy loại zombie:

- Walker dùng flow-field BFS để tối ưu khi có số lượng lớn.
- Runner dùng A* và flank để tạo áp lực.
- Spitter giữ khoảng cách và tìm vị trí bắn acid.
- Boomer dash vào player hoặc cụm công trình, chết sẽ nổ AOE.
- Stalker flank và né đường bắn nếu có thể.
- Titan dùng clearance A*, có phase theo HP, charge, stomp, summon và leap khi bị kẹt.

Nguồn dữ liệu collision:

```text
MapManager collision grid
  + dynamic obstacles từ fence/gate/turret/steel wall
  + path cache trong Game
```

Dynamic obstacles giúp zombie không đi xuyên:

- Tường.
- Container.
- Xe hỏng.
- Hàng rào.
- Cổng đóng.
- Trụ súng nếu trụ đang chặn đường.
- Tường thép.

## 11. Hệ Thống Xây Dựng

Các công trình hiện có:

- Turret cơ bản.
- Machine turret.
- Laser turret.
- Slow turret.
- Hàng rào.
- Cổng mở/đóng bằng `G`.
- Bẫy gai.
- Mìn.
- Tường thép.

Các hàm quan trọng:

```text
Game.can_place_building(...)
Game.place_structure(...)
Structure.update(...)
Structure.draw(...)
MapManager.update_dynamic_obstacles(...)
```

Luật đặt hàng rào/cổng/tường thép hiện đã được nới để người chơi xây tự do hơn. Tuy nhiên game vẫn không cho đặt lên:

- Tường hoặc collision map.
- Spawn point quan trọng.
- Ô người chơi đang đứng.
- Zombie đang chiếm ô.
- Công trình khác.

## 12. Hệ Thống Vũ Khí

Thông số vũ khí được gom trong bảng `WEAPON_DEFS` trong `main.py`.

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

Danh sách progression hiện có:

```text
1. Glock 17
2. Dual Beretta 92FS
3. HK MP5
4. Mossberg 500
5. M4A1 Carbine
6. AK-47
7. Benelli M4
8. RPK
9. XM-LAS Prototype
10. M134 Minigun
11. Barrett M82A1
12. XM-Railbreaker
```

Mỗi nhóm súng có vai trò riêng:

- Pistol: ổn định đầu game.
- SMG: dọn zombie thường.
- Shotgun: mạnh ở tầm gần.
- Rifle: cân bằng tầm trung.
- LMG/Minigun: crowd control.
- Laser/Railgun: xuyên mục tiêu, mạnh về late game.
- Sniper/Barrett: sát thương cao, hợp đánh Elite/Titan.

## 13. Hệ Thống Level, Perk Và Meta Progression

Trong trận:

- Người chơi nhận XP khi hạ zombie.
- Khi lên level, chọn 1 trong 3 perk.
- Perk có thể tăng máu, tốc độ, sát thương, hút vàng, giảm reload hoặc buff turret.

Sau mỗi run:

- SaveManager cập nhật high score.
- Có thể lưu tổng kill, tổng vàng, điểm cao nhất.
- Meta progression cho phép mở rộng nâng cấp vĩnh viễn nhẹ.

## 14. UI Và HUD

HUD hiện gồm:

- HP bar.
- XP bar.
- Level.
- Vàng.
- Wave.
- Số zombie còn lại.
- Countdown giữa wave nếu có.
- Hotbar dưới màn hình.
- Bảng chỉ số bằng phím `I`.
- Minimap.
- Developer/debug info nếu bật Developer Mode.

Các hiệu ứng UI:

- Cảnh báo HP thấp bằng viền đỏ nhẹ.
- Banner khi wave bắt đầu.
- Cảnh báo Titan.
- Floating text khi nhận vàng, gây sát thương, lên level hoặc nâng cấp.

## 15. Map Và Tiled

Game có 3 map chính:

- Warehouse / Nhà kho.
- Crossfire Yard / Sân giao tranh.
- Split Ruins / Tàn tích chia cắt.

Map có thể được import từ Tiled JSON nếu đặt đúng trong:

```text
assets/maps/
```

Tileset đặt trong:

```text
assets/tilesets/
```

Quy chuẩn layer xem tại:

```text
MAP_GUIDE.md
```

Các layer Tiled được hỗ trợ:

- `ground`
- `decals`
- `obstacles`
- `props`
- `collision`
- `lighting`
- `gameplay_objects`

Object gameplay được hỗ trợ:

- `player_spawn`
- `zombie_spawn`
- `boss_spawn`
- `build_zone`
- `no_build_zone`
- `safe_zone`
- `choke_point_marker`

## 16. Hiệu Ứng Và Âm Thanh

Hiệu ứng hình ảnh:

- Floating damage number.
- Floating gold number.
- Muzzle flash.
- Hit flash.
- Blood decal có giới hạn.
- Poison pool của Spitter.
- Shockwave của Boomer/Titan.
- Warning circle trước stomp/leap.
- Camera shake nhẹ.
- Vignette và viền đỏ khi thấp máu.

Âm thanh:

- SFX theo nhóm súng.
- SFX zombie.
- SFX UI.
- SFX reload, coin, hit, explosion.
- Nhạc menu, nhạc combat, nhạc boss.

Nếu thiếu asset âm thanh, game dùng fallback hoặc bỏ qua an toàn để không crash.

## 17. Build EXE

Project có script build EXE:

```powershell
.\build_exe.ps1
```

Hoặc:

```bat
build_exe.bat
```

Hướng dẫn chi tiết nằm trong:

```text
BUILD_EXE.md
```

Mục tiêu build:

- Dùng PyInstaller.
- Ưu tiên `onedir` để dễ debug asset.
- Bundle `assets/`, `maps/`, `tilesets/`, `audio/`.
- Save file lưu ở AppData hoặc thư mục user data, không lưu trong thư mục tạm.

## 18. Công Cụ Cân Bằng Và Demo

### `tools/balance_audit.py`

Dùng để:

- Tính DPS ước lượng từng súng.
- Kiểm tra progression vũ khí.
- Hỗ trợ cân bằng giá nâng cấp, damage, reload, fire rate.

### `ALGORITHM_DEMO_GUIDE.md`

Hướng dẫn bật overlay demo thuật toán:

- `F1`: bật/tắt Algorithm Demo.
- `F2`: đổi layer hiển thị.
- `F3`: bật/tắt panel giải thích.

Các lớp demo:

- Collision.
- Spawn point.
- Flow-field.
- A* path.
- AI role.

## 19. Cách Chạy Và Test

Cài thư viện:

```powershell
py -m pip install -r requirements.txt
```

Chạy game:

```powershell
py main.py
```

Smoke test:

```powershell
py main.py --smoke
```

Compile nhanh:

```powershell
py -m py_compile main.py ui_manager.py map_manager.py save_manager.py path_utils.py tools\balance_audit.py test_gate_and_fence.py
```

Test thủ công:

1. Mở game.
2. Vào Start.
3. Chọn độ khó.
4. Chọn map.
5. Chọn nhân vật.
6. Vào trận.
7. Test bắn, reload, nhặt vàng, nâng cấp súng.
8. Test đặt trụ, hàng rào, cổng.
9. Test zombie không xuyên tường/hàng rào.
10. Bật `F1` để demo thuật toán nếu cần.

## 20. Hướng Refactor Tiếp Theo

Hiện `main.py` vẫn khá lớn. Nếu tiếp tục refactor, nên tách dần:

```text
weapon_system.py     Vũ khí, đạn, reload, upgrade
zombie_system.py     Zombie stats, AI, skill, Titan phase
building_system.py   Công trình, build validation, repair
effect_manager.py    Particle, floating text, shockwave, decal
audio_manager.py     Load/play sound, music switching
wave_manager.py      Spawn queue, wave reward, difficulty scaling
```

Mục tiêu dài hạn:

- `main.py` chỉ còn điều phối vòng lặp chính.
- Mỗi hệ thống có file riêng, dễ test và dễ mở rộng.
- Asset/config tách khỏi code để dễ chỉnh gameplay.
