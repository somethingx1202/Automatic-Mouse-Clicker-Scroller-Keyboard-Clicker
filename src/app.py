# src/app.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading
import os

from src.macro_store import save_macro, load_macro, list_macros, delete_macro
from src.settings import load_settings, save_settings
from src.recorder import Recorder
from src.player import Player

SPEED_OPTIONS = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
HOTKEY_OPTIONS = ["<f5>", "<f6>", "<f7>", "<f8>", "<f9>", "<f10>"]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Macro Recorder")
        self.resizable(False, False)

        self._settings = load_settings()
        self._recorder = Recorder()
        self._player = Player()
        self._recording = False
        self._playing = False
        self._saving = False
        self._hotkey_listener = None

        self._build_ui()
        self._refresh_library()
        self._register_hotkeys()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    @staticmethod
    def _parse_hotkey_to_key(hk_str):
        """Convert a pynput hotkey string like '<f6>' to a Key enum member."""
        from pynput.keyboard import Key as _Key
        name = hk_str.strip("<>")
        try:
            return _Key[name]
        except KeyError:
            return None

    # ── UI construction ─────────────────────────────────────────────────────

    def _build_ui(self):
        pad = {"padx": 8, "pady": 4}

        # ── Library panel ──
        lib_frame = ttk.LabelFrame(self, text="Macro Library")
        lib_frame.grid(row=0, column=0, sticky="nsew", **pad)

        btn_row = tk.Frame(lib_frame)
        btn_row.pack(fill="x", padx=4, pady=2)
        ttk.Button(btn_row, text="New", command=self._new_macro).pack(side="left")
        ttk.Button(btn_row, text="Delete", command=self._delete_macro).pack(side="left", padx=4)

        self._listbox = tk.Listbox(lib_frame, width=32, height=10, selectmode="single")
        self._listbox.pack(fill="both", expand=True, padx=4, pady=4)

        # ── Controls panel ──
        ctrl_frame = ttk.LabelFrame(self, text="Controls")
        ctrl_frame.grid(row=1, column=0, sticky="ew", **pad)

        btn_row2 = tk.Frame(ctrl_frame)
        btn_row2.pack(pady=4)
        self._btn_record = ttk.Button(btn_row2, text="● Record", command=self._toggle_record)
        self._btn_record.pack(side="left", padx=4)
        self._btn_play = ttk.Button(btn_row2, text="▶ Play", command=self._toggle_play)
        self._btn_play.pack(side="left", padx=4)
        ttk.Button(btn_row2, text="■ Stop", command=self._stop_all).pack(side="left", padx=4)

        self._status_var = tk.StringVar(value="Idle")
        ttk.Label(ctrl_frame, textvariable=self._status_var).pack(pady=2)

        # ── Settings panel ──
        cfg_frame = ttk.LabelFrame(self, text="Settings")
        cfg_frame.grid(row=2, column=0, sticky="ew", **pad)

        self._rec_hotkey_var = tk.StringVar(value=self._settings["record_hotkey"])
        self._play_hotkey_var = tk.StringVar(value=self._settings["play_hotkey"])
        self._speed_var = tk.DoubleVar(value=self._settings["speed"])
        self._repeat_var = tk.StringVar(value=str(self._settings.get("repeat_count", 1)))
        self._repeat_var.trace_add("write", self._on_settings_changed)
        self._folder_var = tk.StringVar(value=self._settings["macro_folder"])

        rows = [
            ("Record hotkey:", self._rec_hotkey_var, HOTKEY_OPTIONS),
            ("Play hotkey:", self._play_hotkey_var, HOTKEY_OPTIONS),
        ]
        for i, (label, var, options) in enumerate(rows):
            ttk.Label(cfg_frame, text=label).grid(row=i, column=0, sticky="w", padx=4, pady=2)
            cb = ttk.Combobox(cfg_frame, textvariable=var, values=options, width=8, state="readonly")
            cb.grid(row=i, column=1, sticky="w", padx=4)
            cb.bind("<<ComboboxSelected>>", self._on_settings_changed)

        ttk.Label(cfg_frame, text="Speed:").grid(row=2, column=0, sticky="w", padx=4, pady=2)
        speed_cb = ttk.Combobox(cfg_frame, textvariable=self._speed_var,
                                values=SPEED_OPTIONS, width=8, state="readonly")
        speed_cb.grid(row=2, column=1, sticky="w", padx=4)
        speed_cb.bind("<<ComboboxSelected>>", self._on_settings_changed)

        ttk.Label(cfg_frame, text="Repeat:").grid(row=3, column=0, sticky="w", padx=4, pady=2)
        vcmd = (self.register(self._validate_int), '%P')
        repeat_entry = ttk.Entry(cfg_frame, textvariable=self._repeat_var, width=10, validate="key", validatecommand=vcmd)
        repeat_entry.grid(row=3, column=1, sticky="w", padx=4)

        ttk.Label(cfg_frame, text="Macro folder:").grid(row=4, column=0, sticky="w", padx=4, pady=2)
        folder_row = tk.Frame(cfg_frame)
        folder_row.grid(row=4, column=1, sticky="w", padx=4)
        ttk.Label(folder_row, textvariable=self._folder_var, width=22, anchor="w").pack(side="left")
        ttk.Button(folder_row, text="...", width=3, command=self._choose_folder).pack(side="left")

    def _validate_int(self, P):
        if P == "" or P.isdigit():
            return True
        return False

    # ── Library actions ─────────────────────────────────────────────────────

    def _refresh_library(self):
        self._listbox.delete(0, "end")
        for name in list_macros(folder=self._settings["macro_folder"]):
            self._listbox.insert("end", name)

    def _selected_macro(self):
        sel = self._listbox.curselection()
        return self._listbox.get(sel[0]) if sel else None

    def _new_macro(self):
        """Placeholder — recording creates macros via the Record button."""
        pass

    def _delete_macro(self):
        name = self._selected_macro()
        if not name:
            return
        if messagebox.askyesno("Delete", f"Delete macro '{name}'?"):
            delete_macro(name, folder=self._settings["macro_folder"])
            self._refresh_library()

    # ── Record / Play / Stop ────────────────────────────────────────────────

    def _toggle_record(self):
        if self._saving:
            return  # dialog is open, ignore hotkey
        if self._recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        if self._playing:
            self._stop_playing()
        self._recording = True
        self._btn_record.config(text="■ Stop Rec")
        self._set_status("Recording...")
        rec_key_obj = self._parse_hotkey_to_key(self._settings["record_hotkey"])
        play_key_obj = self._parse_hotkey_to_key(self._settings["play_hotkey"])
        filter_keys = [k for k in [rec_key_obj, play_key_obj] if k is not None]
        self._recorder = Recorder(filter_keys=filter_keys)
        self._recorder.start()

    def _stop_recording(self):
        events = self._recorder.stop()
        self._recording = False
        self._btn_record.config(text="● Record")
        self._set_status("Idle")
        if not events:
            return
        
        try:
            name = "Quick_Record"
            folder = self._settings["macro_folder"]
            save_macro(name, events, folder=folder)
            self._refresh_library()
            # Select the newly saved macro
            for i in range(self._listbox.size()):
                if self._listbox.get(i) == name:
                    self._listbox.selection_clear(0, "end")
                    self._listbox.selection_set(i)
                    self._listbox.activate(i)
                    self._listbox.see(i)
                    break
        except Exception as e:
            self._set_status(f"Save Error: {e}")

    def _toggle_play(self):
        if self._saving:
            return
        if self._playing:
            self._stop_playing()
        else:
            self._start_playing()

    def _start_playing(self):
        if self._recording:
            self._stop_recording()
            if self._recording or self._saving:
                return  # Still saving or cancelled

        name = self._selected_macro()
        if not name:
            messagebox.showinfo("No macro selected", "Select a macro from the library first.")
            return
        try:
            events = load_macro(name, folder=self._settings["macro_folder"])
        except (FileNotFoundError, ValueError) as e:
            messagebox.showerror("Load Error", str(e))
            self._refresh_library()
            return
        
        try:
            repeat_count = int(self._repeat_var.get() or "1")
        except ValueError:
            repeat_count = 1
            
        if repeat_count < 1:
            repeat_count = 1

        self._playing = True
        self._btn_play.config(text="■ Stop Play")
        self._set_status(f"Playing: {name} (1/{repeat_count})")
        speed = self._speed_var.get()
        self._player = Player()

        def run():
            for i in range(repeat_count):
                if not self._playing or self._player._stop_event.is_set():
                    break
                try:
                    self.after(0, lambda current=i+1: self._set_status(f"Playing: {name} ({current}/{repeat_count})"))
                except RuntimeError:
                    pass
                self._player.play(events, speed=speed)
                
            try:
                self.after(0, self._on_play_finished)
            except RuntimeError:
                pass  # window was destroyed before playback finished

        threading.Thread(target=run, daemon=True).start()

    def _stop_playing(self):
        self._player.stop()

    def _on_play_finished(self):
        self._playing = False
        self._btn_play.config(text="▶ Play")
        self._set_status("Idle")

    def _stop_all(self):
        if self._recording:
            self._stop_recording()
        if self._playing:
            self._stop_playing()

    # ── Hotkeys ─────────────────────────────────────────────────────────────

    def _register_hotkeys(self):
        from pynput import keyboard as kb
        if self._hotkey_listener:
            self._hotkey_listener.stop()

        rec_key = self._settings["record_hotkey"]
        play_key = self._settings["play_hotkey"]

        if rec_key == play_key:
            self._set_status("Warning: record and play hotkeys must be different")
            return

        def on_rec():
            self.after(0, self._toggle_record)

        def on_play():
            self.after(0, self._toggle_play)

        try:
            self._hotkey_listener = kb.GlobalHotKeys(
                {rec_key: on_rec, play_key: on_play}
            )
            self._hotkey_listener.start()
        except Exception as e:
            self._set_status(f"Warning: hotkey registration failed ({e})")

    # ── Settings ─────────────────────────────────────────────────────────────

    def _on_settings_changed(self, *args):
        self._settings["record_hotkey"] = self._rec_hotkey_var.get()
        self._settings["play_hotkey"] = self._play_hotkey_var.get()
        self._settings["speed"] = self._speed_var.get()
        try:
            val = int(self._repeat_var.get() or "1")
            self._settings["repeat_count"] = max(1, val)
        except ValueError:
            self._settings["repeat_count"] = 1
        save_settings(self._settings)
        self._register_hotkeys()

    def _choose_folder(self):
        folder = filedialog.askdirectory(title="Choose macro folder")
        if folder:
            self._settings["macro_folder"] = folder
            self._folder_var.set(folder)
            save_settings(self._settings)
            self._refresh_library()

    # ── Misc ─────────────────────────────────────────────────────────────────

    def _set_status(self, msg):
        self._status_var.set(f"Status: {msg}")

    def _on_close(self):
        # Stop recording without prompting — discard in-progress recording
        if self._recording:
            self._recorder.stop()  # discard events
            self._recording = False
        if self._playing:
            self._stop_playing()
        if self._hotkey_listener:
            self._hotkey_listener.stop()
        self.destroy()
