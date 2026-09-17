"""家园室外经营：农田、钱包、合成（脱离原作）。"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

# —— 流通物品 ——
ITEM_LABELS: dict[str, str] = {
    "seed_wheat": "麦种",
    "seed_berry": "莓种",
    "seed_corn": "玉米种",
    "seed_apple": "苹果种",
    "seed_grape": "葡萄种",
    "seed_rose": "玫瑰种",
    "crop_wheat": "小麦",
    "crop_berry": "莓果",
    "crop_corn": "玉米穗",
    "crop_apple": "苹果",
    "crop_grape": "葡萄",
    "crop_rose": "玫瑰",
    "wood": "木材",
    "flower_cut": "采下的花",
    "fish": "鲜鱼",
    "work_reward_box": "工作宝箱",
    "compost": "堆肥",
    "dew_drop": "露水",
    "jam_berry": "莓果酱",
    "flour": "面粉",
    "corn_flakes": "玉米片",
}

SEED_TO_CROP: dict[str, str] = {
    "seed_wheat": "wheat",
    "seed_berry": "berry",
    "seed_corn": "corn",
    "seed_apple": "apple",
    "seed_grape": "grape",
    "seed_rose": "rose",
}

# 可砍伐的树种（布置笔刷）
TREE_KINDS: frozenset[str] = frozenset({"tree", "tree_pine", "tree_fruit", "tree_blossom"})

# 成熟度：满分 100；每小时 +5；浇水后 1 小时内速率 ×2；每天最多浇 2 次
MATURITY_MAX = 100.0
MATURITY_PER_HOUR = 5.0
WATER_BOOST_SEC = 3600.0
WATER_MAX_PER_DAY = 2
TREE_REGROW_SEC = 48 * 3600
CHOP_DICE_MIN = 2
CHOP_DICE_MAX = 6

# 轻度种田：每日行动预算（批量操作只计 1 次，防肝）
DAILY_ACTION_SOFT = 5
DAILY_ACTION_HARD = 8
# 久不浇水：成长变慢（不枯死）；极久干燥可「堆肥」回收
DRY_SLOW_AFTER_SEC = 18 * 3600
DRY_SLOW_RATE = 0.45
WILT_AFTER_SEC = 72 * 3600
# 离线微收益：最长折算小时 / 每日最多自动浇格数 / 金币上限
OFFLINE_GROW_CAP_HOURS = 16.0
OFFLINE_AUTO_WATER_MAX = 3
OFFLINE_BONUS_COIN_MAX = 2

CROP_DEFS: dict[str, dict[str, Any]] = {
    "wheat": {
        "label": "小麦",
        "seed": "seed_wheat",
        "item": "crop_wheat",
        "colors": ("#c8b070", "#d4c078", "#e8d888", "#f0e090"),
        "shape": "grain",
        "season": "常",
        "days_hint": "约 20 时",
        "sell": 4,
        "use": "做饭·稳产",
        "stable": True,
    },
    "berry": {
        "label": "莓果",
        "seed": "seed_berry",
        "item": "crop_berry",
        "colors": ("#886688", "#aa6688", "#cc6688", "#ee5588"),
        "shape": "berry",
        "season": "春夏",
        "days_hint": "约 20 时",
        "sell": 5,
        "use": "做饭·送礼",
        "stable": True,
    },
    "corn": {
        "label": "玉米",
        "seed": "seed_corn",
        "item": "crop_corn",
        "colors": ("#889944", "#aaba44", "#ccdd55", "#ffe066"),
        "shape": "corn",
        "season": "夏秋",
        "days_hint": "约 20 时",
        "sell": 5,
        "use": "做饭·加工",
        "stable": False,
    },
    "apple": {
        "label": "苹果",
        "seed": "seed_apple",
        "item": "crop_apple",
        "colors": ("#88aa66", "#66aa44", "#cc6644", "#e84848"),
        "shape": "fruit",
        "season": "秋",
        "days_hint": "约 20 时",
        "sell": 6,
        "use": "水果·送礼",
        "stable": True,
    },
    "grape": {
        "label": "葡萄",
        "seed": "seed_grape",
        "item": "crop_grape",
        "colors": ("#668866", "#5577aa", "#7755aa", "#8844cc"),
        "shape": "vine",
        "season": "夏秋",
        "days_hint": "约 20 时",
        "sell": 6,
        "use": "藤蔓·果汁",
        "stable": False,
    },
    "rose": {
        "label": "玫瑰",
        "seed": "seed_rose",
        "item": "crop_rose",
        "colors": ("#66aa66", "#88cc88", "#ee6688", "#ff4477"),
        "shape": "flower",
        "season": "春夏",
        "days_hint": "约 20 时",
        "sell": 5,
        "use": "花卉·装饰",
        "stable": True,
    },
}

# 商店：金币买种子/木材
SHOP_PRICES: dict[str, int] = {
    "seed_wheat": 3,
    "seed_berry": 4,
    "seed_corn": 4,
    "seed_apple": 5,
    "seed_grape": 5,
    "seed_rose": 4,
    "wood": 5,
}

# 售出作物
SELL_PRICES: dict[str, int] = {
    "crop_wheat": 4,
    "crop_berry": 5,
    "crop_corn": 5,
    "crop_apple": 6,
    "crop_grape": 6,
    "crop_rose": 5,
    "fish": 6,
    "flower_cut": 2,
    "compost": 1,
    "jam_berry": 14,
    "flour": 10,
    "corn_flakes": 12,
}

# 常免：结构 / 通道 / 铺地 / 室外地物 / 画（布置模式不锁）
DEFAULT_FURNITURE_UNLOCK: frozenset[str] = frozenset(
    {
        "erase",
        "partition",
        "floor_wood",
        "floor_tile",
        "stairs_up",
        "stairs_down",
        "door",
        "window",
        "grass",
        "land",
        "water",
        "brick",
        "tree",
        "tree_pine",
        "tree_fruit",
        "tree_blossom",
        "rock",
        "flower",
        "fence",
        "bush",
        "path",
        "gift_art",
        "user_paint",
    }
)

# 需商店购买或合成解锁的室内家具
LOCKABLE_FURNITURE: frozenset[str] = frozenset(
    {
        "sofa",
        "tv",
        "coffee",
        "table",
        "chair",
        "carpet",
        "lamp",
        "plant",
        "vase",
        "bed",
        "wardrobe",
        "nightstand",
        "shelf",
        "stove",
        "sink",
        "fridge",
        "counter",
        "toilet",
        "bathtub",
        "basin",
    }
)

# 兼容旧名
CRAFT_ONLY_FURNITURE: frozenset[str] = LOCKABLE_FURNITURE

# 新手礼包：首次进家园解锁 + 物资
STARTER_FURNITURE: tuple[str, ...] = (
    "bed",
    "table",
    "chair",
    "lamp",
    "plant",
    "carpet",
    "vase",
    "nightstand",
)
STARTER_PACK_COINS = 40
STARTER_PACK_ITEMS: dict[str, int] = {
    "wood": 5,
    "seed_wheat": 3,
    "seed_berry": 2,
    "seed_corn": 2,
}

# 家具解锁商店价（金币）
FURNITURE_SHOP_PRICES: dict[str, int] = {
    "bed": 25,
    "table": 18,
    "chair": 10,
    "lamp": 12,
    "plant": 8,
    "carpet": 20,
    "vase": 10,
    "nightstand": 14,
    "sofa": 35,
    "tv": 40,
    "coffee": 16,
    "wardrobe": 28,
    "shelf": 22,
    "stove": 30,
    "sink": 24,
    "fridge": 38,
    "counter": 26,
    "toilet": 20,
    "bathtub": 36,
    "basin": 18,
}

FURNITURE_LABELS: dict[str, str] = {
    "bed": "床",
    "table": "桌子",
    "chair": "椅子",
    "lamp": "台灯",
    "plant": "盆栽",
    "carpet": "地毯",
    "vase": "花瓶",
    "nightstand": "床头柜",
    "sofa": "沙发",
    "tv": "电视柜",
    "coffee": "茶几",
    "wardrobe": "衣柜",
    "shelf": "柜子",
    "stove": "灶台",
    "sink": "水槽",
    "fridge": "冰箱",
    "counter": "料理台",
    "toilet": "马桶",
    "bathtub": "浴缸",
    "basin": "洗手台",
}

# 合成配方：id, label, costs{item:n}, result kind
# result: ("food", food_id) | ("furniture", kind) | ("item", item_id)
CRAFT_RECIPES: tuple[dict[str, Any], ...] = (
    {
        "id": "bread",
        "label": "烤面包",
        "costs": {"crop_wheat": 2},
        "result": ("food", "bread"),
        "desc": "2 小麦 → 面包",
    },
    {
        "id": "berry_snack",
        "label": "莓果点心",
        "costs": {"crop_berry": 2},
        "result": ("food", "berry"),
        "desc": "2 莓果 → 草莓",
    },
    {
        "id": "corn_food",
        "label": "烤玉米",
        "costs": {"crop_corn": 2},
        "result": ("food", "corn"),
        "desc": "2 玉米穗 → 玉米",
    },
    {
        "id": "juice",
        "label": "果汁",
        "costs": {"crop_berry": 1, "crop_wheat": 1},
        "result": ("food", "juice"),
        "desc": "莓果+小麦 → 果汁",
    },
    {
        "id": "craft_sofa",
        "label": "制作沙发",
        "costs": {"wood": 3, "crop_wheat": 1},
        "result": ("furniture", "sofa"),
        "desc": "3 木材+1 小麦 → 沙发",
    },
    {
        "id": "craft_shelf",
        "label": "制作柜子",
        "costs": {"wood": 2, "crop_berry": 1},
        "result": ("furniture", "shelf"),
        "desc": "2 木材+1 莓果 → 柜子",
    },
    {
        "id": "craft_table",
        "label": "制作桌子",
        "costs": {"wood": 2},
        "result": ("furniture", "table"),
        "desc": "2 木材 → 桌子",
    },
    {
        "id": "craft_chair",
        "label": "制作椅子",
        "costs": {"wood": 1},
        "result": ("furniture", "chair"),
        "desc": "1 木材 → 椅子",
    },
    {
        "id": "craft_bed",
        "label": "制作床",
        "costs": {"wood": 3, "crop_wheat": 2},
        "result": ("furniture", "bed"),
        "desc": "3 木材+2 小麦 → 床",
    },
    {
        "id": "craft_tv",
        "label": "制作电视柜",
        "costs": {"wood": 3, "crop_corn": 1},
        "result": ("furniture", "tv"),
        "desc": "3 木材+1 玉米 → 电视柜",
    },
    {
        "id": "craft_coffee",
        "label": "制作茶几",
        "costs": {"wood": 2},
        "result": ("furniture", "coffee"),
        "desc": "2 木材 → 茶几",
    },
    {
        "id": "craft_wardrobe",
        "label": "制作衣柜",
        "costs": {"wood": 3, "crop_berry": 1},
        "result": ("furniture", "wardrobe"),
        "desc": "3 木材+1 莓果 → 衣柜",
    },
    {
        "id": "craft_nightstand",
        "label": "制作床头柜",
        "costs": {"wood": 1},
        "result": ("furniture", "nightstand"),
        "desc": "1 木材 → 床头柜",
    },
    {
        "id": "craft_lamp",
        "label": "制作台灯",
        "costs": {"wood": 1, "crop_wheat": 1},
        "result": ("furniture", "lamp"),
        "desc": "1 木材+1 小麦 → 台灯",
    },
    {
        "id": "craft_carpet",
        "label": "制作地毯",
        "costs": {"crop_wheat": 2, "crop_berry": 1},
        "result": ("furniture", "carpet"),
        "desc": "2 小麦+1 莓果 → 地毯",
    },
    {
        "id": "craft_plant",
        "label": "制作盆栽",
        "costs": {"crop_berry": 1},
        "result": ("furniture", "plant"),
        "desc": "1 莓果 → 盆栽",
    },
    {
        "id": "craft_vase",
        "label": "制作花瓶",
        "costs": {"crop_rose": 1},
        "result": ("furniture", "vase"),
        "desc": "1 玫瑰 → 花瓶",
    },
    {
        "id": "craft_stove",
        "label": "制作灶台",
        "costs": {"wood": 2, "crop_corn": 1},
        "result": ("furniture", "stove"),
        "desc": "2 木材+1 玉米 → 灶台",
    },
    {
        "id": "craft_sink",
        "label": "制作水槽",
        "costs": {"wood": 2, "crop_wheat": 1},
        "result": ("furniture", "sink"),
        "desc": "2 木材+1 小麦 → 水槽",
    },
    {
        "id": "craft_fridge",
        "label": "制作冰箱",
        "costs": {"wood": 3, "crop_apple": 1},
        "result": ("furniture", "fridge"),
        "desc": "3 木材+1 苹果 → 冰箱",
    },
    {
        "id": "craft_counter",
        "label": "制作料理台",
        "costs": {"wood": 2, "crop_wheat": 1},
        "result": ("furniture", "counter"),
        "desc": "2 木材+1 小麦 → 料理台",
    },
    {
        "id": "craft_toilet",
        "label": "制作马桶",
        "costs": {"wood": 2},
        "result": ("furniture", "toilet"),
        "desc": "2 木材 → 马桶",
    },
    {
        "id": "craft_bathtub",
        "label": "制作浴缸",
        "costs": {"wood": 3, "crop_grape": 1},
        "result": ("furniture", "bathtub"),
        "desc": "3 木材+1 葡萄 → 浴缸",
    },
    {
        "id": "craft_basin",
        "label": "制作洗手台",
        "costs": {"wood": 1, "crop_wheat": 1},
        "result": ("furniture", "basin"),
        "desc": "1 木材+1 小麦 → 洗手台",
    },
)

FARM_DISCLAIMER = "经营：脱离原作"

# 工具键位：切换 / 确定使用
FARM_TOOL_KEYS: dict[str, str] = {
    "1": "till",
    "z": "till",
    "Z": "till",
    "2": "plant",
    "x": "plant",
    "X": "plant",
    "3": "water",
    "c": "water",
    "C": "water",
    "4": "harvest",
    "v": "harvest",
    "V": "harvest",
    "5": "chop",
    "b": "chop",
    "B": "chop",
    "6": "fish",
    "f": "fish",
    "F": "fish",
    "7": "pick",
    "g": "pick",
    "G": "pick",
}

FARM_TOOL_LABELS: dict[str, str] = {
    "till": "锄地",
    "plant": "播种",
    "water": "浇水",
    "harvest": "收获",
    "chop": "砍树",
    "fish": "钓鱼",
    "pick": "采花",
}

FARM_TOOL_HINTS: dict[str, str] = {
    "till": "先清上面，再锄两下草地→土地；枯萎可堆肥",
    "plant": "仅土地可种；可用「全种」",
    "water": "每天最多2次；浇后1小时成长×2；可用「全浇」",
    "harvest": "成熟可收；可用「全收」",
    "chop": "点树四周格子；掷骰砍够次数得木材",
    "fish": "点水面四周格子；上钩时再按一次",
    "pick": "采小花：可插花瓶，或在面板背包戴到头顶",
}

FARM_GUIDE_BODY = (
    "· 每天一小步：建议 3～5 次操作；「全浇/全收/全种」各只算 1 次。\n"
    "· 流程：锄地 → 播种 → 浇水 →（离线也会慢长）→ 收获。\n"
    "· 季节按登录天数推进；雨天自动润泽（不占浇水次数）。\n"
    "· 订单交付赚钱；小作坊投入原料，明天取成品；可摸喂牧场宠「团子」。\n"
    "· 不浇水不会直接死掉，只会变慢；太久干燥可锄掉堆肥回收。\n"
    "· 番茄钟完成会掉落「露水」可自动浇一格。"
)

FARM_GUIDE_SECTIONS: tuple[tuple[str, str, str], ...] = (
    ("🚪", "进入", "室外 →「经营」"),
    ("🚶", "移动", "WASD / 点格子"),
    ("1️⃣", "锄地", "先清上面；枯萎可堆肥"),
    ("2️⃣", "播种", "种在土地；可用全种"),
    ("3️⃣", "浇水", "每天有限次；可用全浇"),
    ("4️⃣", "收获", "成熟后收；可用全收"),
    ("💧", "露水", "番茄钟掉落；点露水浇一格"),
    ("5️⃣", "砍树", "在树四周格操作"),
    ("6️⃣", "钓鱼", "在水面四周格操作"),
    ("7️⃣", "采花", "可插花瓶；面板背包可戴/摘"),
    ("⏎", "执行", "数字键只切换工具；确定才执行"),
    ("🛒", "商店", "购买种子与木材"),
    ("⚒", "合成", "制作食物 / 解锁家具"),
)

SEED_START: dict[str, int] = {
    "seed_wheat": 4,
    "seed_berry": 2,
    "seed_corn": 2,
    "seed_apple": 1,
    "seed_grape": 1,
    "seed_rose": 1,
    "wood": 1,
    "flower_cut": 0,
    "fish": 0,
    "compost": 0,
    "dew_drop": 0,
    "jam_berry": 0,
    "flour": 0,
    "corn_flakes": 0,
}

# —— P1：季节（登录日推进）/ 雨天免浇 / 今日订单 / 小作坊 / 牧场宠 ——
SEASON_NAMES: tuple[str, ...] = ("春", "夏", "秋", "冬")
SEASON_SKY_TRIM: dict[str, str] = {
    "春": "#88c898",
    "夏": "#e8d090",
    "秋": "#e89868",
    "冬": "#c8d8e8",
}
# 现实 7 天 ≈ 家园一季（用登录天数累加）
DAYS_PER_SEASON = 7
# 雨天：日历日哈希落在这些余数
RAIN_DAY_MODS: frozenset[int] = frozenset({1, 4})

PROCESS_RECIPES: dict[str, dict[str, Any]] = {
    "jam": {
        "id": "jam",
        "label": "果酱小作坊",
        "input": "crop_berry",
        "output": "jam_berry",
        "desc": "1 莓果 → 明日取果酱",
    },
    "flour": {
        "id": "flour",
        "label": "石磨",
        "input": "crop_wheat",
        "output": "flour",
        "desc": "1 小麦 → 明日取面粉",
    },
    "flakes": {
        "id": "flakes",
        "label": "烘烤台",
        "input": "crop_corn",
        "output": "corn_flakes",
        "desc": "1 玉米 → 明日取玉米片",
    },
}

ORDER_POOL: tuple[dict[str, Any], ...] = (
    {"id": "o_wheat", "item": "crop_wheat", "need": 2, "pay": 14, "label": "邻居订单·小麦×2"},
    {"id": "o_berry", "item": "crop_berry", "need": 2, "pay": 16, "label": "邻居订单·莓果×2"},
    {"id": "o_corn", "item": "crop_corn", "need": 2, "pay": 16, "label": "邻居订单·玉米×2"},
    {"id": "o_jam", "item": "jam_berry", "need": 1, "pay": 20, "label": "茶会订单·果酱×1"},
    {"id": "o_flour", "item": "flour", "need": 1, "pay": 15, "label": "面包坊·面粉×1"},
    {"id": "o_fish", "item": "fish", "need": 1, "pay": 12, "label": "晚饭订单·鲜鱼×1"},
)

DEFAULT_RANCH_PET: dict[str, Any] = {
    "name": "团子",
    "kind": "sheep",
    "mood": 70,
    "last_pet_ymd": "",
    "last_feed_ymd": "",
}


def default_wallet() -> dict:
    return {
        "coins": 20,
        "items": dict(SEED_START),
        "last_daily_coin_ymd": "",
        "farm_action_ymd": "",
        "farm_actions": 0,
        "farm_offline_ymd": "",
        "last_farm_visit": 0.0,
        "farm_login_days": 0,
        "farm_login_ymd": "",
        "farm_orders_ymd": "",
        "farm_orders": [],
        "farm_processors": [],
        "ranch_pet": dict(DEFAULT_RANCH_PET),
    }


def normalize_wallet(raw: object) -> dict:
    base = default_wallet()
    if not isinstance(raw, dict):
        return base
    coins = max(0, int(raw.get("coins") or 0))
    items_in = raw.get("items") if isinstance(raw.get("items"), dict) else {}
    items: dict[str, int] = {}
    for k in ITEM_LABELS:
        items[k] = max(0, int(items_in.get(k, base["items"].get(k, 0))))
    # 保留未知键（向前兼容）
    for k, v in items_in.items():
        if k not in items:
            try:
                items[str(k)] = max(0, int(v))
            except Exception:
                pass
    last_day = str(raw.get("last_daily_coin_ymd") or "").strip()
    farm_day = str(raw.get("farm_action_ymd") or "").strip()
    farm_actions = max(0, int(raw.get("farm_actions") or 0))
    offline_day = str(raw.get("farm_offline_ymd") or "").strip()
    last_farm_visit = float(raw.get("last_farm_visit") or 0)
    pet_raw = raw.get("ranch_pet") if isinstance(raw.get("ranch_pet"), dict) else {}
    ranch = dict(DEFAULT_RANCH_PET)
    ranch["name"] = str(pet_raw.get("name") or ranch["name"])[:8] or "团子"
    ranch["kind"] = str(pet_raw.get("kind") or "sheep")
    ranch["mood"] = max(0, min(100, int(pet_raw.get("mood") or 70)))
    ranch["last_pet_ymd"] = str(pet_raw.get("last_pet_ymd") or "")
    ranch["last_feed_ymd"] = str(pet_raw.get("last_feed_ymd") or "")
    orders_raw = raw.get("farm_orders") if isinstance(raw.get("farm_orders"), list) else []
    orders: list[dict] = []
    for o in orders_raw[:4]:
        if isinstance(o, dict) and o.get("item"):
            orders.append(
                {
                    "id": str(o.get("id") or ""),
                    "item": str(o.get("item")),
                    "need": max(1, int(o.get("need") or 1)),
                    "pay": max(1, int(o.get("pay") or 1)),
                    "label": str(o.get("label") or "订单")[:24],
                    "done": bool(o.get("done")),
                }
            )
    procs_raw = raw.get("farm_processors") if isinstance(raw.get("farm_processors"), list) else []
    procs: list[dict] = []
    for p in procs_raw[:6]:
        if isinstance(p, dict) and p.get("recipe"):
            procs.append(
                {
                    "recipe": str(p.get("recipe")),
                    "ready_ymd": str(p.get("ready_ymd") or ""),
                    "claimed": bool(p.get("claimed")),
                }
            )
    return {
        "coins": coins,
        "items": items,
        "last_daily_coin_ymd": last_day,
        "farm_action_ymd": farm_day,
        "farm_actions": farm_actions,
        "farm_offline_ymd": offline_day,
        "last_farm_visit": last_farm_visit,
        "farm_login_days": max(0, int(raw.get("farm_login_days") or 0)),
        "farm_login_ymd": str(raw.get("farm_login_ymd") or "").strip(),
        "farm_orders_ymd": str(raw.get("farm_orders_ymd") or "").strip(),
        "farm_orders": orders,
        "farm_processors": procs,
        "ranch_pet": ranch,
    }


DAILY_LOGIN_COINS = 1


def try_claim_daily_login_coin(wallet: dict, *, today: str | None = None) -> tuple[bool, int]:
    """每天首次打开领取登录金币。返回 (是否领取成功, 当前持有)。"""
    import datetime as _dt

    day = today or _dt.datetime.now().strftime("%Y-%m-%d")
    if str(wallet.get("last_daily_coin_ymd") or "") == day:
        return False, int(wallet.get("coins") or 0)
    wallet["last_daily_coin_ymd"] = day
    total = grant_coins_to_wallet(wallet, DAILY_LOGIN_COINS)
    return True, total


def load_wallet(path: Path) -> dict:
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return normalize_wallet(data)
        except Exception:
            pass
    return default_wallet()


def save_wallet(path: Path, wallet: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = normalize_wallet(wallet)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def blank_farm(cols: int, rows: int) -> list[list[dict | None]]:
    return [[None for _ in range(cols)] for _ in range(rows)]


def _day_key(ts: float | None = None) -> str:
    import datetime as _dt

    return _dt.datetime.fromtimestamp(float(ts if ts is not None else time.time())).strftime("%Y-%m-%d")


def _normalize_plot(v: object) -> dict | None:
    if not isinstance(v, dict):
        return None
    crop = str(v.get("crop") or "").strip()
    if crop not in CROP_DEFS:
        return None
    planted = int(v.get("planted_at") or 0)
    now = time.time()
    if "maturity" in v:
        maturity = max(0.0, min(MATURITY_MAX, float(v.get("maturity") or 0)))
    else:
        # 旧档：按经过小时粗略迁移
        watered = int(v.get("watered") or 0)
        elapsed_h = max(0.0, (now - planted) / 3600.0) if planted else 0.0
        maturity = max(0.0, min(MATURITY_MAX, elapsed_h * MATURITY_PER_HOUR + watered * 8.0))
    return {
        "crop": crop,
        "planted_at": planted,
        "maturity": maturity,
        "last_tick": float(v.get("last_tick") or planted or now),
        "boost_until": float(v.get("boost_until") or 0),
        "water_day": str(v.get("water_day") or ""),
        "water_count": int(v.get("water_count") or 0),
        # 兼容旧 UI 字段
        "watered": int(v.get("water_count") or v.get("watered") or 0),
        "last_water_at": float(
            v.get("last_water_at")
            or (
                (float(v.get("boost_until") or 0) - WATER_BOOST_SEC)
                if float(v.get("boost_until") or 0) > 0
                else (planted or now)
            )
        ),
        "wilted": bool(v.get("wilted")),
    }


def normalize_farm(raw: object, cols: int, rows: int) -> list[list[dict | None]]:
    out = blank_farm(cols, rows)
    if not isinstance(raw, list):
        return out
    for y in range(min(rows, len(raw))):
        row = raw[y]
        if not isinstance(row, list):
            continue
        for x in range(min(cols, len(row))):
            out[y][x] = _normalize_plot(row[x])
    return out


def normalize_crafted_furniture(raw: object) -> list[str]:
    out: list[str] = []
    if not isinstance(raw, list):
        return out
    for v in raw:
        k = str(v or "").strip()
        if k and k not in out:
            out.append(k)
    return out


def furniture_unlocked(kind: str, crafted: list[str] | None) -> bool:
    k = str(kind or "").strip()
    if not k or k in DEFAULT_FURNITURE_UNLOCK:
        return True
    if k.startswith("cm:"):
        return True
    if k in (crafted or []):
        return True
    if k not in LOCKABLE_FURNITURE:
        return True
    return False


def unlock_furniture(crafted: list[str], kind: str) -> bool:
    """写入解锁列表；已有则 False。"""
    k = str(kind or "").strip()
    if not k:
        return False
    if k not in crafted:
        crafted.append(k)
        return True
    return False


def buy_furniture_unlock(wallet: dict, crafted: list[str], kind: str) -> tuple[bool, str]:
    price = FURNITURE_SHOP_PRICES.get(kind)
    if price is None:
        return False, "商店不卖该家具"
    if kind in (crafted or []) or kind in DEFAULT_FURNITURE_UNLOCK:
        return False, f"已拥有{FURNITURE_LABELS.get(kind, kind)}"
    coins = int(wallet.get("coins") or 0)
    if coins < price:
        return False, f"金币不足（需 {price}）"
    wallet["coins"] = coins - price
    unlock_furniture(crafted, kind)
    return True, f"已购入{FURNITURE_LABELS.get(kind, kind)}"


def grant_starter_home_pack(wallet: dict, crafted: list[str]) -> tuple[bool, str]:
    """发放新手家具礼包物资与解锁；调用方负责「仅一次」标记。"""
    newly: list[str] = []
    for k in STARTER_FURNITURE:
        if unlock_furniture(crafted, k):
            newly.append(FURNITURE_LABELS.get(k, k))
    wallet["coins"] = int(wallet.get("coins") or 0) + int(STARTER_PACK_COINS)
    items = wallet.setdefault("items", {})
    for iid, n in STARTER_PACK_ITEMS.items():
        items[iid] = int(items.get(iid, 0)) + int(n)
    names = "、".join(newly) if newly else "基础家具"
    return True, f"新手礼包：金币+{STARTER_PACK_COINS}，解锁{names}"


def advance_plot_maturity(plot: dict | None, *, now: float | None = None) -> None:
    """按真实时间推进成熟度（浇水加成 ×2；久不浇水变慢；极久标枯萎但不清空）。"""
    if not plot:
        return
    t_now = float(now if now is not None else time.time())
    last = float(plot.get("last_tick") or plot.get("planted_at") or t_now)
    if t_now <= last:
        plot["last_tick"] = t_now
        return
    if plot.get("wilted"):
        plot["last_tick"] = t_now
        return
    maturity = float(plot.get("maturity") or 0.0)
    boost_until = float(plot.get("boost_until") or 0.0)
    last_water = float(plot.get("last_water_at") or plot.get("planted_at") or last)
    rate = MATURITY_PER_HOUR / 3600.0
    t0 = last
    while t0 < t_now and maturity < MATURITY_MAX:
        if t0 < boost_until:
            seg = min(t_now, boost_until)
            maturity += (seg - t0) * rate * 2.0
            t0 = seg
            continue
        dry_for = t0 - last_water
        mult = DRY_SLOW_RATE if dry_for >= DRY_SLOW_AFTER_SEC else 1.0
        # 整段到现在（干燥减速时不再细分）
        maturity += (t_now - t0) * rate * mult
        t0 = t_now
    plot["maturity"] = max(0.0, min(MATURITY_MAX, maturity))
    plot["last_tick"] = t_now
    # 未成熟且极久未浇 → 枯萎（可堆肥，不惩罚清空）
    if maturity < MATURITY_MAX - 1e-6 and (t_now - last_water) >= WILT_AFTER_SEC:
        plot["wilted"] = True


def plot_soil_state(plot: dict | None, *, now: float | None = None) -> str:
    """土壤状态：empty / wilted / ready / wet / dry。"""
    if not plot:
        return "empty"
    t_now = float(now if now is not None else time.time())
    advance_plot_maturity(plot, now=t_now)
    if plot.get("wilted"):
        return "wilted"
    if plot_ready(plot, now=t_now):
        return "ready"
    if plot_boost_active(plot, now=t_now):
        return "wet"
    return "dry"


def crop_card_text(crop_id: str) -> str:
    meta = CROP_DEFS.get(crop_id) or {}
    if not meta:
        return crop_id
    return (
        f"{meta.get('label', crop_id)} · {meta.get('season', '常')} · "
        f"{meta.get('days_hint', '')} · 卖{meta.get('sell', '?')} · {meta.get('use', '')}"
    )


def farm_action_count(wallet: dict, *, today: str | None = None) -> int:
    day = today or _day_key()
    if str(wallet.get("farm_action_ymd") or "") != day:
        return 0
    return max(0, int(wallet.get("farm_actions") or 0))


def can_spend_farm_action(wallet: dict, *, today: str | None = None) -> tuple[bool, str]:
    """硬上限：超过 HARD 次则拦；软上限仅提示（由 UI 决定）。"""
    n = farm_action_count(wallet, today=today)
    if n >= DAILY_ACTION_HARD:
        return False, f"今天小事已做满 {DAILY_ACTION_HARD} 件，明天再来～"
    if n >= DAILY_ACTION_SOFT:
        return True, f"今日已做 {n}/{DAILY_ACTION_SOFT} 件（还可继续，别肝坏了）"
    return True, f"今日小事 {n}/{DAILY_ACTION_SOFT}"


def spend_farm_action(wallet: dict, *, n: int = 1, today: str | None = None) -> int:
    day = today or _day_key()
    if str(wallet.get("farm_action_ymd") or "") != day:
        wallet["farm_action_ymd"] = day
        wallet["farm_actions"] = 0
    wallet["farm_actions"] = max(0, int(wallet.get("farm_actions") or 0)) + max(1, int(n))
    return int(wallet["farm_actions"])


def today_farm_quest(farm: list[list[dict | None]], wallet: dict) -> str:
    """短句今日推荐（新手引导用）。"""
    dry = ready = wilted = empty_land = planted = 0
    for row in farm:
        if not isinstance(row, list):
            continue
        for plot in row:
            if not isinstance(plot, dict):
                empty_land += 1
                continue
            planted += 1
            st = plot_soil_state(plot)
            if st == "dry":
                dry += 1
            elif st == "ready":
                ready += 1
            elif st == "wilted":
                wilted += 1
    if wilted:
        return f"今日推荐：把 {wilted} 格枯萎作物锄成堆肥"
    if ready:
        return f"今日推荐：收菜 {ready} 格（可用「全收」）"
    if dry:
        return f"今日推荐：浇水 {min(dry, 5)} 格（可用「全浇」）"
    items = wallet.get("items") or {}
    seeds = sum(int(items.get(s, 0)) for s in SEED_TO_CROP)
    if seeds > 0 and empty_land > 0:
        return "今日推荐：种一格稳产菜（麦/莓）"
    if seeds <= 0:
        return "今日推荐：去商店买点麦种"
    return "今日推荐：摸宠物 / 摆一件装饰也很好"


def claim_offline_garden(
    farm: list[list[dict | None]],
    wallet: dict,
    *,
    now: float | None = None,
) -> tuple[bool, str]:
    """打开经营时：推进成长 + 每日一次离线微收益（自动浇少量干地 + 少量金币）。"""
    t_now = float(now if now is not None else time.time())
    last = float(wallet.get("last_farm_visit") or 0)
    # 先推进（离线成长有上限感：过长间隔仍 advance，但奖励封顶）
    if last > 0:
        gap_h = min(OFFLINE_GROW_CAP_HOURS, max(0.0, (t_now - last) / 3600.0))
        # advance_farm 本身按真实时间；此处只控制「奖励」
        advance_farm(farm, now=t_now)
        day = _day_key(t_now)
        already = str(wallet.get("farm_offline_ymd") or "") == day
        wallet["last_farm_visit"] = t_now
        if already or gap_h < 1.5:
            return False, ""
        watered = 0
        for row in farm:
            if not isinstance(row, list):
                continue
            for plot in row:
                if not isinstance(plot, dict) or plot.get("wilted"):
                    continue
                if plot_ready(plot, now=t_now):
                    continue
                if plot_boost_active(plot, now=t_now):
                    continue
                if watered >= OFFLINE_AUTO_WATER_MAX:
                    break
                plot["boost_until"] = t_now + WATER_BOOST_SEC * 0.5
                plot["last_water_at"] = t_now
                watered += 1
            if watered >= OFFLINE_AUTO_WATER_MAX:
                break
        coins = 0
        if gap_h >= 4.0:
            coins = min(OFFLINE_BONUS_COIN_MAX, 1 + int(gap_h // 8))
            coins += ranch_mood_offline_bonus(wallet)
            grant_coins_to_wallet(wallet, coins)
        season = farm_season_state(wallet, today=day)
        if season.get("raining"):
            apply_rain_blessing(farm, now=t_now)
        wallet["farm_offline_ymd"] = day
        bits = [f"离线约 {gap_h:.0f} 时"]
        if watered:
            bits.append(f"露水自动浇了 {watered} 格")
        if coins:
            bits.append(f"金币+{coins}")
        if season.get("raining"):
            bits.append("雨天润泽")
        return True, " · ".join(bits)
    wallet["last_farm_visit"] = t_now
    advance_farm(farm, now=t_now)
    return False, ""


def grant_pomodoro_farm_drop(wallet: dict) -> str:
    """番茄完成 → 家园掉落露水（可当次自动浇，或攒着）。"""
    items = wallet.setdefault("items", {})
    items["dew_drop"] = int(items.get("dew_drop", 0)) + 1
    return "番茄完成！家园掉落露水 ×1（经营里可用露水浇一格）"


def try_use_dew_drop(farm: list[list[dict | None]], wallet: dict) -> tuple[bool, str]:
    """消耗 1 露水：浇最干的一格（不占每日浇水次数）。"""
    items = wallet.setdefault("items", {})
    if int(items.get("dew_drop", 0)) <= 0:
        return False, "没有露水"
    target = None
    for row in farm:
        if not isinstance(row, list):
            continue
        for plot in row:
            if not isinstance(plot, dict) or plot.get("wilted"):
                continue
            if plot_ready(plot) or plot_boost_active(plot):
                continue
            target = plot
            break
        if target is not None:
            break
    if target is None:
        return False, "没有需要浇的干地"
    items["dew_drop"] = int(items.get("dew_drop", 0)) - 1
    now = time.time()
    advance_plot_maturity(target, now=now)
    target["boost_until"] = now + WATER_BOOST_SEC
    target["last_water_at"] = now
    return True, "用露水浇了一格！"


def batch_water(farm: list[list[dict | None]], *, raining: bool = False) -> tuple[int, str]:
    n = 0
    for y, row in enumerate(farm):
        if not isinstance(row, list):
            continue
        for x, _plot in enumerate(row):
            ok, _ = try_water(farm, x, y, raining=raining)
            if ok:
                n += 1
    if n <= 0:
        return 0, "没有可浇的地"
    if raining:
        return n, f"雨天全润：{n} 格"
    return n, f"全浇完成：{n} 格"


def batch_harvest(farm: list[list[dict | None]], wallet: dict) -> tuple[int, str]:
    n = 0
    for y, row in enumerate(farm):
        if not isinstance(row, list):
            continue
        for x in range(len(row)):
            ok, _ = try_harvest(farm, wallet, x, y)
            if ok:
                n += 1
    if n <= 0:
        return 0, "没有成熟作物"
    return n, f"全收完成：{n} 格"


def batch_plant(
    farm: list[list[dict | None]],
    wallet: dict,
    outdoor_tiles: list,
    seed_id: str,
    *,
    cell_kind,
    limit: int = 8,
) -> tuple[int, str]:
    if seed_id not in SEED_TO_CROP:
        return 0, "请先选择种子"
    n = 0
    for y, row in enumerate(farm):
        if not isinstance(row, list):
            continue
        for x in range(len(row)):
            if n >= limit:
                break
            ok, _ = try_plant(farm, wallet, outdoor_tiles, x, y, seed_id, cell_kind=cell_kind)
            if ok:
                n += 1
        if n >= limit:
            break
    if n <= 0:
        return 0, "没有空土地或种子不足"
    return n, f"全种完成：{n} 格"


def advance_farm(farm: list[list[dict | None]], *, now: float | None = None) -> None:
    t_now = float(now if now is not None else time.time())
    for row in farm:
        if not isinstance(row, list):
            continue
        for plot in row:
            if isinstance(plot, dict):
                advance_plot_maturity(plot, now=t_now)


def plot_stage(plot: dict | None, *, now: float | None = None) -> int:
    """0..3 仅用于上色阶段。"""
    if not plot:
        return -1
    advance_plot_maturity(plot, now=now)
    prog = float(plot.get("maturity") or 0.0) / MATURITY_MAX
    if prog >= 1.0:
        return 3
    if prog >= 0.66:
        return 2
    if prog >= 0.33:
        return 1
    return 0


def plot_progress(plot: dict | None, *, now: float | None = None) -> float:
    """成长进度 0.0..1.0（成熟为 1）。"""
    if not plot:
        return 0.0
    advance_plot_maturity(plot, now=now)
    return max(0.0, min(1.0, float(plot.get("maturity") or 0.0) / MATURITY_MAX))


def plot_ready(plot: dict | None, *, now: float | None = None) -> bool:
    if not plot:
        return False
    advance_plot_maturity(plot, now=now)
    return float(plot.get("maturity") or 0.0) >= MATURITY_MAX - 1e-6


def plot_color(plot: dict | None, *, now: float | None = None) -> str:
    if not plot:
        return "#5a4830"
    if plot.get("wilted"):
        return "#6a5a48"
    crop = str(plot.get("crop") or "")
    meta = CROP_DEFS.get(crop)
    if not meta:
        return "#5a4830"
    colors = meta["colors"]
    st = plot_stage(plot, now=now)
    return colors[min(st, len(colors) - 1)]


def paint_crop_plot(canvas, plot: dict | None, px: int, py: int, tile: int, *, now: float | None = None) -> None:
    """在格子上画幼苗→成熟造型（替代单纯色点）。"""
    if not plot:
        return
    cx = px + tile // 2
    cy = py + tile // 2 + 2
    if plot.get("wilted"):
        canvas.create_line(cx - 4, cy + 4, cx, cy - 2, fill="#8a7050", width=2)
        canvas.create_oval(cx - 3, cy - 6, cx + 3, cy, fill="#a09070", outline="")
        return
    crop = str(plot.get("crop") or "")
    meta = CROP_DEFS.get(crop) or {}
    shape = str(meta.get("shape") or "grain")
    colors = meta.get("colors") or ("#88aa66", "#88aa66", "#88aa66", "#c8e070")
    st = plot_stage(plot, now=now)
    col = colors[min(st, len(colors) - 1)]
    stem = "#3a7a3a"
    # 0 幼苗 / 1 抽叶 / 2 含苞 / 3 成熟
    if st <= 0:
        canvas.create_oval(cx - 2, cy + 4, cx + 2, cy + 8, fill="#5a4030", outline="")
        canvas.create_line(cx, cy + 4, cx, cy - 2, fill=stem, width=1)
        canvas.create_oval(cx - 3, cy - 4, cx + 1, cy, fill="#66cc66", outline="")
        canvas.create_oval(cx - 1, cy - 4, cx + 3, cy, fill="#88ee88", outline="")
        return
    if st == 1:
        canvas.create_line(cx, cy + 6, cx, cy - 6, fill=stem, width=2)
        canvas.create_oval(cx - 6, cy - 4, cx - 1, cy + 2, fill="#66aa55", outline="")
        canvas.create_oval(cx + 1, cy - 4, cx + 6, cy + 2, fill="#77bb66", outline="")
        canvas.create_oval(cx - 2, cy - 8, cx + 2, cy - 4, fill=col, outline="")
        return
    if st == 2:
        canvas.create_line(cx, cy + 8, cx, cy - 8, fill=stem, width=2)
        canvas.create_oval(cx - 7, cy - 2, cx - 1, cy + 4, fill="#55aa44", outline="")
        canvas.create_oval(cx + 1, cy - 2, cx + 7, cy + 4, fill="#66bb55", outline="")
        canvas.create_oval(cx - 4, cy - 10, cx + 4, cy - 2, fill=col, outline="")
        return
    # 成熟：按形状区分
    if shape == "grain":
        canvas.create_line(cx, cy + 8, cx, cy - 10, fill="#88a040", width=2)
        for i, ox in enumerate((-4, -1, 2, 5)):
            canvas.create_oval(cx + ox - 2, cy - 12 + i, cx + ox + 2, cy - 6 + i, fill=col, outline="")
    elif shape == "berry":
        canvas.create_line(cx, cy + 8, cx, cy - 4, fill=stem, width=2)
        canvas.create_oval(cx - 7, cy - 2, cx + 7, cy + 8, fill="#44aa55", outline="#228833")
        for ox, oy in ((-3, -2), (3, -2), (0, 2), (-2, 3), (2, 3)):
            canvas.create_oval(cx + ox - 2, cy + oy - 2, cx + ox + 2, cy + oy + 2, fill=col, outline="")
    elif shape == "corn":
        canvas.create_line(cx, cy + 8, cx, cy - 8, fill=stem, width=2)
        canvas.create_oval(cx - 8, cy - 2, cx - 2, cy + 6, fill="#55aa44", outline="")
        canvas.create_oval(cx + 2, cy - 2, cx + 8, cy + 6, fill="#55aa44", outline="")
        canvas.create_oval(cx - 4, cy - 12, cx + 4, cy + 2, fill=col, outline="#ccaa33")
        canvas.create_line(cx, cy - 12, cx, cy - 16, fill="#66aa44", width=1)
    elif shape == "fruit":
        canvas.create_line(cx, cy + 8, cx, cy - 2, fill="#6a4a28", width=2)
        canvas.create_oval(cx - 8, cy - 10, cx + 8, cy + 2, fill="#3a9a3a", outline="#2a7a2a")
        canvas.create_oval(cx - 4, cy - 4, cx + 2, cy + 4, fill=col, outline="#aa3030")
        canvas.create_oval(cx + 1, cy - 6, cx + 6, cy, fill=_shade_crop(col), outline="")
    elif shape == "vine":
        canvas.create_line(cx - 8, cy + 6, cx + 8, cy - 8, fill=stem, width=2)
        canvas.create_line(cx - 6, cy + 8, cx + 6, cy - 4, fill="#55aa44", width=1)
        for ox, oy in ((-4, 2), (0, -2), (4, -6), (2, 4)):
            canvas.create_oval(cx + ox - 3, cy + oy - 3, cx + ox + 3, cy + oy + 3, fill=col, outline="#553388")
    elif shape == "flower":
        canvas.create_line(cx, cy + 8, cx, cy - 4, fill=stem, width=2)
        canvas.create_oval(cx - 5, cy + 2, cx - 1, cy + 8, fill="#44aa55", outline="")
        for ox, oy in ((-5, -4), (5, -4), (0, -8), (-4, 2), (4, 2)):
            canvas.create_oval(cx + ox - 3, cy + oy - 3, cx + ox + 3, cy + oy + 3, fill=col, outline="")
        canvas.create_oval(cx - 2, cy - 4, cx + 2, cy, fill="#ffe088", outline="")
    else:
        canvas.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill=col, outline="")


def _shade_crop(hex_color: str) -> str:
    c = (hex_color or "#888888").lstrip("#")
    if len(c) != 6:
        return "#aa6666"
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    r = min(255, int(r * 1.15 + 20))
    g = min(255, int(g * 1.05))
    b = min(255, int(b * 0.9))
    return f"#{r:02x}{g:02x}{b:02x}"


def plot_boost_active(plot: dict | None, *, now: float | None = None) -> bool:
    if not plot:
        return False
    t_now = float(now if now is not None else time.time())
    return float(plot.get("boost_until") or 0) > t_now


def can_farm_at(outdoor_tiles: list, x: int, y: int, cell_blocks) -> bool:
    """无实体阻挡才可经营（允许草地等非 solid）。"""
    if y < 0 or x < 0 or y >= len(outdoor_tiles) or x >= len(outdoor_tiles[0]):
        return False
    return not cell_blocks(outdoor_tiles, x, y)


def _tile_key(x: int, y: int) -> str:
    return f"{int(x)},{int(y)}"


def try_till(
    farm: list[list[dict | None]],
    outdoor_tiles: list,
    x: int,
    y: int,
    *,
    till_hits: dict,
    cell_kind,
    try_place,
    clear_at,
    wallet: dict | None = None,
) -> tuple[bool, str]:
    """锄地：枯萎→堆肥；先除掉上面小花/灌木；草地锄两下变土地。"""
    if y < 0 or x < 0 or y >= len(farm) or x >= len(farm[0]):
        return False, "超出范围"
    plot = farm[y][x]
    if isinstance(plot, dict) and plot.get("wilted") and wallet is not None:
        farm[y][x] = None
        items = wallet.setdefault("items", {})
        items["compost"] = int(items.get("compost", 0)) + 1
        till_hits.pop(_tile_key(x, y), None)
        return True, "枯萎作物已堆肥回收（无重罚）"
    farm[y][x] = None
    kind = cell_kind(outdoor_tiles, x, y)
    # 上面的小花/灌木先清掉
    if kind in ("flower", "bush"):
        clear_at(outdoor_tiles, x, y)
        try_place(outdoor_tiles, "grass", x, y)
        till_hits.pop(_tile_key(x, y), None)
        return True, "已除掉上面的东西"
    if kind == "land":
        till_hits.pop(_tile_key(x, y), None)
        return True, "土地已整理，可以播种"
    if kind == "grass" or kind is None:
        key = _tile_key(x, y)
        hits = int(till_hits.get(key) or 0) + 1
        if hits >= 2:
            try_place(outdoor_tiles, "land", x, y)
            till_hits.pop(key, None)
            return True, "草地已翻成土地，可以播种了"
        till_hits[key] = hits
        return True, "再锄一下，草地就会变成土地"
    return False, "这里不能锄成田"


def try_plant(
    farm: list[list[dict | None]],
    wallet: dict,
    outdoor_tiles: list,
    x: int,
    y: int,
    seed_id: str,
    *,
    cell_kind,
) -> tuple[bool, str]:
    if seed_id not in SEED_TO_CROP:
        return False, "请先选择种子"
    if y < 0 or x < 0 or y >= len(farm) or x >= len(farm[0]):
        return False, "超出范围"
    if cell_kind(outdoor_tiles, x, y) != "land":
        return False, "请先把草地锄成土地（锄两下）"
    if farm[y][x] is not None:
        return False, "这里已有作物"
    items = wallet.setdefault("items", {})
    if int(items.get(seed_id, 0)) <= 0:
        return False, f"{ITEM_LABELS.get(seed_id, seed_id)}不足"
    items[seed_id] = int(items.get(seed_id, 0)) - 1
    now = int(time.time())
    farm[y][x] = {
        "crop": SEED_TO_CROP[seed_id],
        "planted_at": now,
        "maturity": 0.0,
        "last_tick": float(now),
        "boost_until": 0.0,
        "water_day": "",
        "water_count": 0,
        "watered": 0,
        "last_water_at": float(now),
        "wilted": False,
    }
    return True, "已播种"


def try_water(farm: list[list[dict | None]], x: int, y: int, *, raining: bool = False) -> tuple[bool, str]:
    if y < 0 or x < 0 or y >= len(farm) or x >= len(farm[0]):
        return False, "超出范围"
    plot = farm[y][x]
    if not plot:
        return False, "空地无需浇水"
    now = time.time()
    advance_plot_maturity(plot, now=now)
    if plot.get("wilted"):
        return False, "已枯萎，请用锄地堆肥回收"
    if plot_ready(plot, now=now):
        return False, "已成熟，请收获"
    if raining:
        # 雨天：免费浇透，不占每日次数
        plot["boost_until"] = now + WATER_BOOST_SEC
        plot["last_water_at"] = now
        plot["wilted"] = False
        return True, "雨天润泽！成长加快（不占浇水次数）"
    day = _day_key(now)
    if str(plot.get("water_day") or "") != day:
        plot["water_day"] = day
        plot["water_count"] = 0
    count = int(plot.get("water_count") or 0)
    if count >= WATER_MAX_PER_DAY:
        return False, "今天已经浇过两次了"
    plot["water_count"] = count + 1
    plot["watered"] = plot["water_count"]
    plot["boost_until"] = now + WATER_BOOST_SEC
    plot["last_water_at"] = now
    plot["wilted"] = False
    return True, "浇水！一小时内成长速度×2"


def try_harvest(farm: list[list[dict | None]], wallet: dict, x: int, y: int) -> tuple[bool, str]:
    if y < 0 or x < 0 or y >= len(farm) or x >= len(farm[0]):
        return False, "超出范围"
    plot = farm[y][x]
    if not plot:
        return False, "没有作物"
    if plot.get("wilted"):
        return False, "已枯萎，请用锄地堆肥"
    if not plot_ready(plot):
        return False, "还没成熟"
    crop = str(plot.get("crop") or "")
    meta = CROP_DEFS.get(crop)
    if not meta:
        farm[y][x] = None
        return False, "未知作物"
    item_id = str(meta["item"])
    items = wallet.setdefault("items", {})
    items[item_id] = int(items.get(item_id, 0)) + 1
    farm[y][x] = None
    return True, f"收获了{ITEM_LABELS.get(item_id, item_id)}"


def try_chop_start_or_hit(
    outdoor_tiles: list,
    wallet: dict,
    x: int,
    y: int,
    *,
    chop_jobs: dict,
    tree_regrow: list,
    cell_kind,
    clear_at,
    try_place,
    rng,
) -> tuple[bool, str, dict | None]:
    """砍树：首次对树掷骰决定次数；砍完得木材，48h 后可再生。"""
    kind = cell_kind(outdoor_tiles, x, y)
    key = _tile_key(x, y)
    job = chop_jobs.get(key) if isinstance(chop_jobs.get(key), dict) else None
    if kind not in TREE_KINDS and not job:
        return False, "这里没有可砍的树（需树木素材）", None
    tree_kind = str(kind if kind in TREE_KINDS else (job or {}).get("kind") or "tree")
    if kind in TREE_KINDS and not job:
        need = int(rng.randint(CHOP_DICE_MIN, CHOP_DICE_MAX))
        chop_jobs[key] = {"need": need, "done": 1, "x": int(x), "y": int(y), "kind": tree_kind}
        if need <= 1:
            clear_at(outdoor_tiles, x, y)
            try_place(outdoor_tiles, "grass", x, y)
            chop_jobs.pop(key, None)
            items = wallet.setdefault("items", {})
            items["wood"] = int(items.get("wood", 0)) + 1
            tree_regrow.append(
                {"x": int(x), "y": int(y), "ready_at": time.time() + TREE_REGROW_SEC, "kind": tree_kind}
            )
            return True, f"掷出 {need}！一斧砍倒，木材+1（48h可再生）", {"dice": need}
        return True, f"掷出 {need}！砍树 1/{need}", {"dice": need}
    assert job is not None
    job["done"] = int(job.get("done") or 0) + 1
    need = max(1, int(job.get("need") or 1))
    done = int(job["done"])
    if done < need:
        return True, f"砍树 {done}/{need}", None
    # 砍倒
    clear_at(outdoor_tiles, x, y)
    try_place(outdoor_tiles, "grass", x, y)
    chop_jobs.pop(key, None)
    items = wallet.setdefault("items", {})
    items["wood"] = int(items.get("wood", 0)) + 1
    tree_regrow.append(
        {
            "x": int(x),
            "y": int(y),
            "ready_at": time.time() + TREE_REGROW_SEC,
            "kind": str(job.get("kind") or tree_kind or "tree"),
        }
    )
    return True, "树倒了！木材+1（48小时后可再生）", None


def process_tree_regrow(
    outdoor_tiles: list,
    tree_regrow: list,
    *,
    cell_kind,
    try_place,
    now: float | None = None,
) -> int:
    """到期的树重新长出来。返回再生数量。"""
    t_now = float(now if now is not None else time.time())
    remain: list = []
    n = 0
    for item in list(tree_regrow):
        if not isinstance(item, dict):
            continue
        ready = float(item.get("ready_at") or 0)
        x, y = int(item.get("x") or 0), int(item.get("y") or 0)
        grow_kind = str(item.get("kind") or "tree")
        if grow_kind not in TREE_KINDS:
            grow_kind = "tree"
        if ready > t_now:
            remain.append(item)
            continue
        if cell_kind(outdoor_tiles, x, y) in (None, "grass", "land", "path", "brick"):
            try_place(outdoor_tiles, grow_kind, x, y)
            n += 1
        else:
            # 格上有东西则稍后再试
            item["ready_at"] = t_now + 3600
            remain.append(item)
    tree_regrow[:] = remain
    return n


def try_pick_flower(
    outdoor_tiles: list,
    wallet: dict,
    x: int,
    y: int,
    *,
    cell_kind,
    clear_at,
    try_place,
) -> tuple[bool, str]:
    if cell_kind(outdoor_tiles, x, y) != "flower":
        return False, "这里没有小花"
    clear_at(outdoor_tiles, x, y)
    try_place(outdoor_tiles, "grass", x, y)
    items = wallet.setdefault("items", {})
    items["flower_cut"] = int(items.get("flower_cut", 0)) + 1
    return True, "采到花了！可插花瓶，或面板背包戴头顶"


def try_put_flower_in_vase(
    indoor_tiles: list,
    wallet: dict,
    x: int,
    y: int,
    *,
    cell_kind,
    make_filled_vase,
    vase_filled=None,
) -> tuple[bool, str]:
    if cell_kind(indoor_tiles, x, y) != "vase":
        return False, "请点在花瓶上"
    if callable(vase_filled) and vase_filled(indoor_tiles, x, y):
        return False, "花瓶里已有花，先拔出来再插"
    items = wallet.setdefault("items", {})
    if int(items.get("flower_cut", 0)) <= 0:
        return False, "还没有采下的花"
    items["flower_cut"] = int(items.get("flower_cut", 0)) - 1
    make_filled_vase(indoor_tiles, x, y)
    return True, "花已插进花瓶"


def try_take_flower_from_vase(
    indoor_tiles: list,
    wallet: dict,
    x: int,
    y: int,
    *,
    cell_kind,
    vase_filled,
    empty_vase,
    vase_color: str | None = None,
) -> tuple[bool, str]:
    """从已插花的花瓶拔出，花回背包。"""
    if cell_kind(indoor_tiles, x, y) != "vase":
        return False, "请点在花瓶上"
    if not vase_filled(indoor_tiles, x, y):
        return False, "花瓶里没有花"
    if not empty_vase(indoor_tiles, x, y, color=vase_color):
        return False, "拔花失败"
    items = wallet.setdefault("items", {})
    items["flower_cut"] = int(items.get("flower_cut", 0)) + 1
    return True, "已拔出花，放回背包"


def find_adjacent_water(tiles: list, x: int, y: int, cell_kind) -> tuple[int, int] | None:
    """四邻中找一格水面；用于岸边钓鱼。"""
    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        nx, ny = int(x) + dx, int(y) + dy
        try:
            if cell_kind(tiles, nx, ny) == "water":
                return nx, ny
        except Exception:
            continue
    return None


def find_adjacent_tree(
    tiles: list,
    x: int,
    y: int,
    cell_kind,
    chop_jobs: dict | None = None,
) -> tuple[int, int] | None:
    """四邻中找一棵树；优先正在砍的那棵。"""
    found: list[tuple[int, int]] = []
    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        nx, ny = int(x) + dx, int(y) + dy
        try:
            if cell_kind(tiles, nx, ny) in TREE_KINDS:
                found.append((nx, ny))
        except Exception:
            continue
    if not found:
        return None
    if isinstance(chop_jobs, dict):
        for nx, ny in found:
            if isinstance(chop_jobs.get(_tile_key(nx, ny)), dict):
                return nx, ny
    return found[0]


def roll_fish_result(rng) -> tuple[bool, str, str]:
    """返回 (成功?, 提示, 奖励类型 coin|fish|fail)。"""
    r = rng.random()
    if r < 0.45:
        return True, "钓到鲜鱼！", "fish"
    if r < 0.7:
        return True, "钓到小东西，换成金币 +2", "coin"
    return False, "鱼跑了……", "fail"


def buy_item(wallet: dict, item_id: str, amount: int = 1) -> tuple[bool, str]:
    price = SHOP_PRICES.get(item_id)
    if price is None:
        return False, "无法购买"
    amount = max(1, int(amount))
    cost = price * amount
    coins = int(wallet.get("coins") or 0)
    if coins < cost:
        return False, f"金币不足（需 {cost}）"
    wallet["coins"] = coins - cost
    items = wallet.setdefault("items", {})
    items[item_id] = int(items.get(item_id, 0)) + amount
    return True, f"购入 {ITEM_LABELS.get(item_id, item_id)} ×{amount}"


def sell_item(wallet: dict, item_id: str, amount: int = 1) -> tuple[bool, str]:
    price = SELL_PRICES.get(item_id)
    if price is None:
        return False, "不可出售"
    amount = max(1, int(amount))
    items = wallet.setdefault("items", {})
    have = int(items.get(item_id, 0))
    if have < amount:
        return False, "数量不足"
    items[item_id] = have - amount
    wallet["coins"] = int(wallet.get("coins") or 0) + price * amount
    return True, f"售出 +{price * amount} 金币"


def can_afford_recipe(wallet: dict, recipe: dict) -> bool:
    items = wallet.get("items") if isinstance(wallet.get("items"), dict) else {}
    costs = recipe.get("costs") or {}
    for k, n in costs.items():
        if int(items.get(k, 0)) < int(n):
            return False
    return True


def try_craft(wallet: dict, crafted: list[str], recipe_id: str) -> tuple[bool, str, Any]:
    """
    成功返回 (True, msg, result_payload)
    result_payload: ("food", id) | ("furniture", kind) | None
    """
    recipe = next((r for r in CRAFT_RECIPES if r["id"] == recipe_id), None)
    if recipe is None:
        return False, "未知配方", None
    if not can_afford_recipe(wallet, recipe):
        return False, "材料不足", None
    kind_t, out_id = recipe["result"]
    if kind_t == "furniture" and out_id in crafted:
        return False, "已解锁该家具", None
    items = wallet.setdefault("items", {})
    for k, n in (recipe.get("costs") or {}).items():
        items[k] = int(items.get(k, 0)) - int(n)
        if items[k] <= 0:
            items[k] = 0
    if kind_t == "furniture":
        if out_id in crafted:
            return False, "已解锁该家具", None
        unlock_furniture(crafted, out_id)
        label = FURNITURE_LABELS.get(out_id, out_id)
        return True, f"已制作家具：{label}", ("furniture", out_id)
    if kind_t == "food":
        return True, f"合成食物：{out_id}", ("food", out_id)
    if kind_t == "item":
        items[out_id] = int(items.get(out_id, 0)) + 1
        return True, f"获得 {ITEM_LABELS.get(out_id, out_id)}", ("item", out_id)
    return False, "配方无效", None


def grant_coins_to_wallet(wallet: dict, n: int) -> int:
    n = max(0, int(n))
    wallet["coins"] = int(wallet.get("coins") or 0) + n
    return int(wallet["coins"])


def spend_coins_from_wallet(wallet: dict, n: int) -> bool:
    n = max(0, int(n))
    coins = int(wallet.get("coins") or 0)
    if coins < n:
        return False
    wallet["coins"] = coins - n
    return True


def item_summary(wallet: dict, *, limit: int = 6) -> str:
    items = wallet.get("items") if isinstance(wallet.get("items"), dict) else {}
    parts = []
    for k, label in ITEM_LABELS.items():
        n = int(items.get(k, 0))
        if n > 0:
            parts.append(f"{label}{n}")
        if len(parts) >= limit:
            break
    return " ".join(parts) if parts else "空"


def touch_farm_login_day(wallet: dict, *, today: str | None = None) -> int:
    """进入经营时累计登录天数（推进季节）。"""
    day = today or _day_key()
    if str(wallet.get("farm_login_ymd") or "") == day:
        return max(0, int(wallet.get("farm_login_days") or 0))
    wallet["farm_login_ymd"] = day
    wallet["farm_login_days"] = max(0, int(wallet.get("farm_login_days") or 0)) + 1
    return int(wallet["farm_login_days"])


def farm_season_state(wallet: dict, *, today: str | None = None) -> dict:
    days = max(0, int(wallet.get("farm_login_days") or 0))
    idx = (days // DAYS_PER_SEASON) % len(SEASON_NAMES)
    name = SEASON_NAMES[idx]
    day = today or _day_key()
    try:
        dig = sum(int(c) for c in day if c.isdigit())
    except Exception:
        dig = 0
    raining = (dig % 7) in RAIN_DAY_MODS
    return {
        "season": name,
        "season_index": idx,
        "login_days": days,
        "days_into_season": days % DAYS_PER_SEASON,
        "raining": raining,
        "trim": SEASON_SKY_TRIM.get(name, "#e8d090"),
        "label": f"{name}·{'雨' if raining else '晴'}",
    }


def apply_rain_blessing(farm: list[list[dict | None]], *, now: float | None = None) -> int:
    """雨天：给未成熟作物一次轻度润泽。"""
    t_now = float(now if now is not None else time.time())
    n = 0
    for row in farm:
        if not isinstance(row, list):
            continue
        for plot in row:
            if not isinstance(plot, dict) or plot.get("wilted"):
                continue
            if plot_ready(plot, now=t_now):
                continue
            plot["boost_until"] = max(float(plot.get("boost_until") or 0), t_now + WATER_BOOST_SEC * 0.75)
            plot["last_water_at"] = t_now
            n += 1
    return n


def ensure_daily_orders(wallet: dict, *, today: str | None = None, season: str | None = None) -> list[dict]:
    day = today or _day_key()
    if str(wallet.get("farm_orders_ymd") or "") == day and isinstance(wallet.get("farm_orders"), list):
        return list(wallet["farm_orders"])
    season = season or str(farm_season_state(wallet, today=day).get("season") or "春")
    dig = sum(int(c) for c in day if c.isdigit()) or 1
    pool = list(ORDER_POOL)
    if season in ("春", "夏"):
        pool = sorted(pool, key=lambda o: 0 if "berry" in str(o["item"]) else 1)
    elif season == "秋":
        pool = sorted(pool, key=lambda o: 0 if "corn" in str(o["item"]) else 1)
    picks: list[dict] = []
    for i in range(2):
        o = dict(pool[(dig + i * 3) % len(pool)])
        o["done"] = False
        picks.append(o)
    wallet["farm_orders_ymd"] = day
    wallet["farm_orders"] = picks
    return picks


def try_fulfill_order(wallet: dict, order_id: str) -> tuple[bool, str]:
    orders = wallet.get("farm_orders") if isinstance(wallet.get("farm_orders"), list) else []
    target = None
    for o in orders:
        if str(o.get("id")) == str(order_id):
            target = o
            break
    if not target:
        return False, "找不到订单"
    if target.get("done"):
        return False, "这份订单已完成"
    item = str(target.get("item") or "")
    need = max(1, int(target.get("need") or 1))
    items = wallet.setdefault("items", {})
    if int(items.get(item, 0)) < need:
        return False, f"{ITEM_LABELS.get(item, item)}不足（需要 {need}）"
    items[item] = int(items.get(item, 0)) - need
    pay = max(1, int(target.get("pay") or 1))
    grant_coins_to_wallet(wallet, pay)
    target["done"] = True
    return True, f"交付成功！+{pay} 金币"


def start_processor(wallet: dict, recipe_id: str, *, today: str | None = None) -> tuple[bool, str]:
    recipe = PROCESS_RECIPES.get(recipe_id)
    if not recipe:
        return False, "未知作坊"
    day = today or _day_key()
    procs = wallet.setdefault("farm_processors", [])
    if not isinstance(procs, list):
        procs = []
        wallet["farm_processors"] = procs
    for p in procs:
        if str(p.get("recipe")) == recipe_id and not p.get("claimed"):
            ready = str(p.get("ready_ymd") or "")
            if ready >= day:
                return False, "这份还在做，明天再来取"
    items = wallet.setdefault("items", {})
    inp = str(recipe["input"])
    if int(items.get(inp, 0)) <= 0:
        return False, f"{ITEM_LABELS.get(inp, inp)}不足"
    items[inp] = int(items.get(inp, 0)) - 1
    import datetime as _dt

    ready = (_dt.datetime.strptime(day, "%Y-%m-%d") + _dt.timedelta(days=1)).strftime("%Y-%m-%d")
    procs.append({"recipe": recipe_id, "ready_ymd": ready, "claimed": False})
    wallet["farm_processors"] = procs[-6:]
    return True, f"已投入{ITEM_LABELS.get(inp, inp)}，{ready[5:]} 可取"


def claim_processors(wallet: dict, *, today: str | None = None) -> tuple[int, str]:
    day = today or _day_key()
    procs = wallet.get("farm_processors") if isinstance(wallet.get("farm_processors"), list) else []
    items = wallet.setdefault("items", {})
    got: list[str] = []
    for p in procs:
        if p.get("claimed"):
            continue
        ready = str(p.get("ready_ymd") or "")
        if ready and ready > day:
            continue
        recipe = PROCESS_RECIPES.get(str(p.get("recipe") or ""))
        if not recipe:
            p["claimed"] = True
            continue
        out = str(recipe["output"])
        items[out] = int(items.get(out, 0)) + 1
        p["claimed"] = True
        got.append(ITEM_LABELS.get(out, out))
    wallet["farm_processors"] = [p for p in procs if not p.get("claimed")][-6:]
    if not got:
        return 0, "暂无成品可取"
    return len(got), "取出：" + "、".join(got)


def ensure_ranch_pet(wallet: dict) -> dict:
    pet = wallet.get("ranch_pet")
    if not isinstance(pet, dict):
        pet = dict(DEFAULT_RANCH_PET)
        wallet["ranch_pet"] = pet
    return pet


def ranch_pet_status(wallet: dict) -> str:
    pet = ensure_ranch_pet(wallet)
    mood = int(pet.get("mood") or 0)
    face = "开心" if mood >= 70 else ("平静" if mood >= 40 else "有点闷")
    return f"{pet.get('name')}·心情{mood}（{face}）"


def pet_ranch_animal(wallet: dict, *, today: str | None = None) -> tuple[bool, str]:
    day = today or _day_key()
    pet = ensure_ranch_pet(wallet)
    if str(pet.get("last_pet_ymd") or "") == day:
        return False, f"今天已经摸过{pet.get('name')}啦"
    pet["last_pet_ymd"] = day
    pet["mood"] = min(100, int(pet.get("mood") or 0) + 12)
    return True, f"摸了摸{pet.get('name')}，心情+12"


def feed_ranch_animal(wallet: dict, *, today: str | None = None) -> tuple[bool, str]:
    day = today or _day_key()
    pet = ensure_ranch_pet(wallet)
    if str(pet.get("last_feed_ymd") or "") == day:
        return False, f"今天已经喂过{pet.get('name')}啦"
    items = wallet.setdefault("items", {})
    food = None
    for cand in ("crop_wheat", "crop_berry", "crop_corn", "compost"):
        if int(items.get(cand, 0)) > 0:
            food = cand
            break
    if not food:
        return False, "没有可喂的作物"
    items[food] = int(items.get(food, 0)) - 1
    pet["last_feed_ymd"] = day
    pet["mood"] = min(100, int(pet.get("mood") or 0) + 18)
    return True, f"用{ITEM_LABELS.get(food, food)}喂了{pet.get('name')}，心情+18"


def ranch_mood_offline_bonus(wallet: dict) -> int:
    pet = ensure_ranch_pet(wallet)
    return 1 if int(pet.get("mood") or 0) >= 80 else 0
