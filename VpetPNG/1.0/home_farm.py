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
    "crop_wheat": "小麦",
    "crop_berry": "莓果",
    "crop_corn": "玉米穗",
    "wood": "木材",
    "flower_cut": "采下的花",
    "fish": "鲜鱼",
    "work_reward_box": "工作宝箱",
}

SEED_TO_CROP: dict[str, str] = {
    "seed_wheat": "wheat",
    "seed_berry": "berry",
    "seed_corn": "corn",
}

# 成熟度：满分 100；每小时 +5；浇水后 1 小时内速率 ×2；每天最多浇 2 次
MATURITY_MAX = 100.0
MATURITY_PER_HOUR = 5.0
WATER_BOOST_SEC = 3600.0
WATER_MAX_PER_DAY = 2
TREE_REGROW_SEC = 48 * 3600
CHOP_DICE_MIN = 2
CHOP_DICE_MAX = 6

CROP_DEFS: dict[str, dict[str, Any]] = {
    "wheat": {
        "label": "小麦",
        "seed": "seed_wheat",
        "item": "crop_wheat",
        "colors": ("#c8b070", "#d4c078", "#e8d888", "#f0e090"),
    },
    "berry": {
        "label": "莓果",
        "seed": "seed_berry",
        "item": "crop_berry",
        "colors": ("#886688", "#aa6688", "#cc6688", "#ee5588"),
    },
    "corn": {
        "label": "玉米",
        "seed": "seed_corn",
        "item": "crop_corn",
        "colors": ("#889944", "#aaba44", "#ccdd55", "#ffe066"),
    },
}

# 商店：金币买种子/木材
SHOP_PRICES: dict[str, int] = {
    "seed_wheat": 3,
    "seed_berry": 4,
    "seed_corn": 4,
    "wood": 5,
}

# 售出作物
SELL_PRICES: dict[str, int] = {
    "crop_wheat": 4,
    "crop_berry": 5,
    "crop_corn": 5,
    "fish": 6,
    "flower_cut": 2,
}

# 默认可放置（布置模式）；合成解锁 sofa / shelf 等
DEFAULT_FURNITURE_UNLOCK: frozenset[str] = frozenset(
    {
        "bed",
        "table",
        "chair",
        "plant",
        "carpet",
        "lamp",
        "window",
        "vase",
        "grass",
        "land",
        "water",
        "brick",
        "tree",
        "rock",
        "flower",
        "fence",
        "bush",
        "path",
        "gift_art",
        "user_paint",
        "erase",
    }
)

CRAFT_ONLY_FURNITURE: frozenset[str] = frozenset({"sofa", "shelf"})

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
        "id": "sofa",
        "label": "解锁沙发",
        "costs": {"wood": 3, "crop_wheat": 1},
        "result": ("furniture", "sofa"),
        "desc": "3 木材+1 小麦 → 解锁沙发",
    },
    {
        "id": "shelf",
        "label": "解锁柜子",
        "costs": {"wood": 2, "crop_berry": 1},
        "result": ("furniture", "shelf"),
        "desc": "2 木材+1 莓果 → 解锁柜子",
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
    "till": "先清上面，再锄两下草地→土地",
    "plant": "仅土地可种；种子在格心",
    "water": "每天最多2次；浇后1小时成长×2",
    "harvest": "成熟度满100可收",
    "chop": "点树四周格子；掷骰砍够次数得木材",
    "fish": "点水面四周格子；上钩时再按一次",
    "pick": "采小花：可插花瓶，或在面板背包戴到头顶",
}

FARM_GUIDE_SECTIONS: tuple[tuple[str, str, str], ...] = (
    ("🚪", "进入", "室外 →「经营」"),
    ("🚶", "移动", "WASD / 点格子"),
    ("1️⃣", "锄地", "先清上面；草地锄两下变土地"),
    ("2️⃣", "播种", "种在土地格中心"),
    ("3️⃣", "浇水", "每天有限次；浇后一段时间成长加快"),
    ("4️⃣", "收获", "成熟后可收"),
    ("5️⃣", "砍树", "在树四周格操作"),
    ("6️⃣", "钓鱼", "在水面四周格操作"),
    ("7️⃣", "采花", "可插花瓶；面板背包可戴/摘"),
    ("⏎", "执行", "数字键只切换工具；确定 / Enter / 空格才执行"),
    ("🛒", "商店", "购买种子与木材"),
    ("⚒", "合成", "制作食物 / 解锁家具"),
)

