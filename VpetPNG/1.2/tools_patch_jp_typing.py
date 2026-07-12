# -*- coding: utf-8 -*-
"""Patch Japanese typing modes into pet.py."""
from pathlib import Path

path = Path(__file__).resolve().parent / "pet.py"
text = path.read_text(encoding="utf-8")

old_start = '''    def _start_typing_game(self, lang: str) -> None:
        self._hide_main_menu()
        if lang == JAPANESE_LANG_LABEL and not _japanese_bank_available():
            self._show_toast("此功能暂不开放", "#ff8844")
            return
        pool = _load_typing_bank(lang)
        if not pool:
            self._show_toast("该语言词库为空", "#ff8844")
            return

        def start() -> None:
            self._start_game_countdown(lambda: self._begin_typing_game(lang))

        def after_guide() -> None:
            self._request_mode_switch(start)

        self._ensure_first_play_guide("typing", after_guide)
'''

new_start = '''    def _start_typing_game(self, lang: str, *, jp_mode: str | None = None) -> None:
        self._hide_main_menu()
        if lang == JAPANESE_LANG_LABEL and not _japanese_bank_available():
            self._show_toast("此功能暂不开放", "#ff8844")
            return
        pool = _load_typing_bank(lang)
        if lang == JAPANESE_LANG_LABEL:
            mode = jp_mode or JP_TYPING_MODE_KANA
            pool = _filter_jp_typing_pool(pool, mode)
        if not pool:
            self._show_toast("该语言词库为空", "#ff8844")
            return
        mode_for_game = jp_mode if lang == JAPANESE_LANG_LABEL else None

        def start() -> None:
            self._start_game_countdown(lambda: self._begin_typing_game(lang, jp_mode=mode_for_game))

        def after_guide() -> None:
            self._request_mode_switch(start)

        self._ensure_first_play_guide("typing", after_guide)
'''

if old_start not in text:
    raise SystemExit("start block not found")
text = text.replace(old_start, new_start, 1)

# Replace begin method body by markers
begin_marker = "    def _begin_typing_game(self, lang: str) -> None:"
end_marker = "    def _close_vocab_game(self, *, resume: bool = True) -> None:"
i0 = text.find(begin_marker)
i1 = text.find(end_marker)
if i0 < 0 or i1 < 0 or i1 <= i0:
    raise SystemExit(f"markers not found {i0} {i1}")

