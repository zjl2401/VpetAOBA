"""导出智能伴侣莲（minipet/allmate）透明立绘。优先 allmate PNG，否则抠 minipet JPG。"""
from pathlib import Path
from collections import deque
from PIL import Image

ROOT = Path(r"C:\Users\36255\Desktop\VpetAOBA\VpetPNG\1.0")
ALLMATE = ROOT / "bundled" / "Vpetgame" / "assets" / "allmate"
MINIPET = ROOT / "assets" / "minipet"
OUT = Path(r"C:\Users\36255\Desktop\VpetAOBA\VpetMobile\app\src\main\assets\minipet")
OUT.mkdir(parents=True, exist_ok=True)

NAMES = [
    "petstand",
    "petfront1", "petfront2",
    "petback1", "petback2",
    "petleft1", "petleft2",
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
        q.append((x, 0)); q.append((x, h - 1))
    for y in range(h):
        q.append((0, y)); q.append((w - 1, y))
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


def export(name: str, max_side=320):
    png = ALLMATE / f"{name}.png"
    jpg = ALLMATE / f"{name}.jpg"
    src = png if png.exists() else (jpg if jpg.exists() else MINIPET / f"{name}.jpg")
    if not src.exists():
        print("MISSING", name)
        return
    keyed = flood_key(Image.open(src))
    bbox = keyed.getbbox()
    if bbox:
        keyed = keyed.crop(bbox)
    w, h = keyed.size
    scale = min(max_side / w, max_side / h, 1.0)
    if scale < 1:
        keyed = keyed.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
    keyed.save(OUT / f"{name}.png", "PNG")
    print("ok", name, keyed.size, "from", src.name)


for n in NAMES:
    export(n)
print("done")
