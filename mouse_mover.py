#!/usr/bin/env python3
"""
mouse_mover.py — Periodically moves the mouse cursor to prevent screen lock.

Configuration (priority order):
  1. CLI argument:        python mouse_mover.py --interval 60
  2. Environment variable: MOUSE_MOVER_INTERVAL=60 python mouse_mover.py
  3. Default value:       60 seconds
"""

import argparse
import os
import sys
import time
import pyautogui

DEFAULT_INTERVAL = 60
MOVE_RADIUS = 10  # pixels to shift on each nudge


def parse_interval() -> int:
    parser = argparse.ArgumentParser(
        description="Move the mouse periodically to prevent screen lock."
    )
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=None,
        help=f"Seconds between each movement (default: {DEFAULT_INTERVAL})",
    )
    args = parser.parse_args()

    if args.interval is not None:
        return args.interval

    env_val = os.environ.get("MOUSE_MOVER_INTERVAL")
    if env_val is not None:
        try:
            return int(env_val)
        except ValueError:
            print(f"[!] MOUSE_MOVER_INTERVAL='{env_val}' is not a valid number. Using {DEFAULT_INTERVAL}s.")

    return DEFAULT_INTERVAL


def move_mouse() -> None:
    """Nudges the cursor slightly and returns it to the original position."""
    pyautogui.moveRel(MOVE_RADIUS, 0, duration=0.2)
    pyautogui.moveRel(-MOVE_RADIUS, 0, duration=0.2)


def main() -> None:
    pyautogui.FAILSAFE = False  # prevent corner-of-screen from killing the script

    interval = parse_interval()
    print(f"[mouse_mover] Started. Moving mouse every {interval} seconds.")
    print("[mouse_mover] Press Ctrl+C to stop.")

    try:
        while True:
            move_mouse()
            print(f"[mouse_mover] Mouse nudged — next move in {interval}s")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[mouse_mover] Stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