new_begin = r'''    def _begin_typing_game(self, lang: str, *, jp_mode: str | None = None) -> None:
        pool = _load_typing_bank(lang)
        if lang == JAPANESE_LANG_LABEL:
            jp_mode = jp_mode or JP_TYPING_MODE_KANA
            pool = _filter_jp_typing_pool(pool, jp_mode)
        else:
            jp_mode = None
        if not pool:
            self._show_toast("该语言词库为空", "#ff8844")
            self._resume_idle_after_activity()
            return
        self._close_typing_game(resume=False)
        try:
            _get_type_sound()
        except Exception:
            pass
        end_ms = int(time.time() * 1000) + TYPING_GAME_MS
        state = {"score": 0, "typed": "", "phase": 0, "done": False, "kb_tick": 0, "jp_mode": jp_mode}
        item0 = random.choice(pool)

        mode_title = lang
        if lang == JAPANESE_LANG_LABEL:
            mode_title = "日语·罗马音" if jp_mode == JP_TYPING_MODE_ROMAJI else "日语·假名"

        self.typing_game_win = tk.Toplevel(self.root)
        self.typing_game_win.title(f"打字 · {mode_title}")
        self.typing_game_win.attributes("-topmost", True)
        self.typing_game_win.configure(bg=MENU_BG)
        self.typing_game_win.protocol("WM_DELETE_WINDOW", self._close_typing_game)

        frame = tk.Frame(self.typing_game_win, bg=MENU_BG, padx=12, pady=10)
        frame.pack()
        mood_row = tk.Frame(frame, bg=MENU_BG)
        mood_row.pack(fill=tk.X, pady=(0, 6))
        mood_label = tk.Label(mood_row, bg=MENU_BG)
        mood_label.pack()
        tk.Label(frame, text=f"打字 · {mode_title}（30s）", font=PIXEL_FONT, fg=PIXEL_COLOR, bg=MENU_BG).pack(anchor=tk.W)
        grade_bar = tk.Canvas(frame, width=300, height=TYPING_GRADE_BAR_H, bg=MENU_BG, highlightthickness=0)
        grade_bar.pack(fill=tk.X, pady=(4, 6))
        timer_label = tk.Label(frame, text="30s", font=PIXEL_FONT, fg="#ffcc44", bg=MENU_BG)
        timer_label.pack(anchor=tk.W)
        score_label = tk.Label(frame, text="得分 0  评级 D", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG)
        score_label.pack(anchor=tk.W)
        word_label = tk.Label(frame, text="", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG, wraplength=320, justify=tk.LEFT)
        word_label.pack(anchor=tk.W, pady=(6, 4))
        kb = tk.Canvas(frame, width=300, height=92, bg="#222233", highlightthickness=0)
        kb.pack(pady=4)
        if lang == JAPANESE_LANG_LABEL and jp_mode == JP_TYPING_MODE_ROMAJI:
            hint_text = "请输入纯字母罗马音全称（例：asatte / konnichiwa）"
        elif lang == JAPANESE_LANG_LABEL:
            hint_text = "请输入平假名或片假名（例：あさって / アサッテ）"
        elif lang == "中文":
            hint_text = "可输拼音，或用输入法直接打汉字"
        else:
            hint_text = "请对照键盘输入英文"
        hint = tk.Label(frame, text=hint_text, font=PIXEL_FONT, fg="#888888", bg=MENU_BG, wraplength=320, justify=tk.LEFT)
        hint.pack(anchor=tk.W)
        entry_wrap = tk.Frame(frame, bg="#88ccff", padx=2, pady=2)
        entry_wrap.pack(fill=tk.X, pady=6)
        entry = tk.Entry(
            entry_wrap,
            width=28,
            font=PIXEL_FONT,
            bg="#1a1a22",
            fg="#ffffff",
            insertbackground="#88ffaa",
            relief=tk.FLAT,
        )
        entry.pack(fill=tk.X, ipady=4)
        result = tk.Label(frame, text="", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG)
        result.pack(pady=2)

        def apply_item(it: dict[str, str]) -> None:
            display = str(it.get("display", ""))
            kana = str(it.get("target", "") or "").strip()
            roma = _romaji_letters_only(it.get("romaji", "") or "")
            meaning = _jp_typing_prompt_meaning(display)
            state["display"] = display
            state["meaning"] = meaning
            state["kana"] = kana
            state["romaji"] = roma
            state["typed"] = ""
            if jp_mode == JP_TYPING_MODE_ROMAJI:
                state["target"] = roma
                state["target_l"] = roma
                word_label.config(text=f"提示：{meaning}\n请输入罗马音：{roma}")
            elif jp_mode == JP_TYPING_MODE_KANA:
                state["target"] = kana
                state["target_l"] = _kana_to_hiragana(kana)
                state["target_kata"] = _kana_to_katakana(kana)
                word_label.config(text=f"提示：{meaning}\n请输入假名：{kana}")
            else:
                state["target"] = str(it.get("target", ""))
                state["target_l"] = state["target"].lower()
                word_label.config(text=f"输入：{display}")
            entry.delete(0, tk.END)

        def next_word() -> None:
            apply_item(random.choice(pool))

        apply_item(item0)

        def update_grade_ui() -> None:
            grade = _typing_grade(state["score"])
            score_label.config(text=f"得分 {state['score']}  评级 {grade}")
            _draw_typing_grade_bar(grade_bar, 300, TYPING_GRADE_BAR_H, state["score"])
            photo = self._typing_mood_photo(grade)
            mood_label.config(image=photo)
            mood_label.image = photo

        def refresh_kb() -> None:
            nxt = None
            typed = state["typed"]
            if jp_mode == JP_TYPING_MODE_ROMAJI:
                guide = state.get("romaji") or ""
            elif jp_mode == JP_TYPING_MODE_KANA:
                guide = ""
            else:
                guide = state.get("target_l") or ""
            if guide and len(typed) < len(guide) and (not typed or str(typed).isascii()):
                nxt = guide[len(typed)]
            hk = _key_for_char(nxt) if nxt else None
            _draw_typing_keyboard(kb, 300, 92, hk, state["phase"])
            state["phase"] += 1

        def finish_game() -> None:
            if state["done"]:
                return
            state["done"] = True
            try:
                self.typing_game_win.grab_release()
            except Exception:
                pass
            grade = _typing_grade(state["score"])
            self._save_game_record(
                "typing",
                {
                    "lang": lang,
                    "jp_mode": jp_mode or "",
                    "score": state["score"],
                    "grade": grade,
                    "difficulty": self.difficulty,
                },
            )
            self.mood = min(100, self.mood + min(5, state["score"] // 4))
            self._refresh_panel()
            result.config(text=f"时间到！得分 {state['score']}  评级 {grade}", fg="#88ccff")
            update_grade_ui()
            grade_colors = {g: c for g, _t, c in TYPING_GRADE_TIERS}
            grade_color = grade_colors.get(grade, "#88ccff")
            self._show_game_clear(
                title=f"得分 {state['score']}",
                subtitle=f"{mode_title} · 打字练习",
                accent=grade_color,
                hero_grade=grade,
                hero_color=grade_color,
                hold_ms=TYPING_CLEAR_HOLD_MS,
                on_done=self._close_typing_game,
            )

        def tick_timer() -> None:
            if state["done"] or not self.typing_game_win or not self.typing_game_win.winfo_exists():
                return
            left = max(0, end_ms - int(time.time() * 1000))
            timer_label.config(text=f"{left // 1000}s")
            if left <= 0:
                finish_game()
                return
            self.typing_game_job = self.root.after(200, tick_timer)

        def on_keypress(event: tk.Event) -> None:
            if state["done"]:
                return
            if event.char and event.char.isprintable():
                self._play_type_sound()

        def _normalize_typed(raw: str) -> str:
            return raw.strip().replace(" ", "").replace("　", "")

        def on_type(_event=None) -> None:
            if state["done"]:
                return
            raw = _normalize_typed(entry.get())
            if jp_mode == JP_TYPING_MODE_ROMAJI:
                typed = _romaji_letters_only(raw)
                state["typed"] = typed
                tgt = state.get("romaji", "")
                ok = bool(tgt) and typed == tgt
                prefix_ok = bool(tgt) and typed and tgt.startswith(typed)
            elif jp_mode == JP_TYPING_MODE_KANA:
                typed = raw
                state["typed"] = typed
                hira = _kana_to_hiragana(typed)
                ok = typed in (state.get("target", ""), state.get("target_kata", "")) or hira == state.get(
                    "target_l", ""
                )
                prefix_ok = bool(typed) and (
                    state.get("target", "").startswith(typed)
                    or state.get("target_kata", "").startswith(typed)
                    or state.get("target_l", "").startswith(hira)
                )
            else:
                state["typed"] = raw.lower() if raw.isascii() else raw
                tgt = state["target"]
                tgt_l = state.get("target_l", tgt.lower())
                ok = raw == tgt or state["typed"] == tgt_l or raw == state.get("display")
                prefix_ok = bool(state["typed"]) and (
                    tgt.startswith(raw) or tgt_l.startswith(state["typed"])
                )

            if ok:
                state["score"] += 1
                update_grade_ui()
                result.config(text="正确！", fg="#88dd88")
                next_word()
            elif raw:
                result.config(text="" if prefix_ok else "不对哦~", fg="#ffaa44" if not prefix_ok else MENU_FG)
            else:
                result.config(text="", fg=MENU_FG)
            refresh_kb()

        entry.bind("<KeyPress>", on_keypress)
        entry.bind("<KeyRelease>", on_type)

        def focus_entry(_event=None) -> None:
            if state["done"] or not self.typing_game_win or not self.typing_game_win.winfo_exists():
                return
            try:
                entry.focus_set()
                entry.icursor(tk.END)
            except Exception:
                pass

        def on_win_key(event: tk.Event) -> str | None:
            if state["done"]:
                return None
            try:
                if self.typing_game_win.focus_get() is entry:
                    return None
            except Exception:
                pass
            if event.widget is entry:
                return None
            if event.char and event.char.isprintable():
                entry.insert(tk.END, event.char)
                self._play_type_sound()
                on_type()
                return "break"
            if event.keysym in ("BackSpace", "Delete"):
                if event.keysym == "BackSpace":
                    cur = entry.get()
                    if cur:
                        entry.delete(len(cur) - 1, tk.END)
                else:
                    entry.delete(0, tk.END)
                on_type()
                return "break"
            return None

        self.typing_game_win.bind("<KeyPress>", on_win_key)
        update_grade_ui()
        refresh_kb()
        self._place_panel_popup(self.typing_game_win)
        try:
            self.typing_game_win.lift()
            self.typing_game_win.focus_force()
        except Exception:
            pass
        focus_entry()
        self.root.after(80, focus_entry)
        tick_timer()

'''

text = text[:i0] + new_begin + text[i1:]
path.write_text(text, encoding="utf-8")
print("patched ok")
