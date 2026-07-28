"""导出工作相关精灵：work* 绿幕外圈；box/flag 品红色键外圈。"""
from pathlib import Path
from collections import deque
from PIL import Image

root = Path(r"C:\Users\36255\Desktop\VpetAOBA\VpetPNG\1.0")
out = Path(r"C:\Users\36255\Desktop\VpetAOBA\VpetMobile\app\src\main\assets\sprites")
shared = Path(r"C:\Users\36255\Desktop\VpetAOBA\VpetMobile\assets_shared\sprites")
out.mkdir(parents=True, exist_ok=True)
shared.mkdir(parents=True, exist_ok=True)

GREEN = [
    "workstand.jpg",
    "workfront1.jpg",
    "workfront2.jpg",
]
MAGENTA = [
    (root / "assets" / "props" / "box.jpg", "box.png"),
    (root / "assets" / "props" / "flag.jpg", "flag.png"),
]


def is_chroma_green(r, g, b, a=255):
    if a < 8:
        return False
    if g > 200 and r < 90 and b < 90:
        return True
    return g > 100 and g >= r + 15 and g >= b + 25


def is_chroma_magenta(r, g, b, a=255):
    # WORK_CHROMA_RGB = (255, 0, 255) 宽松匹配
    if a < 8:
        return False
    return r > 200 and b > 200 and g < 80


def flood_key(img: Image.Image, is_key) -> Image.Image:
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
        if not is_key(r, g, b, a):
            continue
        vis[y][x] = True
        px[x, y] = (r, g, b, 0)
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return rgba


def export(src: Path, out_name: str, is_key, max_side=256):
    keyed = flood_key(Image.open(src), is_key)
    bbox = keyed.getbbox()
    if bbox:
        keyed = keyed.crop(bbox)
    w, h = keyed.size
    scale = min(max_side / w, max_side / h, 1.0)
    if scale < 1:
        keyed = keyed.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
    keyed.save(out / out_name, "PNG")
    keyed.save(shared / out_name, "PNG")
    print(out_name, keyed.size)


for name in GREEN:
    export(root / "assets" / "sprites" / name, name.replace(".jpg", ".png"), is_chroma_green, 512)
for src, name in MAGENTA:
    export(src, name, is_chroma_magenta, 128)
print("done")
