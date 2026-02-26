# Cafelito

Keeps your computer awake by periodically nudging the mouse cursor.
Double-click the app, set your interval, and it runs silently in the system tray.

Works on macOS, Linux, and Windows.

## How it works

```
Double-click Cafelito
        │
        ▼
┌─────────────────────────┐
│  Move mouse every: [60] │
│      [Cancel]  [Start]  │
└─────────────────────────┘
        │ Start
        ▼
  App disappears — tray icon appears
  Mouse nudges every X seconds
        │
        ▼  (right-click the tray icon)
  ┌──────────────────┐
  │  Moving every 60s│
  │  ──────────────  │
  │  Quit            │
  └──────────────────┘
```

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run from source

```bash
python mouse_mover.py
```

## Build a standalone executable

Install the build dependencies first:

```bash
pip install -r requirements-dev.txt
```

Then run PyInstaller:

**macOS** — produces `dist/Cafelito.app`:
```bash
pyinstaller --onefile --windowed --name Cafelito mouse_mover.py
```

**Windows** — produces `dist/Cafelito.exe`:
```bash
pyinstaller --onefile --windowed --name Cafelito mouse_mover.py
```

**Linux** — produces `dist/Cafelito`:
```bash
pyinstaller --onefile --name Cafelito mouse_mover.py
```

> **macOS note:** on first run the system may ask for Accessibility permissions
> (System Settings → Privacy & Security → Accessibility). This is required for
> mouse control to work.

## Run tests

```bash
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pytest test_mouse_mover.py -v
```
