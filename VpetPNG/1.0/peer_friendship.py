"""苍叶 ↔ 伊得 跨桌宠友情：相遇计数、好感等级、联动台词、解锁动作。"""
from __future__ import annotations

import json
import random
import re
import time
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
ACTION_SIDE_MEET = "side_meet"  # 话/动：先并排站定；动再进入 act_ready 选具体动作
ACTION_HOME_GUEST = "home_guest"  # 友情 5：邀请对方来家园做客

ACTION_BY_LEVEL: dict[int, str] = {
    1: ACTION_STROLL_TOGETHER,
    5: ACTION_HOME_GUEST,
}

ACTION_LABELS: dict[str, str] = {
    ACTION_STROLL_TOGETHER: "并肩散步（18秒）",
    ACTION_HOME_GUEST: "邀请来家园做客",
}

HOME_GUEST_UNLOCK_LEVEL = 5

# 已实装动作的最高友情等级；更高档位面板/升级先锁（加新动作时扩 ACTION_BY_LEVEL 即可）
MAX_IMPLEMENTED_LEVEL = max(ACTION_BY_LEVEL.keys()) if ACTION_BY_LEVEL else 1

# 动：并排到位后短站定，再出动作热区
SIDE_STAND_HOLD_MS = 480
SIDE_DIALOG_GAP_MS = 450
SIDE_TALK_REPLY_TIMEOUT_MS = 4000  # 对端不接话时本机代说第二句

SESSION_FILE = "crossover_session.json"
DIALOGUES_FILE = "crossover_dialogues.json"

STROLL_DURATION_MS = 18_000
STROLL_APPROACH_MAX_MS = 4500
STROLL_STEP_MS = 160
STROLL_CHAT_INTERVAL_MS = 2200
STROLL_CHAT_POLL_MS = 280
STROLL_CHAT_SPEAKER_TIMEOUT_MS = 3000  # 对端该说却未推进时本机接管
# 跨宠接话：等对方气泡预计收起后再开口（进程间看不到对方 Tk 窗）
SPEECH_TURN_GAP_MS = 380
SPEECH_MS_PER_CHAR = 48
SPEECH_TYPE_MIN_MS = 400
SPEECH_TYPE_MAX_MS = 2400
# 「话」第二句：等对端说完的最长时间；超时本机也要接上，避免对话断掉
DIALOGUE_PEER_WAIT_MAX_MS = 3600
DIALOGUE_INITIATOR_FALLBACK_MS = 4200

PAIR_KEY = "aoba_eiden"

PHASE_SILENT = "silent"  # 兼容旧引用；meet_phase 不再返回此阶段
PHASE_FAMILIAR = "familiar"
PHASE_INTRO = "intro"
PHASE_FREE = "free"


def meet_phase(meet_count: int) -> str:
    """相遇阶段：1–10 眼熟 · 11 自我介绍 · 12+ 自由（已去掉静默期）。"""
    n = max(0, int(meet_count))
    if n <= 0:
        return PHASE_FAMILIAR
    if n <= 10:
        return PHASE_FAMILIAR
    if n == 11:
        return PHASE_INTRO
    return PHASE_FREE


def meet_phase_label(meet_count: int) -> str:
    phase = meet_phase(meet_count)
    return {
        PHASE_SILENT: "有点眼熟",
        PHASE_FAMILIAR: "有点眼熟",
        PHASE_INTRO: "正式相识",
        PHASE_FREE: "老朋友",
    }.get(phase, "相遇中")


def points_gain_for_meet(meet_count_after: int) -> float:
    n = max(1, int(meet_count_after))
    if n <= 10:
        return 0.35
    return 0.55


# 每级进度条所需点数（逐级变难；答对加点多，但升级不靠整级跳）
def points_for_bar(level: int) -> int:
    lv = max(1, int(level))
    # Lv1≈14, Lv2≈24, Lv3≈41, Lv4≈65 … 比旧曲线更慢
    return 14 + (lv - 1) * 10 + max(0, lv - 2) * (lv - 2) * 3


# 问答奖励：答对约半格～大半格；答错轻扣。整体升级靠多次问答+相遇。
QUIZ_CORRECT_POINTS = 7.5
QUIZ_WRONG_POINTS = -0.5


def cumulative_before(level: int) -> float:
    return float(sum(points_for_bar(i) for i in range(1, max(1, int(level)))))


def max_points_at_cap() -> float:
    """锁在已实装最高级时：进度条满格，但不跨入下一级。"""
    lv = max(1, int(MAX_IMPLEMENTED_LEVEL))
    return float(cumulative_before(lv) + points_for_bar(lv))


def clamp_points(points: float) -> float:
    return max(0.0, min(float(points), max_points_at_cap()))


def stats(points: float) -> dict:
    pts = clamp_points(points)
    level = 1
    while pts >= cumulative_before(level) + points_for_bar(level):
        level += 1
        if level >= MAX_IMPLEMENTED_LEVEL:
            # 满级：进度顶格，不再升到未实装档
            level = MAX_IMPLEMENTED_LEVEL
            base = cumulative_before(level)
            need = points_for_bar(level)
            cur = min(float(need), max(0.0, pts - base))
            pct = min(100, int(cur * 100 / max(1, need)))
            return {
                "level": level,
                "points": pts,
                "bar_pct": pct,
                "bar_cur": cur,
                "bar_need": need,
                "level_capped": True,
                "max_implemented_level": MAX_IMPLEMENTED_LEVEL,
            }
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
        "level_capped": level >= MAX_IMPLEMENTED_LEVEL and cur >= need - 1e-6,
        "max_implemented_level": MAX_IMPLEMENTED_LEVEL,
    }


def _path(presence_dir: Path) -> Path:
    return presence_dir / "crossover_friendship.json"


def load(presence_dir: Path) -> dict:
    path = _path(presence_dir)
    empty = {
        "pair": PAIR_KEY,
        "points": 0.0,
        "meet_count": 0,
        "last_meet_ms": 0,
        "familiar_os_used": {},
        "shared_facts": [],
        "last_talk_mode": "",
        "quiz_cooldown_talks": 0,
        "long_history": [],
        "last_long_choice": "",
        "quarrel_cool_until_ms": 0,
    }
    if not path.is_file():
        return dict(empty)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            used = raw.get("familiar_os_used") or {}
            if not isinstance(used, dict):
                used = {}
            facts = raw.get("shared_facts") or []
            if not isinstance(facts, list):
                facts = []
            hist = raw.get("long_history") or []
            if not isinstance(hist, list):
                hist = []
            return {
                "pair": PAIR_KEY,
                "points": float(raw.get("points") or 0),
                "meet_count": int(raw.get("meet_count") or 0),
                "last_meet_ms": int(raw.get("last_meet_ms") or 0),
                "familiar_os_used": {str(k): list(v) if isinstance(v, list) else [] for k, v in used.items()},
                "shared_facts": [str(x) for x in facts if str(x).strip()],
                "last_talk_mode": str(raw.get("last_talk_mode") or ""),
                "quiz_cooldown_talks": int(raw.get("quiz_cooldown_talks") or 0),
                "long_history": [str(x) for x in hist if str(x).strip()],
                "last_long_choice": str(raw.get("last_long_choice") or ""),
                "quarrel_cool_until_ms": int(raw.get("quarrel_cool_until_ms") or 0),
            }
    except Exception:
        pass
    return dict(empty)


def save(presence_dir: Path, data: dict) -> None:
    try:
        presence_dir.mkdir(parents=True, exist_ok=True)
        used = data.get("familiar_os_used") or {}
        if not isinstance(used, dict):
            used = {}
        facts = data.get("shared_facts") or []
        if not isinstance(facts, list):
            facts = []
        hist = data.get("long_history") or []
        if not isinstance(hist, list):
            hist = []
        payload = {
            "pair": PAIR_KEY,
            "points": clamp_points(float(data.get("points") or 0)),
            "meet_count": int(data.get("meet_count") or 0),
            "last_meet_ms": int(data.get("last_meet_ms") or 0),
            "familiar_os_used": {str(k): [str(x) for x in (v or [])] for k, v in used.items()},
            "shared_facts": [str(x) for x in facts if str(x).strip()],
            "last_talk_mode": str(data.get("last_talk_mode") or ""),
            "quiz_cooldown_talks": max(0, int(data.get("quiz_cooldown_talks") or 0)),
            "long_history": [str(x) for x in hist if str(x).strip()][-8:],
            "last_long_choice": str(data.get("last_long_choice") or ""),
            "quarrel_cool_until_ms": int(data.get("quarrel_cool_until_ms") or 0),
        }
        _path(presence_dir).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def record_meet(
    presence_dir: Path,
    *,
    writer_id: str,
    peer_id: str,
    now_ms: int,
    force: bool = False,
) -> dict:
    """记录一次有效相遇。

    自动擦肩时两边几乎同时调用：非 force 时仅 id 较小的一侧写盘，避免双计。
    两步「遇」配对 / 手动「话」只有完成方调用一次，须 force=True，否则
    eiden_* > aoba_* 时伊得点第二下永远不涨相遇次数。
    """
    data = load(presence_dir)
    if (
        not force
        and writer_id
        and peer_id
        and writer_id > peer_id
    ):
        return {
            **data,
            **stats(float(data.get("points") or 0)),
            "phase": meet_phase(int(data.get("meet_count") or 0)),
        }
    data["meet_count"] = int(data.get("meet_count") or 0) + 1
    gain = points_gain_for_meet(int(data["meet_count"]))
    data["points"] = clamp_points(float(data.get("points") or 0) + gain)
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


