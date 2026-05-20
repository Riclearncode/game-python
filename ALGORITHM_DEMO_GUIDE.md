# Algorithm Demo Guide - Pixel Zombie Siege

File này dùng để hỗ trợ demo và viết báo cáo về các thuật toán AI/pathfinding trong game.

## Cách bật trong game

Chạy game:

```powershell
py main.py
```

Vào trận rồi dùng phím:

- `F1`: bật/tắt Algorithm Demo Overlay.
- `F2`: đổi lớp hiển thị.
- `F3`: bật/tắt panel giải thích.
- `F10`: bật Developer Mode nếu cần test nhanh.

## Các lớp hiển thị

### All

Hiển thị tất cả lớp demo cùng lúc:

- Collision grid.
- Spawn points.
- Flow-field.
- A* path.
- AI role/target lines.

Phù hợp để demo tổng quan.

### Collision

Mục đích:

- Ô đỏ: tường/vật cản từ map collision.
- Ô cam: dynamic obstacles như hàng rào, cổng đóng, turret, tường thép.
- Viền xanh/cam quanh công trình: cho biết công trình có chặn đường hay không.

Dùng trong báo cáo phần:

- Collision grid.
- Dynamic obstacles.
- Zombie không đi xuyên tường/hàng rào.

### Spawns

Mục đích:

- Vòng xanh: spawn zombie thường.
- Vòng tím: boss/Titan spawn.

Dùng trong báo cáo phần:

- Thiết kế wave.
- Spawn an toàn, không spawn trong vật cản.

### Flow Field

Walker dùng flow-field BFS để đi về phía player.

Ý tưởng:

1. Lấy vị trí player làm goal.
2. Build distance field từ goal ra các ô đi được.
3. Mỗi Walker nhìn các ô lân cận và đi về ô có distance nhỏ hơn.

Ưu điểm:

- Nhiều zombie thường có thể dùng chung một field.
- Rẻ hơn việc chạy A* riêng cho từng Walker mỗi frame.
- Rất hợp cho zombie số lượng lớn.

Dùng trong báo cáo phần:

- BFS / distance field.
- Shared pathfinding.
- Tối ưu hiệu năng.

### A* Paths

Hiển thị đường đi đang được từng zombie dùng.

Vai trò:

- Runner: A* tới điểm flank.
- Spitter: A* tới điểm giữ khoảng cách.
- Boomer: A* tới player/cụm công trình ưu tiên.
- Stalker: A* tới vị trí flank, kết hợp né line-of-sight.
- Titan: clearance A* để tránh kẹt vì kích thước lớn.

Dùng trong báo cáo phần:

- A* pathfinding.
- Weighted A*.
- Path cache.
- Zombie có hành vi khác nhau theo chủng loại.

### AI Roles

Hiển thị nhãn ngắn và target line của từng zombie:

- `Flow BFS`: Walker đi theo flow-field.
- `Flank A*`: Runner vòng sang sườn.
- `Keep range`: Spitter giữ khoảng cách để phun độc.
- `Dash priority`: Boomer ưu tiên lao vào player/cụm công trình.
- `Dodge LOS`: Stalker né đường bắn.
- `Titan P1/P2/P3/P4`: boss phase theo máu.

Dùng trong báo cáo phần:

- Thiết kế AI theo vai trò.
- Boss phase.
- Hành vi đặc biệt.

## Gợi ý demo trực tiếp

1. Bật `F10` để có vàng vô hạn nếu cần.
2. Vào map Warehouse hoặc Crossfire Yard.
3. Đặt vài hàng rào/cổng/trụ.
4. Bấm `SPACE` gọi wave.
5. Bật `F1`.
6. Bấm `F2` lần lượt qua các lớp:
   - Collision.
   - Flow Field.
   - A* Paths.
   - AI Roles.
7. Chụp màn hình từng lớp để đưa vào báo cáo.

## Nội dung có thể viết trong báo cáo

### Zombie thường

Walker dùng flow-field BFS dùng chung cho cả đám zombie, giúp giảm chi phí tính toán khi số lượng zombie đông.

### Zombie nhanh

Runner dùng A* tới điểm flank thay vì chỉ chạy thẳng vào player, làm người chơi khó đứng yên phòng thủ.

### Zombie tầm xa

Spitter tìm vị trí có khoảng cách hợp lý và còn line-of-sight để phun độc, tránh lao vào quá gần người chơi.

### Boomer

Boomer chọn mục tiêu ưu tiên giữa player và cụm công trình, sau đó dash vào để nổ hoặc phun dịch.

### Stalker

Stalker kiểm tra hướng ngắm của người chơi. Nếu nằm trong đường bắn, nó ưu tiên né ngang rồi tiếp tục flank.

### Titan

Titan dùng clearance A* vì bán kính lớn hơn zombie thường. Boss có phase theo HP:

- Trên 70%: di chuyển/đánh bình thường.
- Dưới 70%: charge nhiều hơn.
- Dưới 40%: summon zombie.
- Dưới 20%: stomp liên tục hơn nhưng có warning circle.

## Lưu ý hiệu năng

Overlay chỉ nên dùng khi demo/debug vì nó vẽ thêm grid, path và text. Khi chơi bình thường, tắt bằng `F1`.
