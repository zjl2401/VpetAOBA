"""校验：工作旗/箱裁剪后不是大黑块；采集下落非黑。"""
from pathlib import Path
import pet

out = Path(__file__).resolve().parent
for name in ("box.jpg", "flag.jpg"):
    rgb = pet._work_prop_rgb_image(name, 128)
    px = list(rgb.getdata())
    black = sum(1 for r, g, b in px if r <= 30 and g <= 30 and b <= 30)
    print(name, "size", rgb.size, "black%", round(100 * black / len(px), 1), "mid", px[len(px) // 2])
    assert black < 35, f"{name} still too black"
    rgb.save(out / f"debug_{name}.png")

import tkinter as tk

root = tk.Tk()
root.withdraw()
try:
    for kind, fid in (("food", "apple"), ("time_plus", None), ("dizzy", None)):
        img = pet._render_game_drop_rgb(kind, fid, 76)
        black = sum(1 for r, g, b in img.getdata() if r <= 30 and g <= 30 and b <= 30)
        print(f"drop {kind}: black%={round(100 * black / (76 * 76), 1)} mid={img.getpixel((38, 38))}")
        assert black < 40
    print("OK")
finally:
    root.destroy()
