# src/recorder.py
import time
import threading
from pynput import mouse, keyboard


class Recorder:
    """Records mouse clicks/scrolls and keyboard press/release events."""

    def __init__(self, filter_keys=None):
        # filter_keys: list of pynput Key objects to exclude (e.g. hotkeys)
        self._filter_keys = set(filter_keys or [])
        self._events = []
        self._start_time = None
        self._mouse_listener = None
        self._keyboard_listener = None
        self._lock = threading.Lock()

    def start(self):
        self._events = []
        self._start_time = time.time()
        self._mouse_listener = mouse.Listener(
            on_click=self._on_click,
            on_scroll=self._on_scroll,
        )
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._mouse_listener.start()
        self._keyboard_listener.start()

    def stop(self):
        if self._mouse_listener:
            self._mouse_listener.stop()
        if self._keyboard_listener:
            self._keyboard_listener.stop()
        with self._lock:
            return list(self._events)

    # ── helpers ────────────────────────────────────────────────────────────

    def _ts(self):
        return round(time.time() - self._start_time, 4)

    def _key_str(self, key):
        try:
            if getattr(key, 'char', None) is not None:
                c = key.char
                # Handle control characters mapped to letters (e.g. \x16 -> 'v')
                if len(c) == 1 and 1 <= ord(c) <= 26 and ord(c) not in (8, 9, 10, 13):
                    return chr(ord(c) + 96)
                return c
        except AttributeError:
            pass
        return str(key).replace("Key.", "")

    def _is_filtered(self, key):
        return key in self._filter_keys

    # ── listener callbacks ──────────────────────────────────────────────────

    def _on_click(self, x, y, button, pressed):
        ts = self._ts()
        with self._lock:
            self._events.append({
                "type": "click",
                "x": int(x), "y": int(y),
                "button": button.name,
                "pressed": pressed,
                "t": ts,
            })

    def _on_scroll(self, x, y, dx, dy):
        ts = self._ts()
        with self._lock:
            self._events.append({
                "type": "scroll",
                "x": int(x), "y": int(y),
                "dx": dx, "dy": dy,
                "t": ts,
            })

    def _on_key_press(self, key):
        if self._is_filtered(key):
            return
        ts = self._ts()
        with self._lock:
            self._events.append({
                "type": "key",
                "key": self._key_str(key),
                "pressed": True,
                "t": ts,
            })

    def _on_key_release(self, key):
        if self._is_filtered(key):
            return
        ts = self._ts()
        with self._lock:
            self._events.append({
                "type": "key",
                "key": self._key_str(key),
                "pressed": False,
                "t": ts,
            })
