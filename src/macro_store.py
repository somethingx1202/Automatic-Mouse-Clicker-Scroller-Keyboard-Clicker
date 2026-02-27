# src/macro_store.py
import json
from datetime import datetime
from pathlib import Path

DEFAULT_FOLDER = Path.home() / "mouse_macros"


def _ensure_folder(folder):
    Path(folder).mkdir(parents=True, exist_ok=True)


def save_macro(name, events, folder=DEFAULT_FOLDER):
    _ensure_folder(folder)
    data = {
        "name": name,
        "created": datetime.now().isoformat(timespec="seconds"),
        "events": events,
    }
    path = Path(folder) / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def load_macro(name, folder=DEFAULT_FOLDER):
    path = Path(folder) / f"{name}.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["events"]
    except FileNotFoundError:
        raise FileNotFoundError(f"Macro '{name}' not found in {folder}")
    except (KeyError, json.JSONDecodeError) as e:
        raise ValueError(f"Macro file '{name}.json' is corrupt: {e}")


def list_macros(folder=DEFAULT_FOLDER):
    folder = Path(folder)
    if not folder.exists():
        return []
    macros = []
    for p in sorted(folder.glob("*.json")):
        try:
            with open(p, "r", encoding="utf-8") as f:
                json.load(f)
            macros.append(p.stem)
        except Exception:
            print(f"Warning: skipping corrupt file {p}")
    return macros


def delete_macro(name, folder=DEFAULT_FOLDER):
    path = Path(folder) / f"{name}.json"
    if path.exists():
        path.unlink()
