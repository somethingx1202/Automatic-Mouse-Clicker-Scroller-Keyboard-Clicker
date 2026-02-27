import sys

if sys.platform == "win32":
    import ctypes
    try:
        # Prevent Windows UI scaling from breaking pynput coordinate positions
        ctypes.windll.shcore.SetProcessDpiAwareness(2) # PROCESS_PER_MONITOR_DPI_AWARE
    except Exception:
        pass

from src.app import App

if __name__ == "__main__":
    app = App()
    app.mainloop()

