"""bundled 媒体同步：仅保留音频，视频容器在同步时转为 wav 并剔除。"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

# 运行时 / bundled 内认可的纯音频扩展名（不含视频容器）
AUDIO_MEDIA_EXTENSIONS = frozenset({".wav", ".mp3", ".m4a", ".ogg", ".flac"})
# 同步时遇到则抽音转 wav，不保留原文件
VIDEO_CONTAINER_EXTENSIONS = frozenset({".mp4", ".mkv", ".webm", ".avi", ".mov", ".wmv"})


def is_audio_media(path: Path) -> bool:
    return path.suffix.lower() in AUDIO_MEDIA_EXTENSIONS


def is_video_container(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_CONTAINER_EXTENSIONS


def is_supported_media(path: Path) -> bool:
    ext = path.suffix.lower()
    return ext in AUDIO_MEDIA_EXTENSIONS or ext in VIDEO_CONTAINER_EXTENSIONS


def _subprocess_no_window_kwargs() -> dict:
    if sys.platform != "win32":
        return {}
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    return {"creationflags": flags}


def extract_audio_wav(src: Path, dst: Path) -> bool:
    """从视频/音频容器抽取 wav；已存在且较新则跳过。"""
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return True
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        from imageio_ffmpeg import get_ffmpeg_exe

        ffmpeg = get_ffmpeg_exe()
        cmd = [
            ffmpeg,
            "-y",
            "-i",
            str(src),
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "44100",
            "-ac",
            "1",
            str(dst),
        ]
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            **_subprocess_no_window_kwargs(),
        )
        return dst.is_file()
    except Exception:
        return False


def _unlink_force(path: Path) -> bool:
    try:
        import os

        if path.is_file():
            try:
                os.chmod(path, 0o666)
            except OSError:
                pass
            path.unlink()
            return True
    except OSError:
        pass
    return False


def prune_video_files(root: Path) -> int:
    """删除目录内残留的视频容器文件。"""
    removed = 0
    if not root.is_dir():
        return 0
    for path in root.rglob("*"):
        if path.is_file() and is_video_container(path) and _unlink_force(path):
            removed += 1
    return removed


def _replace_dir(src: Path, dst: Path) -> None:
    """用 src 替换 dst（尽量原子）。"""
    if dst.exists():
        shutil.rmtree(dst, ignore_errors=True)
    if dst.exists():
        backup = dst.with_name(f"{dst.name}_old")
        shutil.rmtree(backup, ignore_errors=True)
        try:
            dst.rename(backup)
        except OSError:
            shutil.rmtree(dst, ignore_errors=True)
    src.rename(dst)
    backup = dst.with_name(f"{dst.name}_old")
    if backup.exists():
        shutil.rmtree(backup, ignore_errors=True)


def sync_bundled_audio_only(src: Path, dst: Path, *, force: bool = False) -> tuple[int, int, int]:
    """
    将 src 同步到 dst，仅保留音频：
    - 纯音频：原样复制
    - 视频容器：转为同名 .wav，不保留视频
    返回 (音频文件数, 转换数, 删除视频数)
    """
    if not src.is_dir():
        return 0, 0, 0

    staging = dst.with_name(f"{dst.name}__audio_sync")
    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True, exist_ok=True)

    copied = 0
    converted = 0
    for item in sorted(src.rglob("*")):
        if not item.is_file():
            continue
        rel = item.relative_to(src)
        ext = item.suffix.lower()
        out_dir = staging / rel.parent

        if ext in AUDIO_MEDIA_EXTENSIONS:
            out_dir.mkdir(parents=True, exist_ok=True)
            target = out_dir / item.name
            shutil.copy2(item, target)
            copied += 1
            continue

        if ext in VIDEO_CONTAINER_EXTENSIONS:
            wav_out = out_dir / f"{item.stem}.wav"
            if extract_audio_wav(item, wav_out):
                converted += 1
            continue

    removed = prune_video_files(staging)
    if force or not dst.exists() or dst.resolve() != staging.resolve():
        _replace_dir(staging, dst)
    else:
        shutil.rmtree(staging, ignore_errors=True)
    removed += prune_video_files(dst)
    return copied, converted, removed


def count_media_files(root: Path) -> tuple[int, int]:
    """返回 (音频数, 视频容器数)。"""
    audio_n = 0
    video_n = 0
    if not root.is_dir():
        return 0, 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if is_audio_media(path):
            audio_n += 1
        elif is_video_container(path):
            video_n += 1
    return audio_n, video_n


if __name__ == "__main__":
    from bundled_paths import LEGACY_MUSIC_ROOT, LEGACY_VOICE_ROOT

    root = Path(__file__).resolve().parent / "bundled"
    for name, src in (("Vpetvoice", LEGACY_VOICE_ROOT), ("Vpetmusic", LEGACY_MUSIC_ROOT)):
        dst = root / name
        if not src.is_dir():
            print(f"跳过 {name}：源目录不存在 {src}")
            continue
        copied, converted, removed = sync_bundled_audio_only(src, dst, force=True)
        audio_n, video_n = count_media_files(dst)
        print(f"{name}: 复制 {copied}，转换 {converted}，剔除 {removed} → 音频 {audio_n}，视频 {video_n}")
