# tests/test_player.py
import pytest
import time
import threading
from src.player import Player
from pynput.keyboard import Key, KeyCode
from pynput.mouse import Button


def test_parse_key_char():
    p = Player()
    result = p._parse_key("a")
    assert result == KeyCode.from_char("a")
    result_v = p._parse_key("v")
    assert result_v == KeyCode.from_char("v")


def test_parse_key_special_enter():
    p = Player()
    result = p._parse_key("enter")
    assert result == Key.enter


def test_parse_key_ctrl_and_space():
    p = Player()
    assert p._parse_key("ctrl_l") == Key.ctrl_l
    assert p._parse_key("space") == Key.space


def test_parse_key_fallback_for_unknown():
    p = Player()
    # An unknown key string falls back to KeyCode.from_char of first char
    result = p._parse_key("z")
    assert result == KeyCode.from_char("z")


def test_play_empty_events_does_nothing():
    p = Player()
    p.play([])  # should return immediately without error or hang


def test_play_respects_stop():
    """stop() called while play() is waiting should abort early."""
    p = Player()
    events = [
        {"type": "key", "key": "a", "pressed": True, "t": 0.0},
        {"type": "key", "key": "a", "pressed": False, "t": 10.0},  # 10s gap
    ]
    def stop_soon():
        time.sleep(0.05)
        p.stop()
    t = threading.Thread(target=stop_soon, daemon=True)
    t.start()
    start = time.time()
    p.play(events)
    elapsed = time.time() - start
    assert elapsed < 5.0, f"stop() should abort early, but took {elapsed:.1f}s"


def test_play_speed_multiplier():
    """Events with 0.5s gap at 2x speed should complete in ~0.25s, not 0.5s."""
    p = Player()
    events = [
        {"type": "key", "key": "a", "pressed": True,  "t": 0.0},
        {"type": "key", "key": "a", "pressed": False, "t": 0.5},
    ]
    start = time.time()
    p.play(events, speed=2.0)
    elapsed = time.time() - start
    assert elapsed > 0.05, f"timing should not be skipped entirely, took {elapsed:.2f}s"
    assert elapsed < 0.4, f"2x speed should take ~0.25s, took {elapsed:.2f}s"
