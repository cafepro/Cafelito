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
    """Generates the tray icon (coffee cup) programmatically using Pillow."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Steam
    for x in [22, 30, 38]:
        d.line([(x, 22), (x - 3, 14), (x + 3, 6)], fill=(200, 200, 220, 180), width=2)

    # Cup body
    d.rectangle([12, 26, 46, 50], fill=(101, 67, 33), outline=(60, 35, 10), width=2)

    # Cup handle
    d.arc([43, 31, 55, 45], start=270, end=90, fill=(60, 35, 10), width=3)

    # Saucer
    d.ellipse([8, 48, 50, 56], fill=(130, 85, 40), outline=(60, 35, 10), width=1)

    return img


def _parse_interval(raw: str) -> int:
    """Parses and validates the interval string. Raises ValueError if invalid."""
    value = int(raw)
    if value <= 0:
        raise ValueError("Interval must be a positive integer.")
    return value


def move_mouse() -> None:
    """Nudges the cursor slightly and returns it to the original position."""
    pyautogui.moveRel(MOVE_RADIUS, 0, duration=0.2)
    pyautogui.moveRel(-MOVE_RADIUS, 0, duration=0.2)


def run_mover(interval: int, stop_event: threading.Event) -> None:
    """
    Background loop: nudges the mouse only if it has been idle for `interval` seconds.
    Polls every second to detect user movement without adding noticeable CPU usage.
    """
    last_pos = pyautogui.position()
    last_moved_at = time.monotonic()

    while not stop_event.is_set():
        stop_event.wait(1)  # poll every second

        current_pos = pyautogui.position()
        now = time.monotonic()

        if current_pos != last_pos:
            last_pos = current_pos
            last_moved_at = now
        elif now - last_moved_at >= interval:
            move_mouse()
            last_moved_at = now
            last_pos = pyautogui.position()


def start_tray(interval: int) -> None:
    """Starts the mover thread and runs the system tray icon (blocks until quit)."""
    import pystray

    stop_event = threading.Event()
    threading.Thread(
        target=run_mover, args=(interval, stop_event), daemon=True
    ).start()

    def on_quit(icon, _item):
        stop_event.set()
        icon.stop()

    icon = pystray.Icon(
        name="Cafelito",
        icon=build_icon_image(),
        title="Cafelito",
        menu=pystray.Menu(
            pystray.MenuItem(f"Moving every {interval}s", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", on_quit),
        ),
    )
    icon.run()


def show_dialog() -> int | None:
    """
    Shows the configuration dialog.
    Returns the chosen interval in seconds, or None if the user cancelled.
    """
    import tkinter as tk
    from tkinter import messagebox, ttk

    root = tk.Tk()
    root.title("Cafelito")
    root.resizable(False, False)

    width, height = 300, 150
    root.update_idletasks()
    x = (root.winfo_screenwidth() - width) // 2
    y = (root.winfo_screenheight() - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")

    result: list[int | None] = [None]

    frame = ttk.Frame(root, padding=20)
    frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(frame, text="Move mouse every (seconds):").pack(anchor=tk.W)

    interval_var = tk.StringVar(value=str(DEFAULT_INTERVAL))
    entry = ttk.Entry(frame, textvariable=interval_var, width=12)
    entry.pack(anchor=tk.W, pady=(6, 16))
    entry.focus_set()
    entry.select_range(0, tk.END)

    def on_start():
        try:
            result[0] = _parse_interval(interval_var.get())
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

        interval = show_dialog()
        if interval is None:
            logging.info("User cancelled — exiting")
            sys.exit(0)

        logging.info("Starting tray with interval=%ds", interval)
        start_tray(interval)
    except Exception as exc:
        logging.exception("Unexpected error")
        _show_native_error(f"{exc}\n\nSee {LOG_FILE} for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
