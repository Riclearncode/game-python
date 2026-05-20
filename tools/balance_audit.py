import os
import sys


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import main


def weapon_metrics(level):
    weapon = main.Weapon(level=level)
    shots_per_mag = max(1, weapon.magazine_size // weapon.ammo_per_shot)
    damage_per_trigger = weapon.damage * weapon.bullet_count
    fire_cycle = shots_per_mag * weapon.cooldown + weapon.reload_time
    burst_dps = damage_per_trigger / weapon.cooldown
    sustained_dps = damage_per_trigger * shots_per_mag / fire_cycle
    lane_score = sustained_dps * (
        1
        + min(weapon.pierce, 8) * 0.22
        + min(weapon.explosion_radius, 70) / 70 * 0.35
    )
    return weapon, burst_dps, sustained_dps, lane_score


def cumulative_weapon_cost(target_level, difficulty="normal"):
    multiplier = main.DIFFICULTIES[difficulty].get("weapon_cost", 1.0)
    total = 0
    for level in range(1, target_level):
        weapon = main.Weapon(level=level)
        cost = weapon.upgrade_cost
        if cost > 0:
            total += round(cost * multiplier)
    return total


def wave_queue(wave, difficulty="normal"):
    cfg = main.DIFFICULTIES[difficulty]

    def scaled(count):
        return max(1, round(count * cfg["count"]))

    queue = ["walker"] * scaled(7 + wave * 4)
    if wave >= 2:
        queue += ["runner"] * scaled(3 + wave * 2)
    if wave >= 3:
        queue += ["spitter"] * scaled(max(2, wave // 2 + 1))
    if wave >= 4:
        queue += ["boomer"] * scaled(max(2, wave // 2 + 1))
    if wave >= 5:
        queue += ["stalker"] * scaled(max(2, wave // 3 + 1))
    if wave % 5 == 0:
        queue += ["titan"]
    return queue


def expected_wave_gold(wave, difficulty="normal"):
    cfg = main.DIFFICULTIES[difficulty]
    random_cap = min(main.GOLD_DROP_RANDOM_CAP, 2 + wave // 3)
    late_bonus = max(0, (wave - 10) // main.GOLD_DROP_LATE_BONUS_STEP)
    kill_gold = sum(
        (main.ZOMBIE_TYPES[kind]["reward"] + random_cap / 2 + late_bonus) * cfg["reward"]
        for kind in wave_queue(wave, difficulty)
    )
    clear_gold = (22 + wave * 5 + (wave // 5) * 6) * cfg["reward"]
    return kill_gold + clear_gold


def print_weapon_table():
    print("WEAPON BALANCE")
    print("Tier Level Weapon                UnlockGold BurstDPS SustainDPS LaneScore")
    for definition in main.WEAPON_DEFS:
        level = definition["min_level"]
        weapon, burst, sustain, lane = weapon_metrics(level)
        cost = cumulative_weapon_cost(level)
        print(
            f"{weapon.tier_number:>4} {level:>5} {weapon.tier_name:<21} "
            f"{cost:>10.0f} {burst:>8.1f} {sustain:>10.1f} {lane:>9.1f}"
        )


def print_zombie_table():
    print("\nNORMAL ZOMBIE HP")
    print("Wave Walker Runner Spitter Boomer Stalker Titan")
    for wave in (1, 3, 5, 8, 10, 12, 15, 18, 20, 23, 25):
        values = [
            main.Zombie(kind, (0, 0), wave, "normal").max_hp
            for kind in ("walker", "runner", "spitter", "boomer", "stalker", "titan")
        ]
        print(f"{wave:>4} " + " ".join(f"{value:>7}" for value in values))


def print_economy_table():
    print("\nNORMAL ECONOMY")
    print("Wave Enemies WaveGold CumulativeGold")
    total = 0
    for wave in range(1, 16):
        gold = expected_wave_gold(wave)
        total += gold
        print(f"{wave:>4} {len(wave_queue(wave)):>7} {gold:>8.1f} {total:>14.1f}")


if __name__ == "__main__":
    print_weapon_table()
    print_zombie_table()
    print_economy_table()
