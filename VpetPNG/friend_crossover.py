"""相遇友情素材：Lv 动作图标抠图、selecttalk 帧、红框合成。"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

# selecttalk#.jpg 红框（源图 1840×1840）
SELECTTALK_RED_BOX = (895, 377, 1266, 748)
SELECTTALK_FRAME_MS = 200


def friend_assets_dir() -> Path:
    """优先源码/安装包内带 talk·choices 的目录，避免只拷 py 找不到图。"""
    import os

    here = Path(__file__).resolve().parent
    cands: list[Path] = []
    env = str(os.environ.get("VPET_AOBA_SRC") or "").strip()
    if env:
        cands.append(Path(env) / "assets" / "friend")
    cands.extend(
        (
            here / "assets" / "friend",
            here.parent / "assets" / "friend",
            here.parent / "_internal" / "assets" / "friend",
        )
    )
    for cand in cands:
        try:
            if (cand / "talk").is_dir() or (cand / "choices").is_dir():
                return cand
        except Exception:
            continue
    return here / "assets" / "friend"


def action_icon_path(level: int = 1, *, black: bool = False) -> Path:
    name = f"lv{int(level)}{'black' if black else 'normal'}.jpg"
    return friend_assets_dir() / "action" / name


def selecttalk_frame_path(frame: str) -> Path:
    """frame: '1'|'2'|'3'|'#' """
    key = str(frame or "1").strip()
    if key == "#":
        return friend_assets_dir() / "talk" / "selecttalk#.jpg"
    return friend_assets_dir() / "talk" / f"selecttalk{key}.jpg"


def _is_friend_chroma(r: int, g: int, b: int) -> bool:
    # 素材绿幕约 (157,216,0)
    if g > 170 and b < 50 and 80 < r < 220 and (g - r) > 15 and (g - b) > 100:
        return True
    if g > 200 and r < 100 and b < 80:
        return True
    return False


def chroma_key_rgba(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    px = rgba.load()
    w, h = rgba.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if _is_friend_chroma(r, g, b):
                px[x, y] = (0, 0, 0, 0)
    return rgba


def tight_crop_rgba(img: Image.Image, *, pad: int = 2) -> Image.Image:
    rgba = img.convert("RGBA")
    alpha = rgba.split()[-1]
    bbox = alpha.getbbox()
    if not bbox:
        return rgba
    l, t, r, b = bbox
    l = max(0, l - pad)
    t = max(0, t - pad)
    r = min(rgba.size[0], r + pad)
    b = min(rgba.size[1], b + pad)
    return rgba.crop((l, t, r, b))


def load_action_icon(level: int = 1, *, black: bool = False, size: int = 36) -> Image.Image | None:
    path = action_icon_path(level, black=black)
    if not path.is_file():
        path = action_icon_path(level, black=False)
    if not path.is_file():
        return None
    try:
        raw = Image.open(path)
        keyed = chroma_key_rgba(raw)
        cropped = tight_crop_rgba(keyed)
        side = max(24, int(size))
        # 等比缩入边长，不拉伸压扁
        out = cropped.copy()
        out.thumbnail((side, side), Image.NEAREST)
        return out
    except Exception:
        return None


def load_selecttalk_frame(
    frame: str,
    *,
    display_w: int = 360,
    mirror: bool = False,
    pair_lr: bool = False,
) -> Image.Image | None:
    path = selecttalk_frame_path(frame)
    if not path.is_file():
        return None
    try:
        raw = Image.open(path)
        keyed = chroma_key_rgba(raw)
        if mirror:
            keyed = keyed.transpose(Image.FLIP_LEFT_RIGHT)
        if display_w and keyed.size[0] != display_w:
            h = max(1, int(keyed.size[1] * display_w / keyed.size[0]))
            keyed = keyed.resize((int(display_w), h), Image.NEAREST)
        if pair_lr:
            return make_selecttalk_lr_pair(keyed)
        return keyed
    except Exception:
        return None


def make_selecttalk_lr_pair(img: Image.Image) -> Image.Image:
    """一左一右：右侧整图水平翻转，面对面并排。"""
    left = img.convert("RGBA")
    right = left.transpose(Image.FLIP_LEFT_RIGHT)
    gap = max(4, left.size[0] // 40)
    canvas = Image.new(
        "RGBA",
        (left.size[0] + right.size[0] + gap, max(left.size[1], right.size[1])),
        (0, 0, 0, 0),
    )
    canvas.paste(left, (0, 0), left)
    canvas.paste(right, (left.size[0] + gap, 0), right)
    return canvas


def selecttalk_red_box_scaled(frame_w: int, frame_h: int) -> tuple[int, int, int, int]:
    """把源图红框映射到缩放后的尺寸。"""
    sw, sh = 1840, 1840
    l, t, r, b = SELECTTALK_RED_BOX
    return (
        int(l * frame_w / sw),
        int(t * frame_h / sh),
        int(r * frame_w / sw),
        int(b * frame_h / sh),
    )


def compose_selecttalk_with_icon(
    base_frame: Image.Image,
    icon: Image.Image | None,
    *,
    pair_lr: bool = False,
) -> Image.Image:
    """在 # 帧红框内居中贴上选项像素图；可选左右并排翻转。"""
    out = base_frame.convert("RGBA").copy()
    if icon is not None:
        if not (pair_lr and out.size[0] > out.size[1] * 1.2):
            l, t, r, b = selecttalk_red_box_scaled(out.size[0], out.size[1])
            box_w = max(8, r - l)
            box_h = max(8, b - t)
            ic = icon.convert("RGBA")
            scale = min(box_w / max(1, ic.size[0]), box_h / max(1, ic.size[1]))
            nw = max(1, int(ic.size[0] * scale))
            nh = max(1, int(ic.size[1] * scale))
            ic = ic.resize((nw, nh), Image.NEAREST)
            x = l + (box_w - nw) // 2
            y = t + (box_h - nh) // 2
            out.paste(ic, (x, y), ic)
    if pair_lr:
        return make_selecttalk_lr_pair(out)
    return out


