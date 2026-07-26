"""桌面家园：室内/室外布置、背景（地砖+室外铺地）配色、家具着色、RPG 素材与礼物画。"""

from __future__ import annotations

import json
import random
import re
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageTk

HOME_COLS = 12
HOME_ROWS = 10
HOME_TILE = 32
# 室内默认：石板棋盘地砖
HOME_FLOOR_A = "#6a7080"
HOME_FLOOR_B = "#5a6070"
HOME_FURN_DEFAULT = "#6aa8d8"  # 天蓝家具（画笔默认 / 旧格回退）
HOME_COLS_MIN, HOME_COLS_MAX = 6, 24
HOME_ROWS_MIN, HOME_ROWS_MAX = 6, 20
HOME_ROOMS_MAX = 4
# 自定义命名素材 kind 前缀：cm:{id}（1×1，不产生 @ 延伸格）
CUSTOM_KIND_PREFIX = "cm:"

# 格子：None | "bed" | {"k":"bed","c":"#6aa8d8"} | "@bed:1,0"
Cell = str | dict | None
HOME_WALL = "#2a3340"
HOME_WALL_TRIM = "#4a6a88"
HOME_BED_SLEEP_MS = 15_000
HOME_SQUAT_MS = 2_500
HOME_WALK_MS = 620  # 自由走动间隔；越大越慢
HOME_CONTROL_STEP_MS = 220  # 操控模式最短步间隔

FLOOR_COLOR_PRESETS: tuple[tuple[str, str, str], ...] = (
    ("苔绿", "#3d5a45", "#35523e"),
    ("木板", "#8b6a45", "#7a5a38"),
    ("石砖", "#6a7080", "#5a6070"),
    ("粉格", "#c898a8", "#b88898"),
    ("青瓷", "#4a8a88", "#3a7a78"),
    ("沙地", "#c2a878", "#b09868"),
)

FURN_COLOR_PRESETS: tuple[tuple[str, str], ...] = (
    ("原木", "#8b5a2b"),
    ("樱粉", "#e89ab0"),
    ("天蓝", "#6aa8d8"),
    ("葡萄", "#8a6ab0"),
    ("薄荷", "#6aba98"),
    ("炭灰", "#5a6068"),
)

# 室外背景素材（与地砖同属「背景」区；每种单独改色）
BG_MATERIAL_KINDS: tuple[str, ...] = ("grass", "land", "water", "rock")
BG_MATERIAL_LABELS: dict[str, str] = {
    "grass": "草地",
    "land": "土地",
    "water": "水面",
    "rock": "岩石",
}
DEFAULT_BG_COLORS: dict[str, str] = {
    "grass": "#3d8a45",
    "land": "#8b6a3a",
    "water": "#3a78b8",
    "rock": "#7a7a88",
}
# 每种背景素材各自的预设（不与其它素材共用）
BG_COLOR_PRESETS: dict[str, tuple[tuple[str, str], ...]] = {
    "grass": (
        ("翠绿", "#3d8a45"),
        ("深绿", "#2a6a38"),
        ("嫩绿", "#66aa55"),
        ("秋草", "#8a9a45"),
        ("青苔", "#3a7a68"),
    ),
    "land": (
        ("泥土", "#8b6a3a"),
        ("沙土", "#c2a878"),
        ("红土", "#a06848"),
        ("黑土", "#5a4838"),
        ("黄土", "#b89858"),
    ),
    "water": (
        ("湖蓝", "#3a78b8"),
        ("深蓝", "#2a5088"),
        ("碧绿", "#2a8a88"),
        ("浅滩", "#66aadd"),
        ("暮紫", "#5a6aa8"),
    ),
    "rock": (
        ("灰岩", "#7a7a88"),
        ("青石", "#5a6a78"),
        ("褐石", "#8a7060"),
        ("白石", "#a8a8b0"),
        ("玄石", "#4a4a55"),
    ),
}

# kind, label, solid, w, h, zone("indoor"|"outdoor"|"both")
HOME_FURNITURE: tuple[tuple[str, str, bool, int, int, str], ...] = (
    ("bed", "床", False, 2, 1, "indoor"),
    ("table", "桌子", True, 1, 1, "indoor"),
    ("chair", "椅子", False, 1, 1, "indoor"),
    ("sofa", "沙发", True, 2, 1, "indoor"),
    ("plant", "盆栽", False, 1, 1, "both"),
    ("carpet", "地毯", False, 2, 2, "indoor"),
    ("shelf", "柜子", True, 1, 2, "indoor"),
    ("lamp", "台灯", True, 1, 1, "indoor"),
    ("window", "窗户", False, 2, 1, "indoor"),
    ("vase", "花瓶", False, 1, 1, "indoor"),
    ("door", "门", False, 1, 1, "both"),
    ("gift_art", "礼物画", False, 1, 1, "both"),
    ("user_paint", "自创画", False, 1, 1, "both"),
    ("grass", "草地", False, 1, 1, "outdoor"),
    ("land", "土地", False, 1, 1, "outdoor"),
    ("water", "水面", True, 1, 1, "outdoor"),
    ("brick", "砖地", False, 1, 1, "outdoor"),
    ("tree", "树木", True, 1, 1, "outdoor"),
    ("rock", "岩石", True, 1, 1, "outdoor"),
    ("flower", "小花", False, 1, 1, "outdoor"),
    ("fence", "栅栏", True, 1, 1, "outdoor"),
    ("bush", "灌木", False, 1, 1, "outdoor"),
    ("path", "石径", False, 1, 1, "outdoor"),
    ("erase", "删除", False, 1, 1, "both"),
)

_FURN_PHOTO_CACHE: dict[tuple, ImageTk.PhotoImage] = {}
_RPG_IMG_CACHE: dict[tuple, Image.Image] = {}
_rpg_assets_dir: Path | None = None
_props_dir: Path | None = None
_materials_dir: Path | None = None
_materials_index: list[dict] = []

VASE_FILLED_COLOR = "#ff88aa"
FLOWER_PETAL_COLORS: tuple[str, ...] = (
    "#ff7799",
    "#ffcc66",
    "#ff88cc",
    "#88ddff",
    "#ffaa55",
    "#ee88ff",
    "#ff6666",
    "#66eecc",
    "#ffdd44",
    "#c080ff",
    "#ff90a8",
    "#70d0ff",
    "#ffa0c0",
    "#90e090",
    "#ffb060",
)
# 地物：叠在背景上，外圈抠底（不含铺地类；岩石归铺地满铺）
OUTDOOR_PROP_KINDS = frozenset({"tree", "flower", "fence", "bush", "plant", "gift_art", "user_paint"})
# 室外铺地：背景层；可与地物叠放（地物存在 g 字段）
OUTDOOR_GROUND_KINDS = frozenset({"grass", "land", "water", "rock", "brick", "path"})
# 室外底色（空格 / 素材抠底透出）
OUTDOOR_BASE_COLOR = "#000000"
OUTDOOR_BASE_COLOR_B = "#0a0a0a"


def set_asset_roots(*, rpg_assets: Path | None = None, props_dir: Path | None = None) -> None:
    global _rpg_assets_dir, _props_dir
    _rpg_assets_dir = rpg_assets
    _props_dir = props_dir
    _FURN_PHOTO_CACHE.clear()
    _RPG_IMG_CACHE.clear()


def set_materials_root(materials_dir: Path | None, index: list[dict] | None = None) -> None:
    """自定义命名素材目录 + 索引（id/name/file）。"""
    global _materials_dir, _materials_index
    _materials_dir = materials_dir
    _materials_index = list(index or [])
    _FURN_PHOTO_CACHE.clear()


def is_custom_material_kind(kind: str | None) -> bool:
    return bool(kind) and str(kind).startswith(CUSTOM_KIND_PREFIX)


def custom_material_id(kind: str) -> str:
    return str(kind)[len(CUSTOM_KIND_PREFIX) :] if is_custom_material_kind(kind) else ""


def custom_kind(mat_id: str) -> str:
    return f"{CUSTOM_KIND_PREFIX}{mat_id}"


def max_rooms_for_companion_days(days: int) -> int:
    """相伴天数 → 可开启室内房间数（含主屋）。"""
    d = max(1, int(days or 1))
    if d >= 45:
        return HOME_ROOMS_MAX
    if d >= 21:
        return 3
    if d >= 7:
        return 2
    return 1


def companion_days_for_next_room(current_max: int) -> int | None:
    """再开一间还需的相伴天数门槛；已满则 None。"""
    thresholds = (1, 7, 21, 45)
    idx = max(1, min(HOME_ROOMS_MAX, int(current_max or 1)))
    if idx >= HOME_ROOMS_MAX:
        return None
    return thresholds[idx]


def _hex(c: str) -> tuple[int, int, int]:
    c = (c or "#888888").lstrip("#")
    if len(c) != 6:
        return 136, 136, 136
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def _blend(a: str, b: str, t: float = 0.5) -> str:
    ar, ag, ab = _hex(a)
    br, bg, bb = _hex(b)
    r = int(ar + (br - ar) * t)
    g = int(ag + (bg - ag) * t)
    bl = int(ab + (bb - ab) * t)
    return f"#{r:02x}{g:02x}{bl:02x}"


def _shade(c: str, factor: float) -> str:
    r, g, b = _hex(c)
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return f"#{r:02x}{g:02x}{b:02x}"


def furniture_meta(kind: str) -> tuple[str, bool, int, int, str] | None:
    if is_custom_material_kind(kind):
        mid = custom_material_id(kind)
        label = "自创"
        for item in _materials_index:
            if str(item.get("id") or "") == mid:
                label = str(item.get("name") or "自创").strip()[:10] or "自创"
                break
        return label, False, 1, 1, "both"
    for k, label, solid, w, h, zone in HOME_FURNITURE:
        if k == kind:
            return label, solid, w, h, zone
    return None


def furniture_for_zone(zone: str, *, include_bg: bool = False) -> list[tuple[str, str, bool, int, int, str]]:
    """素材栏用：默认不含背景类（草地/土地/水面/岩石），它们在「背景」区单独选。"""
    z = zone if zone in ("indoor", "outdoor") else "indoor"
    bg = set(BG_MATERIAL_KINDS)
    out: list[tuple[str, str, bool, int, int, str]] = []
    for item in HOME_FURNITURE:
        if item[5] not in (z, "both"):
            continue
        if not include_bg and item[0] in bg:
            continue
        out.append(item)
    # 命名自创素材追加到栏末（删除之后由 UI 排序）
    for item in _materials_index:
        mid = str(item.get("id") or "").strip()
        if not mid:
            continue
        label = str(item.get("name") or "自创").strip()[:10] or "自创"
        out.append((custom_kind(mid), label, False, 1, 1, "both"))
    return out


def default_bg_colors() -> dict[str, str]:
    return {k: DEFAULT_BG_COLORS[k] for k in BG_MATERIAL_KINDS}


def normalize_bg_colors(raw: object) -> dict[str, str]:
    base = default_bg_colors()
    if not isinstance(raw, dict):
        return base
    out = dict(base)
    for kind in BG_MATERIAL_KINDS:
        v = raw.get(kind)
        if isinstance(v, str) and v.strip().startswith("#") and len(v.strip()) >= 4:
            out[kind] = v.strip()
    return out


