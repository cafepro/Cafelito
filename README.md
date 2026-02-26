# Cafelito

Periodically moves the mouse cursor to prevent the computer from auto-locking. Works on macOS, Linux, and Windows.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Default interval (60 seconds)
python mouse_mover.py

# Custom interval in seconds
python mouse_mover.py --interval 30
python mouse_mover.py -i 120

# Using an environment variable
MOUSE_MOVER_INTERVAL=45 python mouse_mover.py
```

## Run in background

**macOS / Linux:**
```bash
nohup python mouse_mover.py --interval 60 &
```

**Windows (PowerShell):**
```powershell
Start-Process python -ArgumentList "mouse_mover.py --interval 60" -WindowStyle Hidden
```
