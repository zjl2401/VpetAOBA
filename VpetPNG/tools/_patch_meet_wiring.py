"""Patch meet wiring: constants, init, speech/voice guards, drag refresh."""
from __future__ import annotations

import re
from pathlib import Path

TARGET = Path(__file__).resolve().parents[1] / "pet.py"


def main() -> None:
    text = TARGET.read_text(encoding="utf-8")

    if "MEET_PRIORITY_HOLD_MS =" not in text:
        const = (
            "\n# 相遇台词/反应占用窗口：期间自由语音与普通文本框让路\n"
            "MEET_PRIORITY_HOLD_MS = 4800\n"
            'MEET_PRIORITY_EVENTS = frozenset({"peer_meet", "crossover_meet"})\n'
            "# 相遇热区出现后：无点击且无对话框持续该时长 → 退出相遇模式\n"
            "MEET_IDLE_EXIT_MS = 10_000\n"
            "MEET_IDLE_CHECK_MS = 500\n"
        )
        text = text.replace(
            "def _user_persistent_root() -> Path:",
            const + "\n\ndef _user_persistent_root() -> Path:",
            1,
        )
        print("inserted MEET_* constants")

    if "self._meet_mode_on" not in text.split("def _meet_priority_active", 1)[0]:
        init = (
            "        self._meet_priority_until_ms: int = 0\n"
            "        self._meet_mode_on: bool = False\n"
            "        self._meet_mode_activity_ms: int = 0\n"
            "        self._meet_mode_allow_dialog_text: bool = False\n"
            "        self._meet_idle_job: str | None = None\n"
            "        self._crossover_bar_sig = None\n"
            "        self._crossover_bar_place_sig = None\n"
            "        self._crossover_bar_w = 0\n"
            "        self._meet_count_badge_win: tk.Toplevel | None = None\n"
            "        self._crossover_stroll_active: bool = False\n"
            "        self._crossover_long_choice_open: bool = False\n"
            "        self._live_peers_cache = None\n"
            "        self._crossover_hotspot_drag_ms: int = 0\n"
        )
        needle = "        self._crossover_meet_last_ms: int = 0\n"
        if needle in text and "self._meet_mode_on: bool = False" not in text:
            text = text.replace(needle, needle + init, 1)
            print("inserted meet init fields")

    # voice subtitle meet guards
    old_voice = '''    def _show_voice_subtitle(self, title: str, duration_ms: int, source: str = "vpet") -> None:
        """语音台词文本框：独立扁平窗；时长 = 语音 + 1s。与语音成对，强制显示标题框。"""
        display = (title or "").strip()'''
    new_voice = '''    def _show_voice_subtitle(self, title: str, duration_ms: int, source: str = "vpet") -> None:
        """语音台词文本框：独立扁平窗；时长 = 语音 + 1s。与语音成对，强制显示标题框。"""
        # 相遇模式：不要语音字幕（含普通自由语音）
        if self._in_crossover_meet_mode() or self._meet_priority_active():
            return
        if self._meet_priority_active() and self.speech_dialog and self.speech_dialog.winfo_exists():
            return
        display = (title or "").strip()'''
    if "相遇模式：不要语音字幕" not in text and old_voice in text:
        text = text.replace(old_voice, new_voice, 1)
        print("patched _show_voice_subtitle meet guards")

    # drag refresh
    old_drag_tail = '''        if self.state == "drag":
            direction = self._drag_move_dir(dx, dy)
            if direction:
                self._track_drag_spin(direction)
        # 工作态拖宠时旗在终点不动，禁止重建 overlay（会色键闪）'''
    new_drag_tail = '''        if self.state == "drag":
            direction = self._drag_move_dir(dx, dy)
            if direction:
                self._track_drag_spin(direction)
        # 拖近对方时立刻刷「遇」热区（不攒到松手/下一次慢轮询）
        try:
            now_ms = int(time.time() * 1000)
            last_ms = int(getattr(self, "_crossover_hotspot_drag_ms", 0) or 0)
            if now_ms - last_ms >= PEER_HOTSPOT_DRAG_REFRESH_MS:
                self._crossover_hotspot_drag_ms = now_ms
                self._refresh_crossover_hotspot_ui()
        except Exception:
            pass
        # 工作态拖宠时旗在终点不动，禁止重建 overlay（会色键闪）'''
    if "_crossover_hotspot_drag_ms" not in text.split("def _on_release", 1)[0][-800:] and old_drag_tail in text:
        text = text.replace(old_drag_tail, new_drag_tail, 1)
        print("patched _on_drag hotspot refresh")

    old_release_tail = '''        # 松手后立刻刷新跨宠靠近（拖动中不触发，避免「拖过去却没反应」）
        try:
            self._publish_peer_presence()
            near = self._nearest_crossover_peer()
            if near is not None:
                self._show_crossover_bar(near)
            else:
                self._hide_crossover_bar()
            self._maybe_trigger_peer_meet()
        except Exception:
            pass'''
    new_release_tail = '''        # 松手后立刻按距离显隐「遇」热区
        try:
            self._publish_peer_presence(force=True)
            self._refresh_crossover_hotspot_ui(force=True)
        except Exception:
            pass'''
    if old_release_tail in text:
        text = text.replace(old_release_tail, new_release_tail, 1)
        print("patched _on_release hotspot refresh")

    # _show_speech_dialog: add from_meet / bubble_tone
    sig_old = '''    def _show_speech_dialog(
        self,
        text: str,
        auto_hide_ms: int | None = None,
        *,
        on_complete=None,
        color: str = SPEECH_TEXT_FG,
        typewriter_ms: int | None = None,
        instant: bool = False,
        use_border5: bool = False,
        from_voice: bool = False,
        chat_role: str | None = None,
    ) -> None:
        if from_voice:
            self._cleanup_voice_subtitle_win()
            self._hide_speech_dialog()
            self._voice_subtitle_active = True
            self._speech_from_voice = True
        else:
            self._hide_voice_subtitle()
            self._hide_speech_dialog()
            self._speech_from_voice = False

        # 白底文本框：淡蓝字加深
        if str(color or "").strip().lower() in ("", str(SPEECH_FG_VPET).lower(), "#88ccff"):
            color = SPEECH_TEXT_FG

        self.speech_use_border5 = use_border5
        role = (chat_role or "").strip().lower() or None
        if role in ("pet", "eiden", "苍叶", "aoba"):
            role = "aoba"
        elif role in ("owner", "user", "me", "所属人"):
            role = "owner"
        self.speech_chat_role = role
        if role:
            # 头像气泡路径不用 border5
            self.speech_use_border5 = False
        self._speech_border5_peak = (0, 0)
        self._speech_border_layout_sig = None
        if not from_voice and str(getattr(self, "speech_bubble_tone", "") or "") != "meet":
            # 非见面路径清掉淡蓝标记，避免普通对话误用
            if str(color or "") != SPEECH_MEET_BUBBLE_FG:
                self.speech_bubble_tone = ""
        self.speech_dialog = tk.Toplevel(self.root)'''

    sig_new = '''    def _show_speech_dialog(
        self,
        text: str,
        auto_hide_ms: int | None = None,
        *,
        on_complete=None,
        color: str = SPEECH_TEXT_FG,
        typewriter_ms: int | None = None,
        instant: bool = False,
        use_border5: bool = False,
        from_voice: bool = False,
        from_meet: bool = False,
        bubble_tone: str | None = None,
        chat_role: str | None = None,
    ) -> None:
        # 相遇模式：禁普通文本；未点开「话」前也不要相遇短句；点开后的 from_meet 对话框才放行
        if self._in_crossover_meet_mode() or self._meet_priority_active():
            allow_meet_dialog = bool(from_meet) and bool(
                getattr(self, "_meet_mode_allow_dialog_text", False)
            )
            if not allow_meet_dialog:
                if callable(on_complete):
                    try:
                        on_complete()
                    except Exception:
                        pass
                return
            self._bump_meet_mode_activity()

        tone = str(bubble_tone or "").strip().lower()
        if tone in ("cyan", "meet", "blue"):
            self.speech_bubble_tone = "meet"
            use_border5 = False
            if str(color or "").strip().lower() in ("", str(SPEECH_FG_VPET).lower(), "#88ccff"):
                color = SPEECH_MEET_BUBBLE_FG
        elif not from_meet:
            # 非见面路径清掉淡蓝标记
            if str(color or "") != SPEECH_MEET_BUBBLE_FG:
                self.speech_bubble_tone = ""

        if from_voice:
            self._cleanup_voice_subtitle_win()
            self._hide_speech_dialog()
            self._voice_subtitle_active = True
            self._speech_from_voice = True
        else:
            self._hide_voice_subtitle()
            self._hide_speech_dialog()
            self._speech_from_voice = False

        # 白底文本框：淡蓝字加深（相遇淡蓝气泡用 SPEECH_MEET_BUBBLE_FG）
        if str(getattr(self, "speech_bubble_tone", "") or "").lower() not in ("meet", "cyan", "blue"):
            if str(color or "").strip().lower() in ("", str(SPEECH_FG_VPET).lower(), "#88ccff"):
                color = SPEECH_TEXT_FG

        self.speech_use_border5 = use_border5
        role = (chat_role or "").strip().lower() or None
        if role in ("pet", "eiden", "苍叶", "aoba"):
            role = "aoba"
        elif role in ("owner", "user", "me", "所属人"):
            role = "owner"
        self.speech_chat_role = role
        if role:
            # 头像气泡路径不用 border5
            self.speech_use_border5 = False
        self._speech_border5_peak = (0, 0)
        self._speech_border_layout_sig = None
        self.speech_dialog = tk.Toplevel(self.root)'''

    if "from_meet: bool = False" not in text and sig_old in text:
        text = text.replace(sig_old, sig_new, 1)
        print("patched _show_speech_dialog for meet")
    elif "from_meet: bool = False" in text:
        print("speech dialog already has from_meet")
    else:
        print("WARN: could not patch _show_speech_dialog signature")

    # meta banter meet priority (optional but important)
    # Find _maybe_meta_banter early return pattern from backup
    m = re.search(
        r"(def _maybe_meta_banter\(self, event: str.*?\n(?:.*?\n){0,40}?)",
        text,
    )
    if m and "MEET_PRIORITY_EVENTS" not in m.group(1):
        # insert after function start body first lines - look for a good anchor inside function
        pass

    # Patch common meta gate if present
    old_meta = None
    for cand in (
        '        if self.mode in ("loading", "game"):\n            return False\n',
        '        if str(event or "") in ("peer_meet", "crossover_meet"):\n',
    ):
        pass
    if "MEET_PRIORITY_EVENTS" not in text.split("def _maybe_meta_banter", 1)[-1][:1200]:
        insert_at = text.find("def _maybe_meta_banter")
        if insert_at >= 0:
            # find first line after docstring/body start that is an if
            body = text[insert_at : insert_at + 800]
            # inject after def line and optional docstring
            m2 = re.match(
                r"def _maybe_meta_banter\([^\)]*\)[^\n]*:\n(?:\s+\"\"\".*?\"\"\"\n)?",
                body,
                re.S,
            )
            if m2:
                gate = (
                    "        # 相遇优先：普通 meta 让路；相遇事件本身仍可出句\n"
                    "        if self._meet_priority_active() and str(event or \"\") not in MEET_PRIORITY_EVENTS:\n"
                    "            return False\n"
                )
                pos = insert_at + m2.end()
                text = text[:pos] + gate + text[pos:]
                print("patched _maybe_meta_banter meet priority")

    TARGET.write_text(text, encoding="utf-8")
    print("done", TARGET)


if __name__ == "__main__":
    main()
