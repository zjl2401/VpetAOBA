"""Vpetvoice 缓存：去掉开头静音并统一响度（保留结尾）。"""
from __future__ import annotations

import subprocess
import sys
import wave
from pathlib import Path

VOICE_WAV_CACHE_REV = 4
VOICE_SAMPLE_RATE = 44100
VOICE_SILENCE_THRESHOLD_DB = -38.0
VOICE_SILENCE_MIN_SEC = 0.03
VOICE_SILENCE_PAD_SEC = 0.012
VOICE_LOUDNORM_I = -16.0
VOICE_LOUDNORM_TP = -1.5
VOICE_LOUDNORM_LRA = 11.0
VOICE_MIN_DURATION_SEC = 0.08

# 进程内已确认可用的缓存路径：命中后不再跑 ffmpeg
_ENSURED_VOICE_WAV: set[str] = set()


def _subprocess_no_window_kwargs() -> dict:
    if sys.platform != "win32":
        return {}
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    return {"creationflags": flags}


def _ffmpeg_exe() -> str:
    from imageio_ffmpeg import get_ffmpeg_exe

    return get_ffmpeg_exe()


def voice_cache_path(cache_dir: Path, stem: str) -> Path:
    safe = stem.strip() or "voice"
    return cache_dir / f"{safe}_p{VOICE_WAV_CACHE_REV}.wav"


def _voice_audio_filters() -> str:
    th = VOICE_SILENCE_THRESHOLD_DB
    d = VOICE_SILENCE_MIN_SEC
    pad = VOICE_SILENCE_PAD_SEC
    # 只去开头静音，保留结尾（stop_periods=0）
    silence = (
        f"silenceremove=start_periods=1:start_duration={d}:start_threshold={th}dB:"
        f"stop_periods=0"
    )
    norm = f"loudnorm=I={VOICE_LOUDNORM_I}:TP={VOICE_LOUDNORM_TP}:LRA={VOICE_LOUDNORM_LRA}"
    return f"{silence},apad=pad_dur={pad},{norm}"


def _wav_duration_sec(path: Path) -> float:
    try:
        with wave.open(str(path), "rb") as wf:
            rate = wf.getframerate() or VOICE_SAMPLE_RATE
            return wf.getnframes() / rate
    except Exception:
        return 0.0


def _run_ffmpeg(cmd: list[str]) -> bool:
    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            **_subprocess_no_window_kwargs(),
        )
        return True
    except Exception:
        return False


def _plain_voice_wav(src: Path, dst: Path) -> bool:
    cmd = [
        _ffmpeg_exe(),
        "-y",
        "-i",
        str(src),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        str(VOICE_SAMPLE_RATE),
        "-ac",
        "1",
        str(dst),
    ]
    return _run_ffmpeg(cmd)


def _processed_voice_wav(src: Path, dst: Path) -> bool:
    cmd = [
        _ffmpeg_exe(),
        "-y",
        "-i",
        str(src),
        "-vn",
        "-af",
        _voice_audio_filters(),
        "-acodec",
        "pcm_s16le",
        "-ar",
        str(VOICE_SAMPLE_RATE),
        "-ac",
        "1",
        str(dst),
    ]
    return _run_ffmpeg(cmd)


def ensure_voice_wav(src: Path, dst: Path) -> Path | None:
    """将 Vpetvoice 源文件转为缓存 wav：只裁开头静音并统一响度。

    已落盘且有效的缓存直接复用，不再二次 ffmpeg（与改规则前行为一致）。
    """
    if not src.is_file():
        return None
    dst_key = str(dst.resolve()) if dst.exists() else str(dst)
    if dst_key in _ENSURED_VOICE_WAV and dst.is_file():
        return dst
    if dst.is_file() and dst.stat().st_mtime >= src.stat().st_mtime:
        if _wav_duration_sec(dst) >= VOICE_MIN_DURATION_SEC:
            _ENSURED_VOICE_WAV.add(str(dst.resolve()))
            return dst

    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(".tmp.wav")
    if tmp.exists():
        try:
            tmp.unlink()
        except OSError:
            pass

    ok = _processed_voice_wav(src, tmp)
    proc_dur = _wav_duration_sec(tmp) if ok and tmp.is_file() else 0.0
    # 优先保留已去开头静音+响度归一的结果；仅当处理失败/过短时回退 plain
    if proc_dur >= VOICE_MIN_DURATION_SEC:
        plain_tmp = dst.with_suffix(".plain.tmp.wav")
        if plain_tmp.exists():
            try:
                plain_tmp.unlink()
            except OSError:
                pass
    else:
        plain_tmp = dst.with_suffix(".plain.tmp.wav")
        if plain_tmp.exists():
            try:
                plain_tmp.unlink()
            except OSError:
                pass
        ok_plain = _plain_voice_wav(src, plain_tmp)
        plain_dur = _wav_duration_sec(plain_tmp) if ok_plain and plain_tmp.is_file() else 0.0
        if plain_dur >= VOICE_MIN_DURATION_SEC:
            if tmp.is_file():
                try:
                    tmp.unlink()
                except OSError:
                    pass
            tmp = plain_tmp
            ok = True
        elif plain_tmp.is_file():
            try:
                plain_tmp.unlink()
            except OSError:
                pass

    if not tmp.is_file() or _wav_duration_sec(tmp) < VOICE_MIN_DURATION_SEC:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        ok = _plain_voice_wav(src, tmp)

    if not ok or not tmp.is_file() or _wav_duration_sec(tmp) < VOICE_MIN_DURATION_SEC:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        return None

    try:
        tmp.replace(dst)
    except OSError:
        try:
            if dst.exists():
                dst.unlink()
            tmp.replace(dst)
        except OSError:
            return None
    if dst.is_file():
        _ENSURED_VOICE_WAV.add(str(dst.resolve()))
        return dst
    return None
