"""控制外部音乐软件：优先系统媒体会话（GSMTC），失败则发全局媒体键。

不强制依赖 winrt；未安装时仅用媒体键（网易云 / QQ 音乐 / Spotify / 浏览器网页播放器等通常可用）。
"""
from __future__ import annotations

import sys

VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002

_COMMAND_VK = {
    "play_pause": VK_MEDIA_PLAY_PAUSE,
    "next": VK_MEDIA_NEXT_TRACK,
    "prev": VK_MEDIA_PREV_TRACK,
    "stop": VK_MEDIA_STOP,
}


def _send_media_key(vk: int) -> bool:
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        user32 = ctypes.windll.user32
        user32.keybd_event(vk, 0, KEYEVENTF_EXTENDEDKEY, 0)
        user32.keybd_event(vk, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
        return True
    except Exception:
        return False


def _gsmtc_command(command: str) -> bool:
    """可选：通过 WinRT GSMTC 控制「当前系统媒体会话」。"""
    if sys.platform != "win32":
        return False
    try:
        import asyncio

        from winrt.windows.media.control import (  # type: ignore
            GlobalSystemMediaTransportControlsSessionManager as SessionManager,
        )
    except Exception:
        return False

    async def _run() -> bool:
        manager = await SessionManager.request_async()
        session = manager.get_current_session()
        if session is None:
            return False
        cmd = str(command or "").strip().lower()
        if cmd == "play_pause":
            return bool(await session.try_toggle_play_pause_async())
        if cmd == "next":
            return bool(await session.try_skip_next_async())
        if cmd == "prev":
            return bool(await session.try_skip_previous_async())
        if cmd == "stop":
            ok = bool(await session.try_stop_async())
            if ok:
                return True
            return bool(await session.try_pause_async())
        return False

    try:
        return bool(asyncio.run(_run()))
    except Exception:
        return False


def send_command(command: str) -> bool:
    """发送媒体命令。成功返回 True（媒体键发出即视为成功）。"""
    cmd = str(command or "").strip().lower()
    if cmd not in _COMMAND_VK:
        return False
    if _gsmtc_command(cmd):
        return True
    return _send_media_key(_COMMAND_VK[cmd])
