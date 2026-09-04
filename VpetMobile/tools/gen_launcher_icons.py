"""从桌面版 stand 立绘生成 Android 启动图标（抠绿幕、等比例缩放/裁剪，禁止非等比拉伸）。"""
from collections import deque
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DESKTOP = ROOT.parent / "VpetPNG" / "1.0"
RES = ROOT / "app" / "src" / "main" / "res"


def _is_chroma_green(r: int, g: int, b: int, a: int = 255) -> bool:
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
        if not _is_chroma_green(r, g, b, a):
            continue
        visited[y][x] = True
        px[x, y] = (r, g, b, 0)
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return rgba


def prepare_stand(im: Image.Image) -> Image.Image:
    keyed = remove_outer_green(im)
    bbox = keyed.getbbox()
    if bbox:
        keyed = keyed.crop(bbox)
    return keyed


def load_source() -> Image.Image:
    # 与电脑版快捷方式同一套：优先现成 app_icon，再 normal cutout stand
    for rel in (
        "app_icon.png",
        "assets/cutout/sprites/stand.png",
        "assets/sprites/stand.png",
        "assets/sprites/stand.jpg",
        "assets/raw_green/sprites/stand.jpg",
        "gallery/stand.png",
        "gallery/stand.jpg",
    ):
        p = DESKTOP / rel
        if p.is_file():
            print("source:", p)
            if p.name.lower().startswith("app_icon"):
                return Image.open(p).convert("RGBA")
            return prepare_stand(Image.open(p))
    raise SystemExit("desktop stand / app_icon not found")


def fit_square_contain_nearest(
    im: Image.Image,
    size: int,
    *,
    bg: tuple[int, int, int, int] = (0, 0, 0, 0),
    pad_ratio: float = 0.04,
) -> Image.Image:
    inner = max(1, int(size * (1.0 - pad_ratio)))
    w, h = im.size
    scale = min(inner / max(w, 1), inner / max(h, 1))
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    scaled = im.resize((nw, nh), Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", (size, size), bg)
    canvas.paste(scaled, ((size - nw) // 2, (size - nh) // 2), scaled)
    return canvas


def main() -> None:
    src = load_source()
    sizes = {
        "mipmap-mdpi": 48,
        "mipmap-hdpi": 72,
        "mipmap-xhdpi": 96,
        "mipmap-xxhdpi": 144,
        "mipmap-xxxhdpi": 192,
    }
    for folder, size in sizes.items():
        out = fit_square_contain_nearest(src, size, bg=(0, 0, 0, 0), pad_ratio=0.04)
        d = RES / folder
        d.mkdir(parents=True, exist_ok=True)
        out.save(d / "ic_launcher.png")
        out.save(d / "ic_launcher_round.png")
        print("wrote", folder, size)

    drawable = RES / "drawable"
    drawable.mkdir(parents=True, exist_ok=True)
    fit_square_contain_nearest(src, 432, bg=(0, 0, 0, 0), pad_ratio=0.18).save(
        drawable / "ic_launcher_foreground.png"
    )
    fit_square_contain_nearest(src, 256, bg=(0, 0, 0, 0), pad_ratio=0.04).save(
        drawable / "app_cover.png"
    )
    fit_square_contain_nearest(src, 96, bg=(0, 0, 0, 0), pad_ratio=0.04).save(
        drawable / "ic_pet_notify.png"
    )
    print("foreground + app_cover + notify ok")


if __name__ == "__main__":
    main()
