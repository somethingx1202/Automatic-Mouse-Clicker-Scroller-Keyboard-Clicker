# tests/test_settings.py
import json
import pytest
from pathlib import Path
from src.settings import load_settings, save_settings, DEFAULT_SETTINGS

@pytest.fixture
def settings_path(tmp_path, monkeypatch):
    path = tmp_path / "settings.json"
    monkeypatch.setattr("src.settings.SETTINGS_PATH", path)
    return path

def test_load_returns_defaults_when_no_file(settings_path):
    s = load_settings()
    assert s["record_hotkey"] == "<f6>"
    assert s["play_hotkey"] == "<f7>"
    assert s["speed"] == 1.0

def test_save_and_load_roundtrip(settings_path):
    original = load_settings()
    original["speed"] = 2.0
    save_settings(original)
    loaded = load_settings()
    assert loaded["speed"] == 2.0

def test_load_merges_missing_keys(settings_path):
    # File with only one key — missing keys filled from defaults
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps({"speed": 3.0}))
    s = load_settings()
    assert s["speed"] == 3.0
    assert "record_hotkey" in s

def test_load_falls_back_on_corrupt_file(settings_path):
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text("not json")
    s = load_settings()
    assert s == DEFAULT_SETTINGS
