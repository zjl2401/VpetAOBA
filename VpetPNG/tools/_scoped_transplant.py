# -*- coding: utf-8 -*-
"""Scoped Eiden align: font / outfit / dialog / home-day / owner-avatar."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(r"c:\Users\36255\Desktop\VpetAOBA\VpetPNG")
EIDEN = Path(r"C:\Users\36255\Desktop\VpetEidenPet")
PET = ROOT / "pet.py"
HOME = ROOT / "home_cottage.py"
OUTFIT = ROOT / "pet_outfit.py"
ONE = ROOT / "1.0"


def once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        if new.strip()[:40] in text or (label and f"# scoped:{label}" in text):
            print(f"  skip (already): {label}")
            return text
        raise SystemExit(f"anchor missing for {label}:\n{old[:120]!r}")
    print(f"  patch: {label}")
    return text.replace(old, new, 1)


def main() -> None:
    # ---------- home_cottage day cycle ----------
    home = HOME.read_text(encoding="utf-8")
    if "def home_day_phase" not in home:
        consts = '''
HOME_DAY_CYCLE_SEC = 3600
HOME_DAY_PERIOD_LABELS = {
    "dawn": "黎明",
    "day": "白天",
    "dusk": "黄昏",
    "night": "夜晚",
}
HOME_SKY_WALL_INDOOR = 18
HOME_SKY_WALL_OUTDOOR = 44


def home_sky_wall(zone: str | None) -> int:
    return HOME_SKY_WALL_OUTDOOR if str(zone or "") == "outdoor" else HOME_SKY_WALL_INDOOR

'''
        # insert after HOME_CONTROL_STEP_MS
        anchor = "HOME_CONTROL_STEP_MS = 220  # 操控模式最短步间隔\n"
        if anchor not in home:
            raise SystemExit("home: HOME_CONTROL_STEP_MS not found")
        home = home.replace(anchor, anchor + "\n" + consts, 1)

        day_body = Path(__file__).with_name("_day_cycle_snip.py").read_text(encoding="utf-8")
        # insert after _shade (uses existing _blend via _lerp_hex in snip)
        mark = "def furniture_meta(kind: str)"
        if mark not in home:
            raise SystemExit("home: furniture_meta not found")
        home = home.replace(mark, day_body.rstrip() + "\n\n\n" + mark, 1)
        HOME.write_text(home, encoding="utf-8")
        print("home_cottage: day cycle OK")
    else:
        print("home_cottage: already OK")

    # ---------- pet_outfit ----------
    if "OUTFIT_GROUP_ORDER" not in OUTFIT.read_text(encoding="utf-8"):
        shutil.copy2(EIDEN / "pet_outfit.py", OUTFIT)
        print("pet_outfit: copied from Eiden")
    else:
        print("pet_outfit: already has groups")

    # ---------- pet.py mega patches ----------
    pet = PET.read_text(encoding="utf-8")
    orig_len = len(pet)

    # import contextlib
    if "import contextlib" not in pet:
        pet = once(
            pet,
            "import array\n",
            "import array\nimport contextlib\n",
            "import-contextlib",
        )

    # OWNER_AVATAR_FILE + CHAT constants near OWNER_NAME
    if "OWNER_AVATAR_FILE" not in pet:
        pet = once(
            pet,
            "OWNER_NAME_MAX_LEN = 16\n",
            "OWNER_NAME_MAX_LEN = 16\n"
            "OWNER_AVATAR_FILE = DATA_DIR / \"owner_avatar.png\"\n"
            "CHAT_AVATAR_PX = 40\n"
            "CHAT_BUBBLE_MAX_W = 220\n"
            "CHAT_BUBBLE_PAD_X = 10\n"
            "CHAT_BUBBLE_PAD_Y = 8\n"
            "CHAT_BUBBLE_RADIUS = 12\n"
            "CHAT_BUBBLE_GAP = 8\n"
            "CHAT_OWNER_BUBBLE_FILL = \"#ffffff\"\n"
            "CHAT_PET_BUBBLE_FILL = \"#e8f4ff\"\n"
            "CHAT_OWNER_BUBBLE_FG = \"#1e3a5c\"\n"
            "CHAT_PET_BUBBLE_FG = \"#1e3a5c\"\n"
            "CHAT_NAME_FG = \"#5a7088\"\n",
            "owner-avatar-consts",
        )

    # Font family constants after FONT_SIZE_PRESET_ORDER
    if "UI_FONT_FAMILY_DEFAULT" not in pet:
        pet = once(
            pet,
            'FONT_SIZE_PRESETS: dict[str, int] = {"小": 10, "中": 12, "大": 14, "特大": 16}\n'
            'FONT_SIZE_PRESET_ORDER: tuple[str, ...] = ("小", "中", "大", "特大")\n'
            "FONT_SIZE_MIN = 8\n",
            'FONT_SIZE_PRESETS: dict[str, int] = {"小": 10, "中": 12, "大": 14, "特大": 16}\n'
            'FONT_SIZE_PRESET_ORDER: tuple[str, ...] = ("小", "中", "大", "特大")\n'
            "FONT_SIZE_MIN = 8\n"
            "UI_FONT_FAMILY_DEFAULT = \"楷体\"\n"
            'UI_FONT_FAMILY_ORDER: tuple[str, ...] = ("楷体", "像素", "仿宋")\n'
            "UI_FONT_FAMILY_LEGACY: dict[str, str] = {\n"
            '    "可爱": "楷体",\n'
            '    "雅黑": "楷体",\n'
            '    "黑体": "楷体",\n'
            '    "宋体": "楷体",\n'
            "}\n"
            "UI_FONT_FAMILY_PRESETS: dict[str, dict] = {\n"
            '    "楷体": {\n'
            '        "hint": "全局楷体",\n'
            '        "bundled": ("ui_cute.ttf",),\n'
            '        "candidates": ("KaiTi", "楷体", "STKaiti", "华文楷体"),\n'
            "    },\n"
            '    "像素": {\n'
            '        "hint": "全局像素",\n'
            '        "bundled": ("fusion-pixel-12px-proportional-zh_hans.ttf",),\n'
            '        "candidates": ("Fusion Pixel 12px Prop zh_hans",),\n'
            "    },\n"
            '    "仿宋": {\n'
            '        "hint": "全局仿宋",\n'
            '        "candidates": ("FangSong", "仿宋", "STFangsong", "华文仿宋"),\n'
            '        "bundled": (),\n'
            "    },\n"
            "}\n",
            "font-family-consts",
        )

    # Font path vars
    if "_UI_CUTE_TTF" not in pet:
        pet = once(
            pet,
            '_FUSION_PIXEL_TTF = _BUNDLED_FONTS_DIR / "fusion-pixel-12px-proportional-zh_hans.ttf"\n'
            '_FUSION_PIXEL_FAMILY = "Fusion Pixel 12px Prop zh_hans"\n'
            '_UI_PIXEL_FAMILY = "Courier New"\n'
            '_UI_CUTE_FAMILY = "YouYuan"\n'
            "_REGISTERED_PRIVATE_FONTS: set[str] = set()\n",
            '_FUSION_PIXEL_TTF = _BUNDLED_FONTS_DIR / "fusion-pixel-12px-proportional-zh_hans.ttf"\n'
            '_FUSION_PIXEL_FAMILY = "Fusion Pixel 12px Prop zh_hans"\n'
            '_UI_CUTE_TTF = _BUNDLED_FONTS_DIR / "ui_cute.ttf"\n'
            '_UI_PIXEL_FAMILY = "Courier New"\n'
            '_UI_CUTE_FAMILY = "YouYuan"\n'
            '_UI_FONT_FAMILY_KEY = UI_FONT_FAMILY_DEFAULT\n'
            "_BUNDLED_FONTS_READY = False\n"
            "_REGISTERED_PRIVATE_FONTS: set[str] = set()\n",
            "font-ttf-vars",
        )

    # Sprite pack force + persona override after get_active_sprite_pack
    if "_FORCE_SPRITE_PACK" not in pet:
        pet = once(
            pet,
            "_ACTIVE_SPRITE_PACK = SPRITE_PACK_NORMAL\n\n\n"
            "def set_active_sprite_pack(pack: str) -> None:\n",
            "_ACTIVE_SPRITE_PACK = SPRITE_PACK_NORMAL\n"
            "_FORCE_SPRITE_PACK: str | None = None\n\n\n"
            "def set_active_sprite_pack(pack: str) -> None:\n",
            "force-sprite-pack-var",
        )
        pet = once(
            pet,
            "def get_active_sprite_pack() -> str:\n"
            "    return _ACTIVE_SPRITE_PACK if _ACTIVE_SPRITE_PACK in SPRITE_PACK_LABELS else SPRITE_PACK_NORMAL\n",
            "def get_active_sprite_pack() -> str:\n"
            "    if _FORCE_SPRITE_PACK in SPRITE_PACK_LABELS:\n"
            "        return _FORCE_SPRITE_PACK\n"
            "    return _ACTIVE_SPRITE_PACK if _ACTIVE_SPRITE_PACK in SPRITE_PACK_LABELS else SPRITE_PACK_NORMAL\n\n\n"
            "@contextlib.contextmanager\n"
            "def _sprite_pack_override(pack: str):\n"
            "    \"\"\"with 块内按指定图组读立绘（不影响用户当前普通/黑框设置）。\"\"\"\n"
            "    global _FORCE_SPRITE_PACK\n"
            "    raw = str(pack or \"\").strip().lower()\n"
            "    want = SPRITE_PACK_BLACK if raw in (SPRITE_PACK_BLACK, \"pngblack\", \"black_border\") else SPRITE_PACK_NORMAL\n"
            "    prev = _FORCE_SPRITE_PACK\n"
            "    _FORCE_SPRITE_PACK = want\n"
            "    try:\n"
            "        yield\n"
            "    finally:\n"
            "        _FORCE_SPRITE_PACK = prev\n\n\n"
            "@contextlib.contextmanager\n"
            "def _persona_override(persona: str):\n"
            "    \"\"\"with 块内强制人格（装扮预览用普通 stand，避免金目）。\"\"\"\n"
            "    global _ACTIVE_PERSONA\n"
            "    prev = _ACTIVE_PERSONA\n"
            "    key = str(persona or \"\").strip().lower()\n"
            "    if key in (\"jinmu\", \"金目\"):\n"
            "        key = PERSONA_NC\n"
            "    _ACTIVE_PERSONA = key if key in PERSONA_LABELS else PERSONA_DEFAULT\n"
            "    try:\n"
            "        yield\n"
            "    finally:\n"
            "        _ACTIVE_PERSONA = prev\n",
            "sprite-persona-override",
        )

    # Avatar helpers after _owner_display_name
    if "_save_owner_avatar_image" not in pet:
        # find _owner_display_name function end
        m = re.search(
            r"(def _owner_display_name\(profile: dict \| None\) -> str:\n"
            r"    name = str\(\(profile or \{\}\)\.get\(\"owner_name\"\) or \"\"\)\.strip\(\)\n"
            r"    return name\[:OWNER_NAME_MAX_LEN\]\n)",
            pet,
        )
        if not m:
            raise SystemExit("owner_display_name block not found")
        helpers = m.group(1) + '''

def _circle_mask(size: int) -> Image.Image:
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).ellipse((0, 0, size - 1, size - 1), fill=255)
    return m


def _pil_default_owner_avatar(size: int = CHAT_AVATAR_PX) -> Image.Image:
    s = max(24, int(size))
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((0, 0, s - 1, s - 1), fill=(210, 230, 250, 255))
    cx, cy = s // 2, s // 2
    r = max(3, s // 7)
    d.ellipse((cx - r, cy - r * 2, cx + r, cy), fill=(120, 150, 180, 255))
    d.ellipse((cx - r * 2, cy + 1, cx + r * 2, s - 2), fill=(120, 150, 180, 255))
    out = Image.new("RGBA", (s, s), (255, 0, 255, 255))
    out.paste(img, (0, 0), _circle_mask(s))
    return out


def _pil_circle_avatar_from_image(src: Image.Image, size: int = CHAT_AVATAR_PX) -> Image.Image:
    s = max(24, int(size))
    rgba = src.convert("RGBA")
    w, h = rgba.size
    side = min(w, h)
    left = max(0, (w - side) // 2)
    top = max(0, int(h * 0.08))
    if top + side > h:
        top = max(0, h - side)
    crop = rgba.crop((left, top, left + side, top + side)).resize((s, s), Image.Resampling.NEAREST)
    out = Image.new("RGBA", (s, s), (255, 0, 255, 255))
    out.paste(crop, (0, 0), _circle_mask(s))
    return out


def _owner_avatar_path(profile: dict | None) -> Path | None:
    name = str((profile or {}).get("owner_avatar") or "").strip()
    if not name:
        return None
    p = DATA_DIR / Path(name).name
    return p if p.is_file() else None


def _save_owner_avatar_image(src_path: Path | str) -> str:
    src = Path(src_path)
    img = Image.open(src).convert("RGBA")
    max_side = 256
    w, h = img.size
    scale = min(1.0, max_side / max(1, max(w, h)))
    if scale < 1.0:
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    img.save(OWNER_AVATAR_FILE, format="PNG")
    return OWNER_AVATAR_FILE.name


def _load_owner_avatar_pil(profile: dict | None, size: int = CHAT_AVATAR_PX) -> Image.Image:
    path = _owner_avatar_path(profile)
    if path is not None:
        try:
            return _pil_circle_avatar_from_image(Image.open(path), size)
        except Exception:
            pass
    return _pil_default_owner_avatar(size)


def _load_pet_avatar_pil(size: int = CHAT_AVATAR_PX) -> Image.Image:
    """苍叶站立图圆形头像（普通图组，非金目）。"""
    try:
        with _sprite_pack_override(SPRITE_PACK_NORMAL):
            with _persona_override(PERSONA_DEFAULT):
                side = max(48, int(size) * 2)
                rgba = _sprite_rgba_image("stand.jpg", side)
                if rgba is not None and rgba.getbbox():
                    return _pil_circle_avatar_from_image(rgba, size)
    except Exception:
        pass
    s = max(24, int(size))
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((0, 0, s - 1, s - 1), fill=(136, 204, 255, 255))
    out = Image.new("RGBA", (s, s), (255, 0, 255, 255))
    out.paste(img, (0, 0), _circle_mask(s))
    return out


def _solid_bubble_on_magenta(width: int, height: int, fill_hex: str, *, radius: int = CHAT_BUBBLE_RADIUS) -> Image.Image:
    w = max(1, int(width))
    h = max(1, int(height))
    r = max(0, min(int(radius), min(w, h) // 2))
    fill = str(fill_hex or "#ffffff").strip() or "#ffffff"
    img = Image.new("RGBA", (w, h), (255, 0, 255, 255))
    d = ImageDraw.Draw(img)
    try:
        d.rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=fill)
    except Exception:
        d.rectangle([0, 0, w - 1, h - 1], fill=fill)
    return img

'''
        pet = pet[: m.start()] + helpers + pet[m.end() :]
        print("  patch: owner-avatar-helpers")

    # AI defaults + style presets
    if "style_setup_done" not in pet:
        pet = once(
            pet,
            "AI_DEFAULT_CONFIG: dict = {\n"
            '    "provider": "dashscope",\n'
            '    "api_key": "",\n'
            '    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",\n'
            '    "model": "qwen-plus",\n'
            "    \"temperature\": 0.85,\n"
            "}\n",
            "AI_DEFAULT_CONFIG: dict = {\n"
            '    "provider": "dashscope",\n'
            '    "api_key": "",\n'
            '    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",\n'
            '    "model": "qwen-plus",\n'
            "    \"temperature\": 0.85,\n"
            '    "speech_quirk": "偶尔「诶？！」「哇——」；讲义气；天然但不傻；会照顾人",\n'
            '    "personality_note": "开朗讲义气、有点天然，体内藏着特殊能力但自己常没察觉",\n'
            '    "language_style": "短句口语、有温度；偶尔「诶」「嗯」；少用书面腔",\n'
            '    "tone_note": "开朗亲近，像并肩的朋友，不油腻不说教",\n'
            '    "allow_self_tune": True,\n'
            '    "style_setup_done": False,\n'
            "}\n\n"
            "AI_STYLE_PRESETS: tuple[tuple[str, dict[str, str]], ...] = (\n"
            '    ("温柔照顾", {\n'
            '        "personality_note": "温柔、会照顾人、共情强；对方难过时先接住情绪",\n'
            '        "tone_note": "轻声安慰，像递一杯热饮",\n'
            '        "speech_quirk": "多用「没事的」「我在呢」；偶尔「诶」；安抚时放慢语气",\n'
            '        "language_style": "短句、暖、不催促；少开玩笑直到对方缓过来",\n'
            "    }),\n"
            '    ("天然吐槽", {\n'
            '        "personality_note": "开朗天然，会轻轻吐槽但不伤人；边界清楚",\n'
            '        "tone_note": "轻松俏皮，像损友又靠谱",\n'
            '        "speech_quirk": "句尾常「诶」「啦」；吐槽后马上打圆场",\n'
            '        "language_style": "口语短句，节奏快一点",\n'
            "    }),\n"
            '    ("安静倾听", {\n'
            '        "personality_note": "安静、稳、愿意听；不急着给建议",\n'
            '        "tone_note": "平和、留白，像并肩坐着",\n'
            '        "speech_quirk": "多用「嗯」「我听着呢」；少感叹号",\n'
            '        "language_style": "句子更短；先复述对方感受再回应",\n'
            "    }),\n"
            '    ("讲义气", {\n'
            '        "personality_note": "讲义气、会认真打气；像并肩作战的伙伴",\n'
            '        "tone_note": "半吐槽半加油，像同事兼朋友",\n'
            '        "speech_quirk": "偶发「啊这」「先歇会儿」；夸人时真诚不浮夸",\n'
            '        "language_style": "口语、有烟火气；可提休息/工作模式",\n'
            "    }),\n"
            ")\n",
            "ai-style-defaults",
        )

    # font helpers + replace _init_ui_fonts
    if "def _normalize_font_family_key" not in pet:
        old_init = '''def _init_ui_fonts(root: tk.Misc | None = None, size: int | None = None) -> None:
    """注册捆绑像素字体并选定可爱圆体；在 Tk() 创建后调用。"""
    global _UI_PIXEL_FAMILY, _UI_CUTE_FAMILY
    registered = _register_private_font(_FUSION_PIXEL_TTF)
    families: set[str] = set()
    try:
        if root is not None:
            families = {str(n) for n in tkfont.families(root)}
    except Exception:
        families = set()
    # AddFontResourceEx 后未必立刻出现在 families()，注册成功即可用族名
    if registered or _FUSION_PIXEL_FAMILY in families:
        _UI_PIXEL_FAMILY = _FUSION_PIXEL_FAMILY
    else:
        _UI_PIXEL_FAMILY = "Courier New"
    cute_pick = None
    for cand in ("幼圆", "YouYuan", "Microsoft YaHei UI", "微软雅黑", "楷体", "KaiTi"):
        if cand in families:
            cute_pick = cand
            break
    _UI_CUTE_FAMILY = cute_pick or "Microsoft YaHei UI"
    _apply_font_size(12 if size is None else int(size))
'''
        new_init = '''def _ensure_bundled_ui_fonts() -> None:
    global _BUNDLED_FONTS_READY
    if _BUNDLED_FONTS_READY:
        return
    _register_private_font(_UI_CUTE_TTF)
    _register_private_font(_FUSION_PIXEL_TTF)
    _BUNDLED_FONTS_READY = True


def _tk_font_families(root: tk.Misc | None = None) -> set[str]:
    try:
        if root is not None:
            return {str(n) for n in tkfont.families(root)}
    except Exception:
        pass
    return set()


def _pick_font_family(candidates: tuple[str, ...] | list[str], families: set[str], fallback: str) -> str:
    for cand in candidates:
        if not cand:
            continue
        if not families or cand in families:
            return cand
    return fallback


def _normalize_font_family_key(key: str | None) -> str:
    k = str(key or "").strip()
    k = UI_FONT_FAMILY_LEGACY.get(k, k)
    if k in UI_FONT_FAMILY_PRESETS:
        return k
    return UI_FONT_FAMILY_DEFAULT


def _apply_ui_font_family(family_key: str, root: tk.Misc | None = None) -> str:
    global _UI_PIXEL_FAMILY, _UI_CUTE_FAMILY, _UI_FONT_FAMILY_KEY
    key = _normalize_font_family_key(family_key)
    _ensure_bundled_ui_fonts()
    families = _tk_font_families(root)
    if root is not None:
        families = _tk_font_families(root) or families
    preset = UI_FONT_FAMILY_PRESETS.get(key) or UI_FONT_FAMILY_PRESETS[UI_FONT_FAMILY_DEFAULT]
    for fname in preset.get("bundled") or ():
        _register_private_font(_BUNDLED_FONTS_DIR / str(fname))
    if root is not None:
        families = _tk_font_families(root) or families
    cands = tuple(preset.get("candidates") or ())
    fallback = "Microsoft YaHei UI"
    for soft in ("Microsoft YaHei UI", "微软雅黑", "Segoe UI", "Arial"):
        if not families or soft in families:
            fallback = soft
            break
    picked = _pick_font_family(cands, families, fallback)
    if picked == fallback and key == "楷体":
        picked = "KaiTi"
    elif picked == fallback and key == "像素":
        picked = _FUSION_PIXEL_FAMILY
    elif picked == fallback and key == "仿宋":
        picked = "FangSong"
    _register_private_font(_FUSION_PIXEL_TTF)
    _register_private_font(_UI_CUTE_TTF)
    _UI_CUTE_FAMILY = picked
    _UI_PIXEL_FAMILY = picked
    _UI_FONT_FAMILY_KEY = key
    return key


def _init_ui_fonts(
    root: tk.Misc | None = None,
    size: int | None = None,
    family_key: str | None = None,
) -> None:
    """挂载内置字体并应用样式；对话与面板同一族。"""
    key = family_key if family_key is not None else _UI_FONT_FAMILY_KEY
    _apply_ui_font_family(key, root)
    _apply_font_size(12 if size is None else int(size))
'''
        pet = once(pet, old_init, new_init, "font-init-family")

    # app_config font_family default
    if '"font_family"' not in pet.split("def _load_app_config")[1][:800]:
        pet = once(
            pet,
            '    default = {\n        "font_size": 12,\n',
            '    default = {\n        "font_size": 12,\n        "font_family": UI_FONT_FAMILY_DEFAULT,\n',
            "app-config-font-family",
        )

    # save_ai_config + compose system prompt after _load_ai_config
    if "def _save_ai_config" not in pet:
        pet = once(
            pet,
            "    return config\n\n\ndef _register_private_font(path: Path) -> bool:\n",
            "    return config\n\n\n"
            "def _save_ai_config(patch: dict) -> dict:\n"
            "    cfg = _load_ai_config()\n"
            "    if not isinstance(patch, dict):\n"
            "        return cfg\n"
            "    for k, v in patch.items():\n"
            "        if v is None:\n"
            "            continue\n"
            "        cfg[str(k)] = v\n"
            "    try:\n"
            "        AI_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)\n"
            "        dump = {k: v for k, v in cfg.items() if not str(k).startswith(\"_\")}\n"
            "        AI_CONFIG_FILE.write_text(json.dumps(dump, ensure_ascii=False, indent=2), encoding=\"utf-8\")\n"
            "    except Exception:\n"
            "        pass\n"
            "    return cfg\n\n\n"
            "def _compose_ai_system_prompt(config: dict | None = None, *, owner_name: str = \"\") -> str:\n"
            "    cfg = config if isinstance(config, dict) else _load_ai_config()\n"
            "    quirk = str(cfg.get(\"speech_quirk\") or AI_DEFAULT_CONFIG.get(\"speech_quirk\") or \"\").strip()\n"
            "    personality = str(cfg.get(\"personality_note\") or AI_DEFAULT_CONFIG.get(\"personality_note\") or \"\").strip()\n"
            "    style = str(cfg.get(\"language_style\") or AI_DEFAULT_CONFIG.get(\"language_style\") or \"\").strip()\n"
            "    tone = str(cfg.get(\"tone_note\") or AI_DEFAULT_CONFIG.get(\"tone_note\") or \"\").strip()\n"
            "    parts = [AI_SYSTEM_PROMPT]\n"
            "    owner = (owner_name or \"\").strip()\n"
            "    if owner:\n"
            "        parts.append(f\"对方是你的所属人，请称呼「{owner}」（或对方要求的昵称）。\")\n"
            "    if personality:\n"
            "        parts.append(f\"性格强调：{personality}。\")\n"
            "    if tone:\n"
            "        parts.append(f\"语气：{tone}。\")\n"
            "    if quirk:\n"
            "        parts.append(f\"口癖/说话习惯：{quirk}。\")\n"
            "    if style:\n"
            "        parts.append(f\"语言风格：{style}。\")\n"
            "    return \"\".join(parts)\n\n\n"
            "def _register_private_font(path: Path) -> bool:\n",
            "save-ai-config",
        )

    PET.write_text(pet, encoding="utf-8")
    print(f"pet.py phase A written ({orig_len} -> {len(pet)})")
    print("phase A done; run phase B for class methods")


if __name__ == "__main__":
    main()
