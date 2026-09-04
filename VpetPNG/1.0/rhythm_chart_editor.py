"""音游谱面编辑器（对照 Malody Key / osu!mania Compose）。

用法概要：
· 左键点轨道：在播放头位置放置短音（自动对齐节拍网格）
· 左键拖拽：放置长按
· 右键：删除最近点
· D/F/J/K：播放时也可落键（录音模式）
· 空格：播放/暂停；←/→：按网格前进/后退
· 可调 BPM、偏移、细分（1/1~1/8）
"""
from __future__ import annotations

import math
import time
import tkinter as tk
from pathlib import Path
from typing import Any, Callable

# 由 pet 注入常量，避免循环导入时硬依赖
RHYTHM_LANES = 4
RHYTHM_KEYS = ("d", "f", "j", "k")
RHYTHM_KEY_LABELS = ("D", "F", "J", "K")
RHYTHM_LANE_COLORS = ("#66ccff", "#88ffaa", "#ffcc66", "#ff88cc")
PIXEL_FONT = ("Courier New", 10, "bold")
MENU_FG = "#e8e8f0"
MENU_ACTIVE = "#3a4a68"


def open_chart_editor(
    pet: Any,
    *,
    track: dict,
    wav: Path,
    duration_ms: int,
    difficulty: str,
    initial_notes: list[dict] | None = None,
    initial_bpm: float | None = None,
    save_fn: Callable[..., Path],
    export_fn: Callable[[Path], None],
    analyze_bpm_fn: Callable[[Path, int], tuple[float, list]] | None = None,
    ensure_mixer_fn: Callable[[], None] | None = None,
    apply_volume_fn: Callable[[], None] | None = None,
    event_lane_fn: Callable[[tk.Event], int | None] | None = None,
    phys_key_down_fn: Callable[[int], bool] | None = None,
    vk_lanes: dict[int, int] | None = None,
    place_popup_fn: Callable[[tk.Toplevel], None] | None = None,
    apply_layer_fn: Callable[[tk.Toplevel], None] | None = None,
) -> None:
    """打开谱面编辑器窗口。"""
    import pygame

    if getattr(pet, "chart_maker_active", False) or getattr(pet, "rhythm_active", False):
        pet._show_toast("请先结束当前音游或编辑", "#ff8844")
        return

    old = getattr(pet, "chart_maker_win", None)
    if old is not None:
        try:
            if old.winfo_exists():
                old.destroy()
        except Exception:
            pass

    win_w, win_h = 520, 620
    win = tk.Toplevel(pet.root)
    pet.chart_maker_win = win
    win.title(f"谱面编辑器 · {track.get('title', '')}")
    if apply_layer_fn:
        apply_layer_fn(win)
    else:
        try:
            pet._apply_window_layer(win)
        except Exception:
            pass
    win.configure(bg="#101018")
    setattr(win, "_panel_fixed_size", (win_w, win_h))
    setattr(win, "_panel_full_size", True)
    pet.chart_maker_active = True

    notes: list[dict] = []
    for n in initial_notes or []:
        if not isinstance(n, dict):
            continue
        t = int(n.get("t", 0))
        end = int(n.get("end", t) or t)
        notes.append(
            {
                "t": t,
                "end": max(t, end),
                "lane": int(n.get("lane", 0)) % RHYTHM_LANES,
                "hold": bool(n.get("hold")) or (end - t >= 220),
            }
        )
    notes.sort(key=lambda x: (x["t"], x["lane"]))

    state: dict[str, Any] = {
        "playing": False,
        "play_anchor_wall": 0,
        "play_anchor_t": 0,
        "t": 0,  # playhead ms
        "bpm": float(initial_bpm or 120),
        "offset": 0,  # first beat offset ms
        "snap_div": 4,  # 1/4 note
        "tool": "place",  # place | erase | hold
        "drag_lane": None,
        "drag_t0": None,
        "job": None,
        "saved_path": None,
        "view_ms": 4000,
    }

    # 尝试自动 BPM
    if analyze_bpm_fn and (initial_bpm is None or not initial_notes):
        try:
            bpm, _ev = analyze_bpm_fn(wav, duration_ms)
            if bpm and bpm > 40:
                state["bpm"] = float(bpm)
        except Exception:
            pass

    top = tk.Frame(win, bg="#101018", padx=8, pady=6)
    top.pack(fill=tk.X)
    tk.Label(top, text=str(track.get("title") or ""), font=PIXEL_FONT, fg="#88ccff", bg="#101018").pack(
        side=tk.LEFT
    )
    status = tk.Label(top, text="左键落键 · 右键删除 · 空格播放", font=("Courier New", 8), fg="#8899aa", bg="#101018")
    status.pack(side=tk.RIGHT)

    tip = tk.Label(
        win,
        text="对照 Malody/osu!mania：先设 BPM→对齐网格→在轨道点按落键；也可边播边按 D F J K",
        font=("Courier New", 8),
        fg="#778899",
        bg="#101018",
        wraplength=480,
        justify=tk.LEFT,
    )
    tip.pack(anchor=tk.W, padx=8)

    # —— 参数行：BPM / 偏移 / 细分 ——
    param = tk.Frame(win, bg="#101018", padx=8, pady=4)
    param.pack(fill=tk.X)
    bpm_var = tk.StringVar(value=f"{state['bpm']:.1f}")
    off_var = tk.StringVar(value="0")
    snap_var = tk.StringVar(value="1/4")
    title_var = tk.StringVar(value=f"{track.get('title', '曲')} · 自制")

    def _spin(parent, label, var, width=7):
        tk.Label(parent, text=label, font=("Courier New", 8), fg="#aaaaaa", bg="#101018").pack(side=tk.LEFT)
        e = tk.Entry(parent, textvariable=var, width=width, font=("Courier New", 9))
        e.pack(side=tk.LEFT, padx=(2, 8))
        return e

    _spin(param, "BPM", bpm_var, 6)
    _spin(param, "偏移ms", off_var, 6)
    tk.Label(param, text="网格", font=("Courier New", 8), fg="#aaaaaa", bg="#101018").pack(side=tk.LEFT)
    snap_box = tk.OptionMenu(param, snap_var, "1/1", "1/2", "1/4", "1/8", "1/16")
    snap_box.config(font=("Courier New", 8), bg="#2a3348", fg=MENU_FG, highlightthickness=0)
    snap_box.pack(side=tk.LEFT, padx=(2, 8))

    def apply_params() -> None:
        try:
            state["bpm"] = max(40.0, min(300.0, float(bpm_var.get())))
        except Exception:
            bpm_var.set(f"{state['bpm']:.1f}")
        try:
            state["offset"] = max(0, int(float(off_var.get())))
        except Exception:
            off_var.set(str(state["offset"]))
        div_map = {"1/1": 1, "1/2": 2, "1/4": 4, "1/8": 8, "1/16": 16}
        state["snap_div"] = div_map.get(snap_var.get(), 4)
        redraw()

    def auto_bpm() -> None:
        if not analyze_bpm_fn:
            pet._show_toast("无法分析 BPM", "#ff8844")
            return
        status.config(text="正在分析节拍…", fg="#88ccff")
        win.update_idletasks()

        def work() -> None:
            try:
                bpm, _ = analyze_bpm_fn(wav, duration_ms)
            except Exception:
                bpm = state["bpm"]

            def done() -> None:
                state["bpm"] = float(bpm) if bpm and bpm > 40 else state["bpm"]
                bpm_var.set(f"{state['bpm']:.1f}")
                status.config(text=f"BPM≈{state['bpm']:.1f}", fg="#88ffaa")
                redraw()

            pet.root.after(0, done)

        import threading

        threading.Thread(target=work, daemon=True).start()

    tk.Button(param, text="应用", font=("Courier New", 8), bg=MENU_ACTIVE, fg=MENU_FG, command=apply_params).pack(
        side=tk.LEFT, padx=2
    )
    tk.Button(param, text="测BPM", font=("Courier New", 8), bg="#2a5544", fg=MENU_FG, command=auto_bpm).pack(
        side=tk.LEFT, padx=2
    )

    title_row = tk.Frame(win, bg="#101018", padx=8)
    title_row.pack(fill=tk.X)
    tk.Label(title_row, text="标题", font=("Courier New", 8), fg="#aaaaaa", bg="#101018").pack(side=tk.LEFT)
    tk.Entry(title_row, textvariable=title_var, font=("Courier New", 9), width=32).pack(
        side=tk.LEFT, padx=4, fill=tk.X, expand=True
    )

    # —— 工具 ——
    tools = tk.Frame(win, bg="#101018", padx=8, pady=2)
    tools.pack(fill=tk.X)
    tool_btns: dict[str, tk.Button] = {}

    def set_tool(name: str) -> None:
        state["tool"] = name
        for k, b in tool_btns.items():
            b.config(bg="#88aa44" if k == name else "#2a3348")

    for key, label in (("place", "放置短音"), ("hold", "放置长音"), ("erase", "橡皮擦")):
        b = tk.Button(tools, text=label, font=("Courier New", 8), bg="#2a3348", fg=MENU_FG, command=lambda n=key: set_tool(n))
        b.pack(side=tk.LEFT, padx=2)
        tool_btns[key] = b
    set_tool("place")
    count_lbl = tk.Label(tools, text="0 音", font=("Courier New", 8), fg="#ccddee", bg="#101018")
    count_lbl.pack(side=tk.RIGHT)

    canvas = tk.Canvas(win, width=win_w - 24, height=340, bg="#12141c", highlightthickness=1, highlightbackground="#334")
    canvas.pack(padx=8, pady=4, fill=tk.BOTH, expand=True)
    try:
        canvas.configure(takefocus=True)
    except Exception:
        pass

    seek = tk.Scale(
        win,
        from_=0,
        to=max(1, duration_ms),
        orient=tk.HORIZONTAL,
        bg="#101018",
        fg="#ccddee",
        troughcolor="#222833",
        highlightthickness=0,
        showvalue=0,
        command=lambda v: seek_to(int(float(v))),
    )
    seek.pack(fill=tk.X, padx=8)

    def beat_ms() -> float:
        return 60000.0 / max(40.0, float(state["bpm"]))

    def snap_ms() -> float:
        return beat_ms() / max(1, int(state["snap_div"]))

    def quantize(t: int) -> int:
        off = int(state["offset"])
        step = snap_ms()
        if step <= 1:
            return max(0, min(duration_ms, t))
        rel = t - off
        q = int(round(rel / step) * step + off)
        return max(0, min(duration_ms, q))

    def playhead() -> int:
        if not state["playing"]:
            return int(state["t"])
        now = int(time.time() * 1000)
        t = int(state["play_anchor_t"] + (now - state["play_anchor_wall"]))
        return max(0, min(duration_ms, t))

    def set_playhead(t: int, *, sync_seek: bool = True) -> None:
        state["t"] = max(0, min(duration_ms, int(t)))
        if sync_seek:
            try:
                seek.set(state["t"])
            except Exception:
                pass

    def seek_to(t: int) -> None:
        if state["playing"]:
            # 播放中拖动：重定位音乐
            pause_play()
            set_playhead(t)
            start_play()
        else:
            set_playhead(t)
            redraw()

    def stop_music() -> None:
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass
        pet.bg_music_playing = False

    def start_play() -> None:
        apply_params()
        t0 = playhead()
        try:
            if ensure_mixer_fn:
                ensure_mixer_fn()
            else:
                from pet import _init_pygame_mixer  # type: ignore

                _init_pygame_mixer()
            pygame.mixer.music.load(str(wav))
            if apply_volume_fn:
                apply_volume_fn()
            # pygame 用秒定位
            pygame.mixer.music.play(0, start=max(0.0, t0 / 1000.0))
            pet.bg_music_playing = True
        except Exception as exc:
            pet._show_toast(f"播放失败：{exc}", "#ff6666")
            return
        state["playing"] = True
        state["play_anchor_wall"] = int(time.time() * 1000)
        state["play_anchor_t"] = t0
        status.config(text="播放中 · D/F/J/K 可落键", fg="#88ffaa")

    def pause_play() -> None:
        if not state["playing"]:
            return
        set_playhead(playhead())
        state["playing"] = False
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.pause()
        except Exception:
            pass
        stop_music()
        status.config(text="已暂停", fg="#ffcc66")

    def toggle_play() -> None:
        if state["playing"]:
            pause_play()
        else:
            start_play()

    def step(dir_: int) -> None:
        apply_params()
        was = state["playing"]
        if was:
            pause_play()
        set_playhead(quantize(playhead() + int(dir_ * snap_ms())))
        redraw()

    def add_note(lane: int, t: int, end: int | None = None) -> None:
        t = quantize(t)
        end_t = quantize(end) if end is not None else t
        if end_t < t:
            end_t = t
        hold = end_t - t >= 220
        # 同轨近距离去重
        notes[:] = [
            n
            for n in notes
            if not (int(n["lane"]) == lane and abs(int(n["t"]) - t) < max(30, snap_ms() * 0.4))
        ]
        notes.append({"t": t, "end": end_t if hold else t, "lane": lane, "hold": hold})
        notes.sort(key=lambda x: (x["t"], x["lane"]))
        count_lbl.config(text=f"{len(notes)} 音")

    def erase_near(lane: int, t: int) -> None:
        best_i = -1
        best_d = 10**9
        for i, n in enumerate(notes):
            if int(n["lane"]) != lane:
                continue
            d = abs(int(n["t"]) - t)
            if d < best_d:
                best_d = d
                best_i = i
        if best_i >= 0 and best_d <= max(180, snap_ms() * 1.5):
            notes.pop(best_i)
            count_lbl.config(text=f"{len(notes)} 音")

    def y_to_time(y: float, h: float, t_now: int) -> int:
        # 判定线在下方；上方是未来
        hit_y = h - 40
        view = float(state["view_ms"])
        # y=hit_y → t_now；y 越小 t 越大
        return int(t_now + (hit_y - y) * view / max(1.0, hit_y - 36))

    def redraw() -> None:
        canvas.delete("all")
        w = max(40, int(canvas.winfo_width() or (win_w - 24)))
        h = max(40, int(canvas.winfo_height() or 340))
        lane_w = w / RHYTHM_LANES
        t_now = playhead()
        state["t"] = t_now
        try:
            if not state["playing"]:
                seek.set(t_now)
        except Exception:
            pass
        # 背景轨
        for i in range(RHYTHM_LANES):
            x0 = i * lane_w
            canvas.create_rectangle(x0 + 1, 0, x0 + lane_w - 1, h, fill="#1a1a28", outline="#2a2a3a")
            canvas.create_text(
                x0 + lane_w / 2,
                12,
                text=RHYTHM_KEY_LABELS[i],
                fill=RHYTHM_LANE_COLORS[i],
                font=("Courier New", 12, "bold"),
            )
        hit_y = h - 40
        canvas.create_line(0, hit_y, w, hit_y, fill="#88ccff", width=2)
        # 网格线
        apply_params_silent = True
        try:
            state["bpm"] = max(40.0, min(300.0, float(bpm_var.get())))
            state["offset"] = max(0, int(float(off_var.get())))
        except Exception:
            pass
        step = snap_ms()
        view = float(state["view_ms"])
        t0 = t_now - 200
        t1 = t_now + view
        if step > 1:
            first = state["offset"] + math.floor((t0 - state["offset"]) / step) * step
            bt = first
            while bt <= t1:
                y = hit_y - (bt - t_now) * (hit_y - 36) / view
                if 20 < y < h - 8:
                    major = abs((bt - state["offset"]) % beat_ms()) < 1.0
                    canvas.create_line(0, y, w, y, fill="#3a4458" if not major else "#556178")
                bt += step
        # 音符
        for n in notes:
            t = int(n["t"])
            end = int(n.get("end", t) or t)
            if end < t_now - 300 or t > t_now + view:
                continue
            lane = int(n["lane"]) % RHYTHM_LANES
            x = lane * lane_w + lane_w / 2
            y_head = hit_y - (t - t_now) * (hit_y - 36) / view
            if bool(n.get("hold")) and end > t:
                y_tail = hit_y - (end - t_now) * (hit_y - 36) / view
                canvas.create_line(x, y_head, x, y_tail, fill=RHYTHM_LANE_COLORS[lane], width=10)
            canvas.create_rectangle(
                x - 14,
                y_head - 7,
                x + 14,
                y_head + 7,
                fill=RHYTHM_LANE_COLORS[lane],
                outline="#ffffff",
            )
        # 拖拽中预览
        if state["drag_lane"] is not None and state["drag_t0"] is not None:
            lane = int(state["drag_lane"])
            x = lane * lane_w + lane_w / 2
            t_a = int(state["drag_t0"])
            t_b = t_now if state["playing"] else int(state.get("drag_t1", t_a))
            y_a = hit_y - (t_a - t_now) * (hit_y - 36) / view
            y_b = hit_y - (t_b - t_now) * (hit_y - 36) / view
            canvas.create_line(x, y_a, x, y_b, fill=RHYTHM_LANE_COLORS[lane], width=8)
        canvas.create_text(
            6,
            h - 12,
            text=f"{t_now/1000:06.2f}s / {duration_ms/1000:.1f}s  |  BPM {state['bpm']:.1f}  |  网格 {snap_var.get()}",
            fill="#ccddee",
            font=("Courier New", 9),
            anchor="w",
        )
        count_lbl.config(text=f"{len(notes)} 音")
        _ = apply_params_silent

    def on_press(e: tk.Event) -> None:
        canvas.focus_set()
        w = max(40, int(canvas.winfo_width() or 1))
        h = max(40, int(canvas.winfo_height() or 1))
        lane = int(e.x / (w / RHYTHM_LANES)) % RHYTHM_LANES
        t = quantize(y_to_time(e.y, h, playhead()))
        if int(getattr(e, "num", 1) or 1) == 3 or state["tool"] == "erase":
            erase_near(lane, t)
            redraw()
            return
        if state["tool"] == "hold":
            state["drag_lane"] = lane
            state["drag_t0"] = t
            state["drag_t1"] = t
            return
        # place short
        add_note(lane, t)
        redraw()

    def on_drag(e: tk.Event) -> None:
        if state["drag_lane"] is None:
            return
        h = max(40, int(canvas.winfo_height() or 1))
        state["drag_t1"] = quantize(y_to_time(e.y, h, playhead()))
        redraw()

    def on_release(e: tk.Event) -> None:
        if state["drag_lane"] is None or state["drag_t0"] is None:
            return
        lane = int(state["drag_lane"])
        t0 = int(state["drag_t0"])
        h = max(40, int(canvas.winfo_height() or 1))
        t1 = quantize(y_to_time(e.y, h, playhead()))
        if t1 < t0:
            t0, t1 = t1, t0
        add_note(lane, t0, t1)
        state["drag_lane"] = None
        state["drag_t0"] = None
        state["drag_t1"] = None
        redraw()

    def on_key(e: tk.Event) -> str | None:
        key = (getattr(e, "keysym", "") or "").lower()
        if key == "space":
            toggle_play()
            return "break"
        if key in ("left",):
            step(-1)
            return "break"
        if key in ("right",):
            step(1)
            return "break"
        if key == "delete" or key == "backspace":
            # 删播放头附近
            t = playhead()
            for lane in range(RHYTHM_LANES):
                erase_near(lane, t)
            redraw()
            return "break"
        lane = None
        if event_lane_fn:
            lane = event_lane_fn(e)
        else:
            ch = (getattr(e, "char", None) or "").lower()
            if ch in RHYTHM_KEYS:
                lane = RHYTHM_KEYS.index(ch)
            elif key in RHYTHM_KEYS:
                lane = RHYTHM_KEYS.index(key)
        if lane is None:
            return None
        add_note(lane, playhead())
        redraw()
        return "break"

    def tick() -> None:
        if not getattr(pet, "chart_maker_active", False) or not win.winfo_exists():
            return
        if state["playing"]:
            t = playhead()
            if t >= duration_ms - 30:
                pause_play()
                set_playhead(duration_ms)
            # 物理键录音
            if phys_key_down_fn and vk_lanes:
                for vk, lane in vk_lanes.items():
                    # 边沿：用 notes 最近时间粗判，简化为每帧若按下且距上音>80ms
                    if phys_key_down_fn(vk):
                        recent = [
                            n
                            for n in notes
                            if int(n["lane"]) == lane and abs(int(n["t"]) - t) < 90
                        ]
                        if not recent:
                            add_note(lane, t)
        redraw()
        state["job"] = pet.root.after(33, tick)

    def undo() -> None:
        if notes:
            notes.pop()
            count_lbl.config(text=f"{len(notes)} 音")
            redraw()

    def clear_all() -> None:
        notes.clear()
        count_lbl.config(text="0 音")
        redraw()

    def save_chart() -> None:
        apply_params()
        if len(notes) < 4:
            pet._show_toast("至少放置 4 个音再保存", "#ff8844")
            return
        title = title_var.get().strip() or f"{track.get('title', '曲')} · 自制"
        try:
            dest = save_fn(
                title=title,
                track_id=str(track["id"]),
                difficulty=difficulty,
                bpm=float(state["bpm"]),
                notes=notes,
            )
        except Exception as exc:
            pet._show_toast(f"保存失败：{exc}", "#ff6666")
            return
        state["saved_path"] = dest
        status.config(text=f"已保存 {dest.name} · 可投稿「音游谱面」", fg="#88ffcc")
        pet._show_toast(
            f"谱面已保存（{len(notes)} 音）· 投稿：系统→社区→投稿创意",
            "#88ffcc",
            duration_ms=3200,
        )

    def export_chart() -> None:
        path = state.get("saved_path")
        if path is None:
            save_chart()
            path = state.get("saved_path")
        if path is None:
            return
        export_fn(Path(path))

    def close_maker() -> None:
        job = state.get("job")
        if job is not None:
            try:
                pet.root.after_cancel(job)
            except Exception:
                pass
        pause_play()
        stop_music()
        pet.chart_maker_active = False
        pet.chart_maker_win = None
        try:
            win.destroy()
        except Exception:
            pass

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    canvas.bind("<ButtonPress-3>", on_press)
    win.bind("<KeyPress>", on_key)
    canvas.bind("<KeyPress>", on_key)
    win.bind("<Escape>", lambda _e: close_maker())
    win.protocol("WM_DELETE_WINDOW", close_maker)

    btns = tk.Frame(win, bg="#101018", padx=8, pady=6)
    btns.pack(fill=tk.X)
    tk.Button(btns, text="▶/⏸", font=PIXEL_FONT, bg="#2a6644", fg=MENU_FG, command=toggle_play).pack(
        side=tk.LEFT, padx=2
    )
    tk.Button(btns, text="◀网格", font=("Courier New", 8), bg="#3a4a68", fg=MENU_FG, command=lambda: step(-1)).pack(
        side=tk.LEFT, padx=2
    )
    tk.Button(btns, text="网格▶", font=("Courier New", 8), bg="#3a4a68", fg=MENU_FG, command=lambda: step(1)).pack(
        side=tk.LEFT, padx=2
    )
    tk.Button(btns, text="撤销", font=("Courier New", 8), bg="#3a4a68", fg=MENU_FG, command=undo).pack(
        side=tk.LEFT, padx=2
    )
    tk.Button(btns, text="清空", font=("Courier New", 8), bg="#553344", fg=MENU_FG, command=clear_all).pack(
        side=tk.LEFT, padx=2
    )
    tk.Button(btns, text="保存", font=PIXEL_FONT, bg=MENU_ACTIVE, fg=MENU_FG, command=save_chart).pack(
        side=tk.LEFT, padx=2
    )
    tk.Button(btns, text="导出", font=PIXEL_FONT, bg="#4a3a68", fg=MENU_FG, command=export_chart).pack(
        side=tk.LEFT, padx=2
    )
    tk.Button(btns, text="关闭", font=PIXEL_FONT, bg="#555555", fg=MENU_FG, command=close_maker).pack(
        side=tk.RIGHT, padx=2
    )

    if place_popup_fn:
        place_popup_fn(win)
    else:
        try:
            pet._place_panel_popup(win)
        except Exception:
            pass
    try:
        win.lift()
        win.focus_force()
        canvas.focus_set()
    except Exception:
        pass
    count_lbl.config(text=f"{len(notes)} 音")
    redraw()
    state["job"] = pet.root.after(33, tick)
