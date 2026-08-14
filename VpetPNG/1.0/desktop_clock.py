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
        # 先缩到时钟尺寸再抠绿：整图 flood-fill 会在首次开音乐/工作时钟卡十几秒
        work = raw.copy()
        work.thumbnail((max(size * 2, 48), max(size * 2, 48)), Image.Resampling.NEAREST)
        return _remove_outer_green(work)

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
        work = raw.copy()
        work.thumbnail((max(size * 2, 48), max(size * 2, 48)), Image.Resampling.NEAREST)
        return _remove_outer_green(work)

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


def _bayer_keep_level(transparency: float) -> int:
    """transparency 0=全不透明，1=全挖空；返回 Bayer 矩阵保留阈值。"""
    tr = max(0.0, min(0.95, float(transparency)))
    return int(round((1.0 - tr) * 16))


_BAYER_4X4 = (
    (0, 8, 2, 10),
    (12, 4, 14, 6),
    (3, 11, 1, 9),
    (15, 7, 13, 5),
)


def make_keyed_fill(
    width: int,
    height: int,
    fill_hex: str,
    *,
    transparency: float = 0.2,
    key_rgb: tuple[int, int, int] = (255, 0, 255),
) -> Image.Image:
    """单色底板 + 品红键色抖动挖空（按钮等小块半透明）。"""
    w = max(1, int(width))
    h = max(1, int(height))
    keep_level = _bayer_keep_level(transparency)

    def _rgb(hx: str) -> tuple[int, int, int]:
        s = (hx or "").strip().lstrip("#")
        if len(s) != 6:
            return (74, 144, 216)
        try:
            return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
        except Exception:
            return (74, 144, 216)

    rgb = _rgb(fill_hex)
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        row = _BAYER_4X4[y & 3]
        for x in range(w):
            px[x, y] = rgb if row[x & 3] < keep_level else key_rgb
    return img


def make_panel_gradient(
    width: int,
    height: int,
    *,
    left_hex: str = "#ff9ec8",
    right_hex: str = "#7eb8ff",
    transparency: float = 0.18,
    key_rgb: tuple[int, int, int] = (255, 0, 255),
) -> Image.Image:
    """粉→蓝水平渐变底板（供秒表/计时器数字框）。

    transparency: 透明度 0~1（默认 0.18，与面板轻微玻璃感接近）。色键窗无法真·半透明，
    用品红键色像素抖动挖空，视觉上约等于该透明度。
    """
    w = max(1, int(width))
    h = max(1, int(height))
    keep_level = _bayer_keep_level(transparency)

    def _rgb(hx: str) -> tuple[int, int, int]:
        s = (hx or "").strip().lstrip("#")
        if len(s) != 6:
            return (255, 158, 200)
        try:
            return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
        except Exception:
            return (255, 158, 200)

    r0, g0, b0 = _rgb(left_hex)
    r1, g1, b1 = _rgb(right_hex)
    img = Image.new("RGB", (w, h))
    px = img.load()
    denom = max(1, w - 1)
    for x in range(w):
        t = x / denom
        r = int(r0 + (r1 - r0) * t)
        g = int(g0 + (g1 - g0) * t)
        b = int(b0 + (b1 - b0) * t)
        col = (r, g, b)
        for y in range(h):
            if _BAYER_4X4[y & 3][x & 3] < keep_level:
                px[x, y] = col
            else:
                px[x, y] = key_rgb
    return img



def trail_points(
    t: float,
    *,
    left: float,
    top: float,
    width: float,
    height: float,
    count: int = 10,
    spacing: float = 0.012,
) -> list[tuple[float, float, int]]:
    """绕圈小人后方采样点（越靠后 index 越大），用于像素流星尾迹。"""
    n = max(1, int(count))
    step = max(0.004, float(spacing))
    out: list[tuple[float, float, int]] = []
    for i in range(1, n + 1):
        ti = (float(t) - i * step) % 1.0
        x, y, _edge = perimeter_point(ti, left=left, top=top, width=width, height=height)
        out.append((x, y, i))
    return out
