#!/usr/bin/env python3
"""桌面立绘 → 手机 assets：先缩到 MAX 再抠绿（快）。"""
from __future__ import annotations

from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(r"C:\Users\36255\Desktop\VpetAOBA\VpetPNG\1.0")
SRC_SPRITES = ROOT / "assets" / "sprites"
SRC_MINI = ROOT / "assets" / "minipet"
SRC_PROPS = ROOT / "assets" / "props"
OUT_SPRITES = Path(r"C:\Users\36255\Desktop\VpetAOBA\VpetMobile\app\src\main\assets\sprites")
OUT_MINI = Path(r"C:\Users\36255\Desktop\VpetAOBA\VpetMobile\app\src\main\assets\minipet")
MAX_SIDE = 512
MINI_CANVAS = 512


def green_mask(arr: np.ndarray) -> np.ndarray:
    r = arr[..., 0].astype(np.int16)
    g = arr[..., 1].astype(np.int16)
    b = arr[..., 2].astype(np.int16)
    a = arr[..., 3]
    return (a > 8) & (
        ((g > 200) & (r < 90) & (b < 90)) | ((g > 100) & (g >= r + 15) & (g >= b + 25))
    )


def magenta_mask(arr: np.ndarray) -> np.ndarray:
    r, g, b, a = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]
    return (a > 8) & (r > 200) & (b > 200) & (g < 80)


def flood_key(img: Image.Image, mask_fn) -> Image.Image:
    arr = np.asarray(img.convert("RGBA"), dtype=np.uint8).copy()
    h, w = arr.shape[:2]
    key = mask_fn(arr)
    vis = np.zeros((h, w), dtype=np.uint8)
    q: deque[tuple[int, int]] = deque()
    for x in range(w):
        q.append((x, 0))
        q.append((x, h - 1))
    for y in range(h):
        q.append((0, y))
        q.append((w - 1, y))
    while q:
        x, y = q.popleft()
        if x < 0 or y < 0 or x >= w or y >= h or vis[y, x]:
            continue
        if not key[y, x]:
            continue
        vis[y, x] = 1
        arr[y, x, 3] = 0
        q.append((x + 1, y))
        q.append((x - 1, y))
        q.append((x, y + 1))
        q.append((x, y - 1))
    return Image.fromarray(arr, "RGBA")


def down_to_max(img: Image.Image, max_side: int) -> Image.Image:
    w, h = img.size
    scale = min(max_side / max(w, 1), max_side / max(h, 1), 1.0)
    if scale >= 1.0:
        return img.convert("RGBA") if img.mode != "RGBA" else img
    return img.convert("RGBA").resize(
        (max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.BILINEAR
    )


def export_cropped(src: Path, dst: Path, *, magenta: bool = False) -> None:
    small = down_to_max(Image.open(src), MAX_SIDE)
    keyed = flood_key(small, magenta_mask if magenta else green_mask)
    bbox = keyed.getbbox()
    if bbox:
        keyed = keyed.crop(bbox)
    dst.parent.mkdir(parents=True, exist_ok=True)
    keyed.save(dst, "PNG")


def export_minipet_canvas(src: Path, dst: Path) -> None:
    small = down_to_max(Image.open(src), MINI_CANVAS)
    keyed = flood_key(small, green_mask)
    bbox = keyed.getbbox()
    if bbox:
        keyed = keyed.crop(bbox)
    w, h = keyed.size
    out = Image.new("RGBA", (MINI_CANVAS, MINI_CANVAS), (0, 0, 0, 0))
    # 不放大：若内容小于画布则原样底对齐
    if w > MINI_CANVAS or h > MINI_CANVAS:
        scale = min(MINI_CANVAS / w, MINI_CANVAS / h)
        keyed = keyed.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
        w, h = keyed.size
    out.alpha_composite(keyed, ((MINI_CANVAS - w) // 2, MINI_CANVAS - h))
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst, "PNG")


def main() -> int:
    OUT_SPRITES.mkdir(parents=True, exist_ok=True)
    OUT_MINI.mkdir(parents=True, exist_ok=True)
    n = 0
    for src in sorted(SRC_SPRITES.iterdir()):
        if not src.is_file() or src.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        stem = src.stem.lower()
        if stem.startswith("border") or stem.startswith("app_icon"):
            continue
        export_cropped(src, OUT_SPRITES / f"{src.stem}.png")
        n += 1
        if n % 15 == 0:
            print(f"... {n}")
    for stem in ("box", "flag"):
        for ext in (".jpg", ".png"):
            src = SRC_PROPS / f"{stem}{ext}"
            if src.is_file():
                export_cropped(src, OUT_SPRITES / f"{stem}.png", magenta=True)
                print("prop", stem)
                break
    m = 0
    for src in sorted(SRC_MINI.iterdir()):
        if not src.is_file() or src.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        export_minipet_canvas(src, OUT_MINI / f"{src.stem}.png")
        m += 1
        print("mini", src.stem)
    print(f"done sprites={n} minipet={m}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
