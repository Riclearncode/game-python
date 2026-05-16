import argparse
from collections import deque
import heapq
import math
import os
import random
import sys
from dataclasses import dataclass

from ui_manager import UIManager


if "--smoke" in sys.argv:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

try:
    import pygame
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing dependency: pygame-ce\n"
        "Install it with: py -m pip install -r requirements.txt"
    ) from exc

from map_manager import MapManager


Vec2 = pygame.math.Vector2

TILE = 32
PLAYER_HEAL_COOLDOWN = 24.0
PLAYER_HEAL_RATIO = 0.34
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

MAPS = {
    "warehouse": MAP_ROWS,
    "crossfire": [
        "############################",
        "#............##............#",
        "#............##............#",
        "#..####....................#",
        "#.................####.....#",
        "#.....##..............##...#",
        "#.....##..............##...#",
        "#..........................#",
        "#..........###.###.........#",
        "#..........#.....#.........#",
        "#..........#.....#.........#",
        "#..........###.###.........#",
        "#..........................#",
        "#...##..............##.....#",
        "#...##..............##.....#",
        "#.....####........####.....#",
        "#..........................#",
        "#....###............###....#",
        "#..........................#",
        "#............##............#",
        "#............##............#",
        "############################",
    ],
    "split": [
        "############################",
        "#..........#....#..........#",
        "#..........#....#..........#",
        "#..####....#....#....####..#",
        "#..........#....#..........#",
        "#..........#....#..........#",
        "#..........................#",
        "#....##..............##....#",
        "#....##....######....##....#",
        "#..........................#",
        "#..##..................##..#",
        "#..##.....###..###.....##..#",
        "#..........................#",
        "#....##....######....##....#",
        "#....##..............##....#",
        "#..........................#",
        "#..........#....#..........#",
        "#..####....#....#....####..#",
        "#..........#....#..........#",
        "#..........#....#..........#",
        "#..........................#",
        "############################",
    ],
}
MAP_ORDER = ("warehouse", "crossfire", "split")
MAP_NAMES = {
    "warehouse": {"en": "Warehouse", "vi": "Nhà kho"},
    "crossfire": {"en": "Crossfire Yard", "vi": "Sân giao tranh"},
    "split": {"en": "Split Ruins", "vi": "Tàn tích chia cắt"},
}
MAP_DESCRIPTIONS = {
    "warehouse": {
        "en": "Metal floor, storage walls, balanced lanes.",
        "vi": "Sàn kim loại, tường kho, lối đi cân bằng.",
    },
    "crossfire": {
        "en": "Open combat yard with barricades and fire lanes.",
        "vi": "Sân giao tranh rộng với chướng ngại và đường bắn chéo.",
    },
    "split": {
        "en": "Mossy ruins split by broken stone passages.",
        "vi": "Tàn tích phủ rêu với các lối đá bị chia cắt.",
    },
}
MAP_THEMES = {
    "warehouse": {
        "bg": (18, 19, 21),
        "floor_a": (43, 45, 43),
        "floor_b": (35, 37, 36),
        "grid": (57, 60, 58),
        "wall_dark": (30, 27, 31),
        "wall": (88, 84, 92),
        "wall_light": (142, 135, 145),
        "accent": (245, 196, 66),
        "prop_a": (122, 84, 48),
        "prop_b": (74, 78, 84),
        "prop_c": (38, 115, 126),
    },
    "crossfire": {
        "bg": (22, 22, 20),
        "floor_a": (58, 51, 43),
        "floor_b": (45, 45, 40),
        "grid": (74, 66, 54),
        "wall_dark": (48, 41, 38),
        "wall": (112, 101, 87),
        "wall_light": (171, 153, 116),
        "accent": (229, 91, 58),
        "prop_a": (202, 162, 74),
        "prop_b": (79, 67, 56),
        "prop_c": (146, 56, 48),
    },
    "split": {
        "bg": (14, 22, 19),
        "floor_a": (36, 52, 43),
        "floor_b": (30, 44, 37),
        "grid": (50, 69, 58),
        "wall_dark": (30, 36, 35),
        "wall": (72, 86, 82),
        "wall_light": (119, 137, 112),
        "accent": (96, 205, 119),
        "prop_a": (70, 127, 73),
        "prop_b": (98, 85, 74),
        "prop_c": (50, 120, 96),
    },
}

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
TURRET_LIMITS = {
    "easy": 5,
    "normal": 4,
    "hard": 3,
    "nightmare": 2,
}
TITAN_LEAP_COOLDOWNS = {
    "easy": 18.0,
    "normal": 16.0,
    "hard": 14.0,
    "nightmare": 12.0,
}
TITAN_STUCK_LEAP_SECONDS = {
    "easy": 5.0,
    "normal": 4.2,
    "hard": 3.6,
    "nightmare": 3.0,
}
TITAN_LEAP_MIN_PLAYER_DISTANCE = 180
TITAN_STOMP_WARNING_SECONDS = 0.78
TITAN_CHARGE_MAX_STRUCTURE_HITS = 2
FENCE_TIER_STATS = {
    1: {"hp": 300, "slow": 0.80, "damage_reduction": 0.0, "spike_damage": 0, "electric_cooldown": 0.0, "titan_guard": False},
    2: {"hp": 430, "slow": 0.72, "damage_reduction": 0.08, "spike_damage": 0, "electric_cooldown": 0.0, "titan_guard": False},
    3: {"hp": 560, "slow": 0.66, "damage_reduction": 0.12, "spike_damage": 7, "electric_cooldown": 0.0, "titan_guard": False},
    4: {"hp": 700, "slow": 0.60, "damage_reduction": 0.16, "spike_damage": 10, "electric_cooldown": 0.0, "titan_guard": True},
    5: {"hp": 840, "slow": 0.56, "damage_reduction": 0.20, "spike_damage": 13, "electric_cooldown": 6.0, "titan_guard": True},
}
MAX_FENCE_LEVEL = max(FENCE_TIER_STATS)

assert all(len(row) == GRID_W for rows in MAPS.values() for row in rows), "Every map row must have the same width."
assert all(len(rows) == GRID_H for rows in MAPS.values()), "Every map must have the same height."


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
    "purple": (166, 116, 224),
}

TEXT = {
    "en": {
        "title": "PIXEL ZOMBIE SIEGE",
        "start": "START",
        "options": "OPTIONS",
        "exit": "EXIT",
        "back": "BACK",
        "begin_run": "BEGIN RUN",
        "next": "NEXT",
        "select_difficulty": "Choose difficulty",
        "select_map": "Choose map",
        "select_character": "Choose character",
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
        "map": "Map",
        "structures": "Structures",
        "powerup": "Power-up",
        "dash": "Dash",
        "heal": "Heal",
        "info": "Info",
        "ready": "Ready",
        "full": "Full",
        "teleport": "TELEPORT",
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
        "gate": "Gate",
        "repair": "Repair",
        "hp": "HP",
        "xp": "XP",
        "level_short": "Lv",
        "max": "MAX",
        "free": "FREE",
        "dmg": "DMG",
        "rate": "Rate",
        "range_short": "RNG",
        "shots": "Shots",
        "pierce": "Pierce",
        "ammo": "Ammo",
        "reload": "Reload",
        "reload_action": "Reload",
        "reloading": "Reloading",
        "armor": "Armor",
        "magnet": "Magnet",
        "cost": "Cost",
        "buffs": "Buffs",
        "turrets": "Turrets",
        "close": "close",
        "cancel_build": "cancel build",
        "wave_key": "Space wave",
        "repair_key": "E repair",
        "build": "Build",
        "game_over": "GAME OVER",
        "restart_hint": "Press ENTER to restart",
        "subtitle": "2D RPG SURVIVAL",
        "start_hint": "Press SPACE to start the next wave",
        "skip_hint": "SPACE skips the countdown",
        "auto_hint": "Auto-fire targets the nearest zombie in range.",
        "next_wave_in": "Next wave in {seconds}s - press SPACE to skip",
        "press_space_wave": "Press SPACE to start wave 1",
        "wave_clear": "Wave clear! Bonus +{reward} gold",
        "wave_label": "Wave {wave}",
        "wave_start_banner": "WAVE {wave} START",
        "titan_approaching": "TITAN APPROACHING!",
        "level_up": "LEVEL {level}",
        "level_message": "Level {level}: {perks}",
        "turret_limit": "Turret limit {count}/{limit}",
        "cannot_build_wall": "Cannot build on wall",
        "tile_occupied": "Tile occupied",
        "too_close_player": "Too close to player",
        "not_enough_gold": "Not enough gold",
        "build_cannot_place": "Cannot place here",
        "would_trap_player": "Would trap player",
        "repair_prompt": "Press E to repair",
        "built": "Built {name}",
        "no_damaged_structure": "No damaged structure nearby",
        "move_closer_repair": "Move closer to repair",
        "need_gold_repair": "Need {cost} gold to repair",
        "weapon_max": "{weapon} is MAX level",
        "need_gold": "Need {cost} gold",
        "heal_ready_message": "Med injector ready",
        "heal_used": "Healed +{amount} HP",
        "heal_full": "HP is already full",
        "heal_cooldown": "Heal cooldown {seconds:.1f}s",
        "reload_full": "Magazine is already full",
        "reload_started": "Reloading",
        "weapon_evolved": "Weapon evolved: {weapon}",
        "weapon_upgraded": "{weapon} upgraded to Lv {level}",
        "dev_on": "Developer Mode: ON",
        "dev_off": "Developer Mode: OFF",
        "build_mode": "Build mode: {name}",
        "elite_incoming": "Elite zombie incoming!",
        "boomer_bile": "Boomer bile! Zombies are enraged!",
        "titan_vault": "Titan vaults the wall!",
        "titan_charge": "Titan charge!",
        "titan_roar": "Titan roar summons infected!",
        "elite_down": "ELITE DOWN",
        "broken": "BROKEN",
        "repair_float": "+repair",
        "fence_level": "Fence Lv {level}",
        "fence_upgrade": "Upgrade fence",
        "fence_upgraded": "Fence upgraded to Lv {level}",
        "fence_max": "Fence already at max tech",
        "need_gold_fence_upgrade": "Need {cost} gold to upgrade fence",
        "move_closer_fence": "Move closer to a fence",
        "perks_base": "Base survivor",
        "perk_hp": "+HP",
        "perk_damage": "+6% damage",
        "perk_fire_rate": "+5% fire rate",
        "perk_magnet_gold": "+magnet/gold",
        "perk_armor_regen": "+armor/regen",
        "perk_armor_magnet": "+armor/magnet",
    },
    "vi": {
        "title": "PIXEL ZOMBIE SIEGE",
        "start": "BẮT ĐẦU",
        "options": "TÙY CHỌN",
        "exit": "THOÁT",
        "back": "QUAY LẠI",
        "begin_run": "VÀO TRẬN",
        "next": "TIẾP",
        "select_difficulty": "Chọn độ khó",
        "select_map": "Chọn bản đồ",
        "select_character": "Chọn nhân vật",
        "setup_title": "CHUẨN BỊ",
        "resume": "TIẾP TỤC",
        "main_menu": "MENU CHÍNH",
        "paused": "TẠM DỪNG",
        "music": "Nhạc",
        "sfx": "Hiệu ứng",
        "language": "Ngôn ngữ",
        "auto_fire": "Tự động bắn",
        "dev_mode": "Chế độ nhà phát triển",
        "infinite": "VÔ HẠN",
        "difficulty": "Độ khó",
        "character": "Nhân vật",
        "map": "Bản đồ",
        "structures": "Công trình",
        "powerup": "Vật phẩm",
        "dash": "Lướt",
        "heal": "Hồi máu",
        "info": "Chỉ số",
        "ready": "Sẵn sàng",
        "full": "Đầy",
        "teleport": "DỊCH CHUYỂN",
        "on": "BẬT",
        "off": "TẮT",
        "wave": "Đợt",
        "gold": "Vàng",
        "kills": "Hạ gục",
        "score": "Điểm",
        "enemies": "Quái",
        "next_wave": "Đợt tiếp",
        "pause": "Dừng",
        "upgrade": "Nâng cấp",
        "turret": "Trụ súng",
        "fence": "Hàng rào",
        "gate": "Cổng",
        "repair": "Sửa",
        "hp": "Máu",
        "xp": "KN",
        "level_short": "Cấp",
        "max": "TỐI ĐA",
        "free": "MIỄN PHÍ",
        "dmg": "ST",
        "rate": "Tốc độ",
        "range_short": "Tầm",
        "shots": "Đạn",
        "pierce": "Xuyên",
        "ammo": "Đạn",
        "reload": "Nạp",
        "reload_action": "Nạp đạn",
        "reloading": "Đang nạp",
        "armor": "Giáp",
        "magnet": "Hút vàng",
        "cost": "Giá",
        "buffs": "Buff",
        "turrets": "Trụ",
        "close": "đóng",
        "cancel_build": "hủy xây",
        "wave_key": "Space gọi đợt",
        "repair_key": "E sửa",
        "build": "Xây",
        "game_over": "THẤT BẠI",
        "restart_hint": "Nhấn ENTER để chơi lại",
        "subtitle": "SINH TỒN RPG 2D",
        "start_hint": "Nhấn SPACE để bắt đầu đợt tiếp theo",
        "skip_hint": "SPACE bỏ qua đếm ngược",
        "auto_hint": "Tự động bắn sẽ ngắm zombie gần nhất trong tầm.",
        "next_wave_in": "Đợt tiếp sau {seconds}s - nhấn SPACE để bỏ qua",
        "press_space_wave": "Nhấn SPACE để bắt đầu đợt 1",
        "wave_clear": "Dọn sạch đợt! Thưởng +{reward} vàng",
        "wave_label": "Đợt {wave}",
        "wave_start_banner": "ĐỢT {wave} BẮT ĐẦU",
        "titan_approaching": "TITAN ĐANG TỚI!",
        "level_up": "LÊN CẤP {level}",
        "level_message": "Cấp {level}: {perks}",
        "turret_limit": "Giới hạn trụ {count}/{limit}",
        "cannot_build_wall": "Không thể xây trên tường",
        "tile_occupied": "Ô này đã bị chiếm",
        "too_close_player": "Quá gần người chơi",
        "not_enough_gold": "Không đủ vàng",
        "build_cannot_place": "Không thể đặt ở đây",
        "would_trap_player": "Sẽ nhốt người chơi",
        "repair_prompt": "Nhấn E để sửa",
        "built": "Đã xây {name}",
        "no_damaged_structure": "Không có công trình hư hại gần đây",
        "move_closer_repair": "Đến gần hơn để sửa",
        "need_gold_repair": "Cần {cost} vàng để sửa",
        "weapon_max": "{weapon} đã đạt cấp tối đa",
        "need_gold": "Cần {cost} vàng",
        "heal_ready_message": "Ống tiêm hồi máu đã sẵn sàng",
        "heal_used": "Hồi +{amount} máu",
        "heal_full": "Máu đã đầy",
        "heal_cooldown": "Hồi máu còn {seconds:.1f}s",
        "reload_full": "Băng đạn đã đầy",
        "reload_started": "Đang nạp đạn",
        "weapon_evolved": "Vũ khí tiến hóa: {weapon}",
        "weapon_upgraded": "{weapon} nâng lên cấp {level}",
        "dev_on": "Chế độ nhà phát triển: BẬT",
        "dev_off": "Chế độ nhà phát triển: TẮT",
        "build_mode": "Chế độ xây: {name}",
        "elite_incoming": "Zombie tinh anh đang tới!",
        "boomer_bile": "Dính dịch Boomer! Zombie nổi cuồng!",
        "titan_vault": "Titan vượt tường!",
        "titan_charge": "Titan xung phong!",
        "titan_roar": "Titan gầm gọi thêm quái!",
        "elite_down": "HẠ TINH ANH",
        "broken": "BỊ PHÁ",
        "repair_float": "+sửa",
        "fence_level": "Hàng rào cấp {level}",
        "fence_upgrade": "Nâng hàng rào",
        "fence_upgraded": "Hàng rào lên cấp {level}",
        "fence_max": "Hàng rào đã đạt cấp tối đa",
        "need_gold_fence_upgrade": "Cần {cost} vàng để nâng hàng rào",
        "move_closer_fence": "Đến gần hàng rào hơn",
        "perks_base": "Người sống sót",
        "perk_hp": "+Máu",
        "perk_damage": "+6% sát thương",
        "perk_fire_rate": "+5% tốc bắn",
        "perk_magnet_gold": "+hút vàng/vàng",
        "perk_armor_regen": "+giáp/hồi máu",
        "perk_armor_magnet": "+giáp/hút vàng",
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
        "fence_hp": 1.08,
        "turret_damage": 0.9,
        "turret_range": 0.94,
        "turret_cooldown": 1.08,
        "cost": 0.82,
        "repair_amount": 0.9,
        "repair_cost": 0.82,
    },
    "normal": {
        "hp": 1.0,
        "fence_hp": 1.12,
        "turret_damage": 1.0,
        "turret_range": 1.0,
        "turret_cooldown": 1.0,
        "cost": 1.0,
        "repair_amount": 1.0,
        "repair_cost": 1.0,
    },
    "hard": {
        "hp": 1.24,
        "fence_hp": 1.22,
        "turret_damage": 1.15,
        "turret_range": 1.04,
        "turret_cooldown": 0.93,
        "cost": 1.07,
        "repair_amount": 1.18,
        "repair_cost": 1.05,
    },
    "nightmare": {
        "hp": 1.55,
        "fence_hp": 1.35,
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
        "name": "Glock 17",
        "damage": 18,
        "cooldown": 0.30,
        "min_cooldown": 0.26,
        "magazine": 17,
        "ammo_per_shot": 1,
        "reload_time": 1.12,
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
        "name": "Dual Beretta 92FS",
        "damage": 16,
        "cooldown": 0.24,
        "min_cooldown": 0.20,
        "magazine": 30,
        "ammo_per_shot": 2,
        "reload_time": 1.42,
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
        "name": "HK MP5",
        "damage": 13,
        "cooldown": 0.105,
        "min_cooldown": 0.09,
        "magazine": 30,
        "ammo_per_shot": 1,
        "reload_time": 1.55,
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
        "name": "Mossberg 500",
        "damage": 15,
        "cooldown": 0.58,
        "min_cooldown": 0.50,
        "magazine": 6,
        "ammo_per_shot": 1,
        "reload_time": 1.65,
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
        "name": "M4A1 Carbine",
        "damage": 28,
        "cooldown": 0.16,
        "min_cooldown": 0.135,
        "magazine": 30,
        "ammo_per_shot": 1,
        "reload_time": 1.75,
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
        "name": "Benelli M4",
        "damage": 22,
        "cooldown": 0.48,
        "min_cooldown": 0.42,
        "magazine": 7,
        "ammo_per_shot": 1,
        "reload_time": 1.70,
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
        "name": "XM-LAS Prototype",
        "damage": 54,
        "cooldown": 0.42,
        "min_cooldown": 0.36,
        "magazine": 6,
        "ammo_per_shot": 1,
        "reload_time": 2.20,
        "bullet_speed": 790,
        "range": 500,
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
        "hp": 420,
        "range": 0,
        "damage": 0,
        "cooldown": 0,
    },
    "gate": {
        "label": "Gate",
        "cost": 60,
        "hp": 480,
        "range": 0,
        "damage": 0,
        "cooldown": 0,
    },
}

POWER_UP_TYPES = {
    "medkit": {
        "label": "Medkit",
        "color": (98, 224, 128),
        "accent": (228, 255, 229),
        "message": "Medkit +45 HP",
    },
    "overdrive": {
        "label": "Overdrive",
        "color": (255, 202, 78),
        "accent": (255, 250, 170),
        "message": "Overdrive: more damage and fire rate",
    },
    "shield": {
        "label": "Shield",
        "color": (92, 170, 255),
        "accent": (192, 232, 255),
        "message": "Shield: damage reduced",
    },
    "haste": {
        "label": "Haste",
        "color": (166, 116, 224),
        "accent": (231, 204, 255),
        "message": "Haste: faster movement",
    },
    "shock": {
        "label": "Shock Core",
        "color": (103, 246, 235),
        "accent": (230, 255, 252),
        "message": "Shock Core blasts nearby zombies",
    },
}

DIFFICULTY_NAMES = {
    "easy": {"en": "Easy", "vi": "Dễ"},
    "normal": {"en": "Normal", "vi": "Thường"},
    "hard": {"en": "Hard", "vi": "Khó"},
    "nightmare": {"en": "Nightmare", "vi": "Ác mộng"},
}

CHARACTER_NAMES = {
    "soldier": {"en": "Soldier", "vi": "Lính"},
    "scout": {"en": "Scout", "vi": "Trinh sát"},
    "engineer": {"en": "Engineer", "vi": "Kỹ sư"},
    "tank": {"en": "Tank", "vi": "Đỡ đòn"},
}

CHARACTER_DESCRIPTIONS = {
    "soldier": {"en": "Balanced rifle survivor.", "vi": "Chiến binh cân bằng, dễ làm quen."},
    "scout": {"en": "Fast, agile, strong pickup control.", "vi": "Nhanh nhẹn, nhặt vàng xa, né vây tốt."},
    "engineer": {"en": "Cheaper builds and better defense tempo.", "vi": "Xây rẻ hơn, hợp lối chơi phòng thủ."},
    "tank": {"en": "Slow, armored, survives heavy pressure.", "vi": "Chậm hơn nhưng trâu, chịu áp lực tốt."},
}

WEAPON_NAMES = {
    "Glock 17": {"en": "Glock 17", "vi": "Glock 17"},
    "Dual Beretta 92FS": {"en": "Dual Beretta 92FS", "vi": "Song Beretta 92FS"},
    "HK MP5": {"en": "HK MP5", "vi": "HK MP5"},
    "Mossberg 500": {"en": "Mossberg 500", "vi": "Mossberg 500"},
    "M4A1 Carbine": {"en": "M4A1 Carbine", "vi": "M4A1 Carbine"},
    "Benelli M4": {"en": "Benelli M4", "vi": "Benelli M4"},
    "XM-LAS Prototype": {"en": "XM-LAS Prototype", "vi": "XM-LAS thử nghiệm"},
}

