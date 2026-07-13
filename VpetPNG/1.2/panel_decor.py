"""像素风 UI 装饰：Vpetsign 素材 + 蓝粉黑白配色。"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageTk

THEME_BLUE = "#66ccff"
THEME_PINK = "#ff88cc"
THEME_BLUE_DEEP = "#4488dd"
THEME_WHITE = "#f4f8ff"
THEME_BLACK = "#0a0c12"
THEME_BG_INNER_RGBA = (14, 18, 30, 255)
THEME_PANEL_INNER = "#12182a"
THEME_ITEM_BG = "#181f34"

_VPETSIGN_DESKTOP = Path(r"C:\Users\36255\Desktop\Vpetsign")
_SIGN_IMG_CACHE: dict[tuple[str, int, int], Image.Image] = {}
_SIGN_PHOTO_CACHE: dict[tuple[str, int, int], ImageTk.PhotoImage] = {}


def resolve_signs_dir(bundle_dir: Path) -> Path:
    return bundle_dir / "assets" / "signs"


def _list_sign_files(signs_dir: Path) -> list[Path]:
    if signs_dir.is_dir():
        pngs = sorted(signs_dir.glob("*.png"))
        if pngs:
            return pngs
    if _VPETSIGN_DESKTOP.is_dir():
        return sorted(_VPETSIGN_DESKTOP.glob("*.jpg"))
    return []


def load_sign_image(signs_dir: Path, index: int) -> Image.Image | None:
    files = _list_sign_files(signs_dir)
    if not files:
        return None
    idx = max(0, min(len(files) - 1, int(index)))
    path = files[idx]
    try:
        img = Image.open(path).convert("RGBA")
        return _trim_sign_alpha(img)
    except Exception:
        return None


def _trim_sign_alpha(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    bbox = rgba.getbbox()
    if bbox is None:
        return rgba
    return rgba.crop(bbox)


def sign_photo(signs_dir: Path, index: int, size: int) -> ImageTk.PhotoImage | None:
    key = (str(signs_dir.resolve()), int(index), int(size))
    cached = _SIGN_PHOTO_CACHE.get(key)
    if cached is not None:
        return cached
    img = load_sign_image(signs_dir, index)
    if img is None:
        return None
    img = img.resize((max(8, size), max(8, size)), Image.NEAREST)
    photo = ImageTk.PhotoImage(img)
    _SIGN_PHOTO_CACHE[key] = photo
    return photo


def decorate_panel_border(img: Image.Image, corner: int, signs_dir: Path) -> Image.Image:
    """在九宫格边框上叠加像素条纹与四角标牌装饰。"""
    out = img.convert("RGBA").copy()
    draw = ImageDraw.Draw(out)
    w, h = out.size
    pink = (255, 136, 204, 255)
    blue = (102, 204, 255, 255)
    white = (220, 230, 255, 180)

    for x in range(corner, max(corner + 1, w - corner), 3):
        c = pink if (x // 3) % 2 == 0 else blue
        if corner >= 2:
            draw.point((x, max(0, corner - 2)), fill=c)
            draw.point((x + 1, max(0, corner - 1)), fill=white)
        if h > corner + 2:
            c2 = blue if (x // 3) % 2 == 0 else pink
            draw.point((x, min(h - 1, h - corner + 1)), fill=c2)

    for y in range(corner + 2, max(corner + 3, h - corner), 5):
        draw.point((max(0, corner - 1), y), fill=pink)
        draw.point((min(w - 1, w - corner), y + 1), fill=blue)

    placements = (
        (1, 2, 2),
        (2, w - corner - 18, 2),
        (8, 2, h - corner - 16),
        (9, w - corner - 18, h - corner - 16),
    )
    ornament = min(20, max(12, corner))
    for sign_idx, px, py in placements:
        sign = load_sign_image(signs_dir, sign_idx)
        if sign is None:
            continue
        scaled = sign.resize((ornament, ornament), Image.NEAREST)
        sx = max(0, min(w - ornament, px))
        sy = max(0, min(h - ornament, py))
        out.alpha_composite(scaled, (sx, sy))

    return out


def draw_pixel_divider(canvas, width: int, *, height: int = 5, bg: str = THEME_PANEL_INNER) -> None:
    canvas.delete("all")
    canvas.config(height=height, bg=bg)
    w = max(40, int(width))
    for i in range(0, w, 8):
        canvas.create_rectangle(i, 0, i + 4, height - 1, fill=THEME_PINK, outline="")
        canvas.create_rectangle(i + 4, 1, i + 8, height, fill=THEME_BLUE, outline="")
    canvas.create_rectangle(0, height - 1, w, height, fill=THEME_WHITE, outline="")


def pack_menu_chrome(parent, *, bg: str):
    import tkinter as tk

    shell = tk.Frame(parent, bg=THEME_BLUE, padx=1, pady=1)
    shell.pack()
    tk.Frame(shell, bg=THEME_PINK, height=2).pack(fill=tk.X)
    inner = tk.Frame(shell, bg=bg, padx=3, pady=3)
    inner.pack(fill=tk.BOTH, expand=True)
    tk.Frame(shell, bg=THEME_BLUE_DEEP, height=1).pack(fill=tk.X)
    return inner


def pack_panel_accent_bar(parent, *, bg: str) -> None:
    import tkinter as tk

    tk.Frame(parent, bg=THEME_PINK, height=3).pack(fill=tk.X)
    tk.Frame(parent, bg=THEME_BLUE, height=1).pack(fill=tk.X)
    tk.Frame(parent, bg=bg, height=2).pack(fill=tk.X)


# 深蓝 / 浅蓝 / 粉 / 黑 / 白 —— 菜单像素小图标与点击动画
_GLYPH_COLORS = (THEME_BLUE_DEEP, THEME_BLUE, THEME_PINK, THEME_BLACK, THEME_WHITE)
_GLYPH_PHOTO_CACHE: dict[tuple[str, int], ImageTk.PhotoImage] = {}


def _glyph_pattern(seed: int) -> list[tuple[int, int, str]]:
    """生成 8×8 像素图案坐标（相对原点）。"""
    colors = _GLYPH_COLORS
    c0 = colors[seed % len(colors)]
    c1 = colors[(seed + 1) % len(colors)]
    c2 = colors[(seed + 2) % len(colors)]
    style = seed % 6
    pts: list[tuple[int, int, str]] = []
    if style == 0:  # 菱形
        for x, y in ((3, 1), (2, 2), (4, 2), (1, 3), (5, 3), (2, 4), (4, 4), (3, 5)):
            pts.append((x, y, c0 if (x + y) % 2 == 0 else c1))
        pts.append((3, 3, c2))
    elif style == 1:  # 星点
        for x, y in ((3, 0), (3, 1), (2, 2), (3, 2), (4, 2), (1, 3), (2, 3), (3, 3), (4, 3), (5, 3), (3, 4), (3, 5), (3, 6)):
            pts.append((x, y, c0 if y < 3 else c1))
        pts.append((3, 3, THEME_WHITE))
    elif style == 2:  # 心形小像素
        for x, y in ((2, 1), (4, 1), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (1, 3), (2, 3), (3, 3), (4, 3), (5, 3), (2, 4), (3, 4), (4, 4), (3, 5)):
            pts.append((x, y, THEME_PINK if y < 4 else c0))
    elif style == 3:  # 对勾 / 箭头
        for x, y in ((1, 3), (2, 4), (3, 5), (4, 4), (5, 3), (6, 2)):
            pts.append((x, y, c0))
        pts.append((3, 3, c1))
    elif style == 4:  # 方框宝石
        for x in range(1, 7):
            pts.append((x, 1, c0))
            pts.append((x, 6, c1))
        for y in range(2, 6):
            pts.append((1, y, c0))
            pts.append((6, y, c1))
        pts.append((3, 3, THEME_PINK))
        pts.append((4, 3, THEME_WHITE))
        pts.append((3, 4, THEME_WHITE))
        pts.append((4, 4, THEME_BLUE))
    else:  # 波浪
        for i, (x, y) in enumerate(((1, 3), (2, 2), (3, 1), (4, 2), (5, 3), (6, 4), (2, 5), (4, 5), (5, 5))):
            pts.append((x, y, colors[i % len(colors)]))
    return pts


def make_menu_glyph_image(seed: int, size: int = 14) -> Image.Image:
    img = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    px = img.load()
    for x, y, col in _glyph_pattern(abs(int(seed))):
        if 0 <= x < 8 and 0 <= y < 8:
            r = int(col[1:3], 16)
            g = int(col[3:5], 16)
            b = int(col[5:7], 16)
            px[x, y] = (r, g, b, 255)
    # 细黑描边，贴合像素风
    out = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    base = img.load()
    out_px = out.load()
    for y in range(8):
        for x in range(8):
            if base[x, y][3] == 0:
                continue
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < 8 and 0 <= ny < 8 and base[nx, ny][3] == 0:
                    out_px[nx, ny] = (10, 12, 18, 220)
            out_px[x, y] = base[x, y]
    return out.resize((max(8, size), max(8, size)), Image.NEAREST)


def menu_glyph_photo(label: str, size: int = 14) -> ImageTk.PhotoImage:
    key = (label, int(size))
    cached = _GLYPH_PHOTO_CACHE.get(key)
    if cached is not None:
        return cached
    photo = ImageTk.PhotoImage(make_menu_glyph_image(hash(label) & 0xFFFF, size))
    _GLYPH_PHOTO_CACHE[key] = photo
    return photo


def play_pixel_click_burst(root, anchor_widget, *, bg: str = THEME_BLACK) -> None:
    """在按钮旁弹出短促像素粒子散开动画（蓝粉黑白）。"""
    import tkinter as tk

    try:
        if not anchor_widget or not anchor_widget.winfo_exists():
            return
        ax = int(anchor_widget.winfo_rootx())
        ay = int(anchor_widget.winfo_rooty())
        aw = max(20, int(anchor_widget.winfo_width()))
        ah = max(16, int(anchor_widget.winfo_height()))
    except Exception:
        return

    size = 56
    win = tk.Toplevel(root)
    win.overrideredirect(True)
    try:
        win.attributes("-topmost", True)
    except Exception:
        pass
    win.configure(bg="magenta")
    try:
        win.wm_attributes("-transparentcolor", "magenta")
    except Exception:
        pass
    canvas = tk.Canvas(win, width=size, height=size, bg="magenta", highlightthickness=0, bd=0)
    canvas.pack()
    cx, cy = size // 2, size // 2
    win.geometry(f"+{ax + aw // 2 - cx}+{ay + ah // 2 - cy}")

    particles = []
    for i, col in enumerate(_GLYPH_COLORS * 2):
        ang = (i / 10.0) * 6.28318
        particles.append(
            {
                "x": float(cx),
                "y": float(cy),
                "vx": 1.6 * (1 if i % 2 == 0 else -1) * (0.6 + (i % 3) * 0.35) * (1 if i < 5 else -0.4),
                "vy": -2.2 - (i % 4) * 0.35,
                "col": col,
                "life": 10 + (i % 4),
                "ang": ang,
            }
        )
        particles[-1]["vx"] = 2.4 * __import__("math").cos(ang)
        particles[-1]["vy"] = 2.4 * __import__("math").sin(ang)

    frame = {"n": 0}

    def tick() -> None:
        if not win.winfo_exists():
            return
        canvas.delete("all")
        alive = False
        for p in particles:
            if p["life"] <= 0:
                continue
            alive = True
            px = int(p["x"])
            py = int(p["y"])
            s = 3 if p["life"] > 5 else 2
            canvas.create_rectangle(px, py, px + s, py + s, fill=p["col"], outline="")
            if p["life"] > 6:
                canvas.create_rectangle(px + 1, py - 2, px + 2, py - 1, fill=THEME_WHITE, outline="")
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.18
            p["life"] -= 1
        frame["n"] += 1
        if alive and frame["n"] < 18:
            root.after(28, tick)
        else:
            try:
                win.destroy()
            except Exception:
                pass

    root.after(0, tick)
