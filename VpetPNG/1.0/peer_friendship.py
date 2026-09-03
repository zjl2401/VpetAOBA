"""苍叶 ↔ 伊得 跨桌宠友情：相遇计数、好感等级、联动台词、解锁动作。"""
from __future__ import annotations

import json
import random
from pathlib import Path

KIND_AOBA = "aoba"
KIND_EIDEN = "eiden"

PET_DISPLAY: dict[str, str] = {
    KIND_AOBA: "苍叶",
    KIND_EIDEN: "伊得",
}

MINIPET_DISPLAY: dict[str, str] = {
    "rei": "莲",
    "allmate": "莲",
    "aster": "艾斯特",
    "morvay": "墨菲",
}

PAIR_KEY = "aoba_eiden"

# 每级解锁的亲密动作。
# 手拉手散步（hand_hold_walk）已暂时移除，稳定后再启用。
ACTION_BY_LEVEL: dict[int, str] = {}

# 每级进度条所需点数（逐级变难）
def points_for_bar(level: int) -> int:
    lv = max(1, int(level))
    return 4 + (lv - 1) * 3 + max(0, lv - 2) * (lv - 2)

def cumulative_before(level: int) -> float:
    return float(sum(points_for_bar(i) for i in range(1, max(1, int(level)))))

def stats(points: float) -> dict:
    pts = max(0.0, float(points))
    level = 1
    while pts >= cumulative_before(level) + points_for_bar(level):
        level += 1
    base = cumulative_before(level)
    need = points_for_bar(level)
    cur = pts - base
    pct = min(100, int(cur * 100 / max(1, need)))
    return {
        "level": level,
        "points": pts,
        "bar_pct": pct,
        "bar_cur": cur,
        "bar_need": need,
    }

def _path(presence_dir: Path) -> Path:
    return presence_dir / "crossover_friendship.json"

def load(presence_dir: Path) -> dict:
    path = _path(presence_dir)
    if not path.is_file():
        return {"pair": PAIR_KEY, "points": 0.0, "meet_count": 0, "last_meet_ms": 0}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            return {
                "pair": PAIR_KEY,
                "points": float(raw.get("points") or 0),
                "meet_count": int(raw.get("meet_count") or 0),
                "last_meet_ms": int(raw.get("last_meet_ms") or 0),
            }
    except Exception:
        pass
    return {"pair": PAIR_KEY, "points": 0.0, "meet_count": 0, "last_meet_ms": 0}

def save(presence_dir: Path, data: dict) -> None:
    try:
        presence_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "pair": PAIR_KEY,
            "points": float(data.get("points") or 0),
            "meet_count": int(data.get("meet_count") or 0),
            "last_meet_ms": int(data.get("last_meet_ms") or 0),
        }
        _path(presence_dir).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

def record_meet(presence_dir: Path, *, writer_id: str, peer_id: str, now_ms: int) -> dict:
    """仅 id 较小的一侧写盘，避免双开重复计分。"""
    data = load(presence_dir)
    if writer_id and peer_id and writer_id > peer_id:
        return {**data, **stats(float(data.get("points") or 0))}
    gain = 1.0
    data["meet_count"] = int(data.get("meet_count") or 0) + 1
    data["points"] = float(data.get("points") or 0) + gain
    data["last_meet_ms"] = int(now_ms)
    save(presence_dir, data)
    return {**data, **stats(float(data["points"]))}

def unlocked_actions(level: int) -> list[str]:
    lv = max(0, int(level))
    return [act for req, act in sorted(ACTION_BY_LEVEL.items()) if lv >= req]

def action_label(action: str) -> str:
    if action == "hand_hold_walk":
        return "手拉手一起走（5秒）"
    return action

def next_unlock_hint(level: int) -> str | None:
    """下一级将解锁的动作说明；未定义则返回 None。"""
    nxt = int(level) + 1
    act = ACTION_BY_LEVEL.get(nxt)
    if not act:
        return None
    return action_label(act)

