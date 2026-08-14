"""导出动作/表情默认立绘（非 nc*）：外圈绿幕连通抠图。"""
from pathlib import Path
from collections import deque
from PIL import Image

src_dir = Path(r"C:\Users\36255\Desktop\VpetAOBA\VpetPNG\1.0\assets\sprites")
out_dir = Path(r"C:\Users\36255\Desktop\VpetAOBA\VpetMobile\app\src\main\assets\sprites")
shared = Path(r"C:\Users\36255\Desktop\VpetAOBA\VpetMobile\assets_shared\sprites")
out_dir.mkdir(parents=True, exist_ok=True)
shared.mkdir(parents=True, exist_ok=True)

files = [
    "sad1.jpg", "sad2.jpg",
    "shy1.jpg", "shy2.jpg",
    "wink.jpg", "like.jpg",
    "squat.jpg", "kick.jpg",
    "yes.jpg", "no.jpg",
    "call1.jpg", "call2.jpg",
    "eat1.jpg", "eat2.jpg",
    "move1.jpg", "move2.jpg", "move3.jpg",
    "walkback1.jpg", "walkback2.jpg",
]


def is_chroma_green(r, g, b, a=255):
    if a < 8:
        return False
    if g > 200 and r < 90 and b < 90:
        return True
    return g > 100 and g >= r + 15 and g >= b + 25


def remove_outer_green(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()
    visited = [[False] * w for _ in range(h)]
    q = deque()
    for x in range(w):
        q.append((x, 0))
        q.append((x, h - 1))
    for y in range(h):
        q.append((0, y))
        q.append((w - 1, y))
    while q:
        x, y = q.popleft()
        if x < 0 or y < 0 or x >= w or y >= h or visited[y][x]:
            continue
        r, g, b, a = px[x, y]
        if not is_chroma_green(r, g, b, a):
            continue
        visited[y][x] = True
        px[x, y] = (r, g, b, 0)
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return rgba


# 只抠图+裁包围盒，不缩放
for name in files:
    src = src_dir / name
    if not src.exists():
        print("MISSING", name)
        continue
    keyed = remove_outer_green(Image.open(src))
    bbox = keyed.getbbox()
    if bbox:
        keyed = keyed.crop(bbox)
    out_name = name.replace(".jpg", ".png")
    keyed.save(out_dir / out_name, "PNG")
    keyed.save(shared / out_name, "PNG")
    print(out_name, keyed.size)
print("done")
