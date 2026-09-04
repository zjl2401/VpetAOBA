#!/usr/bin/env python3
"""把黑框立绘同步进 AOBA（对应普通同步 tools_sync_aoba_normal.py）。

源：
  Desktop/VpetDMMd/VpetAOBAblack  → assets/sprites_black（含 box/flag）
  Desktop/VpetDMMd/VpetAllmateBlack → assets/minipet_black

并写入 raw_green/*_black、预抠 cutout/*_black；若存在 dist/_internal/assets 则一并替换对应文件。
"""
from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
SPRITES_BLACK = ASSETS / "sprites_black"
MINIPET_BLACK = ASSETS / "minipet_black"
RAW_SPRITES_BLACK = ASSETS / "raw_green" / "sprites_black"
RAW_MINIPET_BLACK = ASSETS / "raw_green" / "minipet_black"
CUT_SPRITES_BLACK = ASSETS / "cutout" / "sprites_black"
CUT_MINIPET_BLACK = ASSETS / "cutout" / "minipet_black"

SRC_AOBA = Path.home() / "Desktop" / "VpetDMMd" / "VpetAOBAblack"
SRC_MATE = Path.home() / "Desktop" / "VpetDMMd" / "VpetAllmateBlack"

DIST_ASSETS = ROOT / "dist" / "Vpet" / "_internal" / "assets"
RELEASE_ASSETS = ROOT / "release" / "Vpet" / "_internal" / "assets"


def _is_image(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}


def _is_chroma_green(r: int, g: int, b: int, a: int) -> bool:
    if a <= 8:
        return False
    return ((g > 200) and (r < 90) and (b < 90)) or ((g > 100) and (g >= r + 15) and (g >= b + 25))


def _remove_green_keep_rgb(img: Image.Image) -> Image.Image:
    """只抠与边缘连通的绿幕（与 pet._remove_green 一致），保留图内绿色细节。"""
    from collections import deque

    rgba = img.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()
    outer: set[tuple[int, int]] = set()
    q: deque[tuple[int, int]] = deque()
    for x in range(w):
        q.append((x, 0))
        q.append((x, h - 1))
    for y in range(h):
        q.append((0, y))
        q.append((w - 1, y))
    while q:
        x, y = q.popleft()
        if (x, y) in outer or x < 0 or x >= w or y < 0 or y >= h:
            continue
        r, g, b, a = px[x, y]
        if not _is_chroma_green(r, g, b, a):
            continue
        outer.add((x, y))
        q.append((x - 1, y))
        q.append((x + 1, y))
        q.append((x, y - 1))
        q.append((x, y + 1))
    for x, y in outer:
        r, g, b, _a = px[x, y]
        px[x, y] = (r, g, b, 0)
    return rgba


def _copy_tree_images(src: Path, *dests: Path) -> list[str]:
    if not src.is_dir():
        raise SystemExit(f"缺少源目录：{src}")
    names: list[str] = []
    for path in sorted(src.iterdir()):
        if not _is_image(path):
            continue
        name = path.name
        if path.stem.lower() == "petsand":
            name = f"petstand{path.suffix.lower()}"
        for dst_dir in dests:
            if dst_dir is None:
                continue
            dst_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dst_dir / name)
        names.append(name)
    return names


def _extra_asset_roots() -> list[Path]:
    roots: list[Path] = []
    for base in (DIST_ASSETS, RELEASE_ASSETS):
        if base.is_dir():
            roots.append(base)
    return roots


def _mirror_into(root: Path, rel: str, src_dir: Path, names: list[str]) -> int:
    dst = root / rel
    dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for name in names:
        src = src_dir / name
        if not src.is_file():
            continue
        shutil.copy2(src, dst / name)
        n += 1
    return n


def _bake_cutouts(src_dir: Path, cut_dir: Path, names: list[str]) -> int:
    cut_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for name in names:
        src = src_dir / name
        if not src.is_file():
            continue
        out = cut_dir / f"{Path(name).stem}.png"
        keyed = _remove_green_keep_rgb(Image.open(src))
        keyed.save(out, "PNG")
        n += 1
    return n


def main() -> int:
    if not SRC_AOBA.is_dir():
        raise SystemExit(f"缺少黑框苍叶图组：{SRC_AOBA}")
    if not SRC_MATE.is_dir():
        raise SystemExit(f"缺少黑框 Allmate 图组：{SRC_MATE}")

    aoba_names = _copy_tree_images(SRC_AOBA, SPRITES_BLACK, RAW_SPRITES_BLACK)
    print(f"安装黑框 aoba：{len(aoba_names)} → sprites_black + raw_green/sprites_black")
    mate_names = _copy_tree_images(SRC_MATE, MINIPET_BLACK, RAW_MINIPET_BLACK)
    print(f"安装黑框 Allmate：{len(mate_names)} → minipet_black + raw_green/minipet_black")

    n_cut_s = _bake_cutouts(SPRITES_BLACK, CUT_SPRITES_BLACK, aoba_names)
    n_cut_m = _bake_cutouts(MINIPET_BLACK, CUT_MINIPET_BLACK, mate_names)
    print(f"预抠 cutout/sprites_black：{n_cut_s}")
    print(f"预抠 cutout/minipet_black：{n_cut_m}")

    for root in _extra_asset_roots():
        label = root.relative_to(ROOT) if root.is_relative_to(ROOT) else root
        ns = _mirror_into(root, "sprites_black", SPRITES_BLACK, aoba_names)
        nm = _mirror_into(root, "minipet_black", MINIPET_BLACK, mate_names)
        nrs = _mirror_into(root, "raw_green/sprites_black", SPRITES_BLACK, aoba_names)
        nrm = _mirror_into(root, "raw_green/minipet_black", MINIPET_BLACK, mate_names)
        ncs = _mirror_into(
            root,
            "cutout/sprites_black",
            CUT_SPRITES_BLACK,
            [f"{Path(n).stem}.png" for n in aoba_names],
        )
        ncm = _mirror_into(
            root,
            "cutout/minipet_black",
            CUT_MINIPET_BLACK,
            [f"{Path(n).stem}.png" for n in mate_names],
        )
        print(
            f"同步 {label}: sprites_black={ns}, minipet_black={nm}, "
            f"raw={nrs}+{nrm}, cutout={ncs}+{ncm}"
        )

    print("完成黑框图组替换。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
