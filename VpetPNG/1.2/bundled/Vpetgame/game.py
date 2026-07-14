"""
Silent Oath — 骑士救公主 RPG
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

TILE = 36
# 屏幕可见格子（相机视口）
VIEW_TILES_X, VIEW_TILES_Y = 16, 11
VIEW_W, VIEW_H = VIEW_TILES_X * TILE, VIEW_TILES_Y * TILE
UI_H = 44
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
CAVE = 12  # 旧地下地板（加载时规范为 BRICK）
GATE = 13  # 通往下一关

# 砖地可走（地下背景）；岩石为隔断墙。旧图 BRICK 曾作墙，加载时规范为 ROCK。
SOLID = {WATER, TREE, ROCK, OBSTACLE, HOUSE, BORDER}
WALKABLE_EXTRA = {EMPTY, GRASS, LAND, TREASURE, STAIRS, CAVE, GATE, BRICK}
# 叠在地板上的装饰物（岩石/砖地占满一格，不当道具叠层）
PROP_OVERLAY = {TREE, OBSTACLE, HOUSE, TREASURE, GATE}

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
}

PALETTE = [
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
    (CAVE, "旧岩地"),
    (GATE, "关卡门"),
]

# 关卡设定：更大地图、更密集连片
LEVEL_DEFS = [
    {
        "name": "第一关 · 绿野秘洞",
        "w": 52,
        "h": 40,
        "obstacles": 28,
        "cluster_r": (2, 5),
        "lakes": 3,
        "land_blobs": 16,
        "stairs": 3,
        "treasures": 5,
        "ug_fill": 0.62,
        "ug_corridors": 22,
        "princess": False,
    },
    {
        "name": "第二关 · 荒原地穴",
        "w": 60,
        "h": 46,
        "obstacles": 36,
        "cluster_r": (2, 6),
        "lakes": 4,
        "land_blobs": 20,
        "stairs": 3,
        "treasures": 6,
        "ug_fill": 0.58,
        "ug_corridors": 28,
        "princess": False,
    },
    {
        "name": "第三关 · 湖畔洞窟",
        "w": 68,
        "h": 52,
        "obstacles": 44,
        "cluster_r": (3, 6),
        "lakes": 5,
        "land_blobs": 24,
        "stairs": 4,
        "treasures": 8,
        "ug_fill": 0.55,
        "ug_corridors": 34,
        "princess": False,
    },
    {
        "name": "最终关 · 地下牢笼",
        "w": 76,
        "h": 58,
        "obstacles": 55,
        "cluster_r": (3, 7),
        "lakes": 6,
        "land_blobs": 28,
        "stairs": 4,
        "treasures": 10,
        "ug_fill": 0.52,
        "ug_corridors": 40,
        "princess": True,
    },
]

# 出发点房屋绘制放大（格数边长）
HOUSE_DRAW_TILES = 3


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
        self.princess = pygame.transform.scale(load_img("princess.png"), (cw, ch))
        self.start_bg = self._load_start_bg()
        self.start_logo1, self.start_logo2 = self._load_start_logos()
        self.window_frame = self._load_window_frame()

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
        max_w = int(SCREEN_W * 0.92)
        if l1.get_width() > max_w:
            s = max_w / l1.get_width()
            nw, nh = max_w, max(1, int(l1.get_height() * s))
            l1 = pygame.transform.scale(l1, (nw, nh))
            l2 = pygame.transform.scale(l2, (nw, nh))
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


def border_brick(grid: list[list[int]]) -> None:
    """兼容旧名：外圈改为岩石隔断。"""
    border_wall(grid, ROCK)


def normalize_map_tiles(data: dict) -> dict:
    """地下：砖地=背景、岩石=隔断；旧图 BRICK 墙→ROCK，CAVE 地→BRICK。"""
    if data.get("tile_schema") == 2:
        return data
    for key in ("surface", "underground", "tiles"):
        grid = data.get(key)
        if not isinstance(grid, list) or not grid:
            continue
        under = key == "underground"
        for row in grid:
            for i, t in enumerate(row):
                if under:
                    if t == CAVE:
                        row[i] = BRICK
                    elif t == BRICK:
                        row[i] = ROCK
                elif t == BRICK:
                    row[i] = ROCK
    data["tile_schema"] = 2
    return data


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
        kind = rng.choice([TREE, TREE, ROCK, OBSTACLE, TREE])
        stamp_blob(
            surface,
            cx,
            cy,
            rng.randint(r_lo, r_hi),
            kind,
            rng,
            density=0.82,
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
            if surface[y][x] in (GRASS, LAND) and under[y][x] in (BRICK, ROCK):
                surface[y][x] = STAIRS
                under[y][x] = STAIRS
                stairs.append([x, y])
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
    else:
        sx, sy = max(2, start[0] + 2), max(2, start[1] - 4)
        surface[sy][sx] = STAIRS
        under[sy][sx] = STAIRS
        stairs = [[sx, sy]]
        carve_path(surface, start, (sx, sy), rng, GRASS)
        carve_path(under, (sx, sy), goal, rng, BRICK)

    surface[hy][hx] = HOUSE
    surface[start[1]][start[0]] = GRASS

    for _ in range(cfg["treasures"]):
        if rng.random() < 0.5:
            x, y = rng.randint(1, w - 2), rng.randint(1, h - 2)
            if surface[y][x] in (GRASS, LAND) and (x, y) != start:
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

    def __init__(self) -> None:
        ensure_assets()
        MAPS_DIR.mkdir(exist_ok=True)
        pygame.init()
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        except pygame.error:
            pass
        pygame.display.set_caption("Silent Oath — 骑士救公主")
        self.window = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        # 游戏内容画在内层；外边框包住整块画面
        self.screen = pygame.Surface((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        self.font = self._load_font(22)
        self.font_sm = self._load_font(16)
        self.assets = Assets()
        self.camera = Camera()
        self.state = "menu"
        self.menu_idx = 0
        # 英文菜单项 + 右侧按键提示
        self.menu_items = [
            ("START CAMPAIGN", "ENTER"),
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
        self.brush = GRASS
        self.edit_mode = "tile"
        self.edit_layer = "surface"
        self.custom_maps = self._list_maps()
        self.campaign = True
        # 开场升起：两 logo 开始时间不同，但同一时刻到达终点；整体上移
        self.intro_t = 0.0
        self.intro_dur = 2.6
        self.logo1_delay = 0.0
        self.logo2_delay = 0.55
        self.intro_done = False
        self.menu_fade = 0.0
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
        self.prologue_char_delay = 0.07
        self.prologue_line_hold = 1.15
        self.prologue_fade_out = 0.0
        self.prologue_done_fade = False
        self.prologue_fade_dur = 1.05  # 公主消失时长
        self.state = "prologue"

    def _list_maps(self) -> list[Path]:
        return sorted(MAPS_DIR.glob("*.json"))

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

    def toast(self, text: str, seconds: float = 2.2) -> None:
        self.message = text
        self.message_t = seconds

    @staticmethod
    def dialog_quote(text: str) -> str:
        """所有对白统一格式：*「文本」。"""
        return f"*「{text}」"

    def current_grid(self) -> list[list[int]]:
        assert self.map_data
        return layer_grid(self.map_data, self.layer)

    def start_campaign(self) -> None:
        self.campaign = True
        self.level_idx = 0
        self.total_treasures = 0
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
        self.toast(data.get("name", "探险开始") + " · WASD移动 · 踩楼梯切换地面/地下")

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
            "name": data.get("name", "自定义地图"),
            "level": 0,
        }

    def start_editor(self, data: dict | None = None) -> None:
        if data is None:
            w, h = 52, 40
            surface = blank_grid(w, h, GRASS)
            under = blank_grid(w, h, BRICK)
            border_wall(surface, ROCK)
            border_wall(under, ROCK)
            # DIY 也放一座出发点房屋
            hx, hy = 4, h - 5
            surface[hy][hx] = HOUSE
            data = {
                "width": w,
                "height": h,
                "surface": surface,
                "underground": under,
                "start": [hx, hy + 1],
                "goal": [w - 4, 3],
                "goal_layer": "underground",
                "princess": True,
                "stairs": [],
                "name": "DIY 地图",
                "level": 0,
                "tile_schema": 2,
                "house": [hx, hy],
            }
        elif "surface" not in data:
            data = self._migrate_old_map(data)
        data = normalize_map_tiles(data)
        self.map_data = data
        self.layer = "surface"
        self.edit_layer = "surface"
        self.state = "editor"
        self.camera.x = self.camera.y = 0
        self.toast("滚轮/方向键平移 | Tab切地面地下 | 楼梯自动双层 | Ctrl+S保存 | P试玩")

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
                if t in PROP_OVERLAY:
                    base = default_base
                elif t == STAIRS:
                    base = default_base
                elif t == EMPTY:
                    base = default_base
                else:
                    base = t
                img = self.assets.tiles.get(base) or self.assets.tiles[GRASS]
                sx, sy = self.camera.apply(x * TILE, y * TILE)
                surf.blit(img, (sx, sy))

                if t == STAIRS:
                    stair_img = self.assets.stairs_up if self.layer == "underground" else self.assets.tiles[STAIRS]
                    surf.blit(stair_img, (sx, sy))
                elif t in PROP_OVERLAY and t in self.assets.tiles:
                    prop = self.assets.tiles[t]
                    if t == HOUSE:
                        # 放大房屋：以格底为基准居中落点
                        ox = sx + (TILE - prop.get_width()) // 2
                        oy = sy + TILE - prop.get_height()
                    elif t == GATE:
                        ox = sx + (TILE - prop.get_width()) // 2
                        oy = sy + TILE - prop.get_height()
                    else:
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

    @staticmethod
    def draw_textbox(surf: pygame.Surface, rect: pygame.Rect) -> None:
        """黑底白框（无底部箭头）。"""
        pygame.draw.rect(surf, (0, 0, 0), rect)
        pygame.draw.rect(surf, (255, 255, 255), rect, 2)

    def _reset_logo_anim_targets(self) -> None:
        """两 logo 终点相同；启动时刻不同，但同一 intro_dur 抵达。"""
        l1 = self.assets.start_logo1
        l2 = self.assets.start_logo2
        h = max(l1.get_height(), l2.get_height())
        meet_y = SCREEN_H * 0.05  # 相对原先再上移一点
        self.logo_meet_y = meet_y
        self.logo1_target_y = meet_y
        self.logo2_target_y = meet_y
        self.logo1_start_y = -float(h) - 24
        self.logo2_start_y = float(SCREEN_H) + 24
        self.logo1_y = self.logo1_start_y
        self.logo2_y = self.logo2_start_y
        self.intro_t = 0.0

    def enter_menu(self, play_intro: bool = True) -> None:
        self.state = "menu"
        if play_intro:
            self._reset_logo_anim_targets()
            self.intro_done = False
            self.menu_fade = 0.0
        else:
            self.logo1_y = self.logo1_target_y
            self.logo2_y = self.logo2_target_y
            self.intro_done = True
            self.menu_fade = 1.0

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
                if e.key == pygame.K_ESCAPE:
                    self.enter_menu(play_intro=True)
                    return
                if e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.prologue_done_fade:
                        self.enter_menu(play_intro=True)
                        return
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
            glow = pygame.Surface((300, 300), pygame.SRCALPHA)
            for r, a in ((140, 22), (95, 36), (55, 50)):
                pygame.draw.circle(glow, (90, 70, 120, int(a * princess_a / 255)), (150, 150), r)
            self.screen.blit(glow, (SCREEN_W // 2 - 150, SCREEN_H // 2 - 210))

            pr = self.assets.princess
            big = pygame.transform.scale(pr, (pr.get_width(), pr.get_height()))
            if princess_a < 255:
                big = big.copy()
                big.set_alpha(princess_a)
            bob = math.sin(pygame.time.get_ticks() / 700.0) * 4
            px = SCREEN_W // 2 - big.get_width() // 2
            py = int(SCREEN_H // 2 - big.get_height() // 2 - 40 + bob)
            self.screen.blit(big, (px, py))

        # 文本框随公主一起淡出
        if princess_a > 0:
            box_m = 36
            box_h = 96
            box = pygame.Rect(box_m, SCREEN_H - box_h - 28, SCREEN_W - box_m * 2, box_h)
            box_surf = pygame.Surface((box.w, box.h), pygame.SRCALPHA)
            pygame.draw.rect(box_surf, (0, 0, 0, princess_a), box_surf.get_rect())
            pygame.draw.rect(box_surf, (255, 255, 255, princess_a), box_surf.get_rect(), 2)
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
            self.screen.blit(text_surf, (box.x + 18, box.y + 22))

            hint = self.font_sm.render("ENTER / SPACE — Next     ESC — Skip to Title", True, (200, 200, 200))
            if princess_a < 255:
                hint = hint.copy()
                hint.set_alpha(princess_a)
            self.screen.blit(hint, (box.x + 18, box.bottom - 26))

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
                    self.menu_idx = 1
                    self._menu_select()
                elif e.key == pygame.K_l:
                    self.menu_idx = 2
                    self._menu_select()
                elif e.key == pygame.K_ESCAPE:
                    self.menu_idx = 3
                    self._menu_select()

        # logo1 先动、logo2 稍后；两者在 intro_dur 同一时刻到位
        if not self.intro_done:
            self.intro_t += dt

            def _logo_progress(delay: float) -> float:
                if self.intro_t <= delay:
                    return 0.0
                span = max(0.01, self.intro_dur - delay)
                return max(0.0, min(1.0, (self.intro_t - delay) / span))

            p1 = _logo_progress(self.logo1_delay)
            p2 = _logo_progress(self.logo2_delay)
            self.logo1_y = self.logo1_start_y + (self.logo1_target_y - self.logo1_start_y) * p1
            self.logo2_y = self.logo2_start_y + (self.logo2_target_y - self.logo2_start_y) * p2
            if self.intro_t >= self.intro_dur:
                self.logo1_y = self.logo1_target_y
                self.logo2_y = self.logo2_target_y
                self.intro_done = True
        if self.intro_done:
            self.menu_fade = min(1.0, self.menu_fade + dt * 2.2)

        self.screen.fill(self.assets.start_bg)

        l1 = self.assets.start_logo1
        l2 = self.assets.start_logo2
        # 同一水平位置，仅 Y 不同；汇合后 Y 相同 → 原图完全叠合
        lx = SCREEN_W // 2 - l1.get_width() // 2
        self.screen.blit(l1, (lx, int(self.logo1_y)))
        self.screen.blit(l2, (lx, int(self.logo2_y)))

        if self.menu_fade > 0.01:
            alpha = int(255 * self.menu_fade)
            menu_top = int(self.logo_meet_y) + max(l1.get_height(), l2.get_height()) + 20
            menu_top = min(menu_top, SCREEN_H - 180)
            for i, (label, key) in enumerate(self.menu_items):
                selected = i == self.menu_idx and self.intro_done
                color = (255, 230, 120) if selected else (235, 240, 250)
                prefix = "> " if selected else "  "
                left = self.font.render(prefix + label, True, color)
                right = self.font_sm.render(
                    f"[{key}]", True, (200, 210, 230) if selected else (160, 175, 195)
                )
                left.set_alpha(alpha)
                right.set_alpha(alpha)
                y = menu_top + i * 40
                self.screen.blit(left, (SCREEN_W // 2 - 140, y))
                self.screen.blit(right, (SCREEN_W // 2 + 90, y + 4))

            hint = self.font_sm.render("W/S Select   ENTER Confirm   ESC Quit", True, (190, 200, 220))
            hint.set_alpha(alpha)
            self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H - 40))
        elif not self.intro_done:
            skip = self.font_sm.render("ENTER — Skip", True, (180, 190, 210))
            self.screen.blit(skip, (SCREEN_W // 2 - skip.get_width() // 2, SCREEN_H - 40))

    def _menu_select(self) -> None:
        i = self.menu_idx
        if i == 0:
            self.start_campaign()
        elif i == 1:
            self.start_editor()
        elif i == 2:
            self.custom_maps = self._list_maps()
            if not self.custom_maps:
                self.message = "No DIY map in maps/"
                self.message_t = 3
                return
            with open(self.custom_maps[-1], encoding="utf-8") as f:
                self.start_play(json.load(f), campaign=False)
        else:
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def try_use_stairs(self) -> None:
        assert self.map_data and self.knight
        if self.stairs_cd > 0:
            return
        tx, ty = self.knight.tile_pos()
        mw, mh = map_size(self.map_data)
        if not (0 <= tx < mw and 0 <= ty < mh):
            return
        if self.current_grid()[ty][tx] != STAIRS:
            return
        self.layer = "underground" if self.layer == "surface" else "surface"
        # 保证对面也是楼梯 / 可走
        other = layer_grid(self.map_data, self.layer)
        if other[ty][tx] in SOLID:
            other[ty][tx] = STAIRS
        elif other[ty][tx] != STAIRS:
            other[ty][tx] = STAIRS
        self.knight.place_on_tile(tx, ty)
        self.stairs_cd = 0.6
        where = "地下" if self.layer == "underground" else "地面"
        self.toast(f"沿着楼梯来到了{where}")

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
                if e.key == pygame.K_ESCAPE:
                    self.enter_menu(play_intro=False)
                    return
                if e.key == pygame.K_r and self.campaign:
                    self._load_level(self.level_idx)
                    return

        if self.stairs_cd > 0:
            self.stairs_cd -= dt

        keys = pygame.key.get_pressed()
        self.knight.update(dt, keys, grid, mw, mh)
        self.camera.follow(self.knight.x, self.knight.y, mw, mh)

        tx, ty = self.knight.tile_pos()
        if 0 <= tx < mw and 0 <= ty < mh:
            cell = grid[ty][tx]
            if cell == TREASURE:
                grid[ty][tx] = BRICK if self.layer == "underground" else GRASS
                self.treasures += 1
                self.toast(f"宝箱 +1 （本关 {self.treasures}）")
            elif cell == STAIRS:
                self.try_use_stairs()

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

        layer_cn = "地下" if self.layer == "underground" else "地面"
        name = self.map_data.get("name", "")
        self.draw_ui_bar(
            f"{name} | {layer_cn} | 宝箱 {self.treasures} | Esc菜单"
            + (" | R重开本关" if self.campaign else "")
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
                    self._save_map()
                elif e.key == pygame.K_s and not ctrl:
                    self.edit_mode = "start"
                    self.toast("点击设置起点（地面）")
                elif e.key == pygame.K_g:
                    self.edit_mode = "goal"
                    self.toast("点击设置公主 / 终点（当前层）")
                elif e.key == pygame.K_t:
                    self.edit_mode = "tile"
                elif e.key == pygame.K_p:
                    self.start_play(json.loads(json.dumps(self.map_data)), campaign=False)
                elif e.key == pygame.K_n:
                    self.start_editor(generate_level(0))
                    self.state = "editor"
                    self.toast("已载入随机第1关样式")
                elif e.key == pygame.K_c:
                    self.start_editor()
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
            if e.type == pygame.MOUSEWHEEL:
                self.camera.y -= e.y * TILE * 2
                self.camera.clamp(mw, mh)
            if e.type == pygame.MOUSEBUTTONDOWN and e.button in (1, 3):
                self._paint_at(self._content_mouse(e.pos), erase=(e.button == 3))
            if e.type == pygame.MOUSEMOTION and e.buttons[0] and self.edit_mode == "tile":
                self._paint_at(self._content_mouse(e.pos), erase=False)

        world = pygame.Surface((VIEW_W, VIEW_H))
        world.fill((20, 20, 30) if self.edit_layer == "underground" else (30, 50, 40))
        self.draw_visible_map(world, grid, mw, mh, show_goal=True)
        mx, my = self._content_mouse(pygame.mouse.get_pos())
        if my < VIEW_H:
            wx = int(self.camera.x + mx) // TILE
            wy = int(self.camera.y + my) // TILE
            sx, sy = self.camera.apply(wx * TILE, wy * TILE)
            pygame.draw.rect(world, (255, 255, 100), (sx, sy, TILE, TILE), 2)
        self.screen.blit(world, (0, 0))

        brush_name = next((n for t, n in PALETTE if t == self.brush), "?")
        layer_cn = "地下" if self.edit_layer == "underground" else "地面"
        self.draw_ui_bar(
            f"DIY[{layer_cn}] {brush_name} | Tab切层 1-0/-/=笔刷 方向键平移 Ctrl+S P试玩"
        )

    def _paint_at(self, pos: tuple[int, int], erase: bool) -> None:
        assert self.map_data
        x, y = pos
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

        grid = self.current_grid()
        if erase:
            grid[ty][tx] = BRICK if self.edit_layer == "underground" else GRASS
            return
        grid[ty][tx] = self.brush
        if self.brush == STAIRS:
            # 双层同步楼梯
            other = "underground" if self.edit_layer == "surface" else "surface"
            layer_grid(self.map_data, other)[ty][tx] = STAIRS
            stairs = self.map_data.setdefault("stairs", [])
            if [tx, ty] not in stairs:
                stairs.append([tx, ty])

    def _save_map(self) -> None:
        assert self.map_data
        MAPS_DIR.mkdir(exist_ok=True)
        name = f"diy_{len(list(MAPS_DIR.glob('*.json'))) + 1:03d}.json"
        path = MAPS_DIR / name
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.map_data, f, ensure_ascii=False)
        self.custom_maps = self._list_maps()
        self.toast(f"已保存 {path.name}")

    def run(self) -> None:
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            if self.message_t > 0:
                self.message_t -= dt
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)

            if self.state == "prologue":
                self.run_prologue(events, dt)
            elif self.state == "menu":
                self.run_menu(events, dt)
                if self.message_t > 0:
                    tip = self.font_sm.render(self.message, True, (255, 200, 100))
                    self.screen.blit(tip, (SCREEN_W // 2 - tip.get_width() // 2, SCREEN_H - 70))
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
