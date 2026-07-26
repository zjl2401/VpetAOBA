"""桌面秒表 / 计时器：数字框 + 绕框行走的小像素人。"""

from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Callable

from PIL import Image, ImageTk


def _is_outer_chroma_green(r: int, g: int, b: int, a: int = 255) -> bool:
    """外圈绿幕键色（含青草绿幕与偏亮绿底）。"""
    if a < 8:
        return False
    if g > 200 and r < 90 and b < 90:
        return True
    if g > 170 and b < 45 and 90 < r < 210 and (g - r) > 20 and (g - b) > 120:
        return True
    return g > 100 and g >= r + 15 and g >= b + 25


def _remove_outer_green(img: Image.Image) -> Image.Image:
    """只抠与画面边缘连通的绿色外圈，保留图内绿色细节。"""
    rgba = img.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()
    vis = [[False] * w for _ in range(h)]
    q: deque[tuple[int, int]] = deque()

    def try_push(x: int, y: int) -> None:
        if not (0 <= x < w and 0 <= y < h) or vis[y][x]:
            return
        r, g, b, a = px[x, y]
        if not _is_outer_chroma_green(r, g, b, a):
            return
        vis[y][x] = True
        q.append((x, y))

    for x in range(w):
        try_push(x, 0)
        try_push(x, h - 1)
    for y in range(h):
        try_push(0, y)
        try_push(w - 1, y)

    while q:
        x, y = q.popleft()
        px[x, y] = (0, 0, 0, 0)
        try_push(x + 1, y)
        try_push(x - 1, y)
        try_push(x, y + 1)
        try_push(x, y - 1)
    return rgba


def format_clock_ms(ms: int) -> str:
    """毫秒 → HH:MM:SS 或 MM:SS（不足一小时）。"""
    total = max(0, int(ms) // 1000)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def format_duration_cn(seconds: float) -> str:
    """中文时长：1小时23分 / 45分12秒 / 8秒。"""
    sec = max(0, int(round(seconds)))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    parts: list[str] = []
    if h:
        parts.append(f"{h}小时")
    if m:
        parts.append(f"{m}分")
    if s or not parts:
        parts.append(f"{s}秒")
    return "".join(parts)


def perimeter_point(
    t: float,
    *,
    left: float,
    top: float,
    width: float,
    height: float,
) -> tuple[float, float, str]:
    """
    沿矩形顺时针走一圈。t 为周长归一化 [0,1)。
    返回 (x, y, edge) — edge ∈ top|right|bottom|left。
    """
    w = max(1.0, float(width))
    h = max(1.0, float(height))
    peri = 2.0 * (w + h)
    d = (t % 1.0) * peri
    if d <= w:
        return left + d, top, "top"
    d -= w
    if d <= h:
        return left + w, top + d, "right"
    d -= h
    if d <= w:
        return left + w - d, top + h, "bottom"
    d -= w
    return left, top + h - d, "left"


def edge_to_facing(edge: str) -> str:
    """行走朝向：与边前进方向一致。"""
    return {
        "top": "right",
        "right": "front",
        "bottom": "left",
        "left": "back",
    }.get(edge, "front")


def load_walker_frames(
    sprites_dir: Path,
    *,
    size: int = 28,
    style: str = "walk",
    load_raw: Callable[[str], Image.Image] | None = None,
) -> dict[str, list[ImageTk.PhotoImage]]:
    """加载走动四向各 2 帧，缩放到 size。

    style: walk | work | music（对应 walk*/work*/music* 资源）。
    """
    size = max(12, int(size))
    prefix = str(style or "walk").strip().lower()
    if prefix not in ("walk", "work", "music"):
        prefix = "walk"

    def _open(name: str) -> Image.Image:
        if load_raw is not None:
            raw = load_raw(name).convert("RGBA")
        else:
            raw = Image.open(sprites_dir / name).convert("RGBA")
        return _remove_outer_green(raw)

    def scale(im: Image.Image) -> ImageTk.PhotoImage:
        im = im.copy()
        im.thumbnail((size, size), Image.Resampling.NEAREST)
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        ox = (size - im.width) // 2
        oy = max(0, size - im.height)
        canvas.paste(im, (ox, oy), im)
        return ImageTk.PhotoImage(canvas)

    out: dict[str, list[ImageTk.PhotoImage]] = {}
    for key, names in (
        ("front", (f"{prefix}front1.jpg", f"{prefix}front2.jpg")),
        ("back", (f"{prefix}back1.jpg", f"{prefix}back2.jpg")),
        ("left", (f"{prefix}left1.jpg", f"{prefix}left2.jpg")),
    ):
        frames: list[ImageTk.PhotoImage] = []
        for n in names:
            try:
                frames.append(scale(_open(n)))
            except Exception:
                pass
        out[key] = frames
    right: list[ImageTk.PhotoImage] = []
    for n in (f"{prefix}left1.jpg", f"{prefix}left2.jpg"):
        try:
            right.append(scale(_open(n).transpose(Image.Transpose.FLIP_LEFT_RIGHT)))
        except Exception:
            pass
    out["right"] = right
    # 缺资源时回退到普通 walk，避免环绕小人空白
    if prefix != "walk" and not any(out.values()):
        return load_walker_frames(sprites_dir, size=size, style="walk", load_raw=load_raw)
    return out


def load_sleep_frames(
    sprites_dir: Path,
    *,
    size: int = 28,
    load_raw: Callable[[str], Image.Image] | None = None,
) -> list[ImageTk.PhotoImage]:
    """加载 sleep1/sleep2，缩放到 size，供睡眠时钟环绕轮播。"""
    size = max(12, int(size))

    def _open(name: str) -> Image.Image:
        if load_raw is not None:
            raw = load_raw(name).convert("RGBA")
        else:
            raw = Image.open(sprites_dir / name).convert("RGBA")
        return _remove_outer_green(raw)

    def scale(im: Image.Image) -> ImageTk.PhotoImage:
        im = im.copy()
        im.thumbnail((size, size), Image.Resampling.NEAREST)
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        ox = (size - im.width) // 2
        oy = max(0, size - im.height)
        canvas.paste(im, (ox, oy), im)
        return ImageTk.PhotoImage(canvas)

    frames: list[ImageTk.PhotoImage] = []
    for name in ("sleep1.jpg", "sleep2.jpg"):
        try:
            frames.append(scale(_open(name)))
        except Exception:
            pass
    return frames


def walker_progress(elapsed_ms: float, *, lap_ms: float = 6200.0) -> float:
    """按毫秒推进绕圈进度 [0,1)。"""
    lap = max(800.0, float(lap_ms))
    return (max(0.0, float(elapsed_ms)) / lap) % 1.0
