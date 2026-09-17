"""
Silent Oath — 地底冒险 RPG
大地图 + 镜头跟随；地面 / 地下双层楼梯互通；多关卡冒险。
关卡内含耐久血条、背包吃食物回血、宝箱骰子/猜拳判定，
以及马里奥式要素：金币、加速蘑菇、无敌星、随机机关。
"""
from __future__ import annotations

import json
import math
import random
import shutil
import sys
import time
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
MAPS_DIR = ROOT / "maps"


def _rpg_user_root() -> Path:
    """同一个人跨次下载仍保留的 RPG 存档/进度目录。"""
    import os

    local = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if local:
        return Path(local) / "Vpet" / "rpg"
    return Path.home() / ".vpet" / "rpg"


def _rpg_userdata_root() -> Path:
    """桌宠 userdata（与家园材料库共享）。"""
    import os

    local = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if local:
        return Path(local) / "Vpet" / "userdata"
    return Path.home() / ".vpet" / "userdata"


def _materials_dir_and_index() -> tuple[Path, Path]:
    root = _rpg_userdata_root()
    return root / "home_materials", root / "home_materials.json"


def _load_paint_gallery() -> list[dict]:
    _, index = _materials_dir_and_index()
    if not index.is_file():
        return []
    try:
        raw = json.loads(index.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(raw, list):
        return []
    out = []
    for item in raw:
        if isinstance(item, dict) and str(item.get("id") or "").strip():
            out.append(item)
    return out


def _init_rpg_user_dirs() -> tuple[Path, Path]:
    root = _rpg_user_root()
    saves = root / "saves"
    saves.mkdir(parents=True, exist_ok=True)
    progress = root / "progress.json"
    # 兼容旧版：bundled/Vpetgame/saves → 用户目录
    legacy = ROOT / "saves"
    if legacy.is_dir():
        for path in legacy.glob("slot*.json"):
            dest = saves / path.name
            if not dest.exists():
                try:
                    dest.write_bytes(path.read_bytes())
                except Exception:
                    pass
    return saves, progress


SAVES_DIR, PROGRESS_FILE = _init_rpg_user_dirs()


def _desktop_userdata_dir() -> Path:
    """桌宠 userdata：与 pet.py 的食物库存共用。"""
    import os

    local = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if local:
        return Path(local) / "Vpet" / "userdata"
    return Path.home() / ".vpet" / "userdata"


def _food_inventory_path() -> Path:
    return _desktop_userdata_dir() / "food_inventory.json"


def _wallet_path() -> Path:
    return _desktop_userdata_dir() / "wallet.json"


def _add_coins_to_desktop_wallet(n: int) -> int:
    """把 RPG 本局赚到的币写入桌宠统一钱包。返回钱包余额。"""
    n = max(0, int(n))
    if n <= 0:
        return -1
    path = _wallet_path()
    try:
        data: dict = {"coins": 20, "items": {}}
        if path.is_file():
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                data = raw
        coins = max(0, int(data.get("coins") or 0)) + n
        data["coins"] = coins
        if not isinstance(data.get("items"), dict):
            data["items"] = {}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return coins
    except Exception:
        return -1


def load_shared_food_inventory() -> dict[str, int]:
    path = _food_inventory_path()
    out = {fid: 0 for fid in RPG_FOOD_IDS}
    if not path.is_file():
        return out
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            for fid in RPG_FOOD_IDS:
                out[fid] = max(0, int(data.get(fid, 0) or 0))
    except Exception:
        pass
    return out


def save_shared_food_delta(fid: str, delta: int) -> tuple[int, str]:
    """增减桌宠食物库存；返回 (最终数量, 中文名)。"""
    fid = str(fid)
    label = RPG_FOOD_LABELS.get(fid, fid)
    if fid not in RPG_FOOD_IDS or delta == 0:
        return 0, label
    path = _food_inventory_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    inv: dict[str, int] = {}
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                inv = {str(k): max(0, int(v or 0)) for k, v in raw.items()}
        except Exception:
            inv = {}
    cur = max(0, int(inv.get(fid, 0) or 0))
    cur = max(0, cur + int(delta))
    inv[fid] = cur
    try:
        path.write_text(json.dumps(inv, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
    return cur, label


def rps_beats(a: int, b: int) -> int:
    """1石 2剪 3布；返回 1=a胜 0=平 -1=a负。"""
    if a == b:
        return 0
    if (a == 1 and b == 2) or (a == 2 and b == 3) or (a == 3 and b == 1):
        return 1
    return -1


def load_rpg_progress() -> dict:
    default = {"best_level_idx": -1, "best_level_name": "", "cleared_all": False}
    if not PROGRESS_FILE.is_file():
        return dict(default)
    try:
        data = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return dict(default)
        out = dict(default)
        out["best_level_idx"] = int(data.get("best_level_idx", -1))
        out["best_level_name"] = str(data.get("best_level_name") or "")
        out["cleared_all"] = bool(data.get("cleared_all"))
        return out
    except Exception:
        return dict(default)


def save_rpg_progress(progress: dict) -> None:
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.write_text(json.dumps(progress, ensure_ascii=False, indent=2), encoding="utf-8")


def note_rpg_best_level(level_idx: int, *, cleared_all: bool = False) -> dict:
    """记录战役历史最高关卡（0-based）；全通关时标记。"""
    progress = load_rpg_progress()
    idx = max(-1, int(level_idx))
    if idx > int(progress.get("best_level_idx", -1)):
        progress["best_level_idx"] = idx
        if 0 <= idx < len(LEVEL_DEFS):
            progress["best_level_name"] = str(LEVEL_DEFS[idx]["name"])
        else:
            progress["best_level_name"] = f"第{idx + 1}关"
    if cleared_all:
        progress["cleared_all"] = True
        if progress.get("best_level_idx", -1) < len(LEVEL_DEFS) - 1:
            progress["best_level_idx"] = len(LEVEL_DEFS) - 1
            progress["best_level_name"] = str(LEVEL_DEFS[-1]["name"])
    save_rpg_progress(progress)
    return progress


def format_rpg_best_level_line(progress: dict | None = None) -> str:
    progress = progress or load_rpg_progress()
    idx = int(progress.get("best_level_idx", -1))
    if idx < 0:
        return "历史最高：尚未开始"
    name = str(progress.get("best_level_name") or "")
    if not name and 0 <= idx < len(LEVEL_DEFS):
        name = str(LEVEL_DEFS[idx]["name"])
    suffix = " · 已全通关" if progress.get("cleared_all") else ""
    return f"历史最高：第{idx + 1}关 {name}{suffix}"


# BGM：开始冒险后先播 startmusic，再循环 music，直到关闭游戏
MUSIC_END_EVENT = pygame.USEREVENT + 21
STARTMUSIC_NAMES = ("startmusic.mp3", "startmusic.ogg", "startmusic.wav")
LOOPMUSIC_NAMES = ("music.mp3", "music.ogg", "music.wav")
MUSIC_DEFAULT_VOLUME = 0.05  # 循环 music 默认更轻，可用音量加减键调节
MUSIC_VOLUME_STEP = 0.08
# 点 START 播 startmusic：用接近满音量（文件已响度归一）；循环 music 仍用 music_volume
STARTMUSIC_VOLUME = 0.95
STARTMUSIC_VOLUME_MULT = 12.0  # 兼容旧逻辑：相对循环音量的下限倍数

TILE = 36
# 屏幕可见格子（相机视口）
VIEW_TILES_X, VIEW_TILES_Y = 16, 11
VIEW_W, VIEW_H = VIEW_TILES_X * TILE, VIEW_TILES_Y * TILE
UI_H = 72  # 状态行 + 血条/食物 + toast
PALETTE_H = 52  # 编辑器底部素材条
# 内容区尺寸（对白/菜单/地图都画在这里）
SCREEN_W, SCREEN_H = VIEW_W, VIEW_H + UI_H
# 外边框包围整块内容
FRAME_PAD = 18
WINDOW_W, WINDOW_H = SCREEN_W + FRAME_PAD * 2, SCREEN_H + FRAME_PAD * 2
FPS = 60

# 与桌宠共用的食物 id（写入 userdata/food_inventory.json）
RPG_FOOD_IDS: tuple[str, ...] = (
    "apple",
    "bread",
    "candy",
    "berry",
    "cookie",
    "juice",
    "onigiri",
    "tea",
)
RPG_FOOD_LABELS: dict[str, str] = {
    "apple": "苹果",
    "bread": "面包",
    "candy": "糖果",
    "berry": "草莓",
    "cookie": "曲奇",
    "juice": "果汁",
    "onigiri": "饭团",
    "tea": "热茶",
}
# 背包食用回血（马里奥式「吃道具补状态」）
RPG_FOOD_HEAL: dict[str, int] = {
    "apple": 12,
    "bread": 18,
    "candy": 8,
    "berry": 10,
    "cookie": 14,
    "juice": 16,
    "onigiri": 22,
    "tea": 15,
}
RPS_NAMES = {1: "石头", 2: "剪刀", 3: "布"}
RPG_MAX_HP = 100
RPG_HAZARD_CHANCE = 0.035  # 换格时随机踩机关概率
RPG_COIN_HEAL_EVERY = 10  # 攒够金币回复耐久
RPG_COIN_HEAL = 15
RPG_STAR_SEC = 6.0
RPG_MUSHROOM_SEC = 8.0
RPG_SPEED_MULT = 1.55

# 地块
EMPTY = 0
GRASS = 1
LAND = 2
WATER = 3
BRICK = 4
TREE = 5
ROCK = 6
OBSTACLE = 7
HOUSE = 8
TREASURE = 9
BORDER = 10
STAIRS = 11  # 地面↔地下
CAVE = 12  # 洞窟入口：地面↔地下（旧图规范时地下 CAVE→BRICK）
GATE = 13  # 通往下一关
TREASURE_OPEN = 14  # 已开宝箱（装饰）
MOUNTAIN = 15  # 景区（mountain 素材）
GIFT_ART = 16  # 用户礼物像素画（家园导出）
USER_PAINT = 17  # 家园/RPG 内画板自创素材
TRAP_SPIKE = 18  # 尖刺陷阱（可走，踩中扣耐久 / DIY 提示）
TRAP_PIT = 19  # 陷坑（可走，踩中扣耐久 / DIY 提示）
TRAP_TILES = frozenset({TRAP_SPIKE, TRAP_PIT})
PICKUP_COIN = 20  # DIY 可放置：金币
PICKUP_MUSHROOM = 21  # DIY 可放置：加速蘑菇
PICKUP_STAR = 22  # DIY 可放置：无敌星
PICKUP_TILES = frozenset({PICKUP_COIN, PICKUP_MUSHROOM, PICKUP_STAR})
PICKUP_TILE_KIND: dict[int, str] = {
    PICKUP_COIN: "coin",
    PICKUP_MUSHROOM: "mushroom",
    PICKUP_STAR: "star",
}

# DIY 素材栏虚拟笔刷（非地块 ID）
BRUSH_START = -1
BRUSH_PRINCESS = -2
BRUSH_PAINT = -3  # 打开像素画板

# 砖地可走（地下背景）；岩石为隔断墙。TREE 可走（森林）。旧图 BRICK 曾作墙→ROCK。
SOLID = {WATER, ROCK, OBSTACLE, HOUSE, BORDER, MOUNTAIN}
WALKABLE_EXTRA = {
    EMPTY,
    GRASS,
    LAND,
    TREASURE,
    TREASURE_OPEN,
    STAIRS,
    CAVE,
    GATE,
    BRICK,
    TREE,
    GIFT_ART,
    USER_PAINT,
    TRAP_SPIKE,
    TRAP_PIT,
    PICKUP_COIN,
    PICKUP_MUSHROOM,
    PICKUP_STAR,
}
# 背景铺地：占满一格；地物叠在其上并抠成透明
BACKGROUND_TILES = {GRASS, LAND, WATER, ROCK, BRICK}
PROP_OVERLAY = {
    TREE,
    OBSTACLE,
    HOUSE,
    TREASURE,
    TREASURE_OPEN,
    GATE,
    MOUNTAIN,
    CAVE,
    STAIRS,
    GIFT_ART,
    USER_PAINT,
    TRAP_SPIKE,
    TRAP_PIT,
    PICKUP_COIN,
    PICKUP_MUSHROOM,
    PICKUP_STAR,
}
# 踩上可切换地面 / 地下
LAYER_PORTALS = {STAIRS, CAVE}
LAYER_FLASH_DUR = 0.42  # 层切换黑屏淡出时长（秒）

TILE_FILES = {
    GRASS: "grass.png",
    LAND: "land.png",
    WATER: "water.png",
    BRICK: "brick.png",
    TREE: "tree.png",
    ROCK: "rock.png",
    OBSTACLE: "obstacle.png",
    HOUSE: "house.png",
    TREASURE: "treasure.png",
    BORDER: "border.png",
    STAIRS: "stairs.png",
    CAVE: "cave.png",
    MOUNTAIN: "mountain.png",
    GIFT_ART: "gift_art.png",
    USER_PAINT: "user_paint.png",
}

PALETTE = [
    (EMPTY, "清除"),
    (GRASS, "草地·背景"),
    (LAND, "土地·背景"),
    (WATER, "水面·背景"),
    (BRICK, "砖地·背景"),
    (ROCK, "石头·背景"),
    (TREE, "树木"),
    (OBSTACLE, "障碍"),
    (HOUSE, "房屋"),
    (TREASURE, "宝箱"),
    (STAIRS, "楼梯"),
    (CAVE, "洞窟"),
    (GATE, "关卡门"),
    (MOUNTAIN, "景区"),
    (GIFT_ART, "礼物画"),
    (USER_PAINT, "自创画"),
    (TRAP_SPIKE, "尖刺陷阱"),
    (TRAP_PIT, "陷坑"),
    (PICKUP_COIN, "金币"),
    (PICKUP_MUSHROOM, "加速蘑菇"),
    (PICKUP_STAR, "无敌星"),
    (BRUSH_PAINT, "画素材"),
    (BRUSH_START, "起点"),
    (BRUSH_PRINCESS, "公主"),
]

PIXEL_PAINT_SIZE = 12
PIXEL_PAINT_COLORS: tuple[tuple[int, int, int] | None, ...] = (
    None,
    (255, 107, 157),
    (255, 51, 85),
    (255, 136, 68),
    (255, 221, 102),
    (136, 255, 102),
    (102, 221, 170),
    (68, 204, 255),
    (136, 204, 255),
    (68, 102, 255),
    (204, 136, 255),
    (255, 255, 255),
    (187, 187, 187),
    (51, 68, 85),
    (34, 34, 34),
    (139, 90, 43),
)

# 出发点房屋绘制放大（格数边长）；树木：两张 tree 横向并排，整体仍只占 1 格
# mountain 横纵都严格占 1 格（与 TREE 一样 TILE×TILE）
HOUSE_DRAW_TILES = 3

TREASURE_LOOT = (
    ("金币", "得到几枚闪亮的金币。"),
    ("药水", "一瓶恢复体力的药水。"),
    ("地图碎片", "旧羊皮纸上画着洞窟记号。"),
    ("护身符", "小小的护身符，感觉运气变好了。"),
    ("宝石", "一颗透亮的彩色宝石。"),
)

INTERACT_HINTS = {
    TREASURE: "按 E 打开宝箱（随机骰子或猜拳）",
    HOUSE: "按 E 查看房屋",
    GATE: "靠近关卡门即可进入下一关",
    STAIRS: "踩上楼梯切换地面 / 地下",
    CAVE: "踩上洞窟切换地面 / 地下",
    TREASURE_OPEN: "空宝箱……什么都不剩了",
    TRAP_SPIKE: "尖刺陷阱！小心脚下",
    TRAP_PIT: "陷坑！别掉下去",
    PICKUP_COIN: "金币（开局后可捡）",
    PICKUP_MUSHROOM: "加速蘑菇（开局后可捡）",
    PICKUP_STAR: "无敌星（开局后可捡）",
}

# 关卡设定：更多样素材（森林/水面/景区/洞窟）拼成
# seed 固定：同关布局稳定；存档仍保存当前进度（已开宝箱/坐标），不必删存档
LEVEL_DEFS = [
    {
        "name": "第一关 · 绿野秘洞",
        "seed": 240101,
        "w": 52,
        "h": 40,
        "obstacles": 18,
        "forests": 10,
        "mountains": 4,
        "caves": 2,
        "cluster_r": (2, 5),
        "lakes": 3,
        "land_blobs": 16,
        "stairs": 2,
        "treasures": 5,
        "traps": 6,
        "ug_fill": 0.62,
        "ug_corridors": 22,
        "princess": False,
    },
    {
        "name": "第二关 · 荒原地穴",
        "seed": 240102,
        "w": 60,
        "h": 46,
        "obstacles": 22,
        "forests": 12,
        "mountains": 6,
        "caves": 3,
        "cluster_r": (2, 6),
        "lakes": 4,
        "land_blobs": 20,
        "stairs": 2,
        "treasures": 6,
        "traps": 8,
        "ug_fill": 0.58,
        "ug_corridors": 28,
        "princess": False,
    },
    {
        "name": "第三关 · 湖畔洞窟",
        "seed": 240103,
        "w": 68,
        "h": 52,
        "obstacles": 26,
        "forests": 16,
        "mountains": 8,
        "caves": 4,
        "cluster_r": (3, 6),
        "lakes": 5,
        "land_blobs": 24,
        "stairs": 3,
        "treasures": 8,
        "traps": 10,
        "ug_fill": 0.55,
        "ug_corridors": 34,
        "princess": False,
    },
    {
        "name": "最终关 · 地下牢笼",
        "seed": 240104,
        "w": 76,
        "h": 58,
        "obstacles": 30,
        "forests": 18,
        "mountains": 10,
        "caves": 4,
        "cluster_r": (3, 7),
        "lakes": 6,
        "land_blobs": 28,
        "stairs": 3,
        "treasures": 10,
        "traps": 14,
        "ug_fill": 0.52,
        "ug_corridors": 40,
        "princess": True,
    },
]

def load_img(name: str, *, key_bg: bool = False) -> pygame.Surface:
    import os

    candidates = [
        _rpg_user_root() / "assets" / name,
        ASSETS / name,
    ]
    # 桌宠 userdata（便携包 data/ 或本机 Local）导出的礼物画
    try:
        local = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if local:
            candidates.insert(0, Path(local) / "Vpet" / "userdata" / "rpg_assets" / name)
            candidates.insert(0, Path(local) / "Vpet" / "rpg" / "assets" / name)
    except Exception:
        pass
    # exe 旁便携 data
    if getattr(sys, "frozen", False):
        candidates.insert(0, Path(sys.executable).resolve().parent / "data" / "rpg_assets" / name)
    for path in candidates:
        if path.is_file():
            if key_bg:
                try:
                    from process_assets import flood_key
                    from PIL import Image

                    keyed = flood_key(Image.open(path))
                    return _pil_rgba_to_surface(keyed)
                except Exception:
                    # 抠图失败才退回原图；勿因 convert_alpha 失败丢掉已抠结果
                    pass
            try:
                return pygame.image.load(str(path)).convert_alpha()
            except Exception:
                return pygame.image.load(str(path))
    # 礼物画 / 自创画缺失时生成占位，避免编辑器崩溃
    if name in ("gift_art.png", "user_paint.png"):
        ensure_user_art_placeholder(name)
        path = ASSETS / name
        if path.is_file():
            try:
                return pygame.image.load(str(path)).convert_alpha()
            except Exception:
                return pygame.image.load(str(path))
    raise FileNotFoundError(f"缺少素材: {ASSETS / name}，请先运行 process_assets.py")


def _pil_rgba_to_surface(im) -> pygame.Surface:
    """PIL RGBA → 带透明的 Surface；透明像素清成 (0,0,0,0) 防绿边渗色。"""
    from PIL import Image

    im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 8:
                px[x, y] = (0, 0, 0, 0)
    raw = im.tobytes("raw", "RGBA")
    surf = pygame.image.fromstring(raw, (w, h), "RGBA")
    try:
        return surf.convert_alpha()
    except Exception:
        out = pygame.Surface((w, h), pygame.SRCALPHA, 32)
        out.blit(surf, (0, 0))
        return out


def _draw_checkerboard(surf: pygame.Surface, rect: pygame.Rect, cell: int = 4) -> None:
    """素材栏透明底预览用棋盘格。"""
    c0, c1 = (36, 40, 52), (28, 32, 44)
    for y in range(rect.top, rect.bottom, cell):
        for x in range(rect.left, rect.right, cell):
            odd = ((x - rect.left) // cell + (y - rect.top) // cell) & 1
            pygame.draw.rect(
                surf,
                c1 if odd else c0,
                (
                    x,
                    y,
                    min(cell, rect.right - x),
                    min(cell, rect.bottom - y),
                ),
            )


def ensure_user_art_placeholder(name: str = "gift_art.png") -> None:
    path = ASSETS / name
    if path.is_file():
        return
    ASSETS.mkdir(exist_ok=True)
    from PIL import Image, ImageDraw

    im = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if name == "user_paint.png":
        d.rectangle([2, 2, TILE - 3, TILE - 3], fill=(180, 220, 255, 255), outline=(80, 140, 200, 255))
        d.rectangle([8, 8, TILE - 9, TILE - 9], fill=(220, 240, 255, 255))
    else:
        d.rectangle([2, 2, TILE - 3, TILE - 3], fill=(255, 180, 200, 255), outline=(180, 80, 120, 255))
        d.rectangle([8, 8, TILE - 9, TILE - 9], fill=(255, 220, 230, 255))
    im.save(path)


def ensure_gift_art_placeholder() -> None:
    ensure_user_art_placeholder("gift_art.png")
    ensure_user_art_placeholder("user_paint.png")


def ensure_extra_tiles() -> None:
    """楼梯/洞窟：透明底生成（叠在背景上）；缺失或旧版不透明底时刷新。"""
    ASSETS.mkdir(exist_ok=True)
    ensure_gift_art_placeholder()
    from PIL import Image, ImageDraw

    def _write_stairs_down() -> None:
        im = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for i, c in enumerate([(160, 140, 110), (140, 120, 95), (120, 100, 78), (100, 82, 62)]):
            y0 = 6 + i * 9
            x0 = 4 + i * 3
            d.rectangle([x0, y0, 44, y0 + 8], fill=(*c, 255))
        d.polygon([(24, 34), (18, 26), (30, 26)], fill=(220, 200, 80, 255))
        im.save(ASSETS / "stairs.png")

    def _write_stairs_up() -> None:
        im = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for i, c in enumerate([(70, 65, 90), (85, 78, 105), (100, 92, 120), (115, 105, 135)]):
            y0 = 34 - i * 9
            x0 = 4 + i * 3
            d.rectangle([x0, y0, 44, y0 + 8], fill=(*c, 255))
        d.polygon([(24, 12), (18, 20), (30, 20)], fill=(220, 200, 80, 255))
        im.save(ASSETS / "stairs_up.png")

    def _write_cave() -> None:
        im = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.ellipse([4, 6, TILE - 5, TILE - 3], fill=(70, 62, 78, 255))
        d.ellipse([12, 14, TILE - 13, TILE - 8], fill=(0, 0, 0, 0))
        for x, y in [(5, 7), (18, 4), (30, 12), (8, 22), (35, 20), (12, 35)]:
            d.point((x, y), fill=(55, 50, 68, 255))
        im.save(ASSETS / "cave.png")

    def _needs_refresh(path: Path) -> bool:
        if not path.is_file():
            return True
        try:
            im = Image.open(path).convert("RGBA")
            # 四角皆不透明 → 旧版铺满底，需刷新为透明叠层
            w, h = im.size
            corners = (im.getpixel((0, 0)), im.getpixel((w - 1, 0)), im.getpixel((0, h - 1)), im.getpixel((w - 1, h - 1)))
            return all(a >= 200 for *_rgb, a in corners)
        except Exception:
            return True

    if _needs_refresh(ASSETS / "stairs.png"):
        _write_stairs_down()
    if _needs_refresh(ASSETS / "stairs_up.png"):
        _write_stairs_up()
    if _needs_refresh(ASSETS / "cave.png"):
        _write_cave()


PLAYER_KINDS = ("knight", "vpet", "allmate")
PLAYER_KIND_LABELS = {
    "knight": "knight",
    "vpet": "aoba",
    "allmate": "ren",
}
# 选角/菜单提示：未来可扩展更多同伴
FUTURE_COMPANION_TIP = "也许未来随着其他角色的开发，冒险路上也会遇到更多伙伴。"
# 操控小人起始格：编辑器蓝框
START_MARKER_COLOR = (40, 140, 255)
START_MARKER_FILL = (40, 140, 255, 55)


def _vpet_asset_candidates(filename: str) -> list[Path]:
    """Vpet/aoba：优先 RPG/assets/vpet，其次桌宠 sprites。"""
    out: list[Path] = [
        ASSETS / "vpet" / filename,
        ASSETS / filename,
    ]
    out.extend(_desktop_asset_candidates("sprites", filename))
    out.extend(_desktop_asset_candidates("vpet", filename))
    uniq: list[Path] = []
    for p in out:
        if p not in uniq:
            uniq.append(p)
    return uniq


def _allmate_asset_candidates(filename: str) -> list[Path]:
    """Allmate/ren：优先 RPG/assets/allmate，其次桌宠 minipet。"""
    out: list[Path] = [
        ASSETS / "allmate" / filename,
        ASSETS / "vpet" / filename,  # 兼容旧路径里的 pet*
        ASSETS / filename,
    ]
    out.extend(_desktop_asset_candidates("minipet", filename))
    out.extend(_desktop_asset_candidates("allmate", filename))
    uniq: list[Path] = []
    for p in out:
        if p not in uniq:
            uniq.append(p)
    return uniq


def _desktop_asset_candidates(*parts: str) -> list[Path]:
    """桌宠工程 assets（minipet / sprites）相对 RPG 包的候选路径。"""
    bases = [
        ROOT.parent.parent / "assets",  # VpetPNG/1.0/assets
        ROOT.parent.parent.parent / "assets",
        ROOT.parent / "assets",  # bundled/assets（若有）
        Path.cwd() / "assets",
    ]
    # 打包后：exe 旁 / _MEIPASS 邻近
    if getattr(sys, "frozen", False):
        meipass = Path(getattr(sys, "_MEIPASS", ROOT))
        bases.extend(
            [
                meipass / "assets",
                Path(sys.executable).resolve().parent / "assets",
                meipass.parent / "assets",
            ]
        )
    out: list[Path] = []
    for b in bases:
        p = b.joinpath(*parts)
        if p not in out:
            out.append(p)
    return out


def _key_outer_bg_surface(surf: pygame.Surface) -> pygame.Surface:
    """抠掉外圈连通背景（白/黑/绿幕），选角与素材栏预览用。"""
    try:
        from process_assets import flood_key
        from PIL import Image

        w, h = surf.get_size()
        raw = pygame.image.tostring(surf, "RGBA")
        im = Image.frombytes("RGBA", (w, h), raw)
        keyed = flood_key(im)
        return _pil_rgba_to_surface(keyed)
    except Exception:
        try:
            return surf.convert_alpha()
        except Exception:
            return surf


def _load_surface_any(
    paths: list[Path],
    size: tuple[int, int] | None = None,
    *,
    key_bg: bool = True,
) -> pygame.Surface | None:
    for p in paths:
        if not p.is_file():
            continue
        try:
            if key_bg:
                from process_assets import flood_key
                from PIL import Image

                keyed = flood_key(Image.open(p))
                img = _pil_rgba_to_surface(keyed)
            else:
                try:
                    img = pygame.image.load(str(p)).convert_alpha()
                except Exception:
                    img = pygame.image.load(str(p))
            if size is not None:
                img = pygame.transform.scale(img, size)
                if key_bg:
                    img = _key_outer_bg_surface(img)
            return img
        except Exception:
            continue
    return None


def _tint_surface(src: pygame.Surface, rgba: tuple[int, int, int, int]) -> pygame.Surface:
    out = src.copy()
    tint = pygame.Surface(out.get_size(), pygame.SRCALPHA)
    tint.fill(rgba)
    out.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return out


class Assets:
    def __init__(self) -> None:
        ensure_extra_tiles()
        self.tiles: dict[int, pygame.Surface] = {}
        for tid, fname in TILE_FILES.items():
            # 地物：外圈完全抠透明，叠在背景上；背景素材不抠，铺满一格
            img = load_img(fname, key_bg=(tid in PROP_OVERLAY))
            if tid == HOUSE:
                side = TILE * HOUSE_DRAW_TILES
                self.tiles[tid] = pygame.transform.scale(img, (side, side))
            elif tid == MOUNTAIN:
                # 景区：横纵都压进 1 格
                self.tiles[tid] = pygame.transform.scale(img, (TILE, TILE))
            elif tid == TREE:
                # 两棵树图横向并排；整体宽高都压进 1 格（逻辑仍占一格草地）
                self.tiles[tid] = self._make_pair_tree_tile(img)
            else:
                self.tiles[tid] = pygame.transform.scale(img, (TILE, TILE))
            # 缩放后再抠一次，清掉缩放渗出的绿边
            if tid in PROP_OVERLAY:
                self.tiles[tid] = _key_outer_bg_surface(self.tiles[tid])
            # 关卡门：房屋着色提示（略小一点以免与出发点房屋混淆）
        gate = self.tiles[HOUSE].copy()
        if gate.get_width() > TILE * 2:
            gate = pygame.transform.scale(gate, (TILE * 2, TILE * 2))
        tint = pygame.Surface(gate.get_size(), pygame.SRCALPHA)
        tint.fill((255, 200, 60, 90))
        gate.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        self.tiles[GATE] = gate
        # 已开宝箱：同一素材加暗罩
        open_chest = self.tiles[TREASURE].copy()
        dark = pygame.Surface(open_chest.get_size(), pygame.SRCALPHA)
        dark.fill((0, 0, 0, 110))
        open_chest.blit(dark, (0, 0))
        self.tiles[TREASURE_OPEN] = open_chest
        # 可放置陷阱（程序绘制，无需额外 PNG）
        # 游玩时默认几乎看不见；踩中后显示完整贴图。编辑器始终用完整图。
        spike = self._make_trap_spike_tile()
        pit = self._make_trap_pit_tile()
        self.tiles[TRAP_SPIKE] = spike
        self.tiles[TRAP_PIT] = pit
        self.trap_hidden: dict[int, pygame.Surface] = {
            TRAP_SPIKE: self._make_trap_faint_tile(spike, alpha=32),
            TRAP_PIT: self._make_trap_faint_tile(pit, alpha=28),
        }
        self.tiles[PICKUP_COIN] = self._make_pickup_coin_tile()
        self.tiles[PICKUP_MUSHROOM] = self._make_pickup_mushroom_tile()
        self.tiles[PICKUP_STAR] = self._make_pickup_star_tile()
        self.stairs_up = pygame.transform.scale(load_img("stairs_up.png", key_bg=True), (TILE, TILE))
        self._load_knight_and_ui()

    @staticmethod
    def _make_trap_spike_tile() -> pygame.Surface:
        """尖刺陷阱：草地感底 + 金属尖刺。"""
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        # 暗色石板底
        pygame.draw.rect(s, (52, 48, 58, 220), (2, TILE // 2, TILE - 4, TILE // 2 - 2), border_radius=3)
        pygame.draw.rect(s, (36, 32, 42, 180), (4, TILE // 2 + 2, TILE - 8, TILE // 2 - 6), border_radius=2)
        # 三根尖刺
        tips = ((TILE // 4, TILE // 2 + 2), (TILE // 2, TILE // 2 + 2), (3 * TILE // 4, TILE // 2 + 2))
        for cx, by in tips:
            pts = [(cx, by - TILE // 3), (cx - 5, by + 2), (cx + 5, by + 2)]
            pygame.draw.polygon(s, (190, 200, 210), pts)
            pygame.draw.polygon(s, (120, 130, 145), pts, 1)
            # 尖端高光
            pygame.draw.circle(s, (240, 245, 255), (cx, by - TILE // 3 + 2), 2)
        return s

    @staticmethod
    def _make_trap_pit_tile() -> pygame.Surface:
        """陷坑：黑洞 + 碎石边缘。"""
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        cx, cy = TILE // 2, TILE // 2 + 2
        # 外圈泥土
        pygame.draw.ellipse(s, (78, 58, 42, 230), (4, 8, TILE - 8, TILE - 12))
        # 内黑洞
        pygame.draw.ellipse(s, (18, 14, 22, 255), (10, 14, TILE - 20, TILE - 24))
        pygame.draw.ellipse(s, (8, 6, 12, 255), (14, 18, TILE - 28, TILE - 32))
        # 边缘碎石
        for ox, oy in ((8, 12), (TILE - 10, 14), (12, TILE - 10), (TILE - 14, TILE - 12)):
            pygame.draw.circle(s, (110, 95, 80), (ox, oy), 3)
        # 警示十字微光
        pygame.draw.line(s, (180, 90, 70, 160), (cx - 6, cy), (cx + 6, cy), 1)
        pygame.draw.line(s, (180, 90, 70, 160), (cx, cy - 5), (cx, cy + 5), 1)
        return s

    @staticmethod
    def _make_trap_faint_tile(full: pygame.Surface, *, alpha: int = 30) -> pygame.Surface:
        """未踩中时的微弱提示：几乎看不见，只剩一点点痕迹。"""
        faint = pygame.Surface(full.get_size(), pygame.SRCALPHA)
        tmp = full.copy()
        # SRCALPHA 源上 set_alpha 会与像素 alpha 相乘，得到极淡叠层
        tmp.set_alpha(max(0, min(255, int(alpha))))
        faint.blit(tmp, (0, 0))
        return faint

    @staticmethod
    def _make_pickup_coin_tile() -> pygame.Surface:
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        cx, cy = TILE // 2, TILE // 2
        pygame.draw.circle(s, (255, 200, 40), (cx, cy), 10)
        pygame.draw.circle(s, (255, 240, 140), (cx, cy), 10, 2)
        pygame.draw.line(s, (180, 120, 20), (cx, cy - 5), (cx, cy + 5), 2)
        return s

    @staticmethod
    def _make_pickup_mushroom_tile() -> pygame.Surface:
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        cx, cy = TILE // 2, TILE // 2
        pygame.draw.circle(s, (230, 60, 70), (cx, cy - 2), 9)
        pygame.draw.circle(s, (250, 250, 250), (cx, cy + 6), 7)
        pygame.draw.circle(s, (255, 255, 255), (cx - 3, cy - 4), 2)
        return s

    @staticmethod
    def _make_pickup_star_tile() -> pygame.Surface:
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        cx, cy = TILE // 2, TILE // 2
        pts = []
        for i in range(5):
            a = -math.pi / 2 + i * (2 * math.pi / 5)
            pts.append((cx + int(math.cos(a) * 11), cy + int(math.sin(a) * 11)))
            a2 = a + math.pi / 5
            pts.append((cx + int(math.cos(a2) * 5), cy + int(math.sin(a2) * 5)))
        pygame.draw.polygon(s, (255, 220, 60), pts)
        pygame.draw.polygon(s, (255, 255, 200), pts, 1)
        return s

    @staticmethod
    def _make_pair_tree_tile(img: pygame.Surface) -> pygame.Surface:
        """两张 tree 左右并排，整体严格落在 TILE×TILE 内。"""
        dst = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        slot_w = TILE // 2
        ow, oh = max(1, img.get_width()), max(1, img.get_height())
        scale = min(slot_w / ow, TILE / oh)
        nw = max(1, int(ow * scale))
        nh = max(1, int(oh * scale))
        one = pygame.transform.scale(img, (nw, nh))
        y = TILE - nh  # 底对齐，像扎在草地上
        for i in range(2):
            x = i * slot_w + (slot_w - nw) // 2
            dst.blit(one, (x, y))
        return dst

    def _load_knight_and_ui(self) -> None:
        cw, ch = TILE, int(TILE * 64 / 48)
        self.knight = {
            "down": [
                pygame.transform.scale(load_img("knightstand.png"), (cw, ch)),
                pygame.transform.scale(load_img("knightwalk1.png"), (cw, ch)),
                pygame.transform.scale(load_img("knightwalk2.png"), (cw, ch)),
            ],
            "up": [
                pygame.transform.scale(load_img("knightwalkback1.png"), (cw, ch)),
                pygame.transform.scale(load_img("knightwalkback2.png"), (cw, ch)),
            ],
            "right": [
                pygame.transform.scale(load_img("knightwalkright1.png"), (cw, ch)),
                pygame.transform.scale(load_img("knightwalkright2.png"), (cw, ch)),
            ],
        }
        self.knight["left"] = [pygame.transform.flip(s, True, False) for s in self.knight["right"]]
        # 公主略小于骑士
        pw, ph = max(16, int(cw * 0.72)), max(20, int(ch * 0.72))
        self.princess = pygame.transform.scale(load_img("princess.png", key_bg=True), (pw, ph))
        self.princess = _key_outer_bg_surface(self.princess)
        vpet_sheet = self._load_vpet_sheet((cw, ch))
        allmate_sheet = self._load_allmate_sheet((cw, ch), fallback=vpet_sheet)
        self.players: dict[str, dict[str, list[pygame.Surface]]] = {
            "knight": self.knight,
            "vpet": vpet_sheet,
            "allmate": allmate_sheet,
        }
        self.start_bg = self._load_start_bg()
        self.start_logo1, self.start_logo2 = self._load_start_logos()
        self.window_frame = self._load_window_frame()
        self.text_frame = self._load_text_frame()

    @staticmethod
    def _sheet_from_still(still: pygame.Surface) -> dict[str, list[pygame.Surface]]:
        """单图角色：四向共用，轻微左右镜像区分朝向。"""
        flip = pygame.transform.flip(still, True, False)
        return {
            "down": [still, still, still],
            "up": [still, still],
            "right": [still, still],
            "left": [flip, flip],
        }

    def _load_vpet_sheet(self, size: tuple[int, int]) -> dict[str, list[pygame.Surface]]:
        """Vpet = aoba：桌宠主角色 walk/stand。优先已抠底的 png，其次旧 jpg。"""

        def pick(base: str) -> pygame.Surface | None:
            # png 已在导入时抠掉外圈绿底，直接用无需二次抠
            surf = _load_surface_any(
                _vpet_asset_candidates(base + ".png"), size, key_bg=False
            )
            if surf is None:
                surf = _load_surface_any(_vpet_asset_candidates(base + ".jpg"), size)
            return surf

        stand = pick("stand")
        front1 = pick("walkfront1")
        front2 = pick("walkfront2")
        back1 = pick("walkback1")
        back2 = pick("walkback2")
        left1 = pick("walkleft1")
        left2 = pick("walkleft2")
        if not stand:
            # 兼容旧 pet* 文件名
            stand = _load_surface_any(_vpet_asset_candidates("petstand.jpg"), size)
            front1 = _load_surface_any(_vpet_asset_candidates("petfront1.jpg"), size)
            front2 = _load_surface_any(_vpet_asset_candidates("petfront2.jpg"), size)
            back1 = _load_surface_any(_vpet_asset_candidates("petback1.jpg"), size)
            back2 = _load_surface_any(_vpet_asset_candidates("petback2.jpg"), size)
            left1 = _load_surface_any(_vpet_asset_candidates("petleft1.jpg"), size)
            left2 = _load_surface_any(_vpet_asset_candidates("petleft2.jpg"), size)
        if not stand:
            return dict(self.knight)
        down = [stand, front1 or stand, front2 or stand]
        up = [back1 or stand, back2 or stand]
        left = [left1 or stand, left2 or stand]
        right = [pygame.transform.flip(s, True, False) for s in left]
        return {"down": down, "up": up, "left": left, "right": right}

    def _load_allmate_sheet(
        self,
        size: tuple[int, int],
        fallback: dict[str, list[pygame.Surface]] | None = None,
    ) -> dict[str, list[pygame.Surface]]:
        """Allmate = ren：智能伴侣。优先已抠底 png，其次旧 jpg/minipet。"""

        def pick(base: str) -> pygame.Surface | None:
            surf = _load_surface_any(
                _allmate_asset_candidates(base + ".png"), size, key_bg=False
            )
            if surf is None:
                surf = _load_surface_any(_allmate_asset_candidates(base + ".jpg"), size)
            return surf

        stand = pick("petstand")
        front1 = pick("petfront1")
        front2 = pick("petfront2")
        back1 = pick("petback1")
        back2 = pick("petback2")
        left1 = pick("petleft1")
        left2 = pick("petleft2")
        if not stand:
            return dict(fallback or self.knight)
        down = [stand, front1 or stand, front2 or stand]
        up = [back1 or stand, back2 or stand]
        left = [left1 or stand, left2 or stand]
        right = [pygame.transform.flip(s, True, False) for s in left]
        return {"down": down, "up": up, "left": left, "right": right}

    def _load_text_frame(self) -> pygame.Surface:
        path = ASSETS / "text.png"
        if not path.exists():
            from process_assets import process_text_frame

            process_text_frame()
        if path.exists():
            return load_img("text.png")
        # 兜底：简易黑底白框
        fallback = pygame.Surface((240, 96), pygame.SRCALPHA)
        fallback.fill((0, 0, 0, 255))
        pygame.draw.rect(fallback, (255, 255, 255), fallback.get_rect(), 3)
        return fallback

    def _load_window_frame(self) -> pygame.Surface:
        path = ASSETS / "window_frame.png"
        if not path.exists():
            from process_assets import process_border

            process_border()
        raw = load_img("window_frame.png")
        return self._nine_slice(raw, WINDOW_W, WINDOW_H)

    @staticmethod
    def _nine_slice(src: pygame.Surface, tw: int, th: int) -> pygame.Surface:
        """九宫格拉伸，让边框贴满整个窗口外缘。"""
        sw, sh = src.get_size()
        c = max(8, min(sw, sh) // 5)
        out = pygame.Surface((tw, th), pygame.SRCALPHA)
        # 四角
        out.blit(src.subsurface((0, 0, c, c)), (0, 0))
        out.blit(src.subsurface((sw - c, 0, c, c)), (tw - c, 0))
        out.blit(src.subsurface((0, sh - c, c, c)), (0, th - c))
        out.blit(src.subsurface((sw - c, sh - c, c, c)), (tw - c, th - c))
        # 四边
        top = src.subsurface((c, 0, sw - 2 * c, c))
        bot = src.subsurface((c, sh - c, sw - 2 * c, c))
        left = src.subsurface((0, c, c, sh - 2 * c))
        right = src.subsurface((sw - c, c, c, sh - 2 * c))
        if tw > 2 * c:
            out.blit(pygame.transform.scale(top, (tw - 2 * c, c)), (c, 0))
            out.blit(pygame.transform.scale(bot, (tw - 2 * c, c)), (c, th - c))
        if th > 2 * c:
            out.blit(pygame.transform.scale(left, (c, th - 2 * c)), (0, c))
            out.blit(pygame.transform.scale(right, (c, th - 2 * c)), (tw - c, c))
        return out

    @staticmethod
    def _load_start_bg() -> tuple[int, int, int]:
        path = ASSETS / "startcolor.png"
        raw = ROOT / "startcolor.png"
        src = path if path.exists() else raw
        if src.exists():
            img = pygame.image.load(str(src)).convert()
            return img.get_at((0, 0))[:3]
        return (69, 104, 144)

    @staticmethod
    def _load_start_logos() -> tuple[pygame.Surface, pygame.Surface]:
        need = not (ASSETS / "startlogo1.png").exists() or not (ASSETS / "startlogo2.png").exists()
        if need:
            from process_assets import process_start_screen

            process_start_screen()
        l1 = load_img("startlogo1.png")
        l2 = load_img("startlogo2.png")
        # 给下方菜单预留空间：5 行 ×36 + 底提示 ≈ 220
        menu_reserve = 220
        max_w = int(SCREEN_W * 0.78)
        max_h = max(72, SCREEN_H - menu_reserve - 28)
        sw = max(l1.get_width(), l2.get_width(), 1)
        sh = max(l1.get_height(), l2.get_height(), 1)
        s = min(1.0, max_w / sw, max_h / sh)
        if s < 0.999:
            nw, nh = max(1, int(sw * s)), max(1, int(sh * s))
            l1 = pygame.transform.smoothscale(l1, (max(1, int(l1.get_width() * s)), max(1, int(l1.get_height() * s))))
            l2 = pygame.transform.smoothscale(l2, (max(1, int(l2.get_width() * s)), max(1, int(l2.get_height() * s))))
            # 对齐到同一画布尺寸，叠合更稳
            canvas_w, canvas_h = nw, nh
            c1 = pygame.Surface((canvas_w, canvas_h), pygame.SRCALPHA)
            c2 = pygame.Surface((canvas_w, canvas_h), pygame.SRCALPHA)
            c1.blit(l1, ((canvas_w - l1.get_width()) // 2, (canvas_h - l1.get_height()) // 2))
            c2.blit(l2, ((canvas_w - l2.get_width()) // 2, (canvas_h - l2.get_height()) // 2))
            l1, l2 = c1, c2
        return l1, l2


def blank_grid(w: int, h: int, fill: int) -> list[list[int]]:
    return [[fill for _ in range(w)] for _ in range(h)]


def border_wall(grid: list[list[int]], wall: int = ROCK) -> None:
    """外圈隔断（默认岩石）。"""
    h, w = len(grid), len(grid[0])
    for x in range(w):
        grid[0][x] = wall
        grid[h - 1][x] = wall
    for y in range(h):
        grid[y][0] = wall
        grid[y][w - 1] = wall


def rock_ring_around_content(grid: list[list[int]], wall: int = ROCK) -> tuple[int, int, int, int]:
    """
    石头按内容**轮廓**包边（非正方形包围盒）：
    在 EMPTY 且四邻接有已绘制内容的格子上放岩石。
    全空白则围整张地图边框。返回内容包围盒 (x0,y0,x1,y1) 供提示。
    """
    h, w = len(grid), len(grid[0])
    content = [[False] * w for _ in range(h)]
    xs: list[int] = []
    ys: list[int] = []
    for y in range(h):
        for x in range(w):
            if grid[y][x] != EMPTY:
                content[y][x] = True
                xs.append(x)
                ys.append(y)
    if not xs:
        border_wall(grid, wall)
        return 0, 0, w - 1, h - 1

    place: list[tuple[int, int]] = []
    for y in range(h):
        for x in range(w):
            if content[y][x] or grid[y][x] != EMPTY:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and content[ny][nx]:
                    place.append((x, y))
                    break
    for x, y in place:
        grid[y][x] = wall
    return min(xs), min(ys), max(xs), max(ys)


def border_brick(grid: list[list[int]]) -> None:
    """兼容旧名：外圈改为岩石隔断。"""
    border_wall(grid, ROCK)


def map_has_layer_portals(data: dict) -> bool:
    """地图是否已有楼梯/洞窟（出现后编辑器才显示「地下」层页面）。"""
    if data.get("stairs") or data.get("caves"):
        return True
    for key in ("surface", "underground", "tiles"):
        grid = data.get(key)
        if not isinstance(grid, list):
            continue
        for row in grid:
            for t in row:
                if t in LAYER_PORTALS:
                    return True
    return False


def _map_has_portal_pairs(data: dict) -> bool:
    """新图：楼梯任意层，或同格双层洞窟（门户）。旧图地下满铺 CAVE 不当门户。"""
    surf = data.get("surface") or data.get("tiles")
    under = data.get("underground")
    if not isinstance(surf, list) or not surf:
        return False
    for y, row in enumerate(surf):
        for x, t in enumerate(row):
            if t == STAIRS:
                return True
            if t == CAVE and isinstance(under, list) and under and under[y][x] == CAVE:
                return True
    if isinstance(under, list):
        for row in under:
            for t in row:
                if t == STAIRS:
                    return True
    return False


def repair_layer_portals(data: dict) -> dict:
    """楼梯与洞窟并存：同格双层对齐全为同一种门户。"""
    surf = data.get("surface")
    under = data.get("underground")
    if not isinstance(surf, list) or not isinstance(under, list) or not surf or not under:
        return data
    h = min(len(surf), len(under))
    stairs: list[list[int]] = []
    caves: list[list[int]] = []
    for y in range(h):
        w = min(len(surf[y]), len(under[y]))
        for x in range(w):
            a, b = surf[y][x], under[y][x]
            if a in LAYER_PORTALS or b in LAYER_PORTALS:
                # 优先跟地面，其次地下；楼梯与洞窟都可切换层
                kind = a if a in LAYER_PORTALS else b
                if b in LAYER_PORTALS and a not in LAYER_PORTALS:
                    kind = b
                elif a in LAYER_PORTALS and b in LAYER_PORTALS and a != b:
                    kind = a  # 同格冲突时以地面为准
                surf[y][x] = kind
                under[y][x] = kind
                if kind == STAIRS:
                    stairs.append([x, y])
                else:
                    caves.append([x, y])
    data["stairs"] = stairs
    data["caves"] = caves
    return data


def normalize_map_tiles(data: dict) -> dict:
    """地下：砖地=背景、岩石=隔断；旧图 BRICK 墙→ROCK，非门户 CAVE 地→BRICK。"""
    if data.get("tile_schema") == 2:
        return ensure_ground_layers(repair_layer_portals(data))
    # 已有楼梯/成对洞窟时不再做旧迁移（否则会清掉地下洞窟并堵死砖道）
    if _map_has_portal_pairs(data):
        data["tile_schema"] = 2
        return ensure_ground_layers(repair_layer_portals(data))
    surf = data.get("surface") or data.get("tiles")
    for key in ("surface", "underground", "tiles"):
        grid = data.get(key)
        if not isinstance(grid, list) or not grid:
            continue
        under = key == "underground"
        for y, row in enumerate(grid):
            for i, t in enumerate(row):
                if under:
                    if t == CAVE:
                        # 仅旧岩地：地面同格不是门户才改成砖
                        if (
                            isinstance(surf, list)
                            and y < len(surf)
                            and i < len(surf[y])
                            and surf[y][i] in LAYER_PORTALS
                        ):
                            continue
                        row[i] = BRICK
                    elif t == BRICK:
                        row[i] = ROCK
                elif t == BRICK:
                    row[i] = ROCK
    data["tile_schema"] = 2
    return ensure_ground_layers(repair_layer_portals(data))


def carve_path(grid: list[list[int]], start: tuple[int, int], goal: tuple[int, int], rng: random.Random, floor: int) -> None:
    h, w = len(grid), len(grid[0])
    x, y = start
    gx, gy = goal
    for _ in range(w * h):
        if (x, y) == (gx, gy):
            break
        if abs(gx - x) > abs(gy - y):
            step = (1 if gx > x else -1, 0)
        elif gy != y:
            step = (0, 1 if gy > y else -1)
        else:
            step = (1 if gx > x else -1, 0)
        if rng.random() < 0.4:
            step = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        nx, ny = x + step[0], y + step[1]
        if 1 <= nx < w - 1 and 1 <= ny < h - 1:
            cell = grid[ny][nx]
            if cell == HOUSE:
                step = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
                nx, ny = x + step[0], y + step[1]
                if not (1 <= nx < w - 1 and 1 <= ny < h - 1):
                    continue
                cell = grid[ny][nx]
            if cell in SOLID and cell != HOUSE:
                grid[ny][nx] = floor
            x, y = nx, ny


def stamp_blob(
    grid: list[list[int]],
    cx: int,
    cy: int,
    radius: int,
    tile: int,
    rng: random.Random,
    *,
    density: float = 0.88,
    only_on: set[int] | None = None,
) -> None:
    """在圆心附近连成一片地块。"""
    h, w = len(grid), len(grid[0])
    r2 = radius * radius
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx * dx + dy * dy > r2:
                continue
            if rng.random() > density:
                continue
            gx, gy = cx + dx, cy + dy
            if not (1 <= gx < w - 1 and 1 <= gy < h - 1):
                continue
            if only_on is not None and grid[gy][gx] not in only_on:
                continue
            if grid[gy][gx] == HOUSE:
                continue
            grid[gy][gx] = tile


def generate_level(level_idx: int, seed: int | None = None) -> dict:
    cfg = LEVEL_DEFS[level_idx]
    # 优先调用方传入；否则用关卡表固定 seed（战役布局稳定）；都没有才真随机
    used = seed if seed is not None else cfg.get("seed")
    if used is None:
        used = random.randint(0, 10**9)
    used = int(used)
    rng = random.Random(used)
    w, h = cfg["w"], cfg["h"]
    r_lo, r_hi = cfg.get("cluster_r", (2, 5))

    surface = blank_grid(w, h, GRASS)
    border_wall(surface, ROCK)

    for _ in range(cfg.get("land_blobs", 14)):
        cx, cy = rng.randint(3, w - 4), rng.randint(3, h - 4)
        stamp_blob(surface, cx, cy, rng.randint(r_lo + 1, r_hi + 2), LAND, rng, density=0.9)

    for _ in range(cfg["lakes"]):
        cx, cy = rng.randint(5, w - 6), rng.randint(5, h - 6)
        stamp_blob(
            surface,
            cx,
            cy,
            rng.randint(r_lo + 1, r_hi + 1),
            WATER,
            rng,
            density=0.86,
            only_on={GRASS, LAND},
        )

    for _ in range(cfg["obstacles"]):
        cx, cy = rng.randint(2, w - 3), rng.randint(2, h - 3)
        kind = rng.choice([ROCK, OBSTACLE, ROCK, OBSTACLE, ROCK])
        stamp_blob(
            surface,
            cx,
            cy,
            rng.randint(r_lo, max(r_lo, r_hi - 1)),
            kind,
            rng,
            density=0.8,
            only_on={GRASS, LAND},
        )

    # 可走森林（树木叠层）
    for _ in range(cfg.get("forests", 8)):
        cx, cy = rng.randint(2, w - 3), rng.randint(2, h - 3)
        stamp_blob(
            surface,
            cx,
            cy,
            rng.randint(r_lo, r_hi),
            TREE,
            rng,
            density=0.78,
            only_on={GRASS, LAND},
        )

    # 景区山峦（挡路）
    for _ in range(cfg.get("mountains", 3)):
        cx, cy = rng.randint(3, w - 4), rng.randint(3, h - 4)
        stamp_blob(
            surface,
            cx,
            cy,
            rng.randint(1, max(2, r_lo)),
            MOUNTAIN,
            rng,
            density=0.7,
            only_on={GRASS, LAND},
        )

    # 出发点：放大房屋在左下，骑士站在屋前
    hx, hy = 4, h - 5
    for dy in range(-1, 3):
        for dx in range(-1, 2):
            gx, gy = hx + dx, hy + dy
            if 1 <= gx < w - 1 and 1 <= gy < h - 1:
                surface[gy][gx] = LAND if dy >= 1 else GRASS
    surface[hy][hx] = HOUSE
    start = (hx, hy + 1)
    surface[start[1]][start[0]] = GRASS
    for dx in (-1, 0, 1):
        for dy in (1, 2):
            gx, gy = hx + dx, hy + dy
            if 1 <= gx < w - 1 and 1 <= gy < h - 1 and (gx, gy) != (hx, hy):
                if surface[gy][gx] in SOLID:
                    surface[gy][gx] = GRASS

    under = blank_grid(w, h, ROCK)
    border_wall(under, ROCK)
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if rng.random() < cfg["ug_fill"]:
                under[y][x] = BRICK
    for _ in range(cfg.get("ug_corridors", 20)):
        x, y = rng.randint(1, w - 2), rng.randint(1, h - 2)
        length = rng.randint(10, 22)
        dx, dy = rng.choice([(1, 0), (0, 1), (-1, 0), (0, -1)])
        thick = rng.choice([1, 1, 2])
        for _step in range(length):
            for ox in range(-thick + 1, thick):
                for oy in range(-thick + 1, thick):
                    nx, ny = x + ox, y + oy
                    if 1 <= nx < w - 1 and 1 <= ny < h - 1:
                        under[ny][nx] = BRICK
            if rng.random() < 0.18:
                dx, dy = rng.choice([(1, 0), (0, 1), (-1, 0), (0, -1)])
            nx, ny = x + dx, y + dy
            if 1 <= nx < w - 1 and 1 <= ny < h - 1:
                x, y = nx, ny

    stairs: list[list[int]] = []
    for _ in range(cfg["stairs"]):
        for _try in range(120):
            x, y = rng.randint(3, w - 4), rng.randint(3, h - 4)
            if abs(x - hx) + abs(y - hy) < 6:
                continue
            if surface[y][x] in (GRASS, LAND, TREE) and under[y][x] in (BRICK, ROCK):
                surface[y][x] = STAIRS
                under[y][x] = STAIRS
                stairs.append([x, y])
                break

    # 洞窟入口：地面 ↔ 地下（与楼梯同类）
    caves: list[list[int]] = []
    for _ in range(cfg.get("caves", 2)):
        for _try in range(120):
            x, y = rng.randint(3, w - 4), rng.randint(3, h - 4)
            if abs(x - hx) + abs(y - hy) < 6:
                continue
            if surface[y][x] in (GRASS, LAND, TREE) and under[y][x] in (BRICK, ROCK):
                if [x, y] in stairs:
                    continue
                surface[y][x] = CAVE
                under[y][x] = CAVE
                caves.append([x, y])
                break

    if cfg["princess"]:
        goal_layer = "underground"
        goal = None
        for y in range(1, h - 1):
            for x in range(w - 2, 0, -1):
                if under[y][x] == BRICK:
                    goal = (x, y)
                    under[y][x] = BRICK
                    break
            if goal:
                break
        if not goal:
            goal = (w - 3, 2)
            under[goal[1]][goal[0]] = BRICK
    else:
        goal_layer = "underground"
        goal = None
        for y in range(1, h // 2):
            for x in range(w - 2, w // 2, -1):
                if under[y][x] == BRICK:
                    goal = (x, y)
                    under[y][x] = GATE
                    break
            if goal:
                break
        if not goal:
            goal = (w - 3, 2)
            under[goal[1]][goal[0]] = GATE

    if stairs:
        sx, sy = stairs[0]
        carve_path(surface, start, (sx, sy), rng, GRASS)
        carve_path(under, (sx, sy), goal, rng, BRICK)
        for i in range(1, len(stairs)):
            carve_path(under, tuple(stairs[0]), tuple(stairs[i]), rng, BRICK)
            carve_path(surface, tuple(stairs[0]), tuple(stairs[i]), rng, GRASS)
        for cx, cy in caves:
            carve_path(surface, start, (cx, cy), rng, GRASS)
            carve_path(under, (cx, cy), goal, rng, BRICK)
    else:
        sx, sy = max(2, start[0] + 2), max(2, start[1] - 4)
        surface[sy][sx] = STAIRS
        under[sy][sx] = STAIRS
        stairs = [[sx, sy]]
        carve_path(surface, start, (sx, sy), rng, GRASS)
        carve_path(under, (sx, sy), goal, rng, BRICK)
        for cx, cy in caves:
            carve_path(surface, start, (cx, cy), rng, GRASS)
            carve_path(under, (cx, cy), goal, rng, BRICK)

    # carve_path 可能覆盖门户，重新钉回
    for sx, sy in stairs:
        surface[sy][sx] = STAIRS
        under[sy][sx] = STAIRS
    for cx, cy in caves:
        surface[cy][cx] = CAVE
        under[cy][cx] = CAVE

    surface[hy][hx] = HOUSE
    surface[start[1]][start[0]] = GRASS

    for _ in range(cfg["treasures"]):
        if rng.random() < 0.5:
            x, y = rng.randint(1, w - 2), rng.randint(1, h - 2)
            if surface[y][x] in (GRASS, LAND, TREE) and (x, y) != start:
                surface[y][x] = TREASURE
        else:
            x, y = rng.randint(1, w - 2), rng.randint(1, h - 2)
            if under[y][x] == BRICK:
                under[y][x] = TREASURE

    # 可放置陷阱：尖刺 / 陷坑（避开起点、房屋、门户、宝箱）
    for _ in range(int(cfg.get("traps", 0))):
        trap = TRAP_SPIKE if rng.random() < 0.55 else TRAP_PIT
        if rng.random() < 0.55:
            x, y = rng.randint(1, w - 2), rng.randint(1, h - 2)
            if (
                surface[y][x] in (GRASS, LAND)
                and (x, y) != start
                and (x, y) != (hx, hy)
            ):
                surface[y][x] = trap
        else:
            x, y = rng.randint(1, w - 2), rng.randint(1, h - 2)
            if under[y][x] == BRICK:
                under[y][x] = trap

    return {
        "level": level_idx,
        "name": cfg["name"],
        "width": w,
        "height": h,
        "surface": surface,
        "underground": under,
        "start": list(start),
        "goal": list(goal),
        "goal_layer": goal_layer,
        "stairs": stairs,
        "caves": caves,
        "princess": cfg["princess"],
        "seed": used,
        "tile_schema": 2,
        "house": [hx, hy],
    }



def map_size(data: dict) -> tuple[int, int]:
    return int(data["width"]), int(data["height"])


def layer_grid(data: dict, layer: str) -> list[list[int]]:
    return data["underground"] if layer == "underground" else data["surface"]


def ground_key_for_layer(layer: str) -> str:
    return "ground_underground" if layer == "underground" else "ground_surface"


def default_ground_for_layer(layer: str) -> int:
    return BRICK if layer == "underground" else GRASS


def ensure_ground_layers(data: dict) -> dict:
    """保证每层有 ground_*：背景铺地；地物格保留其下的草/土/水/石/砖。"""
    for layer in ("surface", "underground"):
        grid = data.get(layer)
        if not isinstance(grid, list) or not grid:
            continue
        gkey = ground_key_for_layer(layer)
        default = default_ground_for_layer(layer)
        ground = data.get(gkey)
        h = len(grid)
        w = len(grid[0]) if grid else 0
        bad = (
            not isinstance(ground, list)
            or len(ground) != h
            or (h > 0 and (not ground or len(ground[0]) != w))
        )
        if bad:
            new_g: list[list[int]] = []
            for row in grid:
                grow: list[int] = []
                for t in row:
                    ti = int(t)
                    if ti in BACKGROUND_TILES:
                        grow.append(ti)
                    elif ti == EMPTY:
                        grow.append(EMPTY)
                    else:
                        grow.append(default)
                new_g.append(grow)
            data[gkey] = new_g
        else:
            assert isinstance(ground, list)
            for y, row in enumerate(grid):
                for x, t in enumerate(row):
                    ti = int(t)
                    if ti in BACKGROUND_TILES:
                        ground[y][x] = ti
                    elif ti == EMPTY:
                        ground[y][x] = EMPTY
                    elif int(ground[y][x]) not in BACKGROUND_TILES:
                        ground[y][x] = default
    return data


def layer_ground(data: dict, layer: str) -> list[list[int]]:
    ensure_ground_layers(data)
    return data[ground_key_for_layer(layer)]


def map_center_tile(data: dict) -> tuple[int, int]:
    w, h = map_size(data)
    return max(0, w // 2), max(0, h // 2)


def has_start(data: dict) -> bool:
    """地图是否已显式设置合法起点。"""
    w, h = map_size(data)
    raw = data.get("start")
    if not isinstance(raw, (list, tuple)) or len(raw) < 2:
        return False
    try:
        tx, ty = int(raw[0]), int(raw[1])
    except (TypeError, ValueError):
        return False
    return 0 <= tx < w and 0 <= ty < h


def resolve_start(data: dict) -> tuple[int, int]:
    """出生/镜头锚点：有起点用起点，否则用地图中心；若落在水/墙等不可走格，自动找最近可走格。"""
    if has_start(data):
        raw = data["start"]
        tx, ty = int(raw[0]), int(raw[1])
    else:
        tx, ty = map_center_tile(data)
    return ensure_walkable_spawn(data, tx, ty)


def _layer_grid(data: dict, layer: str = "surface") -> list[list[int]]:
    if layer == "underground" and "underground" in data:
        return data["underground"]
    if "surface" in data:
        return data["surface"]
    return data.get("tiles") or []


def tile_walkable(data: dict, tx: int, ty: int, *, layer: str = "surface") -> bool:
    grid = _layer_grid(data, layer)
    if not grid:
        return True
    h, w = len(grid), len(grid[0]) if grid else 0
    if not (0 <= tx < w and 0 <= ty < h):
        return False
    return int(grid[ty][tx]) not in SOLID


def ensure_walkable_spawn(data: dict, tx: int, ty: int, *, layer: str = "surface") -> tuple[int, int]:
    """若 (tx,ty) 不可走，螺旋向外找最近可走格；找不到则退回原坐标。"""
    if tile_walkable(data, tx, ty, layer=layer):
        return tx, ty
    grid = _layer_grid(data, layer)
    if not grid:
        return tx, ty
    h, w = len(grid), len(grid[0])
    for radius in range(1, max(w, h) + 1):
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if max(abs(dx), abs(dy)) != radius:
                    continue
                nx, ny = tx + dx, ty + dy
                if tile_walkable(data, nx, ny, layer=layer):
                    return nx, ny
    # 全图扫描兜底
    for y in range(h):
        for x in range(w):
            if tile_walkable(data, x, y, layer=layer):
                return x, y
    return tx, ty


class Camera:
    def __init__(self) -> None:
        self.x = 0.0
        self.y = 0.0

    def clamp(self, world_w: int, world_h: int) -> None:
        max_x = max(0, world_w * TILE - VIEW_W)
        max_y = max(0, world_h * TILE - VIEW_H)
        self.x = max(0.0, min(self.x, float(max_x)))
        self.y = max(0.0, min(self.y, float(max_y)))

    def follow(self, target_x: float, target_y: float, world_w: int, world_h: int) -> None:
        self.x = target_x - VIEW_W / 2
        self.y = target_y - VIEW_H / 2
        self.clamp(world_w, world_h)

    def apply(self, wx: float, wy: float) -> tuple[int, int]:
        return int(wx - self.x), int(wy - self.y)


class Knight:
    SPEED = 120

    def __init__(self, assets: Assets, tile_xy: tuple[int, int], *, kind: str = "knight") -> None:
        self.assets = assets
        self.kind = kind if kind in PLAYER_KINDS else "knight"
        self.x = tile_xy[0] * TILE + TILE // 2
        self.y = tile_xy[1] * TILE + TILE // 2
        self.dir = "down"
        self.frame = 0
        self.anim_t = 0.0
        self.moving = False
        self.hw = max(8, TILE // 3)
        self.hh = max(6, TILE // 4)

    def set_kind(self, kind: str) -> None:
        if kind in PLAYER_KINDS:
            self.kind = kind

    def _sheet(self) -> dict[str, list[pygame.Surface]]:
        players = getattr(self.assets, "players", None) or {}
        return players.get(self.kind) or self.assets.knight

    def update(
        self,
        dt: float,
        keys,
        grid: list[list[int]],
        mw: int,
        mh: int,
        *,
        speed_mult: float = 1.0,
    ) -> None:
        vx = vy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            vx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            vx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            vy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            vy += 1

        self.moving = vx != 0 or vy != 0
        if not self.moving:
            self.frame = 0
            return

        if abs(vx) > abs(vy):
            self.dir = "right" if vx > 0 else "left"
        else:
            self.dir = "down" if vy > 0 else "up"

        length = (vx * vx + vy * vy) ** 0.5
        vx, vy = vx / length, vy / length
        spd = self.SPEED * max(0.4, float(speed_mult))
        self._try_move(vx * spd * dt, 0, grid, mw, mh)
        self._try_move(0, vy * spd * dt, grid, mw, mh)

        self.anim_t += dt
        if self.anim_t >= 0.16:
            self.anim_t = 0
            self.frame = (self.frame + 1) % 2

    def _try_move(self, dx: float, dy: float, grid: list[list[int]], mw: int, mh: int) -> None:
        nx, ny = self.x + dx, self.y + dy
        test = pygame.Rect(int(nx) - self.hw, int(ny) - self.hh, self.hw * 2, self.hh * 2)
        if self._blocked(test, grid, mw, mh):
            return
        self.x, self.y = nx, ny

    def _blocked(self, rect: pygame.Rect, grid: list[list[int]], mw: int, mh: int) -> bool:
        for ty in range(max(0, rect.top // TILE), min(mh, rect.bottom // TILE + 1)):
            for tx in range(max(0, rect.left // TILE), min(mw, rect.right // TILE + 1)):
                if grid[ty][tx] in SOLID:
                    cell = pygame.Rect(tx * TILE, ty * TILE, TILE, TILE)
                    if rect.colliderect(cell.inflate(-6, -6)):
                        return True
        return False

    def draw(self, surf: pygame.Surface, cam: Camera, *, flash: bool = False) -> None:
        frames = self._sheet()[self.dir]
        if self.dir == "down":
            img = frames[0] if not self.moving else frames[1 + self.frame % max(1, len(frames) - 1)]
        else:
            img = frames[self.frame % len(frames)]
        if flash:
            img = img.copy()
            img.fill((255, 240, 120, 90), special_flags=pygame.BLEND_RGBA_ADD)
        sx, sy = cam.apply(self.x - img.get_width() // 2, self.y - img.get_height() + 8)
        surf.blit(img, (sx, sy))

    def tile_pos(self) -> tuple[int, int]:
        return int(self.x) // TILE, int(self.y) // TILE

    def facing_tile(self) -> tuple[int, int]:
        tx, ty = self.tile_pos()
        if self.dir == "up":
            return tx, ty - 1
        if self.dir == "down":
            return tx, ty + 1
        if self.dir == "left":
            return tx - 1, ty
        return tx + 1, ty

    def place_on_tile(self, tx: int, ty: int) -> None:
        self.x = tx * TILE + TILE // 2
        self.y = ty * TILE + TILE // 2


def ensure_assets() -> None:
    if not ASSETS.exists() or not (ASSETS / "knightstand.png").exists():
        print("正在处理素材…")
        from process_assets import main as process_main

        process_main()
    if not (ASSETS / "startlogo1.png").exists() or not (ASSETS / "startlogo2.png").exists():
        from process_assets import process_start_screen

        process_start_screen()
    if not (ASSETS / "window_frame.png").exists():
        from process_assets import process_border

        process_border()
    ensure_extra_tiles()


class Game:
    @staticmethod
    def _load_font(size: int) -> pygame.font.Font:
        for path in (
            Path(r"C:\Windows\Fonts\msyh.ttc"),
            Path(r"C:\Windows\Fonts\simhei.ttf"),
            Path(r"C:\Windows\Fonts\simsun.ttc"),
        ):
            if path.exists():
                try:
                    return pygame.font.Font(str(path), size)
                except Exception:
                    continue
        return pygame.font.Font(None, size)

    @staticmethod
    def _load_pixel_font(size: int) -> pygame.font.Font:
        """标题菜单用像素字体（英文最佳）；缺失时回退系统字体。"""
        candidates = (
            ASSETS / "fonts" / "PressStart2P-Regular.ttf",
            ASSETS / "PressStart2P-Regular.ttf",
            ROOT / "assets" / "fonts" / "PressStart2P-Regular.ttf",
        )
        for path in candidates:
            if path.exists():
                try:
                    return pygame.font.Font(str(path), size)
                except Exception:
                    continue
        return Game._load_font(size)

    @staticmethod
    def _resolve_audio(names: tuple[str, ...]) -> Path | None:
        for name in names:
            for path in (ASSETS / name, ROOT / name, ASSETS / "audio" / name):
                if path.exists():
                    return path
        return None

    def __init__(self) -> None:
        ensure_assets()
        MAPS_DIR.mkdir(exist_ok=True)
        SAVES_DIR.mkdir(exist_ok=True)
        pygame.init()
        try:
            # mp3 立体声；失败再退回单声道
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        except pygame.error:
            try:
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            except pygame.error:
                pass
        pygame.display.set_caption("Silent Oath")
        self.window = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        # 游戏内容画在内层；外边框包住整块画面
        self.screen = pygame.Surface((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        self.font = self._load_font(16)
        self.font_sm = self._load_font(13)
        self.font_lg = self._load_font(22)
        # Start 页菜单：像素风（Press Start 2P）
        self.font_pixel = self._load_pixel_font(14)
        self.font_pixel_sm = self._load_pixel_font(10)
        self.assets = Assets()
        self.camera = Camera()
        self.state = "menu"
        self.menu_idx = 0
        # 英文菜单项 + 右侧按键提示
        self.menu_items = [
            ("START", "ENTER"),
            ("LOAD SAVE", "C"),
            ("MAP EDITOR", "E"),
            ("LOAD DIY MAP", "L"),
            ("QUIT", "ESC"),
        ]
        self.map_data: dict | None = None
        self.knight: Knight | None = None
        self.layer = "surface"
        self.level_idx = 0
        self.treasures = 0
        self.total_treasures = 0
        self.hp = RPG_MAX_HP
        self.max_hp = RPG_MAX_HP
        self.chest_event: dict | None = None
        self.hazard_cd = 0.0
        self._last_hazard_tile: tuple[str, int, int] | None = None
        self.map_trap_cd = 0.0
        self._last_map_trap_tile: tuple[str, int, int] | None = None
        self.revealed_traps: set[tuple[str, int, int]] = set()
        self.message = ""
        self.message_t = 0.0
        self.bag_open = False
        self.bag_idx = 0
        self.coins = 0
        self._wallet_earned = 0
        self.pickups: list[dict] = []
        self.star_t = 0.0
        self.speed_t = 0.0
        self.pickup_bob = 0.0
        self.stairs_cd = 0.0
        self.layer_flash = 0.0  # 1→0：地上地下切换黑屏
        self.portal_stand_lock: tuple[str, int, int] | None = None
        self.brush = GRASS
        self.edit_mode = "tile"
        self.edit_layer = "surface"
        self.custom_maps = self._list_maps()
        self.campaign = True
        self.dialog: dict | None = None  # {title, body, hold?}
        self.nearby_hint = ""
        self.save_picker_idx = 0
        self.map_picker_idx = 0
        self.picker_mode = ""  # "save" | "map_editor" | "map_play" | ""
        self.edit_map_path: Path | None = None
        self.picker_delete_pending: Path | None = None
        self.editor_delete_pending = False
        self.editor_panning = False
        self.editor_pan_origin = (0, 0, 0.0, 0.0)
        self.paint_drag = False
        self.paint_cells: list[int] = [0] * (PIXEL_PAINT_SIZE * PIXEL_PAINT_SIZE)
        self.paint_brush = 1
        self.paint_colors: list[tuple[int, int, int] | None] = list(PIXEL_PAINT_COLORS)
        self.paint_return_state = "editor"
        self.paint_delete_pending = False
        self.paint_naming = False
        self.paint_name = ""
        self.paint_gallery: list[dict] = []
        self.paint_gallery_idx = 0
        self.paint_edit_id: str | None = None
        # 操控角色：knight / aoba(Vpet) / ren(Allmate)（加载后选角；游玩中也可按 C 切换）
        self.player_kind = "knight"
        self.pending_play: dict | None = None  # {data, campaign} 选角后再开局
        self.kind_select_idx = 0
        self.reward_sfx = self._make_reward_sfx()
        self.coin_sfx = self._make_coin_sfx()
        # BGM：点 START 播 startmusic，结束后循环 music
        self._bgm_phase: str | None = None  # None | "start" | "loop"
        self.music_volume = MUSIC_DEFAULT_VOLUME
        self._apply_music_volume()
        # 开场升起：两 logo 缓缓汇合，再淡入菜单
        self.intro_t = 0.0
        self.intro_dur = 6.2
        self.logo1_delay = 0.0
        self.logo2_delay = 1.15
        self.intro_done = False
        self.menu_fade = 0.0
        self.menu_fade_speed = 0.55  # 菜单淡入更慢
        self.logo1_y = 0.0
        self.logo2_y = 0.0
        self._reset_logo_anim_targets()
        # 开场剧情（start 页之前）；内容可替换，显示时套 *「…」
        self.type_sfx = self._make_type_sfx()
        self.prologue_lines = [
            "请救救我……",
            "谁来救救我……",
            "谁能，把我从这里救出去……",
        ]
        self.prologue_idx = 0
        self.prologue_chars = 0
        self.prologue_timer = 0.0
        self.prologue_hold = 0.0
        self.prologue_char_delay = 0.12  # 打字稍慢
        self.prologue_line_hold = 1.8
        self.prologue_fade_out = 0.0
        self.prologue_done_fade = False
        self.prologue_fade_dur = 1.4
        self.state = "prologue"

    def _list_maps(self) -> list[Path]:
        return sorted(MAPS_DIR.glob("*.json"))

    def _list_saves(self) -> list[Path]:
        return sorted(SAVES_DIR.glob("slot*.json"))

    def toast(self, text: str, sec: float = 2.2) -> None:
        self.message = text
        self.message_t = sec

    def uses_durability(self) -> bool:
        """仅战役冒险使用耐久；DIY 试玩 / 编辑器不显示、不结算耐久。"""
        if self.state in ("editor", "paint", "menu", "picker"):
            return False
        if self.state == "kind_select" and self.pending_play is not None:
            return bool(self.pending_play.get("campaign"))
        return bool(self.campaign)

    def food_bag_count(self) -> int:
        inv = load_shared_food_inventory()
        return sum(int(inv.get(fid, 0) or 0) for fid in RPG_FOOD_IDS)

    def change_hp(self, delta: int, *, reason: str = "") -> None:
        if not self.uses_durability():
            return
        before = int(self.hp)
        self.hp = max(0, min(int(self.max_hp), before + int(delta)))
        if reason:
            sign = "+" if delta > 0 else ""
            self.toast(f"{reason}（耐久 {sign}{delta} → {self.hp}/{self.max_hp}）", 2.8)
        if self.hp <= 0:
            self._on_hp_empty()

    def _on_hp_empty(self) -> None:
        """耐久耗尽：回到本关起点并恢复一半血。"""
        if not self.map_data or not self.knight:
            self.hp = max(1, self.max_hp // 2)
            return
        sx, sy = resolve_start(self.map_data)
        self.knight.x = sx * TILE + TILE // 2
        self.knight.y = sy * TILE + TILE // 2
        self.layer = "surface"
        self.hp = max(20, self.max_hp // 2)
        self.chest_event = None
        self.bag_open = False
        self.star_t = 0.0
        self.speed_t = 0.0
        self.toast("耐久耗尽…勉强爬回出发点，恢复了一半耐久", 3.5)

    def change_food(self, delta: int) -> str:
        """随机增减一份桌宠食物；返回说明文案。"""
        if delta > 0:
            fid = random.choice(RPG_FOOD_IDS)
            n, label = save_shared_food_delta(fid, 1)
            return f"获得{label}×1（库存 {n}）"
        # 扣食物：优先扣已有的
        inv = load_shared_food_inventory()
        owned = [fid for fid in RPG_FOOD_IDS if inv.get(fid, 0) > 0]
        if not owned:
            return "背包里没有食物可扣"
        fid = random.choice(owned)
        n, label = save_shared_food_delta(fid, -1)
        return f"失去{label}×1（库存 {n}）"

    def bag_food_rows(self) -> list[tuple[str, str, int, int]]:
        """(fid, label, count, heal)"""
        inv = load_shared_food_inventory()
        rows: list[tuple[str, str, int, int]] = []
        for fid in RPG_FOOD_IDS:
            n = int(inv.get(fid, 0) or 0)
            rows.append((fid, RPG_FOOD_LABELS.get(fid, fid), n, int(RPG_FOOD_HEAL.get(fid, 10))))
        return rows

    def toggle_bag(self) -> None:
        if self.bag_open:
            self.bag_open = False
            return
        if self.chest_event or self.dialog:
            return
        self.bag_open = True
        rows = self.bag_food_rows()
        # 默认选中第一份有货的食物
        self.bag_idx = 0
        for i, (_fid, _lab, n, _h) in enumerate(rows):
            if n > 0:
                self.bag_idx = i
                break
        self.toast("打开背包 · ↑↓选择 · Enter吃 · I/Esc关闭", 2.0)

    def eat_bag_food(self, fid: str | None = None) -> None:
        if not self.uses_durability():
            self.toast("DIY 模式没有耐久，无需吃食物")
            return
        rows = self.bag_food_rows()
        if fid is None:
            if not rows:
                self.toast("背包是空的")
                return
            self.bag_idx = max(0, min(self.bag_idx, len(rows) - 1))
            fid = rows[self.bag_idx][0]
        inv = load_shared_food_inventory()
        if int(inv.get(fid, 0) or 0) <= 0:
            self.toast(f"{RPG_FOOD_LABELS.get(fid, fid)}已经没有了")
            return
        if self.hp >= self.max_hp:
            self.toast("耐久已满，先冒险再吃吧")
            return
        heal = int(RPG_FOOD_HEAL.get(fid, 10))
        n, label = save_shared_food_delta(fid, -1)
        before = int(self.hp)
        self.hp = min(self.max_hp, before + heal)
        gained = self.hp - before
        self._play_reward_sfx()
        self.toast(f"吃下{label}！耐久+{gained}（{self.hp}/{self.max_hp}）· 剩{n}", 3.0)

    def handle_bag_key(self, key: int) -> None:
        if key in (pygame.K_ESCAPE, pygame.K_i, pygame.K_b):
            self.bag_open = False
            return
        rows = self.bag_food_rows()
        if not rows:
            return
        if key in (pygame.K_UP, pygame.K_w):
            self.bag_idx = (self.bag_idx - 1) % len(rows)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.bag_idx = (self.bag_idx + 1) % len(rows)
        elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
            self.eat_bag_food()
        elif key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8):
            idx = {
                pygame.K_1: 0,
                pygame.K_2: 1,
                pygame.K_3: 2,
                pygame.K_4: 3,
                pygame.K_5: 4,
                pygame.K_6: 5,
                pygame.K_7: 6,
                pygame.K_8: 7,
            }[key]
            if 0 <= idx < len(rows):
                self.bag_idx = idx
                self.eat_bag_food(rows[idx][0])

    def draw_bag_overlay(self) -> None:
        dim = pygame.Surface((VIEW_W, VIEW_H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        self.screen.blit(dim, (0, 0))
        box = pygame.Rect(48, 36, SCREEN_W - 96, VIEW_H - 72)
        self.draw_textbox(self.screen, box)
        title = self.font.render("背包 · 吃食物补充耐久", True, (255, 220, 120))
        self.screen.blit(title, (box.x + 16, box.y + 12))
        sub = self.font_sm.render(
            (
                f"当前耐久 {self.hp}/{self.max_hp}  ·  金币 {self.coins}"
                if self.uses_durability()
                else f"DIY 模式 · 无耐久  ·  金币 {self.coins}"
            ),
            True,
            (200, 210, 230),
        )
        self.screen.blit(sub, (box.x + 16, box.y + 36))
        rows = self.bag_food_rows()
        y = box.y + 62
        if not any(n > 0 for _fid, _lab, n, _h in rows):
            empty = self.font.render("空空如也…去开宝箱或捡补给吧", True, (180, 190, 210))
            self.screen.blit(empty, (box.x + 16, y + 20))
        for i, (fid, label, n, heal) in enumerate(rows):
            selected = i == self.bag_idx
            if n <= 0:
                col = (110, 118, 136)
            elif selected:
                col = (255, 240, 160)
            else:
                col = (230, 235, 245)
            prefix = "> " if selected else "  "
            line = f"{prefix}{i + 1}.{label}  ×{n}  （+{heal}耐久）"
            self.screen.blit(self.font.render(line, True, col), (box.x + 14, y))
            y += 26
        hint = self.font_sm.render("↑↓ / 1-8 选择 · Enter 吃 · I / Esc 关闭", True, (170, 180, 200))
        self.screen.blit(hint, (box.x + 16, box.bottom - 28))

    def _reset_mario_state(self, *, keep_coins: bool = False) -> None:
        if not keep_coins:
            self.coins = 0
        self.pickups = []
        self.star_t = 0.0
        self.speed_t = 0.0
        self.bag_open = False
        self.pickup_bob = 0.0

    def _harvest_placed_pickups(self) -> list[dict]:
        """把地图上放置的金币/蘑菇/星收成运行时 pickups，格子还原为背景。"""
        out: list[dict] = []
        if not self.map_data:
            return out
        ensure_ground_layers(self.map_data)
        for layer_name in ("surface", "underground"):
            grid = self.map_data.get(layer_name)
            if not isinstance(grid, list):
                continue
            ground = layer_ground(self.map_data, layer_name)
            default = default_ground_for_layer(layer_name)
            for ty, row in enumerate(grid):
                if not isinstance(row, list):
                    continue
                for tx, cell in enumerate(row):
                    kind = PICKUP_TILE_KIND.get(int(cell))
                    if not kind:
                        continue
                    out.append({"kind": kind, "layer": layer_name, "tx": int(tx), "ty": int(ty)})
                    g = int(ground[ty][tx]) if ty < len(ground) and tx < len(ground[ty]) else default
                    fill = g if g in BACKGROUND_TILES else default
                    row[tx] = fill
                    ground[ty][tx] = fill
        return out

    def spawn_level_pickups(self) -> None:
        """关卡内散布金币 / 蘑菇 / 无敌星（马里奥式拾取物）。"""
        self.pickups = []
        if not self.map_data:
            return
        placed = self._harvest_placed_pickups()
        # DIY：优先用编辑器放置的道具；有放置则不再随机刷
        if placed and not self.campaign:
            self.pickups = placed
            return
        # 战役：随机散布；若地图里也摆了道具则一并加入
        if placed and self.campaign:
            self.pickups.extend(placed)

        mw, mh = map_size(self.map_data)
        start = resolve_start(self.map_data)
        candidates: list[tuple[str, int, int]] = []
        occupied = {(str(p["layer"]), int(p["tx"]), int(p["ty"])) for p in self.pickups}
        for layer_name, key in (("surface", "surface"), ("underground", "underground")):
            grid = self.map_data.get(key) or []
            for ty in range(1, mh - 1):
                for tx in range(1, mw - 1):
                    if (layer_name, tx, ty) in occupied:
                        continue
                    cell = grid[ty][tx]
                    if cell not in WALKABLE_EXTRA:
                        continue
                    if cell in PICKUP_TILES or cell in TRAP_TILES:
                        continue
                    if layer_name == "surface" and (tx, ty) == start:
                        continue
                    candidates.append((layer_name, tx, ty))
        random.shuffle(candidates)
        if not candidates:
            return

        def _take(n: int) -> list[tuple[str, int, int]]:
            out = candidates[:n]
            del candidates[:n]
            return out

        # DIY 未放置任何道具时，仍给少量随机，避免空荡
        if self.campaign:
            coin_n = min(14, max(8, len(candidates) // 40))
            mush_n = min(2, len(candidates))
            star_chance = 0.65
        else:
            coin_n = min(6, max(3, len(candidates) // 60))
            mush_n = min(1, len(candidates))
            star_chance = 0.35

        for layer, tx, ty in _take(coin_n):
            self.pickups.append({"kind": "coin", "layer": layer, "tx": tx, "ty": ty})
        for layer, tx, ty in _take(mush_n):
            self.pickups.append({"kind": "mushroom", "layer": layer, "tx": tx, "ty": ty})
        if candidates and random.random() < star_chance:
            layer, tx, ty = _take(1)[0]
            self.pickups.append({"kind": "star", "layer": layer, "tx": tx, "ty": ty})

    def grant_coins(self, n: int = 1, *, reason: str = "", silent: bool = False) -> str:
        add = max(0, int(n))
        self.coins += add
        self._wallet_earned = int(getattr(self, "_wallet_earned", 0) or 0) + add
        if add > 0:
            self._play_coin_sfx()
        msg = reason or f"金币 +{n}（合计 {self.coins}）"
        # 战役：每满 10 枚回血；DIY 无耐久，只攒币
        if self.uses_durability():
            while self.coins >= RPG_COIN_HEAL_EVERY:
                self.coins -= RPG_COIN_HEAL_EVERY
                before = int(self.hp)
                self.hp = min(self.max_hp, before + RPG_COIN_HEAL)
                gained = self.hp - before
                self._play_reward_sfx()
                msg = f"{msg} · 金币×{RPG_COIN_HEAL_EVERY}！耐久+{gained}"
        if not silent:
            self.toast(msg, 2.6)
        return msg

    def flush_wallet_earned(self) -> None:
        """把本局获得的金币同步到桌宠 wallet.json（不扣局内币）。"""
        n = int(getattr(self, "_wallet_earned", 0) or 0)
        if n <= 0:
            return
        bal = _add_coins_to_desktop_wallet(n)
        self._wallet_earned = 0
        if bal >= 0:
            self.toast(f"金币已同步桌宠钱包 +{n}（持有 {bal}）", 2.8)

    def grant_mushroom(self, *, reason: str = "吃到加速蘑菇！", silent: bool = False) -> str:
        self.speed_t = RPG_MUSHROOM_SEC
        self._play_reward_sfx()
        msg = f"{reason} 移速提升 {int(RPG_MUSHROOM_SEC)} 秒"
        if not silent:
            self.toast(msg, 2.8)
        return msg

    def grant_star(self, *, reason: str = "捡到无敌星！", silent: bool = False) -> str:
        self.star_t = RPG_STAR_SEC
        self._play_reward_sfx()
        msg = f"{reason} {int(RPG_STAR_SEC)} 秒内免疫陷阱"
        if not silent:
            self.toast(msg, 2.8)
        return msg

    def update_pickups(self, dt: float) -> None:
        self.pickup_bob += dt
        if self.star_t > 0:
            self.star_t = max(0.0, self.star_t - dt)
            if self.star_t <= 0:
                self.toast("无敌状态结束", 1.4)
        if self.speed_t > 0:
            self.speed_t = max(0.0, self.speed_t - dt)
            if self.speed_t <= 0:
                self.toast("加速效果结束", 1.4)
        if not self.knight or not self.pickups:
            return
        remain: list[dict] = []
        for p in self.pickups:
            if p.get("layer") != self.layer:
                remain.append(p)
                continue
            cx = int(p["tx"]) * TILE + TILE // 2
            cy = int(p["ty"]) * TILE + TILE // 2
            if abs(self.knight.x - cx) <= TILE * 0.42 and abs(self.knight.y - cy) <= TILE * 0.42:
                kind = str(p.get("kind") or "coin")
                if kind == "mushroom":
                    self.grant_mushroom()
                elif kind == "star":
                    self.grant_star()
                else:
                    self.grant_coins(1, reason="捡到金币！")
            else:
                remain.append(p)
        self.pickups = remain

    def draw_pickups(self, surf: pygame.Surface) -> None:
        bob = math.sin(self.pickup_bob * 4.0) * 3.0
        for p in self.pickups:
            if p.get("layer") != self.layer:
                continue
            cx = int(p["tx"]) * TILE + TILE // 2
            cy = int(p["ty"]) * TILE + TILE // 2 + int(bob)
            sx, sy = self.camera.apply(cx, cy)
            kind = str(p.get("kind") or "coin")
            if kind == "mushroom":
                pygame.draw.circle(surf, (230, 60, 70), (sx, sy - 2), 8)
                pygame.draw.circle(surf, (250, 250, 250), (sx, sy + 5), 6)
                pygame.draw.circle(surf, (255, 255, 255), (sx - 3, sy - 4), 2)
            elif kind == "star":
                pts = []
                for i in range(5):
                    a = -math.pi / 2 + i * (2 * math.pi / 5)
                    pts.append((sx + int(math.cos(a) * 9), sy + int(math.sin(a) * 9)))
                    a2 = a + math.pi / 5
                    pts.append((sx + int(math.cos(a2) * 4), sy + int(math.sin(a2) * 4)))
                pygame.draw.polygon(surf, (255, 220, 60), pts)
                pygame.draw.polygon(surf, (255, 255, 200), pts, 1)
            else:
                pygame.draw.circle(surf, (255, 200, 40), (sx, sy), 7)
                pygame.draw.circle(surf, (255, 240, 140), (sx, sy), 7, 1)
                pygame.draw.line(surf, (180, 120, 20), (sx, sy - 4), (sx, sy + 4), 2)

    def apply_chest_outcome(self, won: bool) -> str:
        """胜利：回血/得食物/金币或道具；失败：扣血或扣食物。DIY 无耐久结算。"""
        loot_name, loot_desc = random.choice(TREASURE_LOOT)
        durable = self.uses_durability()
        if won:
            bonus = ""
            roll = random.random()
            if roll < 0.18:
                bonus = "；" + self.grant_mushroom(reason="宝箱里蹦出蘑菇！", silent=True)
            elif roll < 0.28:
                bonus = "；" + self.grant_star(reason="宝箱里闪出无敌星！", silent=True)
            elif roll < 0.55:
                bonus = "；" + self.grant_coins(random.randint(2, 5), reason="宝箱金币哗啦啦！", silent=True)
            if durable:
                if random.random() < 0.55:
                    heal = random.randint(12, 22)
                    self.hp = min(self.max_hp, self.hp + heal)
                    extra = self.change_food(1) if random.random() < 0.35 else ""
                    msg = f"判定成功！{loot_name}：{loot_desc} 耐久+{heal}"
                    if extra:
                        msg += f"；{extra}"
                    msg += bonus
                else:
                    extra = self.change_food(1)
                    heal = random.randint(6, 12)
                    self.hp = min(self.max_hp, self.hp + heal)
                    msg = f"判定成功！{loot_name}：{loot_desc}；{extra}；耐久+{heal}{bonus}"
            else:
                # DIY：只给食物/道具，不碰耐久
                if random.random() < 0.6:
                    extra = self.change_food(1)
                    msg = f"判定成功！{loot_name}：{loot_desc}；{extra}{bonus}"
                else:
                    bonus2 = bonus or ("；" + self.grant_coins(random.randint(2, 4), reason="宝箱金币！", silent=True))
                    msg = f"判定成功！{loot_name}：{loot_desc}{bonus2}"
            self._play_reward_sfx()
            return msg
        # 失败
        if not durable:
            if self.food_bag_count() > 0 and random.random() < 0.45:
                extra = self.change_food(-1)
                msg = f"判定失败…{extra}"
            else:
                msg = f"判定失败…宝箱啪地关上了（DIY 无耐久惩罚）"
            return msg
        if random.random() < 0.5 or self.food_bag_count() <= 0:
            dmg = random.randint(10, 18)
            self.hp = max(0, self.hp - dmg)
            msg = f"判定失败…宝箱机关弹开！耐久-{dmg}"
        else:
            extra = self.change_food(-1)
            dmg = random.randint(6, 12)
            self.hp = max(0, self.hp - dmg)
            msg = f"判定失败…{extra}；耐久-{dmg}"
        if self.hp <= 0:
            self._on_hp_empty()
        return msg

    def begin_chest_event(self, tx: int, ty: int) -> None:
        """开箱：随机二选一——要么掷骰，要么猜拳（玩家不能自选）。"""
        mode = random.choice(("dice", "rps"))
        if mode == "dice":
            phase = "dice"
            msg = "宝箱锁上了骰子机关！按 SPACE 掷骰（需 ≥4 点）"
            toast = "宝箱判定：掷骰子！"
        else:
            phase = "rps"
            msg = "宝箱锁上了猜拳机关！1石头  2剪刀  3布"
            toast = "宝箱判定：石头剪刀布！"
        self.chest_event = {
            "tx": int(tx),
            "ty": int(ty),
            "phase": phase,
            "mode": mode,
            "player_roll": 0,
            "enemy_roll": 0,
            "display_roll": 0,
            "player_rps": 0,
            "enemy_rps": 0,
            "display_enemy_rps": 0,
            "spin": 0,
            "spin_t": 0.0,
            "msg": msg,
        }
        self.toast(toast, 1.8)

    def finish_chest_event(self, won: bool, detail: str = "") -> None:
        """结算奖励/惩罚，并停留在结果面板片刻（更易看清）。"""
        ev = self.chest_event
        if not ev or not self.map_data:
            self.chest_event = None
            return
        if ev.get("phase") == "result" and ev.get("settled"):
            return
        tx, ty = int(ev["tx"]), int(ev["ty"])
        grid = self.current_grid()
        if 0 <= ty < len(grid) and 0 <= tx < len(grid[0]) and grid[ty][tx] == TREASURE:
            grid[ty][tx] = TREASURE_OPEN
            self.treasures += 1
        outcome = self.apply_chest_outcome(won)
        detail = (detail or str(ev.get("msg") or "")).strip()
        ev["phase"] = "result"
        ev["won"] = bool(won)
        ev["settled"] = True
        ev["detail"] = detail
        ev["outcome"] = outcome
        ev["msg"] = outcome
        ev["result_t"] = 2.8
        self.toast(f"{outcome}（本关宝箱 {self.treasures}）", 4.2)

    def close_chest_event(self) -> None:
        self.chest_event = None

    def handle_chest_event_key(self, key: int) -> None:
        ev = self.chest_event
        if not ev:
            return
        phase = str(ev.get("phase") or "")
        if phase == "result":
            if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                self.close_chest_event()
            return
        if key == pygame.K_ESCAPE:
            self.chest_event = None
            self.toast("取消开箱")
            return
        if phase == "dice" and key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_e):
            ev["phase"] = "dice_spin"
            ev["spin"] = 0
            ev["spin_t"] = 0.0
            ev["player_roll"] = random.randint(1, 6)
            ev["display_roll"] = random.randint(1, 6)
            ev["msg"] = "骰子转动中…"
            return
        if phase == "rps" and key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_KP1, pygame.K_KP2, pygame.K_KP3):
            mapping = {
                pygame.K_1: 1,
                pygame.K_KP1: 1,
                pygame.K_2: 2,
                pygame.K_KP2: 2,
                pygame.K_3: 3,
                pygame.K_KP3: 3,
            }
            pr = mapping[key]
            er = random.randint(1, 3)
            ev["player_rps"] = pr
            ev["enemy_rps"] = er
            ev["display_enemy_rps"] = random.randint(1, 3)
            ev["phase"] = "rps_spin"
            ev["spin"] = 0
            ev["spin_t"] = 0.0
            ev["msg"] = f"你出了{RPS_NAMES[pr]}！对手正在出拳…"

    def update_chest_event(self, dt: float) -> None:
        ev = self.chest_event
        if not ev:
            return
        phase = str(ev.get("phase") or "")
        if phase == "result":
            ev["result_t"] = float(ev.get("result_t") or 0) - dt
            if float(ev.get("result_t") or 0) <= 0:
                self.close_chest_event()
            return
        if phase == "dice_spin":
            ev["spin_t"] = float(ev.get("spin_t") or 0) + dt
            ev["spin"] = int(ev.get("spin") or 0) + 1
            # 转动阶段快速换面
            if float(ev["spin_t"]) < 0.95:
                if ev["spin"] % 2 == 0:
                    ev["display_roll"] = random.randint(1, 6)
                return
            pr = int(ev.get("player_roll") or 1)
            ev["display_roll"] = pr
            need = 4
            won = pr >= need
            detail = f"你掷出 {pr} 点（需≥{need}）— {'成功！' if won else '失败…'}"
            self.finish_chest_event(won, detail)
            return
        if phase == "rps_spin":
            ev["spin_t"] = float(ev.get("spin_t") or 0) + dt
            ev["spin"] = int(ev.get("spin") or 0) + 1
            if float(ev["spin_t"]) < 0.85:
                if ev["spin"] % 2 == 0:
                    ev["display_enemy_rps"] = random.randint(1, 3)
                return
            pr = int(ev.get("player_rps") or 1)
            er = int(ev.get("enemy_rps") or 1)
            ev["display_enemy_rps"] = er
            res = rps_beats(pr, er)
            if res > 0:
                detail = f"你出{RPS_NAMES[pr]}，对手{RPS_NAMES[er]} — 你赢了！"
                self.finish_chest_event(True, detail)
            elif res == 0:
                ev["phase"] = "rps"
                ev["player_rps"] = 0
                ev["enemy_rps"] = 0
                ev["display_enemy_rps"] = 0
                ev["msg"] = f"平局（双方{RPS_NAMES[pr]}）！再出一次：1石 2剪 3布"
            else:
                detail = f"你出{RPS_NAMES[pr]}，对手{RPS_NAMES[er]} — 输了…"
                self.finish_chest_event(False, detail)

    def _draw_die_face(self, surf: pygame.Surface, rect: pygame.Rect, value: int, *, highlight: bool = False) -> None:
        """绘制有点数的骰子面。"""
        bg = (255, 245, 210) if highlight else (235, 235, 245)
        border = (255, 200, 80) if highlight else (50, 55, 70)
        pygame.draw.rect(surf, bg, rect, border_radius=10)
        pygame.draw.rect(surf, border, rect, 3, border_radius=10)
        v = max(0, min(6, int(value)))
        if v <= 0:
            q = self.font_lg.render("?", True, (120, 130, 150))
            surf.blit(q, (rect.centerx - q.get_width() // 2, rect.centery - q.get_height() // 2))
            return
        # 九点网格 pip
        inset = max(10, rect.w // 5)
        positions = {
            1: ((1, 1),),
            2: ((0, 0), (2, 2)),
            3: ((0, 0), (1, 1), (2, 2)),
            4: ((0, 0), (0, 2), (2, 0), (2, 2)),
            5: ((0, 0), (0, 2), (1, 1), (2, 0), (2, 2)),
            6: ((0, 0), (0, 1), (0, 2), (2, 0), (2, 1), (2, 2)),
        }
        r = max(4, rect.w // 12)
        for gx, gy in positions[v]:
            cx = rect.x + inset + gx * (rect.w - 2 * inset) // 2
            cy = rect.y + inset + gy * (rect.h - 2 * inset) // 2
            pygame.draw.circle(surf, (35, 40, 55), (cx, cy), r)

    def _draw_rps_icon(self, surf: pygame.Surface, rect: pygame.Rect, choice: int, *, selected: bool = False, dim: bool = False) -> None:
        """石头 / 剪刀 / 布 图标面板。"""
        palette = {
            0: ((70, 78, 98), (160, 170, 190), "?"),
            1: ((90, 110, 150), (210, 220, 240), "石头"),
            2: ((150, 90, 110), (255, 180, 200), "剪刀"),
            3: ((90, 140, 120), (180, 240, 210), "布"),
        }
        bg, accent, label = palette.get(int(choice), palette[0])
        if dim:
            bg = tuple(max(20, c - 35) for c in bg)
        if selected:
            pygame.draw.rect(surf, (255, 220, 100), rect.inflate(6, 6), border_radius=12)
        pygame.draw.rect(surf, bg, rect, border_radius=10)
        pygame.draw.rect(surf, accent, rect, 2, border_radius=10)
        cx, cy = rect.centerx, rect.centery - 6
        c = int(choice)
        if c == 1:
            # 石头：圆拳
            pygame.draw.circle(surf, accent, (cx, cy), rect.w // 4)
            pygame.draw.circle(surf, bg, (cx, cy), rect.w // 7)
        elif c == 2:
            # 剪刀：两叉
            pygame.draw.line(surf, accent, (cx - 14, cy - 16), (cx + 10, cy + 14), 5)
            pygame.draw.line(surf, accent, (cx + 14, cy - 16), (cx - 10, cy + 14), 5)
            pygame.draw.circle(surf, accent, (cx - 14, cy - 16), 5)
            pygame.draw.circle(surf, accent, (cx + 14, cy - 16), 5)
        elif c == 3:
            # 布：方掌
            hand = pygame.Rect(0, 0, rect.w // 2, rect.h // 2)
            hand.center = (cx, cy)
            pygame.draw.rect(surf, accent, hand, border_radius=4)
            pygame.draw.rect(surf, bg, hand.inflate(-8, -8), border_radius=3)
        else:
            q = self.font_lg.render("?", True, accent)
            surf.blit(q, (cx - q.get_width() // 2, cy - q.get_height() // 2))
        lab = self.font_sm.render(label, True, (245, 245, 250))
        surf.blit(lab, (rect.centerx - lab.get_width() // 2, rect.bottom - 22))

    def maybe_trigger_hazard(self) -> None:
        """换格时小概率踩机关：扣血或扣食物（马里奥式突发惩罚）。"""
        if not self.uses_durability():
            return  # DIY：无耐久机关
        if not self.knight or self.chest_event or self.dialog or self.bag_open:
            return
        if self.hazard_cd > 0:
            return
        if self.star_t > 0:
            return  # 无敌星：完全跳过陷阱
        tx, ty = self.knight.tile_pos()
        key = (self.layer, int(tx), int(ty))
        if key == self._last_hazard_tile:
            return
        self._last_hazard_tile = key
        if random.random() > RPG_HAZARD_CHANCE:
            return
        self.hazard_cd = 2.4
        kind = random.choice(("hp", "hp", "food", "heal_trap", "mystery"))
        # heal_trap / mystery：神秘砖风格奖励
        if kind == "mystery":
            roll = random.random()
            if roll < 0.45:
                self.grant_coins(random.randint(1, 3), reason="头顶神秘砖弹出金币！")
            elif roll < 0.75:
                self.grant_mushroom(reason="神秘砖弹出蘑菇！")
            else:
                self.grant_star(reason="神秘砖弹出无敌星！")
            return
        if kind == "heal_trap" and random.random() < 0.45:
            if random.random() < 0.5:
                heal = random.randint(6, 12)
                self.change_hp(heal, reason="脚下滚出一枚幸运币！")
                self.grant_coins(1, reason="幸运币！", silent=True)
            else:
                msg = self.change_food(1)
                self.toast(f"草丛里捡到补给：{msg}", 2.8)
            return
        if kind == "food" and self.food_bag_count() > 0:
            msg = self.change_food(-1)
            self.toast(f"踩到陷阱！{msg}", 2.8)
        else:
            dmg = -random.randint(6, 14)
            self.change_hp(dmg, reason="踩到尖刺机关！")

    def maybe_trigger_map_trap(self) -> None:
        """踩到地图上放置的陷阱地块（尖刺 / 陷坑）。"""
        if not self.knight or self.chest_event or self.dialog or self.bag_open:
            return
        if self.map_trap_cd > 0:
            return
        if self.star_t > 0:
            return
        tx, ty = self.knight.tile_pos()
        grid = self.current_grid()
        mw, mh = map_size(self.map_data) if self.map_data else (0, 0)
        if not (0 <= tx < mw and 0 <= ty < mh):
            return
        cell = grid[ty][tx]
        if cell not in TRAP_TILES:
            self._last_map_trap_tile = None
            return
        key = (self.layer, int(tx), int(ty))
        if key == self._last_map_trap_tile:
            return
        self._last_map_trap_tile = key
        self.revealed_traps.add(key)
        self.map_trap_cd = 1.1
        if cell == TRAP_SPIKE:
            if self.uses_durability():
                dmg = -random.randint(8, 16)
                self.change_hp(dmg, reason="踩中尖刺陷阱！")
            else:
                self.toast("踩中尖刺陷阱！（DIY 不扣耐久）", 2.4)
        else:  # TRAP_PIT
            if self.uses_durability():
                dmg = -random.randint(10, 18)
                self.change_hp(dmg, reason="掉进陷坑！")
                # 小概率额外掉食物
                if self.food_bag_count() > 0 and random.random() < 0.35:
                    msg = self.change_food(-1)
                    self.toast(f"陷坑里掉了补给：{msg}", 2.6)
            else:
                self.toast("掉进陷坑！（DIY 不扣耐久）", 2.4)

    def draw_chest_event_overlay(self) -> None:
        ev = self.chest_event
        if not ev:
            return
        dim = pygame.Surface((VIEW_W, VIEW_H), pygame.SRCALPHA)
        phase = str(ev.get("phase") or "")
        mode = str(ev.get("mode") or "")
        dim.fill((0, 0, 0, 170 if phase == "result" else 150))
        self.screen.blit(dim, (0, 0))

        if phase == "result":
            won = bool(ev.get("won"))
            mode = str(ev.get("mode") or "")
            box = pygame.Rect(32, 36, SCREEN_W - 64, VIEW_H - 72)
            self.draw_textbox(self.screen, box)
            bar_c = (60, 200, 120) if won else (230, 80, 80)
            pygame.draw.rect(self.screen, bar_c, (box.x + 8, box.y + 8, box.w - 16, 8), border_radius=2)
            headline = "判定成功！" if won else "判定失败…"
            title = self.font_lg.render(headline, True, (120, 255, 170) if won else (255, 140, 140))
            self.screen.blit(title, (box.centerx - title.get_width() // 2, box.y + 22))

            # —— 上方图案：骰子终局 / 猜拳双方 ——
            art_y = box.y + 58
            if mode == "dice":
                die_size = 88
                die_rect = pygame.Rect(0, 0, die_size, die_size)
                die_rect.center = (box.centerx, art_y + die_size // 2)
                roll = int(ev.get("player_roll") or ev.get("display_roll") or 0)
                self._draw_die_face(self.screen, die_rect, roll, highlight=True)
                tag = self.font.render(f"{roll} 点", True, (255, 230, 140) if won else (255, 180, 160))
                self.screen.blit(tag, (box.centerx - tag.get_width() // 2, die_rect.bottom + 8))
                y = die_rect.bottom + 36
            else:
                card_w, card_h = 92, 104
                you_r = pygame.Rect(box.x + 56, art_y, card_w, card_h)
                foe_r = pygame.Rect(box.right - 56 - card_w, art_y, card_w, card_h)
                you_lab = self.font_sm.render("你", True, (180, 220, 255))
                foe_lab = self.font_sm.render("机关", True, (255, 180, 180))
                self.screen.blit(you_lab, (you_r.centerx - you_lab.get_width() // 2, you_r.y - 18))
                self.screen.blit(foe_lab, (foe_r.centerx - foe_lab.get_width() // 2, foe_r.y - 18))
                self._draw_rps_icon(self.screen, you_r, int(ev.get("player_rps") or 0), selected=True)
                self._draw_rps_icon(self.screen, foe_r, int(ev.get("enemy_rps") or 0), selected=True)
                vs = self.font_lg.render("VS", True, (255, 230, 140))
                self.screen.blit(vs, (box.centerx - vs.get_width() // 2, art_y + card_h // 2 - 12))
                y = art_y + card_h + 16

            detail = str(ev.get("detail") or "")
            outcome = str(ev.get("outcome") or ev.get("msg") or "")
            if detail:
                d = self.font.render(detail, True, (255, 240, 180))
                self.screen.blit(d, (box.centerx - d.get_width() // 2, y))
                y += 26
            # 结算摘要：过长则截断一行
            if outcome:
                max_w = box.w - 40
                line = outcome
                if self.font.size(line)[0] > max_w:
                    while len(line) > 4 and self.font.size(line + "…")[0] > max_w:
                        line = line[:-1]
                    line += "…"
                t = self.font_sm.render(line, True, (220, 228, 240))
                self.screen.blit(t, (box.centerx - t.get_width() // 2, y))
            hint = self.font_sm.render("Enter / Space 继续", True, (190, 200, 220))
            self.screen.blit(hint, (box.centerx - hint.get_width() // 2, box.bottom - 28))
            return

        # —— 判定进行中：大面板 + 骰子/猜拳画面 ——
        box = pygame.Rect(36, 48, SCREEN_W - 72, VIEW_H - 100)
        self.draw_textbox(self.screen, box)
        if mode == "dice":
            title_txt = "宝箱判定 · 掷骰子"
        else:
            title_txt = "宝箱判定 · 石头剪刀布"
        title = self.font.render(title_txt, True, (255, 220, 120))
        self.screen.blit(title, (box.centerx - title.get_width() // 2, box.y + 14))
        msg = str(ev.get("msg") or "")
        sub = self.font_sm.render(msg, True, (220, 225, 235))
        self.screen.blit(sub, (box.centerx - sub.get_width() // 2, box.y + 42))

        if mode == "dice":
            die_size = 96
            die_rect = pygame.Rect(0, 0, die_size, die_size)
            die_rect.center = (box.centerx, box.centery + 8)
            show_v = int(ev.get("display_roll") or 0)
            if phase == "dice":
                show_v = 0
            spinning = phase == "dice_spin"
            # 轻晃
            if spinning:
                shake = int(4 * math.sin(float(ev.get("spin_t") or 0) * 40))
                die_rect.x += shake
            self._draw_die_face(self.screen, die_rect, show_v, highlight=spinning or phase == "result")
            need_lbl = self.font_sm.render("成功条件：点数 ≥ 4", True, (180, 200, 230))
            self.screen.blit(need_lbl, (box.centerx - need_lbl.get_width() // 2, die_rect.bottom + 14))
            if phase == "dice":
                tip = self.font.render("SPACE / Enter 掷骰", True, (120, 220, 255))
                self.screen.blit(tip, (box.centerx - tip.get_width() // 2, box.bottom - 36))
            elif phase == "dice_spin":
                tip = self.font.render("转动中…", True, (255, 220, 140))
                self.screen.blit(tip, (box.centerx - tip.get_width() // 2, box.bottom - 36))
            return

        # 猜拳画面
        card_w, card_h = 88, 100
        gap = 18
        total_w = card_w * 3 + gap * 2
        x0 = box.centerx - total_w // 2
        y0 = box.y + 78
        if phase == "rps":
            for i, choice in enumerate((1, 2, 3)):
                r = pygame.Rect(x0 + i * (card_w + gap), y0, card_w, card_h)
                self._draw_rps_icon(self.screen, r, choice)
            tip = self.font.render("按 1 / 2 / 3 出拳", True, (120, 220, 255))
            self.screen.blit(tip, (box.centerx - tip.get_width() // 2, box.bottom - 36))
            return

        # rps_spin / 展示双方
        you_r = pygame.Rect(box.x + 48, y0, card_w + 12, card_h + 8)
        foe_r = pygame.Rect(box.right - 48 - (card_w + 12), y0, card_w + 12, card_h + 8)
        you_lab = self.font_sm.render("你", True, (180, 220, 255))
        foe_lab = self.font_sm.render("宝箱机关", True, (255, 180, 180))
        self.screen.blit(you_lab, (you_r.centerx - you_lab.get_width() // 2, you_r.y - 22))
        self.screen.blit(foe_lab, (foe_r.centerx - foe_lab.get_width() // 2, foe_r.y - 22))
        self._draw_rps_icon(self.screen, you_r, int(ev.get("player_rps") or 0), selected=True)
        enemy_show = int(ev.get("display_enemy_rps") or 0)
        self._draw_rps_icon(self.screen, foe_r, enemy_show, selected=phase != "rps_spin")
        vs = self.font_lg.render("VS", True, (255, 230, 140))
        self.screen.blit(vs, (box.centerx - vs.get_width() // 2, y0 + card_h // 2 - 10))
        if phase == "rps_spin":
            tip = self.font.render("揭晓中…", True, (255, 220, 140))
            self.screen.blit(tip, (box.centerx - tip.get_width() // 2, box.bottom - 36))

    def show_dialog(self, title: str, body: str) -> None:
        self.dialog = {"title": title, "body": body}

    def close_dialog(self) -> None:
        self.dialog = None

    def draw_dialog_overlay(self) -> None:
        if not self.dialog:
            return
        dim = pygame.Surface((VIEW_W, VIEW_H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 120))
        self.screen.blit(dim, (0, 0))
        box = pygame.Rect(48, VIEW_H // 2 - 44, SCREEN_W - 96, 92)
        self.draw_textbox(self.screen, box)
        title = self.font.render(self.dialog_quote(self.dialog["title"]), True, (255, 230, 140))
        body = self.font_sm.render(self.dialog["body"], True, (235, 235, 240))
        hint = self.font_sm.render("ENTER / E / SPACE — 关闭", True, (180, 180, 190))
        self.screen.blit(title, (box.x + 14, box.y + 12))
        self.screen.blit(body, (box.x + 14, box.y + 38))
        self.screen.blit(hint, (box.x + 14, box.bottom - 24))

    def dialog_quote(self, text: str) -> str:
        t = text.strip()
        if t.startswith("*「") and t.endswith("」"):
            return t
        return f"*「{t}」"

    def _save_path(self, slot: int) -> Path:
        return SAVES_DIR / f"slot{slot}.json"

    def save_game(self, slot: int = 1) -> None:
        """冒险进度存档（含当前地图状态，已开宝箱会保留）。"""
        if self.state != "play" or not self.map_data or not self.knight:
            self.toast("只能在冒险中存档（先 START 进入关卡）")
            return
        SAVES_DIR.mkdir(exist_ok=True)
        payload = {
            "version": 1,
            "slot": slot,
            "campaign": bool(self.campaign),
            "level_idx": int(self.level_idx),
            "treasures": int(self.treasures),
            "total_treasures": int(self.total_treasures),
            "hp": int(self.hp),
            "max_hp": int(self.max_hp),
            "coins": int(self.coins),
            "layer": self.layer,
            "player_kind": self.player_kind,
            "player": [self.knight.x, self.knight.y, self.knight.dir],
            "map_data": self.map_data,
            "pickups": self.pickups,
            "star_t": float(self.star_t),
            "speed_t": float(self.speed_t),
        }
        path = self._save_path(slot)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)
        except Exception as exc:
            self.toast(f"存档失败：{exc}", 3.5)
            return
        self.flush_wallet_earned()
        self.toast(f"已存档 {path.name}（菜单 LOAD SAVE 读取）", 3.0)

    def load_game(self, slot: int = 1, path: Path | None = None) -> bool:
        if path is None:
            path = self._save_path(slot)
        if not path.exists():
            # 兼容任意 slot*.json
            saves = self._list_saves()
            if not saves:
                self.toast("没有存档")
                return False
            path = saves[min(max(0, slot - 1), len(saves) - 1)]
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            self.toast("存档损坏")
            return False
        map_data = data.get("map_data")
        if not isinstance(map_data, dict):
            self.toast("存档缺少地图")
            return False
        if "surface" not in map_data:
            map_data = self._migrate_old_map(map_data)
        map_data = normalize_map_tiles(map_data)
        self.campaign = bool(data.get("campaign", True))
        self.level_idx = int(data.get("level_idx", 0))
        self.treasures = int(data.get("treasures", 0))
        self.total_treasures = int(data.get("total_treasures", 0))
        self.hp = max(1, min(RPG_MAX_HP, int(data.get("hp", RPG_MAX_HP))))
        self.max_hp = max(1, min(RPG_MAX_HP, int(data.get("max_hp", RPG_MAX_HP))))
        self.coins = max(0, int(data.get("coins", 0)))
        self.star_t = max(0.0, float(data.get("star_t", 0)))
        self.speed_t = max(0.0, float(data.get("speed_t", 0)))
        raw_pickups = data.get("pickups")
        self.pickups = list(raw_pickups) if isinstance(raw_pickups, list) else []
        self.bag_open = False
        self.chest_event = None
        self.layer = str(data.get("layer", "surface"))
        kind = str(data.get("player_kind") or self.player_kind or "knight")
        if kind in PLAYER_KINDS:
            self.player_kind = kind
        self.map_data = map_data
        if self.campaign:
            note_rpg_best_level(self.level_idx)
        px, py, pdir = 0.0, 0.0, "down"
        player = data.get("player") or []
        if len(player) >= 2:
            px, py = float(player[0]), float(player[1])
            if len(player) >= 3:
                pdir = str(player[2])
        else:
            sx, sy = resolve_start(map_data)
            px = sx * TILE + TILE // 2
            py = sy * TILE + TILE // 2
        self.knight = self._make_player((0, 0))
        self.knight.x, self.knight.y = px, py
        if pdir in self.assets.knight:
            self.knight.dir = pdir
        # 存档落点若在湖/墙等不可走格，挪到最近可走格
        stx, sty = ensure_walkable_spawn(
            map_data, int(self.knight.x) // TILE, int(self.knight.y) // TILE, layer=self.layer
        )
        if (stx, sty) != (int(self.knight.x) // TILE, int(self.knight.y) // TILE):
            self.knight.place_on_tile(stx, sty)
        # 旧存档无拾取物：补刷一波
        if not self.pickups:
            self.spawn_level_pickups()
        self.state = "play"
        self.dialog = None
        self.picker_mode = ""
        mw, mh = map_size(map_data)
        self.camera.follow(self.knight.x, self.knight.y, mw, mh)
        if self.campaign:
            self._begin_adventure_bgm()
        else:
            self.stop_bgm()
        self.toast(f"已读取 {path.name}")
        return True

    def open_save_picker(self) -> None:
        saves = self._list_saves()
        if not saves:
            self.toast("暂无存档（冒险中按 F5 存档）")
            return
        self.picker_mode = "save"
        self.save_picker_idx = 0
        self.state = "picker"

    def open_map_picker(self, *, for_editor: bool = False) -> None:
        self.custom_maps = self._list_maps()
        if not self.custom_maps:
            self.toast("maps/ 里还没有 DIY 地图")
            return
        self.picker_mode = "map_editor" if for_editor else "map_play"
        self.map_picker_idx = len(self.custom_maps) - 1
        self.picker_delete_pending = None
        self.state = "picker"

    def run_picker(self, events: list) -> None:
        items = self._list_saves() if self.picker_mode == "save" else self._list_maps()
        if not items:
            self.picker_delete_pending = None
            self.picker_mode = ""
            self.enter_menu(play_intro=False)
            return
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.picker_mode = ""
                    self.picker_delete_pending = None
                    self.enter_menu(play_intro=False)
                    return
                if e.key in (pygame.K_UP, pygame.K_w):
                    self.picker_delete_pending = None
                    if self.picker_mode == "save":
                        self.save_picker_idx = (self.save_picker_idx - 1) % len(items)
                    else:
                        self.map_picker_idx = (self.map_picker_idx - 1) % len(items)
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.picker_delete_pending = None
                    if self.picker_mode == "save":
                        self.save_picker_idx = (self.save_picker_idx + 1) % len(items)
                    else:
                        self.map_picker_idx = (self.map_picker_idx + 1) % len(items)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.picker_delete_pending = None
                    self._picker_confirm(items)
                    return
                elif e.key in (pygame.K_DELETE, pygame.K_x) and self.picker_mode != "save":
                    path = items[self.map_picker_idx]
                    if self.picker_delete_pending and self.picker_delete_pending.resolve() == path.resolve():
                        if self._delete_map_file(path):
                            self.toast(f"已删除 {path.name}")
                            self.picker_delete_pending = None
                            items = self._list_maps()
                            if not items:
                                self.picker_mode = ""
                                self.enter_menu(play_intro=False)
                                return
                            self.map_picker_idx = min(self.map_picker_idx, len(items) - 1)
                            self.custom_maps = items
                    else:
                        self.picker_delete_pending = path
                        self.toast(f"再按 Delete/X 确认删除 {path.name}")
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mx, my = self._content_mouse(e.pos)
                top = 80
                for i, _path in enumerate(items):
                    rect = pygame.Rect(80, top + i * 36, SCREEN_W - 160, 32)
                    if rect.collidepoint(mx, my):
                        self.picker_delete_pending = None
                        if self.picker_mode == "save":
                            self.save_picker_idx = i
                        else:
                            self.map_picker_idx = i
                        self._picker_confirm(items)
                        return

        self.screen.fill((22, 26, 40))
        title = "读取存档" if self.picker_mode == "save" else "选择 DIY 地图"
        self.screen.blit(self.font.render(title, True, (255, 230, 140)), (80, 36))
        idx = self.save_picker_idx if self.picker_mode == "save" else self.map_picker_idx
        top = 80
        for i, path in enumerate(items):
            selected = i == idx
            color = (255, 230, 120) if selected else (210, 215, 230)
            prefix = "> " if selected else "  "
            label = self.font_sm.render(prefix + path.name, True, color)
            self.screen.blit(label, (96, top + i * 36 + 6))
            if selected:
                pygame.draw.rect(self.screen, (255, 220, 100), (80, top + i * 36, SCREEN_W - 160, 32), 1)
        if self.picker_mode == "save":
            tip_text = "W/S 或鼠标选择 · Enter 确认 · Esc 返回"
        else:
            tip_text = "W/S 选择 · Enter 打开 · Delete/X 删除 · Esc 返回"
        tip = self.font_sm.render(tip_text, True, (170, 180, 200))
        self.screen.blit(tip, (80, SCREEN_H - 40))

    def _picker_confirm(self, items: list[Path]) -> None:
        if self.picker_mode == "save":
            path = items[self.save_picker_idx]
            self.load_game(path=path)
            return
        path = items[self.map_picker_idx]
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if self.picker_mode == "map_editor":
            self.start_editor(data, path=path)
            self.toast(f"已载入 {path.name}")
        else:
            self.start_play(data, campaign=False)
            self.toast(f"试玩 {path.name}")
        self.picker_mode = ""
        self.picker_delete_pending = None

    def _interact_targets(self) -> list[tuple[int, int, int]]:
        """脚下与面前的可互动物。"""
        assert self.map_data and self.knight
        mw, mh = map_size(self.map_data)
        grid = self.current_grid()
        found: list[tuple[int, int, int]] = []
        for tx, ty in (self.knight.tile_pos(), self.knight.facing_tile()):
            if not (0 <= tx < mw and 0 <= ty < mh):
                continue
            cell = grid[ty][tx]
            if cell in (TREASURE, TREASURE_OPEN, HOUSE, GATE, STAIRS, CAVE):
                found.append((tx, ty, cell))
        return found

    def try_interact(self) -> None:
        assert self.map_data and self.knight
        if self.dialog:
            self.close_dialog()
            return
        targets = self._interact_targets()
        if not targets:
            self.toast("附近没什么可以互动的")
            return
        # 优先宝箱
        targets.sort(key=lambda t: 0 if t[2] == TREASURE else 1)
        tx, ty, cell = targets[0]
        grid = self.current_grid()
        if cell == TREASURE:
            self.begin_chest_event(tx, ty)
            return
        if cell == TREASURE_OPEN:
            self.toast("空宝箱：已经被翻过了")
            return
        if cell == HOUSE:
            self.toast("小屋：出发点，整理好行装再上路")
            return
        if cell == GATE:
            self.toast("关卡门：靠近即可前往下一关")
            return
        if cell == STAIRS or cell == CAVE:
            self.try_use_layer_portal()
            return

    def _editor_palette_rects(self) -> list[tuple[pygame.Rect, int, str]]:
        """底部素材栏：图标可点。"""
        n = len(PALETTE)
        pad = 6
        cell = min(40, (SCREEN_W - pad * 2) // max(1, n))
        total = cell * n
        x0 = (SCREEN_W - total) // 2
        y0 = VIEW_H - PALETTE_H + 4
        out: list[tuple[pygame.Rect, int, str]] = []
        for i, (tid, name) in enumerate(PALETTE):
            r = pygame.Rect(x0 + i * cell, y0, cell - 2, PALETTE_H - 8)
            out.append((r, tid, name))
        return out

    def _hit_editor_palette(self, pos: tuple[int, int]) -> int | None:
        mx, my = pos
        if my < VIEW_H - PALETTE_H:
            return None
        for rect, tid, _name in self._editor_palette_rects():
            if rect.collidepoint(mx, my):
                return tid
        return None

    def draw_editor_palette(self) -> None:
        strip = pygame.Rect(0, VIEW_H - PALETTE_H, SCREEN_W, PALETTE_H)
        pygame.draw.rect(self.screen, (24, 28, 42), strip)
        pygame.draw.line(self.screen, (90, 100, 130), (0, VIEW_H - PALETTE_H), (SCREEN_W, VIEW_H - PALETTE_H), 2)
        for rect, tid, _name in self._editor_palette_rects():
            pygame.draw.rect(self.screen, (40, 46, 64), rect)
            if tid == EMPTY:
                # 清除笔刷：空格 + 红叉
                pygame.draw.rect(self.screen, (28, 32, 48), rect.inflate(-6, -6))
                pygame.draw.line(
                    self.screen, (220, 80, 80),
                    (rect.left + 8, rect.top + 8), (rect.right - 8, rect.bottom - 8), 2,
                )
                pygame.draw.line(
                    self.screen, (220, 80, 80),
                    (rect.right - 8, rect.top + 8), (rect.left + 8, rect.bottom - 8), 2,
                )
            elif tid == BRUSH_START:
                pygame.draw.rect(self.screen, (28, 32, 48), rect.inflate(-6, -6))
                pygame.draw.rect(
                    self.screen, START_MARKER_COLOR,
                    rect.inflate(-14, -14), 2,
                )
            elif tid == BRUSH_PRINCESS:
                thumb = _key_outer_bg_surface(self.assets.princess)
                max_s = min(rect.w - 4, rect.h - 4)
                preview = rect.inflate(-6, -6)
                _draw_checkerboard(self.screen, preview, cell=4)
                if thumb.get_width() > max_s or thumb.get_height() > max_s:
                    scale = max_s / max(thumb.get_width(), thumb.get_height())
                    thumb = pygame.transform.scale(
                        thumb, (max(1, int(thumb.get_width() * scale)), max(1, int(thumb.get_height() * scale)))
                    )
                self.screen.blit(
                    thumb,
                    (rect.centerx - thumb.get_width() // 2, rect.centery - thumb.get_height() // 2),
                )
            elif tid == BRUSH_PAINT:
                pygame.draw.rect(self.screen, (48, 36, 64), rect.inflate(-6, -6))
                pen = self.font_sm.render("画", True, (255, 180, 220))
                self.screen.blit(pen, (rect.centerx - pen.get_width() // 2, rect.centery - pen.get_height() // 2))
            else:
                img = self.assets.tiles.get(tid)
                if img:
                    # 地物 / 自创画：素材栏预览再抠一层外圈绿幕，棋盘格显示透明底
                    thumb = _key_outer_bg_surface(img) if tid in PROP_OVERLAY else img
                    max_s = min(rect.w - 4, rect.h - 4)
                    if thumb.get_width() > max_s or thumb.get_height() > max_s:
                        scale = max_s / max(thumb.get_width(), thumb.get_height())
                        thumb = pygame.transform.scale(
                            thumb, (max(1, int(thumb.get_width() * scale)), max(1, int(thumb.get_height() * scale)))
                        )
                    if tid in PROP_OVERLAY:
                        preview = pygame.Rect(
                            rect.centerx - max_s // 2,
                            rect.centery - max_s // 2,
                            max_s,
                            max_s,
                        )
                        _draw_checkerboard(self.screen, preview, cell=4)
                    self.screen.blit(
                        thumb,
                        (rect.centerx - thumb.get_width() // 2, rect.centery - thumb.get_height() // 2),
                    )
            selected = tid == self.brush or (
                tid == BRUSH_START and self.edit_mode == "start"
            ) or (
                tid == BRUSH_PRINCESS and self.edit_mode == "goal"
            )
            if selected:
                pygame.draw.rect(self.screen, (255, 220, 90), rect, 2)
            else:
                pygame.draw.rect(self.screen, (70, 80, 110), rect, 1)

    @staticmethod
    def _make_type_sfx() -> pygame.mixer.Sound | None:
        """生成短促打字嘀嗒音，无素材时运行时合成。"""
        if not pygame.mixer.get_init():
            return None
        path = ASSETS / "sfx_type.wav"
        if not path.exists():
            import math
            import struct
            import wave

            ASSETS.mkdir(exist_ok=True)
            fr, dur = 22050, 0.028
            n = int(fr * dur)
            with wave.open(str(path), "w") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(fr)
                frames = bytearray()
                for i in range(n):
                    t = i / fr
                    env = math.exp(-t * 90)
                    # 高频短促咔嗒
                    sample = env * (0.55 * math.sin(2 * math.pi * 2100 * t) + 0.25 * math.sin(2 * math.pi * 4200 * t))
                    val = int(max(-1.0, min(1.0, sample)) * 18000)
                    frames += struct.pack("<h", val)
                wf.writeframes(frames)
        try:
            return pygame.mixer.Sound(str(path))
        except pygame.error:
            return None

    @staticmethod
    def _make_reward_sfx() -> pygame.mixer.Sound | None:
        """开宝箱「获得奖励」短音效；优先读素材，否则合成上行琶音。"""
        if not pygame.mixer.get_init():
            return None
        for name in ("sfx_reward.wav", "sfx_reward.ogg", "sfx_loot.wav"):
            path = ASSETS / name
            if path.exists():
                try:
                    return pygame.mixer.Sound(str(path))
                except pygame.error:
                    pass
        path = ASSETS / "sfx_reward.wav"
        try:
            import math
            import struct
            import wave

            ASSETS.mkdir(exist_ok=True)
            fr = 22050
            notes = (523.25, 659.25, 783.99, 1046.5)  # C5 E5 G5 C6
            note_dur = 0.09
            gap = 0.02
            frames = bytearray()
            for ni, freq in enumerate(notes):
                n = int(fr * note_dur)
                for i in range(n):
                    t = i / fr
                    env = math.sin(math.pi * min(1.0, t / note_dur)) ** 0.5
                    env *= math.exp(-t * 6.5)
                    sample = env * (
                        0.55 * math.sin(2 * math.pi * freq * t)
                        + 0.22 * math.sin(2 * math.pi * freq * 2 * t)
                    )
                    val = int(max(-1.0, min(1.0, sample)) * 20000)
                    frames += struct.pack("<h", val)
                if ni < len(notes) - 1:
                    frames += b"\x00\x00" * int(fr * gap)
            with wave.open(str(path), "w") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(fr)
                wf.writeframes(frames)
            return pygame.mixer.Sound(str(path))
        except Exception:
            return None

    def _play_reward_sfx(self) -> None:
        if self.reward_sfx is None:
            self.reward_sfx = self._make_reward_sfx()
        if self.reward_sfx is None:
            return
        try:
            self.reward_sfx.set_volume(0.72)
            self.reward_sfx.play()
        except pygame.error:
            pass

    @staticmethod
    def _make_coin_sfx() -> pygame.mixer.Sound | None:
        """获得金币短音效：叮叮。优先读素材，否则合成。"""
        if not pygame.mixer.get_init():
            return None
        for name in ("sfx_coin.wav", "sfx_money.wav", "sfx_coin.ogg"):
            path = ASSETS / name
            if path.exists():
                try:
                    return pygame.mixer.Sound(str(path))
                except pygame.error:
                    pass
        path = ASSETS / "sfx_coin.wav"
        try:
            import math
            import struct
            import wave

            ASSETS.mkdir(exist_ok=True)
            fr = 22050
            notes = (987.77, 1318.5)  # B5 E6
            frames = bytearray()
            for ni, freq in enumerate(notes):
                dur = 0.07 if ni == 0 else 0.10
                n = int(fr * dur)
                for i in range(n):
                    t = i / fr
                    env = math.sin(math.pi * min(1.0, t / dur)) ** 0.5
                    env *= math.exp(-t * 8.0)
                    sample = env * (
                        0.6 * math.sin(2 * math.pi * freq * t)
                        + 0.2 * math.sin(2 * math.pi * freq * 2 * t)
                    )
                    val = int(max(-1.0, min(1.0, sample)) * 20000)
                    frames += struct.pack("<h", val)
            with wave.open(str(path), "w") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(fr)
                wf.writeframes(frames)
            return pygame.mixer.Sound(str(path))
        except Exception:
            return None

    def _play_coin_sfx(self) -> None:
        if getattr(self, "coin_sfx", None) is None:
            self.coin_sfx = self._make_coin_sfx()
        if self.coin_sfx is None:
            return
        try:
            self.coin_sfx.set_volume(0.7)
            self.coin_sfx.play()
        except pygame.error:
            pass

    def current_grid(self) -> list[list[int]]:
        assert self.map_data
        return layer_grid(self.map_data, self.layer)

    def _editor_focus_anchor(self) -> None:
        """加载 DIY：有起点则镜头对准起点，否则对准地图中心。"""
        assert self.map_data
        mw, mh = map_size(self.map_data)
        tx, ty = resolve_start(self.map_data)
        self.camera.follow(tx * TILE + TILE // 2, ty * TILE + TILE // 2, mw, mh)

    def _select_editor_brush(self, tid: int) -> None:
        """底栏/快捷键选笔刷；虚拟笔刷进入起点/公主拖放模式。"""
        self.editor_delete_pending = False
        if tid == BRUSH_PAINT:
            self.open_pixel_painter()
            return
        if tid == BRUSH_START:
            self.brush = BRUSH_START
            self.edit_mode = "start"
            self.toast("拖放设置起点（蓝框=操控小人出生格）")
            return
        if tid == BRUSH_PRINCESS:
            self.brush = BRUSH_PRINCESS
            self.edit_mode = "goal"
            self.toast("拖放放置公主=通关目标 · 右键/清除可去掉公主（自由探索）")
            return
        self.brush = tid
        self.edit_mode = "tile"
        self.paint_delete_pending = False
        name = next((n for t, n in PALETTE if t == tid), "?")
        if tid == EMPTY:
            self.toast("清除：擦地物留背景；再擦可清空整格")
        elif tid == USER_PAINT:
            self.toast("自创画 · 左键放置 · Delete删除素材 · F2/画素材重画")
        elif tid in BACKGROUND_TILES:
            self.toast(f"背景：{name} · 铺满一格")
        elif tid in LAYER_PORTALS:
            self.toast(f"地物：{name} · 叠在背景上 · 联通双层")
        elif tid in PROP_OVERLAY:
            self.toast(f"地物：{name} · 叠在背景上（已抠透明）")
        else:
            self.toast(f"笔刷：{name}")

    def open_pixel_painter(self) -> None:
        """地图编辑器内像素画板 → 可多张命名保存，并设为当前「自创画」笔刷。"""
        self.paint_return_state = self.state if self.state in ("editor", "play") else "editor"
        self.paint_cells = [0] * (PIXEL_PAINT_SIZE * PIXEL_PAINT_SIZE)
        self.paint_brush = 1
        self.paint_colors = list(PIXEL_PAINT_COLORS)
        self.paint_drag = False
        self.paint_naming = False
        self.paint_name = ""
        self.paint_edit_id = None
        self.paint_gallery = _load_paint_gallery()
        self.paint_gallery_idx = max(0, len(self.paint_gallery) - 1)
        # 尝试加载草稿
        draft = _rpg_user_root() / "user_paint_draft.json"
        if draft.is_file():
            try:
                raw = json.loads(draft.read_text(encoding="utf-8"))
                if isinstance(raw, dict) and isinstance(raw.get("cells"), list):
                    cells = raw["cells"]
                    pal = raw.get("palette")
                    if isinstance(pal, list) and pal:
                        self._set_paint_colors_from_hex(pal)
                    self.paint_cells = [
                        max(0, min(len(self.paint_colors) - 1, int(v or 0)))
                        for v in cells[: len(self.paint_cells)]
                    ]
                    while len(self.paint_cells) < PIXEL_PAINT_SIZE * PIXEL_PAINT_SIZE:
                        self.paint_cells.append(0)
                elif isinstance(raw, list) and len(raw) >= len(self.paint_cells):
                    self.paint_cells = [
                        max(0, min(len(self.paint_colors) - 1, int(v or 0)))
                        for v in raw[: len(self.paint_cells)]
                    ]
            except Exception:
                pass
        self.state = "pixel_paint"
        self.toast("画素材：Enter命名保存 · P/+取色 · [ ]图库 · Esc返回")

    def _set_paint_colors_from_hex(self, pal: list) -> None:
        """用十六进制色板重建 paint_colors（保留 0=橡皮）。"""
        colors: list[tuple[int, int, int] | None] = [None]
        for c in pal or ():
            if c in (None, "", "null"):
                continue
            if isinstance(c, str) and c.startswith("#") and len(c) >= 7:
                try:
                    colors.append((int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)))
                except Exception:
                    continue
            elif isinstance(c, (list, tuple)) and len(c) >= 3:
                try:
                    colors.append((int(c[0]), int(c[1]), int(c[2])))
                except Exception:
                    continue
        if len(colors) < 2:
            colors = list(PIXEL_PAINT_COLORS)
        self.paint_colors = colors[:24]
        if self.paint_brush >= len(self.paint_colors):
            self.paint_brush = 1

    def _paint_palette_hex(self) -> list[str | None]:
        out: list[str | None] = []
        for col in self.paint_colors:
            if not col:
                out.append(None)
            else:
                out.append("#%02x%02x%02x" % col)
        return out

    def _pick_custom_paint_color(self, *, replace_idx: int | None = None) -> None:
        """系统取色：追加色槽，或替换指定槽。"""
        try:
            import tkinter as tk
            from tkinter import colorchooser
        except Exception:
            self.toast("当前环境无法打开取色器")
            return
        root = None
        try:
            root = tk.Tk()
            root.withdraw()
            try:
                root.attributes("-topmost", True)
            except Exception:
                pass
            initial = None
            if replace_idx is not None and 0 < replace_idx < len(self.paint_colors):
                col = self.paint_colors[replace_idx]
                if col:
                    initial = "#%02x%02x%02x" % col
            kwargs: dict = {"title": "自选画笔颜色" if replace_idx is None else "替换此色"}
            if initial:
                kwargs["color"] = initial
            picked = colorchooser.askcolor(**kwargs)
        except Exception:
            picked = None
        finally:
            if root is not None:
                try:
                    root.destroy()
                except Exception:
                    pass
        if not picked or not picked[1]:
            return
        hex_c = str(picked[1]).strip()
        try:
            rgb = (int(hex_c[1:3], 16), int(hex_c[3:5], 16), int(hex_c[5:7], 16))
        except Exception:
            self.toast("颜色无效")
            return
        if replace_idx is not None and 0 < replace_idx < len(self.paint_colors):
            self.paint_colors[replace_idx] = rgb
            self.paint_brush = replace_idx
            self.toast("已替换该色")
            return
        if len(self.paint_colors) < 24:
            self.paint_colors.append(rgb)
            self.paint_brush = len(self.paint_colors) - 1
        else:
            self.paint_colors[-1] = rgb
            self.paint_brush = len(self.paint_colors) - 1
        self.toast("已加入自选色 · 可继续画")

    def _load_gallery_into_canvas(self, entry: dict) -> bool:
        cells = entry.get("cells")
        if not isinstance(cells, list) or not cells:
            # 尝试从 PNG 无法反推色板下标，仅提示
            self.toast("该作品无画板数据，请在桌宠里再编辑")
            return False
        pal = entry.get("palette")
        if isinstance(pal, list) and pal:
            self._set_paint_colors_from_hex(pal)
        else:
            self.paint_colors = list(PIXEL_PAINT_COLORS)
        n = PIXEL_PAINT_SIZE * PIXEL_PAINT_SIZE
        self.paint_cells = [0] * n
        for i in range(min(n, len(cells))):
            self.paint_cells[i] = max(0, min(len(self.paint_colors) - 1, int(cells[i] or 0)))
        self.paint_edit_id = str(entry.get("id") or "") or None
        self.paint_name = str(entry.get("name") or "")
        self.toast(f"已载入：「{self.paint_name}」")
        return True

    def _apply_gallery_as_brush(self, entry: dict) -> None:
        """把图库作品设为当前自创画笔刷。"""
        materials_dir, _ = _materials_dir_and_index()
        fname = str(entry.get("file") or "")
        src = materials_dir / fname
        if not src.is_file() and isinstance(entry.get("cells"), list):
            # 用 cells 重导出
            self.paint_cells = [
                max(0, min(len(self.paint_colors) - 1, int(v or 0)))
                for v in entry["cells"][: PIXEL_PAINT_SIZE * PIXEL_PAINT_SIZE]
            ]
            while len(self.paint_cells) < PIXEL_PAINT_SIZE * PIXEL_PAINT_SIZE:
                self.paint_cells.append(0)
            self._save_pixel_paint_asset(named=False, force_name=str(entry.get("name") or "自创画"))
            return
        if not src.is_file():
            self.toast("找不到该作品文件")
            return
        from PIL import Image

        try:
            img = Image.open(src).convert("RGBA")
            home_img = img.resize((28, 28), Image.Resampling.NEAREST)
            rpg_img = img.resize((TILE, TILE), Image.Resampling.NEAREST)
            for path in self._user_paint_file_candidates():
                path.parent.mkdir(parents=True, exist_ok=True)
                out = home_img if "home_props" in path.as_posix() else rpg_img
                out.save(path)
            meta = _rpg_user_root() / "user_paint_meta.json"
            meta.write_text(
                json.dumps({"custom": True, "id": entry.get("id"), "name": entry.get("name")}, ensure_ascii=False),
                encoding="utf-8",
            )
            self._reload_user_paint_tile()
            self.brush = USER_PAINT
            self.toast(f"笔刷已设为「{entry.get('name')}」")
        except Exception:
            self.toast("设为笔刷失败")

    def _user_paint_file_candidates(self) -> list[Path]:
        targets = [
            _rpg_user_root() / "assets" / "user_paint.png",
            ASSETS / "user_paint.png",
        ]
        try:
            import os

            local = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
            if local:
                targets.append(Path(local) / "Vpet" / "userdata" / "home_props" / "user_paint.png")
                targets.append(Path(local) / "Vpet" / "userdata" / "rpg_assets" / "user_paint.png")
                targets.append(Path(local) / "Vpet" / "rpg" / "assets" / "user_paint.png")
        except Exception:
            pass
        # 去重并保持顺序
        out: list[Path] = []
        for p in targets:
            if p not in out:
                out.append(p)
        return out

    def _user_paint_is_custom(self) -> bool:
        """是否已有可删的自创画（草稿有笔触或保存标记）。"""
        meta = _rpg_user_root() / "user_paint_meta.json"
        if meta.is_file():
            try:
                data = json.loads(meta.read_text(encoding="utf-8"))
                if isinstance(data, dict) and data.get("custom"):
                    return True
            except Exception:
                pass
        draft = _rpg_user_root() / "user_paint_draft.json"
        if draft.is_file():
            try:
                raw = json.loads(draft.read_text(encoding="utf-8"))
                if isinstance(raw, list) and any(int(v or 0) > 0 for v in raw):
                    return True
            except Exception:
                pass
        return False

    def _reload_user_paint_tile(self) -> None:
        try:
            ensure_user_art_placeholder("user_paint.png")
            surf = load_img("user_paint.png", key_bg=True)
            scaled = pygame.transform.scale(surf, (TILE, TILE))
            self.assets.tiles[USER_PAINT] = _key_outer_bg_surface(scaled)
        except Exception:
            pass

    def _strip_user_paint_from_map(self) -> int:
        """当前地图上的自创画格改回背景；返回清除格数。"""
        if not self.map_data:
            return 0
        ensure_ground_layers(self.map_data)
        cleared = 0
        for layer in ("surface", "underground"):
            grid = self.map_data.get(layer)
            if not isinstance(grid, list):
                continue
            ground = layer_ground(self.map_data, layer)
            default = default_ground_for_layer(layer)
            for y, row in enumerate(grid):
                for x, t in enumerate(row):
                    if int(t) != USER_PAINT:
                        continue
                    base = int(ground[y][x]) if int(ground[y][x]) in BACKGROUND_TILES else default
                    row[x] = base
                    ground[y][x] = base
                    cleared += 1
        return cleared

    def _delete_user_paint_asset(self, *, confirmed: bool = False) -> None:
        """删除已保存的自创画素材（文件 + 草稿），并刷新贴图。"""
        if not self._user_paint_is_custom():
            self.paint_delete_pending = False
            self.toast("当前没有可删除的自创画")
            return
        if not confirmed:
            self.paint_delete_pending = True
            self.toast("再按 Delete / X 确认删除「自创画」素材", 2.8)
            return
        self.paint_delete_pending = False
        for path in self._user_paint_file_candidates():
            try:
                if path.is_file():
                    path.unlink()
            except Exception:
                pass
        for extra in (
            _rpg_user_root() / "user_paint_draft.json",
            _rpg_user_root() / "user_paint_meta.json",
        ):
            try:
                if extra.is_file():
                    extra.unlink()
            except Exception:
                pass
        ensure_user_art_placeholder("user_paint.png")
        try:
            from PIL import Image

            src = ASSETS / "user_paint.png"
            if src.is_file():
                im = Image.open(src).convert("RGBA")
                home = im.resize((28, 28), Image.Resampling.NEAREST)
                rpg = im.resize((TILE, TILE), Image.Resampling.NEAREST)
                for path in self._user_paint_file_candidates():
                    try:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        out = home if "home_props" in path.as_posix() else rpg
                        out.save(path)
                    except Exception:
                        pass
        except Exception:
            pass
        self._reload_user_paint_tile()
        self.paint_cells = [0] * (PIXEL_PAINT_SIZE * PIXEL_PAINT_SIZE)
        cleared = self._strip_user_paint_from_map()
        if self.brush == USER_PAINT:
            self.brush = GRASS
            self.edit_mode = "tile"
        msg = "已删除「自创画」素材"
        if cleared:
            msg += f"（地图上清除 {cleared} 格）"
        self.toast(msg, 3.0)

    def _paint_cell_index(self, pos: tuple[int, int]) -> int | None:
        """画板格索引；颜色条点击返回负索引 -1-color；+取色返回 -1000。"""
        cell = 22
        grid_w = PIXEL_PAINT_SIZE * cell
        ox = (SCREEN_W - grid_w) // 2
        oy = 70
        mx, my = pos
        # 色板（与绘制一致）
        n_swatch = len(self.paint_colors) + 1  # 末尾 +取色
        pal_y = oy + grid_w + 16
        px0 = (SCREEN_W - n_swatch * 28) // 2
        if pal_y <= my <= pal_y + 26:
            idx = (mx - px0) // 28
            if idx == len(self.paint_colors):
                return -1000  # 取色
            if 0 <= idx < len(self.paint_colors):
                return -1 - idx
        if ox <= mx < ox + grid_w and oy <= my < oy + grid_w:
            gx = (mx - ox) // cell
            gy = (my - oy) // cell
            if 0 <= gx < PIXEL_PAINT_SIZE and 0 <= gy < PIXEL_PAINT_SIZE:
                return gy * PIXEL_PAINT_SIZE + gx
        return None

    def _save_pixel_paint_asset(self, *, named: bool = True, force_name: str | None = None) -> bool:
        if not any(int(v or 0) > 0 for v in self.paint_cells):
            self.toast("先画几笔再保存")
            return False
        from PIL import Image, ImageDraw

        # 命名流程
        if named and force_name is None:
            if not self.paint_naming:
                self.paint_naming = True
                self.paint_name = str(self.paint_name or self.paint_edit_id or "")[:16]
                if not self.paint_name:
                    self.paint_name = f"自创{len(self.paint_gallery) + 1}"
                self.toast("输入名字后按 Enter 确认（Backspace 改字）")
                return False
            label = (self.paint_name or "").strip()[:16] or f"自创{len(self.paint_gallery) + 1}"
            self.paint_naming = False
        else:
            label = (force_name or self.paint_name or "自创画").strip()[:16]

        scale = 4
        side = PIXEL_PAINT_SIZE * scale
        im = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for y in range(PIXEL_PAINT_SIZE):
            for x in range(PIXEL_PAINT_SIZE):
                idx = int(self.paint_cells[y * PIXEL_PAINT_SIZE + x] or 0)
                if idx <= 0 or idx >= len(self.paint_colors):
                    continue
                col = self.paint_colors[idx]
                if not col:
                    continue
                x0, y0 = x * scale, y * scale
                d.rectangle([x0, y0, x0 + scale - 1, y0 + scale - 1], fill=(*col, 255))
        if not any(im.getdata()):
            self.toast("画布是空的")
            return False
        home_img = im.resize((28, 28), Image.Resampling.NEAREST)
        rpg_img = im.resize((TILE, TILE), Image.Resampling.NEAREST)
        for path in self._user_paint_file_candidates():
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                out = home_img if "home_props" in path.as_posix() else rpg_img
                out.save(path)
            except Exception:
                pass
        # 写入共享图库（可多张）
        try:
            materials_dir, index_path = _materials_dir_and_index()
            materials_dir.mkdir(parents=True, exist_ok=True)
            mid = self.paint_edit_id or f"m{time.strftime('%Y%m%d%H%M%S')}"
            fname = f"{mid}.png"
            home_img.save(materials_dir / fname)
            items = _load_paint_gallery()
            pal = self._paint_palette_hex()
            entry = {
                "id": mid,
                "name": label,
                "file": fname,
                "source": "rpg",
                "cells": list(self.paint_cells),
                "palette": pal,
            }
            replaced = False
            for i, old in enumerate(items):
                if str(old.get("id")) == mid:
                    items[i] = entry
                    replaced = True
                    break
            if not replaced:
                items.append(entry)
            index_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
            self.paint_gallery = items
            self.paint_gallery_idx = len(items) - 1
            self.paint_edit_id = mid
            self.paint_name = label
        except Exception:
            pass
        try:
            draft = _rpg_user_root() / "user_paint_draft.json"
            draft.write_text(
                json.dumps({"cells": list(self.paint_cells), "palette": self._paint_palette_hex()}, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:
            pass
        try:
            meta = _rpg_user_root() / "user_paint_meta.json"
            meta.write_text(
                json.dumps({"custom": True, "id": self.paint_edit_id, "name": label}, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:
            pass
        self._reload_user_paint_tile()
        self.paint_delete_pending = False
        self.brush = USER_PAINT
        # 额外导出一份带时间戳的 PNG
        try:
            export_dir = _rpg_user_root().parent / "userdata" / "exports"
            if not export_dir.parent.is_dir():
                export_dir = _rpg_user_root() / "exports"
            export_dir.mkdir(parents=True, exist_ok=True)
            stamp = time.strftime("%Y%m%d_%H%M%S")
            out = export_dir / f"rpg_{label}_{stamp}.png"
            rpg_img.save(out)
        except Exception:
            pass
        self.toast(f"已保存「{label}」· 可继续画新图或 [ ] 切换图库")
        return True

    def run_pixel_paint(self, events: list) -> None:
        for e in events:
            if e.type == pygame.KEYDOWN:
                if self.paint_naming:
                    if e.key == pygame.K_ESCAPE:
                        self.paint_naming = False
                        self.toast("已取消命名")
                        continue
                    if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self._save_pixel_paint_asset(named=True)
                        continue
                    if e.key == pygame.K_BACKSPACE:
                        self.paint_name = (self.paint_name or "")[:-1]
                        continue
                    ch = e.unicode or ""
                    if ch and ch.isprintable() and len(self.paint_name or "") < 16:
                        self.paint_name = (self.paint_name or "") + ch
                    continue
                if e.key == pygame.K_ESCAPE:
                    self.paint_delete_pending = False
                    self.paint_naming = False
                    self.state = self.paint_return_state or "editor"
                    self.toast("已返回编辑器")
                    return
                if e.key in (pygame.K_RETURN, pygame.K_s):
                    self._save_pixel_paint_asset(named=True)
                    continue
                if e.key == pygame.K_LEFTBRACKET:
                    self.paint_gallery = _load_paint_gallery()
                    if self.paint_gallery:
                        self.paint_gallery_idx = (self.paint_gallery_idx - 1) % len(self.paint_gallery)
                        g = self.paint_gallery[self.paint_gallery_idx]
                        self.toast(f"图库 {self.paint_gallery_idx + 1}/{len(self.paint_gallery)}：{g.get('name')}")
                    else:
                        self.toast("图库还是空的")
                    continue
                if e.key == pygame.K_RIGHTBRACKET:
                    self.paint_gallery = _load_paint_gallery()
                    if self.paint_gallery:
                        self.paint_gallery_idx = (self.paint_gallery_idx + 1) % len(self.paint_gallery)
                        g = self.paint_gallery[self.paint_gallery_idx]
                        self.toast(f"图库 {self.paint_gallery_idx + 1}/{len(self.paint_gallery)}：{g.get('name')}")
                    else:
                        self.toast("图库还是空的")
                    continue
                if e.key == pygame.K_l:
                    self.paint_gallery = _load_paint_gallery()
                    if self.paint_gallery:
                        self.paint_gallery_idx = max(0, min(self.paint_gallery_idx, len(self.paint_gallery) - 1))
                        self._load_gallery_into_canvas(self.paint_gallery[self.paint_gallery_idx])
                    else:
                        self.toast("图库还是空的")
                    continue
                if e.key == pygame.K_a:
                    self.paint_gallery = _load_paint_gallery()
                    if self.paint_gallery:
                        self.paint_gallery_idx = max(0, min(self.paint_gallery_idx, len(self.paint_gallery) - 1))
                        self._apply_gallery_as_brush(self.paint_gallery[self.paint_gallery_idx])
                    else:
                        self.toast("图库还是空的")
                    continue
                if e.key == pygame.K_n:
                    # 新建空白，再画可另存
                    self.paint_cells = [0] * (PIXEL_PAINT_SIZE * PIXEL_PAINT_SIZE)
                    self.paint_edit_id = None
                    self.paint_name = ""
                    self.toast("新建空白画布")
                    continue
                if e.key in (pygame.K_DELETE, pygame.K_x):
                    self._delete_user_paint_asset(confirmed=bool(self.paint_delete_pending))
                    continue
                if e.key == pygame.K_c:
                    self.paint_delete_pending = False
                    self.paint_cells = [0] * (PIXEL_PAINT_SIZE * PIXEL_PAINT_SIZE)
                    self.paint_edit_id = None
                    self.toast("已清空画板")
                if e.key == pygame.K_p:
                    self._pick_custom_paint_color()
                    continue
                if pygame.K_0 <= e.key <= pygame.K_9:
                    idx = e.key - pygame.K_0
                    if idx < len(self.paint_colors):
                        self.paint_brush = idx
            if e.type == pygame.MOUSEBUTTONDOWN and not self.paint_naming:
                self.paint_delete_pending = False
                pos = self._content_mouse(e.pos)
                hit = self._paint_cell_index(pos)
                if hit is None:
                    continue
                if hit == -1000:
                    # 左键追加 / 右键替换当前笔刷色
                    if e.button == 3 and self.paint_brush > 0:
                        self._pick_custom_paint_color(replace_idx=int(self.paint_brush))
                    else:
                        self._pick_custom_paint_color()
                    continue
                if hit < 0:
                    idx = -1 - hit
                    if e.button == 3 and idx > 0:
                        self._pick_custom_paint_color(replace_idx=idx)
                    else:
                        self.paint_brush = idx
                    continue
                if e.button == 1:
                    self.paint_drag = True
                    self.paint_cells[hit] = int(self.paint_brush)
                elif e.button == 3:
                    self.paint_drag = True
                    self.paint_cells[hit] = 0
            if e.type == pygame.MOUSEBUTTONUP:
                self.paint_drag = False
            if e.type == pygame.MOUSEMOTION and self.paint_drag and not self.paint_naming:
                pos = self._content_mouse(e.pos)
                hit = self._paint_cell_index(pos)
                if hit is not None and hit >= 0:
                    buttons = pygame.mouse.get_pressed(3)
                    self.paint_cells[hit] = 0 if buttons[2] else int(self.paint_brush)

        self.screen.fill((18, 22, 34))
        title = self.font.render("画素材 · 可多张命名", True, (255, 200, 220))
        self.screen.blit(title, (16, 12))
        if self.paint_naming:
            hint = self.font_sm.render(
                f"命名中：{self.paint_name or '_'}  · Enter确认 · Esc取消",
                True,
                (255, 220, 140),
            )
        else:
            hint = self.font_sm.render(
                "Enter命名 · P/+取色 · 右键色块替换 · [ ]图库 · L载入 · A设笔刷 · N新建 · Esc",
                True,
                (170, 180, 200),
            )
        self.screen.blit(hint, (16, 36))
        if self.paint_gallery:
            g = self.paint_gallery[max(0, min(self.paint_gallery_idx, len(self.paint_gallery) - 1))]
            ghint = self.font_sm.render(
                f"图库 {self.paint_gallery_idx + 1}/{len(self.paint_gallery)}：{g.get('name')}",
                True,
                (140, 200, 180),
            )
            self.screen.blit(ghint, (16, 52))

        cell = 22
        grid_w = PIXEL_PAINT_SIZE * cell
        ox = (SCREEN_W - grid_w) // 2
        oy = 70
        pygame.draw.rect(self.screen, (10, 14, 22), (ox - 4, oy - 4, grid_w + 8, grid_w + 8))
        for y in range(PIXEL_PAINT_SIZE):
            for x in range(PIXEL_PAINT_SIZE):
                idx = int(self.paint_cells[y * PIXEL_PAINT_SIZE + x] or 0)
                col = self.paint_colors[idx] if 0 <= idx < len(self.paint_colors) else None
                rect = pygame.Rect(ox + x * cell, oy + y * cell, cell - 1, cell - 1)
                pygame.draw.rect(self.screen, col or (26, 32, 48), rect)

        pal_y = oy + grid_w + 16
        n_swatch = len(self.paint_colors) + 1
        px0 = (SCREEN_W - n_swatch * 28) // 2
        for i, col in enumerate(self.paint_colors):
            r = pygame.Rect(px0 + i * 28, pal_y, 24, 24)
            pygame.draw.rect(self.screen, col or (26, 32, 48), r)
            if i == int(self.paint_brush):
                pygame.draw.rect(self.screen, (255, 230, 120), r, 2)
            else:
                pygame.draw.rect(self.screen, (90, 100, 120), r, 1)
        plus = pygame.Rect(px0 + len(self.paint_colors) * 28, pal_y, 24, 24)
        pygame.draw.rect(self.screen, (70, 100, 130), plus)
        pygame.draw.rect(self.screen, (200, 220, 240), plus, 1)
        plus_txt = self.font_sm.render("+", True, (255, 255, 255))
        self.screen.blit(plus_txt, (plus.x + 7, plus.y + 3))
        bar = "画素材 · 点 + 或按 P 自选颜色（右键色块可替换）"
        if self.paint_naming:
            bar = f"命名：{self.paint_name or ''}|"
        elif self.paint_delete_pending:
            bar = "再按 Delete / X 确认删除当前自创画笔刷！"
        self.draw_ui_bar(bar)

    def _make_player(self, tile_xy: tuple[int, int]) -> Knight:
        kind = self.player_kind if self.player_kind in PLAYER_KINDS else "knight"
        self.player_kind = kind
        return Knight(self.assets, tile_xy, kind=kind)

    def cycle_player_kind(self) -> None:
        """切换操控角色：knight ↔ aoba ↔ ren。"""
        kinds = PLAYER_KINDS
        try:
            idx = kinds.index(self.player_kind)
        except ValueError:
            idx = 0
        self.player_kind = kinds[(idx + 1) % len(kinds)]
        if self.knight:
            self.knight.set_kind(self.player_kind)
        label = PLAYER_KIND_LABELS.get(self.player_kind, self.player_kind)
        self.toast(f"操控角色：{label}（C 切换）")

    def start_campaign(self) -> None:
        self.campaign = True
        self.level_idx = 0
        self.total_treasures = 0
        # 点 START 立刻播 startmusic（再进第一关）
        self._begin_adventure_bgm()
        self._load_level(0)

    def _load_level(self, idx: int) -> None:
        self.level_idx = idx
        data = generate_level(idx)
        self.map_data = data
        self.layer = "surface"
        self.knight = self._make_player(resolve_start(data))
        self.treasures = 0
        self.hp = self.max_hp = RPG_MAX_HP
        self.chest_event = None
        self.hazard_cd = 0.0
        self._last_hazard_tile = None
        self.map_trap_cd = 0.0
        self._last_map_trap_tile = None
        self.revealed_traps = set()
        self.stairs_cd = 0.0
        self._reset_mario_state(keep_coins=bool(self.campaign and idx > 0))
        self.spawn_level_pickups()
        self.state = "play"
        if self.campaign:
            note_rpg_best_level(idx)
        mw, mh = map_size(data)
        self.camera.follow(self.knight.x, self.knight.y, mw, mh)
        tip = "寻找公主！" if data["princess"] else "找到地下金色关卡门进入下一关"
        self.toast(f"{data['name']} — {tip}（I背包吃食物 · 捡金币/蘑菇/星）")

    def start_play(self, data: dict, campaign: bool = False) -> None:
        """加载地图后先选操控角色（knight/aoba/ren），再开局。"""
        # 兼容旧单层 DIY
        if "surface" not in data:
            data = self._migrate_old_map(data)
        data = normalize_map_tiles(data)
        self.pending_play = {"data": data, "campaign": bool(campaign)}
        self.campaign = bool(campaign)  # 选角页起就区分 DIY / 战役（耐久显示）
        try:
            self.kind_select_idx = PLAYER_KINDS.index(self.player_kind)
        except ValueError:
            self.kind_select_idx = 0
        self.state = "kind_select"
        self.toast("选择操控角色：knight / aoba / ren")

    def _begin_play_after_kind(self) -> None:
        assert self.pending_play
        data = self.pending_play["data"]
        campaign = bool(self.pending_play["campaign"])
        self.pending_play = None
        self.player_kind = PLAYER_KINDS[self.kind_select_idx]
        self.campaign = campaign
        self.map_data = data
        self.layer = "surface"
        spawn = resolve_start(data)
        self.knight = self._make_player(spawn)
        self.treasures = 0
        self.hp = self.max_hp = RPG_MAX_HP
        self.chest_event = None
        self.hazard_cd = 0.0
        self._last_hazard_tile = None
        self.map_trap_cd = 0.0
        self._last_map_trap_tile = None
        self.revealed_traps = set()
        self.stairs_cd = 0.0
        self._reset_mario_state(keep_coins=False)
        self.spawn_level_pickups()
        self.state = "play"
        # DIY / 自建地图试玩：不放冒险 BGM
        if campaign:
            self._begin_adventure_bgm()
        else:
            self.stop_bgm()
        mw, mh = map_size(data)
        self.camera.follow(self.knight.x, self.knight.y, mw, mh)
        tip = " · WASD移动 · C切换角色 · 踩楼梯/洞窟切层"
        if campaign:
            tip = " · I背包补耐久" + tip
        if data.get("princess"):
            tip = " · 找到公主通关" + tip
        else:
            tip = " · 自由探索（无通关）" + tip
        if not has_start(data):
            tip = " · 未设起点，从地图中心出发" + tip
        kind_cn = PLAYER_KIND_LABELS.get(self.player_kind, self.player_kind)
        self.toast(f"{data.get('name', '探险开始')}（{kind_cn}）" + tip)

    def _kind_select_rects(self) -> list[tuple[pygame.Rect, str]]:
        """选角页：knight / aoba(Vpet) / ren(Allmate) 三卡片。"""
        n = len(PLAYER_KINDS)
        card_w, card_h, gap = 140, 180, 18
        total = card_w * n + gap * (n - 1)
        x0 = (SCREEN_W - total) // 2
        y0 = VIEW_H // 2 - card_h // 2 - 10
        return [
            (pygame.Rect(x0 + i * (card_w + gap), y0, card_w, card_h), kind)
            for i, kind in enumerate(PLAYER_KINDS)
        ]

    def run_kind_select(self, events: list) -> None:
        """地图加载后：选择操控对象。"""
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.pending_play = None
                    self.enter_menu(play_intro=False)
                    return
                if e.key in (pygame.K_LEFT, pygame.K_a):
                    self.kind_select_idx = (self.kind_select_idx - 1) % len(PLAYER_KINDS)
                elif e.key in (pygame.K_RIGHT, pygame.K_d):
                    self.kind_select_idx = (self.kind_select_idx + 1) % len(PLAYER_KINDS)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                    self._begin_play_after_kind()
                    return
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                pos = self._content_mouse(e.pos)
                for i, (rect, _kind) in enumerate(self._kind_select_rects()):
                    if rect.collidepoint(pos):
                        self.kind_select_idx = i
                        self._begin_play_after_kind()
                        return

        self.screen.fill((18, 22, 36))
        title = self.font.render("选择操控角色", True, (255, 230, 140))
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 36))
        sub = self.font_sm.render("← → 选择 · Enter 确认 · Esc 返回", True, (170, 180, 200))
        self.screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, 64))

        for i, (rect, kind) in enumerate(self._kind_select_rects()):
            selected = i == self.kind_select_idx
            bg = (48, 56, 82) if selected else (32, 38, 56)
            border = (255, 220, 100) if selected else (90, 100, 130)
            pygame.draw.rect(self.screen, bg, rect, border_radius=8)
            pygame.draw.rect(self.screen, border, rect, 2 if selected else 1, border_radius=8)
            sheet = self.assets.players.get(kind) or self.assets.knight
            frames = sheet.get("down") or list(sheet.values())[0]
            spr = frames[0]
            # 选角预览：已抠外圈背景
            scale = 2.0 if kind != "knight" else 2.2
            big = pygame.transform.scale(
                spr, (max(1, int(spr.get_width() * scale)), max(1, int(spr.get_height() * scale)))
            )
            self.screen.blit(
                big,
                (rect.centerx - big.get_width() // 2, rect.y + 22),
            )
            label = PLAYER_KIND_LABELS.get(kind, kind)
            txt = self.font.render(label, True, (255, 240, 200) if selected else (210, 215, 230))
            self.screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.bottom - 36))
        tip = self.font_sm.render(FUTURE_COMPANION_TIP, True, (155, 170, 200))
        self.screen.blit(tip, (SCREEN_W // 2 - tip.get_width() // 2, VIEW_H - 28))
        self.draw_ui_bar("加载完成 · knight / aoba(Vpet) / ren(Allmate)")

    def _migrate_old_map(self, data: dict) -> dict:
        w, h = data["width"], data["height"]
        surface = data["tiles"]
        under = blank_grid(w, h, BRICK)
        border_wall(under, ROCK)
        return {
            **data,
            "surface": surface,
            "underground": under,
            "goal_layer": "surface",
            "princess": True,
            "stairs": [],
            "caves": [],
            "name": data.get("name", "自定义地图"),
            "level": 0,
        }

    def start_editor(self, data: dict | None = None, path: Path | None = None) -> None:
        if data is None:
            # 空白画布：无草地填满、无边框、无预设房屋
            w, h = 52, 40
            surface = blank_grid(w, h, EMPTY)
            under = blank_grid(w, h, EMPTY)
            sx, sy = w // 2, h // 2
            data = {
                "width": w,
                "height": h,
                "surface": surface,
                "underground": under,
                "start": [sx, sy],
                "goal": None,
                "goal_layer": "surface",
                "princess": False,
                "stairs": [],
                "caves": [],
                "name": "DIY 地图",
                "level": 0,
                "tile_schema": 2,
            }
            path = None
        elif "surface" not in data:
            data = self._migrate_old_map(data)
        data = normalize_map_tiles(data)
        self.map_data = data
        self.edit_map_path = path
        self.editor_delete_pending = False
        self.layer = "surface"
        self.edit_layer = "surface"
        self.edit_mode = "tile"
        self.state = "editor"
        self._editor_focus_anchor()
        hint = path.name if path else "新地图"
        focus = "起点" if has_start(data) else "地图中心"
        mode = "有公主通关" if data.get("princess") else "自由探索"
        self.toast(
            f"{hint} · {mode} · 镜头→{focus} | 蓝框=起点 · 公主可拖放/右键去掉 | "
            f"Tab切层 · Ctrl+S 保存 · Shift+S/导出 另存文件"
        )

    def draw_visible_map(self, surf: pygame.Surface, grid: list[list[int]], mw: int, mh: int, show_goal: bool) -> None:
        assert self.map_data
        ensure_ground_layers(self.map_data)
        # 编辑器看 edit_layer；游玩看 self.layer —— 传入的 grid 已对应正确层
        view_layer = self.edit_layer if self.state == "editor" else self.layer
        ground = layer_ground(self.map_data, view_layer)

        tx0 = max(0, int(self.camera.x) // TILE)
        ty0 = max(0, int(self.camera.y) // TILE)
        tx1 = min(mw, tx0 + VIEW_TILES_X + 2)
        ty1 = min(mh, ty0 + VIEW_TILES_Y + 2)

        default_base = BRICK if view_layer == "underground" else GRASS
        for y in range(ty0, ty1):
            for x in range(tx0, tx1):
                t = grid[y][x]
                sx, sy = self.camera.apply(x * TILE, y * TILE)
                if t == EMPTY:
                    # 未绘制格：暗底空白画布
                    pygame.draw.rect(surf, (16, 18, 26), (sx, sy, TILE, TILE))
                    continue

                # 背景铺满；地物叠在对应 ground 上
                if t in BACKGROUND_TILES:
                    base = t
                elif t in PROP_OVERLAY:
                    g = int(ground[y][x]) if y < len(ground) and x < len(ground[y]) else default_base
                    base = g if g in BACKGROUND_TILES else default_base
                else:
                    base = t if t in self.assets.tiles else default_base

                img = self.assets.tiles.get(base) or self.assets.tiles[GRASS]
                surf.blit(img, (sx, sy))

                if t == STAIRS:
                    stair_img = (
                        self.assets.stairs_up if view_layer == "underground" else self.assets.tiles[STAIRS]
                    )
                    surf.blit(stair_img, (sx, sy))
                elif t in PROP_OVERLAY and t != STAIRS and t in self.assets.tiles:
                    prop = self.assets.tiles[t]
                    # 游玩中：陷阱默认极淡，踩中后才显示完整贴图（编辑器始终完整）
                    if t in TRAP_TILES and self.state != "editor":
                        trap_key = (view_layer, int(x), int(y))
                        if trap_key not in getattr(self, "revealed_traps", set()):
                            prop = getattr(self.assets, "trap_hidden", {}).get(t, prop)
                    if t in (HOUSE, GATE):
                        # 高大物体：以格底为脚点，向上伸出多格
                        ox = sx + (TILE - prop.get_width()) // 2
                        oy = sy + TILE - prop.get_height()
                    elif t in (TREE, MOUNTAIN):
                        # 树木/景区：严格 TILE×TILE，贴齐当前格
                        ox, oy = sx, sy
                    else:
                        ox = sx + (TILE - prop.get_width()) // 2
                        oy = sy + (TILE - prop.get_height()) // 2
                    surf.blit(prop, (ox, oy))

        if show_goal:
            goal = self.map_data.get("goal")
            if isinstance(goal, (list, tuple)) and len(goal) >= 2:
                gx, gy = int(goal[0]), int(goal[1])
                if self.layer == self.map_data.get("goal_layer", "surface"):
                    if self.map_data.get("princess"):
                        pr = self.assets.princess
                        sx, sy = self.camera.apply(
                            gx * TILE + (TILE - pr.get_width()) // 2,
                            gy * TILE + TILE - pr.get_height(),
                        )
                        surf.blit(pr, (sx, sy))
                    else:
                        # 非终关已用地图 GATE 绘制
                        pass

        # 起点蓝框：表示操控小人出生格（编辑器；有合法起点时）
        if self.state == "editor" and has_start(self.map_data):
            sx0, sy0 = int(self.map_data["start"][0]), int(self.map_data["start"][1])
            sx, sy = self.camera.apply(sx0 * TILE, sy0 * TILE)
            fill = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
            fill.fill(START_MARKER_FILL)
            surf.blit(fill, (sx, sy))
            pygame.draw.rect(surf, START_MARKER_COLOR, (sx + 2, sy + 2, TILE - 4, TILE - 4), 3)

    def draw_ui_bar(self, text: str) -> None:
        bar = pygame.Rect(0, VIEW_H, SCREEN_W, UI_H)
        pygame.draw.rect(self.screen, (28, 32, 48), bar)
        pygame.draw.line(self.screen, (90, 100, 130), (0, VIEW_H), (SCREEN_W, VIEW_H), 2)
        durable = self.uses_durability()
        row_y = VIEW_H + 6
        x = 12
        if durable:
            # 马里奥式血条（仅战役）
            hp_w, hp_h = 140, 12
            ratio = 0.0 if self.max_hp <= 0 else max(0.0, min(1.0, self.hp / self.max_hp))
            pygame.draw.rect(self.screen, (40, 44, 58), (x, row_y, hp_w, hp_h))
            fill_c = (68, 220, 120) if ratio > 0.45 else ((240, 180, 60) if ratio > 0.2 else (230, 70, 70))
            pygame.draw.rect(self.screen, fill_c, (x, row_y, int(hp_w * ratio), hp_h))
            pygame.draw.rect(self.screen, (200, 200, 210), (x, row_y, hp_w, hp_h), 1)
            hp_lbl = self.font_sm.render(f"耐久 {self.hp}/{self.max_hp}", True, (230, 230, 240))
            self.screen.blit(hp_lbl, (x + hp_w + 8, row_y - 1))
            x = x + hp_w + 100
            food_n = self.food_bag_count()
            food_lbl = self.font_sm.render(f"食物 {food_n}", True, (255, 200, 120))
            self.screen.blit(food_lbl, (x, row_y - 1))
            x += 80
            coin_lbl = self.font_sm.render(f"金币 {self.coins}", True, (255, 220, 80))
            self.screen.blit(coin_lbl, (x, row_y - 1))
        elif self.state == "play":
            # DIY 试玩：不显示耐久
            coin_lbl = self.font_sm.render(f"金币 {self.coins}", True, (255, 220, 80))
            self.screen.blit(coin_lbl, (12, row_y - 1))
            mode_lbl = self.font_sm.render("DIY · 无耐久", True, (160, 175, 200))
            self.screen.blit(mode_lbl, (12 + coin_lbl.get_width() + 16, row_y - 1))
        self.screen.blit(self.font_sm.render(text, True, (200, 205, 220)), (12, VIEW_H + 24))
        if self.message_t > 0 and self.message:
            # 判定结果用更大字号 + 更醒目颜色（成功偏绿 / 失败偏红 / 其它金黄）
            msg = self.message
            if msg.startswith("判定成功"):
                col = (120, 255, 170)
                fnt = self.font
            elif msg.startswith("判定失败"):
                col = (255, 150, 140)
                fnt = self.font
            else:
                col = (255, 220, 100)
                fnt = self.font_sm
            tip = fnt.render(msg, True, col)
            # 过长则截断尾部，避免挤出屏幕
            max_w = SCREEN_W - 24
            if tip.get_width() > max_w:
                while msg and fnt.size(msg + "…")[0] > max_w:
                    msg = msg[:-1]
                tip = fnt.render(msg + "…", True, col)
            self.screen.blit(tip, (12, VIEW_H + 44))

    def draw_textbox(self, surf: pygame.Surface, rect: pygame.Rect) -> None:
        """用 text.png 拉伸为对白框（保留底部三角箭头）。"""
        frame = pygame.transform.scale(self.assets.text_frame, (rect.w, rect.h))
        surf.blit(frame, rect.topleft)

    def _reset_logo_anim_targets(self) -> None:
        """两 logo 终点相同；启动时刻不同，但同一 intro_dur 抵达。"""
        l1 = self.assets.start_logo1
        l2 = self.assets.start_logo2
        h = max(l1.get_height(), l2.get_height())
        # 顶部留白，Logo 下方给菜单完整空间
        menu_block = 36 * len(self.menu_items) + 48
        meet_y = max(10.0, (SCREEN_H - menu_block - h) * 0.28)
        self.logo_meet_y = meet_y
        self.logo1_target_y = meet_y
        self.logo2_target_y = meet_y
        self.logo1_start_y = -float(h) - 36
        self.logo2_start_y = float(SCREEN_H) + 36
        self.logo1_y = self.logo1_start_y
        self.logo2_y = self.logo2_start_y
        self.intro_t = 0.0

    @staticmethod
    def _ease_in_out(t: float) -> float:
        t = max(0.0, min(1.0, t))
        return t * t * (3.0 - 2.0 * t)

    def _skip_prologue(self) -> None:
        """开场剧情一键跳过 → 标题页（仍播 logo 动画）。"""
        self.enter_menu(play_intro=True)

    def enter_menu(self, play_intro: bool = True) -> None:
        self.flush_wallet_earned()
        self.state = "menu"
        self.stop_bgm()
        if play_intro:
            self._reset_logo_anim_targets()
            self.intro_done = False
            self.menu_fade = 0.0
        else:
            self.logo1_y = self.logo1_target_y
            self.logo2_y = self.logo2_target_y
            self.intro_done = True
            self.menu_fade = 1.0

    def stop_bgm(self) -> None:
        self._bgm_phase = None
        if not pygame.mixer.get_init():
            return
        try:
            pygame.mixer.music.set_endevent()
            pygame.mixer.music.stop()
        except pygame.error:
            pass

    def _apply_music_volume(self) -> None:
        if not pygame.mixer.get_init():
            return
        try:
            if getattr(self, "_bgm_phase", None) == "start":
                # 开场 startmusic：固定大声，不受循环 BGM 的低默认音量拖累
                vol = max(STARTMUSIC_VOLUME, min(1.0, float(self.music_volume) * STARTMUSIC_VOLUME_MULT))
            else:
                vol = float(self.music_volume)
            pygame.mixer.music.set_volume(max(0.0, min(1.0, vol)))
        except pygame.error:
            pass

    def adjust_music_volume(self, delta: float) -> None:
        """音量加减键调节 BGM（0%~100%）。"""
        old = self.music_volume
        self.music_volume = max(0.0, min(1.0, self.music_volume + delta))
        if abs(self.music_volume - old) < 1e-6:
            pct = int(round(self.music_volume * 100))
            self.toast(f"音量 {pct}%")
            return
        self._apply_music_volume()
        self.toast(f"音量 {int(round(self.music_volume * 100))}%")

    def _handle_volume_keys(self, events: list) -> None:
        # SDL_SCANCODE_VOLUMEUP / VOLUMEDOWN（部分键盘媒体键）；并兼容 +/- 与小键盘
        vol_up_scan = {128}
        vol_down_scan = {129}
        for e in events:
            if e.type != pygame.KEYDOWN:
                continue
            key = e.key
            scan = getattr(e, "scancode", None)
            if (
                key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS)
                or scan in vol_up_scan
            ):
                self.adjust_music_volume(MUSIC_VOLUME_STEP)
            elif (
                key in (pygame.K_MINUS, pygame.K_KP_MINUS)
                or scan in vol_down_scan
            ):
                self.adjust_music_volume(-MUSIC_VOLUME_STEP)

    def _begin_adventure_bgm(self) -> None:
        """点 START / 进入游玩：先播 startmusic（大声），结束后续播循环 music。"""
        if not pygame.mixer.get_init():
            return
        if self._bgm_phase in ("start", "loop"):
            # 已在冒险 BGM 中（如下一关）则保持循环
            if self._bgm_phase == "loop":
                return
            # start 未结束则继续等结束事件
            return
        start_path = self._resolve_audio(STARTMUSIC_NAMES)
        if start_path is not None:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
                pygame.mixer.music.load(str(start_path))
                self._bgm_phase = "start"
                self._apply_music_volume()
                pygame.mixer.music.play(0)
                # 部分后端需 play 后再设一次音量才生效
                self._apply_music_volume()
                return
            except pygame.error:
                pass
        self._play_loop_music()

    def _play_loop_music(self) -> None:
        if not pygame.mixer.get_init():
            return
        loop_path = self._resolve_audio(LOOPMUSIC_NAMES)
        if loop_path is None:
            self._bgm_phase = None
            return
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.set_endevent()
            pygame.mixer.music.load(str(loop_path))
            pygame.mixer.music.play(-1)
            self._apply_music_volume()
            self._bgm_phase = "loop"
        except pygame.error:
            self._bgm_phase = None

    def _on_music_end_event(self) -> None:
        if self._bgm_phase == "start":
            self._play_loop_music()

    def _prologue_display_line(self, idx: int | None = None) -> str:
        i = self.prologue_idx if idx is None else idx
        return self.dialog_quote(self.prologue_lines[i])

    def _prologue_advance(self) -> None:
        """跳过当前打字 / 进入下一句 / 结束剧情。"""
        line = self._prologue_display_line()
        if self.prologue_chars < len(line):
            self.prologue_chars = len(line)
            self.prologue_hold = 0.0
            return
        if self.prologue_idx < len(self.prologue_lines) - 1:
            self.prologue_idx += 1
            self.prologue_chars = 0
            self.prologue_timer = 0.0
            self.prologue_hold = 0.0
            return
        self.prologue_done_fade = True
        self.prologue_fade_out = 0.0

    def run_prologue(self, events: list, dt: float) -> None:
        for e in events:
            if e.type == pygame.KEYDOWN:
                # ESC / S / 鼠标也可跳过整段开场
                if e.key in (pygame.K_ESCAPE, pygame.K_s):
                    self._skip_prologue()
                    return
                if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.prologue_done_fade:
                        self.enter_menu(play_intro=True)
                        return
                    self._prologue_advance()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                # 点一下：未打完则跳过本句；打完则下一段；淡出中则进标题
                if self.prologue_done_fade:
                    self.enter_menu(play_intro=True)
                    return
                line = self._prologue_display_line()
                if self.prologue_chars < len(line):
                    self.prologue_chars = len(line)
                    self.prologue_hold = 0.0
                else:
                    self._prologue_advance()

        # 打字推进（按 *「…」整句揭示）
        if not self.prologue_done_fade:
            line = self._prologue_display_line()
            if self.prologue_chars < len(line):
                self.prologue_timer += dt
                while self.prologue_timer >= self.prologue_char_delay and self.prologue_chars < len(line):
                    self.prologue_timer -= self.prologue_char_delay
                    self.prologue_chars += 1
                    ch = line[self.prologue_chars - 1]
                    if self.type_sfx and ch not in ("…", "，", " ", "*", "「", "」"):
                        self.type_sfx.play()
            else:
                self.prologue_hold += dt
                if self.prologue_hold >= self.prologue_line_hold:
                    if self.prologue_idx < len(self.prologue_lines) - 1:
                        self.prologue_idx += 1
                        self.prologue_chars = 0
                        self.prologue_timer = 0.0
                        self.prologue_hold = 0.0
                    else:
                        self.prologue_done_fade = True
                        self.prologue_fade_out = 0.0
        else:
            self.prologue_fade_out += dt
            if self.prologue_fade_out >= self.prologue_fade_dur:
                self.enter_menu(play_intro=True)
                return

        # —— 绘制：漆黑 + 公主（结束时淡出消失）——
        self.screen.fill((0, 0, 0))
        fade_t = 0.0
        if self.prologue_done_fade:
            fade_t = min(1.0, self.prologue_fade_out / max(0.01, self.prologue_fade_dur))
        princess_a = max(0, min(255, int(255 * (1.0 - fade_t))))

        if princess_a > 0:
            glow = pygame.Surface((220, 220), pygame.SRCALPHA)
            for r, a in ((100, 22), (70, 36), (40, 50)):
                pygame.draw.circle(glow, (90, 70, 120, int(a * princess_a / 255)), (110, 110), r)
            self.screen.blit(glow, (SCREEN_W // 2 - 110, SCREEN_H // 2 - 170))

            pr = self.assets.princess
            big = pr
            if princess_a < 255:
                big = pr.copy()
                big.set_alpha(princess_a)
            bob = math.sin(pygame.time.get_ticks() / 700.0) * 3
            px = SCREEN_W // 2 - big.get_width() // 2
            py = int(SCREEN_H // 2 - big.get_height() // 2 - 28 + bob)
            self.screen.blit(big, (px, py))

        # 文本框随公主一起淡出：更窄更高，夹在公主与底部操作说明之间
        if princess_a > 0:
            box_w = min(420, SCREEN_W - 140)
            box_h = 118
            hint_reserve = 34
            box_x = (SCREEN_W - box_w) // 2
            box_y = SCREEN_H - hint_reserve - box_h - 12
            # 避免盖住公主（中部偏上）：下限压在公主脚下方附近
            princess_clear_y = SCREEN_H // 2 + 56
            box_y = max(princess_clear_y, min(box_y, SCREEN_H - hint_reserve - box_h - 8))
            box = pygame.Rect(box_x, box_y, box_w, box_h)
            box_surf = pygame.transform.scale(self.assets.text_frame, (box.w, box.h)).copy()
            if princess_a < 255:
                box_surf.set_alpha(princess_a)
            self.screen.blit(box_surf, box.topleft)

            full = self._prologue_display_line()
            shown = full[: self.prologue_chars]
            cursor = ""
            if not self.prologue_done_fade and self.prologue_chars < len(full):
                if (pygame.time.get_ticks() // 400) % 2 == 0:
                    cursor = "_"
            text_surf = self.font.render(shown + cursor, True, (255, 255, 255))
            if princess_a < 255:
                text_surf = text_surf.copy()
                text_surf.set_alpha(princess_a)
            text_x = box.x + (box.w - text_surf.get_width()) // 2
            text_y = box.y + max(18, (box.h - text_surf.get_height()) // 2 - 4)
            self.screen.blit(text_surf, (text_x, text_y))

            hint = self.font_sm.render("ENTER/SPACE/点击 继续     ESC/S 跳过开场", True, (200, 200, 200))
            if princess_a < 255:
                hint = hint.copy()
                hint.set_alpha(princess_a)
            hint_x = (SCREEN_W - hint.get_width()) // 2
            hint_y = SCREEN_H - hint_reserve + 4
            self.screen.blit(hint, (hint_x, hint_y))
        else:
            skip = self.font_sm.render("ESC / S — Skip", True, (160, 170, 190))
            self.screen.blit(skip, (SCREEN_W // 2 - skip.get_width() // 2, SCREEN_H - 36))

    def draw_window_frame(self) -> None:
        """黑底衬托 + 外边框包住整个内容区。"""
        self.window.fill((0, 0, 0))
        self.window.blit(self.screen, (FRAME_PAD, FRAME_PAD))
        self.window.blit(self.assets.window_frame, (0, 0))

    def _content_mouse(self, pos: tuple[int, int]) -> tuple[int, int]:
        """窗口坐标 → 内容区坐标。"""
        return pos[0] - FRAME_PAD, pos[1] - FRAME_PAD

    def run_menu(self, events: list, dt: float) -> None:
        for e in events:
            if e.type == pygame.KEYDOWN:
                if not self.intro_done and e.key in (
                    pygame.K_RETURN,
                    pygame.K_SPACE,
                    pygame.K_ESCAPE,
                    pygame.K_s,
                ):
                    self.logo1_y = self.logo1_target_y
                    self.logo2_y = self.logo2_target_y
                    self.intro_done = True
                    self.menu_fade = 1.0
                    continue
                if not self.intro_done:
                    continue
                if e.key in (pygame.K_UP, pygame.K_w):
                    self.menu_idx = (self.menu_idx - 1) % len(self.menu_items)
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.menu_idx = (self.menu_idx + 1) % len(self.menu_items)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._menu_select()
                elif e.key == pygame.K_e:
                    self.menu_idx = 2
                    self._menu_select()
                elif e.key == pygame.K_c:
                    self.menu_idx = 1
                    self._menu_select()
                elif e.key == pygame.K_l:
                    self.menu_idx = 3
                    self._menu_select()
                elif e.key == pygame.K_ESCAPE:
                    self.menu_idx = 4
                    self._menu_select()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and not self.intro_done:
                self.logo1_y = self.logo1_target_y
                self.logo2_y = self.logo2_target_y
                self.intro_done = True
                self.menu_fade = 1.0

        # logo1 先动、logo2 稍后；缓动汇合
        if not self.intro_done:
            self.intro_t += dt

            def _logo_progress(delay: float) -> float:
                if self.intro_t <= delay:
                    return 0.0
                span = max(0.01, self.intro_dur - delay)
                return self._ease_in_out((self.intro_t - delay) / span)

            p1 = _logo_progress(self.logo1_delay)
            p2 = _logo_progress(self.logo2_delay)
            self.logo1_y = self.logo1_start_y + (self.logo1_target_y - self.logo1_start_y) * p1
            self.logo2_y = self.logo2_start_y + (self.logo2_target_y - self.logo2_start_y) * p2
            if self.intro_t >= self.intro_dur:
                self.logo1_y = self.logo1_target_y
                self.logo2_y = self.logo2_target_y
                self.intro_done = True
        if self.intro_done:
            self.menu_fade = min(1.0, self.menu_fade + dt * self.menu_fade_speed)

        self.screen.fill(self.assets.start_bg)

        l1 = self.assets.start_logo1
        l2 = self.assets.start_logo2
        lx = SCREEN_W // 2 - l1.get_width() // 2
        self.screen.blit(l1, (lx, int(self.logo1_y)))
        self.screen.blit(l2, (lx, int(self.logo2_y)))

        if self.menu_fade > 0.01:
            alpha = int(255 * self.menu_fade)
            row_h = 34
            menu_h = row_h * len(self.menu_items)
            # Logo 底边之下居中放置菜单，保证 5 项完整可见
            logo_bottom = int(self.logo_meet_y) + max(l1.get_height(), l2.get_height())
            menu_top = logo_bottom + 14
            max_top = SCREEN_H - menu_h - 44
            if menu_top > max_top:
                menu_top = max(8, max_top)
            for i, (label, key) in enumerate(self.menu_items):
                selected = i == self.menu_idx and self.intro_done
                color = (255, 230, 120) if selected else (235, 240, 250)
                prefix = "> " if selected else "  "
                left = self.font_pixel.render(prefix + label, True, color)
                right = self.font_pixel_sm.render(
                    f"[{key}]", True, (200, 210, 230) if selected else (160, 175, 195)
                )
                left.set_alpha(alpha)
                right.set_alpha(alpha)
                y = menu_top + i * row_h
                self.screen.blit(left, (SCREEN_W // 2 - 150, y))
                self.screen.blit(right, (SCREEN_W // 2 + 100, y + 4))

            hint = self.font_sm.render("W/S 选择   ENTER 确认   ESC 退出", True, (190, 200, 220))
            hint.set_alpha(alpha)
            self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 28))
            best_line = format_rpg_best_level_line()
            best = self.font_sm.render(best_line, True, (255, 210, 140))
            best.set_alpha(alpha)
            self.screen.blit(best, (SCREEN_W // 2 - best.get_width() // 2, SCREEN_H - 52))
        elif not self.intro_done:
            skip = self.font_sm.render("ENTER / SPACE / 点击 — 跳过动画", True, (180, 190, 210))
            self.screen.blit(skip, (SCREEN_W // 2 - skip.get_width() // 2, SCREEN_H - 28))

    def _menu_select(self) -> None:
        i = self.menu_idx
        if i == 0:
            self.start_campaign()
        elif i == 1:
            self.open_save_picker()
        elif i == 2:
            self.start_editor()
        elif i == 3:
            self.open_map_picker(for_editor=False)
        else:
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def try_use_stairs(self) -> None:
        """兼容旧名：楼梯 / 洞窟层切换。"""
        self.try_use_layer_portal()

    def try_use_layer_portal(self) -> None:
        assert self.map_data and self.knight
        if self.stairs_cd > 0 or self.layer_flash > 0.55:
            return
        tx, ty = self.knight.tile_pos()
        mw, mh = map_size(self.map_data)
        if not (0 <= tx < mw and 0 <= ty < mh):
            return
        cell = self.current_grid()[ty][tx]
        if cell not in LAYER_PORTALS:
            return
        # 刚穿过后仍站在对侧入口上：不再反复切换
        if self.portal_stand_lock == (self.layer, tx, ty):
            return
        self.layer = "underground" if self.layer == "surface" else "surface"
        # 对侧同格强制对齐为同一种门户（楼梯/洞窟可并存于地图，但同格类型一致）
        other = layer_grid(self.map_data, self.layer)
        other[ty][tx] = cell
        self.knight.place_on_tile(tx, ty)
        self.stairs_cd = 0.55
        self.layer_flash = 1.0
        self.portal_stand_lock = (self.layer, tx, ty)
        where = "地下" if self.layer == "underground" else "地面"
        via = "洞窟" if cell == CAVE else "楼梯"
        self.toast(f"穿过{via}，来到了{where}")

    def check_goal(self) -> None:
        assert self.map_data and self.knight
        # DIY 无公主：自由探索，不通关
        if not self.map_data.get("princess") and not self.campaign:
            return
        if self.layer != self.map_data.get("goal_layer", "surface"):
            return
        goal = self.map_data.get("goal")
        if not isinstance(goal, (list, tuple)) or len(goal) < 2:
            return
        gx, gy = int(goal[0]), int(goal[1])
        if abs(self.knight.x - (gx * TILE + TILE // 2)) > 24:
            return
        if abs(self.knight.y - (gy * TILE + TILE // 2)) > 24:
            return
        self.total_treasures += self.treasures
        if self.campaign and not self.map_data.get("princess"):
            nxt = self.level_idx + 1
            if nxt < len(LEVEL_DEFS):
                self.state = "levelclear"
            else:
                self.state = "win"
        else:
            # 有公主（或战役公主关）：到达公主通关
            self.state = "win"

    def run_play(self, events: list, dt: float) -> None:
        assert self.map_data and self.knight
        mw, mh = map_size(self.map_data)
        grid = self.current_grid()

        if self.hazard_cd > 0:
            self.hazard_cd = max(0.0, self.hazard_cd - dt)
        if self.map_trap_cd > 0:
            self.map_trap_cd = max(0.0, self.map_trap_cd - dt)

        for e in events:
            if e.type == pygame.KEYDOWN:
                if self.chest_event:
                    self.handle_chest_event_key(e.key)
                    continue
                if self.bag_open:
                    self.handle_bag_key(e.key)
                    continue
                if self.dialog:
                    if e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e, pygame.K_ESCAPE):
                        self.close_dialog()
                    continue
                if e.key == pygame.K_ESCAPE:
                    self.enter_menu(play_intro=False)
                    return
                if e.key in (pygame.K_i, pygame.K_b):
                    self.toggle_bag()
                    continue
                if e.key == pygame.K_c:
                    self.cycle_player_kind()
                if e.key == pygame.K_r and self.campaign:
                    self._load_level(self.level_idx)
                    return
                # F5 / Ctrl+S 存档（部分笔记本 Fn 锁会导致 F5 无效，故保留 Ctrl+S）
                mods = getattr(e, "mod", 0) or 0
                ctrl = bool(mods & pygame.KMOD_CTRL)
                if e.key == pygame.K_F5 or (e.key == pygame.K_s and ctrl):
                    self.save_game(1)
                elif e.key == pygame.K_F9:
                    self.load_game(1)
                elif e.key == pygame.K_e:
                    self.try_interact()

        if self.chest_event:
            self.update_chest_event(dt)
            world = pygame.Surface((VIEW_W, VIEW_H))
            if self.layer == "underground":
                world.fill((18, 16, 28))
            else:
                world.fill((30, 50, 40))
            self.draw_visible_map(world, self.current_grid(), mw, mh, show_goal=True)
            self.knight.draw(world, self.camera)
            if self.layer == "underground":
                shade = pygame.Surface((VIEW_W, VIEW_H), pygame.SRCALPHA)
                shade.fill((0, 0, 30, 50))
                world.blit(shade, (0, 0))
            self.screen.blit(world, (0, 0))
            self.draw_chest_event_overlay()
            phase = str((self.chest_event or {}).get("phase") or "")
            mode = str((self.chest_event or {}).get("mode") or "")
            if phase == "result":
                bar = "判定结果 · Enter / Space 继续"
            elif mode == "dice":
                bar = "掷骰判定 · SPACE掷骰 · Esc取消"
            elif mode == "rps":
                bar = "猜拳判定 · 1石 2剪 3布 · Esc取消"
            else:
                bar = "宝箱判定中 · Esc取消"
            self.draw_ui_bar(bar)
            return

        if self.bag_open:
            world = pygame.Surface((VIEW_W, VIEW_H))
            if self.layer == "underground":
                world.fill((18, 16, 28))
            else:
                world.fill((30, 50, 40))
            self.draw_visible_map(world, self.current_grid(), mw, mh, show_goal=True)
            self.draw_pickups(world)
            flash = self.star_t > 0 and int(self.pickup_bob * 10) % 2 == 0
            self.knight.draw(world, self.camera, flash=flash)
            if self.layer == "underground":
                shade = pygame.Surface((VIEW_W, VIEW_H), pygame.SRCALPHA)
                shade.fill((0, 0, 30, 50))
                world.blit(shade, (0, 0))
            self.screen.blit(world, (0, 0))
            self.draw_bag_overlay()
            self.draw_ui_bar(
                "背包 · ↑↓选择 · Enter吃食物回血 · I关闭"
                if self.uses_durability()
                else "背包 · DIY无耐久 · I关闭"
            )
            return

        if self.dialog:
            # 对话中暂停移动
            world = pygame.Surface((VIEW_W, VIEW_H))
            if self.layer == "underground":
                world.fill((18, 16, 28))
            else:
                world.fill((30, 50, 40))
            self.draw_visible_map(world, self.current_grid(), mw, mh, show_goal=True)
            self.knight.draw(world, self.camera)
            if self.layer == "underground":
                shade = pygame.Surface((VIEW_W, VIEW_H), pygame.SRCALPHA)
                shade.fill((0, 0, 30, 50))
                world.blit(shade, (0, 0))
            self.screen.blit(world, (0, 0))
            self.draw_dialog_overlay()
            self.draw_ui_bar("对话中 · Enter 关闭")
            return

        if self.stairs_cd > 0:
            self.stairs_cd -= dt
        if self.layer_flash > 0:
            self.layer_flash = max(0.0, self.layer_flash - dt / LAYER_FLASH_DUR)

        keys = pygame.key.get_pressed()
        # 黑屏前半略过移动，避免刚切换又踩门口
        speed_mult = RPG_SPEED_MULT if self.speed_t > 0 else 1.0
        if self.layer_flash < 0.55:
            self.knight.update(dt, keys, grid, mw, mh, speed_mult=speed_mult)
        self.camera.follow(self.knight.x, self.knight.y, mw, mh)

        tx, ty = self.knight.tile_pos()
        if 0 <= tx < mw and 0 <= ty < mh:
            cell = grid[ty][tx]
            if cell in LAYER_PORTALS:
                self.try_use_layer_portal()
            else:
                self.portal_stand_lock = None
        else:
            self.portal_stand_lock = None

        # 换格随机机关（马里奥式突发）+ 地图放置陷阱
        self.maybe_trigger_hazard()
        self.maybe_trigger_map_trap()
        self.update_pickups(dt)

        # 附近互动提示
        self.nearby_hint = ""
        for _tx, _ty, cell in self._interact_targets():
            hint = INTERACT_HINTS.get(cell)
            if hint and cell not in LAYER_PORTALS:
                self.nearby_hint = hint
                break

        self.check_goal()

        world = pygame.Surface((VIEW_W, VIEW_H))
        # 地下稍暗
        if self.layer == "underground":
            world.fill((18, 16, 28))
        else:
            world.fill((30, 50, 40))
        self.draw_visible_map(world, self.current_grid(), mw, mh, show_goal=True)
        self.draw_pickups(world)
        flash = self.star_t > 0 and int(self.pickup_bob * 10) % 2 == 0
        self.knight.draw(world, self.camera, flash=flash)
        if self.layer == "underground":
            shade = pygame.Surface((VIEW_W, VIEW_H), pygame.SRCALPHA)
            shade.fill((0, 0, 30, 50))
            world.blit(shade, (0, 0))
        self.screen.blit(world, (0, 0))

        if self.layer_flash > 0:
            # 黑一下再淡出
            flash = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            a = int(255 * min(1.0, self.layer_flash))
            flash.fill((0, 0, 0, a))
            self.screen.blit(flash, (0, 0))

        layer_cn = "地下" if self.layer == "underground" else "地面"
        name = self.map_data.get("name", "")
        kind_cn = PLAYER_KIND_LABELS.get(self.player_kind, self.player_kind)
        buff = ""
        if self.star_t > 0:
            buff += f" 星{self.star_t:.0f}s"
        if self.speed_t > 0:
            buff += f" 速{self.speed_t:.0f}s"
        tip = self.nearby_hint or (
            "E互动 I背包 F5存档 C角色" if self.uses_durability() else "E互动 F5存档 C角色"
        )
        best = ""
        if self.campaign:
            progress = load_rpg_progress()
            bidx = int(progress.get("best_level_idx", -1))
            if bidx >= 0:
                best = f" | 历史最高第{bidx + 1}关"
        self.draw_ui_bar(
            f"{name} | {kind_cn} | {layer_cn} | 宝箱{self.treasures} 币{self.coins}{buff}{best} | {tip} | Esc"
            + (" | R重开" if self.campaign else "")
        )

    def run_levelclear(self, events: list) -> None:
        for e in events:
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._load_level(self.level_idx + 1)
                return
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.enter_menu(play_intro=False)
                return

        assert self.map_data and self.knight
        mw, mh = map_size(self.map_data)
        self.camera.follow(self.knight.x, self.knight.y, mw, mh)
        world = pygame.Surface((VIEW_W, VIEW_H))
        self.draw_visible_map(world, self.current_grid(), mw, mh, show_goal=True)
        self.knight.draw(world, self.camera)
        dim = pygame.Surface((VIEW_W, VIEW_H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        world.blit(dim, (0, 0))
        self.screen.blit(world, (0, 0))

        box = pygame.Rect(48, VIEW_H // 2 - 50, SCREEN_W - 96, 100)
        self.draw_textbox(self.screen, box)
        msg = self.font.render(self.dialog_quote("关卡通过！"), True, (255, 255, 255))
        nxt = LEVEL_DEFS[self.level_idx + 1]["name"] if self.level_idx + 1 < len(LEVEL_DEFS) else ""
        sub = self.font_sm.render(f"本关宝箱 {self.treasures} · Enter 进入：{nxt}", True, (220, 220, 220))
        self.screen.blit(msg, (box.centerx - msg.get_width() // 2, box.y + 22))
        self.screen.blit(sub, (box.centerx - sub.get_width() // 2, box.y + 56))
        self.draw_ui_bar("通往下一关")

    def run_win(self, events: list) -> None:
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.campaign:
                        self.start_campaign()
                    else:
                        self.enter_menu(play_intro=False)
                elif e.key == pygame.K_ESCAPE:
                    self.enter_menu(play_intro=False)

        assert self.map_data and self.knight
        mw, mh = map_size(self.map_data)
        self.camera.follow(self.knight.x, self.knight.y, mw, mh)
        world = pygame.Surface((VIEW_W, VIEW_H))
        self.draw_visible_map(world, self.current_grid(), mw, mh, show_goal=True)
        self.knight.draw(world, self.camera)
        dim = pygame.Surface((VIEW_W, VIEW_H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        world.blit(dim, (0, 0))
        self.screen.blit(world, (0, 0))

        box = pygame.Rect(40, VIEW_H // 2 - 50, SCREEN_W - 80, 100)
        self.draw_textbox(self.screen, box)
        if self.campaign:
            note_rpg_best_level(self.level_idx, cleared_all=True)
        msg = self.font.render(self.dialog_quote("公主获救了！"), True, (255, 255, 255))
        total = self.total_treasures + (0 if self.campaign else self.treasures)
        if self.campaign:
            total = self.total_treasures
        sub = self.font_sm.render(
            f"累计宝箱 {total} · {format_rpg_best_level_line()} · Enter {'再开一局' if self.campaign else '回菜单'} · Esc 菜单",
            True,
            (220, 220, 220),
        )
        self.screen.blit(msg, (box.centerx - msg.get_width() // 2, box.y + 22))
        self.screen.blit(sub, (box.centerx - sub.get_width() // 2, box.y + 56))
        self.draw_ui_bar("全通关！" if self.campaign else "通关！")

    def run_editor(self, events: list, dt: float) -> None:
        assert self.map_data
        mw, mh = map_size(self.map_data)
        self.layer = self.edit_layer
        grid = self.current_grid()
        keys = pygame.key.get_pressed()
        ctrl = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]
        shift = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        space = keys[pygame.K_SPACE]
        pan = 320 * dt
        if keys[pygame.K_LEFT]:
            self.camera.x -= pan
        if keys[pygame.K_RIGHT]:
            self.camera.x += pan
        if keys[pygame.K_UP]:
            self.camera.y -= pan
        if keys[pygame.K_DOWN]:
            self.camera.y += pan
        self.camera.clamp(mw, mh)

        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.enter_menu(play_intro=False)
                    return
                if e.key == pygame.K_TAB:
                    if not map_has_layer_portals(self.map_data):
                        self.toast("先放楼梯或洞窟，会新增地下层页面")
                    else:
                        self.edit_layer = "underground" if self.edit_layer == "surface" else "surface"
                        self.layer = self.edit_layer
                        layer_cn = "地下" if self.edit_layer == "underground" else "地面"
                        self.toast(f"编辑层：{layer_cn}（点左侧页面也可切换）")
                if e.key == pygame.K_s and ctrl:
                    self.editor_delete_pending = False
                    self._save_map(export_copy=bool(shift))
                elif e.key == pygame.K_e and ctrl:
                    self.editor_delete_pending = False
                    self._save_map(export_copy=True)
                elif e.key == pygame.K_o and ctrl:
                    self.editor_delete_pending = False
                    self.open_map_picker(for_editor=True)
                elif e.key in (pygame.K_DELETE, pygame.K_x) and self.brush == USER_PAINT:
                    # 选中「自创画」时：Delete/X 删除素材（需确认两次）
                    self._delete_user_paint_asset(confirmed=bool(self.paint_delete_pending))
                elif e.key in (pygame.K_DELETE, pygame.K_d) and (ctrl or e.key == pygame.K_DELETE):
                    # Delete 或 Ctrl+D：删除当前已保存地图文件
                    self.paint_delete_pending = False
                    self._editor_delete_current()
                elif e.key == pygame.K_F2:
                    self.open_pixel_painter()
                elif e.key == pygame.K_s and not ctrl:
                    self._select_editor_brush(BRUSH_START)
                elif e.key == pygame.K_g:
                    self._select_editor_brush(BRUSH_PRINCESS)
                elif e.key == pygame.K_t:
                    self.edit_mode = "tile"
                    if self.brush in (BRUSH_START, BRUSH_PRINCESS):
                        self.brush = GRASS
                    self.toast("地块绘制模式")
                elif e.key == pygame.K_p:
                    self.editor_delete_pending = False
                    self.start_play(json.loads(json.dumps(self.map_data)), campaign=False)
                elif e.key == pygame.K_n:
                    self.start_editor(generate_level(0))
                    self.state = "editor"
                    self.toast("已载入随机第1关样式")
                elif e.key == pygame.K_c and not ctrl:
                    self.start_editor()
                elif e.key == pygame.K_b and not ctrl:
                    self._editor_apply_contour_border()
                elif pygame.K_1 <= e.key <= pygame.K_9:
                    idx = e.key - pygame.K_1
                    if idx < len(PALETTE):
                        self._select_editor_brush(PALETTE[idx][0])
                elif e.key == pygame.K_0:
                    if len(PALETTE) > 9:
                        self._select_editor_brush(PALETTE[9][0])
                elif e.key == pygame.K_MINUS and len(PALETTE) > 10:
                    self._select_editor_brush(PALETTE[10][0])
                elif e.key == pygame.K_EQUALS and len(PALETTE) > 11:
                    self._select_editor_brush(PALETTE[11][0])
                elif e.key == pygame.K_LEFTBRACKET and len(PALETTE) > 12:
                    self._select_editor_brush(PALETTE[12][0])
                elif e.key == pygame.K_RIGHTBRACKET and len(PALETTE) > 13:
                    self._select_editor_brush(PALETTE[13][0])
                elif e.key == pygame.K_SEMICOLON and len(PALETTE) > 14:
                    self._select_editor_brush(PALETTE[14][0])
                elif e.key == pygame.K_QUOTE and len(PALETTE) > 15:
                    self._select_editor_brush(PALETTE[15][0])
                elif e.key == pygame.K_BACKSPACE:
                    self._select_editor_brush(EMPTY)
            if e.type == pygame.MOUSEWHEEL:
                self.camera.y -= e.y * TILE * 2
                self.camera.clamp(mw, mh)
            if e.type == pygame.MOUSEBUTTONDOWN:
                pos = self._content_mouse(e.pos)
                if e.button == 2 or (e.button == 1 and space):
                    self.editor_panning = True
                    self.editor_pan_origin = (e.pos[0], e.pos[1], self.camera.x, self.camera.y)
                    continue
                if e.button == 1:
                    file_action = self._hit_editor_file_button(pos)
                    if file_action is not None:
                        self._run_editor_file_action(file_action)
                        continue
                    layer_hit = self._hit_editor_layer_page(pos)
                    if layer_hit is not None:
                        self._switch_edit_layer(layer_hit)
                        continue
                    hit = self._hit_editor_palette(pos)
                    if hit is not None:
                        self._select_editor_brush(hit)
                        continue
                    # 清除笔刷：左键等同擦除；起点/公主可拖放；其它笔刷左键绘制
                    self.paint_drag = self.edit_mode in ("tile", "start", "goal")
                    self._paint_at(pos, erase=(self.brush == EMPTY and self.edit_mode == "tile"))
                elif e.button == 3:
                    hit = self._hit_editor_palette(pos)
                    if hit == USER_PAINT:
                        # 素材栏右键「自创画」：删除素材
                        self._delete_user_paint_asset(confirmed=bool(self.paint_delete_pending))
                        continue
                    if pos[1] >= VIEW_H - PALETTE_H:
                        continue
                    # 右键：擦地块；公主模式下去掉公主
                    self.paint_drag = self.edit_mode in ("tile", "goal")
                    self._paint_at(pos, erase=True)
            if e.type == pygame.MOUSEBUTTONUP:
                if e.button in (1, 2, 3):
                    self.editor_panning = False
                    self.paint_drag = False
            if e.type == pygame.MOUSEMOTION:
                if self.editor_panning or (space and e.buttons[0]):
                    ox, oy, cx, cy = self.editor_pan_origin
                    if not self.editor_panning:
                        self.editor_pan_origin = (e.pos[0], e.pos[1], self.camera.x, self.camera.y)
                        ox, oy, cx, cy = self.editor_pan_origin
                        self.editor_panning = True
                    self.camera.x = cx - (e.pos[0] - ox)
                    self.camera.y = cy - (e.pos[1] - oy)
                    self.camera.clamp(mw, mh)
                elif self.paint_drag and self.edit_mode in ("tile", "start", "goal"):
                    pos = self._content_mouse(e.pos)
                    if self._hit_editor_palette(pos) is not None:
                        continue
                    if e.buttons[0]:
                        self._paint_at(
                            pos,
                            erase=(self.brush == EMPTY and self.edit_mode == "tile"),
                        )
                    elif e.buttons[2] and self.edit_mode in ("tile", "goal"):
                        self._paint_at(pos, erase=True)

        world = pygame.Surface((VIEW_W, VIEW_H))
        world.fill((20, 20, 30) if self.edit_layer == "underground" else (30, 50, 40))
        self.draw_visible_map(world, grid, mw, mh, show_goal=True)
        mx, my = self._content_mouse(pygame.mouse.get_pos())
        if my < VIEW_H - PALETTE_H:
            wx = int(self.camera.x + mx) // TILE
            wy = int(self.camera.y + my) // TILE
            sx, sy = self.camera.apply(wx * TILE, wy * TILE)
            if self.brush == EMPTY and self.edit_mode == "tile":
                pygame.draw.rect(world, (220, 80, 80), (sx, sy, TILE, TILE), 2)
                pygame.draw.line(world, (220, 80, 80), (sx + 4, sy + 4), (sx + TILE - 4, sy + TILE - 4), 2)
                pygame.draw.line(world, (220, 80, 80), (sx + TILE - 4, sy + 4), (sx + 4, sy + TILE - 4), 2)
            else:
                pygame.draw.rect(world, (255, 255, 100), (sx, sy, TILE, TILE), 2)
        self.screen.blit(world, (0, 0))
        self.draw_editor_palette()
        self._draw_editor_layer_pages()

        if self.edit_mode == "start":
            brush_name = "起点(蓝框)"
        elif self.edit_mode == "goal":
            brush_name = "公主(通关/右键去掉)"
        else:
            brush_name = next((n for t, n in PALETTE if t == self.brush), "?")
        layer_cn = "地下" if self.edit_layer == "underground" else "地面"
        file_tag = self.edit_map_path.name if self.edit_map_path else "未保存"
        mode_tag = "通关" if self.map_data.get("princess") else "自由"
        if self.edit_mode in ("start", "goal"):
            erase_hint = " · 左键拖到目标格"
        elif self.brush != EMPTY:
            erase_hint = " · 右键也可擦"
        else:
            erase_hint = " · 左键擦除"
        page_hint = " · 点左侧层页" if map_has_layer_portals(self.map_data) else " · 放楼梯/洞窟新增层页"
        self.draw_ui_bar(
            f"DIY[{layer_cn}/{mode_tag}] {brush_name}{erase_hint}{page_hint} · {file_tag}"
        )
        self._draw_editor_file_buttons()

    def _editor_layer_page_rects(self) -> list[tuple[pygame.Rect, str, str]]:
        """左侧层页面：地面常驻；有楼梯/洞窟后新增地下页。"""
        assert self.map_data
        pages = [("surface", "地面")]
        if map_has_layer_portals(self.map_data):
            pages.append(("underground", "地下"))
        out: list[tuple[pygame.Rect, str, str]] = []
        x, y0, w, h, gap = 6, 10, 44, 28, 6
        for i, (layer, label) in enumerate(pages):
            out.append((pygame.Rect(x, y0 + i * (h + gap), w, h), layer, label))
        return out

    def _hit_editor_layer_page(self, pos: tuple[int, int]) -> str | None:
        for rect, layer, _label in self._editor_layer_page_rects():
            if rect.collidepoint(pos):
                return layer
        return None

    def _switch_edit_layer(self, layer: str) -> None:
        assert self.map_data
        if layer == "underground" and not map_has_layer_portals(self.map_data):
            self.toast("先放楼梯或洞窟，会新增地下层页面")
            return
        if layer not in ("surface", "underground"):
            return
        self.edit_layer = layer
        self.layer = layer
        layer_cn = "地下" if layer == "underground" else "地面"
        self.toast(f"编辑层：{layer_cn}")

    def _draw_editor_layer_pages(self) -> None:
        for rect, layer, label in self._editor_layer_page_rects():
            selected = self.edit_layer == layer
            bg = (55, 70, 110) if selected else (28, 34, 50)
            border = (120, 190, 255) if selected else (80, 90, 120)
            pygame.draw.rect(self.screen, bg, rect, border_radius=4)
            pygame.draw.rect(self.screen, border, rect, 2 if selected else 1, border_radius=4)
            txt = self.font_sm.render(label, True, (240, 245, 255) if selected else (180, 190, 210))
            self.screen.blit(
                txt,
                (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2),
            )

    def _on_first_layer_portal(self) -> None:
        """首次放置楼梯/洞窟：解锁地下层页面。"""
        assert self.map_data
        # 切到地下页提示用户新层可用
        self.toast("已新增「地下」层页面 · 点左侧或 Tab 切换编辑")

    def _clear_princess(self) -> None:
        """去掉公主 → 自由探索（无通关条件）。"""
        assert self.map_data
        had = bool(self.map_data.get("princess")) or self.map_data.get("goal") is not None
        self.map_data["princess"] = False
        self.map_data["goal"] = None
        if had:
            self.toast("已去掉公主 · 自由探索（无通关）")

    def _erase_tile(self, tx: int, ty: int) -> None:
        """清除已放上去的地块；楼梯/洞窟会同步双层并更新列表。地物清除后露出背景。"""
        assert self.map_data
        ensure_ground_layers(self.map_data)
        goal = self.map_data.get("goal")
        if (
            self.map_data.get("princess")
            and isinstance(goal, (list, tuple))
            and len(goal) >= 2
            and int(goal[0]) == tx
            and int(goal[1]) == ty
            and self.edit_layer == self.map_data.get("goal_layer", "surface")
        ):
            self._clear_princess()
        grid = self.current_grid()
        ground = layer_ground(self.map_data, self.edit_layer)
        cell = grid[ty][tx]
        base = int(ground[ty][tx]) if ground[ty][tx] in BACKGROUND_TILES else EMPTY
        if cell in PROP_OVERLAY and base in BACKGROUND_TILES:
            # 只擦地物，留下背景
            grid[ty][tx] = base
        else:
            grid[ty][tx] = EMPTY
            ground[ty][tx] = EMPTY
        if cell in LAYER_PORTALS:
            other = "underground" if self.edit_layer == "surface" else "surface"
            other_grid = layer_grid(self.map_data, other)
            other_ground = layer_ground(self.map_data, other)
            if other_grid[ty][tx] in LAYER_PORTALS:
                ob = int(other_ground[ty][tx]) if other_ground[ty][tx] in BACKGROUND_TILES else EMPTY
                other_grid[ty][tx] = ob if ob in BACKGROUND_TILES else EMPTY
                if ob not in BACKGROUND_TILES:
                    other_ground[ty][tx] = EMPTY
            if cell == STAIRS:
                stairs = self.map_data.setdefault("stairs", [])
                self.map_data["stairs"] = [p for p in stairs if p != [tx, ty]]
            else:
                caves = self.map_data.setdefault("caves", [])
                self.map_data["caves"] = [p for p in caves if p != [tx, ty]]
            if not map_has_layer_portals(self.map_data) and self.edit_layer == "underground":
                self.edit_layer = "surface"
                self.layer = "surface"
                self.toast("已无楼梯/洞窟 · 地下层页面收起")

    def _paint_at(self, pos: tuple[int, int], erase: bool) -> None:
        assert self.map_data
        x, y = pos
        if y >= VIEW_H - PALETTE_H:
            return
        if y >= VIEW_H:
            return
        mw, mh = map_size(self.map_data)
        tx = int(self.camera.x + x) // TILE
        ty = int(self.camera.y + y) // TILE
        if not (0 <= tx < mw and 0 <= ty < mh):
            return
        if self.edit_mode == "start" or self.brush == BRUSH_START:
            if erase:
                return
            prev = self.map_data.get("start")
            # 起点不可落在湖/墙等不可走格：自动挪到最近可走格，并尽量铺成草地
            grid = layer_grid(self.map_data, "surface")
            stx, sty = ensure_walkable_spawn(self.map_data, tx, ty, layer="surface")
            if grid and 0 <= sty < len(grid) and 0 <= stx < len(grid[0]):
                if grid[sty][stx] in SOLID:
                    grid[sty][stx] = GRASS
                    layer_ground(self.map_data, "surface")[sty][stx] = GRASS
            self.map_data["start"] = [stx, sty]
            self.edit_layer = "surface"
            self.layer = "surface"
            # 拖放时保持起点笔刷，松手后再换笔刷
            if self.brush != BRUSH_START:
                self.edit_mode = "tile"
            if prev != [stx, sty]:
                note = f"起点蓝框 ({stx},{sty})"
                if (stx, sty) != (tx, ty):
                    note += "（已避开水面/障碍）"
                self.toast(note)
            return
        if self.edit_mode == "goal" or self.brush == BRUSH_PRINCESS:
            if erase:
                self._clear_princess()
                if self.brush != BRUSH_PRINCESS:
                    self.edit_mode = "tile"
                return
            prev = self.map_data.get("goal")
            prev_layer = self.map_data.get("goal_layer")
            self.map_data["goal"] = [tx, ty]
            self.map_data["goal_layer"] = self.edit_layer
            self.map_data["princess"] = True
            grid = self.current_grid()
            if grid[ty][tx] in SOLID:
                fill = BRICK if self.edit_layer == "underground" else GRASS
                grid[ty][tx] = fill
                layer_ground(self.map_data, self.edit_layer)[ty][tx] = fill
            if self.brush != BRUSH_PRINCESS:
                self.edit_mode = "tile"
            if prev != [tx, ty] or prev_layer != self.edit_layer:
                layer_cn = "地下" if self.edit_layer == "underground" else "地面"
                self.toast(f"公主通关点 ({tx},{ty}) @ {layer_cn}")
            return

        if erase or self.brush == EMPTY:
            self._erase_tile(tx, ty)
            return
        if self.brush in (BRUSH_START, BRUSH_PRINCESS):
            return
        ensure_ground_layers(self.map_data)
        grid = self.current_grid()
        ground = layer_ground(self.map_data, self.edit_layer)
        default = default_ground_for_layer(self.edit_layer)
        brush = int(self.brush)
        if brush in BACKGROUND_TILES:
            # 背景：铺满该格（地物被盖掉）
            grid[ty][tx] = brush
            ground[ty][tx] = brush
        elif brush in PROP_OVERLAY:
            # 地物：叠在已有背景上；若当前是空/地物则保留或补默认背景
            if ground[ty][tx] not in BACKGROUND_TILES:
                if grid[ty][tx] in BACKGROUND_TILES:
                    ground[ty][tx] = int(grid[ty][tx])
                else:
                    ground[ty][tx] = default
            grid[ty][tx] = brush
        else:
            grid[ty][tx] = brush
            if brush != EMPTY:
                ground[ty][tx] = default if ground[ty][tx] not in BACKGROUND_TILES else ground[ty][tx]

        if self.brush in LAYER_PORTALS:
            # 放置前是否已有其它楼梯/洞窟（用于首次解锁地下层页）
            had_before = False
            for key in ("surface", "underground"):
                g = self.map_data.get(key)
                if not isinstance(g, list):
                    continue
                for yy, row in enumerate(g):
                    for xx, t in enumerate(row):
                        if (xx, yy) == (tx, ty):
                            continue
                        if t in LAYER_PORTALS:
                            had_before = True
                            break
                    if had_before:
                        break
                if had_before:
                    break
            # 双层同步楼梯 / 洞窟（可与另一类门户并存于不同格）
            other = "underground" if self.edit_layer == "surface" else "surface"
            other_grid = layer_grid(self.map_data, other)
            other_ground = layer_ground(self.map_data, other)
            other_grid[ty][tx] = self.brush
            if other_ground[ty][tx] not in BACKGROUND_TILES:
                other_ground[ty][tx] = default_ground_for_layer(other)
            stairs = self.map_data.setdefault("stairs", [])
            caves = self.map_data.setdefault("caves", [])
            pos = [tx, ty]
            if self.brush == STAIRS:
                if pos not in stairs:
                    stairs.append(pos)
                self.map_data["caves"] = [p for p in caves if p != pos]
            else:
                if pos not in caves:
                    caves.append(pos)
                self.map_data["stairs"] = [p for p in stairs if p != pos]
            if not had_before:
                self._on_first_layer_portal()

    def _next_diy_path(self) -> Path:
        MAPS_DIR.mkdir(exist_ok=True)
        n = 1
        while True:
            path = MAPS_DIR / f"diy_{n:03d}.json"
            if not path.exists():
                return path
            n += 1

    def _write_map_file(self, path: Path) -> None:
        assert self.map_data
        MAPS_DIR.mkdir(exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.map_data, f, ensure_ascii=False, indent=2)
        self.edit_map_path = path
        self.custom_maps = self._list_maps()

    def _save_map(self, *, export_copy: bool = False) -> None:
        """保存：覆盖当前文件（无则新建）；导出：始终另存新文件，并复制到 userdata/exports。"""
        assert self.map_data
        if export_copy or self.edit_map_path is None or not self.edit_map_path.exists():
            path = self._next_diy_path()
            self._write_map_file(path)
            # 导出时再拷一份到 userdata/exports 方便带走
            if export_copy:
                try:
                    export_dir = _rpg_user_root().parent / "userdata" / "exports"
                    if not export_dir.parent.is_dir():
                        export_dir = _rpg_user_root() / "exports"
                    export_dir.mkdir(parents=True, exist_ok=True)
                    dest = export_dir / path.name
                    shutil.copy2(path, dest)
                    self.toast(f"已导出 JSON → {dest}", 4.5)
                    try:
                        if sys.platform == "win32":
                            import os

                            os.startfile(str(export_dir))  # noqa: S606
                    except Exception:
                        pass
                    return
                except Exception as exc:
                    self.toast(f"已保存 {path.name}，导出副本失败：{exc}", 4.0)
                    return
            self.toast(("已导出 → " if export_copy else "已保存 → ") + str(path), 3.5)
            return
        self._write_map_file(self.edit_map_path)
        self.toast(f"已保存 → {self.edit_map_path}", 3.2)

    def _delete_map_file(self, path: Path) -> bool:
        try:
            path.unlink(missing_ok=True)
        except Exception:
            self.toast("删除失败")
            return False
        if self.edit_map_path is not None and self.edit_map_path.resolve() == path.resolve():
            self.edit_map_path = None
        self.custom_maps = self._list_maps()
        return True

    def _editor_delete_current(self) -> None:
        if self.edit_map_path is None or not self.edit_map_path.exists():
            self.toast("当前地图尚未保存到文件")
            self.editor_delete_pending = False
            return
        path = self.edit_map_path
        if self.editor_delete_pending:
            if self._delete_map_file(path):
                self.toast(f"已删除 {path.name}（编辑内容仍在，可再保存）")
            self.editor_delete_pending = False
            return
        self.editor_delete_pending = True
        self.toast(f"再点删除 / 再按 Delete 确认删除 {path.name}")

    def _editor_apply_contour_border(self) -> None:
        """按内容轮廓包边（非正方形）；键盘 B / 底栏「包边」。"""
        assert self.map_data
        grid = self.current_grid()
        x0, y0, x1, y1 = rock_ring_around_content(grid, ROCK)
        self.editor_delete_pending = False
        self.toast(f"已按轮廓包边 ({x0},{y0})-({x1},{y1}) · B")

    def _editor_file_button_rects(self) -> list[tuple[pygame.Rect, str, str]]:
        """底栏右侧：包边 / 保存 / 导出 / 删除 / 打开。"""
        specs = (
            ("包边", "border"),
            ("保存", "save"),
            ("导出", "export"),
            ("删除", "delete"),
            ("打开", "open"),
        )
        bw, bh, gap = 48, 28, 5
        total = len(specs) * bw + (len(specs) - 1) * gap
        x = SCREEN_W - total - 8
        y = VIEW_H + (UI_H - bh) // 2
        out: list[tuple[pygame.Rect, str, str]] = []
        for label, action in specs:
            out.append((pygame.Rect(x, y, bw, bh), label, action))
            x += bw + gap
        return out

    def _hit_editor_file_button(self, pos: tuple[int, int]) -> str | None:
        for rect, _label, action in self._editor_file_button_rects():
            if rect.collidepoint(pos):
                return action
        return None

    def _draw_editor_file_buttons(self) -> None:
        for rect, label, action in self._editor_file_button_rects():
            if action == "delete" and self.editor_delete_pending:
                bg, fg, border = (90, 36, 36), (255, 200, 200), (255, 120, 120)
            elif action == "border":
                bg, fg, border = (48, 58, 78), (200, 230, 255), (140, 180, 220)
            else:
                bg, fg, border = (40, 48, 68), (230, 235, 245), (120, 140, 180)
            pygame.draw.rect(self.screen, bg, rect, border_radius=4)
            pygame.draw.rect(self.screen, border, rect, 1, border_radius=4)
            txt = self.font_sm.render(label, True, fg)
            self.screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

    def _run_editor_file_action(self, action: str) -> None:
        if action == "border":
            self._editor_apply_contour_border()
        elif action == "save":
            self.editor_delete_pending = False
            self._save_map(export_copy=False)
        elif action == "export":
            self.editor_delete_pending = False
            self._save_map(export_copy=True)
        elif action == "delete":
            self._editor_delete_current()
        elif action == "open":
            self.editor_delete_pending = False
            self.open_map_picker(for_editor=True)

    def run(self) -> None:
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            if self.message_t > 0:
                self.message_t -= dt
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    self.flush_wallet_earned()
                    self.stop_bgm()
                    pygame.quit()
                    sys.exit(0)
                if e.type == MUSIC_END_EVENT:
                    self._on_music_end_event()
            self._handle_volume_keys(events)

            if self.state == "prologue":
                self.run_prologue(events, dt)
            elif self.state == "menu":
                self.run_menu(events, dt)
                if self.message_t > 0:
                    tip = self.font_sm.render(self.message, True, (255, 200, 100))
                    self.screen.blit(tip, (SCREEN_W // 2 - tip.get_width() // 2, SCREEN_H - 70))
            elif self.state == "picker":
                self.run_picker(events)
            elif self.state == "kind_select":
                self.run_kind_select(events)
            elif self.state == "play":
                self.run_play(events, dt)
            elif self.state == "levelclear":
                self.run_levelclear(events)
            elif self.state == "win":
                self.run_win(events)
            elif self.state == "editor":
                self.run_editor(events, dt)
            elif self.state == "pixel_paint":
                self.run_pixel_paint(events)

            # 内容区外加边框，包住整块画面
            self.draw_window_frame()
            pygame.display.flip()


def main() -> None:
    Game().run()


if __name__ == "__main__":
    main()