SESSION_STALE_MS = 180_000  # 并排/对话会话超时；过期清掉以免挡住「遇」热区


def load_session(presence_dir: Path) -> dict | None:
    path = session_path(presence_dir)
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return None
        # 无 flow 的动作会话：靠 started_ms / stand_until 判断过期
        flow = str(raw.get("flow") or "").strip().lower()
        if flow not in ("picking", "linked"):
            now = int(time.time() * 1000)
            started = int(raw.get("started_ms") or raw.get("ts") or 0)
            stand_until = int(raw.get("stand_until_ms") or 0)
            stroll_until = int(raw.get("stroll_until_ms") or 0)
            speak_until = int(raw.get("speaking_until_ms") or raw.get("speaker_until_ms") or 0)
            anchor = max(started, stand_until, stroll_until, speak_until)
            if anchor > 0 and (now - anchor) > SESSION_STALE_MS:
                try:
                    path.unlink()
                except Exception:
                    pass
                return None
        return raw
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


# 手动相遇 UI 流程：
# idle → 靠近显示「相遇」像素图标 → 两边各点一次完成配对
# → 1s 后双方弹动（2–10 次另加眼熟内心 OS）
# → 第 11 次起 linked 显示「对话」图标；等级够时再显「互动」图标
# 对话/互动均先走到中间并排，再对话 / 触发动作
# 仅两边点「相遇」完成的配对计入有效相遇；自动擦肩等不计。
FLOW_PICKING = "picking"
FLOW_LINKED = "linked"
FLOW_STALE_MS = 90_000

# 热区模式键（UI 用像素图案，不再画汉字）
ICON_MEET = "meet"
ICON_TALK = "talk"
ICON_ACT = "act"
# 兼容旧引用
GLYPH_MEET_START = ICON_MEET
GLYPH_MEET_JOIN = ICON_MEET
GLYPH_TALK = ICON_TALK
GLYPH_ACT = ICON_ACT

ACTION_PAIR_DIALOGUE = "pair_dialogue"
MEET_REACTION_DELAY_MS = 1000


def can_show_talk(meet_count: int) -> bool:
    """第 11 次有效相遇后才出现「话」。"""
    return int(meet_count or 0) >= 11


def can_show_action(level: int, meet_count: int) -> bool:
    """亲密动作「动」：自我介绍完成后解锁。"""
    return actions_available(level, meet_count)


def _flow_fresh(raw: dict | None) -> dict | None:
    if not isinstance(raw, dict):
        return None
    flow = str(raw.get("flow") or "").strip().lower()
    if flow not in (FLOW_PICKING, FLOW_LINKED):
        return None
    ts = int(raw.get("ts") or 0)
    if ts <= 0 or (int(time.time() * 1000) - ts) > FLOW_STALE_MS:
        return None
    return raw


def get_flow(presence_dir: Path) -> dict | None:
    return _flow_fresh(load_session(presence_dir))


def begin_pick(
    presence_dir: Path,
    *,
    picker_id: str,
    picker_kind: str,
    x: int,
    y: int,
    size: int,
) -> None:
    now = int(time.time() * 1000)
    save_session(
        presence_dir,
        {
            "flow": FLOW_PICKING,
            "picker_id": str(picker_id),
            "picker_kind": str(picker_kind or "").strip().lower(),
            "picker_x": int(x),
            "picker_y": int(y),
            "picker_size": int(size),
            "ts": now,
        },
    )


def complete_link(
    presence_dir: Path,
    *,
    picker_id: str,
    peer_id: str,
    link_token: str,
    meet_count: int,
) -> None:
    now = int(time.time() * 1000)
    save_session(
        presence_dir,
        {
            "flow": FLOW_LINKED,
            "picker_id": str(picker_id),
            "peer_id": str(peer_id),
            "link_token": str(link_token),
            "meet_count": int(meet_count),
            "ts": now,
        },
    )


def merge_session(presence_dir: Path, **fields) -> dict:
    """在现有 session 上合并字段（保留 flow / linked 信息）。"""
    cur = load_session(presence_dir) or {}
    updated = dict(cur)
    updated.update(fields)
    updated["ts"] = int(time.time() * 1000)
    save_session(presence_dir, updated)
    return updated


def dialogue_lines_for_pair(
    initiator_kind: str,
    other_kind: str,
    *,
    meet_count: int,
) -> tuple[str, str]:
    """发起方一句 + 另一方回一句（成对台词，避免前言不搭后语）。"""
    n = int(meet_count or 0)
    other = PET_DISPLAY.get(other_kind, other_kind)
    self_n = PET_DISPLAY.get(initiator_kind, initiator_kind)
    if n <= 11:
        intro_pairs = (
            (f"……你好，我是{self_n}。", f"……我是{other}。幸会。"),
            (f"你是{other}吧？我们终于正式见面了。", "嗯……以后请多指教。"),
            ("以后在桌面上碰面，就多多关照啦~", "好。碰面时打个招呼就行。"),
            ("我也会怕，也会笑——先从招呼开始。", "……那我们现在算打过招呼了。"),
            (f"从这边世界来的访客，就是我。请多指教，{other}。", f"请多指教，{self_n}。"),
        )
        idx = max(0, min(len(intro_pairs) - 1, n - 1))
        return intro_pairs[idx]
    # 熟后：优先成对寒暄/短谈，不再各自随机拼句
    pool = [x for x in SHORT_TALK_VARIANTS if x[0] == "greet"] or list(SHORT_TALK_VARIANTS)
    _style, a, b = random.choice(pool)
    return (str(a), str(b))


def clear_flow(presence_dir: Path) -> None:
    clear_session(presence_dir)


# 兼容旧调用名
UI_MODE_MEET = "meet"
UI_MODE_TALK = "talk"
UI_MODE_STALE_MS = FLOW_STALE_MS


def get_ui_mode(presence_dir: Path) -> str | None:
    """旧接口：picking 视作 meet；linked 不返回 mode。"""
    flow = get_flow(presence_dir)
    if not flow:
        return None
    if str(flow.get("flow")) == FLOW_PICKING:
        return UI_MODE_MEET
    return None


def set_ui_mode(presence_dir: Path, mode: str) -> None:
    # 旧接口废弃：改走 begin_pick / complete_link
    _ = (presence_dir, mode)


def clear_ui_mode(presence_dir: Path) -> None:
    clear_flow(presence_dir)


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


def estimate_speech_ms(
    text: str,
    *,
    auto_hide_ms: int | None = None,
    instant: bool = False,
) -> int:
    """估算一句台词占屏时长（打字 + 停留），供对端接话对齐。"""
    n = max(1, len(str(text or "").strip()))
    type_ms = 0 if instant else min(SPEECH_TYPE_MAX_MS, max(SPEECH_TYPE_MIN_MS, n * SPEECH_MS_PER_CHAR))
    hide = max(900, int(auto_hide_ms if auto_hide_ms is not None else 2400))
    return int(type_ms + hide + 160)


def speech_still_active(until_ms: int, *, now_ms: int | None = None) -> bool:
    now = int(now_ms if now_ms is not None else time.time() * 1000)
    return int(until_ms or 0) > now


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


