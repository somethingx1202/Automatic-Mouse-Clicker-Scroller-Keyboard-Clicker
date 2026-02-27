# src/settings.py
import json
from pathlib import Path

SETTINGS_PATH = Path.home() / "mouse_macros" / "settings.json"

DEFAULT_SETTINGS = {
    "record_hotkey": "<f6>",
    "play_hotkey": "<f7>",
    "speed": 1.0,
    "repeat_count": 1,
    "macro_folder": str(Path.home() / "mouse_macros"),
}


def load_settings():
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {**DEFAULT_SETTINGS, **data}
        except Exception as e:
            print(f"Warning: could not read settings file ({e}), using defaults")
    return dict(DEFAULT_SETTINGS)


def save_settings(settings):
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
