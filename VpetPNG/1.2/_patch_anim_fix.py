# -*- coding: utf-8 -*-
"""Restore classic pixel-block gather/scatter; one-shot patch for pet.py."""
from pathlib import Path

path = Path(__file__).with_name("pet.py")
text = path.read_text(encoding="utf-8")

# --- constants ---
old_const = """EXIT_DISSOLVE_MS = 26
EXIT_DISSOLVE_FRAMES = 36
PIXEL_BLOCK_DISSOLVE_MS = EXIT_DISSOLVE_MS
PIXEL_BLOCK_DISSOLVE_FRAMES = EXIT_DISSOLVE_FRAMES
# 潮科技像素：霓虹粉青 + 网格光
VPET_ANIM_PALETTE = ("#ff2d95", "#ff66cc", "#66f0ff", "#2ad4ff", "#a8f6ff", "#ffffff")
COMPANION_ANIM_PALETTE = ("#1a3a6e", "#2458a8", "#3d8dff", "#66c8ff", "#9ee0ff", "#e8f7ff")
PIXEL_REASSEMBLY_CYCLE = 44
NEON_GRID_STEP = 10"""

new_const = """EXIT_DISSOLVE_MS = 28
EXIT_DISSOLVE_FRAMES = 32
PIXEL_BLOCK_DISSOLVE_MS = EXIT_DISSOLVE_MS
PIXEL_BLOCK_DISSOLVE_FRAMES = EXIT_DISSOLVE_FRAMES
# 像素聚散主题色（加载环用）；出入场块色来自立绘采样
VPET_ANIM_PALETTE = ("#4488ff", "#66aaff", "#88ccff", "#ff88cc", "#ffffff")
COMPANION_ANIM_PALETTE = ("#44cc88", "#66dd99", "#88ffcc", "#ffdd44", "#ffffff")
PIXEL_REASSEMBLY_CYCLE = 36
STARTUP_WATCHDOG_MS = 14000"""

if old_const not in text:
    raise SystemExit("constants block not found")
text = text.replace(old_const, new_const, 1)

start = text.index("def _draw_spark_chip")
end = text.index("\ndef _draw_like_sticker")

