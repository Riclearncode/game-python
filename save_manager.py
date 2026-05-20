import copy
import json
import os
import time

from path_utils import user_data_path


DEFAULT_SAVE = {
    "settings": {
        "language": "vi",
        "music_volume": 70,
        "sfx_volume": 80,
        "auto_fire": True,
        "developer_mode": False,
    },
    "high_score": {
        "highest_wave": 0,
        "highest_score": 0,
        "most_kills": 0,
        "most_gold": 0,
        "best_survival_time": 0.0,
        "best_map": "-",
        "best_class": "-",
        "best_difficulty": "-",
        "by_combo": {},
    },
    "progression": {
        "total_runs": 0,
        "total_kills": 0,
        "total_gold_collected": 0,
        "meta_points": 0,
        "spent_meta_points": 0,
        "meta_upgrades": {
            "health": 0,
            "damage": 0,
            "economy": 0,
            "build": 0,
        },
        "unlocked_classes": ["soldier"],
        "unlocked_maps": ["warehouse"],
        "unlocked_weapons": [],
        "achievements": [],
        "last_rewards": {},
    },
}


ACHIEVEMENT_RULES = (
    ("first_blood", "First Blood", lambda run, prog: run.get("kills", 0) >= 1),
    ("wave_5", "Reached Wave 5", lambda run, prog: run.get("wave", 0) >= 5),
    ("wave_10", "Reached Wave 10", lambda run, prog: run.get("wave", 0) >= 10),
    ("runner_hunter", "Runner Hunter", lambda run, prog: run.get("runner_kills", 0) >= 20),
    ("titan_slayer", "Titan Slayer", lambda run, prog: run.get("titan_kills", 0) >= 1),
    ("gold_5000", "5000 Gold Collected", lambda run, prog: prog.get("total_gold_collected", 0) >= 5000),
)

UNLOCK_RULES = (
    ("class", "scout", lambda run, prog: prog.get("total_kills", 0) >= 50),
    ("class", "engineer", lambda run, prog: prog.get("total_gold_collected", 0) >= 1500),
    ("class", "tank", lambda run, prog: run.get("wave", 0) >= 8),
    ("map", "crossfire_yard", lambda run, prog: run.get("wave", 0) >= 4),
    ("map", "split_ruins", lambda run, prog: run.get("wave", 0) >= 7),
    ("weapon", "M4A1 Carbine", lambda run, prog: run.get("weapon_tier", 1) >= 5),
    ("weapon", "XM-LAS Prototype", lambda run, prog: run.get("weapon_tier", 1) >= 9),
    ("weapon", "XM-Railbreaker", lambda run, prog: run.get("weapon_tier", 1) >= 12),
)


