#!/usr/bin/env python3
"""
Cafelito — Keeps your computer awake by periodically nudging the mouse cursor.

Usage: double-click the executable (or run `python mouse_mover.py`).
A dialog will ask for the interval; after confirming, the app runs silently
in the system tray until you quit from the tray menu.
"""

import logging
import sys
import threading
import time
from pathlib import Path

import pyautogui
from PIL import Image, ImageDraw

LOG_FILE = Path.home() / "cafelito.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

MOVE_RADIUS = 10
DEFAULT_INTERVAL = 60


def build_icon_image() -> Image.Image:
    """Generates the tray icon (white coffee cup) programmatically using Pillow."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Steam
    for x in [22, 30, 38]:
        d.line([(x, 22), (x - 3, 14), (x + 3, 6)], fill=(220, 220, 230, 180), width=2)

    # Cup body
    d.rectangle([12, 26, 46, 50], fill=(255, 255, 255), outline=(180, 180, 180), width=2)

    # Cup handle
    d.arc([43, 31, 55, 45], start=270, end=90, fill=(180, 180, 180), width=3)

    # Saucer
    d.ellipse([8, 48, 50, 56], fill=(240, 240, 240), outline=(180, 180, 180), width=1)

    return img


def _parse_interval(raw: str) -> int:
    """Parses and validates the interval string. Raises ValueError if invalid."""
    value = int(raw)
    if value <= 0:
        raise ValueError("Interval must be a positive integer.")
    return value


def move_mouse(with_click: bool = False) -> None:
    """Nudges the cursor slightly, returns it to the original position, and optionally clicks."""
    pyautogui.moveRel(MOVE_RADIUS, 0, duration=0.2)
    pyautogui.moveRel(-MOVE_RADIUS, 0, duration=0.2)
    if with_click:
        time.sleep(0.05)  # let the cursor settle before clicking
        pyautogui.mouseDown(button="left")
        time.sleep(0.05)
        pyautogui.mouseUp(button="left")


def _system_idle_seconds() -> float | None:
    """
    Returns seconds since the last keyboard or mouse input using a platform-native API.
    Returns None if unavailable on this platform.

    On macOS, uses CGEventSourceSecondsSinceLastEventType (Quartz) which covers
    keyboard, mouse, and trackpad without requiring event listeners or extra permissions.
    """
    import platform
    if platform.system() == "Darwin":
        try:
            from Quartz import (  # type: ignore[import]
                CGEventSourceSecondsSinceLastEventType,
                kCGAnyInputEventType,
                kCGEventSourceStateHIDSystemState,
            )
            return CGEventSourceSecondsSinceLastEventType(
                kCGEventSourceStateHIDSystemState, kCGAnyInputEventType
            )
        except Exception as exc:
            logging.warning("Quartz idle detection unavailable: %s", exc)
    return None


def run_mover(interval: int, stop_event: threading.Event, with_click: bool = False) -> None:
    """
    Background loop: nudges the mouse only if there has been no input activity
    for `interval` seconds. Polls every second.

    On macOS, uses the Quartz system idle time (covers keyboard + mouse + trackpad).
    On other platforms, falls back to mouse position polling.
    """
    # Fallback state (only used on platforms without native idle detection)
    last_pos = None
    last_activity_at = time.monotonic()

    try:
        while not stop_event.is_set():
            stop_event.wait(1)  # poll every second

            idle = _system_idle_seconds()

            if idle is not None:
                # macOS native path: Quartz reports time since last keyboard/mouse/trackpad event
                if idle >= interval:
                    move_mouse(with_click=with_click)
            else:
                # Fallback: detect activity by polling mouse position
                now = time.monotonic()
                current_pos = pyautogui.position()
                if last_pos is None:
                    last_pos = current_pos
                if current_pos != last_pos:
                    last_pos = current_pos
                    last_activity_at = now
                elif now - last_activity_at >= interval:
                    move_mouse(with_click=with_click)
                    last_activity_at = now
                    last_pos = pyautogui.position()
    except Exception:
        logging.exception("Unexpected error in mover loop")


def start_tray(interval: int, with_click: bool = False) -> None:
    """Starts the mover thread and runs the system tray icon (blocks until quit)."""
    import pystray

    stop_event = threading.Event()

    def mover_target():
        try:
            run_mover(interval, stop_event, with_click)
        except Exception:
            logging.exception("Mover thread crashed")

    threading.Thread(target=mover_target, daemon=True).start()

    def on_quit(icon, _item):
        stop_event.set()
        icon.stop()

    status = f"Every {interval}s — move{' + click' if with_click else ''}"
    icon = pystray.Icon(
        name="Cafelito",
        icon=build_icon_image(),
        title="Cafelito",
        menu=pystray.Menu(
            pystray.MenuItem(status, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", on_quit),
        ),
    )
    icon.run()


def show_dialog() -> tuple[int, bool] | None:
    """
    Shows the configuration dialog.
    Returns (interval_seconds, with_click), or None if the user cancelled.
    """
    import tkinter as tk
    from tkinter import messagebox, ttk

    root = tk.Tk()
    root.title("Cafelito")
    root.resizable(False, False)

    width, height = 300, 180
    root.update_idletasks()
    x = (root.winfo_screenwidth() - width) // 2
    y = (root.winfo_screenheight() - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")

    result: list[tuple[int, bool] | None] = [None]

    frame = ttk.Frame(root, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frame, text="Move mouse every (seconds):").pack(anchor=tk.W)

    interval_var = tk.StringVar(value=str(DEFAULT_INTERVAL))
    entry = ttk.Entry(frame, textvariable=interval_var, width=12)
    entry.pack(anchor=tk.W, pady=(6, 10))
    entry.focus_set()
    entry.select_range(0, tk.END)

    click_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(
        frame,
        text="Also click (for apps like Slack)",
        variable=click_var,
    ).pack(anchor=tk.W, pady=(0, 16))

    def on_start():
        try:
            result[0] = (_parse_interval(interval_var.get()), click_var.get())
            root.destroy()
        except ValueError:
            messagebox.showerror(
                "Invalid value", "Please enter a positive integer.", parent=root
            )

    def on_cancel():
        root.destroy()

    btn_frame = ttk.Frame(frame)
    btn_frame.pack(anchor=tk.E)
    ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=(0, 8))
    ttk.Button(btn_frame, text="Start", command=on_start).pack(side=tk.LEFT)

    root.bind("<Return>", lambda _: on_start())
    root.bind("<Escape>", lambda _: on_cancel())
    root.protocol("WM_DELETE_WINDOW", on_cancel)

    root.mainloop()
    return result[0]


def _show_native_error(message: str) -> None:
    """Shows an error using a platform-native fallback when tkinter is unavailable."""
    import platform
    import subprocess

    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(
                ["osascript", "-e", f'display alert "Cafelito error" message "{message}"'],
                check=False,
            )
        elif system == "Windows":
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, "Cafelito error", 0x10)
        else:
            subprocess.run(["notify-send", "Cafelito error", message], check=False)
    except Exception:
        pass  # last resort — error is already in the log file


def main() -> None:
    try:
        pyautogui.FAILSAFE = False
        logging.info("Starting Cafelito")

        config = show_dialog()
        if config is None:
            logging.info("User cancelled — exiting")
            sys.exit(0)

        interval, with_click = config
        logging.info("Starting tray with interval=%ds, with_click=%s", interval, with_click)
        start_tray(interval, with_click=with_click)
    except Exception as exc:
        logging.exception("Unexpected error")
        _show_native_error(f"{exc}\n\nSee {LOG_FILE} for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
