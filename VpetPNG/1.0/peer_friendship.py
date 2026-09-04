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

ACTION_STROLL_TOGETHER = "stroll_together"

ACTION_BY_LEVEL: dict[int, str] = {
    1: ACTION_STROLL_TOGETHER,
}

ACTION_LABELS: dict[str, str] = {
    ACTION_STROLL_TOGETHER: "并肩散步（15秒）",
}

SESSION_FILE = "crossover_session.json"
DIALOGUES_FILE = "crossover_dialogues.json"

STROLL_DURATION_MS = 15_000
STROLL_APPROACH_MAX_MS = 4500
STROLL_STEP_MS = 160
STROLL_CHAT_INTERVAL_MS = 2600

PAIR_KEY = "aoba_eiden"

PHASE_SILENT = "silent"
PHASE_FAMILIAR = "familiar"
PHASE_INTRO = "intro"
PHASE_FREE = "free"


def meet_phase(meet_count: int) -> str:
    """相遇阶段：1 静默 · 2–3 眼熟 · 4 自我介绍 · 5+ 自由问候。"""
    n = max(0, int(meet_count))
    if n <= 1:
        return PHASE_SILENT
    if n <= 3:
        return PHASE_FAMILIAR
    if n == 4:
        return PHASE_INTRO
    return PHASE_FREE


def meet_phase_label(meet_count: int) -> str:
    phase = meet_phase(meet_count)
    return {
        PHASE_SILENT: "初次擦肩",
        PHASE_FAMILIAR: "有点眼熟",
        PHASE_INTRO: "正式相识",
        PHASE_FREE: "老朋友",
    }.get(phase, "相遇中")


def points_gain_for_meet(meet_count_after: int) -> float:
    n = max(1, int(meet_count_after))
    if n <= 1:
        return 0.0
    if n <= 3:
        return 0.5
    return 1.0


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
        return {**data, **stats(float(data.get("points") or 0)), "phase": meet_phase(int(data.get("meet_count") or 0))}
    data["meet_count"] = int(data.get("meet_count") or 0) + 1
    gain = points_gain_for_meet(int(data["meet_count"]))
    data["points"] = float(data.get("points") or 0) + gain
    data["last_meet_ms"] = int(now_ms)
    save(presence_dir, data)
    phase = meet_phase(int(data["meet_count"]))
    return {**data, **stats(float(data["points"])), "phase": phase}


def unlocked_actions(level: int) -> list[str]:
    lv = max(0, int(level))
    return [act for req, act in sorted(ACTION_BY_LEVEL.items()) if lv >= req]


def action_label(action: str) -> str:
    return ACTION_LABELS.get(action, action)


def session_path(presence_dir: Path) -> Path:
    return presence_dir / SESSION_FILE


def load_session(presence_dir: Path) -> dict | None:
    path = session_path(presence_dir)
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else None
    except Exception:
        return None


def save_session(presence_dir: Path, data: dict) -> None:
    try:
        presence_dir.mkdir(parents=True, exist_ok=True)
        session_path(presence_dir).write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass


def clear_session(presence_dir: Path) -> None:
    try:
        path = session_path(presence_dir)
        if path.is_file():
            path.unlink()
    except Exception:
        pass


def compute_stroll_layout(
    ax: int,
    ay: int,
    asz: int,
    bx: int,
    by: int,
    bsz: int,
    *,
    gap: int = 8,
) -> dict:
    """两桌宠朝中间靠拢后左右并排的目标位。"""
    acx = int(ax) + int(asz) // 2
    bcx = int(bx) + int(bsz) // 2
    acy = int(ay) + int(asz) // 2
    bcy = int(by) + int(bsz) // 2
    mid_x = (acx + bcx) // 2
    mid_y = (acy + bcy) // 2
    slot_y = mid_y - max(int(asz), int(bsz)) // 2
    size = max(int(asz), int(bsz))
    half_gap = max(4, int(gap)) // 2
    if acx <= bcx:
        left_x = mid_x - half_gap - size
        right_x = mid_x + half_gap
        a_is_left = True
    else:
        left_x = mid_x - half_gap - size
        right_x = mid_x + half_gap
        a_is_left = False
    return {
        "mid_x": mid_x,
        "mid_y": mid_y,
        "slot_y": slot_y,
        "left_x": left_x,
        "right_x": right_x,
        "slot_size": size,
        "a_is_left": a_is_left,
    }


