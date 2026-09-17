# -*- coding: utf-8 -*-
from pathlib import Path

path = Path(__file__).resolve().parent / "pet.py"
text = path.read_text(encoding="utf-8")
start = text.index("    def _draw_rhythm_frame(self, now: int) -> None:")
end = text.index("    def _close_typing_game(self, *, resume: bool = True) -> None:")

new = '''    def _draw_rhythm_frame(self, now: int) -> None:
        c = self.rhythm_canvas
        if not c:
            return
        w = RHYTHM_W
        h = max(320, int(getattr(self, "rhythm_play_h", RHYTHM_PLAY_H)))
        pad_x = 28
        top = 48
        hit_y = int(h * 0.80)
        lane_w = (w - pad_x * 2) // RHYTHM_LANES
        track = _music_track(getattr(self, "rhythm_track_id", DEFAULT_MUSIC_TRACK))
        grade = _rhythm_grade(self.rhythm_perfect, self.rhythm_great, self.rhythm_good, self.rhythm_miss)
        acc = _rhythm_accuracy_pct(self.rhythm_perfect, self.rhythm_great, self.rhythm_good, self.rhythm_miss)
        travel = max(400, self._get_rhythm_travel_ms())
        bpm = float(getattr(self, "rhythm_chart_bpm", None) or RHYTHM_BPM)
        beat_ms = max(280.0, 60000.0 / max(60.0, bpm))
        pulse = 0.5 + 0.5 * math.sin((now / beat_ms) * math.tau)
        combo = int(self.rhythm_combo or 0)

        if not getattr(self, "rhythm_bg_ready", False):
            c.delete("all")
            c.create_rectangle(0, 0, w, h, fill="#14121c", outline="", tags=("bg",))
            for i in range(RHYTHM_LANES):
                x0 = pad_x + i * lane_w
                x1 = x0 + lane_w - 6
                col = RHYTHM_LANE_COLORS[i]
                c.create_rectangle(x0, top, x1, h - 36, fill="#1c1a28", outline="#3a3550", tags=("bg",))
                c.create_rectangle(
                    x0, hit_y - 10, x1, hit_y + 10, fill="#2a2840", outline=col, width=2, tags=("hitline", f"hit{i}")
                )
                c.create_text((x0 + x1) // 2, h - 18, text=RHYTHM_KEY_LABELS[i], fill=col, font=PIXEL_FONT, tags=("bg",))
            self.rhythm_bg_ready = True

        c.delete("dyn")
        # BPM 呼吸光带（对齐伊得）
        glow_h = 6 + int(10 * pulse)
        for i in range(RHYTHM_LANES):
            x0 = pad_x + i * lane_w
            x1 = x0 + lane_w - 6
            col = RHYTHM_LANE_COLORS[i]
            c.create_rectangle(
                x0 + 2,
                hit_y - glow_h,
                x1 - 2,
                hit_y + glow_h,
                fill=col,
                outline="",
                stipple="gray50",
                tags=("dyn",),
            )
        if combo >= 5:
            band = THEME_RAINBOW[combo % len(THEME_RAINBOW)]
            stipple = "gray75" if combo < 25 else ("gray50" if combo < 50 else "gray25")
            c.create_rectangle(4, top, 14, h - 36, fill=band, outline="", stipple=stipple, tags=("dyn",))
            c.create_rectangle(w - 14, top, w - 4, h - 36, fill=band, outline="", stipple=stipple, tags=("dyn",))

        tid = str(getattr(self, "rhythm_track_id", DEFAULT_MUSIC_TRACK))
        plate = _music_track_icon_photo(tid, 28)
        self._rhythm_plate_photo = plate
        c.create_image(28, 16, image=plate, tags=("dyn",))
        c.create_text(48, 14, text=f"音乐 · {track['title']}", fill="#88ccff", font=PIXEL_FONT, anchor="w", tags=("dyn",))
        left_s = max(0, (self.rhythm_end_ms - now) // 1000)
        mode_tag = "90s" if int(getattr(self, "rhythm_play_cap_ms", 0) or 0) > 0 else "全曲"
        bpm_tag = f"  {bpm:.0f}BPM"
        speed_tag = str(self.app_config.get("rhythm_speed", "中"))
        auto_tag = " AUTO" if self._rhythm_auto_enabled() else ""
        c.create_text(
            w // 2,
            32,
            text=f"得分 {self.rhythm_score}  连击 {self.rhythm_combo}  评级 {grade}  {acc:.0f}%  {mode_tag}{bpm_tag} {speed_tag}{auto_tag} {left_s}s",
            fill="#ffcc66" if auto_tag else "#dddddd",
            font=PIXEL_FONT,
            tags=("dyn",),
        )
        for i in range(RHYTHM_LANES):
            flash_until = self.rhythm_flash.get(i, 0)
            fill = RHYTHM_LANE_COLORS[i] if now <= flash_until or i in self.rhythm_keys_down else "#2a2840"
            try:
                c.itemconfigure(f"hit{i}", fill=fill)
            except Exception:
                pass

        def y_at(ms: int) -> int:
            appear = int(ms) - travel
            progress = (now - appear) / travel
            return top + int((hit_y - top) * min(1.35, max(0.0, progress)))

        appear_ahead = travel + 80
        for note in self.rhythm_notes[getattr(self, "rhythm_scan_i", 0) :]:
            if note["hit"] or note["missed"]:
                continue
            t = int(note["t"])
            end = int(note.get("end", t) or t)
            hold = self._rhythm_note_is_hold(note)
            holding = bool(note.get("holding"))
            if not holding and t - now > appear_ahead:
                break
            if not holding and now < t - travel:
                continue
            if not holding and not hold and now > t + RHYTHM_HIT_GOOD_MS:
                continue
            if hold and not holding and now > end + RHYTHM_HIT_GOOD_MS:
                continue

            i = int(note["lane"])
            x0 = pad_x + i * lane_w + 8
            x1 = x0 + lane_w - 22
            col = RHYTHM_LANE_COLORS[i]
            if hold:
                y_head = hit_y if holding and now >= t else y_at(t)
                y_tail = y_at(end)
                body_top = min(y_head, y_tail)
                body_bot = max(y_head, y_tail)
                if body_bot - body_top < 8:
                    body_bot = body_top + 8
                body_col = "#445566" if not holding else col
                c.create_rectangle(x0 + 6, body_top, x1 - 6, body_bot, fill=body_col, outline="", tags=("dyn",))
                c.create_rectangle(x0, y_head - 10, x1, y_head + 10, fill=col, outline="#ffffff", width=2, tags=("dyn",))
                c.create_rectangle(x0 + 2, y_tail - 7, x1 - 2, y_tail + 7, fill=col, outline="#ffffff", tags=("dyn",))
            else:
                y = y_at(t)
                if abs(y - hit_y) < 28:
                    c.create_rectangle(x0 - 2, y - 12, x1 + 2, y + 12, fill="", outline=col, width=1, tags=("dyn",))
                c.create_rectangle(x0, y - 10, x1, y + 10, fill=col, outline="#ffffff", width=2, tags=("dyn",))

        parts = getattr(self, "rhythm_fx_parts", None) or []
        alive: list[dict] = []
        for p in parts:
            age = now - int(p.get("t0", 0))
            life = int(p.get("life", 400))
            if age < 0 or age >= life:
                continue
            alive.append(p)
            lane = int(p.get("lane", 0)) % RHYTHM_LANES
            cx = pad_x + lane * lane_w + (lane_w - 6) // 2
            cy = hit_y
            tnorm = age / max(1, life)
            px = cx + float(p.get("vx", 0)) * age * 0.35
            py = cy + float(p.get("vy", 0)) * age * 0.35 + 0.002 * age * age
            sz = max(1, int(int(p.get("sz", 3)) * (1.0 - tnorm)))
            col = str(p.get("col") or "#ffffff")
            if p.get("kind") == "star":
                c.create_oval(px - sz, py - sz, px + sz, py + sz, fill=col, outline="#ffffff", tags=("dyn",))
            else:
                c.create_rectangle(px - sz, py - sz, px + sz, py + sz, fill=col, outline="", tags=("dyn",))
        self.rhythm_fx_parts = alive

        banner = getattr(self, "rhythm_fx_banner", None)
        if isinstance(banner, dict):
            age = now - int(banner.get("t0", 0))
            life = int(banner.get("life", 800))
            if 0 <= age < life:
                fade = 1.0 - age / life
                c.create_text(
                    w // 2,
                    top + 28 + int(8 * (1.0 - fade)),
                    text=str(banner.get("text") or ""),
                    fill=str(banner.get("col") or THEME_RAINBOW[0]),
                    font=("Microsoft YaHei UI", 14 + int(6 * fade), "bold"),
                    tags=("dyn",),
                )
            else:
                self.rhythm_fx_banner = None

        if self.rhythm_judgment and now <= int(getattr(self, "rhythm_judge_until", 0) or 0):
            jcol = {
                "Perfect": "#ffee88",
                "Great": "#88ffaa",
                "Good": "#88ccff",
                "Miss": "#ff6688",
            }.get(self.rhythm_judgment, "#ffffff")
            pop = max(0, int(getattr(self, "rhythm_judge_until", 0)) - now)
            scale = 12 + min(8, pop // 40)
            c.create_text(
                w // 2,
                hit_y - 40 - min(12, (520 - min(520, pop)) // 30),
                text=self.rhythm_judgment,
                fill=jcol,
                font=("Microsoft YaHei UI", scale, "bold"),
                tags=("dyn",),
            )
            if combo >= 2 and self.rhythm_judgment != "Miss":
                c.create_text(
                    w // 2,
                    hit_y - 62,
                    text=f"{combo} COMBO",
                    fill=THEME_RAINBOW[combo % len(THEME_RAINBOW)],
                    font=PIXEL_FONT,
                    tags=("dyn",),
                )

'''

path.write_text(text[:start] + new + text[end:], encoding="utf-8")
print("ok", end - start, "->", len(new))
