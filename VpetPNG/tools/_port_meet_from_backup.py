"""Surgical: restore meet/crossover block from Aoba backup into current pet.py."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKUP = ROOT / "_broken_backup_20260912" / "pet.py"
TARGET = ROOT / "pet.py"


def method_map(lines: list[str]) -> dict[str, tuple[int, int]]:
    idxs: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        m = re.match(r"^    def (\w+)\(", line)
        if m:
            idxs.append((i, m.group(1)))
    out: dict[str, tuple[int, int]] = {}
    for j, (i, name) in enumerate(idxs):
        end = idxs[j + 1][0] if j + 1 < len(idxs) else len(lines)
        out[name] = (i, end)
    return out


def main() -> None:
    b_lines = BACKUP.read_text(encoding="utf-8").splitlines(keepends=True)
    a_lines = TARGET.read_text(encoding="utf-8").splitlines(keepends=True)
    bm = method_map(b_lines)
    am = method_map(a_lines)

    b_start = bm["_stop_peer_meet_poll"][0]
    b_end = bm["_screen_wh"][0]

    meetish = {
        "_stop_peer_meet_poll",
        "_start_peer_meet_poll",
        "_peer_meet_allowed",
        "_schedule_peer_meet_greet",
        "_normalize_meet_line",
        "_show_meet_speech",
        "_react_peer_meet",
        "_list_live_peers",
        "_peer_near",
        "_nearest_crossover_peer",
        "_nearest_any_peer",
        "_hide_crossover_bar",
        "_place_crossover_bar",
        "_make_crossover_hotspot",
        "_show_crossover_bar",
        "_hide_meet_count_badge",
        "_show_meet_count_badge",
        "_hide_crossover_pixel_bubble",
        "_show_crossover_pixel_bubble",
        "_record_crossover_meet",
        "_crossover_line_for_phase",
        "_crossover_manual_meet",
        "_open_ai_chat_with_keyword",
        "_peer_meet_tick",
        "_maybe_trigger_peer_meet",
    }
    a_start = am["_stop_peer_meet_poll"][0]
    if "_screen_wh" in am and am["_screen_wh"][0] > a_start:
        a_end = am["_screen_wh"][0]
    else:
        a_end = max(am[n][1] for n in meetish if n in am)

    block = b_lines[b_start:b_end]
    if "_selecttalk_player" in am and "_selecttalk_player" in bm:
        sel_b_s, sel_b_e = bm["_selecttalk_player"]
        sel_a_s, sel_a_e = am["_selecttalk_player"]
        if b_start <= sel_b_s < b_end:
            block = (
                b_lines[b_start:sel_b_s]
                + a_lines[sel_a_s:sel_a_e]
                + b_lines[sel_b_e:b_end]
            )
            print("preserved target _selecttalk_player")

    print(f"backup block {b_start + 1}..{b_end} ({b_end - b_start} lines)")
    print(f"target block {a_start + 1}..{a_end} ({a_end - a_start} lines)")

    text = "".join(a_lines[:a_start] + block + a_lines[a_end:])

    # import crossover_hotspot_photo
    if "crossover_hotspot_photo" not in text or (
        "crossover_hotspot_photo(" in text
        and not re.search(r"crossover_hotspot_photo\s*[,)]", text.split("def ", 1)[0])
    ):
        m = re.search(r"from panel_decor import \((.*?)\)", text, re.S)
        if m and "crossover_hotspot_photo" not in m.group(1):
            text = (
                text[: m.end(1)].rstrip()
                + ",\n    crossover_hotspot_photo,\n"
                + text[m.end(1) :]
            )
            print("added import crossover_hotspot_photo (paren)")
        else:
            m2 = re.search(r"from panel_decor import ([^\n]+)", text)
            if m2 and "crossover_hotspot_photo" not in m2.group(0):
                text = text[: m2.end()] + ", crossover_hotspot_photo" + text[m2.end() :]
                print("added import crossover_hotspot_photo (inline)")

    if "MEET_PRIORITY_HOLD_MS" not in text:
        const_block = (
            "MEET_PRIORITY_HOLD_MS = 4800\n"
            'MEET_PRIORITY_EVENTS = frozenset({"peer_meet", "crossover_meet"})\n'
            "# 相遇热区出现后：无点击且无对话框持续该时长 → 退出相遇模式\n"
            "MEET_IDLE_EXIT_MS = 10_000\n"
            "MEET_IDLE_CHECK_MS = 500\n"
        )
        for mark in ("PEER_STALE_MS", "PEER_PRESENCE_DIR", "PEER_KIND ="):
            idx = text.find(mark)
            if idx >= 0:
                nl = text.find("\n", idx)
                text = text[: nl + 1] + const_block + text[nl + 1 :]
                print("inserted MEET_* constants after", mark)
                break

    if "PEER_HOTSPOT_DRAG_REFRESH_MS" not in text:
        for mark in ("PEER_MEET_POLL_MS", "PEER_STALE_MS"):
            idx = text.find(mark)
            if idx >= 0:
                nl = text.find("\n", idx)
                text = text[: nl + 1] + "PEER_HOTSPOT_DRAG_REFRESH_MS = 90\n" + text[nl + 1 :]
                print("inserted PEER_HOTSPOT_DRAG_REFRESH_MS")
                break

    text = re.sub(
        r'SPEECH_MEET_BUBBLE_FILL = "[^"]+"',
        'SPEECH_MEET_BUBBLE_FILL = "#E0F0FF"',
        text,
        count=1,
    )
    text = re.sub(
        r'SPEECH_MEET_BUBBLE_STROKE = "[^"]+"',
        'SPEECH_MEET_BUBBLE_STROKE = "#9EC8E8"',
        text,
        count=1,
    )
    if "SPEECH_MEET_BUBBLE_SHADOW" not in text:
        text = text.replace(
            'SPEECH_MEET_BUBBLE_STROKE = "#9EC8E8"',
            'SPEECH_MEET_BUBBLE_STROKE = "#9EC8E8"\nSPEECH_MEET_BUBBLE_SHADOW = "#C8E0F4"',
            1,
        )
    else:
        text = re.sub(
            r'SPEECH_MEET_BUBBLE_SHADOW = "[^"]+"',
            'SPEECH_MEET_BUBBLE_SHADOW = "#C8E0F4"',
            text,
            count=1,
        )
    text = re.sub(
        r'SPEECH_MEET_BUBBLE_FG = "[^"]+"',
        'SPEECH_MEET_BUBBLE_FG = "#1e3a5c"',
        text,
        count=1,
    )
    print(re.search(r'SPEECH_MEET_BUBBLE_FILL = "[^"]+"', text).group(0))

    if "_meet_mode_on" not in text:
        init_snip = (
            "        self._meet_priority_until_ms: int = 0\n"
            "        # 相遇模式：热区可见 / 配对等待；期间禁普通文本与语音字幕，闲置自动退出\n"
            "        self._meet_mode_on: bool = False\n"
            "        self._meet_mode_activity_ms: int = 0\n"
            "        self._meet_mode_allow_dialog_text: bool = False\n"
            "        self._meet_idle_job: str | None = None\n"
        )
        m = re.search(r"self\._crossover_meet_last_ms: int = 0\n", text)
        if not m:
            m = re.search(r"self\._peer_meet_last_ms: int = 0\n", text)
            if m and "self._crossover_meet_last_ms" not in text:
                text = (
                    text[: m.end()]
                    + "        self._crossover_meet_last_ms: int = 0\n"
                    + text[m.end() :]
                )
                m = re.search(r"self\._crossover_meet_last_ms: int = 0\n", text)
        if m:
            text = text[: m.end()] + init_snip + text[m.end() :]
            print("inserted meet mode init fields")

    need_inits = [
        ("self._crossover_bar_sig", "        self._crossover_bar_sig = None\n"),
        ("self._crossover_bar_place_sig", "        self._crossover_bar_place_sig = None\n"),
        ("self._crossover_bar_w", "        self._crossover_bar_w = 0\n"),
        ("self._meet_count_badge_win", "        self._meet_count_badge_win: tk.Toplevel | None = None\n"),
        ("self._crossover_stroll_active", "        self._crossover_stroll_active: bool = False\n"),
        ("self._crossover_long_choice_open", "        self._crossover_long_choice_open: bool = False\n"),
        ("self._live_peers_cache", "        self._live_peers_cache = None\n"),
        ("self._crossover_session_job", "        self._crossover_session_job: str | None = None\n"),
        ("self._crossover_quiz_win", "        self.crossover_quiz_win = None\n"),
        ("self._crossover_long_choice_win", "        self.crossover_long_choice_win = None\n"),
    ]
    anchor = re.search(r"self\._meet_mode_on: bool = False\n", text) or re.search(
        r"self\._peer_meet_last_ms: int = 0\n", text
    )
    if anchor:
        add = "".join(line for key, line in need_inits if key not in text)
        if add:
            text = text[: anchor.end()] + add + text[anchor.end() :]
            print("added extra inits")

    TARGET.write_text(text, encoding="utf-8")
    print("wrote", TARGET, "lines", len(text.splitlines()))


if __name__ == "__main__":
    main()
