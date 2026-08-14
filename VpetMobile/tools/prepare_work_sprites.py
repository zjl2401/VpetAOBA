#!/usr/bin/env python3
"""从桌面 assets 导出工作模式素材到 VpetMobile（透明 PNG）。

对齐 pet.py：
- work* / ncwork*：外圈连通绿幕 → 透明
- box.jpg / flag.jpg：仅抠外圈青草绿幕（_remove_outer_lime_green），保留主体
"""
from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
DESK = ROOT / "VpetPNG" / "1.0" / "assets"
SPRITES = DESK / "sprites"
PROPS = DESK / "props"
OUT = ROOT / "VpetMobile" / "app" / "src" / "main" / "assets" / "sprites"
SHARED = ROOT / "VpetMobile" / "assets_shared" / "sprites"
PROP_SIZE = 96  # 箱/旗仍进固定画布（道具 UI）；立绘不缩放

WORK_GREEN = [
    "workstand.jpg",
    "workfront1.jpg",
    "workfront2.jpg",
    "workback1.jpg",
    "workback2.jpg",
    "workleft1.jpg",
    "workleft2.jpg",
]
NC_WORK = [
    "ncworkstand.png",
    "ncworkfront1.png",
    "ncworkfront2.png",
    "ncworkback1.png",
    "ncworkback2.png",
    "ncworkleft1.png",
    "ncworkleft2.png",
]
LIME_PROPS = ["box.jpg", "flag.jpg"]


def is_chroma_green(r: int, g: int, b: int, a: int = 255) -> bool:
    if a < 8:
        return False
    if g > 200 and r < 90 and b < 90:
        return True
    return g > 100 and g >= r + 15 and g >= b + 25


def is_outer_lime(r: int, g: int, b: int, a: int = 255) -> bool:
    """对齐 pet._is_outer_lime_screen。"""
    if a < 8:
        return False
    return (
        g > 170
        and b < 45
        and 90 < r < 210
        and (g - r) > 20
        and (g - b) > 120
    )


def flood_key(img: Image.Image, pred) -> Image.Image:
    rgba = img.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()
    vis = [[False] * w for _ in range(h)]
    q: deque[tuple[int, int]] = deque()
    for x in range(w):
        q.append((x, 0))
        q.append((x, h - 1))
    for y in range(h):
        q.append((0, y))
        q.append((w - 1, y))
    while q:
        x, y = q.popleft()
        if x < 0 or y < 0 or x >= w or y >= h or vis[y][x]:
            continue
        r, g, b, a = px[x, y]
        if not pred(r, g, b, a):
            continue
        vis[y][x] = True
        px[x, y] = (r, g, b, 0)
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return rgba


def crop_alpha(img: Image.Image) -> Image.Image:
    """只裁透明包围盒，不缩放。"""
    bbox = img.getbbox()
    if bbox:
        return img.crop(bbox)
    return img


def to_fixed_canvas(img: Image.Image, size: int) -> Image.Image:
    """对照 _to_fixed_canvas：等比缩进固定方画布，透明底。"""
    img = img.convert("RGBA")
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    w, h = img.size
    scale = min(size / w, size / h)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    img = img.resize((nw, nh), Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(img, ((size - nw) // 2, (size - nh) // 2), img)
    return canvas


def save_both(img: Image.Image, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    SHARED.mkdir(parents=True, exist_ok=True)
    img.save(OUT / name, "PNG")
    img.save(SHARED / name, "PNG")
    print("ok", name, img.size)


def export_green(name: str) -> None:
    src = SPRITES / name
    if not src.exists():
        print("MISSING", src, file=sys.stderr)
        return
    keyed = crop_alpha(flood_key(Image.open(src), is_chroma_green))
    save_both(keyed, name.replace(".jpg", ".png"))


def export_nc(name: str) -> None:
    src = SPRITES / name
    if not src.exists():
        print("MISSING", src, file=sys.stderr)
        return
    keyed = crop_alpha(flood_key(Image.open(src), is_chroma_green))
    save_both(keyed, name)


def export_prop(name: str) -> None:
    src = PROPS / name
    if not src.exists():
        print("MISSING", src, file=sys.stderr)
        return
    keyed = flood_key(Image.open(src), is_outer_lime)
    canvas = to_fixed_canvas(keyed, PROP_SIZE)
    save_both(canvas, name.replace(".jpg", ".png"))


def main() -> int:
    if not SPRITES.is_dir() or not PROPS.is_dir():
        print(f"missing assets under {DESK}", file=sys.stderr)
        return 1
    for n in WORK_GREEN:
        export_green(n)
    for n in NC_WORK:
        export_nc(n)
    for n in LIME_PROPS:
        export_prop(n)
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