WEAPON_VISUALS = {
    "Glock 17": {
        "body": 13,
        "barrel": 6,
        "stock": 0,
        "height": 6,
        "barrel_width": 3,
        "grip": 8,
        "hand_forward": 7,
        "color": (66, 68, 73),
        "accent": (144, 148, 150),
        "detail": (30, 31, 35),
        "muzzle": (215, 205, 176),
        "kind": "pistol",
    },
    "Dual Beretta 92FS": {
        "body": 13,
        "barrel": 7,
        "stock": 0,
        "height": 6,
        "barrel_width": 3,
        "grip": 8,
        "hand_forward": 7,
        "color": (76, 78, 84),
        "accent": (180, 182, 178),
        "detail": (35, 36, 40),
        "muzzle": (226, 214, 184),
        "kind": "dual_pistol",
    },
    "HK MP5": {
        "body": 18,
        "barrel": 8,
        "stock": 8,
        "height": 8,
        "barrel_width": 4,
        "grip": 10,
        "hand_forward": 8,
        "color": (46, 49, 55),
        "accent": (105, 109, 116),
        "detail": (25, 27, 31),
        "muzzle": (190, 185, 170),
        "kind": "smg",
    },
    "Mossberg 500": {
        "body": 18,
        "barrel": 18,
        "stock": 10,
        "height": 7,
        "barrel_width": 4,
        "grip": 9,
        "hand_forward": 8,
        "color": (65, 68, 72),
        "accent": (119, 76, 43),
        "detail": (38, 39, 42),
        "muzzle": (220, 210, 184),
        "kind": "pump_shotgun",
    },
    "M4A1 Carbine": {
        "body": 20,
        "barrel": 15,
        "stock": 11,
        "height": 8,
        "barrel_width": 4,
        "grip": 11,
        "hand_forward": 9,
        "color": (58, 62, 66),
        "accent": (103, 112, 105),
        "detail": (28, 31, 34),
        "muzzle": (224, 211, 178),
        "kind": "rifle",
    },
    "Benelli M4": {
        "body": 19,
        "barrel": 18,
        "stock": 10,
        "height": 8,
        "barrel_width": 4,
        "grip": 10,
        "hand_forward": 9,
        "color": (55, 58, 62),
        "accent": (95, 100, 103),
        "detail": (27, 29, 32),
        "muzzle": (228, 216, 184),
        "kind": "semi_shotgun",
    },
    "XM-LAS Prototype": {
        "body": 22,
        "barrel": 18,
        "stock": 8,
        "height": 10,
        "barrel_width": 5,
        "grip": 10,
        "hand_forward": 9,
        "color": (62, 66, 82),
        "accent": (80, 225, 245),
        "detail": (24, 28, 44),
        "muzzle": (160, 245, 255),
        "kind": "laser",
    },
}

WEAPON_AUDIO = {
    "Glock 17": {"sound": "gun_glock17", "volume": 0.64, "cooldown": 0.035},
    "Dual Beretta 92FS": {"sound": "gun_dual_beretta", "volume": 0.62, "cooldown": 0.055},
    "HK MP5": {"sound": "gun_mp5", "volume": 0.50, "cooldown": 0.025},
    "Mossberg 500": {"sound": "gun_mossberg500", "volume": 0.78, "cooldown": 0.11},
    "M4A1 Carbine": {"sound": "gun_m4a1", "volume": 0.70, "cooldown": 0.035},
    "Benelli M4": {"sound": "gun_benelli_m4", "volume": 0.76, "cooldown": 0.09},
    "XM-LAS Prototype": {"sound": "gun_xm_las", "volume": 0.56, "cooldown": 0.08},
}

POWER_UP_MESSAGES = {
    "medkit": {"en": "Medkit +45 HP", "vi": "Túi cứu thương +45 máu"},
    "overdrive": {"en": "Overdrive: more damage and fire rate", "vi": "Quá tải: tăng sát thương và tốc bắn"},
    "shield": {"en": "Shield: damage reduced", "vi": "Lá chắn: giảm sát thương nhận vào"},
    "haste": {"en": "Haste: faster movement", "vi": "Tăng tốc: di chuyển nhanh hơn"},
    "shock": {"en": "Shock Core blasts nearby zombies", "vi": "Lõi điện giật nổ quanh người chơi"},
}

BUFF_NAMES = {
    "overdrive": {"en": "OD", "vi": "QT"},
    "shield": {"en": "SH", "vi": "CK"},
    "haste": {"en": "HS", "vi": "TC"},
}


def clamp(value, low, high):
    return max(low, min(high, value))


def dist_point_rect(point, rect):
    px, py = point
    cx = clamp(px, rect.left, rect.right)
    cy = clamp(py, rect.top, rect.bottom)
    return math.hypot(px - cx, py - cy)


def tile_noise(x, y, salt=0):
    value = (x * 928371 + y * 689287 + salt * 19349663) & 0xFFFFFFFF
    value ^= value >> 13
    value = (value * 1274126177) & 0xFFFFFFFF
    return value


def facing_from_vector(vec):
    if abs(vec.x) > abs(vec.y):
        return "right" if vec.x > 0 else "left"
    return "down" if vec.y >= 0 else "up"


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


def make_ui_font(size, bold=False):
    for name in ("Cascadia Mono", "Consolas", "Segoe UI", "Arial", "DejaVu Sans"):
        path = pygame.font.match_font(name, bold=bold)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.Font(None, size)


def pixel_rect(surface, scale, color, x, y, w, h):
    pygame.draw.rect(surface, color, (x * scale, y * scale, w * scale, h * scale))


def pixel_poly(surface, scale, color, points):
    pygame.draw.polygon(surface, color, [(x * scale, y * scale) for x, y in points])


def pixel_circle(surface, scale, color, x, y, radius):
    pygame.draw.circle(surface, color, (round(x * scale), round(y * scale)), max(1, round(radius * scale)))


def outline_rect(surface, scale, color, outline, x, y, w, h):
    pixel_rect(surface, scale, outline, x - 1, y - 1, w + 2, h + 2)
    pixel_rect(surface, scale, color, x, y, w, h)


def weapon_lower_perp(direction):
    perp = Vec2(-direction.y, direction.x)
    if perp.length_squared() <= 0:
        return Vec2(0, 1)
    perp = perp.normalize()
    if perp.y < -0.05 or (abs(perp.y) <= 0.05 and perp.x < 0):
        perp = -perp
    return perp


def weapon_point(base, direction, lower, forward, side):
    return Vec2(base) + direction * forward + lower * side


def draw_weapon_rect(surface, base, direction, lower, forward, side, length, width, color, outline=(18, 18, 22)):
    center = weapon_point(base, direction, lower, forward + length / 2, side)
    half_len = direction * (length / 2)
    half_w = lower * (width / 2)
    points = [
        center - half_len - half_w,
        center + half_len - half_w,
        center + half_len + half_w,
        center - half_len + half_w,
    ]
    if outline:
        outline_points = []
        outline_w = lower * ((width + 3) / 2)
        outline_points.extend(
            [
                center - half_len - outline_w,
                center + half_len - outline_w,
                center + half_len + outline_w,
                center - half_len + outline_w,
            ]
        )
        pygame.draw.polygon(surface, outline, [(round(p.x), round(p.y)) for p in outline_points])
    pygame.draw.polygon(surface, color, [(round(p.x), round(p.y)) for p in points])


def draw_weapon_poly(surface, points, color, outline=(18, 18, 22)):
    int_points = [(round(p.x), round(p.y)) for p in points]
    if outline:
        pygame.draw.polygon(surface, outline, int_points)
        pygame.draw.lines(surface, outline, True, int_points, 3)
    pygame.draw.polygon(surface, color, int_points)


def draw_weapon_circle(surface, pos, radius, color, outline=(18, 18, 22)):
    center = (round(pos.x), round(pos.y))
    if outline:
        pygame.draw.circle(surface, outline, center, radius + 1)
    pygame.draw.circle(surface, color, center, radius)


def make_player_frame(character_id, facing, frame, scale=2):
    if facing == "left":
        return pygame.transform.flip(make_player_frame(character_id, "right", frame, scale), True, False)

    styles = {
        "soldier": {
            "coat": (49, 78, 115),
            "cloth": (21, 45, 70),
            "armor": (118, 89, 59),
            "accent": (214, 58, 61),
            "hair": (218, 232, 218),
            "trim": (236, 236, 210),
            "bulk": 0,
            "cape": True,
        },
        "scout": {
            "coat": (44, 73, 103),
            "cloth": (147, 126, 77),
            "armor": (83, 71, 61),
            "accent": (34, 163, 197),
            "hair": (28, 42, 65),
            "trim": (224, 225, 214),
            "bulk": 0,
            "cape": True,
        },
        "engineer": {
            "coat": (47, 49, 52),
            "cloth": (111, 36, 42),
            "armor": (111, 113, 115),
            "accent": (204, 46, 51),
            "hair": (32, 54, 73),
            "trim": (222, 224, 214),
            "bulk": 1,
            "cape": True,
        },
        "tank": {
            "coat": (38, 83, 92),
            "cloth": (26, 40, 70),
            "armor": (92, 85, 70),
            "accent": (214, 44, 58),
            "hair": (238, 226, 166),
            "trim": (53, 200, 205),
            "bulk": 3,
            "cape": False,
        },
    }
    art = styles.get(character_id, styles["soldier"])
    skin = (226, 168, 122)
    outline = (24, 23, 25)
    boot = (33, 30, 33)
    eye = (31, 27, 25)
    step = (-1, 0, 1, 0)[frame % 4]
    bob = -1 if frame % 2 else 0
    surface = pygame.Surface((26 * scale, 32 * scale), pygame.SRCALPHA)
    pygame.draw.ellipse(surface, (0, 0, 0, 110), (5 * scale, 25 * scale, 16 * scale, 5 * scale))

    bulk = art["bulk"]
    torso_x = 9 - min(2, bulk)
    torso_w = 8 + bulk
    shoulder_w = 3 + max(0, bulk // 2)
    head_y = 5 + bob
    torso_y = 12 + bob

    if art["cape"]:
        if facing == "right":
            pixel_poly(surface, scale, outline, [(8, 11), (2, 13), (4, 25), (10, 23)])
            pixel_poly(surface, scale, art["cloth"], [(8, 12), (3, 14), (5, 24), (10, 22)])
        elif facing == "up":
            pixel_poly(surface, scale, outline, [(8, 12), (18, 12), (20, 26), (6, 26)])
            pixel_poly(surface, scale, art["cloth"], [(9, 13), (17, 13), (19, 25), (7, 25)])
        else:
            pixel_poly(surface, scale, outline, [(7, 12), (19, 12), (17, 26), (9, 26)])
            pixel_poly(surface, scale, art["cloth"], [(8, 13), (18, 13), (16, 25), (10, 25)])

    # Legs and boots first so coat/armor sits on top.
    outline_rect(surface, scale, art["cloth"], outline, 9 + step, 22, 4, 6)
    outline_rect(surface, scale, art["coat"], outline, 14 - step, 22, 4, 6)
    pixel_rect(surface, scale, boot, 8 + step, 28, 6, 2)
    pixel_rect(surface, scale, boot, 14 - step, 28, 6, 2)

    if facing == "right":
        pixel_poly(surface, scale, outline, [(torso_x - 1, torso_y), (torso_x + torso_w + 1, torso_y), (torso_x + torso_w, 22), (torso_x, 22)])
        pixel_poly(surface, scale, art["coat"], [(torso_x, torso_y), (torso_x + torso_w, torso_y), (torso_x + torso_w - 1, 21), (torso_x + 1, 21)])
        outline_rect(surface, scale, art["armor"], outline, torso_x - shoulder_w, torso_y + 1, shoulder_w, 4)
        outline_rect(surface, scale, art["armor"], outline, torso_x + torso_w - 1, torso_y + 1, shoulder_w, 4)
        outline_rect(surface, scale, art["coat"], outline, 6, torso_y + 4 + (frame % 2), 4, 6)
        outline_rect(surface, scale, art["trim"], outline, 16, torso_y + 3 - (frame % 2), 4, 5)
        outline_rect(surface, scale, skin, outline, 10, head_y, 7, 6)
        pixel_rect(surface, scale, eye, 16, head_y + 3, 1, 1)
        pixel_rect(surface, scale, art["hair"], 9, head_y - 1, 8, 2)
        pixel_rect(surface, scale, art["hair"], 10, head_y - 2, 6, 1)
    elif facing == "up":
        pixel_poly(surface, scale, outline, [(torso_x - 1, torso_y), (torso_x + torso_w + 1, torso_y), (torso_x + torso_w, 22), (torso_x, 22)])
        pixel_poly(surface, scale, art["coat"], [(torso_x, torso_y), (torso_x + torso_w, torso_y), (torso_x + torso_w - 1, 21), (torso_x + 1, 21)])
        outline_rect(surface, scale, art["armor"], outline, torso_x - shoulder_w, torso_y + 1, shoulder_w, 5)
        outline_rect(surface, scale, art["armor"], outline, torso_x + torso_w, torso_y + 1, shoulder_w, 5)
        outline_rect(surface, scale, art["coat"], outline, 6, torso_y + 3 + (frame % 2), 4, 6)
        outline_rect(surface, scale, art["coat"], outline, 17, torso_y + 3 - (frame % 2), 4, 6)
        pixel_rect(surface, scale, art["hair"], 9, head_y - 1, 9, 6)
        pixel_rect(surface, scale, art["armor"], 8, head_y - 1, 11, 2)
    else:
        pixel_poly(surface, scale, outline, [(torso_x - 1, torso_y), (torso_x + torso_w + 1, torso_y), (torso_x + torso_w, 22), (torso_x, 22)])
        pixel_poly(surface, scale, art["coat"], [(torso_x, torso_y), (torso_x + torso_w, torso_y), (torso_x + torso_w - 1, 21), (torso_x + 1, 21)])
        outline_rect(surface, scale, art["armor"], outline, torso_x - shoulder_w, torso_y + 1, shoulder_w, 5)
        outline_rect(surface, scale, art["armor"], outline, torso_x + torso_w, torso_y + 1, shoulder_w, 5)
        outline_rect(surface, scale, art["coat"], outline, 5, torso_y + 3 - (frame % 2), 4, 6)
        outline_rect(surface, scale, art["trim"], outline, 17, torso_y + 3 + (frame % 2), 4, 6)
        outline_rect(surface, scale, skin, outline, 10, head_y, 7, 6)
        pixel_rect(surface, scale, eye, 11, head_y + 3, 1, 1)
        pixel_rect(surface, scale, eye, 15, head_y + 3, 1, 1)
        pixel_rect(surface, scale, art["hair"], 9, head_y - 1, 9, 2)
        pixel_rect(surface, scale, art["hair"], 10, head_y - 2, 7, 1)

    # Class-specific readable details inspired by the reference silhouettes.
    if character_id == "soldier":
        pixel_rect(surface, scale, art["trim"], 11, torso_y + 1, 4, 1)
        pixel_rect(surface, scale, art["accent"], 12, head_y - 3, 3, 2)
        pixel_rect(surface, scale, art["accent"], 15, head_y - 4, 2, 2)
    elif character_id == "scout":
        pixel_poly(surface, scale, art["accent"], [(16, head_y), (24, head_y - 3), (19, head_y + 5)])
        pixel_rect(surface, scale, art["trim"], 11, torso_y + 1, 5, 1)
    elif character_id == "engineer":
        pixel_rect(surface, scale, art["accent"], 9, 21, 8, 2)
    elif character_id == "tank":
        outline_rect(surface, scale, art["armor"], outline, 5, torso_y - 1, 5, 8)
        outline_rect(surface, scale, art["armor"], outline, 17, torso_y - 1, 5, 8)
        pixel_rect(surface, scale, art["trim"], 12, torso_y + 2, 4, 2)

    return surface


def make_zombie_frame(kind, facing, frame, scale=2):
    if facing == "left":
        return pygame.transform.flip(make_zombie_frame(kind, "right", frame, scale), True, False)

    cfg = ZOMBIE_TYPES[kind]
    outline = (20, 22, 20)
    rot = (58, 48, 48)
    eye = (238, 239, 117)
    step = (-1, 0, 1, 0)[frame % 4]
    bob = -1 if frame % 2 else 0

    if kind == "titan":
        surface = pygame.Surface((42 * scale, 38 * scale), pygame.SRCALPHA)
        pygame.draw.ellipse(surface, (0, 0, 0, 135), (5 * scale, 30 * scale, 32 * scale, 6 * scale))
        body = cfg["color"]
        accent = cfg["accent"]
        armor = (82, 75, 72)
        skin_dark = (62, 53, 55)
        head_x = 18
        head_y = 5 + bob
        torso_y = 13 + bob
        pixel_poly(surface, scale, outline, [(7, torso_y + 2), (35, torso_y + 1), (38, 26), (31, 32), (11, 32), (4, 25)])
        pixel_poly(surface, scale, body, [(8, torso_y + 3), (34, torso_y + 2), (36, 25), (30, 30), (12, 30), (6, 24)])
        outline_rect(surface, scale, armor, outline, 5, torso_y + 2, 8, 12)
        outline_rect(surface, scale, armor, outline, 30, torso_y + 1, 8, 13)
        outline_rect(surface, scale, skin_dark, outline, 16, head_y, 10, 9)
        pixel_rect(surface, scale, eye, 18, head_y + 3, 2, 2)
        pixel_rect(surface, scale, eye, 23, head_y + 3, 2, 2)
        pixel_rect(surface, scale, (24, 17, 15), 19, head_y + 7, 6, 2)
        pixel_rect(surface, scale, accent, 20, head_y + 8, 1, 2)
        pixel_rect(surface, scale, accent, 24, head_y + 8, 1, 2)
        pixel_poly(surface, scale, outline, [(15, head_y + 1), (12, head_y - 3), (18, head_y)])
        pixel_poly(surface, scale, outline, [(26, head_y + 1), (31, head_y - 3), (24, head_y)])
        pixel_rect(surface, scale, (42, 38, 44), 11, torso_y + 4, 22, 2)
        for cx in (12, 17, 22, 27):
            pixel_rect(surface, scale, (121, 116, 122), cx, torso_y + 3, 2, 3)
        outline_rect(surface, scale, body, outline, 9 + step, 28, 8, 6)
        outline_rect(surface, scale, body, outline, 25 - step, 28, 8, 6)
        pixel_rect(surface, scale, accent, 15, torso_y + 12, 4, 3)
        pixel_rect(surface, scale, accent, 27, torso_y + 10, 3, 3)
        return surface

    surface = pygame.Surface((24 * scale, 28 * scale), pygame.SRCALPHA)
    pygame.draw.ellipse(surface, (0, 0, 0, 112), (5 * scale, 22 * scale, 14 * scale, 4 * scale))
    body = cfg["color"]
    accent = cfg["accent"]
    head = (68, 77, 62) if kind != "boomer" else (112, 103, 51)
    cloth = {
        "walker": (43, 73, 73),
        "runner": (113, 50, 45),
        "spitter": (46, 94, 61),
        "boomer": (113, 89, 43),
        "stalker": (72, 69, 116),
    }.get(kind, body)
    lean = 2 if kind == "runner" else 0
    torso_x = 9 + lean
    torso_y = 10 + bob

    if facing == "right":
        pixel_poly(surface, scale, outline, [(torso_x - 1, torso_y), (torso_x + 8, torso_y + 1), (torso_x + 9, 20), (torso_x + 1, 21)])
        pixel_poly(surface, scale, body, [(torso_x, torso_y + 1), (torso_x + 7, torso_y + 2), (torso_x + 8, 19), (torso_x + 2, 20)])
        outline_rect(surface, scale, head, outline, torso_x + 1, 4 + bob, 6, 5)
        pixel_rect(surface, scale, eye, torso_x + 6, 6 + bob, 1, 1)
        outline_rect(surface, scale, body, outline, torso_x - 4, 12 + (frame % 2), 4, 6)
        outline_rect(surface, scale, body, outline, torso_x + 8, 11 - (frame % 2), 5, 5)
        pixel_rect(surface, scale, cloth, torso_x, 16, 8, 2)
    elif facing == "up":
        pixel_poly(surface, scale, outline, [(8, torso_y), (17, torso_y), (16, 21), (9, 21)])
        pixel_poly(surface, scale, body, [(9, torso_y + 1), (16, torso_y + 1), (15, 20), (10, 20)])
        pixel_rect(surface, scale, head, 9, 4 + bob, 7, 5)
        pixel_rect(surface, scale, cloth, 8, 15, 9, 2)
        outline_rect(surface, scale, body, outline, 5, 12 + (frame % 2), 4, 6)
        outline_rect(surface, scale, body, outline, 16, 12 - (frame % 2), 4, 6)
    else:
        pixel_poly(surface, scale, outline, [(8, torso_y), (17, torso_y), (16, 21), (9, 21)])
        pixel_poly(surface, scale, body, [(9, torso_y + 1), (16, torso_y + 1), (15, 20), (10, 20)])
        outline_rect(surface, scale, head, outline, 9, 4 + bob, 7, 5)
        pixel_rect(surface, scale, eye, 10, 6 + bob, 1, 1)
        pixel_rect(surface, scale, eye, 15, 6 + bob, 1, 1)
        pixel_rect(surface, scale, (37, 23, 22), 11, 8 + bob, 5, 1)
        outline_rect(surface, scale, body, outline, 5, 12 - (frame % 2), 4, 6)
        outline_rect(surface, scale, body, outline, 16, 12 + (frame % 2), 4, 6)
        pixel_rect(surface, scale, cloth, 8, 15, 9, 2)

    outline_rect(surface, scale, body, outline, 8 + step, 20, 4, 5)
    outline_rect(surface, scale, body, outline, 14 - step, 20, 4, 5)
    pixel_rect(surface, scale, rot, 7 + step, 25, 5, 2)
    pixel_rect(surface, scale, rot, 14 - step, 25, 5, 2)

    if kind == "runner":
        pixel_poly(surface, scale, accent, [(10, torso_y), (18, torso_y + 2), (16, torso_y + 5), (9, torso_y + 3)])
        pixel_rect(surface, scale, (229, 93, 76), 6, 12 + frame % 2, 3, 2)
    elif kind == "spitter":
        pixel_circle(surface, scale, (70, 244, 90), 15, 13 + bob, 3)
        pixel_rect(surface, scale, (145, 255, 116), 18, 8 + (frame % 2), 2, 2)
        pixel_rect(surface, scale, (99, 226, 73), 20, 10 + (frame % 2), 2, 1)
    elif kind == "boomer":
        pixel_circle(surface, scale, (204, 181, 70), 13, 15 + bob, 5)
        pixel_rect(surface, scale, (136, 255, 75), 15, 12 + (frame % 2), 2, 2)
        pixel_rect(surface, scale, (86, 142, 54), 11, 18, 6, 1)
    elif kind == "stalker":
        pixel_poly(surface, scale, (122, 111, 176), [(8, 9), (18, 9), (20, 22), (6, 22)])
        pixel_rect(surface, scale, (213, 205, 255), 13, 5 + bob, 2, 1)
    else:
        pixel_rect(surface, scale, accent, 10, 14, 6, 2)
    return surface


def build_sprites():
    sprites = {}
    for character_id in CHARACTERS:
        for facing in ("down", "up", "right", "left"):
            for frame in range(4):
                sprites[f"player_{character_id}_{facing}_{frame}"] = make_player_frame(character_id, facing, frame, 2)
        sprites[f"player_{character_id}"] = sprites[f"player_{character_id}_down_0"]
    sprites["player"] = sprites["player_soldier"]
    for key in ZOMBIE_TYPES:
        for facing in ("down", "up", "right", "left"):
            for frame in range(4):
                sprites[f"zombie_{key}_{facing}_{frame}"] = make_zombie_frame(key, facing, frame, 2)
        sprites[key] = sprites[f"zombie_{key}_down_0"]
    return sprites


ORTHO_NEIGHBORS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
DIAGONAL_NEIGHBORS = ORTHO_NEIGHBORS + [(1, 1), (1, -1), (-1, 1), (-1, -1)]


def astar_heuristic(a, b, allow_diagonal=False):
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    if not allow_diagonal:
        return dx + dy
    return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)


