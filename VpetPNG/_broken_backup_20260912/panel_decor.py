"""像素风 UI 装饰：Vpetsign 素材 + 蓝粉黑白配色。"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageTk

THEME_BLUE = "#66ccff"
THEME_PINK = "#ff88cc"
THEME_BLUE_DEEP = "#2a6bb8"
THEME_ORANGE = "#e8a060"
THEME_YELLOW = "#e8d060"
THEME_GREEN = "#58b888"
THEME_WHITE = "#f4faff"
THEME_BLACK = "#0a1f3d"
THEME_BG_INNER_RGBA = (200, 228, 255, 255)
THEME_PANEL_INNER = "#a8d4f8"
THEME_ITEM_BG = "#c8e4ff"
THEME_RAINBOW: tuple[str, ...] = (
    THEME_PINK,
    THEME_BLUE,
    THEME_GREEN,
    THEME_YELLOW,
    THEME_ORANGE,
    THEME_BLUE_DEEP,
)
# 上浅下深
THEME_BG_TOP = "#e8f4ff"
THEME_BG_MID = "#c8e6ff"
THEME_BG_BOTTOM = "#9ec8e8"
# 蓝系面板底色（用于决定是否上浅蓝渐变）
BLUE_FAMILY_BGS = frozenset(
    {
        THEME_BG_TOP,
        THEME_BG_MID,
        THEME_BG_BOTTOM,
        THEME_PANEL_INNER,
        THEME_ITEM_BG,
        "#c8e4ff",
        "#a8d4f8",
        "#e8f4ff",
        "#d8ecff",
        "#f4faff",
        "#b8dcff",
        "#7eb8f0",
    }
)

_VPETSIGN_DESKTOP = Path.home() / "Desktop" / "Vpetsign"
_SIGN_IMG_CACHE: dict[tuple[str, int, int], Image.Image] = {}
_SIGN_PHOTO_CACHE: dict[tuple[str, int, int], ImageTk.PhotoImage] = {}
_SIGN_FILE_LIST_CACHE: dict[str, list[Path]] = {}
_TRIMMED_SIGN_CACHE: dict[str, Image.Image] = {}


def resolve_signs_dir(bundle_dir: Path) -> Path:
    return bundle_dir / "assets" / "signs"


def _list_sign_files(signs_dir: Path) -> list[Path]:
    key = str(signs_dir.resolve()) if signs_dir.exists() else str(signs_dir)
    cached = _SIGN_FILE_LIST_CACHE.get(key)
    if cached is not None:
        return cached
    files: list[Path] = []
    if signs_dir.is_dir():
        pngs = sorted(signs_dir.glob("*.png"))
        if pngs:
            files = pngs
    if not files and _VPETSIGN_DESKTOP.is_dir():
        files = sorted(_VPETSIGN_DESKTOP.glob("*.jpg"))
    _SIGN_FILE_LIST_CACHE[key] = files
    return files


def load_sign_image(signs_dir: Path, index: int) -> Image.Image | None:
    files = _list_sign_files(signs_dir)
    if not files:
        return None
    idx = max(0, min(len(files) - 1, int(index)))
    path = files[idx]
    path_key = str(path.resolve()) if path.exists() else str(path)
    cached = _TRIMMED_SIGN_CACHE.get(path_key)
    if cached is not None:
        return cached
    try:
        img = Image.open(path).convert("RGBA")
        img = _trim_sign_alpha(img)
        _TRIMMED_SIGN_CACHE[path_key] = img
        return img
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


def _hex_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _lerp_hex(a: str, b: str, t: float) -> str:
    t = max(0.0, min(1.0, float(t)))
    ar, ag, ab = _hex_rgb(a)
    br, bg, bb = _hex_rgb(b)
    r = int(ar + (br - ar) * t)
    g = int(ag + (bg - ag) * t)
    bch = int(ab + (bb - ab) * t)
    return f"#{r:02x}{g:02x}{bch:02x}"


def is_blue_family_bg(bg: str | None) -> bool:
    if not bg:
        return True
    key = str(bg).strip().lower()
    if key in {x.lower() for x in BLUE_FAMILY_BGS}:
        return True
    # 粗判：偏蓝且不太紫/粉/绿/橙
    if not key.startswith("#") or len(key) != 7:
        return False
    try:
        r = int(key[1:3], 16)
        g = int(key[3:5], 16)
        b = int(key[5:7], 16)
    except Exception:
        return False
    return b >= r + 20 and b >= g and b >= 160 and r <= 240


def scrollbar_colors_for_bg(bg: str | None) -> dict[str, str]:
    """滚动条随窗口背景略深/略浅。"""
    base = str(bg or THEME_BG_MID).strip() or THEME_BG_MID
    trough = _lerp_hex(base, "#ffffff", 0.12)
    thumb = _lerp_hex(base, "#163a68", 0.22)
    active = _lerp_hex(base, "#163a68", 0.32)
    return {"bg": thumb, "troughcolor": trough, "activebackground": active}


# 蓝渐变窗上「文字底」不透明度：0=完全透明（垫色取局部渐变色，视觉上无色块）
GRAD_TEXT_PLATE_ALPHA = 0.0

_TEXT_PLATE_BGS = frozenset(
    x.lower()
    for x in (
        THEME_BG_TOP,
        THEME_BG_MID,
        THEME_BG_BOTTOM,
        THEME_PANEL_INNER,
        THEME_ITEM_BG,
        THEME_WHITE,
        "#ffffff",
        "#f4faff",
        "#e8f4ff",
        "#d8ecff",
        "#c8e4ff",
        "#c8e6ff",
        "#b8dcff",
        "#a8d4f8",
        "#9ec8e8",
        "#7eb8f0",
        "systembuttonface",
    )
)

_KEEP_PLATE_BGS = frozenset(
    x.lower()
    for x in (
        THEME_PINK,
        THEME_BLUE,
        THEME_BLUE_DEEP,
        THEME_BLACK,
        "#ff88cc",
        "#66ccff",
        "#2a6bb8",
        "#163a68",
        "magenta",
        "#ff00ff",
    )
)

_SKIP_PLATE_CLASSES = frozenset(
    {
        "Button",
        "TButton",
        "Entry",
        "TEntry",
        "Text",
        "Listbox",
        "Scrollbar",
        "TScrollbar",
        "Spinbox",
        "Scale",
        "TScale",
        "Menubutton",
        "TMenubutton",
    }
)


def blue_gradient_color_at(t: float) -> str:
    """与 paint_blue_gradient 同一套上浅下淡蓝插值。"""
    t = max(0.0, min(1.0, float(t)))
    if t < 0.55:
        return _lerp_hex(THEME_BG_TOP, THEME_BG_MID, t / 0.55)
    return _lerp_hex(THEME_BG_MID, THEME_BG_BOTTOM, (t - 0.55) / 0.45)


def is_text_plate_bg(bg: str | None) -> bool:
    if not bg:
        return False
    key = str(bg).strip().lower()
    if key in _KEEP_PLATE_BGS:
        return False
    if key in _TEXT_PLATE_BGS:
        return True
    return is_blue_family_bg(key)


def plate_color_over_gradient(plate: str, under: str, alpha: float) -> str:
    """alpha=0 → 完全透明（=under）；alpha=1 → 实色 plate。"""
    a = max(0.0, min(1.0, float(alpha)))
    if a <= 0.001:
        return under
    if a >= 0.999:
        return plate
    return _lerp_hex(under, plate, a)


def _hex_luma(hex_color: str) -> float:
    try:
        r, g, b = _hex_rgb(hex_color)
    except Exception:
        return 128.0
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def is_light_panel_bg(bg: str | None) -> bool:
    if not bg:
        return False
    key = str(bg).strip().lower()
    if key in _KEEP_PLATE_BGS or key in {"magenta", "#ff00ff"}:
        return False
    if not key.startswith("#") or len(key) != 7:
        return key in _TEXT_PLATE_BGS
    return _hex_luma(key) >= 155


def deepen_fg_on_light_bg(fg: str, bg: str) -> str:
    """浅色底上过浅的字色加深（保留色相：粉→深玫、蓝→深蓝）。"""
    try:
        fg_s = str(fg or "").strip()
        bg_s = str(bg or "").strip()
        if not fg_s.startswith("#") or len(fg_s) != 7:
            return fg_s
        if not is_light_panel_bg(bg_s):
            return fg_s
        luma = _hex_luma(fg_s)
        # 已经够深的主文字不改
        if luma < 72:
            return fg_s
        r, g, b = _hex_rgb(fg_s)
        if r >= b + 28 and r >= g + 8:
            target = "#4a1838"  # 深玫
        elif b >= r + 18:
            target = "#0c2e58"  # 深蓝
        elif abs(r - g) < 18 and abs(g - b) < 18:
            target = "#1c2c40"  # 深灰蓝（提示字）
        else:
            target = "#142838"
        # 越浅压得越深（比旧版整体再深一档）
        t = min(0.90, max(0.52, (luma - 55) / 130.0))
        return _lerp_hex(fg_s, target, t)
    except Exception:
        return fg


def _deepen_widget_fg(w) -> None:
    if getattr(w, "_vpet_fg_deepened", False):
        return
    try:
        fg = str(w.cget("fg") or "").strip()
        bg = str(w.cget("bg") or "").strip()
    except Exception:
        return
    if not fg.startswith("#"):
        return
    new_fg = deepen_fg_on_light_bg(fg, bg)
    if new_fg == fg:
        return
    try:
        w.configure(fg=new_fg)
        setattr(w, "_vpet_fg_deepened", True)
    except Exception:
        pass
    for opt in ("activeforeground", "disabledforeground"):
        try:
            cur = str(w.cget(opt) or "").strip()
            if cur.startswith("#"):
                w.configure(**{opt: deepen_fg_on_light_bg(cur, bg)})
        except Exception:
            pass


def _nearest_grad_host(w, fallback):
    """找最近的渐变宿主（可滚动内容区优先），用于按局部 Y 取样。"""
    cur = w
    for _ in range(48):
        if cur is None:
            break
        try:
            if getattr(cur, "_vpet_content_grad", None) is not None:
                return cur
            if getattr(cur, "_vpet_blue_grad_host", False):
                return cur
        except Exception:
            pass
        try:
            cur = cur.master
        except Exception:
            break
    return fallback


def apply_transparent_text_plates(root, *, alpha: float | None = None) -> None:
    """蓝渐变窗：文字/行块底跟局部渐变色对齐（alpha=0 视觉全透明）；按键保留。"""
    if root is None:
        return
    try:
        if not root.winfo_exists():
            return
    except Exception:
        return
    a = GRAD_TEXT_PLATE_ALPHA if alpha is None else float(alpha)
    clear_plates = bool(
        getattr(root, "_vpet_blue_grad_host", False) or getattr(root, "_vpet_content_grad", None) is not None
    )

    def _match_plate(w, cls: str) -> None:
        if not clear_plates:
            return
        try:
            bg = str(w.cget("bg") or "").strip()
        except Exception:
            return
        bg_l = bg.lower()
        if bg_l in _KEEP_PLATE_BGS:
            return
        should = cls in ("Label", "Message", "Checkbutton", "Radiobutton", "Frame", "Labelframe") or is_text_plate_bg(
            bg
        )
        # Scale 槽轨保留深色，仅把滑条底板贴齐渐变，避免整条色块
        if cls in ("Scale", "TScale"):
            should = True
        if not should:
            return
        try:
            ref = _nearest_grad_host(w, root)
            host_h = max(int(ref.winfo_height()), 1)
            host_top = int(ref.winfo_rooty())
            mid_y = int(w.winfo_rooty()) - host_top + max(int(w.winfo_height()), 1) // 2
            t = max(0.0, min(1.0, mid_y / float(host_h)))
            under = blue_gradient_color_at(t)
            plate = bg if bg.startswith("#") else under
            new_bg = plate_color_over_gradient(plate, under, a)
            w.configure(bg=new_bg)
            for opt in ("highlightbackground", "activebackground", "selectcolor"):
                try:
                    w.configure(**{opt: new_bg})
                except Exception:
                    pass
        except Exception:
            pass

    def _walk(w) -> None:
        try:
            if not w.winfo_exists():
                return
        except Exception:
            return
        if getattr(w, "_vpet_keep_plate", False):
            for c in w.winfo_children():
                _walk(c)
            return
        if getattr(w, "_vpet_grad_canvas", False):
            return
        try:
            cls = str(w.winfo_class() or "")
        except Exception:
            cls = ""
        if cls in ("Button", "TButton"):
            _deepen_widget_fg(w)
            return
        if cls in _SKIP_PLATE_CLASSES and cls not in ("Scale", "TScale"):
            return
        if cls == "Canvas":
            try:
                if w.find_withtag("bggrad") or w.find_withtag("motif") or getattr(w, "_vpet_grad_canvas", False):
                    for c in w.winfo_children():
                        _walk(c)
                    return
            except Exception:
                pass
        _match_plate(w, cls)
        if cls in ("Label", "Message", "Checkbutton", "Radiobutton"):
            _deepen_widget_fg(w)
        try:
            children = list(w.winfo_children())
        except Exception:
            children = []
        for c in children:
            _walk(c)

    _walk(root)


def apply_light_panel_text_contrast(root) -> None:
    """非渐变浅色窗：只加深过浅字色。"""
    if root is None:
        return
    try:
        if not root.winfo_exists():
            return
    except Exception:
        return

    def _walk(w) -> None:
        try:
            if not w.winfo_exists():
                return
        except Exception:
            return
        try:
            cls = str(w.winfo_class() or "")
        except Exception:
            cls = ""
        if cls in ("Label", "Message", "Checkbutton", "Radiobutton", "Button", "TButton"):
            _deepen_widget_fg(w)
        try:
            children = list(w.winfo_children())
        except Exception:
            children = []
        for c in children:
            _walk(c)

    _walk(root)


def schedule_transparent_text_plates(root, *, alpha: float | None = None) -> None:
    """内容填完后多次补刷文字底与对比度（Configure 防抖）。"""
    if root is None:
        return
    a = GRAD_TEXT_PLATE_ALPHA if alpha is None else float(alpha)
    try:
        setattr(root, "_vpet_text_plate_alpha", a)
    except Exception:
        pass
    job_key = "_vpet_text_plate_job"

    def _run(_event=None) -> None:
        try:
            setattr(root, job_key, None)
        except Exception:
            pass
        apply_transparent_text_plates(root, alpha=a)
        apply_light_panel_text_contrast(root)

    def _debounced(_event=None) -> None:
        try:
            old = getattr(root, job_key, None)
            if old is not None:
                root.after_cancel(old)
        except Exception:
            pass
        try:
            setattr(root, job_key, root.after(40, _run))
        except Exception:
            _run()

    try:
        if not getattr(root, "_vpet_text_plate_bound", False):
            root.bind("<Configure>", _debounced, add="+")
            setattr(root, "_vpet_text_plate_bound", True)
    except Exception:
        pass
    try:
        root.after_idle(_run)
        root.after(80, _run)
        root.after(240, _run)
        root.after(600, _run)
    except Exception:
        _run()


def schedule_light_panel_text_contrast(root) -> None:
    """浅色主题页：补刷字色对比。"""
    if root is None:
        return
    job_key = "_vpet_text_contrast_job"

    def _run(_event=None) -> None:
        try:
            setattr(root, job_key, None)
        except Exception:
            pass
        apply_light_panel_text_contrast(root)

    def _debounced(_event=None) -> None:
        try:
            old = getattr(root, job_key, None)
            if old is not None:
                root.after_cancel(old)
        except Exception:
            pass
        try:
            setattr(root, job_key, root.after(40, _run))
        except Exception:
            _run()

    try:
        if not getattr(root, "_vpet_text_contrast_bound", False):
            root.bind("<Configure>", _debounced, add="+")
            setattr(root, "_vpet_text_contrast_bound", True)
    except Exception:
        pass
    try:
        root.after_idle(_run)
        root.after(80, _run)
        root.after(240, _run)
    except Exception:
        _run()


def paint_blue_gradient(
    canvas,
    *,
    tag: str = "bggrad",
    steps: int = 48,
    width: int | None = None,
    height: int | None = None,
) -> None:
    """上浅下淡蓝纵向渐变（底端保持浅蓝，不再压成深蓝）。"""
    try:
        canvas.delete(tag)
    except Exception:
        pass
    try:
        w = max(int(width if width is not None else canvas.winfo_width()), 1)
        h = max(int(height if height is not None else canvas.winfo_height()), 1)
    except Exception:
        return
    if w <= 1 or h <= 1:
        return
    n = max(16, int(steps))
    for i in range(n):
        y0 = i * h // n
        y1 = (i + 1) * h // n
        t = i / max(1, n - 1)
        col = blue_gradient_color_at(t)
        canvas.create_rectangle(0, y0, w, y1 + 1, fill=col, outline="", tags=tag)
    try:
        canvas.tag_lower(tag)
    except Exception:
        pass


def attach_blue_gradient_bg(host, *, bg: str | None = None) -> None:
    """给 Frame 垫一层渐变 Canvas（置于底层）。"""
    import tkinter as tk

    if getattr(host, "_vpet_blue_grad", None) is not None:
        return
    # 兜底用底部深蓝，避免未绘制时露浅色
    cv = tk.Canvas(host, highlightthickness=0, bd=0, bg=bg or THEME_BG_BOTTOM)
    cv.place(x=0, y=0, relwidth=1, relheight=1)
    try:
        setattr(cv, "_vpet_grad_canvas", True)
        cv.lower()
    except Exception:
        pass

    def _repaint(_event=None) -> None:
        paint_blue_gradient(cv)
        try:
            cv.lower()
        except Exception:
            pass

    cv.bind("<Configure>", _repaint)
    try:
        setattr(host, "_vpet_blue_grad", cv)
    except Exception:
        pass
    host.after_idle(_repaint)


def attach_content_gradient(host, *, fallback: str | None = None) -> None:
    """可滚动内容区：随内容高度拉长的上浅下深渐变（place 垫底，不挡点击）。"""
    import tkinter as tk

    if getattr(host, "_vpet_content_grad", None) is not None:
        return
    try:
        host.configure(bg=fallback or THEME_BG_BOTTOM)
    except Exception:
        pass
    cv = tk.Canvas(host, highlightthickness=0, bd=0, bg=fallback or THEME_BG_BOTTOM)
    cv.place(x=0, y=0, relwidth=1, relheight=1)
    try:
        setattr(cv, "_vpet_grad_canvas", True)
        cv.lower()
    except Exception:
        pass

    def _repaint(_event=None) -> None:
        try:
            w = max(int(host.winfo_width()), int(cv.winfo_width()), 1)
            h = max(int(host.winfo_height()), int(cv.winfo_height()), 1)
        except Exception:
            return
        paint_blue_gradient(cv, width=w, height=h, steps=max(48, h // 8))
        try:
            cv.lower()
        except Exception:
            pass

    host.bind("<Configure>", _repaint, add="+")
    cv.bind("<Configure>", _repaint, add="+")
    try:
        setattr(host, "_vpet_content_grad", cv)
    except Exception:
        pass
    host.after_idle(_repaint)


def draw_pixel_divider(canvas, width: int, *, height: int = 5, bg: str = THEME_PANEL_INNER) -> None:
    canvas.delete("all")
    canvas.config(height=height, bg=bg)
    w = max(40, int(width))
    for i in range(0, w, 8):
        canvas.create_rectangle(i, 0, i + 4, height - 1, fill=THEME_PINK, outline="")
        canvas.create_rectangle(i + 4, 1, i + 8, height, fill=THEME_BLUE, outline="")
    canvas.create_rectangle(0, height - 1, w, height, fill=THEME_WHITE, outline="")


def draw_rainbow_accent(canvas, width: int, *, height: int = 4, y: int = 0) -> None:
    """在 Canvas 上画色带（苍叶用蓝粉系彩虹常量）。"""
    w = max(1, int(width))
    h = max(2, int(height))
    n = len(THEME_RAINBOW)
    step = max(1, w // n)
    for i, col in enumerate(THEME_RAINBOW):
        x0 = i * step
        x1 = w if i == n - 1 else (i + 1) * step
        canvas.create_rectangle(x0, y, x1, y + h, fill=col, outline="")


def _default_signs_dir() -> Path:
    if _VPETSIGN_DESKTOP.is_dir():
        return _VPETSIGN_DESKTOP
    return Path(__file__).resolve().parent / "assets" / "signs"


def _pack_sign_strip(parent, *, bg: str, signs_dir: Path | None, size: int = 16) -> None:
    """顶栏：蓝粉条 + 中间一枚 Vpetsign（与伊得结构对齐，配色保持苍叶）。"""
    import tkinter as tk

    root_dir = signs_dir if signs_dir is not None else _default_signs_dir()
    bar = tk.Frame(parent, bg=bg)
    bar.pack(fill=tk.X)
    mid = sign_photo(root_dir, 3, size)
    stripe = tk.Frame(bar, bg=bg)
    stripe.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    row = tk.Frame(stripe, bg=bg, height=7)
    row.pack(fill=tk.X)
    row.pack_propagate(False)
    for col in (THEME_PINK, THEME_BLUE, THEME_BLUE_DEEP, THEME_BLUE, THEME_PINK, THEME_WHITE):
        tk.Frame(row, bg=col).pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    tk.Frame(stripe, bg=THEME_WHITE, height=1).pack(fill=tk.X)
    if mid is not None:
        heart = tk.Label(stripe, image=mid, bg=bg, bd=0)
        heart.image = mid  # type: ignore[attr-defined]
        heart.place(relx=0.5, rely=0.5, anchor="center")
        bar._vpet_sign_mid = mid  # type: ignore[attr-defined]


def pack_panel_shell(
    parent,
    *,
    bg: str,
    signs_dir: Path | None = None,
    padx: int = 10,
    pady: int = 8,
    use_blue_gradient: bool | None = None,
):
    """面板壳：蓝粉描边；蓝系底默认浅蓝渐变，文字块透明叠色（按键保留）。"""
    import tkinter as tk

    solid = str(bg or THEME_PANEL_INNER)
    do_grad = is_blue_family_bg(solid) if use_blue_gradient is None else bool(use_blue_gradient)
    wrap = tk.Frame(parent, bg=THEME_BLUE, padx=1, pady=1)
    wrap.pack(fill=tk.BOTH, expand=True)
    tk.Frame(wrap, bg=THEME_PINK, height=2).pack(fill=tk.X)
    body_bg = THEME_BG_BOTTOM if do_grad else solid
    body = tk.Frame(wrap, bg=body_bg)
    body.pack(fill=tk.BOTH, expand=True)
    if do_grad:
        attach_blue_gradient_bg(body, bg=THEME_BG_BOTTOM)
    tk.Frame(wrap, bg=THEME_BLUE_DEEP, height=1).pack(fill=tk.X)
    inner = tk.Frame(body, bg=body_bg, padx=padx, pady=pady)
    if do_grad:
        attach_content_gradient(inner, fallback=THEME_BG_BOTTOM)
        try:
            setattr(inner, "_vpet_blue_grad_host", True)
        except Exception:
            pass
        schedule_transparent_text_plates(inner)
    elif is_light_panel_bg(solid):
        schedule_light_panel_text_contrast(inner)
    inner.pack(fill=tk.BOTH, expand=True)
    pack_panel_accent_bar(inner, bg=body_bg, signs_dir=signs_dir)
    return inner


def pack_panel_accent_bar(parent, *, bg: str, signs_dir: Path | None = None) -> None:
    """面板顶栏：蓝粉条 + 一枚 Vpetsign。"""
    import tkinter as tk

    _pack_sign_strip(parent, bg=bg, signs_dir=signs_dir, size=14)
    tk.Frame(parent, bg=bg, height=2).pack(fill=tk.X)


def pack_menu_chrome(parent, *, bg: str, signs_dir: Path | None = None, lite: bool = False, use_blue_gradient: bool | None = None):
    """菜单外框：蓝粉描边；非 lite 时顶栏带 Vpetsign。"""
    import tkinter as tk

    solid = str(bg or THEME_PANEL_INNER)
    do_grad = is_blue_family_bg(solid) if use_blue_gradient is None else bool(use_blue_gradient)
    shell = tk.Frame(parent, bg=THEME_BLUE, padx=1, pady=1)
    shell.pack()
    tk.Frame(shell, bg=THEME_PINK, height=2).pack(fill=tk.X)
    if not lite:
        tk.Frame(shell, bg=THEME_BLUE, height=1).pack(fill=tk.X)
    body_bg = THEME_BG_BOTTOM if do_grad else solid
    body = tk.Frame(shell, bg=body_bg)
    body.pack(fill=tk.BOTH, expand=True)
    if not lite:
        _pack_sign_strip(body, bg=body_bg, signs_dir=signs_dir, size=12)
    elif do_grad:
        tk.Frame(body, bg=THEME_PINK, height=2).pack(fill=tk.X)
        tk.Frame(body, bg=THEME_BLUE, height=1).pack(fill=tk.X)
    inner = tk.Frame(body, bg=body_bg, padx=3, pady=3)
    inner.pack(fill=tk.BOTH, expand=True)
    if do_grad:
        attach_blue_gradient_bg(inner, bg=THEME_BG_BOTTOM)
        try:
            setattr(inner, "_vpet_blue_grad_host", True)
        except Exception:
            pass
        schedule_transparent_text_plates(inner)
    elif is_light_panel_bg(solid):
        schedule_light_panel_text_contrast(inner)
    tk.Frame(shell, bg=THEME_BLUE_DEEP, height=1).pack(fill=tk.X)
    return inner


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


# 相遇热区：像素图案（非汉字）—— 苍叶浅蓝系
_CROSSOVER_HOTSPOT_CACHE: dict[tuple[str, int], ImageTk.PhotoImage] = {}
_FRIEND_ACTION_ICON_CACHE: dict[str, Image.Image] = {}


def _friend_assets_root() -> Path:
    return Path(__file__).resolve().parent / "assets"


def _load_friend_lv_action_icon(level: int = 1, *, prefer_black: bool = False) -> Image.Image | None:
    """友情动作等级图标（act_ready 具体动作用）；顶栏「动」入口不用此图。"""
    key = f"lv{int(level)}_{'black' if prefer_black else 'normal'}"
    hit = _FRIEND_ACTION_ICON_CACHE.get(key)
    if hit is not None:
        return hit
    # 优先绿幕 JPG（friend_crossover 抠图）
    try:
        import friend_crossover as _fc

        img = _fc.load_action_icon(int(level), black=bool(prefer_black), size=64)
        if img is not None:
            _FRIEND_ACTION_ICON_CACHE[key] = img
            return img
    except Exception:
        pass
    root = _friend_assets_root()
    names = (
        [f"lv{level}black_icon.png", f"lv{level}black.png", f"lv{level}normal_icon.png", f"lv{level}normal.png"]
        if prefer_black
        else [f"lv{level}normal_icon.png", f"lv{level}normal.png", f"lv{level}black_icon.png", f"lv{level}black.png"]
    )
    for name in names:
        for sub in ("friend/action", "cutout/friend/action"):
            path = root / sub / name
            if not path.is_file():
                continue
            try:
                img = Image.open(path).convert("RGBA")
                _FRIEND_ACTION_ICON_CACHE[key] = img
                return img
            except Exception:
                continue
    return None


def make_crossover_hotspot_image(kind: str, size: int = 36) -> Image.Image:
    """遇/话/动：16×16 像素图案再放大。

    顶栏「动」简约箭头；act_ready 的 do:动作 用 friend/action/lvN 图标。
    """
    raw = str(kind or "meet").strip().lower()
    side = max(24, int(size))

    # 具体解锁动作：LV 图标（目前 lv1=并肩）
    if raw.startswith("do:") or raw.startswith("lv"):
        lv = 1
        if "lv2" in raw:
            lv = 2
        elif "lv3" in raw:
            lv = 3
        icon = _load_friend_lv_action_icon(lv, prefer_black=False)
        if icon is not None:
            canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
            # 等比装入，不二次压扁；尽量用满热区
            fitted = icon.copy()
            max_side = max(side - 2, 24)
            if max(fitted.size) > max_side:
                fitted.thumbnail((max_side, max_side), Image.NEAREST)
            ox = (side - fitted.size[0]) // 2
            oy = (side - fitted.size[1]) // 2
            canvas.paste(fitted, (ox, oy), fitted)
            return canvas
        # 缺图时回落简约「动」
        raw = "act"

    m = raw
    if m.startswith("do:"):
        m = "act"
    if m not in ("meet", "talk", "act"):
        m = "meet"
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 蓝系：亮粉描边 / 玫粉填充 / 浅青点缀「动」箭头 / 深紫身
    ink, mid, deep, body, ring = "#f4faff", "#88ccff", "#66ccff", "#2a6bb8", "#9ed0ff"
    if m == "meet":
        d.ellipse([1, 4, 7, 11], outline=ink, fill=body)
        d.ellipse([8, 4, 14, 11], outline=ink, fill=body)
        d.rectangle([6, 7, 9, 8], fill=mid)
        d.point((4, 7), fill=ink)
        d.point((11, 7), fill=ink)
    elif m == "talk":
        d.rounded_rectangle([2, 2, 13, 10], radius=3, outline=ink, fill=body)
        d.polygon([(5, 10), (3, 14), (8, 10)], fill=body, outline=ink)
        for x in (5, 8, 11):
            d.rectangle([x, 5, x + 1, 6], fill=ink)
    else:
        # 动入口：简约单箭头（与具体 LV 动作图区分）
        d.polygon([(3, 8), (10, 3), (10, 6), (13, 6), (13, 10), (10, 10), (10, 13)], fill=deep, outline=ink)
    d.rectangle([0, 0, 15, 15], outline=ring)
    return img.resize((side, side), Image.NEAREST)


def crossover_hotspot_photo(kind: str, size: int = 36) -> ImageTk.PhotoImage:
    m = str(kind or "meet").strip().lower()
    # 保留 do: / lv 原样做缓存键，勿折叠成 act
    if not (m.startswith("do:") or m.startswith("lv") or m in ("meet", "talk", "act")):
        m = "meet"
    key = (m, int(size))
    cached = _CROSSOVER_HOTSPOT_CACHE.get(key)
    if cached is not None:
        return cached
    photo = ImageTk.PhotoImage(make_crossover_hotspot_image(m, key[1]))
    _CROSSOVER_HOTSPOT_CACHE[key] = photo
    return photo


def play_pixel_click_burst(root, anchor_widget) -> None:
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
        ang = (i / 10.0) * math.tau
        particles.append(
            {
                "x": float(cx),
                "y": float(cy),
                "vx": 2.4 * math.cos(ang),
                "vy": 2.4 * math.sin(ang),
                "col": col,
                "life": 10 + (i % 4),
            }
        )

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
