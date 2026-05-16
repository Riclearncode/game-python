import json
import math
import os

import pygame


Vec2 = pygame.math.Vector2

TILED_LAYER_ORDER = ("ground", "decals", "obstacles", "props", "lighting")
TILED_MAP_FILES = {
    "warehouse": "warehouse.json",
    "crossfire": "crossfire_yard.json",
    "split": "split_ruins.json",
}
FLIP_MASK = 0x1FFFFFFF


def _clamp(value, low, high):
    return max(low, min(high, value))


def _dist_point_rect(point, rect):
    px, py = point
    cx = _clamp(px, rect.left, rect.right)
    cy = _clamp(py, rect.top, rect.bottom)
    return math.hypot(px - cx, py - cy)


def _tile_noise(x, y, salt=0):
    value = (x * 928371 + y * 689287 + salt * 19349663) & 0xFFFFFFFF
    value ^= value >> 13
    value = (value * 1274126177) & 0xFFFFFFFF
    return value


def _normalized_name(value):
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


class MapManager:
    """Owns the active map and exposes the old TileMap API used by gameplay."""

    def __init__(self, maps, themes, default_map="warehouse", tile_size=32, base_dir=None):
        self.maps = maps
        self.themes = themes
        self.default_map = default_map if default_map in maps else next(iter(maps))
        self.default_tile_size = tile_size
        self.tile_size = tile_size
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self.maps_dir = os.path.join(self.base_dir, "assets", "maps")
        self.tilesets_dir = os.path.join(self.base_dir, "assets", "tilesets")
        self.dynamic_obstacles = set()
        self.rows = []
        self.map_id = self.default_map
        self.theme = {}
        self.grid_w = 0
        self.grid_h = 0
        self.world_w = 0
        self.world_h = 0
        self.collision_grid = []
        self.buildable_grid = []
        self.zombie_spawn_points = []
        self.boss_spawn_points = []
        self.player_spawn = None
        self.safe_zones = []
        self.build_zones = []
        self.no_build_zones = []
        self.choke_point_markers = []
        self.loaded_from_tiled = False
        self.tiled_path = None
        self.tiled_layers = {}
        self.tile_surfaces = {}
        self._missing_warnings = set()
        self._boss_spawn_cache = {}
        self._player_spawn_cache = {}
        self.load_builtin_map(default_map)

    def has_map(self, map_name):
        return map_name in self.maps or os.path.exists(self.tiled_path_for(map_name))

    def tiled_path_for(self, map_name):
        filename = TILED_MAP_FILES.get(map_name, f"{map_name}.json")
        return os.path.join(self.maps_dir, filename)

    def load_builtin_map(self, map_name):
        target = map_name if map_name in self.maps else self.default_map
        tiled_path = self.tiled_path_for(target)
        if os.path.exists(tiled_path):
            try:
                self.load_tiled_map(target, tiled_path, fallback_rows=self.maps.get(target))
                return self
            except Exception as exc:
                print(f"[MapManager] Warning: could not load Tiled map '{tiled_path}': {exc}. Using built-in fallback.")
        else:
            self._warn_missing_tiled(tiled_path, target)
        return self.load_builtin_fallback(target)

    def _warn_missing_tiled(self, path, map_name):
        if path in self._missing_warnings:
            return
        self._missing_warnings.add(path)
        print(f"[MapManager] Warning: Tiled map for '{map_name}' not found at '{path}'. Using built-in fallback.")

    def load_builtin_fallback(self, map_name):
        self.map_id = map_name if map_name in self.maps else self.default_map
        self.tile_size = self.default_tile_size
        self.rows = list(self.maps[self.map_id])
        self.theme = self.themes.get(self.map_id, self.themes.get(self.default_map, {}))
        self.grid_h = len(self.rows)
        self.grid_w = len(self.rows[0]) if self.rows else 0
        self.world_w = self.grid_w * self.tile_size
        self.world_h = self.grid_h * self.tile_size
        self.dynamic_obstacles = set()
        self.loaded_from_tiled = False
        self.tiled_path = None
        self.tiled_layers = {}
        self.tile_surfaces = {}
        self.player_spawn = None
        self.safe_zones = []
        self.build_zones = []
        self.no_build_zones = []
        self.choke_point_markers = []
        self._rebuild_static_grids_from_rows()
        self.zombie_spawn_points = self._build_edge_spawn_points()
        self.boss_spawn_points = []
        self._boss_spawn_cache = {}
        self._player_spawn_cache = {}
        return self

    def load_tiled_map(self, map_name, path=None, fallback_rows=None):
        path = path or self.tiled_path_for(map_name)
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)

        self.map_id = map_name
        self.theme = self.themes.get(map_name, self.themes.get(self.default_map, {}))
        self.tile_size = int(data.get("tilewidth") or self.default_tile_size)
        tile_height = int(data.get("tileheight") or self.tile_size)
        if tile_height != self.tile_size:
            print(f"[MapManager] Warning: non-square tiles in '{path}'. Collision will use tilewidth.")
        if self.tile_size != self.default_tile_size:
            print(
                f"[MapManager] Warning: '{path}' uses {self.tile_size}px tiles; "
                f"game systems are balanced around {self.default_tile_size}px."
            )

        self.grid_w = int(data.get("width") or 0)
        self.grid_h = int(data.get("height") or 0)
        if self.grid_w <= 0 or self.grid_h <= 0:
            raise ValueError("map width/height must be positive")
        self.world_w = self.grid_w * self.tile_size
        self.world_h = self.grid_h * self.tile_size
        self.rows = ["." * self.grid_w for _ in range(self.grid_h)]
        self.dynamic_obstacles = set()
        self.loaded_from_tiled = True
        self.tiled_path = path
        self.tiled_layers = {}
        self.tile_surfaces = self._load_tileset_surfaces(data, path)
        self.player_spawn = None
        self.zombie_spawn_points = []
        self.boss_spawn_points = []
        self.safe_zones = []
        self.build_zones = []
        self.no_build_zones = []
        self.choke_point_markers = []

        layers = data.get("layers") or []
        layer_by_name = {}
        for layer in layers:
            name = _normalized_name(layer.get("name"))
            if not name:
                continue
            layer_by_name[name] = layer
            if layer.get("type") == "tilelayer" and name in TILED_LAYER_ORDER:
                self.tiled_layers[name] = self._extract_layer_data(layer)
            elif layer.get("type") == "objectgroup" and name == "gameplay_objects":
                self._load_gameplay_objects(layer)

        collision_layer = layer_by_name.get("collision")
        obstacle_layer = layer_by_name.get("obstacles")
        if collision_layer and collision_layer.get("type") == "tilelayer":
            self._build_collision_from_tile_data(self._extract_layer_data(collision_layer))
        elif obstacle_layer and obstacle_layer.get("type") == "tilelayer":
            print(f"[MapManager] Warning: '{path}' has no collision layer. Using obstacles as collision fallback.")
            self._build_collision_from_tile_data(self._extract_layer_data(obstacle_layer))
        elif fallback_rows:
            print(f"[MapManager] Warning: '{path}' has no collision layer. Using built-in collision fallback.")
            self.rows = list(fallback_rows)
            self._rebuild_static_grids_from_rows()
        else:
            print(f"[MapManager] Warning: '{path}' has no collision layer. Treating map as open.")
            self._build_collision_from_tile_data([0] * (self.grid_w * self.grid_h))

        self._apply_gameplay_build_zones()
        if not self.zombie_spawn_points:
            self.zombie_spawn_points = self._build_edge_spawn_points()
        if not self.player_spawn:
            self.player_spawn = self._find_player_spawn(0)
        self._boss_spawn_cache = {}
        self._player_spawn_cache = {}
        return self

    def _extract_layer_data(self, layer):
        if "data" in layer and isinstance(layer["data"], list):
            return list(layer["data"])
        data = [0] * (self.grid_w * self.grid_h)
        for chunk in layer.get("chunks") or []:
            chunk_w = int(chunk.get("width") or 0)
            chunk_h = int(chunk.get("height") or 0)
            chunk_x = int(chunk.get("x") or 0)
            chunk_y = int(chunk.get("y") or 0)
            chunk_data = chunk.get("data") or []
            for local_y in range(chunk_h):
                for local_x in range(chunk_w):
                    world_x = chunk_x + local_x
                    world_y = chunk_y + local_y
                    if not (0 <= world_x < self.grid_w and 0 <= world_y < self.grid_h):
                        continue
                    src = local_y * chunk_w + local_x
                    if src < len(chunk_data):
                        data[world_y * self.grid_w + world_x] = chunk_data[src]
        return data

    def _load_tileset_surfaces(self, data, map_path):
        surfaces = {}
        for tileset in data.get("tilesets") or []:
            first_gid = int(tileset.get("firstgid") or 1)
            image_path = self._tileset_image_path(tileset, map_path)
            tile_w = int(tileset.get("tilewidth") or self.tile_size)
            tile_h = int(tileset.get("tileheight") or self.tile_size)
            columns = int(tileset.get("columns") or 0)
            tile_count = int(tileset.get("tilecount") or 0)
            if not image_path or not os.path.exists(image_path):
                if image_path:
                    print(f"[MapManager] Warning: tileset image missing: '{image_path}'. Using placeholder tiles.")
                self._add_placeholder_tiles(surfaces, first_gid, max(tile_count, 64))
                continue
            try:
                image = pygame.image.load(image_path).convert_alpha()
            except pygame.error as exc:
                print(f"[MapManager] Warning: could not load tileset image '{image_path}': {exc}. Using placeholders.")
                self._add_placeholder_tiles(surfaces, first_gid, max(tile_count, 64))
                continue
            if columns <= 0:
                columns = max(1, image.get_width() // tile_w)
            if tile_count <= 0:
                tile_count = max(1, (image.get_width() // tile_w) * (image.get_height() // tile_h))
            for index in range(tile_count):
                sx = (index % columns) * tile_w
                sy = (index // columns) * tile_h
                rect = pygame.Rect(sx, sy, tile_w, tile_h)
                tile = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
                if image.get_rect().contains(rect):
                    source = image.subsurface(rect)
                    if source.get_size() != (self.tile_size, self.tile_size):
                        source = pygame.transform.scale(source, (self.tile_size, self.tile_size))
                    tile.blit(source, (0, 0))
                else:
                    tile.blit(self._placeholder_tile(first_gid + index), (0, 0))
                surfaces[first_gid + index] = tile
        if not surfaces:
            self._add_placeholder_tiles(surfaces, 1, 128)
        return surfaces

    def _tileset_image_path(self, tileset, map_path):
        image = tileset.get("image")
        if not image:
            return None
        if os.path.isabs(image):
            return image
        candidates = [
            os.path.normpath(os.path.join(os.path.dirname(map_path), image)),
            os.path.normpath(os.path.join(self.tilesets_dir, image)),
        ]
        return next((candidate for candidate in candidates if os.path.exists(candidate)), candidates[0])

    def _add_placeholder_tiles(self, surfaces, first_gid, count):
        for index in range(count):
            surfaces[first_gid + index] = self._placeholder_tile(first_gid + index)

    def _placeholder_tile(self, gid):
        surface = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
        n = _tile_noise(gid, gid // 7, 41)
        color = (
            42 + n % 70,
            48 + (n >> 8) % 70,
            54 + (n >> 16) % 70,
            255,
        )
        surface.fill(color)
        pygame.draw.rect(surface, (18, 22, 28, 170), surface.get_rect(), 1)
        if gid % 5 == 0:
            pygame.draw.line(surface, (230, 230, 220, 95), (4, self.tile_size - 5), (self.tile_size - 5, 4), 2)
        return surface

    def _build_collision_from_tile_data(self, data):
        self.collision_grid = []
        self.buildable_grid = []
        rows = []
        for y in range(self.grid_h):
            collision_row = []
            buildable_row = []
            row_chars = []
            for x in range(self.grid_w):
                index = y * self.grid_w + x
                blocked = index < len(data) and (int(data[index]) & FLIP_MASK) != 0
                collision_row.append(blocked)
                buildable_row.append(not blocked)
                row_chars.append("#" if blocked else ".")
            self.collision_grid.append(collision_row)
            self.buildable_grid.append(buildable_row)
            rows.append("".join(row_chars))
        self.rows = rows

    def _load_gameplay_objects(self, layer):
        for obj in layer.get("objects") or []:
            kind = _normalized_name(obj.get("type") or obj.get("class") or obj.get("name"))
            if not kind:
                continue
            cells = self._object_cells(obj)
            if not cells:
                continue
            if kind == "player_spawn":
                self.player_spawn = cells[0]
            elif kind == "zombie_spawn":
                self.zombie_spawn_points.extend(cells)
            elif kind == "boss_spawn":
                self.boss_spawn_points.extend(cells)
            elif kind == "build_zone":
                self.build_zones.extend(cells)
            elif kind == "no_build_zone":
                self.no_build_zones.extend(cells)
            elif kind == "safe_zone":
                self.safe_zones.extend(cells)
            elif kind == "choke_point_marker":
                self.choke_point_markers.extend(cells)

    def _object_cells(self, obj):
        x = float(obj.get("x") or 0)
        y = float(obj.get("y") or 0)
        width = float(obj.get("width") or 0)
        height = float(obj.get("height") or 0)
        if width <= 0 and height <= 0:
            cell = self.world_to_tile(x, y)
            return [cell] if self.in_bounds(cell) else []
        left = int(x // self.tile_size)
        top = int(y // self.tile_size)
        right = max(left, int(math.ceil((x + max(width, 1)) / self.tile_size) - 1))
        bottom = max(top, int(math.ceil((y + max(height, 1)) / self.tile_size) - 1))
        cells = []
        for cy in range(top, bottom + 1):
            for cx in range(left, right + 1):
                cell = (cx, cy)
                if self.in_bounds(cell):
                    cells.append(cell)
        return cells

    def _apply_gameplay_build_zones(self):
        if self.build_zones:
            allowed = set(self.build_zones)
            for y in range(self.grid_h):
                for x in range(self.grid_w):
                    if (x, y) not in allowed:
                        self.buildable_grid[y][x] = False
        for cell in self.no_build_zones:
            if self.in_bounds(cell):
                self.buildable_grid[cell[1]][cell[0]] = False
        for cell in self.safe_zones:
            if self.in_bounds(cell):
                self.buildable_grid[cell[1]][cell[0]] = False
        safe = set(self.safe_zones)
        if safe:
            self.zombie_spawn_points = [cell for cell in self.zombie_spawn_points if cell not in safe]

    def _rebuild_static_grids_from_rows(self):
        self.collision_grid = []
        self.buildable_grid = []
        for row in self.rows:
            collision_row = []
            buildable_row = []
            for value in row:
                blocked = value == "#"
                collision_row.append(blocked)
                buildable_row.append(not blocked)
            self.collision_grid.append(collision_row)
            self.buildable_grid.append(buildable_row)

    def _build_edge_spawn_points(self):
        cells = []
        safe = set(self.safe_zones)
        for y, row in enumerate(self.rows):
            for x, value in enumerate(row):
                cell = (x, y)
                if value == "#" or cell in safe:
                    continue
                if x in (1, self.grid_w - 2) or y in (1, self.grid_h - 2):
                    cells.append(cell)
        return cells

    def update_dynamic_obstacles(self, buildings):
        self.dynamic_obstacles = {building.cell for building in buildings if getattr(building, "alive", False)}

    def get_player_spawn(self, radius=0):
        cache_key = int(radius)
        if cache_key not in self._player_spawn_cache:
            if self.player_spawn and self.is_clear_for_radius(self.player_spawn, radius):
                self._player_spawn_cache[cache_key] = self.player_spawn
            else:
                self._player_spawn_cache[cache_key] = self._find_player_spawn(radius)
        return self._player_spawn_cache[cache_key]

    def get_zombie_spawns(self):
        return list(self.zombie_spawn_points)

    def get_boss_spawns(self, radius=0):
        if self.boss_spawn_points:
            return [cell for cell in self.boss_spawn_points if self.is_clear_for_radius(cell, radius)]
        cache_key = int(radius)
        if cache_key not in self._boss_spawn_cache:
            cells = []
            for y, row in enumerate(self.rows):
                for x, value in enumerate(row):
                    cell = (x, y)
                    if value != "#" and self.is_clear_for_radius(cell, radius):
                        cells.append(cell)
            self._boss_spawn_cache[cache_key] = cells
        return list(self._boss_spawn_cache[cache_key])

    def _find_player_spawn(self, radius=0):
        center_cell = (self.grid_w // 2, self.grid_h // 2)
        center_pos = Vec2(self.world_w / 2, self.world_h / 2)
        best_open = None
        best_open_score = 1_000_000
        best_fallback = None
        best_fallback_score = 1_000_000

        preferred = set(self.safe_zones)
        for y, row in enumerate(self.rows):
            for x, value in enumerate(row):
                cell = (x, y)
                if value == "#" or not self.is_clear_for_radius(cell, radius):
                    continue

                immediate_walls = 0
                near_walls = 0
                open_count = 0
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        if dx == 0 and dy == 0:
                            continue
                        near = (x + dx, y + dy)
                        blocked = not self.in_bounds(near) or self.is_wall(near)
                        if blocked:
                            near_walls += 1
                            if max(abs(dx), abs(dy)) <= 1:
                                immediate_walls += 1
                        else:
                            open_count += 1

                border = min(x, y, self.grid_w - 1 - x, self.grid_h - 1 - y)
                distance = self.cell_center(cell).distance_to(center_pos) / self.tile_size
                safe_bonus = -35 if cell in preferred else 0
                score = distance + near_walls * 4 + immediate_walls * 18 - open_count * 0.45 + max(0, 4 - border) * 8 + safe_bonus

                if immediate_walls == 0 and open_count >= 18 and score < best_open_score:
                    best_open = cell
                    best_open_score = score
                if score < best_fallback_score:
                    best_fallback = cell
                    best_fallback_score = score

        return best_open or best_fallback or self.nearest_clear_tile(center_cell, radius, max_distance=max(self.grid_w, self.grid_h))

    def nearest_clear_tile(self, origin, radius=0, max_distance=12, prefer_pos=None):
        if self.is_clear_for_radius(origin, radius):
            return origin
        best = None
        best_score = 1_000_000
        ox, oy = origin
        for distance in range(1, max_distance + 1):
            for y in range(oy - distance, oy + distance + 1):
                for x in range(ox - distance, ox + distance + 1):
                    if max(abs(x - ox), abs(y - oy)) != distance:
                        continue
                    cell = (x, y)
                    if not self.is_clear_for_radius(cell, radius):
                        continue
                    score = distance
                    if prefer_pos is not None:
                        score += self.cell_center(cell).distance_to(prefer_pos) / self.tile_size
                    if score < best_score:
                        best = cell
                        best_score = score
            if best is not None:
                return best
        return None

    def in_bounds(self, cell):
        x, y = cell
        return 0 <= x < self.grid_w and 0 <= y < self.grid_h

    def is_blocked(self, tile_x, tile_y):
        cell = (tile_x, tile_y)
        return not self.in_bounds(cell) or self.collision_grid[tile_y][tile_x]

    def is_wall(self, cell):
        x, y = cell
        return self.is_blocked(x, y)

    def is_buildable(self, tile_x, tile_y):
        cell = (tile_x, tile_y)
        if not self.in_bounds(cell):
            return False
        if cell in self.dynamic_obstacles:
            return False
        return self.buildable_grid[tile_y][tile_x]

    def world_to_tile(self, x, y=None):
        if y is None:
            x, y = x
        return (int(x // self.tile_size), int(y // self.tile_size))

    def world_to_cell(self, pos):
        return self.world_to_tile(pos)

    def tile_to_world(self, tile_x, tile_y):
        return Vec2(tile_x * self.tile_size + self.tile_size / 2, tile_y * self.tile_size + self.tile_size / 2)

    def cell_center(self, cell):
        return self.tile_to_world(cell[0], cell[1])

    def collides_circle(self, pos, radius, structures=()):
        pos = Vec2(pos)
        if pos.x - radius < 0 or pos.x + radius >= self.world_w:
            return True
        if pos.y - radius < 0 or pos.y + radius >= self.world_h:
            return True

        left = int((pos.x - radius) // self.tile_size)
        right = int((pos.x + radius) // self.tile_size)
        top = int((pos.y - radius) // self.tile_size)
        bottom = int((pos.y + radius) // self.tile_size)
        for gy in range(top, bottom + 1):
            for gx in range(left, right + 1):
                if self.is_wall((gx, gy)):
                    tile_rect = pygame.Rect(gx * self.tile_size, gy * self.tile_size, self.tile_size, self.tile_size)
                    if _dist_point_rect((pos.x, pos.y), tile_rect) < radius:
                        return True

        actor_rect = pygame.Rect(0, 0, int(radius * 2), int(radius * 2))
        actor_rect.center = (round(pos.x), round(pos.y))
        for structure in structures:
            if getattr(structure, "alive", False) and actor_rect.colliderect(structure.rect):
                return True
        return False

    def is_clear_for_radius(self, cell, radius):
        if not self.in_bounds(cell) or self.is_wall(cell):
            return False
        return not self.collides_circle(self.cell_center(cell), radius, ())

    def draw(self, surface):
        self.render(surface)

    def render(self, surface, camera=None):
        if self.loaded_from_tiled and self.tiled_layers:
            self._render_tiled(surface)
        else:
            self._render_builtin(surface)

    def _render_tiled(self, surface):
        theme = self.theme
        surface.fill(theme.get("bg", (16, 18, 22)), (0, 0, self.world_w, self.world_h))
        for layer_name in TILED_LAYER_ORDER:
            data = self.tiled_layers.get(layer_name)
            if not data:
                continue
            self._render_tile_layer(surface, data, layer_name)

    def _render_tile_layer(self, surface, data, layer_name):
        for y in range(self.grid_h):
            for x in range(self.grid_w):
                index = y * self.grid_w + x
                if index >= len(data):
                    continue
                gid = int(data[index]) & FLIP_MASK
                if gid == 0:
                    continue
                tile = self.tile_surfaces.get(gid) or self._placeholder_tile(gid)
                pos = (x * self.tile_size, y * self.tile_size)
                if layer_name == "obstacles":
                    shadow = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
                    shadow.fill((0, 0, 0, 95))
                    surface.blit(shadow, (pos[0] + 2, pos[1] + 3))
                if layer_name == "lighting":
                    tile = tile.copy()
                    tile.set_alpha(120)
                surface.blit(tile, pos)
                if layer_name == "obstacles":
                    rect = pygame.Rect(pos[0], pos[1], self.tile_size, self.tile_size)
                    pygame.draw.rect(surface, (10, 12, 15), rect, 2)
                    pygame.draw.line(surface, (210, 215, 210), rect.topleft, rect.topright, 1)

    def _render_builtin(self, surface):
        theme = self.theme
        surface.fill(theme["bg"], (0, 0, self.world_w, self.world_h))
        for y, row in enumerate(self.rows):
            for x, value in enumerate(row):
                rect = pygame.Rect(x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)
                if value == "#":
                    pygame.draw.rect(surface, theme["wall_dark"], rect)
                    pygame.draw.rect(surface, theme["wall"], rect.inflate(-4, -4))
                    pygame.draw.line(surface, theme["wall_light"], rect.topleft, rect.topright, 2)
                    pygame.draw.line(surface, theme["wall_dark"], rect.bottomleft, rect.bottomright, 2)
                    self._draw_wall_detail(surface, rect, x, y)
                else:
                    color = theme["floor_a"] if (x + y) % 2 == 0 else theme["floor_b"]
                    pygame.draw.rect(surface, color, rect)
                    self._draw_floor_detail(surface, rect, x, y)
                    pygame.draw.rect(surface, theme["grid"], rect, 1)

    def _draw_wall_detail(self, surface, rect, x, y):
        theme = self.theme
        n = _tile_noise(x, y, 17)
        inner = rect.inflate(-6, -6)
        if self.map_id == "warehouse":
            pygame.draw.line(surface, theme["wall_dark"], (inner.left, inner.centery), (inner.right, inner.centery), 1)
            if n % 3 == 0:
                pygame.draw.line(surface, theme["prop_b"], (inner.centerx, inner.top), (inner.centerx, inner.bottom), 2)
            if n % 11 == 0:
                pygame.draw.rect(surface, theme["accent"], (inner.left + 4, inner.top + 5, inner.w - 8, 3))
        elif self.map_id == "crossfire":
            pygame.draw.rect(surface, theme["prop_b"], inner, 1)
            if n % 4 == 0:
                pygame.draw.line(surface, theme["accent"], (inner.left + 3, inner.bottom - 5), (inner.right - 3, inner.top + 5), 2)
            if n % 7 == 0:
                pygame.draw.rect(surface, theme["prop_a"], (inner.left + 5, inner.top + 7, 7, 4))
        else:
            pygame.draw.rect(surface, theme["wall_light"], inner, 1)
            if n % 3 == 0:
                pygame.draw.circle(surface, theme["prop_a"], (inner.left + 7, inner.top + 8), 3)
                pygame.draw.circle(surface, theme["prop_c"], (inner.right - 6, inner.bottom - 7), 2)
            if n % 9 == 0:
                pygame.draw.line(surface, theme["prop_a"], (inner.left + 3, inner.top + 3), (inner.right - 2, inner.bottom - 4), 2)

    def _draw_floor_detail(self, surface, rect, x, y):
        theme = self.theme
        n = _tile_noise(x, y, 31)
        if self.map_id == "warehouse":
            if n % 8 == 0:
                pygame.draw.rect(surface, theme["prop_b"], (rect.x + 7, rect.y + 7, 18, 2))
                pygame.draw.rect(surface, theme["prop_b"], (rect.x + 7, rect.y + 21, 18, 2))
            if n % 23 == 0:
                pygame.draw.rect(surface, theme["prop_a"], (rect.x + 9, rect.y + 9, 14, 14))
                pygame.draw.rect(surface, (78, 50, 30), (rect.x + 12, rect.y + 9, 2, 14))
        elif self.map_id == "crossfire":
            if n % 6 == 0:
                pygame.draw.line(surface, theme["prop_b"], (rect.x + 6, rect.y + 25), (rect.x + 25, rect.y + 8), 1)
            if n % 17 == 0:
                pygame.draw.circle(surface, theme["prop_c"], rect.center, 5)
                pygame.draw.circle(surface, theme["floor_b"], rect.center, 3)
            if n % 29 == 0:
                pygame.draw.rect(surface, theme["prop_a"], (rect.x + 5, rect.y + 14, 22, 4))
        else:
            if n % 5 == 0:
                pygame.draw.circle(surface, theme["prop_a"], (rect.x + 8, rect.y + 9), 2)
                pygame.draw.circle(surface, theme["prop_a"], (rect.x + 23, rect.y + 21), 2)
            if n % 13 == 0:
                pygame.draw.line(surface, theme["prop_b"], (rect.x + 5, rect.y + 7), (rect.x + 27, rect.y + 24), 1)
            if n % 31 == 0:
                pygame.draw.rect(surface, theme["prop_c"], (rect.x + 12, rect.y + 10, 8, 4))
