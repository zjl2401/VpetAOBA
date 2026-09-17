"""桌宠装扮：像素装饰叠层（素材库 / 自创画 / 礼物画 / 公开预设）。"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageDraw

OUTFIT_MAX = 8
# 相对宠框中心：nx/ny ∈ [-0.55, 0.55]；scale 为占宠边长比例；rot 顺时针角度
OUTFIT_SCALE_MIN = 0.12
OUTFIT_SCALE_MAX = 0.55
OUTFIT_DEFAULT_NX = 0.0
OUTFIT_DEFAULT_NY = -0.38
OUTFIT_DEFAULT_SCALE = 0.28
OUTFIT_DEFAULT_ROT = 0.0
OUTFIT_ROT_MIN = -180.0
OUTFIT_ROT_MAX = 180.0

KIND_MATERIAL = "material"
KIND_USER_PAINT = "user_paint"
KIND_GIFT_ART = "gift_art"
KIND_BUILTIN = "builtin"

# 素材栏分组展示顺序
OUTFIT_GROUP_ORDER: tuple[str, ...] = (
    "我的",
    "帽子",
    "眼镜",
    "颈饰",
    "包袋",
    "手持",
    "装饰",
    "表情",
    "公开",
)

# 公开预设：12×12 色板下标（0=透明），简易像素图案
_BUILTIN_PALETTE: tuple[str | None, ...] = (
    None,
    "#ff6688",  # 1 爱心粉
    "#ffcc66",  # 2 星/问号黄
    "#66ccff",  # 3 水滴青
    "#88eeaa",  # 4 叶绿
    "#ffffff",  # 5 白
    "#cc88ff",  # 6 蝴蝶结紫
    "#442233",  # 7 深色描边
    "#ff4444",  # 8 怒气红
    "#8899ee",  # 9 睡觉 Z / 蓝
    "#88ddff",  # 10 流汗浅蓝
    "#8a6848",  # 11 棕（帽/包）
    "#f0e0c8",  # 12 米白
    "#d4a84a",  # 13 金
    "#1a1a22",  # 14 墨黑
    "#ff9944",  # 15 橙
    "#3a5080",  # 16 藏青
    "#f0a0c0",  # 17 围巾粉
    "#8899aa",  # 18 灰
)


def _empty_cells() -> list[int]:
    return [0] * 144


def _paint_cells(draw_fn) -> list[int]:
    cells = _empty_cells()

    def put(x: int, y: int, c: int) -> None:
        if 0 <= x < 12 and 0 <= y < 12:
            cells[y * 12 + x] = c

    draw_fn(put)
    return cells


def _builtin_star(put) -> None:
    for x, y in ((5, 1), (5, 2), (4, 3), (5, 3), (6, 3), (3, 4), (4, 4), (5, 4), (6, 4), (7, 4),
                 (5, 5), (4, 6), (6, 6), (3, 7), (7, 7)):
        put(x, y, 2)


def _builtin_heart(put) -> None:
    for x, y in ((3, 2), (4, 2), (7, 2), (8, 2), (2, 3), (3, 3), (4, 3), (5, 3), (6, 3), (7, 3), (8, 3), (9, 3),
                 (2, 4), (3, 4), (4, 4), (5, 4), (6, 4), (7, 4), (8, 4), (9, 4),
                 (3, 5), (4, 5), (5, 5), (6, 5), (7, 5), (8, 5),
                 (4, 6), (5, 6), (6, 6), (7, 6), (5, 7), (6, 7)):
        put(x, y, 1)


def _builtin_bow(put) -> None:
    for x, y in ((2, 4), (3, 4), (4, 4), (7, 4), (8, 4), (9, 4),
                 (1, 5), (2, 5), (3, 5), (4, 5), (5, 5), (6, 5), (7, 5), (8, 5), (9, 5), (10, 5),
                 (2, 6), (3, 6), (4, 6), (7, 6), (8, 6), (9, 6), (5, 4), (5, 6)):
        put(x, y, 6)
    put(5, 5, 5)


def _builtin_leaf(put) -> None:
    for x, y in ((6, 1), (5, 2), (6, 2), (7, 2), (4, 3), (5, 3), (6, 3), (7, 3),
                 (3, 4), (4, 4), (5, 4), (6, 4), (4, 5), (5, 5), (6, 5), (5, 6), (6, 6), (6, 7), (7, 8)):
        put(x, y, 4)


def _builtin_question(put) -> None:
    # 疑惑问号
    for x, y in ((4, 1), (5, 1), (6, 1), (7, 1), (7, 2), (7, 3), (6, 3), (5, 4), (5, 5), (5, 7)):
        put(x, y, 2)


def _builtin_droplet(put) -> None:
    # 无语水滴
    for x, y in ((5, 1), (4, 2), (5, 2), (6, 2), (3, 3), (4, 3), (5, 3), (6, 3), (7, 3),
                 (3, 4), (4, 4), (5, 4), (6, 4), (7, 4), (4, 5), (5, 5), (6, 5), (5, 6)):
        put(x, y, 3)


def _builtin_sweat(put) -> None:
    # 尴尬流汗
    for x, y in ((6, 1), (5, 2), (6, 2), (7, 2), (4, 3), (5, 3), (6, 3), (5, 4), (6, 4), (6, 5), (7, 6)):
        put(x, y, 10)
    put(8, 3, 10)
    put(8, 4, 10)


def _builtin_angry_mark(put) -> None:
    # 生气怒气符（十字+角点）
    for x, y in ((5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (3, 3), (4, 3), (6, 3), (7, 3),
                 (2, 1), (8, 1), (2, 5), (8, 5)):
        put(x, y, 8)


def _builtin_sleep_z(put) -> None:
    # 睡觉 Z
    for x, y in ((3, 2), (4, 2), (5, 2), (6, 2), (6, 3), (5, 4), (4, 5), (3, 6), (4, 6), (5, 6), (6, 6),
                 (7, 7), (8, 7), (9, 7), (9, 8), (8, 9), (7, 10), (8, 10), (9, 10)):
        put(x, y, 9)


def _fill_rect(put, x0: int, y0: int, x1: int, y1: int, c: int) -> None:
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(x, y, c)


def _builtin_hat_winter(put) -> None:
    # 冬帽：圆顶 + 帽檐 + 绒球
    _fill_rect(put, 3, 3, 8, 6, 8)
    _fill_rect(put, 2, 6, 9, 7, 12)
    put(5, 2, 5)
    put(6, 2, 5)
    put(5, 1, 1)
    put(6, 1, 1)


def _builtin_hat_cap(put) -> None:
    # 鸭舌帽
    _fill_rect(put, 3, 3, 8, 5, 16)
    _fill_rect(put, 2, 5, 9, 6, 16)
    _fill_rect(put, 7, 6, 11, 7, 16)
    put(5, 4, 13)


def _builtin_hat_sleep(put) -> None:
    # 睡帽尖顶
    put(5, 1, 6)
    put(4, 2, 6)
    put(5, 2, 6)
    put(6, 2, 6)
    _fill_rect(put, 3, 3, 8, 6, 6)
    put(5, 0, 1)


def _builtin_beanie(put) -> None:
    # 针织帽：圆顶 + 翻边 + 顶球（对齐苍叶）
    put(5, 0, 1)
    put(6, 0, 1)
    for x in range(3, 9):
        put(x, 1, 6)
        put(x, 2, 6)
        put(x, 3, 6)
    for x in range(2, 10):
        put(x, 4, 5)


def _builtin_beret(put) -> None:
    # 贝雷：扁圆斜戴（对齐苍叶）
    for x in range(2, 10):
        put(x, 2, 8)
    for x in range(1, 10):
        put(x, 3, 8)
    for x in range(3, 9):
        put(x, 4, 7)
    put(1, 4, 7)


def _builtin_glasses_thick(put) -> None:
    _fill_rect(put, 1, 4, 4, 7, 7)
    _fill_rect(put, 7, 4, 10, 7, 7)
    _fill_rect(put, 2, 5, 3, 6, 10)
    _fill_rect(put, 8, 5, 9, 6, 10)
    put(5, 5, 7)
    put(6, 5, 7)


def _builtin_glasses_thin(put) -> None:
    for x in (2, 3, 4, 7, 8, 9):
        put(x, 4, 7)
        put(x, 7, 7)
    put(2, 5, 7)
    put(2, 6, 7)
    put(4, 5, 7)
    put(4, 6, 7)
    put(7, 5, 7)
    put(7, 6, 7)
    put(9, 5, 7)
    put(9, 6, 7)
    put(5, 5, 7)
    put(6, 5, 7)


def _builtin_glasses_gold(put) -> None:
    for x in (2, 3, 4, 7, 8, 9):
        put(x, 4, 13)
        put(x, 7, 13)
    put(2, 5, 13)
    put(2, 6, 13)
    put(4, 5, 13)
    put(4, 6, 13)
    put(7, 5, 13)
    put(7, 6, 13)
    put(9, 5, 13)
    put(9, 6, 13)
    put(5, 5, 13)
    put(6, 5, 13)


def _builtin_thin_round(put) -> None:
    # 细圆框：中间透明（对齐苍叶）
    for x, y in (
        (2, 4), (3, 4), (1, 5), (4, 5), (1, 6), (4, 6), (2, 7), (3, 7),
        (7, 4), (8, 4), (6, 5), (9, 5), (6, 6), (9, 6), (7, 7), (8, 7),
    ):
        put(x, y, 13)
    put(5, 5, 13)
    put(5, 6, 13)


def _builtin_thin_oval(put) -> None:
    # 细椭圆框（对齐苍叶）
    for x, y in (
        (1, 5), (2, 4), (3, 4), (4, 5), (4, 6), (3, 7), (2, 7), (1, 6),
        (7, 5), (8, 4), (9, 4), (10, 5), (10, 6), (9, 7), (8, 7), (7, 6),
    ):
        put(x, y, 13)
    put(5, 5, 13)
    put(6, 5, 13)


def _builtin_half_rim(put) -> None:
    # 半框：上沿与鼻梁，中间透明（对齐苍叶）
    for x in range(1, 5):
        put(x, 4, 13)
    for x in range(7, 11):
        put(x, 4, 13)
    put(1, 5, 13)
    put(4, 5, 13)
    put(7, 5, 13)
    put(10, 5, 13)
    put(5, 4, 13)
    put(6, 4, 13)


def _builtin_glasses_square(put) -> None:
    _fill_rect(put, 1, 4, 4, 7, 7)
    _fill_rect(put, 7, 4, 10, 7, 7)
    _fill_rect(put, 2, 5, 3, 6, 3)
    _fill_rect(put, 8, 5, 9, 6, 3)
    put(5, 5, 7)
    put(6, 5, 7)


def _builtin_glasses_round(put) -> None:
    for x, y in ((2, 4), (3, 4), (4, 4), (1, 5), (1, 6), (2, 7), (3, 7), (4, 7), (5, 5), (5, 6),
                 (7, 4), (8, 4), (9, 4), (10, 5), (10, 6), (7, 7), (8, 7), (9, 7), (6, 5), (6, 6)):
        put(x, y, 7)
    put(3, 5, 10)
    put(3, 6, 10)
    put(8, 5, 10)
    put(8, 6, 10)


def _builtin_glasses_odd(put) -> None:
    # 异形：左方右圆
    _fill_rect(put, 1, 4, 4, 7, 7)
    _fill_rect(put, 2, 5, 3, 6, 15)
    for x, y in ((7, 4), (8, 4), (9, 4), (6, 5), (10, 5), (6, 6), (10, 6), (7, 7), (8, 7), (9, 7)):
        put(x, y, 7)
    put(8, 5, 15)
    put(8, 6, 15)
    put(5, 5, 7)


def _builtin_sunglasses(put) -> None:
    _fill_rect(put, 1, 4, 4, 7, 14)
    _fill_rect(put, 7, 4, 10, 7, 14)
    put(5, 5, 14)
    put(6, 5, 14)
    put(2, 5, 7)
    put(8, 5, 7)


def _builtin_glasses_funny(put) -> None:
    # 搞怪：一大一小 + 鼻梁
    _fill_rect(put, 0, 3, 4, 8, 8)
    _fill_rect(put, 1, 4, 3, 7, 2)
    _fill_rect(put, 7, 5, 10, 8, 6)
    _fill_rect(put, 8, 6, 9, 7, 5)
    put(5, 6, 7)
    put(6, 6, 7)


def _builtin_scarf(put) -> None:
    _fill_rect(put, 2, 7, 9, 8, 17)
    _fill_rect(put, 7, 8, 9, 11, 17)
    put(8, 9, 1)
    put(8, 11, 1)


def _builtin_silk_scarf(put) -> None:
    _fill_rect(put, 1, 6, 10, 7, 6)
    put(2, 5, 6)
    put(9, 5, 6)
    put(4, 7, 5)
    put(5, 7, 1)
    put(6, 7, 5)
    put(3, 8, 6)
    put(8, 8, 6)


def _builtin_necklace(put) -> None:
    for x in range(3, 9):
        put(x, 7, 13)
    put(2, 6, 13)
    put(9, 6, 13)
    put(5, 8, 1)
    put(6, 8, 1)
    put(5, 9, 8)


def _builtin_bouquet(put) -> None:
    put(5, 2, 1)
    put(4, 3, 8)
    put(5, 3, 1)
    put(6, 3, 6)
    put(3, 4, 4)
    put(4, 4, 1)
    put(5, 4, 8)
    put(6, 4, 4)
    put(7, 4, 6)
    put(5, 5, 4)
    put(5, 6, 11)
    put(5, 7, 11)
    put(4, 8, 12)
    put(5, 8, 12)
    put(6, 8, 12)


def _builtin_doll(put) -> None:
    _fill_rect(put, 4, 1, 7, 3, 12)
    put(5, 2, 7)
    put(6, 2, 7)
    _fill_rect(put, 4, 4, 7, 7, 1)
    put(3, 5, 12)
    put(8, 5, 12)
    put(5, 8, 11)
    put(6, 8, 11)


def _builtin_bag(put) -> None:
    _fill_rect(put, 3, 4, 8, 9, 11)
    put(4, 3, 7)
    put(5, 3, 7)
    put(6, 3, 7)
    put(7, 3, 7)
    put(5, 6, 13)
    put(6, 6, 13)


def _builtin_handbag(put) -> None:
    _fill_rect(put, 2, 5, 9, 9, 17)
    put(3, 4, 7)
    put(8, 4, 7)
    put(4, 3, 7)
    put(5, 3, 7)
    put(6, 3, 7)
    put(7, 3, 7)
    put(5, 7, 13)


def _builtin_ita_bag(put) -> None:
    _fill_rect(put, 2, 3, 9, 10, 16)
    put(3, 2, 7)
    put(8, 2, 7)
    put(4, 5, 1)
    put(5, 5, 2)
    put(6, 5, 6)
    put(4, 7, 3)
    put(6, 7, 8)
    put(5, 8, 5)


def _builtin_cheer_fan(put) -> None:
    _fill_rect(put, 2, 2, 9, 6, 1)
    put(3, 3, 5)
    put(4, 3, 5)
    put(5, 3, 8)
    put(6, 3, 5)
    put(7, 3, 5)
    put(5, 4, 5)
    put(5, 7, 11)
    put(5, 8, 11)
    put(5, 9, 11)


def _builtin_cheer_stick(put) -> None:
    put(5, 1, 2)
    put(4, 2, 2)
    put(5, 2, 5)
    put(6, 2, 2)
    put(5, 3, 1)
    put(5, 4, 1)
    put(5, 5, 18)
    put(5, 6, 18)
    put(5, 7, 18)
    put(5, 8, 18)
    put(5, 9, 7)
    put(4, 9, 7)
    put(6, 9, 7)


# —— 扩展配饰（沿用装扮色板）——
def _builtin_crown(put) -> None:
    put(2, 3, 13)
    put(5, 2, 13)
    put(8, 3, 13)
    _fill_rect(put, 2, 4, 9, 5, 13)
    put(3, 4, 2)
    put(5, 4, 1)
    put(7, 4, 2)
    _fill_rect(put, 3, 6, 8, 6, 13)


def _builtin_cat_ears(put) -> None:
    put(2, 2, 17)
    put(3, 1, 17)
    put(3, 2, 1)
    put(4, 2, 17)
    put(7, 2, 17)
    put(8, 1, 17)
    put(8, 2, 1)
    put(9, 2, 17)


def _builtin_bunny_ears(put) -> None:
    put(3, 0, 12)
    put(3, 1, 12)
    put(3, 2, 1)
    put(4, 1, 12)
    put(8, 0, 12)
    put(8, 1, 12)
    put(8, 2, 1)
    put(7, 1, 12)


def _builtin_witch_hat(put) -> None:
    put(5, 0, 14)
    put(4, 1, 14)
    put(5, 1, 14)
    put(6, 1, 14)
    _fill_rect(put, 3, 2, 8, 3, 14)
    put(5, 2, 6)
    _fill_rect(put, 1, 4, 10, 5, 14)
    put(2, 4, 13)


def _builtin_flower_crown(put) -> None:
    for x in range(2, 10):
        put(x, 4, 4)
    put(2, 3, 1)
    put(4, 3, 8)
    put(6, 3, 1)
    put(8, 3, 6)
    put(3, 5, 8)
    put(5, 5, 1)
    put(7, 5, 4)


def _builtin_party_hat(put) -> None:
    put(5, 0, 2)
    put(4, 1, 1)
    put(5, 1, 1)
    put(6, 1, 1)
    put(3, 2, 6)
    put(4, 2, 6)
    put(5, 2, 6)
    put(6, 2, 6)
    put(7, 2, 6)
    _fill_rect(put, 2, 3, 9, 4, 3)
    put(4, 3, 5)
    put(6, 3, 5)


def _builtin_sailor_hat(put) -> None:
    _fill_rect(put, 2, 3, 9, 4, 5)
    _fill_rect(put, 3, 2, 8, 2, 5)
    put(5, 1, 16)
    put(4, 3, 16)
    put(5, 3, 16)
    put(6, 3, 16)
    _fill_rect(put, 1, 5, 10, 5, 5)


def _builtin_headphones(put) -> None:
    for x in range(2, 10):
        put(x, 2, 14)
    _fill_rect(put, 1, 3, 2, 6, 14)
    _fill_rect(put, 9, 3, 10, 6, 14)
    put(1, 4, 3)
    put(10, 4, 3)


def _builtin_hair_clip(put) -> None:
    put(7, 2, 1)
    put(8, 2, 1)
    put(6, 3, 13)
    put(7, 3, 1)
    put(8, 3, 13)
    put(9, 3, 13)
    put(7, 4, 13)
    put(8, 4, 1)


def _builtin_hair_ribbon(put) -> None:
    put(6, 2, 1)
    put(7, 2, 1)
    put(5, 3, 1)
    put(6, 3, 5)
    put(7, 3, 5)
    put(8, 3, 1)
    put(4, 4, 1)
    put(9, 4, 1)
    put(5, 4, 1)
    put(8, 4, 1)


def _builtin_heart_glasses(put) -> None:
    for x, y in (
        (2, 4),
        (3, 4),
        (1, 5),
        (4, 5),
        (2, 6),
        (3, 6),
        (7, 4),
        (8, 4),
        (6, 5),
        (9, 5),
        (7, 6),
        (8, 6),
    ):
        put(x, y, 1)
    put(5, 5, 1)
    put(2, 5, 5)
    put(7, 5, 5)


def _builtin_star_glasses(put) -> None:
    put(2, 4, 2)
    put(3, 5, 2)
    put(1, 5, 2)
    put(4, 5, 2)
    put(2, 6, 2)
    put(3, 6, 2)
    put(7, 4, 2)
    put(8, 5, 2)
    put(6, 5, 2)
    put(9, 5, 2)
    put(7, 6, 2)
    put(8, 6, 2)
    put(5, 5, 2)


def _builtin_monocle(put) -> None:
    for x, y in (
        (7, 4),
        (8, 4),
        (9, 4),
        (6, 5),
        (10, 5),
        (6, 6),
        (10, 6),
        (7, 7),
        (8, 7),
        (9, 7),
    ):
        put(x, y, 13)
    put(8, 5, 3)
    put(8, 6, 3)
    put(10, 8, 13)
    put(10, 9, 13)


def _builtin_choker(put) -> None:
    _fill_rect(put, 3, 7, 8, 7, 14)
    put(5, 8, 13)
    put(6, 8, 13)
    put(5, 9, 1)


def _builtin_bowtie(put) -> None:
    put(2, 6, 8)
    put(3, 6, 8)
    put(4, 6, 8)
    put(7, 6, 8)
    put(8, 6, 8)
    put(9, 6, 8)
    put(5, 6, 5)
    put(6, 6, 5)
    put(3, 7, 8)
    put(8, 7, 8)
    put(5, 7, 5)
    put(6, 7, 5)


def _builtin_bell_collar(put) -> None:
    _fill_rect(put, 2, 7, 9, 7, 8)
    put(5, 8, 13)
    put(6, 8, 13)
    put(5, 9, 13)
    put(6, 9, 2)
    put(4, 8, 8)
    put(7, 8, 8)


def _builtin_backpack(put) -> None:
    _fill_rect(put, 3, 3, 8, 9, 16)
    put(4, 2, 7)
    put(7, 2, 7)
    put(4, 4, 3)
    put(5, 4, 3)
    put(6, 4, 3)
    put(5, 6, 13)
    put(6, 6, 13)
    put(3, 8, 11)
    put(8, 8, 11)


def _builtin_crossbody(put) -> None:
    put(2, 3, 11)
    put(3, 4, 11)
    put(4, 5, 11)
    _fill_rect(put, 5, 5, 10, 9, 17)
    put(7, 6, 1)
    put(8, 7, 13)


def _builtin_coffee(put) -> None:
    _fill_rect(put, 4, 3, 8, 4, 12)
    _fill_rect(put, 4, 5, 8, 9, 5)
    put(5, 6, 11)
    put(6, 6, 11)
    put(7, 6, 11)
    put(9, 6, 18)
    put(9, 7, 18)
    put(5, 2, 18)
    put(6, 1, 18)


def _builtin_book(put) -> None:
    _fill_rect(put, 3, 2, 9, 9, 8)
    _fill_rect(put, 4, 3, 8, 8, 12)
    put(5, 4, 7)
    put(6, 4, 7)
    put(5, 6, 7)
    put(6, 6, 7)
    put(3, 5, 13)


def _builtin_umbrella(put) -> None:
    _fill_rect(put, 2, 2, 9, 3, 3)
    put(1, 3, 3)
    put(10, 3, 3)
    put(3, 1, 3)
    put(5, 1, 3)
    put(7, 1, 3)
    put(5, 4, 11)
    put(5, 5, 11)
    put(5, 6, 11)
    put(5, 7, 11)
    put(6, 8, 11)


def _builtin_phone(put) -> None:
    _fill_rect(put, 4, 1, 7, 10, 14)
    _fill_rect(put, 5, 2, 6, 8, 3)
    put(5, 9, 5)
    put(6, 9, 5)


def _builtin_lollipop(put) -> None:
    put(5, 1, 1)
    put(4, 2, 1)
    put(5, 2, 5)
    put(6, 2, 1)
    put(5, 3, 1)
    put(5, 4, 12)
    put(5, 5, 12)
    put(5, 6, 12)
    put(5, 7, 12)
    put(5, 8, 11)


def _builtin_wand(put) -> None:
    put(8, 1, 2)
    put(7, 2, 2)
    put(8, 2, 5)
    put(9, 2, 2)
    put(8, 3, 2)
    put(7, 4, 13)
    put(6, 5, 13)
    put(5, 6, 13)
    put(4, 7, 13)
    put(3, 8, 13)
    put(2, 9, 11)


def _builtin_moon(put) -> None:
    _fill_rect(put, 4, 2, 8, 8, 2)
    _fill_rect(put, 6, 3, 9, 7, 0)
    put(5, 3, 2)
    put(4, 4, 2)
    put(4, 5, 2)
    put(4, 6, 2)
    put(5, 7, 2)


def _builtin_sparkle(put) -> None:
    put(5, 1, 5)
    put(5, 2, 2)
    put(5, 3, 5)
    put(3, 3, 5)
    put(4, 3, 2)
    put(6, 3, 2)
    put(7, 3, 5)
    put(5, 4, 2)
    put(5, 5, 5)
    put(2, 6, 2)
    put(8, 7, 5)


def _builtin_cloud(put) -> None:
    _fill_rect(put, 3, 4, 8, 6, 5)
    put(2, 5, 5)
    put(9, 5, 5)
    put(4, 3, 5)
    put(5, 3, 5)
    put(6, 3, 5)
    put(7, 3, 5)


def _builtin_sakura(put) -> None:
    put(5, 2, 1)
    put(3, 4, 1)
    put(4, 3, 17)
    put(5, 3, 5)
    put(6, 3, 17)
    put(7, 4, 1)
    put(4, 4, 17)
    put(5, 4, 1)
    put(6, 4, 17)
    put(5, 5, 17)
    put(5, 6, 4)
    put(5, 7, 4)


def _builtin_butterfly(put) -> None:
    put(2, 3, 6)
    put(3, 2, 6)
    put(3, 4, 6)
    put(4, 3, 5)
    put(5, 3, 14)
    put(6, 3, 5)
    put(7, 2, 3)
    put(7, 4, 3)
    put(8, 3, 3)
    put(5, 4, 14)
    put(5, 2, 14)


def _builtin_cherry(put) -> None:
    put(4, 4, 8)
    put(5, 4, 8)
    put(4, 5, 8)
    put(5, 5, 8)
    put(7, 5, 8)
    put(8, 5, 8)
    put(7, 6, 8)
    put(8, 6, 8)
    put(5, 3, 4)
    put(6, 2, 4)
    put(6, 3, 4)
    put(7, 3, 4)


def _builtin_halo(put) -> None:
    for x in range(3, 9):
        put(x, 2, 13)
    put(2, 3, 13)
    put(9, 3, 13)
    put(2, 4, 13)
    put(9, 4, 13)
    for x in range(3, 9):
        put(x, 5, 13)


def _entry(
    eid: str,
    name: str,
    draw_fn,
    *,
    group: str,
    nx: float = OUTFIT_DEFAULT_NX,
    ny: float = OUTFIT_DEFAULT_NY,
    scale: float = OUTFIT_DEFAULT_SCALE,
) -> dict:
    return {
        "id": eid,
        "name": name,
        "group": group,
        "cells": _paint_cells(draw_fn),
        "nx": nx,
        "ny": ny,
        "scale": scale,
    }


BUILTIN_CATALOG: tuple[dict, ...] = (
    # —— 装饰 / 表情 ——
    _entry("star", "星星", _builtin_star, group="装饰"),
    _entry("heart", "爱心", _builtin_heart, group="装饰"),
    _entry("bow", "蝴蝶结", _builtin_bow, group="装饰", ny=-0.36, scale=0.26),
    _entry("leaf", "小叶", _builtin_leaf, group="装饰"),
    _entry("moon", "月牙", _builtin_moon, group="装饰", nx=-0.34, ny=-0.40, scale=0.24),
    _entry("sparkle", "闪闪", _builtin_sparkle, group="装饰", nx=0.34, ny=-0.40, scale=0.22),
    _entry("cloud", "小云", _builtin_cloud, group="装饰", ny=-0.42, scale=0.26),
    _entry("sakura", "樱花", _builtin_sakura, group="装饰", nx=0.32, ny=-0.36, scale=0.24),
    _entry("butterfly", "蝴蝶", _builtin_butterfly, group="装饰", nx=-0.32, ny=-0.34, scale=0.26),
    _entry("cherry", "樱桃", _builtin_cherry, group="装饰", nx=0.30, ny=-0.28, scale=0.24),
    _entry("halo", "光环", _builtin_halo, group="装饰", ny=-0.48, scale=0.28),
    _entry("question", "问号", _builtin_question, group="表情", nx=0.36, ny=-0.42, scale=0.22),
    _entry("droplet", "无语", _builtin_droplet, group="表情", nx=-0.36, ny=-0.42, scale=0.22),
    _entry("sweat", "流汗", _builtin_sweat, group="表情", nx=0.38, ny=-0.40, scale=0.20),
    _entry("angry_mark", "生气", _builtin_angry_mark, group="表情", nx=0.36, ny=-0.38, scale=0.22),
    _entry("sleep_z", "睡觉", _builtin_sleep_z, group="表情", nx=0.34, ny=-0.44, scale=0.24),
    # —— 帽子 ——
    _entry("hat_winter", "冬帽", _builtin_hat_winter, group="帽子", ny=-0.44, scale=0.34),
    _entry("hat_cap", "鸭舌帽", _builtin_hat_cap, group="帽子", ny=-0.42, scale=0.34),
    _entry("hat_sleep", "睡帽", _builtin_hat_sleep, group="帽子", ny=-0.46, scale=0.32),
    _entry("beanie", "针织帽", _builtin_beanie, group="帽子", ny=-0.48, scale=0.30),
    _entry("beret", "贝雷", _builtin_beret, group="帽子", nx=-0.04, ny=-0.46, scale=0.28),
    _entry("crown", "小皇冠", _builtin_crown, group="帽子", ny=-0.48, scale=0.30),
    _entry("cat_ears", "猫耳", _builtin_cat_ears, group="帽子", ny=-0.50, scale=0.28),
    _entry("bunny_ears", "兔耳", _builtin_bunny_ears, group="帽子", ny=-0.52, scale=0.30),
    _entry("witch_hat", "魔女帽", _builtin_witch_hat, group="帽子", ny=-0.48, scale=0.34),
    _entry("flower_crown", "花环", _builtin_flower_crown, group="帽子", ny=-0.44, scale=0.30),
    _entry("party_hat", "派对帽", _builtin_party_hat, group="帽子", ny=-0.50, scale=0.30),
    _entry("sailor_hat", "水手帽", _builtin_sailor_hat, group="帽子", ny=-0.46, scale=0.32),
    _entry("headphones", "耳机", _builtin_headphones, group="帽子", ny=-0.40, scale=0.32),
    _entry("hair_clip", "发夹", _builtin_hair_clip, group="帽子", nx=0.28, ny=-0.40, scale=0.22),
    _entry("hair_ribbon", "发带结", _builtin_hair_ribbon, group="帽子", nx=0.26, ny=-0.42, scale=0.24),
    # —— 眼镜 ——
    _entry("glasses_thick", "粗框眼镜", _builtin_glasses_thick, group="眼镜", ny=-0.16, scale=0.30),
    _entry("glasses_thin", "细框眼镜", _builtin_glasses_thin, group="眼镜", ny=-0.16, scale=0.28),
    _entry("glasses_gold", "金丝边", _builtin_glasses_gold, group="眼镜", ny=-0.16, scale=0.28),
    _entry("thin_round", "细圆框", _builtin_thin_round, group="眼镜", ny=-0.22, scale=0.26),
    _entry("thin_oval", "细椭圆", _builtin_thin_oval, group="眼镜", ny=-0.22, scale=0.26),
    _entry("half_rim", "半框", _builtin_half_rim, group="眼镜", ny=-0.22, scale=0.26),
    _entry("glasses_square", "方框眼镜", _builtin_glasses_square, group="眼镜", ny=-0.16, scale=0.30),
    _entry("glasses_round", "圆框眼镜", _builtin_glasses_round, group="眼镜", ny=-0.16, scale=0.30),
    _entry("glasses_odd", "异形眼镜", _builtin_glasses_odd, group="眼镜", ny=-0.16, scale=0.30),
    _entry("sunglasses", "墨镜", _builtin_sunglasses, group="眼镜", ny=-0.16, scale=0.30),
    _entry("glasses_funny", "搞怪眼镜", _builtin_glasses_funny, group="眼镜", ny=-0.14, scale=0.32),
    _entry("heart_glasses", "爱心镜", _builtin_heart_glasses, group="眼镜", ny=-0.16, scale=0.30),
    _entry("star_glasses", "星星镜", _builtin_star_glasses, group="眼镜", ny=-0.16, scale=0.30),
    _entry("monocle", "单片镜", _builtin_monocle, group="眼镜", nx=0.06, ny=-0.14, scale=0.28),
    # —— 颈饰 ——
    _entry("scarf", "围巾", _builtin_scarf, group="颈饰", ny=0.08, scale=0.32),
    _entry("silk_scarf", "丝巾", _builtin_silk_scarf, group="颈饰", ny=0.02, scale=0.30),
    _entry("necklace", "项链", _builtin_necklace, group="颈饰", ny=0.06, scale=0.26),
    _entry("choker", "项圈", _builtin_choker, group="颈饰", ny=0.08, scale=0.26),
    _entry("bowtie", "领结", _builtin_bowtie, group="颈饰", ny=0.04, scale=0.26),
    _entry("bell_collar", "铃铛颈圈", _builtin_bell_collar, group="颈饰", ny=0.10, scale=0.28),
    # —— 包袋 ——
    _entry("bag", "包包", _builtin_bag, group="包袋", nx=0.36, ny=0.12, scale=0.28),
    _entry("handbag", "手袋", _builtin_handbag, group="包袋", nx=0.34, ny=0.10, scale=0.28),
    _entry("ita_bag", "痛包", _builtin_ita_bag, group="包袋", nx=0.36, ny=0.08, scale=0.32),
    _entry("backpack", "双肩包", _builtin_backpack, group="包袋", nx=-0.34, ny=0.06, scale=0.30),
    _entry("crossbody", "斜挎包", _builtin_crossbody, group="包袋", nx=0.34, ny=0.08, scale=0.30),
    # —— 手持 ——
    _entry("bouquet", "花束", _builtin_bouquet, group="手持", nx=0.34, ny=0.18, scale=0.30),
    _entry("doll", "玩偶", _builtin_doll, group="手持", nx=-0.34, ny=0.16, scale=0.28),
    _entry("cheer_fan", "应援扇", _builtin_cheer_fan, group="手持", nx=0.38, ny=0.05, scale=0.30),
    _entry("cheer_stick", "应援棒", _builtin_cheer_stick, group="手持", nx=0.40, ny=0.02, scale=0.30),
    _entry("coffee", "咖啡杯", _builtin_coffee, group="手持", nx=0.36, ny=0.14, scale=0.26),
    _entry("book", "小书", _builtin_book, group="手持", nx=-0.36, ny=0.12, scale=0.28),
    _entry("umbrella", "雨伞", _builtin_umbrella, group="手持", nx=0.38, ny=-0.02, scale=0.32),
    _entry("phone", "手机", _builtin_phone, group="手持", nx=0.34, ny=0.10, scale=0.24),
    _entry("lollipop", "棒棒糖", _builtin_lollipop, group="手持", nx=0.36, ny=0.06, scale=0.26),
    _entry("wand", "星星杖", _builtin_wand, group="手持", nx=0.38, ny=0.00, scale=0.30),
)


def defaults_for(kind: str, ref: str = "") -> tuple[float, float, float, float]:
    """装扮选素材时的默认位置/缩放/旋转。"""
    if kind == KIND_BUILTIN:
        entry = next((b for b in BUILTIN_CATALOG if b["id"] == ref), None)
        if entry is not None:
            return (
                clamp_norm(entry.get("nx", OUTFIT_DEFAULT_NX)),
                clamp_norm(entry.get("ny", OUTFIT_DEFAULT_NY)),
                clamp_scale(entry.get("scale", OUTFIT_DEFAULT_SCALE)),
                clamp_rot(entry.get("rot", OUTFIT_DEFAULT_ROT)),
            )
    return OUTFIT_DEFAULT_NX, OUTFIT_DEFAULT_NY, OUTFIT_DEFAULT_SCALE, OUTFIT_DEFAULT_ROT


def clamp_norm(v: float, lo: float = -0.55, hi: float = 0.55) -> float:
    try:
        x = float(v)
    except (TypeError, ValueError):
        x = 0.0
    return max(lo, min(hi, x))


def clamp_scale(v: float) -> float:
    try:
        x = float(v)
    except (TypeError, ValueError):
        x = OUTFIT_DEFAULT_SCALE
    return max(OUTFIT_SCALE_MIN, min(OUTFIT_SCALE_MAX, x))


def clamp_rot(v: float) -> float:
    try:
        x = float(v)
    except (TypeError, ValueError):
        x = OUTFIT_DEFAULT_ROT
    return max(OUTFIT_ROT_MIN, min(OUTFIT_ROT_MAX, x))


def normalize_decors(raw) -> list[dict]:
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind") or "").strip()
        if kind not in (KIND_MATERIAL, KIND_USER_PAINT, KIND_GIFT_ART, KIND_BUILTIN):
            continue
        ref = str(item.get("ref") or "").strip()
        if kind == KIND_MATERIAL and not ref:
            continue
        if kind == KIND_BUILTIN and not ref:
            continue
        did = str(item.get("id") or "").strip() or uuid4().hex[:10]
        out.append(
            {
                "id": did,
                "kind": kind,
                "ref": ref,
                "nx": clamp_norm(item.get("nx", OUTFIT_DEFAULT_NX)),
                "ny": clamp_norm(item.get("ny", OUTFIT_DEFAULT_NY)),
                "scale": clamp_scale(item.get("scale", OUTFIT_DEFAULT_SCALE)),
                "rot": clamp_rot(item.get("rot", OUTFIT_DEFAULT_ROT)),
            }
        )
        if len(out) >= OUTFIT_MAX:
            break
    return out


def new_decor(
    kind: str,
    ref: str = "",
    *,
    nx: float | None = None,
    ny: float | None = None,
    scale: float | None = None,
    rot: float | None = None,
) -> dict:
    return {
        "id": uuid4().hex[:10],
        "kind": kind,
        "ref": str(ref or "").strip(),
        "nx": clamp_norm(OUTFIT_DEFAULT_NX if nx is None else nx),
        "ny": clamp_norm(OUTFIT_DEFAULT_NY if ny is None else ny),
        "scale": clamp_scale(OUTFIT_DEFAULT_SCALE if scale is None else scale),
        "rot": clamp_rot(OUTFIT_DEFAULT_ROT if rot is None else rot),
    }


def cells_to_rgba(cells: list[int], palette: tuple[str | None, ...] | list, *, scale: int = 4) -> Image.Image:
    n = 12
    side = n * max(1, int(scale))
    img = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    px = ImageDraw.Draw(img)
    pal = list(palette)
    for y in range(n):
        for x in range(n):
            idx = int(cells[y * n + x] or 0) if y * n + x < len(cells) else 0
            color = pal[idx] if 0 <= idx < len(pal) else None
            if not color:
                continue
            x0, y0 = x * scale, y * scale
            px.rectangle((x0, y0, x0 + scale - 1, y0 + scale - 1), fill=color)
    return img


def builtin_image(ref: str, *, size_px: int) -> Image.Image | None:
    entry = next((b for b in BUILTIN_CATALOG if b["id"] == ref), None)
    if entry is None:
        return None
    base = cells_to_rgba(entry["cells"], _BUILTIN_PALETTE, scale=4)
    if size_px <= 0:
        return base
    return base.resize((size_px, size_px), Image.Resampling.NEAREST)


def load_png_fit(path: Path, size_px: int) -> Image.Image | None:
    if not path.is_file():
        return None
    try:
        img = Image.open(path).convert("RGBA")
    except Exception:
        return None
    if img.getbbox() is None:
        return None
    if size_px > 0:
        img = img.resize((size_px, size_px), Image.Resampling.NEAREST)
    return img


def _material_from_cells(entry: dict, size_px: int) -> Image.Image | None:
    cells = entry.get("cells")
    if not isinstance(cells, list) or not cells:
        return None
    pal_raw = entry.get("palette")
    if isinstance(pal_raw, list) and pal_raw:
        pal: tuple[str | None, ...] = tuple(
            (c if isinstance(c, str) and c.startswith("#") else None) for c in pal_raw
        )
    else:
        pal = _BUILTIN_PALETTE
    try:
        from home_cottage import gift_pixels_to_rgba

        base = gift_pixels_to_rgba([int(v or 0) for v in cells], pal, scale=4)
    except Exception:
        base = None
    if base is None:
        base = cells_to_rgba([int(v or 0) for v in cells], pal, scale=4)
    if base is None or base.getbbox() is None:
        return None
    if size_px > 0:
        return base.resize((size_px, size_px), Image.Resampling.NEAREST)
    return base


def load_decor_image(
    decor: dict,
    *,
    materials_dir: Path,
    materials_index: Path,
    props_dir: Path,
    size_px: int,
) -> Image.Image | None:
    kind = str(decor.get("kind") or "")
    ref = str(decor.get("ref") or "")
    if kind == KIND_BUILTIN:
        return builtin_image(ref, size_px=size_px)
    if kind == KIND_USER_PAINT:
        return load_png_fit(props_dir / "user_paint.png", size_px)
    if kind == KIND_GIFT_ART:
        return load_png_fit(props_dir / "gift_art.png", size_px)
    if kind == KIND_MATERIAL:
        entry = None
        try:
            from home_cottage import find_material, load_materials_index

            entry = find_material(load_materials_index(materials_index), ref)
        except Exception:
            entry = None
        # 优先用索引 cells 重绘（PNG 可能几乎空白或过期）
        if entry:
            from_cells = _material_from_cells(entry, size_px)
            if from_cells is not None:
                return from_cells
        png = materials_dir / f"{ref}.png"
        img = load_png_fit(png, size_px)
        if img is not None:
            return img
        if entry:
            alt = materials_dir / str(entry.get("file") or f"{ref}.png")
            return load_png_fit(alt, size_px)
    return None


def compose_outfit_layer(
    pet_size: int,
    decors: list[dict],
    *,
    materials_dir: Path,
    materials_index: Path,
    props_dir: Path,
) -> Image.Image:
    """透明底 pet_size×pet_size，装饰按相对中心坐标粘贴（支持顺时针旋转）。"""
    side = max(16, int(pet_size))
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    cx = side / 2.0
    cy = side / 2.0
    for d in normalize_decors(decors):
        deco_side = max(8, int(round(side * float(d["scale"]))))
        img = load_decor_image(
            d,
            materials_dir=materials_dir,
            materials_index=materials_index,
            props_dir=props_dir,
            size_px=deco_side,
        )
        if img is None:
            continue
        rot = float(d.get("rot") or 0.0)
        if abs(rot) >= 0.5:
            # 存储为顺时针角；PIL rotate 为逆时针
            img = img.rotate(-rot, expand=True, resample=Image.Resampling.NEAREST)
        x = int(round(cx + float(d["nx"]) * side - img.width / 2))
        y = int(round(cy + float(d["ny"]) * side - img.height / 2))
        canvas.alpha_composite(img, (x, y))
    return canvas


def list_asset_choices(
    *,
    materials_dir: Path,
    materials_index: Path,
    props_dir: Path,
) -> list[dict]:
    """供装扮面板选择：我的自创在前，再按帽子/眼镜等分类。"""
    choices: list[dict] = []
    try:
        from home_cottage import load_materials_index

        mats = load_materials_index(materials_index)
    except Exception:
        mats = []
    # 全部图库条目进「我的」，按来源加前缀，避免只显示一张槽位图
    for m in mats:
        mid = str(m.get("id") or "")
        if not mid:
            continue
        src = str(m.get("source") or "home").strip().lower()
        if src == "gift":
            prefix = "礼物·"
        elif src == "rpg":
            prefix = "RPG·"
        else:
            prefix = "自创·"
        name = str(m.get("name") or mid)[:14]
        choices.append(
            {
                "kind": KIND_MATERIAL,
                "ref": mid,
                "name": f"{prefix}{name}",
                "group": "我的",
            }
        )
    # 活跃槽（最新导出）作为快捷项
    if (props_dir / "user_paint.png").is_file():
        choices.append(
            {"kind": KIND_USER_PAINT, "ref": "", "name": "最新自创槽", "group": "我的"}
        )
    if (props_dir / "gift_art.png").is_file():
        choices.append(
            {"kind": KIND_GIFT_ART, "ref": "", "name": "最新礼物槽", "group": "我的"}
        )
    for b in BUILTIN_CATALOG:
        g = str(b.get("group") or "公开")
        choices.append(
            {
                "kind": KIND_BUILTIN,
                "ref": b["id"],
                "name": str(b["name"]),
                "group": g,
            }
        )
    # 稳定排序：按分组顺序，组内保持目录顺序
    rank = {name: i for i, name in enumerate(OUTFIT_GROUP_ORDER)}
    indexed = list(enumerate(choices))
    indexed.sort(key=lambda it: (rank.get(str(it[1].get("group") or "公开"), 99), it[0]))
    return [c for _, c in indexed]


def thumb_for_choice(
    choice: dict,
    *,
    materials_dir: Path,
    materials_index: Path,
    props_dir: Path,
    size_px: int = 36,
) -> Image.Image | None:
    return load_decor_image(
        {"kind": choice.get("kind"), "ref": choice.get("ref", "")},
        materials_dir=materials_dir,
        materials_index=materials_index,
        props_dir=props_dir,
        size_px=size_px,
    )


def dump_decors(decors: list[dict]) -> list[dict]:
    return normalize_decors(decors)
