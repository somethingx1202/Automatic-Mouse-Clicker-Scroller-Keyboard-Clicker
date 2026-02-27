# tests/test_recorder.py
import time
from src.recorder import Recorder
from pynput.keyboard import Key, KeyCode


# ---------------------------------------------------------------------------
# Helpers: lightweight stand-ins for pynput Key members.
# pynput's "dummy" backend (used in CI / headless dev) collapses every Key
# member to the same Key.alt singleton, making direct Key.enter / Key.f6
# comparisons useless.  These stubs faithfully reproduce the interface that
# Recorder actually inspects (_key_str uses str() and _is_filtered uses ==).
# ---------------------------------------------------------------------------

class _MockSpecialKey:
    """Mimics a pynput Key member: no .char attribute, str() -> 'Key.<name>'."""
    def __init__(self, name):
        self._name = name

    def __str__(self):
        return f"Key.{self._name}"

    def __repr__(self):
        return f"<Key.{self._name}>"

    def __eq__(self, other):
        return isinstance(other, _MockSpecialKey) and self._name == other._name

    def __hash__(self):
        return hash(self._name)


# Pre-built mock keys used across tests
_KEY_ENTER  = _MockSpecialKey("enter")
_KEY_CTRL_L = _MockSpecialKey("ctrl_l")
_KEY_SPACE  = _MockSpecialKey("space")
_KEY_F6     = _MockSpecialKey("f6")
_KEY_F7     = _MockSpecialKey("f7")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_key_str_printable_char():
    r = Recorder()
    key = KeyCode.from_char("a")
    assert r._key_str(key) == "a"


def test_key_str_special_key():
    r = Recorder()
    assert r._key_str(_KEY_ENTER)  == "enter"
    assert r._key_str(_KEY_CTRL_L) == "ctrl_l"
    assert r._key_str(_KEY_SPACE)  == "space"


def test_key_str_dead_key_none_char():
    """key.char exists but is None — should fall back to str(key)."""
    class DeadKey:
        char = None
        def __str__(self):
            return "Key.dead_tilde"
    r = Recorder()
    result = r._key_str(DeadKey())
    assert result == "dead_tilde"


def test_is_filtered_blocks_specified_key():
    r = Recorder(filter_keys=[_KEY_F6])
    assert r._is_filtered(_KEY_F6) is True
    assert r._is_filtered(_KEY_F7) is False


def test_is_filtered_empty_by_default():
    r = Recorder()
    assert r._is_filtered(_KEY_ENTER) is False


def test_stop_before_start_returns_empty_list():
    """stop() called before start() should not crash and should return []."""
    r = Recorder()
    events = r.stop()
    assert events == []


def test_ts_increases_monotonically():
    r = Recorder()
    r._start_time = time.time()
    t1 = r._ts()
    time.sleep(0.01)
    t2 = r._ts()
    assert t2 > t1
