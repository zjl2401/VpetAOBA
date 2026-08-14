from PIL import Image
from pathlib import Path

d = Path(r"c:\Users\36255\Desktop\VpetAOBA\VpetMobile\app\src\main\assets\sprites")
src = Path(r"c:\Users\36255\Desktop\VpetAOBA\VpetPNG\1.0\assets\sprites")
for n in ["box.png", "flag.png", "workstand.png", "workfront1.png"]:
    p = d / n
    if p.exists():
        im = Image.open(p)
        print("mobile", n, im.size, im.mode)
for n in ["box.jpg", "flag.jpg", "workstand.jpg", "workfront1.jpg"]:
    p = src / n
    if p.exists():
        im = Image.open(p)
        print("desktop", n, im.size, im.mode)