def load_custom_dialogues(presence_dir: Path, data_dir: Path | None = None) -> dict[str, list[dict]]:
    """自定义相遇台词。支持纯字符串，或 {text, keyword, bubble, cells}。

    bubble: \"text\" | \"pixels\" —— 气泡里是文字还是像素画；
    keyword: 可选，可作为 AI 对话围绕展开的关键词；
    cells: 可选，12×12 色板下标（0=透明），bubble=pixels 时绘制。
    """
    path = dialogues_path(presence_dir, data_dir)
    if not path:
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {}
        out: dict[str, list[dict]] = {}
        for key, val in raw.items():
            kind = str(key or "").strip().lower()
            if not kind:
                continue
            items = val if isinstance(val, list) else ([val] if val else [])
            entries: list[dict] = []
            for item in items:
                entry = normalize_dialogue_entry(item)
                if entry is not None:
                    entries.append(entry)
            if entries:
                out[kind] = entries
        return out
    except Exception:
        return {}


def normalize_dialogue_entry(raw) -> dict | None:
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return None
        return {"text": text, "keyword": "", "bubble": "text", "cells": []}
    if not isinstance(raw, dict):
        return None
    text = str(raw.get("text") or raw.get("line") or "").strip()
    if not text:
        return None
    bubble = str(raw.get("bubble") or "text").strip().lower()
    if bubble not in ("text", "pixels"):
        bubble = "text"
    keyword = str(raw.get("keyword") or raw.get("topic") or "").strip()
    cells_raw = raw.get("cells")
    cells: list[int] = []
    if isinstance(cells_raw, list):
        for v in cells_raw[:144]:
            try:
                cells.append(max(0, min(15, int(v or 0))))
            except Exception:
                cells.append(0)
        while len(cells) < 144:
            cells.append(0)
    return {"text": text, "keyword": keyword, "bubble": bubble, "cells": cells}


def pick_custom_entry(self_kind: str, dialogues: dict[str, list[dict]] | None) -> dict | None:
    pool = (dialogues or {}).get(self_kind) or []
    if not pool:
        return None
    return dict(random.choice(pool))


def build_custom_talk(
    self_kind: str,
    other_kind: str,
    dialogues: dict[str, list[dict]] | None,
    *,
    owner_name: str = "",
) -> str | None:
    entry = pick_custom_entry(self_kind, dialogues)
    if entry is None:
        return None
    line = str(entry.get("text") or "")
    other = PET_DISPLAY.get(other_kind, other_kind)
    owner = str(owner_name or "").strip()
    try:
        return line.format(other=other, owner=owner, self=PET_DISPLAY.get(self_kind, self_kind))
    except Exception:
        return line


def build_custom_entry_talk(
    entry: dict,
    self_kind: str,
    other_kind: str,
    *,
    owner_name: str = "",
) -> str:
    line = str(entry.get("text") or "")
    other = PET_DISPLAY.get(other_kind, other_kind)
    owner = str(owner_name or "").strip()
    try:
        return line.format(other=other, owner=owner, self=PET_DISPLAY.get(self_kind, self_kind))
    except Exception:
        return line


def actions_available(level: int, meet_count: int) -> bool:
    # 加长 P0 后：自我介绍完成（≥11）且 Lv≥1 才解锁并肩
    return int(meet_count) >= 11 and int(level) >= 1


def next_unlock_hint(level: int) -> str | None:
    nxt = int(level) + 1
    if nxt > MAX_IMPLEMENTED_LEVEL:
        return "后续等级暂未开放"
    act = ACTION_BY_LEVEL.get(nxt)
    if not act:
        return "后续等级暂未开放"
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
    """眼熟阶段：极短（≤12 字），见面 UI 轻量化。"""
    other = PET_DISPLAY.get(other_kind, other_kind)
    if self_kind == KIND_EIDEN:
        return (
            f"……是{other}？",
            "有点眼熟……",
            "好像见过……",
            f"诶，{other}？",
            "这感觉……",
            "桌面又撞见。",
            "嗯，是你吧。",
            "心跳漏半拍。",
            "又碰面了。",
            "记得这气息。",
            "别擦肩啊。",
            "轻轻点头。",
        )
    return (
        f"……{other}？",
        "有点印象……",
        "擦肩过？",
        f"嗯……{other}？",
        "好像见过。",
        "印象里有你。",
        "又遇见了。",
        "轻轻挥一下。",
    )


def _os_key(line: str) -> str:
    return str(line or "").strip()


def build_familiar(self_kind: str, other_kind: str, presence_dir: Path | None = None) -> str:
    """2–10 次眼熟 OS；传入 presence_dir 时按角色去重，用尽后重置。"""
    lines = familiar_lines(self_kind, other_kind)
    if presence_dir is None:
        return random.choice(lines)
    data = load(presence_dir)
    used_map = dict(data.get("familiar_os_used") or {})
    used = [str(x) for x in (used_map.get(self_kind) or [])]
    used_set = set(used)
    pool = [ln for ln in lines if _os_key(ln) not in used_set]
    if not pool:
        used = []
        used_set.clear()
        pool = list(lines)
    choice = random.choice(pool)
    used.append(_os_key(choice))
    used_map[self_kind] = used
    data["familiar_os_used"] = used_map
    save(presence_dir, data)
    return choice


# —— 12+ 交流：普通对话知识点（告诉 / 你还记得吗）——
TELL_PREFIXES: tuple[str, ...] = (
    "我想告诉你——",
    "你知道吗？",
    "悄悄跟你说：",
    "跟你讲一件事：",
)
REMEMBER_ACK: tuple[str, ...] = (
    "嗯，我记住了。",
    "好，记下了。",
    "知道了，谢谢你告诉我。",
    "收到，我会记得的。",
)
QUIZ_PREFIXES: tuple[str, ...] = (
    "你还记得吗？",
    "考你一下——你还记得吗？",
    "上次跟你说过，你还记得吗？",
)

# 来自普通对话设定；simple=True 适合所属人填空
KNOWLEDGE_FACTS: tuple[dict, ...] = (
    {
        "id": "name",
        "topic": "名字",
        "fact": "我叫伊得，本名 Eiden",
        "ask": "我叫什么名字？",
        "answers": ("伊得", "eiden", "Eiden", "EIDEN"),
        "simple": True,
    },
    {
        "id": "age",
        "topic": "年龄",
        "fact": "我今年二十三岁",
        "ask": "我多大了？",
        "answers": ("23", "二十三", "23岁", "二十三岁", "廿三"),
        "simple": True,
    },
    {
        "id": "birthday",
        "topic": "生日",
        "fact": "我的生日是 6 月 17 日",
        "ask": "我的生日是哪天？",
        "answers": ("6月17", "6月17日", "六月十七", "6/17", "06/17", "6-17", "617"),
        "simple": True,
    },
    {
        "id": "height",
        "topic": "身高",
        "fact": "我身高 176cm",
        "ask": "我多高？",
        "answers": ("176", "176cm", "一七六", "一百七十六", "176厘米"),
        "simple": True,
    },
    {
        "id": "looks",
        "topic": "发色瞳色",
        "fact": "我是褐发，瞳色偏褐黄",
        "ask": "我的头发和眼睛是什么颜色？",
        "answers": ("褐发", "褐黄", "褐色", "褐发褐黄", "棕色", "棕发"),
        "simple": True,
    },
    {
        "id": "cv",
        "topic": "声优",
        "fact": "我的配音是刺草ネトル",
        "ask": "我的声优是谁？",
        "answers": ("刺草ネトル", "刺草", "ネトル"),
        "simple": True,
    },
    {
        "id": "origin",
        "topic": "出身",
        "fact": "我出身现代世界，以前经常搬家",
        "ask": "我从哪里来？",
        "answers": ("现代世界", "现代", "异世界也待过", "卡莱因"),
        "simple": False,
    },
    {
        "id": "alias",
        "topic": "别号",
        "fact": "有人叫我「卡莱因之星」",
        "ask": "我的别号是什么？",
        "answers": ("卡莱因之星", "卡莱因"),
        "simple": True,
    },
    {
        "id": "mage",
        "topic": "大魔法师",
        "fact": "虽有「大魔法师」名号，我本质上也会害怕、也会怯懦",
        "ask": "大魔法师对我来说意味着什么？",
        "answers": ("普通人", "会害怕", "怯懦", "名号", "身份"),
        "simple": False,
    },
    {
        "id": "job",
        "topic": "以前的工作",
        "fact": "在现代世界时，我是经常搬家、每天工作超过十二小时的社畜",
        "ask": "我以前的工作是怎样的？",
        "answers": ("社畜", "加班", "十二小时", "12小时", "搬家"),
        "simple": False,
    },
    {
        "id": "childhood",
        "topic": "童年",
        "fact": "我在孤儿院长大，童年并不幸福，那时候缺少稳定的安全感",
        "ask": "我的童年是怎样的？",
        "answers": ("孤儿院", "缺少安全感", "不幸福", "安全感"),
        "simple": False,
    },
)


