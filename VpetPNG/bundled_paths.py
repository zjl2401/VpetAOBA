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
