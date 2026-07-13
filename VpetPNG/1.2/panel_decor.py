"""像素风 UI 装饰：霓虹潮科技条纹 + 蓝粉黑白配色。"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageTk

THEME_BLUE = "#66f0ff"
THEME_PINK = "#ff4db8"
THEME_BLUE_DEEP = "#2a6fd6"
THEME_WHITE = "#f4f8ff"
THEME_BLACK = "#070a12"
THEME_BG_INNER_RGBA = (10, 14, 26, 255)
THEME_PANEL_INNER = "#0e1424"
THEME_ITEM_BG = "#161e32"
THEME_NEON_CYAN = "#39ffe0"
THEME_NEON_MAGENTA = "#ff2f9f"

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
    """在九宫格边框上叠加霓虹像素条纹与四角标牌装饰。"""
    out = img.convert("RGBA").copy()
    draw = ImageDraw.Draw(out)
    w, h = out.size
    pink = (255, 77, 184, 255)
    blue = (102, 240, 255, 255)
    white = (220, 230, 255, 180)
    cyan = (57, 255, 224, 220)

    for x in range(corner, max(corner + 1, w - corner), 3):
        draw.rectangle((x, 1, min(w - 2, x + 1), 3), fill=pink)
        draw.rectangle((x + 1, h - 4, min(w - 2, x + 2), h - 2), fill=blue)
    for y in range(corner, max(corner + 1, h - corner), 4):
        draw.rectangle((1, y, 3, min(h - 2, y + 1)), fill=cyan)
        draw.rectangle((w - 4, y + 1, w - 2, min(h - 2, y + 2)), fill=pink)

    # 霓虹角括号
    arm = max(10, corner // 2)
    for x0, y0, dx, dy in (
        (2, 2, 1, 1),
        (w - 3, 2, -1, 1),
        (2, h - 3, 1, -1),
        (w - 3, h - 3, -1, -1),
    ):
        draw.rectangle((x0, y0, x0 + dx * arm, y0 + dy * 1), fill=white)
        draw.rectangle((x0, y0, x0 + dx * 1, y0 + dy * arm), fill=white)

    ornament = max(18, min(42, corner))
    placements = (
        (0, 4, 4),
        (1, w - ornament - 4, 4),
        (2, 4, h - ornament - 4),
        (3, w - ornament - 4, h - ornament - 4),
    )
    for sign_idx, px, py in placements:
        sign = load_sign_image(signs_dir, sign_idx)
        if sign is None:
            continue
        scaled = sign.resize((ornament, ornament), Image.NEAREST)
        sx = max(0, min(w - ornament, px))
        sy = max(0, min(h - ornament, py))
        out.alpha_composite(scaled, (sx, sy))

    return out


def draw_pixel_divider(canvas, width: int, *, height: int = 6, bg: str = THEME_PANEL_INNER) -> None:
    canvas.delete("all")
    canvas.config(height=height, bg=bg)
    w = max(40, int(width))
    for i in range(0, w, 10):
        canvas.create_rectangle(i, 0, i + 4, height - 2, fill=THEME_PINK, outline="")
        canvas.create_rectangle(i + 4, 1, i + 7, height - 1, fill=THEME_BLUE, outline="")
        canvas.create_rectangle(i + 7, 0, i + 10, height - 2, fill=THEME_NEON_CYAN, outline="")
    canvas.create_rectangle(0, height - 1, w, height, fill=THEME_WHITE, outline="")


def pack_menu_chrome(parent, *, bg: str):
    import tkinter as tk

    # 外层霓虹壳：双色描边 + 角标感
    shell = tk.Frame(parent, bg=THEME_NEON_CYAN, padx=1, pady=1)
    shell.pack()
    mid = tk.Frame(shell, bg=THEME_PINK, padx=1, pady=1)
    mid.pack(fill=tk.BOTH, expand=True)
    tk.Frame(mid, bg=THEME_BLUE, height=2).pack(fill=tk.X)
    # 科技点阵条
    dash = tk.Canvas(mid, height=4, bg=THEME_BLACK, highlightthickness=0, borderwidth=0)
    dash.pack(fill=tk.X)
    for i in range(0, 220, 8):
        col = THEME_PINK if (i // 8) % 2 == 0 else THEME_BLUE
        dash.create_rectangle(i, 1, i + 4, 3, fill=col, outline="")
    inner = tk.Frame(mid, bg=bg, padx=4, pady=4)
    inner.pack(fill=tk.BOTH, expand=True)
    tk.Frame(mid, bg=THEME_BLUE_DEEP, height=2).pack(fill=tk.X)
    return inner


def pack_panel_accent_bar(parent, *, bg: str) -> None:
    import tkinter as tk

    # 多层霓虹顶栏：粉 / 青 / 点阵 / 深层蓝
    tk.Frame(parent, bg=THEME_PINK, height=2).pack(fill=tk.X)
    tk.Frame(parent, bg=THEME_NEON_CYAN, height=1).pack(fill=tk.X)
    strip = tk.Canvas(parent, height=5, bg=THEME_BLACK, highlightthickness=0, borderwidth=0)
    strip.pack(fill=tk.X)
    for i in range(0, 640, 6):
        if (i // 6) % 3 == 0:
            strip.create_rectangle(i, 1, i + 3, 4, fill=THEME_PINK, outline="")
        elif (i // 6) % 3 == 1:
            strip.create_rectangle(i, 0, i + 3, 3, fill=THEME_BLUE, outline="")
        else:
            strip.create_rectangle(i, 2, i + 2, 4, fill=THEME_NEON_CYAN, outline="")
    tk.Frame(parent, bg=THEME_BLUE_DEEP, height=1).pack(fill=tk.X)
    tk.Frame(parent, bg=bg, height=2).pack(fill=tk.X)
