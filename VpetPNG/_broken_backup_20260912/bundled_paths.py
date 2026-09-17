"""内置媒体目录：开发/发布时位于 <app>/bundled/，不打进 exe。"""
from __future__ import annotations

import sys
from pathlib import Path


def _desktop_legacy(name: str) -> Path:
    """可选：本机桌面同名目录（仅开发机方便热更新，公开包不依赖）。"""
    return Path.home() / "Desktop" / name


LEGACY_VOICE_ROOT = _desktop_legacy("Vpetvoice")
LEGACY_MUSIC_ROOT = _desktop_legacy("Vpetmusic")
LEGACY_GAME_ROOT = _desktop_legacy("Vpetgame")


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def bundled_root() -> Path:
    return app_dir() / "bundled"


def resolve_bundled(name: str, *, legacy: Path | None = None) -> Path:
    """优先 <app>/bundled/<name>，否则回退 legacy 桌面目录。"""
    bundled = bundled_root() / name
    if bundled.is_dir():
        return bundled
    if legacy and legacy.is_dir():
        return legacy
    return bundled


def _dir_has_audio(path: Path) -> bool:
    if not path.is_dir():
        return False
    for pat in ("*.mp3", "*.wav", "*.ogg", "*.flac", "*.m4a", "*.aac"):
        try:
            next(path.rglob(pat))
            return True
        except StopIteration:
            continue
        except Exception:
            continue
    return False


def resolve_music_src() -> Path:
    """曲库：打包后 bundled/Vpetmusic，开发机可回退桌面 Vpetmusic。"""
    bundled = bundled_root() / "Vpetmusic"
    legacy = LEGACY_MUSIC_ROOT
    if getattr(sys, "frozen", False):
        if _dir_has_audio(bundled):
            return bundled
        if _dir_has_audio(legacy):
            return legacy
        return bundled if bundled.is_dir() else legacy
    if _dir_has_audio(legacy):
        return legacy
    if _dir_has_audio(bundled):
        return bundled
    return legacy if legacy.is_dir() else bundled


def _dir_has_jpg(path: Path) -> bool:
    if not path.is_dir():
        return False
    try:
        next(path.glob("*.jpg"))
        return True
    except StopIteration:
        return False
    except Exception:
        return False


def resolve_png_black_src() -> Path:
    """黑框立绘：assets/sprites_black，其次 bundled/PNGblack。"""
    local = app_dir() / "assets" / "sprites_black"
    bundled = bundled_root() / "PNGblack"
    if getattr(sys, "frozen", False):
        for p in (local, bundled):
            if _dir_has_jpg(p):
                return p
        return local if local.is_dir() else bundled
    for p in (local, bundled):
        if _dir_has_jpg(p):
            return p
    return local if local.is_dir() else bundled
