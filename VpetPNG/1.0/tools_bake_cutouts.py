#!/usr/bin/env python3
"""把绿幕图预抠成透明 PNG → assets/cutout/，原图移到 assets/raw_green/。

覆盖普通与黑框图组：sprites / minipet / props / ui / sprites_black / minipet_black
已有 RGBA PNG（如 nc*）也会写入 cutout（必要时再抠外圈绿）。
"""
from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
CUTOUT = ASSETS / "cutout"
RAW = ASSETS / "raw_green"
SUBDIRS = ("sprites", "minipet", "props", "ui", "sprites_black", "minipet_black")
OUTER_LIME = frozenset({"yes.jpg", "no.jpg", "box.jpg", "flag.jpg", "shy3.jpg", "yes.png", "no.png", "box.png", "flag.png", "shy3.png"})


def _is_chroma_green(r: int, g: int, b: int) -> bool:
    return ((g > 200) and (r < 90) and (b < 90)) or ((g > 100) and (g >= r + 15) and (g >= b + 25))


def _remove_outer_key_rgba(img: Image.Image, key_mask) -> Image.Image:
    try:
        import numpy as np
        from collections import deque

        arr = np.asarray(img.convert("RGBA"), dtype=np.uint8).copy()
        h, w = arr.shape[:2]
        key = np.asarray(key_mask, dtype=bool)
        if key.shape[:2] != (h, w):
            return img.convert("RGBA")
        visited = np.zeros((h, w), dtype=bool)
        q: deque[tuple[int, int]] = deque()
        for x in range(w):
            for y in (0, h - 1):
                if key[y, x] and not visited[y, x]:
                    visited[y, x] = True
                    q.append((x, y))
        for y in range(h):
            for x in (0, w - 1):
                if key[y, x] and not visited[y, x]:
                    visited[y, x] = True
                    q.append((x, y))
        while q:
            x, y = q.popleft()
            arr[y, x, 3] = 0
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < w and 0 <= ny < h and key[ny, nx] and not visited[ny, nx]:
                    visited[ny, nx] = True
                    q.append((nx, ny))
        return Image.fromarray(arr, "RGBA")
    except Exception:
        rgba = img.convert("RGBA")
        px = rgba.load()
        w, h = rgba.size
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if a > 8 and _is_chroma_green(r, g, b):
                    if x == 0 or y == 0 or x == w - 1 or y == h - 1:
                        px[x, y] = (r, g, b, 0)
        return rgba


def _remove_green(img: Image.Image) -> Image.Image:
    try:
        import numpy as np

        arr = np.asarray(img.convert("RGBA"), dtype=np.uint8)
        r = arr[..., 0].astype(np.int16)
        g = arr[..., 1].astype(np.int16)
        b = arr[..., 2].astype(np.int16)
        a = arr[..., 3]
        key = (a > 8) & (
            ((g > 200) & (r < 90) & (b < 90))
            | ((g > 100) & (g >= r + 15) & (g >= b + 25))
        )
        return _remove_outer_key_rgba(img, key)
    except Exception:
        rgba = img.convert("RGBA")
        px = rgba.load()
        w, h = rgba.size
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if a > 8 and _is_chroma_green(r, g, b):
                    px[x, y] = (r, g, b, 0)
        return rgba


def _remove_outer_lime_green(img: Image.Image) -> Image.Image:
    try:
        import numpy as np

        arr = np.asarray(img.convert("RGBA"), dtype=np.uint8)
        r = arr[..., 0].astype(np.int16)
        g = arr[..., 1].astype(np.int16)
        b = arr[..., 2].astype(np.int16)
        a = arr[..., 3]
        key = (a > 8) & (g > 140) & (g >= r + 20) & (g >= b + 10) & (b < 180)
        return _remove_outer_key_rgba(img, key)
    except Exception:
        return _remove_green(img)


def _already_mostly_transparent(img: Image.Image) -> bool:
    """已有大量透明通道的 PNG（如已抠 nc）不必再强抠，仍跑外圈绿键以清残留。"""
    if img.mode != "RGBA":
        return False
    a = img.getchannel("A")
    # 粗略：若存在透明像素则视为已抠过
    extrema = a.getextrema()
    return bool(extrema and extrema[0] < 250)


def _key_image(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGBA")
    name = path.name.lower()
    if name in OUTER_LIME or Path(name).stem + ".jpg" in OUTER_LIME:
        return _remove_outer_lime_green(img)
    # png 已透明也再抠一次外圈绿，清干净
    return _remove_green(img)


def bake_one(src: Path, sub: str) -> str:
    stem = src.stem
    out = CUTOUT / sub / f"{stem}.png"
    raw_dst = RAW / sub / src.name
    out.parent.mkdir(parents=True, exist_ok=True)
    raw_dst.parent.mkdir(parents=True, exist_ok=True)

    if out.is_file():
        try:
            if out.stat().st_mtime >= src.stat().st_mtime:
                # 源在 assets/ 下的 jpg 才挪走；png（nc）保留原位副本并写 cutout
                if src.suffix.lower() in {".jpg", ".jpeg"} and src.resolve() != raw_dst.resolve() and src.is_file():
                    if not raw_dst.exists():
                        shutil.move(str(src), str(raw_dst))
                    elif src.parent.resolve() != raw_dst.parent.resolve():
                        try:
                            src.unlink()
                        except Exception:
                            pass
                return "skip"
        except Exception:
            pass

    rgba = _key_image(src)
    rgba.save(out, format="PNG", optimize=True)
    if src.suffix.lower() in {".jpg", ".jpeg"} and src.resolve() != raw_dst.resolve():
        if raw_dst.exists():
            try:
                src.unlink()
            except Exception:
                pass
        else:
            shutil.move(str(src), str(raw_dst))
    return "bake"


def iter_sources(sub: str):
    for folder in (ASSETS / sub, RAW / sub):
        if not folder.is_dir():
            continue
        yield from sorted(folder.glob("*.jpg"))
        yield from sorted(folder.glob("*.jpeg"))
        # 已生成的 nc*.png 等也进 cutout
        yield from sorted(folder.glob("*.png"))


def main() -> int:
    baked = skipped = failed = 0
    seen: set[tuple[str, str]] = set()
    for sub in SUBDIRS:
        for src in iter_sources(sub):
            key = (sub, src.stem.lower())
            if key in seen:
                continue
            seen.add(key)
            try:
                status = bake_one(src, sub)
            except Exception as exc:
                print(f"FAIL {sub}/{src.name}: {exc}")
                failed += 1
                continue
            if status == "bake":
                baked += 1
                print(f"  bake {sub}/{src.stem}.png")
            else:
                skipped += 1
    print(f"\n完成：新建 {baked}，跳过 {skipped}，失败 {failed}")
    print(f"抠好图：{CUTOUT}")
    print(f"绿幕原图：{RAW}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