def bg_color_for(layout: dict, kind: str) -> str:
    colors = layout.get("bg_colors") if isinstance(layout.get("bg_colors"), dict) else {}
    return str(colors.get(kind) or DEFAULT_BG_COLORS.get(kind) or "#888888")


def _valid_hex_color(color: object) -> str | None:
    if isinstance(color, str) and color.strip().startswith("#") and len(color.strip()) >= 4:
        return color.strip()
    return None


def is_outdoor_stack_prop(kind: str | None) -> bool:
    """需要叠在背景上的室外素材（树/花/门/自创画等）。"""
    if not kind:
        return False
    if kind in OUTDOOR_PROP_KINDS or kind == "door":
        return True
    return is_custom_material_kind(kind)


def cell_ground_kind(cell: Cell) -> str | None:
    """底层背景 kind；无背景则 None。"""
    if cell is None:
        return None
    if isinstance(cell, dict):
        g = str(cell.get("g") or "").strip()
        if g in OUTDOOR_GROUND_KINDS:
            return g
        k = str(cell.get("k") or "").strip()
        if k in OUTDOOR_GROUND_KINDS and not cell.get("g"):
            return k
        return None
    s = str(cell)
    if s.startswith("@"):
        return None
    return s if s in OUTDOOR_GROUND_KINDS else None


def cell_prop_kind(cell: Cell) -> str | None:
    """上层素材 kind；仅背景则 None。"""
    if cell is None:
        return None
    if isinstance(cell, dict):
        if cell.get("g"):
            k = str(cell.get("k") or "").strip()
            if k.startswith("@"):
                parsed = parse_overlay(k)
                return parsed[0] if parsed else None
            return k or None
        k = str(cell.get("k") or "").strip()
        if k and k not in OUTDOOR_GROUND_KINDS:
            return k
        return None
    s = str(cell)
    if s.startswith("@"):
        parsed = parse_overlay(s)
        return parsed[0] if parsed else None
    return None if s in OUTDOOR_GROUND_KINDS else (s or None)


def cell_ground_tint(cell: Cell, layout: dict | None) -> str | None:
    """背景绘制色：单格色优先，否则用统一 bg_colors。brick/path 无 tint。"""
    gk = cell_ground_kind(cell)
    if not gk or gk not in BG_MATERIAL_KINDS:
        return None
    if isinstance(cell, dict):
        if cell.get("g"):
            own = _valid_hex_color(cell.get("gc"))
            if own:
                return own
        else:
            own = _valid_hex_color(cell.get("c"))
            if own:
                return own
    if layout is not None:
        return bg_color_for(layout, gk)
    return DEFAULT_BG_COLORS.get(gk)


def make_ground_cell(kind: str, color: str | None = None) -> Cell:
    k = str(kind or "").strip()
    if k not in OUTDOOR_GROUND_KINDS:
        return None
    own = _valid_hex_color(color) if k in BG_MATERIAL_KINDS else None
    if own:
        return {"k": k, "c": own}
    return k


def make_stack_cell(
    ground: str,
    prop: str,
    *,
    ground_color: str | None = None,
    prop_color: str | None = None,
) -> Cell:
    g = str(ground or "").strip()
    p = str(prop or "").strip()
    if g not in OUTDOOR_GROUND_KINDS or not p:
        return make_ground_cell(g, ground_color)
    cell: dict = {"g": g, "k": p}
    gc = _valid_hex_color(ground_color) if g in BG_MATERIAL_KINDS else None
    if gc:
        cell["gc"] = gc
    pc = _valid_hex_color(prop_color)
    if pc:
        cell["c"] = pc
    return cell


def make_cell(kind: str, color: str | None = None) -> Cell:
    """锚点格：背景可带单格色；家具带家具色。叠放请用 make_stack_cell。"""
    k = str(kind or "").strip()
    if not k or k == "erase":
        return None
    if k in OUTDOOR_GROUND_KINDS:
        return make_ground_cell(k, color)
    if _valid_hex_color(color):
        return {"k": k, "c": color.strip()}
    return k


def cell_value_kind(cell: Cell) -> str | None:
    """最上层 kind（有素材取素材，否则取背景）——用于阻挡/点击判断。"""
    if cell is None:
        return None
    if isinstance(cell, dict):
        if cell.get("g"):
            k = str(cell.get("k") or "").strip()
            if k.startswith("@"):
                parsed = parse_overlay(k)
                return parsed[0] if parsed else (str(cell.get("g") or "").strip() or None)
            return k or str(cell.get("g") or "").strip() or None
        k = str(cell.get("k") or "").strip()
        return k or None
    s = str(cell)
    if s.startswith("@"):
        parsed = parse_overlay(s)
        return parsed[0] if parsed else None
    return s or None


def cell_color(cell: Cell, fallback: str = HOME_FURN_DEFAULT) -> str:
    """上层家具色；无则回退。"""
    if isinstance(cell, dict):
        c = _valid_hex_color(cell.get("c"))
        if c:
            return c
    return str(fallback or HOME_FURN_DEFAULT)


def _normalize_cell(v: object) -> Cell:
    if v in (None, "", "erase"):
        return None
    if isinstance(v, dict):
        g = str(v.get("g") or "").strip()
        k = str(v.get("k") or "").strip()
        if g in OUTDOOR_GROUND_KINDS and k.startswith("@"):
            cell: dict = {"g": g, "k": k}
            gc = _valid_hex_color(v.get("gc"))
            if gc:
                cell["gc"] = gc
            return cell
        if g in OUTDOOR_GROUND_KINDS and k and k not in OUTDOOR_GROUND_KINDS:
            return make_stack_cell(g, k, ground_color=v.get("gc"), prop_color=v.get("c"))
        if not k or k == "erase":
            return None
        if k in OUTDOOR_GROUND_KINDS:
            return make_ground_cell(k, v.get("c"))
        return make_cell(k, v.get("c") if _valid_hex_color(v.get("c")) else None)
    s = str(v)
    if s.startswith("@"):
        return s
    return s


def migrate_outdoor_layers(tiles: list[list[Cell]]) -> None:
    """旧档：无背景的地物补上草地底层。"""
    rows = len(tiles)
    cols = len(tiles[0]) if rows else 0
    for y in range(rows):
        for x in range(cols):
            cell = tiles[y][x]
            if cell is None:
                continue
            if isinstance(cell, str) and cell.startswith("@"):
                continue
            pk = cell_prop_kind(cell)
            gk = cell_ground_kind(cell)
            if pk and not gk:
                pc = cell_color(cell, HOME_FURN_DEFAULT) if isinstance(cell, dict) else None
                tiles[y][x] = make_stack_cell("grass", pk, prop_color=pc)


def blank_tiles(cols: int = HOME_COLS, rows: int = HOME_ROWS) -> list[list[Cell]]:
    return [[None for _ in range(cols)] for _ in range(rows)]


def _place(tiles: list[list[Cell]], kind: str, x: int, y: int, *, color: str | None = None) -> None:
    """室内家具 / 不叠层放置（会清空格子）。室外叠层请用 try_place。"""
    meta = furniture_meta(kind)
    if meta is None:
        return
    _, _, w, h, _ = meta
    rows = len(tiles)
    cols = len(tiles[0]) if rows else 0
    if x < 0 or y < 0 or x + w > cols or y + h > rows:
        return
    for dy in range(h):
        for dx in range(w):
            tiles[y + dy][x + dx] = None
    tiles[y][x] = make_cell(kind, color)
    for dy in range(h):
        for dx in range(w):
            if dx or dy:
                tiles[y + dy][x + dx] = f"@{kind}:{dx},{dy}"


def default_indoor_tiles() -> list[list[Cell]]:
    tiles = blank_tiles()
    color = HOME_FURN_DEFAULT
    _place(tiles, "window", 1, 0, color=color)
    _place(tiles, "bed", 1, 2, color=color)
    _place(tiles, "carpet", 4, 4, color=color)
    _place(tiles, "table", 5, 6, color=color)
    _place(tiles, "chair", 5, 7, color=color)
    _place(tiles, "plant", 9, 7, color=color)
    _place(tiles, "lamp", 3, 2, color=color)
    _place(tiles, "plant", 10, 1, color=color)
    _place(tiles, "door", 0, 5, color=color)
    return tiles


def default_outdoor_tiles() -> list[list[Cell]]:
    """室外默认铺满草地，再叠地物（不删背景）。"""
    tiles = blank_tiles()
    for y in range(HOME_ROWS):
        for x in range(HOME_COLS):
            tiles[y][x] = "grass"
    color = HOME_FURN_DEFAULT

    def stack(kind: str, x: int, y: int) -> None:
        g = cell_ground_kind(tiles[y][x]) or "grass"
        gc = None
        cell = tiles[y][x]
        if isinstance(cell, dict) and not cell.get("g"):
            gc = _valid_hex_color(cell.get("c"))
        tiles[y][x] = make_stack_cell(g, kind, ground_color=gc, prop_color=color)

    stack("tree", 2, 2)
    stack("tree", 9, 3)
    tiles[7][1] = "rock"
    stack("flower", 4, 5)
    stack("flower", 7, 6)
    stack("bush", 10, 7)
    stack("fence", 0, 4)
    stack("fence", 0, 5)
    tiles[1][5] = "path"
    tiles[2][5] = "path"
    tiles[3][5] = "path"
    stack("door", 5, 4)
    tiles[8][8] = "water"
    tiles[8][3] = "land"
    return tiles


def default_layout() -> dict:
    indoor = default_indoor_tiles()
    outdoor = default_outdoor_tiles()
    # 深拷一份给房间，避免与 indoor_tiles 共享引用
    room0_tiles = [[c for c in row] for row in indoor]
    return {
        "cols": HOME_COLS,
        "rows": HOME_ROWS,
        "zone": "indoor",
        "move_mode": "free",
        "floor_a": HOME_FLOOR_A,
        "floor_b": HOME_FLOOR_B,
        "furn_color": HOME_FURN_DEFAULT,
        "bg_colors": default_bg_colors(),
        "indoor_tiles": indoor,
        "outdoor_tiles": outdoor,
        "indoor_pet": [6, 5],
        "outdoor_pet": [5, 4],
        "pet_x": 6,
        "pet_y": 5,
        "tiles": indoor,
        "on_desktop": False,
        "desktop_x": -1,
        "desktop_y": -1,
        "house_name": "",
        "farm": blank_tiles(),  # 室外农田；值由 home_farm.normalize_farm 规范
        "crafted_furniture": [],
        "till_hits": {},
        "chop_jobs": {},
        "tree_regrow": [],
        "rooms": [{"name": "主屋", "tiles": room0_tiles, "pet": [6, 5]}],
        "active_room": 0,
    }