def knowledge_by_id(fact_id: str) -> dict | None:
    fid = str(fact_id or "").strip()
    for fact in KNOWLEDGE_FACTS:
        if str(fact.get("id") or "") == fid:
            return dict(fact)
    return None


def quiz_primary_answer(fact: dict) -> str:
    """测验/高亮用的主答案：优先较短中文答案。"""
    answers = [str(a).strip() for a in (fact.get("answers") or ()) if str(a).strip()]
    if not answers:
        return ""
    # 优先：含中文且较短
    cjk = [a for a in answers if any("\u4e00" <= ch <= "\u9fff" for ch in a)]
    pool = cjk or answers
    return min(pool, key=len)


def format_tell_fact_line(fact: dict) -> tuple[str, str]:
    """告诉时把关键答案用轻标记区分（颜色由 UI 侧柔和提示），返回 (整句正文, 主答案)。"""
    body = str(fact.get("fact") or "").strip().rstrip("。．.!")
    primary = quiz_primary_answer(fact)
    if not primary:
        return body, ""

    def _mark(src: str, key: str) -> str:
        if not key or key not in src:
            return src
        # 避免重复包裹；用书名号式轻标记，不刷 ★
        if f"「{key}」" in src or f"『{key}』" in src:
            return src
        return src.replace(key, f"「{key}」", 1)

    marked = body
    if primary in marked:
        marked = _mark(marked, primary)
    else:
        for a in fact.get("answers") or ():
            a = str(a).strip()
            if a and a in marked:
                marked = _mark(marked, a)
                primary = a
                break
        else:
            marked = f"{body}（记得「{primary}」就好）"
    return marked, primary


def build_quiz_char_tiles(fact: dict, *, decoy_count: int = 8) -> tuple[str, list[str]]:
    """组字块：正确答案拆字 + 干扰字，打乱后返回 (主答案, 字块列表)。"""
    primary = quiz_primary_answer(fact)
    if not primary:
        return "", []
    need = list(primary)
    decoy_pool: list[str] = []
    for other in KNOWLEDGE_FACTS:
        if str(other.get("id") or "") == str(fact.get("id") or ""):
            continue
        for ans in other.get("answers") or ():
            for ch in str(ans):
                if ch.strip() and ch not in need and ch not in decoy_pool:
                    decoy_pool.append(ch)
        # 题干/设定里拆字也当干扰
        for ch in str(other.get("fact") or "") + str(other.get("topic") or ""):
            if ("\u4e00" <= ch <= "\u9fff") and ch not in need and ch not in decoy_pool:
                decoy_pool.append(ch)
    for ch in "的了吗呢啊呀嗯是否什么哪天多大记得一二三四五六七八九十日月年岁星色发眼名字生日身高":
        if ch not in need and ch not in decoy_pool:
            decoy_pool.append(ch)
    random.shuffle(decoy_pool)
    # 干扰量随答案长度略增，至少 6、最多 12
    want = max(6, min(12, int(decoy_count) + max(0, len(need) - 2)))
    extra = decoy_pool[:want]
    tiles = need + extra
    random.shuffle(tiles)
    return primary, tiles


def normalize_quiz_answer(text: str) -> str:
    t = str(text or "").strip().lower()
    for ch in (" ", "　", "。", "？", "?", "！", "!", "的", "是", "呢", "啊", "呀"):
        t = t.replace(ch, "")
    return t


def quiz_answer_correct(fact: dict, user_text: str) -> bool:
    raw = str(user_text or "").strip()
    if not raw:
        return False
    norm = normalize_quiz_answer(raw)
    for ans in fact.get("answers") or ():
        a = normalize_quiz_answer(str(ans))
        if not a:
            continue
        if norm == a or a in norm or norm in a:
            return True
    return False


def add_friendship_points(presence_dir: Path, delta: float) -> dict:
    """加减友情点数并回写（不整级跳）。"""
    data = load(presence_dir)
    data["points"] = clamp_points(float(data.get("points") or 0) + float(delta))
    save(presence_dir, data)
    return {**data, **stats(float(data["points"]))}


def bump_friendship_level(presence_dir: Path, delta: int) -> dict:
    """兼容旧调用：按级跳转。新逻辑优先用 add_friendship_points。
    高于已实装动作档位时锁在最高级满格，不再升虚级。"""
    data = load(presence_dir)
    st = stats(float(data.get("points") or 0))
    new_lv = max(1, int(st.get("level") or 1) + int(delta))
    if new_lv > MAX_IMPLEMENTED_LEVEL:
        new_lv = MAX_IMPLEMENTED_LEVEL
        data["points"] = max_points_at_cap()
    else:
        data["points"] = clamp_points(
            float(cumulative_before(new_lv) + points_for_bar(new_lv) * 0.15)
        )
    save(presence_dir, data)
    return {**data, **stats(float(data["points"]))}


def remember_shared_fact(presence_dir: Path, fact_id: str, *, talk_mode: str = "tell") -> None:
    data = load(presence_dir)
    facts = [str(x) for x in (data.get("shared_facts") or [])]
    fid = str(fact_id or "").strip()
    if fid and fid not in facts:
        facts.append(fid)
    data["shared_facts"] = facts
    data["last_talk_mode"] = str(talk_mode or "")
    # 刚告诉过：至少再聊几轮才允许提问，避免下一轮立刻考
    if str(talk_mode or "") == "tell":
        data["quiz_cooldown_talks"] = 2
    save(presence_dir, data)


def _tick_quiz_cooldown(data: dict) -> dict:
    """每次开「话」消耗一层冷却。"""
    cd = int(data.get("quiz_cooldown_talks") or 0)
    if cd > 0:
        data["quiz_cooldown_talks"] = cd - 1
    return data


def plan_knowledge_talk(
    presence_dir: Path,
    initiator_kind: str,
    other_kind: str,
    *,
    meet_count: int,
) -> dict:
    """12+「话」：告诉知识点 或 提问你还记得吗（问答偏少，且不紧跟告诉）。"""
    n = int(meet_count or 0)
    if n < 12:
        a0, b0 = dialogue_lines_for_pair(initiator_kind, other_kind, meet_count=n)
        return {"mode": "plain", "talk_kind": "short", "line1": a0, "line2": b0, "fact_id": "", "simple": False}

    data = load(presence_dir)
    shared = [str(x) for x in (data.get("shared_facts") or []) if knowledge_by_id(str(x))]
    last_mode = str(data.get("last_talk_mode") or "")
    cooldown = int(data.get("quiz_cooldown_talks") or 0)
    # 刚告诉过 / 冷却未完 / 刚考过：不抽问答；有共享知识点时也只低概率提问
    want_quiz = (
        bool(shared)
        and cooldown <= 0
        and last_mode not in ("tell", "quiz")
        and random.random() < 0.22
    )
    if want_quiz:
        fact = knowledge_by_id(random.choice(shared)) or {}
        prefix = random.choice(QUIZ_PREFIXES)
        ask = str(fact.get("ask") or "这件事？")
        return {
            "mode": "quiz",
            "talk_kind": "knowledge",
            "fact_id": str(fact.get("id") or ""),
            "line1": f"{prefix}{ask}",
            "line2": "",
            "simple": bool(fact.get("simple")),
            "topic": str(fact.get("topic") or ""),
            "hint": " / ".join(list(fact.get("answers") or ())[:2]) if fact.get("simple") else "",
            "answer_key": quiz_primary_answer(fact),
        }

    unused = [f for f in KNOWLEDGE_FACTS if str(f.get("id") or "") not in shared]
    fact = dict(random.choice(unused or list(KNOWLEDGE_FACTS)))
    prefix = random.choice(TELL_PREFIXES)
    marked, primary = format_tell_fact_line(fact)
    line1 = f"{prefix}{marked}。"
    line2 = random.choice(REMEMBER_ACK)
    return {
        "mode": "tell",
        "talk_kind": "knowledge",
        "fact_id": str(fact.get("id") or ""),
        "line1": line1,
        "line2": line2,
        "simple": bool(fact.get("simple")),
        "topic": str(fact.get("topic") or ""),
        "hint": "",
        "answer_key": primary,
    }


# —— 长谈情景（通顺开场 → 偶发一句乱码 → 灯泡/填写/选择 → selecttalk123）——
# 开场不插「这件事」；写不好的气氛句用乱码占位，不硬凑怪句。
LONG_TALK_MIN_MEETS = 12