def pick_stroll_direction(left_x: int, right_x: int, slot_y: int, screen_w: int, size: int) -> str:
    room_l = max(0, left_x)
    room_r = max(0, screen_w - (right_x + size))
    return "right" if room_r >= room_l else "left"


def garbled_chat_line(*, length: int | None = None) -> str:
    moji = "啊嗯哦唔嘿呀嘛呢吧啦噗嘻呜哇呐哟"
    garb = "▓░▒■□●◆"
    n = max(4, int(length or random.randint(6, 14)))
    parts: list[str] = []
    for _ in range(n):
        if random.random() < 0.22:
            parts.append(random.choice(garb))
        else:
            parts.append(random.choice(moji))
    if random.random() < 0.45:
        parts.append("~" * random.randint(1, 3))
    return "".join(parts)


def dialogues_path(presence_dir: Path, data_dir: Path | None = None) -> Path | None:
    for base in (presence_dir, data_dir):
        if base is None:
            continue
        path = base / DIALOGUES_FILE
        if path.is_file():
            return path
    return None


def load_custom_dialogues(presence_dir: Path, data_dir: Path | None = None) -> dict[str, list[str]]:
    path = dialogues_path(presence_dir, data_dir)
    if not path:
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {}
        out: dict[str, list[str]] = {}
        for key, val in raw.items():
            kind = str(key or "").strip().lower()
            if not kind:
                continue
            if isinstance(val, list):
                lines = [str(x).strip() for x in val if str(x).strip()]
            elif isinstance(val, str) and val.strip():
                lines = [val.strip()]
            else:
                continue
            if lines:
                out[kind] = lines
        return out
    except Exception:
        return {}


def build_custom_talk(
    self_kind: str,
    other_kind: str,
    dialogues: dict[str, list[str]] | None,
    *,
    owner_name: str = "",
) -> str | None:
    pool = (dialogues or {}).get(self_kind) or []
    if not pool:
        return None
    line = random.choice(pool)
    other = PET_DISPLAY.get(other_kind, other_kind)
    owner = str(owner_name or "").strip()
    try:
        return line.format(other=other, owner=owner, self=PET_DISPLAY.get(self_kind, self_kind))
    except Exception:
        return line


def actions_available(level: int, meet_count: int) -> bool:
    return int(meet_count) >= 4 and int(level) >= 1


def next_unlock_hint(level: int) -> str | None:
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
            parts.append("莲也在那边呢，打个招呼吧~")
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


def familiar_lines(self_kind: str, other_kind: str) -> tuple[str, ...]:
    other = PET_DISPLAY.get(other_kind, other_kind)
    if self_kind == KIND_EIDEN:
        return (
            f"……嗯？那边好像是{other}？",
            f"有点眼熟……是{other}吗？",
            "好像在哪里见过一面……",
            f"诶，是{other}？我们之前碰过面吗？",
        )
    return (
        f"……是{other}？我们见过吗？",
        f"有点印象……{other}？",
        "诶，是不是之前擦肩过？",
        f"嗯……{other}，好像不是第一次见了。",
    )


def intro_script(self_kind: str, other_kind: str) -> tuple[str, ...]:
    other = PET_DISPLAY.get(other_kind, other_kind)
    self_n = PET_DISPLAY.get(self_kind, self_kind)
    if self_kind == KIND_EIDEN:
        return (
            f"……你好，我是{self_n}。",
            f"你是{other}吧？我们终于正式见面了。",
            "以后在桌面上碰面，就多多关照啦~",
        )
    return (
        f"……我是{self_n}。",
        f"原来你就是{other}啊，幸会。",
        "嗯……以后请多指教。",
    )


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


def build_familiar(self_kind: str, other_kind: str) -> str:
    return random.choice(familiar_lines(self_kind, other_kind))


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
