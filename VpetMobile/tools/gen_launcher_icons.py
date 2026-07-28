"""从桌面版 app_icon1 生成 Android 启动图标。"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DESKTOP = ROOT.parent / "VpetPNG" / "1.0"
RES = ROOT / "app" / "src" / "main" / "res"


def load_source() -> Image.Image:
    for name in ("app_icon1.jpg", "app_icon1.png", "app_icon.png"):
        p = DESKTOP / name
        if p.exists():
            src = Image.open(p).convert("RGBA")
            print("source:", p)
            return src
    raise SystemExit("desktop app icon not found")


def normalize_bg(im: Image.Image) -> Image.Image:
    pixels = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if r < 18 and g < 18 and b < 18:
                pixels[x, y] = (0, 0, 0, 255)
    return im


def fit_square(im: Image.Image, size: int, pad_ratio: float = 0.0) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 255))
    inner = max(1, int(size * (1 - pad_ratio)))
    scaled = im.resize((inner, inner), Image.Resampling.LANCZOS)
    off = (size - inner) // 2
    canvas.paste(scaled, (off, off), scaled)
    return canvas


def main() -> None:
    src = normalize_bg(load_source())
    sizes = {
        "mipmap-mdpi": 48,
        "mipmap-hdpi": 72,
        "mipmap-xhdpi": 96,
        "mipmap-xxhdpi": 144,
        "mipmap-xxxhdpi": 192,
    }
    for folder, size in sizes.items():
        out = fit_square(src, size)
        d = RES / folder
        d.mkdir(parents=True, exist_ok=True)
        out.save(d / "ic_launcher.png")
        out.save(d / "ic_launcher_round.png")
        print("wrote", folder, size)

    drawable = RES / "drawable"
    drawable.mkdir(parents=True, exist_ok=True)
    fit_square(src, 432, pad_ratio=0.18).save(drawable / "ic_launcher_foreground.png")
    fit_square(src, 256).save(drawable / "app_cover.png")
    print("foreground + app_cover ok")


if __name__ == "__main__":
    main()
