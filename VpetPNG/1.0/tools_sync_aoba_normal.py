#!/usr/bin/env python3
"""把普通模式立绘同步进 AOBA，旧图归档为黑框，并补齐缺图。

源：
  Desktop/VpetDMMd/VpetAOBAnormal  → assets/sprites（aoba）+ props(box/flag)
  Desktop/VpetDMMd/VpetAllmateNormal → assets/minipet（petsand→petstand）

旧 assets/sprites、minipet 先完整备份到 sprites_black / minipet_black。
普通缺的非 nc 图用黑框备份补齐；nc 由后续 ensure_nc_outfit_sprites(force=True) 按普通图重生成。
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
SPRITES = ASSETS / "sprites"
MINIPET = ASSETS / "minipet"
PROPS = ASSETS / "props"
SPRITES_BLACK = ASSETS / "sprites_black"
MINIPET_BLACK = ASSETS / "minipet_black"

SRC_AOBA = Path.home() / "Desktop" / "VpetDMMd" / "VpetAOBAnormal"
SRC_MATE = Path.home() / "Desktop" / "VpetDMMd" / "VpetAllmateNormal"

PROP_NAMES = {"box.jpg", "flag.jpg", "box.png", "flag.png"}
# 边框/图标等 UI 与图组无关，同步时保留在 sprites
SHARED_KEEP = {
    "app_icon1.jpg",
    "app_icon1.png",
    "border1.jpg",
    "border5.jpg",
    "border.jpg",
    "border.png",
}


def _is_image(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}


def _is_nc(name: str) -> bool:
    return name.lower().startswith("nc")


def backup_dir(src: Path, dst: Path) -> int:
    if not src.is_dir():
        return 0
    dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for path in src.iterdir():
        if not _is_image(path):
            continue
        target = dst / path.name
        shutil.copy2(path, target)
        n += 1
    return n


def install_aoba_normal() -> tuple[int, int]:
    if not SRC_AOBA.is_dir():
        raise SystemExit(f"缺少普通苍叶图组：{SRC_AOBA}")
    SPRITES.mkdir(parents=True, exist_ok=True)
    PROPS.mkdir(parents=True, exist_ok=True)
    installed = 0
    props_n = 0
    for path in sorted(SRC_AOBA.iterdir()):
        if not _is_image(path):
            continue
        name = path.name
        if name.lower() in PROP_NAMES:
            shutil.copy2(path, PROPS / name)
            props_n += 1
            continue
        shutil.copy2(path, SPRITES / name)
        installed += 1
    return installed, props_n


def install_minipet_normal() -> int:
    if not SRC_MATE.is_dir():
        raise SystemExit(f"缺少普通 Allmate 图组：{SRC_MATE}")
    MINIPET.mkdir(parents=True, exist_ok=True)
    n = 0
    for path in sorted(SRC_MATE.iterdir()):
        if not _is_image(path):
            continue
        name = path.name
        # 源目录笔误 petsand → petstand
        if path.stem.lower() == "petsand":
            name = f"petstand{path.suffix.lower()}"
        shutil.copy2(path, MINIPET / name)
        n += 1
    return n


def fill_missing(normal_dir: Path, black_dir: Path, *, skip_nc: bool = True) -> list[str]:
    if not black_dir.is_dir():
        return []
    normal_dir.mkdir(parents=True, exist_ok=True)
    filled: list[str] = []
    black_by_stem: dict[str, Path] = {}
    for path in black_dir.iterdir():
        if not _is_image(path):
            continue
        if skip_nc and _is_nc(path.name):
            continue
        black_by_stem[path.stem.lower()] = path

    present_stems = {p.stem.lower() for p in normal_dir.iterdir() if _is_image(p)}
    for stem, src in sorted(black_by_stem.items()):
        if stem in present_stems:
            continue
        if skip_nc and stem.startswith("nc"):
            continue
        # 不把黑框 UI 共享文件重复补进（已在 sprites）
        if src.name.lower() in SHARED_KEEP:
            continue
        dst = normal_dir / src.name
        shutil.copy2(src, dst)
        filled.append(src.name)
    return filled


def clear_normal_nc() -> int:
    """普通目录里旧金目图清掉，避免残留黑框 nc；随后再 force 重生成。"""
    n = 0
    if not SPRITES.is_dir():
        return 0
    for path in list(SPRITES.iterdir()):
        if _is_image(path) and _is_nc(path.name):
            path.unlink(missing_ok=True)
            n += 1
    return n


def main() -> int:
    print(f"备份黑框 sprites → {SPRITES_BLACK}")
    n1 = backup_dir(SPRITES, SPRITES_BLACK)
    print(f"  备份 {n1} 张")
    print(f"备份黑框 minipet → {MINIPET_BLACK}")
    n2 = backup_dir(MINIPET, MINIPET_BLACK)
    print(f"  备份 {n2} 张")

    inst, props_n = install_aoba_normal()
    print(f"安装普通 aoba：{inst} → sprites，道具 {props_n} → props")
    mate_n = install_minipet_normal()
    print(f"安装普通 Allmate：{mate_n} → minipet")

    filled_s = fill_missing(SPRITES, SPRITES_BLACK, skip_nc=True)
    filled_m = fill_missing(MINIPET, MINIPET_BLACK, skip_nc=True)
    print(f"普通 sprites 补缺（来自黑框，非nc）：{len(filled_s)} → {filled_s}")
    print(f"普通 minipet 补缺：{len(filled_m)} → {filled_m}")

    cleared = clear_normal_nc()
    print(f"已清除普通目录旧 nc：{cleared}（请随后 force 重生成无黑框金目图）")
    print("完成同步。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
