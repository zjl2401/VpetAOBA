def _lerp_hex(a: str, b: str, t: float) -> str:
    return _blend(a, b, max(0.0, min(1.0, float(t))))


def home_day_phase(now: float | None = None) -> float:
    """0..1，一小时一轮。"""
    t = float(time.time() if now is None else now)
    return (t % float(HOME_DAY_CYCLE_SEC)) / float(HOME_DAY_CYCLE_SEC)


def home_day_period(phase: float | None = None) -> str:
    p = home_day_phase() if phase is None else float(phase) % 1.0
    if p < 0.18:
        return "dawn"
    if p < 0.48:
        return "day"
    if p < 0.62:
        return "dusk"
    return "night"


def home_day_period_label(phase: float | None = None) -> str:
    return HOME_DAY_PERIOD_LABELS.get(home_day_period(phase), "白天")


def _celestial_arc(progress: float) -> tuple[float, float]:
    """升落弧：progress∈[0,1] 左地平→天顶→右地平。返回 (cx, cy)，cy=0 靠天顶、1 靠地平。"""
    p = 0.0 if progress < 0 else 1.0 if progress > 1 else float(progress)
    cx = 0.04 + 0.92 * p
    lift = 4.0 * p * (1.0 - p)
    cy = 0.88 - 0.72 * lift
    return cx, cy


def _horizon_fade(progress: float, *, edge: float = 0.10) -> float:
    """靠近升/落点时变淡。"""
    p = 0.0 if progress < 0 else 1.0 if progress > 1 else float(progress)
    d = min(p, 1.0 - p)
    if d >= edge:
        return 1.0
    return max(0.0, d / edge)


def home_day_sky_state(phase: float | None = None) -> dict:
    """
    室外天空/明暗：随 1h 周期平滑过渡。
    sun/moon 含弧线位置；黄昏日落+月出、黎明月落+日升可短暂同框。
    仍保留 celestial/cx/cy 供旧绘制路径兼容。
    """
    p = home_day_phase() if phase is None else float(phase) % 1.0
    period = home_day_period(p)
    if p < 0.18:
        t = p / 0.18
        sky = _lerp_hex("#2a2848", "#7eb8e8", t)
        trim = _lerp_hex("#c89878", "#e8d090", t)
        veil = max(0.0, 0.35 * (1.0 - t))
        glow_color = _lerp_hex("#ff9060", "#ffe0a0", t)
        glow_str = max(0.18, 0.9 * (1.0 - t * 0.65))
    elif p < 0.48:
        t = (p - 0.18) / 0.30
        sky = _lerp_hex("#7eb8e8", "#5a9fd4", t * 0.4)
        trim = "#e8d090"
        veil = 0.0
        glow_color = "#ffe8c8"
        glow_str = 0.1
    elif p < 0.62:
        t = (p - 0.48) / 0.14
        sky = _lerp_hex("#5a9fd4", "#3a2848", t)
        trim = _lerp_hex("#e8d090", "#e89868", t)
        veil = 0.15 + 0.35 * t
        glow_color = _lerp_hex("#ffc070", "#ff6848", t)
        glow_str = 0.4 + 0.55 * t
    else:
        t = (p - 0.62) / 0.38
        sky = _lerp_hex("#1a1830", "#12182a", min(1.0, t * 1.2))
        trim = _lerp_hex("#6a5888", "#3a4060", t)
        veil = 0.45 + 0.25 * min(1.0, t * 1.4)
        glow_color = "#4a5080"
        glow_str = max(0.0, 0.28 * (1.0 - t))

    sun: dict | None = None
    if p < 0.64:
        sp = p / 0.64
        sx, sy = _celestial_arc(sp)
        sun = {"cx": sx, "cy": sy, "alpha": _horizon_fade(sp, edge=0.11), "progress": sp}

    moon: dict | None = None
    moon_span = (1.0 - 0.50) + 0.14
    if p >= 0.50:
        mp = (p - 0.50) / moon_span
        if mp <= 1.0:
            mx, my = _celestial_arc(mp)
            moon = {"cx": mx, "cy": my, "alpha": _horizon_fade(mp, edge=0.12), "progress": mp}
    elif p < 0.14:
        # 黎明：昨夜之月尚未落尽
        mp = ((1.0 - 0.50) + p) / moon_span
        mx, my = _celestial_arc(mp)
        moon = {"cx": mx, "cy": my, "alpha": _horizon_fade(mp, edge=0.12), "progress": mp}

    if sun and float(sun["alpha"]) >= 0.12 and period in ("dawn", "day", "dusk"):
        if period == "dusk" and p >= 0.56 and moon and float(moon["alpha"]) > float(sun["alpha"]):
            celestial = "moon"
            cx, cy = float(moon["cx"]), float(moon["cy"])
        else:
            celestial = "sun"
            cx, cy = float(sun["cx"]), float(sun["cy"])
    elif moon and float(moon["alpha"]) >= 0.08:
        celestial = "moon"
        cx, cy = float(moon["cx"]), float(moon["cy"])
    elif sun:
        celestial = "sun"
        cx, cy = float(sun["cx"]), float(sun["cy"])
    else:
        celestial = "none"
        cx, cy = 0.5, 0.5

    indoor_wall = HOME_WALL if veil < 0.2 else _lerp_hex(HOME_WALL, "#2a2838", min(1.0, veil))
    indoor_trim = HOME_WALL_TRIM if veil < 0.25 else _lerp_hex(HOME_WALL_TRIM, "#c8a878", min(1.0, veil * 1.2))
    return {
        "phase": p,
        "period": period,
        "label": HOME_DAY_PERIOD_LABELS.get(period, "白天"),
        "sky": sky,
        "trim": trim,
        "celestial": celestial,
        "cx": cx,
        "cy": cy,
        "sun": sun,
        "moon": moon,
        "glow_color": glow_color,
        "glow": max(0.0, min(1.0, glow_str)),
        "night_veil": max(0.0, min(0.75, veil)),
        "indoor_wall": indoor_wall,
        "indoor_trim": indoor_trim,
        "stars": period == "night" or (period == "dusk" and p > 0.55) or (period == "dawn" and p < 0.06),
    }