class SaveManager:
    def __init__(self, path=None):
        self.path = path or user_data_path("save_data.json")
        self.data = copy.deepcopy(DEFAULT_SAVE)

    def load(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            self.data = copy.deepcopy(DEFAULT_SAVE)
            self.save()
            return self.data
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                raw = json.load(handle)
            self.data = self._merge_defaults(raw)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            self._backup_corrupt_save()
            self.data = copy.deepcopy(DEFAULT_SAVE)
            self.save()
        return self.data

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp_path = self.path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as handle:
            json.dump(self.data, handle, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self.path)
        return self.data

    def update_high_score(self, run_stats):
        high_score = self.data.setdefault("high_score", copy.deepcopy(DEFAULT_SAVE["high_score"]))
        progression = self.data.setdefault("progression", copy.deepcopy(DEFAULT_SAVE["progression"]))
        progression.setdefault("meta_points", 0)
        progression.setdefault("spent_meta_points", 0)
        progression.setdefault("meta_upgrades", copy.deepcopy(DEFAULT_SAVE["progression"]["meta_upgrades"]))
        progression.setdefault("unlocked_classes", ["soldier"])
        progression.setdefault("unlocked_maps", ["warehouse"])
        progression.setdefault("unlocked_weapons", [])
        progression.setdefault("achievements", [])
        changed = []

        checks = (
            ("highest_wave", int(run_stats.get("wave", 0))),
            ("highest_score", int(run_stats.get("score", 0))),
            ("most_kills", int(run_stats.get("kills", 0))),
            ("most_gold", int(run_stats.get("gold_collected", 0))),
            ("best_survival_time", float(run_stats.get("survival_time", 0.0))),
        )
        for key, value in checks:
            if value > high_score.get(key, 0):
                high_score[key] = value
                changed.append(key)

        if "highest_score" in changed or high_score.get("best_map", "-") == "-":
            high_score["best_map"] = run_stats.get("map", "-")
            high_score["best_class"] = run_stats.get("character", "-")
            high_score["best_difficulty"] = run_stats.get("difficulty", "-")

        progression["total_kills"] = int(progression.get("total_kills", 0)) + int(run_stats.get("kills", 0))
        progression["total_gold_collected"] = int(progression.get("total_gold_collected", 0)) + int(run_stats.get("gold_collected", 0))
        earned_meta = self._meta_points_for_run(run_stats)
        progression["meta_points"] = int(progression.get("meta_points", 0)) + earned_meta

        combo_changed = self._update_combo_record(high_score, run_stats)
        if combo_changed:
            changed.append(combo_changed)

        new_achievements = self._update_achievements(progression, run_stats)
        changed.extend(new_achievements)
        new_unlocks = self._update_unlocks(progression, run_stats)
        changed.extend(new_unlocks)
        progression["last_rewards"] = {
            "meta_points": earned_meta,
            "achievements": new_achievements,
            "unlocks": new_unlocks,
        }
        self.save()
        return changed

    def get_high_score(self):
        return self.data.setdefault("high_score", copy.deepcopy(DEFAULT_SAVE["high_score"]))

    def get_progression(self):
        return self.data.setdefault("progression", copy.deepcopy(DEFAULT_SAVE["progression"]))

    def spend_meta_point(self, upgrade_id):
        progression = self.get_progression()
        upgrades = progression.setdefault("meta_upgrades", copy.deepcopy(DEFAULT_SAVE["progression"]["meta_upgrades"]))
        if upgrade_id not in upgrades or int(progression.get("meta_points", 0)) <= 0:
            return False
        if int(upgrades.get(upgrade_id, 0)) >= 5:
            return False
        upgrades[upgrade_id] = int(upgrades.get(upgrade_id, 0)) + 1
        progression["meta_points"] = int(progression.get("meta_points", 0)) - 1
        progression["spent_meta_points"] = int(progression.get("spent_meta_points", 0)) + 1
        self.save()
        return True

    def reset_save(self):
        self.data = copy.deepcopy(DEFAULT_SAVE)
        self.save()
        return self.data

    def _merge_defaults(self, raw):
        merged = copy.deepcopy(DEFAULT_SAVE)
        if not isinstance(raw, dict):
            return merged
        for section, defaults in DEFAULT_SAVE.items():
            value = raw.get(section, {})
            if isinstance(defaults, dict) and isinstance(value, dict):
                merged[section] = self._merge_dict(defaults, value)
            else:
                merged[section] = value
        return merged

    def _merge_dict(self, defaults, value):
        merged = copy.deepcopy(defaults)
        for key, item in value.items():
            if isinstance(merged.get(key), dict) and isinstance(item, dict):
                merged[key] = self._merge_dict(merged[key], item)
            else:
                merged[key] = item
        return merged

    def _backup_corrupt_save(self):
        if not os.path.exists(self.path):
            return
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.path}.corrupt_{timestamp}.bak"
        try:
            os.replace(self.path, backup_path)
        except OSError:
            pass

    def _meta_points_for_run(self, run_stats):
        wave = int(run_stats.get("wave", 0))
        score = int(run_stats.get("score", 0))
        kills = int(run_stats.get("kills", 0))
        titan_bonus = int(run_stats.get("titan_kills", 0)) * 2
        return max(1, wave // 3 + score // 3500 + kills // 90 + titan_bonus)

    def _combo_key(self, run_stats):
        return "|".join(
            str(run_stats.get(key, "-"))
            for key in ("difficulty_id", "map_id", "character_id")
        )

    def _update_combo_record(self, high_score, run_stats):
        records = high_score.setdefault("by_combo", {})
        key = self._combo_key(run_stats)
        old = records.get(key, {})
        score = int(run_stats.get("score", 0))
        wave = int(run_stats.get("wave", 0))
        if score <= int(old.get("score", 0)) and wave <= int(old.get("wave", 0)):
            return None
        records[key] = {
            "score": max(score, int(old.get("score", 0))),
            "wave": max(wave, int(old.get("wave", 0))),
            "kills": max(int(run_stats.get("kills", 0)), int(old.get("kills", 0))),
            "gold": max(int(run_stats.get("gold_collected", 0)), int(old.get("gold", 0))),
            "time": max(float(run_stats.get("survival_time", 0.0)), float(old.get("time", 0.0))),
            "difficulty": run_stats.get("difficulty", "-"),
            "map": run_stats.get("map", "-"),
            "character": run_stats.get("character", "-"),
            "weapon": run_stats.get("weapon", "-"),
        }
        return "combo_record"

    def _update_achievements(self, progression, run_stats):
        owned = set(progression.setdefault("achievements", []))
        unlocked = []
        for achievement_id, _label, predicate in ACHIEVEMENT_RULES:
            if achievement_id in owned:
                continue
            try:
                if predicate(run_stats, progression):
                    owned.add(achievement_id)
                    unlocked.append(f"achievement:{achievement_id}")
            except Exception:
                continue
        progression["achievements"] = sorted(owned)
        return unlocked

    def _update_unlocks(self, progression, run_stats):
        unlocked = []
        for unlock_type, value, predicate in UNLOCK_RULES:
            key = {
                "class": "unlocked_classes",
                "map": "unlocked_maps",
                "weapon": "unlocked_weapons",
            }[unlock_type]
            collection = progression.setdefault(key, [])
            if value in collection:
                continue
            try:
                if predicate(run_stats, progression):
                    collection.append(value)
                    unlocked.append(f"unlock:{unlock_type}:{value}")
            except Exception:
                continue
        return unlocked