def find_path(tile_map, start, goal, blocked=(), allow_diagonal=False, weight=1.0, radius=0, max_nodes=900):
    blocked = set(blocked)
    blocked.discard(start)
    blocked.discard(goal)

    def passable(cell):
        if not tile_map.in_bounds(cell) or cell in blocked:
            return False
        if radius > 0:
            return tile_map.is_clear_for_radius(cell, radius)
        return not tile_map.is_wall(cell)

    if not passable(start) or not passable(goal):
        return []

    neighbors = DIAGONAL_NEIGHBORS if allow_diagonal else ORTHO_NEIGHBORS
    open_heap = [(0, 0, start)]
    came_from = {}
    g_score = {start: 0.0}
    closed = set()
    counter = 0
    visited = 0

    while open_heap and visited < max_nodes:
        _, _, current = heapq.heappop(open_heap)
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
        visited += 1

        for dx, dy in neighbors:
            nxt = (current[0] + dx, current[1] + dy)
            if not passable(nxt):
                continue
            if dx and dy and (not passable((current[0] + dx, current[1])) or not passable((current[0], current[1] + dy))):
                continue
            move_cost = math.sqrt(2) if dx and dy else 1.0
            tentative = g_score[current] + move_cost
            if tentative < g_score.get(nxt, 1_000_000):
                came_from[nxt] = current
                g_score[nxt] = tentative
                counter += 1
                f_score = tentative + astar_heuristic(nxt, goal, allow_diagonal) * weight
                heapq.heappush(open_heap, (f_score, counter, nxt))
    return []