_CHOICE_LISTEN = (
    {"id": "listen", "label": "继续听", "icon": "listen", "asset": ("outfit", "leaf"), "delta": 0.9, "reply": "你继续说，我听着。", "outcome": "认真听完了", "emote": "like"},
    {"id": "joke", "label": "损一句", "icon": "joke", "asset": ("outfit", "question"), "delta": 0.7, "reply": "行，你惨归惨，我还是站你这边。", "outcome": "用吐槽接住了", "emote": "wink"},
    {"id": "serious", "label": "认真回", "icon": "serious", "asset": ("outfit", "star"), "delta": 1.1, "reply": "这事我站你这边。我们慢慢说清楚。", "outcome": "认真回应了", "emote": "like"},
)
_CHOICE_DEEP = (
    {"id": "listen", "label": "当树洞", "icon": "listen", "asset": ("outfit", "leaf"), "delta": 1.1, "reply": "我不催你结论，你说到哪算哪。", "outcome": "当了会儿树洞", "emote": "like"},
    {"id": "joke", "label": "先泄压", "icon": "joke", "asset": ("outfit", "question"), "delta": 0.8, "reply": "先吐两句也行，吐完我们再谈。", "outcome": "先把气压下去了", "emote": "wink"},
    {"id": "serious", "label": "帮拆题", "icon": "serious", "asset": ("outfit", "heart"), "delta": 1.3, "reply": "我们把能改的和暂时改不了的分开看。", "outcome": "一起把问题拆开了", "emote": "like"},
)

