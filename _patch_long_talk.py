# -*- coding: utf-8 -*-
"""Patch peer_friendship long-talk scenarios + coherent stroll pairs (both pets)."""
from __future__ import annotations

from pathlib import Path

SCENARIO_BLOCK = r'''
# —— 长谈情景（实词开场 → 乱码氛围 → selecttalk 选择）——
LONG_TALK_MIN_MEETS = 12

LONG_TALK_SCENARIOS: dict[str, dict] = {
    "bond": {
        "mood_hint": "似乎聊得很投缘",
        "mood_fmt": "似乎聊得很投缘（关于「{topic}」）",
        "topics": ("今天的小事", "各自世界的差别", "一起发呆", "旧货店与旅途"),
        "mood_emote": "like",
        "open_lines": (
            ("今天天气不错呢。", "嗯，适合随便走走，顺便聊聊。"),
            ("最近有什么开心的事吗？", "有啊……比如现在这样聊天。"),
            ("你那边世界和这边差很多吗？", "差很多，但人的感觉挺像的。"),
            ("要不要交换一个小秘密？", "……可以，但别笑我太傻。"),
        ),
        "choices": (
            {"id": "listen", "label": "继续听", "icon": "listen", "asset": ("outfit", "star"), "delta": 0.9, "reply": "那就再多说一会儿吧。", "outcome": "继续听了下去", "emote": "like"},
            {"id": "joke", "label": "开玩笑", "icon": "joke", "asset": ("outfit", "question"), "delta": 0.6, "reply": "噗……你这人真好玩。", "outcome": "被一句玩笑逗乐了", "emote": "wink"},
            {"id": "serious", "label": "认真回应", "icon": "serious", "asset": ("outfit", "leaf"), "delta": 1.1, "reply": "嗯，我记住了。", "outcome": "认真地把话收下了", "emote": "like"},
        ),
    },
    "quarrel": {
        "mood_hint": "似乎发生了争吵",
        "mood_fmt": "似乎因为「{topic}」发生了争吵",
        "topics": ("走路太慢", "谁先开口", "听不懂的笑话", "抢半步", "耳机音量", "随口一句话"),
        "mood_emote": "angry",
        "open_lines": (
            ("你刚才那句话……是什么意思？", "我只是随口一说，你别想太多。"),
            ("有点不太开心。", "……我也觉得气氛怪怪的。"),
            ("我们是不是想岔了？", "也许吧。要不把话说清楚？"),
            ("你总是抢半步，我会跟丢的。", "那你走快点啊……好吧，我放慢。"),
        ),
        "choices": (
            {"id": "cold", "label": "冷战", "icon": "cold", "asset": ("outfit", "droplet"), "delta": -1.0, "reply": "……那就先各自冷静一下。", "outcome": "陷入了冷战", "emote": "speechless", "cool_quarrel": True},
            {"id": "peace", "label": "和解", "icon": "peace", "asset": ("outfit", "heart"), "delta": 2.2, "reply": "对不起。我们和好吧。", "outcome": "达成了和解", "emote": "like"},
            {"id": "break", "label": "闹掰", "icon": "breakup", "asset": ("outfit", "angry_mark"), "delta": -2.0, "reply": "……先这样吧。", "outcome": "闹掰了", "emote": "angry", "cool_quarrel": True},
        ),
    },
    "food": {
        "mood_hint": "似乎在点单",
        "mood_fmt": "似乎在商量吃「{topic}」",
        "topics": ("夜宵", "甜品", "路边摊", "热汤"),
        "mood_emote": "idea",
        "open_lines": (
            ("突然有点饿了……想吃什么？", "嗯……你选吧，我都行。"),
            ("要不要一起决定吃的？", "好啊，我听听你的。"),
            ("如果现在能点外卖，你点啥？", "这个嘛……让我想想。"),
            ("热汤还是甜点？你先说。", "我想要……两边都想要。"),
        ),
        "choices": (
            {"id": "ramen", "label": "拉面", "icon": "ramen", "asset": ("food", "ramen"), "delta": 0.8, "reply": "那就拉面！热乎乎的。", "outcome": "决定吃拉面", "emote": "like"},
            {"id": "onigiri", "label": "饭团", "icon": "bento", "asset": ("food", "onigiri"), "delta": 0.8, "reply": "饭团稳妥，吃完还能散步。", "outcome": "决定吃饭团", "emote": "like"},
            {"id": "cake", "label": "蛋糕", "icon": "cake", "asset": ("food", "cake"), "delta": 0.8, "reply": "甜点治愈一切！", "outcome": "决定吃蛋糕", "emote": "wink"},
        ),
    },
    "weather": {
        "mood_hint": "似乎在聊天气",
        "mood_fmt": "似乎在聊「{topic}」",
        "topics": ("忽然下雨", "海风", "阴天发呆", "阳光刺眼"),
        "mood_emote": "question",
        "open_lines": (
            ("你那边也会突然下雨吗？", "会。有时来得比心情还快。"),
            ("今天风有点大。", "那就并肩挡一下风吧。"),
            ("阴天适合发呆。", "嗯，发呆也算正经事。"),
        ),
        "choices": (
            {"id": "listen", "label": "听下去", "icon": "listen", "asset": ("outfit", "droplet"), "delta": 0.7, "reply": "那就多听一会儿风声。", "outcome": "安静听完了", "emote": "like"},
            {"id": "joke", "label": "吐槽天气", "icon": "joke", "asset": ("outfit", "question"), "delta": 0.5, "reply": "天气脾气比人还大。", "outcome": "把天气吐槽了一通", "emote": "wink"},
            {"id": "serious", "label": "关心对方", "icon": "serious", "asset": ("outfit", "heart"), "delta": 1.0, "reply": "别着凉，靠近一点。", "outcome": "互相叮嘱了一句", "emote": "like"},
        ),
    },
    "gift": {
        "mood_hint": "似乎在谈礼物",
        "mood_fmt": "似乎在聊「{topic}」该不该送",
        "topics": ("一颗糖", "小徽章", "手写小纸条", "多余的零件"),
        "mood_emote": "shy",
        "open_lines": (
            ("我口袋里有点东西……给你也行。", "诶？突然送礼我会紧张。"),
            ("要是跨世界能寄快递就好了。", "那邮费得按心情算。"),
            ("你更想要实用的，还是可爱的？", "……我想要记得住的。"),
        ),
        "choices": (
            {"id": "listen", "label": "收下", "icon": "listen", "asset": ("outfit", "star"), "delta": 1.0, "reply": "那就谢谢啦。我会收好。", "outcome": "收下了心意", "emote": "like"},
            {"id": "joke", "label": "害羞推脱", "icon": "joke", "asset": ("outfit", "question"), "delta": 0.5, "reply": "太突然了……下次提前说！", "outcome": "害羞地推脱了一下", "emote": "awkward"},
            {"id": "serious", "label": "回礼约定", "icon": "serious", "asset": ("outfit", "leaf"), "delta": 1.2, "reply": "下次我也给你带一样。", "outcome": "约好了回礼", "emote": "like"},
        ),
    },
    "game": {
        "mood_hint": "似乎在比试什么",
        "mood_fmt": "似乎在比「{topic}」",
        "topics": ("谁先走到边", "石头剪刀布", "数步数", "谁更会发呆"),
        "mood_emote": "idea",
        "open_lines": (
            ("比比谁先走到屏幕边？", "来啊，输的请对方喝虚拟饮料。"),
            ("石头剪刀布，三局两胜。", "我可是会认真出的。"),
            ("数到二十换方向，犯规要说。", "行，我盯着你。"),
        ),
        "choices": (
            {"id": "listen", "label": "认输", "icon": "listen", "asset": ("outfit", "droplet"), "delta": 0.6, "reply": "好好好，你赢。", "outcome": "笑着认输了", "emote": "awkward"},
            {"id": "joke", "label": "再来一局", "icon": "joke", "asset": ("outfit", "question"), "delta": 0.8, "reply": "一局不算！再来！", "outcome": "约了再来一局", "emote": "wink"},
            {"id": "serious", "label": "公平裁判", "icon": "serious", "asset": ("outfit", "star"), "delta": 0.9, "reply": "平局也行，开心最重要。", "outcome": "宣布平局收场", "emote": "like"},
        ),
    },
    "secret": {
        "mood_hint": "似乎在说悄悄话",
        "mood_fmt": "似乎在说关于「{topic}」的悄悄话",
        "topics": ("怕黑", "想家", "小梦想", "不敢说的名字"),
        "mood_emote": "shy",
        "open_lines": (
            ("其实我有时也会怕。", "……谢谢你告诉我。"),
            ("有个名字，我还不太敢喊出口。", "那就不喊，先放在心里。"),
            ("想家的时候，你会做什么？", "发呆。或者找人并肩走走。"),
        ),
        "choices": (
            {"id": "listen", "label": "安静听", "icon": "listen", "asset": ("outfit", "leaf"), "delta": 1.0, "reply": "我听着，不催你。", "outcome": "安静听完了悄悄话", "emote": "like"},
            {"id": "joke", "label": "轻轻化解", "icon": "joke", "asset": ("outfit", "star"), "delta": 0.7, "reply": "那我们一起当一点点勇敢。", "outcome": "把气氛轻轻化解了", "emote": "wink"},
            {"id": "serious", "label": "郑重答应", "icon": "serious", "asset": ("outfit", "heart"), "delta": 1.3, "reply": "我替你保密。真的。", "outcome": "郑重答应保密", "emote": "like"},
        ),
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
    topic = str(topic or "").strip()
    fmt = str(sc.get("mood_fmt") or sc.get("mood_hint") or "").strip()
    if topic and "{topic}" in fmt:
        return fmt.format(topic=topic)
    base = str(sc.get("mood_hint") or fmt or "似乎在聊天")
    if topic:
        return f"{base}（关于「{topic}」）"
    return base


def format_long_outcome(choice: dict | None, topic: str = "") -> str:
    if not isinstance(choice, dict):
        return ""
    topic = str(topic or "").strip()
    oc = str(choice.get("outcome") or choice.get("label") or "").strip()
    if not oc:
        return ""
    if topic:
        return f"关于「{topic}」，{oc}"
    return oc
'''

