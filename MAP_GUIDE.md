# Pixel Zombie Siege - Tiled Map Guide

Tài liệu này mô tả quy chuẩn tạo map bằng Tiled Map Editor để game có thể load map từ file JSON trong `assets/maps/`.

## 1. Thiết lập Map

Tile size khuyến nghị:
- `32x32`: phù hợp nhất với gameplay hiện tại.
- `48x48`: có thể dùng nếu muốn tile lớn hơn, nhưng gameplay đang được cân bằng quanh `32x32`.

Map size khuyến nghị:
- `60x40 tiles`: kích thước vừa, dễ kiểm soát wave.
- `80x50 tiles`: rộng hơn, phù hợp map nhiều lối và nhiều khu thủ.

Map type nên dùng:
- Orientation: `Orthogonal`
- Tile Layer Format khi export JSON: ưu tiên `CSV` hoặc data JSON dạng list không nén.

## 2. Layer Bắt Buộc

Tạo đúng các layer sau, viết thường và dùng dấu gạch dưới nếu cần:

1. `ground`
2. `decals`
3. `obstacles`
4. `props`
5. `collision`
6. `lighting`
7. `gameplay_objects`

Render order trong game:

```text
ground -> decals -> obstacles -> props -> lighting
```

## 3. Quy Tắc Layer

`ground`
: Nền chính của map như sàn bê tông, đất, cỏ, gạch, nền kho.

`decals`
: Chi tiết nằm trên nền như máu, vết nứt, vết dầu, lá, rêu, cỏ nhỏ, vết cháy.

`obstacles`
: Vật thể nhìn thấy có thể chắn đường như tường, thùng hàng, xe hỏng, đá lớn, barricade.

`props`
: Vật trang trí không nhất thiết có collision như đèn, dây điện, biển báo, rác, hộp nhỏ.

`collision`
: Layer quyết định vùng bị chặn. Tile nào có giá trị khác `0` sẽ được coi là blocked cho player, zombie, pathfinding và xây dựng.

`lighting`
: Overlay ánh sáng nếu có. Layer này được render cuối cùng và có thể dùng tile bán trong suốt.

`gameplay_objects`
: Object layer dùng để đặt spawn point, vùng xây dựng, vùng cấm xây, vùng an toàn và marker gameplay.

## 4. Object Cần Có

Trong layer `gameplay_objects`, tạo object rồi đặt `Type`, `Class`, hoặc `Name` đúng một trong các giá trị sau:

`player_spawn`
: Vị trí spawn của người chơi. Nên có đúng 1 object.

`zombie_spawn`
: Vị trí zombie thường xuất hiện. Mỗi map nên có 3-5 điểm.

`boss_spawn`
: Vị trí Titan/Boss xuất hiện. Nên đặt ở vùng rộng, không bị kẹt.

`build_zone`
: Vùng cho phép xây trụ/hàng rào. Nếu có ít nhất một `build_zone`, game chỉ cho xây trong các vùng này.

`no_build_zone`
: Vùng cấm xây. Dùng để chặn các vị trí quá mạnh hoặc dễ phá cân bằng.

`safe_zone`
: Vùng an toàn quanh người chơi hoặc khu khởi đầu. Zombie spawn trong vùng này sẽ bị loại khỏi danh sách spawn.

`choke_point_marker`
: Marker đánh dấu điểm nghẽn quan trọng. Hiện tại dùng cho thiết kế/balancing, có thể mở rộng AI sau này.

Object point phù hợp cho spawn/marker. Object rectangle phù hợp cho `build_zone`, `no_build_zone`, `safe_zone`.

## 5. Custom Properties Đề Xuất

Các custom properties này chưa bắt buộc cho loader hiện tại, nhưng nên dùng để chuẩn bị mở rộng:

`collision: true/false`
: Gợi ý tile/object có chặn đường hay không.

`buildable: true/false`
: Gợi ý khu vực có cho xây dựng hay không.

`destructible: true/false`
: Gợi ý vật thể có thể bị phá hủy.

`cover: true/false`
: Gợi ý vật thể có thể dùng làm cover hoặc cản line of sight.

