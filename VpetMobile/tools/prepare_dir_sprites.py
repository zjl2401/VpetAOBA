"""补导出四向走动/工作/音乐立绘 + 金目 nc 方向图。"""
from pathlib import Path
from collections import deque
import shutil
from PIL import Image

ROOT = Path(r"C:\Users\36255\Desktop\VpetAOBA\VpetPNG\1.0")
SRC = ROOT / "assets" / "sprites"
OUT = Path(r"C:\Users\36255\Desktop\VpetAOBA\VpetMobile\app\src\main\assets\sprites")
OUT.mkdir(parents=True, exist_ok=True)

GREEN_JPG = [
    "walkleft1.jpg", "walkleft2.jpg",
    "walkback1.jpg", "walkback2.jpg",
    "workleft1.jpg", "workleft2.jpg",
    "workback1.jpg", "workback2.jpg",
    "musicleft1.jpg", "musicleft2.jpg",
    "musicback1.jpg", "musicback2.jpg",
    "musicstand.jpg", "musicfront1.jpg", "musicfront2.jpg",
]

NC_PNG = [
    "ncwalkleft1.png", "ncwalkleft2.png",
    "ncwalkback1.png", "ncwalkback2.png",
    "ncworkleft1.png", "ncworkleft2.png",
    "ncworkback1.png", "ncworkback2.png",
    "ncmusicleft1.png", "ncmusicleft2.png",
    "ncmusicback1.png", "ncmusicback2.png",
]


def is_chroma_green(r, g, b, a=255):
    if a < 8:
        return False
    if g > 200 and r < 90 and b < 90:
        return True
    return g > 100 and g >= r + 15 and g >= b + 25


def flood_key(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()
    vis = [[False] * w for _ in range(h)]
    q = deque()
    for x in range(w):
        q.append((x, 0))
        q.append((x, h - 1))
    for y in range(h):
        q.append((0, y))
        q.append((w - 1, y))
    while q:
        x, y = q.popleft()
        if x < 0 or y < 0 or x >= w or y >= h or vis[y][x]:
            continue
        r, g, b, a = px[x, y]
        if not is_chroma_green(r, g, b, a):
            continue
        vis[y][x] = True
        px[x, y] = (r, g, b, 0)
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return rgba


def export_jpg(name: str):
    src = SRC / name
    if not src.exists():
        print("MISSING", name)
        return
    keyed = flood_key(Image.open(src))
    bbox = keyed.getbbox()
    if bbox:
        keyed = keyed.crop(bbox)
    out_name = name.replace(".jpg", ".png")
    keyed.save(OUT / out_name, "PNG")
    print("ok", out_name, keyed.size)


def copy_nc(name: str):
    src = SRC / name
    if not src.exists():
        print("MISSING", name)
        return
    im = Image.open(src).convert("RGBA")
    # nc 已是透明 PNG；若仍有绿边再抠；不缩放
    keyed = flood_key(im)
    bbox = keyed.getbbox()
    if bbox:
        keyed = keyed.crop(bbox)
    keyed.save(OUT / name, "PNG")
    print("ok", name, keyed.size)


for n in GREEN_JPG:
    export_jpg(n)
for n in NC_PNG:
    copy_nc(n)

# RPG 用小人物：从 Vpetgame 拷已抠好的 walk/stand
rpg_src = ROOT / "bundled" / "Vpetgame" / "assets" / "vpet"
rpg_out = Path(r"C:\Users\36255\Desktop\VpetAOBA\VpetMobile\app\src\main\assets\rpg")
rpg_out.mkdir(parents=True, exist_ok=True)
for name in ("stand.png", "walkfront1.png", "walkfront2.png", "walkback1.png", "walkback2.png",
             "walkleft1.png", "walkleft2.png"):
    p = rpg_src / name
    if p.exists():
        shutil.copy2(p, rpg_out / name)
        print("rpg", name)
print("done")