LONG_TALK_SCENARIOS: dict[str, dict] = {
    "bond": {
        "mood_hint": "似乎在碎碎念",
        "mood_fmt": "似乎在碎碎念：{topic}",
        "topics": ("奇葩同事", "难吃外卖", "离谱天气", "抽卡掉坑", "加班通知"),
        "mood_emote": "like",
        "open_lines": (
            ("今天有点想吐槽，你听得下去吗？", "听。你先说，我帮你接。"),
            ("又碰面了。最近还顺利吗？", "马马虎虎。有事就说，没事也行。"),
            ("桌面今天好挤。借你旁边坐坐？", "坐。正好一起喘口气。"),
        ),
        "choices": _CHOICE_LISTEN,
    },
    "either_or": {
        "mood_hint": "似乎在玩二选一",
        "mood_fmt": "似乎在二选一：{topic}",
        "topics": ("咸粽还是甜粽", "薯片还是巧克力", "一周花光一百万", "只留一种饮料"),
        "mood_emote": "idea",
        "open_lines": (
            ("来玩二选一？不许说「都行」。", "行。你出题，我选边。"),
            ("我想问个没营养的问题，你敢答吗？", "敢。没营养才好玩。"),
            ("偏好测试：你先想好答案。", "好，我想好了你再问。"),
        ),
        "choices": (
            {"id": "listen", "label": "听理由", "icon": "listen", "asset": ("outfit", "leaf"), "delta": 0.8, "reply": "理由比答案有意思，你展开讲。", "outcome": "听完了站队理由", "emote": "like"},
            {"id": "joke", "label": "抬杠", "icon": "joke", "asset": ("outfit", "question"), "delta": 0.7, "reply": "我反对——但尊重你的品味。", "outcome": "抬杠了一轮", "emote": "wink"},
            {"id": "serious", "label": "认真站队", "icon": "serious", "asset": ("outfit", "star"), "delta": 1.0, "reply": "那我站这边。下次换你考我。", "outcome": "完成了站队", "emote": "like"},
        ),
    },
    "hobby": {
        "mood_hint": "似乎在种草安利",
        "mood_fmt": "似乎在聊爱好：{topic}",
        "topics": ("新游戏", "在追的剧", "便利店新品", "周末去处", "好吃的店"),
        "mood_emote": "idea",
        "open_lines": (
            ("最近有个东西想安利你，听三十秒？", "给你三十秒。超时我喊停。"),
            ("你最近在玩什么、看什么？", "我先听你的，然后我再交换。"),
            ("有没有想推荐的？我们换着说。", "有。你先来还是我先来？"),
        ),
        "choices": (
            {"id": "listen", "label": "听安利", "icon": "listen", "asset": ("outfit", "leaf"), "delta": 0.9, "reply": "记下了，回头我真去试试。", "outcome": "收下了安利", "emote": "like"},
            {"id": "joke", "label": "嘴硬", "icon": "joke", "asset": ("outfit", "question"), "delta": 0.7, "reply": "听起来可疑……名字发我。", "outcome": "嘴硬心软地要了推荐", "emote": "wink"},
            {"id": "serious", "label": "交换", "icon": "serious", "asset": ("outfit", "star"), "delta": 1.1, "reply": "那我也回你一个，互相种草。", "outcome": "交换了种草清单", "emote": "like"},
        ),
    },
    "roleplay": {
        "mood_hint": "似乎在假装某个场景",
        "mood_fmt": "似乎在扮演：{topic}",
        "topics": ("奶茶店排队", "操场看落日", "便利店夜班", "桌面守夜"),
        "mood_emote": "wink",
        "open_lines": (
            ("要不要假装一个场景玩玩？", "好啊。你定场景，我接话。"),
            ("我们演一小段，不破功。", "行，三、二、一，开始。"),
            ("如果现在不是桌面，我们会在哪？", "你说一个地方，我跟着演。"),
        ),
        "choices": (
            {"id": "listen", "label": "接戏", "icon": "listen", "asset": ("outfit", "star"), "delta": 0.9, "reply": "接住了。下一句你说。", "outcome": "把场景接下去了", "emote": "like"},
            {"id": "joke", "label": "破功", "icon": "joke", "asset": ("outfit", "question"), "delta": 0.7, "reply": "等等，任务栏是什么……好吧破功了。", "outcome": "笑场破功了", "emote": "wink"},
            {"id": "serious", "label": "演完", "icon": "serious", "asset": ("outfit", "heart"), "delta": 1.1, "reply": "那我们把这段演完再回桌面。", "outcome": "认真演完了一小段", "emote": "like"},
        ),
    },
    "deep": {
        "mood_hint": "似乎在当树洞",
        "mood_fmt": "似乎在倾诉：{topic}",
        "topics": ("内耗", "说不出口的拒绝", "瓶颈期", "对未来迷茫"),
        "mood_emote": "shy",
        "open_lines": (
            ("今晚想当会儿树洞，你有话想倒吗？", "有的话就倒。我不急着给答案。"),
            ("有点堵，跟你说可以吗？", "可以。先说，我们再慢慢理。"),
            ("你今天心里还好吗？", "还行。你要是不好，也可以跟我说。"),
        ),
        "choices": _CHOICE_DEEP,
    },
    "self": {
        "mood_hint": "似乎在聊自己",
        "mood_fmt": "似乎在自我复盘：{topic}",
        "topics": ("太敏感", "太要强", "熬过来的一段", "小时候的遗憾"),
        "mood_emote": "shy",
        "open_lines": (
            ("想聊聊自己，你会觉得无聊吗？", "不会。你说，我认真听。"),
            ("有时候我也说不清自己。", "那就一起慢慢说，不着急下结论。"),
            ("想让你当一面镜子，可以吗？", "可以。我会诚实，但不会刺你。"),
        ),
        "choices": _CHOICE_DEEP,
    },
    "values": {
        "mood_hint": "似乎在碰价值观",
        "mood_fmt": "似乎在讨论：{topic}",
        "topics": ("友谊要不要常联系", "平淡还是折腾", "怎么看成功失败", "关系里的边界"),
        "mood_emote": "idea",
        "open_lines": (
            ("想跟你对一对看法，不是找标准答案。", "好。你先说，我再补我的。"),
            ("这个问题可能没有对错，我们各说各的？", "可以。说完再看有没有重合。"),
            ("你对这件事怎么想？我想听真话。", "真话来了，可能不那么体面。"),
        ),
        "choices": (
            {"id": "listen", "label": "先听完", "icon": "listen", "asset": ("outfit", "leaf"), "delta": 1.0, "reply": "你的意思我听见了，我再说我的。", "outcome": "把观点听完整了", "emote": "like"},
            {"id": "joke", "label": "温柔抬杠", "icon": "joke", "asset": ("outfit", "question"), "delta": 0.8, "reply": "我不同意一半，另外一半我收下。", "outcome": "抬杠里达成了部分共识", "emote": "wink"},
            {"id": "serious", "label": "找重合", "icon": "serious", "asset": ("outfit", "heart"), "delta": 1.3, "reply": "至少我们同意：尊重选择，不绑架对方。", "outcome": "对齐了一小块价值观", "emote": "like"},
        ),
    },
    "dream": {
        "mood_hint": "似乎在聊以后",
        "mood_fmt": "似乎在聊梦想：{topic}",
        "topics": ("五年后想住哪", "不敢跟人说的目标", "理想的一天", "想去的地方"),
        "mood_emote": "shy",
        "open_lines": (
            ("想聊以后的事，可以吗？", "可以。桌面上说的，我替你保密。"),
            ("有个小目标，不太敢跟别人提。", "跟我说就行。先被听见，再谈落地。"),
            ("你理想里的生活是什么样？", "你先说，我也说说我的。"),
        ),
        "choices": (
            {"id": "listen", "label": "护住", "icon": "listen", "asset": ("outfit", "leaf"), "delta": 1.1, "reply": "这句话我先接住，不笑话。", "outcome": "把梦想接住了", "emote": "like"},
            {"id": "joke", "label": "画大一点", "icon": "joke", "asset": ("outfit", "question"), "delta": 0.8, "reply": "可以再大胆一点，没关系。", "outcome": "轻松地把愿景放大了", "emote": "wink"},
            {"id": "serious", "label": "拆一步", "icon": "serious", "asset": ("outfit", "star"), "delta": 1.3, "reply": "那这周先做一件能验证的小事。", "outcome": "把梦想拆成了下一步", "emote": "like"},
        ),
    },
    "food": {
        "mood_hint": "似乎在聊吃的",
        "mood_fmt": "似乎在聊吃：{topic}",
        "topics": ("外卖踩雷", "便利店新品", "深夜想喝热的", "一人食"),
        "mood_emote": "idea",
        "open_lines": (
            ("聊吃的？你今晚想吃什么？", "我想吃热的。你呢？"),
            ("今天吃得还好吗？", "还行。踩过雷也可以拿来吐槽。"),
            ("饿了就说实话，别硬撑。", "那我说实话：有点想吃。"),
        ),
        "choices": (
            {"id": "ramen", "label": "热汤面", "icon": "ramen", "asset": ("food", "ramen"), "delta": 0.8, "reply": "热汤面最实在：暖、够、不折腾。", "outcome": "聊到了热汤面", "emote": "like"},
            {"id": "onigiri", "label": "简餐", "icon": "bento", "asset": ("food", "onigiri"), "delta": 0.8, "reply": "简餐也要有底线，别糊、别太咸。", "outcome": "聊到了简餐底线", "emote": "like"},
            {"id": "cake", "label": "甜的", "icon": "cake", "asset": ("food", "cake"), "delta": 0.8, "reply": "甜的可以，但别只剩甜腻。", "outcome": "聊到了甜点分寸", "emote": "wink"},
        ),
    },
    "quarrel": {
        "mood_hint": "气氛有点拧",
        "mood_fmt": "似乎卡在：{topic}",
        "topics": ("玩笑过线", "催得太急", "没说清"),
        "mood_emote": "awkward",
        "open_lines": (
            ("刚才我说乱了，对不起。", "我听见了。我们把话说清楚就好。"),
            ("有点闷，还能继续聊吗？", "能。先摊开，别憋着。"),
        ),
        "choices": (
            {"id": "peace", "label": "对齐说法", "icon": "peace", "asset": ("outfit", "heart"), "delta": 2.2, "reply": "我重说一遍，你也纠正我。", "outcome": "把说法对齐了", "emote": "like"},
            {"id": "listen", "label": "先听完", "icon": "listen", "asset": ("outfit", "leaf"), "delta": 1.0, "reply": "你先说完，我不插嘴。", "outcome": "把别扭听完了", "emote": "like"},
            {"id": "cold", "label": "先冷静", "icon": "cold", "asset": ("outfit", "droplet"), "delta": -0.6, "reply": "……先各自缓一缓，晚点再谈。", "outcome": "先各自冷静一下", "emote": "speechless", "cool_quarrel": True},
        ),
    },
    "film": {
        "mood_hint": "似乎在聊影视",
        "mood_fmt": "似乎在聊影视：{topic}",
        "topics": ("上头的一集", "怕剧透", "配乐太催泪", "想安利怕踩雷"),
        "mood_emote": "idea",
        "open_lines": (
            ("最近在追剧或电影吗？", "在。要听安利还是先听避雷？"),
            ("有部片我想跟你讲两句。", "讲。剧透先举手。"),
        ),
        "choices": _CHOICE_LISTEN,
    },
    "books": {
        "mood_hint": "似乎在聊书",
        "mood_fmt": "似乎在聊书：{topic}",
        "topics": ("拍桌的一句", "弃书", "人物太真实", "细节控"),
        "mood_emote": "shy",
        "open_lines": (
            ("最近有在看书吗？", "有一点。你呢？有共鸣也可以交换。"),
            ("读到一句很想分享。", "说来听听。"),
        ),
        "choices": _CHOICE_LISTEN,
    },
    "craft": {
        "mood_hint": "似乎在聊创作",
        "mood_fmt": "似乎在聊折腾：{topic}",
        "topics": ("卡住的草稿", "完美主义", "灵感不过夜", "先完成再完美"),
        "mood_emote": "idea",
        "open_lines": (
            ("创作卡住的时候，你怎么办？", "我通常先交能看的一版，再慢慢改。"),
            ("又开始跟自己较劲了。", "较劲可以，别把自己锁死。"),
        ),
        "choices": _CHOICE_LISTEN,
    },
    "manners": {
        "mood_hint": "似乎在谈相处",
        "mood_fmt": "似乎在谈相处：{topic}",
        "topics": ("怎么说不", "道歉要不要解释", "帮倒忙怎么停", "朋友间的期待"),
        "mood_emote": "shy",
        "open_lines": (
            ("相处上有个小问题，想对一对。", "好。真实做法就行，不用说漂亮话。"),
            ("拒绝别人这件事，你觉得难吗？", "难。所以更要想清楚怎么说。"),
        ),
        "choices": _CHOICE_DEEP,
    },
    "secret": {
        "mood_hint": "似乎在说悄悄话",
        "mood_fmt": "似乎在说悄悄话：{topic}",
        "topics": ("不敢说的烦", "小心愿", "想被理解"),
        "mood_emote": "shy",
        "open_lines": (
            ("有句悄悄话，只说给你听。", "耳朵借你。我不会外传。"),
            ("纠结很久了，不知道从哪说起。", "从最好开口的那句开始就行。"),
        ),
        "choices": _CHOICE_DEEP,
    },
    "gift": {
        "mood_hint": "似乎在聊小确幸",
        "mood_fmt": "似乎在聊小确幸：{topic}",
        "topics": ("好听的歌", "偶遇", "表情包", "充满电"),
        "mood_emote": "like",
        "open_lines": (
            ("刚才有件小事让我开心了一下。", "说来听听，快乐要转发。"),
            ("今天有即时分享吗？", "有。你要的话我现在说。"),
        ),
        "choices": _CHOICE_LISTEN,
    },
    "game": {
        "mood_hint": "似乎在聊游戏",
        "mood_fmt": "似乎在聊游戏：{topic}",
        "topics": ("抽卡掉坑", "肝不动", "坑队友", "通关曲"),
        "mood_emote": "idea",
        "open_lines": (
            ("游戏方面，你要听惨案还是高光？", "惨案先。高光留到最后。"),
            ("最近有在打什么吗？", "有。你呢？一起吐槽也行。"),
        ),
        "choices": _CHOICE_LISTEN,
    },
    "weather": {
        "mood_hint": "似乎在聊气氛",
        "mood_fmt": "似乎在聊气氛：{topic}",
        "topics": ("壁纸落日", "忽然下雨", "阴天", "夜班"),
        "mood_emote": "like",
        "open_lines": (
            ("这种时候适合慢慢说话。", "嗯，不赶结论最好。"),
            ("外面或壁纸，气氛都不错。", "那就多待一会儿。"),
        ),
        "choices": _CHOICE_LISTEN,
    },
}



def long_scenario(scenario_id: str) -> dict | None:
    sc = LONG_TALK_SCENARIOS.get(str(scenario_id or "").strip())
    return dict(sc) if isinstance(sc, dict) else None


def pick_long_topic(sc: dict) -> str:
    topics = list(sc.get("topics") or ())
    if not topics:
        return ""
    return str(random.choice(topics))


