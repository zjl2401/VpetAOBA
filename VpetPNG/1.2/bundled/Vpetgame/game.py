"""
Silent Oath — 地底冒险 RPG
大地图 + 镜头跟随；地面 / 地下双层楼梯互通；多关卡冒险。
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

import pygame

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
MAPS_DIR = ROOT / "maps"
SAVES_DIR = ROOT / "saves"

# BGM：开始冒险后先播 startmusic，再循环 music，直到关闭游戏
MUSIC_END_EVENT = pygame.USEREVENT + 21
STARTMUSIC_NAMES = ("startmusic.mp3", "startmusic.ogg", "startmusic.wav")
LOOPMUSIC_NAMES = ("music.mp3", "music.ogg", "music.wav")
MUSIC_DEFAULT_VOLUME = 0.28  # 默认偏小，可用音量加减键调节
MUSIC_VOLUME_STEP = 0.08

TILE = 36
# 屏幕可见格子（相机视口）
VIEW_TILES_X, VIEW_TILES_Y = 16, 11
VIEW_W, VIEW_H = VIEW_TILES_X * TILE, VIEW_TILES_Y * TILE
UI_H = 44
PALETTE_H = 52  # 编辑器底部素材条
# 内容区尺寸（对白/菜单/地图都画在这里）
SCREEN_W, SCREEN_H = VIEW_W, VIEW_H + UI_H
# 外边框包围整块内容
FRAME_PAD = 18
WINDOW_W, WINDOW_H = SCREEN_W + FRAME_PAD * 2, SCREEN_H + FRAME_PAD * 2
FPS = 60

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

# 砖地可走（地下背景）；岩石为隔断墙。TREE 可走（森林）。旧图 BRICK 曾作墙→ROCK。
SOLID = {WATER, ROCK, OBSTACLE, HOUSE, BORDER, MOUNTAIN}
WALKABLE_EXTRA = {EMPTY, GRASS, LAND, TREASURE, TREASURE_OPEN, STAIRS, CAVE, GATE, BRICK, TREE}
# 叠在地板上的装饰物（岩石/砖地占满一格，不当道具叠层）
PROP_OVERLAY = {TREE, OBSTACLE, HOUSE, TREASURE, TREASURE_OPEN, GATE, MOUNTAIN, CAVE}
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
}

PALETTE = [
    (EMPTY, "清除"),
    (GRASS, "草地"),
    (LAND, "土地"),
    (WATER, "水面"),
    (BRICK, "砖地"),
    (TREE, "树木"),
    (ROCK, "岩石隔断"),
    (OBSTACLE, "障碍"),
    (HOUSE, "房屋"),
    (TREASURE, "宝箱"),
    (STAIRS, "楼梯"),
    (CAVE, "洞窟"),
    (GATE, "关卡门"),
    (MOUNTAIN, "景区"),
]

# 出发点房屋绘制放大（格数边长）；树木严格占 1 格草地（不拉长）
HOUSE_DRAW_TILES = 3
MOUNTAIN_DRAW_TILES = 2

TREASURE_LOOT = (
    ("金币", "得到几枚闪亮的金币。"),
    ("药水", "一瓶恢复体力的药水。"),
    ("地图碎片", "旧羊皮纸上画着洞窟记号。"),
    ("护身符", "小小的护身符，感觉运气变好了。"),
    ("宝石", "一颗透亮的彩色宝石。"),
)

INTERACT_HINTS = {
    TREASURE: "按 E 打开宝箱",
    HOUSE: "按 E 查看房屋",
    GATE: "靠近关卡门即可进入下一关",
    STAIRS: "踩上楼梯切换地面 / 地下",
    CAVE: "踩上洞窟切换地面 / 地下",
    TREASURE_OPEN: "空宝箱……什么都不剩了",
}

# 关卡设定：更多样素材（森林/水面/景区/洞窟）拼成
LEVEL_DEFS = [
    {
        "name": "第一关 · 绿野秘洞",
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
        "ug_fill": 0.62,
        "ug_corridors": 22,
        "princess": False,
    },
    {
        "name": "第二关 · 荒原地穴",
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
        "ug_fill": 0.58,
        "ug_corridors": 28,
        "princess": False,
    },
    {
        "name": "第三关 · 湖畔洞窟",
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
        "ug_fill": 0.55,
        "ug_corridors": 34,
        "princess": False,
    },
    {
        "name": "最终关 · 地下牢笼",
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
        "ug_fill": 0.52,
        "ug_corridors": 40,
        "princess": True,
    },
]

def load_img(name: str) -> pygame.Surface:
    path = ASSETS / name
    if not path.exists():
        raise FileNotFoundError(f"缺少素材: {path}，请先运行 process_assets.py")
    return pygame.image.load(str(path)).convert_alpha()


def ensure_extra_tiles() -> None:
    """若缺少楼梯/岩地，现场生成。"""
    ASSETS.mkdir(exist_ok=True)
    need = [("stairs.png", "down"), ("stairs_up.png", "up"), ("cave.png", "cave")]
    missing = [n for n, _ in need if not (ASSETS / n).exists()]
    if not missing:
        return
    from PIL import Image, ImageDraw

    if not (ASSETS / "stairs.png").exists():
        im = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 47, 47], fill=(90, 78, 58, 255))
        for i, c in enumerate([(160, 140, 110), (140, 120, 95), (120, 100, 78), (100, 82, 62)]):
            y0 = 6 + i * 9
            x0 = 4 + i * 3
            d.rectangle([x0, y0, 44, y0 + 8], fill=(*c, 255))
        d.polygon([(24, 34), (18, 26), (30, 26)], fill=(220, 200, 80, 255))
        im.save(ASSETS / "stairs.png")
    if not (ASSETS / "stairs_up.png").exists():
        im = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 47, 47], fill=(50, 45, 62, 255))
        for i, c in enumerate([(70, 65, 90), (85, 78, 105), (100, 92, 120), (115, 105, 135)]):
            y0 = 34 - i * 9
            x0 = 4 + i * 3
            d.rectangle([x0, y0, 44, y0 + 8], fill=(*c, 255))
        d.polygon([(24, 12), (18, 20), (30, 20)], fill=(220, 200, 80, 255))
        im.save(ASSETS / "stairs_up.png")
    if not (ASSETS / "cave.png").exists():
        im = Image.new("RGBA", (TILE, TILE), (42, 38, 52, 255))
        d = ImageDraw.Draw(im)
        for x, y in [(5, 7), (18, 4), (30, 12), (8, 22), (22, 28), (35, 20), (12, 35), (28, 38)]:
            d.point((x, y), fill=(55, 50, 68, 255))
        im.save(ASSETS / "cave.png")


class Assets:
    def __init__(self) -> None:
        ensure_extra_tiles()
        self.tiles: dict[int, pygame.Surface] = {}
        for tid, fname in TILE_FILES.items():
            img = load_img(fname)
            if tid == HOUSE:
                side = TILE * HOUSE_DRAW_TILES
                self.tiles[tid] = pygame.transform.scale(img, (side, side))
            elif tid == MOUNTAIN:
                side = TILE * MOUNTAIN_DRAW_TILES
                self.tiles[tid] = pygame.transform.scale(img, (side, side))
            else:
                self.tiles[tid] = pygame.transform.scale(img, (TILE, TILE))
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
        self.stairs_up = pygame.transform.scale(load_img("stairs_up.png"), (TILE, TILE))

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
        self.princess = pygame.transform.scale(load_img("princess.png"), (pw, ph))
        self.start_bg = self._load_start_bg()
        self.start_logo1, self.start_logo2 = self._load_start_logos()
        self.window_frame = self._load_window_frame()
        self.text_frame = self._load_text_frame()

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
    石头围一圈：有绘制内容则绕内容包围盒外扩一格；
    全空白则围整张地图边框。返回包围盒 (x0,y0,x1,y1)。
    """
    h, w = len(grid), len(grid[0])
    xs: list[int] = []
    ys: list[int] = []
    for y in range(h):
        for x in range(w):
            if grid[y][x] != EMPTY:
                xs.append(x)
                ys.append(y)
    if not xs:
        border_wall(grid, wall)
        return 0, 0, w - 1, h - 1
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    # 外扩一格，石头贴在内容外围
    x0 = max(0, x0 - 1)
    y0 = max(0, y0 - 1)
    x1 = min(w - 1, x1 + 1)
    y1 = min(h - 1, y1 + 1)
    for x in range(x0, x1 + 1):
        grid[y0][x] = wall
        grid[y1][x] = wall
    for y in range(y0, y1 + 1):
        grid[y][x0] = wall
        grid[y][x1] = wall
    return x0, y0, x1, y1