# Note: the SCENARIO_BLOCK above uses random - need import already in file

STROLL_BLOCK = r'''
STROLL_OPEN_LINES: tuple[tuple[str, str], ...] = (
    ("走吧，随便转转。", "嗯，并肩走走也好。"),
    ("这边风还挺轻的。", "别走太快，我跟得上。"),
    ("要不要绕着屏幕边走一圈？", "可以啊，当散步打卡。"),
    ("并肩的时候……好像安静一点。", "那就安静地走一会儿。"),
    ("先往右边走走？", "好，你定方向，我跟着。"),
)

# 成对续聊：问句/陈述 ↔ 贴合回应，避免前言不搭后语
STROLL_CHAT_PAIRS: tuple[tuple[str, str], ...] = (
    ("这边风景还不错。", "嗯，比一个人看有意思。"),
    ("刚才差点撞到图标。", "哈哈，下次我提醒你。"),
    ("你平时都往哪边闲逛？", "看心情……有时绕圈，有时发呆。"),
    ("走累了就停一下也行。", "好，那就慢慢来，不赶。"),
    ("要不要数步数？", "数到二十再换方向吧。"),
    ("你脚步好稳。", "你也别掉队就行。"),
    ("……其实有点开心。", "我也是。别告诉别人。"),
    ("说起来，今天气氛挺轻松。", "嗯，并肩就不那么闷。"),
    ("左边好像更安静。", "那我们往左边靠一点。"),
    ("要是能并排喝一杯就好了。", "下次用想象的杯子干杯。"),
)


def pick_stroll_open_lines() -> tuple[str, str]:
    pair = random.choice(STROLL_OPEN_LINES)
    return str(pair[0]), str(pair[1])


def plan_stroll_chat_script(*, count: int = 6) -> list[str]:
    """并肩散步：成对实词脚本（交替说，语义连贯）。"""
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
        out.append(str(a))
        out.append(str(b))
    while len(out) < n:
        a, b = random.choice(STROLL_CHAT_PAIRS)
        out.extend([str(a), str(b)])
    return out[:n]


def pick_stroll_filler_line() -> str:
    a, b = random.choice(STROLL_CHAT_PAIRS)
    return str(random.choice((a, b)))
'''


