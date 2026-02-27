# tests/test_macro_store.py
import json
import pytest
from pathlib import Path
from src.macro_store import save_macro, load_macro, list_macros, delete_macro

SAMPLE_EVENTS = [
    {"type": "click", "x": 100, "y": 200, "button": "left", "pressed": True, "t": 0.0},
    {"type": "key", "key": "a", "pressed": True, "t": 0.5},
]

@pytest.fixture
def tmp_folder(tmp_path):
    return tmp_path / "macros"

def test_save_creates_file(tmp_folder):
    save_macro("test", SAMPLE_EVENTS, folder=tmp_folder)
    assert (tmp_folder / "test.json").exists()

def test_save_load_roundtrip(tmp_folder):
    save_macro("test", SAMPLE_EVENTS, folder=tmp_folder)
    loaded = load_macro("test", folder=tmp_folder)
    assert loaded == SAMPLE_EVENTS

def test_list_macros_empty_folder(tmp_folder):
    assert list_macros(folder=tmp_folder) == []

def test_list_macros_returns_names(tmp_folder):
    save_macro("alpha", SAMPLE_EVENTS, folder=tmp_folder)
    save_macro("beta", SAMPLE_EVENTS, folder=tmp_folder)
    names = list_macros(folder=tmp_folder)
    assert sorted(names) == ["alpha", "beta"]

def test_list_macros_skips_corrupt(tmp_folder):
    tmp_folder.mkdir(parents=True)
    (tmp_folder / "bad.json").write_text("not json")
    save_macro("good", SAMPLE_EVENTS, folder=tmp_folder)
    assert list_macros(folder=tmp_folder) == ["good"]

def test_delete_macro(tmp_folder):
    save_macro("test", SAMPLE_EVENTS, folder=tmp_folder)
    delete_macro("test", folder=tmp_folder)
    assert not (tmp_folder / "test.json").exists()

def test_delete_nonexistent_is_noop(tmp_folder):
    delete_macro("ghost", folder=tmp_folder)  # should not raise
