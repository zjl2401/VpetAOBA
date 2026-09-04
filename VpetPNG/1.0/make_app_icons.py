#!/usr/bin/env python3
"""用 stand 立绘生成桌面快捷方式 / 托盘图标（抠绿幕、等比例缩放或居中裁剪，禁止非等比拉伸）。"""

from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent


def stand_sources() -> list[Path]:
    # 优先普通（normal）预抠 stand；勿用 sprites_black / 黑框立绘
    return [
        ROOT / "assets" / "cutout" / "sprites" / "stand.png",
        ROOT / "assets" / "sprites" / "stand.png",
        ROOT / "assets" / "sprites" / "stand.jpg",
        ROOT / "assets" / "raw_green" / "sprites" / "stand.jpg",
        ROOT / "gallery" / "stand.png",
        ROOT / "gallery" / "stand.jpg",
    ]


def _is_chroma_green(r: int, g: int, b: int, a: int = 255) -> bool:
    if a < 8:
        return False
    if g > 200 and r < 90 and b < 90:
        return True
    return g > 100 and g >= r + 15 and g >= b + 25


def remove_outer_green(img: Image.Image) -> Image.Image:
    """只抠与边缘连通的绿幕，保留角色内部绿色像素。"""
    rgba = img.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()
    visited = [[False] * w for _ in range(h)]
    q: deque[tuple[int, int]] = deque()
    for x in range(w):
        q.append((x, 0))
        q.append((x, h - 1))
    for y in range(h):
        q.append((0, y))
        q.append((w - 1, y))
    while q:
        x, y = q.popleft()
        if x < 0 or y < 0 or x >= w or y >= h or visited[y][x]:
            continue
        r, g, b, a = px[x, y]
        if not _is_chroma_green(r, g, b, a):
            continue
        visited[y][x] = True
        px[x, y] = (r, g, b, 0)
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return rgba


def prepare_stand(im: Image.Image) -> Image.Image:
    keyed = remove_outer_green(im)
    bbox = keyed.getbbox()
    if bbox:
        keyed = keyed.crop(bbox)
    return keyed


def load_stand() -> Image.Image:
    for p in stand_sources():
        if p.is_file():
            print("source:", p)
            return prepare_stand(Image.open(p))
    raise SystemExit("stand sprite not found")


def fit_square_cover(im: Image.Image, size: int) -> Image.Image:
    """居中裁成正方形后再等比缩放（cover）。"""
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    cropped = im.crop((left, top, left + side, top + side))
    return cropped.resize((size, size), Image.Resampling.LANCZOS)


def fit_square_contain(
    im: Image.Image,
    size: int,
    *,
    bg: tuple[int, int, int, int] = (0, 0, 0, 0),
    pad_ratio: float = 0.08,
) -> Image.Image:
    """等比缩放入正方形（contain），四周补边，不拉伸。"""
    inner = max(1, int(size * (1.0 - pad_ratio)))
    w, h = im.size
    scale = min(inner / max(w, 1), inner / max(h, 1))
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    scaled = im.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), bg)
    canvas.paste(scaled, ((size - nw) // 2, (size - nh) // 2), scaled)
    return canvas


def _save_replace(img: Image.Image, path: Path, **kwargs) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    img.save(tmp, **kwargs)
    try:
        tmp.replace(path)
    except OSError:
        # 被预览/杀软占用时尽力覆盖
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        tmp.replace(path)


def fit_square_contain_nearest(
    im: Image.Image,
    size: int,
    *,
    bg: tuple[int, int, int, int] = (0, 0, 0, 0),
    pad_ratio: float = 0.04,
) -> Image.Image:
    """像素立绘用最近邻缩放，避免 LANCZOS 发糊。"""
    inner = max(1, int(size * (1.0 - pad_ratio)))
    w, h = im.size
    scale = min(inner / max(w, 1), inner / max(h, 1))
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    scaled = im.resize((nw, nh), Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", (size, size), bg)
    canvas.paste(scaled, ((size - nw) // 2, (size - nh) // 2), scaled)
    return canvas


def main() -> None:
    src = load_stand()
    # 快捷方式 / 托盘：normal stand、透明底、最近邻保像素
    icon256 = fit_square_contain_nearest(src, 256, bg=(0, 0, 0, 0), pad_ratio=0.04)
    png = ROOT / "app_icon.png"
    ico = ROOT / "app_icon.ico"
    _save_replace(icon256, png, format="PNG")
    _save_replace(
        icon256,
        ico,
        format="ICO",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
    )
    _save_replace(icon256, ROOT / "app_icon1.png", format="PNG")
    print("wrote", png)
    print("wrote", ico)


if __name__ == "__main__":
    main()
