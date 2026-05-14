import argparse
import heapq
import math
import os
import random
import sys
from dataclasses import dataclass


if "--smoke" in sys.argv:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

try:
    import pygame
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing dependency: pygame-ce\n"
        "Install it with: py -m pip install -r requirements.txt"
    ) from exc


Vec2 = pygame.math.Vector2

TILE = 32
MAP_ROWS = [
    "############################",
    "#..........................#",
    "#..........................#",
    "#..###..............###....#",
    "#..........................#",
    "#.....##..........##.......#",
    "#...........##.............#",
    "#..##................##....#",
    "#..........................#",
    "#......###....###..........#",
    "#..........................#",
    "#..........##....##........#",
    "#..........................#",
    "#....##................##..#",
    "#.............##...........#",
    "#.......##........##.......#",
    "#..........................#",
    "#..###..............###....#",
    "#..........................#",
    "#..........................#",
    "#..........................#",
    "############################",
]

GRID_W = len(MAP_ROWS[0])
GRID_H = len(MAP_ROWS)
WORLD_W = GRID_W * TILE
WORLD_H = GRID_H * TILE
DESIGN_W = 1920
DESIGN_H = 1080
BOTTOM_UI_H = 156
TOP_UI_H = 146
FPS = 60
WAVE_BREAK_SECONDS = 30
WEAPON_MAX_LEVEL = 18
PLAYER_MAX_LEVEL = 18
BILE_BOOST_MULTIPLIER = 2.35
BILE_BOOST_DURATION = 5.5

assert all(len(row) == GRID_W for row in MAP_ROWS), "Every map row must have the same width."


COLORS = {
    "bg": (18, 18, 22),
    "floor_a": (42, 43, 41),
    "floor_b": (36, 37, 36),
    "grid": (52, 54, 52),
    "wall_dark": (36, 31, 38),
    "wall": (82, 78, 88),
    "wall_light": (126, 120, 132),
    "hud": (20, 22, 27),
    "hud_line": (70, 75, 86),
    "text": (230, 234, 226),
    "muted": (149, 157, 154),
    "gold": (245, 196, 66),
    "red": (225, 73, 66),
    "green": (96, 205, 119),
    "blue": (93, 156, 236),
    "cyan": (89, 215, 205),
    "orange": (246, 144, 66),
}

TEXT = {
    "en": {
        "title": "PIXEL ZOMBIE SIEGE",
        "start": "START",
        "options": "OPTIONS",
        "exit": "EXIT",
        "back": "BACK",
        "begin_run": "BEGIN RUN",
        "setup_title": "MISSION SETUP",
        "resume": "RESUME",
        "main_menu": "MAIN MENU",
        "paused": "PAUSED",
        "music": "Music",
        "sfx": "SFX",
        "language": "Language",
        "auto_fire": "Auto Fire",
        "dev_mode": "Developer Mode",
        "infinite": "INF",
        "difficulty": "Difficulty",
        "character": "Character",
        "structures": "Structures",
        "on": "ON",
        "off": "OFF",
        "wave": "Wave",
        "gold": "Gold",
        "kills": "Kills",
        "score": "Score",
        "enemies": "Enemies",
        "next_wave": "Next wave",
        "pause": "Pause",
        "upgrade": "Upgrade",
        "turret": "Turret",
        "fence": "Fence",
        "repair": "Repair",
        "start_hint": "Press SPACE to start the next wave",
        "skip_hint": "SPACE skips the countdown",
        "auto_hint": "Auto-fire targets the nearest zombie in range.",
    },
    "vi": {
        "title": "PIXEL ZOMBIE SIEGE",
        "start": "BAT DAU",
        "options": "TUY CHON",
        "exit": "THOAT",
        "back": "QUAY LAI",
        "begin_run": "VAO TRAN",
        "setup_title": "CHUAN BI",
        "resume": "TIEP TUC",
        "main_menu": "MENU CHINH",
        "paused": "TAM DUNG",
        "music": "Nhac",
        "sfx": "Hieu ung",
        "language": "Ngon ngu",
        "auto_fire": "Tu dong ban",
        "dev_mode": "Che do nha phat trien",
        "infinite": "VO HAN",
        "difficulty": "Do kho",
        "character": "Nhan vat",
        "structures": "Cong trinh",
        "on": "BAT",
        "off": "TAT",
        "wave": "Dot",
        "gold": "Vang",
        "kills": "Ha guc",
        "score": "Diem",
        "enemies": "Quai",
        "next_wave": "Dot tiep",
        "pause": "Dung",
        "upgrade": "Nang cap",
        "turret": "Tru sung",
        "fence": "Hang rao",
        "repair": "Sua",
        "start_hint": "Nhan SPACE de bat dau dot tiep theo",
        "skip_hint": "SPACE bo qua dem nguoc",
        "auto_hint": "Tu dong ban se ngam zombie gan nhat trong tam.",
    },
}

DIFFICULTIES = {
    "easy": {
        "label": "Easy",
        "hp": 0.82,
        "damage": 0.78,
        "speed": 0.92,
        "count": 0.82,
        "reward": 1.15,
        "player_damage": 1.05,
    },
    "normal": {
        "label": "Normal",
        "hp": 1.0,
        "damage": 1.0,
        "speed": 1.0,
        "count": 1.0,
        "reward": 1.0,
        "player_damage": 1.0,
    },
    "hard": {
        "label": "Hard",
        "hp": 1.35,
        "damage": 1.35,
        "speed": 1.15,
        "count": 1.25,
        "reward": 0.95,
        "player_damage": 0.94,
    },
    "nightmare": {
        "label": "Nightmare",
        "hp": 1.78,
        "damage": 1.72,
        "speed": 1.32,
        "count": 1.55,
        "reward": 0.85,
        "player_damage": 0.86,
    },
}

STRUCTURE_DIFFICULTY_BALANCE = {
    "easy": {
        "hp": 0.88,
        "turret_damage": 0.9,
        "turret_range": 0.94,
        "turret_cooldown": 1.08,
        "cost": 0.82,
        "repair_amount": 0.9,
        "repair_cost": 0.82,
    },
    "normal": {
        "hp": 1.0,
        "turret_damage": 1.0,
        "turret_range": 1.0,
        "turret_cooldown": 1.0,
        "cost": 1.0,
        "repair_amount": 1.0,
        "repair_cost": 1.0,
    },
    "hard": {
        "hp": 1.24,
        "turret_damage": 1.15,
        "turret_range": 1.04,
        "turret_cooldown": 0.93,
        "cost": 1.07,
        "repair_amount": 1.18,
        "repair_cost": 1.05,
    },
    "nightmare": {
        "hp": 1.55,
        "turret_damage": 1.32,
        "turret_range": 1.08,
        "turret_cooldown": 0.86,
        "cost": 1.14,
        "repair_amount": 1.38,
        "repair_cost": 1.1,
    },
}

CHARACTERS = {
    "soldier": {
        "label": "Soldier",
        "hp": 130,
        "speed": 160,
        "damage_bonus": 0.0,
        "fire_rate_bonus": 0.0,
        "gold_bonus": 0.0,
        "armor": 0,
        "pickup_radius": 105,
        "build_discount": 0.0,
    },
    "scout": {
        "label": "Scout",
        "hp": 105,
        "speed": 188,
        "damage_bonus": -0.04,
        "fire_rate_bonus": 0.08,
        "gold_bonus": 0.0,
        "armor": 0,
        "pickup_radius": 130,
        "build_discount": 0.0,
    },
    "engineer": {
        "label": "Engineer",
        "hp": 118,
        "speed": 150,
        "damage_bonus": -0.02,
        "fire_rate_bonus": 0.0,
        "gold_bonus": 0.08,
        "armor": 1,
        "pickup_radius": 112,
        "build_discount": 0.18,
    },
    "tank": {
        "label": "Tank",
        "hp": 165,
        "speed": 134,
        "damage_bonus": 0.04,
        "fire_rate_bonus": -0.08,
        "gold_bonus": 0.0,
        "armor": 3,
        "pickup_radius": 95,
        "build_discount": 0.0,
    },
}


ZOMBIE_TYPES = {
    "walker": {
        "label": "Walker",
        "hp": 50,
        "speed": 42,
        "damage": 8,
        "attack_rate": 0.85,
        "reward": 8,
        "xp": 12,
        "radius": 12,
        "color": (91, 166, 82),
        "accent": (43, 101, 47),
        "special": None,
    },
    "runner": {
        "label": "Runner",
        "hp": 38,
        "speed": 92,
        "damage": 8,
        "attack_rate": 0.58,
        "reward": 12,
        "xp": 17,
        "radius": 11,
        "color": (173, 95, 76),
        "accent": (113, 48, 43),
        "special": None,
    },
    "spitter": {
        "label": "Spitter",
        "hp": 70,
        "speed": 50,
        "damage": 9,
        "attack_rate": 0.86,
        "reward": 18,
        "xp": 24,
        "radius": 12,
        "color": (96, 176, 122),
        "accent": (56, 215, 90),
        "special": "acid",
    },
    "boomer": {
        "label": "Boomer",
        "hp": 62,
        "speed": 78,
        "damage": 9,
        "attack_rate": 0.78,
        "reward": 16,
        "xp": 22,
        "radius": 14,
        "color": (177, 151, 67),
        "accent": (229, 190, 72),
        "special": "explode",
    },
    "stalker": {
        "label": "Stalker",
        "hp": 48,
        "speed": 80,
        "damage": 13,
        "attack_rate": 0.68,
        "reward": 22,
        "xp": 30,
        "radius": 11,
        "color": (116, 114, 162),
        "accent": (186, 175, 236),
        "special": "lunge",
    },
    "titan": {
        "label": "Titan",
        "hp": 430,
        "speed": 38,
        "damage": 28,
        "attack_rate": 1.05,
        "reward": 95,
        "xp": 130,
        "radius": 24,
        "color": (111, 84, 97),
        "accent": (214, 78, 78),
        "special": "stomp",
    },
}

WEAPON_TIERS = [
    {
        "min_level": 1,
        "name": "Pistol",
        "damage": 18,
        "cooldown": 0.32,
        "bullet_speed": 560,
        "range": 330,
        "spread": 0.035,
        "shots": 1,
        "pierce": 0,
        "explosion_radius": 0,
        "style": "single",
    },
    {
        "min_level": 3,
        "name": "Dual Pistols",
        "damage": 16,
        "cooldown": 0.20,
        "bullet_speed": 585,
        "range": 330,
        "spread": 0.085,
        "shots": 2,
        "pierce": 0,
        "explosion_radius": 0,
        "style": "paired",
    },
    {
        "min_level": 5,
        "name": "SMG",
        "damage": 13,
        "cooldown": 0.085,
        "bullet_speed": 610,
        "range": 300,
        "spread": 0.11,
        "shots": 1,
        "pierce": 0,
        "explosion_radius": 0,
        "style": "single",
    },
    {
        "min_level": 7,
        "name": "Shotgun",
        "damage": 15,
        "cooldown": 0.46,
        "bullet_speed": 535,
        "range": 255,
        "spread": 0.34,
        "shots": 6,
        "pierce": 1,
        "explosion_radius": 0,
        "style": "fan",
    },
    {
        "min_level": 10,
        "name": "Assault Rifle",
        "damage": 28,
        "cooldown": 0.14,
        "bullet_speed": 690,
        "range": 430,
        "spread": 0.045,
        "shots": 1,
        "pierce": 1,
        "explosion_radius": 0,
        "style": "single",
    },
    {
        "min_level": 13,
        "name": "Combat Shotgun",
        "damage": 22,
        "cooldown": 0.36,
        "bullet_speed": 610,
        "range": 300,
        "spread": 0.28,
        "shots": 7,
        "pierce": 2,
        "explosion_radius": 0,
        "style": "fan",
    },
    {
        "min_level": 16,
        "name": "Laser Rifle",
        "damage": 50,
        "cooldown": 0.19,
        "bullet_speed": 790,
        "range": 520,
        "spread": 0.012,
        "shots": 1,
        "pierce": 5,
        "explosion_radius": 0,
        "style": "laser",
    },
]

STRUCTURE_TYPES = {
    "turret": {
        "label": "Turret",
        "cost": 85,
        "hp": 145,
        "range": 305,
        "damage": 20,
        "cooldown": 0.38,
    },
    "fence": {
        "label": "Fence",
        "cost": 45,
        "hp": 260,
        "range": 0,
        "damage": 0,
        "cooldown": 0,
    },
}


def clamp(value, low, high):
    return max(low, min(high, value))


def dist_point_rect(point, rect):
    px, py = point
    cx = clamp(px, rect.left, rect.right)
    cy = clamp(py, rect.top, rect.bottom)
    return math.hypot(px - cx, py - cy)


def make_pixel_sprite(pattern, palette, scale=2):
    width = len(pattern[0]) * scale
    height = len(pattern) * scale
    sprite = pygame.Surface((width, height), pygame.SRCALPHA)
    for y, row in enumerate(pattern):
        for x, key in enumerate(row):
            if key == ".":
                continue
            pygame.draw.rect(sprite, palette[key], (x * scale, y * scale, scale, scale))
    return sprite


def build_sprites():
    zombie_pattern = [
        "..hhhh..",
        ".hbbbbh.",
        "hbeeeebh",
        "hbebebbh",
        ".bbbbbb.",
        ".bbaabb.",
        ".baaabb.",
        "..b..b..",
        ".bb..bb.",
    ]
    player_pattern = [
        "...hhhh...",
        "..hFFFFh..",
        "..hFEEFh..",
        "...FFFF...",
        "..bbbbbb..",
        ".bbBbbBbb.",
        ".bbBbbBbb.",
        "..bBbbB...",
        "..bb..bb..",
        ".bbb..bbb.",
    ]
    player_palettes = {
        "soldier": ((62, 132, 177), (35, 79, 112)),
        "scout": ((83, 174, 119), (38, 96, 70)),
        "engineer": ((218, 151, 64), (132, 82, 36)),
        "tank": ((125, 116, 151), (74, 66, 93)),
    }
    sprites = {}
    for character_id, (body, trim) in player_palettes.items():
        sprites[f"player_{character_id}"] = make_pixel_sprite(
            player_pattern,
            {
                "h": (66, 45, 38),
                "F": (225, 170, 124),
                "E": (36, 32, 30),
                "b": body,
                "B": trim,
            },
            3,
        )
    sprites["player"] = sprites["player_soldier"]
    for key, cfg in ZOMBIE_TYPES.items():
        palette = {
            "h": (46, 41, 45),
            "b": cfg["color"],
            "a": cfg["accent"],
            "e": (240, 231, 126),
        }
        scale = 5 if key == "titan" else 3
        sprites[key] = make_pixel_sprite(zombie_pattern, palette, scale)
    return sprites