new_block = r'''def _build_pixel_block_specs(
    img: Image.Image,
    size: int,
    *,
    palette: tuple[str, ...] | None = None,
    lively: bool = True,
) -> tuple[int, list[tuple]]:
    """像素块规格：(block_size, [(tx, ty, color, drift_x, drift_y, delay, wobble, speed), ...])"""
    bs = max(4, _pixel_block_size(size) - (1 if lively else 0))
    cols = max(1, (size + bs - 1) // bs)
    rows = max(1, (size + bs - 1) // bs)
    rng = random.Random(time.time_ns() ^ (id(img) << 7) ^ os.getpid())
    specs: list[tuple] = []
    for row in range(rows):
        for col in range(cols):
            x0, y0 = col * bs, row * bs
            x1, y1 = min(size, x0 + bs), min(size, y0 + bs)
            sampled = _avg_block_color(img, x0, y0, x1, y1)
            if sampled is None:
                continue
            color, _alpha = sampled
            if palette:
                color = _palette_tint_color(color, palette, row * 31 + col * 17 + int(rng.random() * 10000))
            angle = rng.uniform(0.0, math.tau)
            mag = rng.uniform(0.45, 1.55 if lively else 1.15) * bs * (1.35 if lively else 1.05)
            from_cx = (x0 + bs * 0.5) - size * 0.5
            from_cy = (y0 + bs * 0.5) - size * 0.5
            radial = math.hypot(from_cx, from_cy) or 1.0
            drift_x = math.cos(angle) * mag + from_cx / radial * bs * rng.uniform(0.35, 1.4)
            drift_y = math.sin(angle) * mag + from_cy / radial * bs * rng.uniform(0.25, 1.2)
            delay = min(0.78, (row / max(1, rows - 1)) * 0.28 + rng.uniform(0.0, 0.45))
            wobble = rng.uniform(0.0, math.tau)
            speed = rng.uniform(0.75, 1.32)
            specs.append((x0, y0, color, drift_x, drift_y, delay, wobble, speed))
    rng.shuffle(specs)
    return bs, specs


def _draw_pixel_block_dissolve_frame(
    canvas: tk.Canvas,
    specs: list[tuple],
    block_size: int,
    size: int,
    phase: int,
    total_phases: int,
    *,
    reverse: bool = False,
    sparkle_palette: tuple[str, ...] | None = None,
) -> None:
    """像素聚散：入场块从外侧飘回原位；退场块向外飘散淡出。"""
    canvas.delete("all")
    if not specs:
        return
    t_global = phase / max(1, total_phases - 1)
    home = block_size * 0.5
    for item in specs:
        tx, ty, color, drift_x, drift_y, delay, wobble, speed = item[:8]
        stagger = delay * 0.42
        denom = max(0.18, 1.0 - stagger * 0.45)
        t_local = min(1.0, max(0.0, ((t_global * speed) - stagger * 0.28) / denom))
        if reverse:
            t_eased = _ease_in_cubic(t_local)
            float_up = t_eased * block_size * 0.2
            wobble_px = math.sin(wobble + t_eased * math.pi * 1.4) * block_size * 0.08 * (1.0 - t_eased)
            cx = tx + home + drift_x * t_eased + wobble_px
            cy = ty + home + drift_y * t_eased - float_up + wobble_px * 0.35
            alpha = 1.0 - t_eased
            scale = 1.0 - t_eased * 0.28
        else:
            t_eased = _ease_in_out_quad(t_local)
            remain = 1.0 - t_eased
            wobble_px = math.sin(wobble + t_eased * math.pi) * block_size * 0.1 * remain
            cx = tx + home + drift_x * remain + wobble_px
            cy = ty + home + drift_y * remain + wobble_px * 0.45
            alpha = t_eased
            scale = 0.55 + t_eased * 0.45
        if alpha < 0.05:
            continue
        half = block_size * scale * 0.5
        x1, y1 = int(cx - half), int(cy - half)
        x2, y2 = int(cx + half), int(cy + half)
        if x2 <= 0 or y2 <= 0 or x1 >= size or y1 >= size:
            continue
        canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")


def _run_pixel_block_dissolve_animation(
    root: tk.Tk,
    canvas: tk.Canvas,
    img: Image.Image,
    size: int,
    *,
    reverse: bool,
    on_done=None,
    ms: int = PIXEL_BLOCK_DISSOLVE_MS,
    frames: int = PIXEL_BLOCK_DISSOLVE_FRAMES,
    palette: tuple[str, ...] | None = None,
    lively: bool = True,
) -> None:
    try:
        block_size, specs = _build_pixel_block_specs(img, size, palette=palette, lively=lively)
    except Exception:
        if on_done:
            on_done()
        return
    frames = max(22, min(40, frames + (random.randint(-2, 3) if lively else 0)))
    ms = max(20, min(36, ms + (random.randint(-3, 2) if lively else 0)))
    frame = {"n": 0}

    def tick() -> None:
        try:
            if not canvas.winfo_exists():
                if on_done:
                    on_done()
                return
            _draw_pixel_block_dissolve_frame(
                canvas,
                specs,
                block_size,
                size,
                frame["n"],
                frames,
                reverse=reverse,
            )
            frame["n"] += 1
            if frame["n"] < frames:
                root.after(ms, tick)
            elif on_done:
                on_done()
        except Exception:
            if on_done:
                on_done()

    tick()


def _draw_themed_pixel_reassembly(
    canvas: tk.Canvas,
    size: int,
    phase: int,
    *,
    palette: tuple[str, ...] = VPET_ANIM_PALETTE,
    label: str = "",
) -> None:
    """加载：像素网格聚拢 ↔ 散开循环。"""
    canvas.delete("all")
    canvas.create_rectangle(0, 0, size, size, fill="#101018", outline="")
    cycle = PIXEL_REASSEMBLY_CYCLE
    t = (phase % cycle) / max(1, cycle - 1)
    if t <= 0.5:
        u = _ease_out_cubic(t * 2.0)
        scatter = u
    else:
        u = _ease_in_cubic((t - 0.5) * 2.0)
        scatter = 1.0 - u
    bs = max(4, size // 12)
    cols = max(1, (size + bs - 1) // bs)
    rows = max(1, (size + bs - 1) // bs)
    mid = size * 0.5
    rng = random.Random((phase // 2) * 9973 + size)
    for row in range(rows):
        for col in range(cols):
            if (row + col + phase) % 5 == 0 and scatter < 0.15:
                continue
            tx = col * bs + bs * 0.5
            ty = row * bs + bs * 0.5
            ang = math.atan2(ty - mid, tx - mid) + rng.uniform(-0.2, 0.2)
            dist = math.hypot(tx - mid, ty - mid) * 0.55 + bs * 1.8
            cx = tx + math.cos(ang) * dist * scatter
            cy = ty + math.sin(ang) * dist * scatter
            half = bs * (0.45 + 0.2 * (1.0 - scatter))
            color = palette[(row * 3 + col + phase) % len(palette)]
            canvas.create_rectangle(
                int(cx - half),
                int(cy - half),
                int(cx + half),
                int(cy + half),
                fill=color,
                outline="",
            )
    # 中心核
    core = max(2, int(bs * (0.8 + 0.5 * (1.0 - scatter))))
    canvas.create_rectangle(
        int(mid - core),
        int(mid - core),
        int(mid + core),
        int(mid + core),
        fill=palette[-1],
        outline="",
    )
    if label:
        canvas.create_text(
            size // 2,
            size - max(bs, 12),
            text=label,
            fill=palette[-1],
            font=("Courier New", max(8, bs - 1), "bold"),
        )


def _draw_size_loading_frame(
    canvas: tk.Canvas,
    size: int,
    phase: int,
    *,
    label: str = "",
    simple: bool = False,
    reverse: bool = False,
    theme: str = "vpet",
) -> None:
    palette = COMPANION_ANIM_PALETTE if theme == "companion" else VPET_ANIM_PALETTE
    draw_phase = -phase if reverse else phase
    _draw_themed_pixel_reassembly(canvas, size, draw_phase, palette=palette, label=label)
    if not simple:
        px = max(3, size // 16)
        bar_w = size - px * 4
        bar_x = px * 2
        bar_y = size - px * 2
        canvas.create_rectangle(bar_x, bar_y, bar_x + bar_w, bar_y + px, fill="#1a2233", outline="")
        cycle = PIXEL_REASSEMBLY_CYCLE
        fill_ratio = ((phase % cycle) / max(1, cycle - 1))
        if reverse:
            fill_ratio = 1.0 - fill_ratio
        fill_w = max(px, int(bar_w * fill_ratio))
        canvas.create_rectangle(bar_x, bar_y, bar_x + fill_w, bar_y + px, fill=palette[2], outline="")

'''

text = text[:start] + new_block + text[end:]

# comments mentioning 星屑
text = text.replace("# 入场：星屑绽放收束后再显示精灵", "# 入场：像素聚散收束后再显示精灵")

path.write_text(text, encoding="utf-8")
print("animation block patched OK")