def replace_between(text: str, start_marker: str, end_marker: str, new_mid: str) -> str:
    i = text.find(start_marker)
    if i < 0:
        raise SystemExit(f"start not found: {start_marker[:40]}")
    j = text.find(end_marker, i + len(start_marker))
    if j < 0:
        raise SystemExit(f"end not found after start: {end_marker[:40]}")
    return text[:i] + new_mid + text[j:]


def patch_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    # Replace LONG_TALK block through apply_long_talk_choice start — keep apply function
    start = "# —— 长谈情景"
    # Find apply_long_talk_choice after long_scenario
    mid_end = "def apply_long_talk_choice"
    i = text.find(start)
    j = text.find(mid_end, i)
    if i < 0 or j < 0:
        raise SystemExit(f"{path}: long talk markers missing")
    # Keep apply_long_talk_choice as-is but update to store topic if needed later
    text = text[:i] + SCENARIO_BLOCK.strip() + "\n\n\n" + text[j:]

    # Replace stroll open/chat section
    s2 = "STROLL_OPEN_LINES:"
    # end at plan_short_talk_varied or pick_stroll_open if duplicated
    # After our insert we may have duplicate pick_stroll / plan_stroll — remove old STROLL_CHAT_LINES block
    i2 = text.find(s2)
    if i2 < 0:
        raise SystemExit(f"{path}: STROLL_OPEN missing")
    # Find next def plan_short_talk_varied OR def pick_stroll_open_lines after STROLL
    # Prefer ending before plan_short_talk_varied if it comes after; else before plan_talk_session
    candidates = []
    for marker in ("def plan_short_talk_varied", "def plan_talk_session", "def intro_script"):
        k = text.find(marker, i2 + 10)
        if k > 0:
            candidates.append(k)
    if not candidates:
        raise SystemExit(f"{path}: no end for stroll block")
    j2 = min(candidates)
    # If pick_stroll_open_lines / plan_stroll already exist after j2, leave them; our STROLL_BLOCK includes them
    # Remove duplicate defs that follow
    text = text[:i2] + STROLL_BLOCK.strip() + "\n\n\n" + text[j2:]

    # Deduplicate pick_stroll_open_lines / plan_stroll_chat_script / pick_stroll_filler_line
    for fname in ("pick_stroll_open_lines", "plan_stroll_chat_script", "pick_stroll_filler_line"):
        first = text.find(f"def {fname}")
        if first < 0:
            continue
        second = text.find(f"def {fname}", first + 10)
        while second > 0:
            # delete from second def until next def at same indent
            nxt = text.find("\ndef ", second + 4)
            if nxt < 0:
                text = text[:second]
                break
            text = text[:second] + text[nxt + 1 :]
            second = text.find(f"def {fname}", first + 10)

    # Patch plan_talk_session long branch to include topic
    old_long_return = '''        sc = LONG_TALK_SCENARIOS[sid]
        pair = random.choice(list(sc.get("open_lines") or (("……", "……"),)))
        return {
            "talk_kind": "long",
            "mode": "long",
            "long_scenario_id": sid,
            "long_phase": "open",
            "garble_left": 4,
            "mood_hint": str(sc.get("mood_hint") or ""),
            "line1": str(pair[0]),
            "line2": str(pair[1]),
            "initiator_line": str(pair[0]),
            "reply_line": str(pair[1]),
        }'''
    new_long_return = '''        sc = LONG_TALK_SCENARIOS[sid]
        topic = pick_long_topic(sc)
        pair = random.choice(list(sc.get("open_lines") or (("……", "……"),)))
        return {
            "talk_kind": "long",
            "mode": "long",
            "long_scenario_id": sid,
            "long_phase": "open",
            "garble_left": 4,
            "long_topic": topic,
            "mood_hint": format_mood_hint(sc, topic),
            "mood_emote": str(sc.get("mood_emote") or ""),
            "line1": str(pair[0]),
            "line2": str(pair[1]),
            "initiator_line": str(pair[0]),
            "reply_line": str(pair[1]),
        }'''
    if old_long_return not in text:
        # Aoba may have open_extra
        old_long_return2 = old_long_return.replace(
            '            "reply_line": str(pair[1]),\n        }',
            '            "reply_line": str(pair[1]),\n            "open_extra": [],\n        }',
        )
        if old_long_return2 in text:
            new_long_return2 = new_long_return.replace(
                '            "reply_line": str(pair[1]),\n        }',
                '            "reply_line": str(pair[1]),\n            "open_extra": [],\n        }',
            )
            text = text.replace(old_long_return2, new_long_return2)
        else:
            print(f"WARN: long return not exact in {path.name}, trying loose replace")
            if '"mood_hint": str(sc.get("mood_hint") or ""),' in text:
                text = text.replace(
                    '"mood_hint": str(sc.get("mood_hint") or ""),',
                    '"long_topic": pick_long_topic(sc),\n            "mood_hint": format_mood_hint(sc, locals().get("topic") or pick_long_topic(sc)),\n            "mood_emote": str(sc.get("mood_emote") or ""),',
                    1,
                )
                # Fix: need topic variable — inject before pair
                text = text.replace(
                    "sc = LONG_TALK_SCENARIOS[sid]\n        pair = random.choice",
                    "sc = LONG_TALK_SCENARIOS[sid]\n        topic = pick_long_topic(sc)\n        pair = random.choice",
                    1,
                )
                text = text.replace(
                    "format_mood_hint(sc, locals().get(\"topic\") or pick_long_topic(sc))",
                    "format_mood_hint(sc, topic)",
                )
    else:
        text = text.replace(old_long_return, new_long_return)

    path.write_text(text, encoding="utf-8")
    print("patched", path)


def main() -> None:
    roots = [
        Path(r"C:\Users\36255\Desktop\VpetEidenPet\peer_friendship.py"),
        Path(r"C:\Users\36255\Desktop\VpetAOBA\VpetPNG\peer_friendship.py"),
    ]
    for p in roots:
        patch_file(p)


if __name__ == "__main__":
    main()
