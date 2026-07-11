#!/usr/bin/env python3
"""将 1.2 根目录散落的图片/音频/配置整理到子文件夹（可重复运行，已就位则跳过）。"""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
SPRITES = ASSETS / "sprites"
PROPS = ASSETS / "props"
MINIPET = ASSETS / "minipet"
AUDIO_ASSETS = ASSETS / "audio"
DATA = ROOT / "data"
DATA_AUDIO = DATA / "audio"

PROP_FILES = {"box.jpg", "flag.jpg"}
BUNDLED_AUDIO = {"type_tick.wav"}
DATA_AUDIO_FILES = {
    "call_cache.wav",
    "call2_cache.wav",
    "type_cache.wav",
    "music_aicatch_cache.wav",
}
DATA_JSON = {
    "app_config.json",
    "pet_profile.json",
    "food_inventory.json",
    "diary.json",
    "schedules.json",
    "music_config.json",
    "pet_id_registry.json",
    "vocab.json",
    "ai_config.example.json",
    "ai_config.json",
}


def _move(src: Path, dst: Path) -> bool:
    if not src.is_file() or src.resolve() == dst.resolve():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return False
    shutil.move(str(src), str(dst))
    print(f"  {src.name} -> {dst.relative_to(ROOT)}")
    return True


def main() -> None:
    for d in (SPRITES, PROPS, MINIPET, AUDIO_ASSETS, DATA, DATA_AUDIO):
        d.mkdir(parents=True, exist_ok=True)

    moved = 0
    for path in sorted(ROOT.glob("*.jpg")):
        name = path.name
        if name in PROP_FILES:
            moved += _move(path, PROPS / name)
        elif name.startswith("pet"):
            moved += _move(path, MINIPET / name)
        else:
            moved += _move(path, SPRITES / name)

    for path in sorted(ROOT.glob("*.wav")):
        name = path.name
        if name in BUNDLED_AUDIO:
            moved += _move(path, AUDIO_ASSETS / name)
        else:
            moved += _move(path, DATA_AUDIO / name)

    for name in DATA_JSON:
        moved += _move(ROOT / name, DATA / name)

    print(f"\n完成，移动 {moved} 个文件。")
    print("目录结构：")
    print("  assets/sprites/  桌宠立绘 JPG")
    print("  assets/props/    箱子、旗子")
    print("  assets/minipet/  金目立绘")
    print("  assets/audio/    内置音效")
    print("  data/            存档与配置 JSON")
    print("  data/audio/      运行时音频缓存")
    print("  gallery/         画廊 PNG")
    print("  word_banks/      词库")


if __name__ == "__main__":
    main()
