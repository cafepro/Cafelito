#!/usr/bin/env python3
"""
Generates platform-specific icon files for the Cafelito executable.

Usage:
    python make_icon.py

Outputs:
    macOS   → icon.icns  (requires iconutil, bundled with Xcode Command Line Tools)
    Windows → icon.ico
    Linux   → icon.png
"""

import platform
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

from mouse_mover import build_icon_image


def make_icns(output: Path) -> None:
    base = build_icon_image().convert("RGBA")

    # iconutil requires a specific folder structure with exact filenames
    icon_sizes = [16, 32, 128, 256, 512]

    with tempfile.TemporaryDirectory() as tmp:
        iconset = Path(tmp) / "icon.iconset"
        iconset.mkdir()

        for size in icon_sizes:
            base.resize((size, size), Image.LANCZOS).save(
                iconset / f"icon_{size}x{size}.png"
            )
            base.resize((size * 2, size * 2), Image.LANCZOS).save(
                iconset / f"icon_{size}x{size}@2x.png"
            )

        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset), "-o", str(output)],
            check=True,
        )

    print(f"Generated {output}")


def make_ico(output: Path) -> None:
    sizes = [16, 32, 48, 64, 128, 256]
    base = build_icon_image().convert("RGBA")
    images = [base.resize((s, s), Image.LANCZOS) for s in sizes]
    images[0].save(
        output,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )
    print(f"Generated {output}")


def main() -> None:
    system = platform.system()
    if system == "Darwin":
        make_icns(Path("icon.icns"))
    elif system == "Windows":
        make_ico(Path("icon.ico"))
    else:
        build_icon_image().save("icon.png")
        print("Generated icon.png (Linux)")


if __name__ == "__main__":
    main()