def compose_selecttalk_with_label(
    base_frame: Image.Image,
    label: str,
    *,
    pair_lr: bool = False,
) -> Image.Image:
    """无选项图时：在红框内绘制选项文字。"""
    from PIL import ImageDraw as PilImageDraw
    from PIL import ImageFont

    out = base_frame.convert("RGBA").copy()
    text = str(label or "?").strip() or "?"
    if not (pair_lr and out.size[0] > out.size[1] * 1.2):
        l, t, r, b = selecttalk_red_box_scaled(out.size[0], out.size[1])
        box_w = max(8, r - l)
        box_h = max(8, b - t)
        draw = PilImageDraw.Draw(out)
        # 浅底
        draw.rectangle([l + 2, t + 2, r - 2, b - 2], fill=(255, 248, 230, 230))
        font = None
        font_paths = (
            Path(__file__).resolve().parent / "assets" / "fonts" / "fusion-pixel-12px-proportional-zh_hans.ttf",
            Path(__file__).resolve().parent / "_internal" / "assets" / "fonts" / "fusion-pixel-12px-proportional-zh_hans.ttf",
        )
        for fp in font_paths:
            try:
                if fp.is_file():
                    font = ImageFont.truetype(str(fp), max(14, min(28, box_w // max(2, len(text)))))
                    break
            except Exception:
                continue
        if font is None:
            for name in ("msyh.ttc", "msyhbd.ttc", "simhei.ttf", "simsun.ttc", "arial.ttf"):
                try:
                    font = ImageFont.truetype(name, max(14, min(28, box_w // max(2, len(text)))))
                    break
                except Exception:
                    continue
        if font is None:
            font = ImageFont.load_default()
        # 居中（粗略）
        try:
            bbox = draw.textbbox((0, 0), text[:8], font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except Exception:
            tw, th = box_w // 2, box_h // 3
        tx = l + max(4, (box_w - tw) // 2)
        ty = t + max(4, (box_h - th) // 2)
        draw.text((tx, ty), text[:8], fill=(60, 40, 30, 255), font=font)
    if pair_lr:
        return make_selecttalk_lr_pair(out)
    return out


def make_pixel_choice_icon(kind: str, size: int = 48) -> Image.Image:
    """内置选项像素图（食物 / 情绪）。"""
    from PIL import ImageDraw as PilImageDraw

    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = PilImageDraw.Draw(img)
    k = str(kind or "")
    if k in ("ramen", "food_ramen"):
        d.ellipse([2, 5, 13, 14], fill="#e8c070", outline="#8a6030")
        d.rectangle([4, 3, 5, 8], fill="#f4f4f4")
        d.rectangle([10, 3, 11, 8], fill="#f4f4f4")
        d.ellipse([6, 7, 9, 10], fill="#d05040")
    elif k in ("bento", "food_bento", "onigiri", "food_onigiri"):
        d.rectangle([2, 4, 13, 13], fill="#f0e0c0", outline="#806040")
        d.rectangle([4, 6, 7, 9], fill="#e06060")
        d.rectangle([9, 6, 11, 11], fill="#70b070")
    elif k in ("cake", "food_cake"):
        d.rectangle([3, 7, 12, 13], fill="#f0c0d0", outline="#a06080")
        d.polygon([(7, 2), (9, 2), (8, 7)], fill="#ff6688")
        d.rectangle([7, 6, 8, 7], fill="#886644")
    elif k in ("cold", "choice_cold"):
        d.rectangle([4, 3, 11, 13], fill="#88b8d8", outline="#406080")
        d.point((6, 6), fill="#203040")
        d.point((9, 6), fill="#203040")
    elif k in ("peace", "choice_peace"):
        d.ellipse([3, 4, 12, 13], fill="#ff88aa", outline="#a04060")
        d.rectangle([7, 2, 8, 5], fill="#ff88aa")
    elif k in ("breakup", "choice_break"):
        d.line([(4, 4), (11, 12)], fill="#cc3344", width=2)
        d.line([(11, 4), (4, 12)], fill="#cc3344", width=2)
    elif k in ("listen", "choice_listen"):
        d.ellipse([3, 4, 12, 13], fill="#88ccff", outline="#4060a0")
        d.arc([5, 6, 10, 11], 200, 340, fill="#204080")
    elif k in ("joke", "choice_joke"):
        d.ellipse([3, 4, 12, 13], fill="#ffcc66", outline="#a08030")
        d.point((6, 7), fill="#403010")
        d.point((9, 7), fill="#403010")
        d.arc([6, 8, 10, 11], 20, 160, fill="#403010")
    else:
        d.ellipse([3, 4, 12, 13], fill="#c8d8f0", outline="#506080")
        d.rectangle([6, 7, 9, 10], fill="#506080")
    return img.resize((max(16, int(size)), max(16, int(size))), Image.NEAREST)