def _copy_grid(src: list, *, cols: int | None = None, rows: int | None = None) -> list[list[Cell]]:
    src_rows = len(src) if isinstance(src, list) else 0
    src_cols = len(src[0]) if src_rows and isinstance(src[0], list) else HOME_COLS
    out_cols = int(cols) if cols is not None else src_cols
    out_rows = int(rows) if rows is not None else (src_rows or HOME_ROWS)
    out = blank_tiles(out_cols, out_rows)
    for y in range(min(len(out), src_rows)):
        row = src[y]
        if not isinstance(row, list):
            continue
        for x in range(min(len(out[0]), len(row))):
            out[y][x] = _normalize_cell(row[x])
    return out


def clamp_grid_size(cols: int, rows: int) -> tuple[int, int]:
    c = max(HOME_COLS_MIN, min(HOME_COLS_MAX, int(cols)))
    r = max(HOME_ROWS_MIN, min(HOME_ROWS_MAX, int(rows)))
    return c, r


def resize_layout(layout: dict, cols: int, rows: int) -> dict:
    """按新尺寸裁切/补空室内外格子，钳宠坐标，强制 cols/rows 与数组一致。"""
    cols, rows = clamp_grid_size(cols, rows)
    sync_rooms_from_active(layout)
    sync_active_zone(layout)
    indoor = layout.get("indoor_tiles") if isinstance(layout.get("indoor_tiles"), list) else blank_tiles()
    outdoor = layout.get("outdoor_tiles") if isinstance(layout.get("outdoor_tiles"), list) else blank_tiles()
    layout["indoor_tiles"] = _copy_grid(indoor, cols=cols, rows=rows)
    layout["outdoor_tiles"] = _copy_grid(outdoor, cols=cols, rows=rows)
    # 农田随尺寸裁切/补空
    farm_src = layout.get("farm") if isinstance(layout.get("farm"), list) else []
    new_farm: list[list] = [[None for _ in range(cols)] for _ in range(rows)]
    for y in range(min(rows, len(farm_src))):
        row = farm_src[y]
        if not isinstance(row, list):
            continue
        for x in range(min(cols, len(row))):
            new_farm[y][x] = row[x]
    layout["farm"] = new_farm
    layout["cols"] = cols
    layout["rows"] = rows

    def clamp_pet(pair: object, fallback: list[int]) -> list[int]:
        if isinstance(pair, (list, tuple)) and len(pair) >= 2:
            return [max(0, min(cols - 1, int(pair[0]))), max(0, min(rows - 1, int(pair[1])))]
        return [max(0, min(cols - 1, fallback[0])), max(0, min(rows - 1, fallback[1]))]

    layout["indoor_pet"] = clamp_pet(layout.get("indoor_pet"), [6, 5])
    layout["outdoor_pet"] = clamp_pet(layout.get("outdoor_pet"), [5, 4])
    # 多房间一并缩放
    rooms_out: list[dict] = []
    for i, room in enumerate(layout.get("rooms") or []):
        if not isinstance(room, dict):
            continue
        tiles = room.get("tiles") if isinstance(room.get("tiles"), list) else blank_tiles(cols, rows)
        rooms_out.append(
            {
                "name": str(room.get("name") or f"房间{i + 1}")[:12],
                "tiles": _copy_grid(tiles, cols=cols, rows=rows),
                "pet": clamp_pet(room.get("pet"), layout["indoor_pet"]),
            }
        )
    if not rooms_out:
        rooms_out = [
            {
                "name": "主屋",
                "tiles": _copy_grid(layout["indoor_tiles"], cols=cols, rows=rows),
                "pet": list(layout["indoor_pet"]),
            }
        ]
    else:
        # 活动房间与 indoor 对齐
        active = int(layout.get("active_room") or 0)
        active = max(0, min(len(rooms_out) - 1, active))
        rooms_out[active]["tiles"] = _copy_grid(layout["indoor_tiles"], cols=cols, rows=rows)
        rooms_out[active]["pet"] = list(layout["indoor_pet"])
        layout["active_room"] = active
    layout["rooms"] = rooms_out

    zone = str(layout.get("zone") or "indoor")
    if zone == "outdoor":
        layout["tiles"] = layout["outdoor_tiles"]
        pet = layout["outdoor_pet"]
    else:
        layout["tiles"] = layout["indoor_tiles"]
        pet = layout["indoor_pet"]
    layout["pet_x"] = int(pet[0])
    layout["pet_y"] = int(pet[1])
    return layout


def normalize_layout(raw: dict | None) -> dict:
    base = default_layout()
    if not isinstance(raw, dict):
        return base
    cols, rows = clamp_grid_size(int(raw.get("cols") or HOME_COLS), int(raw.get("rows") or HOME_ROWS))
    zone = str(raw.get("zone") or "indoor")
    if zone not in ("indoor", "outdoor"):
        zone = "indoor"
    mode = str(raw.get("move_mode") or "free")
    if mode not in ("free", "control"):
        mode = "free"
    floor_a = str(raw.get("floor_a") or HOME_FLOOR_A)
    floor_b = str(raw.get("floor_b") or HOME_FLOOR_B)
    furn_color = str(raw.get("furn_color") or HOME_FURN_DEFAULT)
    bg_colors = normalize_bg_colors(raw.get("bg_colors"))

    indoor = raw.get("indoor_tiles")
    outdoor = raw.get("outdoor_tiles")
    if not isinstance(indoor, list):
        indoor = raw.get("tiles") if zone == "indoor" else None
    if not isinstance(outdoor, list):
        outdoor = raw.get("tiles") if zone == "outdoor" else None
    indoor_tiles = _copy_grid(indoor, cols=cols, rows=rows) if isinstance(indoor, list) else default_indoor_tiles()
    outdoor_tiles = _copy_grid(outdoor, cols=cols, rows=rows) if isinstance(outdoor, list) else default_outdoor_tiles()
    # 若默认格尺寸与目标不一致，对齐
    if len(indoor_tiles) != rows or (indoor_tiles and len(indoor_tiles[0]) != cols):
        indoor_tiles = _copy_grid(indoor_tiles, cols=cols, rows=rows)
    if len(outdoor_tiles) != rows or (outdoor_tiles and len(outdoor_tiles[0]) != cols):
        outdoor_tiles = _copy_grid(outdoor_tiles, cols=cols, rows=rows)
    migrate_outdoor_layers(outdoor_tiles)

    def pet_pair(key: str, fallback: list[int]) -> list[int]:
        v = raw.get(key)
        if isinstance(v, (list, tuple)) and len(v) >= 2:
            return [max(0, min(cols - 1, int(v[0]))), max(0, min(rows - 1, int(v[1])))]
        return [max(0, min(cols - 1, fallback[0])), max(0, min(rows - 1, fallback[1]))]

    indoor_pet = pet_pair("indoor_pet", [6, 5])
    outdoor_pet = pet_pair("outdoor_pet", [5, 4])
    if "pet_x" in raw and "pet_y" in raw:
        cur = [max(0, min(cols - 1, int(raw["pet_x"]))), max(0, min(rows - 1, int(raw["pet_y"])))]
        if zone == "outdoor":
            outdoor_pet = cur
        else:
            indoor_pet = cur

    tiles = outdoor_tiles if zone == "outdoor" else indoor_tiles
    pet = outdoor_pet if zone == "outdoor" else indoor_pet

    # 农田 / 合成解锁（依赖 home_farm，避免循环 import 用内联规范化）
    farm_raw = raw.get("farm")
    farm: list[list] = [[None for _ in range(cols)] for _ in range(rows)]
    if isinstance(farm_raw, list):
        for y in range(min(rows, len(farm_raw))):
            row = farm_raw[y]
            if not isinstance(row, list):
                continue
            for x in range(min(cols, len(row))):
                v = row[x]
                if isinstance(v, dict) and str(v.get("crop") or "").strip():
                    farm[y][x] = {
                        "crop": str(v.get("crop")).strip(),
                        "planted_at": int(v.get("planted_at") or 0),
                        "watered": int(v.get("water_count") or v.get("watered") or 0),
                        "maturity": float(v.get("maturity") or 0),
                        "last_tick": float(v.get("last_tick") or v.get("planted_at") or 0),
                        "boost_until": float(v.get("boost_until") or 0),
                        "water_day": str(v.get("water_day") or ""),
                        "water_count": int(v.get("water_count") or 0),
                    }
    crafted: list[str] = []
    raw_crafted = raw.get("crafted_furniture")
    if isinstance(raw_crafted, list):
        for v in raw_crafted:
            k = str(v or "").strip()
            if k and k not in crafted:
                crafted.append(k)

    till_hits: dict = {}
    raw_till = raw.get("till_hits")
    if isinstance(raw_till, dict):
        for k, v in raw_till.items():
            try:
                till_hits[str(k)] = max(0, int(v))
            except Exception:
                pass
    chop_jobs: dict = {}
    raw_chop = raw.get("chop_jobs")
    if isinstance(raw_chop, dict):
        for k, v in raw_chop.items():
            if isinstance(v, dict):
                chop_jobs[str(k)] = {
                    "need": max(1, int(v.get("need") or 1)),
                    "done": max(0, int(v.get("done") or 0)),
                    "x": int(v.get("x") or 0),
                    "y": int(v.get("y") or 0),
                }
    tree_regrow: list = []
    raw_regrow = raw.get("tree_regrow")
    if isinstance(raw_regrow, list):
        for item in raw_regrow:
            if isinstance(item, dict):
                tree_regrow.append(
                    {
                        "x": int(item.get("x") or 0),
                        "y": int(item.get("y") or 0),
                        "ready_at": float(item.get("ready_at") or 0),
                    }
                )

    rooms, active_room = _normalize_rooms(
        raw.get("rooms"),
        cols=cols,
        rows=rows,
        indoor_tiles=indoor_tiles,
        indoor_pet=indoor_pet,
        active=raw.get("active_room"),
    )
    # 活动房间驱动 indoor_tiles / indoor_pet
    active_room = max(0, min(len(rooms) - 1, active_room))
    indoor_tiles = _copy_grid(rooms[active_room]["tiles"], cols=cols, rows=rows)
    indoor_pet = list(rooms[active_room]["pet"])
    tiles = outdoor_tiles if zone == "outdoor" else indoor_tiles
    pet = outdoor_pet if zone == "outdoor" else indoor_pet

    return {
        "cols": cols,
        "rows": rows,
        "zone": zone,
        "move_mode": mode,
        "floor_a": floor_a,
        "floor_b": floor_b,
        "furn_color": furn_color,
        "bg_colors": bg_colors,
        "indoor_tiles": indoor_tiles,
        "outdoor_tiles": outdoor_tiles,
        "indoor_pet": indoor_pet,
        "outdoor_pet": outdoor_pet,
        "tiles": tiles,
        "pet_x": pet[0],
        "pet_y": pet[1],
        "on_desktop": bool(raw.get("on_desktop")),
        "desktop_x": int(raw.get("desktop_x") if raw.get("desktop_x") is not None else -1),
        "desktop_y": int(raw.get("desktop_y") if raw.get("desktop_y") is not None else -1),
        "house_name": str(raw.get("house_name") or "").strip()[:16],
        "farm": farm,
        "crafted_furniture": crafted,
        "till_hits": till_hits,
        "chop_jobs": chop_jobs,
        "tree_regrow": tree_regrow,
        "rooms": rooms,
        "active_room": active_room,
    }


