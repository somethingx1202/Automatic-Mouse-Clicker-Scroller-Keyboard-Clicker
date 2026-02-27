# tests/conftest.py
# On Linux dev machines without an X display, pynput cannot load its xorg
# backend at import time.  Setting PYNPUT_BACKEND=dummy selects the no-op
# backend that allows all imports to succeed while we develop/test on Linux.
# On Windows (the deployment target) this variable is not set, so the real
# win32 backend is used automatically.
import os

os.environ.setdefault("PYNPUT_BACKEND", "dummy")
