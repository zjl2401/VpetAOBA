"""从桌面默认 JPG 外圈绿幕抠图，导出手机用透明 PNG；并同步 app 图标。"""
from pathlib import Path
from collections import deque
import shutil
from PIL import Image

src_dir = Path(r"C:\Users\36255\Desktop\VpetAOBA\VpetPNG\1.0\assets\sprites")
out_dir = Path(r"C:\Users\36255\Desktop\VpetAOBA\VpetMobile\app\src\main\assets\sprites")
shared = Path(r"C:\Users\36255\Desktop\VpetAOBA\VpetMobile\assets_shared\sprites")
out_dir.mkdir(parents=True, exist_ok=True)
shared.mkdir(parents=True, exist_ok=True)

for p in list(out_dir.glob("nc*")) + list(shared.glob("nc*")):
    p.unlink()

files = [
    "stand.jpg",
    "hi1.jpg",
    "hi2.jpg",
    "sleep1.jpg",
    "sleep2.jpg",
    "happy.jpg",
    "walkfront1.jpg",
    "walkfront2.jpg",
    "play_game1.jpg",
    "play_game2.jpg",
    "watch_video1.jpg",
    "video.jpg",
    "allmate.jpg",
]


def is_chroma_green(r: int, g: int, b: int, a: int = 255) -> bool:
    # 与桌面 pet.py _is_chroma_green / _remove_green 一致：只抠外圈连通键色
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
    q: deque[tuple[int, int]] = deque()
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


# 只抠外圈绿幕并裁包围盒，不缩放（显示尺寸由 App 运行时控制）
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
    shutil.copy2(src, shared / name)
    print(out_name, keyed.size)

icon_src = Path(r"C:\Users\36255\Desktop\VpetAOBA\VpetPNG\1.0\app_icon.png")
res = Path(r"C:\Users\36255\Desktop\VpetAOBA\VpetMobile\app\src\main\res")
# 启动图标改由 tools/gen_launcher_icons.py 生成（透明抠图）；此处仅同步通知小图
if icon_src.is_file():
    icon = Image.open(icon_src).convert("RGBA")
    drawable = res / "drawable"
    drawable.mkdir(parents=True, exist_ok=True)
    # 若仍是旧深色底，尽量去掉近黑不透明底
    px = icon.load()
    w, h = icon.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 200 and r <= 24 and g <= 28 and b <= 40:
                px[x, y] = (0, 0, 0, 0)
    icon.resize((96, 96), Image.Resampling.LANCZOS).save(
        drawable / "ic_pet_notify.png", "PNG"
    )
    print("notify icon synced from app_icon (transparent-safe)")
else:
    print("skip icons: app_icon.png missing")
print("done")