def border_brick(grid: list[list[int]]) -> None:
    """兼容旧名：外圈改为岩石隔断。"""
    border_wall(grid, ROCK)


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
        return repair_layer_portals(data)
    # 已有楼梯/成对洞窟时不再做旧迁移（否则会清掉地下洞窟并堵死砖道）
    if _map_has_portal_pairs(data):
        data["tile_schema"] = 2
        return repair_layer_portals(data)
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
    return repair_layer_portals(data)


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
    rng = random.Random(seed if seed is not None else random.randint(0, 10**9))
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
        "seed": seed,
        "tile_schema": 2,
        "house": [hx, hy],
    }



def map_size(data: dict) -> tuple[int, int]:
    return int(data["width"]), int(data["height"])


def layer_grid(data: dict, layer: str) -> list[list[int]]:
    return data["underground"] if layer == "underground" else data["surface"]


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

    def __init__(self, assets: Assets, tile_xy: tuple[int, int]) -> None:
        self.assets = assets
        self.x = tile_xy[0] * TILE + TILE // 2
        self.y = tile_xy[1] * TILE + TILE // 2
        self.dir = "down"
        self.frame = 0
        self.anim_t = 0.0
        self.moving = False
        self.hw = max(8, TILE // 3)
        self.hh = max(6, TILE // 4)

    def update(self, dt: float, keys, grid: list[list[int]], mw: int, mh: int) -> None:
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
        self._try_move(vx * self.SPEED * dt, 0, grid, mw, mh)
        self._try_move(0, vy * self.SPEED * dt, grid, mw, mh)

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

    def draw(self, surf: pygame.Surface, cam: Camera) -> None:
        frames = self.assets.knight[self.dir]
        if self.dir == "down":
            img = frames[0] if not self.moving else frames[1 + self.frame]
        else:
            img = frames[self.frame % len(frames)]
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
        self.message = ""
        self.message_t = 0.0
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
            self.toast("只能在冒险中存档")
            return
        SAVES_DIR.mkdir(exist_ok=True)
        payload = {
            "version": 1,
            "slot": slot,
            "campaign": bool(self.campaign),
            "level_idx": int(self.level_idx),
            "treasures": int(self.treasures),
            "total_treasures": int(self.total_treasures),
            "layer": self.layer,
            "player": [self.knight.x, self.knight.y, self.knight.dir],
            "map_data": self.map_data,
        }
        path = self._save_path(slot)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        self.toast(f"已存档 → {path.name}")

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
        self.layer = str(data.get("layer", "surface"))
        self.map_data = map_data
        px, py, pdir = 0.0, 0.0, "down"
        player = data.get("player") or []
        if len(player) >= 2:
            px, py = float(player[0]), float(player[1])
            if len(player) >= 3:
                pdir = str(player[2])
        else:
            sx, sy = map_data["start"]
            px = sx * TILE + TILE // 2
            py = sy * TILE + TILE // 2
        self.knight = Knight(self.assets, (0, 0))
        self.knight.x, self.knight.y = px, py
        if pdir in self.assets.knight:
            self.knight.dir = pdir
        self.state = "play"
        self.dialog = None
        self.picker_mode = ""
        mw, mh = map_size(map_data)
        self.camera.follow(self.knight.x, self.knight.y, mw, mh)
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
            loot_name, loot_desc = random.choice(TREASURE_LOOT)
            grid[ty][tx] = TREASURE_OPEN
            self.treasures += 1
            self.show_dialog("打开宝箱", f"找到了{loot_name}！{loot_desc}（本关 {self.treasures}）")
            return
        if cell == TREASURE_OPEN:
            self.show_dialog("空宝箱", "已经被翻过了，里面什么也没有。")
            return
        if cell == HOUSE:
            self.show_dialog("小屋", "温暖的出发点小屋。整理好行装，踏上旅途吧。")
            return
        if cell == GATE:
            self.show_dialog("关卡门", "金色光芒流转的门扉——靠近即可前往下一关。")
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
            else:
                img = self.assets.tiles.get(tid)
                if img:
                    thumb = img
                    max_s = min(rect.w - 4, rect.h - 4)
                    if thumb.get_width() > max_s or thumb.get_height() > max_s:
                        scale = max_s / max(thumb.get_width(), thumb.get_height())
                        thumb = pygame.transform.scale(
                            thumb, (max(1, int(thumb.get_width() * scale)), max(1, int(thumb.get_height() * scale)))
                        )
                    self.screen.blit(
                        thumb,
                        (rect.centerx - thumb.get_width() // 2, rect.centery - thumb.get_height() // 2),
                    )
            if tid == self.brush:
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

    def current_grid(self) -> list[list[int]]:
        assert self.map_data
        return layer_grid(self.map_data, self.layer)

    def start_campaign(self) -> None:
        self.campaign = True
        self.level_idx = 0
        self.total_treasures = 0
        self._begin_adventure_bgm()
        self._load_level(0)

    def _load_level(self, idx: int) -> None:
        self.level_idx = idx
        data = generate_level(idx)
        self.map_data = data
        self.layer = "surface"
        self.knight = Knight(self.assets, tuple(data["start"]))
        self.treasures = 0
        self.stairs_cd = 0.0
        self.state = "play"
        tip = "寻找公主！" if data["princess"] else "找到地下金色关卡门进入下一关"
        self.toast(f"{data['name']} — {tip}")

    def start_play(self, data: dict, campaign: bool = False) -> None:
        self.campaign = campaign
        # 兼容旧单层 DIY
        if "surface" not in data:
            data = self._migrate_old_map(data)
        data = normalize_map_tiles(data)
        self.map_data = data
        self.layer = "surface"
        self.knight = Knight(self.assets, tuple(data["start"]))
        self.treasures = 0
        self.stairs_cd = 0.0
        self.state = "play"
        self._begin_adventure_bgm()
        self.toast(data.get("name", "探险开始") + " · WASD移动 · 踩楼梯/洞窟切换地面地下")

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
                "goal": [sx + 4, sy],
                "goal_layer": "surface",
                "princess": True,
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
        self.state = "editor"
        self.camera.x = self.camera.y = 0
        hint = path.name if path else "新地图"
        self.toast(f"{hint} | 保存/导出/删除点底栏 | Ctrl+S 保存 · Ctrl+Shift+S 导出")

    def draw_visible_map(self, surf: pygame.Surface, grid: list[list[int]], mw: int, mh: int, show_goal: bool) -> None:
        assert self.map_data
        tx0 = max(0, int(self.camera.x) // TILE)
        ty0 = max(0, int(self.camera.y) // TILE)
        tx1 = min(mw, tx0 + VIEW_TILES_X + 2)
        ty1 = min(mh, ty0 + VIEW_TILES_Y + 2)

        default_base = BRICK if self.layer == "underground" else GRASS
        for y in range(ty0, ty1):
            for x in range(tx0, tx1):
                t = grid[y][x]
                sx, sy = self.camera.apply(x * TILE, y * TILE)
                if t == EMPTY:
                    # 未绘制格：暗底空白画布
                    pygame.draw.rect(surf, (16, 18, 26), (sx, sy, TILE, TILE))
                    continue
                if t in PROP_OVERLAY:
                    base = default_base
                elif t == STAIRS:
                    base = default_base
                else:
                    base = t
                img = self.assets.tiles.get(base) or self.assets.tiles[GRASS]
                surf.blit(img, (sx, sy))

                if t == STAIRS:
                    stair_img = self.assets.stairs_up if self.layer == "underground" else self.assets.tiles[STAIRS]
                    surf.blit(stair_img, (sx, sy))
                elif t in PROP_OVERLAY and t in self.assets.tiles:
                    prop = self.assets.tiles[t]
                    if t in (HOUSE, GATE, MOUNTAIN):
                        # 高大物体：以格底为脚点，向上伸出多格
                        ox = sx + (TILE - prop.get_width()) // 2
                        oy = sy + TILE - prop.get_height()
                    else:
                        # 树木等：严格贴合当前一格
                        ox = sx + (TILE - prop.get_width()) // 2
                        oy = sy + (TILE - prop.get_height()) // 2
                    surf.blit(prop, (ox, oy))

        if show_goal:
            gx, gy = self.map_data["goal"]
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

        # 起点标记（仅编辑器）
        if self.state == "editor":
            sx0, sy0 = self.map_data["start"]
            sx, sy = self.camera.apply(sx0 * TILE + 4, sy0 * TILE + 4)
            pygame.draw.rect(surf, (80, 200, 255), (sx, sy, TILE - 8, TILE - 8), 2)

    def draw_ui_bar(self, text: str) -> None:
        bar = pygame.Rect(0, VIEW_H, SCREEN_W, UI_H)
        pygame.draw.rect(self.screen, (28, 32, 48), bar)
        pygame.draw.line(self.screen, (90, 100, 130), (0, VIEW_H), (SCREEN_W, VIEW_H), 2)
        self.screen.blit(self.font_sm.render(text, True, (230, 230, 240)), (12, VIEW_H + 6))
        if self.message_t > 0:
            self.screen.blit(self.font_sm.render(self.message, True, (255, 220, 120)), (12, VIEW_H + 32))

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
            pygame.mixer.music.set_volume(max(0.0, min(1.0, self.music_volume)))
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
        """点 START / 进入游玩：先播 startmusic，结束后续播循环 music。"""
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
                pygame.mixer.music.play(0)
                self._apply_music_volume()
                self._bgm_phase = "start"
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

        # 文本框随公主一起淡出
        if princess_a > 0:
            box_m = 36
            box_h = 88
            box = pygame.Rect(box_m, SCREEN_H - box_h - 16, SCREEN_W - box_m * 2, box_h)
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
            self.screen.blit(text_surf, (box.x + 18, box.y + 20))

            hint = self.font_sm.render("ENTER/SPACE/点击 继续     ESC/S 跳过开场", True, (200, 200, 200))
            if princess_a < 255:
                hint = hint.copy()
                hint.set_alpha(princess_a)
            self.screen.blit(hint, (box.x + 18, box.bottom - 28))
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
        if self.layer != self.map_data.get("goal_layer", "surface"):
            return
        gx, gy = self.map_data["goal"]
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
            self.state = "win"

    def run_play(self, events: list, dt: float) -> None:
        assert self.map_data and self.knight
        mw, mh = map_size(self.map_data)
        grid = self.current_grid()

        for e in events:
            if e.type == pygame.KEYDOWN:
                if self.dialog:
                    if e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e, pygame.K_ESCAPE):
                        self.close_dialog()
                    continue
                if e.key == pygame.K_ESCAPE:
                    self.enter_menu(play_intro=False)
                    return
                if e.key == pygame.K_r and self.campaign:
                    self._load_level(self.level_idx)
                    return
                if e.key == pygame.K_F5:
                    self.save_game(1)
                elif e.key == pygame.K_F9:
                    self.load_game(1)
                elif e.key == pygame.K_e:
                    self.try_interact()

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
        if self.layer_flash < 0.55:
            self.knight.update(dt, keys, grid, mw, mh)
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
        self.knight.draw(world, self.camera)
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
        tip = self.nearby_hint or "E互动 F5存档"
        self.draw_ui_bar(
            f"{name} | {layer_cn} | 宝箱 {self.treasures} | {tip} | Esc"
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
        msg = self.font.render(self.dialog_quote("公主获救了！"), True, (255, 255, 255))
        total = self.total_treasures + (0 if self.campaign else self.treasures)
        if self.campaign:
            total = self.total_treasures
        sub = self.font_sm.render(
            f"累计宝箱 {total} · Enter {'再开一局' if self.campaign else '回菜单'} · Esc 菜单",
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
                    self.edit_layer = "underground" if self.edit_layer == "surface" else "surface"
                    self.layer = self.edit_layer
                    self.toast("编辑层：" + ("地下" if self.edit_layer == "underground" else "地面"))
                if e.key == pygame.K_s and ctrl:
                    self.editor_delete_pending = False
                    self._save_map(export_copy=bool(shift))
                elif e.key == pygame.K_e and ctrl:
                    self.editor_delete_pending = False
                    self._save_map(export_copy=True)
                elif e.key == pygame.K_o and ctrl:
                    self.editor_delete_pending = False
                    self.open_map_picker(for_editor=True)
                elif e.key in (pygame.K_DELETE, pygame.K_d) and (ctrl or e.key == pygame.K_DELETE):
                    # Delete 或 Ctrl+D：删除当前已保存文件
                    self._editor_delete_current()
                elif e.key == pygame.K_s and not ctrl:
                    self.editor_delete_pending = False
                    self.edit_mode = "start"
                    self.toast("点击地图设置起点（地面）")
                elif e.key == pygame.K_g:
                    self.editor_delete_pending = False
                    self.edit_mode = "goal"
                    self.toast("点击设置公主 / 终点（当前层）")
                elif e.key == pygame.K_t:
                    self.edit_mode = "tile"
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
                    grid = self.current_grid()
                    x0, y0, x1, y1 = rock_ring_around_content(grid, ROCK)
                    self.toast(f"岩石已围一圈 ({x0},{y0})-({x1},{y1})")
                elif pygame.K_1 <= e.key <= pygame.K_9:
                    idx = e.key - pygame.K_1
                    if idx < len(PALETTE):
                        self.brush = PALETTE[idx][0]
                        self.edit_mode = "tile"
                        self.toast(f"笔刷：{PALETTE[idx][1]}")
                elif e.key == pygame.K_0:
                    if len(PALETTE) > 9:
                        self.brush = PALETTE[9][0]
                        self.toast(f"笔刷：{PALETTE[9][1]}")
                elif e.key == pygame.K_MINUS and len(PALETTE) > 10:
                    self.brush = PALETTE[10][0]
                    self.toast(f"笔刷：{PALETTE[10][1]}")
                elif e.key == pygame.K_EQUALS and len(PALETTE) > 11:
                    self.brush = PALETTE[11][0]
                    self.toast(f"笔刷：{PALETTE[11][1]}")
                elif e.key == pygame.K_LEFTBRACKET and len(PALETTE) > 12:
                    self.brush = PALETTE[12][0]
                    self.edit_mode = "tile"
                    self.toast(f"笔刷：{PALETTE[12][1]}")
                elif e.key == pygame.K_RIGHTBRACKET and len(PALETTE) > 13:
                    self.brush = PALETTE[13][0]
                    self.edit_mode = "tile"
                    self.toast(f"笔刷：{PALETTE[13][1]}")
                elif e.key == pygame.K_BACKSPACE:
                    self.brush = EMPTY
                    self.edit_mode = "tile"
                    self.toast("笔刷：清除（左键擦除素材）")
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
                    hit = self._hit_editor_palette(pos)
                    if hit is not None:
                        self.brush = hit
                        self.edit_mode = "tile"
                        name = next((n for t, n in PALETTE if t == hit), "?")
                        self.toast(f"笔刷：{name}")
                        continue
                    # 清除笔刷：左键等同擦除；其它笔刷左键绘制
                    self.paint_drag = self.edit_mode == "tile"
                    self._paint_at(pos, erase=(self.brush == EMPTY))
                elif e.button == 3:
                    if pos[1] >= VIEW_H - PALETTE_H:
                        continue
                    self.paint_drag = True
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
                elif self.paint_drag and self.edit_mode == "tile":
                    pos = self._content_mouse(e.pos)
                    if self._hit_editor_palette(pos) is not None:
                        continue
                    if e.buttons[0]:
                        self._paint_at(pos, erase=(self.brush == EMPTY))
                    elif e.buttons[2]:
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

        brush_name = next((n for t, n in PALETTE if t == self.brush), "?")
        layer_cn = "地下" if self.edit_layer == "underground" else "地面"
        file_tag = self.edit_map_path.name if self.edit_map_path else "未保存"
        erase_hint = " · 右键也可擦" if self.brush != EMPTY else " · 左键擦除"
        self.draw_ui_bar(f"DIY[{layer_cn}] {brush_name}{erase_hint} · {file_tag}")
        self._draw_editor_file_buttons()

    def _erase_tile(self, tx: int, ty: int) -> None:
        """清除已放上去的地块；楼梯/洞窟会同步双层并更新列表。"""
        assert self.map_data
        grid = self.current_grid()
        cell = grid[ty][tx]
        grid[ty][tx] = EMPTY
        if cell in LAYER_PORTALS:
            other = "underground" if self.edit_layer == "surface" else "surface"
            other_grid = layer_grid(self.map_data, other)
            if other_grid[ty][tx] in LAYER_PORTALS:
                other_grid[ty][tx] = EMPTY
            if cell == STAIRS:
                stairs = self.map_data.setdefault("stairs", [])
                self.map_data["stairs"] = [p for p in stairs if p != [tx, ty]]
            else:
                caves = self.map_data.setdefault("caves", [])
                self.map_data["caves"] = [p for p in caves if p != [tx, ty]]

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
        if self.edit_mode == "start":
            self.map_data["start"] = [tx, ty]
            self.edit_layer = "surface"
            self.edit_mode = "tile"
            self.toast(f"起点 ({tx},{ty})")
            return
        if self.edit_mode == "goal":
            self.map_data["goal"] = [tx, ty]
            self.map_data["goal_layer"] = self.edit_layer
            self.map_data["princess"] = True
            grid = self.current_grid()
            if grid[ty][tx] in SOLID:
                grid[ty][tx] = BRICK if self.edit_layer == "underground" else GRASS
            self.edit_mode = "tile"
            self.toast(f"终点 ({tx},{ty}) @ {self.edit_layer}")
            return

        if erase or self.brush == EMPTY:
            self._erase_tile(tx, ty)
            return
        grid = self.current_grid()
        grid[ty][tx] = self.brush
        if self.brush in LAYER_PORTALS:
            # 双层同步楼梯 / 洞窟（可与另一类门户并存于不同格）
            other = "underground" if self.edit_layer == "surface" else "surface"
            layer_grid(self.map_data, other)[ty][tx] = self.brush
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
        """保存：覆盖当前文件（无则新建）；导出：始终另存新文件。"""
        assert self.map_data
        if export_copy or self.edit_map_path is None or not self.edit_map_path.exists():
            path = self._next_diy_path()
            self._write_map_file(path)
            self.toast(("已导出 → " if export_copy else "已保存 → ") + path.name)
            return
        self._write_map_file(self.edit_map_path)
        self.toast(f"已保存 → {self.edit_map_path.name}")

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

    def _editor_file_button_rects(self) -> list[tuple[pygame.Rect, str, str]]:
        """底栏右侧：保存 / 导出 / 删除 / 打开。"""
        specs = (("保存", "save"), ("导出", "export"), ("删除", "delete"), ("打开", "open"))
        bw, bh, gap = 52, 28, 6
        total = len(specs) * bw + (len(specs) - 1) * gap
        x = SCREEN_W - total - 10
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
            else:
                bg, fg, border = (40, 48, 68), (230, 235, 245), (120, 140, 180)
            pygame.draw.rect(self.screen, bg, rect, border_radius=4)
            pygame.draw.rect(self.screen, border, rect, 1, border_radius=4)
            txt = self.font_sm.render(label, True, fg)
            self.screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

    def _run_editor_file_action(self, action: str) -> None:
        if action == "save":
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
            elif self.state == "play":
                self.run_play(events, dt)
            elif self.state == "levelclear":
                self.run_levelclear(events)
            elif self.state == "win":
                self.run_win(events)
            elif self.state == "editor":
                self.run_editor(events, dt)

            # 内容区外加边框，包住整块画面
            self.draw_window_frame()
            pygame.display.flip()


def main() -> None:
    Game().run()


if __name__ == "__main__":
    main()
