"""桌宠装扮：像素装饰叠层（素材库 / 自创画 / 礼物画 / 公开预设）。"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageDraw

OUTFIT_MAX = 8
# 相对宠框中心：nx/ny ∈ [-0.55, 0.55]；scale 为占宠边长比例
OUTFIT_SCALE_MIN = 0.12
OUTFIT_SCALE_MAX = 0.55
OUTFIT_DEFAULT_NX = 0.0
OUTFIT_DEFAULT_NY = -0.38
OUTFIT_DEFAULT_SCALE = 0.28

KIND_MATERIAL = "material"
KIND_USER_PAINT = "user_paint"
KIND_GIFT_ART = "gift_art"
KIND_BUILTIN = "builtin"

# 公开预设：12×12 色板下标（0=透明），简易像素图案
_BUILTIN_PALETTE: tuple[str | None, ...] = (
    None,
    "#ff6688",
    "#ffcc66",
    "#66ccff",
    "#88eeaa",
    "#ffffff",
    "#cc88ff",
    "#442233",
)


def _empty_cells() -> list[int]:
    return [0] * 144


def _paint_cells(draw_fn) -> list[int]:
    cells = _empty_cells()

    def put(x: int, y: int, c: int) -> None:
        if 0 <= x < 12 and 0 <= y < 12:
            cells[y * 12 + x] = c

    draw_fn(put)
    return cells


def _builtin_star(put) -> None:
    for x, y in ((5, 1), (5, 2), (4, 3), (5, 3), (6, 3), (3, 4), (4, 4), (5, 4), (6, 4), (7, 4),
                 (5, 5), (4, 6), (6, 6), (3, 7), (7, 7)):
        put(x, y, 2)


def _builtin_heart(put) -> None:
    for x, y in ((3, 2), (4, 2), (7, 2), (8, 2), (2, 3), (3, 3), (4, 3), (5, 3), (6, 3), (7, 3), (8, 3), (9, 3),
                 (2, 4), (3, 4), (4, 4), (5, 4), (6, 4), (7, 4), (8, 4), (9, 4),
                 (3, 5), (4, 5), (5, 5), (6, 5), (7, 5), (8, 5),
                 (4, 6), (5, 6), (6, 6), (7, 6), (5, 7), (6, 7)):
        put(x, y, 1)


def _builtin_bow(put) -> None:
    for x, y in ((2, 4), (3, 4), (4, 4), (7, 4), (8, 4), (9, 4),
                 (1, 5), (2, 5), (3, 5), (4, 5), (5, 5), (6, 5), (7, 5), (8, 5), (9, 5), (10, 5),
                 (2, 6), (3, 6), (4, 6), (7, 6), (8, 6), (9, 6), (5, 4), (5, 6)):
        put(x, y, 6)
    put(5, 5, 5)


def _builtin_leaf(put) -> None:
    for x, y in ((6, 1), (5, 2), (6, 2), (7, 2), (4, 3), (5, 3), (6, 3), (7, 3),
                 (3, 4), (4, 4), (5, 4), (6, 4), (4, 5), (5, 5), (6, 5), (5, 6), (6, 6), (6, 7), (7, 8)):
        put(x, y, 4)


BUILTIN_CATALOG: tuple[dict, ...] = (
    {"id": "star", "name": "星星", "cells": _paint_cells(_builtin_star)},
    {"id": "heart", "name": "爱心", "cells": _paint_cells(_builtin_heart)},
    {"id": "bow", "name": "蝴蝶结", "cells": _paint_cells(_builtin_bow)},
    {"id": "leaf", "name": "小叶", "cells": _paint_cells(_builtin_leaf)},
)


def clamp_norm(v: float, lo: float = -0.55, hi: float = 0.55) -> float:
    try:
        x = float(v)
    except (TypeError, ValueError):
        x = 0.0
    return max(lo, min(hi, x))


def clamp_scale(v: float) -> float:
    try:
        x = float(v)
    except (TypeError, ValueError):
        x = OUTFIT_DEFAULT_SCALE
    return max(OUTFIT_SCALE_MIN, min(OUTFIT_SCALE_MAX, x))


def normalize_decors(raw) -> list[dict]:
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind") or "").strip()
        if kind not in (KIND_MATERIAL, KIND_USER_PAINT, KIND_GIFT_ART, KIND_BUILTIN):
            continue
        ref = str(item.get("ref") or "").strip()
        if kind == KIND_MATERIAL and not ref:
            continue
        if kind == KIND_BUILTIN and not ref:
            continue
        did = str(item.get("id") or "").strip() or uuid4().hex[:10]
        out.append(
            {
                "id": did,
                "kind": kind,
                "ref": ref,
                "nx": clamp_norm(item.get("nx", OUTFIT_DEFAULT_NX)),
                "ny": clamp_norm(item.get("ny", OUTFIT_DEFAULT_NY)),
                "scale": clamp_scale(item.get("scale", OUTFIT_DEFAULT_SCALE)),
            }
        )
        if len(out) >= OUTFIT_MAX:
            break
    return out


def new_decor(kind: str, ref: str = "", *, nx: float | None = None, ny: float | None = None, scale: float | None = None) -> dict:
    return {
        "id": uuid4().hex[:10],
        "kind": kind,
        "ref": str(ref or "").strip(),
        "nx": clamp_norm(OUTFIT_DEFAULT_NX if nx is None else nx),
        "ny": clamp_norm(OUTFIT_DEFAULT_NY if ny is None else ny),
        "scale": clamp_scale(OUTFIT_DEFAULT_SCALE if scale is None else scale),
    }


def cells_to_rgba(cells: list[int], palette: tuple[str | None, ...] | list, *, scale: int = 4) -> Image.Image:
    n = 12
    side = n * max(1, int(scale))
    img = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    px = ImageDraw.Draw(img)
    pal = list(palette)
    for y in range(n):
        for x in range(n):
            idx = int(cells[y * n + x] or 0) if y * n + x < len(cells) else 0
            color = pal[idx] if 0 <= idx < len(pal) else None
            if not color:
                continue
            x0, y0 = x * scale, y * scale
            px.rectangle((x0, y0, x0 + scale - 1, y0 + scale - 1), fill=color)
    return img


def builtin_image(ref: str, *, size_px: int) -> Image.Image | None:
    entry = next((b for b in BUILTIN_CATALOG if b["id"] == ref), None)
    if entry is None:
        return None
    base = cells_to_rgba(entry["cells"], _BUILTIN_PALETTE, scale=4)
    if size_px <= 0:
        return base
    return base.resize((size_px, size_px), Image.Resampling.NEAREST)


def load_png_fit(path: Path, size_px: int) -> Image.Image | None:
    if not path.is_file():
        return None
    try:
        img = Image.open(path).convert("RGBA")
    except Exception:
        return None
    if img.getbbox() is None:
        return None
    if size_px > 0:
        img = img.resize((size_px, size_px), Image.Resampling.NEAREST)
    return img


def _material_from_cells(entry: dict, size_px: int) -> Image.Image | None:
    cells = entry.get("cells")
    if not isinstance(cells, list) or not cells:
        return None
    pal_raw = entry.get("palette")
    if isinstance(pal_raw, list) and pal_raw:
        pal: tuple[str | None, ...] = tuple(
            (c if isinstance(c, str) and c.startswith("#") else None) for c in pal_raw
        )
    else:
        pal = _BUILTIN_PALETTE
    try:
        from home_cottage import gift_pixels_to_rgba

        base = gift_pixels_to_rgba([int(v or 0) for v in cells], pal, scale=4)
    except Exception:
        base = None
    if base is None:
        base = cells_to_rgba([int(v or 0) for v in cells], pal, scale=4)
    if base is None or base.getbbox() is None:
        return None
    if size_px > 0:
        return base.resize((size_px, size_px), Image.Resampling.NEAREST)
    return base


def load_decor_image(
    decor: dict,
    *,
    materials_dir: Path,
    materials_index: Path,
    props_dir: Path,
    size_px: int,
) -> Image.Image | None:
    kind = str(decor.get("kind") or "")
    ref = str(decor.get("ref") or "")
    if kind == KIND_BUILTIN:
        return builtin_image(ref, size_px=size_px)
    if kind == KIND_USER_PAINT:
        return load_png_fit(props_dir / "user_paint.png", size_px)
    if kind == KIND_GIFT_ART:
        return load_png_fit(props_dir / "gift_art.png", size_px)
    if kind == KIND_MATERIAL:
        entry = None
        try:
            from home_cottage import find_material, load_materials_index

            entry = find_material(load_materials_index(materials_index), ref)
        except Exception:
            entry = None
        # 优先用索引 cells 重绘（PNG 可能几乎空白或过期）
        if entry:
            from_cells = _material_from_cells(entry, size_px)
            if from_cells is not None:
                return from_cells
        png = materials_dir / f"{ref}.png"
        img = load_png_fit(png, size_px)
        if img is not None:
            return img
        if entry:
            alt = materials_dir / str(entry.get("file") or f"{ref}.png")
            return load_png_fit(alt, size_px)
    return None


def compose_outfit_layer(
    pet_size: int,
    decors: list[dict],
    *,
    materials_dir: Path,
    materials_index: Path,
    props_dir: Path,
) -> Image.Image:
    """透明底 pet_size×pet_size，装饰按相对中心坐标粘贴。"""
    side = max(16, int(pet_size))
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    cx = side / 2.0
    cy = side / 2.0
    for d in normalize_decors(decors):
        deco_side = max(8, int(round(side * float(d["scale"]))))
        img = load_decor_image(
            d,
            materials_dir=materials_dir,
            materials_index=materials_index,
            props_dir=props_dir,
            size_px=deco_side,
        )
        if img is None:
            continue
        x = int(round(cx + float(d["nx"]) * side - img.width / 2))
        y = int(round(cy + float(d["ny"]) * side - img.height / 2))
        canvas.alpha_composite(img, (x, y))
    return canvas


def list_asset_choices(
    *,
    materials_dir: Path,
    materials_index: Path,
    props_dir: Path,
) -> list[dict]:
    """供装扮面板选择：我的自创（可多张）在前，再公开预设。"""
    choices: list[dict] = []
    try:
        from home_cottage import load_materials_index

        mats = load_materials_index(materials_index)
    except Exception:
        mats = []
    # 全部图库条目进「我的」，按来源加前缀，避免只显示一张槽位图
    for m in mats:
        mid = str(m.get("id") or "")
        if not mid:
            continue
        src = str(m.get("source") or "home").strip().lower()
        if src == "gift":
            prefix = "礼物·"
        elif src == "rpg":
            prefix = "RPG·"
        else:
            prefix = "自创·"
        name = str(m.get("name") or mid)[:14]
        choices.append(
            {
                "kind": KIND_MATERIAL,
                "ref": mid,
                "name": f"{prefix}{name}",
                "group": "我的",
            }
        )
    # 活跃槽（最新导出）作为快捷项
    if (props_dir / "user_paint.png").is_file():
        choices.append(
            {"kind": KIND_USER_PAINT, "ref": "", "name": "最新自创槽", "group": "我的"}
        )
    if (props_dir / "gift_art.png").is_file():
        choices.append(
            {"kind": KIND_GIFT_ART, "ref": "", "name": "最新礼物槽", "group": "我的"}
        )
    for b in BUILTIN_CATALOG:
        choices.append(
            {
                "kind": KIND_BUILTIN,
                "ref": b["id"],
                "name": f"公开·{b['name']}",
                "group": "公开",
            }
        )
    return choices


def thumb_for_choice(
    choice: dict,
    *,
    materials_dir: Path,
    materials_index: Path,
    props_dir: Path,
    size_px: int = 36,
) -> Image.Image | None:
    return load_decor_image(
        {"kind": choice.get("kind"), "ref": choice.get("ref", "")},
        materials_dir=materials_dir,
        materials_index=materials_index,
        props_dir=props_dir,
        size_px=size_px,
    )


def dump_decors(decors: list[dict]) -> list[dict]:
    return normalize_decors(decors)