def minipet_names(kinds: list[str], *, limit: int = 2) -> str:
    names: list[str] = []
    for key in kinds[:limit]:
        label = MINIPET_DISPLAY.get(key, key)
        if label not in names:
            names.append(label)
    return "、".join(names)

def normalize_companions(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        key = str(item or "").strip().lower()
        if key and key not in out:
            out.append(key)
    return out

def minipet_line(self_kind: str, self_companions: list[str], other_companions: list[str]) -> str | None:
    if not self_companions and not other_companions:
        return None
    self_name = PET_DISPLAY.get(self_kind, self_kind)
    parts: list[str] = []
    other_label = minipet_names(other_companions)
    self_label = minipet_names(self_companions)
    if other_companions:
        parts.append(f"{self_name}向{other_label}挥挥手")
        if self_kind == KIND_AOBA and "rei" in other_companions:
            parts.append(f"莲也在那边呢，打个招呼吧~")
    if self_companions:
        if other_companions:
            parts.extend(
                (
                    f"{self_label}：嗨，{other_label}~",
                    f"迷你宠 {self_label} 和 {other_label} 碰面了。",
                    f"{self_label}小声说：你好呀，{other_label}。",
                )
            )
        else:
            parts.append(f"{self_label}也在呢")
    if not parts:
        return None
    return random.choice(parts)

def greeting_lines(self_kind: str, other_kind: str) -> tuple[str, ...]:
    other = PET_DISPLAY.get(other_kind, other_kind)
    self_n = PET_DISPLAY.get(self_kind, self_kind)
    if self_kind == KIND_EIDEN and other_kind == KIND_AOBA:
        return (
            f"嗨，{other}！没想到在桌面遇见你。",
            f"{other}，碧岛的空气还习惯吗？我是{self_n}。",
            f"原来{other}也会跑出来啊……你好！",
            f"诶，是{other}！要不要一起待会儿？",
        )
    if self_kind == KIND_AOBA and other_kind == KIND_EIDEN:
        return (
            f"……{other}？你怎么也在这儿？",
            f"嗨，{other}。旧货店今天客人少，到处逛逛也好。",
            f"{other}，欢迎来到碧岛……算是吧。",
            f"桌面另一边是{other}啊，幸会~",
        )
    return (f"你好，{other}~", f"{self_n}遇见{other}了。")

def exchange_lines(self_kind: str, other_kind: str) -> tuple[str, ...]:
    other = PET_DISPLAY.get(other_kind, other_kind)
    if self_kind == KIND_EIDEN:
        return (
            f"今天{other}看起来精神不错。",
            "我这边刚忙完，过来透口气。",
            "要是能一起去散步就好了……",
        )
    return (
        f"莲说{other}看起来挺可靠的。",
        "平凡今天不算忙，可以多聊两句。",
        "下次要不要交换各自世界的见闻？",
    )

def build_greeting(
    self_kind: str,
    other_kind: str,
    *,
    self_companions: list[str] | None = None,
    other_companions: list[str] | None = None,
) -> str:
    sc = normalize_companions(self_companions or [])
    oc = normalize_companions(other_companions or [])
    main = random.choice(greeting_lines(self_kind, other_kind))
    extra = minipet_line(self_kind, sc, oc)
    if extra and random.random() < 0.72:
        return f"{main}\n{extra}"
    return main

def build_exchange(self_kind: str, other_kind: str) -> str:
    return random.choice(exchange_lines(self_kind, other_kind))

ACTION_FILE = "crossover_action.json"

def publish_action(presence_dir: Path, payload: dict) -> None:
    try:
        presence_dir.mkdir(parents=True, exist_ok=True)
        (presence_dir / ACTION_FILE).write_text(
            json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass

def read_action(presence_dir: Path) -> dict | None:
    path = presence_dir / ACTION_FILE
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else None
    except Exception:
        return None

def clear_action(presence_dir: Path) -> None:
    try:
        path = presence_dir / ACTION_FILE
        if path.is_file():
            path.unlink()
    except Exception:
        pass