def _normalize_rooms(
    raw_rooms: object,
    *,
    cols: int,
    rows: int,
    indoor_tiles: list[list[Cell]],
    indoor_pet: list[int],
    active: object,
) -> tuple[list[dict], int]:
    rooms: list[dict] = []
    if isinstance(raw_rooms, list):
        for i, room in enumerate(raw_rooms):
            if not isinstance(room, dict):
                continue
            tiles_src = room.get("tiles") if isinstance(room.get("tiles"), list) else None
            tiles = _copy_grid(tiles_src, cols=cols, rows=rows) if tiles_src is not None else blank_tiles(cols, rows)
            pet_v = room.get("pet")
            if isinstance(pet_v, (list, tuple)) and len(pet_v) >= 2:
                pet = [max(0, min(cols - 1, int(pet_v[0]))), max(0, min(rows - 1, int(pet_v[1])))]
            else:
                pet = [max(0, min(cols - 1, indoor_pet[0])), max(0, min(rows - 1, indoor_pet[1]))]
            rooms.append(
                {
                    "name": str(room.get("name") or f"房间{i + 1}")[:12],
                    "tiles": tiles,
                    "pet": pet,
                }
            )
    if not rooms:
        rooms = [
            {
                "name": "主屋",
                "tiles": _copy_grid(indoor_tiles, cols=cols, rows=rows),
                "pet": list(indoor_pet),
            }
        ]
    try:
        active_i = int(active) if active is not None else 0
    except Exception:
        active_i = 0
    active_i = max(0, min(len(rooms) - 1, active_i))
    return rooms, active_i


def sync_rooms_from_active(layout: dict) -> None:
    """把当前 indoor_tiles / indoor_pet 写回 rooms[active]。"""
    rooms = layout.get("rooms")
    if not isinstance(rooms, list) or not rooms:
        layout["rooms"] = [
            {
                "name": "主屋",
                "tiles": _copy_grid(layout.get("indoor_tiles") or blank_tiles()),
                "pet": list(layout.get("indoor_pet") or [6, 5]),
            }
        ]
        layout["active_room"] = 0
        rooms = layout["rooms"]
    try:
        active = int(layout.get("active_room") or 0)
    except Exception:
        active = 0
    active = max(0, min(len(rooms) - 1, active))
    layout["active_room"] = active
    room = rooms[active]
    if not isinstance(room, dict):
        room = {"name": f"房间{active + 1}", "tiles": blank_tiles(), "pet": [6, 5]}
        rooms[active] = room
    cols = int(layout.get("cols") or HOME_COLS)
    rows = int(layout.get("rows") or HOME_ROWS)
    room["tiles"] = _copy_grid(layout.get("indoor_tiles") or blank_tiles(cols, rows), cols=cols, rows=rows)
    pet = layout.get("indoor_pet") or [6, 5]
    if isinstance(pet, (list, tuple)) and len(pet) >= 2:
        room["pet"] = [int(pet[0]), int(pet[1])]
    room["name"] = str(room.get("name") or f"房间{active + 1}")[:12]


def apply_active_room(layout: dict) -> None:
    """从 rooms[active] 载入 indoor，并刷新 zone=indoor 时的 tiles。"""
    rooms = layout.get("rooms")
    if not isinstance(rooms, list) or not rooms:
        sync_rooms_from_active(layout)
        rooms = layout["rooms"]
    try:
        active = int(layout.get("active_room") or 0)
    except Exception:
        active = 0
    active = max(0, min(len(rooms) - 1, active))
    layout["active_room"] = active
    room = rooms[active] if isinstance(rooms[active], dict) else {}
    cols = int(layout.get("cols") or HOME_COLS)
    rows = int(layout.get("rows") or HOME_ROWS)
    tiles = room.get("tiles") if isinstance(room.get("tiles"), list) else blank_tiles(cols, rows)
    layout["indoor_tiles"] = _copy_grid(tiles, cols=cols, rows=rows)
    pet_v = room.get("pet")
    if isinstance(pet_v, (list, tuple)) and len(pet_v) >= 2:
        layout["indoor_pet"] = [
            max(0, min(cols - 1, int(pet_v[0]))),
            max(0, min(rows - 1, int(pet_v[1]))),
        ]
    else:
        layout["indoor_pet"] = [min(cols - 1, 6), min(rows - 1, 5)]
    if str(layout.get("zone") or "indoor") != "outdoor":
        layout["tiles"] = layout["indoor_tiles"]
        layout["pet_x"] = layout["indoor_pet"][0]
        layout["pet_y"] = layout["indoor_pet"][1]


def switch_room(layout: dict, index: int) -> bool:
    """切换室内房间；成功返回 True。"""
    rooms = layout.get("rooms")
    if not isinstance(rooms, list) or not rooms:
        return False
    idx = int(index)
    if idx < 0 or idx >= len(rooms):
        return False
    sync_active_zone(layout)
    sync_rooms_from_active(layout)
    layout["active_room"] = idx
    apply_active_room(layout)
    if str(layout.get("zone") or "indoor") == "outdoor":
        # 切房间不强制回室内，但室内数据已切换
        pass
    else:
        layout["zone"] = "indoor"
    return True


def add_room(layout: dict, *, name: str = "", max_rooms: int = HOME_ROOMS_MAX) -> bool:
    """新增空房间并切过去；超过上限返回 False。"""
    sync_active_zone(layout)
    sync_rooms_from_active(layout)
    rooms = layout.get("rooms")
    if not isinstance(rooms, list):
        rooms = []
        layout["rooms"] = rooms
    if len(rooms) >= max(1, min(HOME_ROOMS_MAX, int(max_rooms))):
        return False
    cols = int(layout.get("cols") or HOME_COLS)
    rows = int(layout.get("rows") or HOME_ROWS)
    label = str(name or f"房间{len(rooms) + 1}").strip()[:12] or f"房间{len(rooms) + 1}"
    rooms.append({"name": label, "tiles": blank_tiles(cols, rows), "pet": [min(cols - 1, 6), min(rows - 1, 5)]})
    layout["active_room"] = len(rooms) - 1
    apply_active_room(layout)
    layout["zone"] = "indoor"
    layout["tiles"] = layout["indoor_tiles"]
    layout["pet_x"] = layout["indoor_pet"][0]
    layout["pet_y"] = layout["indoor_pet"][1]
    return True


def rename_active_room(layout: dict, name: str) -> None:
    sync_rooms_from_active(layout)
    rooms = layout.get("rooms") or []
    active = int(layout.get("active_room") or 0)
    if 0 <= active < len(rooms) and isinstance(rooms[active], dict):
        rooms[active]["name"] = str(name or f"房间{active + 1}").strip()[:12] or f"房间{active + 1}"


def sync_active_zone(layout: dict) -> None:
    zone = layout.get("zone") or "indoor"
    if zone == "outdoor":
        layout["outdoor_tiles"] = layout.get("tiles") or blank_tiles()
        layout["outdoor_pet"] = [int(layout.get("pet_x") or 0), int(layout.get("pet_y") or 0)]
    else:
        layout["indoor_tiles"] = layout.get("tiles") or blank_tiles()
        layout["indoor_pet"] = [int(layout.get("pet_x") or 0), int(layout.get("pet_y") or 0)]
        sync_rooms_from_active(layout)

def switch_zone(layout: dict, zone: str) -> None:
    if zone not in ("indoor", "outdoor"):
        return
    sync_active_zone(layout)
    layout["zone"] = zone
    if zone == "outdoor":
        layout["tiles"] = layout.get("outdoor_tiles") or default_outdoor_tiles()
        pet = layout.get("outdoor_pet") or [5, 4]
    else:
        layout["tiles"] = layout.get("indoor_tiles") or default_indoor_tiles()
        pet = layout.get("indoor_pet") or [6, 5]
    layout["pet_x"] = int(pet[0])
    layout["pet_y"] = int(pet[1])


def find_first_kind(tiles: list[list[Cell]], kind: str) -> tuple[int, int] | None:
    """找第一格指定家具锚点。"""
    want = str(kind or "")
    if not want or not tiles:
        return None
    for y, row in enumerate(tiles):
        if not isinstance(row, list):
            continue
        for x, cell in enumerate(row):
            if not is_anchor(cell):
                continue
            if cell_value_kind(cell) == want:
                return int(x), int(y)
    return None


def spawn_at_or_near(tiles: list[list[Cell]], x: int, y: int) -> tuple[int, int]:
    """优先落在 (x,y)；不可站则扫邻格，再全图找空格。"""
    rows = len(tiles) if tiles else 0
    cols = len(tiles[0]) if rows and isinstance(tiles[0], list) else 0
    if rows <= 0 or cols <= 0:
        return 0, 0
    x, y = int(x), int(y)
    if 0 <= x < cols and 0 <= y < rows and not cell_blocks(tiles, x, y):
        return x, y
    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < cols and 0 <= ny < rows and not cell_blocks(tiles, nx, ny):
            return nx, ny
    for yy in range(rows):
        for xx in range(cols):
            if not cell_blocks(tiles, xx, yy):
                return xx, yy
    return max(0, min(cols - 1, x)), max(0, min(rows - 1, y))


def use_door(layout: dict) -> tuple[bool, str]:
    """站在门上：切到对侧区域，优先落在对侧门旁。"""
    sync_active_zone(layout)
    cur = str(layout.get("zone") or "indoor")
    target = "outdoor" if cur == "indoor" else "indoor"
    layout["zone"] = target
    if target == "outdoor":
        tiles = layout.get("outdoor_tiles") or default_outdoor_tiles()
        layout["tiles"] = tiles
        layout["outdoor_tiles"] = tiles
        door = find_first_kind(tiles, "door")
        if door is not None:
            px, py = spawn_at_or_near(tiles, door[0], door[1])
            msg = "走出门外"
        else:
            pet = layout.get("outdoor_pet") or [5, 4]
            px, py = spawn_at_or_near(tiles, int(pet[0]), int(pet[1]))
            msg = "到了室外（对侧还没放门）"
        layout["pet_x"] = px
        layout["pet_y"] = py
        layout["outdoor_pet"] = [px, py]
    else:
        tiles = layout.get("indoor_tiles") or default_indoor_tiles()
        layout["tiles"] = tiles
        layout["indoor_tiles"] = tiles
        door = find_first_kind(tiles, "door")
        if door is not None:
            px, py = spawn_at_or_near(tiles, door[0], door[1])
            msg = "进到屋里"
        else:
            pet = layout.get("indoor_pet") or [6, 5]
            px, py = spawn_at_or_near(tiles, int(pet[0]), int(pet[1]))
            msg = "到了室内（对侧还没放门）"
        layout["pet_x"] = px
        layout["pet_y"] = py
        layout["indoor_pet"] = [px, py]
        sync_rooms_from_active(layout)
    return True, msg


def load_layout(path: Path) -> dict:
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return normalize_layout(data if isinstance(data, dict) else None)
        except Exception:
            pass
    return default_layout()