class TileMap:
    def __init__(self, rows):
        self.rows = rows

    def in_bounds(self, cell):
        x, y = cell
        return 0 <= x < GRID_W and 0 <= y < GRID_H

    def is_wall(self, cell):
        x, y = cell
        if not self.in_bounds(cell):
            return True
        return self.rows[y][x] == "#"

    def world_to_cell(self, pos):
        return (int(pos[0] // TILE), int(pos[1] // TILE))

    def cell_center(self, cell):
        x, y = cell
        return Vec2(x * TILE + TILE / 2, y * TILE + TILE / 2)

    def collides_circle(self, pos, radius, structures=()):
        if pos.x - radius < 0 or pos.x + radius >= WORLD_W:
            return True
        if pos.y - radius < 0 or pos.y + radius >= WORLD_H:
            return True

        left = int((pos.x - radius) // TILE)
        right = int((pos.x + radius) // TILE)
        top = int((pos.y - radius) // TILE)
        bottom = int((pos.y + radius) // TILE)
        for gy in range(top, bottom + 1):
            for gx in range(left, right + 1):
                if self.is_wall((gx, gy)):
                    tile_rect = pygame.Rect(gx * TILE, gy * TILE, TILE, TILE)
                    if dist_point_rect((pos.x, pos.y), tile_rect) < radius:
                        return True

        actor_rect = pygame.Rect(0, 0, int(radius * 2), int(radius * 2))
        actor_rect.center = (round(pos.x), round(pos.y))
        for structure in structures:
            if structure.alive and actor_rect.colliderect(structure.rect):
                return True
        return False

    def is_clear_for_radius(self, cell, radius):
        if not self.in_bounds(cell) or self.is_wall(cell):
            return False
        return not self.collides_circle(self.cell_center(cell), radius, ())

    def draw(self, surface):
        surface.fill(COLORS["bg"], (0, 0, WORLD_W, WORLD_H))
        for y, row in enumerate(self.rows):
            for x, value in enumerate(row):
                rect = pygame.Rect(x * TILE, y * TILE, TILE, TILE)
                if value == "#":
                    pygame.draw.rect(surface, COLORS["wall_dark"], rect)
                    pygame.draw.rect(surface, COLORS["wall"], rect.inflate(-4, -4))
                    pygame.draw.line(surface, COLORS["wall_light"], rect.topleft, rect.topright, 2)
                    pygame.draw.line(surface, (30, 27, 32), rect.bottomleft, rect.bottomright, 2)
                else:
                    color = COLORS["floor_a"] if (x + y) % 2 == 0 else COLORS["floor_b"]
                    pygame.draw.rect(surface, color, rect)
                    pygame.draw.rect(surface, COLORS["grid"], rect, 1)


def astar(tile_map, start, goal, blocked):
    if tile_map.is_wall(goal):
        return []

    blocked = set(blocked)
    blocked.discard(start)
    blocked.discard(goal)
    neighbors = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    open_heap = []
    heapq.heappush(open_heap, (0, start))
    came_from = {}
    g_score = {start: 0}
    closed = set()

    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    while open_heap:
        _, current = heapq.heappop(open_heap)
        if current == goal:
            path = []
            while current != start:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path

        if current in closed:
            continue
        closed.add(current)

        for dx, dy in neighbors:
            nxt = (current[0] + dx, current[1] + dy)
            if not tile_map.in_bounds(nxt) or tile_map.is_wall(nxt) or nxt in blocked:
                continue
            tentative = g_score[current] + 1
            if tentative < g_score.get(nxt, 1_000_000):
                came_from[nxt] = current
                g_score[nxt] = tentative
                f_score = tentative + heuristic(nxt, goal)
                heapq.heappush(open_heap, (f_score, nxt))
    return []


def astar_clearance(tile_map, start, goal, radius, blocked=()):
    blocked = set(blocked)
    blocked.discard(start)
    blocked.discard(goal)

    def passable(cell):
        return (
            tile_map.in_bounds(cell)
            and cell not in blocked
            and tile_map.is_clear_for_radius(cell, radius)
        )

    if not passable(start) or not passable(goal):
        return []

    neighbors = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    open_heap = [(0, start)]
    came_from = {}
    g_score = {start: 0}
    closed = set()

    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    while open_heap:
        _, current = heapq.heappop(open_heap)
        if current == goal:
            path = []
            while current != start:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path
        if current in closed:
            continue
        closed.add(current)

        for dx, dy in neighbors:
            nxt = (current[0] + dx, current[1] + dy)
            if not passable(nxt):
                continue
            tentative = g_score[current] + 1
            if tentative < g_score.get(nxt, 1_000_000):
                came_from[nxt] = current
                g_score[nxt] = tentative
                heapq.heappush(open_heap, (tentative + heuristic(nxt, goal), nxt))
    return []


def nearest_clear_cell(tile_map, origin, radius, max_distance=12, prefer_pos=None):
    if tile_map.is_clear_for_radius(origin, radius):
        return origin

    best = None
    best_score = 1_000_000
    ox, oy = origin
    for distance in range(1, max_distance + 1):
        for y in range(oy - distance, oy + distance + 1):
            for x in range(ox - distance, ox + distance + 1):
                cell = (x, y)
                if abs(x - ox) != distance and abs(y - oy) != distance:
                    continue
                if not tile_map.is_clear_for_radius(cell, radius):
                    continue
                score = abs(x - ox) + abs(y - oy)
                if prefer_pos is not None:
                    score += tile_map.cell_center(cell).distance_to(prefer_pos) / TILE
                if score < best_score:
                    best = cell
                    best_score = score
        if best is not None:
            return best
    return None


def has_wall_line(tile_map, a, b):
    start = Vec2(a)
    end = Vec2(b)
    delta = end - start
    distance = delta.length()
    if distance <= 1:
        return True
    steps = max(1, int(distance // 12))
    for i in range(1, steps + 1):
        pos = start.lerp(end, i / steps)
        if tile_map.is_wall(tile_map.world_to_cell(pos)):
            return False
    return True


@dataclass
class Weapon:
    level: int = 1

    @property
    def upgrade_cost(self):
        if self.is_maxed:
            return 0
        return 45 + self.level * 36 + (self.level // 3) * 18

    @property
    def is_maxed(self):
        return self.level >= WEAPON_MAX_LEVEL

    @property
    def tier(self):
        active = WEAPON_TIERS[0]
        for tier in WEAPON_TIERS:
            if self.level >= tier["min_level"]:
                active = tier
            else:
                break
        return active

    @property
    def tier_name(self):
        return self.tier["name"]

    @property
    def tier_rank(self):
        return self.level - self.tier["min_level"]

    @property
    def damage(self):
        tier = self.tier
        return tier["damage"] + self.tier_rank * 4 + self.level // 4

    @property
    def cooldown(self):
        tier = self.tier
        return max(0.055, tier["cooldown"] * (0.97 ** self.tier_rank))

    @property
    def bullet_speed(self):
        return self.tier["bullet_speed"] + self.tier_rank * 18

    @property
    def bullet_range(self):
        return self.tier["range"] + self.tier_rank * 18

    @property
    def spread(self):
        tier = self.tier
        if tier["style"] == "fan":
            return max(0.18, tier["spread"] - self.tier_rank * 0.01)
        return max(0.006, tier["spread"] - self.tier_rank * 0.004)

    @property
    def bullet_count(self):
        tier = self.tier
        return tier["shots"] + (1 if tier["style"] == "fan" and self.tier_rank >= 3 else 0)

    @property
    def pierce(self):
        return self.tier["pierce"] + self.tier_rank // 4

    @property
    def explosion_radius(self):
        radius = self.tier["explosion_radius"]
        if radius <= 0:
            return 0
        return radius + self.tier_rank * 2

    @property
    def style(self):
        return self.tier["style"]

    def upgrade(self):
        if self.is_maxed:
            return False
        self.level += 1
        return True


class Player:
    def __init__(self, pos, character_id="soldier"):
        character = CHARACTERS.get(character_id, CHARACTERS["soldier"])
        self.character_id = character_id if character_id in CHARACTERS else "soldier"
        self.pos = Vec2(pos)
        self.radius = 13
        self.speed = character["speed"]
        self.max_hp = character["hp"]
        self.hp = self.max_hp
        self.gold = 80
        self.score = 0
        self.weapon = Weapon()
        self.fire_timer = 0
        self.invuln = 0
        self.kills = 0
        self.level = 1
        self.xp = 0
        self.next_xp = 110
        self.damage_bonus = character["damage_bonus"]
        self.fire_rate_bonus = character["fire_rate_bonus"]
        self.gold_bonus = character["gold_bonus"]
        self.pickup_radius = character["pickup_radius"]
        self.armor = character["armor"]
        self.build_discount = character["build_discount"]
        self.regen_rate = 0.0
        self.level_notes = [character["label"]]

    def update(self, dt, game):
        keys = pygame.key.get_pressed()
        move = Vec2(0, 0)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            move.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            move.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            move.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            move.x += 1
        if move.length_squared() > 0:
            move = move.normalize() * self.speed * dt
            self.try_move(move, game)

        self.fire_timer = max(0, self.fire_timer - dt)
        self.invuln = max(0, self.invuln - dt)
        if self.regen_rate > 0 and self.hp < self.max_hp:
            self.hp = min(self.max_hp, self.hp + self.regen_rate * dt)
        if game.build_mode is not None:
            return
        if game.auto_fire:
            target = game.find_auto_fire_target()
            if target is not None:
                self.shoot_at(target, game)
                return
        mouse_pressed = pygame.mouse.get_pressed(num_buttons=3)[0]
        mouse_world = game.mouse_world()
        if mouse_pressed and mouse_world is not None and not game.pointer_over_ui():
            self.shoot_at(mouse_world, game)

    def try_move(self, delta, game):
        blockers = [s for s in game.structures if s.alive]
        new_pos = self.pos + delta
        if not game.tile_map.collides_circle(new_pos, self.radius, blockers):
            self.pos = new_pos
            return
        x_pos = Vec2(self.pos.x + delta.x, self.pos.y)
        if not game.tile_map.collides_circle(x_pos, self.radius, blockers):
            self.pos = x_pos
        y_pos = Vec2(self.pos.x, self.pos.y + delta.y)
        if not game.tile_map.collides_circle(y_pos, self.radius, blockers):
            self.pos = y_pos

    def shoot_at(self, world_pos, game):
        if self.fire_timer > 0:
            return
        mx, my = world_pos
        if not (0 <= mx < WORLD_W and 0 <= my < WORLD_H):
            return
        direction = Vec2(mx, my) - self.pos
        if direction.length_squared() <= 1:
            return
        base_angle = math.atan2(direction.y, direction.x)
        damage = int(self.weapon.damage * (1 + self.damage_bonus) * game.difficulty_cfg()["player_damage"])
        if self.weapon.style == "laser":
            angle = base_angle + random.uniform(-self.weapon.spread, self.weapon.spread)
            laser_dir = Vec2(math.cos(angle), math.sin(angle))
            game.fire_laser(self.pos + laser_dir * (self.radius + 8), laser_dir, damage, self.weapon.bullet_range, self.weapon.pierce)
            self.fire_timer = self.weapon.cooldown / (1 + self.fire_rate_bonus)
            return

        shots = self.weapon.bullet_count
        if self.weapon.style == "fan" and shots > 1:
            offsets = [
                -self.weapon.spread / 2 + self.weapon.spread * i / max(1, shots - 1)
                for i in range(shots)
            ]
        elif self.weapon.style == "paired":
            offsets = [-self.weapon.spread * 0.45, self.weapon.spread * 0.45]
        else:
            offsets = [random.uniform(-self.weapon.spread, self.weapon.spread) for _ in range(shots)]

        for offset in offsets:
            angle = base_angle + offset + random.uniform(-self.weapon.spread * 0.18, self.weapon.spread * 0.18)
            vel = Vec2(math.cos(angle), math.sin(angle)) * self.weapon.bullet_speed
            spawn = self.pos + vel.normalize() * (self.radius + 8)
            game.bullets.append(
                Bullet(
                    spawn,
                    vel,
                    damage,
                    self.weapon.bullet_range,
                    "player",
                    pierce=self.weapon.pierce,
                    explosion_radius=self.weapon.explosion_radius,
                )
            )
            game.add_muzzle_particle(spawn, vel)
        game.play_sound("shoot", 0.34, cooldown=0.045)
        self.fire_timer = self.weapon.cooldown / (1 + self.fire_rate_bonus)

    def take_damage(self, amount, game):
        if self.invuln > 0:
            return
        reduction = min(0.38, self.armor * 0.025)
        amount = max(1, int(round(amount * (1 - reduction))))
        self.hp -= amount
        self.invuln = 0.18
        game.play_sound("hurt", 0.55, cooldown=0.22)
        game.floating_texts.append(FloatingText(self.pos + Vec2(0, -28), f"-{amount}", COLORS["red"]))
        if self.hp <= 0:
            self.hp = 0
            game.game_over = True

    def add_xp(self, amount, game):
        if self.level >= PLAYER_MAX_LEVEL:
            self.xp = min(self.next_xp, self.xp + amount)
            return
        self.xp += amount
        while self.xp >= self.next_xp and self.level < PLAYER_MAX_LEVEL:
            self.xp -= self.next_xp
            self.level += 1
            self.next_xp = int(self.next_xp * 1.25 + 30)
            perks = self.apply_level_perks()
            game.floating_texts.append(
                FloatingText(self.pos + Vec2(0, -44), f"LEVEL {self.level}", COLORS["cyan"], life=1.4)
            )
            game.message = f"Level {self.level}: {', '.join(perks)}"
            game.message_timer = 2.6
        if self.level >= PLAYER_MAX_LEVEL:
            self.xp = min(self.xp, self.next_xp)

    def apply_level_perks(self):
        perks = []
        self.max_hp += 16
        self.hp = min(self.max_hp, self.hp + 42)
        self.speed += 2.5
        perks.append("+HP")

        if self.level % 2 == 0:
            self.damage_bonus += 0.06
            perks.append("+6% damage")
        if self.level % 3 == 0:
            self.fire_rate_bonus += 0.05
            perks.append("+5% fire rate")
        if self.level % 4 == 0:
            self.pickup_radius += 16
            self.gold_bonus += 0.05
            perks.append("+magnet/gold")
        if self.level % 5 == 0:
            self.armor += 2
            self.regen_rate += 0.35
            perks.append("+armor/regen")
        if len(perks) == 1:
            self.armor += 1
            self.pickup_radius += 8
            perks.append("+armor/magnet")

        self.level_notes = perks[-3:]
        return perks

    def draw(self, surface, sprites, aim_pos=None):
        sprite = sprites.get(f"player_{self.character_id}", sprites["player"])
        rect = sprite.get_rect(center=(round(self.pos.x), round(self.pos.y)))
        if self.invuln > 0 and int(self.invuln * 40) % 2 == 0:
            return
        surface.blit(sprite, rect)
        if aim_pos is not None:
            direction = Vec2(aim_pos) - self.pos
            if direction.length_squared() > 4:
                direction = direction.normalize()
                start = self.pos + direction * 10
                end = self.pos + direction * 23
                pygame.draw.line(surface, (35, 34, 35), start, end, 6)
                pygame.draw.line(surface, (190, 184, 164), start, end, 3)


class Bullet:
    def __init__(self, pos, vel, damage, max_range, owner, pierce=0, explosion_radius=0):
        self.pos = Vec2(pos)
        self.vel = Vec2(vel)
        self.damage = damage
        self.remaining = max_range
        self.owner = owner
        self.radius = 4 if owner == "player" else 3
        self.alive = True
        self.pierce = pierce
        self.explosion_radius = explosion_radius
        self.hit_zombies = set()

    def update(self, dt, game):
        if not self.alive:
            return
        step = self.vel * dt
        self.pos += step
        self.remaining -= step.length()
        if self.remaining <= 0 or not (0 <= self.pos.x < WORLD_W and 0 <= self.pos.y < WORLD_H):
            self.alive = False
            return
        if game.tile_map.is_wall(game.tile_map.world_to_cell(self.pos)):
            self.alive = False
            game.spawn_spark(self.pos, (140, 130, 116))
            return
        for zombie in game.zombies:
            if (
                zombie.alive
                and id(zombie) not in self.hit_zombies
                and self.pos.distance_squared_to(zombie.pos) <= (self.radius + zombie.radius) ** 2
            ):
                self.hit_zombies.add(id(zombie))
                zombie.take_damage(self.damage, game)
                if self.explosion_radius > 0:
                    game.damage_zombies_in_radius(self.pos, self.explosion_radius, max(5, self.damage // 2), exclude=zombie)
                    game.create_explosion(self.pos, self.explosion_radius, max(1, self.damage // 3), enemy_owned=False, visual_only=True)
                game.spawn_spark(self.pos, COLORS["gold"])
                if self.pierce <= 0:
                    self.alive = False
                    return
                self.pierce -= 1
                self.damage = max(1, int(self.damage * 0.72))
                return

    def draw(self, surface):
        color = COLORS["gold"] if self.owner == "player" else COLORS["cyan"]
        pygame.draw.circle(surface, color, (round(self.pos.x), round(self.pos.y)), self.radius)
        pygame.draw.circle(surface, (255, 248, 190), (round(self.pos.x), round(self.pos.y)), max(1, self.radius - 2))


class AcidProjectile:
    def __init__(self, pos, target, damage, kind="acid", pool_radius=62):
        self.pos = Vec2(pos)
        direction = Vec2(target) - self.pos
        if direction.length_squared() == 0:
            direction = Vec2(1, 0)
        self.vel = direction.normalize() * (255 if kind == "bile" else 230)
        self.damage = damage
        self.life = 2.1 if kind != "poison" else 2.5
        self.radius = 7 if kind == "bile" else 6
        self.kind = kind
        self.pool_radius = pool_radius
        self.alive = True

    def burst(self, game):
        self.alive = False
        if self.kind == "poison":
            game.poison_pools.append(PoisonPool(self.pos, self.pool_radius, self.damage, life=4.8))
            game.spawn_spark(self.pos, (88, 238, 75))
            game.play_sound("poison", 0.45, cooldown=0.25)
        elif self.kind == "bile":
            game.create_bile_splash(self.pos, self.pool_radius)
            game.play_sound("poison", 0.45, cooldown=0.25)
        else:
            game.spawn_spark(self.pos, (105, 224, 91))

    def update(self, dt, game):
        self.pos += self.vel * dt
        self.life -= dt
        if self.life <= 0 or not (0 <= self.pos.x < WORLD_W and 0 <= self.pos.y < WORLD_H):
            self.burst(game)
            return
        if game.tile_map.is_wall(game.tile_map.world_to_cell(self.pos)):
            self.burst(game)
            return
        if self.pos.distance_squared_to(game.player.pos) <= (self.radius + game.player.radius) ** 2:
            if self.kind == "bile":
                game.player.take_damage(max(2, self.damage // 2), game)
                game.apply_bile(self.pos)
                self.alive = False
            elif self.kind == "poison":
                game.player.take_damage(self.damage, game)
                self.burst(game)
            else:
                game.player.take_damage(self.damage, game)
                self.alive = False
                game.spawn_spark(self.pos, (105, 224, 91))
            return
        for structure in game.structures:
            if structure.alive and dist_point_rect((self.pos.x, self.pos.y), structure.rect) < self.radius:
                structure.take_damage(self.damage + (8 if self.kind == "poison" else 4), game)
                self.burst(game)
                return

    def draw(self, surface):
        color = (118, 255, 68) if self.kind == "bile" else (86, 224, 78)
        inner = (220, 255, 110) if self.kind == "bile" else (205, 255, 152)
        pygame.draw.circle(surface, color, (round(self.pos.x), round(self.pos.y)), self.radius)
        pygame.draw.circle(surface, inner, (round(self.pos.x - 2), round(self.pos.y - 2)), 2)


class PoisonPool:
    def __init__(self, pos, radius, damage, life=4.5):
        self.pos = Vec2(pos)
        self.radius = radius
        self.damage = damage
        self.life = life
        self.max_life = life
        self.tick_timer = 0
        self.alive = True

    def update(self, dt, game):
        self.life -= dt
        self.tick_timer -= dt
        if self.life <= 0:
            self.alive = False
            return
        if self.tick_timer <= 0:
            self.tick_timer = 0.35
            if self.pos.distance_to(game.player.pos) <= self.radius + game.player.radius:
                game.player.take_damage(max(2, int(self.damage * 0.65)), game)
            for structure in game.structures:
                if structure.alive and dist_point_rect((self.pos.x, self.pos.y), structure.rect) <= self.radius:
                    structure.take_damage(max(2, int(self.damage * 0.45)), game)

    def draw(self, surface):
        alpha = int(95 * clamp(self.life / self.max_life, 0, 1))
        pool = pygame.Surface((int(self.radius * 2), int(self.radius * 2)), pygame.SRCALPHA)
        pygame.draw.circle(pool, (80, 230, 63, alpha), (int(self.radius), int(self.radius)), int(self.radius))
        pygame.draw.circle(pool, (168, 255, 93, max(25, alpha // 2)), (int(self.radius), int(self.radius)), max(4, int(self.radius * 0.62)), 2)
        surface.blit(pool, (self.pos.x - self.radius, self.pos.y - self.radius))


class LaserBeam:
    def __init__(self, start, end, width=7, life=0.11):
        self.start = Vec2(start)
        self.end = Vec2(end)
        self.width = width
        self.life = life
        self.max_life = life
        self.alive = True

    def update(self, dt):
        self.life -= dt
        if self.life <= 0:
            self.alive = False

    def draw(self, surface):
        alpha = clamp(self.life / self.max_life, 0, 1)
        glow_width = max(3, int(self.width * 2.4 * alpha))
        core_width = max(1, int(self.width * alpha))
        pygame.draw.line(surface, (38, 154, 255), self.start, self.end, glow_width)
        pygame.draw.line(surface, (120, 242, 255), self.start, self.end, core_width)
        pygame.draw.circle(surface, (226, 255, 255), self.end, max(2, core_width))


class Structure:
    def __init__(self, kind, cell, stats=None):
        self.kind = kind
        self.cell = cell
        cfg = STRUCTURE_TYPES[kind]
        self.stats = stats or {
            "hp": cfg["hp"],
            "range": cfg["range"],
            "damage": cfg["damage"],
            "cooldown": cfg["cooldown"],
        }
        self.max_hp = self.stats["hp"]
        self.hp = self.max_hp
        self.fire_timer = random.uniform(0, 0.2)
        self.rect = pygame.Rect(cell[0] * TILE + 4, cell[1] * TILE + 4, TILE - 8, TILE - 8)
        self.alive = True

    def update(self, dt, game):
        if not self.alive or self.kind != "turret":
            return
        self.fire_timer = max(0, self.fire_timer - dt)
        if self.fire_timer > 0:
            return
        target = None
        best_dist = self.stats["range"] ** 2
        center = Vec2(self.rect.center)
        for zombie in game.zombies:
            if not zombie.alive:
                continue
            dist_sq = center.distance_squared_to(zombie.pos)
            if dist_sq < best_dist and has_wall_line(game.tile_map, center, zombie.pos):
                best_dist = dist_sq
                target = zombie
        if target is None:
            return
        direction = target.pos - center
        if direction.length_squared() == 0:
            return
        vel = direction.normalize() * 500
        game.bullets.append(Bullet(center + vel.normalize() * 18, vel, self.stats["damage"], self.stats["range"] + 40, "turret"))
        self.fire_timer = self.stats["cooldown"]

    def take_damage(self, amount, game):
        self.hp -= amount
        game.spawn_spark(Vec2(self.rect.center), (210, 92, 73))
        if self.hp <= 0:
            self.alive = False
            game.floating_texts.append(FloatingText(Vec2(self.rect.center), "BROKEN", COLORS["red"], life=0.9))

    def repair(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def draw(self, surface):
        if self.kind == "turret":
            base = pygame.Rect(self.rect)
            pygame.draw.rect(surface, (55, 65, 76), base)
            pygame.draw.rect(surface, (121, 134, 145), base.inflate(-6, -6))
            center = Vec2(base.center)
            pygame.draw.circle(surface, (45, 49, 55), center, 8)
            pygame.draw.rect(surface, COLORS["cyan"], (center.x - 4, center.y - 15, 8, 18))
        else:
            pygame.draw.rect(surface, (112, 82, 54), self.rect)
            pygame.draw.rect(surface, (165, 120, 72), self.rect.inflate(-5, -5))
            for offset in (6, 16):
                pygame.draw.line(
                    surface,
                    (83, 58, 41),
                    (self.rect.left + 3, self.rect.top + offset),
                    (self.rect.right - 3, self.rect.top + offset),
                    3,
                )

        pct = clamp(self.hp / self.max_hp, 0, 1)
        bar = pygame.Rect(self.rect.left, self.rect.bottom + 3, self.rect.width, 4)
        pygame.draw.rect(surface, (40, 32, 32), bar)
        pygame.draw.rect(surface, COLORS["green"] if pct > 0.45 else COLORS["orange"], (bar.x, bar.y, int(bar.w * pct), bar.h))


class Zombie:
    def __init__(self, kind, pos, wave, difficulty_id="normal"):
        self.kind = kind
        self.cfg = ZOMBIE_TYPES[kind]
        difficulty = DIFFICULTIES.get(difficulty_id, DIFFICULTIES["normal"])
        self.pos = Vec2(pos)
        hp_scale = 1.0 + max(0, wave - 1) * 0.18
        if kind == "titan":
            hp_scale += wave * 0.08
        self.max_hp = int(self.cfg["hp"] * hp_scale * difficulty["hp"])
        self.hp = self.max_hp
        self.radius = self.cfg["radius"]
        self.damage = int(self.cfg["damage"] * (1.0 + max(0, wave - 1) * 0.12) * difficulty["damage"])
        self.speed = self.cfg["speed"] * (1.0 + min(0.95, wave * 0.035)) * difficulty["speed"]
        self.path = []
        self.path_timer = random.uniform(0, 0.35)
        self.attack_timer = random.uniform(0, 0.2)
        self.special_timer = random.uniform(0.6, 1.4)
        self.flash = 0
        self.alive = True
        self.lunge_boost = 0
        self.dash_timer = random.uniform(1.4, 2.4)
        self.dash_time = 0
        self.dash_dir = Vec2(0, 0)
        self.trample_timer = 0
        self.charge_timer = random.uniform(2.3, 3.4)
        self.charge_time = 0
        self.charge_dir = Vec2(0, 0)
        self.charge_hit_player = False
        self.shockwave_timer = random.uniform(3.8, 5.2)
        self.wall_leap_timer = random.uniform(3.0, 4.8)
        self.wall_leap_time = 0
        self.wall_leap_duration = 0.7
        self.wall_leap_start = Vec2(self.pos)
        self.wall_leap_target = Vec2(self.pos)
        self.summon_thresholds = [0.72, 0.48, 0.24] if kind == "titan" else []
        self.last_pos = Vec2(self.pos)
        self.stuck_timer = 0

    def take_damage(self, amount, game):
        self.hp -= amount
        self.flash = 0.08
        game.play_sound("hit", 0.28, cooldown=0.05)
        if self.hp <= 0 and self.alive:
            self.die(game)

    def die(self, game):
        self.alive = False
        reward = int(round((self.cfg["reward"] + random.randint(0, 3 + game.wave)) * game.difficulty_cfg()["reward"]))
        game.drop_gold(self.pos, reward)
        game.player.kills += 1
        game.player.score += reward * 6
        game.player.add_xp(self.cfg["xp"], game)
        game.floating_texts.append(FloatingText(self.pos + Vec2(0, -24), f"+{reward}g", COLORS["gold"]))
        if self.kind == "boomer":
            game.create_explosion(self.pos, 105, self.damage + 22, enemy_owned=True)

    def update(self, dt, game):
        if not self.alive:
            return
        if self.kind == "titan":
            self.update_titan(dt, game)
            return
        self.flash = max(0, self.flash - dt)
        self.attack_timer = max(0, self.attack_timer - dt)
        self.special_timer = max(0, self.special_timer - dt)
        self.lunge_boost = max(0, self.lunge_boost - dt)
        self.dash_timer = max(0, self.dash_timer - dt)
        self.dash_time = max(0, self.dash_time - dt)

        if self.kind == "boomer":
            self.try_boomer_bile(game)
            self.try_boomer_dash(game)
            if self.should_explode(game):
                self.alive = False
                game.create_explosion(self.pos, 110, self.damage + 30, enemy_owned=True)
                return
        elif self.cfg["special"] == "acid":
            self.try_acid(dt, game)
        elif self.cfg["special"] == "lunge":
            self.try_lunge(game)
        elif self.cfg["special"] == "stomp":
            self.try_stomp(game)

        target_structure = self.nearby_structure(game)
        if target_structure is not None and self.attack_timer <= 0:
            target_structure.take_damage(self.damage, game)
            self.attack_timer = self.cfg["attack_rate"]
            return

        player_dist = self.pos.distance_to(game.player.pos)
        if player_dist <= self.radius + game.player.radius + 4:
            if self.attack_timer <= 0:
                game.player.take_damage(self.damage, game)
                self.attack_timer = self.cfg["attack_rate"]
            return

        self.follow_path(dt, game)

    def update_titan(self, dt, game):
        self.flash = max(0, self.flash - dt)
        self.attack_timer = max(0, self.attack_timer - dt)
        self.special_timer = max(0, self.special_timer - dt)
        self.trample_timer = max(0, self.trample_timer - dt)
        self.charge_timer = max(0, self.charge_timer - dt)
        self.shockwave_timer = max(0, self.shockwave_timer - dt)
        self.wall_leap_timer = max(0, self.wall_leap_timer - dt)

        self.ensure_titan_clear(game)
        self.try_titan_summon(game)

        if self.wall_leap_time > 0:
            self.update_titan_wall_leap(dt, game)
            return

        if self.charge_time > 0:
            self.update_titan_charge(dt, game)
            return

        target_structure = self.nearby_structure(game)
        player_dist = self.pos.distance_to(game.player.pos)
        if self.attack_timer <= 0 and (player_dist < 100 or target_structure is not None):
            self.titan_stomp(game, radius=118, damage=self.damage + 8)
            self.attack_timer = self.cfg["attack_rate"]
            return

        if self.shockwave_timer <= 0 and player_dist < 340:
            self.titan_stomp(game, radius=150, damage=self.damage + 2)
            self.shockwave_timer = random.uniform(5.2, 7.2)
            self.attack_timer = max(self.attack_timer, 0.65)

        if self.charge_timer <= 0 and 135 < player_dist < 520 and self.has_titan_charge_lane(game, game.player.pos):
            self.start_titan_charge(game.player.pos, game)
            return

        self.follow_titan_path(dt, game)
        moved = self.pos.distance_to(self.last_pos)
        self.stuck_timer = self.stuck_timer + dt if moved < 1.2 else 0
        self.last_pos = Vec2(self.pos)
        if self.stuck_timer > 0.8:
            if self.wall_leap_timer <= 0:
                self.start_titan_wall_leap(game)
            else:
                self.nudge_titan_out(game)
            self.stuck_timer = 0

    def ensure_titan_clear(self, game):
        if not game.tile_map.collides_circle(self.pos, self.radius, ()):
            return
        cell = game.tile_map.world_to_cell(self.pos)
        clear_cell = nearest_clear_cell(game.tile_map, cell, self.radius, max_distance=10, prefer_pos=game.player.pos)
        if clear_cell is not None:
            self.pos = game.tile_map.cell_center(clear_cell)
            self.path.clear()
            game.create_shockwave(self.pos, 46, 0, visual_only=True)

    def nudge_titan_out(self, game):
        cell = game.tile_map.world_to_cell(self.pos)
        clear_cell = nearest_clear_cell(game.tile_map, cell, self.radius, max_distance=7, prefer_pos=game.player.pos)
        if clear_cell is None:
            return
        target = game.tile_map.cell_center(clear_cell)
        if self.pos.distance_to(target) > 2:
            self.pos = self.pos.lerp(target, 0.55)
            self.path.clear()

    def start_titan_wall_leap(self, game):
        player_cell = game.tile_map.world_to_cell(game.player.pos)
        target_cell = nearest_clear_cell(game.tile_map, player_cell, self.radius, max_distance=9, prefer_pos=self.pos)
        if target_cell is None:
            return False
        self.wall_leap_start = Vec2(self.pos)
        self.wall_leap_target = game.tile_map.cell_center(target_cell)
        if self.wall_leap_target.distance_to(self.pos) < 90:
            return False
        self.wall_leap_duration = clamp(self.wall_leap_target.distance_to(self.pos) / 520, 0.55, 0.95)
        self.wall_leap_time = self.wall_leap_duration
        self.wall_leap_timer = random.uniform(6.5, 8.5)
        self.path.clear()
        game.message = "Titan vaults the wall!"
        game.message_timer = 1.4
        game.create_shockwave(self.pos, 62, 0, visual_only=True)
        return True

    def update_titan_wall_leap(self, dt, game):
        self.wall_leap_time -= dt
        progress = 1 - clamp(self.wall_leap_time / self.wall_leap_duration, 0, 1)
        eased = progress * progress * (3 - 2 * progress)
        self.pos = self.wall_leap_start.lerp(self.wall_leap_target, eased)
        if self.wall_leap_time <= 0:
            self.pos = Vec2(self.wall_leap_target)
            self.titan_stomp(game, radius=128, damage=self.damage + 12)
            self.path_timer = 0
            self.stuck_timer = 0

    def follow_titan_path(self, dt, game):
        self.path_timer -= dt
        if self.path_timer <= 0:
            self.rebuild_titan_path(game)
            self.path_timer = random.uniform(0.22, 0.38)
            if not self.path and self.wall_leap_timer <= 0:
                self.start_titan_wall_leap(game)
                return

        target_pos = None
        while self.path:
            target_pos = game.tile_map.cell_center(self.path[0])
            if self.pos.distance_to(target_pos) < 10:
                self.path.pop(0)
                target_pos = None
            else:
                break
        if target_pos is None:
            target_pos = game.player.pos

        self.move_titan_towards(target_pos, dt, game)

    def rebuild_titan_path(self, game):
        start = nearest_clear_cell(game.tile_map, game.tile_map.world_to_cell(self.pos), self.radius, max_distance=8)
        goal = nearest_clear_cell(
            game.tile_map,
            game.tile_map.world_to_cell(game.player.pos),
            self.radius,
            max_distance=12,
            prefer_pos=self.pos,
        )
        if start is None or goal is None:
            self.path = []
            return
        self.path = astar_clearance(game.tile_map, start, goal, self.radius)[:16]

    def move_titan_towards(self, target_pos, dt, game, speed_multiplier=1.0):
        direction = Vec2(target_pos) - self.pos
        if direction.length_squared() <= 1:
            return False
        desired = direction.normalize()
        step_size = self.speed * speed_multiplier * dt
        candidates = [
            desired,
            desired.rotate(22),
            desired.rotate(-22),
            desired.rotate(45),
            desired.rotate(-45),
            desired.rotate(75),
            desired.rotate(-75),
            desired.rotate(105),
            desired.rotate(-105),
        ]
        best = None
        best_score = -999
        for candidate in candidates:
            new_pos = self.pos + candidate * step_size
            if game.tile_map.collides_circle(new_pos, self.radius, ()):
                continue
            score = candidate.dot(desired) - new_pos.distance_to(game.player.pos) / 2000
            if score > best_score:
                best = candidate
                best_score = score
        if best is None:
            return False
        self.pos += best * step_size
        self.trample_structures(game, self.cfg["damage"] // 2)
        return True

    def start_titan_charge(self, target_pos, game):
        direction = Vec2(target_pos) - self.pos
        if direction.length_squared() <= 1:
            return
        self.charge_dir = direction.normalize()
        self.charge_time = 0.82
        self.charge_hit_player = False
        self.charge_timer = random.uniform(5.4, 7.0)
        self.path.clear()
        game.message = "Titan charge!"
        game.message_timer = 1.2
        game.create_shockwave(self.pos, 54, 0, visual_only=True)

    def update_titan_charge(self, dt, game):
        self.charge_time -= dt
        distance = self.speed * 3.3 * dt
        steps = max(1, int(distance // 7))
        for _ in range(steps):
            new_pos = self.pos + self.charge_dir * (distance / steps)
            if game.tile_map.collides_circle(new_pos, self.radius, ()):
                self.charge_time = 0
                if self.wall_leap_timer <= 0:
                    self.start_titan_wall_leap(game)
                else:
                    self.titan_stomp(game, radius=95, damage=self.damage + 3)
                return
            self.pos = new_pos
            self.trample_structures(game, self.damage + 18)
            if not self.charge_hit_player and self.pos.distance_to(game.player.pos) < self.radius + game.player.radius + 12:
                game.player.take_damage(self.damage + 16, game)
                self.charge_hit_player = True
                game.create_shockwave(self.pos, 74, 0, visual_only=True)
        if self.charge_time <= 0:
            self.titan_stomp(game, radius=86, damage=self.damage // 2)

    def has_titan_charge_lane(self, game, target_pos):
        target = Vec2(target_pos)
        delta = target - self.pos
        distance = delta.length()
        if distance <= 1:
            return False
        direction = delta.normalize()
        steps = max(1, int(distance // 14))
        for i in range(1, steps + 1):
            pos = self.pos + direction * (distance * i / steps)
            if game.tile_map.collides_circle(pos, self.radius, ()):
                return False
        return True

    def titan_stomp(self, game, radius, damage):
        game.create_shockwave(self.pos, radius, damage)
        self.trample_structures(game, damage + 12, force=True)

    def trample_structures(self, game, damage, force=False):
        if self.trample_timer > 0 and not force:
            return
        hit = False
        for structure in game.structures:
            if structure.alive and dist_point_rect((self.pos.x, self.pos.y), structure.rect) < self.radius + 12:
                structure.take_damage(damage, game)
                hit = True
        if hit:
            self.trample_timer = 0.24

    def try_titan_summon(self, game):
        if not self.summon_thresholds:
            return
        hp_pct = self.hp / self.max_hp
        if hp_pct > self.summon_thresholds[0]:
            return
        self.summon_thresholds.pop(0)
        game.message = "Titan roar summons infected!"
        game.message_timer = 1.6
        game.create_shockwave(self.pos, 120, 0, visual_only=True)
        for kind in ["walker", "walker", "runner", "runner", "spitter"]:
            game.spawn_minion_near(kind, self.pos)

    def try_acid(self, dt, game):
        if self.special_timer > 0:
            return
        target = game.player.pos
        dist = self.pos.distance_to(target)
        if 105 < dist < 360 and has_wall_line(game.tile_map, self.pos, target):
            game.acid_projectiles.append(
                AcidProjectile(self.pos, target, self.damage + 5 + game.wave // 2, kind="poison", pool_radius=62 + min(34, game.wave * 2))
            )
            self.special_timer = random.uniform(1.45, 2.15)
            game.play_sound("poison", 0.42, cooldown=0.45)

    def try_boomer_bile(self, game):
        if self.special_timer > 0:
            return
        target = game.player.pos
        dist = self.pos.distance_to(target)
        if 100 < dist < 340 and has_wall_line(game.tile_map, self.pos, target):
            game.acid_projectiles.append(
                AcidProjectile(self.pos, target, max(4, self.damage // 2), kind="bile", pool_radius=70)
            )
            self.special_timer = random.uniform(2.0, 3.0)
            game.play_sound("poison", 0.45, cooldown=0.45)

    def try_boomer_dash(self, game):
        if self.dash_time > 0:
            return
        if self.dash_timer > 0:
            return
        target = game.player.pos
        dist = self.pos.distance_to(target)
        if 70 < dist < 255:
            direction = target - self.pos
            if direction.length_squared() > 1:
                self.dash_dir = direction.normalize()
                self.dash_time = 0.28
                self.dash_timer = random.uniform(2.1, 3.2)
                game.spawn_spark(self.pos, (135, 255, 71))
                game.play_sound("dash", 0.42, cooldown=0.2)

    def should_explode(self, game):
        if self.pos.distance_to(game.player.pos) < 44:
            return True
        for structure in game.structures:
            if structure.alive and dist_point_rect((self.pos.x, self.pos.y), structure.rect) < 38:
                return True
        return False

    def try_lunge(self, game):
        if self.special_timer > 0:
            return
        dist = self.pos.distance_to(game.player.pos)
        if 70 < dist < 210 and has_wall_line(game.tile_map, self.pos, game.player.pos):
            self.lunge_boost = 0.32
            self.special_timer = random.uniform(2.2, 3.6)

    def try_stomp(self, game):
        if self.attack_timer > 0:
            return
        if self.pos.distance_to(game.player.pos) < 58:
            game.create_explosion(self.pos, 62, self.damage, enemy_owned=True, visual_only=False)
            self.attack_timer = self.cfg["attack_rate"]
            return
        for structure in game.structures:
            if structure.alive and dist_point_rect((self.pos.x, self.pos.y), structure.rect) < 50:
                game.create_explosion(self.pos, 62, self.damage, enemy_owned=True, visual_only=False)
                self.attack_timer = self.cfg["attack_rate"]
                return

    def nearby_structure(self, game):
        best = None
        best_dist = 1_000_000
        for structure in game.structures:
            if not structure.alive:
                continue
            reach = self.radius + 8
            distance = dist_point_rect((self.pos.x, self.pos.y), structure.rect)
            if distance < reach and distance < best_dist:
                best = structure
                best_dist = distance
        return best

    def follow_path(self, dt, game):
        self.path_timer -= dt
        if self.path_timer <= 0:
            self.rebuild_path(game)
            self.path_timer = random.uniform(0.28, 0.55)

        target_pos = None
        while self.path:
            target_pos = game.tile_map.cell_center(self.path[0])
            if self.pos.distance_to(target_pos) < 6:
                self.path.pop(0)
                target_pos = None
            else:
                break
        if target_pos is None:
            target_pos = game.player.pos

        direction = target_pos - self.pos
        if direction.length_squared() <= 1:
            return
        speed = self.speed * game.zombie_speed_multiplier(self.kind)
        if self.lunge_boost > 0:
            speed *= 1.9
        if self.dash_time > 0 and self.dash_dir.length_squared() > 0:
            direction = self.dash_dir
            speed *= 3.2
        self.try_move(direction.normalize() * speed * dt, game)

    def rebuild_path(self, game):
        start = game.tile_map.world_to_cell(self.pos)
        goal = game.tile_map.world_to_cell(game.player.pos)
        blocked = game.blocked_cells()
        path = astar(game.tile_map, start, goal, blocked)
        if not path:
            structure = game.nearest_structure(self.pos)
            if structure is not None:
                path = astar(game.tile_map, start, structure.cell, blocked)
        self.path = path[:14]

    def try_move(self, delta, game):
        blockers = [s for s in game.structures if s.alive]
        new_pos = self.pos + delta
        if not game.tile_map.collides_circle(new_pos, self.radius, blockers):
            self.pos = new_pos
            return
        x_pos = Vec2(self.pos.x + delta.x, self.pos.y)
        if not game.tile_map.collides_circle(x_pos, self.radius, blockers):
            self.pos = x_pos
            return
        y_pos = Vec2(self.pos.x, self.pos.y + delta.y)
        if not game.tile_map.collides_circle(y_pos, self.radius, blockers):
            self.pos = y_pos

    def draw(self, surface, sprites):
        sprite = sprites[self.kind]
        rect = sprite.get_rect(center=(round(self.pos.x), round(self.pos.y)))
        if self.kind == "stalker":
            ghost = sprite.copy()
            ghost.set_alpha(135 if self.lunge_boost <= 0 else 220)
            surface.blit(ghost, rect)
        else:
            surface.blit(sprite, rect)
        if self.flash > 0:
            pygame.draw.circle(surface, (255, 255, 255), self.pos, self.radius + 2, 2)

        pct = clamp(self.hp / self.max_hp, 0, 1)
        width = 28 if self.kind != "titan" else 52
        bar = pygame.Rect(0, 0, width, 5)
        bar.center = (round(self.pos.x), round(self.pos.y - self.radius - 12))
        pygame.draw.rect(surface, (45, 28, 30), bar)
        pygame.draw.rect(surface, COLORS["red"], (bar.x, bar.y, int(bar.w * pct), bar.h))


class GoldDrop:
    def __init__(self, pos, amount):
        self.pos = Vec2(pos) + Vec2(random.uniform(-12, 12), random.uniform(-12, 12))
        self.amount = amount
        self.life = 20
        self.pulse = random.uniform(0, math.tau)
        self.alive = True

    def update(self, dt, game):
        self.life -= dt
        if self.life <= 0:
            self.alive = False
            return
        distance = self.pos.distance_to(game.player.pos)
        if distance < game.player.pickup_radius:
            direction = game.player.pos - self.pos
            if direction.length_squared() > 1:
                self.pos += direction.normalize() * (game.player.pickup_radius * 2 - distance) * dt
        if distance < 19:
            amount = max(1, int(round(self.amount * (1 + game.player.gold_bonus))))
            game.player.gold += amount
            game.play_sound("coin", 0.44, cooldown=0.07)
            game.floating_texts.append(FloatingText(self.pos, f"+{amount}", COLORS["gold"], life=0.7))
            self.alive = False

    def draw(self, surface):
        radius = 5 + int(math.sin(pygame.time.get_ticks() * 0.006 + self.pulse) > 0)
        pygame.draw.rect(surface, (144, 92, 32), (self.pos.x - radius, self.pos.y - radius, radius * 2, radius * 2))
        pygame.draw.rect(surface, COLORS["gold"], (self.pos.x - radius + 2, self.pos.y - radius + 2, radius * 2 - 4, radius * 2 - 4))


class Particle:
    def __init__(self, pos, vel, color, life=0.45, size=3):
        self.pos = Vec2(pos)
        self.vel = Vec2(vel)
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size
        self.alive = True

    def update(self, dt):
        self.life -= dt
        if self.life <= 0:
            self.alive = False
            return
        self.pos += self.vel * dt
        self.vel *= 0.92

    def draw(self, surface):
        alpha = clamp(self.life / self.max_life, 0, 1)
        size = max(1, int(self.size * alpha))
        pygame.draw.rect(surface, self.color, (self.pos.x - size, self.pos.y - size, size * 2, size * 2))


class FloatingText:
    def __init__(self, pos, text, color, life=0.9):
        self.pos = Vec2(pos)
        self.text = text
        self.color = color
        self.life = life
        self.max_life = life
        self.alive = True

    def update(self, dt):
        self.life -= dt
        self.pos.y -= 30 * dt
        if self.life <= 0:
            self.alive = False

    def draw(self, surface, font):
        image = font.render(self.text, True, self.color)
        image.set_alpha(int(255 * clamp(self.life / self.max_life, 0, 1)))
        rect = image.get_rect(center=(round(self.pos.x), round(self.pos.y)))
        surface.blit(image, rect)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Pixel Zombie Siege")
        headless = "--smoke" in sys.argv or os.environ.get("SDL_VIDEODRIVER") == "dummy"
        if headless:
            self.screen = pygame.display.set_mode((DESIGN_W, DESIGN_H))
        else:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.screen_w, self.screen_h = self.screen.get_size()
        self.ui_scale = clamp(min(self.screen_w / DESIGN_W, self.screen_h / DESIGN_H), 0.68, 1.15)
        self.top_ui_h = max(104, int(TOP_UI_H * self.ui_scale))
        self.bottom_ui_h = max(112, int(BOTTOM_UI_H * self.ui_scale))
        self.margin = max(10, int(16 * self.ui_scale))
        self.world_surface = pygame.Surface((WORLD_W, WORLD_H))
        self.play_rect = pygame.Rect(
            self.margin,
            self.top_ui_h,
            max(320, self.screen_w - self.margin * 2),
            max(240, self.screen_h - self.top_ui_h - self.bottom_ui_h - self.margin),
        )
        self.world_scale = min(self.play_rect.w / WORLD_W, self.play_rect.h / WORLD_H)
        self.world_rect = pygame.Rect(0, 0, int(WORLD_W * self.world_scale), int(WORLD_H * self.world_scale))
        self.world_rect.center = self.play_rect.center
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", max(18, int(24 * self.ui_scale)))
        self.small_font = pygame.font.SysFont("consolas", max(14, int(18 * self.ui_scale)))
        self.tiny_font = pygame.font.SysFont("consolas", max(11, int(14 * self.ui_scale)))
        self.big_font = pygame.font.SysFont("consolas", max(38, int(64 * self.ui_scale)), bold=True)
        self.title_font = pygame.font.SysFont("consolas", max(42, int(74 * self.ui_scale)), bold=True)
        self.sprites = build_sprites()
        self.state = "menu"
        self.paused = False
        self.language = "vi"
        self.music_volume = 70
        self.sfx_volume = 80
        self.auto_fire = True
        self.dev_mode = False
        self.difficulty_id = "normal"
        self.character_id = "soldier"
        self.options_return_state = "menu"
        self.options_return_paused = False
        self.ui_buttons = {}
        self.headless = headless
        self.audio_enabled = False
        self.sounds = {}
        self.sound_cooldowns = {}
        self.init_audio()
        self.reset_gameplay()

    def reset_gameplay(self):
        self.tile_map = TileMap(MAP_ROWS)
        self.player = Player((WORLD_W / 2, WORLD_H / 2), self.character_id)
        self.zombies = []
        self.bullets = []
        self.lasers = []
        self.acid_projectiles = []
        self.poison_pools = []
        self.structures = []
        self.gold_drops = []
        self.particles = []
        self.floating_texts = []
        self.wave = 0
        self.wave_active = False
        self.wave_break_timer = 0
        self.spawn_queue = []
        self.spawn_timer = 0
        self.build_mode = None
        self.game_over = False
        self.bile_timer = 0
        self.message = "Press SPACE to start wave 1"
        self.message_timer = 4
        self.spawn_cells = self.build_spawn_cells()
        self.boss_spawn_cells = self.build_boss_spawn_cells()
        self.paused = False
        self.build_mode = None

    def t(self, key):
        return TEXT[self.language].get(key, key)

    def init_audio(self):
        if self.headless:
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except pygame.error:
            self.audio_enabled = False
            return

        audio_dir = os.path.join(os.path.dirname(__file__), "assets", "audio", "kenney_rpg", "OGG")
        sound_files = {
            "click": "metalClick.ogg",
            "shoot": "knifeSlice.ogg",
            "laser": "drawKnife3.ogg",
            "coin": "handleCoins.ogg",
            "build": "metalLatch.ogg",
            "upgrade": "handleCoins2.ogg",
            "hit": "chop.ogg",
            "explosion": "metalPot3.ogg",
            "poison": "creak3.ogg",
            "hurt": "cloth3.ogg",
            "wave": "doorOpen_1.ogg",
            "dash": "clothBelt.ogg",
        }
        for name, filename in sound_files.items():
            path = os.path.join(audio_dir, filename)
            if not os.path.exists(path):
                continue
            try:
                self.sounds[name] = pygame.mixer.Sound(path)
            except pygame.error:
                continue
        self.audio_enabled = bool(self.sounds)

    def play_sound(self, name, volume=1.0, cooldown=0.0):
        if not self.audio_enabled or self.sfx_volume <= 0:
            return
        sound = self.sounds.get(name)
        if sound is None:
            return
        now = pygame.time.get_ticks() / 1000
        if cooldown > 0 and now < self.sound_cooldowns.get(name, 0):
            return
        sound.set_volume(clamp(volume * self.sfx_volume / 100, 0, 1))
        sound.play()
        if cooldown > 0:
            self.sound_cooldowns[name] = now + cooldown

    def open_options(self, return_state="menu", return_paused=False):
        self.options_return_state = return_state
        self.options_return_paused = return_paused
        self.state = "options"
        self.paused = False

    def close_options(self):
        self.state = self.options_return_state
        self.paused = self.options_return_paused if self.state == "playing" else False

    def gold_text(self):
        return self.t("infinite") if self.dev_mode else str(self.player.gold)

    def difficulty_cfg(self):
        return DIFFICULTIES.get(self.difficulty_id, DIFFICULTIES["normal"])

    def structure_balance_cfg(self):
        return STRUCTURE_DIFFICULTY_BALANCE.get(self.difficulty_id, STRUCTURE_DIFFICULTY_BALANCE["normal"])

    def scaled_wave_count(self, count):
        return max(1, int(round(count * self.difficulty_cfg()["count"])))

    def structure_stats(self, kind):
        cfg = STRUCTURE_TYPES[kind]
        balance = self.structure_balance_cfg()
        return {
            "hp": max(1, int(round(cfg["hp"] * balance["hp"]))),
            "range": max(0, int(round(cfg["range"] * balance["turret_range"]))),
            "damage": max(0, int(round(cfg["damage"] * balance["turret_damage"]))),
            "cooldown": max(0.08, cfg["cooldown"] * balance["turret_cooldown"]),
        }

    def structure_cost(self, kind):
        base_cost = STRUCTURE_TYPES[kind]["cost"]
        difficulty_cost = self.structure_balance_cfg()["cost"]
        discount = CHARACTERS.get(self.character_id, CHARACTERS["soldier"])["build_discount"]
        return max(1, int(round(base_cost * difficulty_cost * (1 - discount))))

    def repair_cost(self):
        difficulty_cost = self.structure_balance_cfg()["repair_cost"]
        discount = CHARACTERS.get(self.character_id, CHARACTERS["soldier"])["build_discount"]
        return max(1, int(round(15 * difficulty_cost * (1 - discount))))

    def can_afford(self, cost):
        return self.dev_mode or self.player.gold >= cost

    def spend_gold(self, cost):
        if not self.dev_mode:
            self.player.gold -= cost

    def draw_text_center(self, text, rect, color=None, font=None):
        color = color or COLORS["text"]
        font = font or self.font
        image = font.render(text, True, color)
        self.screen.blit(image, image.get_rect(center=rect.center))

    def draw_panel(self, rect, color=(18, 20, 25), alpha=210, border=True):
        panel = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        panel.fill((*color, alpha))
        self.screen.blit(panel, rect)
        if border:
            pygame.draw.rect(self.screen, COLORS["hud_line"], rect, 2, border_radius=8)

    def draw_button(self, key, rect, label, *, active=False, disabled=False, font=None):
        mouse = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse) and not disabled
        if disabled:
            fill = (44, 47, 54)
            text_color = (118, 124, 130)
        elif active:
            fill = (58, 105, 104)
            text_color = COLORS["text"]
        elif hover:
            fill = (64, 68, 78)
            text_color = COLORS["gold"]
        else:
            fill = (35, 38, 46)
            text_color = COLORS["text"]
        pygame.draw.rect(self.screen, fill, rect, border_radius=8)
        pygame.draw.rect(self.screen, COLORS["hud_line"], rect, 2, border_radius=8)
        self.draw_text_center(label, rect, text_color, font or self.font)
        self.ui_buttons[key] = rect

    def screen_to_world(self, pos):
        if not self.world_rect.collidepoint(pos):
            return None
        x = (pos[0] - self.world_rect.x) / self.world_scale
        y = (pos[1] - self.world_rect.y) / self.world_scale
        if 0 <= x < WORLD_W and 0 <= y < WORLD_H:
            return Vec2(x, y)
        return None

    def mouse_world(self):
        return self.screen_to_world(pygame.mouse.get_pos())

    def pointer_over_ui(self):
        x, y = pygame.mouse.get_pos()
        if y <= self.top_ui_h or y >= self.screen_h - self.bottom_ui_h:
            return True
        return any(rect.collidepoint((x, y)) for rect in self.ui_buttons.values())

    def find_auto_fire_target(self):
        weapon_range = self.player.weapon.bullet_range
        best = None
        best_dist = weapon_range * weapon_range
        for zombie in self.zombies:
            if not zombie.alive:
                continue
            dist_sq = self.player.pos.distance_squared_to(zombie.pos)
            if dist_sq < best_dist and has_wall_line(self.tile_map, self.player.pos, zombie.pos):
                best = zombie
                best_dist = dist_sq
        return best.pos if best is not None else None

    def zombie_speed_multiplier(self, kind):
        if self.bile_timer <= 0:
            return 1.0
        if kind == "titan":
            return 1.25
        return BILE_BOOST_MULTIPLIER

    def apply_bile(self, pos):
        self.bile_timer = BILE_BOOST_DURATION
        self.message = "Boomer bile! Zombies are enraged!"
        self.message_timer = 2.0
        self.create_bile_splash(pos, 82)
        self.play_sound("poison", 0.55, cooldown=0.25)

    def create_bile_splash(self, pos, radius):
        pos = Vec2(pos)
        for _ in range(24):
            angle = random.uniform(0, math.tau)
            direction = Vec2(math.cos(angle), math.sin(angle))
            self.particles.append(Particle(pos, direction * random.uniform(50, 170), (118, 255, 68), life=0.55, size=3))
        for zombie in self.zombies:
            if zombie.alive and zombie.pos.distance_to(pos) <= radius + zombie.radius:
                zombie.flash = 0.18

    def fire_laser(self, start, direction, damage, max_range, pierce):
        start = Vec2(start)
        direction = Vec2(direction)
        if direction.length_squared() == 0:
            return
        direction = direction.normalize()
        end = start + direction * max_range
        steps = max(1, int(max_range // 8))
        for i in range(1, steps + 1):
            probe = start + direction * (max_range * i / steps)
            if not (0 <= probe.x < WORLD_W and 0 <= probe.y < WORLD_H) or self.tile_map.is_wall(self.tile_map.world_to_cell(probe)):
                end = probe
                break

        hits = []
        laser_vec = end - start
        length_sq = max(1, laser_vec.length_squared())
        for zombie in self.zombies:
            if not zombie.alive:
                continue
            t = clamp((zombie.pos - start).dot(laser_vec) / length_sq, 0, 1)
            closest = start + laser_vec * t
            distance = closest.distance_to(zombie.pos)
            if distance <= zombie.radius + 8:
                hits.append((t, zombie, closest))
        hits.sort(key=lambda item: item[0])
        hit_limit = max(1, pierce + 1)
        for index, (_, zombie, point) in enumerate(hits[:hit_limit]):
            falloff = 0.82 ** index
            zombie.take_damage(max(1, int(damage * falloff)), self)
            self.spawn_spark(point, (126, 244, 255))

        self.lasers.append(LaserBeam(start, end, width=8, life=0.13))
        self.add_muzzle_particle(start, direction * 500)
        self.play_sound("laser", 0.48, cooldown=0.045)

    def build_spawn_cells(self):
        cells = []
        for y, row in enumerate(MAP_ROWS):
            for x, value in enumerate(row):
                if value == "#":
                    continue
                if x in (1, GRID_W - 2) or y in (1, GRID_H - 2):
                    cells.append((x, y))
        return cells

    def build_boss_spawn_cells(self):
        radius = ZOMBIE_TYPES["titan"]["radius"]
        cells = []
        for y, row in enumerate(MAP_ROWS):
            for x, value in enumerate(row):
                cell = (x, y)
                if value != "#" and self.tile_map.is_clear_for_radius(cell, radius):
                    cells.append(cell)
        return cells

    def blocked_cells(self):
        return {structure.cell for structure in self.structures if structure.alive}

    def nearest_structure(self, pos):
        alive = [s for s in self.structures if s.alive]
        if not alive:
            return None
        return min(alive, key=lambda s: Vec2(s.rect.center).distance_squared_to(pos))

    def start_wave(self):
        if self.wave_active or self.game_over:
            return
        self.wave_break_timer = 0
        self.wave += 1
        self.spawn_queue = self.make_wave(self.wave)
        random.shuffle(self.spawn_queue)
        self.spawn_timer = 0.4
        self.wave_active = True
        self.message = f"Wave {self.wave}"
        self.message_timer = 2.0
        self.play_sound("wave", 0.42, cooldown=0.5)

    def make_wave(self, wave):
        queue = ["walker"] * self.scaled_wave_count(7 + wave * 4)
        if wave >= 2:
            queue += ["runner"] * self.scaled_wave_count(3 + wave * 2)
        if wave >= 3:
            queue += ["spitter"] * self.scaled_wave_count(max(2, wave // 2 + 1))
        if wave >= 4:
            queue += ["boomer"] * self.scaled_wave_count(max(2, wave // 2 + 1))
        if wave >= 5:
            queue += ["stalker"] * self.scaled_wave_count(max(2, wave // 3 + 1))
        if wave % 5 == 0:
            queue += ["titan"]
        return queue

    def spawn_zombie(self, kind):
        player_cell = self.tile_map.world_to_cell(self.player.pos)
        source_cells = self.boss_spawn_cells if kind == "titan" else self.spawn_cells
        if kind == "titan":
            source_cells = [cell for cell in source_cells if self.tile_map.cell_center(cell).distance_to(self.player.pos) > 360]
            if not source_cells:
                source_cells = self.boss_spawn_cells
        candidates = sorted(
            source_cells,
            key=lambda cell: abs(cell[0] - player_cell[0]) + abs(cell[1] - player_cell[1]),
            reverse=True,
        )
        if not candidates:
            fallback = nearest_clear_cell(self.tile_map, player_cell, ZOMBIE_TYPES[kind]["radius"], max_distance=14)
            if fallback is None:
                return
            candidates = [fallback]
        cell = random.choice(candidates[: max(4, len(candidates) // 3)])
        pos = self.tile_map.cell_center(cell)
        self.zombies.append(Zombie(kind, pos, self.wave, self.difficulty_id))

    def spawn_minion_near(self, kind, pos):
        radius = ZOMBIE_TYPES[kind]["radius"]
        origin = self.tile_map.world_to_cell(pos)
        cells = []
        blocked = self.blocked_cells()
        for distance in range(2, 8):
            for y in range(origin[1] - distance, origin[1] + distance + 1):
                for x in range(origin[0] - distance, origin[0] + distance + 1):
                    cell = (x, y)
                    if abs(x - origin[0]) != distance and abs(y - origin[1]) != distance:
                        continue
                    if cell in blocked or not self.tile_map.is_clear_for_radius(cell, radius):
                        continue
                    if self.tile_map.cell_center(cell).distance_to(self.player.pos) < 90:
                        continue
                    cells.append(cell)
            if cells:
                break
        if not cells:
            self.spawn_zombie(kind)
            return
        self.zombies.append(Zombie(kind, self.tile_map.cell_center(random.choice(cells)), self.wave, self.difficulty_id))

    def drop_gold(self, pos, total):
        chunks = max(1, min(5, total // 7))
        remaining = total
        for i in range(chunks):
            amount = remaining // (chunks - i)
            remaining -= amount
            self.gold_drops.append(GoldDrop(pos, amount))

    def place_structure(self, kind, cell):
        if cell[0] >= GRID_W or cell[1] >= GRID_H or not self.tile_map.in_bounds(cell):
            return False
        if self.tile_map.is_wall(cell):
            self.message = "Cannot build on wall"
            self.message_timer = 1.4
            return False
        if cell in self.blocked_cells():
            self.message = "Tile occupied"
            self.message_timer = 1.4
            return False
        if self.tile_map.cell_center(cell).distance_to(self.player.pos) < 40:
            self.message = "Too close to player"
            self.message_timer = 1.4
            return False
        cost = self.structure_cost(kind)
        if not self.can_afford(cost):
            self.message = "Not enough gold"
            self.message_timer = 1.4
            return False
        self.spend_gold(cost)
        self.structures.append(Structure(kind, cell, self.structure_stats(kind)))
        self.message = f"Built {STRUCTURE_TYPES[kind]['label']}"
        self.message_timer = 1.2
        self.play_sound("build", 0.55, cooldown=0.12)
        return True

    def repair_nearest(self):
        damaged = [s for s in self.structures if s.alive and s.hp < s.max_hp]
        if not damaged:
            self.message = "No damaged structure nearby"
            self.message_timer = 1.3
            return
        nearest = min(damaged, key=lambda s: Vec2(s.rect.center).distance_squared_to(self.player.pos))
        if Vec2(nearest.rect.center).distance_to(self.player.pos) > 90:
            self.message = "Move closer to repair"
            self.message_timer = 1.3
            return
        cost = self.repair_cost()
        if not self.can_afford(cost):
            self.message = f"Need {cost} gold to repair"
            self.message_timer = 1.3
            return
        self.spend_gold(cost)
        repair_amount = int(round(70 * self.structure_balance_cfg()["repair_amount"]))
        nearest.repair(repair_amount)
        self.floating_texts.append(FloatingText(Vec2(nearest.rect.center), "+repair", COLORS["green"]))
        self.play_sound("build", 0.42, cooldown=0.12)

    def upgrade_weapon(self):
        if self.player.weapon.is_maxed:
            self.message = f"{self.player.weapon.tier_name} is MAX level"
            self.message_timer = 1.4
            return
        cost = self.player.weapon.upgrade_cost
        if not self.can_afford(cost):
            self.message = f"Need {cost} gold"
            self.message_timer = 1.3
            return
        self.spend_gold(cost)
        old_name = self.player.weapon.tier_name
        self.player.weapon.upgrade()
        new_name = self.player.weapon.tier_name
        if new_name != old_name:
            self.message = f"Weapon evolved: {new_name}"
        else:
            self.message = f"{new_name} upgraded to Lv {self.player.weapon.level}"
        self.message_timer = 1.8
        self.play_sound("upgrade", 0.62, cooldown=0.12)

    def damage_zombies_in_radius(self, pos, radius, damage, exclude=None):
        for zombie in self.zombies:
            if not zombie.alive or zombie is exclude:
                continue
            distance = zombie.pos.distance_to(pos)
            if distance <= radius + zombie.radius:
                scale = 1 - min(1, distance / max(1, radius))
                zombie.take_damage(max(1, int(damage * (0.45 + scale * 0.55))), self)

    def create_shockwave(self, pos, radius, damage, visual_only=False):
        pos = Vec2(pos)
        for angle_deg in range(0, 360, 9):
            angle = math.radians(angle_deg + random.uniform(-3, 3))
            direction = Vec2(math.cos(angle), math.sin(angle))
            start = pos + direction * random.uniform(10, 22)
            speed = random.uniform(145, 260)
            color = random.choice([(188, 84, 76), (242, 166, 69), (238, 216, 118)])
            self.particles.append(Particle(start, direction * speed, color, life=0.46, size=4))
        if visual_only or damage <= 0:
            return
        player_dist = self.player.pos.distance_to(pos)
        if player_dist < radius:
            scale = 1 - player_dist / radius
            self.player.take_damage(max(3, int(damage * (0.42 + scale * 0.58))), self)
        for structure in self.structures:
            if structure.alive and dist_point_rect((pos.x, pos.y), structure.rect) < radius:
                distance = dist_point_rect((pos.x, pos.y), structure.rect)
                scale = 1 - distance / radius
                structure.take_damage(max(5, int(damage * (0.45 + scale * 0.55))), self)

    def create_explosion(self, pos, radius, damage, enemy_owned=True, visual_only=False):
        self.play_sound("explosion", 0.5, cooldown=0.18)
        for _ in range(26):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(45, 190)
            color = random.choice([(248, 126, 62), (244, 210, 93), (172, 68, 64)])
            self.particles.append(Particle(pos, Vec2(math.cos(angle), math.sin(angle)) * speed, color, life=0.65, size=4))
        if visual_only:
            return
        if enemy_owned and self.player.pos.distance_to(pos) < radius:
            scale = 1 - self.player.pos.distance_to(pos) / radius
            self.player.take_damage(max(4, int(damage * scale)), self)
        for structure in self.structures:
            if structure.alive and dist_point_rect((pos.x, pos.y), structure.rect) < radius:
                distance = dist_point_rect((pos.x, pos.y), structure.rect)
                scale = 1 - distance / radius
                structure.take_damage(max(6, int(damage * scale)), self)

    def add_muzzle_particle(self, pos, vel):
        for _ in range(4):
            direction = vel.normalize().rotate(random.uniform(-26, 26))
            self.particles.append(Particle(pos, direction * random.uniform(25, 90), COLORS["gold"], life=0.18, size=2))

    def spawn_spark(self, pos, color):
        for _ in range(5):
            angle = random.uniform(0, math.tau)
            self.particles.append(Particle(pos, Vec2(math.cos(angle), math.sin(angle)) * random.uniform(30, 115), color, life=0.28, size=2))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and self.state == "menu":
                    return False
                if event.key == pygame.K_ESCAPE and self.state == "setup":
                    self.state = "menu"
                    return True
                if event.key == pygame.K_ESCAPE and self.state == "options":
                    self.close_options()
                    return True
                if event.key == pygame.K_ESCAPE and self.state == "playing":
                    self.paused = not self.paused
                    return True
                if self.state != "playing":
                    continue
                if self.game_over and event.key == pygame.K_RETURN:
                    self.reset_gameplay()
                    return True
                if event.key == pygame.K_p:
                    self.paused = not self.paused
                elif event.key == pygame.K_f:
                    self.auto_fire = not self.auto_fire
                elif event.key == pygame.K_F10:
                    self.dev_mode = not self.dev_mode
                    self.message = "Developer Mode: ON" if self.dev_mode else "Developer Mode: OFF"
                    self.message_timer = 1.5
                elif not self.paused and event.key == pygame.K_SPACE:
                    self.start_wave()
                elif not self.paused and event.key == pygame.K_1:
                    self.upgrade_weapon()
                elif not self.paused and event.key == pygame.K_2:
                    self.build_mode = "turret"
                    self.message = "Build mode: Turret"
                    self.message_timer = 1.0
                elif not self.paused and event.key == pygame.K_3:
                    self.build_mode = "fence"
                    self.message = "Build mode: Fence"
                    self.message_timer = 1.0
                elif event.key == pygame.K_b:
                    self.build_mode = None
                elif not self.paused and event.key == pygame.K_r:
                    self.repair_nearest()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button != 1:
                    if event.button == 3:
                        self.build_mode = None
                    continue
                action = self.button_at(event.pos)
                if action and self.handle_button(action):
                    if action in ("menu_exit", "exit_game"):
                        return False
                    continue
                if self.state != "playing" or self.paused:
                    continue
                if self.build_mode is not None:
                    world_pos = self.screen_to_world(event.pos)
                    if world_pos is not None:
                        self.place_structure(self.build_mode, self.tile_map.world_to_cell(world_pos))
        return True

    def button_at(self, pos):
        for key, rect in self.ui_buttons.items():
            if rect.collidepoint(pos):
                return key
        return None

    def handle_button(self, action):
        self.play_sound("click", 0.35, cooldown=0.06)
        if self.state == "menu":
            if action == "menu_start":
                self.state = "setup"
                return True
            if action == "menu_options":
                self.open_options("menu", False)
                return True
            if action == "menu_exit":
                return True
        elif self.state == "setup":
            if action == "setup_begin":
                self.reset_gameplay()
                self.state = "playing"
                return True
            if action == "setup_back":
                self.state = "menu"
                return True
            if action.startswith("difficulty_"):
                difficulty_id = action.removeprefix("difficulty_")
                if difficulty_id in DIFFICULTIES:
                    self.difficulty_id = difficulty_id
                    return True
            if action.startswith("character_"):
                character_id = action.removeprefix("character_")
                if character_id in CHARACTERS:
                    self.character_id = character_id
                    return True
        elif self.state == "options":
            if action == "options_back":
                self.close_options()
            elif action == "lang_toggle":
                self.language = "en" if self.language == "vi" else "vi"
            elif action == "auto_toggle":
                self.auto_fire = not self.auto_fire
            elif action == "dev_toggle":
                self.dev_mode = not self.dev_mode
            elif action == "music_down":
                self.music_volume = max(0, self.music_volume - 10)
            elif action == "music_up":
                self.music_volume = min(100, self.music_volume + 10)
            elif action == "sfx_down":
                self.sfx_volume = max(0, self.sfx_volume - 10)
            elif action == "sfx_up":
                self.sfx_volume = min(100, self.sfx_volume + 10)
            return True
        elif self.state == "playing":
            if action == "pause_toggle":
                self.paused = not self.paused
            elif self.paused and action == "pause_resume":
                self.paused = False
            elif self.paused and action == "pause_options":
                self.open_options("playing", True)
            elif self.paused and action == "pause_menu":
                self.state = "menu"
                self.paused = False
            elif not self.paused and action == "hotbar_upgrade":
                self.upgrade_weapon()
            elif not self.paused and action == "hotbar_turret":
                self.build_mode = "turret"
                self.message = "Build mode: Turret"
                self.message_timer = 1.0
            elif not self.paused and action == "hotbar_fence":
                self.build_mode = "fence"
                self.message = "Build mode: Fence"
                self.message_timer = 1.0
            elif not self.paused and action == "auto_toggle_game":
                self.auto_fire = not self.auto_fire
            else:
                return False
            return True
        return action in self.ui_buttons

    def update(self, dt):
        if self.state != "playing" or self.paused:
            return
        if self.game_over:
            return
        self.message_timer = max(0, self.message_timer - dt)
        self.bile_timer = max(0, self.bile_timer - dt)
        if self.wave_active:
            self.spawn_timer -= dt
            if self.spawn_queue and self.spawn_timer <= 0:
                self.spawn_zombie(self.spawn_queue.pop(0))
                self.spawn_timer = max(0.24, 0.95 - self.wave * 0.045)
            if not self.spawn_queue and not any(z.alive for z in self.zombies):
                self.wave_active = False
                self.wave_break_timer = WAVE_BREAK_SECONDS
                reward = int(round((25 + self.wave * 7) * self.difficulty_cfg()["reward"]))
                self.player.gold += reward
                self.message = f"Wave clear! Bonus +{reward} gold"
                self.message_timer = 3.0
        elif self.wave > 0 and self.wave_break_timer > 0:
            self.wave_break_timer -= dt
            if self.wave_break_timer <= 0:
                self.start_wave()

        self.player.update(dt, self)
        for structure in self.structures:
            structure.update(dt, self)
        for zombie in self.zombies:
            zombie.update(dt, self)
        for bullet in self.bullets:
            bullet.update(dt, self)
        for laser in self.lasers:
            laser.update(dt)
        for acid in self.acid_projectiles:
            acid.update(dt, self)
        for pool in self.poison_pools:
            pool.update(dt, self)
        for gold in self.gold_drops:
            gold.update(dt, self)
        for particle in self.particles:
            particle.update(dt)
        for floating in self.floating_texts:
            floating.update(dt)

        self.zombies = [z for z in self.zombies if z.alive]
        self.bullets = [b for b in self.bullets if b.alive]
        self.lasers = [l for l in self.lasers if l.alive]
        self.acid_projectiles = [a for a in self.acid_projectiles if a.alive]
        self.poison_pools = [p for p in self.poison_pools if p.alive]
        self.structures = [s for s in self.structures if s.alive]
        self.gold_drops = [g for g in self.gold_drops if g.alive]
        self.particles = [p for p in self.particles if p.alive]
        self.floating_texts = [f for f in self.floating_texts if f.alive]

    def draw_bar(self, surface, rect, pct, fill, back=(52, 38, 43)):
        pygame.draw.rect(surface, back, rect)
        pygame.draw.rect(surface, fill, (rect.x, rect.y, int(rect.w * clamp(pct, 0, 1)), rect.h))
        pygame.draw.rect(surface, COLORS["hud_line"], rect, 1)

    def draw_world(self):
        world = self.world_surface
        self.tile_map.draw(world)
        for pool in self.poison_pools:
            pool.draw(world)
        for gold in self.gold_drops:
            gold.draw(world)
        for structure in self.structures:
            structure.draw(world)
        for bullet in self.bullets:
            bullet.draw(world)
        for laser in self.lasers:
            laser.draw(world)
        for acid in self.acid_projectiles:
            acid.draw(world)
        for zombie in self.zombies:
            zombie.draw(world, self.sprites)
        self.player.draw(world, self.sprites, self.mouse_world())
        for particle in self.particles:
            particle.draw(world)
        for floating in self.floating_texts:
            floating.draw(world, self.tiny_font)
        self.draw_build_preview()
        scaled_world = pygame.transform.scale(world, self.world_rect.size)
        self.screen.blit(scaled_world, self.world_rect)

    def draw_build_preview(self):
        if self.build_mode is None:
            return
        mouse_world = self.mouse_world()
        if mouse_world is None:
            return
        cell = self.tile_map.world_to_cell(mouse_world)
        rect = pygame.Rect(cell[0] * TILE, cell[1] * TILE, TILE, TILE)
        valid = (
            self.tile_map.in_bounds(cell)
            and not self.tile_map.is_wall(cell)
            and cell not in self.blocked_cells()
            and self.tile_map.cell_center(cell).distance_to(self.player.pos) >= 40
            and self.can_afford(self.structure_cost(self.build_mode))
        )
        overlay = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        overlay.fill((82, 215, 126, 120) if valid else (230, 70, 70, 130))
        self.world_surface.blit(overlay, rect)

    def draw_text(self, text, x, y, color=None, font=None):
        color = color or COLORS["text"]
        font = font or self.font
        self.screen.blit(font.render(text, True, color), (x, y))

    def draw_hud(self):
        sw, sh, s = self.screen_w, self.screen_h, self.ui_scale
        top = pygame.Rect(self.margin, self.margin, sw - self.margin * 2, max(46, int(62 * s)))
        self.draw_panel(top, alpha=205)
        left_x = top.x + max(14, int(22 * s))
        self.draw_text(self.t("title"), left_x, top.y + max(8, int(14 * s)), COLORS["gold"], self.font)
        alive = len([z for z in self.zombies if z.alive])
        queued = len(self.spawn_queue)
        self.draw_text(
            f"{self.t('wave')}: {self.wave if self.wave else 1}   {self.t('enemies')}: {alive} (+{queued})",
            left_x + int(330 * s),
            top.y + max(10, int(16 * s)),
            COLORS["text"],
            self.small_font,
        )
        self.draw_text(
            f"{self.t('gold')}: {self.gold_text()}   {self.t('kills')}: {self.player.kills}   {self.t('score')}: {self.player.score}",
            left_x + int(690 * s),
            top.y + max(10, int(16 * s)),
            COLORS["gold"],
            self.small_font,
        )
        if self.dev_mode:
            self.draw_text("DEV", left_x + int(1010 * s), top.y + max(10, int(16 * s)), COLORS["orange"], self.small_font)
        if not self.wave_active and self.wave > 0 and self.wave_break_timer > 0:
            timer_text = f"{self.t('next_wave')}: {math.ceil(self.wave_break_timer)}s"
            self.draw_text(timer_text, left_x + int(1110 * s), top.y + max(10, int(16 * s)), COLORS["orange"], self.small_font)

        bar_w = min(int(540 * s), max(240, int(sw * 0.42)))
        hp_rect = pygame.Rect(sw // 2 - bar_w // 2, top.bottom + max(8, int(12 * s)), bar_w, max(14, int(22 * s)))
        xp_rect = pygame.Rect(hp_rect.x, hp_rect.bottom + max(6, int(10 * s)), bar_w, max(10, int(16 * s)))
        self.draw_text("HP", hp_rect.x - 44, hp_rect.y - 3, COLORS["text"], self.small_font)
        self.draw_bar(self.screen, hp_rect, self.player.hp / self.player.max_hp, COLORS["green"])
        self.draw_text("XP", xp_rect.x - 44, xp_rect.y - 4, COLORS["text"], self.small_font)
        self.draw_bar(self.screen, xp_rect, self.player.xp / self.player.next_xp, COLORS["cyan"], (32, 39, 48))
        self.draw_text(f"Lv {self.player.level}", hp_rect.right + 18, hp_rect.y - 2, COLORS["cyan"], self.small_font)

        pause_rect = pygame.Rect(sw - self.margin - int(132 * s), hp_rect.y, int(132 * s), max(38, int(46 * s)))
        self.draw_button("pause_toggle", pause_rect, self.t("pause"), font=self.small_font)

        panel = pygame.Rect(0, sh - self.bottom_ui_h, sw, self.bottom_ui_h)
        self.draw_panel(panel, color=(16, 18, 24), alpha=222, border=False)
        pygame.draw.line(self.screen, COLORS["hud_line"], (0, panel.y), (sw, panel.y), 2)

        weapon = self.player.weapon
        weapon_damage = int(weapon.damage * (1 + self.player.damage_bonus) * self.difficulty_cfg()["player_damage"])
        fire_rate = (1 + self.player.fire_rate_bonus) / weapon.cooldown
        slot_w = int(188 * s)
        slot_h = min(int(104 * s), self.bottom_ui_h - max(22, int(42 * s)))
        gap = max(8, int(18 * s))
        total_w = slot_w * 4 + gap * 3
        if total_w > sw - self.margin * 2:
            slot_w = max(118, int((sw - self.margin * 2 - gap * 3) / 4))
            total_w = slot_w * 4 + gap * 3
        start_x = sw // 2 - total_w // 2
        y = panel.y + max(10, (self.bottom_ui_h - slot_h) // 2)

        if start_x > 330 * s:
            self.draw_text(f"{weapon.tier_name} Lv {weapon.level}", self.margin + 18, panel.y + int(20 * s), COLORS["cyan"], self.font)
            self.draw_text(
                f"DMG {weapon_damage} | Shots {weapon.bullet_count} | Pierce {weapon.pierce} | Rate {fire_rate:.1f}/s",
                self.margin + 18,
                panel.y + int(56 * s),
                COLORS["muted"],
                self.small_font,
            )
            self.draw_text(
                f"{CHARACTERS[self.player.character_id]['label']} | {DIFFICULTIES[self.difficulty_id]['label']} | Armor {self.player.armor} | Range {weapon.bullet_range}",
                self.margin + 18,
                panel.y + int(86 * s),
                COLORS["muted"],
                self.small_font,
            )

        upgrade_value = "MAX" if weapon.is_maxed else ("FREE" if self.dev_mode else f"{weapon.upgrade_cost}g")
        self.draw_hotbar_slot("hotbar_upgrade", pygame.Rect(start_x, y, slot_w, slot_h), "1", self.t("upgrade"), upgrade_value, COLORS["gold"], active=weapon.is_maxed)
        turret_value = "FREE" if self.dev_mode else f"{self.structure_cost('turret')}g"
        fence_value = "FREE" if self.dev_mode else f"{self.structure_cost('fence')}g"
        self.draw_hotbar_slot("hotbar_turret", pygame.Rect(start_x + (slot_w + gap), y, slot_w, slot_h), "2", self.t("turret"), turret_value, COLORS["cyan"], active=self.build_mode == "turret")
        self.draw_hotbar_slot("hotbar_fence", pygame.Rect(start_x + (slot_w + gap) * 2, y, slot_w, slot_h), "3", self.t("fence"), fence_value, COLORS["orange"], active=self.build_mode == "fence")
        auto_text = self.t("on") if self.auto_fire else self.t("off")
        self.draw_hotbar_slot("auto_toggle_game", pygame.Rect(start_x + (slot_w + gap) * 3, y, slot_w, slot_h), "F", self.t("auto_fire"), auto_text, COLORS["green"], active=self.auto_fire)

        mode = self.build_mode.upper() if self.build_mode else self.t("off")
        if sw - (start_x + total_w) > 320 * s:
            right_x = sw - int(520 * s)
            self.draw_text(f"Build: {mode}", right_x, panel.y + int(26 * s), COLORS["orange"] if self.build_mode else COLORS["muted"], self.small_font)
            self.draw_text("WASD | Mouse aim | Space wave | P pause", right_x, panel.y + int(64 * s), COLORS["muted"], self.small_font)
            self.draw_text(self.t("auto_hint"), right_x, panel.y + int(96 * s), COLORS["muted"], self.tiny_font)

    def draw_hotbar_slot(self, key, rect, number, label, value, accent, active=False):
        mouse = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse)
        fill = (47, 55, 62) if active else ((45, 48, 58) if hover else (30, 34, 42))
        pygame.draw.rect(self.screen, fill, rect, border_radius=8)
        pygame.draw.rect(self.screen, accent if active else COLORS["hud_line"], rect, 2, border_radius=8)
        badge = pygame.Rect(rect.centerx - 22, rect.y + 10, 44, 34)
        pygame.draw.rect(self.screen, accent, badge, border_radius=6)
        self.draw_text_center(number, badge, (15, 18, 22), self.font)
        self.draw_text_center(label, pygame.Rect(rect.x + 8, rect.y + 48, rect.w - 16, 26), COLORS["text"], self.small_font)
        self.draw_text_center(value, pygame.Rect(rect.x + 8, rect.y + 76, rect.w - 16, 22), accent, self.small_font)
        self.ui_buttons[key] = rect

    def draw_overlay(self):
        sw, sh = self.screen_w, self.screen_h
        if self.message_timer > 0 and self.message:
            image = self.font.render(self.message, True, COLORS["text"])
            rect = image.get_rect(center=(sw // 2, self.top_ui_h + 20))
            box = rect.inflate(28, 14)
            pygame.draw.rect(self.screen, (25, 27, 32), box)
            pygame.draw.rect(self.screen, COLORS["hud_line"], box, 1)
            self.screen.blit(image, rect)
        if not self.wave_active and not self.spawn_queue and not self.game_over:
            if self.wave > 0 and self.wave_break_timer > 0:
                hint = f"Next wave in {math.ceil(self.wave_break_timer)}s - press SPACE to skip"
            else:
                hint = self.t("start_hint")
            image = self.font.render(hint, True, COLORS["gold"])
            rect = image.get_rect(center=(sw // 2, sh - self.bottom_ui_h - max(18, int(28 * self.ui_scale))))
            self.screen.blit(image, rect)
        if self.game_over:
            veil = pygame.Surface((sw, sh), pygame.SRCALPHA)
            veil.fill((0, 0, 0, 165))
            self.screen.blit(veil, (0, 0))
            title = self.big_font.render("GAME OVER", True, COLORS["red"])
            title_rect = title.get_rect(center=(sw // 2, sh // 2 - int(38 * self.ui_scale)))
            self.screen.blit(title, title_rect)
            sub = self.font.render("Press ENTER to restart", True, COLORS["text"])
            self.screen.blit(sub, sub.get_rect(center=(sw // 2, sh // 2 + int(28 * self.ui_scale))))
        if self.paused:
            self.draw_pause_overlay()

    def draw_pause_overlay(self):
        sw, sh, s = self.screen_w, self.screen_h, self.ui_scale
        veil = pygame.Surface((sw, sh), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 150))
        self.screen.blit(veil, (0, 0))
        box_w = min(int(420 * s), sw - self.margin * 2)
        box_h = min(int(380 * s), sh - self.margin * 2)
        box = pygame.Rect(sw // 2 - box_w // 2, sh // 2 - box_h // 2, box_w, box_h)
        self.draw_panel(box, alpha=235)
        self.draw_text_center(self.t("paused"), pygame.Rect(box.x, box.y + int(32 * s), box.w, int(70 * s)), COLORS["gold"], self.big_font)
        button_w = min(int(280 * s), box.w - int(90 * s))
        button_h = max(42, int(56 * s))
        bx = box.centerx - button_w // 2
        self.draw_button("pause_resume", pygame.Rect(bx, box.y + int(130 * s), button_w, button_h), self.t("resume"))
        self.draw_button("pause_options", pygame.Rect(bx, box.y + int(204 * s), button_w, button_h), self.t("options"))
        self.draw_button("pause_menu", pygame.Rect(bx, box.y + int(278 * s), button_w, button_h), self.t("main_menu"))

    def draw_menu(self):
        sw, sh, s = self.screen_w, self.screen_h, self.ui_scale
        self.screen.fill((12, 14, 18))
        grid = max(32, int(48 * s))
        for y in range(0, sh, grid):
            pygame.draw.line(self.screen, (24, 28, 34), (0, y), (sw, y), 1)
        for x in range(0, sw, grid):
            pygame.draw.line(self.screen, (24, 28, 34), (x, 0), (x, sh), 1)
        title_rect = pygame.Rect(0, int(170 * s), sw, int(110 * s))
        self.draw_text_center(self.t("title"), title_rect, COLORS["gold"], self.title_font)
        self.draw_text_center("2D RPG SURVIVAL", pygame.Rect(0, int(282 * s), sw, int(40 * s)), COLORS["cyan"], self.font)
        button_w = min(int(340 * s), sw - self.margin * 2)
        button_h = max(48, int(66 * s))
        bx = sw // 2 - button_w // 2
        y0 = int(390 * s)
        step = int(88 * s)
        self.draw_button("menu_start", pygame.Rect(bx, y0, button_w, button_h), self.t("start"), font=self.font)
        self.draw_button("menu_options", pygame.Rect(bx, y0 + step, button_w, button_h), self.t("options"), font=self.font)
        self.draw_button("menu_exit", pygame.Rect(bx, y0 + step * 2, button_w, button_h), self.t("exit"), font=self.font)

    def draw_setup(self):
        sw, sh, s = self.screen_w, self.screen_h, self.ui_scale
        self.screen.fill((12, 14, 18))
        grid = max(32, int(48 * s))
        for y in range(0, sh, grid):
            pygame.draw.line(self.screen, (24, 28, 34), (0, y), (sw, y), 1)
        for x in range(0, sw, grid):
            pygame.draw.line(self.screen, (24, 28, 34), (x, 0), (x, sh), 1)

        self.draw_text_center(self.t("setup_title"), pygame.Rect(0, int(112 * s), sw, int(88 * s)), COLORS["gold"], self.big_font)
        self.draw_text_center(self.t("title"), pygame.Rect(0, int(196 * s), sw, int(40 * s)), COLORS["cyan"], self.font)

        box_w = min(int(940 * s), sw - self.margin * 2)
        box_h = min(int(640 * s), sh - int(280 * s))
        box = pygame.Rect(sw // 2 - box_w // 2, int(285 * s), box_w, box_h)
        self.draw_panel(box, alpha=224)

        option_h = max(38, int(48 * s))
        gap = max(8, int(12 * s))
        row_w = min(int(780 * s), box.w - int(96 * s))
        item_w = int((row_w - gap * 3) / 4)
        row_x = box.centerx - row_w // 2
        y = box.y + int(64 * s)

        self.draw_text_center(self.t("difficulty"), pygame.Rect(box.x, y - int(38 * s), box.w, int(28 * s)), COLORS["cyan"], self.small_font)
        for index, difficulty_id in enumerate(DIFFICULTIES):
            rect = pygame.Rect(row_x + index * (item_w + gap), y, item_w, option_h)
            self.draw_button(
                f"difficulty_{difficulty_id}",
                rect,
                DIFFICULTIES[difficulty_id]["label"],
                active=self.difficulty_id == difficulty_id,
                font=self.small_font,
            )

        y += option_h + int(78 * s)
        self.draw_text_center(self.t("character"), pygame.Rect(box.x, y - int(38 * s), box.w, int(28 * s)), COLORS["cyan"], self.small_font)
        for index, character_id in enumerate(CHARACTERS):
            rect = pygame.Rect(row_x + index * (item_w + gap), y, item_w, option_h)
            self.draw_button(
                f"character_{character_id}",
                rect,
                CHARACTERS[character_id]["label"],
                active=self.character_id == character_id,
                font=self.small_font,
            )

        y += option_h + int(70 * s)
        turret = self.structure_stats("turret")
        fence = self.structure_stats("fence")
        summary_w = min(int(650 * s), box.w - int(96 * s))
        summary = pygame.Rect(box.centerx - summary_w // 2, y, summary_w, max(86, int(104 * s)))
        pygame.draw.rect(self.screen, (28, 32, 39), summary, border_radius=8)
        pygame.draw.rect(self.screen, COLORS["hud_line"], summary, 1, border_radius=8)
        self.draw_text_center(self.t("structures"), pygame.Rect(summary.x, summary.y + int(8 * s), summary.w, int(28 * s)), COLORS["gold"], self.small_font)
        self.draw_text_center(
            f"Turret {self.structure_cost('turret')}g | HP {turret['hp']} | DMG {turret['damage']} | RNG {turret['range']}",
            pygame.Rect(summary.x, summary.y + int(38 * s), summary.w, int(26 * s)),
            COLORS["text"],
            self.small_font,
        )
        self.draw_text_center(
            f"Fence {self.structure_cost('fence')}g | HP {fence['hp']} | Repair {self.repair_cost()}g",
            pygame.Rect(summary.x, summary.y + int(66 * s), summary.w, int(26 * s)),
            COLORS["muted"],
            self.small_font,
        )

        button_w = min(int(280 * s), box.w - int(120 * s))
        button_h = max(46, int(58 * s))
        bottom_y = box.bottom - int(86 * s)
        total_w = button_w * 2 + int(24 * s)
        left_x = box.centerx - total_w // 2
        self.draw_button("setup_back", pygame.Rect(left_x, bottom_y, button_w, button_h), self.t("back"), font=self.font)
        self.draw_button("setup_begin", pygame.Rect(left_x + button_w + int(24 * s), bottom_y, button_w, button_h), self.t("begin_run"), active=True, font=self.font)

    def draw_options(self):
        sw, sh, s = self.screen_w, self.screen_h, self.ui_scale
        self.screen.fill((13, 15, 20))
        box_w = min(int(720 * s), sw - self.margin * 2)
        box_h = min(int(690 * s), sh - self.margin * 2)
        box = pygame.Rect(sw // 2 - box_w // 2, sh // 2 - box_h // 2, box_w, box_h)
        self.draw_panel(box, alpha=232)
        self.draw_text_center(self.t("options"), pygame.Rect(box.x, box.y + int(26 * s), box.w, int(70 * s)), COLORS["gold"], self.big_font)
        y = box.y + int(132 * s)
        self.draw_option_row(box, y, self.t("music"), f"{self.music_volume}%", "music_down", "music_up")
        y += int(95 * s)
        self.draw_option_row(box, y, self.t("sfx"), f"{self.sfx_volume}%", "sfx_down", "sfx_up")
        y += int(105 * s)
        lang_label = "Tieng Viet" if self.language == "vi" else "English"
        self.draw_text(self.t("language"), box.x + int(82 * s), y + int(14 * s), COLORS["text"], self.font)
        self.draw_button("lang_toggle", pygame.Rect(box.right - int(330 * s), y, int(210 * s), max(42, int(54 * s))), lang_label, active=True, font=self.small_font)
        y += int(95 * s)
        auto_label = self.t("on") if self.auto_fire else self.t("off")
        self.draw_text(self.t("auto_fire"), box.x + int(82 * s), y + int(14 * s), COLORS["text"], self.font)
        self.draw_button("auto_toggle", pygame.Rect(box.right - int(330 * s), y, int(210 * s), max(42, int(54 * s))), auto_label, active=self.auto_fire, font=self.small_font)
        y += int(92 * s)
        dev_label = self.t("on") if self.dev_mode else self.t("off")
        self.draw_text(self.t("dev_mode"), box.x + int(82 * s), y + int(14 * s), COLORS["text"], self.font)
        self.draw_button("dev_toggle", pygame.Rect(box.right - int(330 * s), y, int(210 * s), max(42, int(54 * s))), dev_label, active=self.dev_mode, font=self.small_font)
        back_w = min(int(300 * s), box.w - int(120 * s))
        self.draw_button("options_back", pygame.Rect(box.centerx - back_w // 2, box.bottom - int(96 * s), back_w, max(46, int(58 * s))), self.t("back"), font=self.font)

    def draw_option_row(self, box, y, label, value, down_key, up_key):
        s = self.ui_scale
        self.draw_text(label, box.x + int(82 * s), y + int(14 * s), COLORS["text"], self.font)
        button = max(42, int(54 * s))
        controls_x = box.right - int(330 * s)
        self.draw_button(down_key, pygame.Rect(controls_x, y, button, button), "-", font=self.font)
        self.draw_text_center(value, pygame.Rect(controls_x + button + int(12 * s), y, int(88 * s), button), COLORS["cyan"], self.font)
        self.draw_button(up_key, pygame.Rect(controls_x + button + int(112 * s), y, button, button), "+", font=self.font)

    def draw(self):
        self.ui_buttons = {}
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "setup":
            self.draw_setup()
        elif self.state == "options":
            self.draw_options()
        else:
            self.screen.fill((8, 10, 14))
            self.draw_world()
            self.draw_hud()
            self.draw_overlay()
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000
            running = self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()

    def smoke(self, frames=180):
        self.state = "playing"
        self.start_wave()
        for _ in range(frames):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
            self.update(1 / FPS)
            self.draw()
        return True


def parse_args():
    parser = argparse.ArgumentParser(description="Pixel Zombie Siege")
    parser.add_argument("--smoke", action="store_true", help="Run a short headless startup check.")
    return parser.parse_args()


def main():
    args = parse_args()
    game = Game()
    if args.smoke:
        ok = game.smoke()
        pygame.quit()
        print("Smoke test passed" if ok else "Smoke test stopped")
        return
    game.run()


if __name__ == "__main__":
    main()
