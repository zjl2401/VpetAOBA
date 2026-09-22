# -*- coding: utf-8 -*-
"""绘画 / 记事：按鼠标或电容笔（系统指针）水平区位选择 draw 姿。

区位（屏幕宽度归一化）：
- far_left / left / mid / right / far_right
对应 draw1–3 及自动生成的左右镜像图，表示更多笔触位置。
"""
from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

# 基础三帧 + 镜像扩展（ensure 时生成 draw1_m / draw3_m）
DRAW_ZONE_FILES: dict[str, str] = {
    "far_left": "draw3_m.jpg",   # 右侧姿镜像 → 更靠左
    "left": "draw1.jpg",
    "mid": "draw2.jpg",
    "right": "draw3.jpg",
    "far_right": "draw1_m.jpg",  # 左侧姿镜像 → 更靠右
}
DRAW_ZONE_ORDER: tuple[str, ...] = ("far_left", "left", "mid", "right", "far_right")
# 无指针活动时循环用的基础帧
DRAW_CYCLE_FILES: tuple[str, ...] = ("draw1.jpg", "draw2.jpg", "draw3.jpg")

# 镜像源 → 目标
DRAW_MIRROR_PAIRS: tuple[tuple[str, str], ...] = (
    ("draw1.jpg", "draw1_m.jpg"),
    ("draw3.jpg", "draw3_m.jpg"),
    ("draw2.jpg", "draw2_m.jpg"),  # 中姿也备一份，远区位备用
)

VK_LBUTTON = 0x01
VK_RBUTTON = 0x02
VK_MBUTTON = 0x04
VK_XBUTTON1 = 0x05
VK_XBUTTON2 = 0x06


def cursor_screen_norm() -> tuple[float, float] | None:
    """返回指针屏幕坐标归一化 (nx, ny)，失败为 None。"""
    if sys.platform != "win32":
        return None
    try:
        user32 = ctypes.windll.user32
        pt = wintypes.POINT()
        if not user32.GetCursorPos(ctypes.byref(pt)):
            return None
        sw = int(user32.GetSystemMetrics(0) or 0)  # SM_CXSCREEN
        sh = int(user32.GetSystemMetrics(1) or 0)
        if sw <= 1 or sh <= 1:
            return None
        nx = max(0.0, min(1.0, float(pt.x) / float(sw)))
        ny = max(0.0, min(1.0, float(pt.y) / float(sh)))
        return nx, ny
    except Exception:
        return None


def pointer_buttons_down() -> bool:
    """左/右/中键或侧键按下（含多数电容笔落笔映射）。"""
    if sys.platform != "win32":
        return False
    try:
        user32 = ctypes.windll.user32
        for vk in (VK_LBUTTON, VK_RBUTTON, VK_MBUTTON, VK_XBUTTON1, VK_XBUTTON2):
            if user32.GetAsyncKeyState(vk) & 0x8000:
                return True
    except Exception:
        return False
    return False


def classify_draw_zone(nx: float) -> str:
    """水平五段区位。"""
    if nx < 0.18:
        return "far_left"
    if nx < 0.38:
        return "left"
    if nx < 0.62:
        return "mid"
    if nx < 0.82:
        return "right"
    return "far_right"


def draw_file_for_zone(zone: str) -> str:
    return DRAW_ZONE_FILES.get(zone, "draw2.jpg")
