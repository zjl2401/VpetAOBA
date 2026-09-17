# -*- coding: utf-8 -*-
"""从 Desktop/VpetDMMd/Vpet_music 去重后导入曲库「尚未分类」。

规则：
- 相同歌曲名（去掉 (2)/(3)/copy 等后缀后）只留一首：优先无编号、体积更大者；其余删除源里重复文件
- 导入到 bundled/Vpetmusic/尚未分类（同名则覆盖替换）
- 分类工作未完成：新曲一律尚未分类
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

SRC = Path.home() / "Desktop" / "VpetDMMd" / "Vpet_music"
# 优先写入发布用 bundled；同时写桌面 Vpetmusic 方便热更新
DST_CANDIDATES = [
    Path(__file__).resolve().parents[1] / "bundled" / "Vpetmusic" / "尚未分类",
    Path.home() / "Desktop" / "Vpetmusic" / "尚未分类",
]
AUDIO_EXT = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".wma"}


def _song_key(stem: str) -> str:
    """规范化歌名键：去编号后缀、压缩空白。"""
    s = (stem or "").strip()
    # Artist - Title → 用整段，但去掉末尾 (2)
    s = re.sub(r"\s*\(\d+\)\s*$", "", s)
    s = re.sub(r"\s*[-_]?\s*copy\s*\d*$", "", s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def _display_title(stem: str) -> str:
    s = re.sub(r"\s*\(\d+\)\s*$", "", (stem or "").strip())
    if " - " in s:
        s = s.split(" - ", 1)[-1].strip()
    return s or stem


def _pick_best(files: list[Path]) -> Path:
    def score(p: Path) -> tuple:
        stem = p.stem
        has_num = 1 if re.search(r"\(\d+\)\s*$", stem) else 0
        try:
            size = p.stat().st_size
        except OSError:
            size = 0
        # 无编号优先，然后更大
        return (has_num, -size, stem.lower())

    return sorted(files, key=score)[0]


def main() -> None:
    if not SRC.is_dir():
        raise SystemExit(f"源目录不存在: {SRC}")

    groups: dict[str, list[Path]] = {}
    for p in SRC.iterdir():
        if not p.is_file() or p.suffix.lower() not in AUDIO_EXT:
            continue
        key = _song_key(p.stem)
        groups.setdefault(key, []).append(p)

    kept: list[Path] = []
    deleted = 0
    for key, files in groups.items():
        best = _pick_best(files)
        kept.append(best)
        for other in files:
            if other == best:
                continue
            try:
                other.unlink()
                deleted += 1
                print(f"DEL dup: {other.name}".encode("utf-8", "replace").decode("utf-8"))
            except OSError as exc:
                print(f"WARN del fail: {exc}")

    dests = []
    for d in DST_CANDIDATES:
        d.mkdir(parents=True, exist_ok=True)
        dests.append(d)

    imported = 0
    replaced = 0
    for src in kept:
        title = _display_title(src.stem)
        safe = re.sub(r'[<>:"/\\|?*]', "_", src.name)
        for dest_dir in dests:
            dest = dest_dir / safe
            for old in list(dest_dir.glob("*")):
                if not old.is_file() or old.suffix.lower() not in AUDIO_EXT:
                    continue
                if _song_key(old.stem) == _song_key(src.stem) and old.name != safe:
                    try:
                        old.unlink()
                        replaced += 1
                        print("REPL old ->", safe.encode("ascii", "replace").decode())
                    except OSError:
                        pass
            if dest.exists():
                replaced += 1
            shutil.copy2(src, dest)
            imported += 1
        msg = f"OK: {src.name} ({title})"
        try:
            print(msg)
        except UnicodeEncodeError:
            print(msg.encode("ascii", "replace").decode("ascii"))

    # 源目录说明
    readme = SRC / "README_尚未分类.txt"
    readme.write_text(
        "新加入曲目暂不分类，已统一导入曲库「尚未分类」。\n"
        "人物文件夹分类是作者工作未完成项，播放时「尚未分类」先用随机颜色。\n"
        "重复曲（同名/(2)）已删除，只保留一首。\n"
        "音游开局暂缓；可为单曲制作/指定自制谱面。\n",
        encoding="utf-8",
    )

    print("---")
    print(f"kept={len(kept)} deleted_dups={deleted} copy_ops={imported} replaced={replaced}")
    for d in dests:
        print(f"dest={d}")


if __name__ == "__main__":
    main()
