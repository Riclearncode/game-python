# Pixel Zombie Siege

Pixel Zombie Siege là game top-down 2D zombie survival viết bằng Python + Pygame. Người chơi sinh tồn theo từng wave, bắn zombie, nhặt vàng, lên cấp, chọn perk, nâng cấp vũ khí, xây công trình phòng thủ và chiến đấu với Titan Boss.

Game tập trung vào 3 trụ cột:

- Combat: nhiều loại súng, đạn giới hạn, reload, auto-fire, power-up và hiệu ứng bắn.
- Defense: turret, hàng rào, cổng, bẫy, mìn, tường thép và sửa/nâng cấp công trình.
- AI/Pathfinding: flow-field, A*, collision grid, dynamic obstacle và boss phase.

## Cài Đặt

```powershell
py -m pip install -r requirements.txt
```

## Chạy Game

```powershell
py main.py
```

Smoke test không mở cửa sổ:

```powershell
py main.py --smoke
```

Game mặc định chạy fullscreen/adaptive resolution, có menu chính, option, màn chọn độ khó, chọn map, chọn nhân vật và màn chơi chính.

## Điều Khiển

- `WASD` hoặc phím mũi tên: di chuyển.
- Chuột trái: bắn/đặt công trình.
- Chuột phải hoặc `B`: hủy chế độ xây.
- `Space`: bắt đầu wave hoặc bỏ qua countdown giữa wave.
- `1`: nâng cấp vũ khí.
- `2`: xây turret thường.
- `3`: xây hàng rào.
- `4`: xây cổng.
- `5`: bẫy gai.
- `6`: mìn.
- `7`: tường thép.
- `8`: machine turret.
- `9`: laser turret.
- `0`: slow turret.
- `G`: mở/đóng cổng gần nhất.
- `R`: nạp đạn.
- `E`: sửa công trình gần nhất.
- `Shift`: dash.
- `F`: bật/tắt auto-fire.
- `I`: bật/tắt bảng chỉ số.
- `P` hoặc nút Pause: tạm dừng.
- `F10`: Developer Mode, vô hạn vàng để test.

## Algorithm Demo

Game có chế độ hỗ trợ demo thuật toán để dùng khi thuyết trình hoặc viết báo cáo.

- `F1`: bật/tắt Algorithm Demo Overlay.
- `F2`: đổi lớp hiển thị.
- `F3`: bật/tắt panel giải thích.

Các lớp hiển thị:

- `All`: toàn bộ lớp demo.
- `Collision`: tường, vật cản động, hàng rào, cổng, turret.
- `Spawns`: điểm spawn zombie thường và boss.
- `Flow Field`: mũi tên flow-field BFS cho Walker.
- `A* Paths`: đường đi A* của zombie.
- `AI Roles`: nhãn hành vi từng zombie như Flow BFS, Flank A*, Keep Range, Dash Priority, Dodge LOS, Titan Phase.

Xem thêm: [ALGORITHM_DEMO_GUIDE.md](ALGORITHM_DEMO_GUIDE.md)

## Hệ Thống Zombie

- Walker: zombie chậm, đi theo flow-field BFS dùng chung.
- Runner: zombie nhanh, ưu tiên flank/đường vòng bằng A*.
- Spitter: giữ khoảng cách, phun độc tạo vùng AOE gây sát thương theo thời gian.
- Boomer: dash vào người chơi hoặc cụm công trình, phun dịch xanh làm zombie tăng tốc, chết sẽ nổ AOE.
- Stalker: flank và né đường bắn nếu nằm trong line-of-fire.
- Titan Boss: kích thước lớn, dùng clearance A*, có charge, stomp, summon, leap khi bị kẹt và phase theo HP.

Titan phase:

- Trên 70% HP: đánh và di chuyển bình thường.
- Dưới 70% HP: charge thường xuyên hơn.
- Dưới 40% HP: summon zombie.
- Dưới 20% HP: stomp liên tục hơn nhưng có warning circle để né.

## AI Và Pathfinding

Game dùng nhiều thuật toán theo từng mục tiêu gameplay:

- Flow-field BFS cho Walker để xử lý số lượng zombie lớn hiệu quả.
- Weighted A* cho Runner/Boomer/Stalker/Spitter.
- Clearance A* cho Titan vì boss có bán kính lớn.
- Collision grid từ MapManager.
- Dynamic obstacles từ hàng rào, cổng đóng, turret và tường thép.
- Path cache để tránh tính A* cho mọi zombie mỗi frame.

Zombie không đi xuyên tường, container, xe hỏng, hàng rào, cổng đóng hoặc turret. Khi bị chặn, zombie có thể đánh công trình hoặc đi vòng nếu có đường hợp lý.

## Vũ Khí

Vũ khí có tier, magazine, reload time, fire rate, spread, pierce và vai trò riêng. Người chơi nâng cấp bằng vàng:

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

Mỗi nhóm súng có SFX/feedback riêng: pistol, SMG, shotgun, rifle, machine gun, sniper, laser và railgun. Shotgun có pellet/spread rõ, laser có beam, railgun có trail mạnh và Minigun có spin-up.

## Level, Perk Và Meta Progression

Trong trận:

- Mỗi lần lên level, người chơi chọn 1 trong 3 perk.
- Perk gồm tăng máu, tăng tốc, giảm reload, tăng hút vàng, tăng sát thương turret, giảm giá xây.

Sau mỗi run:

- Người chơi nhận meta point.
- Meta point tạo bonus vĩnh viễn nhẹ cho HP, damage, hút vàng và giảm giá xây.
- SaveManager lưu progression, achievement, unlock class/map/weapon và high score.