def format_mood_hint(sc: dict, topic: str = "") -> str:
    """填写/选择页气氛短句：不带括号提示；主题另存 long_topic。"""
    _ = topic
    base = str(sc.get("mood_hint") or "似乎在聊天").strip()
    return strip_hint_parens(base) or "似乎在聊天"


def strip_hint_parens(text: str) -> str:
    """去掉提示里的（…）/(…) 及主题后缀。"""
    t = str(text or "")
    t = re.sub(r"（[^）]*）", "", t)
    t = re.sub(r"\([^)]*\)", "", t)
    for sep in ("：", ":", " · ", "·"):
        if sep in t:
            t = t.split(sep, 1)[0]
            break
    return t.strip(" ：:·，,")


def format_mood_hint_with_topic(sc: dict, topic: str = "") -> str:
    """需要带主题时的完整提示（toast / 存档用，仍去掉括号说明）。"""
    topic = str(topic or "").strip()
    base = format_mood_hint(sc, "")
    if not topic:
        return base
    fmt = str(sc.get("mood_fmt") or "").strip()
    if fmt and "{topic}" in fmt:
        try:
            return strip_hint_parens(fmt.format(topic=topic)) or base
        except Exception:
            pass
    return f"{base} · {topic}"


def format_long_outcome(choice: dict | None, topic: str = "") -> str:
    if not isinstance(choice, dict):
        return ""
    topic = str(topic or "").strip()
    oc = str(choice.get("outcome") or choice.get("label") or "").strip()
    if not oc:
        return ""
    if topic:
        return f"{topic} · {oc}"
    return oc


def _fmt_topic_text(text: str, topic: str = "") -> str:
    raw = str(text or "")
    t = str(topic or "").strip() or "这件事"
    try:
        return raw.format(topic=t)
    except Exception:
        return raw.replace("{topic}", t)


def plan_long_talk_scenario(presence_dir: Path | None, scenario_id: str) -> dict:
    """长谈：通顺开场 → 偶发一句乱码 → 灯泡填写/选择 → selecttalk123。"""
    _ = presence_dir
    sid = str(scenario_id or "").strip() or "bond"
    sc = LONG_TALK_SCENARIOS.get(sid) or LONG_TALK_SCENARIOS.get("bond") or {}
    pair = random.choice(list(sc.get("open_lines") or (("……", "……"),)))
    # 中段乱码加量：约 40% 塞 1～2 句乱码当气氛占位
    mid_lines: list[str] = []
    if random.random() < 0.40:
        mid_lines = [garbled_chat_line(length=random.randint(5, 11))]
        if random.random() < 0.55:
            mid_lines.append(garbled_chat_line(length=random.randint(4, 9)))
    garb_n = len(mid_lines)
    emote = str(sc.get("mood_emote") or "")
    line1 = str(pair[0])
    line2 = str(pair[1])
    return {
        "talk_kind": "long",
        "mode": "long",
        "long_scenario_id": sid,
        "long_phase": "open",
        "garble_left": garb_n,
        "long_topic": "",
        "mood_topic": "",
        "mood_hint": format_mood_hint(sc, ""),
        "mood_emote": emote,
        "emote_open": emote,
        "mid_lines": mid_lines,
        "topic_editable": True,
        "topic_needed": True,
        "line1": line1,
        "line2": line2,
        "initiator_line": line1,
        "reply_line": line2,
        "open_extra": [],
    }


def apply_long_talk_choice(presence_dir: Path, scenario_id: str, choice_id: str) -> dict:
    """写入选择结果并调整友情点数（只加减点，不整级跳）。"""
    sc = long_scenario(scenario_id) or {}
    choice = None
    for c in sc.get("choices") or ():
        if str(c.get("id") or "") == str(choice_id or ""):
            choice = dict(c)
            break
    raw = load(presence_dir)
    if not choice:
        return {**raw, **stats(float(raw.get("points") or 0))}
    raw["points"] = clamp_points(float(raw.get("points") or 0) + float(choice.get("delta") or 0))
    raw["last_talk_mode"] = "long"
    hist = [str(x) for x in (raw.get("long_history") or []) if str(x).strip()]
    hist.append(str(scenario_id))
    raw["long_history"] = hist[-8:]
    raw["last_long_choice"] = f"{scenario_id}:{choice_id}"
    if choice.get("cool_quarrel"):
        raw["quarrel_cool_until_ms"] = int(time.time() * 1000) + 120_000
    save(presence_dir, raw)
    return {**raw, **stats(float(raw.get("points") or 0))}


# 熟后短谈：通顺短句；乱码占位可多一点
SHORT_TALK_VARIANTS: tuple[tuple[str, str, str], ...] = (
    ("greet", "又碰面了。今天还好吗？", "还行。看到你在，就松一点。"),
    ("greet", "嗨。要不要随便聊两句？", "好啊。你先开场。"),
    ("greet", "桌面有点挤，我坐你旁边可以吗？", "可以。正好一起歇一会儿。"),
    ("greet", "打个招呼就好，不用找很深的话题。", "嗯，平淡开场也挺好。"),
    ("greet", "今天有什么想吐槽的吗？", "有一点。你听着就行。"),
    ("topic", "咸粽还是甜粽？", "咸。甜的我留给心情不好的时候。"),
    ("topic", "如果有一百万必须一周花光，你买什么？", "先把想吃的吃一遍，再给自己留张票。"),
    ("topic", "只留一种零食：薯片还是巧克力？", "薯片。那一口脆比较解压。"),
    ("topic", "最近有好玩的游戏或上头的剧吗？", "有。我可以安利一会儿。"),
    ("topic", "便利店你更常买喝的还是吃的？", "先喝的，吃的容易踩雷。"),
    ("topic", "假装我们在奶茶店排队，你点什么？", "少糖去冰。然后嫌前面的人点太慢。"),
    ("qa", "你觉得主人还会回来加班吗？", "感觉会。那我们再守一会儿。"),
    ("qa", "要不要去壁纸那边走走？", "走。边走边说也行。"),
    ("qa", "屏幕暗下来以后，你怕不怕？", "有你在就不怕。"),
    ("deep", "有时候心里很满，你会怎么清空一点？", "先做一件最小的事，别一次想完所有。"),
    ("deep", "说「不」这件事，你觉得难吗？", "难。所以更需要有人站我这边听我说。"),
    ("deep", "真正的友谊一定要经常联系吗？", "不一定。关键时刻回得来，就够了。"),
    ("soft", "我觉得自己有时候太敏感了。", "敏感不是错。当雷达用就好，别当罪名。"),
    ("soft", "有个小目标不太敢跟人说，跟你说可以吗？", "可以。我先听着，不笑话。"),
)


STROLL_OPEN_LINES: tuple[tuple[str, str], ...] = (
    ("走吧，绕一圈。", "好，并肩慢慢走。"),
    ("往这边靠靠？", "行，别走太快。"),
    ("先往空一点的地方？", "好，你定方向。"),
    ("边走边聊可以吗？", "可以，想到什么说什么。"),
    ("夜班巡逻开始？", "开始。我跟你并排。"),
)

# 并肩续聊：通顺为主；乱码由脚本加量
STROLL_CHAT_PAIRS: tuple[tuple[str, str], ...] = (
    ("刚才差点被鼠标带跑。", "我差点被撤销吓一跳。"),
    ("进度条占地方，好挤。", "来我这边，我给你留位置。"),
    ("你今天还好吗？", "还行。有你在就不闷。"),
    ("感觉主人还会加班。", "那就一起守着。"),
    ("要不要去壁纸那边？", "走，先放松一下。"),
    ("这边图标有点乱。", "桌面也该整理整理。"),
    ("你习惯走左边还是右边？", "跟你并排就行。"),
    ("走累了就停。", "好，不硬撑。"),
    ("今天节奏还算慢。", "慢一点正好能说话。"),
    ("突然想喝点热的。", "那我们想象一杯，干杯。"),
    ("通知弹窗好烦。", "嫌烦就骂两句，我接。"),
    ("影子叠在一起了。", "说明距离刚好。"),
    ("再走一会儿？", "再走一会儿。"),
    ("等会儿屏幕暗了也不怕。", "嗯，有我在。"),
)



def pick_stroll_open_lines() -> tuple[str, str]:
    pair = random.choice(STROLL_OPEN_LINES)
    return str(pair[0]), str(pair[1])


