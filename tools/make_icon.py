#!/usr/bin/env python3
"""
Regenerate the multi-resolution Windows icon for IPTV-Saba.

The title-bar / taskbar "mini" icon wants a 16x16 frame; a single-size .ico
forces Windows and Qt to downscale on the fly, which looks blurry. This script
rebuilds Assets/iptv-logo2.ico with the standard set of sizes so each context
(16/24/32/48/256) gets a crisp frame.

By default it reuses the largest frame already embedded in the existing .ico as
the master. Pass a higher-resolution PNG (e.g. 256x256) as the first argument to
produce sharper large icons:

    python tools/make_icon.py [source_image.png]

Pillow is a dev-only dependency (it is excluded from the PyInstaller bundle).
"""
import os
import sys

from PIL import Image

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_PATH = os.path.join(PROJECT_ROOT, "src", "Assets", "iptv-logo2.ico")
ICON_SIZES = [16, 24, 32, 48, 64, 128, 256]


def load_master(source: str) -> Image.Image:
    """Load the best available source image as an RGBA master."""
    img = Image.open(source)

    # An .ico is a container; pick its largest embedded frame as the master.
    if (img.format or "").upper() == "ICO":
        largest = None
        for size in sorted(getattr(img, "ico", img).sizes()) if hasattr(img, "ico") else []:
            pass  # fall through to manual scan below
        # Robust scan: Pillow exposes frames via n_frames for some formats, but
        # for ICO the reliable path is to try each declared size.
        try:
            sizes = img.ico.sizes()  # type: ignore[attr-defined]
        except Exception:
            sizes = None
        if sizes:
            w, h = max(sizes, key=lambda s: s[0] * s[1])
            img.size = (w, h)
            largest = img.ico.getimage((w, h))  # type: ignore[attr-defined]
        if largest is not None:
            img = largest

    return img.convert("RGBA")


def main() -> int:
    source = sys.argv[1] if len(sys.argv) > 1 else ICON_PATH
    if not os.path.isfile(source):
        print(f"ERROR: source not found: {source}")
        return 1

    master = load_master(source)
    print(f"Master image: {source}  ({master.width}x{master.height})")

    # Only emit sizes up to the master resolution; upscaling looks worse than
    # letting Windows scale a larger frame down.
    sizes = [s for s in ICON_SIZES if s <= max(master.size)]
    if 16 not in sizes:
        sizes.append(16)  # always provide the mini icon
    sizes = sorted(set(sizes))

    master.save(ICON_PATH, format="ICO", sizes=[(s, s) for s in sizes])
    print(f"Wrote {ICON_PATH} with sizes: {sizes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