def save_layout(path: Path, layout: dict) -> None:
    sync_active_zone(layout)
    sync_rooms_from_active(layout)
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = int(layout.get("cols") or HOME_COLS)
    rows = int(layout.get("rows") or HOME_ROWS)
    rooms_payload: list[dict] = []
    for i, room in enumerate(layout.get("rooms") or []):
        if not isinstance(room, dict):
            continue
        rooms_payload.append(
            {
                "name": str(room.get("name") or f"房间{i + 1}")[:12],
                "tiles": room.get("tiles") if isinstance(room.get("tiles"), list) else blank_tiles(cols, rows),
                "pet": list(room.get("pet") or [6, 5]),
            }
        )
    if not rooms_payload:
        rooms_payload = [
            {
                "name": "主屋",
                "tiles": layout.get("indoor_tiles") or blank_tiles(cols, rows),
                "pet": list(layout.get("indoor_pet") or [6, 5]),
            }
        ]
    payload = {
        "cols": cols,
        "rows": rows,
        "zone": str(layout.get("zone") or "indoor"),
        "move_mode": str(layout.get("move_mode") or "free"),
        "floor_a": str(layout.get("floor_a") or HOME_FLOOR_A),
        "floor_b": str(layout.get("floor_b") or HOME_FLOOR_B),
        "furn_color": str(layout.get("furn_color") or HOME_FURN_DEFAULT),
        "bg_colors": normalize_bg_colors(layout.get("bg_colors")),
        "indoor_tiles": layout.get("indoor_tiles") or blank_tiles(),
        "outdoor_tiles": layout.get("outdoor_tiles") or blank_tiles(),
        "indoor_pet": layout.get("indoor_pet") or [6, 5],
        "outdoor_pet": layout.get("outdoor_pet") or [5, 4],
        "on_desktop": bool(layout.get("on_desktop")),
        "desktop_x": int(layout.get("desktop_x") if layout.get("desktop_x") is not None else -1),
        "desktop_y": int(layout.get("desktop_y") if layout.get("desktop_y") is not None else -1),
        "house_name": str(layout.get("house_name") or "").strip()[:16],
        "farm": layout.get("farm") if isinstance(layout.get("farm"), list) else blank_tiles(),
        "crafted_furniture": list(layout.get("crafted_furniture") or []),
        "till_hits": dict(layout.get("till_hits") or {}) if isinstance(layout.get("till_hits"), dict) else {},
        "chop_jobs": dict(layout.get("chop_jobs") or {}) if isinstance(layout.get("chop_jobs"), dict) else {},
        "tree_regrow": list(layout.get("tree_regrow") or []) if isinstance(layout.get("tree_regrow"), list) else [],
        "rooms": rooms_payload,
        "active_room": int(layout.get("active_room") or 0),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def is_anchor(cell: Cell) -> bool:
    if cell is None:
        return False
    if isinstance(cell, dict):
        k = str(cell.get("k") or "").strip()
        if k.startswith("@"):
            return False
        # 叠放锚点 / 背景锚点 / 家具锚点
        if cell.get("g") and k:
            return True
        return bool(k)
    s = str(cell)
    return bool(s) and not s.startswith("@")


def parse_overlay(cell: Cell) -> tuple[str, int, int] | None:
    if cell is None:
        return None
    if isinstance(cell, dict):
        k = str(cell.get("k") or "").strip()
        if k.startswith("@"):
            return parse_overlay(k)
        return None
    if not str(cell).startswith("@"):
        return None
    body = str(cell)[1:]
    if ":" not in body:
        return None
    kind, rest = body.split(":", 1)
    try:
        dx_s, dy_s = rest.split(",", 1)
        return kind, int(dx_s), int(dy_s)
    except Exception:
        return None


def cell_kind(tiles: list[list[Cell]], x: int, y: int) -> str | None:
    if y < 0 or x < 0 or y >= len(tiles) or x >= len(tiles[0]):
        return None
    return cell_value_kind(tiles[y][x])


def cell_blocks(tiles: list[list[Cell]], x: int, y: int) -> bool:
    kind = cell_kind(tiles, x, y)
    if kind is None:
        return y < 0 or x < 0 or y >= len(tiles) or x >= len(tiles[0])
    meta = furniture_meta(kind)
    if meta is None:
        return False
    return bool(meta[1])


def on_kinds(tiles: list[list[Cell]], x: int, y: int, kinds: set[str]) -> bool:
    """是否正站在指定家具所占格子上（含多格家具的延伸格）。"""
    return cell_kind(tiles, x, y) in kinds


def near_kinds(tiles: list[list[Cell]], x: int, y: int, kinds: set[str], *, dist: int = 1) -> bool:
    for dy in range(-dist, dist + 1):
        for dx in range(-dist, dist + 1):
            k = cell_kind(tiles, x + dx, y + dy)
            if k in kinds:
                return True
    return False


def _anchor_xy(tiles: list[list[Cell]], x: int, y: int) -> tuple[int, int, str] | None:
    """返回 (锚点x, 锚点y, kind)；空格则 None。"""
    if y < 0 or x < 0 or y >= len(tiles) or x >= len(tiles[0]):
        return None
    cell = tiles[y][x]
    if cell is None:
        return None
    if isinstance(cell, dict):
        k = str(cell.get("k") or "").strip()
        if k.startswith("@"):
            parsed = parse_overlay(k)
            if not parsed:
                return None
            kind, dx, dy = parsed
            return x - dx, y - dy, kind
        kind = cell_value_kind(cell)
        return (x, y, kind) if kind else None
    if isinstance(cell, str) and not cell.startswith("@"):
        kind = cell_value_kind(cell)
        return (x, y, kind) if kind else None
    parsed = parse_overlay(cell)
    if not parsed:
        return None
    kind, dx, dy = parsed
    return x - dx, y - dy, kind


def _flower_petal_colors(seed: int) -> tuple[str, str, str, str]:
    """四片花瓣颜色：由格子种子决定，稳定且彼此随机。"""
    rng = random.Random(int(seed) & 0x7FFFFFFF)
    pool = list(FLOWER_PETAL_COLORS)
    rng.shuffle(pool)
    # 尽量不四片同色：抽 4 个，不够则允许重复
    picked: list[str] = []
    for i in range(4):
        if i < len(pool):
            picked.append(pool[i])
        else:
            picked.append(rng.choice(FLOWER_PETAL_COLORS))
    return picked[0], picked[1], picked[2], picked[3]


def fill_vase_at(tiles: list[list[Cell]], x: int, y: int) -> bool:
    """把花瓶标成已插花。"""
    found = _anchor_xy(tiles, x, y)
    if found is None:
        return False
    ax, ay, kind = found
    if kind != "vase":
        return False
    tiles[ay][ax] = make_cell("vase", VASE_FILLED_COLOR)
    return True


def vase_is_filled(tiles: list[list[Cell]], x: int, y: int) -> bool:
    found = _anchor_xy(tiles, x, y)
    if found is None:
        return False
    ax, ay, kind = found
    if kind != "vase":
        return False
    cell = tiles[ay][ax]
    c = cell_color(cell, "")
    return isinstance(c, str) and c.strip().lower() == VASE_FILLED_COLOR.lower()


def empty_vase_at(tiles: list[list[Cell]], x: int, y: int, *, color: str | None = None) -> bool:
    """拔出花，花瓶恢复为空瓶（可指定家具色）。"""
    found = _anchor_xy(tiles, x, y)
    if found is None:
        return False
    ax, ay, kind = found
    if kind != "vase":
        return False
    col = _valid_hex_color(color) or HOME_FURN_DEFAULT
    # 避免空瓶仍带插花标记色
    if col.strip().lower() == VASE_FILLED_COLOR.lower():
        col = HOME_FURN_DEFAULT
    tiles[ay][ax] = make_cell("vase", col)
    return True


def clear_furniture_at(tiles: list[list[Cell]], x: int, y: int) -> None:
    """整格清空（背景+素材）。分层删除请用 erase_at。"""
    found = _anchor_xy(tiles, x, y)
    if found is None:
        if 0 <= y < len(tiles) and 0 <= x < len(tiles[0]):
            tiles[y][x] = None
        return
    ax, ay, kind = found
    meta = furniture_meta(str(kind))
    if meta is None:
        tiles[y][x] = None
        return
    _, _, w, h, _ = meta
    for dy in range(h):
        for dx in range(w):
            yy, xx = ay + dy, ax + dx
            if 0 <= yy < len(tiles) and 0 <= xx < len(tiles[0]):
                tiles[yy][xx] = None


def erase_at(tiles: list[list[Cell]], x: int, y: int) -> bool:
    """删除：先删上层素材（保留背景），再删背景。"""
    if y < 0 or x < 0 or y >= len(tiles) or x >= len(tiles[0]):
        return False
    found = _anchor_xy(tiles, x, y)
    if found is None:
        if tiles[y][x] is not None:
            tiles[y][x] = None
            return True
        return False
    ax, ay, _top = found
    cell = tiles[ay][ax]
    pk = cell_prop_kind(cell)
    gk = cell_ground_kind(cell)
    if pk:
        # 只去掉素材，留下背景
        gc = None
        if isinstance(cell, dict):
            gc = _valid_hex_color(cell.get("gc")) or (
                _valid_hex_color(cell.get("c")) if not cell.get("g") else None
            )
        meta = furniture_meta(pk)
        w = int(meta[2]) if meta else 1
        h = int(meta[3]) if meta else 1
        # 多格：各格恢复各自背景；未知则用锚点背景
        for dy in range(h):
            for dx in range(w):
                yy, xx = ay + dy, ax + dx
                if not (0 <= yy < len(tiles) and 0 <= xx < len(tiles[0])):
                    continue
                sub = tiles[yy][xx]
                sg = cell_ground_kind(sub) or gk
                sgc = None
                if isinstance(sub, dict):
                    sgc = _valid_hex_color(sub.get("gc"))
                if not sg:
                    tiles[yy][xx] = None
                elif dx == 0 and dy == 0:
                    tiles[yy][xx] = make_ground_cell(sg, gc or sgc)
                else:
                    tiles[yy][xx] = make_ground_cell(sg, sgc)
        return True
    if gk:
        clear_furniture_at(tiles, ax, ay)
        return True
    clear_furniture_at(tiles, ax, ay)
    return True


def recolor_furniture_at(tiles: list[list[Cell]], x: int, y: int, color: str) -> bool:
    """右键上色：背景格=单格背景色；上层素材=家具色。"""
    found = _anchor_xy(tiles, x, y)
    if found is None:
        return False
    ax, ay, kind = found
    col = _valid_hex_color(color)
    if not col:
        return False
    cell = tiles[ay][ax]
    if not is_anchor(cell):
        return False
    gk = cell_ground_kind(cell)
    pk = cell_prop_kind(cell)
    # 纯背景 / 仅点到背景层：写单格背景色（brick/path 不改色）
    if gk and not pk:
        if gk not in BG_MATERIAL_KINDS:
            return False
        tiles[ay][ax] = make_ground_cell(gk, col)
        return True
    if pk and gk:
        # 叠放：右键改上层素材色；背景统一色仍由 bg_colors / 单格 gc 管
        tiles[ay][ax] = make_stack_cell(
            gk,
            pk,
            ground_color=_valid_hex_color(cell.get("gc")) if isinstance(cell, dict) else None,
            prop_color=col,
        )
        return True
    if pk or (kind and kind not in OUTDOOR_GROUND_KINDS):
        tiles[ay][ax] = make_cell(str(kind), col)
        return True
    return False


def recolor_ground_at(tiles: list[list[Cell]], x: int, y: int, color: str) -> bool:
    """给背景单格改色（含叠放格的底层）；草地/土地/水面/岩石。"""
    if y < 0 or x < 0 or y >= len(tiles) or x >= len(tiles[0]):
        return False
    cell = tiles[y][x]
    # 点到延伸格时回到锚点
    found = _anchor_xy(tiles, x, y)
    if found is not None:
        ax, ay, _ = found
        cell = tiles[ay][ax]
        x, y = ax, ay
    gk = cell_ground_kind(cell)
    if gk not in BG_MATERIAL_KINDS:
        return False
    col = _valid_hex_color(color)
    if not col:
        return False
    pk = cell_prop_kind(cell)
    if pk:
        pc = cell_color(cell, HOME_FURN_DEFAULT) if isinstance(cell, dict) else None
        tiles[y][x] = make_stack_cell(gk, pk, ground_color=col, prop_color=pc)
    else:
        tiles[y][x] = make_ground_cell(gk, col)
    return True


def try_place(tiles: list[list[Cell]], kind: str, x: int, y: int, *, color: str | None = None) -> bool:
    if kind == "erase":
        return erase_at(tiles, x, y)
    meta = furniture_meta(kind)
    if meta is None:
        return False
    _, _, w, h, _ = meta
    rows = len(tiles)
    cols = len(tiles[0]) if rows else 0
    if x < 0 or y < 0 or x + w > cols or y + h > rows:
        return False

    # —— 铺背景：替换底层，尽量保留上层 1×1 素材 ——
    if kind in OUTDOOR_GROUND_KINDS:
        for dy in range(h):
            for dx in range(w):
                xx, yy = x + dx, y + dy
                old = tiles[yy][xx]
                pk = cell_prop_kind(old) if (w == 1 and h == 1) else None
                # 多格背景或非 1×1：清掉占用
                if w > 1 or h > 1:
                    clear_furniture_at(tiles, xx, yy)
                    pk = None
                elif pk:
                    # 先卸掉旧素材占用，再叠回
                    pass
                else:
                    clear_furniture_at(tiles, xx, yy)
                if pk and dx == 0 and dy == 0:
                    pc = cell_color(old, HOME_FURN_DEFAULT) if isinstance(old, dict) else color
                    tiles[yy][xx] = make_stack_cell(kind, pk, ground_color=color, prop_color=pc)
                elif dx == 0 and dy == 0:
                    tiles[yy][xx] = make_ground_cell(kind, color if kind in BG_MATERIAL_KINDS else None)
                else:
                    tiles[yy][xx] = make_ground_cell(kind, None)
        return True

    # —— 叠放素材：目标区已有背景时必须铺满背景；全无背景则按室内整格放 ——
    if is_outdoor_stack_prop(kind):
        grounds: list[tuple[str, str | None]] = []
        has_any_g = False
        missing = False
        for dy in range(h):
            for dx in range(w):
                xx, yy = x + dx, y + dy
                sub = tiles[yy][xx]
                g = cell_ground_kind(sub)
                if g:
                    has_any_g = True
                else:
                    missing = True
                gc = None
                if isinstance(sub, dict):
                    gc = _valid_hex_color(sub.get("gc")) or (
                        _valid_hex_color(sub.get("c")) if cell_ground_kind(sub) and not cell_prop_kind(sub) else None
                    )
                grounds.append((g or "", gc))
        if has_any_g:
            if missing:
                return False
            # 先清占用锚点，再按已收集背景叠放
            anchors: set[tuple[int, int]] = set()
            for dy in range(h):
                for dx in range(w):
                    found = _anchor_xy(tiles, x + dx, y + dy)
                    if found:
                        anchors.add((found[0], found[1]))
            for ax, ay in anchors:
                clear_furniture_at(tiles, ax, ay)
            g0, gc0 = grounds[0]
            tiles[y][x] = make_stack_cell(g0, kind, ground_color=gc0, prop_color=color)
            idx = 1
            for dy in range(h):
                for dx in range(w):
                    if dx == 0 and dy == 0:
                        continue
                    g, gc = grounds[idx]
                    idx += 1
                    cell_ov: dict = {"g": g, "k": f"@{kind}:{dx},{dy}"}
                    if gc:
                        cell_ov["gc"] = gc
                    tiles[y + dy][x + dx] = cell_ov
            return True
        # 无背景：纯室外地物不可放；plant/door 等 both 可室内整格放
        if meta[4] == "outdoor":
            return False
        # 无背景：室内盆栽/门等，落到下方整格替换

    # —— 室内等：整格替换 ——
    for dy in range(h):
        for dx in range(w):
            clear_furniture_at(tiles, x + dx, y + dy)
    _place(tiles, kind, x, y, color=color)
    return True


def _near_chroma_bg(r: int, g: int, b: int, a: int) -> bool:
    """外圈常见抠图色：透明 / 白 / 黑 / 绿幕（含青草绿幕约 157,216,0）。"""
    if a < 16:
        return True
    if r >= 245 and g >= 245 and b >= 245:
        return True
    if r >= 220 and g >= 220 and b >= 220 and max(r, g, b) - min(r, g, b) <= 16:
        return True
    if r <= 12 and g <= 12 and b <= 12:
        return True
    # 青草绿幕
    if g >= 160 and b <= 55 and 70 <= r <= 220 and (g - r) >= 15 and (g - b) >= 100:
        return True
    if g >= 200 and g > r + 50 and g > b + 50 and r <= 120 and b <= 120:
        return True
    if g >= 180 and r <= 80 and b <= 80 and g > r + 40 and g > b + 40:
        return True
    if g >= 200 and b <= 40 and r <= 200 and (g - b) >= 140:
        return True
    return False


def _fill_tile_strip_edge_frame(im: Image.Image, tile: int) -> Image.Image:
    """铺地满铺：若四周贴边近黑框则裁掉再缩放到格子，避免黑边框残留。"""
    im = im.convert("RGBA")
    w, h = im.size
    if w >= 4 and h >= 4:
        px = im.load()

        def dark(x: int, y: int) -> bool:
            r, g, b, a = px[x, y]
            return a >= 8 and max(r, g, b) <= 48

        edge = (
            sum(1 for x in range(w) if dark(x, 0))
            + sum(1 for x in range(w) if dark(x, h - 1))
            + sum(1 for y in range(h) if dark(0, y))
            + sum(1 for y in range(h) if dark(w - 1, y))
        )
        # 大半圈贴边是近黑 → 视为素材自带 1px 框
        if edge >= int((w + h) * 1.5):
            im = im.crop((1, 1, w - 1, h - 1))
    return im.resize((max(1, int(tile)), max(1, int(tile))), Image.Resampling.NEAREST)


def _knock_outer_bg(im: Image.Image, *, tol: float = 42.0) -> Image.Image:
    """从外圈 flood 抠掉底色（白/黑/绿幕，或与四角相近的连通底）。"""
    im = im.convert("RGBA")
    w, h = im.size
    if w < 2 or h < 2:
        return im
    px = im.load()
    corners = (
        px[0, 0],
        px[w - 1, 0],
        px[0, h - 1],
        px[w - 1, h - 1],
    )
    # 取仍不透明的角作为参考底色
    refs: list[tuple[int, int, int]] = []
    for r, g, b, a in corners:
        if a >= 16:
            refs.append((r, g, b))
    if not refs:
        return im

    def is_key(r: int, g: int, b: int, a: int) -> bool:
        if _near_chroma_bg(r, g, b, a):
            return True
        if a < 16:
            return True
        for kr, kg, kb in refs:
            dist = ((r - kr) ** 2 + (g - kg) ** 2 + (b - kb) ** 2) ** 0.5
            if dist <= tol:
                return True
        return False

    visited = [[False] * w for _ in range(h)]
    stack: list[tuple[int, int]] = []
    for x in range(w):
        for y in (0, h - 1):
            r, g, b, a = px[x, y]
            if is_key(r, g, b, a):
                stack.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            r, g, b, a = px[x, y]
            if is_key(r, g, b, a):
                stack.append((x, y))

    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= w or y >= h or visited[y][x]:
            continue
        r, g, b, a = px[x, y]
        if not is_key(r, g, b, a):
            continue
        visited[y][x] = True
        px[x, y] = (0, 0, 0, 0)
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return im


def _fit_bottom(im: Image.Image, tw: int, th: int) -> Image.Image:
    """等比缩进画布，底对齐（脚底扎在地砖上）。"""
    im = im.convert("RGBA")
    iw, ih = im.size
    if iw <= 0 or ih <= 0:
        return Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    scale = min(tw / iw, th / ih)
    nw = max(1, int(round(iw * scale)))
    nh = max(1, int(round(ih * scale)))
    im = im.resize((nw, nh), Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    canvas.paste(im, ((tw - nw) // 2, th - nh), im)
    return canvas


def _make_pair_tree_tile(im: Image.Image, tile: int) -> Image.Image:
    """两张 tree 左右并排，整体严格占 1×1 格（同 RPG）。"""
    im = im.convert("RGBA")
    iw, ih = max(1, im.size[0]), max(1, im.size[1])
    slot_w = max(1, tile // 2)
    scale = min(slot_w / iw, tile / ih)
    nw = max(1, int(round(iw * scale)))
    nh = max(1, int(round(ih * scale)))
    one = im.resize((nw, nh), Image.Resampling.NEAREST)
    dst = Image.new("RGBA", (tile, tile), (0, 0, 0, 0))
    y = tile - nh
    for i in range(2):
        x = i * slot_w + (slot_w - nw) // 2
        dst.paste(one, (x, y), one)
    return dst


def _load_rpg_rgba(name: str, tile: int, *, knock: bool = False, pair_tree: bool = False) -> Image.Image | None:
    key = (name, tile, knock, pair_tree)
    hit = _RPG_IMG_CACHE.get(key)
    if hit is not None:
        return hit.copy()
    roots: list[Path] = []
    if _rpg_assets_dir is not None:
        roots.append(_rpg_assets_dir)
    for root in roots:
        for fname in (name, f"{Path(name).stem}.png", f"{Path(name).stem}.jpg"):
            path = root / fname
            if not path.is_file():
                continue
            img = Image.open(path).convert("RGBA")
            if knock:
                if Path(name).stem == "tree":
                    img = _knock_outer_bg(img, tol=28.0)
                else:
                    img = _knock_outer_bg(img, tol=46.0)
            if pair_tree:
                img = _make_pair_tree_tile(img, tile)
            elif knock:
                img = _fit_bottom(img, tile, tile)
            else:
                # 草地/土地/水面等铺地：满铺，并去掉素材自带黑框
                img = _fill_tile_strip_edge_frame(img, tile)
            _RPG_IMG_CACHE[key] = img
            return img.copy()
    return None


def _gift_art_rgba(tile: int) -> Image.Image | None:
    if _props_dir is None:
        return None
    path = _props_dir / "gift_art.png"
    if not path.is_file():
        return None
    img = Image.open(path).convert("RGBA")
    img = _knock_outer_bg(img, tol=36.0)
    return _fit_bottom(img, tile, tile)


def _user_paint_rgba(tile: int) -> Image.Image | None:
    if _props_dir is None:
        return None
    path = _props_dir / "user_paint.png"
    if not path.is_file():
        return None
    img = Image.open(path).convert("RGBA")
    img = _knock_outer_bg(img, tol=36.0)
    return _fit_bottom(img, tile, tile)


def _custom_material_rgba(kind: str, tile: int) -> Image.Image | None:
    if not is_custom_material_kind(kind) or _materials_dir is None:
        return None
    mid = custom_material_id(kind)
    fname = f"{mid}.png"
    for item in _materials_index:
        if str(item.get("id") or "") == mid and item.get("file"):
            fname = str(item.get("file"))
            break
    path = _materials_dir / fname
    if not path.is_file():
        return None
    img = Image.open(path).convert("RGBA")
    img = _knock_outer_bg(img, tol=36.0)
    return _fit_bottom(img, tile, tile)


def _tint_rgba(img: Image.Image, hex_color: str) -> Image.Image:
    """按亮度着色：保留纹理明暗，换主题色（背景素材改色用）。"""
    base = img.convert("RGBA")
    tr, tg, tb = _hex(hex_color)
    px = base.load()
    w, h = base.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
            # 略抬中间调，避免整片发黑
            lum = min(1.0, lum * 1.15 + 0.08)
            px[x, y] = (int(tr * lum), int(tg * lum), int(tb * lum), a)
    return base


def _draw_furniture_rgb(
    kind: str,
    tile: int,
    furn_color: str,
    *,
    tint_color: str | None = None,
    vary_seed: int | None = None,
) -> Image.Image:
    if kind == "gift_art":
        art = _gift_art_rgba(tile)
        if art is not None:
            return art
    if kind == "user_paint" or is_custom_material_kind(kind):
        art = _custom_material_rgba(kind, tile) if is_custom_material_kind(kind) else _user_paint_rgba(tile)
        if art is not None:
            return art
        # 无自创画时给占位，方便先选笔刷再去画
        img = Image.new("RGBA", (tile, tile), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rectangle([2, 2, tile - 3, tile - 3], fill=(255, 200, 220, 220), outline=(200, 100, 140, 255))
        d.rectangle([6, 6, tile - 7, tile - 7], fill=(255, 240, 248, 200))
        return img
    rpg_map = {
        "grass": "grass.png",
        "land": "land.png",
        "water": "water.png",
        "brick": "brick.png",
        "tree": "tree.png",
        "rock": "rock.png",
    }
    mat_tint = tint_color if kind in BG_MATERIAL_KINDS else None
    if kind in rpg_map:
        # 铺地满铺不抠图；仅树等叠放地物抠底
        knock = kind in OUTDOOR_PROP_KINDS and kind not in OUTDOOR_GROUND_KINDS
        pair_tree = kind == "tree"
        rpg = _load_rpg_rgba(rpg_map[kind], tile, knock=knock, pair_tree=pair_tree)
        if rpg is not None:
            if mat_tint:
                return _tint_rgba(rpg, mat_tint)
            return rpg

    meta = furniture_meta(kind)
    if meta is None:
        return Image.new("RGBA", (tile, tile), (0, 0, 0, 0))
    _, _, w, h, _ = meta
    img = Image.new("RGBA", (tile * w, tile * h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    tw, th = tile * w, tile * h
    wood = furn_color or HOME_FURN_DEFAULT
    wood_d = _shade(wood, 0.65)
    accent = _blend(wood, "#88aacc", 0.45)
    fabric = _blend(wood, "#ddeeff", 0.55)

    def box(x0, y0, x1, y1, fill: str, outline: str | None = None) -> None:
        d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=_hex(fill), outline=_hex(outline) if outline else None)

    if kind == "bed":
        box(2, 6, tw - 2, th - 2, wood, wood_d)
        box(4, 4, tw - 4, th // 2 + 2, fabric, _shade(fabric, 0.75))
        box(tw - tile // 2 - 2, 2, tw - 4, th // 2, "#ddeeff")
    elif kind == "table":
        box(4, th // 3, tw - 4, th - 6, wood, wood_d)
        box(6, th - 6, 10, th - 2, wood_d)
        box(tw - 10, th - 6, tw - 6, th - 2, wood_d)
    elif kind == "chair":
        box(6, 4, tw - 6, 10, wood_d)
        box(5, 10, tw - 5, th - 4, wood, wood_d)
    elif kind == "sofa":
        box(2, 8, tw - 2, th - 2, accent, _shade(accent, 0.7))
        box(2, 4, 10, th - 4, _blend(accent, "#ffffff", 0.2))
        box(tw - 10, 4, tw - 2, th - 4, _blend(accent, "#ffffff", 0.2))
        box(10, 6, tw - 10, th // 2 + 2, fabric)
    elif kind == "plant":
        box(tile // 2 - 5, th - 10, tile // 2 + 5, th - 2, wood)
        box(tile // 2 - 8, 4, tile // 2 + 8, th - 10, "#44aa66", "#228844")
        box(tile // 2 - 3, 2, tile // 2 + 3, 8, "#66cc88")
    elif kind == "carpet":
        c1 = _blend(wood, "#aa5566", 0.7)
        box(1, 1, tw - 1, th - 1, c1, _shade(c1, 0.7))
        box(4, 4, tw - 4, th - 4, _blend(c1, "#ffffff", 0.25))
    elif kind == "shelf":
        box(3, 2, tw - 3, th - 2, wood, wood_d)
        box(5, th // 3, tw - 5, th // 3 + 3, _blend(wood, "#ffffff", 0.15))
        box(5, 2 * th // 3, tw - 5, 2 * th // 3 + 3, _blend(wood, "#ffffff", 0.15))
        box(7, 6, 14, 14, "#88ccff")
        box(tw - 16, th // 2, tw - 7, th // 2 + 10, "#ffcc66")
    elif kind == "lamp":
        box(tile // 2 - 3, th // 2, tile // 2 + 3, th - 2, "#555566")
        box(tile // 2 - 8, 4, tile // 2 + 8, th // 2, "#ffee88", "#ccaa44")
    elif kind == "window":
        box(2, 4, tw - 2, th - 4, "#88ccee", "#446688")
        mid = tw // 2
        box(mid - 1, 4, mid + 1, th - 4, "#446688")
        box(2, th // 2 - 1, tw - 2, th // 2 + 1, "#446688")
        box(0, 2, tw, 6, wood)
    elif kind == "door":
        # 木框门扇（可站立切换室内外）
        box(2, 1, tw - 2, th - 1, wood_d, _shade(wood_d, 0.7))
        box(5, 3, tw - 5, th - 2, wood, wood_d)
        box(tw - 10, th // 2 - 1, tw - 7, th // 2 + 3, _blend(wood, "#ffee88", 0.35))
        box(4, 2, tw - 4, 5, _shade(wood, 0.55))
    elif kind == "vase":
        # 陶瓷花瓶；单元格色为 VASE_FILLED_COLOR 时表示已插花
        filled = isinstance(furn_color, str) and furn_color.strip().lower() == VASE_FILLED_COLOR.lower()
        body, rim = "#b8c4cc", "#8a98a4"
        box(tile // 2 - 6, th // 2 + 2, tile // 2 + 6, th - 2, body, rim)
        box(tile // 2 - 8, th // 2 - 2, tile // 2 + 8, th // 2 + 4, "#d0d8e0", rim)
        box(tile // 2 - 4, th // 2 + 4, tile // 2 + 4, th - 4, "#a8b4bc")
        if filled:
            for ox, oy, col in ((-4, -6, "#ff7799"), (4, -6, "#ffcc66"), (0, -10, "#ff88cc"), (0, -4, "#88ddff")):
                box(tile // 2 + ox - 2, tile // 2 + oy - 2, tile // 2 + ox + 2, tile // 2 + oy + 2, col)
            box(tile // 2 - 1, th // 2 - 8, tile // 2 + 1, th // 2 + 2, "#44aa55")
    elif kind == "flower":
        box(tile // 2 - 2, th // 2, tile // 2 + 2, th - 2, "#44aa55")
        seed = int(vary_seed) if vary_seed is not None else abs(hash(str(furn_color))) % 10_000_007
        c0, c1, c2, c3 = _flower_petal_colors(seed)
        for ox, oy, col in ((-5, -2, c0), (5, -2, c1), (0, -6, c2), (0, 2, c3)):
            box(tile // 2 + ox - 2, tile // 2 + oy - 2, tile // 2 + ox + 2, tile // 2 + oy + 2, col)
    elif kind == "fence":
        box(2, 8, tw - 2, 12, wood, wood_d)
        box(4, 4, 8, th - 2, wood_d)
        box(tw - 8, 4, tw - 4, th - 2, wood_d)
    elif kind == "bush":
        box(3, th // 3, tw - 3, th - 2, "#3a8844", "#226633")
        box(6, 4, tw - 6, th // 2, "#55aa66")
    elif kind == "path":
        box(1, 1, tw - 1, th - 1, "#9a8a6a", "#7a6a4a")
        box(4, 4, 8, 8, "#b0a080")
        box(tw - 10, th - 10, tw - 4, th - 4, "#b0a080")
    elif kind == "grass":
        base = mat_tint or DEFAULT_BG_COLORS["grass"]
        box(0, 0, tw, th, base)
        box(2, 2, 6, 8, _shade(base, 1.25))
        box(tw - 8, th - 10, tw - 3, th - 2, _blend(base, "#88ff88", 0.35))
    elif kind == "land":
        base = mat_tint or DEFAULT_BG_COLORS["land"]
        box(0, 0, tw, th, base)
        box(3, 3, 9, 9, _shade(base, 0.85))
        box(tw - 10, th - 10, tw - 3, th - 3, _blend(base, "#ffffff", 0.15))
    elif kind == "water":
        base = mat_tint or DEFAULT_BG_COLORS["water"]
        box(0, 0, tw, th, base)
        box(4, 6, tw - 4, 10, _blend(base, "#ffffff", 0.35))
    elif kind == "brick":
        box(0, 0, tw, th, "#8a6a5a")
        box(1, 1, tw // 2 - 1, th // 2 - 1, "#9a7a6a")
        box(tw // 2 + 1, th // 2 + 1, tw - 1, th - 1, "#9a7a6a")
    elif kind == "tree":
        box(tile // 2 - 3, th // 2, tile // 2 + 3, th - 1, wood)
        box(4, 2, tw - 4, th // 2 + 4, "#2f8a3a", "#1f6a2a")
    elif kind == "rock":
        base = mat_tint or DEFAULT_BG_COLORS["rock"]
        box(3, 8, tw - 3, th - 2, base, _shade(base, 0.7))
        box(6, 4, tw - 6, 12, _blend(base, "#ffffff", 0.25))
    else:
        box(4, 4, tw - 4, th - 4, wood)
    return img


def furniture_photo(
    kind: str,
    tile: int = HOME_TILE,
    furn_color: str = HOME_FURN_DEFAULT,
    *,
    tint_color: str | None = None,
    vary_seed: int | None = None,
) -> ImageTk.PhotoImage | None:
    if kind == "erase":
        return None
    tint_key = tint_color if kind in BG_MATERIAL_KINDS else None
    seed_key = int(vary_seed) if (kind == "flower" and vary_seed is not None) else None
    key = (kind, tile, furn_color, tint_key, seed_key, str(_props_dir), str(_rpg_assets_dir))
    hit = _FURN_PHOTO_CACHE.get(key)
    if hit is not None:
        return hit
    photo = ImageTk.PhotoImage(
        _draw_furniture_rgb(kind, tile, furn_color, tint_color=tint_key, vary_seed=seed_key)
    )
    _FURN_PHOTO_CACHE[key] = photo
    return photo


def pet_photo_from_rgba(rgba: Image.Image, size: int) -> ImageTk.PhotoImage:
    img = rgba.convert("RGBA")
    img.thumbnail((size, size), Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ox = (size - img.size[0]) // 2
    oy = size - img.size[1]
    canvas.paste(img, (ox, max(0, oy)), img)
    return ImageTk.PhotoImage(canvas)


def gift_pixels_to_rgba(cells: list[int], palette: tuple[str | None, ...], *, scale: int = 4) -> Image.Image | None:
    side = 12
    if len(cells) < side * side:
        return None
    painted = 0
    img = Image.new("RGBA", (side * scale, side * scale), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(side):
        for x in range(side):
            idx = int(cells[y * side + x] or 0)
            if idx <= 0:
                continue
            color = palette[idx] if 0 <= idx < len(palette) else None
            if not color:
                continue
            painted += 1
            x0, y0 = x * scale, y * scale
            d.rectangle([x0, y0, x0 + scale - 1, y0 + scale - 1], fill=_hex(color))
    return img if painted else None


def gift_art_quality(cells: list[int], palette: tuple[str | None, ...]) -> tuple[bool, str]:
    """是否达到「优秀」收录标准（提示用）；导出本身只需有涂色。"""
    side = 12
    if len(cells) < side * side:
        return False, "画布太空"
    painted = 0
    colors: set[int] = set()
    for v in cells:
        idx = int(v or 0)
        if idx <= 0:
            continue
        if idx >= len(palette) or not palette[idx]:
            continue
        painted += 1
        colors.add(idx)
    if painted < 8:
        return False, f"再多画一点会更好看（现 {painted} 格）"
    if len(colors) < 2:
        return False, "再多用一种颜色会更丰富"
    return True, f"很棒！已同步家园/RPG（{painted} 格 · {len(colors)} 色）"


def export_gift_art(
    cells: list[int],
    palette: tuple[str | None, ...],
    *,
    home_props: Path,
    rpg_assets: Path,
) -> bool:
    rgba = gift_pixels_to_rgba(cells, palette, scale=4)
    if rgba is None:
        return False
    home_props.mkdir(parents=True, exist_ok=True)
    rpg_assets.mkdir(parents=True, exist_ok=True)
    # 家园用 28 左右，RPG 用 48
    home_img = rgba.resize((HOME_TILE, HOME_TILE), Image.Resampling.NEAREST)
    rpg_img = rgba.resize((48, 48), Image.Resampling.NEAREST)
    home_img.save(home_props / "gift_art.png")
    rpg_img.save(rpg_assets / "gift_art.png")
    _FURN_PHOTO_CACHE.clear()
    return True


def export_user_paint(
    cells: list[int],
    palette: tuple[str | None, ...],
    *,
    home_props: Path,
    rpg_assets: Path,
) -> bool:
    """家园/RPG 内画板保存为「自创画」素材。"""
    rgba = gift_pixels_to_rgba(cells, palette, scale=4)
    if rgba is None:
        return False
    home_props.mkdir(parents=True, exist_ok=True)
    rpg_assets.mkdir(parents=True, exist_ok=True)
    home_img = rgba.resize((HOME_TILE, HOME_TILE), Image.Resampling.NEAREST)
    rpg_img = rgba.resize((48, 48), Image.Resampling.NEAREST)
    home_img.save(home_props / "user_paint.png")
    rpg_img.save(rpg_assets / "user_paint.png")
    _FURN_PHOTO_CACHE.clear()
    return True


def export_pixel_png(
    cells: list[int],
    palette: tuple[str | None, ...],
    path: Path,
    *,
    size: int = 48,
) -> bool:
    """把像素画导出为独立 PNG 文件。"""
    rgba = gift_pixels_to_rgba(cells, palette, scale=4)
    if rgba is None:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    rgba.resize((max(8, int(size)), max(8, int(size))), Image.Resampling.NEAREST).save(path)
    return True


def load_materials_index(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        mid = str(item.get("id") or "").strip()
        if not mid:
            continue
        cells_raw = item.get("cells")
        cells: list[int] | None = None
        if isinstance(cells_raw, list) and cells_raw:
            cells = [max(0, int(v or 0)) for v in cells_raw]
        pal_raw = item.get("palette")
        palette: list[str | None] | None = None
        if isinstance(pal_raw, list) and pal_raw:
            palette = []
            for c in pal_raw:
                if c is None or c == "":
                    palette.append(None)
                elif isinstance(c, str) and c.startswith("#"):
                    palette.append(c)
        out.append(
            {
                "id": mid,
                "name": str(item.get("name") or "自创").strip()[:16] or "自创",
                "file": str(item.get("file") or f"{mid}.png"),
                "source": str(item.get("source") or "home")[:12],
                "cells": cells,
                "palette": palette,
            }
        )
    return out


def save_materials_index(path: Path, items: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = []
    for item in items:
        mid = str(item.get("id") or "").strip()
        if not mid:
            continue
        row: dict = {
            "id": mid,
            "name": str(item.get("name") or "自创").strip()[:16] or "自创",
            "file": str(item.get("file") or f"{mid}.png"),
            "source": str(item.get("source") or "home")[:12],
        }
        if isinstance(item.get("cells"), list) and item["cells"]:
            row["cells"] = [int(v or 0) for v in item["cells"]]
        if isinstance(item.get("palette"), list) and item["palette"]:
            row["palette"] = list(item["palette"])
        payload.append(row)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def find_material(items: list[dict], mat_id: str) -> dict | None:
    mid = str(mat_id or "").strip()
    for item in items:
        if str(item.get("id") or "") == mid:
            return item
    return None


def register_named_material(
    *,
    cells: list[int],
    palette: tuple[str | None, ...] | list,
    name: str,
    materials_dir: Path,
    index_path: Path,
    home_props: Path | None = None,
    rpg_assets: Path | None = None,
    source: str = "home",
    mat_id: str | None = None,
    set_active_user: bool = True,
    set_active_gift: bool = False,
) -> dict | None:
    """命名保存像素画：可多张；写入 materials + 索引（含可再编辑的 cells）。"""
    label = str(name or "").strip()[:16]
    if not label:
        return None
    if not any(int(v or 0) > 0 for v in cells):
        return None
    pal_tuple = tuple(palette)
    rgba = gift_pixels_to_rgba(list(cells), pal_tuple, scale=4)
    if rgba is None:
        return None
    materials_dir.mkdir(parents=True, exist_ok=True)
    items = load_materials_index(index_path)
    mid = str(mat_id or "").strip()
    if mid and find_material(items, mid):
        fname = f"{mid}.png"
    else:
        mid = f"m{time.strftime('%Y%m%d%H%M%S')}"
        # 同秒多张时加后缀
        if find_material(items, mid):
            mid = f"{mid}_{len(items)}"
        fname = f"{mid}.png"
    home_img = rgba.resize((HOME_TILE, HOME_TILE), Image.Resampling.NEAREST)
    rpg_img = rgba.resize((48, 48), Image.Resampling.NEAREST)
    home_img.save(materials_dir / fname)
    entry = {
        "id": mid,
        "name": label,
        "file": fname,
        "source": str(source or "home")[:12],
        "cells": [int(v or 0) for v in cells],
        "palette": [c if c else None for c in pal_tuple],
    }
    existing = find_material(items, mid)
    if existing:
        existing.update(entry)
    else:
        items.append(entry)
    save_materials_index(index_path, items)
    set_materials_root(materials_dir, items)
    if set_active_user and home_props is not None and rpg_assets is not None:
        export_user_paint(list(cells), pal_tuple, home_props=home_props, rpg_assets=rpg_assets)
    if set_active_gift and home_props is not None and rpg_assets is not None:
        export_gift_art(list(cells), pal_tuple, home_props=home_props, rpg_assets=rpg_assets)
    return entry


def apply_material_png(
    entry: dict,
    *,
    materials_dir: Path,
    dest_home: Path,
    dest_rpg: Path,
    dest_name: str,
) -> bool:
    """把命名素材复制为指定槽位 PNG（user_paint / gift_art）。"""
    fname = str(entry.get("file") or "")
    src = materials_dir / fname
    if not src.is_file():
        return False
    try:
        dest_home.mkdir(parents=True, exist_ok=True)
        dest_rpg.mkdir(parents=True, exist_ok=True)
        img = Image.open(src).convert("RGBA")
        img.resize((HOME_TILE, HOME_TILE), Image.Resampling.NEAREST).save(dest_home / dest_name)
        img.resize((48, 48), Image.Resampling.NEAREST).save(dest_rpg / dest_name)
        _FURN_PHOTO_CACHE.clear()
        return True
    except Exception:
        return False


def material_cells_palette(entry: dict) -> tuple[list[int], list[str | None]] | None:
    cells = entry.get("cells")
    if not isinstance(cells, list) or not cells:
        return None
    pal = entry.get("palette")
    if not isinstance(pal, list) or not pal:
        return None
    return [int(v or 0) for v in cells], [c if c else None for c in pal]


def list_home_presets(homes_dir: Path) -> list[dict]:
    """列出已命名保存的家园：[{id,name,path,mtime}]。"""
    if not homes_dir.is_dir():
        return []
    out: list[dict] = []
    for path in sorted(homes_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        name = path.stem
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                name = str(data.get("house_name") or data.get("preset_name") or path.stem).strip() or path.stem
        except Exception:
            pass
        try:
            mtime = path.stat().st_mtime
        except Exception:
            mtime = 0
        out.append({"id": path.stem, "name": name[:24], "path": path, "mtime": mtime})
    return out


def save_home_preset(homes_dir: Path, layout: dict, name: str) -> Path:
    """命名保存当前家园布置（可再打开编辑）。"""
    label = str(name or "").strip()[:16] or "我的小屋"
    homes_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "_", label).strip("_")[:20] or "home"
    path = homes_dir / f"{slug}_{time.strftime('%Y%m%d_%H%M%S')}.json"
    layout = dict(layout)
    layout["house_name"] = label
    layout["preset_name"] = label
    save_layout(path, layout)
    return path


def export_layout_copy(layout: dict, path: Path) -> None:
    """导出家园布置为独立 JSON 文件。"""
    save_layout(path, layout)