## 6. Quy Tắc Thiết Kế Gameplay

- Mỗi map nên có `3-5` điểm `zombie_spawn`.
- Mỗi map nên có `2-4` choke point rõ ràng.
- Mỗi map nên có ít nhất `2` khu phòng thủ tốt.
- Không tạo vị trí phòng thủ bất tử, ví dụ chỉ có một lối vào rộng 1 tile và Titan không thể tiếp cận.
- Không đặt `player_spawn` trong hoặc sát vùng collision.
- Không tạo vùng khiến player bị kẹt khi spawn.
- Không tạo hành lang quá hẹp khiến Titan bị kẹt vĩnh viễn.
- Nên để các đường chính rộng tối thiểu `3-4 tiles`.
- Khu boss nên có khoảng trống lớn hơn zombie thường, đặc biệt quanh `boss_spawn`.
- Không đặt `zombie_spawn` quá gần `player_spawn`; nên cách ít nhất `10-14 tiles`.
- `safe_zone` quanh player spawn nên vừa đủ, không quá rộng để tránh làm wave trống trải.
- `build_zone` nên có giới hạn để trụ/hàng rào có giá trị chiến thuật nhưng không bị spam toàn map.
- `no_build_zone` nên đặt ở cửa spawn zombie, hành lang quá hẹp, hoặc vị trí có thể khóa Titan.

## 7. Cách Export JSON Từ Tiled

1. Mở map trong Tiled.
2. Kiểm tra tên layer đúng theo quy chuẩn.
3. Kiểm tra `gameplay_objects` là Object Layer.
4. Vào `File -> Export As...`.
5. Chọn định dạng `JSON map files (*.json)`.
6. Đặt tên file theo map cần thay:
   - `warehouse.json`
   - `crossfire_yard.json`
   - `split_ruins.json`
7. Tránh bật nén layer data nếu có thể. Loader hiện tại ưu tiên data dạng list/CSV trong JSON.

## 8. Vị Trí Đặt File

Map JSON đặt tại:

```text
assets/maps/
```

Ví dụ:

```text
assets/maps/warehouse.json
assets/maps/crossfire_yard.json
assets/maps/split_ruins.json
```

Tileset image đặt tại:

```text
assets/tilesets/
```

Ví dụ:

```text
assets/tilesets/industrial_tiles.png
assets/tilesets/ruins_tiles.png
assets/tilesets/zombie_city_tiles.png
```

Trong Tiled, đường dẫn tileset image nên dùng đường dẫn tương đối nếu có thể. Nếu thiếu tileset image, game sẽ tạo placeholder tile để tránh crash, nhưng map sẽ không đẹp.

## 9. Checklist Trước Khi Test

- Có layer `collision`.
- `collision` có tile tại mọi tường/vật cản chính.
- Có ít nhất 1 `player_spawn`.
- Có 3-5 `zombie_spawn`.
- Có ít nhất 1 `boss_spawn` nếu map có Titan.
- `player_spawn` không nằm trong collision.
- `boss_spawn` nằm ở khu đủ rộng.
- Không có choke point rộng 1 tile dùng để khóa Titan.
- JSON nằm đúng trong `assets/maps/`.
- Tileset image nằm đúng trong `assets/tilesets/`.

## 10. Cách Test Trong Game

Chạy game:

```powershell
py main.py
```

Nếu JSON đúng tên tồn tại, game sẽ load map từ Tiled. Nếu thiếu file hoặc lỗi JSON, console sẽ hiện warning và game dùng map built-in fallback.

Test nhanh:

1. Chọn map tương ứng trong màn chuẩn bị.
2. Vào trận, kiểm tra player spawn đúng chỗ.
3. Bấm `SPACE` để bắt đầu wave.
4. Kiểm tra zombie spawn đúng vị trí.
5. Kiểm tra zombie/player không đi xuyên vùng `collision`.
6. Chọn đặt trụ/hàng rào, kiểm tra `build_zone` và `no_build_zone`.
7. Đợi Titan xuất hiện hoặc test bằng wave boss, kiểm tra Titan không bị kẹt vĩnh viễn.