## Xây Dựng

Công trình hiện có:

- Turret thường.
- Machine turret.
- Laser turret.
- Slow turret.
- Hàng rào.
- Cổng mở/đóng bằng `G`.
- Bẫy gai.
- Mìn.
- Tường thép.

UI xây dựng có ghost preview:

- Màu xanh: đặt được.
- Màu đỏ: không đặt được.
- Hiển thị giá vàng, lý do không đặt được và tầm bắn turret.
- Hover công trình hiện HP và chi phí sửa.

Hàng rào và cổng có giá trị chiến thuật: chặn zombie thường, có HP, có thể bị phá, có thể sửa, nhưng Titan vẫn có công cụ phá tuyến phòng thủ.

## Map Và Tiled

Game có 3 map chính:

- Warehouse / Nhà kho.
- Crossfire Yard / Sân giao tranh.
- Split Ruins / Tàn tích chia cắt.

MapManager chịu trách nhiệm:

- Load map builtin.
- Load Tiled JSON nếu có.
- Render layer map.
- Quản lý collision grid.
- Quản lý buildable grid.
- Quản lý spawn point.
- Cập nhật dynamic obstacles.

Thư mục map:

- `assets/maps/`
- `assets/tilesets/`

Hướng dẫn tạo map bằng Tiled: [MAP_GUIDE.md](MAP_GUIDE.md)

## UI/HUD

Game có:

- Main menu với background.
- Option menu cho ngôn ngữ, music, SFX, auto-fire, Developer Mode.
- Flow chọn difficulty -> map -> character.
- HUD HP/XP, vàng, wave, enemy count.
- Hotbar đầy đủ phím tắt.
- Minimap góc màn hình.
- Boss HP bar.
- Mission tracker.
- Game Over screen có thống kê run và New Record.

## Mission, Loot Và Power-Up

Mission trong trận:

- Sống sót 3 phút.
- Hạ 20 Runner.
- Giữ ít nhất 1 turret sống qua wave.

Power-up:

- Medkit.
- Overdrive.
- Shield.
- Haste.
- Shock Core.
- Double Damage.
- Ammo Pack.
- Repair Pulse.
- Supply Crate.

Elite/Titan có thể rơi loot hiếm.

## Audio

Game có mixer riêng cho:

- UI.
- Weapon.
- Zombie.
- World/SFX.

Nhạc nền đổi khi Titan xuất hiện. Có cảnh báo âm thanh khi HP thấp và khi wave bắt đầu.

Nguồn audio:

- Kenney RPG Audio.
- OpenGameArt monster/explosion SFX.
- Bộ synth audio tự tạo trong `assets/audio/synth`.

Tạo lại synth audio:

```powershell
py tools\generate_synth_audio.py
```

Chi tiết nguồn: `assets/audio/SOURCES.md`

## Save Và High Score

SaveManager lưu JSON an toàn:

- Settings.
- High score tổng.
- High score theo difficulty/map/class.
- Total runs.
- Total kills.
- Total gold.
- Meta points.
- Unlocks.
- Achievements.

Khi chạy từ source, save ở:

```text
save/save_data.json
```

Khi chạy bản EXE, save ở:

```text
%APPDATA%/PixelZombieSiege/save_data.json
```

Nếu save bị lỗi/corrupt, game backup file lỗi và tạo save mới, không crash.

## Balance Tools

Chạy audit cân bằng weapon/zombie/economy:

```powershell
py tools\balance_audit.py
```

Ghi chú cân bằng: [BALANCE_NOTES.md](BALANCE_NOTES.md)

## Build EXE

Build bản Windows onedir:

```powershell
.\build_exe.ps1
```

Hoặc:

```bat
build_exe.bat
```

Output:

```text
dist/PixelZombieSiege/PixelZombieSiege.exe
```

Hướng dẫn chi tiết: [BUILD_EXE.md](BUILD_EXE.md)

## GitHub Actions

Workflow `.github/workflows/build-exe.yml` tự build EXE Windows khi:

- chạy thủ công bằng `workflow_dispatch`;
- push tag dạng `v*`;
- publish GitHub Release.

Workflow sẽ:

1. Cài dependency.
2. Chạy smoke test.
3. Build EXE bằng PyInstaller.
4. Zip thư mục `dist/PixelZombieSiege`.
5. Upload artifact `PixelZombieSiege-windows.zip`.

## Cấu Trúc Chính

- `main.py`: game loop, gameplay, zombie, player, weapon, building, UI hooks.
- `ui_manager.py`: UI/menu/HUD/hotbar.
- `map_manager.py`: map, collision, Tiled JSON, spawn/build grid.
- `save_manager.py`: save, high score, meta progression.
- `path_utils.py`: xử lý đường dẫn source/EXE.
- `tools/balance_audit.py`: audit cân bằng.
- `tools/generate_synth_audio.py`: tạo audio synth.
- `ALGORITHM_DEMO_GUIDE.md`: hướng dẫn demo thuật toán.
- `MAP_GUIDE.md`: hướng dẫn tạo map bằng Tiled.
- `BUILD_EXE.md`: hướng dẫn build EXE.

## Test Nhanh Trước Khi Nộp/Release

```powershell
py -m py_compile main.py ui_manager.py map_manager.py save_manager.py path_utils.py tools\balance_audit.py test_gate_and_fence.py
py main.py --smoke
py test_gate_and_fence.py
py tools\balance_audit.py
```