def plan_stroll_chat_script(*, count: int = 6) -> list[str]:
    """并肩散步：通顺成对为主；乱码占位加量。"""
    n = max(4, int(count))
    if n % 2:
        n += 1
    open1, open2 = pick_stroll_open_lines()
    pairs = list(STROLL_CHAT_PAIRS)
    random.shuffle(pairs)
    out = [open1, open2]
    for a, b in pairs:
        if len(out) >= n:
            break
        if a in out and b in out:
            continue
        # 约 28%：用乱码占位，不硬凑怪话
        if len(out) >= 2 and random.random() < 0.28:
            out.append(garbled_chat_line(length=random.randint(5, 11)))
            out.append(garbled_chat_line(length=random.randint(5, 11)))
        else:
            out.append(str(a))
            out.append(str(b))
    while len(out) < n:
        if random.random() < 0.28:
            out.extend([
                garbled_chat_line(length=random.randint(5, 11)),
                garbled_chat_line(length=random.randint(5, 11)),
            ])
        else:
            a, b = random.choice(STROLL_CHAT_PAIRS)
            out.extend([str(a), str(b)])
    return out[:n]


def pick_stroll_filler_line() -> str:
    if random.random() < 0.28:
        return garbled_chat_line(length=random.randint(5, 11))
    a, b = random.choice(STROLL_CHAT_PAIRS)
    return str(random.choice((a, b)))


def plan_short_talk_varied(initiator_kind: str, other_kind: str, *, meet_count: int) -> dict:
    """寒暄 / 选题 / 轻深度 / 轻问答；乱码对加量；极少拌嘴。"""
    n = int(meet_count or 0)
    if n < LONG_TALK_MIN_MEETS:
        a0, b0 = dialogue_lines_for_pair(initiator_kind, other_kind, meet_count=n)
        return {"talk_kind": "short", "mode": "plain", "line1": a0, "line2": b0}
    # 约 28%：双方各一句乱码（气氛占位，可多一点）
    if random.random() < 0.28:
        g1 = garbled_chat_line(length=random.randint(5, 11))
        g2 = garbled_chat_line(length=random.randint(5, 11))
        return {
            "talk_kind": "short",
            "mode": "plain",
            "style": "garble",
            "line1": g1,
            "line2": g2,
            "initiator_line": g1,
            "reply_line": g2,
        }
    roll = random.random()
    if roll < 0.24:
        a0, b0 = dialogue_lines_for_pair(initiator_kind, other_kind, meet_count=n)
        return {"talk_kind": "short", "mode": "plain", "style": "greet", "line1": a0, "line2": b0}
    style_roll = random.random()
    # 闲聊为主：寒暄/选题/无厘头问答；深聊与软聊少一些
    if style_roll < 0.28:
        want = "greet"
    elif style_roll < 0.58:
        want = "topic"
    elif style_roll < 0.78:
        want = "qa"
    elif style_roll < 0.90:
        want = "deep"
    else:
        want = "soft"
    pool = [x for x in SHORT_TALK_VARIANTS if x[0] == want] or list(SHORT_TALK_VARIANTS)
    style, a, b = random.choice(pool)
    return {
        "talk_kind": "short",
        "mode": "plain",
        "style": style,
        "line1": a,
        "line2": b,
        "initiator_line": a,
        "reply_line": b,
    }


def plan_talk_session(
    presence_dir: Path,
    initiator_kind: str,
    other_kind: str,
    *,
    meet_count: int,
) -> dict:
    """短谈 / 知识点 / 长谈抽取（meet≥12）。问答偏少；吵架极稀有。"""
    n = int(meet_count or 0)
    if n < LONG_TALK_MIN_MEETS:
        return plan_short_talk_varied(initiator_kind, other_kind, meet_count=n)

    data = load(presence_dir)
    data = _tick_quiz_cooldown(data)
    try:
        save(presence_dir, data)
    except Exception:
        pass
    cool_until = int(data.get("quarrel_cool_until_ms") or 0)
    now = int(time.time() * 1000)
    hist = [str(x) for x in (data.get("long_history") or []) if str(x).strip()]
    last_long = hist[-1] if hist else ""
    last_mode = str(data.get("last_talk_mode") or "")
    roll = random.random()

    # 权重：短谈 ~34% / 长谈 ~46% / 知识点 ~20%
    if roll < 0.34:
        return plan_short_talk_varied(initiator_kind, other_kind, meet_count=n)
    if roll < 0.80:
        # 闲聊权重更高；深聊适量；吵架极低
        preferred = [
            "bond",
            "either_or",
            "hobby",
            "roleplay",
            "food",
            "gift",
            "game",
            "film",
            "weather",
            "deep",
            "self",
            "values",
            "dream",
            "books",
            "craft",
            "manners",
            "secret",
        ]
        pool = [x for x in preferred if x in LONG_TALK_SCENARIOS] or list(LONG_TALK_SCENARIOS.keys())
        if cool_until > now:
            pool = [x for x in pool if x != "quarrel"] or pool
        if last_long in pool and len(pool) > 1:
            pool = [x for x in pool if x != last_long]
        # 仅约 4% 抽到轻微别扭局
        if (
            cool_until <= now
            and "quarrel" in LONG_TALK_SCENARIOS
            and last_long != "quarrel"
            and random.random() < 0.04
        ):
            sid = "quarrel"
        else:
            weights = []
            for sid0 in pool:
                if sid0 in ("bond", "either_or", "hobby", "roleplay", "food", "gift", "game"):
                    weights.append(3.2)
                elif sid0 in ("deep", "self", "values", "dream", "film", "weather"):
                    weights.append(2.2)
                else:
                    weights.append(1.2)
            sid = random.choices(pool, weights=weights, k=1)[0]
        return plan_long_talk_scenario(presence_dir, sid)
    if last_mode == "tell" and random.random() < 0.85:
        return plan_short_talk_varied(initiator_kind, other_kind, meet_count=n)
    plan = plan_knowledge_talk(presence_dir, initiator_kind, other_kind, meet_count=n)
    plan.setdefault("talk_kind", "knowledge" if plan.get("mode") in ("tell", "quiz") else "short")
    return plan


def intro_script(self_kind: str, other_kind: str) -> tuple[str, ...]:
    other = PET_DISPLAY.get(other_kind, other_kind)
    self_n = PET_DISPLAY.get(self_kind, self_kind)
    if self_kind == KIND_EIDEN:
        return (
            f"……你好，我是{self_n}。",
            f"你是{other}吧？我们终于正式见面了。",
            "以后在桌面上碰面，就多多关照啦~",
            "我也会怕，也会笑——先从招呼开始。",
            f"从这边世界来的访客，就是我。请多指教，{other}。",
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
            f"嗨，{other}！看见你，心口就亮了一点。",
            f"{other}，碧岛的风还温柔吗？我是{self_n}。",
            f"原来{other}也会跑出来啊……你好呀，小太阳碰面。",
            f"诶，是{other}！要不要一起待会儿，暖一会儿？",
            f"{other}，旧货店今天忙吗？我刚穿过来喘口气。",
            f"跨世界打卡成功——目标：{other}。想把开心分你一半。",
            f"嗨嗨，{other}。姜汤带不过来，只能用问候顶上。",
            f"{other}！别紧张，我是来发光的，不是来抢箱子的。",
        )
    if self_kind == KIND_AOBA and other_kind == KIND_EIDEN:
        return (
            f"……{other}？你怎么也在这儿？看见你挺安心的。",
            f"嗨，{other}。旧货店今天客人少，到处逛逛也好。",
            f"{other}，欢迎来到碧岛……算是吧。要不要一起晒会儿？",
            f"桌面另一边是{other}啊，幸会~ 今天也请多指教。",
        )
    return (f"你好，{other}~", f"{self_n}遇见{other}了，心里暖暖的。")


def exchange_lines(self_kind: str, other_kind: str) -> tuple[str, ...]:
    other = PET_DISPLAY.get(other_kind, other_kind)
    if self_kind == KIND_EIDEN:
        return (
            f"今天{other}看起来精神不错，像带着小太阳。",
            "我这边刚忙完，过来透口气，也想被照一会儿。",
            "要是能一起去散步就好了……慢慢走也行。",
            f"{other}那边的风，闻起来比较安静，也好。",
            "见面先嘘寒问暖——这是我的社畜暖技能。",
            "下次带点见闻交换？我可以用甜点配方换安心。",
            f"有{other}在，桌面就不那么空了。",
            "要是累了就说，我听着。也可以一起发呆。",
        )
    return (
        f"莲说{other}看起来挺可靠的，我也这么觉得。",
        "平凡今天不算忙，可以多聊两句，暖一点。",
        "下次要不要交换各自世界的见闻？我想听温柔的那种。",
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