def has_cell_line(tile_map, start, goal, blocked=(), radius=0):
    blocked = set(blocked)
    start_pos = tile_map.cell_center(start)
    end_pos = tile_map.cell_center(goal)
    distance = start_pos.distance_to(end_pos)
    steps = max(1, int(distance // 10))
    for i in range(1, steps + 1):
        pos = start_pos.lerp(end_pos, i / steps)
        cell = tile_map.world_to_cell(pos)
        if cell in blocked:
            return False
        if radius > 0:
            if not tile_map.is_clear_for_radius(cell, radius):
                return False
        elif tile_map.is_wall(cell):
            return False
    return True


def smooth_path(tile_map, start, path, blocked=(), radius=0, lookahead=6):
    if len(path) <= 2:
        return path
    smoothed = []
    anchor = start
    index = 0
    while index < len(path):
        best = index
        limit = min(len(path) - 1, index + lookahead)
        for j in range(limit, index - 1, -1):
            if has_cell_line(tile_map, anchor, path[j], blocked, radius):
                best = j
                break
        smoothed.append(path[best])
        anchor = path[best]
        index = best + 1
    return smoothed


def astar(tile_map, start, goal, blocked):
    return find_path(tile_map, start, goal, blocked, allow_diagonal=False, weight=1.0, radius=0, max_nodes=900)


def astar_clearance(tile_map, start, goal, radius, blocked=()):
    return find_path(tile_map, start, goal, blocked, allow_diagonal=True, weight=1.05, radius=radius, max_nodes=1200)


def build_distance_field(tile_map, goals, blocked=()):
    blocked = set(blocked)
    distances = {}
    queue = deque()
    for goal in goals:
        if not tile_map.in_bounds(goal) or tile_map.is_wall(goal):
            continue
        distances[goal] = 0
        queue.append(goal)
    while queue:
        current = queue.popleft()
        for dx, dy in ORTHO_NEIGHBORS:
            nxt = (current[0] + dx, current[1] + dy)
            if nxt in distances or nxt in blocked or not tile_map.in_bounds(nxt) or tile_map.is_wall(nxt):
                continue
            distances[nxt] = distances[current] + 1
            queue.append(nxt)
    return distances


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
    ammo: int = 0
    reload_timer: float = 0.0

    def __post_init__(self):
        if self.ammo <= 0:
            self.ammo = self.magazine_size

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
        return max(tier.get("min_cooldown", 0.075), tier["cooldown"] * (0.985 ** self.tier_rank))

    @property
    def magazine_size(self):
        return self.tier["magazine"]

    @property
    def ammo_per_shot(self):
        return self.tier.get("ammo_per_shot", 1)

    @property
    def reload_time(self):
        return max(0.8, self.tier["reload_time"] - self.tier_rank * 0.04)

    @property
    def is_reloading(self):
        return self.reload_timer > 0

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

    def update(self, dt):
        if self.reload_timer <= 0:
            return
        self.reload_timer = max(0, self.reload_timer - dt)
        if self.reload_timer <= 0:
            self.ammo = self.magazine_size

    def start_reload(self):
        if self.reload_timer > 0 or self.ammo >= self.magazine_size:
            return False
        self.reload_timer = self.reload_time
        return True

    def spend_ammo(self):
        if self.reload_timer > 0 or self.ammo < self.ammo_per_shot:
            return False
        self.ammo -= self.ammo_per_shot
        return True

    def upgrade(self):
        if self.is_maxed:
            return False
        old_name = self.tier_name
        self.level += 1
        if self.tier_name != old_name:
            self.ammo = self.magazine_size
            self.reload_timer = 0
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
        self.level_notes = []
        self.buff_timers = {"overdrive": 0.0, "shield": 0.0, "haste": 0.0}
        self.heal_cooldown = 0.0
        self.dash_cooldown = 0.0
        self.dash_time = 0.0
        self.dash_dir = Vec2(0, 0)
        self.aim_dir = Vec2(0, 1)
        self.muzzle_flash_timer = 0.0
        self.last_move_dir = Vec2(0, 1)
        self.facing = "down"
        self.anim_time = 0.0
        self.is_moving = False

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
        for key in self.buff_timers:
            self.buff_timers[key] = max(0, self.buff_timers[key] - dt)
        self.heal_cooldown = max(0, self.heal_cooldown - dt)
        self.dash_cooldown = max(0, self.dash_cooldown - dt)
        self.dash_time = max(0, self.dash_time - dt)

        moving = False
        if self.dash_time > 0 and self.dash_dir.length_squared() > 0:
            self.try_move(self.dash_dir.normalize() * 560 * dt, game)
            self.last_move_dir = self.dash_dir.normalize()
            self.facing = facing_from_vector(self.last_move_dir)
            moving = True
        elif move.length_squared() > 0:
            move_dir = move.normalize()
            self.last_move_dir = move_dir
            self.facing = facing_from_vector(move_dir)
            speed = self.speed * (1.35 if self.buff_timers["haste"] > 0 else 1.0)
            self.try_move(move_dir * speed * dt, game)
            moving = True
        self.is_moving = moving
        if moving:
            self.anim_time += dt * (14 if self.dash_time > 0 else 9)
        else:
            self.anim_time = 0

        self.weapon.update(dt)
        self.fire_timer = max(0, self.fire_timer - dt)
        self.muzzle_flash_timer = max(0, self.muzzle_flash_timer - dt)
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
        blockers = [s for s in game.structures if s.alive and s.kind != "gate"]
        if self.dash_time > 0:
            blockers = [s for s in blockers if s.kind != "fence" or s.level >= 4]
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
        if self.weapon.is_reloading:
            return
        mx, my = world_pos
        if not (0 <= mx < WORLD_W and 0 <= my < WORLD_H):
            return
        direction = Vec2(mx, my) - self.pos
        if direction.length_squared() <= 1:
            return
        self.aim_dir = direction.normalize()
        self.facing = facing_from_vector(direction)
        base_angle = math.atan2(direction.y, direction.x)
        overdrive_damage = 1.35 if self.buff_timers["overdrive"] > 0 else 1.0
        fire_rate_mult = 1 + self.fire_rate_bonus + (0.45 if self.buff_timers["overdrive"] > 0 else 0)
        damage = int(self.weapon.damage * (1 + self.damage_bonus) * overdrive_damage * game.difficulty_cfg()["player_damage"])
        if not self.weapon.spend_ammo():
            if self.weapon.start_reload():
                game.play_sound("reload", 0.42, cooldown=0.12)
            return
        if self.weapon.style == "laser":
            angle = base_angle + random.uniform(-self.weapon.spread, self.weapon.spread)
            laser_dir = Vec2(math.cos(angle), math.sin(angle))
            game.fire_laser(self.pos + laser_dir * (self.radius + 8), laser_dir, damage, self.weapon.bullet_range, self.weapon.pierce)
            game.play_weapon_sound()
            self.muzzle_flash_timer = 0.11
            self.fire_timer = self.weapon.cooldown / fire_rate_mult
            if self.weapon.ammo <= 0:
                self.weapon.start_reload()
                game.play_sound("reload", 0.38, cooldown=0.16)
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
        self.muzzle_flash_timer = 0.06
        game.play_weapon_sound()
        self.fire_timer = self.weapon.cooldown / fire_rate_mult
        if self.weapon.ammo <= 0:
            self.weapon.start_reload()
            game.play_sound("reload", 0.38, cooldown=0.16)

    def take_damage(self, amount, game):
        if self.invuln > 0:
            return
        reduction = min(0.38, self.armor * 0.025)
        if self.buff_timers["shield"] > 0:
            reduction = min(0.72, reduction + 0.42)
        amount = max(1, int(round(amount * (1 - reduction))))
        self.hp -= amount
        self.invuln = 0.18
        game.play_sound("hurt", 0.55, cooldown=0.22)
        game.floating_texts.append(FloatingText(self.pos + Vec2(0, -28), f"-{amount}", COLORS["red"]))
        if self.hp <= 0:
            self.hp = 0
            game.game_over = True

    def start_dash(self, game):
        if self.dash_cooldown > 0 or self.dash_time > 0 or game.build_mode is not None:
            return False
        direction = Vec2(self.last_move_dir)
        mouse_world = game.mouse_world()
        if mouse_world is not None:
            aim = Vec2(mouse_world) - self.pos
            if aim.length_squared() > 36:
                direction = aim.normalize()
        if direction.length_squared() <= 0:
            direction = Vec2(0, 1)
        self.dash_dir = direction.normalize()
        self.dash_time = 0.18
        self.dash_cooldown = 2.35
        self.invuln = max(self.invuln, 0.2)
        for _ in range(14):
            game.particles.append(Particle(self.pos, -self.dash_dir.rotate(random.uniform(-34, 34)) * random.uniform(40, 170), COLORS["cyan"], life=0.28, size=3))
        game.play_sound("dash", 0.46, cooldown=0.12)
        return True

    def activate_powerup(self, kind, game):
        if kind == "medkit":
            heal = min(self.max_hp - self.hp, 45 + game.wave * 3)
            self.hp = min(self.max_hp, self.hp + heal)
            game.floating_texts.append(FloatingText(self.pos + Vec2(0, -36), f"+{int(heal)} {game.t('hp')}", COLORS["green"], life=1.0))
        elif kind == "overdrive":
            self.buff_timers["overdrive"] = max(self.buff_timers["overdrive"], 7.0)
        elif kind == "shield":
            self.buff_timers["shield"] = max(self.buff_timers["shield"], 8.0)
        elif kind == "haste":
            self.buff_timers["haste"] = max(self.buff_timers["haste"], 6.0)
        elif kind == "shock":
            damage = 52 + game.wave * 7
            game.damage_zombies_in_radius(self.pos, 128, damage)
            game.create_shockwave(self.pos, 128, 0, visual_only=True)
        game.message = game.powerup_message(kind)
        game.message_timer = 2.0
        game.play_sound("powerup", 0.58, cooldown=0.08)

    def add_xp(self, amount, game):
        if self.level >= PLAYER_MAX_LEVEL:
            self.xp = min(self.next_xp, self.xp + amount)
            return
        self.xp += amount
        while self.xp >= self.next_xp and self.level < PLAYER_MAX_LEVEL:
            self.xp -= self.next_xp
            self.level += 1
            self.next_xp = int(self.next_xp * 1.25 + 30)
            perks = self.apply_level_perks(game)
            game.floating_texts.append(
                FloatingText(self.pos + Vec2(0, -44), game.t("level_up").format(level=self.level), COLORS["cyan"], life=1.4)
            )
            game.message = game.t("level_message").format(level=self.level, perks=", ".join(perks))
            game.message_timer = 2.6
            game.create_level_up_effect(self.pos, self.level)
        if self.level >= PLAYER_MAX_LEVEL:
            self.xp = min(self.xp, self.next_xp)

    def apply_level_perks(self, game):
        perks = []
        self.max_hp += 16
        self.hp = min(self.max_hp, self.hp + 42)
        self.speed += 2.5
        perks.append(game.t("perk_hp"))

        if self.level % 2 == 0:
            self.damage_bonus += 0.06
            perks.append(game.t("perk_damage"))
        if self.level % 3 == 0:
            self.fire_rate_bonus += 0.05
            perks.append(game.t("perk_fire_rate"))
        if self.level % 4 == 0:
            self.pickup_radius += 16
            self.gold_bonus += 0.05
            perks.append(game.t("perk_magnet_gold"))
        if self.level % 5 == 0:
            self.armor += 2
            self.regen_rate += 0.35
            perks.append(game.t("perk_armor_regen"))
        if len(perks) == 1:
            self.armor += 1
            self.pickup_radius += 8
            perks.append(game.t("perk_armor_magnet"))

        self.level_notes = perks[-3:]
        return perks

    def weapon_aim_direction(self, aim_pos):
        if self.muzzle_flash_timer > 0 and self.aim_dir.length_squared() > 0:
            return self.aim_dir.normalize()
        if aim_pos is not None:
            direction = Vec2(aim_pos) - self.pos
            if direction.length_squared() > 4:
                return direction.normalize()
        if self.aim_dir.length_squared() > 0:
            return self.aim_dir.normalize()
        if self.last_move_dir.length_squared() > 0:
            return self.last_move_dir.normalize()
        return Vec2(0, 1)

    def draw_weapon_model(self, surface, base, direction, profile, compact=False):
        direction = Vec2(direction)
        if direction.length_squared() <= 0:
            return
        direction = direction.normalize()
        lower = weapon_lower_perp(direction)
        scale = 0.88 if compact else 1.0
        body = profile["body"] * scale
        barrel = profile["barrel"] * scale
        stock = profile["stock"] * scale
        height = profile["height"] * scale
        barrel_width = max(2.0, profile["barrel_width"] * scale)
        grip = profile["grip"] * scale
        kind = profile["kind"]
        color = profile["color"]
        accent = profile["accent"]
        detail = profile["detail"]
        muzzle = profile["muzzle"]
        outline = (16, 16, 20)

        if stock > 0:
            draw_weapon_rect(surface, base, direction, lower, -stock + 1, 0, stock + 2, max(4, height * 0.65), detail, outline)
            if kind in ("pump_shotgun", "rifle"):
                draw_weapon_rect(surface, base, direction, lower, -stock + 2, height * 0.28, stock * 0.65, 3, accent, None)

        draw_weapon_rect(surface, base, direction, lower, body - 1, -height * 0.08, barrel, barrel_width, detail, outline)
        draw_weapon_rect(surface, base, direction, lower, body + barrel - 1, -height * 0.08, 4, barrel_width + 1, muzzle, outline)
        draw_weapon_rect(surface, base, direction, lower, 0, 0, body, height, color, outline)
        draw_weapon_rect(surface, base, direction, lower, 2, -height * 0.28, body * 0.56, max(2, height * 0.24), accent, None)

        if kind in ("smg", "rifle", "laser"):
            draw_weapon_rect(surface, base, direction, lower, body * 0.12, -height * 0.72, body * 0.36, 2, detail, outline)

        grip_forward = 3 if kind in ("pistol", "dual_pistol") else body * 0.23
        grip_width = 5 if kind in ("pistol", "dual_pistol") else 6
        grip_points = [
            weapon_point(base, direction, lower, grip_forward, height * 0.36),
            weapon_point(base, direction, lower, grip_forward + grip_width, height * 0.30),
            weapon_point(base, direction, lower, grip_forward + grip_width * 0.82, height * 0.40 + grip),
            weapon_point(base, direction, lower, grip_forward + 1, height * 0.44 + grip * 0.86),
        ]
        draw_weapon_poly(surface, grip_points, detail, outline)

        if kind == "smg":
            mag_points = [
                weapon_point(base, direction, lower, body * 0.50, height * 0.45),
                weapon_point(base, direction, lower, body * 0.70, height * 0.45),
                weapon_point(base, direction, lower, body * 0.77, height * 1.55),
                weapon_point(base, direction, lower, body * 0.56, height * 1.42),
            ]
            draw_weapon_poly(surface, mag_points, detail, outline)
            draw_weapon_rect(surface, base, direction, lower, body + 1, height * 0.50, 6, 4, accent, outline)
        elif kind == "rifle":
            mag_points = [
                weapon_point(base, direction, lower, body * 0.48, height * 0.44),
                weapon_point(base, direction, lower, body * 0.70, height * 0.44),
                weapon_point(base, direction, lower, body * 0.75, height * 1.70),
                weapon_point(base, direction, lower, body * 0.52, height * 1.62),
            ]
            draw_weapon_poly(surface, mag_points, detail, outline)
            draw_weapon_rect(surface, base, direction, lower, body + 4, -height * 0.05, 9, height * 0.70, accent, outline)
        elif kind == "pump_shotgun":
            draw_weapon_rect(surface, base, direction, lower, body + 1, height * 0.56, barrel - 2, 3, detail, outline)
            draw_weapon_rect(surface, base, direction, lower, body + 4, height * 0.72, 10, 5, accent, outline)
        elif kind == "semi_shotgun":
            draw_weapon_rect(surface, base, direction, lower, body + 1, height * 0.55, barrel - 1, 3, accent, outline)
            draw_weapon_rect(surface, base, direction, lower, body + 7, height * 0.62, 8, 4, detail, outline)
        elif kind == "laser":
            glow_core = weapon_point(base, direction, lower, body * 0.55, 0)
            draw_weapon_circle(surface, glow_core, 6, (28, 93, 113), outline)
            draw_weapon_circle(surface, glow_core, 3, accent, None)
            draw_weapon_rect(surface, base, direction, lower, body + 3, -height * 0.12, barrel * 0.65, 2, accent, None)

        if self.muzzle_flash_timer > 0 and not self.weapon.is_reloading:
            side = Vec2(-direction.y, direction.x)
            if side.length_squared() <= 0:
                side = Vec2(0, 1)
            side = side.normalize()
            muzzle_pos = weapon_point(base, direction, lower, body + barrel + 4, -height * 0.08)
            if kind == "laser":
                pygame.draw.circle(surface, (80, 230, 255), (round(muzzle_pos.x), round(muzzle_pos.y)), 7)
                pygame.draw.line(surface, (195, 255, 255), muzzle_pos, muzzle_pos + direction * 15, 3)
            else:
                flash = [
                    muzzle_pos + direction * 10,
                    muzzle_pos - direction * 2 + side * 5,
                    muzzle_pos - direction * 2 - side * 5,
                ]
                draw_weapon_poly(surface, flash, (255, 204, 84), None)
                pygame.draw.line(surface, (255, 244, 172), muzzle_pos, muzzle_pos + direction * 8, 2)

        skin = (226, 168, 122)
        main_hand = weapon_point(base, direction, lower, 4, height * 0.55)
        draw_weapon_circle(surface, main_hand, 3 if compact else 4, skin, outline)
        if kind not in ("pistol", "dual_pistol"):
            support_forward = min(body + barrel - 6, body + 8)
            support_hand = weapon_point(base, direction, lower, support_forward, height * 0.52)
            draw_weapon_circle(surface, support_hand, 3, skin, outline)

    def draw_held_weapon(self, surface, aim_pos=None):
        profile = WEAPON_VISUALS.get(self.weapon.tier_name, WEAPON_VISUALS["Glock 17"])
        direction = self.weapon_aim_direction(aim_pos)
        hand_base = self.pos + direction * profile.get("hand_forward", 8) + Vec2(0, -4)
        if profile["kind"] == "dual_pistol":
            side_axis = Vec2(-direction.y, direction.x)
            if side_axis.length_squared() <= 0:
                side_axis = Vec2(0, 1)
            side_axis = side_axis.normalize()
            for offset in (-5, 5):
                self.draw_weapon_model(surface, hand_base + side_axis * offset, direction, profile, compact=True)
            return
        self.draw_weapon_model(surface, hand_base, direction, profile)

    def draw(self, surface, sprites, aim_pos=None):
        frame = int(self.anim_time) % 4 if self.is_moving else 0
        sprite = sprites.get(f"player_{self.character_id}_{self.facing}_{frame}", sprites["player"])
        rect = sprite.get_rect(center=(round(self.pos.x), round(self.pos.y)))
        if self.invuln > 0 and int(self.invuln * 40) % 2 == 0:
            return
        if self.buff_timers["shield"] > 0:
            pygame.draw.circle(surface, (92, 170, 255), self.pos, self.radius + 10, 2)
        if self.buff_timers["overdrive"] > 0:
            pygame.draw.circle(surface, COLORS["gold"], self.pos, self.radius + 7, 1)
        if self.buff_timers["haste"] > 0:
            pygame.draw.circle(surface, COLORS["purple"], self.pos, self.radius + 5, 1)
        surface.blit(sprite, rect)
        self.draw_held_weapon(surface, aim_pos)


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
        self.level = self.stats.get("level", 0)
        self.electric_timer = 0.0
        self.titan_guard_ready = bool(self.stats.get("titan_guard", False))
        self.fire_timer = random.uniform(0, 0.2)
        self.rect = pygame.Rect(cell[0] * TILE + 4, cell[1] * TILE + 4, TILE - 8, TILE - 8)
        self.alive = True

    def update(self, dt, game):
        if not self.alive:
            return
        if self.kind in ("fence", "gate"):
            self.electric_timer = max(0, self.electric_timer - dt)
            return
        if self.kind != "turret":
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
        if self.kind in ("fence", "gate"):
            amount = max(1, int(round(amount * (1 - self.stats.get("damage_reduction", 0.0)))))
        self.hp -= amount
        game.spawn_spark(Vec2(self.rect.center), (210, 92, 73))
        if self.hp <= 0:
            self.alive = False
            game.floating_texts.append(FloatingText(Vec2(self.rect.center), game.t("broken"), COLORS["red"], life=0.9))

    def repair(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def upgrade_to(self, stats):
        old_pct = self.hp / max(1, self.max_hp)
        self.stats = stats
        self.level = stats.get("level", self.level)
        self.max_hp = stats["hp"]
        self.hp = min(self.max_hp, max(self.hp, int(self.max_hp * old_pct) + int(self.max_hp * 0.22)))
        self.titan_guard_ready = bool(stats.get("titan_guard", False))
        self.electric_timer = 0.0

    def on_zombie_attack(self, zombie, game):
        if self.kind != "fence" or not zombie.alive:
            return
        spike = self.stats.get("spike_damage", 0)
        if spike > 0 and zombie.kind != "titan":
            zombie.take_damage(spike, game)
            game.spawn_spark(Vec2(self.rect.center), COLORS["orange"])
        cooldown = self.stats.get("electric_cooldown", 0.0)
        if cooldown > 0 and self.electric_timer <= 0:
            self.electric_timer = cooldown
            game.create_shockwave(Vec2(self.rect.center), 58, 0, visual_only=True)
            for other in game.zombies:
                if other.alive and other.kind != "titan" and other.pos.distance_to(Vec2(self.rect.center)) < 70:
                    other.stun_timer = max(other.stun_timer, 0.45)
                    other.flash = max(other.flash, 0.12)
            game.play_sound("laser", 0.28, cooldown=0.18)

    def draw(self, surface):
        if self.kind == "turret":
            base = pygame.Rect(self.rect)
            pygame.draw.rect(surface, (55, 65, 76), base)
            pygame.draw.rect(surface, (121, 134, 145), base.inflate(-6, -6))
            center = Vec2(base.center)
            pygame.draw.circle(surface, (45, 49, 55), center, 8)
            pygame.draw.rect(surface, COLORS["cyan"], (center.x - 4, center.y - 15, 8, 18))
        elif self.kind == "gate":
            base = pygame.Rect(self.rect)
            post_w = max(4, self.rect.width // 6)
            left_post = pygame.Rect(self.rect.left, self.rect.top, post_w, self.rect.height)
            right_post = pygame.Rect(self.rect.right - post_w, self.rect.top, post_w, self.rect.height)
            pygame.draw.rect(surface, (83, 58, 41), left_post)
            pygame.draw.rect(surface, (83, 58, 41), right_post)
            center_rect = pygame.Rect(self.rect.left + post_w, self.rect.top, self.rect.width - post_w * 2, self.rect.height)
            pygame.draw.rect(surface, (62, 63, 64), center_rect)
            pygame.draw.rect(surface, (36, 38, 42), center_rect.inflate(-4, -4))
            pygame.draw.rect(surface, (143, 108, 64), (base.left + 3, base.top + 4, base.w - 6, 5), border_radius=2)
            pygame.draw.rect(surface, (143, 108, 64), (base.left + 3, base.bottom - 9, base.w - 6, 5), border_radius=2)
            for x in (base.left + base.w // 3, base.left + base.w * 2 // 3):
                pygame.draw.line(surface, (190, 185, 168), (x, base.top + 7), (x, base.bottom - 7), 2)
            pygame.draw.circle(surface, COLORS["gold"], (base.centerx + base.w // 6, base.centery), 2)
        else:
            level = max(1, self.level)
            base_color = (112, 82, 54) if level < 4 else (93, 92, 88)
            inner_color = (165, 120, 72) if level < 4 else (144, 140, 127)
            if level >= 5:
                inner_color = (82, 139, 127)
            pygame.draw.rect(surface, base_color, self.rect)
            pygame.draw.rect(surface, inner_color, self.rect.inflate(-5, -5))
            for offset in (6, 16):
                pygame.draw.line(
                    surface,
                    (83, 58, 41),
                    (self.rect.left + 3, self.rect.top + offset),
                    (self.rect.right - 3, self.rect.top + offset),
                    3,
                )
            if level >= 3:
                for x in range(self.rect.left + 5, self.rect.right - 3, 7):
                    pygame.draw.line(surface, (218, 210, 184), (x, self.rect.top + 4), (x + 3, self.rect.top - 2), 2)
            if level >= 4 and self.titan_guard_ready:
                pygame.draw.rect(surface, COLORS["gold"], self.rect.inflate(-2, -2), 2)
            if level >= 5:
                pulse = 1 + int(math.sin(pygame.time.get_ticks() * 0.009) > 0)
                pygame.draw.line(surface, COLORS["cyan"], (self.rect.left + 4, self.rect.centery), (self.rect.right - 4, self.rect.centery), pulse)

        pct = clamp(self.hp / self.max_hp, 0, 1)
        bar = pygame.Rect(self.rect.left, self.rect.bottom + 3, self.rect.width, 4)
        pygame.draw.rect(surface, (40, 32, 32), bar)
        pygame.draw.rect(surface, COLORS["green"] if pct > 0.45 else COLORS["orange"], (bar.x, bar.y, int(bar.w * pct), bar.h))


class Zombie:
    def __init__(self, kind, pos, wave, difficulty_id="normal", elite=False):
        self.kind = kind
        self.cfg = ZOMBIE_TYPES[kind]
        difficulty = DIFFICULTIES.get(difficulty_id, DIFFICULTIES["normal"])
        self.difficulty_id = difficulty_id
        self.elite = elite and kind != "titan"
        self.pos = Vec2(pos)
        hp_scale = 1.0 + max(0, wave - 1) * 0.18
        if kind == "titan":
            hp_scale += wave * 0.08
        self.max_hp = int(self.cfg["hp"] * hp_scale * difficulty["hp"])
        self.hp = self.max_hp
        self.radius = self.cfg["radius"]
        self.damage = int(self.cfg["damage"] * (1.0 + max(0, wave - 1) * 0.12) * difficulty["damage"])
        self.speed = self.cfg["speed"] * (1.0 + min(0.95, wave * 0.035)) * difficulty["speed"]
        if self.elite:
            self.max_hp = int(self.max_hp * 1.75)
            self.hp = self.max_hp
            self.damage = int(self.damage * 1.25)
            self.speed *= 1.12
            self.radius += 2
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
        self.charge_structure_hits = 0
        self.charge_hit_structure_ids = set()
        self.last_trampled_structure = None
        self.shockwave_timer = random.uniform(3.8, 5.2)
        leap_cooldown = TITAN_LEAP_COOLDOWNS.get(difficulty_id, TITAN_LEAP_COOLDOWNS["normal"])
        self.wall_leap_timer = random.uniform(leap_cooldown * 0.55, leap_cooldown * 0.85)
        self.wall_leap_time = 0
        self.wall_leap_duration = 0.7
        self.wall_leap_start = Vec2(self.pos)
        self.wall_leap_target = Vec2(self.pos)
        self.summon_thresholds = [0.72, 0.48, 0.24] if kind == "titan" else []
        self.last_pos = Vec2(self.pos)
        self.stuck_timer = 0
        self.stun_timer = 0.0
        self.facing = "down"
        self.anim_phase = random.uniform(0, 4)

    def take_damage(self, amount, game):
        self.hp -= amount
        self.flash = 0.08
        game.play_sound("hit", 0.28, cooldown=0.05)
        if random.random() < 0.12:
            game.play_zombie_sound("groan", self.kind, volume=0.22, cooldown=0.35)
        if self.hp <= 0 and self.alive:
            self.die(game)

    def die(self, game):
        self.alive = False
        game.play_zombie_sound("death", self.kind, volume=0.48 if self.kind != "titan" else 0.82, cooldown=0.12)
        reward = int(round((self.cfg["reward"] + random.randint(0, 3 + game.wave)) * game.difficulty_cfg()["reward"]))
        if self.elite:
            reward = int(round(reward * 1.65))
        game.drop_gold(self.pos, reward)
        game.player.kills += 1
        game.player.score += reward * 6
        game.player.add_xp(int(round(self.cfg["xp"] * (1.55 if self.elite else 1.0))), game)
        game.floating_texts.append(FloatingText(self.pos + Vec2(0, -24), f"+{reward}g", COLORS["gold"]))
        if self.elite:
            game.floating_texts.append(FloatingText(self.pos + Vec2(0, -42), game.t("elite_down"), COLORS["orange"], life=1.1))
            if random.random() < 0.62:
                game.spawn_powerup(self.pos)
        elif random.random() < min(0.03 + game.wave * 0.006, 0.12):
            game.spawn_powerup(self.pos)
        if self.kind == "boomer":
            game.create_explosion(self.pos, 105, self.damage + 22, enemy_owned=True, sound_name="boomer_explosion", sound_volume=0.76)

    def update(self, dt, game):
        if not self.alive:
            return
        if self.kind == "titan":
            self.update_titan(dt, game)
            return
        self.flash = max(0, self.flash - dt)
        self.stun_timer = max(0, self.stun_timer - dt)
        self.attack_timer = max(0, self.attack_timer - dt)
        self.special_timer = max(0, self.special_timer - dt)
        self.lunge_boost = max(0, self.lunge_boost - dt)
        self.dash_timer = max(0, self.dash_timer - dt)
        self.dash_time = max(0, self.dash_time - dt)
        if self.stun_timer > 0:
            self.flash = max(self.flash, 0.06)
            return

        if self.kind == "boomer":
            self.try_boomer_bile(game)
            self.try_boomer_dash(game)
            if self.should_explode(game):
                self.alive = False
                game.create_explosion(self.pos, 110, self.damage + 30, enemy_owned=True, sound_name="boomer_explosion", sound_volume=0.76)
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
            target_structure.on_zombie_attack(self, game)
            game.play_zombie_sound("attack", self.kind, volume=0.26, cooldown=0.28)
            self.attack_timer = self.cfg["attack_rate"]
            return

        player_dist = self.pos.distance_to(game.player.pos)
        if player_dist <= self.radius + game.player.radius + 4:
            if self.attack_timer <= 0:
                game.player.take_damage(self.damage, game)
                game.play_zombie_sound("attack", self.kind, volume=0.38, cooldown=0.22)
                self.attack_timer = self.cfg["attack_rate"]
            return

        self.follow_path(dt, game)

    def update_titan(self, dt, game):
        self.flash = max(0, self.flash - dt)
        self.stun_timer = max(0, self.stun_timer - dt)
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

        if self.stun_timer > 0:
            self.flash = max(self.flash, 0.08)
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
            return

        if self.charge_timer <= 0 and 135 < player_dist < 520 and self.has_titan_charge_lane(game, game.player.pos):
            self.start_titan_charge(game.player.pos, game)
            return

        self.follow_titan_path(dt, game)
        moved = self.pos.distance_to(self.last_pos)
        self.stuck_timer = self.stuck_timer + dt if moved < 1.2 else 0
        self.last_pos = Vec2(self.pos)
        if self.stuck_timer >= game.titan_stuck_threshold():
            if self.wall_leap_timer <= 0 and self.start_titan_wall_leap(game):
                self.stuck_timer = 0
            else:
                self.nudge_titan_out(game)
                self.stuck_timer = max(0, self.stuck_timer - 1.0)

    def can_titan_leap(self, game):
        if self.wall_leap_timer > 0 or self.stuck_timer < game.titan_stuck_threshold():
            return False
        if self.nearby_structure(game, reach_bonus=36) is not None:
            return False
        return not game.titan_has_reasonable_path(self)

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
        if not self.can_titan_leap(game):
            return False
        target_cell = game.find_titan_leap_cell(self)
        if target_cell is None:
            return False
        self.wall_leap_start = Vec2(self.pos)
        self.wall_leap_target = game.tile_map.cell_center(target_cell)
        if self.wall_leap_target.distance_to(self.pos) < 90:
            return False
        self.wall_leap_duration = clamp(self.wall_leap_target.distance_to(self.pos) / 520, 0.65, 1.05)
        self.wall_leap_time = self.wall_leap_duration
        self.wall_leap_timer = game.titan_leap_cooldown()
        self.path.clear()
        game.message = game.t("titan_vault")
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
            self.titan_stomp(game, radius=118, damage=max(4, self.damage // 2))
            self.stun_timer = random.uniform(0.8, 1.2)
            self.path_timer = 0
            self.stuck_timer = 0

    def follow_titan_path(self, dt, game):
        self.path_timer -= dt
        if self.path_timer <= 0:
            self.rebuild_titan_path(game)
            self.path_timer = random.uniform(0.22, 0.38)
            if not self.path and self.can_titan_leap(game):
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
        self.path = astar_clearance(game.tile_map, start, goal, self.radius, game.blocked_cells())[:16]

    def move_titan_towards(self, target_pos, dt, game, speed_multiplier=1.0):
        direction = Vec2(target_pos) - self.pos
        if direction.length_squared() <= 1:
            return False
        desired = direction.normalize()
        self.facing = facing_from_vector(desired)
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
            if game.tile_map.collides_circle(new_pos, self.radius, [s for s in game.structures if s.alive]):
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
        self.facing = facing_from_vector(self.charge_dir)
        self.charge_time = 0.82
        self.charge_hit_player = False
        self.charge_structure_hits = 0
        self.charge_hit_structure_ids = set()
        self.charge_timer = random.uniform(5.4, 7.0)
        self.path.clear()
        game.message = game.t("titan_charge")
        game.message_timer = 1.2
        game.create_shockwave(self.pos, 54, 0, visual_only=True)
        game.play_zombie_sound("titan", self.kind, volume=0.7, cooldown=1.2)

    def update_titan_charge(self, dt, game):
        self.charge_time -= dt
        charge_speed = 3.3 if self.charge_structure_hits == 0 else 2.35
        distance = self.speed * charge_speed * dt
        steps = max(1, int(distance // 7))
        for _ in range(steps):
            new_pos = self.pos + self.charge_dir * (distance / steps)
            if game.tile_map.collides_circle(new_pos, self.radius, ()):
                self.charge_time = 0
                self.titan_stomp(game, radius=95, damage=self.damage + 3)
                self.stun_timer = max(self.stun_timer, 0.85)
                return
            self.pos = new_pos
            self.last_trampled_structure = None
            if self.trample_structures(game, self.damage + 18, charge=True):
                hit_structure = self.last_trampled_structure
                self.charge_structure_hits += 1
                can_push_next_fence = (
                    hit_structure is not None
                    and hit_structure.kind == "fence"
                    and not hit_structure.alive
                    and self.charge_structure_hits < TITAN_CHARGE_MAX_STRUCTURE_HITS
                )
                if can_push_next_fence:
                    self.charge_time = min(self.charge_time, 0.34)
                    continue
                self.charge_time = 0
                self.stun_timer = max(self.stun_timer, 0.75)
                return
            if not self.charge_hit_player and self.pos.distance_to(game.player.pos) < self.radius + game.player.radius + 12:
                game.player.take_damage(self.damage + 16, game)
                self.charge_hit_player = True
                game.create_shockwave(self.pos, 74, 0, visual_only=True)
        if self.charge_time <= 0:
            self.titan_stomp(game, radius=86, damage=self.damage // 2)
            self.stun_timer = max(self.stun_timer, 0.75)

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
        game.warning_zones.append(WarningZone(self.pos, radius, damage))
        game.create_shockwave(self.pos, radius, 0, visual_only=True)
        self.stun_timer = max(self.stun_timer, TITAN_STOMP_WARNING_SECONDS * 0.72)
        game.play_zombie_sound("titan", self.kind, volume=0.62, cooldown=1.0)

    def trample_structures(self, game, damage, force=False, charge=False):
        if self.trample_timer > 0 and not force and not charge:
            return False
        hit = False
        self.last_trampled_structure = None
        for structure in game.structures:
            if structure.alive and dist_point_rect((self.pos.x, self.pos.y), structure.rect) < self.radius + 12:
                if charge and id(structure) in self.charge_hit_structure_ids:
                    continue
                if charge and structure.kind == "fence" and structure.titan_guard_ready:
                    structure.titan_guard_ready = False
                    structure.take_damage(max(damage, int(structure.max_hp * 0.42)), game)
                    game.create_shockwave(Vec2(structure.rect.center), 58, 0, visual_only=True)
                elif charge and structure.kind == "fence":
                    structure.take_damage(max(damage, int(structure.max_hp * 1.05)), game)
                else:
                    structure.take_damage(max(damage, int(structure.max_hp * 0.55)) if charge else damage, game)
                structure.on_zombie_attack(self, game)
                hit = True
                self.last_trampled_structure = structure
                if charge:
                    self.charge_hit_structure_ids.add(id(structure))
                if charge:
                    break
        if hit:
            self.trample_timer = 0.24
        return hit

    def try_titan_summon(self, game):
        if not self.summon_thresholds:
            return
        hp_pct = self.hp / self.max_hp
        if hp_pct > self.summon_thresholds[0]:
            return
        self.summon_thresholds.pop(0)
        game.message = game.t("titan_roar")
        game.message_timer = 1.6
        game.create_shockwave(self.pos, 120, 0, visual_only=True)
        game.play_zombie_sound("titan", self.kind, volume=0.78, cooldown=1.2)
        for kind in ["walker", "walker", "runner", "runner", "spitter"]:
            game.spawn_minion_near(kind, self.pos, min_player_distance=220, prefer_spawn_edges=True, require_path=True)

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
                self.facing = facing_from_vector(self.dash_dir)
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

    def nearby_structure(self, game, reach_bonus=8):
        best = None
        best_dist = 1_000_000
        for structure in game.structures:
            if not structure.alive:
                continue
            reach = self.radius + reach_bonus
            distance = dist_point_rect((self.pos.x, self.pos.y), structure.rect)
            if distance < reach and distance < best_dist:
                best = structure
                best_dist = distance
        return best

    def nearby_fence(self, game, reach=18):
        best = None
        best_dist = 1_000_000
        for structure in game.structures:
            if not structure.alive or structure.kind != "fence":
                continue
            distance = dist_point_rect((self.pos.x, self.pos.y), structure.rect)
            if distance < self.radius + reach and distance < best_dist:
                best = structure
                best_dist = distance
        return best

    def fence_slow_multiplier(self, game):
        fence = self.nearby_fence(game, reach=20)
        if fence is None:
            return 1.0
        if self.kind == "titan":
            return 0.86
        return fence.stats.get("slow", 1.0)

    def follow_path(self, dt, game):
        speed = self.speed * game.zombie_speed_multiplier(self.kind) * self.fence_slow_multiplier(game)
        if self.lunge_boost > 0:
            speed *= 1.9
        if self.dash_time > 0 and self.dash_dir.length_squared() > 0:
            self.facing = facing_from_vector(self.dash_dir)
            self.try_move(self.dash_dir.normalize() * speed * 3.2 * dt, game)
            return

        if self.kind == "walker":
            flow_dir = game.flow_direction(self.pos)
            if flow_dir is not None:
                self.facing = facing_from_vector(flow_dir)
                self.try_move(flow_dir * speed * dt, game)
                return

        if self.kind == "runner" and has_wall_line(game.tile_map, self.pos, game.player.pos):
            direction = game.player.pos - self.pos
            if direction.length_squared() > 1:
                self.facing = facing_from_vector(direction)
                self.try_move(direction.normalize() * speed * dt, game)
                return

        self.path_timer -= dt
        if self.path_timer <= 0:
            self.rebuild_path(game)
            self.path_timer = random.uniform(0.20, 0.36) if self.kind in ("runner", "stalker", "boomer") else random.uniform(0.34, 0.62)

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
        self.facing = facing_from_vector(direction)
        self.try_move(direction.normalize() * speed * dt, game)

    def rebuild_path(self, game):
        start = game.tile_map.world_to_cell(self.pos)
        player_cell = game.tile_map.world_to_cell(game.player.pos)
        if self.kind == "spitter":
            goal = game.spitter_goal_cell(self.pos)
            path = game.cached_path("spitter_keep_range", start, goal, allow_diagonal=True, weight=1.08, max_nodes=620, smooth=True)
        elif self.kind == "boomer":
            goal = game.predicted_player_cell(lead_tiles=2) or player_cell
            path = game.cached_path("boomer_intercept", start, goal, allow_diagonal=True, weight=1.28, max_nodes=520, smooth=True)
        elif self.kind == "runner":
            goal = game.predicted_player_cell(lead_tiles=3) or player_cell
            path = game.cached_path("runner_weighted_astar", start, goal, allow_diagonal=True, weight=1.45, max_nodes=360, smooth=True)
        elif self.kind == "stalker":
            goal = game.stalker_flank_cell(self.pos)
            stalker_blockers = {s.cell for s in game.structures if s.alive and (s.kind != "fence" or s.level >= 3)}
            path = find_path(game.tile_map, start, goal, stalker_blockers, allow_diagonal=True, weight=1.18, max_nodes=620)
            path = smooth_path(game.tile_map, start, path, stalker_blockers, 0) if path else []
        else:
            path = game.cached_path("walker_astar_fallback", start, player_cell, allow_diagonal=False, weight=1.0, max_nodes=520, smooth=False)
        if not path:
            structure = game.nearest_structure(self.pos)
            if structure is not None:
                path = game.cached_path(f"{self.kind}_structure", start, structure.cell, allow_diagonal=True, weight=1.2, max_nodes=360, smooth=False)
        self.path = path[:16 if self.kind in ("runner", "stalker", "boomer") else 12]

    def try_move(self, delta, game):
        blockers = [s for s in game.structures if s.alive]
        if self.kind == "stalker":
            blockers = [s for s in blockers if s.kind != "fence" or s.level >= 3]
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
        speed_hint = {
            "walker": 4.8,
            "runner": 10.5,
            "spitter": 5.6,
            "boomer": 7.4,
            "stalker": 9.2,
            "titan": 3.4,
        }.get(self.kind, 6.0)
        if self.dash_time > 0 or self.lunge_boost > 0 or self.charge_time > 0:
            speed_hint *= 1.6
        frame = int(pygame.time.get_ticks() / 1000 * speed_hint + self.anim_phase) % 4
        sprite = sprites.get(f"zombie_{self.kind}_{self.facing}_{frame}", sprites[self.kind])
        rect = sprite.get_rect(center=(round(self.pos.x), round(self.pos.y)))
        if self.elite:
            pygame.draw.circle(surface, COLORS["orange"], self.pos, self.radius + 8, 2)
            pygame.draw.circle(surface, (255, 176, 82), self.pos, self.radius + 2 + (frame % 2) * 2, 1)
        if self.kind == "spitter" and self.special_timer < 0.45:
            pygame.draw.circle(surface, (99, 245, 75), self.pos, self.radius + 8, 1)
        if self.kind == "boomer" and self.dash_time > 0:
            pygame.draw.circle(surface, (142, 255, 71), self.pos, self.radius + 10, 2)
        if self.kind == "titan" and (self.charge_time > 0 or self.wall_leap_time > 0):
            pygame.draw.circle(surface, COLORS["red"], self.pos, self.radius + 10, 2)
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
        pygame.draw.rect(surface, COLORS["orange"] if self.elite else COLORS["red"], (bar.x, bar.y, int(bar.w * pct), bar.h))


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


class PowerUpDrop:
    def __init__(self, pos, kind):
        self.pos = Vec2(pos) + Vec2(random.uniform(-14, 14), random.uniform(-14, 14))
        self.kind = kind
        self.life = 22
        self.pulse = random.uniform(0, math.tau)
        self.alive = True

    def update(self, dt, game):
        self.life -= dt
        if self.life <= 0:
            self.alive = False
            return
        distance = self.pos.distance_to(game.player.pos)
        magnet_radius = game.player.pickup_radius * 0.8
        if distance < magnet_radius:
            direction = game.player.pos - self.pos
            if direction.length_squared() > 1:
                self.pos += direction.normalize() * (magnet_radius * 1.8 - distance) * dt
        if distance < 22:
            game.player.activate_powerup(self.kind, game)
            self.alive = False

    def draw(self, surface):
        cfg = POWER_UP_TYPES[self.kind]
        pulse = int(math.sin(pygame.time.get_ticks() * 0.007 + self.pulse) > 0)
        size = 12 + pulse
        rect = pygame.Rect(0, 0, size, size)
        rect.center = (round(self.pos.x), round(self.pos.y))
        pygame.draw.rect(surface, (24, 29, 34), rect.inflate(6, 6))
        pygame.draw.rect(surface, cfg["color"], rect)
        pygame.draw.rect(surface, cfg["accent"], rect.inflate(-6, -6))
        if self.kind == "medkit":
            pygame.draw.rect(surface, (230, 65, 72), (rect.centerx - 2, rect.y + 2, 4, size - 4))
            pygame.draw.rect(surface, (230, 65, 72), (rect.x + 2, rect.centery - 2, size - 4, 4))
        elif self.kind == "shock":
            pygame.draw.line(surface, (22, 42, 45), (rect.centerx - 2, rect.y + 1), (rect.x + 4, rect.centery), 2)
            pygame.draw.line(surface, (22, 42, 45), (rect.x + 4, rect.centery), (rect.centerx + 2, rect.bottom - 1), 2)


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


class PulseRing:
    def __init__(self, pos, color, radius=72, life=0.55, width=3, start_radius=8):
        self.pos = Vec2(pos)
        self.color = color
        self.radius = radius
        self.start_radius = start_radius
        self.life = life
        self.max_life = life
        self.width = width
        self.alive = True

    def update(self, dt):
        self.life -= dt
        if self.life <= 0:
            self.alive = False

    def draw(self, surface):
        pct = 1 - clamp(self.life / self.max_life, 0, 1)
        radius = int(self.start_radius + (self.radius - self.start_radius) * pct)
        alpha = int(210 * (1 - pct))
        if radius <= 0 or alpha <= 0:
            return
        padding = self.width + 3
        size = (radius + padding) * 2
        ring = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(ring, (*self.color, alpha), (size // 2, size // 2), radius, self.width)
        surface.blit(ring, (self.pos.x - size // 2, self.pos.y - size // 2))


class WarningZone:
    def __init__(self, pos, radius, damage, delay=TITAN_STOMP_WARNING_SECONDS, color=None):
        self.pos = Vec2(pos)
        self.radius = radius
        self.damage = damage
        self.delay = delay
        self.timer = delay
        self.color = color or COLORS["red"]
        self.alive = True

    def update(self, dt, game):
        self.timer -= dt
        if self.timer > 0:
            return
        self.alive = False
        game.create_shockwave(self.pos, self.radius, self.damage)

    def draw(self, surface):
        pct = 1 - clamp(self.timer / max(0.01, self.delay), 0, 1)
        pulse = 0.55 + 0.45 * math.sin(pygame.time.get_ticks() * 0.03)
        radius = int(self.radius)
        padding = 8
        size = (radius + padding) * 2
        warning = pygame.Surface((size, size), pygame.SRCALPHA)
        fill_alpha = int(24 + 32 * pct)
        line_alpha = int(105 + 120 * pulse)
        pygame.draw.circle(warning, (*self.color, fill_alpha), (size // 2, size // 2), radius)
        pygame.draw.circle(warning, (*self.color, line_alpha), (size // 2, size // 2), radius, 3)
        inner = max(8, int(radius * pct))
        pygame.draw.circle(warning, (*self.color, 150), (size // 2, size // 2), inner, 2)
        surface.blit(warning, (self.pos.x - size // 2, self.pos.y - size // 2))


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
        self.clock = pygame.time.Clock()
        self.font = make_ui_font(max(18, int(24 * self.ui_scale)))
        self.small_font = make_ui_font(max(14, int(18 * self.ui_scale)))
        self.tiny_font = make_ui_font(max(11, int(14 * self.ui_scale)))
        self.big_font = make_ui_font(max(38, int(64 * self.ui_scale)), bold=True)
        self.title_font = make_ui_font(max(42, int(74 * self.ui_scale)), bold=True)
        self.ui = UIManager()
        self.sprites = build_sprites()
        self.menu_background = self.load_menu_background()
        self.state = "menu"
        self.paused = False
        self.language = "vi"
        self.music_volume = 70
        self.sfx_volume = 80
        self.auto_fire = True
        self.dev_mode = False
        self.difficulty_id = "normal"
        self.character_id = "soldier"
        self.map_id = "warehouse"
        self.setup_step = "difficulty"
        self.COLORS = COLORS
        self.character_defs = CHARACTERS
        self.difficulty_defs = DIFFICULTIES
        self.map_order = MAP_ORDER
        self.map_themes = MAP_THEMES
        self.map_rows_by_id = MAPS
        self.map_manager = MapManager(MAPS, MAP_THEMES, self.map_id, TILE)
        self.refresh_world_layout()
        self.options_return_state = "menu"
        self.options_return_paused = False
        self.ui_buttons = {}
        self.info_panel_open = False
        self.headless = headless
        self.audio_enabled = False
        self.sounds = {}
        self.sound_cooldowns = {}
        self.music_tracks = {}
        self.current_music_key = None
        self.wave_banner_text = ""
        self.wave_banner_timer = 0.0
        self.titan_banner_timer = 0.0
        self.path_blockers = set()
        self.path_signature = None
        self.path_cache = {}
        self.flow_field = {}
        self.init_audio()
        self.reset_gameplay()

    def refresh_world_layout(self):
        world_w = getattr(self.map_manager, "world_w", WORLD_W)
        world_h = getattr(self.map_manager, "world_h", WORLD_H)
        self.world_surface = pygame.Surface((world_w, world_h))
        self.play_rect = pygame.Rect(
            self.margin,
            self.top_ui_h,
            max(320, self.screen_w - self.margin * 2),
            max(240, self.screen_h - self.top_ui_h - self.bottom_ui_h - self.margin),
        )
        self.world_scale = min(self.play_rect.w / world_w, self.play_rect.h / world_h)
        self.world_rect = pygame.Rect(0, 0, int(world_w * self.world_scale), int(world_h * self.world_scale))
        self.world_rect.center = self.play_rect.center

    def reset_gameplay(self):
        self.map_manager.load_builtin_map(self.map_id)
        self.tile_map = self.map_manager
        self.refresh_world_layout()
        self.player = Player((self.map_manager.world_w / 2, self.map_manager.world_h / 2), self.character_id)
        self.zombies = []
        self.bullets = []
        self.lasers = []
        self.acid_projectiles = []
        self.poison_pools = []
        self.structures = []
        self.gold_drops = []
        self.powerups = []
        self.particles = []
        self.rings = []
        self.warning_zones = []
        self.floating_texts = []
        self.teleport_player_to_spawn(effect=True)
        self.wave = 0
        self.wave_active = False
        self.wave_break_timer = 0
        self.spawn_queue = []
        self.spawn_timer = 0
        self.build_mode = None
        self.game_over = False
        self.bile_timer = 0
        self.message = self.t("press_space_wave")
        self.message_timer = 4
        self.wave_banner_text = ""
        self.wave_banner_timer = 0.0
        self.titan_banner_timer = 0.0
        self.spawn_cells = self.build_spawn_cells()
        self.boss_spawn_cells = self.build_boss_spawn_cells()
        self.path_blockers = set()
        self.path_signature = None
        self.path_cache = {}
        self.flow_field = {}
        self.paused = False
        self.build_mode = None

    def t(self, key):
        return TEXT[self.language].get(key, key)

    def localized_name(self, table, key):
        values = table.get(key, {})
        return values.get(self.language) or values.get("en") or key

    def difficulty_name(self, difficulty_id=None):
        return self.localized_name(DIFFICULTY_NAMES, difficulty_id or self.difficulty_id)

    def character_name(self, character_id=None):
        return self.localized_name(CHARACTER_NAMES, character_id or self.character_id)

    def character_description(self, character_id=None):
        return self.localized_name(CHARACTER_DESCRIPTIONS, character_id or self.character_id)

    def map_name(self, map_id=None):
        return self.localized_name(MAP_NAMES, map_id or self.map_id)

    def map_description(self, map_id=None):
        return self.localized_name(MAP_DESCRIPTIONS, map_id or self.map_id)

    def weapon_name(self, weapon_name):
        return self.localized_name(WEAPON_NAMES, weapon_name)

    def structure_name(self, kind):
        return self.t(kind)

    def powerup_message(self, kind):
        return self.localized_name(POWER_UP_MESSAGES, kind)

    def buff_label(self, kind):
        return self.localized_name(BUFF_NAMES, kind)

    def init_audio(self):
        if self.headless:
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except pygame.error:
            self.audio_enabled = False
            return

        base_audio_dir = os.path.join(os.path.dirname(__file__), "assets", "audio")
        kenney_dir = os.path.join(base_audio_dir, "kenney_rpg", "OGG")
        synth_dir = os.path.join(base_audio_dir, "synth")
        oga_dir = os.path.join(base_audio_dir, "opengameart")
        sound_files = {
            "click": os.path.join(kenney_dir, "metalClick.ogg"),
            "ui_confirm": os.path.join(oga_dir, "8bit_confirm.wav"),
            "coin": os.path.join(kenney_dir, "handleCoins.ogg"),
            "build": os.path.join(kenney_dir, "metalLatch.ogg"),
            "upgrade": os.path.join(kenney_dir, "handleCoins2.ogg"),
            "hit": os.path.join(kenney_dir, "chop.ogg"),
            "explosion": os.path.join(kenney_dir, "metalPot3.ogg"),
            "boomer_explosion": os.path.join(oga_dir, "chunky_explosion.mp3"),
            "poison": os.path.join(kenney_dir, "creak3.ogg"),
            "hurt": os.path.join(kenney_dir, "cloth3.ogg"),
            "wave": os.path.join(kenney_dir, "doorOpen_1.ogg"),
            "dash": os.path.join(kenney_dir, "clothBelt.ogg"),
            "powerup": os.path.join(kenney_dir, "handleSmallLeather.ogg"),
            "reload": os.path.join(synth_dir, "reload_mag.wav"),
            "levelup": os.path.join(synth_dir, "level_up.wav"),
            "weapon_upgrade": os.path.join(synth_dir, "weapon_upgrade.wav"),
            "gun_glock17": os.path.join(synth_dir, "gun_glock17.wav"),
            "gun_dual_beretta": os.path.join(synth_dir, "gun_dual_beretta.wav"),
            "gun_mp5": os.path.join(synth_dir, "gun_mp5.wav"),
            "gun_mossberg500": os.path.join(synth_dir, "gun_mossberg500.wav"),
            "gun_m4a1": os.path.join(synth_dir, "gun_m4a1.wav"),
            "gun_benelli_m4": os.path.join(synth_dir, "gun_benelli_m4.wav"),
            "gun_xm_las": os.path.join(synth_dir, "gun_xm_las.wav"),
            "zombie_groan": os.path.join(oga_dir, "monster_groan.wav"),
            "zombie_attack": os.path.join(oga_dir, "monster_attack.wav"),
            "zombie_death": os.path.join(oga_dir, "monster_death.wav"),
            "zombie_titan": os.path.join(oga_dir, "monster_titan.wav"),
            "zombie_groan_synth": os.path.join(synth_dir, "zombie_groan.wav"),
            "zombie_attack_synth": os.path.join(synth_dir, "zombie_attack.wav"),
            "zombie_death_synth": os.path.join(synth_dir, "zombie_death.wav"),
            "zombie_titan_synth": os.path.join(synth_dir, "zombie_titan.wav"),
        }
        for name, path in sound_files.items():
            if not os.path.exists(path):
                continue
            try:
                self.sounds[name] = pygame.mixer.Sound(path)
            except pygame.error:
                continue
        self.music_tracks = {
            "menu": os.path.join(synth_dir, "bgm_dead_factory.wav"),
            "battle": os.path.join(synth_dir, "bgm_last_stand.wav"),
            "boss": os.path.join(synth_dir, "bgm_boss_warning.wav"),
        }
        self.music_tracks = {key: path for key, path in self.music_tracks.items() if os.path.exists(path)}
        self.audio_enabled = bool(self.sounds or self.music_tracks)
        if self.music_tracks:
            self.apply_music_volume()

    def load_menu_background(self):
        asset_dir = os.path.join(os.path.dirname(__file__), "assets")
        for filename in ("menu_background.png", "menu_background.jpg", "menu_background.jpeg", "menu_background.webp"):
            path = os.path.join(asset_dir, filename)
            if not os.path.exists(path):
                continue
            try:
                return pygame.image.load(path).convert()
            except pygame.error:
                continue
        return None

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

    def play_weapon_sound(self):
        audio = WEAPON_AUDIO.get(self.player.weapon.tier_name, WEAPON_AUDIO["Glock 17"])
        self.play_sound(audio["sound"], audio["volume"], audio["cooldown"])

    def play_zombie_sound(self, mood, kind="walker", volume=0.38, cooldown=0.35):
        if kind == "titan" or mood == "titan":
            key = "zombie_titan"
        elif mood == "death":
            key = "zombie_death"
        elif mood == "attack":
            key = "zombie_attack"
        else:
            key = "zombie_groan"
        self.play_sound(key, volume, cooldown)

    def apply_music_volume(self):
        if self.headless or not pygame.mixer.get_init():
            return
        pygame.mixer.music.set_volume(clamp(self.music_volume / 100, 0, 1))

    def desired_music_key(self):
        if self.state == "playing":
            if any(z.alive and z.kind == "titan" for z in self.zombies):
                return "boss"
            return "battle"
        return "menu"

    def update_music(self):
        if not self.audio_enabled or self.headless or not self.music_tracks or not pygame.mixer.get_init():
            return
        self.apply_music_volume()
        key = self.desired_music_key()
        path = self.music_tracks.get(key)
        if path is None:
            return
        if self.music_volume <= 0:
            return
        if self.current_music_key == key and pygame.mixer.music.get_busy():
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1, fade_ms=900)
            self.current_music_key = key
        except pygame.error:
            self.current_music_key = None

    def create_level_up_effect(self, pos, level):
        pos = Vec2(pos)
        self.rings.append(PulseRing(pos, COLORS["cyan"], radius=92, life=0.65, width=4, start_radius=16))
        self.rings.append(PulseRing(pos, COLORS["gold"], radius=56, life=0.45, width=3, start_radius=8))
        for i in range(64):
            angle = math.tau * i / 64 + random.uniform(-0.04, 0.04)
            direction = Vec2(math.cos(angle), math.sin(angle))
            speed = random.uniform(120, 260)
            color = random.choice([COLORS["cyan"], COLORS["gold"], (232, 255, 250), (86, 220, 255)])
            self.particles.append(Particle(pos + direction * random.uniform(8, 18), direction * speed, color, life=random.uniform(0.42, 0.82), size=random.randint(3, 5)))
        self.floating_texts.append(FloatingText(pos + Vec2(0, -64), self.t("level_up").format(level=level), COLORS["gold"], life=1.35))
        self.play_sound("levelup", 0.72, cooldown=0.12)

    def create_weapon_upgrade_effect(self, pos, evolved=False, label=None):
        pos = Vec2(pos)
        main_color = COLORS["purple"] if evolved else COLORS["orange"]
        self.rings.append(PulseRing(pos, main_color, radius=74 if evolved else 58, life=0.55, width=4, start_radius=10))
        self.rings.append(PulseRing(pos, COLORS["cyan"], radius=42, life=0.38, width=2, start_radius=6))
        for i in range(42 if evolved else 30):
            angle = math.tau * i / (42 if evolved else 30) + random.uniform(-0.1, 0.1)
            direction = Vec2(math.cos(angle), math.sin(angle))
            color = random.choice([main_color, COLORS["gold"], COLORS["cyan"], (255, 232, 156)])
            self.particles.append(Particle(pos + direction * random.uniform(5, 14), direction * random.uniform(90, 210), color, life=random.uniform(0.32, 0.68), size=random.randint(2, 4)))
        label = label or self.t("upgrade")
        self.floating_texts.append(FloatingText(pos + Vec2(0, -54), label, main_color, life=1.1))
        self.play_sound("weapon_upgrade", 0.66 if evolved else 0.52, cooldown=0.12)

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

    def weapon_ammo_text(self):
        weapon = self.player.weapon
        if weapon.is_reloading:
            return f"{self.t('reloading')} {weapon.reload_timer:.1f}s"
        return f"{self.t('ammo')} {weapon.ammo}/{weapon.magazine_size}"

    def weapon_reload_text(self):
        weapon = self.player.weapon
        if weapon.is_reloading:
            return f"{self.t('reloading')} {weapon.reload_timer:.1f}s"
        return f"{self.t('reload')} {weapon.reload_time:.1f}s"

    def difficulty_cfg(self):
        return DIFFICULTIES.get(self.difficulty_id, DIFFICULTIES["normal"])

    def structure_balance_cfg(self):
        return STRUCTURE_DIFFICULTY_BALANCE.get(self.difficulty_id, STRUCTURE_DIFFICULTY_BALANCE["normal"])

    def scaled_wave_count(self, count):
        return max(1, int(round(count * self.difficulty_cfg()["count"])))

    def fence_level(self):
        progress = max(self.wave, self.player.level)
        level = 1 + progress // 4
        if self.character_id == "engineer" and progress >= 4:
            level += 1
        return int(clamp(level, 1, MAX_FENCE_LEVEL))

    def fence_stats_for_level(self, level):
        level = int(clamp(level, 1, MAX_FENCE_LEVEL))
        stats = dict(FENCE_TIER_STATS[level])
        balance = self.structure_balance_cfg()
        stats["level"] = level
        stats["hp"] = max(1, int(round(stats["hp"] * balance["hp"] * balance.get("fence_hp", 1.0))))
        stats["range"] = 0
        stats["damage"] = 0
        stats["cooldown"] = 0
        return stats

    def structure_stats(self, kind, level=None):
        cfg = STRUCTURE_TYPES[kind]
        balance = self.structure_balance_cfg()
        if kind == "fence":
            return self.fence_stats_for_level(level or self.fence_level())
        if kind == "gate":
            return {
                "hp": max(1, int(round(cfg["hp"] * balance["hp"] * balance.get("fence_hp", 1.0)))),
                "range": 0,
                "damage": 0,
                "cooldown": 0,
                "damage_reduction": 0.18,
            }
        hp_multiplier = balance["hp"]
        return {
            "hp": max(1, int(round(cfg["hp"] * hp_multiplier))),
            "range": max(0, int(round(cfg["range"] * balance["turret_range"]))),
            "damage": max(0, int(round(cfg["damage"] * balance["turret_damage"]))),
            "cooldown": max(0.08, cfg["cooldown"] * balance["turret_cooldown"]),
        }

    def structure_cost(self, kind):
        base_cost = STRUCTURE_TYPES[kind]["cost"]
        if kind == "fence":
            base_cost = int(round(base_cost * (1 + (self.fence_level() - 1) * 0.32)))
        difficulty_cost = self.structure_balance_cfg()["cost"]
        discount = CHARACTERS.get(self.character_id, CHARACTERS["soldier"])["build_discount"]
        return max(1, int(round(base_cost * difficulty_cost * (1 - discount))))

    def fence_upgrade_cost(self, target_level):
        difficulty_cost = self.structure_balance_cfg()["cost"]
        discount = CHARACTERS.get(self.character_id, CHARACTERS["soldier"])["build_discount"]
        return max(1, int(round((28 + target_level * 26) * difficulty_cost * (1 - discount))))

    def repair_cost(self):
        difficulty_cost = self.structure_balance_cfg()["repair_cost"]
        discount = CHARACTERS.get(self.character_id, CHARACTERS["soldier"])["build_discount"]
        return max(1, int(round(15 * difficulty_cost * (1 - discount))))

    def turret_count(self):
        return len([s for s in self.structures if s.alive and s.kind == "turret"])

    def turret_limit(self):
        base = TURRET_LIMITS.get(self.difficulty_id, TURRET_LIMITS["normal"])
        if self.character_id == "engineer":
            base += 1
        return base

    def can_afford(self, cost):
        return self.dev_mode or self.player.gold >= cost

    def spend_gold(self, cost):
        if not self.dev_mode:
            self.player.gold -= cost

    def draw_text_center(self, text, rect, color=None, font=None):
        self.ui.draw_text_center(self.screen, text, rect, color or COLORS["text"], font or self.font)

    def draw_panel(self, rect, color=(18, 20, 25), alpha=210, border=True):
        self.ui.draw_panel(self.screen, rect, color=color, alpha=alpha, border=border, border_color=COLORS["hud_line"])

    def draw_button(self, key, rect, label, *, active=False, disabled=False, font=None):
        self.ui.draw_button(
            self.screen,
            self.ui_buttons,
            key,
            rect,
            label,
            colors=COLORS,
            active=active,
            disabled=disabled,
            font=font or self.font,
        )

    def draw_cover_image(self, image, darken=88):
        sw, sh = self.screen_w, self.screen_h
        iw, ih = image.get_size()
        scale = max(sw / iw, sh / ih)
        size = (max(1, math.ceil(iw * scale)), max(1, math.ceil(ih * scale)))
        scaled = pygame.transform.smoothscale(image, size)
        rect = scaled.get_rect(center=(sw // 2, sh // 2))
        self.screen.blit(scaled, rect)
        veil = pygame.Surface((sw, sh), pygame.SRCALPHA)
        veil.fill((0, 0, 0, darken))
        self.screen.blit(veil, (0, 0))

    def draw_menu_background(self, map_id=None, use_menu_art=False):
        if use_menu_art and self.menu_background is not None:
            self.draw_cover_image(self.menu_background, darken=88)
            return
        map_id = map_id or self.map_id
        theme = MAP_THEMES.get(map_id, MAP_THEMES["warehouse"])
        sw, sh, s = self.screen_w, self.screen_h, self.ui_scale
        self.screen.fill(theme["bg"])
        grid = max(30, int(42 * s))
        for y in range(0, sh, grid):
            pygame.draw.line(self.screen, theme["grid"], (0, y), (sw, y), 1)
        for x in range(0, sw, grid):
            pygame.draw.line(self.screen, theme["grid"], (x, 0), (x, sh), 1)

        horizon = int(sh * 0.64)
        pygame.draw.rect(self.screen, (10, 12, 15), (0, horizon, sw, sh - horizon))
        for i in range(-2, sw // grid + 4):
            x = i * grid + int((pygame.time.get_ticks() * 0.012) % grid)
            pygame.draw.line(self.screen, theme["grid"], (x, horizon), (x - int(170 * s), sh), 1)
        for i in range(7):
            y = horizon + int((i + 1) * (sh - horizon) / 8)
            pygame.draw.line(self.screen, theme["grid"], (0, y), (sw, y), 1)

        for i in range(32):
            n = tile_noise(i, len(map_id), 77)
            x = int((n % max(1, sw)))
            y = int((n >> 8) % max(1, sh))
            if map_id == "warehouse":
                color = theme["prop_b"] if i % 3 else theme["accent"]
                pygame.draw.rect(self.screen, color, (x, y, int(18 * s), max(2, int(4 * s))))
            elif map_id == "crossfire":
                color = theme["accent"] if i % 2 else theme["prop_a"]
                pygame.draw.line(self.screen, color, (x, y), (x + int(26 * s), y + int(10 * s)), 2)
            else:
                color = theme["prop_a"] if i % 2 else theme["prop_c"]
                pygame.draw.circle(self.screen, color, (x, y), max(2, int(3 * s)))

        veil = pygame.Surface((sw, sh), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 82))
        self.screen.blit(veil, (0, 0))

    def draw_select_card(self, key, rect, title, subtitle="", *, active=False, accent=None):
        self.ui.draw_select_card(
            self.screen,
            self.ui_buttons,
            key,
            rect,
            title,
            subtitle,
            active=active,
            accent=accent or COLORS["cyan"],
            colors=COLORS,
            small_font=self.small_font,
            tiny_font=self.tiny_font,
            ui_scale=self.ui_scale,
        )

    def fit_text(self, text, font, max_width):
        return self.ui.fit_text(text, font, max_width)

    def draw_map_preview(self, rect, map_id, title=True):
        theme = MAP_THEMES.get(map_id, MAP_THEMES["warehouse"])
        pygame.draw.rect(self.screen, (19, 22, 27), rect, border_radius=8)
        pygame.draw.rect(self.screen, theme["accent"], rect, 2, border_radius=8)
        label_h = max(34, int(42 * self.ui_scale)) if title else 0
        inner = pygame.Rect(rect.x + 16, rect.y + 14 + label_h, rect.w - 32, rect.h - 28 - label_h)
        if title:
            self.draw_text_center(self.map_name(map_id), pygame.Rect(rect.x + 12, rect.y + 8, rect.w - 24, label_h - 4), theme["accent"], self.font)
        rows = self.map_manager.maps.get(map_id, MAP_ROWS)
        grid_w = max(1, len(rows[0]))
        grid_h = max(1, len(rows))
        cell = max(2, int(min(inner.w / grid_w, inner.h / grid_h)))
        map_w, map_h = grid_w * cell, grid_h * cell
        ox = inner.centerx - map_w // 2
        oy = inner.centery - map_h // 2
        preview_rect = pygame.Rect(ox, oy, map_w, map_h)
        pygame.draw.rect(self.screen, theme["bg"], preview_rect)
        for y, row in enumerate(rows):
            for x, value in enumerate(row):
                tile = pygame.Rect(ox + x * cell, oy + y * cell, cell, cell)
                if value == "#":
                    pygame.draw.rect(self.screen, theme["wall"], tile)
                    if cell >= 5:
                        pygame.draw.rect(self.screen, theme["wall_light"], tile.inflate(-cell // 2, -cell // 2))
                else:
                    color = theme["floor_a"] if (x + y) % 2 == 0 else theme["floor_b"]
                    pygame.draw.rect(self.screen, color, tile)
                    if cell >= 5 and tile_noise(x, y, 5) % 19 == 0:
                        pygame.draw.rect(self.screen, theme["prop_a"], tile.inflate(-cell // 2, -cell // 2))
        pygame.draw.rect(self.screen, theme["grid"], preview_rect, 1)

    def draw_character_preview(self, rect, character_id):
        pygame.draw.rect(self.screen, (19, 22, 27), rect, border_radius=8)
        pygame.draw.rect(self.screen, COLORS["cyan"], rect, 2, border_radius=8)
        ticks = pygame.time.get_ticks()
        facing = ("down", "right", "up", "left")[(ticks // 1100) % 4]
        frame = (ticks // 150) % 4
        sprite = self.sprites.get(f"player_{character_id}_{facing}_{frame}", self.sprites["player"])
        scale = max(2, int(min((rect.w * 0.48) / sprite.get_width(), (rect.h * 0.5) / sprite.get_height())))
        preview = pygame.transform.scale(sprite, (sprite.get_width() * scale, sprite.get_height() * scale))
        preview_rect = preview.get_rect(center=(rect.centerx, rect.y + int(rect.h * 0.36)))
        pygame.draw.ellipse(self.screen, (8, 10, 13), (preview_rect.centerx - preview_rect.w // 2, preview_rect.bottom - 18, preview_rect.w, 22))
        self.screen.blit(preview, preview_rect)
        self.draw_text_center(self.character_name(character_id), pygame.Rect(rect.x + 12, rect.y + int(rect.h * 0.62), rect.w - 24, 34), COLORS["gold"], self.font)
        self.draw_text_center(self.fit_text(self.character_description(character_id), self.tiny_font, rect.w - 44), pygame.Rect(rect.x + 18, rect.y + int(rect.h * 0.72), rect.w - 36, 30), COLORS["muted"], self.tiny_font)
        cfg = CHARACTERS.get(character_id, CHARACTERS["soldier"])
        stat = f"{self.t('hp')} {cfg['hp']} | {self.t('armor')} {cfg['armor']} | {self.t('magnet')} {cfg['pickup_radius']}"
        self.draw_text_center(stat, pygame.Rect(rect.x + 18, rect.bottom - 44, rect.w - 36, 28), COLORS["cyan"], self.tiny_font)

    def screen_to_world(self, pos):
        if not self.world_rect.collidepoint(pos):
            return None
        x = (pos[0] - self.world_rect.x) / self.world_scale
        y = (pos[1] - self.world_rect.y) / self.world_scale
        if 0 <= x < WORLD_W and 0 <= y < WORLD_H:
            return Vec2(x, y)
        return None

    def world_to_screen(self, pos):
        pos = Vec2(pos)
        return Vec2(self.world_rect.x + pos.x * self.world_scale, self.world_rect.y + pos.y * self.world_scale)

    def world_rect_to_screen(self, rect):
        return pygame.Rect(
            int(self.world_rect.x + rect.x * self.world_scale),
            int(self.world_rect.y + rect.y * self.world_scale),
            max(1, int(rect.w * self.world_scale)),
            max(1, int(rect.h * self.world_scale)),
        )

    def mouse_world(self):
        return self.screen_to_world(pygame.mouse.get_pos())

    def can_place_building(self, position, building_type):
        if building_type not in STRUCTURE_TYPES:
            return False, "build_cannot_place"
        if hasattr(position, "x") and hasattr(position, "y"):
            cell = self.tile_map.world_to_cell(Vec2(position))
        else:
            cell = (int(position[0]), int(position[1]))
        if building_type == "turret" and self.turret_count() >= self.turret_limit():
            return False, "turret_limit"
        self.map_manager.update_dynamic_obstacles(self.structures)
        if not self.map_manager.in_bounds(cell) or self.map_manager.is_wall(cell):
            return False, "build_cannot_place"
        if not self.map_manager.is_buildable(cell[0], cell[1]):
            return False, "build_cannot_place"
        if self.tile_map.cell_center(cell).distance_to(self.player.pos) < 40:
            return False, "build_cannot_place"
        if not self.can_afford(self.structure_cost(building_type)):
            return False, "not_enough_gold"
        # Prevent building fences or gates that would fully trap the player (no path to zombie spawns)
        if building_type in ("fence", "gate"):
            player_cell = self.tile_map.world_to_cell(self.player.pos)
            spawn_goals = self.spawn_cells or self.build_spawn_cells()
            blocked = set(self.map_manager.dynamic_obstacles) | {cell}
            path_ok = False
            for goal in (spawn_goals or []):
                if find_path(self.tile_map, player_cell, goal, blocked=blocked, allow_diagonal=True, weight=1.05, radius=int(self.player.radius)):
                    path_ok = True
                    break
            if not path_ok:
                return False, "would_trap_player"
        return True, ""

    def building_block_reason_text(self, reason):
        if reason == "not_enough_gold":
            return self.t("not_enough_gold")
        if reason == "turret_limit":
            return self.t("turret_limit").format(count=self.turret_count(), limit=self.turret_limit())
        if reason == "would_trap_player":
            return self.t("would_trap_player")
        return self.t("build_cannot_place")

    def structure_at_world(self, pos):
        if pos is None:
            return None
        for structure in reversed(self.structures):
            if structure.alive and structure.rect.inflate(5, 5).collidepoint((pos.x, pos.y)):
                return structure
        return None

    def nearby_damaged_structure(self, distance=90):
        damaged = [
            structure
            for structure in self.structures
            if structure.alive and structure.hp < structure.max_hp and Vec2(structure.rect.center).distance_to(self.player.pos) <= distance
        ]
        if not damaged:
            return None
        return min(damaged, key=lambda structure: Vec2(structure.rect.center).distance_squared_to(self.player.pos))

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

    def titan_leap_cooldown(self):
        return TITAN_LEAP_COOLDOWNS.get(self.difficulty_id, TITAN_LEAP_COOLDOWNS["normal"])

    def titan_stuck_threshold(self):
        return TITAN_STUCK_LEAP_SECONDS.get(self.difficulty_id, TITAN_STUCK_LEAP_SECONDS["normal"])

    def titan_has_reasonable_path(self, titan):
        self.refresh_pathfinding_context()
        start = nearest_clear_cell(self.tile_map, self.tile_map.world_to_cell(titan.pos), titan.radius, max_distance=8)
        goal = nearest_clear_cell(
            self.tile_map,
            self.tile_map.world_to_cell(self.player.pos),
            titan.radius,
            max_distance=12,
            prefer_pos=titan.pos,
        )
        if start is None or goal is None:
            return False
        path = find_path(
            self.tile_map,
            start,
            goal,
            self.path_blockers,
            allow_diagonal=True,
            weight=1.05,
            radius=titan.radius,
            max_nodes=900,
        )
        return bool(path)

    def titan_cell_clear(self, cell, radius):
        return (
            self.tile_map.in_bounds(cell)
            and cell not in self.path_blockers
            and self.tile_map.is_clear_for_radius(cell, radius)
        )

    def titan_open_neighbor_count(self, cell, radius):
        return sum(
            1
            for dx, dy in ORTHO_NEIGHBORS
            if self.titan_cell_clear((cell[0] + dx, cell[1] + dy), radius)
        )

    def titan_cell_has_escape_route(self, cell, radius):
        if self.titan_open_neighbor_count(cell, radius) < 3:
            return False
        goals = [
            goal
            for goal in self.boss_spawn_cells
            if goal != cell and self.tile_map.cell_center(goal).distance_to(self.player.pos) > TITAN_LEAP_MIN_PLAYER_DISTANCE
        ]
        if not goals:
            return False
        step = max(1, len(goals) // 18)
        for goal in goals[::step]:
            path = find_path(
                self.tile_map,
                cell,
                goal,
                self.path_blockers,
                allow_diagonal=True,
                weight=1.05,
                radius=radius,
                max_nodes=560,
            )
            if path:
                return True
        return False

    def find_titan_leap_cell(self, titan):
        self.refresh_pathfinding_context()
        player_cell = self.tile_map.world_to_cell(self.player.pos)
        candidates = []
        for ring in range(6, 11):
            for y in range(player_cell[1] - ring, player_cell[1] + ring + 1):
                for x in range(player_cell[0] - ring, player_cell[0] + ring + 1):
                    if max(abs(x - player_cell[0]), abs(y - player_cell[1])) != ring:
                        continue
                    cell = (x, y)
                    if not self.titan_cell_clear(cell, titan.radius):
                        continue
                    center = self.tile_map.cell_center(cell)
                    player_distance = center.distance_to(self.player.pos)
                    if player_distance < TITAN_LEAP_MIN_PLAYER_DISTANCE:
                        continue
                    if not self.titan_cell_has_escape_route(cell, titan.radius):
                        continue
                    score = abs(player_distance - 260) + center.distance_to(titan.pos) * 0.18 + (tile_noise(x, y, 91) % 17)
                    candidates.append((score, cell))
        if not candidates:
            return None
        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]

    def apply_bile(self, pos):
        self.bile_timer = BILE_BOOST_DURATION
        self.message = self.t("boomer_bile")
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

    def build_spawn_cells(self):
        return self.map_manager.get_zombie_spawns()

    def build_boss_spawn_cells(self):
        radius = ZOMBIE_TYPES["titan"]["radius"]
        return self.map_manager.get_boss_spawns(radius)

    def find_player_spawn_cell(self):
        return self.map_manager.get_player_spawn(self.player.radius + 4)

    def teleport_player_to_spawn(self, effect=False):
        cell = self.find_player_spawn_cell()
        if cell is None:
            return
        self.player.pos = self.tile_map.cell_center(cell)
        self.player.last_move_dir = Vec2(0, 1)
        self.player.facing = "down"
        self.player.anim_time = 0
        self.player.is_moving = False
        if effect:
            self.create_teleport_effect(self.player.pos)

    def blocked_cells(self):
        self.map_manager.update_dynamic_obstacles(self.structures)
        return set(self.map_manager.dynamic_obstacles)

    def refresh_pathfinding_context(self):
        blockers = self.blocked_cells()
        player_cell = self.tile_map.world_to_cell(self.player.pos)
        signature = (self.tile_map.map_id, player_cell, tuple(sorted(blockers)))
        if signature == self.path_signature:
            return
        self.path_signature = signature
        self.path_blockers = blockers
        self.path_cache = {}
        self.flow_field = build_distance_field(self.tile_map, [player_cell], blockers)

    def flow_direction(self, pos):
        cell = self.tile_map.world_to_cell(pos)
        if not self.flow_field or cell not in self.flow_field:
            return None
        best_cell = None
        best_score = self.flow_field[cell]
        for dx, dy in DIAGONAL_NEIGHBORS:
            nxt = (cell[0] + dx, cell[1] + dy)
            if nxt not in self.flow_field:
                continue
            score = self.flow_field[nxt] + (0.12 if dx and dy else 0)
            if score < best_score:
                best_cell = nxt
                best_score = score
        if best_cell is None:
            return None
        direction = self.tile_map.cell_center(best_cell) - Vec2(pos)
        if direction.length_squared() <= 1:
            return None
        return direction.normalize()

    def cached_path(self, strategy, start, goal, *, allow_diagonal=False, weight=1.0, radius=0, max_nodes=700, smooth=False):
        self.refresh_pathfinding_context()
        cache_key = (
            strategy,
            start,
            goal,
            allow_diagonal,
            round(weight, 2),
            int(radius),
            bool(smooth),
            self.path_signature,
        )
        if cache_key not in self.path_cache:
            path = find_path(
                self.tile_map,
                start,
                goal,
                self.path_blockers,
                allow_diagonal=allow_diagonal,
                weight=weight,
                radius=radius,
                max_nodes=max_nodes,
            )
            if smooth:
                path = smooth_path(self.tile_map, start, path, self.path_blockers, radius)
            self.path_cache[cache_key] = path
        return list(self.path_cache[cache_key])

    def nearest_walkable_cell(self, target_cell, radius=0, max_distance=8, prefer_pos=None):
        if self.tile_map.in_bounds(target_cell) and target_cell not in self.path_blockers:
            if radius > 0:
                if self.tile_map.is_clear_for_radius(target_cell, radius):
                    return target_cell
            elif not self.tile_map.is_wall(target_cell):
                return target_cell
        ox, oy = target_cell
        best = None
        best_score = 1_000_000
        for distance in range(1, max_distance + 1):
            for y in range(oy - distance, oy + distance + 1):
                for x in range(ox - distance, ox + distance + 1):
                    cell = (x, y)
                    if abs(x - ox) != distance and abs(y - oy) != distance:
                        continue
                    if cell in self.path_blockers or not self.tile_map.in_bounds(cell):
                        continue
                    if radius > 0:
                        if not self.tile_map.is_clear_for_radius(cell, radius):
                            continue
                    elif self.tile_map.is_wall(cell):
                        continue
                    score = abs(x - ox) + abs(y - oy)
                    if prefer_pos is not None:
                        score += self.tile_map.cell_center(cell).distance_to(prefer_pos) / TILE
                    if score < best_score:
                        best = cell
                        best_score = score
            if best is not None:
                return best
        return None

    def predicted_player_cell(self, lead_tiles=3):
        self.refresh_pathfinding_context()
        direction = Vec2(self.player.last_move_dir)
        if direction.length_squared() <= 0:
            direction = Vec2(self.player.aim_dir)
        if direction.length_squared() <= 0:
            direction = Vec2(0, 1)
        target_pos = self.player.pos + direction.normalize() * TILE * lead_tiles
        target_pos.x = clamp(target_pos.x, TILE * 1.5, WORLD_W - TILE * 1.5)
        target_pos.y = clamp(target_pos.y, TILE * 1.5, WORLD_H - TILE * 1.5)
        return self.nearest_walkable_cell(self.tile_map.world_to_cell(target_pos), max_distance=7, prefer_pos=self.player.pos)

    def spitter_goal_cell(self, zombie_pos):
        self.refresh_pathfinding_context()
        player_cell = self.tile_map.world_to_cell(self.player.pos)
        best = None
        best_score = 1_000_000
        for radius in range(5, 10):
            for y in range(player_cell[1] - radius, player_cell[1] + radius + 1):
                for x in range(player_cell[0] - radius, player_cell[0] + radius + 1):
                    if max(abs(x - player_cell[0]), abs(y - player_cell[1])) != radius:
                        continue
                    cell = (x, y)
                    if cell in self.path_blockers or not self.tile_map.in_bounds(cell) or self.tile_map.is_wall(cell):
                        continue
                    center = self.tile_map.cell_center(cell)
                    dist = center.distance_to(self.player.pos)
                    if not (160 <= dist <= 330) or not has_wall_line(self.tile_map, center, self.player.pos):
                        continue
                    score = abs(dist - 235) + center.distance_to(zombie_pos) * 0.32
                    if score < best_score:
                        best = cell
                        best_score = score
        return best or self.predicted_player_cell(1) or player_cell

    def stalker_flank_cell(self, zombie_pos):
        direction = Vec2(self.player.last_move_dir)
        if direction.length_squared() <= 0:
            direction = Vec2(self.player.pos) - Vec2(zombie_pos)
        if direction.length_squared() <= 0:
            direction = Vec2(0, 1)
        direction = direction.normalize()
        side = Vec2(-direction.y, direction.x)
        candidates = [
            self.player.pos - direction * TILE * 3 + side * TILE * 2,
            self.player.pos - direction * TILE * 3 - side * TILE * 2,
            self.player.pos + side * TILE * 4,
            self.player.pos - side * TILE * 4,
        ]
        best = None
        best_score = 1_000_000
        for pos in candidates:
            pos.x = clamp(pos.x, TILE * 1.5, WORLD_W - TILE * 1.5)
            pos.y = clamp(pos.y, TILE * 1.5, WORLD_H - TILE * 1.5)
            cell = self.nearest_walkable_cell(self.tile_map.world_to_cell(pos), max_distance=5, prefer_pos=zombie_pos)
            if cell is None:
                continue
            score = self.tile_map.cell_center(cell).distance_to(zombie_pos)
            if score < best_score:
                best = cell
                best_score = score
        return best or self.tile_map.world_to_cell(self.player.pos)

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
        self.message = self.t("wave_label").format(wave=self.wave)
        self.message_timer = 2.0
        self.wave_banner_text = self.t("wave_start_banner").format(wave=self.wave)
        self.wave_banner_timer = 2.0
        self.play_sound("wave", 0.42, cooldown=0.5)
        if self.wave == 1 or random.random() < 0.72:
            self.spawn_powerup()

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
        elite = kind != "titan" and random.random() < self.elite_chance()
        self.zombies.append(Zombie(kind, pos, self.wave, self.difficulty_id, elite=elite))
        if kind == "titan":
            self.titan_banner_timer = 3.0
        if random.random() < (0.95 if kind == "titan" else 0.18):
            self.play_zombie_sound("titan" if kind == "titan" else "groan", kind, volume=0.72 if kind == "titan" else 0.24, cooldown=0.95)
        if elite and random.random() < 0.28:
            self.message = self.t("elite_incoming")
            self.message_timer = 1.4

    def spawn_minion_near(self, kind, pos, min_player_distance=90, prefer_spawn_edges=False, require_path=False):
        radius = ZOMBIE_TYPES[kind]["radius"]
        origin = self.tile_map.world_to_cell(pos)
        cells = []
        blocked = self.blocked_cells()
        player_cell = self.tile_map.world_to_cell(self.player.pos)

        def valid_summon_cell(cell):
            if cell in blocked or not self.tile_map.is_clear_for_radius(cell, radius):
                return False
            center = self.tile_map.cell_center(cell)
            if center.distance_to(self.player.pos) < min_player_distance:
                return False
            if require_path:
                path = find_path(
                    self.tile_map,
                    cell,
                    player_cell,
                    blocked,
                    allow_diagonal=True,
                    weight=1.08,
                    radius=radius,
                    max_nodes=800,
                )
                if not path:
                    return False
            return True

        if prefer_spawn_edges:
            edge_cells = [cell for cell in self.spawn_cells if valid_summon_cell(cell)]
            if edge_cells:
                edge_cells.sort(key=lambda cell: self.tile_map.cell_center(cell).distance_to(pos))
                choices = edge_cells[: min(4, len(edge_cells))]
                self.zombies.append(Zombie(kind, self.tile_map.cell_center(random.choice(choices)), self.wave, self.difficulty_id))
                if random.random() < 0.2:
                    self.play_zombie_sound("groan", kind, volume=0.2, cooldown=0.8)
                return

        for distance in range(2, 8):
            for y in range(origin[1] - distance, origin[1] + distance + 1):
                for x in range(origin[0] - distance, origin[0] + distance + 1):
                    cell = (x, y)
                    if abs(x - origin[0]) != distance and abs(y - origin[1]) != distance:
                        continue
                    if not valid_summon_cell(cell):
                        continue
                    cells.append(cell)
            if cells:
                break
        if not cells:
            self.spawn_zombie(kind)
            return
        self.zombies.append(Zombie(kind, self.tile_map.cell_center(random.choice(cells)), self.wave, self.difficulty_id))
        if random.random() < 0.2:
            self.play_zombie_sound("groan", kind, volume=0.2, cooldown=0.8)

    def drop_gold(self, pos, total):
        chunks = max(1, min(5, total // 7))
        remaining = total
        for i in range(chunks):
            amount = remaining // (chunks - i)
            remaining -= amount
            self.gold_drops.append(GoldDrop(pos, amount))

    def random_floor_position(self, min_player_distance=120):
        for _ in range(80):
            cell = random.choice(self.spawn_cells or [(self.map_manager.grid_w // 2, self.map_manager.grid_h // 2)])
            if self.tile_map.is_wall(cell):
                continue
            pos = self.tile_map.cell_center(cell)
            if pos.distance_to(self.player.pos) < min_player_distance:
                continue
            return pos
        return Vec2(self.map_manager.world_w / 2, self.map_manager.world_h / 2)

    def spawn_powerup(self, pos=None, kind=None):
        if kind is None:
            weights = ["medkit", "overdrive", "shield", "haste", "shock"]
            if self.player.hp < self.player.max_hp * 0.55:
                weights += ["medkit", "medkit"]
            kind = random.choice(weights)
        if pos is None:
            pos = self.random_floor_position()
        self.powerups.append(PowerUpDrop(pos, kind))

    def elite_chance(self):
        if self.wave < 3:
            return 0.0
        base = min(0.08 + self.wave * 0.008, 0.24)
        if self.difficulty_id == "easy":
            base -= 0.035
        elif self.difficulty_id == "hard":
            base += 0.035
        elif self.difficulty_id == "nightmare":
            base += 0.065
        return clamp(base, 0, 0.32)

    def place_structure(self, kind, cell):
        valid, reason = self.can_place_building(cell, kind)
        if not valid:
            self.message = self.building_block_reason_text(reason)
            self.message_timer = 1.4
            return False
        cost = self.structure_cost(kind)
        self.spend_gold(cost)
        self.structures.append(Structure(kind, cell, self.structure_stats(kind)))
        self.message = self.t("built").format(name=self.structure_name(kind))
        self.message_timer = 1.2
        self.play_sound("build", 0.55, cooldown=0.12)
        return True

    def repair_nearest(self):
        damaged = [s for s in self.structures if s.alive and s.hp < s.max_hp]
        nearby_damaged = [s for s in damaged if Vec2(s.rect.center).distance_to(self.player.pos) <= 90]
        if not nearby_damaged:
            if self.upgrade_nearest_fence():
                return
            self.message = self.t("move_closer_repair") if damaged else self.t("no_damaged_structure")
            self.message_timer = 1.3
            return
        nearest = min(nearby_damaged, key=lambda s: Vec2(s.rect.center).distance_squared_to(self.player.pos))
        cost = self.repair_cost()
        if not self.can_afford(cost):
            self.message = self.t("need_gold_repair").format(cost=cost)
            self.message_timer = 1.3
            return
        self.spend_gold(cost)
        repair_amount = int(round(70 * self.structure_balance_cfg()["repair_amount"]))
        nearest.repair(repair_amount)
        self.floating_texts.append(FloatingText(Vec2(nearest.rect.center), self.t("repair_float"), COLORS["green"]))
        self.play_sound("build", 0.42, cooldown=0.12)

    def reload_weapon(self):
        weapon = self.player.weapon
        if weapon.is_reloading:
            self.message = self.weapon_reload_text()
            self.message_timer = 0.9
            return False
        if weapon.ammo >= weapon.magazine_size:
            self.message = self.t("reload_full")
            self.message_timer = 1.0
            return False
        weapon.start_reload()
        self.message = self.t("reload_started")
        self.message_timer = 1.0
        self.play_sound("reload", 0.42, cooldown=0.12)
        return True

    def upgrade_nearest_fence(self):
        fences = [s for s in self.structures if s.alive and s.kind == "fence" and Vec2(s.rect.center).distance_to(self.player.pos) <= 90]
        if not fences:
            return False
        nearest = min(fences, key=lambda s: Vec2(s.rect.center).distance_squared_to(self.player.pos))
        target_level = min(self.fence_level(), nearest.level + 1)
        if nearest.level >= target_level:
            self.message = self.t("fence_max")
            self.message_timer = 1.3
            return True
        cost = self.fence_upgrade_cost(target_level)
        if not self.can_afford(cost):
            self.message = self.t("need_gold_fence_upgrade").format(cost=cost)
            self.message_timer = 1.3
            return True
        self.spend_gold(cost)
        nearest.upgrade_to(self.structure_stats("fence", level=target_level))
        center = Vec2(nearest.rect.center)
        self.floating_texts.append(FloatingText(center, self.t("fence_upgraded").format(level=target_level), COLORS["gold"], life=1.1))
        self.create_shockwave(center, 48, 0, visual_only=True)
        self.play_sound("build", 0.5, cooldown=0.12)
        return True

    def upgrade_weapon(self):
        if self.player.weapon.is_maxed:
            self.message = self.t("weapon_max").format(weapon=self.weapon_name(self.player.weapon.tier_name))
            self.message_timer = 1.4
            return
        cost = self.player.weapon.upgrade_cost
        if not self.can_afford(cost):
            self.message = self.t("need_gold").format(cost=cost)
            self.message_timer = 1.3
            return
        self.spend_gold(cost)
        old_name = self.player.weapon.tier_name
        self.player.weapon.upgrade()
        new_name = self.player.weapon.tier_name
        if new_name != old_name:
            self.message = self.t("weapon_evolved").format(weapon=self.weapon_name(new_name))
        else:
            self.message = self.t("weapon_upgraded").format(weapon=self.weapon_name(new_name), level=self.player.weapon.level)
        self.message_timer = 1.8
        effect_label = self.weapon_name(new_name) if new_name != old_name else self.t("upgrade")
        self.create_weapon_upgrade_effect(self.player.pos, evolved=new_name != old_name, label=effect_label)

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

    def create_explosion(self, pos, radius, damage, enemy_owned=True, visual_only=False, sound_name="explosion", sound_volume=0.5):
        self.play_sound(sound_name, sound_volume, cooldown=0.18)
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

    def create_teleport_effect(self, pos):
        pos = Vec2(pos)
        theme = MAP_THEMES.get(self.map_id, MAP_THEMES["warehouse"])
        colors = (COLORS["cyan"], theme["accent"], COLORS["blue"], COLORS["gold"])
        for i in range(42):
            angle = i / 42 * math.tau
            direction = Vec2(math.cos(angle), math.sin(angle))
            start = pos + direction * random.uniform(4, 18)
            velocity = direction * random.uniform(70, 230) + Vec2(0, random.uniform(-90, 20))
            self.particles.append(Particle(start, velocity, random.choice(colors), life=random.uniform(0.34, 0.72), size=random.randint(2, 5)))
        for _ in range(18):
            angle = random.uniform(0, math.tau)
            radius = random.uniform(6, 30)
            start = pos + Vec2(math.cos(angle), math.sin(angle)) * radius
            velocity = Vec2(0, -random.uniform(80, 180)).rotate(random.uniform(-18, 18))
            self.particles.append(Particle(start, velocity, random.choice(colors), life=random.uniform(0.28, 0.55), size=3))
        self.create_shockwave(pos, 70, 0, visual_only=True)
        self.floating_texts.append(FloatingText(pos + Vec2(0, -48), self.t("teleport"), theme["accent"], life=1.0))
        self.play_sound("dash", 0.34, cooldown=0.12)

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
                elif not self.paused and event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    self.player.start_dash(self)
                elif event.key == pygame.K_F10:
                    self.dev_mode = not self.dev_mode
                    self.message = self.t("dev_on") if self.dev_mode else self.t("dev_off")
                    self.message_timer = 1.5
                elif not self.paused and event.key == pygame.K_SPACE:
                    self.start_wave()
                elif not self.paused and event.key == pygame.K_i:
                    self.info_panel_open = not self.info_panel_open
                elif not self.paused and event.key == pygame.K_1:
                    self.upgrade_weapon()
                elif not self.paused and event.key == pygame.K_2:
                    self.build_mode = "turret"
                    self.message = self.t("build_mode").format(name=self.structure_name("turret"))
                    self.message_timer = 1.0
                elif not self.paused and event.key == pygame.K_3:
                    self.build_mode = "fence"
                    self.message = self.t("build_mode").format(name=self.structure_name("fence"))
                    self.message_timer = 1.0
                elif not self.paused and event.key == pygame.K_4:
                    self.build_mode = "gate"
                    self.message = self.t("build_mode").format(name=self.structure_name("gate"))
                    self.message_timer = 1.0
                elif event.key == pygame.K_b:
                    self.build_mode = None
                elif not self.paused and event.key == pygame.K_r:
                    self.reload_weapon()
                elif not self.paused and event.key == pygame.K_e:
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
                self.setup_step = "difficulty"
                return True
            if action == "menu_options":
                self.open_options("menu", False)
                return True
            if action == "menu_exit":
                return True
        elif self.state == "setup":
            if action == "setup_next":
                self.advance_setup_step()
                return True
            if action == "setup_begin":
                if self.setup_step != "character":
                    self.advance_setup_step()
                else:
                    self.reset_gameplay()
                    self.state = "playing"
                return True
            if action == "setup_back":
                if not self.retreat_setup_step():
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
            if action.startswith("map_"):
                map_id = action.removeprefix("map_")
                if self.map_manager.has_map(map_id):
                    self.map_id = map_id
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
                self.apply_music_volume()
            elif action == "music_up":
                self.music_volume = min(100, self.music_volume + 10)
                self.apply_music_volume()
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
                self.message = self.t("build_mode").format(name=self.structure_name("turret"))
                self.message_timer = 1.0
            elif not self.paused and action == "hotbar_fence":
                self.build_mode = "fence"
                self.message = self.t("build_mode").format(name=self.structure_name("fence"))
                self.message_timer = 1.0
            elif not self.paused and action == "hotbar_gate":
                self.build_mode = "gate"
                self.message = self.t("build_mode").format(name=self.structure_name("gate"))
                self.message_timer = 1.0
            elif not self.paused and action == "hotbar_reload":
                self.reload_weapon()
            elif not self.paused and action == "hotbar_repair":
                self.repair_nearest()
            elif not self.paused and action == "hotbar_dash":
                self.player.start_dash(self)
            elif not self.paused and action == "auto_toggle_game":
                self.auto_fire = not self.auto_fire
            elif not self.paused and action == "info_toggle":
                self.info_panel_open = not self.info_panel_open
            else:
                return False
            return True
        return action in self.ui_buttons

    def advance_setup_step(self):
        steps = ("difficulty", "map", "character")
        index = steps.index(self.setup_step) if self.setup_step in steps else 0
        self.setup_step = steps[min(len(steps) - 1, index + 1)]

    def retreat_setup_step(self):
        steps = ("difficulty", "map", "character")
        index = steps.index(self.setup_step) if self.setup_step in steps else 0
        if index <= 0:
            return False
        self.setup_step = steps[index - 1]
        return True

    def update(self, dt):
        if self.state != "playing" or self.paused:
            return
        if self.game_over:
            return
        self.message_timer = max(0, self.message_timer - dt)
        self.wave_banner_timer = max(0, self.wave_banner_timer - dt)
        self.titan_banner_timer = max(0, self.titan_banner_timer - dt)
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
                self.message = self.t("wave_clear").format(reward=reward)
                self.message_timer = 3.0
        elif self.wave > 0 and self.wave_break_timer > 0:
            self.wave_break_timer -= dt
            if self.wave_break_timer <= 0:
                self.start_wave()

        self.player.update(dt, self)
        for structure in self.structures:
            structure.update(dt, self)
        self.refresh_pathfinding_context()
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
        for powerup in self.powerups:
            powerup.update(dt, self)
        for particle in self.particles:
            particle.update(dt)
        for ring in self.rings:
            ring.update(dt)
        for warning in self.warning_zones:
            warning.update(dt, self)
        for floating in self.floating_texts:
            floating.update(dt)

        self.zombies = [z for z in self.zombies if z.alive]
        self.bullets = [b for b in self.bullets if b.alive]
        self.lasers = [l for l in self.lasers if l.alive]
        self.acid_projectiles = [a for a in self.acid_projectiles if a.alive]
        self.poison_pools = [p for p in self.poison_pools if p.alive]
        self.structures = [s for s in self.structures if s.alive]
        self.gold_drops = [g for g in self.gold_drops if g.alive]
        self.powerups = [p for p in self.powerups if p.alive]
        self.particles = [p for p in self.particles if p.alive]
        self.rings = [r for r in self.rings if r.alive]
        self.warning_zones = [w for w in self.warning_zones if w.alive]
        self.floating_texts = [f for f in self.floating_texts if f.alive]

    def draw_bar(self, surface, rect, pct, fill, back=(52, 38, 43)):
        self.ui.draw_progress_bar(surface, rect, pct, fill, back, COLORS["hud_line"])

    def draw_world(self):
        world = self.world_surface
        self.map_manager.render(world)
        for pool in self.poison_pools:
            pool.draw(world)
        for gold in self.gold_drops:
            gold.draw(world)
        for powerup in self.powerups:
            powerup.draw(world)
        for structure in self.structures:
            structure.draw(world)
        for warning in self.warning_zones:
            warning.draw(world)
        for bullet in self.bullets:
            bullet.draw(world)
        for laser in self.lasers:
            laser.draw(world)
        for acid in self.acid_projectiles:
            acid.draw(world)
        for zombie in self.zombies:
            zombie.draw(world, self.sprites)
        self.player.draw(world, self.sprites, self.mouse_world())
        for ring in self.rings:
            ring.draw(world)
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
        valid, _ = self.can_place_building(cell, self.build_mode)
        accent = COLORS["green"] if valid else COLORS["red"]
        center = self.tile_map.cell_center(cell)
        stats = self.structure_stats(self.build_mode)

        if self.build_mode == "turret":
            radius = stats["range"]
            diameter = int(radius * 2 + 8)
            ring = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            pygame.draw.circle(ring, (*accent, 28), (diameter // 2, diameter // 2), int(radius))
            pygame.draw.circle(ring, (*accent, 135), (diameter // 2, diameter // 2), int(radius), 2)
            self.world_surface.blit(ring, (center.x - diameter // 2, center.y - diameter // 2))

        overlay = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        overlay.fill((*accent, 88 if valid else 118))
        pygame.draw.rect(overlay, (*accent, 230), overlay.get_rect(), 2)
        if self.build_mode == "turret":
            pygame.draw.circle(overlay, (*accent, 210), (TILE // 2, TILE // 2), 9)
            pygame.draw.rect(overlay, (235, 245, 245, 180), (TILE // 2 - 3, 7, 6, 15))
        elif self.build_mode == "gate":
            pygame.draw.rect(overlay, (*accent, 210), (5, 5, 7, TILE - 10), border_radius=2)
            pygame.draw.rect(overlay, (*accent, 210), (TILE - 12, 5, 7, TILE - 10), border_radius=2)
            pygame.draw.rect(overlay, (*accent, 210), (6, 7, TILE - 12, 5), border_radius=2)
            pygame.draw.rect(overlay, (*accent, 210), (6, TILE - 12, TILE - 12, 5), border_radius=2)
            for x in (TILE // 3, TILE * 2 // 3):
                pygame.draw.line(overlay, (245, 232, 190, 190), (x, 8), (x, TILE - 8), 2)
        else:
            pygame.draw.rect(overlay, (*accent, 210), (5, 8, TILE - 10, 6), border_radius=2)
            pygame.draw.rect(overlay, (*accent, 210), (5, TILE - 13, TILE - 10, 6), border_radius=2)
            for x in (8, TILE // 2 - 3, TILE - 13):
                pygame.draw.rect(overlay, (245, 232, 190, 185), (x, 4, 6, TILE - 8), border_radius=2)
        self.world_surface.blit(overlay, rect)

    def draw_text(self, text, x, y, color=None, font=None):
        self.ui.draw_text(self.screen, text, x, y, color or COLORS["text"], font or self.font)

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
        self.draw_text(self.t("hp"), hp_rect.x - 54, hp_rect.y - 3, COLORS["text"], self.small_font)
        self.draw_bar(self.screen, hp_rect, self.player.hp / self.player.max_hp, COLORS["green"])
        self.draw_text(self.t("xp"), xp_rect.x - 54, xp_rect.y - 4, COLORS["text"], self.small_font)
        self.draw_bar(self.screen, xp_rect, self.player.xp / self.player.next_xp, COLORS["cyan"], (32, 39, 48))
        self.draw_text(f"{self.t('level_short')} {self.player.level}", hp_rect.right + 18, hp_rect.y - 2, COLORS["cyan"], self.small_font)
        ammo_color = COLORS["orange"] if self.player.weapon.is_reloading else COLORS["gold"]
        self.draw_text(self.weapon_ammo_text(), hp_rect.right + 18, xp_rect.y - 4, ammo_color, self.small_font)

        pause_rect = pygame.Rect(sw - self.margin - int(132 * s), hp_rect.y, int(132 * s), max(38, int(46 * s)))
        self.draw_button("pause_toggle", pause_rect, self.t("pause"), font=self.small_font)

        panel = pygame.Rect(0, sh - self.bottom_ui_h, sw, self.bottom_ui_h)
        self.draw_panel(panel, color=(16, 18, 24), alpha=222, border=False)
        pygame.draw.line(self.screen, COLORS["hud_line"], (0, panel.y), (sw, panel.y), 2)

        weapon = self.player.weapon
        slot_w = int(154 * s)
        slot_h = min(int(104 * s), self.bottom_ui_h - max(22, int(42 * s)))
        gap = max(8, int(14 * s))
        total_w = slot_w * 6 + gap * 5
        if total_w > sw - self.margin * 2:
            slot_w = max(96, int((sw - self.margin * 2 - gap * 5) / 6))
            total_w = slot_w * 6 + gap * 5
        start_x = sw // 2 - total_w // 2
        y = panel.y + max(10, (self.bottom_ui_h - slot_h) // 2)

        upgrade_value = self.t("max") if weapon.is_maxed else (self.t("free") if self.dev_mode else f"{weapon.upgrade_cost}g")
        self.draw_hotbar_slot("hotbar_upgrade", pygame.Rect(start_x, y, slot_w, slot_h), "1", self.t("upgrade"), upgrade_value, COLORS["gold"], active=weapon.is_maxed)
        turret_cost = self.t("free") if self.dev_mode else f"{self.structure_cost('turret')}g"
        turret_value = f"{turret_cost} {self.turret_count()}/{self.turret_limit()}"
        fence_value = self.t("free") if self.dev_mode else f"{self.structure_cost('fence')}g"
        fence_level = self.structure_stats("fence")["level"]
        fence_value = f"{fence_value} L{fence_level}"
        self.draw_hotbar_slot("hotbar_turret", pygame.Rect(start_x + (slot_w + gap), y, slot_w, slot_h), "2", self.t("turret"), turret_value, COLORS["cyan"], active=self.build_mode == "turret")
        self.draw_hotbar_slot("hotbar_fence", pygame.Rect(start_x + (slot_w + gap) * 2, y, slot_w, slot_h), "3", self.t("fence"), fence_value, COLORS["orange"], active=self.build_mode == "fence")
        gate_value = self.t("free") if self.dev_mode else f"{self.structure_cost('gate')}g"
        self.draw_hotbar_slot("hotbar_gate", pygame.Rect(start_x + (slot_w + gap) * 3, y, slot_w, slot_h), "4", self.t("gate"), gate_value, COLORS["orange"], active=self.build_mode == "gate")
        auto_text = self.t("on") if self.auto_fire else self.t("off")
        self.draw_hotbar_slot("auto_toggle_game", pygame.Rect(start_x + (slot_w + gap) * 4, y, slot_w, slot_h), "F", self.t("auto_fire"), auto_text, COLORS["green"], active=self.auto_fire)
        info_text = self.t("on") if self.info_panel_open else self.t("off")
        self.draw_hotbar_slot("info_toggle", pygame.Rect(start_x + (slot_w + gap) * 5, y, slot_w, slot_h), "I", self.t("info"), info_text, COLORS["blue"], active=self.info_panel_open)

    def draw_hotbar_slot(self, key, rect, number, label, value, accent, active=False):
        self.ui.draw_hotbar_slot(
            self.screen,
            self.ui_buttons,
            key,
            rect,
            number,
            label,
            value,
            accent,
            active=active,
            colors=COLORS,
            font=self.font,
            small_font=self.small_font,
        )

    def draw_info_panel(self):
        if not self.info_panel_open or self.state != "playing" or self.game_over:
            return
        sw, sh, s = self.screen_w, self.screen_h, self.ui_scale
        panel_w = min(int(520 * s), sw - self.margin * 2)
        panel_h = max(360, int(390 * s))
        panel = pygame.Rect(sw - panel_w - self.margin, self.top_ui_h + int(18 * s), panel_w, panel_h)
        self.draw_panel(panel, alpha=232)

        weapon = self.player.weapon
        overdrive_mult = 1.35 if self.player.buff_timers["overdrive"] > 0 else 1.0
        weapon_damage = int(weapon.damage * (1 + self.player.damage_bonus) * overdrive_mult * self.difficulty_cfg()["player_damage"])
        fire_rate = (1 + self.player.fire_rate_bonus + (0.45 if self.player.buff_timers["overdrive"] > 0 else 0)) / weapon.cooldown
        turret = self.structure_stats("turret")
        fence = self.structure_stats("fence")
        gate = self.structure_stats("gate")
        buffs = [
            f"{self.buff_label(key)} {math.ceil(value)}s"
            for key, value in self.player.buff_timers.items()
            if value > 0
        ]
        dash = self.t("ready") if self.player.dash_cooldown <= 0 else f"{self.player.dash_cooldown:.1f}s"
        lines = [
            (self.t("info"), COLORS["gold"], self.font),
            (f"{self.character_name()} | {self.difficulty_name()} | {self.t('level_short')} {self.player.level}", COLORS["cyan"], self.small_font),
            (f"{self.weapon_name(weapon.tier_name)} {self.t('level_short')} {weapon.level}: {self.t('dmg')} {weapon_damage} | {self.t('rate')} {fire_rate:.1f}/s | {self.t('range_short')} {weapon.bullet_range}", COLORS["text"], self.small_font),
            (f"{self.weapon_ammo_text()} | {self.weapon_reload_text()} | {self.t('shots')} {weapon.bullet_count} | {self.t('pierce')} {weapon.pierce}", COLORS["muted"], self.small_font),
            (f"{self.t('armor')} {self.player.armor} | {self.t('magnet')} {int(self.player.pickup_radius)}", COLORS["muted"], self.small_font),
            (f"{self.t('turrets')} {self.turret_count()}/{self.turret_limit()} | {self.t('cost')} {self.structure_cost('turret')}g | {self.t('hp')} {turret['hp']} | {self.t('dmg')} {turret['damage']}", COLORS["cyan"], self.small_font),
            (f"{self.t('fence_level').format(level=fence['level'])} | {self.t('cost')} {self.structure_cost('fence')}g | {self.t('hp')} {fence['hp']} | {self.t('repair')} {self.repair_cost()}g", COLORS["orange"], self.small_font),
            (f"{self.t('gate')} | {self.t('cost')} {self.structure_cost('gate')}g | {self.t('hp')} {gate['hp']} | {self.t('repair')} {self.repair_cost()}g", COLORS["gold"], self.small_font),
            (f"{self.t('dash')}: {dash} | {self.t('buffs')}: {', '.join(buffs) if buffs else '-'}", COLORS["purple"], self.small_font),
            (f"{self.t('wave_key')} | R {self.t('reload')} | {self.t('repair_key')} | B {self.t('cancel_build')} | I {self.t('close')}", COLORS["muted"], self.tiny_font),
        ]
        x = panel.x + int(24 * s)
        y = panel.y + int(20 * s)
        for text, color, font in lines:
            self.draw_text(text, x, y, color, font)
            y += max(26, int((30 if font is self.tiny_font else 36) * s))

    def draw_overlay(self):
        sw, sh = self.screen_w, self.screen_h
        self.draw_info_panel()
        self.draw_build_screen_feedback()
        if self.message_timer > 0 and self.message:
            image = self.font.render(self.message, True, COLORS["text"])
            rect = image.get_rect(center=(sw // 2, self.top_ui_h + 20))
            box = rect.inflate(28, 14)
            pygame.draw.rect(self.screen, (25, 27, 32), box)
            pygame.draw.rect(self.screen, COLORS["hud_line"], box, 1)
            self.screen.blit(image, rect)
        if not self.wave_active and not self.spawn_queue and not self.game_over:
            if self.wave > 0 and self.wave_break_timer > 0:
                hint = self.t("next_wave_in").format(seconds=math.ceil(self.wave_break_timer))
            else:
                hint = self.t("start_hint")
            image = self.font.render(hint, True, COLORS["gold"])
            rect = image.get_rect(center=(sw // 2, sh - self.bottom_ui_h - max(18, int(28 * self.ui_scale))))
            self.screen.blit(image, rect)
        if self.game_over:
            veil = pygame.Surface((sw, sh), pygame.SRCALPHA)
            veil.fill((0, 0, 0, 165))
            self.screen.blit(veil, (0, 0))
            title = self.big_font.render(self.t("game_over"), True, COLORS["red"])
            title_rect = title.get_rect(center=(sw // 2, sh // 2 - int(38 * self.ui_scale)))
            self.screen.blit(title, title_rect)
            sub = self.font.render(self.t("restart_hint"), True, COLORS["text"])
            self.screen.blit(sub, sub.get_rect(center=(sw // 2, sh // 2 + int(28 * self.ui_scale))))
        if self.paused:
            self.draw_pause_overlay()

    def draw_build_screen_feedback(self):
        if self.state != "playing" or self.game_over or self.paused:
            return
        if self.build_mode is not None:
            self.draw_build_tooltip()
        else:
            self.draw_structure_hover_tooltip()
        self.draw_repair_prompt()

    def draw_build_tooltip(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_world = self.screen_to_world(mouse_pos)
        if mouse_world is None:
            return
        cell = self.tile_map.world_to_cell(mouse_world)
        valid, reason = self.can_place_building(cell, self.build_mode)
        cost = self.structure_cost(self.build_mode)
        color = COLORS["green"] if valid else COLORS["red"]
        lines = [
            (self.structure_name(self.build_mode), color, self.small_font),
            (f"{self.t('cost')}: {self.t('free') if self.dev_mode else str(cost) + 'g'}", COLORS["gold"], self.tiny_font),
        ]
        if not valid:
            lines.append((self.building_block_reason_text(reason), COLORS["red"], self.tiny_font))
        elif self.build_mode == "turret":
            stats = self.structure_stats("turret")
            lines.append((f"{self.t('range_short')} {stats['range']} | {self.t('dmg')} {stats['damage']}", COLORS["cyan"], self.tiny_font))
        else:
            stats = self.structure_stats(self.build_mode)
            lines.append((f"{self.t('hp')}: {stats['hp']}", color, self.tiny_font))
        self.draw_tooltip(lines, (mouse_pos[0] + 18, mouse_pos[1] + 18), accent=color)

    def draw_structure_hover_tooltip(self):
        mouse_pos = pygame.mouse.get_pos()
        structure = self.structure_at_world(self.screen_to_world(mouse_pos))
        if structure is None:
            return
        hp = f"{max(0, int(structure.hp))}/{int(structure.max_hp)}"
        lines = [
            (self.structure_name(structure.kind), COLORS["gold"], self.small_font),
            (f"{self.t('hp')}: {hp}", COLORS["text"], self.tiny_font),
        ]
        if structure.hp < structure.max_hp:
            cost = self.t("free") if self.dev_mode else f"{self.repair_cost()}g"
            lines.append((f"{self.t('repair')}: {cost}", COLORS["green"] if self.can_afford(self.repair_cost()) else COLORS["red"], self.tiny_font))
        self.draw_tooltip(lines, (mouse_pos[0] + 18, mouse_pos[1] + 18), accent=COLORS["cyan"])

    def draw_repair_prompt(self):
        structure = self.nearby_damaged_structure()
        if structure is None or self.build_mode is not None:
            return
        cost = self.t("free") if self.dev_mode else f"{self.repair_cost()}g"
        text = f"{self.t('repair_prompt')}  |  {cost}"
        pos = self.world_to_screen(self.player.pos + Vec2(0, -48))
        image = self.small_font.render(text, True, COLORS["green"] if self.can_afford(self.repair_cost()) else COLORS["red"])
        rect = image.get_rect(center=(int(pos.x), int(pos.y)))
        rect.clamp_ip(pygame.Rect(8, self.top_ui_h, self.screen_w - 16, self.screen_h - self.top_ui_h - self.bottom_ui_h))
        box = rect.inflate(24, 12)
        self.draw_panel(box, color=(13, 16, 22), alpha=224, border=True)
        self.screen.blit(image, rect)

    def draw_tooltip(self, lines, pos, accent=COLORS["cyan"]):
        if not lines:
            return
        padding = max(10, int(10 * self.ui_scale))
        line_gap = max(4, int(5 * self.ui_scale))
        widths = [font.size(text)[0] for text, _, font in lines]
        heights = [font.get_height() for _, _, font in lines]
        box_w = max(widths) + padding * 2
        box_h = sum(heights) + line_gap * (len(lines) - 1) + padding * 2
        rect = pygame.Rect(int(pos[0]), int(pos[1]), box_w, box_h)
        rect.clamp_ip(pygame.Rect(8, 8, self.screen_w - 16, self.screen_h - 16))
        self.draw_panel(rect, color=(12, 15, 21), alpha=234, border=True)
        pygame.draw.line(self.screen, accent, (rect.x + padding, rect.y + 1), (rect.right - padding, rect.y + 1), 2)
        y = rect.y + padding
        for text, color, font in lines:
            self.screen.blit(font.render(text, True, color), (rect.x + padding, y))
            y += font.get_height() + line_gap

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
        self.draw_menu_background("crossfire", use_menu_art=True)
        title_rect = pygame.Rect(0, int(170 * s), sw, int(110 * s))
        self.draw_text_center(self.t("title"), title_rect, COLORS["gold"], self.title_font)
        self.draw_text_center(self.t("subtitle"), pygame.Rect(0, int(282 * s), sw, int(40 * s)), COLORS["cyan"], self.font)
        button_w = min(int(340 * s), sw - self.margin * 2)
        button_h = max(48, int(66 * s))
        bx = sw // 2 - button_w // 2
        y0 = int(390 * s)
        step = int(88 * s)
        menu_panel = pygame.Rect(bx - int(36 * s), y0 - int(34 * s), button_w + int(72 * s), step * 2 + button_h + int(68 * s))
        self.draw_panel(menu_panel, alpha=178)
        self.draw_button("menu_start", pygame.Rect(bx, y0, button_w, button_h), self.t("start"), font=self.font)
        self.draw_button("menu_options", pygame.Rect(bx, y0 + step, button_w, button_h), self.t("options"), font=self.font)
        self.draw_button("menu_exit", pygame.Rect(bx, y0 + step * 2, button_w, button_h), self.t("exit"), font=self.font)

    def draw_setup(self):
        sw, sh, s = self.screen_w, self.screen_h, self.ui_scale
        self.draw_menu_background(self.map_id)

        self.draw_text_center(self.t("setup_title"), pygame.Rect(0, int(54 * s), sw, int(82 * s)), COLORS["gold"], self.big_font)
        self.draw_text_center(self.t("title"), pygame.Rect(0, int(132 * s), sw, int(38 * s)), COLORS["cyan"], self.font)

        box_w = min(int(1540 * s), sw - self.margin * 2)
        box_h = min(int(790 * s), sh - int(190 * s))
        box = pygame.Rect(sw // 2 - box_w // 2, int(190 * s), box_w, box_h)
        self.draw_panel(box, alpha=220)

        pad = max(16, int(28 * s))
        gap = max(12, int(20 * s))
        bottom_h = max(56, int(74 * s))
        content_top = box.y + pad
        content_bottom = box.bottom - bottom_h - pad
        left_w = min(int(360 * s), max(230, int(box.w * 0.27)))
        right_w = min(int(460 * s), max(280, int(box.w * 0.32)))
        center_w = box.w - pad * 2 - left_w - right_w - gap * 2
        left = pygame.Rect(box.x + pad, content_top, left_w, content_bottom - content_top)
        center = pygame.Rect(left.right + gap, content_top, center_w, content_bottom - content_top)
        right = pygame.Rect(center.right + gap, content_top, right_w, content_bottom - content_top)

        self.draw_character_preview(left, self.character_id)

        map_preview = pygame.Rect(right.x, right.y, right.w, int(right.h * 0.58))
        self.draw_map_preview(map_preview, self.map_id)
        desc = pygame.Rect(right.x, map_preview.bottom + int(14 * s), right.w, right.bottom - map_preview.bottom - int(14 * s))
        self.draw_panel(desc, color=(20, 24, 29), alpha=225)
        self.draw_text_center(self.fit_text(self.map_description(self.map_id), self.tiny_font, desc.w - 40), pygame.Rect(desc.x + 16, desc.y + int(18 * s), desc.w - 32, int(42 * s)), COLORS["text"], self.tiny_font)
        difficulty_line = f"{self.t('difficulty')}: {self.difficulty_name()}  |  {self.t('turrets')}: {self.turret_limit()}"
        self.draw_text_center(difficulty_line, pygame.Rect(desc.x + 16, desc.y + int(70 * s), desc.w - 32, int(30 * s)), COLORS["gold"], self.small_font)
        self.draw_text_center(
            f"{self.t('hp')} {CHARACTERS[self.character_id]['hp']} | {self.t('armor')} {CHARACTERS[self.character_id]['armor']} | {self.t('cost')} {self.structure_cost('turret')}g",
            pygame.Rect(desc.x + 16, desc.y + int(112 * s), desc.w - 32, int(30 * s)),
            COLORS["cyan"],
            self.tiny_font,
        )

        option_h = max(42, int(54 * s))
        y = center.y + int(10 * s)
        self.draw_text_center(self.t("difficulty"), pygame.Rect(center.x, y, center.w, int(30 * s)), COLORS["cyan"], self.small_font)
        y += int(36 * s)
        item_w = int((center.w - gap * 3) / 4)
        for index, difficulty_id in enumerate(DIFFICULTIES):
            rect = pygame.Rect(center.x + index * (item_w + gap), y, item_w, option_h)
            self.draw_select_card(
                f"difficulty_{difficulty_id}",
                rect,
                self.difficulty_name(difficulty_id),
                active=self.difficulty_id == difficulty_id,
                accent=COLORS["gold"],
            )

        y += option_h + int(44 * s)
        self.draw_text_center(self.t("character"), pygame.Rect(center.x, y, center.w, int(30 * s)), COLORS["cyan"], self.small_font)
        y += int(36 * s)
        card_w = int((center.w - gap) / 2)
        card_h = max(58, int(82 * s))
        for index, character_id in enumerate(CHARACTERS):
            cx = center.x + (index % 2) * (card_w + gap)
            cy = y + (index // 2) * (card_h + int(12 * s))
            rect = pygame.Rect(cx, cy, card_w, card_h)
            self.draw_select_card(
                f"character_{character_id}",
                rect,
                self.character_name(character_id),
                self.character_description(character_id),
                active=self.character_id == character_id,
                accent=COLORS["cyan"],
            )

        y += card_h * 2 + int(48 * s)
        self.draw_text_center(self.t("map"), pygame.Rect(center.x, y, center.w, int(30 * s)), COLORS["cyan"], self.small_font)
        y += int(36 * s)
        map_count = len(MAP_ORDER)
        map_item_w = int((center.w - gap * (map_count - 1)) / map_count)
        map_card_h = max(58, int(76 * s))
        for index, map_id in enumerate(MAP_ORDER):
            rect = pygame.Rect(center.x + index * (map_item_w + gap), y, map_item_w, map_card_h)
            self.draw_select_card(
                f"map_{map_id}",
                rect,
                self.map_name(map_id),
                self.map_description(map_id),
                active=self.map_id == map_id,
                accent=MAP_THEMES[map_id]["accent"],
            )

        y += map_card_h + int(30 * s)
        turret = self.structure_stats("turret")
        fence = self.structure_stats("fence")
        summary = pygame.Rect(center.x, y, center.w, min(max(86, int(104 * s)), center.bottom - y))
        pygame.draw.rect(self.screen, (28, 32, 39), summary, border_radius=8)
        pygame.draw.rect(self.screen, COLORS["hud_line"], summary, 1, border_radius=8)
        self.draw_text_center(self.t("structures"), pygame.Rect(summary.x, summary.y + int(8 * s), summary.w, int(28 * s)), COLORS["gold"], self.small_font)
        self.draw_text_center(
            f"{self.t('turret')} {self.structure_cost('turret')}g | {self.t('hp')} {turret['hp']} | {self.t('dmg')} {turret['damage']} | {self.t('range_short')} {turret['range']}",
            pygame.Rect(summary.x, summary.y + int(38 * s), summary.w, int(26 * s)),
            COLORS["text"],
            self.small_font,
        )
        self.draw_text_center(
            f"{self.t('fence_level').format(level=fence['level'])} {self.structure_cost('fence')}g | {self.t('hp')} {fence['hp']} | {self.t('repair')} {self.repair_cost()}g",
            pygame.Rect(summary.x, summary.y + int(66 * s), summary.w, int(26 * s)),
            COLORS["muted"],
            self.small_font,
        )

        button_w = min(int(280 * s), box.w - int(120 * s))
        button_h = max(46, int(58 * s))
        bottom_y = box.bottom - pad - button_h
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
        lang_label = "Tiếng Việt" if self.language == "vi" else "English"
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
            self.ui.draw_main_menu(self.screen, self)
        elif self.state == "setup":
            self.ui.draw_prepare_screen(self.screen, self)
        elif self.state == "options":
            self.ui.draw_options_menu(self.screen, self)
        else:
            self.screen.fill((8, 10, 14))
            self.draw_world()
            self.ui.draw_hud(self.screen, self)
            self.ui.draw_overlay(self.screen, self)
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000
            running = self.handle_events()
            self.update_music()
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
