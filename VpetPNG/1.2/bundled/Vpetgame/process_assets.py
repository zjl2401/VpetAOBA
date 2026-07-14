"""抠除外圈黑/白/绿背景，统一缩放到游戏尺寸，输出到 assets/。"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "assets"

TILE = 48
CHAR_W, CHAR_H = 48, 64
PROP = 48
OVERSIZED = 96  # house 等超大地物

# 全幅铺砖纹理：只缩放，不抠图
TILE_ONLY = {
    "grass.png",
    "land.png",
    "water.png",
    "brick.jpg",
}

# 对话框边框：抠绿后另存
BORDER_SRC = "border.jpg"

# 旧整屏标题（备用）
TITLE = {"start.png"}

# 开场：纯色样板 + Logo 部件
START_COLOR = "startcolor.png"
START_LOGO = "startlogo.png"  # 旧整图备用
START_LOGO1 = "startlogo1.jpg"  # 十字架，上方入场
START_LOGO2 = "startlogo2.png"  # 标题字，下方入场（上层）
SKIP_GENERIC = {START_COLOR, START_LOGO, START_LOGO1, START_LOGO2, BORDER_SRC}

# 角色（含走路帧）
CHARS = {
    "knightstand.png",
    "knightwalk1.png",
    "knightwalk2.png",
    "knightwalkback1.png",
    "knightwalkback2.png",
    "knightwalkright1.png",
    "knightwalkright2.png",
    "princess.png",
}

# 障碍 / 道具
PROPS = {
    "tree.png",
    "rock.png",
    "obstacle.png",
    "treasure.png",
}

# 超大建筑
BIG = {"house.png"}


def near_chroma(r: int, g: int, b: int, a: int) -> bool:
    """外圈常见抠图色：白、黑、绿幕。"""
    if a < 16:
        return True
    # 近白
    if r >= 245 and g >= 245 and b >= 245:
        return True
    if r >= 230 and g >= 230 and b >= 230 and max(r, g, b) - min(r, g, b) <= 12:
        return True
    # 近黑
    if r <= 12 and g <= 12 and b <= 12:
        return True
    # 绿幕（饱和绿）
    if g >= 180 and g > r + 40 and g > b + 40:
        return True
    if g >= 140 and r <= 100 and b <= 100 and g > r + 30 and g > b + 30:
        return True
    return False


def flood_key(im: Image.Image) -> Image.Image:
    """从四角 flood-fill 去掉连通的色键背景（仅外圈连通，不伤图内同色）。"""
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    visited = [[False] * w for _ in range(h)]
    stack: list[tuple[int, int]] = []

    for sx, sy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        r, g, b, a = px[sx, sy]
        if near_chroma(r, g, b, a):
            stack.append((sx, sy))
    # 外围一圈也入栈，避免四角恰好不是色键
    for x in range(w):
        for y in (0, h - 1):
            r, g, b, a = px[x, y]
            if near_chroma(r, g, b, a):
                stack.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            r, g, b, a = px[x, y]
            if near_chroma(r, g, b, a):
                stack.append((x, y))

    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= w or y >= h or visited[y][x]:
            continue
        r, g, b, a = px[x, y]
        if not near_chroma(r, g, b, a):
            continue
        visited[y][x] = True
        px[x, y] = (r, g, b, 0)
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return im


def bbox_alpha(im: Image.Image) -> Image.Image:
    """裁到不透明内容包围盒。"""
    a = im.split()[-1]
    box = a.getbbox()
    if not box:
        return im
    return im.crop(box)


def fit_canvas(im: Image.Image, tw: int, th: int) -> Image.Image:
    """等比缩放进固定画布，底部对齐（角色脚底），最近邻保持像素感。"""
    im = im.convert("RGBA")
    iw, ih = im.size
    if iw == 0 or ih == 0:
        return Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    scale = min(tw / iw, th / ih)
    nw = max(1, int(round(iw * scale)))
    nh = max(1, int(round(ih * scale)))
    im = im.resize((nw, nh), Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    ox = (tw - nw) // 2
    oy = th - nh  # 脚底对齐
    canvas.paste(im, (ox, oy), im)
    return canvas


def stretch_tile(im: Image.Image, size: int) -> Image.Image:
    return im.convert("RGBA").resize((size, size), Image.Resampling.NEAREST)


def sample_bg_color(im: Image.Image) -> tuple[int, int, int]:
    """取 startcolor 主色。"""
    im = im.convert("RGB")
    # 缩小后取平均，抗噪
    small = im.resize((8, 8), Image.Resampling.BOX)
    pixels = list(small.getdata())
    n = len(pixels)
    return (
        sum(p[0] for p in pixels) // n,
        sum(p[1] for p in pixels) // n,
        sum(p[2] for p in pixels) // n,
    )


def key_blue_bg(im: Image.Image, key_rgb: tuple[int, int, int], thresh: float = 38.0) -> Image.Image:
    """抠掉接近蓝底色的连通背景（从四角 flood）。"""
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    kr, kg, kb = key_rgb

    def is_key(r: int, g: int, b: int, a: int) -> bool:
        if a < 16:
            return True
        dist = ((r - kr) ** 2 + (g - kg) ** 2 + (b - kb) ** 2) ** 0.5
        return dist <= thresh

    visited = [[False] * w for _ in range(h)]
    stack: list[tuple[int, int]] = []
    for sx, sy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        r, g, b, a = px[sx, sy]
        if is_key(r, g, b, a):
            stack.append((sx, sy))

    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= w or y >= h or visited[y][x]:
            continue
        r, g, b, a = px[x, y]
        if not is_key(r, g, b, a):
            continue
        visited[y][x] = True
        px[x, y] = (r, g, b, 0)
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    return im


def is_chroma_green(r: int, g: int, b: int, a: int = 255) -> bool:
    """外圈青草绿幕。"""
    if a < 16:
        return True
    # 高绿低红蓝（border 绿幕约 160,215,12）
    if g >= 140 and g > r + 35 and g > b + 35:
        return True
    if g >= 180 and r < 200 and b < 120 and g > r + 20:
        return True
    return False


def key_green_outer(im: Image.Image) -> Image.Image:
    """从四角 flood 抠掉外圈绿色。"""
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    visited = [[False] * w for _ in range(h)]
    stack: list[tuple[int, int]] = []
    for sx, sy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        r, g, b, a = px[sx, sy]
        if is_chroma_green(r, g, b, a):
            stack.append((sx, sy))
    # 底边可能全是绿，多扫一圈外圈像素入栈
    for x in range(w):
        for y in (0, 1, h - 2, h - 1):
            r, g, b, a = px[x, y]
            if is_chroma_green(r, g, b, a):
                stack.append((x, y))
    for y in range(h):
        for x in (0, 1, w - 2, w - 1):
            r, g, b, a = px[x, y]
            if is_chroma_green(r, g, b, a):
                stack.append((x, y))

    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= w or y >= h or visited[y][x]:
            continue
        r, g, b, a = px[x, y]
        if not is_chroma_green(r, g, b, a):
            continue
        visited[y][x] = True
        px[x, y] = (r, g, b, 0)
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return im


def punch_dark_interior(im: Image.Image, lum_thresh: int = 48) -> Image.Image:
    """挖空画面中心深色区域，只留外圈发光边框。"""
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()

    def is_interior(r: int, g: int, b: int, a: int) -> bool:
        if a < 16:
            return True
        # 中心黑 / 深灰，排除青蓝边框（边框 g、b 通常较高）
        lum = (r + g + b) // 3
        if lum <= lum_thresh and abs(r - g) < 25 and abs(g - b) < 25:
            return True
        if r < 40 and g < 50 and b < 55:
            return True
        return False

    visited = [[False] * w for _ in range(h)]
    stack = [(w // 2, h // 2)]
    # 多点从中心附近种子，防止正中刚好不黑
    for dx in (-20, 0, 20):
        for dy in (-20, 0, 20):
            stack.append((w // 2 + dx, h // 2 + dy))

    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= w or y >= h or visited[y][x]:
            continue
        r, g, b, a = px[x, y]
        if not is_interior(r, g, b, a):
            continue
        visited[y][x] = True
        px[x, y] = (r, g, b, 0)
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return im


def process_border() -> None:
    """抠绿 + 挖空中心 → 窗口外边框；另存 48 地砖。"""
    src = ROOT / BORDER_SRC
    if not src.exists():
        return
    OUT.mkdir(parents=True, exist_ok=True)
    keyed = key_green_outer(Image.open(src))
    hollow = punch_dark_interior(keyed)
    cropped = bbox_alpha(hollow)
    cropped.save(OUT / "window_frame.png")
    # 兼容旧文件名
    cropped.save(OUT / "ui_border.png")
    print(f"[frame] border.jpg -> window_frame.png {cropped.size} (green keyed, hollow)")

    # 地图用地砖：从挖空前的素材取青边区域缩放
    tile_src = bbox_alpha(keyed).resize((TILE, TILE), Image.Resampling.NEAREST)
    tile_src.save(OUT / "border.png")
    print(f"[tile]  border.jpg -> border.png {TILE}x{TILE}")


def _key_logo_keep_align(src: Path, bg: tuple[int, int, int]) -> Image.Image:
    """只抠蓝，保留原画布尺寸，避免裁切导致两张图错位。"""
    return key_blue_bg(Image.open(src), bg, thresh=42.0)


def process_start_screen() -> tuple[int, int, int]:
    """处理 startcolor / startlogo1 / startlogo2，返回背景 RGB。"""
    OUT.mkdir(parents=True, exist_ok=True)
    color_path = ROOT / START_COLOR
    if not color_path.exists():
        bg = (69, 104, 144)
    else:
        bg = sample_bg_color(Image.open(color_path))
        Image.new("RGB", (1, 1), bg).save(OUT / "startcolor.png")
        print(f"[start] startcolor -> RGB{bg}")

    logo1_path = ROOT / START_LOGO1
    logo2_path = ROOT / START_LOGO2
    legacy = ROOT / START_LOGO

    imgs: list[tuple[str, Image.Image]] = []
    if logo1_path.exists():
        imgs.append(("startlogo1.png", _key_logo_keep_align(logo1_path, bg)))
    if logo2_path.exists():
        imgs.append(("startlogo2.png", _key_logo_keep_align(logo2_path, bg)))
    elif legacy.exists():
        imgs.append(("startlogo.png", _key_logo_keep_align(legacy, bg)))

    if len(imgs) >= 2:
        # 统一到相同画布（取最大宽高），一律贴在 (0,0)，不缩放不居中
        mw = max(im.size[0] for _, im in imgs)
        mh = max(im.size[1] for _, im in imgs)
        for name, im in imgs:
            canvas = Image.new("RGBA", (mw, mh), (0, 0, 0, 0))
            canvas.paste(im, (0, 0), im)
            canvas.save(OUT / name)
            print(f"[start] {name} -> {mw}x{mh} (blue keyed, aligned canvas)")
    else:
        for name, im in imgs:
            im.save(OUT / name)
            print(f"[start] {name} -> {im.size} (blue keyed)")
    return bg


def process_one(src: Path) -> None:
    name = src.name
    out_name = src.stem + ".png"
    OUT.mkdir(parents=True, exist_ok=True)
    im = Image.open(src)

    if name in SKIP_GENERIC:
        return

    if name in TITLE:
        # 标题屏专用，缩放到 800x600
        im = im.convert("RGBA").resize((800, 600), Image.Resampling.NEAREST)
        im.save(OUT / out_name)
        print(f"[title] {name} -> {out_name} 800x600")
        return

    if name in TILE_ONLY:
        out = stretch_tile(im, TILE)
        out.save(OUT / out_name)
        print(f"[tile]  {name} -> {out_name} {TILE}x{TILE}")
        return

    keyed = flood_key(im)
    cropped = bbox_alpha(keyed)

    if name in CHARS:
        out = fit_canvas(cropped, CHAR_W, CHAR_H)
        out.save(OUT / out_name)
        print(f"[char]  {name} -> {out_name} {CHAR_W}x{CHAR_H}")
    elif name in BIG:
        out = fit_canvas(cropped, OVERSIZED, OVERSIZED)
        out.save(OUT / out_name)
        print(f"[big]   {name} -> {out_name} {OVERSIZED}x{OVERSIZED}")
    elif name in PROPS:
        out = fit_canvas(cropped, PROP, PROP)
        out.save(OUT / out_name)
        print(f"[prop]  {name} -> {out_name} {PROP}x{PROP}")
    else:
        out = fit_canvas(cropped, PROP, PROP)
        out.save(OUT / out_name)
        print(f"[other] {name} -> {out_name} {PROP}x{PROP}")


def main() -> None:
    exts = {".png", ".jpg", ".jpeg"}
    files = sorted(p for p in ROOT.iterdir() if p.suffix.lower() in exts and p.is_file())
    if not files:
        raise SystemExit("未找到素材文件")
    print(f"处理 {len(files)} 张素材 -> {OUT}")
    process_start_screen()
    process_border()
    for f in files:
        process_one(f)
    print("完成。")


if __name__ == "__main__":
    main()
