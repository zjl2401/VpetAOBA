# -*- coding: utf-8 -*-
"""打字姿势：按键盘区位选择 type_down1/2 · type_up_left/right · type_up。

规则（与素材约定一致）：
- type_down1：按到外侧键（左右边缘列）
- type_down2：按到内侧键（中部主区）
- type_up_left：主要在键盘左侧打字
- type_up_right：主要在键盘右侧打字
- type_up：识别到写作/办公/代码等「要打字」环境，但尚未有按键
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes

# 可打印 / 常用打字键 → (side, ring)
# side: "L" | "R"    ring: "outer" | "inner"
_KEY_ZONE: dict[int, tuple[str, str]] = {}


def _z(vk: int, side: str, ring: str) -> None:
    _KEY_ZONE[int(vk)] = (side, ring)


# 数字行
for vk, side, ring in (
    (0xC0, "L", "outer"),  # `~
    (0x31, "L", "outer"),  # 1
    (0x32, "L", "outer"),
    (0x33, "L", "inner"),
    (0x34, "L", "inner"),
    (0x35, "L", "inner"),
    (0x36, "R", "inner"),
    (0x37, "R", "inner"),
    (0x38, "R", "inner"),
    (0x39, "R", "outer"),
    (0x30, "R", "outer"),  # 0
    (0xBD, "R", "outer"),  # -
    (0xBB, "R", "outer"),  # =
):
    _z(vk, side, ring)

# Q 行
for vk, side, ring in (
    (0x51, "L", "outer"),  # Q
    (0x57, "L", "outer"),  # W
    (0x45, "L", "inner"),  # E
    (0x52, "L", "inner"),  # R
    (0x54, "L", "inner"),  # T
    (0x59, "R", "inner"),  # Y
    (0x55, "R", "inner"),  # U
    (0x49, "R", "inner"),  # I
    (0x4F, "R", "outer"),  # O
    (0x50, "R", "outer"),  # P
    (0xDB, "R", "outer"),  # [
    (0xDD, "R", "outer"),  # ]
    (0xDC, "R", "outer"),  # \
):
    _z(vk, side, ring)

# A 行
for vk, side, ring in (
    (0x41, "L", "outer"),  # A
    (0x53, "L", "outer"),  # S
    (0x44, "L", "inner"),  # D
    (0x46, "L", "inner"),  # F
    (0x47, "L", "inner"),  # G
    (0x48, "R", "inner"),  # H
    (0x4A, "R", "inner"),  # J
    (0x4B, "R", "inner"),  # K
    (0x4C, "R", "outer"),  # L
    (0xBA, "R", "outer"),  # ;
    (0xDE, "R", "outer"),  # '
):
    _z(vk, side, ring)

# Z 行
for vk, side, ring in (
    (0x5A, "L", "outer"),  # Z
    (0x58, "L", "outer"),  # X
    (0x43, "L", "inner"),  # C
    (0x56, "L", "inner"),  # V
    (0x42, "L", "inner"),  # B
    (0x4E, "R", "inner"),  # N
    (0x4D, "R", "inner"),  # M
    (0xBC, "R", "outer"),  # ,
    (0xBE, "R", "outer"),  # .
    (0xBF, "R", "outer"),  # /
):
    _z(vk, side, ring)

# 功能/修饰（仍视为外侧）
for vk, side in (
    (0x09, "L"),  # Tab
    (0x14, "L"),  # Caps
    (0xA0, "L"),  # LShift
    (0xA2, "L"),  # LCtrl
    (0xA4, "L"),  # LAlt
    (0x5B, "L"),  # LWin
    (0x20, "L"),  # Space → 偏左计（双手共用时靠其它键定侧）
    (0x08, "R"),  # Backspace
    (0x0D, "R"),  # Enter
    (0xA1, "R"),  # RShift
    (0xA3, "R"),  # RCtrl
    (0xA5, "R"),  # RAlt
):
    _z(vk, side, "outer")

TYPING_POSE_FILES = {
    "type_down1": "type_down1.jpg",
    "type_down2": "type_down2.jpg",
    "type_up_left": "type_up_left.jpg",
    "type_up_right": "type_up_right.jpg",
    "type_up": "type_up.jpg",
}

TYPING_READY_SCENES = frozenset({"code", "study", "office", "chat"})


def sample_pressed_zones() -> tuple[int, int, int, int, int]:
    """返回 (left, right, outer, inner, total_typing_keys)。"""
    user32 = ctypes.windll.user32
    left = right = outer = inner = total = 0
    for vk, (side, ring) in _KEY_ZONE.items():
        try:
            down = bool(user32.GetAsyncKeyState(vk) & 0x8000)
        except Exception:
            down = False
        if not down:
            continue
        total += 1
        if side == "L":
            left += 1
        else:
            right += 1
        if ring == "outer":
            outer += 1
        else:
            inner += 1
    return left, right, outer, inner, total


def foreground_is_our_process() -> bool:
    """前台是本进程窗口时，不抢打字姿势（避免在自家输入框打字还摆姿势）。"""
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return False
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return int(pid.value) == int(ctypes.windll.kernel32.GetCurrentProcessId())
    except Exception:
        return False


def classify_typing_pose(
    *,
    ready_scene: bool,
    left: int,
    right: int,
    outer: int,
    inner: int,
    total: int,
) -> str | None:
    """根据当前按键区位与是否处于「要打字」场景，返回姿势 id 或 None。

    - 打在左侧（仅左半区有键）→ type_up_left
    - 打在右侧（仅右半区有键）→ type_up_right
    - 左右同时有键且偏外侧 → type_down1
    - 左右同时有键且偏内侧 → type_down2
    - 无按键但已识别写作场景 → type_up
    """
    if total <= 0:
        if ready_scene:
            return "type_up"
        return None

    if left > 0 and right == 0:
        return "type_up_left"
    if right > 0 and left == 0:
        return "type_up_right"

    # 左右同时：外侧 / 内侧
    if outer >= inner:
        return "type_down1"
    return "type_down2"
