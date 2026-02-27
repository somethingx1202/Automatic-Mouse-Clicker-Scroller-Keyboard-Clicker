# src/player.py
import time
import threading
from pynput import mouse, keyboard
from pynput.keyboard import Key, KeyCode
from pynput.mouse import Button


class Player:
    """Replays a recorded event list."""

    def __init__(self):
        self._mouse = mouse.Controller()
        self._keyboard = keyboard.Controller()
        self._stop_event = threading.Event()

    def play(self, events, speed=1.0):
        if not events:
            return
        self._stop_event.clear()
        held_keys = set()
        base_t = events[0]["t"]
        play_start = time.time()

        for event in events:
            if self._stop_event.is_set():
                break
            target_elapsed = (event["t"] - base_t) / speed
            now_elapsed = time.time() - play_start
            wait = target_elapsed - now_elapsed
            if wait > 0:
                if self._stop_event.wait(wait):
                    break
            self._dispatch(event, held_keys)

        # Release any keys still held at end/abort
        for key in list(held_keys):
            try:
                self._keyboard.release(key)
            except Exception:
                pass

    def stop(self):
        self._stop_event.set()

    # ── dispatch ────────────────────────────────────────────────────────────

    def _dispatch(self, event, held_keys):
        t = event["type"]
        try:
            if t == "click":
                btn = Button[event["button"]]
                self._mouse.position = (int(event["x"]), int(event["y"]))
                time.sleep(0.01)
                if event["pressed"]:
                    self._mouse.press(btn)
                else:
                    self._mouse.release(btn)
            elif t == "scroll":
                self._mouse.position = (int(event["x"]), int(event["y"]))
                time.sleep(0.01)
                self._mouse.scroll(event["dx"], event["dy"])
            elif t == "key":
                key = self._parse_key(event["key"])
                if event["pressed"]:
                    self._keyboard.press(key)
                    held_keys.add(key)
                else:
                    self._keyboard.release(key)
                    held_keys.discard(key)
        except NotImplementedError:
            pass

    def _parse_key(self, key_str):
        try:
            return Key[key_str]
        except KeyError:
            pass
        return KeyCode.from_char(key_str[0]) if key_str else KeyCode.from_char(" ")
