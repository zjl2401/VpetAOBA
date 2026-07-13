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


def pack_menu_chrome(parent, *, bg: str) -> tk.Frame:
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
