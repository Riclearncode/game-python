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
    },
    "progression": {
        "total_runs": 0,
        "total_kills": 0,
        "total_gold_collected": 0,
        "unlocked_weapons": [],
        "achievements": [],
    },
}


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
        self.save()
        return changed

    def get_high_score(self):
        return self.data.setdefault("high_score", copy.deepcopy(DEFAULT_SAVE["high_score"]))

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
                merged[section].update(value)
            else:
                merged[section] = value
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