FARM_GUIDE_BODY = (
    "· 数字键切换工具；点「确定」或按 Enter / 空格才会在脚下执行。\n"
    "· 推荐流程：锄地 → 播种 → 浇水 → 收获；亦可砍树、钓鱼、采花。\n"
    "· 每天首次打开桌宠可领取登录礼金币（同日仅一次）。"
)

SEED_START: dict[str, int] = {
    "seed_wheat": 4,
    "seed_berry": 2,
    "seed_corn": 2,
    "wood": 1,
    "flower_cut": 0,
    "fish": 0,
}


def default_wallet() -> dict:
    return {"coins": 20, "items": dict(SEED_START), "last_daily_coin_ymd": ""}


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
    return {"coins": coins, "items": items, "last_daily_coin_ymd": last_day}


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
    if kind in DEFAULT_FURNITURE_UNLOCK:
        return True
    if kind in (crafted or []):
        return True
    # 非合成限定的其它 kind（如未来扩展）默认可用
    if kind not in CRAFT_ONLY_FURNITURE:
        return True
    return False


def advance_plot_maturity(plot: dict | None, *, now: float | None = None) -> None:
    """按真实时间推进成熟度（浇水加成区间内 ×2）。"""
    if not plot:
        return
    t_now = float(now if now is not None else time.time())
    last = float(plot.get("last_tick") or plot.get("planted_at") or t_now)
    if t_now <= last:
        plot["last_tick"] = t_now
        return
    maturity = float(plot.get("maturity") or 0.0)
    boost_until = float(plot.get("boost_until") or 0.0)
    rate = MATURITY_PER_HOUR / 3600.0
    t0 = last
    while t0 < t_now and maturity < MATURITY_MAX:
        if t0 < boost_until:
            seg = min(t_now, boost_until)
            maturity += (seg - t0) * rate * 2.0
            t0 = seg
        else:
            maturity += (t_now - t0) * rate
            t0 = t_now
    plot["maturity"] = max(0.0, min(MATURITY_MAX, maturity))
    plot["last_tick"] = t_now


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
    crop = str(plot.get("crop") or "")
    meta = CROP_DEFS.get(crop)
    if not meta:
        return "#5a4830"
    colors = meta["colors"]
    st = plot_stage(plot, now=now)
    return colors[min(st, len(colors) - 1)]


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
) -> tuple[bool, str]:
    """锄地：先除掉上面小花/灌木；草地需锄两下变成土地；顺带清空作物。"""
    if y < 0 or x < 0 or y >= len(farm) or x >= len(farm[0]):
        return False, "超出范围"
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
    }
    return True, "已播种"


def try_water(farm: list[list[dict | None]], x: int, y: int) -> tuple[bool, str]:
    if y < 0 or x < 0 or y >= len(farm) or x >= len(farm[0]):
        return False, "超出范围"
    plot = farm[y][x]
    if not plot:
        return False, "空地无需浇水"
    now = time.time()
    advance_plot_maturity(plot, now=now)
    if plot_ready(plot, now=now):
        return False, "已成熟，请收获"
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
    return True, "浇水！一小时内成长速度×2"


def try_harvest(farm: list[list[dict | None]], wallet: dict, x: int, y: int) -> tuple[bool, str]:
    if y < 0 or x < 0 or y >= len(farm) or x >= len(farm[0]):
        return False, "超出范围"
    plot = farm[y][x]
    if not plot:
        return False, "没有作物"
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
    if kind != "tree" and not job:
        return False, "这里没有可砍的树（需树木素材）", None
    if kind == "tree" and not job:
        need = int(rng.randint(CHOP_DICE_MIN, CHOP_DICE_MAX))
        chop_jobs[key] = {"need": need, "done": 1, "x": int(x), "y": int(y)}
        if need <= 1:
            clear_at(outdoor_tiles, x, y)
            try_place(outdoor_tiles, "grass", x, y)
            chop_jobs.pop(key, None)
            items = wallet.setdefault("items", {})
            items["wood"] = int(items.get("wood", 0)) + 1
            tree_regrow.append({"x": int(x), "y": int(y), "ready_at": time.time() + TREE_REGROW_SEC})
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
        {"x": int(x), "y": int(y), "ready_at": time.time() + TREE_REGROW_SEC}
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
        if ready > t_now:
            remain.append(item)
            continue
        if cell_kind(outdoor_tiles, x, y) in (None, "grass", "land", "path", "brick"):
            try_place(outdoor_tiles, "tree", x, y)
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
            if cell_kind(tiles, nx, ny) == "tree":
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
        if out_id not in crafted:
            crafted.append(out_id)
        return True, f"已解锁家具：{out_id}", ("furniture", out_id)
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
