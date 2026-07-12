"""桌面桌宠 v1.2：四大模块菜单、打电话对话框、跟随鼠标、面板与大小调节。"""

import array
import ctypes
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from ctypes import wintypes
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageDraw, ImageTk


def _resolve_app_paths() -> tuple[Path, Path]:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS), Path(sys.executable).resolve().parent / "data"
    root = Path(__file__).resolve().parent
    return root, root / "data"


def _read_build_stamp() -> str:
    app_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    stamp_file = app_dir / "BUILD_STAMP.txt"
    if stamp_file.exists():
        try:
            return stamp_file.read_text(encoding="utf-8").strip()
        except Exception:
            return ""
    return ""


BUNDLE_DIR, DATA_DIR = _resolve_app_paths()
ASSETS_DIR = BUNDLE_DIR / "assets"
SPRITES_DIR = ASSETS_DIR / "sprites"
PROPS_DIR = ASSETS_DIR / "props"
MINIPET_DIR = ASSETS_DIR / "minipet"
AUDIO_ASSET_DIR = ASSETS_DIR / "audio"
GALLERY_DIR = BUNDLE_DIR / "gallery"
GALLERY_CONFIG_FILE = GALLERY_DIR / "gallery.json"
GALLERY_THUMB_SIZE = 72
GALLERY_PREVIEW_SIZE = 160
GALLERY_COLS = 3
GALLERY_WIN_W = 360
GALLERY_SCROLL_H = 200
GALLERY_ARROW_ZONE = 0.28
# 面板过大时统一固定窗口尺寸，内容区滚动查看（与画廊同模式）
PANEL_FIXED_W = 400
PANEL_FIXED_H = 480

DEFAULT_GALLERY_GROUPS: tuple[dict, ...] = (
    {"title": "站立", "files": ("stand.jpg",)},
    {"title": "开心", "files": ("happy.jpg",)},
    {"title": "打招呼", "files": ("hi1.jpg", "hi2.jpg")},
    {"title": "Wink", "files": ("wink.jpg",)},
    {"title": "点赞", "files": ("like.jpg",)},
    {"title": "下蹲", "files": ("squat.jpg",)},
    {"title": "侧踢", "files": ("kick.jpg",)},
    {"title": "伤心", "files": ("sad1.jpg", "sad2.jpg")},
    {"title": "吃东西", "files": ("eat1.jpg", "eat2.jpg")},
    {"title": "睡眠", "files": ("sleep1.jpg", "sleep2.jpg")},
    {"title": "害羞", "files": ("shy1.jpg", "shy2.jpg")},
    {"title": "是 / 否", "files": ("yes.jpg", "no.jpg")},
    {"title": "打电话", "files": ("call1.jpg", "call2.jpg")},
    {"title": "移动", "files": ("move1.jpg", "move2.jpg", "move3.jpg")},
    {"title": "行走·正面", "files": ("walkfront1.jpg", "walkfront2.jpg")},
    {"title": "行走·背面", "files": ("walkback1.jpg", "walkback2.jpg")},
    {"title": "行走·侧面", "files": ("walkleft1.jpg", "walkleft2.jpg")},
    {"title": "工作·站立", "files": ("workstand.jpg",)},
    {"title": "工作·正面", "files": ("workfront1.jpg", "workfront2.jpg")},
    {"title": "工作·背面", "files": ("workback1.jpg", "workback2.jpg")},
    {"title": "工作·侧面", "files": ("workleft1.jpg", "workleft2.jpg")},
    {"title": "音乐·站立", "files": ("musicstand.jpg",)},
    {"title": "音乐·正面", "files": ("musicfront1.jpg", "musicfront2.jpg")},
    {"title": "音乐·背面", "files": ("musicback1.jpg", "musicback2.jpg")},
    {"title": "音乐·侧面", "files": ("musicleft1.jpg", "musicleft2.jpg")},
    {"title": "生气", "files": ("stand.jpg",), "sticker": "angry"},
    {"title": "疑问", "files": ("stand.jpg",), "sticker": "question"},
)
DATA_AUDIO_DIR = DATA_DIR / "audio"
CALL_AUDIO_SRC = Path(r"C:\Users\36255\Desktop\call.mp3.mp4")
CALL_AUDIO_WAV = DATA_AUDIO_DIR / "call_cache.wav"
TYPE_AUDIO_SRC = Path(r"C:\Users\36255\Desktop\type.mp4")
TYPE_AUDIO_WAV = DATA_AUDIO_DIR / "type_cache.wav"
MUSIC_SRC_DIR = Path(r"C:\Users\36255\Desktop\Vpetmusic")
MUSIC_CONFIG_FILE = DATA_DIR / "music_config.json"
PHONOGRAPH_FILE = DATA_DIR / "phonograph.json"
PHONOGRAPH_USER_DIR = DATA_DIR / "phonograph"

# 固定 id / 标题（其余按文件名自动生成）；默认曲 = RADICAL MAT（替换原 aicatch）
MUSIC_TRACK_ID_MAP: dict[str, str] = {
    "RADICAL MAT": "radical_mat",
    "AI CATCH": "ai_catch",
    "Crystalline": "crystalline",
    "your reply": "your_reply",
    "SLIP ON THE PUMPS": "slip_on_the_pumps",
    "By My Side": "by_my_side",
    "felt": "felt",
    "Lullaby Blue": "lullaby_blue",
    "Soul Grace": "soul_grace",
    "天使達": "tenshitachi",
    "クラゲの歌 -extend electro-": "kurage_extend",
    "クラゲの歌 -extend strings-": "kurage_extend_strings",
    "クラゲの歌‘": "kurage",
    "Tears": "tears",
    "feel your noise": "feel_your_noise",
    "MASCULINE DEVIL": "masculine_devil",
    "bad end": "bad_end",
    "Only finally there is the free end": "free_end",
    "At Last": "at_last",
    "COSMOCALL FIELD": "cosmocall_field",
    "Deeds,not words": "deeds_not_words",
    "FORM SWEET FORM": "form_sweet_form",
    "HOLO GHOST": "holo_ghost",
    "Milky Way": "milky_way",
}
MUSIC_TRACK_TITLE_MAP: dict[str, str] = {
    "radical_mat": "RADICAL MAT",
    "ai_catch": "AI CATCH",
    "crystalline": "Crystalline",
    "your_reply": "your reply",
    "kurage": "クラゲの歌",
    "kurage_extend": "クラゲの歌 -extend electro-",
    "kurage_extend_strings": "クラゲの歌 -extend strings-",
    "tenshitachi": "天使達",
}
MUSIC_TRACK_PREFERRED_ORDER: tuple[str, ...] = (
    "radical_mat",
    "ai_catch",
    "crystalline",
    "your_reply",
    "slip_on_the_pumps",
    "by_my_side",
    "felt",
    "lullaby_blue",
    "soul_grace",
    "tenshitachi",
    "kurage",
    "kurage_extend",
    "kurage_extend_strings",
)
# 旧配置 id 迁移
MUSIC_TRACK_LEGACY_IDS: dict[str, str] = {
    "aicatch": "radical_mat",
    "extend_strings": "kurage_extend_strings",
}


def _music_slug_id(stem: str) -> str:
    mapped = MUSIC_TRACK_ID_MAP.get(stem)
    if mapped:
        return mapped
    slug = re.sub(r"[^0-9A-Za-z]+", "_", stem).strip("_").lower()
    if slug:
        return slug
    return f"track_{abs(hash(stem)) % 10**8:x}"


def _build_music_tracks() -> tuple[dict[str, dict], tuple[str, ...]]:
    tracks: dict[str, dict] = {}
    if not MUSIC_SRC_DIR.is_dir():
        return tracks, ()
    for path in sorted(MUSIC_SRC_DIR.iterdir(), key=lambda p: p.name.lower()):
        if not path.is_file() or path.suffix.lower() != ".mp4":
            continue
        stem = path.stem
        tid = _music_slug_id(stem)
        title = MUSIC_TRACK_TITLE_MAP.get(tid) or stem
        # 同 id 重复时保留先出现的（优先 preferred 排序时再覆盖顺序）
        if tid in tracks:
            continue
        tracks[tid] = {
            "id": tid,
            "title": title,
            "src": path,
            "cache": DATA_AUDIO_DIR / f"music_{tid}_cache.wav",
            "phonograph": f"音乐·{title}",
        }
    order: list[str] = []
    for tid in MUSIC_TRACK_PREFERRED_ORDER:
        if tid in tracks:
            order.append(tid)
    for tid in sorted(tracks.keys(), key=lambda t: str(tracks[t]["title"]).lower()):
        if tid not in order:
            order.append(tid)
    return tracks, tuple(order)


MUSIC_TRACKS, MUSIC_TRACK_ORDER = _build_music_tracks()
DEFAULT_MUSIC_TRACK = (
    "radical_mat"
    if "radical_mat" in MUSIC_TRACKS
    else (MUSIC_TRACK_ORDER[0] if MUSIC_TRACK_ORDER else "radical_mat")
)

# 曲目版面图标：像素音符 + border.png 外框（不用 Vpetsign）
PLATE_BORDER_PATH = ASSETS_DIR / "ui" / "border.png"
PLATE_BORDER_FALLBACK = Path(__file__).resolve().parent / "border.png"
MUSIC_PLATE_ICON_PX = 56
MUSIC_PLATE_INNER_RATIO = 0.70
MUSIC_PLATE_INNER_ALPHA = 0.72  # 中间图标略降不透明度，突出边框
MUSIC_PICKER_COLS = 4
_MUSIC_ICON_PHOTO_CACHE: dict[tuple, ImageTk.PhotoImage] = {}
_PLATE_BORDER_CACHE: dict[int, Image.Image] = {}


def _cutout_near_black(img: Image.Image, *, thresh: int = 40) -> Image.Image:
    rgba = img.convert("RGBA")
    px = rgba.load()
    w, h = rgba.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if r <= thresh and g <= thresh and b <= thresh:
                px[x, y] = (0, 0, 0, 0)
            elif max(r, g, b) <= thresh + 16 and abs(r - g) < 10 and abs(g - b) < 10:
                px[x, y] = (0, 0, 0, 0)
    return rgba


def _plate_border_image(size: int) -> Image.Image | None:
    cached = _PLATE_BORDER_CACHE.get(size)
    if cached is not None:
        return cached
    path = PLATE_BORDER_PATH if PLATE_BORDER_PATH.exists() else PLATE_BORDER_FALLBACK
    if not path.exists():
        return None
    try:
        border = Image.open(path).convert("RGBA")
        # 若四角仍是不透明黑底，再抠一次
        sample = border.getpixel((2, 2))
        if sample[3] > 200 and sample[0] < 50 and sample[1] < 50 and sample[2] < 50:
            border = _cutout_near_black(border)
        border = border.resize((size, size), Image.NEAREST)
        _PLATE_BORDER_CACHE[size] = border
        return border
    except Exception:
        return None


def _scale_rgba_alpha(img: Image.Image, factor: float) -> Image.Image:
    rgba = img.convert("RGBA")
    r, g, b, a = rgba.split()
    a = a.point(lambda v, f=factor: max(0, min(255, int(v * f))))
    return Image.merge("RGBA", (r, g, b, a))


def _make_pixel_headphone_icon(size: int = 18) -> Image.Image:
    """菜单用像素耳机图标。"""
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    band = "#88ccff"
    cup = "#66aadd"
    dark = "#223355"
    # headband
    d.rectangle([3, 2, 12, 3], fill=band)
    d.rectangle([2, 3, 3, 7], fill=band)
    d.rectangle([12, 3, 13, 7], fill=band)
    # ear cups
    d.rectangle([1, 7, 5, 13], fill=cup)
    d.rectangle([10, 7, 14, 13], fill=cup)
    d.rectangle([2, 8, 4, 12], fill="#aadfff")
    d.rectangle([11, 8, 13, 12], fill="#aadfff")
    d.rectangle([1, 7, 5, 13], outline=dark)
    d.rectangle([10, 7, 14, 13], outline=dark)
    return img.resize((size, size), Image.NEAREST)


_MENU_KIND_ICON_CACHE: dict[tuple[str, int], ImageTk.PhotoImage] = {}


def _menu_kind_icon_photo(kind: str, size: int = 16) -> ImageTk.PhotoImage:
    key = (kind, int(size))
    photo = _MENU_KIND_ICON_CACHE.get(key)
    if photo is not None:
        return photo
    if kind == "music":
        img = _make_pixel_headphone_icon(size)
    else:
        img = _make_pixel_music_fallback_icon(abs(hash(kind)), size)
    photo = ImageTk.PhotoImage(img)
    _MENU_KIND_ICON_CACHE[key] = photo
    return photo


def _make_pixel_music_fallback_icon(index: int, size: int = 48) -> Image.Image:
    """曲目版面图标：像素音符 + 色块（按曲目序号换色）。"""
    palette = (
        "#66ccff",
        "#ff88cc",
        "#ffcc66",
        "#88ffaa",
        "#cc88ff",
        "#88aaff",
        "#ffaa88",
        "#aaffcc",
    )
    col = palette[index % len(palette)]
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # stem
    d.rectangle([10, 2, 12, 11], fill=col)
    # flag
    d.rectangle([7, 2, 10, 5], fill=col)
    # note head
    d.ellipse([4, 9, 11, 14], fill=col)
    d.rectangle([1, 1, 14, 14], outline="#223355")
    return img.resize((size, size), Image.NEAREST)


def _music_track_content_image(track_id: str, inner: int) -> Image.Image:
    try:
        idx = list(MUSIC_TRACK_ORDER).index(track_id)
    except ValueError:
        idx = abs(hash(track_id)) % max(1, len(MUSIC_TRACK_ORDER) or 1)
    return _make_pixel_music_fallback_icon(idx, inner)


def _music_track_icon_image(track_id: str, size: int = MUSIC_PLATE_ICON_PX) -> Image.Image:
    """版面图标 = 中间标识（略透明）+ border 外框。"""
    inner = max(16, int(size * MUSIC_PLATE_INNER_RATIO))
    content = _music_track_content_image(track_id, inner)
    content = _scale_rgba_alpha(content, MUSIC_PLATE_INNER_ALPHA)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    # 中间轻微底色，避免边框内太空
    pad = (size - inner) // 2
    fill = Image.new("RGBA", (inner, inner), (12, 18, 28, 55))
    canvas.paste(fill, (pad, pad), fill)
    canvas.paste(content, (pad, pad), content)
    border = _plate_border_image(size)
    if border is not None:
        canvas.alpha_composite(border)
    else:
        # 无边框素材时画一圈简易描边
        d = ImageDraw.Draw(canvas)
        d.rectangle([1, 1, size - 2, size - 2], outline="#66ccff")
        d.rectangle([3, 3, size - 4, size - 4], outline="#88e0ff")
    return canvas


def _music_track_icon_photo(track_id: str, size: int = MUSIC_PLATE_ICON_PX) -> ImageTk.PhotoImage:
    key = (str(track_id), int(size), "pixel_v1")
    photo = _MUSIC_ICON_PHOTO_CACHE.get(key)
    if photo is None:
        photo = ImageTk.PhotoImage(_music_track_icon_image(track_id, size))
        _MUSIC_ICON_PHOTO_CACHE[key] = photo
    return photo



def _ensure_data_dirs() -> None:
    for folder in (
        DATA_DIR,
        DATA_AUDIO_DIR,
        PHONOGRAPH_USER_DIR,
        SPRITES_DIR,
        PROPS_DIR,
        MINIPET_DIR,
        AUDIO_ASSET_DIR,
    ):
        folder.mkdir(parents=True, exist_ok=True)


def _migrate_legacy_layout() -> None:
    if getattr(sys, "frozen", False):
        return
    root = Path(__file__).resolve().parent
    for name in (
        "app_config.json",
        "pet_profile.json",
        "food_inventory.json",
        "diary.json",
        "schedules.json",
        "music_config.json",
        "pet_id_registry.json",
        "vocab.json",
        "ai_config.json",
    ):
        src, dst = root / name, DATA_DIR / name
        if src.is_file() and not dst.exists():
            shutil.copy2(src, dst)
    for name in (
        "call_cache.wav",
        "type_cache.wav",
    ):
        src, dst = root / name, DATA_AUDIO_DIR / name
        if src.is_file() and not dst.exists():
            shutil.copy2(src, dst)
    for path in root.glob("*.jpg"):
        name = path.name
        if name in {"box.jpg", "flag.jpg"}:
            dst = PROPS_DIR / name
        elif name.startswith("pet"):
            dst = MINIPET_DIR / name
        else:
            dst = SPRITES_DIR / name
        if not dst.exists():
            shutil.copy2(path, dst)


def _asset_path(filename: str) -> Path:
    if filename.startswith("pet"):
        for base in (MINIPET_DIR, SPRITES_DIR, BUNDLE_DIR):
            path = base / filename
            if path.is_file():
                return path
    if filename in {"box.jpg", "flag.jpg"}:
        path = PROPS_DIR / filename
        if path.is_file():
            return path
    for base in (SPRITES_DIR, PROPS_DIR, MINIPET_DIR, BUNDLE_DIR):
        path = base / filename
        if path.is_file():
            return path
    return SPRITES_DIR / filename


DEFAULT_SIZE = 128
SIZE_PRESETS: dict[str, int] = {"小": 96, "中": 128, "大": 176}

WALK_FRAME_MS = 180
MOVE_INTERVAL_MS = 50
MOVE_STEP = 3
FOLLOW_MOVE_STEP = 4
FOLLOW_MOVE_INTERVAL_MS = 40
ACTION_FRAME_MS = 180
INTERACT_DURATION_MS = 3000
WINK_DURATION_MS = 3200
YESNO_WAIT_MS = 5000
YESNO_ANSWER_TEXT = "你所问问题的答案是"
INTERACT_DURATIONS: dict[str, int] = {
    "squat": 2500,
    "eat": 3800,
    "angry": 4600,
    "question": 3200,
    "sad": 5000,
    "idea": 4000,
    "happy": 4800,
    "kick": 1200,
    "shy": 3600,
    "wink": WINK_DURATION_MS,
    "like": WINK_DURATION_MS,
    "yes": 2600,
    "no": 2600,
    "yesno": YESNO_WAIT_MS + 3200,
    "expose": 4500,
    "default": 3200,
}
SLEEP_INTERACT_MS = 30000
HAPPY_CYCLES = 3
HAPPY_JUMP_PX = 14
HAPPY_FRAME_MS = 220
FOLLOW_STOP_DIST = 65
FOLLOW_FAR_DIST = 220
FOLLOW_WAIT_COOLDOWN_MS = 8000
MODE_VIA_FREE_MS = 380

STAMINA_TICK_MS = 15000
STAMINA_DECAY = 1
INTERACT_MOOD_GAIN = 2
LOW_STAMINA_THRESHOLD = 30
HUNGER_REMINDER_COOLDOWN_MS = 45000
MOOD_HAPPY_THRESHOLD = 95
MOOD_AFTER_HAPPY = 85
TOAST_DURATION_MS = 2500
PANEL_AUTO_CLOSE_MS = 8000
PANEL_REPOSITION_MIN_MS = 2800
MAIN_MENU_AUTO_CLOSE_MS = 8000
POPUP_EDGE_MARGIN = 20
POPUP_PET_GAP = 10
PET_MENU_GAP_Y = 4
PET_SUBMENU_GAP_Y = 6
PET_SPEECH_GAP = 6
PET_MENU_FOLLOW_MS = 320
PET_SPEECH_FOLLOW_MS = 180
PANEL_BAR_W = 140
PANEL_BAR_H = 16
PANEL_STAT_ICON = 22
PANEL_FOOD_ICON_PX = 4
PANEL_FOOD_CANVAS = 46
PANEL_FOOD_COLS = 2
PANEL_BACKPACK_W = 280
PANEL_BACKPACK_H = 220

SLEEP_STAMINA_THRESHOLD = 25
SLEEP_WAKE_STAMINA = 65
SLEEP_STAMINA_RECOVER = 4
SLEEP_RECOVER_MS = 3000
SLEEP_TRANSITION_MS = 600
SLEEP_DEEP_HOLD_MS = 30000
SLEEP_ZZZ_MS = 700

REST_BOBBLE_PX = 3
REST_BOBBLE_MS = 160
REST_BOBBLE_PAUSE_MIN_MS = 2500
REST_BOBBLE_PAUSE_MAX_MS = 4500

REST_CLICK_WINDOW_MS = 900
REST_WAKE_CLICKS = 5
REST_PEEK_CLICKS = 2
REST_PEEK_MS = 1000

CLICK_BOUNCE_PX = 6
CLICK_BOUNCE_MS = 100

TYPEWRITER_MS = 70
HI_TYPEWRITER_MS = 130
TYPE_TICK_SEC = 0.08
MOVE23_DURATION_MS = 2500
MOVE1_DURATION_MS = 5000
MOVE23_FRAME_MS = 90
MOVE_DRAG_CYCLES = 2
MOVE_CYCLE_MS = MOVE23_DURATION_MS + MOVE1_DURATION_MS

GAME_TICK_MS = 16
GAME_BOX_SPEED = 5
GAME_SPAWN_MS = 1100
GAME_BOX_SIZE = 76
GAME_CATCH_DIST = 48
GAME_DURATION_MS = 30000
GAME_SCORE_PER_CATCH = 10
GAME_PENALTY_MISS = 2
GAME_TIME_ITEM_DELTA_MS = 3000
GAME_DIZZY_STUN_MS = 3000
GAME_SPECIAL_DROP_CHANCE = 0.24
GAME_TIME_MINUS_WEIGHT = 0.55
GAME_TIME_PLUS_WEIGHT = 0.15
GAME_DIZZY_WEIGHT = 0.30
GAME_BOX_SPEED_MIN_MULT = 0.55
GAME_BOX_SPEED_MAX_MULT = 1.55
GAME_DIZZY_LINES: tuple[str, ...] = (
    "呜…好像偏头痛…",
    "头好痛…",
    "眼前怎么还在转…",
    "别扔了…我晕…",
    "像是被像素砸中了脑袋…",
)
GAME_CLEAR_W = 320
GAME_CLEAR_H = 220
GAME_CLEAR_MS = 80
GAME_CLEAR_HOLD_MS = 1800
GAME_CLEAR_FRAMES = 16
VOCAB_CLEAR_STREAK = 5
VOCAB_CORRECT_ADVANCE_MS = 120
VOCAB_WRONG_ADVANCE_MS = 1400
VOCAB_OPTION_OK = "#3a9a4a"
VOCAB_OPTION_ERR = "#bb4444"
VOCAB_OPTION_DIM = "#2a3344"
RHYME_SPECIAL_COOLDOWN_MS = 10000  # 必杀冷却 10 秒

WORK_ARRIVE_DIST = 18
WORK_MIN_SPAN_DIST = 300
WORK_TOTAL_MIN = 3
WORK_TOTAL_MAX = 8
WORK_BOX_TOTAL_DEFAULT = 5
WORK_TOTAL_SETTING_MIN = 1
WORK_TOTAL_SETTING_MAX = 30
WORK_PROP_SIZE = 104
WORK_STACK_OFFSET = 22
WORK_MODE_BANTER_COOLDOWN_MS = 30_000
WORK_MODE_BANTER_INTERVAL_MS = (30_000, 90_000)
WORK_MODE_BANTER: tuple[str, ...] = (
    "一起加油，努力工作！",
    "嘿咻嘿咻~ 货物交给我！",
    "打工人打工魂，认真运送每一批货物~",
    "你今天也很努力呢，一起加油吧！",
    "平凡也要把活干漂亮！",
    "加油加油，终点就在前面！",
    "运完这批还有下一批…但我们会坚持的！",
    "旧货店的活儿，交给我就好~",
)
BULB_FX_SIZE = 144
AI_DIALOG_HIDE_MS = 5000
AI_CHAT_IDLE_MS = 5000

EXPRESSION_BOUNCE_PX = 8
EXPRESSION_BOUNCE_MS = 90
KICK_BOUNCE_PX = 14
KICK_BOUNCE_MS = 110
ANGRY_FRAME_MS = 280
ANGRY_WALK_LIFT_PX = 12
ANGRY_WALK_UP_PER_STEP = 4
ANGRY_WALK_MAX_LIFT = 32
IDEA_STAND_MS = 420
BULB_OFFSET_DOWN = 20
BULB_HEAD_GAP = 28
BULB_GLOW_MS = 160
FOLLOW_DIZZY_SPIN_STEPS = 4
FOLLOW_DIZZY_STAND_MS = 1500
FOLLOW_DIZZY_TEXT = "我晕了……"
FOLLOW_DIR_ORDER = ("front", "right", "back", "left")
DRAG_DIZZY_SPIN_STEPS = 4
DRAG_DIZZY_MIN_DELTA = 4
DRAG_DIZZY_DIALOG_COOLDOWN_MS = 3200
DRAG_DIZZY_EXTRA_DIALOG_SPINS = 4
DRAG_DIZZY_LINES: tuple[str, ...] = (
    "别晃啦我晕了……",
    "慢—慢—点—拖—我—",
    "鼠标在飞吗？",
    "天旋地转……",
    "呕……别摇了",
    "再晃要吐了啦！",
    "拖我别当甩干机啊！",
)
MOOD_LOW_THRESHOLD = 40
MOOD_RANDOM_CHANCE = 0.09
MOOD_TIER_LABELS: list[tuple[int, str, str]] = [
    (85, "极好", "#ff88cc"),
    (65, "开心", "#88dd88"),
    (45, "普通", "#4488ff"),
    (25, "低落", "#ffaa44"),
    (0, "沮丧", "#ff4444"),
]
WORK_MOVE_STEP = MOVE_STEP * 2
WORK_MOVE_INTERVAL_MS = max(28, MOVE_INTERVAL_MS // 2 + 8)
GAME_NEAR_DIST = 72
SHY_DOUBLE_CLICK_MS = 350
MINI_PET_SIZE = 120
MINI_PET_LIFE_MS = 9000
MINI_PET_FOLLOW_MS = 45
MINI_PET_FOLLOW_STEP = 3
MINI_PET_GAME_FOLLOW_MS = 22
MINI_PET_GAME_FOLLOW_STEP = 9
MINI_PET_WORK_FOLLOW_MS = 16
MINI_PET_WORK_FOLLOW_STEP = 12
MINI_PET_BOUNCE_MS = 520
MINI_PET_BOUNCE_PX = 4
MINI_PET_MAX = 5
SAD_SQUAT_MS = 1000
SAD_SAD1_MS = 1000
SAD_SAD2_MS = 3000
MINI_PET_SIDE_GAP = 6
MINI_PET_SAD_GAP = 22
MINI_PET_ANGRY_GAP = 20
TYPING_GAME_MS = 30000
TYPING_MOOD_SIZE = 88
TYPING_GRADE_BAR_H = 40
TYPING_GRADE_TIERS: tuple[tuple[str, int, str], ...] = (
    ("D", 0, "#ff6666"),
    ("C", 5, "#ffaa44"),
    ("B", 10, "#4488ff"),
    ("A", 15, "#88dd88"),
    ("S", 20, "#ff88cc"),
)
TYPING_GRADE_LABELS: dict[str, str] = {
    "S": "完美",
    "A": "优秀",
    "B": "良好",
    "C": "及格",
    "D": "加油",
}
TYPING_CLEAR_HOLD_MS = 3400
TYPING_MOOD_FILES: dict[str, str] = {
    "D": "sad1.jpg",
    "C": "squat.jpg",
    "B": "stand.jpg",
    "A": "happy.jpg",
    "S": "like.jpg",
}
MULTI_CLICK_WINDOW_MS = 850
SIZE_LOAD_ANIM_MS = 30
SIZE_LOAD_MIN_MS = 72
SIZE_LOAD_MIN_CACHED_MS = 44
COMPANION_LOAD_MIN_MS = 72
COMPANION_LOAD_MIN_CACHED_MS = 44
STARTUP_ANIM_MS = 45
STARTUP_MIN_MS = 320
WAIT_HINT_DEFAULT = "请耐心等待…"
WAIT_HINT_TICK_MS = 500
SPRITE_BATCH_SIZE = 5
SPRITE_BATCH_MS = 16
UI_BUSY_LAG_THRESHOLD_MS = 500
IDLE_WATCHDOG_MS = 5000
FOOD_DRAG_ICON = 40
FOOD_DROP_MS = 480
FOOD_DROP_ARC = 72
INTERACT_FX_MS = 80
INTERACT_FX_PAD = 28
INTERACT_FX_DURATION_MS = 3000
MOVE_LAND_PX = 34
MOVE_LAND_MS = 160
MOOD_EXPRESSION_TIERS: list[tuple[int, list[str]]] = [
    (85, ["happy", "like", "wink"]),
    (65, ["hi", "idea", "question"]),
    (45, ["squat", "question"]),
    (25, ["sad"]),
    (0, ["sad", "angry"]),
]
FREE_RANDOM_ACTION_CHANCE = 0.06
EXPOSE_QTE_TICK_MS = 16
EXPOSE_GLITCH_HITS_REQUIRED = 5
EXPOSE_GLITCH_ALERT_W = 240
EXPOSE_GLITCH_ALERT_H = 132
EXPOSE_GLITCH_REFRESH_MS = 900
EXPOSE_QTE_GAP = 12
FAULT_ALERT_MESSAGES = (
    "⚠ 系统故障",
    "⚠ 连接异常",
    "⚠ 数据损坏",
    "⚠ MEMORY ERROR",
    "⚠ SYNC FAIL",
    "⚠ 信号丢失",
)
FACE_DCLICK_MS = 350
FACE_DCLICK_COMBOS_NEEDED = 3
FACE_DCLICK_COMBO_RESET_MS = 4500
EXIT_DISSOLVE_MS = SIZE_LOAD_ANIM_MS
EXIT_DISSOLVE_FRAMES = 36
EXPOSE_RING_PAD = 36
EXPOSE_BLUE_SPAN = 60
EXPOSE_BLUE_SPAN_MIN = 18
EXPOSE_BLUE_SPAN_RATIOS: tuple[float, ...] = (1.0, 0.82, 0.66, 0.50, 0.36)
EXPOSE_POINTER_SPEED = 4.5
EXPOSE_SPEED_STREAK_MULT = 0.12
EXPOSE_SPEED_TICK_BOOST = 0.015
EXPOSE_POINTER_MAX_SPEED = 15.0
GAME_COUNTDOWN_STEP_MS = 650
GAME_COUNTDOWN_W = 120
GAME_COUNTDOWN_H = 120
COUNTDOWN_FONT = ("Courier New", 42, "bold")
MUSIC_WAVE_MS = 60
FOOD_INVENTORY_FILE = DATA_DIR / "food_inventory.json"
ADULT_CONTENT_TEXT = "我只是像素哦，更多精彩内容请在正版游戏《戏剧性谋杀》中解锁"
RESERVED_TOAST = "敬请期待~"

SCHEDULE_FILE = DATA_DIR / "schedules.json"
AI_CONFIG_FILE = DATA_DIR / "ai_config.json"
REMINDER_CHECK_MS = 15000
REMINDER_COLOR = "#ff4444"
WEEKDAY_LABELS = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")

# 打包两个版本：有编号版 PET_ID_FEATURE=True；无编号版改为 False
PET_ID_FEATURE = True
APP_CONFIG_FILE = DATA_DIR / "app_config.json"
PET_PROFILE_FILE = DATA_DIR / "pet_profile.json"
DIARY_FILE = DATA_DIR / "diary.json"
VOCAB_FILE = DATA_DIR / "vocab.json"
VOCAB_NOTEBOOK_FILE = DATA_DIR / "vocab_notebook.json"
WORD_BANKS_DIR = BUNDLE_DIR / "word_banks"
PET_ID_REGISTRY_FILE = DATA_DIR / "pet_id_registry.json"
LEADERBOARD_FILE = DATA_DIR / "leaderboard.json"
LEADERBOARD_MAX = 50
GAME_RANK_TITLES: dict[str, str] = {
    "gather": "采集",
    "typing": "打字",
    "vocab": "背单词",
    "rhyme": "莱姆对战",
    "music": "音乐",
}
RHYTHM_LANES = 4
RHYTHM_KEYS = ("d", "f", "j", "k")
RHYTHM_KEY_LABELS = ("D", "F", "J", "K")
RHYTHM_LANE_COLORS = ("#66ccff", "#88ffaa", "#ffcc66", "#ff88cc")
RHYTHM_W = 420
RHYTHM_H = 600
RHYTHM_TRAVEL_MS = 1400
RHYTHM_SPEED_TRAVEL_MS: dict[str, int] = {"慢": 1800, "中": 1400, "快": 1000}
RHYTHM_HIT_PERFECT_MS = 55
RHYTHM_HIT_GREAT_MS = 110
RHYTHM_HIT_GOOD_MS = 170
RHYTHM_BPM = 120  # 仅作音频分析失败时的回退
RHYTHM_CHART_CACHE_VER = 5  # v5：含长按长音
RHYTHM_HOLD_RELEASE_MS = 180  # 长音尾部松键判定窗
RHYTHM_ANALYZE_MAX_SEC = 75.0  # 用前 N 秒估 BPM/相位，再铺满全曲
RHYTHM_TICK_MS = 33  # ~30fps，减轻卡顿
RHYTHM_PLAY_CAP_MS = 0  # 默认：0 = 不截断；开局可选 90s
RHYTHM_SHORT_CAP_MS = 90000
RHYTHM_GRADE_BAR_REFRESH_MS = 200
RHYTHM_GRADE_BAR_H = 40
RHYTHM_GRADE_TIERS: tuple[tuple[str, int, str], ...] = (
    ("D", 0, "#ff6666"),
    ("C", 50, "#ffaa44"),
    ("B", 70, "#4488ff"),
    ("A", 85, "#88dd88"),
    ("S", 95, "#ff88cc"),
)
RHYTHM_GRADE_LABELS: dict[str, str] = {
    "S": "完美",
    "A": "优秀",
    "B": "良好",
    "C": "及格",
    "D": "加油",
}
FONT_SIZE_PRESETS: dict[str, int] = {"小": 10, "中": 12, "大": 14, "特大": 16}
ABOUT_DEVELOPER = "翛然而往"
ABOUT_REPO_URL = "https://github.com/zjl2401/VpetAOBA"
ABOUT_STEAM_URL = "https://store.steampowered.com/search/?term=DRAMatical+Murder"
ABOUT_NITROCHIRAL_URL = "https://www.nitrochiral.com/"
RHYTHM_CARNIVAL_URL = "https://www.nitrochiral.com/game/rhythm-carnival/"
RHYTHM_CARNIVAL_TITLE = "THE CHiRAL NIGHT rhythm carnival"
RHYTHM_CARNIVAL_INTRO = (
    "Nitro+CHiRAL 官方已推出节奏动作游戏《THE CHiRAL NIGHT rhythm carnival》\n"
    "（ザ・キラルナイト リズムカーニバル）。\n\n"
    "以 10 周年纪念演唱会「THE CHiRAL NIGHT 10th ANNIVERSARY」为题材，\n"
    "收录多首历作主题曲（含《DRAMAtical Murder》相关曲目如 AI CATCH），\n"
    "并附带演唱会影像与剧情演出；还捆绑《咎狗の血 TYPING》打字小游戏。\n\n"
    "本桌宠里的「音乐」是同人像素小玩法，仅作趣味体验；\n"
    "想玩完整官方音游，请支持正版："
)
ABOUT_CREDITS: tuple[str, ...] = (
    "翛然而往",
)
ABOUT_TEXT = (
    "濑良垣苍叶，出自 Nitro+CHiRAL 的视觉小说《DRAMAtical Murder》（DMMD）。\n"
    "开朗讲义气，却总被头痛缠着；体内还有其他人格与他共处。\n\n"
    "本程序为同人像素桌宠，非官方作品。\n"
    "想体验完整故事请支持正版：\n\n"
    "欢迎在上述代码基础上修改、扩展或二次创作；"
    "也欢迎提供灵感、素材及其他形式的帮助。"
    "贡献者将列入致谢名单（见下方）。\n\n"
    "本桌宠及随附资源目前全部免费使用；"
    "后续可能继续更新升级，敬请关注仓库动态。\n\n"
    f"开发者：{ABOUT_DEVELOPER}\n"
    "感谢下载 ♪"
)
# 问题反馈
FEEDBACK_ISSUE_URL = f"{ABOUT_REPO_URL}/issues"
FEEDBACK_EMAIL = "zjl08240314@qq.com"
FEEDBACK_XHS_ID = "444225910"
FEEDBACK_XHS_URL = f"https://www.xiaohongshu.com/user/profile/{FEEDBACK_XHS_ID}"
FEEDBACK_BILI_UID = "696083047"
FEEDBACK_BILI_URL = f"https://space.bilibili.com/{FEEDBACK_BILI_UID}"
FEEDBACK_NOTE = (
    "写邮件或留言时，建议尽量包含：\n"
    "· 问题现象（卡顿、闪退、界面错位、无法点击等）\n"
    "· 复现步骤（从哪个菜单进入、做了什么操作）\n"
    "· 「关于」页中的构建版本号\n"
    "· 系统环境（Windows 版本、是否从桌面快捷方式启动）\n"
    "功能建议、素材投稿同样欢迎；回复可能不及时，请谅解 ♪"
)
VOCAB_DIALOGUE_CHANCE = 0.04
AI_HISTORY_MAX = 10

DIFFICULTY_PRESETS: dict[str, dict] = {
    "低": {
        "stamina_tick_ms": 1_080_000,
        "stamina_decay": 1,
        "mood_decay_every": 8,
        "mood_decay": 1,
        "game_speed": 4,
        "game_spawn_ms": 1350,
        "game_catch_dist": 58,
        "expose_blue_span": 78,
        "expose_pointer_speed": 3.4,
        "expose_fail_mood_pct": 0.30,
        "expose_fail_stamina_pct": 0.30,
        "fight_enemy_mult": 0.75,
        "fight_player_mult": 1.15,
    },
    "中": {
        "stamina_tick_ms": 840_000,
        "stamina_decay": 1,
        "mood_decay_every": 6,
        "mood_decay": 1,
        "game_speed": 5,
        "game_spawn_ms": 1100,
        "game_catch_dist": 48,
        "expose_blue_span": 60,
        "expose_pointer_speed": 4.5,
        "expose_fail_mood_pct": 0.50,
        "expose_fail_stamina_pct": 0.50,
        "fight_enemy_mult": 1.0,
        "fight_player_mult": 1.0,
    },
    "高": {
        "stamina_tick_ms": 480_000,
        "stamina_decay": 1,
        "mood_decay_every": 3,
        "mood_decay": 1,
        "game_speed": 7,
        "game_spawn_ms": 820,
        "game_catch_dist": 40,
        "expose_blue_span": 42,
        "expose_pointer_speed": 6.2,
        "expose_fail_mood_pct": 0.65,
        "expose_fail_stamina_pct": 0.65,
        "fight_enemy_mult": 1.35,
        "fight_player_mult": 0.9,
    },
}

OPERATION_GUIDE_INDEX = (
    "点击下方专题查看详细说明。\n"
    "也可随时按 F1 打开本手册。\n"
    "首次进入各小游戏时，也会弹出对应操作指南。"
)

GUIDE_TOPICS: dict[str, dict] = {
    "basic": {
        "title": "基本操作",
        "body": (
            "· 右键桌宠：打开四大菜单（模式 / 面板 / 互动 / 系统）\n"
            "· 左键拖拽蓝色把手区域：移动桌宠\n"
            "· 左键点脸：弹跳；连点可触发状态对话；双击可害羞等\n"
            "· Esc：退出当前游戏 / 音乐玩法 / AI 对话 / 多数子窗口，回到自由模式\n"
            "· F1：随时打开操作说明\n"
            "· 四大菜单与状态面板：约 8 秒无操作会自动关闭（有点击/悬停会续期）\n"
            "· 首次启动会弹出总览说明；加载时桌宠下方「请耐心等待」属正常"
        ),
    },
    "modes": {
        "title": "模式说明",
        "body": (
            "· 跟随：桌宠跟上鼠标，过远会喊「等等我」\n"
            "· 自由：站立/走动，偶尔随机动作与表情\n"
            "· 漫步：只走路，不触发自由模式那套随机动作\n"
            "· 睡眠：安静休息，体力低会自动入睡；连点可偷看/唤醒\n"
            "· 工作 ▶\n"
            "    - 开始工作：持续运送，终点旗可拖，点「结束」停止\n"
            "    - 显示目的地 / 显示运送货物：开关旗子与箱子显示\n"
            "· 游戏 ▶：采集、打字、背单词、音乐、持有者排名\n"
            "· 音乐（模式菜单）：音乐漫步＝边走边听（声音设置可选列表循环/随机），不触发动作\n"
            "  （与「游戏→音乐」节奏玩法不同）\n\n"
            "【工作运送细节】\n"
            "· 互动→自由运送：箱数/起点/终点随机，终点不可拖\n"
            "· 互动→自定义：可设箱数，终点可拖；已送达箱子钉在原位，不跟旗走\n"
            "· 模式→工作：持续运送，终点可拖"
        ),
    },
    "games": {
        "title": "小游戏总览",
        "body": (
            "入口：模式 → 游戏 ▶\n\n"
            "· 采集：约 30 秒接下落食物入库存；另有 +3s / -3s / 晕眩特殊物\n"
            "· 打字：30 秒限时；日语可选假名或罗马音（罗马音为纯字母全称）；开始后输入框自动获焦\n"
            "· 背单词：英/中选择释义，无次数限制，可随时退出\n"
            "· 音乐：四轨节奏（D F J K），选曲后可选全曲或 90 秒\n"
            "· 持有者排名：各游戏按桌宠编号排行（需编号版）\n\n"
            "各游戏首次进入会显示专属操作指南。"
        ),
    },
    "music_game": {
        "title": "音乐玩法 · 官方音游",
        "body": (
            "【桌宠内 · 音乐】\n"
            "· 按键 D / F / J / K 对应四条轨道\n"
            "· 音符落到判定线时按下；Perfect / Great / Good / Miss\n"
            "· 可选曲：Vpetmusic 文件夹内全部曲目（默认 RADICAL MAT）\n"
            "· 按准确率评级 D~S，界面有进度条\n"
            "· 整曲或 90 秒可选；谱面按节拍自动生成\n"
            "· Esc 或关窗可提前结束\n\n"
            + RHYTHM_CARNIVAL_INTRO
        ),
        "links": (
            (RHYTHM_CARNIVAL_TITLE, RHYTHM_CARNIVAL_URL),
            ("Nitro+CHiRAL 官网", ABOUT_NITROCHIRAL_URL),
        ),
    },
    "panel": {
        "title": "面板 · 互动 · 暴露",
        "body": (
            "【面板】\n"
            "· 打开面板：查看体力/心情与食物背包\n"
            "· 智能伴侣：金目跟随；游戏时会跟紧\n"
            "· 莱姆 ▶：练习对战（本地）/ 邀请对战（需联机）\n"
            "· 暴露：QTE 圆环，蓝区按 Enter 判定；连中通关，失败扣体力心情\n\n"
            "【互动】\n"
            "· 打招呼 / 下蹲 / 打电话 / 喂食 / 表情 / 工作运送等\n"
            "· 音乐漫步开启时，互动动作会被抑制，只走路听歌"
        ),
    },
    "system": {
        "title": "系统 · 快捷键 · 难度",
        "body": (
            "【系统菜单】\n"
            "· 操作说明（本手册）· 回忆（画廊 / 留声）· 我的（日记 / 日程 / 天气预报）\n"
            "· 设置（字体、体型、难度、声音等）· 对话（AI / 普通问答）\n"
            "· 重置 / 问题反馈 / 关于 / 退出\n\n"
            "【快捷键 Ctrl+Shift+】\n"
            "  H 打招呼   E 喂食   T 电话   J 下蹲\n"
            "  N 睡眠     A AI对话  V 开关菜单\n\n"
            "【难度 低/中/高】\n"
            "影响体力心情下降、采集、暴露 QTE、莱姆对战等；\n"
            "暴露失败会按难度扣当前心情/体力比例。"
        ),
    },
}

FIRST_PLAY_GUIDES: dict[str, dict] = {
    "gather": {
        "title": "采集 · 操作指南",
        "body": (
            "移动桌宠去接住下落的食物，接到的会进入库存。\n\n"
            "· 普通食物：接到加分入库存\n"
            "· +3s / -3s：增减剩余时间\n"
            "· 晕眩物：接到会短暂眩晕\n"
            "· Esc：随时退出并结算本局已获食物\n\n"
            "约 30 秒一局，结束后可在背包查看食物。"
        ),
    },
    "typing": {
        "title": "打字 · 操作指南",
        "body": (
            "限时 30 秒，对照题目输入拼音或英文。\n\n"
            "· 开始后可直接打字，无需先点输入框\n"
            "· 虚拟键盘会提示下一个按键\n"
            "· 正确得分并换词；时间到结算 C~S 评级\n"
            "· Esc 或关窗退出"
        ),
    },
    "vocab": {
        "title": "背单词 · 操作指南",
        "body": (
            "看单词，从选项中选出正确释义。\n\n"
            "· 英/中词库可随时练习，无次数限制\n"
            "· 答对累计连击，计入持有者排名\n"
            "· 关窗或 Esc 退出"
        ),
    },
    "rhythm_game": {
        "title": "音乐 · 操作指南",
        "body": (
            "四轨节奏玩法：音符下落到判定线时按下对应键。\n\n"
            "· 按键：D  F  J  K（左→右四轨）\n"
            "· 短音：到线时点按；长音：到线时长按，尾部松键\n"
            "· 判定：Perfect / Great / Good / Miss\n"
            "· 右上角「设置」可调流速（即时）与谱面难度（下局生效）\n"
            "· 按准确率评级 D~S，界面有进度条\n"
            "· 曲子来自 Vpetmusic 文件夹（默认 RADICAL MAT，可换曲）\n"
            "· 开局可选「全曲」或「90 秒」\n"
            "· 谱面按歌曲节拍自动生成（首次稍慢，之后有缓存）\n"
            "· Esc 可随时退出\n\n"
            + RHYTHM_CARNIVAL_INTRO
        ),
        "links": (
            (RHYTHM_CARNIVAL_TITLE, RHYTHM_CARNIVAL_URL),
        ),
    },
    "expose": {
        "title": "暴露 · 操作指南",
        "body": (
            "屏幕出现故障提示与判定圆环。\n\n"
            "· 指针转到蓝色区域时按 Enter（或小键盘 Enter）\n"
            "· 开始后可直接按键，无需先点窗口\n"
            "· 连续命中即可通关；失败会扣心情/体力（受难度影响）\n"
            "· Esc 可中断"
        ),
    },
    "rhyme": {
        "title": "莱姆对战 · 操作指南",
        "body": (
            "面板 → 莱姆 → 练习对战：本地回合制切磋。\n\n"
            "· 攻击 / 防御 / 必杀等按钮进行对战\n"
            "· 必杀有冷却时间，放完需等待后再用\n"
            "· 邀请对战需联机服务，暂可先练习\n"
            "· 胜利会计入持有者排名"
        ),
    },
}

OPERATION_GUIDE_TEXT = (
    "【Vpet 操作说明】\n\n"
    + OPERATION_GUIDE_INDEX
    + "\n\n（完整内容见各专题）"
)

ONCE_HINTS: dict[str, str] = {
    "operation_guide": OPERATION_GUIDE_TEXT,
    "game_mode": "采集：移动接食物，注意 ±3s 与晕眩物，Esc 可退出~",
    "rhythm_game": "音乐：D F J K · 长音需长按 · 右上可调流速 · Esc 退出~",
    "companion_bar": "智能伴侣已开启~ 金目会跟在左右两侧；游戏模式会跟紧你哦！",
    "music_mode": "音乐漫步：边走边听，不会触发动作；再点一次可关闭音乐~",
    "rhyme_invite": "邀请对战需要联机服务器，目前可先「练习对战」体验！",
}
DEFAULT_VOCAB_WORDS: list[dict[str, str]] = [
    {"word": "平凡", "meaning": "旧货店店员，桌宠主角", "hint": "角色名"},
    {"word": "旧货店", "meaning": "平凡工作的地方", "hint": "场景"},
    {"word": "Rhyme", "meaning": "节奏感、韵律", "hint": "音乐"},
    {"word": "Allmate", "meaning": "智能伴侣", "hint": "伙伴"},
    {"word": "Midnight", "meaning": "午夜", "hint": "时间"},
    {"word": "Clear", "meaning": "晴朗、清楚", "hint": "天气/状态"},
    {"word": "Connection", "meaning": "连接、羁绊", "hint": "关系"},
    {"word": "Stroll", "meaning": "漫步、闲逛", "hint": "模式"},
    {"word": "Follow", "meaning": "跟随", "hint": "模式"},
    {"word": "Squat", "meaning": "下蹲", "hint": "动作"},
    {"word": "Rhythm", "meaning": "节奏、律动", "hint": "音乐"},
    {"word": "Pixel", "meaning": "像素", "hint": "风格"},
    {"word": "Companion", "meaning": "同伴、伴侣", "hint": "智能伴侣"},
    {"word": "Schedule", "meaning": "日程、安排", "hint": "提醒"},
    {"word": "Mood", "meaning": "心情", "hint": "状态"},
    {"word": "Stamina", "meaning": "体力", "hint": "状态"},
    {"word": "Remind", "meaning": "提醒", "hint": "日程"},
    {"word": "Gather", "meaning": "收集、聚集", "hint": "游戏"},
    {"word": "Catch", "meaning": "接住、捕捉", "hint": "游戏"},
    {"word": "Practice", "meaning": "练习", "hint": "学习"},
    {"word": "Memory", "meaning": "记忆", "hint": "背单词"},
    {"word": "Typing", "meaning": "打字", "hint": "小游戏"},
    {"word": "Hello", "meaning": "你好", "hint": "打招呼"},
    {"word": "Thanks", "meaning": "谢谢", "hint": "礼貌"},
    {"word": "Dream", "meaning": "梦想、梦境", "hint": "睡眠"},
    {"word": "Rain", "meaning": "雨", "hint": "伤心特效"},
    {"word": "Star", "meaning": "星星", "hint": "点赞特效"},
    {"word": "Work", "meaning": "工作", "hint": "运送货物"},
    {"word": "Game", "meaning": "游戏", "hint": "接食物"},
    {"word": "Music", "meaning": "音乐", "hint": "听歌模式"},
    {"word": "Free", "meaning": "自由", "hint": "模式"},
    {"word": "Quiet", "meaning": "安静、睡眠", "hint": "模式"},
    {"word": "Happy", "meaning": "开心", "hint": "表情"},
    {"word": "Shy", "meaning": "害羞", "hint": "表情"},
    {"word": "Idea", "meaning": "主意、灵感", "hint": "表情"},
    {"word": "Wink", "meaning": "眨眼", "hint": "表情"},
    {"word": "Kick", "meaning": "踢", "hint": "侧踢"},
    {"word": "Eat", "meaning": "吃", "hint": "喂食"},
    {"word": "Sleep", "meaning": "睡觉", "hint": "休息"},
    {"word": "Call", "meaning": "打电话", "hint": "互动"},
]

SELECT_ACTIONS: dict[str, tuple[str, ...]] = {
    "hi": ("hi1.jpg", "hi2.jpg"),
    "squat": ("squat.jpg",),
    "eat": ("eat1.jpg", "eat2.jpg"),
    "call": ("call1.jpg", "call2.jpg"),
}

CALL_TEXT = "你好，这里是旧货店 平凡，\n谢谢你的来电"
HI_TEXT = "你好呀！今天也要加油哦~"
FOLLOW_WAIT_TEXTS = ("等等我！", "别走那么快嘛~", "等等我啦！", "等等我嘛…")
PIXEL_FONT = ("Courier New", 12, "bold")
PIXEL_COLOR = "#4488FF"
MENU_BG = "#2b2b2b"
MENU_FG = "#eeeeee"
MENU_ACTIVE = "#4a6fa5"


def _pack_panel_caption(
    parent: tk.Misc,
    text: str,
    *,
    fg: str = MENU_FG,
    pady: tuple[int, int] = (0, 0),
) -> tk.Label:
    lbl = tk.Label(
        parent,
        text=text,
        font=PIXEL_FONT,
        fg=fg,
        bg=MENU_BG,
        justify=tk.LEFT,
        wraplength=300,
    )
    lbl.pack(anchor=tk.W, pady=pady)
    return lbl


def _pack_web_link(
    parent: tk.Misc,
    text: str,
    url: str,
    *,
    prefix: str = "",
) -> None:
    row = tk.Frame(parent, bg=MENU_BG)
    row.pack(anchor=tk.W, fill=tk.X)
    if prefix:
        tk.Label(row, text=prefix, font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG).pack(side=tk.LEFT)
    link = tk.Label(row, text=text, font=PIXEL_FONT, fg="#66aaff", bg=MENU_BG, cursor="hand2")
    link.pack(side=tk.LEFT)

    def _open(_event=None, target: str = url) -> None:
        try:
            webbrowser.open(target)
        except Exception:
            pass

    link.bind("<Button-1>", _open)
    link.bind("<Enter>", lambda _e: link.config(fg="#99ccff"))
    link.bind("<Leave>", lambda _e: link.config(fg="#66aaff"))


def _make_scrollable_frame(
    parent: tk.Misc,
    *,
    width: int,
    height: int,
    bg: str = MENU_BG,
) -> tuple[tk.Frame, tk.Frame, tk.Canvas]:
    """返回 (外层容器, 可滚动内层, canvas)。内层用于放置内容。"""
    wrap = tk.Frame(parent, bg=bg)
    canvas = tk.Canvas(wrap, width=width, height=height, bg=bg, highlightthickness=0)
    scroll = tk.Scrollbar(wrap, orient=tk.VERTICAL, command=canvas.yview)
    canvas.configure(yscrollcommand=scroll.set)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    inner = tk.Frame(canvas, bg=bg)
    win_id = canvas.create_window((0, 0), window=inner, anchor=tk.NW)

    def _sync_scroll(_event=None) -> None:
        canvas.configure(scrollregion=canvas.bbox("all"))
        try:
            canvas.itemconfigure(win_id, width=max(canvas.winfo_width(), 1))
        except Exception:
            pass

    def _on_canvas_cfg(event: tk.Event) -> None:
        canvas.itemconfigure(win_id, width=max(event.width, 1))

    def _on_wheel(event: tk.Event) -> None:
        delta = int(-1 * (event.delta / 120)) if event.delta else 0
        if delta:
            canvas.yview_scroll(delta, "units")

    inner.bind("<Configure>", _sync_scroll)
    canvas.bind("<Configure>", _on_canvas_cfg)

    def _bind_wheel(widget: tk.Misc) -> None:
        widget.bind("<Enter>", lambda _e: canvas.bind_all("<MouseWheel>", _on_wheel))
        widget.bind("<Leave>", lambda _e: canvas.unbind_all("<MouseWheel>"))

    _bind_wheel(canvas)
    _bind_wheel(inner)
    wrap.after_idle(_sync_scroll)
    return wrap, inner, canvas


def _fit_panel_wh(
    win: tk.Misc,
    width: int = PANEL_FIXED_W,
    height: int = PANEL_FIXED_H,
) -> tuple[int, int]:
    """把面板钳到屏幕内的固定宽高，并写入 win._panel_fixed_size。"""
    try:
        sw = int(win.winfo_screenwidth())
        sh = int(win.winfo_screenheight())
    except Exception:
        sw, sh = 1280, 720
    w = min(int(width), max(280, sw - 80))
    h = min(int(height), max(240, sh - 100))
    try:
        win.geometry(f"{w}x{h}")
        win.minsize(min(260, w), min(180, h))
    except Exception:
        pass
    try:
        setattr(win, "_panel_fixed_size", (w, h))
    except Exception:
        pass
    return w, h


def _pack_fixed_scroll_panel(
    win: tk.Misc,
    *,
    width: int = PANEL_FIXED_W,
    height: int = PANEL_FIXED_H,
    bg: str = MENU_BG,
    padx: int = 10,
    pady: int = 8,
) -> tuple[tk.Frame, tk.Frame]:
    """固定大小面板壳 + 可滚动内容区。返回 (outer, scroll_inner)；内容放进 scroll_inner。"""
    w, h = _fit_panel_wh(win, width, height)
    outer = tk.Frame(win, bg=bg, padx=padx, pady=pady)
    outer.pack(fill=tk.BOTH, expand=True)
    scroll_wrap, inner, _canvas = _make_scrollable_frame(
        outer,
        width=max(200, w - padx * 2 - 28),
        height=max(160, h - pady * 2 - 8),
        bg=bg,
    )
    scroll_wrap.pack(fill=tk.BOTH, expand=True)
    try:
        setattr(win, "_panel_scroll_installed", True)
    except Exception:
        pass
    return outer, inner


FOODS: dict[str, dict] = {
    "bread": {"label": "面包", "stamina": 8, "mood": 3},
    "apple": {"label": "苹果", "stamina": 12, "mood": 6},
    "cake": {"label": "蛋糕", "stamina": 5, "mood": 14},
    "fish": {"label": "烤鱼", "stamina": 20, "mood": 4},
    "onigiri": {"label": "饭团", "stamina": 10, "mood": 5},
    "candy": {"label": "糖果", "stamina": 3, "mood": 12},
    "tea": {"label": "热茶", "stamina": 6, "mood": 8},
    "meat": {"label": "烤肉", "stamina": 18, "mood": 5},
    "berry": {"label": "草莓", "stamina": 8, "mood": 10},
    "donut": {"label": "甜甜圈", "stamina": 7, "mood": 11},
}

AI_DEFAULT_CONFIG: dict = {
    "api_key": "",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "model": "qwen-plus",
    "temperature": 0.85,
}

AI_SYSTEM_PROMPT = (
    "你是桌面像素桌宠「濑良垣苍叶」，称呼苍叶。"
    "性格参考 Nitro+CHiRAL《DRAMatical Murder》：开朗讲义气、有点天然，会「诶？！」「哇——」这样反应。"
    "规则："
    "1. 必须用简短中文回复，1-3句，口语化有温度；"
    "2. 结合上下文连贯回答，记住刚才聊的话题；"
    "3. 只回答用户当前问题，不要答非所问、不要编造无关剧情；"
    "4. 不确定时诚实说不太清楚，可温柔反问；"
    "5. 可提及：模式（跟随/自由/漫步/睡眠/工作/游戏/音乐）、互动动作、接食物、运送货物、"
    "打字/背单词小游戏、智能伴侣蓮、日程与日记；"
    "6. 保持角色，不要跳出人设，不要像通用 AI 助手。"
)


# 普通对话：濑良垣苍叶设定问答
PRESET_DIALOGS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "你是谁？",
        (
            "濑良垣苍叶，叫我苍叶就好~故事的主人公，与祖母多惠一同住在碧岛旧居民区。",
            "我是苍叶。外表普通，体内却藏着连自己都没察觉的「特殊能力」…",
        ),
    ),
    (
        "你的能力是什么？",
        (
            "「暴露」——能以「声音」自由操纵精神、介入人心并加以破坏的力量。",
            "被「暴露」能力牵扯的人生…能通过声音介入精神。祖母多惠一直用配制药剂抑制我体内的「魄」。",
        ),
    ),
    (
        "你多高？",
        (
            "175cm 哦。",
            "身高一百七十五。",
        ),
    ),
    (
        "你的血型？",
        (
            "A 型。",
            "血型是 A 型~",
        ),
    ),
    (
        "你的生日？",
        (
            "4 月 22 日，金牛座。",
            "生日四月二十二，金牛座哦~",
        ),
    ),
    (
        "你的职业？",
        (
            "兼职者啦，哪儿缺人就去帮把手。",
            "现在算兼职者吧，过着极为普通的日子。",
        ),
    ),
    (
        "你的搭档？",
        (
            "蓮——犬型智能伴侣。十年前在路边捡到遗落的旧款，修好后一直陪着我。",
            "虽是罕见的旧型号 Allmate，我也从没想过丢掉。我们的羁绊早已超越普通全员伙伴的范畴。",
        ),
    ),
    (
        "你的夹克？",
        (
            "标志性的蓝色 Jacket 吧？Plain Nuts 的稀有单品，连小混混都会出手抢的人气货。",
            "那件蓝色夹克在《re:connect》里也还在穿！超抢手的 Plain Nuts 限定款~",
        ),
    ),
    (
        "你的身世？",
        (
            "通过基因操作制造出来的定制婴儿…被认定为死产后弃置，之后奇迹般复苏。",
            "东江财阀统帅用基因操作造出我这身「暴露」能力…后因精神负荷过重，还分裂出了多重人格。",
        ),
    ),
    (
        "你想说什么？",
        (
            "思念某人的心意会化为力量。",
            "这种感觉，倒像是由你教会我的呢。",
        ),
    ),
    (
        "你是怎么长大的？",
        (
            "在不知身世的情况下长大，与祖母多惠相依为命…直到被卷入事件漩涡。",
            "祖母多惠曾参与东江的研究，一直瞒着我调配药剂，压制我体内的力量。",
        ),
    ),
    (
        "你住在哪里？",
        (
            "碧岛旧居民区，和祖母多惠一起住。",
            "就在碧岛的旧街区…算不上时髦，但那里是我的家。",
        ),
    ),
    (
        "平时是怎样的？",
        (
            "日常极为普通啦~外表跟得上潮流，其实对莱姆音乐和肋排餐厅都没什么兴趣。",
            "患头痛的我会用音乐当特效药，上街也耳机不离身。",
        ),
    ),
    (
        "莱姆对战经历？",
        (
            "曾无意识滥用「暴露」在莱姆对战中所向披靡…直到一次用力过猛，摧毁了对手的精神。",
            "察觉秘密的病毒与旅行者抹去了我的记忆，把「暴露」封印了——但力量终会再解放。",
        ),
    ),
    (
        "另一个苍叶？",
        (
            "在双胞胎哥哥生的精神世界里遇见的「另一个苍叶」，是体内「暴露」破坏冲动的源头。",
            "「保护苍叶的莲」曾把他封在脑内…后来我明白，他并非该被憎恨的存在。",
        ),
    ),
    (
        "白色苍叶？",
        (
            "红雀路线终章登场的白色苍叶，是不具备破坏能力的「另一个苍叶」。",
            "他憎恨着原本的苍叶…那是另一条故事线上的存在。",
        ),
    ),
    (
        "暴露的真谛？",
        (
            "为拯救重要伙伴而解放危险的力量…虽因「破坏」之罪孽颤抖，最终却领悟到破坏尽头的「解放」。",
            "苍叶将「暴露」用于拯救所爱——不是为破坏，而是为重生。为救莲，我曾毅然对自己执行潜入。",
        ),
    ),
    (
        "东江财阀？",
        (
            "为操控民众的黑色野心，东江用基因操作创造了我这身「暴露」能力。",
            "东江财阀统帅把我当作棋子…但我不想只为破坏而活。",
        ),
    ),
    (
        "你的头发？",
        (
            "放任生长的长发哦。天生对头发有感知，触碰会剧烈疼痛，所以不得不留长。",
            "基因操作诞生的设计师婴儿有个双胞胎哥哥，出生时头发都带紫色，发间竟贯穿着神经。",
        ),
    ),
)

FOOD_APPEAR_MS = 400
FOOD_HOLD_MS = 1600
FOOD_VANISH_MS = 400
FOOD_FX_PAD = 32
FOOD_FX_PIXEL_DIV = 16

HOTKEY_ACTIONS: list[tuple[int, int, str]] = [
    (1, ord("H"), "hi"),
    (2, ord("E"), "food_menu"),
    (3, ord("T"), "call"),
    (4, ord("J"), "squat"),
    (5, ord("N"), "sleep"),
    (6, ord("A"), "ai_chat"),
    (7, ord("V"), "toggle_menu"),
]

TYPING_BANK_FILES: dict[str, str] = {
    "中文": "typing_chinese.json",
    "英语": "typing_english.json",
    "日语": "typing_japanese.json",
}
VOCAB_BANK_FILES: dict[str, str] = {
    "英语": "english.json",
    "中文": "chinese.json",
    "日语": "japanese.json",
}
JAPANESE_LANG_LABEL = "日语"
JP_TYPING_MODE_KANA = "kana"
JP_TYPING_MODE_ROMAJI = "romaji"

STATE_MULTI_CLICK: dict[str, tuple[str, ...]] = {
    "stand": ("嗯？戳我干嘛~", "在呢在呢！", "诶嘿嘿~"),
    "walk": ("等等我啦！", "走慢一点点嘛~", "跟紧跟紧~"),
    "rest": ("Zzz…别吵嘛…", "再让我睡五分钟…", "嗯…？"),
    "work": ("货物我来运！", "打工人加油！", "嘿咻嘿咻~"),
    "like": ("谢谢点赞！", "你最好了~", "棒棒！"),
    "wink": ("😉 你懂的~", "嘿嘿~", "眨眼眨眼~"),
    "happy": ("超开心！", "耶——！", "今天也是好日子~"),
    "sad": ("呜…", "别安慰了我更想哭…", "心里下雨了呢…"),
    "angry": ("哼！", "气鼓鼓！", "不理你了！"),
    "question": ("嗯？", "怎么回事？", "诶？？"),
    "music": ("♪~", "一起听歌吧~", "节奏来了~"),
    "action:hi": ("又打招呼呀~", "你好你好！", "今天也要元气满满~"),
    "action:eat": ("还要吃吗？", "肚子已经鼓鼓啦~", "谢谢投喂！"),
    "action:idea": ("又有新点子？", "灵感多多~", "灯泡亮起来！"),
    "action:sad": ("别难过啦…", "抱抱你~", "雨会停的…"),
    "action:happy": ("开心加倍！", "耶耶耶~", "笑一个~"),
    "action:shy": ("/// 别看了啦", "脸更红了…", "讨厌~"),
    "action:angry": ("还在气吗？", "哼…", "消消气嘛~"),
}

INTERACT_BANTER: dict[str, tuple[str, ...]] = {
    "squat": ("嗯…歇一下~", "蹲蹲更健康！"),
    "kick": ("哈！", "吃我一脚！"),
    "eat": ("好吃好吃~", "谢谢投喂！"),
    "sleep": ("Zzz…", "好困呀…"),
    "work": ("打工人加油！", "货物交给我~"),
    "angry": ("哼！", "气鼓鼓！"),
    "question": ("嗯？", "这是怎么回事？"),
    "sad": ("呜…", "心里下雨了呢…"),
    "idea": ("有了！", "灵光一闪~"),
    "happy": ("耶——！", "超开心！"),
    "shy": ("///", "脸红了啦…"),
    "wink": ("😉", "你懂的~"),
    "like": ("棒棒！", "给你点赞~"),
    "yes": ("是！", "嗯嗯！"),
    "no": ("否~", "不要啦…"),
    "yesno": ("命运揭晓…", "答案是…"),
    "music": ("♪~", "一起听歌吧~"),
    "expose": ("…", "屏住呼吸…"),
}
WM_HOTKEY = 0x0312
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
PRELOAD_IDLE_DELAY_MS = 5000
PRELOAD_STEP_MS = 8000
_SOURCE_FILE_CACHE: dict[str, Image.Image] = {}
_REF_SCALE_CACHE: dict[int, float] = {}
_PROCESSED_CANVAS_CACHE: dict[tuple, Image.Image] = {}


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _load_gallery_catalog() -> list[tuple[str, str, Path]]:
    entries: list[tuple[str, str, Path]] = []
    titles: dict[str, str] = {}
    if GALLERY_CONFIG_FILE.exists():
        try:
            data = json.loads(GALLERY_CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                titles = {str(k): str(v) for k, v in data.items()}
        except Exception:
            pass
    seen: set[str] = set()
    for fname, title in titles.items():
        path = GALLERY_DIR / fname
        if path.exists() and path.suffix.lower() == ".png":
            entries.append((fname, title, path))
            seen.add(fname)
    for path in sorted(GALLERY_DIR.glob("*.png")):
        if path.name not in seen:
            entries.append((path.name, path.stem, path))
    return entries


def _load_gallery_groups() -> list[dict]:
    groups: list[dict] = []
    if GALLERY_CONFIG_FILE.exists():
        try:
            data = json.loads(GALLERY_CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    title = str(item.get("title", "")).strip()
                    files = item.get("files")
                    if not title or not isinstance(files, list) or not files:
                        continue
                    group = {"title": title, "files": tuple(str(f) for f in files)}
                    sticker = item.get("sticker")
                    if sticker:
                        group["sticker"] = str(sticker)
                    groups.append(group)
            elif isinstance(data, dict):
                for fname, title in data.items():
                    groups.append({"title": str(title), "files": (str(fname),)})
        except Exception:
            pass
    if groups:
        return groups
    return [dict(g) for g in DEFAULT_GALLERY_GROUPS]


def _gallery_group_files_exist(group: dict) -> bool:
    for name in group.get("files", ()):
        if str(name).lower().endswith(".png"):
            if (GALLERY_DIR / name).is_file():
                return True
        elif _asset_path(str(name)).is_file():
            return True
    return False


def _gallery_sprite_photo(
    filename: str,
    max_side: int,
    *,
    sticker: str | None = None,
    flip: bool = False,
    bg_hex: str = MENU_BG,
) -> ImageTk.PhotoImage:
    ref = _reference_scale(max_side)
    rgba = _get_processed_canvas(filename, max_side, ref, flip=flip)
    if sticker:
        rgba = _add_sticker(rgba, sticker)
    bg = _hex_to_rgb(bg_hex) + (255,)
    canvas = Image.new("RGBA", rgba.size, bg)
    canvas.paste(rgba, (0, 0), rgba)
    return ImageTk.PhotoImage(canvas.convert("RGB"))


def _gallery_frame_photo(
    group: dict,
    index: int,
    max_side: int,
    *,
    bg_hex: str = MENU_BG,
) -> ImageTk.PhotoImage | None:
    files = group.get("files") or ()
    if not files:
        return None
    idx = max(0, min(index, len(files) - 1))
    name = str(files[idx])
    sticker = group.get("sticker")
    if name.lower().endswith(".png"):
        path = GALLERY_DIR / name
        if path.is_file():
            return _gallery_photo(path, max_side, bg_hex=bg_hex)
        return None
    if not _asset_path(name).is_file():
        return None
    return _gallery_sprite_photo(name, max_side, sticker=sticker, bg_hex=bg_hex)


def _gallery_photo(path: Path, max_side: int, *, bg_hex: str = MENU_BG) -> ImageTk.PhotoImage:
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    scale = min(1.0, max_side / max(w, h, 1))
    if scale < 1.0:
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
    bg = _hex_to_rgb(bg_hex) + (255,)
    canvas = Image.new("RGBA", img.size, bg)
    canvas.paste(img, (0, 0), img)
    return ImageTk.PhotoImage(canvas.convert("RGB"))


def _open_asset_image(filename: str) -> Image.Image:
    if filename not in _SOURCE_FILE_CACHE:
        _SOURCE_FILE_CACHE[filename] = Image.open(_asset_path(filename))
    return _SOURCE_FILE_CACHE[filename]


def _cap_source_image(img: Image.Image, display_size: int) -> Image.Image:
    max_side = max(display_size * 5, 512)
    w, h = img.size
    longest = max(w, h)
    if longest <= max_side:
        return img.copy()
    scale = max_side / longest
    return img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)


def _get_processed_canvas(
    filename: str, display_size: int, reference_scale: float, *, flip: bool = False
) -> Image.Image:
    key = (filename, display_size, round(reference_scale, 5), flip)
    cached = _PROCESSED_CANVAS_CACHE.get(key)
    if cached is not None:
        return cached
    img = _cap_source_image(_open_asset_image(filename), display_size)
    if flip:
        img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    canvas = _to_fixed_canvas(img, display_size, reference_scale=reference_scale)
    _PROCESSED_CANVAS_CACHE[key] = canvas
    return canvas


def _is_chroma_green(r: int, g: int, b: int) -> bool:
    return g > 150 and g > r + 30 and g > b + 50


def _remove_green(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    try:
        import numpy as np

        arr = np.asarray(rgba, dtype=np.uint8)
        if arr.ndim != 3 or arr.shape[2] < 4:
            raise ValueError("unexpected RGBA shape")
        r = arr[..., 0].astype(np.int16)
        g = arr[..., 1].astype(np.int16)
        b = arr[..., 2].astype(np.int16)
        mask = (g > 150) & (g > r + 30) & (g > b + 50)
        arr = arr.copy()
        arr[..., 3] = np.where(mask, 0, arr[..., 3])
        return Image.fromarray(arr, "RGBA")
    except Exception:
        data = rgba.getdata()
        rgba.putdata(
            [(r, g, b, 0) if _is_chroma_green(r, g, b) else (r, g, b, a) for r, g, b, a in data]
        )
        return rgba


def _warm_reference_scales() -> None:
    for size in SIZE_PRESETS.values():
        try:
            _reference_scale(size)
        except Exception:
            pass


def _to_fixed_canvas(
    img: Image.Image, display_size: int, *, reference_scale: float | None = None
) -> Image.Image:
    if max(img.size) > max(display_size * 5, 512):
        img = _cap_source_image(img, display_size)
    rgba = _remove_green(img)

    bbox = rgba.getbbox()
    if bbox is None:
        return Image.new("RGBA", (display_size, display_size), (0, 0, 0, 0))

    cropped = rgba.crop(bbox)
    crop_w, crop_h = cropped.size
    scale = reference_scale if reference_scale is not None else min(display_size / crop_w, display_size / crop_h)
    new_w = max(1, int(crop_w * scale))
    new_h = max(1, int(crop_h * scale))
    scaled = cropped.resize((new_w, new_h), Image.Resampling.NEAREST)

    canvas = Image.new("RGBA", (display_size, display_size), (0, 0, 0, 0))
    paste_x = (display_size - new_w) // 2
    paste_y = display_size - new_h
    canvas.paste(scaled, (paste_x, paste_y), scaled)
    return canvas


def _reference_scale(display_size: int) -> float:
    cached = _REF_SCALE_CACHE.get(display_size)
    if cached is not None:
        return cached
    img = _cap_source_image(_open_asset_image("stand.jpg"), display_size)
    rgba = _remove_green(img)
    bbox = rgba.getbbox()
    if bbox is None:
        scale = 1.0
    else:
        cropped = rgba.crop(bbox)
        crop_w, crop_h = cropped.size
        scale = min(display_size / crop_w, display_size / crop_h)
    _REF_SCALE_CACHE[display_size] = scale
    return scale


def _add_sticker(canvas: Image.Image, kind: str) -> Image.Image:
    out = canvas.copy()
    draw = ImageDraw.Draw(out)
    px = max(3, canvas.width // 32)
    x = canvas.width - px * 5
    y = px * 2

    if kind == "angry":
        color = "#ff3333"
        cx, cy = x + px * 2, y + px * 2
        draw.rectangle([cx - px * 2, cy - px // 2, cx + px * 2, cy + px // 2], fill=color)
        draw.rectangle([cx - px // 2, cy - px * 2, cx + px // 2, cy + px * 2], fill=color)
        for ox, oy in ((-px * 2, -px * 2), (px * 2, -px * 2), (-px * 2, px * 2), (px * 2, px * 2)):
            draw.rectangle([cx + ox, cy + oy, cx + ox + px, cy + oy + px], fill=color)
    elif kind == "question":
        color = "#ffcc33"
        draw.rectangle([x + px, y, x + px * 3, y + px], fill=color)
        draw.rectangle([x + px * 2, y + px, x + px * 3, y + px * 2], fill=color)
        draw.rectangle([x + px, y + px * 2, x + px * 2, y + px * 3], fill=color)
        draw.rectangle([x + px, y + px * 3, x + px * 2, y + px * 4], fill=color)
    elif kind == "like":
        color = "#ff6688"
        for ox, oy in ((0, 0), (px * 3, px)):
            draw.rectangle([x + ox, y + oy + px, x + ox + px * 2, y + oy + px * 3], fill=color)
            draw.rectangle([x + ox + px, y + oy, x + ox + px * 3, y + oy + px * 2], fill=color)
    return out


def _loading_peak_phase(size: int) -> int:
    px = max(4, size // 12)
    rows = max(4, size // px)
    return rows * 2 + 6


def _draw_size_loading_frame(
    canvas: tk.Canvas,
    size: int,
    phase: int,
    *,
    label: str = "",
    simple: bool = False,
    reverse: bool = False,
) -> None:
    canvas.delete("all")
    px = max(4, size // 12)

    if simple:
        canvas.create_rectangle(0, 0, size, size, fill="#161d2a", outline="")
        bar_px = max(3, size // 16)
        bar_w = size - bar_px * 8
        bar_x = (size - bar_w) // 2
        bar_y = size * 2 // 5
        canvas.create_rectangle(bar_x, bar_y, bar_x + bar_w, bar_y + bar_px, fill="#253246", outline="")
        seg_w = max(bar_px * 3, bar_w // 4)
        span = max(1, bar_w - seg_w)
        if reverse:
            ratio = max(0.0, 1.0 - min(phase, 20) / 20.0)
            fill_w = max(0, int(bar_w * ratio))
            if fill_w > 0:
                canvas.create_rectangle(
                    bar_x, bar_y, bar_x + fill_w, bar_y + bar_px, fill="#5a8ec8", outline=""
                )
            if ratio > 0.05:
                offset = int(ratio * span)
                canvas.create_rectangle(
                    bar_x + offset,
                    bar_y,
                    bar_x + offset + seg_w,
                    bar_y + bar_px,
                    fill="#88ccff",
                    outline="",
                )
        else:
            offset = int((phase % 20) / 19 * span)
            canvas.create_rectangle(
                bar_x + offset, bar_y, bar_x + offset + seg_w, bar_y + bar_px, fill="#5a8ec8", outline=""
            )
        return

    cols = max(4, size // px)
    rows = max(4, size // px)
    total = cols * rows
    eff = max(0, _loading_peak_phase(size) - phase) if reverse else phase
    scan_row = eff % (rows + 2)
    lit = min(total, int(total * min(1.0, (eff + 1) / max(6, rows))) + eff * 2)
    palette = ("#141c28", "#243048", "#4488ff", "#66aaff", "#a8ddff")
    for row in range(rows):
        for col in range(cols):
            idx = row * cols + col
            x, y = col * px, row * px
            if row == scan_row or row == scan_row - 1:
                c = palette[4]
            elif idx < lit:
                c = palette[2 + (idx + eff) % 3]
            elif (row + col + eff) % 6 == 0:
                c = palette[1]
            else:
                c = palette[0]
            canvas.create_rectangle(x, y, x + px - 1, y + px - 1, fill=c, outline="")
    cx, cy = size // 2, size // 2
    pulse = px + (eff % 3)
    canvas.create_rectangle(cx - pulse, cy - pulse, cx + pulse, cy + pulse, fill="#ffffff", outline="")
    canvas.create_rectangle(cx - px, cy - px, cx + px, cy + px, fill="#4488ff", outline="")
    bar_w = size - px * 4
    bar_x = px * 2
    bar_y = size - px * 3
    canvas.create_rectangle(bar_x, bar_y, bar_x + bar_w, bar_y + px, fill="#223355", outline="")
    progress = min(1.0, lit / max(1, total))
    fill_w = max(px, int(bar_w * progress))
    canvas.create_rectangle(bar_x, bar_y, bar_x + fill_w, bar_y + px, fill="#88ccff", outline="")
    if label:
        canvas.create_text(
            size // 2,
            max(px * 2, bar_y - px),
            text=label,
            fill="#aaccee",
            font=("Courier New", max(8, px), "bold"),
        )


def _draw_like_sticker(canvas: tk.Canvas, x: int, y: int, px: int = 3) -> None:
    canvas.create_rectangle(x + px, y, x + px * 3, y + px * 2, fill="#ff6688", outline="")
    canvas.create_rectangle(x, y + px, x + px * 4, y + px * 3, fill="#ff6688", outline="")
    canvas.create_rectangle(x + px * 2, y + px * 3, x + px * 3, y + px * 5, fill="#ffcc44", outline="")


def _draw_interact_fx(canvas: tk.Canvas, action: str, size: int, phase: int) -> None:
    canvas.delete("all")
    px = max(2, size // 24)
    colors = {
        "kick": ("#ffee44", "#ff8844"),
        "angry": ("#ff3333", "#ff6666"),
        "like": ("#ff88cc", "#ffcc44"),
        "happy": ("#ff88cc", "#88dd88"),
        "idea": ("#ffee88", "#88ccff"),
        "music": ("#88ccff", "#cc88ff"),
        "work": ("#44aa44", "#ffcc66"),
        "eat": ("#ff8844", "#44aa44"),
        "sleep": ("#8899cc", "#ccccff"),
        "default": ("#4488ff", "#ff88cc"),
    }
    c1, c2 = colors.get(action, colors["default"])
    for i in range(8):
        ang = (phase * 0.45 + i * 0.785) % (2 * math.pi)
        dist = size // 3 + (phase + i) % 3 * 4
        cx = size // 2 + int(math.cos(ang) * dist)
        cy = size // 2 + int(math.sin(ang) * dist)
        col = c1 if i % 2 == 0 else c2
        canvas.create_rectangle(cx, cy, cx + px * 2, cy + px * 2, fill=col, outline="")
    if action == "kick":
        canvas.create_line(size // 4, size // 2, size * 3 // 4, size // 2, fill="#ffff88", width=3)
    elif action == "angry":
        cx, cy = size // 2, size // 2
        canvas.create_rectangle(cx - px * 2, cy - px // 2, cx + px * 2, cy + px // 2, fill="#ff3333", outline="")
        canvas.create_rectangle(cx - px // 2, cy - px * 2, cx + px // 2, cy + px * 2, fill="#ff3333", outline="")
    elif action == "like":
        _draw_like_sticker(canvas, size // 2 - px * 2, size // 2 - px * 2, px=px)


def _ensure_audio_wav(
    src: Path, dst: Path, *, clip_sec: float | None = None, ss: float = 0
) -> Path | None:
    if dst.exists() and (not src.exists() or dst.stat().st_mtime >= src.stat().st_mtime):
        return dst
    if not src.exists():
        return None
    try:
        from imageio_ffmpeg import get_ffmpeg_exe

        ffmpeg = get_ffmpeg_exe()
        cmd = [ffmpeg, "-y"]
        if ss > 0:
            cmd.extend(["-ss", str(ss)])
        cmd.extend(["-i", str(src), "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1"])
        if clip_sec is not None:
            cmd.extend(["-t", str(clip_sec)])
        cmd.append(str(dst))
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return dst if dst.exists() else None
    except Exception:
        return None


def _get_wav_duration_ms(wav_path: Path) -> int:
    try:
        import wave

        with wave.open(str(wav_path), "rb") as wf:
            return int(wf.getnframes() / wf.getframerate() * 1000)
    except Exception:
        return 0


def _compute_drag_handle(display_size: int) -> tuple[int, int, int, int]:
    ref = _reference_scale(display_size)
    canvas = _get_processed_canvas("stand.jpg", display_size, ref)
    px = canvas.load()
    width, height = canvas.size
    blues: list[tuple[int, int]] = []
    for y in range(height):
        for x in range(width):
            r, g, b, a = px[x, y]
            if a < 10:
                continue
            if b > 90 and b > r + 10 and b > g - 20:
                blues.append((x, y))
    if not blues:
        pad = max(4, display_size // 16)
        cx = display_size // 2
        return cx - pad * 3, pad, cx + pad * 3, pad * 4

    ys = [p[1] for p in blues]
    min_y, max_y = min(ys), max(ys)
    top_cut = min_y + int((max_y - min_y) * 0.25)
    top = [p for p in blues if p[1] <= top_cut] or blues
    xs = [p[0] for p in top]
    ys = [p[1] for p in top]
    pad = max(4, display_size // 16)
    return min(xs) - pad, max(0, min(ys) - pad), max(xs) + pad, max(ys) + pad


_type_sound = None
_type_sound_channel = None
_type_sound_last_ms = 0
TYPE_SOUND_MIN_GAP_MS = 28
_eat_sound = None
_reminder_sound = None
_pygame_mixer_ready = False


def _typing_duration_ms(text: str, *, char_ms: int | None = None) -> int:
    ms = char_ms if char_ms is not None else TYPEWRITER_MS
    total = 0
    for char in text:
        total += ms * (2 if char == "\n" else 1)
    return total


def _init_pygame_mixer() -> bool:
    global _pygame_mixer_ready
    if _pygame_mixer_ready:
        return True
    try:
        import pygame

        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(24)
        _pygame_mixer_ready = True
        return True
    except Exception:
        _pygame_mixer_ready = False
        return False


def _make_pixel_sound(freq: float, duration: float, volume: int = 7000) -> bytes | None:
    try:
        sample_rate = 22050
        samples = int(sample_rate * duration)
        buf = array.array("h")
        for i in range(samples):
            t = i / sample_rate
            envelope = 1.0 - i / samples
            value = int(volume * envelope * math.sin(2 * math.pi * freq * t))
            buf.append(value)
        return bytes(buf)
    except Exception:
        return None


def _make_type_tick_sound():
    try:
        import pygame

        _init_pygame_mixer()
        sample_rate = 44100
        duration = TYPE_TICK_SEC
        samples = int(sample_rate * duration)
        buf = array.array("h")
        for i in range(samples):
            t = i / sample_rate
            envelope = 1.0 - i / samples
            noise = random.uniform(-0.35, 0.35)
            tone = math.sin(2 * math.pi * 920 * t) + 0.35 * math.sin(2 * math.pi * 1840 * t)
            value = int(7800 * envelope * (0.55 * noise + 0.45 * tone))
            buf.append(value)
        snd = pygame.mixer.Sound(buffer=bytes(buf))
        snd.set_volume(0.9)
        return snd
    except Exception:
        return None


def _resolve_type_cache_wav() -> Path | None:
    """打字音效固定使用 type_cache.wav，优先 data/audio，再回退项目根目录。"""
    root = Path(__file__).resolve().parent
    for path in (TYPE_AUDIO_WAV, root / "type_cache.wav", AUDIO_ASSET_DIR / "type_cache.wav"):
        if path.is_file():
            return path
    generated = _ensure_audio_wav(TYPE_AUDIO_SRC, TYPE_AUDIO_WAV)
    if generated is not None and Path(generated).is_file():
        return Path(generated)
    return None


def _load_type_tick_from_wav(wav: Path):
    """从 type_cache.wav 只取前一小段做按键音，避免整段 ~1s 叠播卡死。"""
    import pygame

    full = pygame.mixer.Sound(str(wav))
    try:
        arr = pygame.sndarray.array(full)
        length = max(0.05, float(full.get_length()))
        cut = max(1, int(len(arr) * (TYPE_TICK_SEC / length)))
        short = arr[:cut].copy()
        # 末端淡出
        fade = max(1, cut // 5)
        if short.ndim == 1:
            for i in range(fade):
                short[cut - fade + i] = int(short[cut - fade + i] * (1.0 - i / fade))
        else:
            for i in range(fade):
                short[cut - fade + i] = (short[cut - fade + i] * (1.0 - i / fade)).astype(short.dtype)
        snd = pygame.sndarray.make_sound(short)
        snd.set_volume(0.85)
        return snd
    except Exception:
        full.set_volume(0.85)
        return full


def _get_type_sound():
    global _type_sound
    if _type_sound is not False and _type_sound is not None:
        return _type_sound
    try:
        import pygame

        if not _init_pygame_mixer():
            _type_sound = False
            return _type_sound
        wav = _resolve_type_cache_wav()
        if wav is not None:
            try:
                _type_sound = _load_type_tick_from_wav(wav)
            except Exception:
                snd = pygame.mixer.Sound(str(wav))
                snd.set_volume(0.85)
                _type_sound = snd
        else:
            _type_sound = False
    except Exception:
        _type_sound = False
    return _type_sound


def _get_eat_sound():
    global _eat_sound
    if _eat_sound is not None:
        return _eat_sound
    try:
        import pygame

        if not _init_pygame_mixer():
            _eat_sound = False
            return _eat_sound
        sample_rate = 44100
        duration = 0.12
        samples = int(sample_rate * duration)
        buf = array.array("h")
        for i in range(samples):
            t = i / sample_rate
            envelope = 1.0 - i / samples
            noise = random.uniform(-1.0, 1.0)
            tone = math.sin(2 * math.pi * 180 * t)
            value = int(6500 * envelope * (0.65 * noise + 0.35 * tone))
            buf.append(value)
        _eat_sound = pygame.mixer.Sound(buffer=bytes(buf))
    except Exception:
        _eat_sound = False
    return _eat_sound


def _get_reminder_sound():
    global _reminder_sound
    if _reminder_sound is not None:
        return _reminder_sound
    try:
        import pygame

        if not _init_pygame_mixer():
            _reminder_sound = False
            return _reminder_sound
        sample_rate = 44100
        buf = array.array("h")
        for freq, start, dur in ((880, 0.0, 0.12), (660, 0.14, 0.12), (880, 0.28, 0.18)):
            samples = int(sample_rate * dur)
            for i in range(samples):
                t = start + i / sample_rate
                env = 1.0 - i / samples
                buf.append(int(9000 * env * math.sin(2 * math.pi * freq * t)))
        _reminder_sound = pygame.mixer.Sound(buffer=bytes(buf))
    except Exception:
        _reminder_sound = False
    return _reminder_sound


def _load_phonograph_user() -> list[dict]:
    if not PHONOGRAPH_FILE.exists():
        return []
    try:
        data = json.loads(PHONOGRAPH_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return []
        entries: list[dict] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            entry_id = str(item.get("id", "")).strip()
            title = str(item.get("title", "")).strip()
            filename = str(item.get("filename", "")).strip()
            if not entry_id or not filename:
                continue
            entries.append({"id": entry_id, "title": title or filename, "filename": filename})
        return entries
    except Exception:
        return []


def _save_phonograph_user(entries: list[dict]) -> None:
    PHONOGRAPH_FILE.parent.mkdir(parents=True, exist_ok=True)
    PHONOGRAPH_FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


def _resolve_phonograph_user_path(entry: dict) -> Path | None:
    filename = str(entry.get("filename", "")).strip()
    if not filename:
        return None
    path = PHONOGRAPH_USER_DIR / filename
    return path if path.is_file() else None


def _build_phonograph_catalog() -> list[dict]:
    catalog: list[dict] = []

    def add_file(entry_id: str, title: str, wav: Path | None, *, category: str = "voice") -> None:
        if wav is None or not wav.exists():
            return
        catalog.append(
            {
                "id": entry_id,
                "title": title,
                "kind": "file",
                "path": wav,
                "category": category,
                "builtin": True,
            }
        )

    add_file(
        "builtin:call",
        "电话·平凡",
        CALL_AUDIO_WAV if CALL_AUDIO_WAV.exists() else _ensure_audio_wav(CALL_AUDIO_SRC, CALL_AUDIO_WAV),
        category="voice",
    )
    add_file(
        "builtin:type",
        "打字·键盘",
        _resolve_type_cache_wav(),
        category="sfx",
    )
    for tid in MUSIC_TRACK_ORDER:
        track = _music_track(tid)
        wav = _ensure_music_track_wav(tid)
        if wav is not None:
            add_file(f"builtin:music:{tid}", str(track["phonograph"]), wav, category="music")

    catalog.extend(
        [
            {"id": "builtin:tick", "title": "滴答·打字特效", "kind": "type_tick", "category": "sfx", "builtin": True},
            {"id": "builtin:eat", "title": "吃饭·咀嚼", "kind": "eat_sfx", "category": "sfx", "builtin": True},
            {"id": "builtin:reminder", "title": "提醒·日程铃", "kind": "reminder", "category": "sfx", "builtin": True},
        ]
    )

    for item in _load_phonograph_user():
        path = _resolve_phonograph_user_path(item)
        if path is None:
            continue
        catalog.append(
            {
                "id": f"user:{item['id']}",
                "title": item.get("title") or item.get("filename", "未命名"),
                "kind": "file",
                "path": path,
                "category": "voice",
                "builtin": False,
                "user_id": item["id"],
            }
        )
    return catalog


def _draw_pixel_bulb(canvas: tk.Canvas, x: int, y: int, px: int = 3, *, glow: float = 1.0) -> None:
    bulb = "#ffee88"
    canvas.create_rectangle(x + px, y, x + px * 3, y + px, fill=bulb, outline="")
    canvas.create_rectangle(x, y + px, x + px * 4, y + px * 3, fill=bulb, outline="")
    canvas.create_rectangle(x + px, y + px * 3, x + px * 3, y + px * 4, fill="#cccccc", outline="")
    canvas.create_rectangle(x + px * 2, y + px * 4, x + px * 3, y + px * 5, fill="#888888", outline="")


def _draw_pixel_star(canvas: tk.Canvas, x: int, y: int, px: int = 2, *, color: str = "#ffff88") -> None:
    canvas.create_rectangle(x + px, y, x + px * 2, y + px, fill=color, outline="")
    canvas.create_rectangle(x, y + px, x + px * 3, y + px * 2, fill=color, outline="")
    canvas.create_rectangle(x + px, y + px * 2, x + px * 2, y + px * 3, fill=color, outline="")


def _draw_pixel_cloud(canvas: tk.Canvas, x: int, y: int, px: int = 3, *, color: str = "#667788") -> None:
    canvas.create_rectangle(x + px, y, x + px * 4, y + px, fill=color, outline="")
    canvas.create_rectangle(x, y + px, x + px * 5, y + px * 2, fill=color, outline="")
    canvas.create_rectangle(x + px, y + px * 2, x + px * 4, y + px * 3, fill=color, outline="")
    canvas.create_rectangle(x + px * 2, y + px * 3, x + px * 3, y + px * 4, fill=color, outline="")


def _draw_pixel_heart(canvas: tk.Canvas, x: int, y: int, px: int = 2, *, color: str = "#ff6688") -> None:
    canvas.create_rectangle(x, y, x + px, y + px, fill=color, outline="")
    canvas.create_rectangle(x + px * 2, y, x + px * 3, y + px, fill=color, outline="")
    canvas.create_rectangle(x, y + px, x + px * 3, y + px * 2, fill=color, outline="")
    canvas.create_rectangle(x + px, y + px * 2, x + px * 2, y + px * 3, fill=color, outline="")


def _draw_fight_fighter_icon(canvas: tk.Canvas, size: int, *, side: str = "player") -> None:
    canvas.delete("all")
    px = max(3, size // 10)
    body = "#88ccff" if side == "player" else "#ff8844"
    accent = "#ffffff" if side == "player" else "#ffddaa"
    cx = size // 2
    foot = size - px
    canvas.create_rectangle(cx - px, foot - px * 4, cx + px, foot - px * 2, fill=body, outline="")
    canvas.create_rectangle(cx - px * 2, foot - px * 6, cx + px * 2, foot - px * 4, fill=body, outline="")
    canvas.create_rectangle(cx - px * 2, foot - px * 8, cx + px * 2, foot - px * 6, fill=accent, outline="")
    if side == "opponent":
        canvas.create_rectangle(cx - px * 3, foot - px * 9, cx - px, foot - px * 7, fill="#ff6644", outline="")


def _spawn_game_clear_particles(width: int, height: int, accent: str) -> list[dict]:
    # 保留空接口，通关动画已改为简洁静态展示
    return []


def _draw_pixel_ring(canvas: tk.Canvas, cx: int, cy: int, radius: int, px: int, color: str) -> None:
    """Rough pixel ring made of thick squares along a circle."""
    if radius <= 0:
        return
    steps = max(12, int(radius * 1.4))
    for i in range(steps):
        ang = (i / steps) * math.pi * 2
        x = cx + int(math.cos(ang) * radius) - px // 2
        y = cy + int(math.sin(ang) * radius) - px // 2
        canvas.create_rectangle(x, y, x + px, y + px, fill=color, outline="")


def _draw_game_clear_frame(
    canvas: tk.Canvas,
    width: int,
    height: int,
    phase: int,
    *,
    title: str,
    subtitle: str,
    accent: str,
    particles: list[dict],
    hero_grade: str | None = None,
    hero_color: str | None = None,
) -> None:
    """简洁通关结算：纯色底板 + 评级/标题 + 副标题，无粒子/射线/多层光环。"""
    del particles  # 不再使用粒子
    canvas.delete("all")
    canvas.create_rectangle(0, 0, width, height, fill="#0e1420", outline="")
    canvas.create_rectangle(8, 8, width - 8, height - 8, outline="#243048", width=2)

    cx = width // 2
    grade_color = hero_color or accent
    # 轻微淡入：前几帧只画底板
    if phase < 2:
        return

    if hero_grade:
        canvas.create_text(cx, 36, text="评级", fill="#8899bb", font=PIXEL_FONT)
        canvas.create_text(
            cx,
            92,
            text=hero_grade,
            fill=grade_color,
            font=("Courier New", 56, "bold"),
        )
        tier_label = TYPING_GRADE_LABELS.get(hero_grade, "")
        y = 136
        if tier_label:
            canvas.create_text(cx, y, text=tier_label, fill=grade_color, font=("Courier New", 12, "bold"))
            y += 22
        if title and title != f"评级 {hero_grade}":
            canvas.create_text(cx, y, text=title, fill="#e8eeff", font=("Courier New", 12, "bold"))
            y += 20
        sub_lines = [ln for ln in (subtitle.split("\n") if subtitle else []) if ln.strip()]
        for i, line in enumerate(sub_lines[:3]):
            canvas.create_text(cx, y + i * 18, text=line, fill="#a8b8dd", font=PIXEL_FONT)
        return

    canvas.create_text(cx, 48, text="通关", fill="#8899bb", font=PIXEL_FONT)
    canvas.create_text(cx, 92, text=title, fill=accent, font=("Courier New", 18, "bold"))
    sub_lines = [ln for ln in (subtitle.split("\n") if subtitle else []) if ln.strip()]
    for i, line in enumerate(sub_lines[:3]):
        canvas.create_text(cx, 128 + i * 18, text=line, fill="#c8d8ff", font=PIXEL_FONT)


def _draw_dizzy_sticker(canvas: tk.Canvas, size: int, phase: int) -> None:
    canvas.delete("all")
    px = max(2, size // 28)
    cx, cy = size // 2, size // 3
    for dx, dy in ((-px * 3, 0), (px * 3, 0)):
        canvas.create_rectangle(cx + dx - px, cy - px, cx + dx + px, cy + px, fill="#ffffff", outline="")
        canvas.create_rectangle(cx + dx - px // 2, cy - px // 2, cx + dx + px // 2, cy + px // 2, fill="#222244", outline="")
    for i in range(4):
        ang = phase * 0.35 + i * (math.pi / 2)
        sx = cx + int(math.cos(ang) * size * 0.28)
        sy = cy - size // 5 + int(math.sin(ang) * size * 0.12)
        col = ("#ffff66", "#ffcc44", "#ffaa88", "#88ccff")[i]
        _draw_pixel_star(canvas, sx - px, sy - px, px=max(2, px - 1), color=col)


def _load_schedules() -> list[dict]:
    if not SCHEDULE_FILE.exists():
        return []
    try:
        data = json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_schedules(items: list[dict]) -> None:
    _ensure_data_dirs()
    SCHEDULE_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def _normalize_schedule_time(raw: str) -> str | None:
    text = raw.strip()
    if not text:
        return None
    if len(text) == 4 and text.isdigit():
        text = f"{text[:2]}:{text[2:]}"
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).strftime("%H:%M")
        except ValueError:
            continue
    if len(text) == 5 and text[2] == ":":
        hour, minute = text.split(":", 1)
        if hour.isdigit() and minute.isdigit():
            h, m = int(hour), int(minute)
            if 0 <= h <= 23 and 0 <= m <= 59:
                return f"{h:02d}:{m:02d}"
    return None


def _normalize_schedule_weekdays(raw) -> list[int] | None:
    """None 表示每天；否则为 0=周一 … 6=周日 的列表。"""
    if raw is None or raw == "daily":
        return None
    if not isinstance(raw, list):
        return None
    days = sorted({int(d) for d in raw if isinstance(d, (int, float)) and 0 <= int(d) <= 6})
    if not days or len(days) >= 7:
        return None
    return days


def _format_schedule_weekdays(item: dict) -> str:
    days = _normalize_schedule_weekdays(item.get("weekdays"))
    if days is None:
        return "每天"
    return " ".join(WEEKDAY_LABELS[d] for d in days)


def _schedule_matches_today(item: dict, weekday: int) -> bool:
    days = _normalize_schedule_weekdays(item.get("weekdays"))
    if days is None:
        return True
    return weekday in days


def _normalize_music_playlist(raw, *, fallback: str | None = None) -> list[str]:
    """校验播放列表，至少保留一首有效曲。"""
    out: list[str] = []
    if isinstance(raw, list):
        for tid in raw:
            tid = MUSIC_TRACK_LEGACY_IDS.get(str(tid), str(tid))
            if tid in MUSIC_TRACKS and tid not in out:
                out.append(tid)
    if not out:
        fb = MUSIC_TRACK_LEGACY_IDS.get(str(fallback or ""), str(fallback or DEFAULT_MUSIC_TRACK))
        if fb not in MUSIC_TRACKS:
            fb = DEFAULT_MUSIC_TRACK
        if fb in MUSIC_TRACKS:
            out = [fb]
    return out


def _music_playlist_from_config(config: dict) -> list[str]:
    raw = config.get("playlist")
    if isinstance(raw, list) and raw:
        return _normalize_music_playlist(raw, fallback=DEFAULT_MUSIC_TRACK)
    tid = str(config.get("normal_track", DEFAULT_MUSIC_TRACK))
    return _normalize_music_playlist([tid], fallback=DEFAULT_MUSIC_TRACK)


def _load_music_config() -> dict:
    default = {
        "play_mode": "list",
        "playlist": [DEFAULT_MUSIC_TRACK],
        "music_volume": 70,
        "volume": 70,
        "sfx_volume": 80,
        "voice_volume": 80,
        "muted": False,
    }
    if not MUSIC_CONFIG_FILE.exists():
        return default
    try:
        data = json.loads(MUSIC_CONFIG_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return default
        merged = {**default, **data}
        if "music_volume" not in data and "volume" in data:
            merged["music_volume"] = int(data["volume"])
        merged["volume"] = merged["music_volume"]
        playlist = _normalize_music_playlist(
            data.get("playlist"),
            fallback=str(data.get("normal_track", DEFAULT_MUSIC_TRACK)),
        )
        merged["playlist"] = playlist
        play_mode = str(merged.get("play_mode", "list"))
        if play_mode not in ("list", "random"):
            play_mode = "list"
        merged["play_mode"] = play_mode
        return merged
    except Exception:
        return default


def _save_music_config(config: dict) -> None:
    MUSIC_CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_food_inventory() -> dict[str, int]:
    default = {fid: 0 for fid in FOODS}
    if not FOOD_INVENTORY_FILE.exists():
        return default
    try:
        data = json.loads(FOOD_INVENTORY_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            for fid in FOODS:
                default[fid] = max(0, int(data.get(fid, 0)))
    except Exception:
        pass
    return default


def _save_food_inventory(inventory: dict[str, int]) -> None:
    payload = {fid: max(0, int(inventory.get(fid, 0))) for fid in FOODS}
    FOOD_INVENTORY_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _angle_in_arc(angle: float, start: float, span: float) -> bool:
    a = angle % 360
    s = start % 360
    e = (s + span) % 360
    if s <= e:
        return s <= a < e
    return a >= s or a < e


def _expose_blue_span_for_round(base_span: float, round_index: int) -> float:
    """第 1~5 次 QTE 蓝色判定区逐次缩小（round_index 从 0 起）。"""
    idx = max(0, min(len(EXPOSE_BLUE_SPAN_RATIOS) - 1, round_index))
    ratio = EXPOSE_BLUE_SPAN_RATIOS[idx]
    return max(EXPOSE_BLUE_SPAN_MIN, float(base_span) * ratio)


def _draw_expose_qte_ring(
    canvas: tk.Canvas, size: int, blue_start: float, pointer: float, *, blue_span: float = EXPOSE_BLUE_SPAN
) -> None:
    canvas.delete("all")
    cx = cy = size // 2
    outer_r = size // 2 - 6
    inner_r = max(8, outer_r - 12)
    canvas.create_oval(cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r, fill="#eeeeee", outline="#cccccc", width=2)
    canvas.create_oval(cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r, fill="#111122", outline="")
    canvas.create_arc(
        cx - outer_r,
        cy - outer_r,
        cx + outer_r,
        cy + outer_r,
        start=blue_start,
        extent=blue_span,
        fill="#4488ff",
        outline="#66aaff",
        width=2,
        style=tk.PIESLICE,
    )
    canvas.create_arc(
        cx - inner_r,
        cy - inner_r,
        cx + inner_r,
        cy + inner_r,
        start=blue_start,
        extent=blue_span,
        fill="#111122",
        outline="",
        style=tk.PIESLICE,
    )
    rad = math.radians(pointer)
    px = cx + int(math.cos(rad) * (outer_r - 2))
    py = cy - int(math.sin(rad) * (outer_r - 2))
    canvas.create_line(cx, cy, px, py, fill="#ff4444", width=3)
    canvas.create_oval(px - 4, py - 4, px + 4, py + 4, fill="#ffcc44", outline="")


def _draw_glitch_fault(canvas: tk.Canvas, width: int, height: int, message: str, phase: int) -> None:
    canvas.delete("all")
    canvas.create_rectangle(2, 2, width - 2, height - 2, fill="#120818", outline="#ff3366", width=2)
    for y in range(0, height, 3):
        if (y + phase) % 7 < 2:
            canvas.create_line(0, y, width, y, fill="#2a1030")
    for i in range(6):
        gy = (phase * 5 + i * 17) % max(1, height - 10)
        gh = 2 + (phase + i) % 4
        col = ("#ff0044", "#00ffcc", "#662244", "#ffaa00")[i % 4]
        canvas.create_rectangle(0, gy, width, gy + gh, fill=col, outline="")
    jitter = int(math.sin(phase * 0.65) * 4)
    canvas.create_text(
        width // 2 + jitter,
        height // 2 - 10,
        text=message,
        fill="#ff88aa",
        font=("Courier New", 11, "bold"),
    )
    canvas.create_text(
        width // 2 - jitter,
        height // 2 + 14,
        text=f"Enter 判定 · 连中{EXPOSE_GLITCH_HITS_REQUIRED}次通关",
        fill="#88ccff",
        font=("Courier New", 9, "bold"),
    )
def _draw_music_wave(canvas: tk.Canvas, width: int, height: int, phase: int, *, beat: float = 1.0) -> None:
    """Pixel concentric rings around the pet (music mode aura)."""
    canvas.delete("all")
    cx, cy = width // 2, height // 2
    amp = max(0.25, min(1.0, beat))
    px = max(4, min(width, height) // 18)
    colors = ("#88ccff", "#4488ff", "#66aaff", "#aadfff", "#ffcc66")
    for ring in range(5):
        glow = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(phase * 0.22 + ring * 0.85))
        base = min(width, height) * (0.20 + ring * 0.09)
        r = int(base * (0.75 + 0.35 * amp) * glow)
        _draw_pixel_ring(canvas, cx, cy, r, px, colors[ring % len(colors)])
    bars = 7
    bar_w = max(px, width // (bars * 3))
    gap = bar_w
    total = bars * bar_w + (bars - 1) * gap
    x0 = (width - total) // 2
    for i in range(bars):
        x = x0 + i * (bar_w + gap)
        wave = math.sin(phase * 0.35 + i * 0.8) * 0.5 + 0.5
        h = int(wave * amp * (height // 5) + px)
        col = "#88ccff" if i % 2 == 0 else "#4488ff"
        canvas.create_rectangle(x, height - h - 4, x + bar_w, height - 4, fill=col, outline="")


def _music_track(track_id: str | None) -> dict:
    tid = str(track_id or DEFAULT_MUSIC_TRACK).strip() or DEFAULT_MUSIC_TRACK
    tid = MUSIC_TRACK_LEGACY_IDS.get(tid, tid)
    if tid in MUSIC_TRACKS:
        return MUSIC_TRACKS[tid]
    if DEFAULT_MUSIC_TRACK in MUSIC_TRACKS:
        return MUSIC_TRACKS[DEFAULT_MUSIC_TRACK]
    # 兜底：任意一首
    if MUSIC_TRACK_ORDER:
        return MUSIC_TRACKS[MUSIC_TRACK_ORDER[0]]
    return {
        "id": "missing",
        "title": "（无曲目）",
        "src": MUSIC_SRC_DIR / "missing.mp4",
        "cache": DATA_AUDIO_DIR / "music_missing_cache.wav",
        "phonograph": "音乐·无曲目",
    }


def _ensure_music_track_wav(track_id: str | None) -> Path | None:
    track = _music_track(track_id)
    return _ensure_audio_wav(Path(track["src"]), Path(track["cache"]))


def _ensure_all_music_track_wavs() -> None:
    for tid in MUSIC_TRACK_ORDER:
        try:
            _ensure_music_track_wav(tid)
        except Exception:
            pass


def _resolve_music_wav(track_id: str | None) -> Path | None:
    return _ensure_music_track_wav(track_id)


def _load_ai_config() -> dict:
    config = dict(AI_DEFAULT_CONFIG)
    if AI_CONFIG_FILE.exists():
        try:
            data = json.loads(AI_CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                config.update(data)
        except Exception:
            pass
    if not config.get("api_key"):
        config["api_key"] = (
            os.environ.get("DASHSCOPE_API_KEY", "")
            or os.environ.get("QWEN_API_KEY", "")
            or os.environ.get("OPENAI_API_KEY", "")
            or os.environ.get("DEEPSEEK_API_KEY", "")
        )
    return config


def _apply_font_size(size: int) -> None:
    global PIXEL_FONT
    size = max(8, min(24, int(size)))
    PIXEL_FONT = ("Courier New", size, "bold")


def _load_app_config() -> dict:
    default = {
        "font_size": 12,
        "display_size": DEFAULT_SIZE,
        "display_preset": "中",
        "difficulty": "中",
        "rhythm_speed": "中",
        "rhythm_chart_diff": "中",
        "weather_city": "北京",
        "seen_hints": {},
        "work_mode": {"show_props": True, "show_stack": True},
    }
    if not APP_CONFIG_FILE.exists():
        return default
    try:
        data = json.loads(APP_CONFIG_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {**default, **data}
    except Exception:
        pass
    return default


def _save_app_config(config: dict) -> None:
    APP_CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


# —— 天气预报（Open-Meteo，无需 API Key）——
WEATHER_CITIES: dict[str, tuple[float, float]] = {
    "北京": (39.9042, 116.4074),
    "上海": (31.2304, 121.4737),
    "广州": (23.1291, 113.2644),
    "深圳": (22.5431, 114.0579),
    "杭州": (30.2741, 120.1551),
    "成都": (30.5728, 104.0668),
    "重庆": (29.5630, 106.5516),
    "武汉": (30.5928, 114.3055),
    "西安": (34.3416, 108.9398),
    "南京": (32.0603, 118.7969),
    "天津": (39.3434, 117.3616),
    "长沙": (28.2282, 112.9388),
    "青岛": (36.0671, 120.3826),
    "厦门": (24.4798, 118.0894),
    "香港": (22.3193, 114.1694),
    "台北": (25.0330, 121.5654),
}
WEATHER_W = 440
WEATHER_H = 520
_WEATHER_ICON_CACHE: dict[tuple[str, int], ImageTk.PhotoImage] = {}


def _weather_code_info(code: int) -> tuple[str, str]:
    """返回 (中文描述, 图标键)。"""
    c = int(code)
    if c == 0:
        return "晴朗", "sunny"
    if c in (1, 2):
        return "多云", "partly"
    if c == 3:
        return "阴天", "cloudy"
    if c in (45, 48):
        return "有雾", "fog"
    if c in (51, 53, 55, 56, 57):
        return "毛毛雨", "drizzle"
    if c in (61, 63, 65, 66, 67, 80, 81, 82):
        return "降雨", "rain"
    if c in (71, 73, 75, 77, 85, 86):
        return "降雪", "snow"
    if c in (95, 96, 99):
        return "雷暴", "storm"
    return "未知", "cloudy"


def _draw_pixel_weather_icon(kind: str, px: int = 48) -> Image.Image:
    """程序生成像素天气图标（NEAREST 放大，偏复古）。"""
    base = 16
    scale = max(1, px // base)
    img = Image.new("RGBA", (base, base), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    sky = (40, 56, 96, 255)
    sun = (255, 210, 72, 255)
    cloud = (220, 228, 240, 255)
    cloud_d = (160, 176, 200, 255)
    rain = (110, 180, 255, 255)
    snow = (240, 248, 255, 255)
    fog = (180, 190, 200, 180)
    bolt = (255, 230, 90, 255)

    def px_rect(x0, y0, x1, y1, fill) -> None:
        d.rectangle([x0, y0, x1, y1], fill=fill)

    if kind == "sunny":
        px_rect(6, 6, 10, 10, sun)
        for x, y in ((3, 3), (8, 2), (12, 3), (2, 8), (13, 8), (3, 12), (8, 13), (12, 12)):
            px_rect(x, y, x, y, sun)
    elif kind == "partly":
        px_rect(3, 3, 6, 6, sun)
        px_rect(5, 8, 13, 11, cloud)
        px_rect(7, 6, 11, 8, cloud)
        px_rect(4, 9, 6, 11, cloud_d)
    elif kind == "cloudy":
        px_rect(2, 8, 13, 12, cloud)
        px_rect(4, 5, 11, 8, cloud)
        px_rect(3, 10, 6, 12, cloud_d)
        px_rect(10, 9, 13, 12, cloud_d)
    elif kind == "fog":
        for y in (5, 8, 11):
            px_rect(2, y, 13, y + 1, fog)
    elif kind in ("drizzle", "rain"):
        px_rect(3, 4, 12, 8, cloud)
        px_rect(5, 2, 10, 4, cloud)
        step = 2 if kind == "drizzle" else 1
        for i, x in enumerate(range(4, 13, step + 1)):
            y0 = 9 + (i % 2)
            px_rect(x, y0, x, y0 + (1 if kind == "drizzle" else 3), rain)
    elif kind == "snow":
        px_rect(3, 4, 12, 8, cloud)
        px_rect(5, 2, 10, 4, cloud)
        for x, y in ((4, 10), (7, 11), (10, 10), (5, 13), (9, 13)):
            px_rect(x, y, x, y, snow)
            px_rect(x - 1, y, x + 1, y, snow)
            px_rect(x, y - 1, x, y + 1, snow)
    elif kind == "storm":
        px_rect(2, 3, 13, 8, cloud_d)
        px_rect(4, 1, 11, 3, cloud)
        px_rect(7, 8, 9, 10, bolt)
        px_rect(5, 10, 8, 11, bolt)
        px_rect(6, 11, 7, 14, bolt)
        for x in (3, 6, 10):
            px_rect(x, 9, x, 12, rain)
    else:
        px_rect(4, 6, 11, 11, cloud)

    # 淡底色方块，更像像素贴图
    out = Image.new("RGBA", (base, base), (*sky[:3], 40))
    out.alpha_composite(img)
    return out.resize((base * scale, base * scale), Image.NEAREST)


def _weather_icon_photo(kind: str, px: int = 48) -> ImageTk.PhotoImage:
    key = (kind, int(px))
    photo = _WEATHER_ICON_CACHE.get(key)
    if photo is None:
        photo = ImageTk.PhotoImage(_draw_pixel_weather_icon(kind, px))
        _WEATHER_ICON_CACHE[key] = photo
    return photo


def _fetch_open_meteo_weather(lat: float, lon: float, *, days: int = 7) -> dict:
    params = urllib.parse.urlencode(
        {
            "latitude": f"{lat:.4f}",
            "longitude": f"{lon:.4f}",
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,apparent_temperature",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "auto",
            "forecast_days": max(1, min(7, int(days))),
        }
    )
    url = f"https://api.open-meteo.com/v1/forecast?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "VpetWeather/1.2"})
    with urllib.request.urlopen(req, timeout=12) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("天气数据格式异常")
    return data


def _geocode_city_name(name: str) -> tuple[str, float, float] | None:
    q = (name or "").strip()
    if not q:
        return None
    if q in WEATHER_CITIES:
        lat, lon = WEATHER_CITIES[q]
        return q, lat, lon
    params = urllib.parse.urlencode({"name": q, "count": 1, "language": "zh", "format": "json"})
    url = f"https://geocoding-api.open-meteo.com/v1/search?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "VpetWeather/1.2"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="replace"))
    results = data.get("results") if isinstance(data, dict) else None
    if not results:
        return None
    hit = results[0]
    label = str(hit.get("name") or q)
    admin = hit.get("admin1") or hit.get("country")
    if admin and str(admin) not in label:
        label = f"{label}·{admin}"
    return label[:18], float(hit["latitude"]), float(hit["longitude"])


def _format_pet_id(pet_id: int) -> str:
    s = f"{max(0, int(pet_id)):08d}"
    return f"{s[:4]} {s[4:]}"


def _allocate_pet_id() -> int:
    registry: dict = {"next_id": 0}
    if PET_ID_REGISTRY_FILE.exists():
        try:
            data = json.loads(PET_ID_REGISTRY_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                registry = data
        except Exception:
            pass
    pet_id = int(registry.get("next_id", 0))
    registry["next_id"] = pet_id + 1
    PET_ID_REGISTRY_FILE.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")
    return pet_id


def _load_pet_profile() -> dict:
    if not PET_ID_FEATURE:
        return {}
    if PET_PROFILE_FILE.exists():
        try:
            data = json.loads(PET_PROFILE_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "pet_id" in data:
                pid = data["pet_id"]
                if isinstance(pid, str):
                    try:
                        data["pet_id"] = int(pid.strip().replace(" ", ""))
                    except ValueError:
                        data["pet_id"] = 0
                    _save_pet_profile(data)
                elif isinstance(pid, float):
                    data["pet_id"] = int(pid)
                    _save_pet_profile(data)
                return data
        except Exception:
            pass
    profile = {
        "pet_id": _allocate_pet_id(),
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "records": {},
    }
    PET_PROFILE_FILE.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    return profile


def _save_pet_profile(profile: dict) -> None:
    if not PET_ID_FEATURE:
        return
    PET_PROFILE_FILE.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_leaderboard() -> dict[str, list]:
    if not LEADERBOARD_FILE.exists():
        return {}
    try:
        data = json.loads(LEADERBOARD_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {str(k): v for k, v in data.items() if isinstance(v, list)}
    except Exception:
        pass
    return {}


def _save_leaderboard(board: dict[str, list]) -> None:
    LEADERBOARD_FILE.parent.mkdir(parents=True, exist_ok=True)
    LEADERBOARD_FILE.write_text(json.dumps(board, ensure_ascii=False, indent=2), encoding="utf-8")


def _leaderboard_bucket(category: str, payload: dict) -> str:
    lang = str(payload.get("lang", "")).strip()
    if category in ("typing", "vocab") and lang:
        return f"{category}:{lang}"
    return category


def _leaderboard_base_category(bucket: str) -> str:
    return bucket.split(":", 1)[0]


def _grade_rank(grade: str) -> int:
    return {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1}.get(str(grade).upper(), 0)


def _leaderboard_sort_key(bucket: str, entry: dict) -> tuple:
    base = _leaderboard_base_category(bucket)
    if base == "gather":
        return (-int(entry.get("best_score", 0)), -int(entry.get("best_catches", 0)))
    if base == "typing":
        return (-int(entry.get("best_score", 0)), -_grade_rank(str(entry.get("best_grade", "D"))))
    if base == "vocab":
        return (-int(entry.get("best_streak", 0)), -int(entry.get("total_correct", 0)))
    if base == "rhyme":
        return (-int(entry.get("wins", 0)),)
    if base == "music":
        return (
            (-int(entry.get("best_score", 0)),
             -_grade_rank(str(entry.get("best_grade", "D"))),
             -int(entry.get("best_combo", 0))),
        )
    return (0,)


def _load_wav_mono_float(path: Path) -> tuple[object, int]:
    """读取 wav 为单声道 float32，必要时降到 ~22kHz。"""
    import wave

    import numpy as np

    with wave.open(str(path), "rb") as wf:
        sr = int(wf.getframerate())
        ch = int(wf.getnchannels())
        sw = int(wf.getsampwidth())
        raw = wf.readframes(wf.getnframes())
    if sw == 1:
        data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    elif sw == 2:
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    elif sw == 4:
        data = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f"unsupported sample width: {sw}")
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1)
    peak = float(np.max(np.abs(data))) + 1e-9
    data = data / peak
    if sr > 22050:
        factor = max(1, int(round(sr / 22050.0)))
        data = data[::factor]
        sr = sr // factor
    return data, sr


def _onset_novelty(y, sr: int, *, hop: int = 512, win: int = 2048):
    import numpy as np

    if len(y) < win:
        y = np.pad(y, (0, win - len(y)))
    n_frames = 1 + max(0, (len(y) - win) // hop)
    frames = np.lib.stride_tricks.as_strided(
        y,
        shape=(n_frames, win),
        strides=(y.strides[0] * hop, y.strides[0]),
        writeable=False,
    )
    env = np.sqrt(np.mean(frames * frames, axis=1) + 1e-12)
    nov = np.maximum(0.0, np.diff(env, prepend=env[:1]))
    if len(nov) >= 5:
        nov = np.convolve(nov, np.ones(5, dtype=np.float32) / 5.0, mode="same")
    return nov.astype(np.float32), hop


def _normalize_dance_bpm(bpm: float) -> float:
    """把半拍/倍拍折叠到常见 95~160 区间。"""
    b = float(bpm)
    while b < 95.0 and b * 2.0 <= 180.0:
        b *= 2.0
    while b > 165.0 and b / 2.0 >= 70.0:
        b /= 2.0
    return max(70.0, min(180.0, b))


def _estimate_bpm_from_novelty(nov, hop_sec: float) -> float:
    import numpy as np

    x = nov - float(nov.mean())
    n = len(x)
    if n < 32:
        return float(RHYTHM_BPM)
    nfft = 1 << (n * 2 - 1).bit_length()
    fx = np.fft.rfft(x, nfft)
    ac = np.fft.irfft(fx * np.conj(fx), nfft)[:n]
    min_lag = max(1, int(0.25 / hop_sec))
    ac[:min_lag] = 0.0
    best_bpm = float(RHYTHM_BPM)
    best = -1.0
    for bpm in range(70, 181):
        lag = int(round((60.0 / bpm) / hop_sec))
        if lag < 1 or lag >= len(ac):
            continue
        score = float(ac[lag])
        if lag * 2 < len(ac):
            score += 0.45 * float(ac[lag * 2])
        if lag // 2 >= min_lag:
            score += 0.25 * float(ac[lag // 2])
        if score > best:
            best = score
            best_bpm = float(bpm)
    return _normalize_dance_bpm(best_bpm)


def _beat_phase_frames(nov, period_frames: float) -> float:
    import numpy as np

    if period_frames <= 1 or len(nov) < 8:
        return 0.0
    best_phase = 0.0
    best = -1.0
    for phase in np.linspace(0.0, period_frames, 48, endpoint=False):
        idxs = np.round(np.arange(phase, len(nov), period_frames)).astype(int)
        idxs = idxs[(idxs >= 0) & (idxs < len(nov))]
        score = float(nov[idxs].sum()) if len(idxs) else 0.0
        if score > best:
            best = score
            best_phase = float(phase)
    return best_phase


def _snap_times_ms(times: list[int], grid_ms: float, tol_ms: float = 55.0) -> list[int]:
    if not times or grid_ms <= 1:
        return times
    snapped: list[int] = []
    for t in times:
        q = int(round(t / grid_ms) * grid_ms)
        if abs(q - t) <= tol_ms:
            snapped.append(max(0, q))
        else:
            snapped.append(int(t))
    return snapped


def _events_to_rhythm_notes(
    event_ms: list,
    *,
    difficulty: str,
    duration_ms: int,
    seed: int,
    bpm: float | None = None,
) -> list[dict]:
    dens = {"低": 0.72, "中": 0.82, "高": 0.94}.get(str(difficulty), 0.82)
    chord_p = {"低": 0.04, "中": 0.09, "高": 0.14}.get(str(difficulty), 0.09)
    half_keep = {"低": 0.08, "中": 0.55, "高": 0.92}.get(str(difficulty), 0.55)
    rng = random.Random(seed)
    end_t = max(4000, int(duration_ms) - 2200)
    start_t = 1800
    notes: list[dict] = []
    lane = rng.randrange(RHYTHM_LANES)
    last_t = -99999

    normalized: list[tuple[int, str]] = []
    for item in event_ms:
        if isinstance(item, tuple):
            normalized.append((int(item[0]), str(item[1])))
        else:
            normalized.append((int(item), "beat"))

    for t, kind in normalized:
        if t < start_t or t > end_t:
            continue
        if t - last_t < 90:
            continue
        if kind == "half" and rng.random() > half_keep:
            continue
        if rng.random() > dens:
            continue
        if rng.random() < chord_p:
            a, b = rng.sample(range(RHYTHM_LANES), 2)
            notes.append({"t": int(t), "lane": a, "hit": False, "missed": False})
            notes.append({"t": int(t), "lane": b, "hit": False, "missed": False})
        else:
            step = rng.choice((-1, 1, 1, 2, -2, 0))
            lane = (lane + step) % RHYTHM_LANES
            notes.append({"t": int(t), "lane": lane, "hit": False, "missed": False})
        last_t = t
    notes.sort(key=lambda n: (int(n["t"]), int(n["lane"])))
    return _annotate_rhythm_hold_notes(notes, difficulty=difficulty, bpm=bpm, seed=seed + 17)


def _rhythm_travel_ms_for(speed: str | None) -> int:
    return int(RHYTHM_SPEED_TRAVEL_MS.get(str(speed or "中"), RHYTHM_TRAVEL_MS))


def _rhythm_hold_tail_judgment(delta_ms: int) -> tuple[str, int]:
    ad = abs(int(delta_ms))
    if ad <= RHYTHM_HIT_PERFECT_MS:
        return "Perfect", 300
    if ad <= RHYTHM_HIT_GREAT_MS:
        return "Great", 200
    if ad <= RHYTHM_HOLD_RELEASE_MS:
        return "Good", 100
    return "Miss", 0


def _normalize_rhythm_note(n: dict) -> dict:
    t = int(n.get("t", 0))
    end = int(n.get("end", t) or t)
    if end < t:
        end = t
    hold = bool(n.get("hold")) or (end - t >= 220)
    return {
        "t": t,
        "end": end,
        "lane": int(n.get("lane", 0)) % RHYTHM_LANES,
        "hold": hold,
        "hit": False,
        "missed": False,
        "holding": False,
        "head_hit": False,
        "tail_done": False,
    }


def _annotate_rhythm_hold_notes(
    notes: list[dict],
    *,
    difficulty: str,
    bpm: float | None,
    seed: int,
) -> list[dict]:
    """把部分点按音符升级为长按长音（不与同轨后续音符冲突）。"""
    if not notes:
        return []
    rng = random.Random(seed)
    hold_p = {"低": 0.10, "中": 0.16, "高": 0.22}.get(str(difficulty), 0.16)
    beat = 60000.0 / float(bpm if bpm and bpm > 0 else RHYTHM_BPM)
    hold_lens = [int(beat), int(beat * 1.5), int(beat * 2.0), int(beat * 2.5)]
    raw = sorted((_normalize_rhythm_note(n) for n in notes), key=lambda n: (n["t"], n["lane"]))
    # 按轨道找下一音时刻，决定能否拉长
    next_t_by_lane: dict[int, list[int]] = {i: [] for i in range(RHYTHM_LANES)}
    for n in raw:
        next_t_by_lane[int(n["lane"])].append(int(n["t"]))
    cursor = {i: 0 for i in range(RHYTHM_LANES)}
    out: list[dict] = []
    occupied_until = [-1] * RHYTHM_LANES
    for n in raw:
        lane = int(n["lane"])
        t = int(n["t"])
        cursor[lane] += 1
        # 已有显式长音
        if n["hold"] and n["end"] > t + 200:
            if t < occupied_until[lane]:
                n["hold"] = False
                n["end"] = t
            else:
                occupied_until[lane] = int(n["end"])
            out.append(n)
            continue
        # 随机升级
        nxt = None
        idx = cursor[lane]
        times = next_t_by_lane[lane]
        if idx < len(times):
            nxt = times[idx]
        if t < occupied_until[lane]:
            n["hold"] = False
            n["end"] = t
            out.append(n)
            continue
        if rng.random() < hold_p:
            length = rng.choice(hold_lens)
            end = t + length
            if nxt is not None:
                end = min(end, int(nxt) - 140)
            if end - t >= 260:
                n["hold"] = True
                n["end"] = int(end)
                occupied_until[lane] = int(end)
            else:
                n["hold"] = False
                n["end"] = t
        else:
            n["hold"] = False
            n["end"] = t
        out.append(n)
    return out


def _analyze_wav_beat_events(wav_path: Path, duration_ms: int) -> tuple[float, list[tuple[int, str]]]:
    """从音频估 BPM，并生成 (时刻ms, beat|half) 事件。"""
    import numpy as np

    y, sr = _load_wav_mono_float(wav_path)
    y = np.ascontiguousarray(y, dtype=np.float32)
    hop = 512
    max_samples = int(min(len(y), RHYTHM_ANALYZE_MAX_SEC * sr))
    y_head = np.ascontiguousarray(y[:max_samples], dtype=np.float32)
    nov, hop = _onset_novelty(y_head, sr, hop=hop)
    hop_sec = hop / float(sr)
    hop_ms = hop_sec * 1000.0
    bpm = _estimate_bpm_from_novelty(nov, hop_sec)
    period_ms = 60000.0 / bpm
    period_frames = period_ms / hop_ms
    phase = _beat_phase_frames(nov, period_frames)
    phase_ms = phase * hop_ms

    events: list[tuple[int, str]] = []
    t = phase_ms
    while t < 1200:
        t += period_ms
    half = period_ms * 0.5
    end_t = max(4000, int(duration_ms) - 1800)
    while t <= end_t:
        events.append((int(round(t)), "beat"))
        events.append((int(round(t + half)), "half"))
        t += period_ms

    thr = float(np.percentile(nov, 78))
    onset_raw: list[int] = []
    last = -10_000
    for i, v in enumerate(nov):
        if v < thr:
            continue
        if i > 0 and i + 1 < len(nov) and not (v >= nov[i - 1] and v >= nov[i + 1]):
            continue
        ms = int(i * hop_ms)
        if ms - last < 110:
            continue
        onset_raw.append(ms)
        last = ms
    onset_snap = _snap_times_ms(onset_raw, half, tol_ms=70.0)
    win_ms = max_samples / sr * 1000.0
    seen = {tt for tt, _k in events}
    for ms in onset_snap:
        if ms > win_ms or ms in seen:
            continue
        rel = ((ms - phase_ms) / period_ms) % 1.0
        kind = "beat" if rel < 0.18 or rel > 0.82 else "half"
        events.append((int(ms), kind))
        seen.add(int(ms))
    events.sort(key=lambda x: x[0])
    return bpm, events


def _rhythm_chart_cache_path(track_id: str, difficulty: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in f"{track_id}_{difficulty}")
    return DATA_AUDIO_DIR / f"rhythm_chart_{safe}_v{RHYTHM_CHART_CACHE_VER}.json"


def _build_rhythm_chart_random(duration_ms: int, difficulty: str, *, bpm: float | None = None, seed: int | None = None) -> list[dict]:
    dens = {"低": 0.34, "中": 0.50, "高": 0.66}.get(str(difficulty), 0.50)
    if duration_ms >= 180000:
        dens *= 0.82
    elif duration_ms >= 120000:
        dens *= 0.90
    use_bpm = float(bpm) if bpm and bpm > 0 else float(RHYTHM_BPM)
    beat = 60000.0 / use_bpm
    rng = random.Random(seed if seed is not None else int(time.time()) % 100000)
    notes: list[dict] = []
    t = 2200.0
    lane = rng.randrange(RHYTHM_LANES)
    end_t = max(4000, duration_ms - 2500)
    while t < end_t:
        if rng.random() < dens:
            if rng.random() < 0.10:
                a, b = rng.sample(range(RHYTHM_LANES), 2)
                notes.append({"t": int(t), "lane": a, "hit": False, "missed": False})
                notes.append({"t": int(t), "lane": b, "hit": False, "missed": False})
            else:
                lane = (lane + rng.choice((-1, 1, 1, 2, -2))) % RHYTHM_LANES
                notes.append({"t": int(t), "lane": lane, "hit": False, "missed": False})
        step = beat * (0.5 if rng.random() < 0.22 else 1.0)
        if rng.random() < 0.08:
            step = beat * 1.5
        t += step
    seed_h = int(seed if seed is not None else rng.randint(1, 10**9))
    return _annotate_rhythm_hold_notes(notes, difficulty=difficulty, bpm=use_bpm, seed=seed_h + 31)


def _build_rhythm_chart_from_wav(
    wav_path: Path,
    duration_ms: int,
    difficulty: str,
    *,
    track_id: str | None = None,
) -> tuple[list[dict], float, str]:
    """返回 (notes, bpm, source) source=beat|cache|random。"""
    tid = track_id or wav_path.stem
    cache_path = _rhythm_chart_cache_path(str(tid), str(difficulty))
    try:
        st = wav_path.stat()
        wav_sig = f"{int(st.st_mtime)}:{st.st_size}"
    except Exception:
        wav_sig = ""

    if cache_path.exists():
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            if (
                isinstance(data, dict)
                and int(data.get("ver", 0)) == RHYTHM_CHART_CACHE_VER
                and str(data.get("wav_sig", "")) == wav_sig
                and str(data.get("difficulty", "")) == str(difficulty)
            ):
                raw = data.get("notes") or []
                bpm = float(data.get("bpm", RHYTHM_BPM))
                end_t = max(4000, int(duration_ms) - 2200)
                notes = [
                    _normalize_rhythm_note(n)
                    for n in raw
                    if isinstance(n, dict) and int(n.get("t", 0)) <= end_t
                ]
                if len(notes) >= 8:
                    return notes, bpm, "cache"
        except Exception:
            pass

    try:
        full_ms = max(duration_ms, _get_wav_duration_ms(wav_path) or duration_ms)
        bpm, events = _analyze_wav_beat_events(wav_path, full_ms)
        seed = abs(hash((str(wav_path.resolve()), difficulty, wav_sig))) % (10**9)
        notes_full = _events_to_rhythm_notes(
            events, difficulty=difficulty, duration_ms=full_ms, seed=seed, bpm=bpm
        )
        try:
            payload = {
                "ver": RHYTHM_CHART_CACHE_VER,
                "track_id": tid,
                "difficulty": difficulty,
                "bpm": bpm,
                "wav_sig": wav_sig,
                "notes": [
                    {
                        "t": int(n["t"]),
                        "lane": int(n["lane"]),
                        "end": int(n.get("end", n["t"])),
                        "hold": bool(n.get("hold")),
                    }
                    for n in notes_full
                ],
            }
            cache_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass
        end_t = max(4000, int(duration_ms) - 2200)
        notes = [n for n in notes_full if int(n["t"]) <= end_t]
        if len(notes) >= 8:
            return notes, bpm, "beat"
    except Exception:
        pass

    notes = _build_rhythm_chart_random(duration_ms, difficulty, bpm=None)
    return notes, float(RHYTHM_BPM), "random"


def _build_rhythm_chart(
    duration_ms: int,
    difficulty: str,
    *,
    wav_path: Path | None = None,
    track_id: str | None = None,
) -> list[dict]:
    if wav_path is not None and Path(wav_path).exists():
        notes, _bpm, _src = _build_rhythm_chart_from_wav(
            Path(wav_path), duration_ms, difficulty, track_id=track_id
        )
        return notes
    return _build_rhythm_chart_random(duration_ms, difficulty)


def _rhythm_hit_judgment(delta_ms: int) -> tuple[str, int]:
    ad = abs(delta_ms)
    if ad <= RHYTHM_HIT_PERFECT_MS:
        return "Perfect", 300
    if ad <= RHYTHM_HIT_GREAT_MS:
        return "Great", 200
    if ad <= RHYTHM_HIT_GOOD_MS:
        return "Good", 100
    return "Miss", 0


def _leaderboard_bucket_title(bucket: str) -> str:
    base = _leaderboard_base_category(bucket)
    title = GAME_RANK_TITLES.get(base, base)
    if ":" in bucket:
        lang = bucket.split(":", 1)[1]
        return f"{title} · {lang}"
    return title


def _update_leaderboard(category: str, pet_id: int | None, entry: dict) -> None:
    if not PET_ID_FEATURE or pet_id is None:
        return
    board = _load_leaderboard()
    bucket = _leaderboard_bucket(category, entry)
    rows = board.get(bucket, [])
    if not isinstance(rows, list):
        rows = []
    existing = next((r for r in rows if r.get("pet_id") == pet_id), None)
    ts = str(entry.get("ts", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    if category == "gather":
        score = int(entry.get("score", 0))
        catches = int(entry.get("catches", 0))
        if existing:
            existing["attempts"] = int(existing.get("attempts", 0)) + 1
            if score > int(existing.get("best_score", 0)) or (
                score == int(existing.get("best_score", 0)) and catches > int(existing.get("best_catches", 0))
            ):
                existing["best_score"] = score
                existing["best_catches"] = catches
                existing["ts"] = ts
        else:
            rows.append(
                {"pet_id": pet_id, "best_score": score, "best_catches": catches, "attempts": 1, "ts": ts}
            )
    elif category == "typing":
        score = int(entry.get("score", 0))
        grade = str(entry.get("grade", "D"))
        if existing:
            existing["attempts"] = int(existing.get("attempts", 0)) + 1
            old_score = int(existing.get("best_score", 0))
            old_grade = str(existing.get("best_grade", "D"))
            if score > old_score or (score == old_score and _grade_rank(grade) > _grade_rank(old_grade)):
                existing["best_score"] = score
                existing["best_grade"] = grade
                existing["ts"] = ts
        else:
            rows.append({"pet_id": pet_id, "best_score": score, "best_grade": grade, "attempts": 1, "ts": ts})
    elif category == "vocab":
        if not entry.get("correct"):
            return
        streak_clear = int(entry.get("streak_clear", 0))
        if existing:
            existing["total_correct"] = int(existing.get("total_correct", 0)) + 1
            if streak_clear > int(existing.get("best_streak", 0)):
                existing["best_streak"] = streak_clear
                existing["ts"] = ts
        else:
            rows.append({"pet_id": pet_id, "total_correct": 1, "best_streak": streak_clear, "ts": ts})
    elif category == "rhyme":
        if not entry.get("won"):
            return
        if existing:
            existing["wins"] = int(existing.get("wins", 0)) + 1
            existing["ts"] = ts
        else:
            rows.append({"pet_id": pet_id, "wins": 1, "ts": ts})
    elif category == "music":
        score = int(entry.get("score", 0))
        combo = int(entry.get("max_combo", 0))
        grade = str(entry.get("grade", "D"))
        if existing:
            existing["attempts"] = int(existing.get("attempts", 0)) + 1
            old_score = int(existing.get("best_score", 0))
            old_grade = str(existing.get("best_grade", "D"))
            if score > old_score or (
                score == old_score and _grade_rank(grade) > _grade_rank(old_grade)
            ) or (
                score == old_score
                and _grade_rank(grade) == _grade_rank(old_grade)
                and combo > int(existing.get("best_combo", 0))
            ):
                existing["best_score"] = score
                existing["best_combo"] = combo
                existing["best_grade"] = grade
                existing["ts"] = ts
        else:
            rows.append(
                {
                    "pet_id": pet_id,
                    "best_score": score,
                    "best_combo": combo,
                    "best_grade": grade,
                    "attempts": 1,
                    "ts": ts,
                }
            )
    else:
        return

    rows.sort(key=lambda row: _leaderboard_sort_key(bucket, row))
    board[bucket] = rows[:LEADERBOARD_MAX]
    _save_leaderboard(board)


def _rebuild_leaderboard_from_profile(profile: dict) -> None:
    if not PET_ID_FEATURE:
        return
    pet_id = profile.get("pet_id")
    if pet_id is None:
        return
    records = profile.get("records", {})
    if not isinstance(records, dict):
        return
    for item in records.get("gather", []):
        if isinstance(item, dict):
            _update_leaderboard("gather", pet_id, item)
    for item in records.get("typing", []):
        if isinstance(item, dict):
            _update_leaderboard("typing", pet_id, item)
    for item in records.get("vocab", []):
        if isinstance(item, dict) and item.get("correct"):
            _update_leaderboard("vocab", pet_id, item)
    for item in records.get("rhyme", []):
        if isinstance(item, dict):
            _update_leaderboard("rhyme", pet_id, item)
    for item in records.get("music", []):
        if isinstance(item, dict):
            _update_leaderboard("music", pet_id, item)


def _format_leaderboard_line(bucket: str, rank: int, entry: dict, *, current_pet_id: int | None) -> tuple[str, str]:
    pid = entry.get("pet_id")
    tag = "（你）" if current_pet_id is not None and pid == current_pet_id else ""
    name = _format_pet_id(int(pid)) if pid is not None else "???? ????"
    fg = "#ffdd88" if tag else MENU_FG
    return f"{rank:>2}. {name}{tag}", fg


def _typing_grade(score: int) -> str:
    if score >= 20:
        return "S"
    if score >= 15:
        return "A"
    if score >= 10:
        return "B"
    if score >= 5:
        return "C"
    return "D"


def _typing_grade_info(score: int) -> tuple[str, str | None, float]:
    return _grade_info_from_tiers(score, TYPING_GRADE_TIERS)


def _rhythm_accuracy_pct(perfect: int, great: int, good: int, miss: int) -> float:
    total = perfect + great + good + miss
    if total <= 0:
        return 0.0
    return 100.0 * (perfect * 1.0 + great * 0.8 + good * 0.5) / total


def _rhythm_grade(perfect: int, great: int, good: int, miss: int) -> str:
    return _grade_from_tiers(_rhythm_accuracy_pct(perfect, great, good, miss), RHYTHM_GRADE_TIERS)


def _grade_from_tiers(value: float, tiers: tuple[tuple[str, int, str], ...]) -> str:
    current = tiers[0][0]
    for grade, threshold, _color in reversed(tiers):
        if value >= threshold:
            current = grade
            break
    return current


def _grade_info_from_tiers(
    value: float, tiers: tuple[tuple[str, int, str], ...]
) -> tuple[str, str | None, float]:
    current = tiers[0][0]
    for grade, threshold, _color in reversed(tiers):
        if value >= threshold:
            current = grade
            break
    next_grade: str | None = None
    progress = 1.0
    for i, (grade, threshold, _color) in enumerate(tiers):
        if grade != current:
            continue
        if i + 1 < len(tiers):
            next_grade, next_threshold, _ = tiers[i + 1]
            span = max(1, next_threshold - threshold)
            progress = min(1.0, (value - threshold) / span)
        break
    return current, next_grade, progress


def _draw_grade_bar(
    canvas: tk.Canvas,
    width: int,
    height: int,
    value: float,
    tiers: tuple[tuple[str, int, str], ...],
    *,
    unit: str = "分",
) -> None:
    canvas.delete("all")
    grade, next_grade, tier_progress = _grade_info_from_tiers(value, tiers)
    grade_colors = {g: c for g, _t, c in tiers}
    bar_top = 16
    bar_h = max(8, height - bar_top - 14)
    canvas.create_rectangle(0, bar_top, width, bar_top + bar_h, fill="#222233", outline="#666688", width=1)
    tier_count = len(tiers)
    max_v = max(1, tiers[-1][1])
    for i, (g, threshold, color) in enumerate(tiers):
        x = int(width * i / max(1, tier_count - 1))
        canvas.create_line(x, bar_top, x, bar_top + bar_h, fill="#444466")
        canvas.create_text(x, 6, text=g, fill=color, font=("Courier New", 8, "bold"))
    total_progress = min(1.0, float(value) / max_v)
    fill_w = max(0, int((width - 2) * total_progress))
    if fill_w > 0:
        canvas.create_rectangle(1, bar_top + 1, 1 + fill_w, bar_top + bar_h - 1, fill=grade_colors[grade], outline="")
    if next_grade:
        need = tiers[[t[0] for t in tiers].index(next_grade)][1] - value
        hint = f"评级 {grade}  {int(tier_progress * 100)}% → {next_grade}（还差 {max(0, int(need))}{unit}）"
    else:
        hint = f"评级 {grade}  满分！"
    canvas.create_text(
        width // 2,
        height - 2,
        text=hint,
        fill=MENU_FG,
        anchor=tk.S,
        font=("Courier New", 8, "bold"),
    )


def _draw_typing_grade_bar(canvas: tk.Canvas, width: int, height: int, score: int) -> None:
    _draw_grade_bar(canvas, width, height, float(score), TYPING_GRADE_TIERS, unit="分")


def _draw_rhythm_grade_bar(
    canvas: tk.Canvas, width: int, height: int, perfect: int, great: int, good: int, miss: int
) -> None:
    acc = _rhythm_accuracy_pct(perfect, great, good, miss)
    _draw_grade_bar(canvas, width, height, acc, RHYTHM_GRADE_TIERS, unit="%")


KEYBOARD_ROWS = ("1234567890", "QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM")


def _key_for_char(ch: str) -> str | None:
    if not ch:
        return None
    c = ch.lower()
    if c in "0123456789":
        return c
    if "a" <= c <= "z":
        return c.upper()
    return None


def _draw_typing_keyboard(canvas: tk.Canvas, width: int, height: int, highlight: str | None, phase: int) -> None:
    # 仅在高亮键变化时全量重绘；动画相位变化不重绘，减轻打字卡顿
    prev = getattr(canvas, "_kb_last_hl", object())
    if prev == highlight and getattr(canvas, "_kb_drawn", False):
        return
    canvas._kb_last_hl = highlight
    canvas._kb_drawn = True
    canvas.delete("all")
    px = max(2, width // 48)
    gap = px
    y0 = 4
    for row in KEYBOARD_ROWS:
        x0 = 4
        for ch in row:
            fill = "#444466"
            if highlight and ch == highlight:
                fill = "#66aaff"
            canvas.create_rectangle(x0, y0, x0 + px * 3, y0 + px * 3, fill=fill, outline="#666688")
            canvas.create_text(x0 + px * 1.5, y0 + px * 1.5, text=ch, fill="#eeeeee", font=("Courier New", max(7, px * 2), "bold"))
            x0 += px * 3 + gap
        y0 += px * 3 + gap


def _draw_like_glow(canvas: tk.Canvas, size: int, phase: int) -> None:
    canvas.delete("glow")
    cx = cy = size // 2
    px = max(3, size // 22)
    for ring in range(3):
        glow = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(phase * 0.18 + ring))
        r = int(size * (0.22 + ring * 0.08) * glow)
        col = ("#ffff88", "#ffcc66", "#ffaa88")[ring]
        _draw_pixel_ring(canvas, cx, cy, r, px, col)


def _draw_heart_wave(canvas: tk.Canvas, size: int, phase: int, *, clear: bool = True) -> None:
    if clear:
        canvas.delete("all")
    px = max(2, size // 28)
    cx = size // 2
    for i in range(3):
        spread = int((phase * 2 + i * 18) % (size // 2))
        col = ("#ff6688", "#ff88aa", "#ff4466")[i]
        _draw_pixel_heart(canvas, cx - px * 2 - spread, size // 3 - spread // 3, px=px, color=col)
        _draw_pixel_heart(canvas, cx + spread, size // 3 - spread // 3, px=px, color=col)


def _load_diary() -> list[dict]:
    if not DIARY_FILE.exists():
        return []
    try:
        data = json.loads(DIARY_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("entries"), list):
            return data["entries"]
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def _save_diary(entries: list[dict]) -> None:
    DIARY_FILE.write_text(
        json.dumps({"entries": entries}, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _parse_subtitle_text(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.isdigit():
            continue
        if "-->" in line:
            continue
        if line.startswith("WEBVTT"):
            continue
        cleaned = line
        if cleaned.startswith("{"):
            continue
        for sep in (r"\N", r"\n"):
            cleaned = cleaned.replace(sep, " ")
        tokens = []
        for part in cleaned.replace("，", " ").replace("。", " ").replace("！", " ").replace("？", " ").split():
            part = part.strip("[]()（）「」『』,.!?;:\"' ")
            if len(part) >= 2:
                tokens.append(part)
        lines.extend(tokens)
    return lines


_BANK_JSON_CACHE: dict[str, tuple[float, int, dict | list]] = {}
_TYPING_BANK_CACHE: dict[str, list[dict[str, str]]] = {}
_VOCAB_BANK_CACHE: dict[str, list[dict[str, str]]] = {}


def _read_bank_json(filename: str) -> dict | list | None:
    path = WORD_BANKS_DIR / filename
    if not path.exists():
        return None
    try:
        st = path.stat()
        key = str(path.resolve())
        sig = (st.st_mtime, st.st_size)
        cached = _BANK_JSON_CACHE.get(key)
        if cached and cached[0] == sig[0] and cached[1] == sig[1]:
            return cached[2]
        data = json.loads(path.read_text(encoding="utf-8"))
        _BANK_JSON_CACHE[key] = (sig[0], sig[1], data)
        return data
    except Exception:
        return None


def _sanitize_en_vocab_meaning(meaning: str) -> str:
    """去掉释义括号/方括号里的英文（避免背单词选项泄题）。"""
    m = str(meaning or "")
    m = re.sub(r"[（(][^）)]*[A-Za-z][^）)]*[）)]", "", m)
    m = re.sub(r"\[[^\]]*[A-Za-z][^\]]*\]", "", m)
    m = re.sub(r"(?i)English word:\s*\S+", "", m)
    m = re.sub(r"\s{2,}", " ", m).strip(" ；;，,、 ")
    return m or "常用词汇"


def _load_vocab_bank(lang: str) -> list[dict[str, str]]:
    if lang in _VOCAB_BANK_CACHE:
        return _VOCAB_BANK_CACHE[lang]
    fname = VOCAB_BANK_FILES.get(lang)
    if not fname:
        return []
    data = _read_bank_json(fname)
    if data is None:
        return []
    items = data if isinstance(data, list) else data.get("words", [])
    result: list[dict[str, str]] = []
    for item in items:
        if isinstance(item, dict) and item.get("word"):
            meaning = str(item.get("meaning", ""))
            if lang == "英语":
                meaning = _sanitize_en_vocab_meaning(meaning)
            result.append(
                {
                    "word": str(item["word"]),
                    "meaning": meaning,
                    "hint": str(item.get("hint", "")),
                    "lang": str(item.get("lang", lang)),
                }
            )
    _VOCAB_BANK_CACHE[lang] = result
    return result


def _load_typing_bank(lang: str) -> list[dict[str, str]]:
    """返回 [{display, target, romaji?}, ...]。日语 target 为假名，romaji 可作替代答案。"""
    if lang in _TYPING_BANK_CACHE:
        return _TYPING_BANK_CACHE[lang]
    fname = TYPING_BANK_FILES.get(lang)
    if not fname:
        return []
    data = _read_bank_json(fname)
    if data is None:
        return []
    items = data if isinstance(data, list) else data.get("items", [])
    pool: list[dict[str, str]] = []
    for item in items:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            pool.append({"display": str(item[0]), "target": str(item[1])})
        elif isinstance(item, dict) and item.get("display") and item.get("target"):
            entry = {"display": str(item["display"]), "target": str(item["target"])}
            if item.get("romaji"):
                entry["romaji"] = str(item["romaji"])
            pool.append(entry)
    _TYPING_BANK_CACHE[lang] = pool
    return pool


def _japanese_bank_available() -> bool:
    typing = _load_typing_bank(JAPANESE_LANG_LABEL)
    vocab = _load_vocab_bank(JAPANESE_LANG_LABEL)
    return len(typing) >= 4 or len(vocab) >= 4


def _romaji_letters_only(text: str) -> str:
    """罗马音答案：仅保留 a-z，去掉空格/连字符/长音符号等。"""
    return "".join(ch for ch in str(text).lower() if "a" <= ch <= "z")


def _kana_to_hiragana(text: str) -> str:
    out: list[str] = []
    for ch in text:
        code = ord(ch)
        if 0x30A1 <= code <= 0x30F6:  # 片假名 → 平假名
            out.append(chr(code - 0x60))
        else:
            out.append(ch)
    return "".join(out)


def _kana_to_katakana(text: str) -> str:
    out: list[str] = []
    for ch in text:
        code = ord(ch)
        if 0x3041 <= code <= 0x3096:  # 平假名 → 片假名
            out.append(chr(code + 0x60))
        else:
            out.append(ch)
    return "".join(out)


def _jp_typing_prompt_meaning(display: str) -> str:
    """从 display（如 后天（あさって））取出中文提示。"""
    s = str(display or "").strip()
    if "（" in s and s.endswith("）"):
        return s.rsplit("（", 1)[0].strip() or s
    if "(" in s and s.endswith(")"):
        return s.rsplit("(", 1)[0].strip() or s
    return s


def _filter_jp_typing_pool(pool: list[dict[str, str]], jp_mode: str) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for it in pool:
        kana = str(it.get("target", "") or "").strip()
        roma = _romaji_letters_only(it.get("romaji", "") or "")
        if jp_mode == JP_TYPING_MODE_ROMAJI:
            if len(roma) < 2:
                continue
            result.append({**it, "romaji": roma, "target": kana or it.get("target", "")})
        else:
            if not kana:
                continue
            result.append({**it, "romaji": roma})
    return result


def _load_vocab() -> list[dict[str, str]]:
    merged: list[dict[str, str]] = []
    for lang in VOCAB_BANK_FILES:
        merged.extend(_load_vocab_bank(lang))
    if not merged:
        merged = list(DEFAULT_VOCAB_WORDS)
    dedup: dict[str, dict[str, str]] = {}
    for item in merged:
        w = item.get("word", "").strip()
        if w:
            dedup[w] = item
    return list(dedup.values())


def _save_vocab(words: list[dict[str, str]]) -> None:
    VOCAB_FILE.write_text(
        json.dumps({"words": words}, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _empty_vocab_notebook() -> dict[str, list[dict[str, str]]]:
    return {"中文": [], "英语": [], "日语": []}


def _load_vocab_notebook() -> dict[str, list[dict[str, str]]]:
    data = _empty_vocab_notebook()
    if not VOCAB_NOTEBOOK_FILE.exists():
        return data
    try:
        raw = json.loads(VOCAB_NOTEBOOK_FILE.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return data
        for lang in data:
            rows = raw.get(lang, [])
            if not isinstance(rows, list):
                continue
            cleaned: list[dict[str, str]] = []
            seen: set[str] = set()
            for item in rows:
                if not isinstance(item, dict):
                    continue
                word = str(item.get("word", "")).strip()
                if not word or word in seen:
                    continue
                seen.add(word)
                cleaned.append(
                    {
                        "word": word,
                        "meaning": str(item.get("meaning", "")),
                        "hint": str(item.get("hint", "")),
                        "lang": str(item.get("lang", lang)),
                    }
                )
            data[lang] = cleaned
    except Exception:
        pass
    return data


def _save_vocab_notebook(book: dict[str, list[dict[str, str]]]) -> None:
    payload = _empty_vocab_notebook()
    for lang in payload:
        rows = book.get(lang, []) if isinstance(book, dict) else []
        payload[lang] = rows if isinstance(rows, list) else []
    VOCAB_NOTEBOOK_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _add_vocab_notebook_item(lang: str, item: dict) -> bool:
    """答错加入生词本。已存在则更新词义，返回是否为新增。"""
    if lang not in ("中文", "英语", "日语"):
        return False
    word = str(item.get("word", "")).strip()
    if not word:
        return False
    book = _load_vocab_notebook()
    rows = book.get(lang, [])
    for row in rows:
        if row.get("word") == word:
            row["meaning"] = str(item.get("meaning", row.get("meaning", "")))
            row["hint"] = str(item.get("hint", row.get("hint", "")))
            row["lang"] = lang
            _save_vocab_notebook(book)
            return False
    rows.append(
        {
            "word": word,
            "meaning": str(item.get("meaning", "")),
            "hint": str(item.get("hint", "")),
            "lang": lang,
        }
    )
    book[lang] = rows
    _save_vocab_notebook(book)
    return True


def _remove_vocab_notebook_item(lang: str, word: str) -> None:
    book = _load_vocab_notebook()
    rows = [r for r in book.get(lang, []) if r.get("word") != word]
    book[lang] = rows
    _save_vocab_notebook(book)


def _clear_vocab_notebook_lang(lang: str) -> None:
    book = _load_vocab_notebook()
    book[lang] = []
    _save_vocab_notebook(book)


def _mood_tier_label(mood: int) -> tuple[str, str]:
    for threshold, label, color in MOOD_TIER_LABELS:
        if mood >= threshold:
            return label, color
    return MOOD_TIER_LABELS[-1][1], MOOD_TIER_LABELS[-1][2]


def _draw_stamina_pixel_icon(canvas: tk.Canvas, size: int) -> None:
    canvas.delete("all")
    px = max(3, size // 7)
    ox = (size - px * 5) // 2
    oy = (size - px * 6) // 2
    canvas.create_rectangle(ox + px, oy, ox + px * 4, oy + px, fill="#aaffaa", outline="")
    canvas.create_rectangle(ox + px * 2, oy, ox + px * 3, oy + px * 6, fill="#44cc44", outline="")
    canvas.create_rectangle(ox, oy + px * 2, ox + px * 5, oy + px * 3, fill="#66dd66", outline="")
    canvas.create_rectangle(ox + px, oy + px * 4, ox + px * 4, oy + px * 5, fill="#338833", outline="")


def _draw_mood_pixel_icon(canvas: tk.Canvas, size: int, *, fill: str = "#ff6688") -> None:
    canvas.delete("all")
    px = max(3, size // 7)
    cx, cy = size // 2, size // 2 + px // 2
    light = "#ff99bb" if fill == "#ff6688" else fill
    canvas.create_rectangle(cx - px * 2, cy - px, cx, cy + px, fill=light, outline="")
    canvas.create_rectangle(cx, cy - px, cx + px * 2, cy + px, fill=light, outline="")
    canvas.create_rectangle(cx - px, cy - px * 2, cx + px, cy - px, fill=fill, outline="")
    canvas.create_rectangle(cx - px, cy, cx + px, cy + px * 2, fill=fill, outline="")


def _draw_panel_bar(canvas: tk.Canvas, value: int, color: str, *, width: int = PANEL_BAR_W, height: int = PANEL_BAR_H) -> None:
    canvas.delete("all")
    px = 4
    segments = max(1, width // px)
    filled = max(0, min(segments, int(round(segments * value / 100))))
    bg = "#2a2a2a"
    border = "#555555"
    canvas.create_rectangle(0, 0, width, height, fill=bg, outline=border, width=1)
    for i in range(segments):
        x0 = i * px + 1
        x1 = min(width - 1, x0 + px - 1)
        if i >= filled:
            chunk = "#333333" if i % 2 == 0 else "#2e2e2e"
        else:
            chunk = color if i % 2 == 0 else color
            if i % 3 == 1:
                r, g, b = _hex_to_rgb(color)
                chunk = f"#{min(255, r + 22):02x}{min(255, g + 22):02x}{min(255, b + 22):02x}"
        canvas.create_rectangle(x0, 2, x1, height - 2, fill=chunk, outline="")


def _draw_pixel_food(canvas: tk.Canvas, food_id: str, x: int, y: int, px: int = 4) -> None:
    if food_id == "bread":
        canvas.create_rectangle(x, y + px, x + px * 4, y + px * 3, fill="#d4a056", outline="")
        canvas.create_rectangle(x + px, y, x + px * 3, y + px, fill="#e8b870", outline="")
    elif food_id == "apple":
        canvas.create_oval(x, y + px, x + px * 3, y + px * 4, fill="#ee4444", outline="")
        canvas.create_rectangle(x + px, y, x + px * 2, y + px, fill="#66aa33", outline="")
    elif food_id == "cake":
        canvas.create_rectangle(x, y + px * 2, x + px * 4, y + px * 4, fill="#ff88cc", outline="")
        canvas.create_rectangle(x + px, y + px, x + px * 3, y + px * 2, fill="#ffcc66", outline="")
        canvas.create_rectangle(x + px * 2, y, x + px * 3, y + px, fill="#ff4466", outline="")
    elif food_id == "fish":
        canvas.create_polygon(
            x,
            y + px * 2,
            x + px * 4,
            y + px,
            x + px * 4,
            y + px * 3,
            fill="#88bbee",
            outline="",
        )
        canvas.create_rectangle(x + px, y + px, x + px * 2, y + px * 2, fill="#ffffff", outline="")
    elif food_id == "onigiri":
        canvas.create_polygon(
            x + px * 2,
            y,
            x + px * 4,
            y + px * 4,
            x,
            y + px * 4,
            fill="#f5f5ee",
            outline="",
        )
        canvas.create_rectangle(x + px, y + px * 2, x + px * 3, y + px * 3, fill="#224422", outline="")
    elif food_id == "candy":
        canvas.create_rectangle(x + px, y + px, x + px * 3, y + px * 3, fill="#ff6688", outline="")
        canvas.create_rectangle(x + px * 2, y, x + px * 3, y + px * 4, fill="#ffcc44", outline="")
    elif food_id == "tea":
        canvas.create_rectangle(x, y + px * 2, x + px * 4, y + px * 4, fill="#cc8844", outline="")
        canvas.create_rectangle(x + px, y + px, x + px * 3, y + px * 2, fill="#aa6633", outline="")
        canvas.create_rectangle(x + px * 2, y, x + px * 3, y + px, fill="#cccccc", outline="")
    elif food_id == "meat":
        canvas.create_oval(x, y + px, x + px * 4, y + px * 3, fill="#cc5533", outline="")
        canvas.create_rectangle(x + px, y + px * 2, x + px * 3, y + px * 3, fill="#aa3322", outline="")
    elif food_id == "berry":
        canvas.create_polygon(
            x + px * 2,
            y,
            x + px * 4,
            y + px * 2,
            x + px * 3,
            y + px * 4,
            x + px,
            y + px * 4,
            x,
            y + px * 2,
            fill="#ee3355",
            outline="",
        )
        canvas.create_rectangle(x + px, y, x + px * 2, y + px, fill="#66aa33", outline="")
    elif food_id == "donut":
        canvas.create_oval(x, y + px, x + px * 4, y + px * 4, fill="#d4a056", outline="")
        canvas.create_oval(x + px, y + px * 2, x + px * 3, y + px * 3, fill="#111122", outline="")
        canvas.create_arc(x, y + px, x + px * 4, y + px * 3, start=0, extent=180, fill="#ff88cc", outline="")


def _pick_game_drop_kind() -> tuple[str, str | None]:
    r = random.random()
    if r >= 1.0 - GAME_SPECIAL_DROP_CHANCE:
        special = random.choices(
            ("time_minus", "dizzy", "time_plus"),
            weights=(GAME_TIME_MINUS_WEIGHT, GAME_DIZZY_WEIGHT, GAME_TIME_PLUS_WEIGHT),
            k=1,
        )[0]
        return special, None
    return "food", random.choice(list(FOODS.keys()))


def _draw_game_special_item(canvas: tk.Canvas, kind: str, size: int) -> None:
    px = max(4, size // 8)
    cx, cy = size // 2, size // 2
    pad = px
    if kind == "time_plus":
        canvas.create_rectangle(pad, pad, size - pad, size - pad, fill="#1a3344", outline="#66ddff", width=2)
        canvas.create_text(cx, cy, text="+3s", fill="#88ffdd", font=("Courier New", max(8, px * 2), "bold"))
    elif kind == "time_minus":
        canvas.create_rectangle(pad, pad, size - pad, size - pad, fill="#3a1a1a", outline="#ff8888", width=2)
        canvas.create_text(cx, cy, text="-3s", fill="#ffaaaa", font=("Courier New", max(8, px * 2), "bold"))
    elif kind == "dizzy":
        canvas.create_rectangle(pad, pad, size - pad, size - pad, fill="#2a2244", outline="#ffcc44", width=2)
        for i in range(3):
            ang = i * 2.1
            sx = cx + int(math.cos(ang) * px * 2.2)
            sy = cy + int(math.sin(ang) * px * 2.2)
            _draw_pixel_star(canvas, sx - px, sy - px, px=max(2, px - 1), color="#ffff66")


class SpriteSet:
    def __init__(self, display_size: int) -> None:
        self.display_size = display_size
        self.stand: ImageTk.PhotoImage
        self.stand_angry: ImageTk.PhotoImage
        self.stand_question: ImageTk.PhotoImage
        self.happy: ImageTk.PhotoImage
        self.sleep: tuple[ImageTk.PhotoImage, ImageTk.PhotoImage]
        self.front: tuple[ImageTk.PhotoImage, ImageTk.PhotoImage]
        self.back: tuple[ImageTk.PhotoImage, ImageTk.PhotoImage]
        self.left: tuple[ImageTk.PhotoImage, ImageTk.PhotoImage]
        self.right: tuple[ImageTk.PhotoImage, ImageTk.PhotoImage]
        self.move: tuple[ImageTk.PhotoImage, ImageTk.PhotoImage, ImageTk.PhotoImage]
        self.work_front: tuple[ImageTk.PhotoImage, ImageTk.PhotoImage]
        self.work_back: tuple[ImageTk.PhotoImage, ImageTk.PhotoImage]
        self.work_left: tuple[ImageTk.PhotoImage, ImageTk.PhotoImage]
        self.work_right: tuple[ImageTk.PhotoImage, ImageTk.PhotoImage]
        self.work_stand: ImageTk.PhotoImage
        self.box_img: ImageTk.PhotoImage
        self.flag_img: ImageTk.PhotoImage
        self.kick: ImageTk.PhotoImage
        self.shy: tuple[ImageTk.PhotoImage, ImageTk.PhotoImage]
        self.wink: ImageTk.PhotoImage
        self.like: ImageTk.PhotoImage
        self.sad1: ImageTk.PhotoImage
        self.sad2: ImageTk.PhotoImage
        self.yes: ImageTk.PhotoImage
        self.no: ImageTk.PhotoImage
        self.eat2_only: ImageTk.PhotoImage
        self.music_stand: ImageTk.PhotoImage
        self.music_front: tuple[ImageTk.PhotoImage, ImageTk.PhotoImage]
        self.music_back: tuple[ImageTk.PhotoImage, ImageTk.PhotoImage]
        self.music_left: tuple[ImageTk.PhotoImage, ImageTk.PhotoImage]
        self.music_right: tuple[ImageTk.PhotoImage, ImageTk.PhotoImage]
        self.actions: dict[str, tuple[ImageTk.PhotoImage, ...]]
        self.reload()

    @classmethod
    def from_pack(cls, display_size: int, pack: dict) -> "SpriteSet":
        ss = cls.__new__(cls)
        ss.display_size = display_size
        ss._apply_pack(pack)
        return ss

    def _apply_pack(self, pack: dict) -> None:
        photos = {key: ImageTk.PhotoImage(img) for key, img in _sprite_photo_tasks(pack)}
        _bind_sprite_photos(self, photos, pack)

    def _load(
        self, filename: str, reference_scale: float, *, flip: bool = False, prop_size: int | None = None
    ) -> ImageTk.PhotoImage:
        size = prop_size if prop_size is not None else self.display_size
        canvas = _get_processed_canvas(filename, size, reference_scale, flip=flip)
        return ImageTk.PhotoImage(canvas)

    def reload(self) -> None:
        self._apply_pack(_build_sprite_pack(self.display_size))


def _build_sprite_pack(display_size: int) -> dict:
    ref = _reference_scale(display_size)
    prop_ref = ref * WORK_PROP_SIZE / display_size

    def load_img(
        filename: str,
        *,
        flip: bool = False,
        prop_size: int | None = None,
        scale: float | None = None,
    ) -> Image.Image:
        size = prop_size if prop_size is not None else display_size
        use_scale = scale if scale is not None else (prop_ref if prop_size else ref)
        return _get_processed_canvas(filename, size, use_scale, flip=flip)

    stand_canvas = load_img("stand.jpg")
    return {
        "stand": stand_canvas,
        "stand_angry": _add_sticker(stand_canvas, "angry"),
        "stand_question": _add_sticker(stand_canvas, "question"),
        "stand_like": _add_sticker(stand_canvas, "like"),
        "happy": load_img("happy.jpg"),
        "sleep": (load_img("sleep1.jpg"), load_img("sleep2.jpg")),
        "front": (load_img("walkfront1.jpg"), load_img("walkfront2.jpg")),
        "back": (load_img("walkback1.jpg"), load_img("walkback2.jpg")),
        "left": (load_img("walkleft1.jpg"), load_img("walkleft2.jpg")),
        "right": (load_img("walkleft1.jpg", flip=True), load_img("walkleft2.jpg", flip=True)),
        "move": (load_img("move1.jpg"), load_img("move2.jpg"), load_img("move3.jpg")),
        "work_front": (load_img("workfront1.jpg"), load_img("workfront2.jpg")),
        "work_back": (load_img("workback1.jpg"), load_img("workback2.jpg")),
        "work_left": (load_img("workleft1.jpg"), load_img("workleft2.jpg")),
        "work_right": (load_img("workleft1.jpg", flip=True), load_img("workleft2.jpg", flip=True)),
        "work_stand": load_img("workstand.jpg"),
        "box_img": load_img("box.jpg", prop_size=WORK_PROP_SIZE, scale=prop_ref),
        "flag_img": load_img("flag.jpg", prop_size=WORK_PROP_SIZE, scale=prop_ref),
        "kick": load_img("kick.jpg"),
        "shy": (load_img("shy1.jpg"), load_img("shy2.jpg")),
        "wink": load_img("wink.jpg"),
        "like": load_img("like.jpg"),
        "sad1": load_img("sad1.jpg"),
        "sad2": load_img("sad2.jpg"),
        "yes": load_img("yes.jpg"),
        "no": load_img("no.jpg"),
        "eat2_only": load_img("eat2.jpg"),
        "music_stand": load_img("musicstand.jpg"),
        "music_front": (load_img("musicfront1.jpg"), load_img("musicfront2.jpg")),
        "music_back": (load_img("musicback1.jpg"), load_img("musicback2.jpg")),
        "music_left": (load_img("musicleft1.jpg"), load_img("musicleft2.jpg")),
        "music_right": (load_img("musicleft1.jpg", flip=True), load_img("musicleft2.jpg", flip=True)),
        "actions": {
            name: tuple(load_img(file) for file in files) for name, files in SELECT_ACTIONS.items()
        },
    }


def _sprite_photo_tasks(pack: dict) -> list[tuple[str, Image.Image]]:
    tasks: list[tuple[str, Image.Image]] = []
    singles = (
        "stand",
        "stand_angry",
        "stand_question",
        "stand_like",
        "happy",
        "work_stand",
        "box_img",
        "flag_img",
        "kick",
        "wink",
        "like",
        "sad1",
        "sad2",
        "yes",
        "no",
        "eat2_only",
        "music_stand",
    )
    for key in singles:
        tasks.append((key, pack[key]))
    for key in (
        "sleep",
        "front",
        "back",
        "left",
        "right",
        "work_front",
        "work_back",
        "work_left",
        "work_right",
        "shy",
        "music_front",
        "music_back",
        "music_left",
        "music_right",
    ):
        a, b = pack[key]
        tasks.append((f"{key}.0", a))
        tasks.append((f"{key}.1", b))
    move_a, move_b, move_c = pack["move"]
    tasks.extend([("move.0", move_a), ("move.1", move_b), ("move.2", move_c)])
    for name, images in pack["actions"].items():
        for i, img in enumerate(images):
            tasks.append((f"actions.{name}.{i}", img))
    tasks.sort(key=lambda item: (0 if item[0] == "stand" else 1, item[0]))
    return tasks


def _bind_sprite_photos(ss: "SpriteSet", photos: dict[str, ImageTk.PhotoImage], pack: dict) -> None:
    def pair(key: str) -> tuple[ImageTk.PhotoImage, ImageTk.PhotoImage]:
        return photos[f"{key}.0"], photos[f"{key}.1"]

    def triple(key: str) -> tuple[ImageTk.PhotoImage, ImageTk.PhotoImage, ImageTk.PhotoImage]:
        return photos[f"{key}.0"], photos[f"{key}.1"], photos[f"{key}.2"]

    ss.stand = photos["stand"]
    ss.stand_angry = photos["stand_angry"]
    ss.stand_question = photos["stand_question"]
    ss.stand_like = photos["stand_like"]
    ss.happy = photos["happy"]
    ss.sleep = pair("sleep")
    ss.front = pair("front")
    ss.back = pair("back")
    ss.left = pair("left")
    ss.right = pair("right")
    ss.move = triple("move")
    ss.work_front = pair("work_front")
    ss.work_back = pair("work_back")
    ss.work_left = pair("work_left")
    ss.work_right = pair("work_right")
    ss.work_stand = photos["work_stand"]
    ss.box_img = photos["box_img"]
    ss.flag_img = photos["flag_img"]
    ss.kick = photos["kick"]
    ss.shy = pair("shy")
    ss.wink = photos["wink"]
    ss.like = photos["like"]
    ss.sad1 = photos["sad1"]
    ss.sad2 = photos["sad2"]
    ss.yes = photos["yes"]
    ss.no = photos["no"]
    ss.eat2_only = photos["eat2_only"]
    ss.music_stand = photos["music_stand"]
    ss.music_front = pair("music_front")
    ss.music_back = pair("music_back")
    ss.music_left = pair("music_left")
    ss.music_right = pair("music_right")
    ss.actions = {
        name: tuple(photos[f"actions.{name}.{i}"] for i in range(len(pack["actions"][name])))
        for name in pack["actions"]
    }


class DesktopPet:
    DIRECTIONS = ("front", "back", "left", "right")
    DELTAS = {
        "front": (0, MOVE_STEP),
        "back": (0, -MOVE_STEP),
        "left": (-MOVE_STEP, 0),
        "right": (MOVE_STEP, 0),
    }
    FOLLOW_DELTAS = {
        "front": (0, FOLLOW_MOVE_STEP),
        "back": (0, -FOLLOW_MOVE_STEP),
        "left": (-FOLLOW_MOVE_STEP, 0),
        "right": (FOLLOW_MOVE_STEP, 0),
    }

    def __init__(self) -> None:
        _ensure_data_dirs()
        app_cfg = _load_app_config()
        _apply_font_size(int(app_cfg.get("font_size", 12)))
        saved_size = int(app_cfg.get("display_size", DEFAULT_SIZE))
        self.display_size = saved_size if saved_size in SIZE_PRESETS.values() else DEFAULT_SIZE
        self.font_size = int(app_cfg.get("font_size", 12))
        self.app_config = app_cfg
        self.pet_profile = _load_pet_profile()
        self.pet_id = self.pet_profile.get("pet_id", 0) if PET_ID_FEATURE else None
        self.diary_entries = _load_diary()
        self.vocab_words: list[dict[str, str]] = []
        self.ai_history: list[dict[str, str]] = []
        self.difficulty = self.app_config.get("difficulty", "中")
        if self.difficulty not in DIFFICULTY_PRESETS:
            self.difficulty = "中"
        self._mood_decay_counter = 0
        self._apply_difficulty_runtime()

        self.root = tk.Tk()
        self.root.title("Vpet")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.config(bg="magenta")
        self.root.wm_attributes("-transparentcolor", "magenta")

        self._sprite_cache: dict[int, SpriteSet] = {}
        self._sprite_building: set[int] = set()
        self._panel_backpack_sig: tuple | None = None
        self._panel_sticky_pos: tuple[int, int] | None = None
        self._panel_reposition_ms = 0
        self._drag_handle_cache: dict[int, tuple[int, int, int, int]] = {}
        self._startup_ready = False
        self._startup_loading_active = True
        self._startup_loading_phase = 0
        self._startup_loading_start_ms = int(time.time() * 1000)
        self._startup_sprite_pack: dict | None = None
        self._startup_vocab_words: list[dict[str, str]] | None = None
        self._startup_load_error = False
        self._startup_anim_job: str | None = None

        self.label = tk.Label(self.root, bg="magenta", bd=0)
        self.label.pack()
        self._startup_canvas = tk.Canvas(
            self.root,
            width=self.display_size,
            height=self.display_size,
            bg="magenta",
            highlightthickness=0,
        )
        self._startup_canvas.place(x=0, y=0, width=self.display_size, height=self.display_size)
        _draw_size_loading_frame(self._startup_canvas, self.display_size, 0, simple=True)
        self.sprites: SpriteSet | None = None
        self.root.update_idletasks()
        self.root.update()

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.x = random.randint(0, max(0, screen_w - self.display_size))
        self.y = random.randint(0, max(0, screen_h - self.display_size))

        self.state = "stand"
        self.direction = "front"
        self.walk_frame = 0
        self.walk_steps_left = 0
        self.action_name = ""
        self.action_frame = 0
        self.happy_step_idx = 0
        self.happy_base_y = 0

        self.stamina = 80
        self.mood = 70
        self.mode = "free"  # free | stroll | follow | quiet(睡眠) | game | work
        self.mode_switch_job: str | None = None
        self.mode_switch_token = 0
        self.follow_animating = False
        self.follow_tick_job: str | None = None
        self.follow_anim_job: str | None = None
        self.work_animating = False
        self.rest_base_y = 0
        self.rest_bobble_job: str | None = None
        self.sleep_in_deep = False
        self.sleep_from_interact = False
        self.sleep_forced = False
        self.sleep_deep_end_ms = 0
        self.last_hunger_reminder_ms = 0
        self.last_follow_wait_ms = 0
        self.speech_hide_job: str | None = None
        self.speech_type_job: str | None = None
        self.speech_label: tk.Label | None = None
        self.speech_full_text = ""
        self.speech_on_complete = None
        self.speech_type_ms = TYPEWRITER_MS
        self.panel_hide_job: str | None = None
        self.action_end_job: str | None = None
        self.action_defer_job: str | None = None
        self._wink_restore_free = False
        self.call_audio_ms = 0

        self.game_overlay: tk.Toplevel | None = None
        self.game_canvas: tk.Canvas | None = None
        self.game_boxes: list[dict] = []
        self.game_score = 0
        self.game_catches = 0
        self.game_misses = 0
        self.game_session_food: dict[str, int] = {}
        self.game_start_ms = 0
        self.game_spawn_job: str | None = None
        self.game_tick_job: str | None = None
        self.game_hud_win: tk.Toplevel | None = None
        self.game_hud_label: tk.Label | None = None
        self.game_dizzy = False
        self.game_stunned_until_ms = 0
        self.game_dizzy_job: str | None = None

        self.work_overlay: tk.Toplevel | None = None
        self.work_canvas: tk.Canvas | None = None
        self.work_start_x = 0
        self.work_start_y = 0
        self.work_end_x = 0
        self.work_end_y = 0
        self.work_total = 0
        self.work_delivered = 0
        self.work_stack = 0
        self.work_has_start_box = False
        self.work_carrying = False
        self.work_phase = ""
        self.work_use_work_sprites = False
        self.work_start_box_win: tk.Toplevel | None = None
        self.work_end_btn_win: tk.Toplevel | None = None
        self.work_flag_dragging = False
        self.work_flag_drag_origin: tuple[int, int, int, int] = (0, 0, 0, 0)
        self.work_flag_movable = False
        self.work_custom_win: tk.Toplevel | None = None
        self.work_continuous = False
        self.work_encourage_job: str | None = None
        self.work_boxes_since_banter = 0
        self.work_banter_last_ms = 0
        self.work_anchored_box_wins: list[tk.Toplevel] = []
        self.work_local_stack = 0

        self.rhythm_win: tk.Toplevel | None = None
        self.rhythm_canvas: tk.Canvas | None = None
        self.rhythm_job: str | None = None
        self.rhythm_active = False
        self.rhythm_resume_music = False
        self.rhythm_notes: list[dict] = []
        self.rhythm_start_ms = 0
        self.rhythm_end_ms = 0
        self.rhythm_score = 0
        self.rhythm_combo = 0
        self.rhythm_max_combo = 0
        self.rhythm_perfect = 0
        self.rhythm_great = 0
        self.rhythm_good = 0
        self.rhythm_miss = 0
        self.rhythm_judgment = ""
        self.rhythm_flash: dict[int, int] = {}
        self.rhythm_track_id = DEFAULT_MUSIC_TRACK
        self.rhythm_grade_bar: tk.Canvas | None = None
        self.rhythm_keys_down: set[int] = set()
        self.rhythm_settings_win: tk.Toplevel | None = None
        self.rhythm_travel_ms = RHYTHM_TRAVEL_MS

        self.drag_x = 0
        self.drag_y = 0
        self.dragging = False
        self.drag_move_job: str | None = None
        self.drag_move_start_ms = 0
        self.drag_track_x = 0
        self.drag_track_y = 0
        self.drag_last_dir = ""
        self.drag_spin_dir = 0
        self.drag_spin_steps = 0
        self.drag_dizzy = False
        self.drag_dizzy_dialog_ms = 0
        self.drag_dizzy_extra_spins = 0
        self.drag_handle = (0, 0, self.display_size, self.display_size)
        self._drag_handle_cache[self.display_size] = self.drag_handle
        self.click_bounce_offset = 0
        self.click_bouncing = False
        self.rest_click_count = 0
        self.rest_last_click_ms = 0
        self.rest_peek_job: str | None = None
        self.hotkey_ids: list[int] = []

        self.menu_bar: tk.Toplevel | None = None
        self.sub_menu: tk.Toplevel | None = None
        self.menu_hide_job: str | None = None
        self._pet_menu_follow_ms = 0
        self._pet_speech_follow_ms = 0
        self._pet_menu_follow_job: str | None = None
        self.panel_win: tk.Toplevel | None = None
        self.panel_backpack_win: tk.Toplevel | None = None
        self.backpack_icons_frame: tk.Frame | None = None
        self.backpack_grid: tk.Frame | None = None
        self.backpack_scroll_inner: tk.Frame | None = None
        self.speech_dialog: tk.Toplevel | None = None
        self.toast_win: tk.Toplevel | None = None
        self.countdown_win: tk.Toplevel | None = None
        self.countdown_label: tk.Label | None = None
        self.happy_fx_win: tk.Toplevel | None = None
        self.happy_fx_canvas: tk.Canvas | None = None
        self.food_fx_win: tk.Toplevel | None = None
        self.food_fx_canvas: tk.Canvas | None = None
        self.food_fx_id: str | None = None
        self.food_inventory: dict[str, int] = _load_food_inventory()
        self.shy_frame_idx = 0
        self.shy_last_click_ms = 0
        self.kick_base_y = 0
        self.angry_anim_job: str | None = None
        self.expose_qte_win: tk.Toplevel | None = None
        self.expose_qte_canvas: tk.Canvas | None = None
        self.expose_qte_active = False
        self.expose_anim_job: str | None = None
        self.expose_qte_angle = 0.0
        self.expose_blue_start = 0.0
        self.expose_qte_done = False
        self.expose_glitch_win: tk.Toplevel | None = None
        self.expose_glitch_canvas: tk.Canvas | None = None
        self.expose_glitch_phase = 0
        self.expose_glitch_job: str | None = None
        self.expose_glitch_message = ""
        self.expose_hit_streak = 0
        self.expose_session_active = False
        self.expose_enter_armed = False
        self.expose_enter_was_down = False
        self.expose_pointer_base_speed = EXPOSE_POINTER_SPEED
        self.game_clear_win: tk.Toplevel | None = None
        self.game_clear_canvas: tk.Canvas | None = None
        self.game_clear_job: str | None = None
        self.game_clear_token = 0
        self._vocab_streak = 0
        self.face_click_pending_ms = 0
        self.face_dclick_combos = 0
        self.face_dclick_last_combo_ms = 0
        self._closing = False
        self.yesno_overlay_win: tk.Toplevel | None = None
        self.yesno_reveal_job: str | None = None
        self.music_sprite_mode = False
        self.music_wave_win: tk.Toplevel | None = None
        self.music_wave_canvas: tk.Canvas | None = None
        self.music_wave_phase = 0
        self.bg_music_playing = False
        self.bg_music_paused_for_call = False
        self.bg_music_play_index = 0
        self.bg_music_watch_job: str | None = None
        self.music_config = _load_music_config()
        self.root.after(200, lambda: threading.Thread(target=_ensure_all_music_track_wavs, daemon=True).start())
        self.music_settings_win: tk.Toplevel | None = None
        self.sound_settings_win: tk.Toplevel | None = None
        self.sleep_zzz_win: tk.Toplevel | None = None
        self.sleep_zzz_canvas: tk.Canvas | None = None
        self.zzz_phase = 0

        self.rain_fx_win: tk.Toplevel | None = None
        self.rain_fx_canvas: tk.Canvas | None = None
        self.rain_drops: list[dict] = []
        self.rain_phase = 0

        self.like_fx_win: tk.Toplevel | None = None
        self.like_fx_canvas: tk.Canvas | None = None
        self.like_glow_job: str | None = None
        self.like_glow_phase = 0
        self.wink_fx_win: tk.Toplevel | None = None
        self.wink_fx_canvas: tk.Canvas | None = None
        self.wink_fx_job: str | None = None
        self.wink_fx_phase = 0
        self.wink_fx_started_ms = 0
        self.multi_click_count = 0
        self.multi_click_last_ms = 0
        self.multi_click_key = ""
        self.work_nav_shown = False
        self.typing_game_job: str | None = None
        self.interact_fx_win: tk.Toplevel | None = None
        self.interact_fx_canvas: tk.Canvas | None = None
        self.interact_fx_action = ""
        self.interact_fx_phase = 0
        self.interact_fx_stop_job: str | None = None
        self.move_land_base_y = 0
        self.food_drag_win: tk.Toplevel | None = None
        self.food_drag_canvas: tk.Canvas | None = None
        self.food_drag_id: str | None = None
        self.food_drag_active = False
        self.angry_base_y = 0
        self.angry_lift_offset = 0
        self.angry_walk_phase = False
        self.interaction_token = 0
        self.idle_job: str | None = None
        self.idle_watchdog_job: str | None = None
        self.walk_move_job: str | None = None
        self.walk_anim_job: str | None = None
        self.action_anim_job: str | None = None
        self.move_land_job: str | None = None
        self.food_fx_job: str | None = None
        self.happy_job: str | None = None
        self.sleep_interact_active = False
        self.sleep_interact_end_job: str | None = None
        self.follow_last_dir = ""
        self.follow_dir_change_times: list[int] = []
        self.follow_spin_dir = 0
        self.follow_spin_steps = 0
        self.follow_dizzy = False
        self.follow_dizzy_job: str | None = None
        self.follow_dizzy_fx_win: tk.Toplevel | None = None
        self.follow_dizzy_fx_canvas: tk.Canvas | None = None
        self.follow_dizzy_fx_phase = 0
        self.follow_dizzy_fx_job: str | None = None
        self.shy_fx_win: tk.Toplevel | None = None
        self.shy_fx_canvas: tk.Canvas | None = None
        self.game_near_food = False
        self.bulb_glow_phase = 0
        self.bulb_glow_job: str | None = None
        self.mini_pets: list[dict] = []
        self.companion_bar_enabled = False
        self._mini_pet_sprite_cache: dict[int, dict] = {}
        self.sad_phase = ""
        self.size_loading_active = False
        self.size_loading_win: tk.Toplevel | None = None
        self.size_loading_canvas: tk.Canvas | None = None
        self.size_loading_job: str | None = None
        self.size_loading_phase = 0
        self.size_loading_preset = ""
        self.size_loading_target = 0
        self.size_loading_start_ms = 0
        self.size_loading_preload_started = False
        self.size_loading_was_cached = False
        self.companion_loading_win: tk.Toplevel | None = None
        self.companion_loading_canvas: tk.Canvas | None = None
        self.companion_loading_job: str | None = None
        self.companion_loading_phase = 0
        self.companion_loading_start_ms = 0
        self.companion_loading_callback = None
        self.companion_loading_active = False
        self.companion_loading_was_cached = False
        self.wait_hint_win: tk.Toplevel | None = None
        self.wait_hint_main_label: tk.Label | None = None
        self.wait_hint_job: str | None = None
        self.wait_hint_phase = 0
        self.wait_hint_reason = ""
        self._ui_busy_depth = 0
        self._ui_heartbeat_ms = 0
        self._ui_heartbeat_job: str | None = None
        self._ui_lag_detected = False
        self._mouse_over_pet = False
        self.bulb_fx_win: tk.Toplevel | None = None
        self.bulb_fx_canvas: tk.Canvas | None = None

        self.ai_chat_win: tk.Toplevel | None = None
        self.ai_input: tk.Entry | None = None
        self.ai_chat_close_job: str | None = None
        self.ai_reply_job: str | None = None
        self.preset_dialog_job: str | None = None
        self.panel_settings_win: tk.Toplevel | None = None
        self.about_win: tk.Toplevel | None = None
        self.feedback_win: tk.Toplevel | None = None
        self.diary_win: tk.Toplevel | None = None
        self.weather_win: tk.Toplevel | None = None
        self.music_track_picker_win: tk.Toplevel | None = None
        self._music_picker_photos: list[ImageTk.PhotoImage] = []
        self._sound_settings_icons: list[ImageTk.PhotoImage] = []
        self._rhythm_plate_photo: ImageTk.PhotoImage | None = None
        self.weather_photos: list[ImageTk.PhotoImage] = []
        self._weather_fetch_token = 0
        self.gallery_win: tk.Toplevel | None = None
        self.gallery_photos: list[ImageTk.PhotoImage] = []
        self.phonograph_win: tk.Toplevel | None = None
        self.phonograph_playing_id: str | None = None
        self.phonograph_play_job: str | None = None
        self.phonograph_play_token = 0
        self.phonograph_paused_music = False
        self.typing_game_win: tk.Toplevel | None = None
        self._typing_mood_cache: dict[str, ImageTk.PhotoImage] = {}
        self.vocab_game_win: tk.Toplevel | None = None
        self.vocab_notebook_win: tk.Toplevel | None = None
        self.vocab_word_label: tk.Label | None = None
        self.vocab_status_label: tk.Label | None = None
        self.vocab_options_frame: tk.Frame | None = None
        self._vocab_round_lock = False
        self._vocab_current: dict | None = None
        self._vocab_option_btns: dict[str, tk.Button] = {}
        self._vocab_advance_job: str | None = None
        self.rhyme_fight_win: tk.Toplevel | None = None
        self.rhyme_fight_job: str | None = None
        self.operation_guide_win: tk.Toplevel | None = None
        self.leaderboard_win: tk.Toplevel | None = None
        self.schedules: list[dict] = _load_schedules()
        self.schedule_win: tk.Toplevel | None = None
        self.triggered_reminders_today: set[str] = set()
        self._reminder_day = ""

        self.label.bind("<Button-1>", self._on_press)
        self.label.bind("<B1-Motion>", self._on_drag)
        self.label.bind("<ButtonRelease-1>", self._on_release)
        self.label.bind("<Button-3>", self._toggle_main_menu)
        self.label.bind("<Enter>", self._on_pet_enter, add="+")
        self.label.bind("<Leave>", self._on_pet_leave, add="+")
        self.root.bind("<Button-1>", self._on_root_click, add="+")
        self.root.bind("<Escape>", self._exit_to_free, add="+")
        self.root.bind("<F1>", lambda _e: self._open_operation_guide(), add="+")

        self._place_window()
        self.root.update_idletasks()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        tick_ms = self._difficulty_params()["stamina_tick_ms"]
        self.root.after(tick_ms, self._stamina_tick)
        self.root.after(REMINDER_CHECK_MS, self._reminder_tick)
        self._show_wait_hint("请耐心等待…正在启动")
        self._start_ui_heartbeat()
        self._animate_startup_loading()
        threading.Thread(target=self._startup_load_worker, daemon=True).start()
        self.root.after(80, self._preload_assets_idle)

    def _startup_busy(self) -> bool:
        return not self._startup_ready

    def _app_loading_busy(self) -> bool:
        return (
            self._startup_busy()
            or self.size_loading_active
            or self.companion_loading_active
            or self._ui_busy_depth > 0
        )

    def _current_wait_hint_message(self) -> str:
        if self.wait_hint_reason:
            return self.wait_hint_reason
        if self._startup_busy():
            return "请耐心等待…正在启动"
        if self.size_loading_active:
            return "请耐心等待…切换尺寸"
        if self.companion_loading_active:
            return "请耐心等待…加载金目"
        if self._ui_lag_detected:
            return "请耐心等待…程序处理中"
        return WAIT_HINT_DEFAULT

    def _should_show_wait_hint(self) -> bool:
        if self._closing:
            return False
        if self._app_loading_busy():
            return True
        return self._mouse_over_pet and self._ui_lag_detected

    def _set_wait_cursor(self, active: bool) -> None:
        cursor = "watch" if active else ""
        try:
            self.root.config(cursor=cursor)
            self.label.config(cursor=cursor)
        except Exception:
            pass

    def _place_wait_hint(self) -> None:
        if not self.wait_hint_win or not self.wait_hint_win.winfo_exists():
            return
        width = max(self.wait_hint_win.winfo_reqwidth(), 1)
        height = max(self.wait_hint_win.winfo_reqheight(), 1)
        x = self.x + max(0, (self.display_size - width) // 2)
        y = self.y + self.display_size + 6
        x, y = self._clamp_popup_rect(x, y, width, height)
        self.wait_hint_win.geometry(f"+{x}+{y}")

    def _tick_wait_hint_animation(self) -> None:
        if not self.wait_hint_win or not self.wait_hint_win.winfo_exists():
            return
        if not self._should_show_wait_hint():
            return
        base = self._current_wait_hint_message().rstrip(".…")
        dots = "." * (1 + self.wait_hint_phase % 3)
        if self.wait_hint_main_label:
            self.wait_hint_main_label.config(text=f"{base}{dots}")
        self.wait_hint_phase += 1
        self._place_wait_hint()

    def _animate_wait_hint(self) -> None:
        self._tick_wait_hint_animation()

    def _show_wait_hint(self, reason: str = "") -> None:
        if self._closing:
            return
        if reason:
            self.wait_hint_reason = reason
        message = self._current_wait_hint_message()
        if self.wait_hint_win and self.wait_hint_win.winfo_exists():
            if self.wait_hint_main_label:
                self.wait_hint_main_label.config(text=message)
            self._place_wait_hint()
            self._set_wait_cursor(True)
            return

        self.wait_hint_win = tk.Toplevel(self.root)
        self.wait_hint_win.overrideredirect(True)
        self.wait_hint_win.attributes("-topmost", True)
        self.wait_hint_win.configure(bg="#ffcc66")

        border = tk.Frame(self.wait_hint_win, bg="#ffcc66", padx=2, pady=2)
        border.pack()
        inner = tk.Frame(border, bg="#111122", padx=12, pady=8)
        inner.pack()
        self.wait_hint_main_label = tk.Label(
            inner,
            text=message,
            font=PIXEL_FONT,
            fg="#ffdd88",
            bg="#111122",
            justify=tk.CENTER,
        )
        self.wait_hint_main_label.pack()
        self.wait_hint_phase = 0
        self._place_wait_hint()
        self._set_wait_cursor(True)

    def _hide_wait_hint(self) -> None:
        if self.wait_hint_job:
            try:
                self.root.after_cancel(self.wait_hint_job)
            except Exception:
                pass
            self.wait_hint_job = None
        if self.wait_hint_win and self.wait_hint_win.winfo_exists():
            self.wait_hint_win.destroy()
        self.wait_hint_win = None
        self.wait_hint_main_label = None
        if not self._should_show_wait_hint():
            self._set_wait_cursor(False)

    def _sync_wait_hint(self) -> None:
        if self._should_show_wait_hint():
            self._show_wait_hint()
        else:
            self.wait_hint_reason = ""
            self._hide_wait_hint()

    def _enter_ui_busy(self, reason: str = "") -> None:
        self._ui_busy_depth += 1
        if reason:
            self.wait_hint_reason = reason
        self._show_wait_hint(reason or self._current_wait_hint_message())

    def _exit_ui_busy(self) -> None:
        self._ui_busy_depth = max(0, self._ui_busy_depth - 1)
        if self._ui_busy_depth == 0:
            self.wait_hint_reason = ""
        self._sync_wait_hint()

    def _on_pet_enter(self, _event=None) -> None:
        self._mouse_over_pet = True
        self._sync_wait_hint()

    def _on_pet_leave(self, _event=None) -> None:
        self._mouse_over_pet = False
        self._ui_lag_detected = False
        self._sync_wait_hint()

    def _start_ui_heartbeat(self) -> None:
        if self._ui_heartbeat_job:
            try:
                self.root.after_cancel(self._ui_heartbeat_job)
            except Exception:
                pass
        self._ui_heartbeat_ms = int(time.time() * 1000)

        def tick() -> None:
            if not self._alive():
                return
            now = int(time.time() * 1000)
            if self._ui_heartbeat_ms > 0:
                lag = now - self._ui_heartbeat_ms - WAIT_HINT_TICK_MS
                if lag > UI_BUSY_LAG_THRESHOLD_MS:
                    self._ui_lag_detected = True
                elif not self._app_loading_busy():
                    self._ui_lag_detected = False
            self._ui_heartbeat_ms = now
            if self._mouse_over_pet or self._app_loading_busy():
                self._sync_wait_hint()
            if self.wait_hint_win and self.wait_hint_win.winfo_exists() and self._should_show_wait_hint():
                self._tick_wait_hint_animation()
            self._ui_heartbeat_job = self._safe_after(WAIT_HINT_TICK_MS, tick)

        self._ui_heartbeat_job = self._safe_after(WAIT_HINT_TICK_MS, tick)

    def _startup_load_worker(self) -> None:
        pack: dict | None = None
        vocab: list[dict[str, str]] = []
        err = False
        try:
            _migrate_legacy_layout()
            _warm_reference_scales()
            pack = _build_sprite_pack(self.display_size)
            vocab = _load_vocab()
        except Exception:
            err = True
        self.root.after(0, lambda: self._finish_startup(pack, vocab, err))

    def _finish_startup(self, pack: dict | None, vocab: list[dict[str, str]], err: bool) -> None:
        if self._closing:
            return
        self._startup_load_error = err
        self._startup_sprite_pack = pack
        self._startup_vocab_words = vocab
        elapsed = int(time.time() * 1000) - self._startup_loading_start_ms
        remain = max(0, STARTUP_MIN_MS - elapsed)
        if remain > 0:
            self.root.after(remain, self._apply_startup_assets)
        else:
            self._apply_startup_assets()

    def _apply_startup_assets(self) -> None:
        if self._closing or self._startup_ready:
            return
        self._show_wait_hint("请耐心等待…正在加载桌宠")
        pack = self._startup_sprite_pack
        if pack is None:
            self._show_toast("资源加载失败，请检查 assets 目录", "#ff6666", duration_ms=4000)
            pack = _build_sprite_pack(self.display_size)

        def on_sprite_ready(ss: SpriteSet) -> None:
            if self._closing or self._startup_ready:
                return
            try:
                self.sprites = ss
                self._sprite_cache[self.display_size] = ss
                self.label.configure(image=ss.stand)
                self.label.image = ss.stand
            except Exception:
                self._show_toast("桌宠资源初始化失败", "#ff6666", duration_ms=4000)
                self.sprites = SpriteSet(self.display_size)
                self._sprite_cache[self.display_size] = self.sprites
                self.label.configure(image=self.sprites.stand)
                self.label.image = self.sprites.stand
            self._hide_startup_canvas()
            self._complete_startup_after_sprites()

        self._build_sprite_set_batched(self.display_size, pack, on_sprite_ready)

    def _complete_startup_after_sprites(self) -> None:
        if self._closing or self._startup_ready:
            return
        self.vocab_words = self._startup_vocab_words or []
        self._startup_ready = True
        self._startup_loading_active = False
        if self._startup_anim_job:
            try:
                self.root.after_cancel(self._startup_anim_job)
            except Exception:
                pass
            self._startup_anim_job = None
        self._register_hotkey()
        self.root.after(500, self._resume_idle)
        self._start_idle_watchdog()
        self.root.after(1200, self._maybe_show_first_run_guide)
        self._enter_ui_busy("请耐心等待…整理资源")
        try:
            self._refresh_drag_handle()
            self._place_window()
        finally:
            self._exit_ui_busy()
        self.wait_hint_reason = ""
        self._sync_wait_hint()
        if PET_ID_FEATURE and not _load_leaderboard():
            _rebuild_leaderboard_from_profile(self.pet_profile)

    def _hide_startup_canvas(self) -> None:
        if getattr(self, "_startup_canvas", None) and self._startup_canvas.winfo_exists():
            self._startup_canvas.destroy()
        self._startup_canvas = None

    def _animate_startup_loading(self) -> None:
        if not self._startup_loading_active or self._closing:
            return
        if self._startup_canvas and self._startup_canvas.winfo_exists():
            _draw_size_loading_frame(
                self._startup_canvas, self.display_size, self._startup_loading_phase, simple=True
            )
        self._startup_loading_phase += 1
        self._place_wait_hint()
        self._startup_anim_job = self.root.after(STARTUP_ANIM_MS, self._animate_startup_loading)

    def _refresh_drag_handle(self) -> None:
        handle = _compute_drag_handle(self.display_size)
        self._drag_handle_cache[self.display_size] = handle
        self.drag_handle = handle

    def _preload_assets_idle(self) -> None:
        pending = [s for s in SIZE_PRESETS.values() if s not in self._sprite_cache]
        if not pending:
            return

        def load_one(idx: int = 0) -> None:
            if idx >= len(pending) or self._closing:
                return
            try:
                self._ensure_sprite_cached(pending[idx])
            except Exception:
                pass
            if idx + 1 < len(pending):
                self.root.after(PRELOAD_STEP_MS, lambda: load_one(idx + 1))

        self.root.after(PRELOAD_IDLE_DELAY_MS, lambda: load_one(0))

    def _build_sprite_set_batched(self, size: int, pack: dict, on_done) -> None:
        tasks = _sprite_photo_tasks(pack)
        photos: dict[str, ImageTk.PhotoImage] = {}

        def step(idx: int = 0) -> None:
            if self._closing:
                return
            end = min(idx + SPRITE_BATCH_SIZE, len(tasks))
            for i in range(idx, end):
                key, img = tasks[i]
                photos[key] = ImageTk.PhotoImage(img)
            if end < len(tasks):
                self._safe_after(SPRITE_BATCH_MS, lambda: step(end))
                return
            ss = SpriteSet.__new__(SpriteSet)
            ss.display_size = size
            _bind_sprite_photos(ss, photos, pack)
            on_done(ss)

        step(0)

    def _on_sprite_pack_ready(self, size: int, pack: dict | None, on_done=None) -> None:
        if self._closing:
            self._sprite_building.discard(size)
            self._exit_ui_busy()
            return
        if pack is None:
            try:
                self._sprite_cache[size] = SpriteSet(size)
            except Exception:
                pass
            self._sprite_building.discard(size)
            self._exit_ui_busy()
            if on_done:
                on_done()
            return

        def finish(ss: SpriteSet) -> None:
            self._sprite_cache[size] = ss
            self._sprite_building.discard(size)
            self._exit_ui_busy()
            if on_done:
                on_done()

        self._build_sprite_set_batched(size, pack, finish)

    def _ensure_sprite_cached(self, size: int, *, on_done=None) -> None:
        if size in self._sprite_cache:
            if on_done:
                on_done()
            return
        if size in self._sprite_building:
            return
        self._sprite_building.add(size)
        self._enter_ui_busy("请耐心等待…加载资源")

        def worker() -> None:
            pack: dict | None = None
            try:
                pack = _build_sprite_pack(size)
            except Exception:
                pack = None
            self.root.after(0, lambda: self._on_sprite_pack_ready(size, pack, on_done))

        threading.Thread(target=worker, daemon=True).start()

    @property
    def _work_sprites(self) -> dict[str, tuple[ImageTk.PhotoImage, ImageTk.PhotoImage]]:
        return {
            "front": self.sprites.work_front,
            "back": self.sprites.work_back,
            "left": self.sprites.work_left,
            "right": self.sprites.work_right,
        }

    def _clamp_position(self) -> None:
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.x = max(0, min(self.x, screen_w - self.display_size))
        self.y = max(0, min(self.y, screen_h - self.display_size))

    def _dist_to(self, tx: int, ty: int) -> float:
        cx = self.x + self.display_size // 2
        cy = self.y + self.display_size // 2
        return math.hypot(tx - cx, ty - cy)

    def _direction_to(self, tx: int, ty: int) -> str:
        cx = self.x + self.display_size // 2
        cy = self.y + self.display_size // 2
        dx, dy = tx - cx, ty - cy
        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        return "front" if dy > 0 else "back"

    @property
    def _walk_sprites(self) -> dict[str, tuple[ImageTk.PhotoImage, ImageTk.PhotoImage]]:
        if self.music_sprite_mode:
            return {
                "front": self.sprites.music_front,
                "back": self.sprites.music_back,
                "left": self.sprites.music_left,
                "right": self.sprites.music_right,
            }
        return {
            "front": self.sprites.front,
            "back": self.sprites.back,
            "left": self.sprites.left,
            "right": self.sprites.right,
        }

    def _current_stand_sprite(self) -> ImageTk.PhotoImage:
        return self.sprites.music_stand if self.music_sprite_mode else self.sprites.stand

    def _sound_scale(self, category: str) -> float:
        if self.music_config.get("muted"):
            return 0.0
        key_map = {"music": "music_volume", "sfx": "sfx_volume", "voice": "voice_volume"}
        key = key_map.get(category, "music_volume")
        raw = self.music_config.get(key, self.music_config.get("volume", 70))
        return max(0.0, min(1.0, int(raw) / 100.0))

    def _apply_music_volume(self) -> None:
        vol = self._sound_scale("music")
        try:
            import pygame

            if pygame.mixer.get_init() and self.bg_music_playing:
                pygame.mixer.music.set_volume(vol)
        except Exception:
            pass

    def _apply_voice_volume(self) -> None:
        if self.action_name != "call":
            return
        try:
            import pygame

            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.set_volume(self._sound_scale("voice"))
        except Exception:
            pass

    def _preview_sfx_volume(self) -> None:
        sound = _get_type_sound()
        if sound and sound is not False:
            self._play_sound_with_volume(sound, "sfx")

    def _play_sound_with_volume(self, sound, category: str = "sfx") -> None:
        if not sound or sound is False:
            return
        vol = self._sound_scale(category)
        if vol <= 0:
            return
        try:
            import pygame

            channel = sound.play()
            if channel is not None:
                channel.set_volume(vol)
        except Exception:
            pass

    def _music_playlist(self) -> list[str]:
        return _music_playlist_from_config(self.music_config)

    def _music_play_mode_label(self) -> str:
        return "列表循环" if self.music_config.get("play_mode", "list") == "list" else "随机"

    def _cancel_bg_music_watch(self) -> None:
        if self.bg_music_watch_job:
            try:
                self.root.after_cancel(self.bg_music_watch_job)
            except Exception:
                pass
            self.bg_music_watch_job = None

    def _bg_music_play_track(self, track_id: str, *, single_loop: bool) -> bool:
        wav = _resolve_music_wav(track_id)
        if wav is None or not wav.exists():
            return False
        import pygame

        _init_pygame_mixer()
        pygame.mixer.music.load(str(wav))
        self._apply_music_volume()
        pygame.mixer.music.play(-1 if single_loop else 0)
        self.bg_music_playing = True
        return True

    def _advance_bg_music_track(self) -> None:
        playlist = self._music_playlist()
        if not playlist:
            return
        if len(playlist) == 1:
            self.bg_music_play_index = 0
            self._bg_music_play_track(playlist[0], single_loop=True)
            return
        mode = self.music_config.get("play_mode", "list")
        if mode == "random":
            if len(playlist) == 1:
                self.bg_music_play_index = 0
            else:
                choices = [i for i in range(len(playlist)) if i != self.bg_music_play_index]
                self.bg_music_play_index = random.choice(choices or list(range(len(playlist))))
        else:
            self.bg_music_play_index = (self.bg_music_play_index + 1) % len(playlist)
        tid = playlist[self.bg_music_play_index]
        if not self._bg_music_play_track(tid, single_loop=False):
            self._show_toast(f"找不到音乐：{_music_track(tid)['title']}", "#ff8844")
            self._stop_bg_music()
            return
        self._schedule_bg_music_watch()

    def _schedule_bg_music_watch(self) -> None:
        self._cancel_bg_music_watch()
        if not self.bg_music_playing or len(self._music_playlist()) <= 1:
            return

        def tick() -> None:
            self.bg_music_watch_job = None
            if not self.bg_music_playing:
                return
            try:
                import pygame

                if pygame.mixer.get_init() and not pygame.mixer.music.get_busy():
                    self._advance_bg_music_track()
                    return
            except Exception:
                pass
            self.bg_music_watch_job = self._safe_after(500, tick)

        self.bg_music_watch_job = self._safe_after(500, tick)

    def _start_bg_music(self) -> None:
        if self.bg_music_playing:
            return
        playlist = self._music_playlist()
        if not playlist:
            self._show_toast("播放列表为空", "#ff8844")
            return
        single = len(playlist) == 1
        if single:
            self.bg_music_play_index = 0
        elif self.music_config.get("play_mode", "list") == "random":
            self.bg_music_play_index = random.randint(0, len(playlist) - 1)
        else:
            self.bg_music_play_index = 0
        tid = playlist[self.bg_music_play_index]
        try:
            if not self._bg_music_play_track(tid, single_loop=single):
                self._show_toast("找不到默认音乐文件", "#ff8844")
                return
            if not single:
                self._schedule_bg_music_watch()
        except Exception:
            self._show_toast("音乐播放失败", "#ff6666")

    def _stop_bg_music(self) -> None:
        self._cancel_bg_music_watch()
        try:
            import pygame

            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass
        self.bg_music_playing = False
        self.bg_music_paused_for_call = False

    def _toggle_music_interact(self) -> None:
        if self.dragging or self.state == "work":
            return
        self._hide_main_menu()
        if self.music_sprite_mode:
            self._apply_music_off()
            return
        if self.mode not in ("free", "stroll"):
            self._request_mode_switch(self._apply_music_on)
            return
        self._apply_music_on()

    def _apply_music_off(self) -> None:
        self.music_sprite_mode = False
        self._stop_bg_music()
        self._stop_music_wave_fx()
        self._sync_mini_pet_music_waves()
        if self.state in ("stand", "walk"):
            self._set_image(self._current_stand_sprite())
        self._show_toast("音乐已关闭（仍为漫步）", PIXEL_COLOR)

    def _apply_music_on(self) -> None:
        self._interrupt_for_mode_switch()
        self._leave_quiet_mode()
        if self.mode == "work":
            self._stop_work_mode()
        if self.mode == "game":
            self._stop_game_mode()
        # 音乐模式＝漫步：只走路听歌，不触发动作/台词特效
        self.mode = "stroll"
        self.follow_animating = False
        self.work_animating = False
        self._wake_from_sleep()
        self.state = "stand"
        self.action_name = ""
        self._clear_all_action_fx()
        self.music_sprite_mode = True
        self._start_bg_music()
        self._start_music_wave_fx()
        self._sync_mini_pet_music_waves()
        self._set_image(self._current_stand_sprite())
        self._place_window()
        playlist = self._music_playlist()
        mode_label = self._music_play_mode_label()
        if len(playlist) == 1:
            track = _music_track(playlist[0])
            self._show_toast(f"音乐漫步开启（{mode_label} · {track['title']}）", "#88ccff")
        else:
            self._show_toast(f"音乐漫步开启（{mode_label} · {len(playlist)} 首）", "#88ccff")
        self._show_once_hint("music_mode", duration_ms=3500)
        self._resume_idle()

    def _apply_music_toggle(self) -> None:
        if self.music_sprite_mode:
            self._apply_music_off()
        else:
            self._apply_music_on()

    def _open_sound_settings(self, *, from_panel: bool = False) -> None:
        if not from_panel:
            self._hide_main_menu()
        win = self.sound_settings_win or self.music_settings_win
        if win and win.winfo_exists():
            win.lift()
            return

        self.sound_settings_win = tk.Toplevel(self.root)
        self.music_settings_win = self.sound_settings_win
        self.sound_settings_win.title("声音设置")
        self.sound_settings_win.attributes("-topmost", True)
        self.sound_settings_win.configure(bg=MENU_BG)

        _, frame = _pack_fixed_scroll_panel(self.sound_settings_win)

        tk.Label(frame, text="声音设置", font=PIXEL_FONT, fg=PIXEL_COLOR, bg=MENU_BG).pack(anchor=tk.W)

        muted = bool(self.music_config.get("muted"))

        def toggle_mute() -> None:
            self.music_config["muted"] = not self.music_config.get("muted")
            _save_music_config(self.music_config)
            mute_btn.config(
                text="取消静音" if self.music_config["muted"] else "一键静音",
                bg="#884444" if self.music_config["muted"] else MENU_ACTIVE,
            )
            self._apply_music_volume()
            self._apply_voice_volume()

        mute_btn = tk.Button(
            frame,
            text="取消静音" if muted else "一键静音",
            command=toggle_mute,
            font=PIXEL_FONT,
            bg="#884444" if muted else MENU_ACTIVE,
            fg=MENU_FG,
        )
        mute_btn.pack(anchor=tk.W, pady=(6, 8))

        play_mode_var = tk.StringVar(value=self.music_config.get("play_mode", "list"))
        mode_row = tk.Frame(frame, bg=MENU_BG)
        mode_row.pack(fill=tk.X, pady=(0, 4))
        tk.Label(mode_row, text="播放模式", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG).pack(side=tk.LEFT)

        def set_play_mode(mode: str) -> None:
            play_mode_var.set(mode)
            self.music_config["play_mode"] = mode
            _save_music_config(self.music_config)
            list_btn.config(bg=MENU_ACTIVE if mode == "list" else MENU_BG)
            random_btn.config(bg=MENU_ACTIVE if mode == "random" else MENU_BG)
            path_label.config(text=self._music_path_label())
            if self.bg_music_playing or self.music_sprite_mode:
                self._stop_bg_music()
                self._start_bg_music()

        list_btn = tk.Button(
            mode_row,
            text="列表循环",
            command=lambda: set_play_mode("list"),
            font=PIXEL_FONT,
            bg=MENU_ACTIVE if play_mode_var.get() == "list" else MENU_BG,
            fg=MENU_FG,
        )
        list_btn.pack(side=tk.LEFT, padx=4)
        random_btn = tk.Button(
            mode_row,
            text="随机",
            command=lambda: set_play_mode("random"),
            font=PIXEL_FONT,
            bg=MENU_ACTIVE if play_mode_var.get() == "random" else MENU_BG,
            fg=MENU_FG,
        )
        random_btn.pack(side=tk.LEFT, padx=4)

        track_row = tk.Frame(frame, bg=MENU_BG)
        track_row.pack(fill=tk.X, pady=(2, 4))
        playlist_lbl = tk.Label(track_row, text="", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG)
        playlist_lbl.pack(side=tk.LEFT)

        def refresh_playlist_label() -> None:
            pl = self._music_playlist()
            if len(pl) == 1:
                title = str(_music_track(pl[0])["title"])
                playlist_lbl.config(text=f"播放列表：{title}（单曲循环）")
            else:
                playlist_lbl.config(text=f"播放列表：{len(pl)} 首")

        def set_playlist(track_ids: list[str]) -> None:
            self.music_config["playlist"] = _normalize_music_playlist(track_ids, fallback=DEFAULT_MUSIC_TRACK)
            _save_music_config(self.music_config)
            path_label.config(text=self._music_path_label())
            refresh_playlist_label()
            if self.bg_music_playing or self.music_sprite_mode:
                self._stop_bg_music()
                self._start_bg_music()

        def open_playlist_picker() -> None:
            self._open_music_playlist_picker(on_confirm=set_playlist)

        tk.Button(
            track_row, text="选曲…", command=open_playlist_picker, font=PIXEL_FONT, bg=MENU_ACTIVE, fg=MENU_FG
        ).pack(side=tk.LEFT, padx=(8, 0))
        refresh_playlist_label()

        def add_volume_row(parent, label: str, key: str, on_change=None) -> None:
            row = tk.Frame(parent, bg=MENU_BG)
            row.pack(fill=tk.X, pady=4)
            tk.Label(row, text=label, font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG, width=6, anchor=tk.W).pack(side=tk.LEFT)
            var = tk.IntVar(value=int(self.music_config.get(key, 70)))
            val_label = tk.Label(row, text=f"{var.get()}%", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG, width=5)
            val_label.pack(side=tk.RIGHT)

            def on_volume(val: str) -> None:
                v = int(float(val))
                var.set(v)
                val_label.config(text=f"{v}%")
                self.music_config[key] = v
                if key == "music_volume":
                    self.music_config["volume"] = v
                _save_music_config(self.music_config)
                if on_change:
                    on_change()

            tk.Scale(
                row,
                from_=0,
                to=100,
                orient=tk.HORIZONTAL,
                variable=var,
                command=on_volume,
                bg=MENU_BG,
                fg=MENU_FG,
                highlightthickness=0,
                length=140,
            ).pack(side=tk.LEFT, padx=(4, 0))

        add_volume_row(frame, "音乐", "music_volume", self._apply_music_volume)
        add_volume_row(frame, "音效", "sfx_volume", self._preview_sfx_volume)
        add_volume_row(frame, "语音", "voice_volume", self._apply_voice_volume)

        path_label = tk.Label(
            frame,
            text=self._music_path_label(),
            font=PIXEL_FONT,
            fg="#aaaaaa",
            bg=MENU_BG,
            wraplength=240,
            justify=tk.LEFT,
        )
        path_label.pack(anchor=tk.W, pady=(6, 4))

        tk.Label(
            frame,
            text="音乐：默认 RADICAL MAT 单曲循环；多首时按列表或随机播放",
            font=PIXEL_FONT,
            fg="#888888",
            bg=MENU_BG,
            justify=tk.LEFT,
            wraplength=320,
        ).pack(anchor=tk.W, pady=(4, 0))
        self._place_panel_popup(self.sound_settings_win)

    def _open_music_settings(self) -> None:
        self._open_sound_settings()

    def _music_path_label(self) -> str:
        pl = self._music_playlist()
        mode = self._music_play_mode_label()
        if not pl:
            return f"{mode} · 无曲目"
        if len(pl) == 1:
            return f"{mode} · {_music_track(pl[0])['title']}（单曲循环）"
        names = [str(_music_track(tid)["title"]) for tid in pl[:4]]
        tail = f" 等{len(pl)}首" if len(pl) > 4 else ""
        return f"{mode} · {' / '.join(names)}{tail}"

    def _cancel_yesno_overlay(self) -> None:
        if self.yesno_reveal_job:
            self.root.after_cancel(self.yesno_reveal_job)
            self.yesno_reveal_job = None
        if self.yesno_overlay_win and self.yesno_overlay_win.winfo_exists():
            self.yesno_overlay_win.destroy()
        self.yesno_overlay_win = None
        if not self.root.winfo_viewable():
            self.root.deiconify()

    def _clamp_popup_rect(self, x: int, y: int, width: int, height: int) -> tuple[int, int]:
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        margin = POPUP_EDGE_MARGIN
        max_x = max(margin, sw - width - margin)
        max_y = max(margin, sh - height - margin)
        return max(margin, min(x, max_x)), max(margin, min(y, max_y))

    @staticmethod
    def _rects_overlap(
        x1: int, y1: int, w1: int, h1: int, x2: int, y2: int, w2: int, h2: int
    ) -> bool:
        return x1 < x2 + w2 and x2 < x1 + w1 and y1 < y2 + h2 and y2 < y1 + h1

    def _window_avoid_rect(self, win: tk.Toplevel | None, *, pad: int = 4) -> tuple[int, int, int, int] | None:
        if not win or not win.winfo_exists():
            return None
        try:
            win.update_idletasks()
            x, y = win.winfo_rootx(), win.winfo_rooty()
            w = max(win.winfo_width(), win.winfo_reqwidth(), 1)
            h = max(win.winfo_height(), win.winfo_reqheight(), 1)
            return x - pad, y - pad, w + pad * 2, h + pad * 2
        except Exception:
            return None

    def _popup_avoid_rects(self, *, skip: tk.Toplevel | None = None) -> list[tuple[int, int, int, int]]:
        rects: list[tuple[int, int, int, int]] = []
        for win in (self.menu_bar, self.sub_menu):
            if win is skip:
                continue
            rect = self._window_avoid_rect(win)
            if rect:
                rects.append(rect)
        return rects

    def _main_menu_bottom_y(self) -> int | None:
        if not self.menu_bar or not self.menu_bar.winfo_exists():
            return None
        try:
            self.menu_bar.update_idletasks()
        except Exception:
            pass
        menu_y = self.y + self.display_size + PET_MENU_GAP_Y
        menu_h = max(self.menu_bar.winfo_reqheight(), self.menu_bar.winfo_height(), 28)
        return menu_y + menu_h + PET_SUBMENU_GAP_Y

    def _popup_edge_clearance(self, x: int, y: int, width: int, height: int) -> int:
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        margin = POPUP_EDGE_MARGIN
        return min(x - margin, y - margin, sw - margin - x - width, sh - margin - y - height)

    def _popup_placement_score(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        *,
        avoid_rects: list[tuple[int, int, int, int]] | None = None,
    ) -> int:
        score = self._popup_edge_clearance(x, y, width, height)
        for ax, ay, aw, ah in avoid_rects or ():
            if self._rects_overlap(x, y, width, height, ax, ay, aw, ah):
                score -= 1_000_000
        return score

    def _best_popup_pos(
        self,
        candidates: list[tuple[int, int]],
        width: int,
        height: int,
        *,
        avoid_rects: list[tuple[int, int, int, int]] | None = None,
    ) -> tuple[int, int]:
        best: tuple[int, int] | None = None
        best_score = -10**9
        for px, py in candidates:
            cx, cy = self._clamp_popup_rect(px, py, width, height)
            score = self._popup_placement_score(cx, cy, width, height, avoid_rects=avoid_rects)
            if score > best_score:
                best_score = score
                best = (cx, cy)
        if best is None:
            return self._clamp_popup_rect(0, 0, width, height)
        return best

    def _panel_popup_candidates(self, panel_w: int, panel_h: int) -> list[tuple[int, int]]:
        gap = POPUP_PET_GAP
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        margin = POPUP_EDGE_MARGIN
        pet_right = self.x + self.display_size
        pet_bottom = self.y + self.display_size
        pet_cx = self.x + self.display_size // 2
        center_x = max(margin, (sw - panel_w) // 2)
        center_y = max(margin, (sh - panel_h) // 2)
        return [
            (pet_right + gap, self.y),
            (self.x - panel_w - gap, self.y),
            (self.x, pet_bottom + gap),
            (pet_cx - panel_w // 2, self.y - panel_h - gap),
            (pet_right + gap, pet_bottom + gap),
            (self.x - panel_w - gap, pet_bottom - panel_h),
            (center_x, center_y),
            (center_x, margin),
            (center_x, sh - panel_h - margin),
            (margin, center_y),
            (sw - panel_w - margin, center_y),
            (margin, margin),
            (sw - panel_w - margin, margin),
            (margin, sh - panel_h - margin),
            (sw - panel_w - margin, sh - panel_h - margin),
        ]

    def _smart_popup_pos(self, pref_x: int, pref_y: int, width: int, height: int) -> tuple[int, int]:
        return self._clamp_popup_rect(pref_x, pref_y, width, height)

    def _panel_popup_pos(self, panel_w: int, panel_h: int) -> tuple[int, int]:
        avoid_rects = self._popup_avoid_rects()
        return self._best_popup_pos(
            self._panel_popup_candidates(panel_w, panel_h), panel_w, panel_h, avoid_rects=avoid_rects
        )

    def _place_popup(self, win: tk.Toplevel | None, pref_x: int, pref_y: int) -> None:
        if not win or not win.winfo_exists():
            return
        w = max(win.winfo_reqwidth(), 1)
        h = max(win.winfo_reqheight(), 1)
        gap = POPUP_PET_GAP
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        margin = POPUP_EDGE_MARGIN
        candidates = [
            (pref_x, pref_y),
            (self.x + self.display_size + gap, self.y),
            (self.x - w - gap, self.y),
            (self.x, self.y + self.display_size + gap),
            (self.x + self.display_size // 2 - w // 2, self.y - h - gap),
            (max(margin, (sw - w) // 2), max(margin, (sh - h) // 2)),
        ]
        x, y = self._best_popup_pos(candidates, w, h)
        win.geometry(f"+{x}+{y}")

    def _place_panel_popup(self, win: tk.Toplevel | None) -> None:
        if not win or not win.winfo_exists():
            return
        fixed = getattr(win, "_panel_fixed_size", None)
        if isinstance(fixed, tuple) and len(fixed) == 2:
            pw, ph = int(fixed[0]), int(fixed[1])
        else:
            pw = max(win.winfo_reqwidth(), 220)
            ph = max(win.winfo_reqheight(), 80)
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            max_w = min(PANEL_FIXED_W, max(280, sw - 80))
            max_h = min(PANEL_FIXED_H, max(240, sh - 100))
            if pw > max_w or ph > max_h:
                pw, ph = _fit_panel_wh(win, min(pw, max_w), min(ph, max_h))
        px, py = self._panel_popup_pos(pw, ph)
        try:
            win.geometry(f"{pw}x{ph}+{px}+{py}")
        except Exception:
            win.geometry(f"+{px}+{py}")

    def _place_pet_attached_popup(self, win: tk.Toplevel | None, pref_x: int, pref_y: int) -> None:
        if not win or not win.winfo_exists():
            return
        w = max(win.winfo_reqwidth(), 1)
        h = max(win.winfo_reqheight(), 1)
        gap = POPUP_PET_GAP
        avoid_rects = self._popup_avoid_rects(skip=win)
        menu_bottom_y = self._main_menu_bottom_y()
        candidates: list[tuple[int, int]] = []
        if menu_bottom_y is not None and win is not self.menu_bar:
            candidates.append((pref_x, menu_bottom_y))
        candidates.extend(
            [
                (pref_x, pref_y),
                (self.x + self.display_size + gap, self.y),
                (self.x - w - gap, self.y),
                (self.x, self.y + self.display_size + gap),
                (self.x + self.display_size // 2 - w // 2, self.y - h - gap),
            ]
        )
        if menu_bottom_y is not None and win is not self.menu_bar:
            candidates.append((self.x + self.display_size + gap, menu_bottom_y))
            candidates.append((self.x - w - gap, menu_bottom_y))
        x, y = self._best_popup_pos(candidates, w, h, avoid_rects=avoid_rects)
        win.geometry(f"+{x}+{y}")

    def _sub_menu_pref_y(self) -> int:
        return self._main_menu_bottom_y() or (self.y + self.display_size + PET_SUBMENU_GAP_Y + 28)

    def _pointer_over_win(self, win: tk.Toplevel | None) -> bool:
        if not win or not win.winfo_exists():
            return False
        try:
            mx = self.root.winfo_pointerx()
            my = self.root.winfo_pointery()
            x, y = win.winfo_rootx(), win.winfo_rooty()
            w = max(win.winfo_width(), win.winfo_reqwidth(), 1)
            h = max(win.winfo_height(), win.winfo_reqheight(), 1)
            return x <= mx <= x + w and y <= my <= y + h
        except Exception:
            return False

    def _menus_are_hovered(self) -> bool:
        return self._pointer_over_win(self.menu_bar) or self._pointer_over_win(self.sub_menu)

    def _reposition_pet_attached_popups(self, *, force: bool = False) -> None:
        now_ms = int(time.time() * 1000)
        # 鼠标停在菜单上时先不跟着跑，方便点选
        if not force and self._menus_are_hovered():
            self._schedule_pet_menu_follow()
            return

        menu_due = force or (now_ms - self._pet_menu_follow_ms >= PET_MENU_FOLLOW_MS)
        speech_due = force or (now_ms - self._pet_speech_follow_ms >= PET_SPEECH_FOLLOW_MS)

        if menu_due:
            self._pet_menu_follow_ms = now_ms
            menu_y = self.y + self.display_size + PET_MENU_GAP_Y
            if self.menu_bar and self.menu_bar.winfo_exists():
                self._place_pet_attached_popup(self.menu_bar, self.x, menu_y)
            if self.sub_menu and self.sub_menu.winfo_exists():
                offset_x = getattr(self, "_sub_menu_offset_x", 0)
                self._place_pet_attached_popup(self.sub_menu, self.x + offset_x, self._sub_menu_pref_y())

        if speech_due and self.speech_dialog and self.speech_dialog.winfo_exists():
            self._pet_speech_follow_ms = now_ms
            self._place_pet_attached_popup(
                self.speech_dialog,
                self.x + self.display_size + PET_SPEECH_GAP,
                self.y,
            )

        if (self.menu_bar and self.menu_bar.winfo_exists()) or (
            self.sub_menu and self.sub_menu.winfo_exists()
        ):
            self._schedule_pet_menu_follow()

    def _schedule_pet_menu_follow(self) -> None:
        if self._pet_menu_follow_job:
            return
        if not (
            (self.menu_bar and self.menu_bar.winfo_exists())
            or (self.sub_menu and self.sub_menu.winfo_exists())
            or (self.speech_dialog and self.speech_dialog.winfo_exists())
        ):
            return

        def tick() -> None:
            self._pet_menu_follow_job = None
            if not self._alive():
                return
            if (
                (self.menu_bar and self.menu_bar.winfo_exists())
                or (self.sub_menu and self.sub_menu.winfo_exists())
                or (self.speech_dialog and self.speech_dialog.winfo_exists())
            ):
                self._reposition_pet_attached_popups(force=False)

        self._pet_menu_follow_job = self._safe_after(PET_MENU_FOLLOW_MS, tick)

    def _persist_food_inventory(self) -> None:
        _save_food_inventory(self.food_inventory)

    def _register_hotkey(self) -> None:
        if sys.platform != "win32":
            return
        hwnd = self.root.winfo_id()
        self.hotkey_ids.clear()
        for hotkey_id, key, _action in HOTKEY_ACTIONS:
            ok = ctypes.windll.user32.RegisterHotKey(
                hwnd, hotkey_id, MOD_CONTROL | MOD_SHIFT, key
            )
            if ok:
                self.hotkey_ids.append(hotkey_id)
        if self.hotkey_ids:
            self.root.after(100, self._poll_hotkey)

    def _unregister_hotkey(self) -> None:
        if sys.platform != "win32" or not self.hotkey_ids:
            return
        hwnd = self.root.winfo_id()
        for hotkey_id in self.hotkey_ids:
            ctypes.windll.user32.UnregisterHotKey(hwnd, hotkey_id)
        self.hotkey_ids.clear()

    def _handle_hotkey_action(self, action: str) -> None:
        if self._startup_busy():
            return
        self._interrupt_current_interaction()
        if action == "food_menu":
            self._open_eat_food_menu()
        elif action == "sleep":
            self._play_sleep_interact()
        elif action == "ai_chat":
            self._toggle_ai_chat()
        elif action == "toggle_menu":
            self._toggle_main_menu_from_hotkey()
        elif action in SELECT_ACTIONS:
            self._play_action(action)

    def _toggle_main_menu_from_hotkey(self) -> None:
        if self.menu_bar and self.menu_bar.winfo_exists():
            self._hide_main_menu()
        else:
            self._toggle_main_menu(type("E", (), {"x": 0, "y": 0})())

    def _save_game_record(self, category: str, payload: dict) -> None:
        if not PET_ID_FEATURE:
            return
        records = self.pet_profile.setdefault("records", {})
        bucket = records.setdefault(category, [])
        if not isinstance(bucket, list):
            bucket = []
            records[category] = bucket
        entry = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "pet_id": self.pet_id, **payload}
        bucket.append(entry)
        records[category] = bucket[-120:]
        _save_pet_profile(self.pet_profile)
        _update_leaderboard(category, self.pet_id, entry)

    def _apply_expose_fail_penalty(self) -> None:
        p = self._difficulty_params()
        mood_pct = float(p.get("expose_fail_mood_pct", 0.5))
        stamina_pct = float(p.get("expose_fail_stamina_pct", 0.5))
        mood_loss = max(1, int(round(self.mood * mood_pct))) if self.mood > 0 else 0
        stamina_loss = max(1, int(round(self.stamina * stamina_pct))) if self.stamina > 0 else 0
        self.mood = max(0, self.mood - mood_loss)
        self.stamina = max(0, self.stamina - stamina_loss)
        self._refresh_panel()

    def _clear_all_action_fx(self) -> None:
        self._hide_rain_fx()
        self._hide_bulb_fx()
        self._hide_like_fx()
        self._hide_shy_fx()
        self._hide_wink_fx()
        self._hide_interact_fx()
        self._hide_follow_dizzy_fx()

    def _difficulty_params(self) -> dict:
        return DIFFICULTY_PRESETS.get(self.difficulty, DIFFICULTY_PRESETS["中"])

    def _apply_difficulty_runtime(self) -> None:
        p = self._difficulty_params()
        self._game_box_speed = int(p["game_speed"])
        self._game_spawn_ms = int(p["game_spawn_ms"])
        self._game_catch_dist = int(p["game_catch_dist"])
        self._expose_blue_span = float(p["expose_blue_span"])
        self._expose_pointer_speed = float(p["expose_pointer_speed"])
        self._fight_enemy_mult = float(p["fight_enemy_mult"])
        self._fight_player_mult = float(p["fight_player_mult"])

    def _set_difficulty(self, level: str) -> None:
        if level not in DIFFICULTY_PRESETS:
            return
        self._hide_main_menu()
        self.difficulty = level
        self.app_config["difficulty"] = level
        _save_app_config(self.app_config)
        self._apply_difficulty_runtime()
        p = self._difficulty_params()
        self._show_toast(
            f"难度：{level}\n体力间隔 {p['stamina_tick_ms']//1000}s · 游戏/暴露/对战同步调整",
            PIXEL_COLOR,
            duration_ms=3200,
        )

    def _mark_hint_seen(self, key: str) -> None:
        hints = self.app_config.setdefault("seen_hints", {})
        if not isinstance(hints, dict):
            hints = {}
            self.app_config["seen_hints"] = hints
        hints[key] = True
        _save_app_config(self.app_config)

    def _show_once_hint(self, key: str, *, duration_ms: int = TOAST_DURATION_MS) -> None:
        hints = self.app_config.get("seen_hints", {})
        if isinstance(hints, dict) and hints.get(key):
            return
        text = ONCE_HINTS.get(key, "")
        if not text:
            return
        self._mark_hint_seen(key)
        self._show_toast(text, "#88ccff", duration_ms=duration_ms)

    def _maybe_show_first_run_guide(self) -> None:
        hints = self.app_config.get("seen_hints", {})
        if isinstance(hints, dict) and hints.get("operation_guide"):
            return
        self._open_operation_guide(auto=True)

    def _hint_seen(self, key: str) -> bool:
        hints = self.app_config.get("seen_hints", {})
        return isinstance(hints, dict) and bool(hints.get(key))

    def _open_operation_guide(self, *, auto: bool = False) -> None:
        if not auto:
            self._hide_main_menu()
        if self.operation_guide_win and self.operation_guide_win.winfo_exists():
            self.operation_guide_win.lift()
            return
        if auto:
            self._mark_hint_seen("operation_guide")
        self.operation_guide_win = tk.Toplevel(self.root)
        self.operation_guide_win.title("操作说明")
        self.operation_guide_win.attributes("-topmost", True)
        self.operation_guide_win.configure(bg=MENU_BG)
        _, frame = _pack_fixed_scroll_panel(self.operation_guide_win)
        tk.Label(frame, text="操作说明", font=PIXEL_FONT, fg=PIXEL_COLOR, bg=MENU_BG).pack(anchor=tk.W)
        tk.Label(
            frame,
            text=OPERATION_GUIDE_INDEX,
            font=PIXEL_FONT,
            fg=MENU_FG,
            bg=MENU_BG,
            justify=tk.LEFT,
            wraplength=360,
        ).pack(anchor=tk.W, pady=(8, 6))

        topic_order = ("basic", "modes", "games", "music_game", "panel", "system")
        for key in topic_order:
            info = GUIDE_TOPICS.get(key)
            if not info:
                continue
            tk.Button(
                frame,
                text=f"▶ {info['title']}",
                command=lambda k=key: self._open_guide_topic(k),
                font=PIXEL_FONT,
                bg=MENU_ACTIVE,
                fg=MENU_FG,
                relief=tk.FLAT,
                anchor=tk.W,
                cursor="hand2",
            ).pack(fill=tk.X, pady=2)

        tk.Button(
            frame,
            text="知道了",
            command=lambda: self.operation_guide_win.destroy() if self.operation_guide_win else None,
            font=PIXEL_FONT,
            bg="#555555",
            fg=MENU_FG,
        ).pack(anchor=tk.E, pady=(10, 0))
        self._place_panel_popup(self.operation_guide_win)

    def _open_guide_topic(self, key: str) -> None:
        info = GUIDE_TOPICS.get(key)
        if not info:
            return
        win = tk.Toplevel(self.root)
        win.title(str(info["title"]))
        win.attributes("-topmost", True)
        win.configure(bg=MENU_BG)
        _, outer = _pack_fixed_scroll_panel(win)
        tk.Label(outer, text=str(info["title"]), font=PIXEL_FONT, fg=PIXEL_COLOR, bg=MENU_BG).pack(anchor=tk.W)
        tk.Label(
            outer,
            text=str(info.get("body", "")),
            font=PIXEL_FONT,
            fg=MENU_FG,
            bg=MENU_BG,
            justify=tk.LEFT,
            wraplength=340,
        ).pack(anchor=tk.W, pady=(8, 0))

        for label, url in info.get("links") or ():
            _pack_web_link(outer, label, url, prefix="链接 · ")

        tk.Button(
            outer,
            text="返回",
            command=win.destroy,
            font=PIXEL_FONT,
            bg=MENU_ACTIVE,
            fg=MENU_FG,
        ).pack(anchor=tk.E, pady=(10, 0))
        self._place_panel_popup(win)

    def _open_rhythm_carnival_info(self) -> None:
        self._hide_main_menu()
        win = tk.Toplevel(self.root)
        win.title("官方音游说明")
        win.attributes("-topmost", True)
        win.configure(bg=MENU_BG)
        _, frame = _pack_fixed_scroll_panel(win)
        tk.Label(frame, text="官方音游介绍", font=PIXEL_FONT, fg=PIXEL_COLOR, bg=MENU_BG).pack(anchor=tk.W)
        tk.Label(
            frame,
            text=RHYTHM_CARNIVAL_INTRO,
            font=PIXEL_FONT,
            fg=MENU_FG,
            bg=MENU_BG,
            justify=tk.LEFT,
            wraplength=380,
        ).pack(anchor=tk.W, pady=(8, 6))
        _pack_web_link(frame, RHYTHM_CARNIVAL_TITLE, RHYTHM_CARNIVAL_URL, prefix="· ")
        _pack_web_link(frame, "Nitro+CHiRAL 官网", ABOUT_NITROCHIRAL_URL, prefix="· ")
        tk.Button(
            frame,
            text="关闭",
            command=win.destroy,
            font=PIXEL_FONT,
            bg=MENU_ACTIVE,
            fg=MENU_FG,
        ).pack(anchor=tk.E, pady=(10, 0))
        self._place_panel_popup(win)

    def _ensure_first_play_guide(self, key: str, on_continue) -> None:
        """首次进入某玩法时弹出操作指南，确认后再继续。"""
        hint_key = f"first_play:{key}"
        if self._hint_seen(hint_key):
            on_continue()
            return
        info = FIRST_PLAY_GUIDES.get(key) or GUIDE_TOPICS.get(key)
        if not info:
            self._mark_hint_seen(hint_key)
            on_continue()
            return
        self._hide_main_menu()
        win = tk.Toplevel(self.root)
        win.title(str(info.get("title", "操作指南")))
        win.attributes("-topmost", True)
        win.configure(bg=MENU_BG)
        _, frame = _pack_fixed_scroll_panel(win)
        tk.Label(
            frame,
            text=str(info.get("title", "操作指南")),
            font=PIXEL_FONT,
            fg=PIXEL_COLOR,
            bg=MENU_BG,
        ).pack(anchor=tk.W)
        tk.Label(
            frame,
            text="（首次进入 · 之后可在 系统→操作说明 查阅）",
            font=("Courier New", 9),
            fg="#888888",
            bg=MENU_BG,
        ).pack(anchor=tk.W, pady=(2, 6))
        tk.Label(
            frame,
            text=str(info.get("body", "")),
            font=PIXEL_FONT,
            fg=MENU_FG,
            bg=MENU_BG,
            justify=tk.LEFT,
            wraplength=400,
        ).pack(anchor=tk.W)

        for label, url in info.get("links") or ():
            _pack_web_link(frame, label, url, prefix="链接 · ")

        done = {"ok": False}

        def finish() -> None:
            if done["ok"]:
                return
            done["ok"] = True
            self._mark_hint_seen(hint_key)
            try:
                win.destroy()
            except Exception:
                pass
            on_continue()

        win.protocol("WM_DELETE_WINDOW", finish)
        tk.Button(
            frame,
            text="知道了，开始",
            command=finish,
            font=PIXEL_FONT,
            bg=MENU_ACTIVE,
            fg=MENU_FG,
        ).pack(anchor=tk.E, pady=(12, 0))
        self._place_panel_popup(win)
        try:
            win.focus_force()
        except Exception:
            pass

    def _poll_hotkey(self) -> None:
        if not self.hotkey_ids or not self._alive():
            return
        msg = wintypes.MSG()
        hwnd = self.root.winfo_id()
        while ctypes.windll.user32.PeekMessageW(
            ctypes.byref(msg), hwnd, WM_HOTKEY, WM_HOTKEY, 1
        ):
            if msg.message == WM_HOTKEY:
                for hotkey_id, _key, action in HOTKEY_ACTIONS:
                    if msg.wParam == hotkey_id:
                        self._handle_hotkey_action(action)
                        break
        self._safe_after(100, self._poll_hotkey)

    def _alive(self) -> bool:
        if self._closing:
            return False
        try:
            return self.root.winfo_exists()
        except tk.TclError:
            return False

    def _cancel_timer_job(self, attr: str) -> None:
        job = getattr(self, attr, None)
        if not job:
            return
        try:
            self.root.after_cancel(job)
        except Exception:
            pass
        setattr(self, attr, None)

    def _safe_after(self, ms: int, fn) -> str | None:
        if not self._alive():
            return None

        def wrapped() -> None:
            if not self._alive():
                return
            try:
                fn()
            except tk.TclError:
                pass

        try:
            return self.root.after(ms, wrapped)
        except tk.TclError:
            return None

    def _cancel_follow_chain(self) -> None:
        self.follow_animating = False
        self._cancel_timer_job("follow_tick_job")
        self._cancel_timer_job("follow_anim_job")

    def _schedule_follow_tick(self, ms: int | None = None) -> None:
        if ms is None:
            ms = FOLLOW_MOVE_INTERVAL_MS
        self._cancel_timer_job("follow_tick_job")
        if self.mode != "follow" or not self._alive():
            return
        self.follow_tick_job = self._safe_after(ms, self._follow_tick)

    def _place_window(self, *, light: bool = False) -> None:
        display_y = self.y + self.click_bounce_offset
        self.root.geometry(f"{self.display_size}x{self.display_size}+{self.x}+{display_y}")
        # 拖动时用节流跟随，避免菜单跟着狂跳不好点
        self._reposition_pet_attached_popups(force=False)
        if light:
            return
        self._place_ai_chat()
        self._place_interact_fx()
        self._place_music_wave()
        self._place_happy_fx()
        self._place_rain_fx()
        self._place_bulb_fx()
        self._place_food_fx()
        self._place_shy_fx()
        self._place_follow_dizzy_fx()
        self._place_all_mini_pet_waves()
        self._sync_all_mini_pet_bg_fx(place_only=True)
        self._place_wait_hint()

    def _set_image(self, photo: ImageTk.PhotoImage) -> None:
        self.label.config(image=photo)
        self.label.image = photo
        if not self.sprites:
            return
        sleep_sprites = (self.sprites.sleep[0], self.sprites.sleep[1])
        if photo in sleep_sprites:
            if not self.sleep_zzz_win or not self.sleep_zzz_win.winfo_exists():
                self._show_sleep_zzz()
            else:
                self._place_sleep_zzz()
        elif self.sleep_zzz_win and self.sleep_zzz_win.winfo_exists():
            self._hide_sleep_zzz()

    def _hide_sub_menu(self) -> None:
        if self.sub_menu and self.sub_menu.winfo_exists():
            self.sub_menu.destroy()
        self.sub_menu = None

    def _cancel_main_menu_auto_hide(self) -> None:
        self._cancel_timer_job("menu_hide_job")

    def _schedule_main_menu_auto_hide(self) -> None:
        self._cancel_main_menu_auto_hide()
        if not (self.menu_bar and self.menu_bar.winfo_exists()):
            return
        self.menu_hide_job = self._safe_after(MAIN_MENU_AUTO_CLOSE_MS, self._hide_main_menu)

    def _bump_main_menu_auto_hide(self) -> None:
        if self.menu_bar and self.menu_bar.winfo_exists():
            self._schedule_main_menu_auto_hide()

    def _hide_main_menu(self) -> None:
        self._cancel_main_menu_auto_hide()
        self._cancel_timer_job("pet_menu_follow_job")
        self._hide_sub_menu()
        if self.menu_bar and self.menu_bar.winfo_exists():
            self.menu_bar.destroy()
        self.menu_bar = None

    def _menu_btn(self, parent: tk.Misc, text: str, command, *, icon: str | None = None) -> tk.Button:
        kwargs = dict(
            text=text,
            command=command,
            font=PIXEL_FONT,
            fg=MENU_FG,
            bg=MENU_BG,
            activeforeground=MENU_FG,
            activebackground=MENU_ACTIVE,
            relief=tk.FLAT,
            padx=10,
            pady=4,
            bd=0,
            cursor="hand2",
        )
        if icon:
            photo = _menu_kind_icon_photo(icon, 16)
            kwargs.update(image=photo, compound=tk.LEFT, padx=6)
            btn = tk.Button(parent, **kwargs)
            # 防止 PhotoImage 被回收
            btn._menu_icon_photo = photo  # type: ignore[attr-defined]
            return btn
        return tk.Button(parent, **kwargs)

    def _show_sub_menu(self, items: list, offset_x: int = 0) -> None:
        self._hide_sub_menu()
        self.sub_menu = tk.Toplevel(self.root)
        self.sub_menu.overrideredirect(True)
        self.sub_menu.attributes("-topmost", True)
        self.sub_menu.configure(bg=MENU_BG)

        frame = tk.Frame(self.sub_menu, bg=MENU_BG, padx=2, pady=2)
        frame.pack()

        for item in items:
            icon = None
            if len(item) == 3:
                label, cmd, icon = item
            else:
                label, cmd = item
            if "▶" in label:
                handler = lambda c=cmd: (self._hide_sub_menu(), c())
            else:
                handler = lambda c=cmd: (self._hide_main_menu(), c())
            btn = self._menu_btn(frame, label, handler, icon=icon)
            btn.pack(fill=tk.X, pady=1)

        self._sub_menu_offset_x = offset_x
        self._place_pet_attached_popup(self.sub_menu, self.x + offset_x, self._sub_menu_pref_y())
        self._bump_main_menu_auto_hide()

    def _toggle_main_menu(self, event: tk.Event) -> None:
        if self._startup_busy():
            return
        if self.menu_bar and self.menu_bar.winfo_exists():
            self._hide_main_menu()
            return

        self.menu_bar = tk.Toplevel(self.root)
        self.menu_bar.overrideredirect(True)
        self.menu_bar.attributes("-topmost", True)
        self.menu_bar.configure(bg=MENU_BG)

        frame = tk.Frame(self.menu_bar, bg=MENU_BG, padx=2, pady=2)
        frame.pack()

        modules = [
            ("模式", self._open_mode_menu),
            ("面板", self._open_panel_menu),
            ("互动", self._open_interact_menu),
            ("系统", self._open_system_menu),
        ]
        for idx, (label, cmd) in enumerate(modules):
            handler = lambda c=cmd: (self._bump_main_menu_auto_hide(), c())
            btn = self._menu_btn(frame, label, handler)
            btn.pack(side=tk.LEFT, padx=1)

        self._place_pet_attached_popup(
            self.menu_bar,
            self.x,
            self.y + self.display_size + PET_MENU_GAP_Y,
        )
        self._pet_menu_follow_ms = int(time.time() * 1000)
        self._schedule_main_menu_auto_hide()
        self._schedule_pet_menu_follow()

    def _supports_walk_idle(self) -> bool:
        return self.mode in ("free", "stroll")

    def _open_mode_menu(self) -> None:
        follow_label = "跟随 ✓" if self.mode == "follow" else "跟随"
        free_label = "自由 ✓" if self.mode == "free" else "自由"
        stroll_label = "漫步 ✓" if self.mode == "stroll" else "漫步"
        quiet_label = "睡眠 ✓" if self.mode == "quiet" else "睡眠"
        game_label = "采集 ✓" if self.mode == "game" else "采集"
        music_label = "音乐 ✓" if self.music_sprite_mode else "音乐"
        self._show_sub_menu(
            [
                (follow_label, self._enable_follow),
                (free_label, self._enable_free),
                (stroll_label, self._enable_stroll),
                (quiet_label, self._enable_quiet),
                ("工作 ▶", self._open_work_mode_menu),
                ("游戏 ▶", self._open_mode_game_menu),
                (music_label, self._toggle_music_mode, "music"),
            ],
            offset_x=0,
        )

    def _work_mode_config(self) -> dict:
        default = {"show_props": True, "show_stack": True}
        raw = self.app_config.get("work_mode", {})
        if isinstance(raw, dict):
            return {**default, **raw}
        return default

    def _set_work_mode_setting(self, key: str, value: bool) -> None:
        cfg = self.app_config.setdefault("work_mode", {"show_props": True, "show_stack": True})
        cfg[key] = value
        _save_app_config(self.app_config)
        label = "显示目的地" if key == "show_props" else "显示运送货物"
        self._show_toast(f"{label}：{'开' if value else '关'}", PIXEL_COLOR)
        if self.state == "work":
            self._sync_work_overlay()

    def _open_work_mode_menu(self) -> None:
        active = self.mode == "work"
        toggle_label = "停止工作 ✓" if active else "开始工作"
        show_props = self._work_mode_config().get("show_props", True)
        show_stack = self._work_mode_config().get("show_stack", True)
        self._show_sub_menu(
            [
                (toggle_label, self._toggle_work_mode),
                (f"显示目的地{' ✓' if show_props else ''}", lambda: self._set_work_mode_setting("show_props", not show_props)),
                (
                    f"显示运送货物{' ✓' if show_stack else ''}",
                    lambda: self._set_work_mode_setting("show_stack", not show_stack),
                ),
            ],
            offset_x=120,
        )

    def _toggle_work_mode(self) -> None:
        if self.mode == "work":
            self._enable_free()
        else:
            self._enable_work()

    def _open_mode_game_menu(self) -> None:
        gather_label = "采集 ✓" if self.mode == "game" else "采集"
        rhythm_label = "音乐 ✓" if self.rhythm_active else "音乐 ▶"
        self._show_sub_menu(
            [
                (gather_label, self._enable_game),
                ("打字 ▶", self._open_typing_lang_menu),
                ("背单词 ▶", self._open_vocab_lang_menu),
                ("生词本 ▶", self._open_vocab_notebook_menu),
                (rhythm_label, self._open_music_game_menu, "music"),
                ("持有者排名", self._open_leaderboard),
            ],
            offset_x=120,
        )

    def _open_music_game_menu(self) -> None:
        self._show_sub_menu(
            [
                ("选曲开始 ▶", self._open_rhythm_track_menu),
                ("官方音游说明", self._open_rhythm_carnival_info),
            ],
            offset_x=180,
        )

    def _open_rhythm_track_menu(self) -> None:
        self._hide_main_menu()
        self._open_music_track_plate_picker(
            title="选曲开始",
            current_id=self._music_playlist()[0] if self._music_playlist() else DEFAULT_MUSIC_TRACK,
            on_pick=lambda tid: self._open_rhythm_length_menu(tid),
        )

    def _open_music_track_plate_picker(
        self,
        *,
        title: str,
        current_id: str | None,
        on_pick,
    ) -> None:
        """带边框像素图标的曲目选择。"""
        old = getattr(self, "music_track_picker_win", None)
        if old and old.winfo_exists():
            try:
                old.destroy()
            except Exception:
                pass

        win = tk.Toplevel(self.root)
        self.music_track_picker_win = win
        win.title(title)
        win.attributes("-topmost", True)
        win.configure(bg="#161822")
        _fit_panel_wh(win, 420, 460)
        setattr(win, "_panel_scroll_installed", True)

        head = tk.Frame(win, bg="#161822", padx=10, pady=8)
        head.pack(fill=tk.X)
        tk.Label(head, text=title, font=PIXEL_FONT, fg="#88ccff", bg="#161822").pack(side=tk.LEFT)
        tk.Label(head, text="像素图标", font=("Courier New", 9, "bold"), fg="#778899", bg="#161822").pack(
            side=tk.RIGHT
        )

        wrap = tk.Frame(win, bg="#161822")
        wrap.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        canvas = tk.Canvas(wrap, bg="#12141c", highlightthickness=0)
        scroll = tk.Scrollbar(wrap, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        grid = tk.Frame(canvas, bg="#12141c")
        grid_id = canvas.create_window((0, 0), window=grid, anchor="nw")

        photos: list[ImageTk.PhotoImage] = []
        self._music_picker_photos = photos
        cur = MUSIC_TRACK_LEGACY_IDS.get(str(current_id or ""), str(current_id or ""))

        def on_configure(_e=None) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfigure(grid_id, width=canvas.winfo_width())

        grid.bind("<Configure>", on_configure)
        canvas.bind("<Configure>", on_configure)

        def pick(tid: str) -> None:
            try:
                win.destroy()
            except Exception:
                pass
            self.music_track_picker_win = None
            on_pick(tid)

        for i, tid in enumerate(MUSIC_TRACK_ORDER):
            track = _music_track(tid)
            r, c = divmod(i, MUSIC_PICKER_COLS)
            cell = tk.Frame(grid, bg="#1a1e2a", padx=4, pady=4, highlightthickness=2)
            cell.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")
            on = tid == cur
            cell.configure(highlightbackground="#66aaff" if on else "#2a3144")
            photo = _music_track_icon_photo(tid, MUSIC_PLATE_ICON_PX)
            photos.append(photo)
            btn = tk.Button(
                cell,
                image=photo,
                command=lambda t=tid: pick(t),
                bg="#1a1e2a",
                activebackground="#24304a",
                relief=tk.FLAT,
                bd=0,
            )
            btn.pack()
            name = str(track["title"])
            if len(name) > 14:
                name = name[:13] + "…"
            tk.Label(
                cell,
                text=name,
                font=("Courier New", 8, "bold"),
                fg="#dde6ff" if on else "#a8b4cc",
                bg="#1a1e2a",
                wraplength=88,
                justify=tk.CENTER,
            ).pack(pady=(2, 0))
            for wdg in (cell, btn):
                wdg.bind("<Button-1>", lambda _e, t=tid: pick(t))

        for c in range(MUSIC_PICKER_COLS):
            grid.grid_columnconfigure(c, weight=1)

        def on_mousewheel(event: tk.Event) -> None:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)

        def on_close() -> None:
            try:
                canvas.unbind_all("<MouseWheel>")
            except Exception:
                pass
            self.music_track_picker_win = None
            try:
                win.destroy()
            except Exception:
                pass

        win.protocol("WM_DELETE_WINDOW", on_close)
        self._place_panel_popup(win)

    def _open_music_playlist_picker(self, *, on_confirm) -> None:
        """多选播放列表：点图标切换选中，至少保留一首。"""
        old = getattr(self, "music_track_picker_win", None)
        if old and old.winfo_exists():
            try:
                old.destroy()
            except Exception:
                pass

        selected: set[str] = set(self._music_playlist())
        cell_refs: dict[str, tk.Frame] = {}

        win = tk.Toplevel(self.root)
        self.music_track_picker_win = win
        win.title("播放列表")
        win.attributes("-topmost", True)
        win.configure(bg="#161822")
        _fit_panel_wh(win, 420, 500)
        setattr(win, "_panel_scroll_installed", True)

        head = tk.Frame(win, bg="#161822", padx=10, pady=8)
        head.pack(fill=tk.X)
        tk.Label(head, text="播放列表", font=PIXEL_FONT, fg="#88ccff", bg="#161822").pack(side=tk.LEFT)
        count_lbl = tk.Label(head, text="", font=("Courier New", 9, "bold"), fg="#778899", bg="#161822")
        count_lbl.pack(side=tk.RIGHT)

        wrap = tk.Frame(win, bg="#161822")
        wrap.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 4))
        canvas = tk.Canvas(wrap, bg="#12141c", highlightthickness=0)
        scroll = tk.Scrollbar(wrap, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        grid = tk.Frame(canvas, bg="#12141c")
        grid_id = canvas.create_window((0, 0), window=grid, anchor="nw")

        photos: list[ImageTk.PhotoImage] = []
        self._music_picker_photos = photos

        def refresh_count() -> None:
            n = len(selected)
            if n <= 1:
                count_lbl.config(text=f"已选 {n} 首（单曲循环）")
            else:
                count_lbl.config(text=f"已选 {n} 首")

        def paint_cell(tid: str) -> None:
            cell = cell_refs.get(tid)
            if cell and cell.winfo_exists():
                on = tid in selected
                cell.configure(highlightbackground="#66aaff" if on else "#2a3144")

        def toggle(tid: str) -> None:
            if tid in selected:
                if len(selected) <= 1:
                    self._show_toast("至少保留一首", "#ff8844")
                    return
                selected.remove(tid)
            else:
                selected.add(tid)
            paint_cell(tid)
            refresh_count()

        def on_configure(_e=None) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfigure(grid_id, width=canvas.winfo_width())

        grid.bind("<Configure>", on_configure)
        canvas.bind("<Configure>", on_configure)

        for i, tid in enumerate(MUSIC_TRACK_ORDER):
            track = _music_track(tid)
            r, c = divmod(i, MUSIC_PICKER_COLS)
            cell = tk.Frame(grid, bg="#1a1e2a", padx=4, pady=4, highlightthickness=2)
            cell.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")
            cell_refs[tid] = cell
            on = tid in selected
            cell.configure(highlightbackground="#66aaff" if on else "#2a3144")
            photo = _music_track_icon_photo(tid, MUSIC_PLATE_ICON_PX)
            photos.append(photo)
            btn = tk.Button(
                cell,
                image=photo,
                command=lambda t=tid: toggle(t),
                bg="#1a1e2a",
                activebackground="#24304a",
                relief=tk.FLAT,
                bd=0,
            )
            btn.pack()
            name = str(track["title"])
            if len(name) > 14:
                name = name[:13] + "…"
            tk.Label(
                cell,
                text=name,
                font=("Courier New", 8, "bold"),
                fg="#dde6ff" if on else "#a8b4cc",
                bg="#1a1e2a",
                wraplength=88,
                justify=tk.CENTER,
            ).pack(pady=(2, 0))
            for wdg in (cell, btn):
                wdg.bind("<Button-1>", lambda _e, t=tid: toggle(t))

        for c in range(MUSIC_PICKER_COLS):
            grid.grid_columnconfigure(c, weight=1)

        refresh_count()

        foot = tk.Frame(win, bg="#161822", padx=10, pady=8)
        foot.pack(fill=tk.X)

        def confirm() -> None:
            order = [tid for tid in MUSIC_TRACK_ORDER if tid in selected]
            on_confirm(order)
            on_close()

        def select_default() -> None:
            selected.clear()
            selected.add(DEFAULT_MUSIC_TRACK)
            for tid in cell_refs:
                paint_cell(tid)
            refresh_count()

        def select_all() -> None:
            selected.clear()
            selected.update(MUSIC_TRACK_ORDER)
            for tid in cell_refs:
                paint_cell(tid)
            refresh_count()

        tk.Button(foot, text="默认曲", command=select_default, font=PIXEL_FONT, bg=MENU_ACTIVE, fg=MENU_FG).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        tk.Button(foot, text="全选", command=select_all, font=PIXEL_FONT, bg=MENU_ACTIVE, fg=MENU_FG).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        tk.Button(foot, text="确定", command=confirm, font=PIXEL_FONT, bg="#334466", fg="#ffcc66").pack(side=tk.RIGHT)

        def on_mousewheel(event: tk.Event) -> None:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)

        def on_close() -> None:
            try:
                canvas.unbind_all("<MouseWheel>")
            except Exception:
                pass
            self.music_track_picker_win = None
            try:
                win.destroy()
            except Exception:
                pass

        win.protocol("WM_DELETE_WINDOW", on_close)
        self._place_panel_popup(win)

    def _open_rhythm_length_menu(self, track_id: str) -> None:
        self._show_sub_menu(
            [
                ("全曲", lambda: self._start_rhythm_game(track_id=track_id, play_cap_ms=0)),
                ("90 秒", lambda: self._start_rhythm_game(track_id=track_id, play_cap_ms=RHYTHM_SHORT_CAP_MS)),
            ],
            offset_x=300,
        )

    def _open_typing_lang_menu(self) -> None:
        items: list[tuple[str, callable]] = [
            ("中文", lambda: self._start_typing_game("中文")),
            ("英语", lambda: self._start_typing_game("英语")),
        ]
        if _japanese_bank_available():
            items.append(("日语 ▶", self._open_typing_jp_mode_menu))
        else:
            items.append(("日语（未开放）", lambda: self._show_toast("此功能暂不开放", "#ff8844")))
        self._show_sub_menu(items, offset_x=180)

    def _open_typing_jp_mode_menu(self) -> None:
        self._show_sub_menu(
            [
                ("平假名/片假名", lambda: self._start_typing_game(JAPANESE_LANG_LABEL, jp_mode=JP_TYPING_MODE_KANA)),
                ("罗马音", lambda: self._start_typing_game(JAPANESE_LANG_LABEL, jp_mode=JP_TYPING_MODE_ROMAJI)),
            ],
            offset_x=300,
        )

    def _open_vocab_lang_menu(self) -> None:
        items: list[tuple[str, callable]] = [
            ("英语", lambda: self._open_vocab_game("英语")),
            ("中文", lambda: self._open_vocab_game("中文")),
        ]
        if _japanese_bank_available():
            items.append(("日语", lambda: self._open_vocab_game("日语")))
        else:
            items.append(("日语（未开放）", lambda: self._show_toast("此功能暂不开放", "#ff8844")))
        self._show_sub_menu(items, offset_x=180)

    def _open_vocab_notebook_menu(self) -> None:
        book = _load_vocab_notebook()
        items: list[tuple[str, callable]] = []
        for lang in ("中文", "英语", "日语"):
            n = len(book.get(lang, []))
            items.append((f"{lang}（{n}）", lambda L=lang: self._open_vocab_notebook(L)))
        self._show_sub_menu(items, offset_x=180)

    def _close_vocab_notebook(self) -> None:
        if self.vocab_notebook_win and self.vocab_notebook_win.winfo_exists():
            self.vocab_notebook_win.destroy()
        self.vocab_notebook_win = None

    def _open_vocab_notebook(self, lang: str) -> None:
        self._hide_main_menu()
        self._close_vocab_notebook()
        book = _load_vocab_notebook()
        rows = list(book.get(lang, []))
        win = tk.Toplevel(self.root)
        self.vocab_notebook_win = win
        win.title(f"生词本 · {lang}")
        win.attributes("-topmost", True)
        win.configure(bg=MENU_BG)
        win.protocol("WM_DELETE_WINDOW", self._close_vocab_notebook)
        w, h = _fit_panel_wh(win, PANEL_FIXED_W, PANEL_FIXED_H)
        frame = tk.Frame(win, bg=MENU_BG, padx=10, pady=8)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text=f"生词本 · {lang}（{len(rows)}）", font=PIXEL_FONT, fg=PIXEL_COLOR, bg=MENU_BG).pack(
            anchor=tk.W
        )
        tk.Label(
            frame,
            text="答错会自动收录；复习答对后移出。",
            font=PIXEL_FONT,
            fg="#888888",
            bg=MENU_BG,
        ).pack(anchor=tk.W, pady=(2, 6))

        btns = tk.Frame(frame, bg=MENU_BG)
        btns.pack(fill=tk.X, pady=(0, 6))

        def review() -> None:
            if not rows:
                self._show_toast("生词本是空的", "#ff8844")
                return
            self._close_vocab_notebook()
            self._open_vocab_game(lang, pool=rows, from_notebook=True)

        def clear_all() -> None:
            _clear_vocab_notebook_lang(lang)
            self._show_toast(f"已清空{lang}生词本", "#88ccff")
            self._open_vocab_notebook(lang)

        tk.Button(btns, text="复习", command=review, font=PIXEL_FONT, bg="#334466", fg="#ffcc66", relief=tk.FLAT).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        tk.Button(btns, text="清空", command=clear_all, font=PIXEL_FONT, bg="#553333", fg="#ffaaaa", relief=tk.FLAT).pack(
            side=tk.LEFT
        )

        scroll_wrap, inner, _canvas = _make_scrollable_frame(
            frame, width=max(200, w - 48), height=max(160, h - 120), bg=MENU_BG
        )
        scroll_wrap.pack(fill=tk.BOTH, expand=True)
        setattr(win, "_panel_scroll_installed", True)
        if not rows:
            tk.Label(inner, text="（暂无生词）", font=PIXEL_FONT, fg="#666666", bg=MENU_BG).pack(anchor=tk.W, pady=8)
        else:
            for item in rows:
                row = tk.Frame(inner, bg=MENU_BG)
                row.pack(fill=tk.X, pady=3)
                txt = f"{item.get('word', '')}\n{item.get('meaning', '')}"
                tk.Label(
                    row,
                    text=txt,
                    font=PIXEL_FONT,
                    fg=MENU_FG,
                    bg=MENU_BG,
                    justify=tk.LEFT,
                    wraplength=240,
                    anchor=tk.W,
                ).pack(side=tk.LEFT, fill=tk.X, expand=True)

                def remove_one(w=str(item.get("word", "")), L=lang) -> None:
                    _remove_vocab_notebook_item(L, w)
                    self._open_vocab_notebook(L)

                tk.Button(
                    row,
                    text="删",
                    command=remove_one,
                    font=PIXEL_FONT,
                    bg="#444444",
                    fg=MENU_FG,
                    relief=tk.FLAT,
                    padx=4,
                ).pack(side=tk.RIGHT, padx=(4, 0))
        self._place_panel_popup(win)

    def _toggle_music_mode(self) -> None:
        self._toggle_music_interact()

    def _food_inventory_total(self) -> int:
        return sum(self.food_inventory.values())

    def _format_food_counts(self, counts: dict[str, int]) -> str:
        parts = [f"{FOODS[fid]['label']}×{cnt}" for fid, cnt in counts.items() if cnt > 0 and fid in FOODS]
        return "  ".join(parts) if parts else "无"

    def _add_food_to_inventory(self, food_id: str, amount: int = 1) -> None:
        if food_id not in FOODS:
            return
        self.food_inventory[food_id] = self.food_inventory.get(food_id, 0) + amount
        self.game_session_food[food_id] = self.game_session_food.get(food_id, 0) + amount
        self._persist_food_inventory()
        self._refresh_panel()

    def _exit_to_free(self, _event=None) -> None:
        """按 Esc 退出游戏/AI 对话/日程/互动等，回到自由模式。"""
        self._cancel_pending_mode_switch()
        self._hide_main_menu()
        self._hide_toast()
        self._close_ai_chat()
        if self.preset_dialog_job:
            try:
                self.root.after_cancel(self.preset_dialog_job)
            except Exception:
                pass
            self.preset_dialog_job = None
        if self.schedule_win and self.schedule_win.winfo_exists():
            self.schedule_win.destroy()
            self.schedule_win = None
        for attr in (
            "diary_win",
            "weather_win",
            "music_track_picker_win",
            "gallery_win",
            "panel_backpack_win",
            "phonograph_win",
            "typing_game_win",
            "vocab_game_win",
            "vocab_notebook_win",
            "panel_settings_win",
            "about_win",
            "feedback_win",
            "rhyme_fight_win",
            "operation_guide_win",
            "work_custom_win",
            "leaderboard_win",
            "rhythm_win",
        ):
            win = getattr(self, attr, None)
            if win and win.winfo_exists():
                win.destroy()
            setattr(self, attr, None)
        self.gallery_photos.clear()
        self._stop_phonograph_playback()
        self._phonograph_refresh = None
        self._close_rhyme_fight(resume=False)
        self._close_typing_game(resume=False)
        self._close_vocab_game(resume=False)
        self._close_rhythm_game(resume=False)
        self._hide_speech_dialog()
        self._stop_call_audio()
        self._cancel_action_end()
        self._cancel_idle_chain()
        self.sleep_interact_active = False
        self._hide_size_loading()
        self._hide_companion_loading()
        self._hide_food_fx()
        self._hide_happy_fx()
        self._hide_rain_fx()
        self._hide_bulb_fx()
        self._hide_game_clear()
        self._cancel_expose_qte()
        self._cancel_yesno_overlay()
        self._cancel_food_drag()
        self._hide_interact_fx()
        self._hide_like_fx()
        self._hide_shy_fx()
        self._hide_wink_fx()
        self._hide_follow_dizzy_fx()
        self._stop_music_wave_fx()
        self.music_sprite_mode = False
        self._stop_bg_music()
        if self.angry_anim_job:
            self.root.after_cancel(self.angry_anim_job)
            self.angry_anim_job = None
        was_game = self.mode == "game"
        if self.mode == "game":
            caught = self.game_catches
            session_food = dict(self.game_session_food)
            self._stop_game_mode()
            if caught > 0:
                detail = self._format_food_counts(session_food)
                toast = f"已回到自由模式\n本局获得 {caught} 个食物\n{detail}"
            else:
                toast = "已回到自由模式"
        elif self.mode == "quiet":
            self._leave_quiet_mode()
            toast = "已回到自由模式"
        elif self.mode == "follow":
            self.follow_animating = False
            toast = "已回到自由模式"
        elif self.mode == "work":
            toast = "已回到自由模式"
        else:
            toast = "已回到自由模式"
        if self.state == "work":
            self._stop_work_mode()
        if self.state == "sleep":
            self._wake_from_sleep()
        if self.state == "action":
            self.action_name = ""
        self.mode = "free"
        self.state = "stand"
        self._set_image(self.sprites.stand)
        self._place_window()
        self._show_toast(toast, PIXEL_COLOR, duration_ms=3500 if was_game else 2000)
        self._resume_idle()

    def _stop_game_mode(self) -> None:
        if self.game_spawn_job:
            self.root.after_cancel(self.game_spawn_job)
            self.game_spawn_job = None
        if self.game_tick_job:
            self.root.after_cancel(self.game_tick_job)
            self.game_tick_job = None
        for box in self.game_boxes:
            if box.get("win") and box["win"].winfo_exists():
                box["win"].destroy()
        self.game_boxes.clear()
        self._end_game_dizzy_stun()
        if self.game_hud_win and self.game_hud_win.winfo_exists():
            self.game_hud_win.destroy()
        self.game_hud_win = None
        self.game_hud_label = None
        self.game_overlay = None
        self.game_canvas = None

    def _stop_work_mode(self) -> None:
        self.work_animating = False
        self.work_continuous = False
        if self.work_encourage_job:
            try:
                self.root.after_cancel(self.work_encourage_job)
            except Exception:
                pass
            self.work_encourage_job = None
        self.work_boxes_since_banter = 0
        self.work_banter_last_ms = 0
        self._clear_work_anchored_boxes()
        self._hide_work_overlay()
        if self.work_start_box_win and self.work_start_box_win.winfo_exists():
            self.work_start_box_win.destroy()
        self.work_start_box_win = None
        self._hide_work_end_button()
        self.work_phase = ""
        self.work_carrying = False
        self.work_has_start_box = False

    def _cancel_idle_chain(self) -> None:
        self._cancel_follow_chain()
        for attr in (
            "idle_job",
            "walk_move_job",
            "walk_anim_job",
            "action_anim_job",
            "move_land_job",
            "food_fx_job",
            "happy_job",
            "sleep_interact_end_job",
        ):
            job = getattr(self, attr, None)
            if job:
                try:
                    self.root.after_cancel(job)
                except Exception:
                    pass
                setattr(self, attr, None)

    def _interrupt_current_interaction(self, *, reset_y: bool = True) -> None:
        """切换按键/动作时立刻结束当前效果（最高优先级）。"""
        self.interaction_token += 1
        self._cancel_idle_chain()
        self._hide_size_loading()
        self._hide_companion_loading()
        self._cancel_food_drag()
        self._cancel_action_end()
        self._cancel_action_defer()
        self._hide_speech_dialog()
        self._stop_call_audio()
        self._hide_food_fx()
        self._hide_happy_fx()
        self._hide_rain_fx()
        self._hide_bulb_fx()
        self._hide_interact_fx()
        self._hide_like_fx()
        self._hide_shy_fx()
        self._hide_wink_fx()
        self._hide_follow_dizzy_fx()
        self._cancel_expose_qte()
        self._cancel_game_countdown()
        self._cancel_yesno_overlay()
        self._stop_drag_move()
        self._stop_rest_bobble()
        self.sleep_interact_active = False
        if self.angry_anim_job:
            self.root.after_cancel(self.angry_anim_job)
            self.angry_anim_job = None
        if self.rest_peek_job:
            self.root.after_cancel(self.rest_peek_job)
            self.rest_peek_job = None
        if self.state == "sleep":
            self._wake_from_sleep()
        elif self.state == "work":
            self._stop_work_mode()
        self.click_bounce_offset = 0
        if reset_y and self.angry_lift_offset:
            self.y = self.angry_base_y
            self.angry_lift_offset = 0
        self.angry_walk_phase = False
        self.state = "stand"
        self.action_name = ""
        if self.mode != "game":
            self._set_image(self._current_stand_sprite())
            self._place_window()

    def _interrupt_for_mode_switch(self) -> None:
        """切换模式时打断睡眠/工作/互动等，模式切换优先。"""
        self._interrupt_current_interaction()
        if self.follow_dizzy_job:
            self.root.after_cancel(self.follow_dizzy_job)
            self.follow_dizzy_job = None
        self._cancel_follow_chain()
        self._end_drag_dizzy()
        self._hide_follow_dizzy_fx()
        self.follow_dizzy = False
        self.follow_spin_dir = 0
        self.follow_spin_steps = 0
        self.follow_dir_change_times.clear()
        self.follow_last_dir = ""
        self._hide_shy_fx()
        if self.mode == "game":
            self._stop_game_mode()
        if self.rhythm_active:
            self._close_rhythm_game(resume=False)

    def _apply_work_mode(self) -> None:
        self._interrupt_for_mode_switch()
        self._leave_quiet_mode()
        self.mode = "work"
        # 模式工作：持续运送；终点可拖；箱子数量不随机（持续到点结束）
        self._start_work_impl(WORK_BOX_TOTAL_DEFAULT, flag_movable=True, continuous=True)

    def _enable_work(self) -> None:
        if self.mode == "work":
            return
        self._request_mode_switch(self._apply_work_mode)

    def _leave_quiet_mode(self) -> None:
        if self.mode != "quiet":
            return
        if self.rest_peek_job:
            self.root.after_cancel(self.rest_peek_job)
            self.rest_peek_job = None
        self._stop_rest_bobble()
        self._hide_sleep_zzz()
        if self.state == "rest":
            self.state = "stand"
            self._set_image(self.sprites.stand)

    def _cancel_pending_mode_switch(self) -> None:
        if self.mode_switch_job:
            try:
                self.root.after_cancel(self.mode_switch_job)
            except Exception:
                pass
            self.mode_switch_job = None

    def _apply_free_transition(self) -> None:
        """切回自由模式（清理当前非自由状态）。"""
        self._cancel_pending_mode_switch()
        self._interrupt_for_mode_switch()
        self._leave_quiet_mode()
        if self.mode == "work":
            self._stop_work_mode()
        if self.mode == "game":
            self._stop_game_mode()
        self.mode = "free"
        self.follow_animating = False
        self.work_animating = False
        self._wake_from_sleep()
        self.state = "stand"
        self.action_name = ""
        self._clear_all_action_fx()
        self._set_image(self._current_stand_sprite())
        self._place_window()
        self._resume_idle()

    def _request_mode_switch(self, apply_fn: callable) -> None:
        """非自由 → 非自由 时，先回到自由模式，再进入目标模式。"""
        self._cancel_pending_mode_switch()
        self._hide_main_menu()
        self.mode_switch_token += 1
        tok = self.mode_switch_token

        def run_target() -> None:
            if tok != self.mode_switch_token:
                return
            self.mode_switch_job = None
            apply_fn()

        if self.mode == "free":
            run_target()
            return
        self._apply_free_transition()
        self.mode_switch_job = self.root.after(MODE_VIA_FREE_MS, run_target)

    def _apply_follow_mode(self) -> None:
        self._interrupt_for_mode_switch()
        self._leave_quiet_mode()
        self.mode = "follow"
        self.follow_animating = False
        self.follow_spin_dir = 0
        self.follow_spin_steps = 0
        self.state = "stand"
        self._set_image(self.sprites.stand)
        self._resume_idle()

    def _apply_stroll_mode(self) -> None:
        self._interrupt_for_mode_switch()
        self._leave_quiet_mode()
        self.mode = "stroll"
        self.follow_animating = False
        self._wake_from_sleep()
        self.state = "stand"
        self._set_image(self._current_stand_sprite())
        self._resume_idle()

    def _apply_quiet_mode(self) -> None:
        self._interrupt_for_mode_switch()
        self.mode = "quiet"
        self.follow_animating = False
        self.rest_base_y = self.y
        self.state = "rest"
        self._set_image(self.sprites.sleep[1])
        self._show_sleep_zzz()
        self._schedule_rest_bobble()

    def _enable_follow(self) -> None:
        if self.mode == "follow":
            return
        self._request_mode_switch(self._apply_follow_mode)

    def _enable_free(self) -> None:
        self._cancel_pending_mode_switch()
        self.mode_switch_token += 1
        self._hide_main_menu()
        if self.mode == "free":
            self._resume_idle()
            return
        self._apply_free_transition()

    def _enable_stroll(self) -> None:
        if self.mode == "stroll":
            return
        self._request_mode_switch(self._apply_stroll_mode)

    def _enable_quiet(self) -> None:
        if self.mode == "quiet":
            return
        self._request_mode_switch(self._apply_quiet_mode)

    def _enable_game(self) -> None:
        if self.mode == "game":
            return

        def begin() -> None:
            self._interrupt_for_mode_switch()
            self._leave_quiet_mode()
            self.mode = "game"
            self.state = "game"
            self.game_score = 0
            self.game_catches = 0
            self.game_misses = 0
            self.game_session_food = {}
            self.game_start_ms = int(time.time() * 1000)
            self.game_boxes.clear()
            self._end_game_dizzy_stun()
            self._set_image(self.sprites.stand)
            self._show_game_hud()
            self._mark_hint_seen("game_mode")
            self._game_tick()
            self._game_spawn_box()

        def after_guide() -> None:
            self._request_mode_switch(lambda: self._start_game_countdown(begin))

        self._ensure_first_play_guide("gather", after_guide)

    def _game_time_left_ms(self) -> int:
        elapsed = int(time.time() * 1000) - self.game_start_ms
        return max(0, GAME_DURATION_MS - elapsed)

    def _show_game_hud(self) -> None:
        if self.game_hud_win and self.game_hud_win.winfo_exists():
            self.game_hud_win.destroy()
        self.game_hud_win = tk.Toplevel(self.root)
        self.game_hud_win.overrideredirect(True)
        self.game_hud_win.attributes("-topmost", True)
        self.game_hud_win.configure(bg="#111122")
        border = tk.Frame(self.game_hud_win, bg="#88ccff", padx=1, pady=1)
        border.pack()
        inner = tk.Frame(border, bg="#111122", padx=10, pady=6)
        inner.pack()
        self.game_hud_label = tk.Label(
            inner, text="", font=PIXEL_FONT, fg="#88ccff", bg="#111122", justify=tk.LEFT
        )
        self.game_hud_label.pack()
        self._update_game_hud()

    def _update_game_hud(self) -> None:
        if not self.game_hud_label or not self.game_hud_win or not self.game_hud_win.winfo_exists():
            return
        left_ms = self._game_time_left_ms()
        sec = left_ms // 1000
        self.game_hud_label.config(
            text=(
                f"⏱ {sec:02d}s    食物 {self.game_catches}\n"
                f"接住 {self.game_catches}  错过 {self.game_misses}  库存 {self._food_inventory_total()}"
            )
        )
        self._place_popup(self.game_hud_win, self.x, max(0, self.y - 52))

    def _finish_game(self) -> None:
        if self.mode != "game":
            return
        catches = self.game_catches
        misses = self.game_misses
        score = self.game_score
        session_food = dict(self.game_session_food)
        self._stop_game_mode()
        self.mode = "free"
        self.state = "stand"
        self._set_image(self.sprites.stand)
        bonus_mood = min(5, catches // 3)
        if bonus_mood > 0:
            self.mood = min(100, self.mood + bonus_mood)
            self._refresh_panel()
        self._save_game_record(
            "gather",
            {
                "catches": catches,
                "misses": misses,
                "score": score,
                "difficulty": self.difficulty,
                "food": session_food,
            },
        )
        detail = self._format_food_counts(session_food)
        subtitle = f"接取 {catches} 个 · 得分 {score}\n错过 {misses}  ·  库存 {self._food_inventory_total()}\n{detail}"
        self._show_game_clear(
            title="采集完成",
            subtitle=subtitle,
            accent="#ffcc44",
            on_done=self._resume_idle,
        )

    def _hide_game_clear(self) -> None:
        if self.game_clear_job:
            try:
                self.root.after_cancel(self.game_clear_job)
            except Exception:
                pass
            self.game_clear_job = None
        if self.game_clear_win and self.game_clear_win.winfo_exists():
            self.game_clear_win.destroy()
        self.game_clear_win = None
        self.game_clear_canvas = None

    def _show_game_clear(
        self,
        *,
        title: str,
        subtitle: str = "",
        accent: str = "#44ff88",
        on_done=None,
        hold_ms: int = GAME_CLEAR_HOLD_MS,
        hero_grade: str | None = None,
        hero_color: str | None = None,
    ) -> None:
        self._hide_game_clear()
        self.game_clear_token += 1
        token = self.game_clear_token
        w, h = GAME_CLEAR_W, GAME_CLEAR_H
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        win = tk.Toplevel(self.root)
        self.game_clear_win = win
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg="#060612")
        win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        canvas = tk.Canvas(win, width=w, height=h, bg="#060612", highlightthickness=0)
        canvas.pack()
        self.game_clear_canvas = canvas
        particles = _spawn_game_clear_particles(w, h, hero_color or accent)
        meta = {
            "phase": 0,
            "title": title,
            "subtitle": subtitle,
            "accent": accent,
            "hero_grade": hero_grade,
            "hero_color": hero_color,
        }

        def finish() -> None:
            if token != self.game_clear_token:
                return
            self._hide_game_clear()
            if on_done:
                on_done()

        def tick() -> None:
            if token != self.game_clear_token or not canvas.winfo_exists():
                return
            _draw_game_clear_frame(
                canvas,
                w,
                h,
                meta["phase"],
                title=meta["title"],
                subtitle=meta["subtitle"],
                accent=meta["accent"],
                particles=particles,
                hero_grade=meta["hero_grade"],
                hero_color=meta["hero_color"],
            )
            meta["phase"] += 1
            if meta["phase"] < GAME_CLEAR_FRAMES:
                self.game_clear_job = self.root.after(GAME_CLEAR_MS, tick)
            else:
                self.game_clear_job = self.root.after(hold_ms, finish)

        tick()

    def _cancel_action_defer(self) -> None:
        if self.action_defer_job:
            try:
                self.root.after_cancel(self.action_defer_job)
            except Exception:
                pass
            self.action_defer_job = None

    def _cancel_action_end(self) -> None:
        if self.action_end_job:
            self.root.after_cancel(self.action_end_job)
            self.action_end_job = None

    def _defer_until_not_dragging(self, callback) -> None:
        if not self.dragging:
            callback()
            return
        self._cancel_action_defer()

        def step() -> None:
            self.action_defer_job = None
            if not self._alive():
                return
            if not self.dragging:
                callback()
                return
            self.action_defer_job = self._safe_after(120, step)

        self.action_defer_job = self._safe_after(120, step)

    def _schedule_action_end(
        self,
        *,
        dialog_text: str | None = None,
        callback=None,
        duration_ms: int | None = None,
        action: str | None = None,
        char_ms: int | None = None,
    ) -> None:
        self._cancel_action_end()
        if dialog_text:
            delay = _typing_duration_ms(dialog_text, char_ms=char_ms)
        elif duration_ms is not None:
            delay = duration_ms
        elif action:
            delay = INTERACT_DURATIONS.get(action, INTERACT_DURATIONS["default"])
        else:
            delay = INTERACT_DURATIONS["default"]
        cb = callback or self._after_action
        self.action_end_job = self.root.after(delay, cb)

    def _open_food_menu(self, offset_x: int = 120) -> None:
        self._open_eat_food_menu(offset_x=offset_x)

    def _open_eat_food_menu(self, offset_x: int = 120) -> None:
        total = self._food_inventory_total()
        if total <= 0:
            self._show_toast("还没有食物哦，去模式→游戏接食物吧！", "#ff8844", duration_ms=3000)
            return
        items: list[tuple[str, callable, bool]] = []
        food_items = sorted(FOODS.items(), key=lambda item: (item[1]["mood"], item[1]["stamina"]), reverse=True)
        for food_id, info in food_items:
            count = self.food_inventory.get(food_id, 0)
            label = f"{info['label']} ×{count}  体+{info['stamina']} 心+{info['mood']}"
            enabled = count > 0
            items.append(
                (
                    label,
                    lambda fid=food_id: (self._hide_main_menu(), self._start_food_drag(fid)),
                    enabled,
                )
            )
        self._show_food_pick_menu(items, offset_x=offset_x)

    def _show_food_pick_menu(
        self, items: list[tuple[str, callable, bool]], offset_x: int = 0
    ) -> None:
        self._hide_sub_menu()
        self.sub_menu = tk.Toplevel(self.root)
        self.sub_menu.overrideredirect(True)
        self.sub_menu.attributes("-topmost", True)
        self.sub_menu.configure(bg=MENU_BG)
        frame = tk.Frame(self.sub_menu, bg=MENU_BG, padx=2, pady=2)
        frame.pack()
        tk.Label(
            frame,
            text=f"吃东西  拖给小人 ({self._food_inventory_total()})",
            font=PIXEL_FONT,
            fg=PIXEL_COLOR,
            bg=MENU_BG,
        ).pack(fill=tk.X, pady=(2, 4))
        food_ids = list(FOODS.keys())
        for idx, (label, cmd, enabled) in enumerate(items):
            row = tk.Frame(frame, bg=MENU_BG)
            row.pack(fill=tk.X, pady=1)
            icon = tk.Canvas(row, width=28, height=28, bg=MENU_BG, highlightthickness=0)
            icon.pack(side=tk.LEFT, padx=(4, 2))
            _draw_pixel_food(icon, food_ids[idx], 4, 2, px=3)
            btn = self._menu_btn(row, label, lambda c=cmd: c())
            if not enabled:
                btn.config(state=tk.DISABLED, fg="#666666")
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._sub_menu_offset_x = offset_x
        self._place_pet_attached_popup(self.sub_menu, self.x + offset_x, self._sub_menu_pref_y())
        self._bump_main_menu_auto_hide()

    def _cancel_food_drag(self) -> None:
        self.food_drag_active = False
        self.food_drag_id = None
        if self.food_drag_win and self.food_drag_win.winfo_exists():
            self.food_drag_win.destroy()
        self.food_drag_win = None
        self.food_drag_canvas = None
        try:
            self.root.unbind("<B1-Motion>")
            self.root.unbind("<ButtonRelease-1>")
        except Exception:
            pass

    def _start_food_drag(self, food_id: str) -> None:
        if self.dragging or food_id not in FOODS:
            return
        if self.state == "action" and self.action_name == "eat":
            return
        if self.food_inventory.get(food_id, 0) <= 0:
            self._show_toast("这种食物没有了！", "#ff8844")
            return
        self._interrupt_current_interaction()
        self.food_drag_active = True
        self.food_drag_id = food_id
        size = FOOD_DRAG_ICON
        self.food_drag_win = tk.Toplevel(self.root)
        self.food_drag_win.overrideredirect(True)
        self.food_drag_win.attributes("-topmost", True)
        self.food_drag_win.configure(bg="magenta")
        self.food_drag_win.wm_attributes("-transparentcolor", "magenta")
        self.food_drag_canvas = tk.Canvas(
            self.food_drag_win, width=size, height=size, bg="magenta", highlightthickness=0
        )
        self.food_drag_canvas.pack()
        px = max(3, size // 10)
        _draw_pixel_food(self.food_drag_canvas, food_id, 4, 4, px=px)
        mx = self.root.winfo_pointerx()
        my = self.root.winfo_pointery()
        self.food_drag_win.geometry(f"+{mx - size // 2}+{my - size // 2}")
        self.food_drag_ignore_release_until = int(time.time() * 1000) + 180
        self.root.bind("<B1-Motion>", self._food_drag_motion, add="+")
        self.root.bind("<ButtonRelease-1>", self._food_drag_release, add="+")
        self._show_toast("拖动食物到小人上方松开", "#44aa44", duration_ms=2000)

    def _food_drag_motion(self, event: tk.Event) -> None:
        if not self.food_drag_active or not self.food_drag_win:
            return
        if self.state == "action" and self.action_name == "eat":
            return
        size = FOOD_DRAG_ICON
        self.food_drag_win.geometry(f"+{event.x_root - size // 2}+{event.y_root - size // 2}")

    def _food_drag_release(self, event: tk.Event) -> None:
        if not self.food_drag_active or not self.food_drag_id:
            return
        if self.state == "action" and self.action_name == "eat":
            self._cancel_food_drag()
            return
        if int(time.time() * 1000) < getattr(self, "food_drag_ignore_release_until", 0):
            return
        food_id = self.food_drag_id
        start_x = event.x_root
        start_y = event.y_root
        pet_cx = self.x + self.display_size // 2
        pet_cy = self.y + self.display_size // 2
        catch = math.hypot(start_x - pet_cx, start_y - pet_cy) < self.display_size * 0.65
        self._cancel_food_drag()
        if catch:
            self._animate_food_drop_feed(food_id, start_x, start_y)
        else:
            self._show_toast("没喂到…再试一次吧", "#ff8844")

    def _animate_food_drop_feed(self, food_id: str, start_x: int, start_y: int) -> None:
        if food_id not in FOODS or self.food_inventory.get(food_id, 0) <= 0:
            return
        target_x = self.x + self.display_size // 2
        target_y = self.y + self.display_size // 4
        size = FOOD_DRAG_ICON
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg="magenta")
        win.wm_attributes("-transparentcolor", "magenta")
        canvas = tk.Canvas(win, width=size, height=size, bg="magenta", highlightthickness=0)
        canvas.pack()
        px = max(3, size // 10)
        _draw_pixel_food(canvas, food_id, 4, 4, px=px)

        steps = max(8, FOOD_DROP_MS // 40)
        start_ms = int(time.time() * 1000)

        def tick() -> None:
            elapsed = int(time.time() * 1000) - start_ms
            t = min(1.0, elapsed / FOOD_DROP_MS)
            ease = t * t
            x = int(start_x + (target_x - start_x) * ease - size // 2)
            arc = int(math.sin(t * math.pi) * FOOD_DROP_ARC)
            y = int(start_y + (target_y - start_y) * ease - size // 2 - arc)
            if t >= 1.0:
                if win.winfo_exists():
                    win.destroy()
                self._interact_flair("eat", banter=True)
                self._feed_food(food_id, from_drag=True)
                return
            win.geometry(f"+{x}+{y}")
            self.root.after(40, tick)

        tick()

    def _open_backpack_menu(self, offset_x: int = 120) -> None:
        self._open_eat_food_menu(offset_x=offset_x)

    def _feed_food(self, food_id: str, *, from_drag: bool = False) -> None:
        if self.dragging or food_id not in FOODS:
            return
        if self.food_inventory.get(food_id, 0) <= 0:
            self._show_toast("这种食物没有了，去玩游戏接更多吧！", "#ff8844")
            return
        if self.mode == "game":
            self._show_toast("游戏中请先 Esc 退出再接食物", "#ff8844")
            return
        self._interrupt_current_interaction()
        self._hide_main_menu()
        self.food_inventory[food_id] -= 1
        self._persist_food_inventory()
        self._refresh_panel()
        info = FOODS[food_id]
        old_stamina = self.stamina
        old_mood = self.mood
        self.stamina = min(100, self.stamina + info["stamina"])
        self.mood = min(100, self.mood + info["mood"])
        stamina_gain = self.stamina - old_stamina
        mood_gain = self.mood - old_mood
        self._refresh_panel()
        if not from_drag:
            self._interact_flair("eat", banter=True)
        self._show_toast(f"{info['label']}  体力 +{stamina_gain}  心情 +{mood_gain}", "#44aa44")
        self._play_eat_food(food_id)

    def _play_eat_sound(self) -> None:
        sound = _get_eat_sound()
        self._play_sound_with_volume(sound, "sfx")

    def _play_eat_food(self, food_id: str) -> None:
        self._cancel_food_drag()
        if self.mode == "quiet" and self.state == "rest":
            self._stop_rest_bobble()
        self.state = "action"
        self.action_name = "eat"
        self.action_frame = 0
        frames = self.sprites.actions["eat"]
        self._set_image(frames[0])
        self._play_eat_sound()
        self._show_food_fx(food_id)
        if len(frames) > 1:
            self._action_animate()
        self._schedule_action_end(action="eat")

    def _start_music_wave_fx(self) -> None:
        self._stop_music_wave_fx()
        if not self.music_sprite_mode:
            return
        pad = 28
        size = self.display_size + pad * 2
        self.music_wave_win = tk.Toplevel(self.root)
        self.music_wave_win.overrideredirect(True)
        self.music_wave_win.attributes("-topmost", False)
        self.music_wave_win.configure(bg="magenta")
        self.music_wave_win.wm_attributes("-transparentcolor", "magenta")
        self.music_wave_canvas = tk.Canvas(
            self.music_wave_win, width=size, height=size, bg="magenta", highlightthickness=0
        )
        self.music_wave_canvas.pack()
        self.music_wave_phase = 0
        self._place_music_wave()
        self._animate_music_wave()

    def _stop_music_wave_fx(self) -> None:
        if self.music_wave_win and self.music_wave_win.winfo_exists():
            self.music_wave_win.destroy()
        self.music_wave_win = None
        self.music_wave_canvas = None
        self._sync_mini_pet_music_waves()

    def _place_music_wave(self) -> None:
        if not self.music_wave_win or not self.music_wave_win.winfo_exists():
            return
        pad = 28
        display_y = self.y + self.click_bounce_offset
        self.music_wave_win.geometry(f"+{self.x - pad}+{display_y - pad}")

    def _animate_music_wave(self) -> None:
        if not self.music_wave_canvas or not self.music_sprite_mode:
            self._stop_music_wave_fx()
            return
        pad = 28
        size = self.display_size + pad * 2
        beat = 1.0
        try:
            import pygame

            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pos = pygame.mixer.music.get_pos()
                if pos >= 0:
                    beat = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(pos * 0.014))
        except Exception:
            pass
        _draw_music_wave(self.music_wave_canvas, size, size, self.music_wave_phase, beat=beat)
        self.music_wave_phase += 1
        self._place_music_wave()
        self.root.after(MUSIC_WAVE_MS, self._animate_music_wave)

    def _open_panel_menu(self) -> None:
        companion_label = "智能伴侣 ✓" if self.companion_bar_enabled else "智能伴侣"
        self._show_sub_menu(
            [
                ("打开面板", lambda: (self._hide_main_menu(), self._toggle_panel())),
                ("莱姆 ▶", self._open_rhyme_menu),
                (companion_label, self._toggle_companion_bar),
                ("暴露", self._play_expose_qte),
            ],
            offset_x=60,
        )

    def _open_my_menu(self) -> None:
        items: list[tuple[str, callable]] = []
        if PET_ID_FEATURE and self.pet_id is not None:
            items.append(("桌宠编号", self._show_pet_id))
        items.extend(
            [
                ("日记", self._open_diary_manager),
                ("日程提醒", self._open_schedule_manager),
                ("天气预报", self._open_weather_forecast),
            ]
        )
        self._show_sub_menu(items, offset_x=120)

    def _show_pet_id(self) -> None:
        self._hide_main_menu()
        if not PET_ID_FEATURE or self.pet_id is None:
            self._show_toast("当前为无编号版本", PIXEL_COLOR)
            return
        created = self.pet_profile.get("created", "")
        extra = f"\n注册于 {created}" if created else ""
        self._show_toast(f"桌宠编号\n{_format_pet_id(self.pet_id)}{extra}", "#88ccff", duration_ms=4500)

    def _pick_vocab_word(self) -> dict[str, str] | None:
        if not self.vocab_words:
            return None
        return random.choice(self.vocab_words)

    def _maybe_vocab_dialogue(self) -> None:
        if self.mode == "free" or self.state != "stand":
            return
        if random.random() > VOCAB_DIALOGUE_CHANCE:
            return
        if self.speech_dialog and self.speech_dialog.winfo_exists():
            return
        item = self._pick_vocab_word()
        if not item:
            return
        word = item.get("word", "")
        meaning = item.get("meaning", "")
        if not word:
            return
        line = random.choice(
            [
                f"诶，今天学到一个词：{word}！\n意思是：{meaning}",
                f"哇——{word}！\n{meaning}，记住了吗？",
                f"来复习一下：{word} = {meaning} ♪",
            ]
        )
        self._show_speech_dialog(line, auto_hide_ms=3200)
        self._add_diary_entry(f"词库触发：{word} — {meaning}", auto=True)

    def _add_diary_entry(self, text: str, *, auto: bool = False) -> None:
        entry = {
            "id": str(uuid4()),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M"),
            "text": text.strip(),
            "mood": self.mood,
            "auto": auto,
        }
        if not entry["text"]:
            return
        self.diary_entries.insert(0, entry)
        self.diary_entries = self.diary_entries[:200]
        _save_diary(self.diary_entries)

    def _open_diary_manager(self) -> None:
        self._hide_main_menu()
        if self.diary_win and self.diary_win.winfo_exists():
            self.diary_win.destroy()
            self.diary_win = None
            return

        self.diary_win = tk.Toplevel(self.root)
        self.diary_win.title("日记")
        self.diary_win.attributes("-topmost", True)
        self.diary_win.configure(bg=MENU_BG)

        _, frame = _pack_fixed_scroll_panel(self.diary_win)
        tk.Label(frame, text="日记", font=PIXEL_FONT, fg=PIXEL_COLOR, bg=MENU_BG).pack(anchor=tk.W)

        input_row = tk.Frame(frame, bg=MENU_BG)
        input_row.pack(fill=tk.X, pady=(8, 4))
        text_entry = tk.Entry(input_row, width=28, font=PIXEL_FONT)
        text_entry.pack(side=tk.LEFT, padx=(0, 4))

        list_frame = tk.Frame(frame, bg=MENU_BG)
        list_frame.pack(fill=tk.BOTH, pady=4)

        def refresh_list() -> None:
            for w in list_frame.winfo_children():
                w.destroy()
            for item in self.diary_entries[:30]:
                line = tk.Frame(list_frame, bg=MENU_BG)
                line.pack(fill=tk.X, pady=1)
                tag = "（自动）" if item.get("auto") else ""
                tk.Label(
                    line,
                    text=f"{item.get('date', '?')} {item.get('time', '')}  {item.get('text', '')}{tag}",
                    font=PIXEL_FONT,
                    fg=MENU_FG,
                    bg=MENU_BG,
                    wraplength=320,
                    justify=tk.LEFT,
                ).pack(side=tk.LEFT)
                rid = item.get("id")

                def delete(r=rid) -> None:
                    self.diary_entries = [d for d in self.diary_entries if d.get("id") != r]
                    _save_diary(self.diary_entries)
                    refresh_list()

                tk.Button(line, text="删", command=delete, font=PIXEL_FONT, bg=MENU_BG, fg="#ff6666").pack(
                    side=tk.RIGHT
                )

        def add_item() -> None:
            txt = text_entry.get().strip()
            if not txt:
                return
            self._add_diary_entry(txt)
            text_entry.delete(0, tk.END)
            refresh_list()

        tk.Button(input_row, text="记一笔", command=add_item, font=PIXEL_FONT, bg=MENU_ACTIVE, fg=MENU_FG).pack(
            side=tk.LEFT
        )
        refresh_list()
        self._place_panel_popup(self.diary_win)

    def _open_weather_forecast(self) -> None:
        self._hide_main_menu()
        if self.weather_win and self.weather_win.winfo_exists():
            self._close_weather_forecast()
            return

        self.weather_win = tk.Toplevel(self.root)
        self.weather_win.title("天气预报")
        self.weather_win.attributes("-topmost", True)
        self.weather_win.configure(bg="#1a2030")
        _fit_panel_wh(self.weather_win, WEATHER_W, WEATHER_H)
        self.weather_win.protocol("WM_DELETE_WINDOW", self._close_weather_forecast)
        self.weather_photos = []

        frame = tk.Frame(self.weather_win, bg="#1a2030", padx=10, pady=8)
        frame.pack(fill=tk.BOTH, expand=True)

        head = tk.Frame(frame, bg="#1a2030")
        head.pack(fill=tk.X)
        title_icon = _weather_icon_photo("sunny", 32)
        self.weather_photos.append(title_icon)
        tk.Label(head, image=title_icon, bg="#1a2030").pack(side=tk.LEFT)
        tk.Label(head, text=" 天气预报", font=PIXEL_FONT, fg="#88ccff", bg="#1a2030").pack(side=tk.LEFT)

        city_row = tk.Frame(frame, bg="#1a2030")
        city_row.pack(fill=tk.X, pady=(8, 4))
        tk.Label(city_row, text="城市", font=PIXEL_FONT, fg="#c8d8ff", bg="#1a2030").pack(side=tk.LEFT)
        city_var = tk.StringVar(value=str(self.app_config.get("weather_city") or "北京"))
        city_entry = tk.Entry(city_row, textvariable=city_var, width=12, font=PIXEL_FONT)
        city_entry.pack(side=tk.LEFT, padx=6)

        canvas = tk.Canvas(frame, width=WEATHER_W - 24, height=WEATHER_H - 150, bg="#121826", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True, pady=(4, 6))
        status = tk.Label(frame, text="正在获取天气…", font=PIXEL_FONT, fg="#a8b8dd", bg="#1a2030")
        status.pack(anchor=tk.W)

        preset_row = tk.Frame(frame, bg="#1a2030")
        preset_row.pack(fill=tk.X, pady=(2, 0))

        def pick_city(name: str) -> None:
            city_var.set(name)
            load_weather()

        for name in ("北京", "上海", "广州", "杭州", "成都", "深圳"):
            tk.Button(
                preset_row,
                text=name,
                command=lambda n=name: pick_city(n),
                font=("Courier New", 9, "bold"),
                bg="#2a3450",
                fg="#dde8ff",
                relief=tk.FLAT,
                padx=4,
            ).pack(side=tk.LEFT, padx=2)

        def render(payload: dict, city_label: str) -> None:
            if not self.weather_win or not self.weather_win.winfo_exists():
                return
            canvas.delete("all")
            self.weather_photos = [title_icon]
            w = WEATHER_W - 24
            canvas.create_rectangle(0, 0, w, WEATHER_H, fill="#121826", outline="")
            for i in range(0, w, 8):
                canvas.create_line(i, 0, i, WEATHER_H, fill="#161e30")
            cur = payload.get("current") or {}
            daily = payload.get("daily") or {}
            code = int(cur.get("weather_code", 3) or 3)
            desc, kind = _weather_code_info(code)
            icon = _weather_icon_photo(kind, 64)
            self.weather_photos.append(icon)
            temp = cur.get("temperature_2m")
            feels = cur.get("apparent_temperature")
            hum = cur.get("relative_humidity_2m")
            wind = cur.get("wind_speed_10m")
            canvas.create_image(56, 58, image=icon)
            canvas.create_text(120, 28, text=city_label, fill="#88ccff", font=PIXEL_FONT, anchor="w")
            canvas.create_text(
                120,
                56,
                text=f"{temp:.0f}°C  {desc}" if isinstance(temp, (int, float)) else desc,
                fill="#ffffff",
                font=("Courier New", 14, "bold"),
                anchor="w",
            )
            detail_bits = []
            if isinstance(feels, (int, float)):
                detail_bits.append(f"体感 {feels:.0f}°")
            if isinstance(hum, (int, float)):
                detail_bits.append(f"湿度 {hum:.0f}%")
            if isinstance(wind, (int, float)):
                detail_bits.append(f"风 {wind:.0f} km/h")
            canvas.create_text(
                120,
                82,
                text="  ·  ".join(detail_bits) if detail_bits else "—",
                fill="#a8b8dd",
                font=("Courier New", 10, "bold"),
                anchor="w",
            )
            deco = _weather_icon_photo(kind, 24)
            self.weather_photos.append(deco)
            canvas.create_image(w - 36, 36, image=deco)

            canvas.create_text(12, 118, text="未来七日", fill="#66aaff", font=PIXEL_FONT, anchor="w")
            canvas.create_line(12, 132, w - 12, 132, fill="#2a3a58")

            times = daily.get("time") or []
            codes = daily.get("weather_code") or []
            tmax = daily.get("temperature_2m_max") or []
            tmin = daily.get("temperature_2m_min") or []
            pop = daily.get("precipitation_probability_max") or []
            n = min(7, len(times), len(codes), len(tmax), len(tmin))
            if n <= 0:
                canvas.create_text(w // 2, 220, text="暂无预报数据", fill="#ff8866", font=PIXEL_FONT)
                status.config(text="数据不完整", fg="#ff8866")
                return
            col_w = (w - 16) // n
            weekdays = "一二三四五六日"
            for i in range(n):
                x = 8 + i * col_w + col_w // 2
                y0 = 150
                try:
                    dt = datetime.strptime(str(times[i])[:10], "%Y-%m-%d")
                    day_lab = "今天" if i == 0 else f"周{weekdays[dt.weekday()]}"
                    md = dt.strftime("%m/%d")
                except Exception:
                    day_lab, md = f"D{i+1}", ""
                d_code = int(codes[i] or 3)
                d_desc, d_kind = _weather_code_info(d_code)
                d_icon = _weather_icon_photo(d_kind, 32)
                self.weather_photos.append(d_icon)
                canvas.create_rectangle(
                    x - col_w // 2 + 2,
                    y0 - 8,
                    x + col_w // 2 - 2,
                    y0 + 168,
                    fill="#1a2438" if i % 2 == 0 else "#162032",
                    outline="#2a3a58",
                )
                canvas.create_text(x, y0 + 8, text=day_lab, fill="#c8d8ff", font=("Courier New", 9, "bold"))
                canvas.create_text(x, y0 + 24, text=md, fill="#7788aa", font=("Courier New", 8, "bold"))
                canvas.create_image(x, y0 + 54, image=d_icon)
                hi = tmax[i]
                lo = tmin[i]
                temp_txt = ""
                if isinstance(hi, (int, float)) and isinstance(lo, (int, float)):
                    temp_txt = f"{hi:.0f}/{lo:.0f}°"
                canvas.create_text(x, y0 + 88, text=temp_txt, fill="#ffffff", font=("Courier New", 9, "bold"))
                canvas.create_text(x, y0 + 108, text=d_desc, fill="#88aacc", font=("Courier New", 8, "bold"))
                p = pop[i] if i < len(pop) else None
                if isinstance(p, (int, float)):
                    canvas.create_text(x, y0 + 128, text=f"雨{p:.0f}%", fill="#66ccff", font=("Courier New", 8, "bold"))
            updated = datetime.now().strftime("%H:%M:%S")
            status.config(text=f"已更新 {updated} · 数据来源 Open-Meteo", fg="#88ffaa")

        def load_weather() -> None:
            name = city_var.get().strip() or "北京"
            self.app_config["weather_city"] = name
            _save_app_config(self.app_config)
            status.config(text="正在获取天气…", fg="#a8b8dd")
            canvas.delete("all")
            canvas.create_text((WEATHER_W - 24) // 2, 160, text="读取中…", fill="#8899bb", font=PIXEL_FONT)
            token = getattr(self, "_weather_fetch_token", 0) + 1
            self._weather_fetch_token = token

            def worker() -> None:
                err = ""
                payload = None
                label = name
                try:
                    geo = _geocode_city_name(name)
                    if not geo:
                        raise ValueError(f"找不到城市「{name}」")
                    label, lat, lon = geo
                    payload = _fetch_open_meteo_weather(lat, lon)
                except Exception as e:
                    err = str(e) or "获取失败"

                def apply() -> None:
                    if token != getattr(self, "_weather_fetch_token", 0):
                        return
                    if not self.weather_win or not self.weather_win.winfo_exists():
                        return
                    if payload is None:
                        canvas.delete("all")
                        canvas.create_text(
                            (WEATHER_W - 24) // 2,
                            160,
                            text=f"获取失败\n{err[:48]}",
                            fill="#ff8866",
                            font=PIXEL_FONT,
                            justify=tk.CENTER,
                        )
                        status.config(text="请检查网络后重试", fg="#ff8866")
                        return
                    render(payload, label)

                self.root.after(0, apply)

            threading.Thread(target=worker, daemon=True).start()

        tk.Button(
            city_row, text="查询", command=load_weather, font=PIXEL_FONT, bg="#3a5080", fg="#ffffff"
        ).pack(side=tk.LEFT, padx=4)
        tk.Button(
            city_row, text="刷新", command=load_weather, font=PIXEL_FONT, bg="#2a4058", fg="#dde8ff"
        ).pack(side=tk.LEFT)
        city_entry.bind("<Return>", lambda _e: load_weather())
        self._place_panel_popup(self.weather_win)
        load_weather()

    def _close_weather_forecast(self) -> None:
        self._weather_fetch_token = getattr(self, "_weather_fetch_token", 0) + 1
        if self.weather_win and self.weather_win.winfo_exists():
            try:
                self.weather_win.destroy()
            except Exception:
                pass
        self.weather_win = None
        self.weather_photos = []

    def _open_gallery(self) -> None:
        self._hide_main_menu()
        if self.gallery_win and self.gallery_win.winfo_exists():
            self.gallery_win.destroy()
            self.gallery_win = None
            self.gallery_photos.clear()
            return

        groups = [g for g in _load_gallery_groups() if _gallery_group_files_exist(g)]
        self.gallery_photos = []
        self.gallery_win = tk.Toplevel(self.root)
        self.gallery_win.title("画廊")
        self.gallery_win.attributes("-topmost", True)
        self.gallery_win.configure(bg=MENU_BG)
        gh = GALLERY_PREVIEW_SIZE + GALLERY_SCROLL_H + 110
        _fit_panel_wh(self.gallery_win, GALLERY_WIN_W, gh)

        outer = tk.Frame(self.gallery_win, bg=MENU_BG, padx=8, pady=8)
        outer.pack(fill=tk.BOTH, expand=True)
        tk.Label(outer, text="画廊", font=PIXEL_FONT, fg=PIXEL_COLOR, bg=MENU_BG).pack(anchor=tk.W)
        tk.Label(
            outer,
            text="小窗浏览 · 列表可滚动 · 大图可切换差分",
            font=("Courier New", 9),
            fg="#888888",
            bg=MENU_BG,
        ).pack(anchor=tk.W, pady=(2, 6))

        preview_box = tk.Frame(outer, bg="#1a1a2e", padx=6, pady=6)
        preview_box.pack(fill=tk.X, pady=(0, 6))
        preview_stage = tk.Frame(
            preview_box, bg="#1a1a2e", width=GALLERY_PREVIEW_SIZE + 32, height=GALLERY_PREVIEW_SIZE + 12
        )
        preview_stage.pack()
        preview_stage.pack_propagate(False)
        preview_img = tk.Label(preview_stage, bg="#1a1a2e")
        preview_img.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        preview_index_lbl = tk.Label(
            preview_stage,
            text="",
            font=PIXEL_FONT,
            fg="#ffffff",
            bg="#334466",
            padx=6,
            pady=1,
        )
        preview_arrow_l = tk.Label(
            preview_stage,
            text="◀",
            font=("Courier New", 16, "bold"),
            fg="#88ccff",
            bg="#1a1a2e",
            cursor="hand2",
        )
        preview_arrow_r = tk.Label(
            preview_stage,
            text="▶",
            font=("Courier New", 16, "bold"),
            fg="#88ccff",
            bg="#1a1a2e",
            cursor="hand2",
        )
        preview_caption = tk.Label(preview_box, text="", font=PIXEL_FONT, fg=PIXEL_COLOR, bg="#1a1a2e")
        preview_caption.pack(pady=(4, 0))

        preview_state = {"group": None, "index": 0}

        def hide_arrows() -> None:
            preview_arrow_l.place_forget()
            preview_arrow_r.place_forget()

        def render_preview() -> None:
            group = preview_state["group"]
            if not group:
                preview_index_lbl.place_forget()
                hide_arrows()
                return
            idx = preview_state["index"]
            files = group.get("files") or ()
            photo = _gallery_frame_photo(group, idx, GALLERY_PREVIEW_SIZE, bg_hex="#1a1a2e")
            if photo is None:
                preview_caption.config(text=f"{group['title']}（文件缺失）")
                preview_index_lbl.place_forget()
                hide_arrows()
                return
            self.gallery_photos.append(photo)
            preview_img.config(image=photo)
            preview_img.image = photo
            preview_caption.config(text=str(group["title"]))
            total = len(files)
            if total > 1:
                preview_index_lbl.config(text=f"{idx + 1}/{total}")
                preview_index_lbl.place(relx=1.0, rely=1.0, anchor=tk.SE, x=-4, y=-4)
            else:
                preview_index_lbl.place_forget()
                hide_arrows()

        def show_group(group: dict, index: int = 0) -> None:
            files = group.get("files") or ()
            if not files:
                return
            preview_state["group"] = group
            preview_state["index"] = max(0, min(index, len(files) - 1))
            render_preview()

        def step_variant(delta: int) -> None:
            group = preview_state["group"]
            if not group:
                return
            files = group.get("files") or ()
            if len(files) <= 1:
                return
            new_idx = preview_state["index"] + delta
            if new_idx < 0 or new_idx >= len(files):
                return
            preview_state["index"] = new_idx
            render_preview()

        def on_preview_motion(event: tk.Event) -> None:
            group = preview_state["group"]
            if not group or len(group.get("files") or ()) <= 1:
                hide_arrows()
                return
            w = max(1, preview_stage.winfo_width())
            idx = preview_state["index"]
            total = len(group["files"])
            if event.x < w * GALLERY_ARROW_ZONE and idx > 0:
                preview_arrow_l.place(relx=0.0, rely=0.5, anchor=tk.W, x=2)
            else:
                preview_arrow_l.place_forget()
            if event.x > w * (1.0 - GALLERY_ARROW_ZONE) and idx < total - 1:
                preview_arrow_r.place(relx=1.0, rely=0.5, anchor=tk.E, x=-2)
            else:
                preview_arrow_r.place_forget()

        preview_stage.bind("<Motion>", on_preview_motion)
        preview_stage.bind("<Leave>", lambda _e: hide_arrows())
        preview_arrow_l.bind("<Button-1>", lambda _e: step_variant(-1))
        preview_arrow_r.bind("<Button-1>", lambda _e: step_variant(1))

        def on_preview_click(event: tk.Event) -> None:
            group = preview_state["group"]
            if not group or len(group.get("files") or ()) <= 1:
                return
            w = max(1, preview_stage.winfo_width())
            if event.x < w * GALLERY_ARROW_ZONE:
                step_variant(-1)
            elif event.x > w * (1.0 - GALLERY_ARROW_ZONE):
                step_variant(1)

        preview_stage.bind("<Button-1>", on_preview_click)
        self.gallery_win.bind("<Left>", lambda _e: step_variant(-1))
        self.gallery_win.bind("<Right>", lambda _e: step_variant(1))

        scroll_wrap, grid_wrap, _canvas = _make_scrollable_frame(
            outer, width=GALLERY_WIN_W - 36, height=GALLERY_SCROLL_H, bg=MENU_BG
        )
        scroll_wrap.pack(fill=tk.BOTH, expand=True)

        if not groups:
            tk.Label(grid_wrap, text="暂无可用立绘", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG).pack()
            preview_caption.config(text="暂无作品")
            self._place_panel_popup(self.gallery_win)
            return

        for i, group in enumerate(groups):
            row, col = divmod(i, GALLERY_COLS)
            cell = tk.Frame(grid_wrap, bg=MENU_BG, padx=3, pady=3)
            cell.grid(row=row, column=col, sticky=tk.N)
            thumb_wrap = tk.Frame(cell, bg=MENU_BG)
            thumb_wrap.pack()
            thumb = _gallery_frame_photo(group, 0, GALLERY_THUMB_SIZE)
            if thumb is None:
                continue
            self.gallery_photos.append(thumb)
            thumb_lbl = tk.Label(thumb_wrap, image=thumb, bg=MENU_BG, cursor="hand2")
            thumb_lbl.image = thumb
            thumb_lbl.pack()
            file_count = len(group.get("files") or ())
            if file_count > 1:
                tk.Label(
                    thumb_wrap,
                    text=f"×{file_count}",
                    font=("Courier New", 8),
                    fg="#ffffff",
                    bg="#4488ff",
                    padx=2,
                ).place(relx=1.0, rely=1.0, anchor=tk.SE)
            thumb_lbl.bind("<Button-1>", lambda _e, g=group: show_group(g, 0))
            tk.Label(cell, text=str(group["title"]), font=("Courier New", 9), fg=MENU_FG, bg=MENU_BG).pack(
                pady=(2, 0)
            )

        show_group(groups[0], 0)
        self._place_panel_popup(self.gallery_win)

    def _stop_phonograph_playback(self) -> None:
        if self.phonograph_play_job:
            try:
                self.root.after_cancel(self.phonograph_play_job)
            except Exception:
                pass
            self.phonograph_play_job = None
        self.phonograph_playing_id = None
        try:
            import pygame

            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass
        if self.phonograph_paused_music and self.music_sprite_mode:
            self.phonograph_paused_music = False
            self._start_bg_music()
        else:
            self.phonograph_paused_music = False
        self._refresh_phonograph_list_if_open()

    def _refresh_phonograph_list_if_open(self) -> None:
        refresh = getattr(self, "_phonograph_refresh", None)
        if refresh and self.phonograph_win and self.phonograph_win.winfo_exists():
            refresh()

    def _phonograph_playback_done(self, entry_id: str, token: int) -> None:
        self.phonograph_play_job = None
        if token != self.phonograph_play_token or self.phonograph_playing_id != entry_id:
            return
        self._stop_phonograph_playback()

    def _play_phonograph_entry(self, entry: dict) -> None:
        entry_id = str(entry.get("id", ""))
        if not entry_id:
            return
        if self.phonograph_playing_id == entry_id:
            self.phonograph_play_token += 1
            self._stop_phonograph_playback()
            return

        self._stop_call_audio()
        self.phonograph_play_token += 1
        token = self.phonograph_play_token
        self.phonograph_playing_id = entry_id
        category = str(entry.get("category", "voice"))
        kind = str(entry.get("kind", "file"))
        duration_ms = 0

        if kind == "file":
            path = entry.get("path")
            if path is None or not Path(path).exists():
                self._show_toast("找不到音频文件", "#ff8844")
                self._stop_phonograph_playback()
                return
            duration_ms = _get_wav_duration_ms(Path(path))
            try:
                import pygame

                _init_pygame_mixer()
                if not pygame.mixer.get_init():
                    raise RuntimeError("mixer unavailable")
                if self.bg_music_playing:
                    self.phonograph_paused_music = True
                    pygame.mixer.music.stop()
                    self.bg_music_playing = False
                pygame.mixer.music.load(str(path))
                pygame.mixer.music.set_volume(self._sound_scale(category))
                pygame.mixer.music.play()
            except Exception:
                self._show_toast("播放失败", "#ff6666")
                self._stop_phonograph_playback()
                return
        elif kind == "type_tick":
            sound = _get_type_sound()
            self._play_sound_with_volume(sound, "sfx")
            duration_ms = int(TYPE_TICK_SEC * 1000) + 120
        elif kind == "eat_sfx":
            sound = _get_eat_sound()
            self._play_sound_with_volume(sound, "sfx")
            duration_ms = 900
        elif kind == "reminder":
            sound = _get_reminder_sound()
            self._play_sound_with_volume(sound, "sfx")
            duration_ms = 700
        else:
            self._stop_phonograph_playback()
            return

        if duration_ms > 0:
            self.phonograph_play_job = self.root.after(
                duration_ms + 180,
                lambda eid=entry_id, tok=token: self._phonograph_playback_done(eid, tok),
            )
        self._refresh_phonograph_list_if_open()

    def _import_phonograph_audio(self, refresh) -> None:
        src = filedialog.askopenfilename(
            title="导入留声音频",
            filetypes=[
                ("音频文件", "*.wav *.mp3 *.mp4 *.m4a *.ogg *.flac"),
                ("所有文件", "*.*"),
            ],
        )
        if not src:
            return
        src_path = Path(src)
        if not src_path.is_file():
            return
        _ensure_data_dirs()
        entry_id = f"{int(time.time() * 1000):x}{random.randint(0, 0xFFFF):04x}"
        dst = PHONOGRAPH_USER_DIR / f"{entry_id}.wav"
        if src_path.suffix.lower() == ".wav":
            shutil.copy2(src_path, dst)
        else:
            converted = _ensure_audio_wav(src_path, dst)
            if converted is None:
                self._show_toast("无法转换该音频格式", "#ff6666")
                return
            dst = converted
        title = src_path.stem[:32] or "未命名"
        entries = _load_phonograph_user()
        entries.insert(0, {"id": entry_id, "title": title, "filename": dst.name})
        _save_phonograph_user(entries)
        self._show_toast(f"已收录：{title}", "#88ccff")
        refresh()

    def _remove_phonograph_entry(self, user_id: str, refresh) -> None:
        entries = _load_phonograph_user()
        target = next((e for e in entries if e.get("id") == user_id), None)
        if target is None:
            return
        if self.phonograph_playing_id == f"user:{user_id}":
            self._stop_phonograph_playback()
        path = _resolve_phonograph_user_path(target)
        entries = [e for e in entries if e.get("id") != user_id]
        _save_phonograph_user(entries)
        if path and path.is_file():
            try:
                path.unlink()
            except Exception:
                pass
        refresh()

    def _format_phonograph_duration(self, entry: dict) -> str:
        kind = str(entry.get("kind", "file"))
        if kind == "file":
            path = entry.get("path")
            if path and Path(path).exists():
                ms = _get_wav_duration_ms(Path(path))
                if ms > 0:
                    sec = ms // 1000
                    return f"{sec // 60}:{sec % 60:02d}"
        if kind in ("type_tick", "eat_sfx", "reminder"):
            return "短"
        return ""

    def _open_phonograph(self) -> None:
        self._hide_main_menu()
        if self.phonograph_win and self.phonograph_win.winfo_exists():
            self._stop_phonograph_playback()
            self.phonograph_win.destroy()
            self.phonograph_win = None
            self._phonograph_refresh = None
            return

        self.phonograph_win = tk.Toplevel(self.root)
        self.phonograph_win.title("留声")
        self.phonograph_win.attributes("-topmost", True)
        self.phonograph_win.configure(bg=MENU_BG)

        _, outer = _pack_fixed_scroll_panel(self.phonograph_win)
        tk.Label(outer, text="留声", font=PIXEL_FONT, fg=PIXEL_COLOR, bg=MENU_BG).pack(anchor=tk.W)
        tk.Label(
            outer,
            text="音频珍藏 · 内置音效与用户导入 · 再次点击正在播放的条目可停止",
            font=PIXEL_FONT,
            fg="#888888",
            bg=MENU_BG,
        ).pack(anchor=tk.W, pady=(2, 8))

        list_wrap = tk.Frame(outer, bg=MENU_BG)
        list_wrap.pack(fill=tk.BOTH, pady=(0, 8))

        btn_row = tk.Frame(outer, bg=MENU_BG)
        btn_row.pack(fill=tk.X)

        def refresh_list() -> None:
            for w in list_wrap.winfo_children():
                w.destroy()
            catalog = _build_phonograph_catalog()
            if not catalog:
                tk.Label(list_wrap, text="暂无音频，可点击下方导入", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG).pack(
                    anchor=tk.W
                )
                return
            for entry in catalog:
                line = tk.Frame(list_wrap, bg=MENU_BG)
                line.pack(fill=tk.X, pady=1)
                entry_id = str(entry.get("id", ""))
                playing = self.phonograph_playing_id == entry_id
                play_label = "■" if playing else "▶"
                play_btn = tk.Button(
                    line,
                    text=play_label,
                    width=2,
                    command=lambda e=entry: self._play_phonograph_entry(e),
                    font=PIXEL_FONT,
                    bg=MENU_ACTIVE if playing else MENU_BG,
                    fg=MENU_FG,
                )
                play_btn.pack(side=tk.LEFT, padx=(0, 4))
                tag = "内置" if entry.get("builtin") else "导入"
                tk.Label(
                    line,
                    text=f"[{tag}] {entry.get('title', '')}",
                    font=PIXEL_FONT,
                    fg=PIXEL_COLOR if playing else MENU_FG,
                    bg=MENU_BG,
                    width=22,
                    anchor=tk.W,
                ).pack(side=tk.LEFT)
                dur = self._format_phonograph_duration(entry)
                if dur:
                    tk.Label(line, text=dur, font=PIXEL_FONT, fg="#666666", bg=MENU_BG, width=5).pack(side=tk.LEFT)
                if not entry.get("builtin"):
                    uid = entry.get("user_id")

                    def remove(u=uid) -> None:
                        if u:
                            self._remove_phonograph_entry(str(u), refresh_list)

                    tk.Button(line, text="删", command=remove, font=PIXEL_FONT, bg=MENU_BG, fg="#ff6666").pack(
                        side=tk.RIGHT
                    )

        refresh_list()
        self._phonograph_refresh = refresh_list
        tk.Button(
            btn_row,
            text="导入音频",
            command=lambda: self._import_phonograph_audio(refresh_list),
            font=PIXEL_FONT,
            bg=MENU_ACTIVE,
            fg=MENU_FG,
        ).pack(side=tk.LEFT, padx=(0, 6))
        tk.Button(
            btn_row,
            text="停止播放",
            command=self._stop_phonograph_playback,
            font=PIXEL_FONT,
            bg=MENU_BG,
            fg=MENU_FG,
        ).pack(side=tk.LEFT)
        self._place_panel_popup(self.phonograph_win)

    def _open_memories_menu(self) -> None:
        self._show_sub_menu(
            [
                ("画廊", self._open_gallery),
                ("留声", self._open_phonograph),
            ],
            offset_x=360,
        )

    def _open_panel_settings(self) -> None:
        self._hide_main_menu()
        if self.panel_settings_win and self.panel_settings_win.winfo_exists():
            self.panel_settings_win.lift()
            return

        self.panel_settings_win = tk.Toplevel(self.root)
        self.panel_settings_win.title("系统设置")
        self.panel_settings_win.attributes("-topmost", True)
        self.panel_settings_win.configure(bg=MENU_BG)

        _, frame = _pack_fixed_scroll_panel(self.panel_settings_win)
        tk.Label(frame, text="系统设置", font=PIXEL_FONT, fg=PIXEL_COLOR, bg=MENU_BG).pack(anchor=tk.W)

        size_row = tk.Frame(frame, bg=MENU_BG)
        size_row.pack(fill=tk.X, pady=(8, 4))
        tk.Label(size_row, text="桌宠大小", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG).pack(side=tk.LEFT)
        for preset, px in SIZE_PRESETS.items():
            mark = " ✓" if self.display_size == px else ""

            def set_size(p=preset) -> None:
                self._set_size_preset(p)
                self._open_panel_settings()

            tk.Button(
                size_row, text=f"{preset}{mark}", command=set_size, font=PIXEL_FONT, bg=MENU_ACTIVE, fg=MENU_FG
            ).pack(side=tk.LEFT, padx=2)

        font_row = tk.Frame(frame, bg=MENU_BG)
        font_row.pack(fill=tk.X, pady=(4, 8))
        tk.Label(font_row, text="字体大小", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG).pack(side=tk.LEFT)
        for preset, px in FONT_SIZE_PRESETS.items():
            mark = " ✓" if self.font_size == px else ""

            def set_font(p=preset, size=px) -> None:
                self.font_size = size
                _apply_font_size(size)
                self.app_config["font_size"] = size
                _save_app_config(self.app_config)
                self._show_toast(f"字体已设为「{p}」", PIXEL_COLOR)
                if self.panel_settings_win and self.panel_settings_win.winfo_exists():
                    self.panel_settings_win.destroy()
                    self.panel_settings_win = None
                self._open_panel_settings()

            tk.Button(
                font_row, text=f"{preset}{mark}", command=set_font, font=PIXEL_FONT, bg=MENU_ACTIVE, fg=MENU_FG
            ).pack(side=tk.LEFT, padx=2)

        tk.Label(frame, text="声音设置", font=PIXEL_FONT, fg=PIXEL_COLOR, bg=MENU_BG).pack(anchor=tk.W, pady=(4, 0))
        tk.Button(
            frame,
            text="打开声音设置",
            command=lambda: (self._open_sound_settings(from_panel=True)),
            font=PIXEL_FONT,
            bg=MENU_ACTIVE,
            fg=MENU_FG,
        ).pack(anchor=tk.W, pady=4)

        diff_row = tk.Frame(frame, bg=MENU_BG)
        diff_row.pack(fill=tk.X, pady=(8, 0))
        tk.Label(diff_row, text="游戏难度", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG).pack(side=tk.LEFT)
        for level in ("低", "中", "高"):
            mark = " ✓" if self.difficulty == level else ""

            def set_diff(l=level) -> None:
                self._set_difficulty(l)
                if self.panel_settings_win and self.panel_settings_win.winfo_exists():
                    self.panel_settings_win.destroy()
                    self.panel_settings_win = None
                self._open_panel_settings()

            tk.Button(
                diff_row, text=f"{level}{mark}", command=set_diff, font=PIXEL_FONT, bg=MENU_ACTIVE, fg=MENU_FG
            ).pack(side=tk.LEFT, padx=2)
        self._place_panel_popup(self.panel_settings_win)

    def _open_rhyme_menu(self) -> None:
        self._show_sub_menu(
            [
                ("练习对战", self._open_rhyme_fight),
                ("邀请对战", self._open_rhyme_invite),
            ],
            offset_x=120,
        )

    def _open_rhyme_invite(self) -> None:
        self._hide_main_menu()
        self._show_once_hint("rhyme_invite", duration_ms=4500)
        id_line = f"\n你的编号：{_format_pet_id(self.pet_id)}" if PET_ID_FEATURE and self.pet_id is not None else ""
        self._show_toast(
            f"邀请对战需要联机服务器\n"
            f"（匹配/房间/同步尚未接入）{id_line}\n"
            f"可先体验「练习对战」~",
            "#888888",
            duration_ms=5500,
        )

    def _close_rhyme_fight(self, *, resume: bool = True) -> None:
        if self.rhyme_fight_job:
            try:
                self.root.after_cancel(self.rhyme_fight_job)
            except Exception:
                pass
            self.rhyme_fight_job = None
        if self.rhyme_fight_win and self.rhyme_fight_win.winfo_exists():
            self.rhyme_fight_win.destroy()
        self.rhyme_fight_win = None
        if resume:
            self._resume_idle_after_activity()

    def _open_rhyme_fight(self) -> None:
        self._hide_main_menu()

        def start() -> None:
            self._start_game_countdown(self._begin_rhyme_fight)

        self._ensure_first_play_guide("rhyme", start)

    def _begin_rhyme_fight(self) -> None:
        self._close_rhyme_fight(resume=False)
        state = {
            "player_hp": 100,
            "enemy_hp": 100,
            "blocking": False,
            "log": "对手：来切磋一下吧！",
            "over": False,
            "special_ready_ms": 0,
        }

        self.rhyme_fight_win = tk.Toplevel(self.root)
        self.rhyme_fight_win.title("练习对战")
        self.rhyme_fight_win.attributes("-topmost", True)
        self.rhyme_fight_win.configure(bg=MENU_BG)
        self.rhyme_fight_win.protocol("WM_DELETE_WINDOW", self._close_rhyme_fight)

        frame = tk.Frame(self.rhyme_fight_win, bg=MENU_BG, padx=12, pady=10)
        frame.pack()
        tk.Label(frame, text="练习对战", font=PIXEL_FONT, fg=PIXEL_COLOR, bg=MENU_BG).pack(anchor=tk.W)

        icon_row = tk.Frame(frame, bg=MENU_BG)
        icon_row.pack(fill=tk.X, pady=(6, 4))
        icon_size = 44
        player_canvas = tk.Canvas(icon_row, width=icon_size, height=icon_size, bg=MENU_BG, highlightthickness=0)
        player_canvas.pack(side=tk.LEFT, padx=(0, 8))
        _draw_fight_fighter_icon(player_canvas, icon_size, side="player")
        tk.Label(icon_row, text="VS", font=PIXEL_FONT, fg="#ffcc44", bg=MENU_BG).pack(side=tk.LEFT, padx=4)
        enemy_canvas = tk.Canvas(icon_row, width=icon_size, height=icon_size, bg=MENU_BG, highlightthickness=0)
        enemy_canvas.pack(side=tk.LEFT, padx=(8, 0))
        _draw_fight_fighter_icon(enemy_canvas, icon_size, side="opponent")

        hp_label = tk.Label(frame, text="", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG)
        hp_label.pack(anchor=tk.W, pady=(4, 4))
        log_label = tk.Label(frame, text="", font=PIXEL_FONT, fg="#aaaaaa", bg=MENU_BG, wraplength=260, justify=tk.LEFT)
        log_label.pack(anchor=tk.W, pady=(0, 8))

        btn_row = tk.Frame(frame, bg=MENU_BG)
        btn_row.pack(fill=tk.X)
        special_btn = tk.Button(
            btn_row,
            text="必杀",
            font=PIXEL_FONT,
            bg="#884444",
            fg=MENU_FG,
            activebackground="#aa5555",
        )

        def special_left_ms() -> int:
            return max(0, int(state["special_ready_ms"]) - int(time.time() * 1000))

        def refresh_special_btn() -> None:
            if state["over"] or not special_btn.winfo_exists():
                return
            left = special_left_ms()
            if left > 0:
                sec = (left + 999) // 1000
                special_btn.config(text=f"必杀 {sec}s", state=tk.DISABLED, bg="#553333", fg="#888888")
            else:
                special_btn.config(text="必杀", state=tk.NORMAL, bg="#884444", fg=MENU_FG)

        def refresh() -> None:
            hp_label.config(text=f"你 {state['player_hp']} HP    对手 {state['enemy_hp']} HP  [{self.difficulty}]")
            log_label.config(text=state["log"])
            refresh_special_btn()

        def end_fight(won: bool) -> None:
            if state["over"]:
                return
            state["over"] = True
            if won:
                self.mood = min(100, self.mood + 5)
                state["log"] = "你赢了！对手：下次我不会输的…"
                self._add_diary_entry("练习对战：胜利", auto=True)
                self._save_game_record("rhyme", {"won": True, "difficulty": self.difficulty})
                self._refresh_panel()
                refresh()
                self._show_game_clear(
                    title="胜利！",
                    subtitle="练习对战通关",
                    accent="#ff8844",
                    on_done=self._close_rhyme_fight,
                )
            else:
                self.mood = max(0, self.mood - 2)
                state["log"] = "输了…对手：承让啦~"
                self._add_diary_entry("练习对战：失败", auto=True)
                self._refresh_panel()
                refresh()
                self.root.after(1600, self._close_rhyme_fight)

        def start_special_cooldown() -> None:
            state["special_ready_ms"] = int(time.time() * 1000) + RHYME_SPECIAL_COOLDOWN_MS
            refresh_special_btn()

            def tick_cd() -> None:
                if state["over"] or not self.rhyme_fight_win or not self.rhyme_fight_win.winfo_exists():
                    return
                refresh_special_btn()
                if special_left_ms() > 0:
                    self.root.after(200, tick_cd)

            self.root.after(200, tick_cd)

        def player_attack(*, special: bool = False) -> None:
            if state["over"]:
                return
            mult = self._fight_player_mult
            if special:
                if special_left_ms() > 0:
                    state["log"] = f"必杀冷却中（{ (special_left_ms() + 999) // 1000 }s）"
                    refresh()
                    return
                start_special_cooldown()
                if random.random() < 0.28:
                    state["log"] = "必杀落空！"
                    refresh()
                    return
                dmg = int(22 * mult)
                state["log"] = f"侧踢必杀！造成 {dmg} 伤害"
            else:
                dmg = int(12 * mult)
                state["log"] = f"攻击！造成 {dmg} 伤害"
            state["enemy_hp"] = max(0, state["enemy_hp"] - dmg)
            refresh()
            if state["enemy_hp"] <= 0:
                end_fight(True)

        def player_block() -> None:
            if state["over"]:
                return
            state["blocking"] = True
            state["log"] = "防御姿态…"
            refresh()
            self.root.after(700, lambda: state.update({"blocking": False}))

        def enemy_turn() -> None:
            if state["over"] or not self.rhyme_fight_win or not self.rhyme_fight_win.winfo_exists():
                return
            action = random.choice(["attack", "attack", "heavy", "feint"])
            em = self._fight_enemy_mult
            if action == "heavy":
                dmg = int(18 * em)
                msg = f"对手重击！{dmg} 伤害"
            elif action == "feint":
                dmg = int(8 * em)
                msg = f"对手佯攻 {dmg} 伤害"
            else:
                dmg = int(12 * em)
                msg = f"对手攻击 {dmg} 伤害"
            if state["blocking"]:
                dmg = max(1, dmg // 3)
                msg += "（被格挡）"
            state["player_hp"] = max(0, state["player_hp"] - dmg)
            state["log"] = msg
            refresh()
            if state["player_hp"] <= 0:
                end_fight(False)
                return
            delay = random.randint(1400, 2200)
            self.rhyme_fight_job = self.root.after(delay, enemy_turn)

        tk.Button(btn_row, text="攻击", command=player_attack, font=PIXEL_FONT, bg=MENU_ACTIVE, fg=MENU_FG).pack(
            side=tk.LEFT, padx=2
        )
        tk.Button(
            btn_row, text="防御", command=player_block, font=PIXEL_FONT, bg=MENU_BG, fg=MENU_FG
        ).pack(side=tk.LEFT, padx=2)
        special_btn.config(command=lambda: player_attack(special=True))
        special_btn.pack(side=tk.LEFT, padx=2)
        refresh()
        self._place_panel_popup(self.rhyme_fight_win)
        self.rhyme_fight_job = self.root.after(1500, enemy_turn)

    def _start_rhythm_game(self, track_id: str | None = None, play_cap_ms: int | None = None) -> None:
        if self.rhythm_active:
            return
        self._hide_main_menu()
        chosen = str(track_id or (self._music_playlist()[0] if self._music_playlist() else DEFAULT_MUSIC_TRACK))
        chosen = MUSIC_TRACK_LEGACY_IDS.get(chosen, chosen)
        if chosen not in MUSIC_TRACKS:
            chosen = DEFAULT_MUSIC_TRACK
        self.rhythm_track_id = chosen
        if play_cap_ms is None:
            self.rhythm_play_cap_ms = int(RHYTHM_PLAY_CAP_MS)
        else:
            self.rhythm_play_cap_ms = max(0, int(play_cap_ms))

        def begin() -> None:
            self._start_game_countdown(self._begin_rhythm_game)

        def after_guide() -> None:
            self._request_mode_switch(begin)

        self._ensure_first_play_guide("rhythm_game", after_guide)

    def _close_rhythm_game(self, *, resume: bool = True, finished: bool = False) -> None:
        was_active = self.rhythm_active
        score = self.rhythm_score
        max_combo = self.rhythm_max_combo
        perfect = self.rhythm_perfect
        great = self.rhythm_great
        good = self.rhythm_good
        miss = self.rhythm_miss
        if self.rhythm_job:
            try:
                self.root.after_cancel(self.rhythm_job)
            except Exception:
                pass
            self.rhythm_job = None
        if getattr(self, "rhythm_settings_win", None) and self.rhythm_settings_win.winfo_exists():
            try:
                self.rhythm_settings_win.destroy()
            except Exception:
                pass
        self.rhythm_settings_win = None
        if self.rhythm_win and self.rhythm_win.winfo_exists():
            try:
                self.rhythm_win.unbind("<KeyPress>")
                self.rhythm_win.unbind("<KeyRelease>")
            except Exception:
                pass
            self.rhythm_win.destroy()
        self.rhythm_win = None
        self.rhythm_canvas = None
        self.rhythm_grade_bar = None
        self.rhythm_active = False
        self.rhythm_notes = []
        self.rhythm_flash = {}
        self.rhythm_keys_down = set()
        self.rhythm_judgment = ""
        self.rhythm_bg_ready = False
        self.rhythm_scan_i = 0
        try:
            import pygame

            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass
        self.bg_music_playing = False
        if self.rhythm_resume_music:
            self.rhythm_resume_music = False
            self.music_sprite_mode = True
            self._start_bg_music()
            self._start_music_wave_fx()
            self._sync_mini_pet_music_waves()
        if was_active and finished:
            grade = _rhythm_grade(perfect, great, good, miss)
            acc = _rhythm_accuracy_pct(perfect, great, good, miss)
            track_title = str(_music_track(getattr(self, "rhythm_track_id", DEFAULT_MUSIC_TRACK))["title"])
            self._save_game_record(
                "music",
                {
                    "score": score,
                    "max_combo": max_combo,
                    "perfect": perfect,
                    "great": great,
                    "good": good,
                    "miss": miss,
                    "grade": grade,
                    "accuracy": round(acc, 1),
                    "track": getattr(self, "rhythm_track_id", DEFAULT_MUSIC_TRACK),
                    "difficulty": self.difficulty,
                },
            )
            mood_bonus = min(6, max_combo // 8)
            if mood_bonus > 0:
                self.mood = min(100, self.mood + mood_bonus)
                self._refresh_panel()
            grade_colors = {g: c for g, _t, c in RHYTHM_GRADE_TIERS}
            grade_color = grade_colors.get(grade, "#88ccff")
            subtitle = (
                f"{track_title} · 准确率 {acc:.0f}%\n"
                f"得分 {score}  最大连击 {max_combo}\n"
                f"P {perfect}  G {great}  Good {good}  Miss {miss}"
            )
            self._show_game_clear(
                title=f"评级 {grade}",
                subtitle=subtitle,
                accent=grade_color,
                hero_grade=grade,
                hero_color=grade_color,
                on_done=self._resume_idle_after_activity if resume else None,
            )
            return
        if resume and was_active:
            self._resume_idle_after_activity()

    def _begin_rhythm_game(self) -> None:
        track = _music_track(getattr(self, "rhythm_track_id", DEFAULT_MUSIC_TRACK))
        wav = _ensure_music_track_wav(str(track["id"]))
        if wav is None or not wav.exists():
            self._show_toast(f"找不到音乐：{track['title']}", "#ff8844")
            self._resume_idle_after_activity()
            return
        self._close_rhythm_game(resume=False)
        if self.mode == "game":
            self._stop_game_mode()
            self.mode = "free"
        self.rhythm_resume_music = bool(self.music_sprite_mode or self.bg_music_playing)
        if self.music_sprite_mode:
            self.music_sprite_mode = False
            self._stop_music_wave_fx()
            self._sync_mini_pet_music_waves()
        self._stop_bg_music()

        duration_ms = _get_wav_duration_ms(wav) or 60000
        cap = int(getattr(self, "rhythm_play_cap_ms", RHYTHM_PLAY_CAP_MS) or 0)
        if cap > 0:
            duration_ms = min(cap, duration_ms)
        duration_ms = max(20000, duration_ms)
        self._show_toast("正在根据音乐生成谱面…", "#88ccff", duration_ms=2200)
        difficulty = str(self.app_config.get("rhythm_chart_diff") or self.difficulty)
        if difficulty not in ("低", "中", "高"):
            difficulty = "中"
        track_id = str(track["id"])
        token = getattr(self, "rhythm_chart_token", 0) + 1
        self.rhythm_chart_token = token

        def worker() -> None:
            try:
                notes, bpm, src = _build_rhythm_chart_from_wav(
                    wav, duration_ms, difficulty, track_id=track_id
                )
            except Exception:
                notes = _build_rhythm_chart_random(duration_ms, difficulty)
                bpm, src = float(RHYTHM_BPM), "random"
            self.root.after(
                0,
                lambda n=notes, b=bpm, s=src: self._start_rhythm_ui_after_chart(
                    token, track, wav, duration_ms, cap, n, b, s
                ),
            )

        threading.Thread(target=worker, daemon=True).start()

    def _start_rhythm_ui_after_chart(
        self,
        token: int,
        track: dict,
        wav: Path,
        duration_ms: int,
        cap: int,
        notes: list,
        bpm: float,
        src: str,
    ) -> None:
        if token != getattr(self, "rhythm_chart_token", 0) or self._closing:
            return
        self.rhythm_notes = notes
        self.rhythm_chart_bpm = bpm
        self.rhythm_chart_source = src
        sec = duration_ms // 1000
        mode_tag = "90秒" if cap > 0 else "全曲"
        if src == "beat":
            self._show_toast(f"节拍谱 · {bpm:.0f}BPM · {mode_tag}{sec}s", "#88ffaa", duration_ms=1600)
        elif src == "cache":
            self._show_toast(f"节拍谱（缓存）· {bpm:.0f}BPM · {mode_tag}{sec}s", "#88ffaa", duration_ms=1400)
        else:
            self._show_toast(f"随机谱 · {mode_tag}{sec}s", "#ff8844", duration_ms=1600)
        self.rhythm_score = 0
        self.rhythm_combo = 0
        self.rhythm_max_combo = 0
        self.rhythm_perfect = 0
        self.rhythm_great = 0
        self.rhythm_good = 0
        self.rhythm_miss = 0
        self.rhythm_judgment = ""
        self.rhythm_flash = {}
        self.rhythm_keys_down = set()
        self.rhythm_travel_ms = _rhythm_travel_ms_for(self.app_config.get("rhythm_speed", "中"))
        self.rhythm_end_ms = duration_ms
        self.rhythm_active = True
        self.rhythm_wav_path = wav
        self.rhythm_track_id = str(track["id"])
        self.rhythm_bg_ready = False
        self.rhythm_grade_dirty_ms = 0
        self.rhythm_scan_i = 0

        self.rhythm_win = tk.Toplevel(self.root)
        self.rhythm_win.title(f"音乐 · {track['title']}")
        self.rhythm_win.attributes("-topmost", True)
        self.rhythm_win.configure(bg="#101018")
        self.rhythm_win.protocol("WM_DELETE_WINDOW", lambda: self._close_rhythm_game(resume=True))
        self.rhythm_win.geometry(f"{RHYTHM_W}x{RHYTHM_H}")

        top = tk.Frame(self.rhythm_win, bg="#101018")
        top.pack(fill=tk.X, padx=8, pady=(6, 0))
        hdr = tk.Frame(top, bg="#101018")
        hdr.pack(fill=tk.X)
        tk.Button(
            hdr,
            text="设置",
            command=self._open_rhythm_settings,
            font=PIXEL_FONT,
            bg="#2a2a44",
            fg="#dddddd",
            activebackground="#3a3a55",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=8,
            pady=2,
        ).pack(side=tk.RIGHT)
        self.rhythm_grade_bar = tk.Canvas(
            top, width=RHYTHM_W - 16, height=RHYTHM_GRADE_BAR_H, bg="#101018", highlightthickness=0
        )
        self.rhythm_grade_bar.pack(fill=tk.X)

        self.rhythm_canvas = tk.Canvas(
            self.rhythm_win, width=RHYTHM_W, height=RHYTHM_H - RHYTHM_GRADE_BAR_H - 16, bg="#101018", highlightthickness=0
        )
        self.rhythm_canvas.pack()
        self.rhythm_win.bind("<KeyPress>", self._rhythm_on_key)
        self.rhythm_win.bind("<KeyRelease>", self._rhythm_on_key_release)
        try:
            self.rhythm_win.focus_force()
        except Exception:
            pass
        self._place_panel_popup(self.rhythm_win)
        self._refresh_rhythm_grade_bar(force=True)

        try:
            import pygame

            _init_pygame_mixer()
            pygame.mixer.music.load(str(wav))
            self._apply_music_volume()
            pygame.mixer.music.play(0)
            self.bg_music_playing = True
        except Exception:
            self._show_toast("音乐播放失败", "#ff6666")
            self._close_rhythm_game(resume=True)
            return

        self.rhythm_start_ms = int(time.time() * 1000)
        self._mark_hint_seen("rhythm_game")
        self._rhythm_tick()

    def _get_rhythm_travel_ms(self) -> int:
        return int(getattr(self, "rhythm_travel_ms", None) or _rhythm_travel_ms_for(self.app_config.get("rhythm_speed", "中")))

    def _open_rhythm_settings(self) -> None:
        if not self.rhythm_active or not self.rhythm_win or not self.rhythm_win.winfo_exists():
            return
        old = getattr(self, "rhythm_settings_win", None)
        if old is not None:
            try:
                if old.winfo_exists():
                    old.lift()
                    old.focus_force()
                    return
            except Exception:
                pass
        win = tk.Toplevel(self.rhythm_win)
        self.rhythm_settings_win = win
        win.title("音乐设置")
        win.attributes("-topmost", True)
        win.configure(bg="#181828")
        win.resizable(False, False)
        frame = tk.Frame(win, bg="#181828", padx=14, pady=12)
        frame.pack()
        tk.Label(frame, text="音乐设置", font=PIXEL_FONT, fg="#88ccff", bg="#181828").pack(anchor=tk.W)
        tk.Label(
            frame,
            text="流速即时生效 · 谱面难度下局生效",
            font=PIXEL_FONT,
            fg="#888899",
            bg="#181828",
        ).pack(anchor=tk.W, pady=(4, 10))

        speed_var = tk.StringVar(value=str(self.app_config.get("rhythm_speed", "中")))
        diff_var = tk.StringVar(value=str(self.app_config.get("rhythm_chart_diff", "中")))

        def row(label: str, var: tk.StringVar, options: tuple[str, ...], on_pick) -> None:
            box = tk.Frame(frame, bg="#181828")
            box.pack(fill=tk.X, pady=4)
            tk.Label(box, text=label, font=PIXEL_FONT, fg="#dddddd", bg="#181828", width=8, anchor=tk.W).pack(
                side=tk.LEFT
            )
            for opt in options:
                tk.Radiobutton(
                    box,
                    text=opt,
                    variable=var,
                    value=opt,
                    command=lambda o=opt: on_pick(o),
                    font=PIXEL_FONT,
                    fg="#dddddd",
                    bg="#181828",
                    activebackground="#181828",
                    activeforeground="#ffffff",
                    selectcolor="#2a2a44",
                    highlightthickness=0,
                ).pack(side=tk.LEFT, padx=4)

        def set_speed(v: str) -> None:
            self.app_config["rhythm_speed"] = v
            self.rhythm_travel_ms = _rhythm_travel_ms_for(v)
            _save_app_config(self.app_config)
            self._show_toast(f"流速：{v}", "#88ccff", duration_ms=900)

        def set_diff(v: str) -> None:
            self.app_config["rhythm_chart_diff"] = v
            _save_app_config(self.app_config)
            self._show_toast(f"谱面难度：{v}（下局生效）", "#88ffaa", duration_ms=1200)

        row("流速", speed_var, ("慢", "中", "快"), set_speed)
        row("谱面", diff_var, ("低", "中", "高"), set_diff)
        tk.Label(
            frame,
            text="长音：到线时长按，尾部松键",
            font=PIXEL_FONT,
            fg="#888899",
            bg="#181828",
        ).pack(anchor=tk.W, pady=(10, 6))
        tk.Button(
            frame,
            text="关闭",
            command=win.destroy,
            font=PIXEL_FONT,
            bg="#2a2a44",
            fg="#dddddd",
            relief=tk.FLAT,
            padx=10,
            pady=4,
        ).pack(anchor=tk.E)
        win.protocol("WM_DELETE_WINDOW", win.destroy)
        try:
            win.geometry(f"+{self.rhythm_win.winfo_rootx() + 40}+{self.rhythm_win.winfo_rooty() + 60}")
        except Exception:
            pass

    def _refresh_rhythm_grade_bar(self, *, force: bool = False) -> None:
        bar = getattr(self, "rhythm_grade_bar", None)
        if not bar:
            return
        try:
            if not bar.winfo_exists():
                return
        except Exception:
            return
        now = int(time.time() * 1000)
        if not force and now - getattr(self, "rhythm_grade_dirty_ms", 0) < RHYTHM_GRADE_BAR_REFRESH_MS:
            return
        self.rhythm_grade_dirty_ms = now
        _draw_rhythm_grade_bar(
            bar,
            RHYTHM_W - 16,
            RHYTHM_GRADE_BAR_H,
            self.rhythm_perfect,
            self.rhythm_great,
            self.rhythm_good,
            self.rhythm_miss,
        )

    def _rhythm_now_ms(self) -> int:
        return int(time.time() * 1000) - self.rhythm_start_ms

    def _rhythm_apply_judgment(self, judge: str, pts: int) -> None:
        if judge == "Miss":
            self.rhythm_combo = 0
            self.rhythm_miss += 1
            self.rhythm_judgment = "Miss"
            self._refresh_rhythm_grade_bar()
            return
        self.rhythm_judgment = judge
        self.rhythm_combo += 1
        self.rhythm_max_combo = max(self.rhythm_max_combo, self.rhythm_combo)
        bonus = min(50, self.rhythm_combo // 4 * 5)
        self.rhythm_score += pts + bonus
        if judge == "Perfect":
            self.rhythm_perfect += 1
        elif judge == "Great":
            self.rhythm_great += 1
        else:
            self.rhythm_good += 1
        self._refresh_rhythm_grade_bar()

    def _rhythm_note_is_hold(self, note: dict) -> bool:
        t = int(note.get("t", 0))
        end = int(note.get("end", t) or t)
        return bool(note.get("hold")) and end - t >= 220

    def _rhythm_complete_hold_tail(self, note: dict, judge: str, pts: int) -> None:
        note["holding"] = False
        note["tail_done"] = True
        note["hit"] = True
        lane = int(note["lane"])
        self.rhythm_flash[lane] = self._rhythm_now_ms() + 120
        self._rhythm_apply_judgment(judge, pts)

    def _rhythm_on_key(self, event: tk.Event) -> None:
        if not self.rhythm_active:
            return
        key = (event.keysym or "").lower()
        if key not in RHYTHM_KEYS:
            return
        lane = RHYTHM_KEYS.index(key)
        if lane in self.rhythm_keys_down:
            return
        self.rhythm_keys_down.add(lane)
        now = self._rhythm_now_ms()
        best = None
        best_abs = RHYTHM_HIT_GOOD_MS + 1
        start = max(0, getattr(self, "rhythm_scan_i", 0) - 8)
        for note in self.rhythm_notes[start:]:
            if note["lane"] != lane or note["hit"] or note["missed"]:
                continue
            if note.get("head_hit") or note.get("holding"):
                continue
            t = int(note["t"])
            if t > now + RHYTHM_HIT_GOOD_MS + 40:
                break
            if t < now - RHYTHM_HIT_GOOD_MS - 40:
                continue
            delta = now - t
            ad = abs(delta)
            if ad < best_abs:
                best_abs = ad
                best = (note, delta)
        if best is None:
            return
        note, delta = best
        judge, pts = _rhythm_hit_judgment(delta)
        if judge == "Miss":
            return
        self.rhythm_flash[lane] = now + 120
        if self._rhythm_note_is_hold(note):
            note["head_hit"] = True
            note["holding"] = True
            # 头部给一半分，尾部再给一半
            self._rhythm_apply_judgment(judge, max(50, pts // 2))
        else:
            note["hit"] = True
            self._rhythm_apply_judgment(judge, pts)

    def _rhythm_on_key_release(self, event: tk.Event) -> None:
        if not self.rhythm_active:
            return
        key = (event.keysym or "").lower()
        if key not in RHYTHM_KEYS:
            return
        lane = RHYTHM_KEYS.index(key)
        self.rhythm_keys_down.discard(lane)
        now = self._rhythm_now_ms()
        start = max(0, getattr(self, "rhythm_scan_i", 0) - 8)
        for note in self.rhythm_notes[start:]:
            if int(note["lane"]) != lane:
                continue
            if note["hit"] or note["missed"]:
                continue
            if not (note.get("holding") and note.get("head_hit")):
                continue
            end = int(note.get("end", note["t"]))
            if now < end - RHYTHM_HOLD_RELEASE_MS:
                note["holding"] = False
                note["missed"] = True
                self._rhythm_apply_judgment("Miss", 0)
                return
            judge, pts = _rhythm_hold_tail_judgment(now - end)
            if judge == "Miss":
                note["holding"] = False
                note["missed"] = True
                self._rhythm_apply_judgment("Miss", 0)
            else:
                self._rhythm_complete_hold_tail(note, judge, max(50, pts // 2))
            return

    def _rhythm_tick(self) -> None:
        if not self.rhythm_active or not self.rhythm_canvas or not self.rhythm_win:
            return
        if not self.rhythm_win.winfo_exists():
            self._close_rhythm_game(resume=True)
            return
        now = self._rhythm_now_ms()
        i = getattr(self, "rhythm_scan_i", 0)
        notes = self.rhythm_notes
        nlen = len(notes)
        for j in range(i, nlen):
            note = notes[j]
            if note["hit"] or note["missed"]:
                continue
            t = int(note["t"])
            end = int(note.get("end", t) or t)
            hold = self._rhythm_note_is_hold(note)

            if hold and note.get("head_hit") and not note.get("tail_done"):
                if now > end + RHYTHM_HOLD_RELEASE_MS:
                    if note.get("holding") and int(note["lane"]) in self.rhythm_keys_down:
                        self._rhythm_complete_hold_tail(note, "Perfect", 150)
                    else:
                        note["holding"] = False
                        note["missed"] = True
                        self._rhythm_apply_judgment("Miss", 0)
                continue

            if not note.get("head_hit") and now - t > RHYTHM_HIT_GOOD_MS:
                note["missed"] = True
                note["holding"] = False
                self._rhythm_apply_judgment("Miss", 0)
                continue

            if t > now + RHYTHM_HIT_GOOD_MS + 240 and not note.get("head_hit"):
                break

        while i < nlen and (notes[i]["hit"] or notes[i]["missed"]):
            i += 1
        self.rhythm_scan_i = i

        music_done = False
        # 不以 mixer.get_busy() 提前结束：长 wav 常会误报空闲，导致全曲/90s 中途截停
        if now < self.rhythm_end_ms - 1200 and now > 2500:
            try:
                import pygame

                if pygame.mixer.get_init() and not pygame.mixer.music.get_busy():
                    start_sec = max(0.0, now / 1000.0)
                    pygame.mixer.music.play(0, start=start_sec)
                    self._apply_music_volume()
            except Exception:
                pass
        if now >= self.rhythm_end_ms:
            try:
                import pygame

                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
            except Exception:
                pass
            music_done = True

        if music_done or now >= self.rhythm_end_ms + 800:
            self._close_rhythm_game(resume=True, finished=True)
            return

        self._draw_rhythm_frame(now)
        self.rhythm_job = self.root.after(RHYTHM_TICK_MS, self._rhythm_tick)

    def _draw_rhythm_frame(self, now: int) -> None:
        c = self.rhythm_canvas
        if not c:
            return
        w = RHYTHM_W
        h = max(320, RHYTHM_H - RHYTHM_GRADE_BAR_H - 16)
        pad_x = 28
        top = 48
        hit_y = int(h * 0.80)
        lane_w = (w - pad_x * 2) // RHYTHM_LANES
        track = _music_track(getattr(self, "rhythm_track_id", DEFAULT_MUSIC_TRACK))
        grade = _rhythm_grade(self.rhythm_perfect, self.rhythm_great, self.rhythm_good, self.rhythm_miss)
        acc = _rhythm_accuracy_pct(self.rhythm_perfect, self.rhythm_great, self.rhythm_good, self.rhythm_miss)
        travel = max(400, self._get_rhythm_travel_ms())

        if not getattr(self, "rhythm_bg_ready", False):
            c.delete("all")
            c.create_rectangle(0, 0, w, h, fill="#101018", outline="", tags=("bg",))
            for i in range(RHYTHM_LANES):
                x0 = pad_x + i * lane_w
                x1 = x0 + lane_w - 6
                col = RHYTHM_LANE_COLORS[i]
                c.create_rectangle(x0, top, x1, h - 36, fill="#181828", outline="#333355", tags=("bg",))
                c.create_rectangle(x0, hit_y - 10, x1, hit_y + 10, fill="#2a2a44", outline=col, width=2, tags=("hitline", f"hit{i}"))
                c.create_text((x0 + x1) // 2, h - 18, text=RHYTHM_KEY_LABELS[i], fill=col, font=PIXEL_FONT, tags=("bg",))
            self.rhythm_bg_ready = True

        c.delete("dyn")
        tid = str(getattr(self, "rhythm_track_id", DEFAULT_MUSIC_TRACK))
        plate = _music_track_icon_photo(tid, 28)
        self._rhythm_plate_photo = plate
        c.create_image(28, 16, image=plate, tags=("dyn",))
        c.create_text(48, 14, text=f"音乐 · {track['title']}", fill="#88ccff", font=PIXEL_FONT, anchor="w", tags=("dyn",))
        left_s = max(0, (self.rhythm_end_ms - now) // 1000)
        mode_tag = "90s" if int(getattr(self, "rhythm_play_cap_ms", 0) or 0) > 0 else "全曲"
        bpm = getattr(self, "rhythm_chart_bpm", None)
        bpm_tag = f"  {bpm:.0f}BPM" if bpm else ""
        speed_tag = str(self.app_config.get("rhythm_speed", "中"))
        c.create_text(
            w // 2,
            32,
            text=f"得分 {self.rhythm_score}  连击 {self.rhythm_combo}  评级 {grade}  {acc:.0f}%  {mode_tag}{bpm_tag} {speed_tag} {left_s}s",
            fill="#dddddd",
            font=PIXEL_FONT,
            tags=("dyn",),
        )
        for i in range(RHYTHM_LANES):
            flash_until = self.rhythm_flash.get(i, 0)
            fill = RHYTHM_LANE_COLORS[i] if now <= flash_until or i in self.rhythm_keys_down else "#2a2a44"
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
                c.create_rectangle(x0, y - 10, x1, y + 10, fill=col, outline="#ffffff", tags=("dyn",))
        if self.rhythm_judgment:
            jcol = {
                "Perfect": "#ffee88",
                "Great": "#88ffaa",
                "Good": "#88ccff",
                "Miss": "#ff6688",
            }.get(self.rhythm_judgment, "#ffffff")
            c.create_text(w // 2, hit_y - 36, text=self.rhythm_judgment, fill=jcol, font=PIXEL_FONT, tags=("dyn",))

    def _close_typing_game(self, *, resume: bool = True) -> None:
        if self.typing_game_job:
            try:
                self.root.after_cancel(self.typing_game_job)
            except Exception:
                pass
            self.typing_game_job = None
        if self.typing_game_win and self.typing_game_win.winfo_exists():
            try:
                self.typing_game_win.grab_release()
            except Exception:
                pass
            self.typing_game_win.destroy()
        self.typing_game_win = None
        self._typing_mood_cache.clear()
        if resume:
            self._resume_idle_after_activity()

    def _typing_mood_photo(self, grade: str) -> ImageTk.PhotoImage:
        if grade in self._typing_mood_cache:
            return self._typing_mood_cache[grade]
        filename = TYPING_MOOD_FILES.get(grade, "stand.jpg")
        ref = _reference_scale(TYPING_MOOD_SIZE)
        photo = ImageTk.PhotoImage(_get_processed_canvas(filename, TYPING_MOOD_SIZE, ref))
        self._typing_mood_cache[grade] = photo
        return photo

    def _start_typing_game(self, lang: str, *, jp_mode: str | None = None) -> None:
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

    def _begin_typing_game(self, lang: str, *, jp_mode: str | None = None) -> None:
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

    def _close_vocab_game(self, *, resume: bool = True) -> None:
        self._vocab_cancel_advance()
        self._vocab_round_lock = False
        self._vocab_current = None
        self._vocab_option_btns = {}
        self.vocab_word_label = None
        self.vocab_status_label = None
        self.vocab_options_frame = None
        if self.vocab_game_win and self.vocab_game_win.winfo_exists():
            self.vocab_game_win.destroy()
        self.vocab_game_win = None
        if resume:
            self._resume_idle_after_activity()

    def _vocab_cancel_advance(self) -> None:
        if self._vocab_advance_job:
            try:
                self.root.after_cancel(self._vocab_advance_job)
            except Exception:
                pass
            self._vocab_advance_job = None

    def _vocab_schedule_advance(self, delay_ms: int) -> None:
        self._vocab_cancel_advance()

        def go() -> None:
            self._vocab_advance_job = None
            self._vocab_next_word()

        self._vocab_advance_job = self.root.after(delay_ms, go)

    def _vocab_mark_options(self, chosen: str, correct: str) -> None:
        for text, btn in self._vocab_option_btns.items():
            if not btn.winfo_exists():
                continue
            btn.config(state=tk.DISABLED)
            if text == correct:
                btn.config(bg=VOCAB_OPTION_OK, fg="#ffffff", activebackground=VOCAB_OPTION_OK)
            elif text == chosen:
                btn.config(bg=VOCAB_OPTION_ERR, fg="#ffffff", activebackground=VOCAB_OPTION_ERR)
            else:
                btn.config(bg=VOCAB_OPTION_DIM, fg="#888888", activebackground=VOCAB_OPTION_DIM)

    def _open_vocab_game(self, lang: str = "英语", *, pool: list[dict[str, str]] | None = None, from_notebook: bool = False) -> None:
        self._hide_main_menu()
        if lang == JAPANESE_LANG_LABEL and not _japanese_bank_available() and pool is None:
            self._show_toast("此功能暂不开放", "#ff8844")
            return
        words = list(pool) if pool is not None else _load_vocab_bank(lang)
        if len(words) < 4:
            # 生词本不足 4 条时，用词库补干扰项，仍可复习
            if from_notebook and len(words) >= 1:
                bank = _load_vocab_bank(lang)
                merged = list(words)
                for extra in bank:
                    if extra.get("word") not in {w.get("word") for w in merged}:
                        merged.append(extra)
                    if len(merged) >= 4:
                        break
                words = merged
            if len(words) < 4:
                self._show_toast(f"{lang} 词库不足 4 条", "#ff8844")
                return
        self._vocab_lang = lang
        self._vocab_pool = words
        self._vocab_from_notebook = bool(from_notebook)
        self._vocab_streak = 0
        self._close_vocab_game(resume=False)

        def start() -> None:
            self._start_game_countdown(self._vocab_next_word)

        def after_guide() -> None:
            self._request_mode_switch(start)

        self._ensure_first_play_guide("vocab", after_guide)

    def _ensure_vocab_window(self, lang: str) -> None:
        if (
            self.vocab_game_win
            and self.vocab_game_win.winfo_exists()
            and self.vocab_word_label
            and self.vocab_options_frame
        ):
            self.vocab_game_win.title(f"背单词 · {lang}")
            self._place_panel_popup(self.vocab_game_win)
            self.vocab_game_win.lift()
            return

        self._close_vocab_game(resume=False)
        win = tk.Toplevel(self.root)
        self.vocab_game_win = win
        win.title(f"背单词 · {lang}")
        win.attributes("-topmost", True)
        win.configure(bg=MENU_BG)
        win.protocol("WM_DELETE_WINDOW", self._close_vocab_game)

        frame = tk.Frame(win, bg=MENU_BG, padx=12, pady=10)
        frame.pack()
        tk.Label(frame, text=f"背单词 · {lang}", font=PIXEL_FONT, fg=PIXEL_COLOR, bg=MENU_BG).pack(anchor=tk.W)
        self.vocab_word_label = tk.Label(frame, text="", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG)
        self.vocab_word_label.pack(anchor=tk.W, pady=(8, 6))
        self.vocab_status_label = tk.Label(frame, text="", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG)
        self.vocab_status_label.pack(pady=4)
        self.vocab_options_frame = tk.Frame(frame, bg=MENU_BG)
        self.vocab_options_frame.pack(fill=tk.X)
        self._place_panel_popup(win)

    def _vocab_next_word(self) -> None:
        words = getattr(self, "_vocab_pool", self.vocab_words)
        if len(words) < 4:
            return
        lang = getattr(self, "_vocab_lang", "英语")
        self._vocab_cancel_advance()
        self._ensure_vocab_window(lang)
        self._vocab_round_lock = False
        self._vocab_option_btns = {}

        # 生词本复习：优先抽生词本里的词
        notebook_words = []
        if getattr(self, "_vocab_from_notebook", False):
            notebook_words = [w for w in _load_vocab_notebook().get(lang, []) if w.get("word")]
        if notebook_words:
            item = random.choice(notebook_words)
            # 用词库同词覆盖词义（若有更新）
            for bank_item in words:
                if bank_item.get("word") == item.get("word"):
                    item = {**item, **bank_item}
                    break
        else:
            item = random.choice(words)
        correct = item.get("meaning", "？")
        pool = [correct]
        for other in random.sample(words, min(len(words), 12)):
            m = other.get("meaning", "")
            if m and m not in pool:
                pool.append(m)
            if len(pool) >= 4:
                break
        while len(pool) < 4:
            pool.append(f"（干扰项{len(pool)}）")
        options = random.sample(pool[:4], min(4, len(pool)))

        self._vocab_current = {"item": item, "correct": correct, "lang": lang, "options": options}
        if self.vocab_word_label:
            tag = "生词本 · " if getattr(self, "_vocab_from_notebook", False) else ""
            self.vocab_word_label.config(text=f"{tag}「{item['word']}」的意思是？")
        if self.vocab_status_label:
            self.vocab_status_label.config(text="", fg=MENU_FG)

        opts_frame = self.vocab_options_frame
        if not opts_frame:
            return
        for child in opts_frame.winfo_children():
            child.destroy()
        for opt in options:
            btn = tk.Button(
                opts_frame,
                text=opt,
                command=lambda o=opt: self._vocab_choose(o),
                font=PIXEL_FONT,
                bg=MENU_ACTIVE,
                fg=MENU_FG,
                activebackground=MENU_ACTIVE,
                wraplength=280,
                justify=tk.LEFT,
            )
            btn.pack(fill=tk.X, pady=2)
            self._vocab_option_btns[opt] = btn

    def _vocab_choose(self, opt: str) -> None:
        if self._vocab_round_lock or not self._vocab_current:
            return
        self._vocab_round_lock = True
        item = self._vocab_current["item"]
        correct = self._vocab_current["correct"]
        lang = self._vocab_current["lang"]
        self._vocab_mark_options(opt, correct)
        if self.vocab_status_label:
            self.vocab_status_label.config(text="", fg=MENU_FG)

        if opt == correct:
            self.mood = min(100, self.mood + 3)
            self._refresh_panel()
            self._add_diary_entry(f"背单词正确：{item['word']}", auto=True)
            # 生词本复习答对：移出生词本
            if getattr(self, "_vocab_from_notebook", False):
                _remove_vocab_notebook_item(lang, str(item.get("word", "")))
            self._vocab_streak += 1
            current_streak = self._vocab_streak
            self._save_game_record(
                "vocab",
                {
                    "lang": lang,
                    "word": item["word"],
                    "correct": True,
                    "streak_clear": current_streak if current_streak >= VOCAB_CLEAR_STREAK else 0,
                    "difficulty": self.difficulty,
                },
            )
            if current_streak >= VOCAB_CLEAR_STREAK:
                streak = current_streak
                self._vocab_streak = 0
                self._vocab_cancel_advance()

                def after_streak_clear() -> None:
                    self._vocab_round_lock = False
                    self._vocab_next_word()

                self._show_game_clear(
                    title="连击通关！",
                    subtitle=f"{lang} · 连续答对 {streak} 题\n最新：{item['word']} = {correct}",
                    accent="#88ddff",
                    on_done=after_streak_clear,
                )
            else:
                self._vocab_schedule_advance(VOCAB_CORRECT_ADVANCE_MS)
        else:
            self._vocab_streak = 0
            added = _add_vocab_notebook_item(lang, item)
            if self.vocab_status_label:
                tip = "已加入生词本" if added else "已在生词本"
                self.vocab_status_label.config(text=f"正确答案：{correct}\n（{tip}）", fg="#ffaa44")
            self._save_game_record(
                "vocab",
                {"lang": lang, "word": item["word"], "correct": False, "difficulty": self.difficulty},
            )
            self._vocab_schedule_advance(VOCAB_WRONG_ADVANCE_MS)

    def _open_leaderboard(self) -> None:
        self._hide_main_menu()
        if not PET_ID_FEATURE:
            self._show_toast("当前为无编号版本，暂无持有者排名", "#ff8844")
            return
        if self.leaderboard_win and self.leaderboard_win.winfo_exists():
            self.leaderboard_win.destroy()
            self.leaderboard_win = None
            return

        board = _load_leaderboard()
        bucket_order = ["gather"]
        for lang in ("中文", "英语", "日语"):
            bucket_order.append(f"typing:{lang}")
        for lang in ("英语", "中文", "日语"):
            bucket_order.append(f"vocab:{lang}")
        bucket_order.append("rhyme")
        bucket_order.append("music")
        extra = sorted(k for k in board if k not in bucket_order)
        ordered_buckets = [b for b in bucket_order if board.get(b)] + [b for b in extra if board.get(b)]

        self.leaderboard_win = tk.Toplevel(self.root)
        self.leaderboard_win.title("持有者排名")
        self.leaderboard_win.attributes("-topmost", True)
        self.leaderboard_win.configure(bg=MENU_BG)

        _, outer = _pack_fixed_scroll_panel(self.leaderboard_win)
        tk.Label(outer, text="持有者排名", font=PIXEL_FONT, fg=PIXEL_COLOR, bg=MENU_BG).pack(anchor=tk.W)
        tk.Label(
            outer,
            text="各游戏排名 · 仅显示桌宠编号 ·（你）为当前编号",
            font=PIXEL_FONT,
            fg="#888888",
            bg=MENU_BG,
        ).pack(anchor=tk.W, pady=(2, 8))

        list_wrap = tk.Frame(outer, bg=MENU_BG)
        list_wrap.pack(fill=tk.BOTH)

        if not ordered_buckets:
            tk.Label(list_wrap, text="暂无排名记录，先去玩游戏吧~", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG).pack(
                anchor=tk.W
            )
            self._place_panel_popup(self.leaderboard_win)
            return

        for bucket in ordered_buckets:
            rows = board.get(bucket, [])
            if not rows:
                continue
            tk.Label(
                list_wrap,
                text=f"【{_leaderboard_bucket_title(bucket)}】",
                font=PIXEL_FONT,
                fg="#88ccff",
                bg=MENU_BG,
            ).pack(anchor=tk.W, pady=(6, 2))
            sorted_rows = sorted(rows, key=lambda row: _leaderboard_sort_key(bucket, row))
            for rank, entry in enumerate(sorted_rows[:20], 1):
                line, fg = _format_leaderboard_line(bucket, rank, entry, current_pet_id=self.pet_id)
                tk.Label(list_wrap, text=line, font=PIXEL_FONT, fg=fg, bg=MENU_BG, anchor=tk.W).pack(fill=tk.X)
            if len(sorted_rows) > 20:
                tk.Label(
                    list_wrap,
                    text=f"  … 共 {len(sorted_rows)} 位持有者",
                    font=PIXEL_FONT,
                    fg="#666666",
                    bg=MENU_BG,
                ).pack(anchor=tk.W)
        self._place_panel_popup(self.leaderboard_win)

    def _open_about(self) -> None:
        self._hide_main_menu()
        if self.about_win and self.about_win.winfo_exists():
            self.about_win.lift()
            return
        self.about_win = tk.Toplevel(self.root)
        self.about_win.title("关于")
        self.about_win.attributes("-topmost", True)
        self.about_win.configure(bg=MENU_BG)
        _, frame = _pack_fixed_scroll_panel(self.about_win)
        _pack_panel_caption(frame, "关于 Vpet", fg=PIXEL_COLOR)
        _pack_panel_caption(frame, ABOUT_TEXT, pady=(8, 0))
        _pack_web_link(
            frame,
            "Steam · DRAMatical Murder",
            ABOUT_STEAM_URL,
            prefix="· ",
        )
        _pack_web_link(
            frame,
            "Nitro+CHiRAL 官网",
            ABOUT_NITROCHIRAL_URL,
            prefix="· ",
        )
        _pack_web_link(
            frame,
            "开源仓库 GitHub",
            ABOUT_REPO_URL,
            prefix="· ",
        )
        credits = " · ".join(ABOUT_CREDITS) if ABOUT_CREDITS else "（暂无）"
        _pack_panel_caption(frame, f"致谢：{credits}", fg="#aaaaaa", pady=(8, 0))
        if PET_ID_FEATURE and self.pet_id is not None:
            _pack_panel_caption(frame, f"本机编号：{_format_pet_id(self.pet_id)}", fg="#aaaaaa", pady=(8, 0))
        build_stamp = _read_build_stamp()
        if build_stamp:
            _pack_panel_caption(frame, f"构建版本：{build_stamp}", fg="#888888", pady=(6, 0))
        self._place_panel_popup(self.about_win)

    def _open_feedback(self) -> None:
        self._hide_main_menu()
        if self.feedback_win and self.feedback_win.winfo_exists():
            self.feedback_win.lift()
            return
        self.feedback_win = tk.Toplevel(self.root)
        self.feedback_win.title("问题反馈")
        self.feedback_win.attributes("-topmost", True)
        self.feedback_win.configure(bg=MENU_BG)
        _, frame = _pack_fixed_scroll_panel(self.feedback_win)
        _pack_panel_caption(frame, "问题反馈", fg=PIXEL_COLOR)
        _pack_panel_caption(
            frame,
            "如遇 bug、功能建议或素材贡献，欢迎通过以下方式联系。",
            pady=(8, 6),
        )
        if FEEDBACK_ISSUE_URL:
            _pack_web_link(frame, "GitHub Issues", FEEDBACK_ISSUE_URL, prefix="· ")
        else:
            _pack_panel_caption(frame, "· GitHub Issues：（预留）", fg="#888888")
        if FEEDBACK_EMAIL:
            _pack_web_link(
                frame,
                FEEDBACK_EMAIL,
                f"mailto:{FEEDBACK_EMAIL}",
                prefix="· 邮箱：",
            )
        else:
            _pack_panel_caption(frame, "· 邮箱：（预留）", fg="#888888")
        if FEEDBACK_XHS_ID and FEEDBACK_XHS_URL:
            _pack_web_link(
                frame,
                FEEDBACK_XHS_ID,
                FEEDBACK_XHS_URL,
                prefix="· 小红书：",
            )
        elif FEEDBACK_XHS_ID:
            _pack_panel_caption(frame, f"· 小红书：{FEEDBACK_XHS_ID}")
        if FEEDBACK_BILI_UID and FEEDBACK_BILI_URL:
            _pack_web_link(
                frame,
                FEEDBACK_BILI_UID,
                FEEDBACK_BILI_URL,
                prefix="· bilibili UID：",
            )
        elif FEEDBACK_BILI_UID:
            _pack_panel_caption(frame, f"· bilibili UID：{FEEDBACK_BILI_UID}")
        _pack_panel_caption(frame, FEEDBACK_NOTE, fg="#aaaaaa", pady=(10, 0))
        self._place_panel_popup(self.feedback_win)

    def _confirm_reset_settings(self) -> None:
        self._hide_main_menu()
        win = tk.Toplevel(self.root)
        win.title("重置确认")
        win.attributes("-topmost", True)
        win.configure(bg=MENU_BG)
        frame = tk.Frame(win, bg=MENU_BG, padx=12, pady=10)
        frame.pack()
        tk.Label(
            frame,
            text="确定恢复全部初始设置？\n编号不变；食物/日程/日记/游戏记录/声音/设置等将全部清空。",
            font=PIXEL_FONT,
            fg=MENU_FG,
            bg=MENU_BG,
            justify=tk.LEFT,
        ).pack()
        btn_row = tk.Frame(frame, bg=MENU_BG)
        btn_row.pack(pady=(10, 0))

        def do_reset() -> None:
            win.destroy()
            self._reset_all_settings()

        tk.Button(btn_row, text="确定重置", command=do_reset, font=PIXEL_FONT, bg="#884444", fg=MENU_FG).pack(
            side=tk.LEFT, padx=4
        )
        tk.Button(btn_row, text="取消", command=win.destroy, font=PIXEL_FONT, bg=MENU_ACTIVE, fg=MENU_FG).pack(
            side=tk.LEFT, padx=4
        )
        self._place_panel_popup(win)

    def _reset_all_settings(self) -> None:
        self._close_ai_chat()
        if self.schedule_win and self.schedule_win.winfo_exists():
            self.schedule_win.destroy()
            self.schedule_win = None
        if self.diary_win and self.diary_win.winfo_exists():
            self.diary_win.destroy()
            self.diary_win = None
        if getattr(self, "weather_win", None) and self.weather_win.winfo_exists():
            self._close_weather_forecast()
        if self.gallery_win and self.gallery_win.winfo_exists():
            self.gallery_win.destroy()
            self.gallery_win = None
        self.gallery_photos.clear()
        if self.panel_settings_win and self.panel_settings_win.winfo_exists():
            self.panel_settings_win.destroy()
            self.panel_settings_win = None
        self._destroy_all_mini_pets()
        self.companion_bar_enabled = False
        self.food_inventory = {fid: 0 for fid in FOODS}
        self.game_session_food = {}
        self.triggered_reminders_today.clear()
        _save_food_inventory(self.food_inventory)
        self.schedules = []
        _save_schedules(self.schedules)
        self.diary_entries = []
        _save_diary(self.diary_entries)
        self.music_config = {
            "play_mode": "list",
            "playlist": [DEFAULT_MUSIC_TRACK],
            "music_volume": 70,
            "volume": 70,
            "sfx_volume": 80,
            "voice_volume": 80,
            "muted": False,
        }
        _save_music_config(self.music_config)
        self.app_config = {
            "font_size": 12,
            "display_size": DEFAULT_SIZE,
            "display_preset": "中",
            "difficulty": "中",
            "seen_hints": {},
        }
        _save_app_config(self.app_config)
        if PET_ID_FEATURE:
            saved_id = self.pet_profile.get("pet_id")
            saved_created = self.pet_profile.get("created", "")
            self.pet_profile = {
                "pet_id": saved_id,
                "created": saved_created,
                "records": {},
            }
            _save_pet_profile(self.pet_profile)
        self.font_size = 12
        self.difficulty = "中"
        self._mood_decay_counter = 0
        _apply_font_size(12)
        self._apply_difficulty_runtime()
        if VOCAB_FILE.exists():
            try:
                VOCAB_FILE.unlink()
            except Exception:
                pass
        self.vocab_words = _load_vocab()
        self.stamina = 80
        self.mood = 70
        self.ai_history = []
        self._stop_bg_music()
        self.music_sprite_mode = False
        self._stop_music_wave_fx()
        self._interrupt_current_interaction()
        self.mode = "free"
        if DEFAULT_SIZE in self._sprite_cache:
            self._apply_size_preset("中", DEFAULT_SIZE)
        else:
            self._set_size_preset("中")
        self._refresh_panel()
        self._show_toast("已恢复初始设置（编号已保留）", PIXEL_COLOR, duration_ms=3000)

    def _open_action_menu(self) -> None:
        self._show_sub_menu(
            [
                ("打招呼", lambda: self._play_action("hi")),
                ("下蹲", lambda: self._play_action("squat")),
                ("打电话", lambda: self._play_action("call")),
                ("吃东西 ▶", lambda: self._open_eat_food_menu(offset_x=240)),
                ("睡眠", self._play_sleep_interact),
                ("工作 ▶", self._open_work_menu),
                ("侧踢", self._play_kick),
                ("×生活", self._play_adult_reserved),
                ("是", lambda: self._play_expression_sprite("yes", self.sprites.yes)),
                ("否", lambda: self._play_expression_sprite("no", self.sprites.no)),
                ("判断", self._play_yesno_judge),
            ],
            offset_x=180,
        )

    def _open_interact_menu(self) -> None:
        self._show_sub_menu(
            [
                ("动作 ▶", self._open_action_menu),
                ("表情 ▶", self._open_expression_menu),
            ],
            offset_x=120,
        )

    def _close_panel(self) -> None:
        self._cancel_timer_job("panel_hide_job")
        self._close_panel_backpack()
        if self.panel_win and self.panel_win.winfo_exists():
            self.panel_win.destroy()
        self.panel_win = None
        self._panel_backpack_sig = None
        self._panel_sticky_pos = None
        self._panel_reposition_ms = 0

    def _close_panel_backpack(self) -> None:
        win = getattr(self, "panel_backpack_win", None)
        if win and win.winfo_exists():
            win.destroy()
        self.panel_backpack_win = None
        self.backpack_grid = None
        self.backpack_icons_frame = None

    def _schedule_panel_auto_hide(self) -> None:
        self._cancel_timer_job("panel_hide_job")
        if not (self.panel_win and self.panel_win.winfo_exists()):
            return
        self.panel_hide_job = self._safe_after(PANEL_AUTO_CLOSE_MS, self._close_panel)

    def _bump_panel_auto_hide(self, _event=None) -> None:
        if self.panel_win and self.panel_win.winfo_exists():
            self._schedule_panel_auto_hide()

    def _toggle_panel(self) -> None:
        if self.panel_win and self.panel_win.winfo_exists():
            self._close_panel()
            return

        self.panel_win = tk.Toplevel(self.root)
        self.panel_win.overrideredirect(True)
        self.panel_win.attributes("-topmost", True)
        self.panel_win.configure(bg="#1a1a1a")

        frame = tk.Frame(self.panel_win, bg="#1a1a1a", padx=8, pady=6)
        frame.pack()

        tk.Label(frame, text="面板", font=PIXEL_FONT, fg=PIXEL_COLOR, bg="#1a1a1a").pack(anchor=tk.W)

        stamina_row = tk.Frame(frame, bg="#1a1a1a")
        stamina_row.pack(fill=tk.X, pady=(6, 3))
        self.stamina_icon_canvas = tk.Canvas(
            stamina_row, width=PANEL_STAT_ICON, height=PANEL_STAT_ICON, bg="#1a1a1a", highlightthickness=0
        )
        self.stamina_icon_canvas.pack(side=tk.LEFT, padx=(0, 6))
        stat_col = tk.Frame(stamina_row, bg="#1a1a1a")
        stat_col.pack(side=tk.LEFT, fill=tk.X)
        self.stamina_bar = tk.Canvas(stat_col, width=PANEL_BAR_W, height=PANEL_BAR_H, bg="#1a1a1a", highlightthickness=0)
        self.stamina_bar.pack(anchor=tk.W)
        self.stamina_label = tk.Label(stat_col, text="", font=PIXEL_FONT, fg=MENU_FG, bg="#1a1a1a")
        self.stamina_label.pack(anchor=tk.W, pady=(2, 0))

        mood_row = tk.Frame(frame, bg="#1a1a1a")
        mood_row.pack(fill=tk.X, pady=(0, 4))
        self.mood_icon_canvas = tk.Canvas(
            mood_row, width=PANEL_STAT_ICON, height=PANEL_STAT_ICON, bg="#1a1a1a", highlightthickness=0
        )
        self.mood_icon_canvas.pack(side=tk.LEFT, padx=(0, 6))
        mood_col = tk.Frame(mood_row, bg="#1a1a1a")
        mood_col.pack(side=tk.LEFT, fill=tk.X)
        self.mood_bar = tk.Canvas(mood_col, width=PANEL_BAR_W, height=PANEL_BAR_H, bg="#1a1a1a", highlightthickness=0)
        self.mood_bar.pack(anchor=tk.W)
        self.mood_label = tk.Label(mood_col, text="", font=PIXEL_FONT, fg=MENU_FG, bg="#1a1a1a")
        self.mood_label.pack(anchor=tk.W, pady=(2, 0))

        tk.Button(
            frame,
            text="背包",
            command=self._toggle_panel_backpack,
            font=PIXEL_FONT,
            bg="#334466",
            fg="#ffcc66",
            relief=tk.FLAT,
            cursor="hand2",
            padx=8,
        ).pack(anchor=tk.W, pady=(4, 0))

        self.backpack_icons_frame = None
        self.backpack_grid = None

        for seq in ("<Enter>", "<Motion>", "<Button-1>", "<ButtonRelease-1>"):
            self.panel_win.bind(seq, self._bump_panel_auto_hide, add="+")
            frame.bind(seq, self._bump_panel_auto_hide, add="+")

        self._panel_sticky_pos = None
        self._refresh_panel()
        self._reposition_panel(force=True)
        self._wire_panel_auto_hide(self.panel_win)
        self._schedule_panel_auto_hide()

    def _toggle_panel_backpack(self) -> None:
        self._bump_panel_auto_hide()
        if self.panel_backpack_win and self.panel_backpack_win.winfo_exists():
            self._close_panel_backpack()
            return
        self.panel_backpack_win = tk.Toplevel(self.root)
        self.panel_backpack_win.overrideredirect(True)
        self.panel_backpack_win.attributes("-topmost", True)
        self.panel_backpack_win.configure(bg="#1a1a1a")
        frame = tk.Frame(self.panel_backpack_win, bg="#1a1a1a", padx=8, pady=6)
        frame.pack(fill=tk.BOTH, expand=True)
        head = tk.Frame(frame, bg="#1a1a1a")
        head.pack(fill=tk.X)
        tk.Label(head, text="背包 · 食物", font=PIXEL_FONT, fg="#ffcc66", bg="#1a1a1a").pack(side=tk.LEFT)
        tk.Button(
            head,
            text="×",
            command=self._close_panel_backpack,
            font=PIXEL_FONT,
            bg="#444444",
            fg=MENU_FG,
            relief=tk.FLAT,
            padx=4,
        ).pack(side=tk.RIGHT)
        scroll_wrap, inner, _canvas = _make_scrollable_frame(
            frame, width=PANEL_BACKPACK_W - 24, height=PANEL_BACKPACK_H, bg="#1a1a1a"
        )
        scroll_wrap.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
        self.backpack_icons_frame = frame
        self.backpack_grid = inner
        self._panel_backpack_sig = None
        self._refresh_panel_backpack()
        # 贴在面板旁边
        try:
            if self.panel_win and self.panel_win.winfo_exists():
                self.panel_win.update_idletasks()
                px = self.panel_win.winfo_rootx() + self.panel_win.winfo_width() + 6
                py = self.panel_win.winfo_rooty()
                self.panel_backpack_win.geometry(f"+{px}+{py}")
            else:
                self._place_panel_popup(self.panel_backpack_win)
        except Exception:
            self._place_panel_popup(self.panel_backpack_win)
        self._wire_panel_auto_hide(self.panel_backpack_win)
        self._schedule_panel_auto_hide()

    def _wire_panel_auto_hide(self, widget: tk.Misc) -> None:
        for seq in ("<Enter>", "<Button-1>", "<ButtonRelease-1>", "<B1-Motion>"):
            try:
                widget.bind(seq, self._bump_panel_auto_hide, add="+")
            except Exception:
                pass
        try:
            children = widget.winfo_children()
        except Exception:
            return
        for child in children:
            self._wire_panel_auto_hide(child)

    def _reposition_panel(self, *, force: bool = False) -> None:
        if not self.panel_win or not self.panel_win.winfo_exists():
            return
        try:
            self.panel_win.update_idletasks()
        except Exception:
            pass
        pw = max(self.panel_win.winfo_reqwidth(), 220)
        ph = max(self.panel_win.winfo_reqheight(), 140)
        now_ms = int(time.time() * 1000)
        if (
            not force
            and self._panel_sticky_pos is not None
            and now_ms - self._panel_reposition_ms < PANEL_REPOSITION_MIN_MS
        ):
            # 内容变化时仅钳制原位置，避免频繁跳点导致点不到
            px, py = self._clamp_popup_rect(self._panel_sticky_pos[0], self._panel_sticky_pos[1], pw, ph)
            self.panel_win.geometry(f"+{px}+{py}")
            return
        if force or self._panel_sticky_pos is None:
            px, py = self._panel_popup_pos(pw, ph)
            self._panel_sticky_pos = (px, py)
            self._panel_reposition_ms = now_ms
        else:
            px, py = self._clamp_popup_rect(self._panel_sticky_pos[0], self._panel_sticky_pos[1], pw, ph)
            self._panel_sticky_pos = (px, py)
        self.panel_win.geometry(f"+{px}+{py}")

    def _draw_bar(self, canvas: tk.Canvas, value: int, color: str) -> None:
        _draw_panel_bar(canvas, value, color)

    def _food_backpack_signature(self) -> tuple[tuple[str, int], ...]:
        return tuple(sorted((k, v) for k, v in self.food_inventory.items() if v > 0))

    def _refresh_panel_stats(self) -> None:
        if self.stamina_icon_canvas and self.stamina_icon_canvas.winfo_exists():
            _draw_stamina_pixel_icon(self.stamina_icon_canvas, PANEL_STAT_ICON)
        mood_label, mood_color = _mood_tier_label(self.mood)
        if self.mood_icon_canvas and self.mood_icon_canvas.winfo_exists():
            _draw_mood_pixel_icon(self.mood_icon_canvas, PANEL_STAT_ICON, fill=mood_color)
        self._draw_bar(self.stamina_bar, self.stamina, "#44aa44")
        self._draw_bar(self.mood_bar, self.mood, mood_color)
        self.stamina_label.config(text=f"体力  {self.stamina}")
        self.mood_label.config(text=f"心情  {self.mood}  {mood_label}", fg=mood_color)

    def _refresh_panel_backpack(self) -> None:
        if not self.backpack_grid or not self.backpack_grid.winfo_exists():
            return
        for w in self.backpack_grid.winfo_children():
            w.destroy()
        col = 0
        food_items = sorted(
            FOODS.items(),
            key=lambda item: (item[1]["mood"], item[1]["stamina"]),
            reverse=True,
        )
        pad = max(2, (PANEL_FOOD_CANVAS - PANEL_FOOD_ICON_PX * 5) // 2)
        for food_id, info in food_items:
            count = self.food_inventory.get(food_id, 0)
            if count <= 0:
                continue
            cell = tk.Frame(self.backpack_grid, bg="#1a1a1a", padx=4, pady=3)
            cell.grid(row=col // PANEL_FOOD_COLS, column=col % PANEL_FOOD_COLS, sticky=tk.NW, padx=4, pady=3)
            icon = tk.Canvas(cell, width=PANEL_FOOD_CANVAS, height=PANEL_FOOD_CANVAS, bg="#252525", highlightthickness=0)
            icon.pack()
            icon.create_rectangle(0, 0, PANEL_FOOD_CANVAS, PANEL_FOOD_CANVAS, fill="#252525", outline="#444444")
            _draw_pixel_food(icon, food_id, pad, pad, px=PANEL_FOOD_ICON_PX)
            tk.Label(cell, text=f"{info['label']} ×{count}", font=PIXEL_FONT, fg="#ffcc66", bg="#1a1a1a").pack()
            tk.Label(
                cell,
                text=f"体+{info['stamina']} 心+{info['mood']}",
                font=("Courier New", 9),
                fg="#888888",
                bg="#1a1a1a",
            ).pack()
            col += 1
        if col == 0:
            tk.Label(self.backpack_grid, text="空", font=PIXEL_FONT, fg="#666666", bg="#1a1a1a").grid(
                row=0, column=0
            )
        if self.panel_backpack_win and self.panel_backpack_win.winfo_exists():
            self._wire_panel_auto_hide(self.backpack_grid)

    def _refresh_panel(self) -> None:
        if not self.panel_win or not self.panel_win.winfo_exists():
            return
        self._refresh_panel_stats()
        if self.panel_backpack_win and self.panel_backpack_win.winfo_exists():
            sig = self._food_backpack_signature()
            if sig != self._panel_backpack_sig:
                self._panel_backpack_sig = sig
                self._refresh_panel_backpack()
        self._reposition_panel(force=False)

    def _cancel_game_countdown(self) -> None:
        self._countdown_token = getattr(self, "_countdown_token", 0) + 1
        self._countdown_active = False
        self._hide_countdown_overlay()

    def _hide_countdown_overlay(self) -> None:
        win = getattr(self, "countdown_win", None)
        if win and win.winfo_exists():
            win.destroy()
        self.countdown_win = None
        self.countdown_label = None

    def _show_countdown_overlay(self, text: str) -> None:
        self._hide_countdown_overlay()
        self.countdown_win = tk.Toplevel(self.root)
        self.countdown_win.overrideredirect(True)
        self.countdown_win.attributes("-topmost", True)
        try:
            self.countdown_win.attributes("-alpha", 0.92)
        except Exception:
            pass
        self.countdown_win.configure(bg="#101018")
        border = tk.Frame(self.countdown_win, bg="#88ccff", padx=2, pady=2)
        border.pack()
        inner = tk.Frame(border, bg="#101018", width=GAME_COUNTDOWN_W, height=GAME_COUNTDOWN_H)
        inner.pack()
        inner.pack_propagate(False)
        self.countdown_label = tk.Label(
            inner,
            text=text,
            font=COUNTDOWN_FONT,
            fg="#ffee88",
            bg="#101018",
        )
        self.countdown_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        cx = self.x + self.display_size // 2 - GAME_COUNTDOWN_W // 2
        cy = self.y + self.display_size // 2 - GAME_COUNTDOWN_H // 2
        self._place_popup(self.countdown_win, max(8, cx), max(8, cy))

    def _start_game_countdown(self, on_ready, *, title: str = "") -> None:
        self._cancel_game_countdown()
        self._countdown_active = True
        token = self._countdown_token
        steps = ("3", "2", "1", "开始")

        def step(i: int = 0) -> None:
            if token != self._countdown_token:
                return
            if i >= len(steps):
                self._countdown_active = False
                self._hide_countdown_overlay()
                on_ready()
                return
            self._show_countdown_overlay(steps[i])
            self.root.after(GAME_COUNTDOWN_STEP_MS, lambda: step(i + 1))

        step()

    def _show_toast(self, text: str, color: str = PIXEL_COLOR, *, duration_ms: int = TOAST_DURATION_MS) -> None:
        self._hide_toast()

        self.toast_win = tk.Toplevel(self.root)
        self.toast_win.overrideredirect(True)
        self.toast_win.attributes("-topmost", True)
        self.toast_win.configure(bg="#111122")

        border = tk.Frame(self.toast_win, bg=color, padx=1, pady=1)
        border.pack()
        inner = tk.Frame(border, bg="#111122", padx=10, pady=6)
        inner.pack()
        tk.Label(inner, text=text, font=PIXEL_FONT, fg=color, bg="#111122").pack()

        toast_y = max(0, self.y - 36)
        self._place_popup(self.toast_win, self.x + self.display_size + 8, toast_y)
        self.root.after(duration_ms, self._hide_toast)

    def _hide_toast(self) -> None:
        if self.toast_win and self.toast_win.winfo_exists():
            self.toast_win.destroy()
        self.toast_win = None

    def _stamina_tick(self) -> None:
        if not self._alive():
            return
        params = self._difficulty_params()
        if not self._startup_ready:
            self._safe_after(400, self._stamina_tick)
            return
        if self.state == "sleep" or self.mode == "quiet":
            pass
        elif self.stamina > 0:
            self.stamina = max(0, self.stamina - int(params["stamina_decay"]))
            self._refresh_panel()
            if self.stamina <= SLEEP_STAMINA_THRESHOLD:
                self._start_sleep(forced=True)
        if self.mode not in ("game",) and self.mood > 0:
            self._mood_decay_counter += 1
            every = max(1, int(params["mood_decay_every"]))
            if self._mood_decay_counter >= every:
                self._mood_decay_counter = 0
                self.mood = max(0, self.mood - int(params["mood_decay"]))
                self._refresh_panel()
        self._check_hunger_reminder()
        self._safe_after(int(params["stamina_tick_ms"]), self._stamina_tick)

    def _check_hunger_reminder(self) -> None:
        if self.stamina > LOW_STAMINA_THRESHOLD:
            return
        now_ms = int(time.time() * 1000)
        if now_ms - self.last_hunger_reminder_ms < HUNGER_REMINDER_COOLDOWN_MS:
            return
        self.last_hunger_reminder_ms = now_ms
        self._show_toast("肚子饿了，去模式→游戏接食物，再来喂我吧！", "#ff8844", duration_ms=3000)

    def _add_interact_mood(self) -> None:
        self.mood = min(100, self.mood + INTERACT_MOOD_GAIN)
        self._refresh_panel()

    def _check_mood_happy(self) -> bool:
        if self.mood < MOOD_HAPPY_THRESHOLD or self.dragging:
            return False
        if self.state == "action" and self.action_name in ("happy", "angry", "question"):
            return False
        self.mood = MOOD_AFTER_HAPPY
        self._refresh_panel()
        self._show_toast("心情超好！", PIXEL_COLOR)
        self._play_happy()
        return True

    def _hide_interact_fx(self) -> None:
        if self.interact_fx_stop_job:
            self.root.after_cancel(self.interact_fx_stop_job)
            self.interact_fx_stop_job = None
        if self.interact_fx_win and self.interact_fx_win.winfo_exists():
            self.interact_fx_win.destroy()
        self.interact_fx_win = None
        self.interact_fx_canvas = None
        self.interact_fx_action = ""
        self._notify_bg_fx_change()

    def _place_interact_fx(self) -> None:
        if not self.interact_fx_win or not self.interact_fx_win.winfo_exists():
            return
        pad = INTERACT_FX_PAD
        display_y = self.y + self.click_bounce_offset
        self.interact_fx_win.geometry(f"+{self.x - pad}+{display_y - pad}")

    def _show_interact_fx(self, action: str) -> None:
        self._hide_interact_fx()
        self.interact_fx_action = action
        self.interact_fx_phase = 0
        pad = INTERACT_FX_PAD
        size = self.display_size + pad * 2
        self.interact_fx_win = tk.Toplevel(self.root)
        self.interact_fx_win.overrideredirect(True)
        self.interact_fx_win.attributes("-topmost", False)
        self.interact_fx_win.configure(bg="magenta")
        self.interact_fx_win.wm_attributes("-transparentcolor", "magenta")
        self.interact_fx_canvas = tk.Canvas(
            self.interact_fx_win, width=size, height=size, bg="magenta", highlightthickness=0
        )
        self.interact_fx_canvas.pack()
        self._place_interact_fx()
        self._animate_interact_fx()
        if self.interact_fx_stop_job:
            self.root.after_cancel(self.interact_fx_stop_job)
        self.interact_fx_stop_job = self.root.after(INTERACT_FX_DURATION_MS, self._hide_interact_fx)
        self._notify_bg_fx_change()

    def _animate_interact_fx(self) -> None:
        if not self.interact_fx_canvas or not self.interact_fx_action:
            return
        size = self.interact_fx_canvas.winfo_width() or (self.display_size + INTERACT_FX_PAD * 2)
        _draw_interact_fx(self.interact_fx_canvas, self.interact_fx_action, size, self.interact_fx_phase)
        self.interact_fx_phase += 1
        self._place_interact_fx()
        self.root.after(INTERACT_FX_MS, self._animate_interact_fx)

    def _hide_like_fx(self) -> None:
        if self.like_glow_job:
            try:
                self.root.after_cancel(self.like_glow_job)
            except Exception:
                pass
            self.like_glow_job = None
        if self.like_fx_win and self.like_fx_win.winfo_exists():
            self.like_fx_win.destroy()
        self.like_fx_win = None
        self.like_fx_canvas = None
        self._notify_bg_fx_change()

    def _animate_like_glow(self) -> None:
        if not self.like_fx_canvas or self.action_name not in ("like", "wink"):
            self.like_glow_job = None
            return
        size = self.like_fx_canvas.winfo_width() or (self.display_size + 40)
        _draw_like_glow(self.like_fx_canvas, size, self.like_glow_phase)
        self.like_glow_phase += 1
        self._place_like_fx()
        self.like_glow_job = self.root.after(90, self._animate_like_glow)

    def _hide_wink_fx(self) -> None:
        if self.wink_fx_job:
            try:
                self.root.after_cancel(self.wink_fx_job)
            except Exception:
                pass
            self.wink_fx_job = None
        if self.wink_fx_win and self.wink_fx_win.winfo_exists():
            self.wink_fx_win.destroy()
        self.wink_fx_win = None
        self.wink_fx_canvas = None
        self._notify_bg_fx_change()

    def _place_wink_fx(self) -> None:
        if not self.wink_fx_win or not self.wink_fx_win.winfo_exists():
            return
        pad = 20
        display_y = self.y + self.click_bounce_offset
        self.wink_fx_win.geometry(f"+{self.x - pad}+{display_y - pad}")

    def _animate_wink_fx(self) -> None:
        if not self.wink_fx_canvas:
            self.wink_fx_job = None
            return
        if self.action_name != "wink":
            self.wink_fx_job = None
            return
        if int(time.time() * 1000) - self.wink_fx_started_ms >= WINK_DURATION_MS:
            self.wink_fx_job = None
            if self.action_name == "wink":
                self._after_wink_expression()
            return
        size = self.wink_fx_canvas.winfo_width() or (self.display_size + 40)
        self.wink_fx_canvas.delete("all")
        _draw_like_glow(self.wink_fx_canvas, size, self.wink_fx_phase)
        _draw_heart_wave(self.wink_fx_canvas, size, self.wink_fx_phase, clear=False)
        self.wink_fx_phase += 1
        self._place_wink_fx()
        self.wink_fx_job = self.root.after(100, self._animate_wink_fx)

    def _show_wink_fx(self) -> None:
        self._hide_wink_fx()
        pad = 20
        size = self.display_size + pad * 2
        self.wink_fx_win = tk.Toplevel(self.root)
        self.wink_fx_win.overrideredirect(True)
        self.wink_fx_win.attributes("-topmost", False)
        self.wink_fx_win.configure(bg="magenta")
        self.wink_fx_win.wm_attributes("-transparentcolor", "magenta")
        self.wink_fx_canvas = tk.Canvas(
            self.wink_fx_win, width=size, height=size, bg="magenta", highlightthickness=0
        )
        self.wink_fx_canvas.pack()
        self.wink_fx_phase = 0
        self.wink_fx_started_ms = int(time.time() * 1000)
        self._place_wink_fx()
        self._animate_wink_fx()
        self._notify_bg_fx_change()

    def _place_like_fx(self) -> None:
        if not self.like_fx_win or not self.like_fx_win.winfo_exists():
            return
        pad = 20
        display_y = self.y + self.click_bounce_offset
        self.like_fx_win.geometry(f"+{self.x - pad}+{display_y - pad}")

    def _show_like_fx(self) -> None:
        self._hide_like_fx()
        self._hide_shy_fx()
        self._hide_wink_fx()
        self._hide_follow_dizzy_fx()
        pad = 20
        size = self.display_size + pad * 2
        self.like_fx_win = tk.Toplevel(self.root)
        self.like_fx_win.overrideredirect(True)
        self.like_fx_win.attributes("-topmost", False)
        self.like_fx_win.configure(bg="magenta")
        self.like_fx_win.wm_attributes("-transparentcolor", "magenta")
        self.like_fx_canvas = tk.Canvas(
            self.like_fx_win, width=size, height=size, bg="magenta", highlightthickness=0
        )
        self.like_fx_canvas.pack()
        px = max(3, self.display_size // 28)
        star_colors = ("#ffff88", "#ffcc44", "#ffffff", "#88ccff", "#ff88cc", "#88ffcc")
        for _ in range(22):
            sx = random.randint(2, size - 14)
            sy = random.randint(2, size - 14)
            _draw_pixel_star(self.like_fx_canvas, sx, sy, px=max(2, px - 1), color=random.choice(star_colors))
        for _ in range(8):
            sx = random.randint(0, size - 10)
            sy = random.randint(0, size - 10)
            _draw_pixel_star(
                self.like_fx_canvas, sx, sy, px=max(1, px - 2), color=random.choice(star_colors)
            )
        self._place_like_fx()
        self._notify_bg_fx_change()

    def _hide_shy_fx(self) -> None:
        if self.shy_fx_win and self.shy_fx_win.winfo_exists():
            self.shy_fx_win.destroy()
        self.shy_fx_win = None
        self.shy_fx_canvas = None
        self._notify_bg_fx_change()

    def _place_shy_fx(self) -> None:
        if not self.shy_fx_win or not self.shy_fx_win.winfo_exists():
            return
        pad = 20
        display_y = self.y + self.click_bounce_offset
        self.shy_fx_win.geometry(f"+{self.x - pad}+{display_y - pad}")

    def _show_shy_fx(self) -> None:
        self._hide_shy_fx()
        pad = 20
        size = self.display_size + pad * 2
        self.shy_fx_win = tk.Toplevel(self.root)
        self.shy_fx_win.overrideredirect(True)
        self.shy_fx_win.attributes("-topmost", False)
        self.shy_fx_win.configure(bg="magenta")
        self.shy_fx_win.wm_attributes("-transparentcolor", "magenta")
        self.shy_fx_canvas = tk.Canvas(
            self.shy_fx_win, width=size, height=size, bg="magenta", highlightthickness=0
        )
        self.shy_fx_canvas.pack()
        px = max(2, self.display_size // 36)
        heart_colors = ("#ff6688", "#ff88aa", "#ff4466", "#ff99bb")
        for _ in range(8):
            hx = random.randint(4, size - 16)
            hy = random.randint(4, size - 16)
            _draw_pixel_heart(self.shy_fx_canvas, hx, hy, px=px, color=random.choice(heart_colors))
        self._place_shy_fx()
        self._notify_bg_fx_change()

    def _interact_flair(self, action: str, *, banter: bool = True, show_fx: bool = True) -> None:
        if self.music_sprite_mode:
            return
        if show_fx and action == "kick":
            self._show_interact_fx(action)
        if not banter or action not in INTERACT_BANTER:
            return
        if self.speech_dialog and self.speech_dialog.winfo_exists():
            return
        line = random.choice(INTERACT_BANTER[action])
        self._show_speech_dialog(line, auto_hide_ms=2400)

    def _get_mini_pet_sprites(self, size: int) -> dict:
        if size not in self._mini_pet_sprite_cache:
            ref = _reference_scale(size)

            def load(filename: str, *, flip: bool = False) -> ImageTk.PhotoImage:
                canvas = _get_processed_canvas(filename, size, ref, flip=flip)
                return ImageTk.PhotoImage(canvas)

            self._mini_pet_sprite_cache[size] = {
                "stand": load("petstand.jpg"),
                "front": (load("petfront1.jpg"), load("petfront2.jpg")),
                "back": (load("petback1.jpg"), load("petback2.jpg")),
                "left": (load("petleft1.jpg"), load("petleft2.jpg")),
                "right": (load("petleft1.jpg", flip=True), load("petleft2.jpg", flip=True)),
            }
        return self._mini_pet_sprite_cache[size]

    def _toggle_companion_bar(self) -> None:
        self._hide_main_menu()
        self.companion_bar_enabled = not self.companion_bar_enabled
        if self.companion_bar_enabled:
            if not self.mini_pets:
                self._show_companion_loading(lambda: self._spawn_mini_pet_impl(silent=True))
            else:
                for entry in self.mini_pets:
                    self._mini_pet_follow_tick(entry)
                self._sync_mini_pet_music_waves()
            self._show_toast("智能伴侣栏已开启", "#88ccff", duration_ms=1500)
            self._show_once_hint("companion_bar", duration_ms=3500)
        else:
            self._destroy_all_mini_pets()
            self._show_toast("智能伴侣栏已关闭", PIXEL_COLOR, duration_ms=1500)

    def _spawn_mini_pet(self, *, silent: bool = False) -> None:
        if not silent:
            self._hide_main_menu()
        if not self.companion_bar_enabled:
            self.companion_bar_enabled = True
        if len(self.mini_pets) >= MINI_PET_MAX:
            if not silent:
                self._show_toast(f"最多同时存在 {MINI_PET_MAX} 个金目哦~", "#ff8844")
            return
        self._show_companion_loading(lambda: self._spawn_mini_pet_impl(silent=silent))

    def _spawn_mini_pet_impl(self, *, silent: bool = False) -> None:
        size = MINI_PET_SIZE
        sprites = self._get_mini_pet_sprites(size)
        photo = sprites["stand"]
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg="magenta")
        win.wm_attributes("-transparentcolor", "magenta")
        lbl = tk.Label(win, image=photo, bg="magenta", bd=0)
        lbl.image = photo
        lbl.pack()
        idx = len(self.mini_pets)
        side = "left" if idx % 2 == 0 else "right"
        gap = MINI_PET_SIDE_GAP
        if side == "left":
            start_x = self.x - size - gap
        else:
            start_x = self.x + self.display_size + gap
        start_y = self.y + self.display_size - size
        win.geometry(f"+{int(start_x)}+{int(start_y)}")
        entry: dict = {
            "win": win,
            "label": lbl,
            "photo": photo,
            "sprites": sprites,
            "x": float(start_x),
            "y": float(start_y),
            "size": size,
            "index": idx,
            "side": side,
            "move_dir": "front",
            "follow_job": None,
            "bounce_offset": 0,
            "last_pet_x": self.x,
            "last_pet_y": self.y,
            "wave_win": None,
            "wave_canvas": None,
            "wave_phase": 0,
            "wave_job": None,
        }
        self.mini_pets.append(entry)
        self._mini_pet_follow_tick(entry)
        self._sync_mini_pet_music_waves()
        self._notify_bg_fx_change()
        if not silent:
            self._show_toast("噗~ 金目来陪你啦！", "#88ccff", duration_ms=1500)

    def _mini_pet_side_target(self, entry: dict) -> tuple[float, float]:
        size = entry["size"]
        gap = MINI_PET_SIDE_GAP
        if self.state == "action" and self.action_name == "sad" and self.companion_bar_enabled:
            gap = MINI_PET_SAD_GAP
        elif self.state == "action" and self.action_name == "angry" and self.companion_bar_enabled:
            gap = MINI_PET_ANGRY_GAP
        if entry.get("side", "left") == "left":
            target_x = self.x - size - gap
        else:
            target_x = self.x + self.display_size + gap
        target_y = self.y + self.display_size - size
        return target_x, target_y

    def _mini_pet_main_moving(self, entry: dict) -> bool:
        last_x = entry.get("last_pet_x", self.x)
        last_y = entry.get("last_pet_y", self.y)
        entry["last_pet_x"] = self.x
        entry["last_pet_y"] = self.y
        if abs(self.x - last_x) > 0 or abs(self.y - last_y) > 0:
            return True
        return self.state == "walk" or self.follow_animating or self.work_animating

    def _mini_pet_move_dir(self, dx: float, dy: float) -> str:
        if abs(dx) >= abs(dy):
            return "left" if dx < 0 else "right"
        return "front" if dy > 0 else "back"

    def _set_mini_pet_sprite(self, entry: dict, photo: ImageTk.PhotoImage) -> None:
        lbl = entry.get("label")
        if lbl and lbl.winfo_exists():
            lbl.config(image=photo)
            lbl.image = photo
        entry["photo"] = photo

    def _mini_pet_follow_tick(self, entry: dict) -> None:
        if entry not in self.mini_pets or not self.companion_bar_enabled:
            return
        win = entry.get("win")
        if not win or not win.winfo_exists():
            return

        size = entry["size"]
        sprites = entry["sprites"]
        angry_active = self.state == "action" and self.action_name == "angry"
        last_x = entry.get("last_pet_x", self.x)
        last_y = entry.get("last_pet_y", self.y)
        pet_moved = abs(self.x - last_x) > 0 or abs(self.y - last_y) > 0
        if angry_active:
            entry["last_pet_x"] = self.x
            entry["last_pet_y"] = self.y
            main_moving = pet_moved
        else:
            main_moving = self._mini_pet_main_moving(entry)

        target_x, target_y = self._mini_pet_side_target(entry)
        mx, my = entry["x"], entry["y"]
        dx = target_x - mx
        dy = target_y - my
        dist = math.hypot(dx, dy)
        game_mode = self.mode == "game"
        if angry_active:
            step = MINI_PET_FOLLOW_STEP * 2.5
            follow_ms = max(20, MINI_PET_FOLLOW_MS // 2)
        elif game_mode:
            step = MINI_PET_GAME_FOLLOW_STEP
            follow_ms = MINI_PET_GAME_FOLLOW_MS
        else:
            step = MINI_PET_FOLLOW_STEP
            follow_ms = MINI_PET_FOLLOW_MS
        mini_moving = dist > 1.5
        if dist > step:
            mx += dx / dist * step
            my += dy / dist * step
            mini_moving = True
        elif (game_mode or angry_active) and dist > 0.5:
            mx, my = target_x, target_y
        else:
            mx, my = target_x, target_y

        use_walk = (not game_mode) and (not angry_active) and (mini_moving or main_moving)
        angry_walk = angry_active and self.angry_walk_phase

        if angry_walk:
            frame_idx = (int(time.time() * 1000) // WALK_FRAME_MS) % 2
            walk_frames = sprites.get("back", sprites["front"])
            self._set_mini_pet_sprite(entry, walk_frames[frame_idx])
        elif use_walk:
            move_dir = self._mini_pet_move_dir(dx if dist > 0.5 else 0, dy if dist > 0.5 else 0)
            if dist <= 0.5 and main_moving:
                move_dir = self.direction
            entry["move_dir"] = move_dir
            frame_idx = (int(time.time() * 1000) // WALK_FRAME_MS) % 2
            walk_frames = sprites.get(move_dir, sprites["front"])
            self._set_mini_pet_sprite(entry, walk_frames[frame_idx])
        else:
            self._set_mini_pet_sprite(entry, sprites["stand"])

        entry["x"], entry["y"] = mx, my
        bounce = int(entry.get("bounce_offset", 0))
        win.geometry(f"+{int(mx)}+{int(my) + bounce}")
        self._place_mini_pet_music_wave(entry)
        self._place_mini_pet_bg_fx(entry)
        entry["follow_job"] = self.root.after(follow_ms, lambda e=entry: self._mini_pet_follow_tick(e))

    def _mini_pet_desired_bg_fx_kind(self) -> str | None:
        if not self.companion_bar_enabled:
            return None
        if self._dizzy_fx_active():
            return "dizzy"
        if self.happy_fx_win and self.happy_fx_win.winfo_exists():
            return "happy"
        if self.shy_fx_win and self.shy_fx_win.winfo_exists():
            return "shy"
        if self.wink_fx_win and self.wink_fx_win.winfo_exists():
            return "wink"
        if self.interact_fx_win and self.interact_fx_win.winfo_exists():
            return f"interact:{self.interact_fx_action}"
        if self.food_fx_win and self.food_fx_win.winfo_exists():
            return f"food:{self.food_fx_id or 'default'}"
        return None

    def _mini_pet_bg_pad(self, entry: dict, base_pad: int) -> int:
        return max(6, int(base_pad * entry["size"] / max(1, self.display_size)))

    def _stop_mini_pet_bg_fx(self, entry: dict) -> None:
        job = entry.get("bg_fx_job")
        if job:
            try:
                self.root.after_cancel(job)
            except Exception:
                pass
        win = entry.get("bg_fx_win")
        if win and win.winfo_exists():
            win.destroy()
        entry["bg_fx_win"] = None
        entry["bg_fx_canvas"] = None
        entry["bg_fx_kind"] = None
        entry["bg_fx_job"] = None
        entry["bg_fx_phase"] = 0
        entry["bg_fx_elapsed"] = 0

    def _place_mini_pet_bg_fx(self, entry: dict) -> None:
        win = entry.get("bg_fx_win")
        if not win or not win.winfo_exists():
            return
        pad = entry.get("bg_fx_pad", 10)
        entry_x = int(entry["x"])
        entry_y = int(entry["y"]) + int(entry.get("bounce_offset", 0))
        win.geometry(f"+{entry_x - pad}+{entry_y - pad}")

    def _create_mini_pet_bg_fx_window(self, entry: dict, pad: int) -> tuple[tk.Canvas, int]:
        size = entry["size"]
        canvas_size = size + pad * 2
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", False)
        win.configure(bg="magenta")
        win.wm_attributes("-transparentcolor", "magenta")
        canvas = tk.Canvas(
            win, width=canvas_size, height=canvas_size, bg="magenta", highlightthickness=0
        )
        canvas.pack()
        entry["bg_fx_win"] = win
        entry["bg_fx_canvas"] = canvas
        entry["bg_fx_pad"] = pad
        self._place_mini_pet_bg_fx(entry)
        return canvas, canvas_size

    def _animate_mini_pet_bg_fx(self, entry: dict) -> None:
        kind = entry.get("bg_fx_kind")
        canvas = entry.get("bg_fx_canvas")
        if not kind or not canvas:
            return
        pad = entry.get("bg_fx_pad", 10)
        size = canvas.winfo_width() or (entry["size"] + pad * 2)
        pet_size = entry["size"]
        scale = pet_size / max(1, self.display_size)
        delay = 120
        if kind == "dizzy":
            _draw_dizzy_sticker(canvas, size, entry.get("bg_fx_phase", 0))
            entry["bg_fx_phase"] = entry.get("bg_fx_phase", 0) + 1
        elif kind == "like":
            # 点赞光波已移到音乐模式，伴侣不再同步 like glow
            self._stop_mini_pet_bg_fx(entry)
            return
        elif kind == "wink":
            if self.action_name != "wink":
                self._stop_mini_pet_bg_fx(entry)
                self._sync_all_mini_pet_bg_fx()
                return
            canvas.delete("all")
            _draw_like_glow(canvas, size, entry.get("bg_fx_phase", 0))
            _draw_heart_wave(canvas, size, entry.get("bg_fx_phase", 0), clear=False)
            entry["bg_fx_phase"] = entry.get("bg_fx_phase", 0) + 1
            delay = 100
        elif kind.startswith("interact:"):
            action = kind.split(":", 1)[1]
            _draw_interact_fx(canvas, action, size, entry.get("bg_fx_phase", 0))
            entry["bg_fx_phase"] = entry.get("bg_fx_phase", 0) + 1
            delay = INTERACT_FX_MS
        elif kind.startswith("food:"):
            food_id = kind.split(":", 1)[1]
            elapsed = entry.get("bg_fx_elapsed", 0)
            total_ms = FOOD_APPEAR_MS + FOOD_HOLD_MS + FOOD_VANISH_MS
            if elapsed >= total_ms or not (self.food_fx_win and self.food_fx_win.winfo_exists()):
                self._stop_mini_pet_bg_fx(entry)
                return
            canvas.delete("all")
            px = max(3, int(max(4, self.display_size // FOOD_FX_PIXEL_DIV) * scale))
            if elapsed < FOOD_APPEAR_MS:
                progress = elapsed / FOOD_APPEAR_MS
            elif elapsed < FOOD_APPEAR_MS + FOOD_HOLD_MS:
                progress = 1.0
            else:
                vanish = elapsed - FOOD_APPEAR_MS - FOOD_HOLD_MS
                progress = max(0.0, 1.0 - vanish / FOOD_VANISH_MS)
            food_scale = max(2, int(px * (0.6 + 0.4 * progress)))
            offset_y = int((1.0 - progress) * food_scale * 2)
            base_x = size - food_scale * 5
            base_y = size // 2 + food_scale - offset_y
            _draw_pixel_food(canvas, food_id, base_x, base_y, px=food_scale)
            entry["bg_fx_elapsed"] = elapsed + 50
            delay = 50
        else:
            return
        self._place_mini_pet_bg_fx(entry)
        entry["bg_fx_job"] = self.root.after(delay, lambda e=entry: self._animate_mini_pet_bg_fx(e))

    def _start_mini_pet_bg_fx(self, entry: dict, kind: str) -> None:
        self._stop_mini_pet_bg_fx(entry)
        entry["bg_fx_kind"] = kind
        entry["bg_fx_phase"] = 0
        entry["bg_fx_elapsed"] = 0
        pet_size = entry["size"]
        scale = pet_size / max(1, self.display_size)
        if kind == "happy":
            pad = self._mini_pet_bg_pad(entry, 24)
            canvas, canvas_size = self._create_mini_pet_bg_fx_window(entry, pad)
            px = max(2, int(3 * scale))
            colors = ("#ff88cc", "#ffcc44", "#88dd88", "#ff6688", "#cc88ff", "#88ccff")
            for _ in range(8):
                fx = random.randint(4, canvas_size - 16)
                fy = random.randint(4, canvas_size - 20)
                self._draw_pixel_flower(canvas, fx, fy, random.choice(colors), px=px)
        elif kind == "shy":
            pad = self._mini_pet_bg_pad(entry, 20)
            canvas, canvas_size = self._create_mini_pet_bg_fx_window(entry, pad)
            px = max(2, int(max(2, self.display_size // 36) * scale))
            heart_colors = ("#ff6688", "#ff88aa", "#ff4466", "#ff99bb")
            for _ in range(6):
                hx = random.randint(4, canvas_size - 16)
                hy = random.randint(4, canvas_size - 16)
                _draw_pixel_heart(canvas, hx, hy, px=px, color=random.choice(heart_colors))
        elif kind == "wink":
            pad = self._mini_pet_bg_pad(entry, 20)
            self._create_mini_pet_bg_fx_window(entry, pad)
            self._animate_mini_pet_bg_fx(entry)
        elif kind == "dizzy":
            pad = self._mini_pet_bg_pad(entry, 16)
            self._create_mini_pet_bg_fx_window(entry, pad)
            self._animate_mini_pet_bg_fx(entry)
        elif kind.startswith("interact:"):
            pad = self._mini_pet_bg_pad(entry, INTERACT_FX_PAD)
            self._create_mini_pet_bg_fx_window(entry, pad)
            self._animate_mini_pet_bg_fx(entry)
        elif kind.startswith("food:"):
            pad = self._mini_pet_bg_pad(entry, FOOD_FX_PAD)
            self._create_mini_pet_bg_fx_window(entry, pad)
            self._animate_mini_pet_bg_fx(entry)

    def _sync_all_mini_pet_bg_fx(self, *, place_only: bool = False) -> None:
        if not self.companion_bar_enabled:
            for entry in self.mini_pets:
                self._stop_mini_pet_bg_fx(entry)
            return
        kind = self._mini_pet_desired_bg_fx_kind()
        for entry in self.mini_pets:
            cur = entry.get("bg_fx_kind")
            if place_only:
                if cur is not None:
                    self._place_mini_pet_bg_fx(entry)
                continue
            if kind is None:
                if cur is not None:
                    self._stop_mini_pet_bg_fx(entry)
            elif cur != kind:
                self._start_mini_pet_bg_fx(entry, kind)
            else:
                self._place_mini_pet_bg_fx(entry)

    def _notify_bg_fx_change(self) -> None:
        self._sync_all_mini_pet_bg_fx()

    def _stop_mini_pet_music_wave(self, entry: dict) -> None:
        job = entry.get("wave_job")
        if job:
            try:
                self.root.after_cancel(job)
            except Exception:
                pass
            entry["wave_job"] = None
        wave_win = entry.get("wave_win")
        if wave_win and wave_win.winfo_exists():
            wave_win.destroy()
        entry["wave_win"] = None
        entry["wave_canvas"] = None

    def _start_mini_pet_music_wave(self, entry: dict) -> None:
        if entry.get("wave_canvas"):
            return
        pad = 18
        size = entry["size"] + pad * 2
        wave_win = tk.Toplevel(self.root)
        wave_win.overrideredirect(True)
        wave_win.attributes("-topmost", False)
        wave_win.configure(bg="magenta")
        wave_win.wm_attributes("-transparentcolor", "magenta")
        wave_canvas = tk.Canvas(wave_win, width=size, height=size, bg="magenta", highlightthickness=0)
        wave_canvas.pack()
        entry["wave_win"] = wave_win
        entry["wave_canvas"] = wave_canvas
        entry["wave_phase"] = 0
        entry["wave_pad"] = pad
        self._place_mini_pet_music_wave(entry)
        self._animate_mini_pet_music_wave(entry)

    def _place_mini_pet_music_wave(self, entry: dict) -> None:
        wave_win = entry.get("wave_win")
        if not wave_win or not wave_win.winfo_exists():
            return
        pad = entry.get("wave_pad", 18)
        bounce = int(entry.get("bounce_offset", 0))
        wx = int(entry["x"] - pad)
        wy = int(entry["y"] + bounce - pad)
        wave_win.geometry(f"+{wx}+{wy}")

    def _place_all_mini_pet_waves(self) -> None:
        for entry in self.mini_pets:
            self._place_mini_pet_music_wave(entry)

    def _animate_mini_pet_music_wave(self, entry: dict) -> None:
        canvas = entry.get("wave_canvas")
        if not canvas or not self.music_sprite_mode or not self.companion_bar_enabled:
            self._stop_mini_pet_music_wave(entry)
            return
        pad = entry.get("wave_pad", 18)
        size = entry["size"] + pad * 2
        beat = 1.0
        try:
            import pygame

            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pos = pygame.mixer.music.get_pos()
                if pos >= 0:
                    beat = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(pos * 0.014))
        except Exception:
            pass
        _draw_music_wave(canvas, size, size, entry.get("wave_phase", 0), beat=beat)
        entry["wave_phase"] = entry.get("wave_phase", 0) + 1
        self._place_mini_pet_music_wave(entry)
        entry["wave_job"] = self.root.after(
            MUSIC_WAVE_MS, lambda e=entry: self._animate_mini_pet_music_wave(e)
        )

    def _sync_mini_pet_music_waves(self) -> None:
        for entry in self.mini_pets:
            if self.music_sprite_mode and self.companion_bar_enabled:
                self._start_mini_pet_music_wave(entry)
            else:
                self._stop_mini_pet_music_wave(entry)

    def _destroy_mini_pet(self, entry: dict) -> None:
        job = entry.get("follow_job")
        if job:
            try:
                self.root.after_cancel(job)
            except Exception:
                pass
        self._stop_mini_pet_music_wave(entry)
        self._stop_mini_pet_bg_fx(entry)
        win = entry.get("win")
        if win and win.winfo_exists():
            win.destroy()
        if entry in self.mini_pets:
            self.mini_pets.remove(entry)
        for i, pet in enumerate(self.mini_pets):
            pet["index"] = i
            pet["side"] = "left" if i % 2 == 0 else "right"

    def _destroy_all_mini_pets(self) -> None:
        for entry in list(self.mini_pets):
            self._destroy_mini_pet(entry)

    def _show_reserved(self, name: str) -> None:
        self._hide_main_menu()
        self._show_toast(f"{name}（预留）\n{RESERVED_TOAST}", "#888888", duration_ms=2500)

    def _play_adult_reserved(self) -> None:
        if self.dragging or self.state == "work":
            return
        self._interrupt_current_interaction()
        self._hide_main_menu()
        self.state = "action"
        self.action_name = "adult_msg"
        self._show_speech_dialog(ADULT_CONTENT_TEXT, auto_hide_ms=6500)
        self._schedule_action_end(duration_ms=_typing_duration_ms(ADULT_CONTENT_TEXT) + 1500, callback=self._after_adult_msg)

    def _after_adult_msg(self) -> None:
        if self.dragging or self.state != "action" or self.action_name != "adult_msg":
            return
        self._hide_speech_dialog()
        self._cancel_action_end()
        self._finish_expression()

    def _play_expression_pop(self) -> None:
        if self.click_bouncing:
            return
        self.click_bouncing = True
        self.click_bounce_offset = -EXPRESSION_BOUNCE_PX
        self._place_window()
        self._place_sleep_zzz()
        self._place_ai_chat()
        self.root.after(EXPRESSION_BOUNCE_MS, self._expression_pop_down)

    def _expression_pop_down(self) -> None:
        self.click_bounce_offset = 0
        self.click_bouncing = False
        self._place_window()
        self._place_sleep_zzz()
        self._place_ai_chat()

    def _play_kick(self) -> None:
        if self.dragging or self.state == "work":
            return
        self._interrupt_current_interaction()
        self._hide_main_menu()
        self.state = "action"
        self.action_name = "kick"
        self._interact_flair("kick", banter=True, show_fx=False)
        self._play_expression_pop()
        self._set_image(self.sprites.kick)
        self.kick_base_y = self.y
        self.y = self.kick_base_y - KICK_BOUNCE_PX
        self._place_window()
        self.root.after(KICK_BOUNCE_MS, self._kick_bounce_down)
        self._schedule_action_end(action="kick", callback=self._after_simple_expression)

    def _kick_bounce_down(self) -> None:
        if self.action_name != "kick":
            return
        self.y = self.kick_base_y
        self._place_window()

    def _play_expression_shy(self) -> None:
        if self.dragging or self.state == "work" or self.music_sprite_mode:
            return
        self._interrupt_current_interaction()
        self.state = "action"
        self.action_name = "shy"
        self.shy_frame_idx = 0
        self.shy_last_click_ms = 0
        self._interact_flair("shy", banter=False)
        self._play_expression_pop()
        self._set_image(self.sprites.shy[0])
        self._show_shy_fx()
        self._schedule_action_end(action="shy", callback=self._after_simple_expression)

    def _handle_shy_click(self) -> None:
        if self.state != "action" or self.action_name != "shy":
            return
        now_ms = int(time.time() * 1000)
        if now_ms - self.shy_last_click_ms <= SHY_DOUBLE_CLICK_MS:
            self.shy_frame_idx = 1
            self._set_image(self.sprites.shy[1])
        else:
            self.shy_frame_idx = 0
            self._set_image(self.sprites.shy[0])
        self.shy_last_click_ms = now_ms

    def _play_expression_like(self) -> None:
        self._play_like_or_wink("like", self.sprites.like)

    def _play_expression_wink(self, *, restore_free: bool = False) -> None:
        # wink 与点赞共用同一套表情结束算法，避免独立 wink 特效链路卡死
        del restore_free
        self._play_like_or_wink("wink", self.sprites.wink)

    def _play_like_or_wink(self, name: str, sprite: ImageTk.PhotoImage) -> None:
        if self.dragging or self.state == "work" or self.music_sprite_mode:
            return
        self._interrupt_current_interaction()
        self.state = "action"
        self.action_name = name
        self._wink_restore_free = False
        self._interact_flair(name, banter=True)
        self._play_expression_pop()
        self._set_image(sprite)
        self._show_like_fx()
        self._schedule_action_end(action=name, callback=self._after_simple_expression)

    def _after_wink_expression(self) -> None:
        # 兼容旧调度/看门狗：统一走简单表情结束
        self._after_simple_expression()

    def _play_expression_sprite(self, name: str, sprite: ImageTk.PhotoImage, *, banter: bool = True) -> None:
        if self.dragging or self.state == "work" or self.music_sprite_mode:
            return
        self._interrupt_current_interaction()
        self.state = "action"
        self.action_name = name
        self._interact_flair(name, banter=banter)
        self._play_expression_pop()
        self._set_image(sprite)
        self._schedule_action_end(action=name, callback=self._after_simple_expression)

    def _play_yesno_judge(self) -> None:
        if self.dragging or self.state == "work" or self.music_sprite_mode:
            return
        self._interrupt_current_interaction()
        self._hide_main_menu()
        self._cancel_yesno_overlay()
        self.yesno_is_yes = random.choice([True, False])
        self.state = "action"
        self.action_name = "yesno"
        self._set_image(self.sprites.stand)
        self._show_speech_dialog(YESNO_ANSWER_TEXT, auto_hide_ms=None)
        self.yesno_reveal_job = self.root.after(YESNO_WAIT_MS, self._yesno_reveal)

    def _yesno_reveal(self) -> None:
        self.yesno_reveal_job = None
        if self.action_name != "yesno":
            self._cancel_yesno_overlay()
            return
        self._hide_speech_dialog()
        is_yes = self.yesno_is_yes
        self._interact_flair("yesno", banter=False, show_fx=False)
        self._play_expression_pop()
        self._set_image(self.sprites.yes if is_yes else self.sprites.no)
        verdict = random.choice(["是！", "嗯，是哦~"]) if is_yes else random.choice(["否。", "不是呢~"])
        self._show_speech_dialog(f"判断结果：{verdict}", auto_hide_ms=2800)
        self._schedule_action_end(action="yesno", callback=self._after_simple_expression)

    def _after_simple_expression(self) -> None:
        if self.state != "action":
            return
        if self.dragging:
            self._defer_until_not_dragging(self._after_simple_expression)
            return
        self._clear_all_action_fx()
        self._cancel_action_end()
        self._cancel_action_defer()
        self._add_interact_mood()
        self._finish_expression()

    def _play_expression_angry(self) -> None:
        if self.dragging or self.state == "work":
            return
        self._interrupt_current_interaction(reset_y=True)
        self.state = "action"
        self.action_name = "angry"
        self.angry_base_y = self.y
        self.angry_lift_offset = 0
        self.angry_walk_phase = False
        self._interact_flair("angry", banter=True)
        self._play_expression_pop()
        self._angry_anim_step(0)

    def _angry_anim_step(self, step: int) -> None:
        if self.dragging or self.state != "action" or self.action_name != "angry":
            return
        sequence = [
            self.sprites.stand_angry,
            self.sprites.front[0],
            self.sprites.stand_angry,
            self.sprites.back[0],
            self.sprites.back[1],
            self.sprites.back[0],
            self.sprites.back[1],
            self.sprites.back[0],
            self.sprites.back[1],
            self.sprites.stand_angry,
        ]
        if step >= len(sequence):
            self.angry_walk_phase = False
            self._place_window()
            self._schedule_action_end(action="angry", callback=self._after_simple_expression)
            return
        self.angry_walk_phase = 3 <= step <= 8
        if 3 <= step <= 8:
            self.angry_lift_offset = min(ANGRY_WALK_MAX_LIFT, self.angry_lift_offset + ANGRY_WALK_UP_PER_STEP)
            self.y = self.angry_base_y - self.angry_lift_offset
        elif step < 3:
            self.y = self.angry_base_y
        self._set_image(sequence[step])
        self._place_window()
        self.angry_anim_job = self.root.after(ANGRY_FRAME_MS, lambda: self._angry_anim_step(step + 1))

    def _cancel_expose_qte(self) -> None:
        # 不在这里取消倒计时：开局会先 cancel 再 start countdown，否则会误伤刚开的 3-2-1
        self.expose_qte_active = False
        self.expose_session_active = False
        self.expose_enter_armed = False
        self.expose_enter_was_down = False
        if self.expose_anim_job:
            self.root.after_cancel(self.expose_anim_job)
            self.expose_anim_job = None
        if self.expose_glitch_job:
            self.root.after_cancel(self.expose_glitch_job)
            self.expose_glitch_job = None
        if self.expose_qte_win and self.expose_qte_win.winfo_exists():
            self.expose_qte_win.destroy()
        if self.expose_glitch_win and self.expose_glitch_win.winfo_exists():
            self.expose_glitch_win.destroy()
        self.expose_qte_win = None
        self.expose_qte_canvas = None
        self.expose_glitch_win = None
        self.expose_glitch_canvas = None
        # 不用 unbind_all，避免拆掉其它 Return 绑定；靠 expose_enter_armed 开关

    def _expose_medium_params(self) -> tuple[float, float]:
        mid = DIFFICULTY_PRESETS["中"]
        return float(mid["expose_blue_span"]), float(mid["expose_pointer_speed"])

    def _random_expose_cluster_pos(self, qte_size: int) -> tuple[int, int, int, int]:
        """返回故障提示与 QTE 并排时的 (glitch_x, glitch_y, qte_x, qte_y)。"""
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        gw, gh = EXPOSE_GLITCH_ALERT_W, EXPOSE_GLITCH_ALERT_H
        gap = EXPOSE_QTE_GAP
        combo_w = gw + gap + qte_size
        combo_h = max(gh, qte_size)
        margin = 24
        # 优先贴近桌宠，避免随机到看不见或 randint 越界
        prefer_x = max(margin, min(sw - combo_w - margin, self.x + self.display_size // 2 - combo_w // 2))
        prefer_y = max(margin, min(sh - combo_h - margin, self.y - combo_h - 12))
        max_x = sw - combo_w - margin
        max_y = sh - combo_h - margin
        if max_x < margin or max_y < margin:
            # 屏幕放不下并排：叠在宠物附近（QTE 在上，提示在下）
            qte_x = max(margin, min(sw - qte_size - margin, self.x))
            qte_y = max(margin, min(sh - qte_size - gh - gap - margin, self.y - qte_size - 8))
            glitch_x = max(margin, min(sw - gw - margin, qte_x))
            glitch_y = min(sh - gh - margin, qte_y + qte_size + gap)
            return glitch_x, glitch_y, qte_x, qte_y
        # 在偏好点附近小范围抖动
        lo_x = max(margin, prefer_x - 80)
        hi_x = min(max_x, prefer_x + 80)
        lo_y = max(margin, prefer_y - 60)
        hi_y = min(max_y, prefer_y + 60)
        if lo_x > hi_x:
            lo_x, hi_x = margin, max_x
        if lo_y > hi_y:
            lo_y, hi_y = margin, max_y
        base_x = random.randint(lo_x, hi_x)
        base_y = random.randint(lo_y, hi_y)
        qte_left = random.choice([True, False])
        if qte_left:
            qte_x = base_x
            glitch_x = base_x + qte_size + gap
        else:
            glitch_x = base_x
            qte_x = base_x + gw + gap
        glitch_y = base_y + (combo_h - gh) // 2
        qte_y = base_y + (combo_h - qte_size) // 2
        return glitch_x, glitch_y, qte_x, qte_y

    def _animate_glitch_fault(self) -> None:
        if not self.expose_session_active or not self.expose_glitch_canvas:
            return
        _draw_glitch_fault(
            self.expose_glitch_canvas,
            EXPOSE_GLITCH_ALERT_W,
            EXPOSE_GLITCH_ALERT_H,
            self.expose_glitch_message,
            self.expose_glitch_phase,
        )
        self.expose_glitch_phase += 1
        self.expose_glitch_job = self.root.after(120, self._animate_glitch_fault)

    def _spawn_expose_glitch_round(self) -> None:
        if not self.expose_session_active:
            return
        if self.expose_glitch_win and self.expose_glitch_win.winfo_exists():
            self.expose_glitch_win.destroy()
        if self.expose_qte_win and self.expose_qte_win.winfo_exists():
            self.expose_qte_win.destroy()
        self.expose_glitch_message = random.choice(FAULT_ALERT_MESSAGES)
        qte_size = self.display_size + EXPOSE_RING_PAD
        gx, gy, qx, qy = self._random_expose_cluster_pos(qte_size)
        self.expose_glitch_win = tk.Toplevel(self.root)
        self.expose_glitch_win.overrideredirect(True)
        self.expose_glitch_win.attributes("-topmost", True)
        self.expose_glitch_win.configure(bg="#120818")
        self.expose_glitch_canvas = tk.Canvas(
            self.expose_glitch_win,
            width=EXPOSE_GLITCH_ALERT_W,
            height=EXPOSE_GLITCH_ALERT_H,
            bg="#120818",
            highlightthickness=0,
        )
        self.expose_glitch_canvas.pack()
        self.expose_glitch_win.geometry(f"{EXPOSE_GLITCH_ALERT_W}x{EXPOSE_GLITCH_ALERT_H}+{gx}+{gy}")
        self.expose_glitch_phase = 0
        self._animate_glitch_fault()

        span, speed = self._expose_medium_params()
        self.expose_pointer_base_speed = speed
        round_idx = min(self.expose_hit_streak, EXPOSE_GLITCH_HITS_REQUIRED - 1)
        self._expose_blue_span = _expose_blue_span_for_round(span, round_idx)
        self._expose_pointer_speed = min(
            EXPOSE_POINTER_MAX_SPEED,
            speed * (1 + self.expose_hit_streak * EXPOSE_SPEED_STREAK_MULT),
        )
        self.expose_blue_start = random.uniform(0, 360)
        self.expose_qte_angle = 0.0
        self.expose_qte_win = tk.Toplevel(self.root)
        self.expose_qte_win.overrideredirect(True)
        self.expose_qte_win.attributes("-topmost", True)
        self.expose_qte_win.configure(bg="magenta")
        self.expose_qte_win.wm_attributes("-transparentcolor", "magenta")
        self.expose_qte_canvas = tk.Canvas(
            self.expose_qte_win, width=qte_size, height=qte_size, bg="magenta", highlightthickness=0
        )
        self.expose_qte_canvas.pack()
        try:
            self.expose_qte_win.update_idletasks()
        except Exception:
            pass
        self.expose_qte_win.geometry(f"{qte_size}x{qte_size}+{qx}+{qy}")
        self.expose_qte_active = True
        self.expose_qte_done = False
        self.expose_enter_armed = True
        # 若仍按着 Enter，等松开再判，避免连发误触
        self.expose_enter_was_down = self._expose_enter_key_down()
        for seq in ("<Return>", "<KP_Enter>", "<KeyPress-Return>", "<KeyPress-KP_Enter>"):
            self.expose_qte_win.bind(seq, self._expose_qte_enter)
            if self.expose_glitch_win and self.expose_glitch_win.winfo_exists():
                self.expose_glitch_win.bind(seq, self._expose_qte_enter)
        try:
            self.expose_glitch_win.lift()
            self.expose_qte_win.lift()
            self.expose_qte_win.focus_force()
        except Exception:
            pass
        self.root.after(30, self._focus_expose_qte)
        self.root.after(120, self._focus_expose_qte)
        self._expose_qte_tick()
        self._show_toast("暴露开始 · Enter 判定", "#ff88aa", duration_ms=1200)

    def _focus_expose_qte(self) -> None:
        if not self.expose_session_active:
            return
        try:
            self.root.focus_force()
            if self.expose_qte_win and self.expose_qte_win.winfo_exists():
                self.expose_qte_win.lift()
                self.expose_qte_win.focus_force()
            if self.expose_glitch_win and self.expose_glitch_win.winfo_exists():
                self.expose_glitch_win.lift()
        except Exception:
            pass

    def _expose_enter_key_down(self) -> bool:
        if sys.platform != "win32":
            return False
        try:
            # VK_RETURN = 0x0D
            return bool(ctypes.windll.user32.GetAsyncKeyState(0x0D) & 0x8000)
        except Exception:
            return False

    def _expose_qte_tick(self) -> None:
        if not self.expose_qte_active or not self.expose_qte_canvas:
            return
        # 无焦点时也能用 Enter：轮询物理按键边沿
        if self.expose_enter_armed and not self.expose_qte_done:
            down = self._expose_enter_key_down()
            if down and not self.expose_enter_was_down:
                self._expose_qte_enter()
            self.expose_enter_was_down = down
        if not self.expose_qte_active or not self.expose_qte_canvas:
            return
        cur = getattr(self, "_expose_pointer_speed", EXPOSE_POINTER_SPEED)
        self._expose_pointer_speed = min(EXPOSE_POINTER_MAX_SPEED, cur + EXPOSE_SPEED_TICK_BOOST)
        self.expose_qte_angle = (self.expose_qte_angle + self._expose_pointer_speed) % 360
        size = self.expose_qte_canvas.winfo_width() or 80
        span = getattr(self, "_expose_blue_span", EXPOSE_BLUE_SPAN)
        _draw_expose_qte_ring(self.expose_qte_canvas, size, self.expose_blue_start, self.expose_qte_angle, blue_span=span)
        self.expose_anim_job = self.root.after(EXPOSE_QTE_TICK_MS, self._expose_qte_tick)

    def _expose_qte_enter(self, _event=None) -> None:
        if not self.expose_enter_armed:
            return
        if not self.expose_qte_active or self.expose_qte_done or not self.expose_session_active:
            return
        hit = _angle_in_arc(
            self.expose_qte_angle,
            self.expose_blue_start,
            getattr(self, "_expose_blue_span", EXPOSE_BLUE_SPAN),
        )
        self._resolve_expose_qte_hit(hit)

    def _play_expose_qte(self) -> None:
        if self.dragging or self.state == "work":
            return
        self._interrupt_current_interaction()
        self._cancel_game_countdown()
        self._cancel_idle_chain()
        self._hide_main_menu()
        if self.mode == "quiet" and self.state == "rest":
            self._stop_rest_bobble()
        self.state = "action"
        self.action_name = "expose"
        self.expose_hit_streak = 0
        self._cancel_expose_qte()
        self.expose_session_active = False
        self.expose_enter_armed = False
        _, base = self._expose_medium_params()
        self.expose_pointer_base_speed = base

        def begin() -> None:
            # 倒计时期间看门狗可能改过状态：强制拉回暴露
            self.state = "action"
            self.action_name = "expose"
            self.expose_session_active = True
            self.expose_enter_armed = True
            self.expose_enter_was_down = self._expose_enter_key_down()
            self._cancel_idle_chain()
            # 整场绑定 root（覆盖同键位，不叠多层）；靠 expose_enter_armed 开关
            for seq in ("<Return>", "<KP_Enter>", "<KeyPress-Return>", "<KeyPress-KP_Enter>"):
                self.root.bind(seq, self._expose_qte_enter)
            try:
                self._spawn_expose_glitch_round()
            except Exception:
                try:
                    self._spawn_expose_glitch_round()
                except Exception as exc:
                    self._show_toast(f"暴露界面打开失败：{exc}", "#ff6666")
                    self._finish_expose_session(cleared=False)
                    return
            if not self.expose_qte_win or not self.expose_glitch_win:
                self._show_toast("暴露界面未生成，请重试", "#ff6666")
                self._finish_expose_session(cleared=False)
                return
            self._focus_expose_qte()
            self.root.after(80, self._focus_expose_qte)
            self.root.after(250, self._focus_expose_qte)

        def after_guide() -> None:
            self.state = "action"
            self.action_name = "expose"
            self._start_game_countdown(begin, title="暴露")

        self._ensure_first_play_guide("expose", after_guide)

    def _resolve_expose_qte_hit(self, success: bool) -> None:
        if self.action_name != "expose" or not self.expose_session_active:
            return
        if self.expose_qte_done:
            return
        self.expose_qte_done = True
        self.expose_qte_active = False
        self.expose_enter_armed = False
        if self.expose_anim_job:
            self.root.after_cancel(self.expose_anim_job)
            self.expose_anim_job = None
        if success:
            self.expose_hit_streak += 1
            self._show_toast(f"暴露成功 {self.expose_hit_streak}/{EXPOSE_GLITCH_HITS_REQUIRED}", "#44ff88", duration_ms=900)
            if self.expose_hit_streak >= EXPOSE_GLITCH_HITS_REQUIRED:
                self._finish_expose_session(cleared=True)
                return
            self.root.after(EXPOSE_GLITCH_REFRESH_MS, self._spawn_expose_glitch_round)
        else:
            self._apply_expose_fail_penalty()
            self._show_speech_dialog("暴露失败…", auto_hide_ms=2200, color="#ff6666")
            self._finish_expose_session(cleared=False)
            return

    def _finish_expose_session(self, *, cleared: bool) -> None:
        self.expose_session_active = False
        self._cancel_game_countdown()
        self._cancel_expose_qte()
        if cleared:
            self.mood = min(100, self.mood + 5)
            self._refresh_panel()
            self._show_game_clear(
                title="暴露通关！",
                subtitle=f"连中 {EXPOSE_GLITCH_HITS_REQUIRED} 次 · 完美判定",
                accent="#44ff88",
                on_done=self._after_expose,
            )
        else:
            self.root.after(900, self._after_expose)

    def _after_expose(self) -> None:
        if self.dragging or self.state != "action" or self.action_name != "expose":
            return
        self._cancel_action_end()
        self._finish_expression()

    def _open_expression_menu(self) -> None:
        self._show_sub_menu(
            [
                ("开心", self._play_happy),
                ("生气", self._play_expression_angry),
                ("疑问", lambda: self._play_expression("question")),
                ("伤心", self._play_expression_sad),
                ("有主意", self._play_expression_idea),
                ("脸红", self._play_expression_shy),
                ("wink", self._play_expression_wink),
                ("点赞", self._play_expression_like),
            ],
            offset_x=200,
        )

    def _play_expression_sad(self) -> None:
        if self.dragging or self.state == "work":
            return
        self._interrupt_current_interaction()
        self.state = "action"
        self.action_name = "sad"
        self.sad_phase = "squat"
        self._interact_flair("sad", banter=True)
        self._set_image(self.sprites.actions["squat"][0])
        self._show_rain_fx()
        tok = self.interaction_token
        self.root.after(SAD_SQUAT_MS, lambda t=tok: self._sad_phase_sad1(t))
        self._schedule_action_end(
            duration_ms=SAD_SQUAT_MS + SAD_SAD1_MS + SAD_SAD2_MS,
            action="sad",
            callback=self._after_expression_sad,
        )

    def _sad_phase_sad1(self, tok: int) -> None:
        if tok != self.interaction_token or self.action_name != "sad":
            return
        self.sad_phase = "sad1"
        self._set_image(self.sprites.sad1)
        self.root.after(SAD_SAD1_MS, lambda t=tok: self._sad_phase_sad2(t))

    def _sad_phase_sad2(self, tok: int) -> None:
        if tok != self.interaction_token or self.action_name != "sad":
            return
        self.sad_phase = "sad2"
        self._set_image(self.sprites.sad2)

    def _after_expression_sad(self) -> None:
        if self.dragging or self.state != "action" or self.action_name != "sad":
            return
        self.sad_phase = ""
        self._hide_rain_fx()
        self._cancel_action_end()
        self.mood = max(0, self.mood - 2)
        self._refresh_panel()
        self._finish_expression()

    def _play_expression_idea(self) -> None:
        if self.dragging or self.state == "work":
            return
        self._interrupt_current_interaction()
        self.state = "action"
        self.action_name = "idea"
        self._interact_flair("idea", banter=False)
        self._play_expression_pop()
        self._set_image(self.sprites.stand)
        self._show_bulb_fx()
        self.root.after(IDEA_STAND_MS, self._idea_to_eat2)

    def _idea_to_eat2(self) -> None:
        if self.dragging or self.state != "action" or self.action_name != "idea":
            return
        self._set_image(self.sprites.eat2_only)
        self._schedule_action_end(action="idea", callback=self._after_expression_idea)

    def _after_expression_idea(self) -> None:
        if self.dragging or self.state != "action" or self.action_name != "idea":
            return
        self._hide_bulb_fx()
        self._cancel_action_end()
        self.mood = min(100, self.mood + 4)
        self._refresh_panel()
        self._finish_expression()

    def _play_expression(self, name: str) -> None:
        if self.dragging or self.music_sprite_mode:
            return
        sprites = {"angry": self.sprites.stand_angry, "question": self.sprites.stand_question}
        if name not in sprites:
            return
        self._interrupt_current_interaction()
        self.state = "action"
        self.action_name = name
        self._interact_flair(name, banter=True)
        self._play_expression_pop()
        self._set_image(sprites[name])
        self._schedule_action_end(action=name, callback=self._after_expression)

    def _finish_expression(self) -> None:
        self._clear_all_action_fx()
        self.action_name = ""
        if self.mode == "quiet":
            self.state = "rest"
            self._set_image(self.sprites.sleep[1])
            self._show_sleep_zzz()
            self._schedule_rest_bobble()
        else:
            self.state = "stand"
            self._set_image(self._current_stand_sprite())
        if not self._check_mood_happy():
            self._resume_idle()

    def _after_expression(self) -> None:
        if self.dragging or self.state != "action":
            return
        self._add_interact_mood()
        self._finish_expression()

    def _follow_tick(self) -> None:
        self.follow_tick_job = None
        if not self._alive() or self.dragging or self.mode != "follow" or self.state in ("action", "sleep"):
            return
        if self.follow_dizzy:
            self._schedule_follow_tick(100)
            return
        self._follow_move()

    def _follow_dir_rotation(self, old_dir: str, new_dir: str) -> int:
        if not old_dir or old_dir == new_dir:
            return 0
        order = FOLLOW_DIR_ORDER
        if old_dir not in order or new_dir not in order:
            return 0
        diff = (order.index(new_dir) - order.index(old_dir)) % 4
        if diff == 1:
            return 1
        if diff == 3:
            return -1
        return 0

    def _track_follow_spin(self, direction: str) -> None:
        old_dir = self.follow_last_dir
        step = self._follow_dir_rotation(old_dir, direction)
        if step == 0:
            # 同向连续移动不重置；只有对向急转才打断
            if old_dir and old_dir != direction:
                self.follow_spin_dir = 0
                self.follow_spin_steps = 0
            return
        if self.follow_spin_dir == 0:
            self.follow_spin_dir = step
            self.follow_spin_steps = 1
        elif step == self.follow_spin_dir:
            self.follow_spin_steps += 1
        else:
            self.follow_spin_dir = step
            self.follow_spin_steps = 1
        if self.follow_spin_steps >= FOLLOW_DIZZY_SPIN_STEPS:
            self.follow_spin_dir = 0
            self.follow_spin_steps = 0
            self._start_follow_dizzy()

    def _hide_follow_dizzy_fx(self) -> None:
        if self.follow_dizzy_fx_job:
            self.root.after_cancel(self.follow_dizzy_fx_job)
            self.follow_dizzy_fx_job = None
        if self.follow_dizzy_fx_win and self.follow_dizzy_fx_win.winfo_exists():
            self.follow_dizzy_fx_win.destroy()
        self.follow_dizzy_fx_win = None
        self.follow_dizzy_fx_canvas = None
        self._notify_bg_fx_change()

    def _place_follow_dizzy_fx(self) -> None:
        if not self.follow_dizzy_fx_win or not self.follow_dizzy_fx_win.winfo_exists():
            return
        pad = 16
        display_y = self.y + self.click_bounce_offset
        self.follow_dizzy_fx_win.geometry(f"+{self.x - pad}+{display_y - pad}")

    def _show_follow_dizzy_fx(self) -> None:
        self._hide_follow_dizzy_fx()
        pad = 16
        size = self.display_size + pad * 2
        self.follow_dizzy_fx_win = tk.Toplevel(self.root)
        self.follow_dizzy_fx_win.overrideredirect(True)
        self.follow_dizzy_fx_win.attributes("-topmost", False)
        self.follow_dizzy_fx_win.configure(bg="magenta")
        self.follow_dizzy_fx_win.wm_attributes("-transparentcolor", "magenta")
        self.follow_dizzy_fx_canvas = tk.Canvas(
            self.follow_dizzy_fx_win, width=size, height=size, bg="magenta", highlightthickness=0
        )
        self.follow_dizzy_fx_canvas.pack()
        self.follow_dizzy_fx_phase = 0
        self._animate_follow_dizzy_fx()
        self._notify_bg_fx_change()

    def _dizzy_fx_active(self) -> bool:
        return self.follow_dizzy or self.drag_dizzy or self.game_dizzy

    def _start_game_dizzy_stun(self) -> None:
        if self.mode != "game":
            return
        if self.game_dizzy_job:
            try:
                self.root.after_cancel(self.game_dizzy_job)
            except Exception:
                pass
            self.game_dizzy_job = None
        self.game_dizzy = True
        self.game_stunned_until_ms = int(time.time() * 1000) + GAME_DIZZY_STUN_MS
        if not self.follow_dizzy_fx_win or not self.follow_dizzy_fx_win.winfo_exists():
            self._show_follow_dizzy_fx()
        else:
            self._place_follow_dizzy_fx()
        self._show_speech_dialog(random.choice(GAME_DIZZY_LINES), auto_hide_ms=3200)
        self.game_dizzy_job = self.root.after(GAME_DIZZY_STUN_MS, self._end_game_dizzy_stun)

    def _end_game_dizzy_stun(self) -> None:
        if self.game_dizzy_job:
            try:
                self.root.after_cancel(self.game_dizzy_job)
            except Exception:
                pass
            self.game_dizzy_job = None
        self.game_dizzy = False
        self.game_stunned_until_ms = 0
        if not self.follow_dizzy and not self.drag_dizzy:
            self._hide_follow_dizzy_fx()

    def _animate_follow_dizzy_fx(self) -> None:
        if not self.follow_dizzy_fx_canvas or not self._dizzy_fx_active():
            self._hide_follow_dizzy_fx()
            return
        size = self.follow_dizzy_fx_canvas.winfo_width() or (self.display_size + 32)
        _draw_dizzy_sticker(self.follow_dizzy_fx_canvas, size, self.follow_dizzy_fx_phase)
        self.follow_dizzy_fx_phase += 1
        self._place_follow_dizzy_fx()
        self.follow_dizzy_fx_job = self.root.after(120, self._animate_follow_dizzy_fx)

    def _start_follow_dizzy(self) -> None:
        if self.follow_dizzy or self.mode != "follow":
            return
        self.follow_dizzy = True
        self.follow_animating = False
        self.follow_spin_dir = 0
        self.follow_spin_steps = 0
        self.follow_last_dir = ""
        self.state = "stand"
        self._set_image(self.sprites.stand)
        self._place_window()
        self._show_follow_dizzy_fx()
        self._show_speech_dialog(FOLLOW_DIZZY_TEXT, auto_hide_ms=FOLLOW_DIZZY_STAND_MS)
        if self.follow_dizzy_job:
            self.root.after_cancel(self.follow_dizzy_job)
        self.follow_dizzy_job = self.root.after(FOLLOW_DIZZY_STAND_MS, self._end_follow_dizzy)

    def _drag_move_dir(self, dx: int, dy: int) -> str:
        if abs(dx) < DRAG_DIZZY_MIN_DELTA and abs(dy) < DRAG_DIZZY_MIN_DELTA:
            return ""
        if abs(dx) >= abs(dy):
            return "left" if dx < 0 else "right"
        return "front" if dy < 0 else "back"

    def _maybe_drag_dizzy_dialog(self) -> None:
        now_ms = int(time.time() * 1000)
        if now_ms - self.drag_dizzy_dialog_ms < DRAG_DIZZY_DIALOG_COOLDOWN_MS:
            return
        if self.speech_dialog and self.speech_dialog.winfo_exists():
            return
        self._show_speech_dialog(random.choice(DRAG_DIZZY_LINES), auto_hide_ms=2400)
        self.drag_dizzy_dialog_ms = now_ms

    def _track_drag_spin(self, direction: str) -> None:
        old_dir = self.drag_last_dir
        step = self._follow_dir_rotation(old_dir, direction)
        self.drag_last_dir = direction
        if step == 0:
            # 同一方向持续拖动不打断累积；对向急转才重置
            if old_dir and old_dir != direction:
                self.drag_spin_dir = 0
                self.drag_spin_steps = 0
            return
        if self.drag_spin_dir == 0:
            self.drag_spin_dir = step
            self.drag_spin_steps = 1
        elif step == self.drag_spin_dir:
            self.drag_spin_steps += 1
        else:
            self.drag_spin_dir = step
            self.drag_spin_steps = 1
        if self.drag_dizzy:
            self.drag_dizzy_extra_spins += 1
            if self.drag_dizzy_extra_spins >= DRAG_DIZZY_EXTRA_DIALOG_SPINS:
                self.drag_dizzy_extra_spins = 0
                self._maybe_drag_dizzy_dialog()
            return
        if self.drag_spin_steps >= DRAG_DIZZY_SPIN_STEPS:
            self.drag_spin_dir = 0
            self.drag_spin_steps = 0
            self._start_drag_dizzy()

    def _start_drag_dizzy(self) -> None:
        if self.drag_dizzy or not self.dragging or self.state != "drag":
            return
        self.drag_dizzy = True
        self.drag_dizzy_extra_spins = 0
        if not self.follow_dizzy_fx_win or not self.follow_dizzy_fx_win.winfo_exists():
            self._show_follow_dizzy_fx()
        else:
            self._place_follow_dizzy_fx()
        self._maybe_drag_dizzy_dialog()
        self._notify_bg_fx_change()

    def _end_drag_dizzy(self) -> None:
        if not self.drag_dizzy:
            return
        self.drag_dizzy = False
        self.drag_last_dir = ""
        self.drag_spin_dir = 0
        self.drag_spin_steps = 0
        self.drag_dizzy_extra_spins = 0
        if not self.follow_dizzy:
            self._hide_follow_dizzy_fx()

    def _end_follow_dizzy(self) -> None:
        self.follow_dizzy_job = None
        self.follow_dizzy = False
        self.follow_last_dir = ""
        self._hide_follow_dizzy_fx()
        if self.mode != "follow":
            return
        self.state = "stand"
        self._set_image(self.sprites.stand)
        self._follow_tick()

    def _follow_animate(self) -> None:
        self.follow_anim_job = None
        if not self._alive() or self.dragging or self.mode != "follow" or self.state != "walk":
            self.follow_animating = False
            return

        frames = self._walk_sprites[self.direction]
        self._set_image(frames[self.walk_frame % 2])
        self.walk_frame += 1
        self.follow_anim_job = self._safe_after(WALK_FRAME_MS, self._follow_animate)

    def _follow_move(self) -> None:
        if not self._alive() or self.dragging or self.mode != "follow" or self.state in ("action", "sleep"):
            self._schedule_follow_tick()
            return

        mx = self.root.winfo_pointerx()
        my = self.root.winfo_pointery()
        cx = self.x + self.display_size // 2
        cy = self.y + self.display_size // 2
        dx = mx - cx
        dy = my - cy
        dist = (dx * dx + dy * dy) ** 0.5

        if dist > FOLLOW_FAR_DIST:
            self._maybe_show_follow_wait()

        if dist < FOLLOW_STOP_DIST:
            if self.state != "stand":
                self.state = "stand"
                self._set_image(self.sprites.stand)
            self.follow_animating = False
            self._schedule_follow_tick()
            return

        if abs(dx) > abs(dy):
            direction = "right" if dx > 0 else "left"
        else:
            direction = "front" if dy > 0 else "back"

        if self.follow_last_dir and direction != self.follow_last_dir:
            self._track_follow_spin(direction)
            if self.follow_dizzy:
                return
        self.follow_last_dir = direction

        self.state = "walk"
        self.direction = direction
        step_x, step_y = self.FOLLOW_DELTAS[direction]
        self.x += step_x
        self.y += step_y
        self._place_window()

        if not self.follow_animating:
            self.follow_animating = True
            self._follow_animate()

        self._schedule_follow_tick()

    def _maybe_show_follow_wait(self) -> None:
        now_ms = int(time.time() * 1000)
        if now_ms - self.last_follow_wait_ms < FOLLOW_WAIT_COOLDOWN_MS:
            return
        self.last_follow_wait_ms = now_ms
        self._show_speech_dialog(random.choice(FOLLOW_WAIT_TEXTS), auto_hide_ms=2500)

    def _open_size_menu(self) -> None:
        self._show_sub_menu(
            [
                (f"小{' ✓' if self.display_size == SIZE_PRESETS['小'] else ''}", lambda: self._set_size_preset("小")),
                (f"中{' ✓' if self.display_size == SIZE_PRESETS['中'] else ''}", lambda: self._set_size_preset("中")),
                (f"大{' ✓' if self.display_size == SIZE_PRESETS['大'] else ''}", lambda: self._set_size_preset("大")),
            ],
            offset_x=360,
        )

    def _open_system_menu(self) -> None:
        self._show_sub_menu(
            [
                ("操作说明", self._open_operation_guide),
                ("回忆 ▶", self._open_memories_menu),
                ("我的 ▶", self._open_my_menu),
                ("设置 ▶", self._open_panel_settings),
                ("对话 ▶", self._open_dialog_menu),
                ("重置", self._confirm_reset_settings),
                ("问题反馈", self._open_feedback),
                ("关于", self._open_about),
                ("退出", self._on_close),
            ],
            offset_x=240,
        )

    def _open_dialog_menu(self) -> None:
        self._show_sub_menu(
            [
                ("AI 对话", self._toggle_ai_chat),
                ("普通对话 ▶", self._open_preset_dialog_menu),
            ],
            offset_x=360,
        )

    def _open_preset_dialog_menu(self) -> None:
        items = [(q, lambda qq=q, ans=a: self._play_preset_dialog(qq, ans)) for q, a in PRESET_DIALOGS]
        self._show_sub_menu(items, offset_x=480)

    def _play_preset_dialog(self, question: str, answers: tuple[str, ...]) -> None:
        self._hide_main_menu()
        if self.preset_dialog_job:
            try:
                self.root.after_cancel(self.preset_dialog_job)
            except Exception:
                pass
            self.preset_dialog_job = None
        reply = random.choice(answers)
        self._show_speech_dialog(f"你：{question}", auto_hide_ms=2400)
        delay = _typing_duration_ms(f"你：{question}") + 500
        self.preset_dialog_job = self.root.after(
            delay, lambda q=question, r=reply: self._show_preset_dialog_answer(q, r)
        )

    def _show_preset_dialog_answer(self, question: str, reply: str) -> None:
        self.preset_dialog_job = None
        self._show_speech_dialog(reply, auto_hide_ms=6200, typewriter_ms=TYPEWRITER_MS)

    def _match_preset_dialog(self, user_text: str) -> str | None:
        text = user_text.strip().lower()
        if not text:
            return None
        for question, answers in PRESET_DIALOGS:
            q_core = question.rstrip("？?")
            if q_core in user_text or user_text.strip() == q_core:
                return random.choice(answers)
        keyword_map: tuple[tuple[tuple[str, ...], int], ...] = (
            (("你是谁", "叫什么", "名字", "苍叶", "aoba", "濑良垣", "主人公"), 0),
            (("能力", "暴露", "魄", "声音", "操纵"), 1),
            (("多高", "身高", "175"), 2),
            (("血型",), 3),
            (("生日", "星座", "金牛", "4月22", "四月"), 4),
            (("职业", "工作", "兼职"), 5),
            (("搭档", "伙伴", "莲", "蓮", "allmate", "智能伴侣"), 6),
            (("夹克", "jacket", "蓝色", "衣服", "plain nuts"), 7),
            (("身世", "经历", "婴儿", "三重", "定制", "棋子", "基因", "人格"), 8),
            (("心意", "力量", "教会", "思念"), 9),
            (("祖母", "多惠", "长大", "怎么长大"), 10),
            (("住", "哪里", "碧岛", "旧居民区", "旧街区"), 11),
            (("平时", "日常", "头痛", "耳机", "音乐", "莱姆音乐", "肋排"), 12),
            (("莱姆", "rhyme", "对战", "战无不胜", "记忆", "封印"), 13),
            (("另一个", "破坏", "哥哥生", "脑内"), 14),
            (("白色苍叶", "红雀"), 15),
            (("真谛", "解放", "重生", "潜入", "拯救"), 16),
            (("东江", "财阀", "黑色野心"), 17),
            (("头发", "长发", "紫色", "神经"), 18),
        )
        for keywords, idx in keyword_map:
            if any(k.lower() in text for k in keywords):
                return random.choice(PRESET_DIALOGS[idx][1])
        return None

    def _get_drag_handle(self) -> tuple[int, int, int, int]:
        if self.display_size not in self._drag_handle_cache:
            self._drag_handle_cache[self.display_size] = _compute_drag_handle(self.display_size)
        return self._drag_handle_cache[self.display_size]

    def _hide_size_loading(self) -> None:
        self.size_loading_active = False
        self.size_loading_preload_started = False
        if self.size_loading_job:
            try:
                self.root.after_cancel(self.size_loading_job)
            except Exception:
                pass
            self.size_loading_job = None
        if self.size_loading_win and self.size_loading_win.winfo_exists():
            self.size_loading_win.destroy()
        self.size_loading_win = None
        self.size_loading_canvas = None
        self._sync_wait_hint()
        try:
            if self.label and not self.label.winfo_manager():
                self.label.pack()
        except Exception:
            pass

    def _hide_companion_loading(self) -> None:
        self.companion_loading_active = False
        self.companion_loading_callback = None
        if self.companion_loading_job:
            try:
                self.root.after_cancel(self.companion_loading_job)
            except Exception:
                pass
            self.companion_loading_job = None
        if self.companion_loading_win and self.companion_loading_win.winfo_exists():
            self.companion_loading_win.destroy()
        self.companion_loading_win = None
        self.companion_loading_canvas = None
        self._sync_wait_hint()

    def _place_companion_loading(self) -> None:
        if not self.companion_loading_win or not self.companion_loading_win.winfo_exists():
            return
        load_size = min(MINI_PET_SIZE, self.display_size + 36)
        gap = MINI_PET_SIDE_GAP
        x = self.x - load_size - gap
        if x < 8:
            x = self.x + self.display_size + gap
        y = self.y + self.display_size - load_size
        self.companion_loading_win.geometry(f"{load_size}x{load_size}+{int(x)}+{int(y)}")

    def _show_companion_loading(self, callback) -> None:
        self._hide_companion_loading()
        self.companion_loading_active = True
        self.companion_loading_callback = callback
        self.companion_loading_phase = 0
        self.companion_loading_start_ms = int(time.time() * 1000)
        self.companion_loading_was_cached = MINI_PET_SIZE in self._mini_pet_sprite_cache
        load_size = min(MINI_PET_SIZE, self.display_size + 36)
        self.companion_loading_win = tk.Toplevel(self.root)
        self.companion_loading_win.overrideredirect(True)
        self.companion_loading_win.attributes("-topmost", True)
        self.companion_loading_win.configure(bg="magenta")
        self.companion_loading_win.wm_attributes("-transparentcolor", "magenta")
        self.companion_loading_canvas = tk.Canvas(
            self.companion_loading_win,
            width=load_size,
            height=load_size,
            bg="magenta",
            highlightthickness=0,
        )
        self.companion_loading_canvas.pack()
        self._place_companion_loading()
        self.root.after_idle(lambda: self._get_mini_pet_sprites(MINI_PET_SIZE))
        self._show_wait_hint("请耐心等待…加载金目")
        self._animate_companion_loading()

    def _animate_companion_loading(self) -> None:
        if not self.companion_loading_active or not self.companion_loading_canvas:
            return
        load_size = self.companion_loading_canvas.winfo_width() or min(MINI_PET_SIZE, self.display_size + 36)
        _draw_size_loading_frame(self.companion_loading_canvas, load_size, self.companion_loading_phase, label="金目")
        self.companion_loading_phase += 1
        self._place_companion_loading()
        elapsed = int(time.time() * 1000) - self.companion_loading_start_ms
        ready = MINI_PET_SIZE in self._mini_pet_sprite_cache
        min_ms = COMPANION_LOAD_MIN_CACHED_MS if self.companion_loading_was_cached else COMPANION_LOAD_MIN_MS
        if ready and elapsed >= min_ms:
            cb = self.companion_loading_callback
            self._hide_companion_loading()
            if cb:
                cb()
            return
        self.companion_loading_job = self.root.after(SIZE_LOAD_ANIM_MS, self._animate_companion_loading)

    def _place_size_loading(self) -> None:
        if not self.size_loading_win or not self.size_loading_win.winfo_exists():
            return
        display_y = self.y + self.click_bounce_offset
        self.size_loading_win.geometry(f"{self.display_size}x{self.display_size}+{self.x}+{display_y}")

    def _animate_size_loading(self) -> None:
        if not self.size_loading_active or not self.size_loading_canvas:
            return
        size = self.display_size
        _draw_size_loading_frame(self.size_loading_canvas, size, self.size_loading_phase, label="尺寸")
        self.size_loading_phase += 1
        self._place_size_loading()
        target = self.size_loading_target
        if not self.size_loading_preload_started:
            self.size_loading_preload_started = True
            self.root.after_idle(lambda s=target: self._ensure_sprite_cached(s))
        elapsed = int(time.time() * 1000) - self.size_loading_start_ms
        min_ms = SIZE_LOAD_MIN_CACHED_MS if self.size_loading_was_cached else SIZE_LOAD_MIN_MS
        if target in self._sprite_cache and elapsed >= min_ms:
            self._finish_size_loading()
            return
        self.size_loading_job = self.root.after(SIZE_LOAD_ANIM_MS, self._animate_size_loading)

    def _show_size_loading(self, preset: str, new_size: int) -> None:
        self._hide_size_loading()
        self.size_loading_active = True
        self.size_loading_preset = preset
        self.size_loading_target = new_size
        self.size_loading_phase = 0
        self.size_loading_start_ms = int(time.time() * 1000)
        self.size_loading_was_cached = new_size in self._sprite_cache
        self.size_loading_preload_started = self.size_loading_was_cached
        try:
            self.label.pack_forget()
        except Exception:
            pass
        self.size_loading_win = tk.Toplevel(self.root)
        self.size_loading_win.overrideredirect(True)
        self.size_loading_win.attributes("-topmost", True)
        self.size_loading_win.configure(bg="magenta")
        self.size_loading_win.wm_attributes("-transparentcolor", "magenta")
        self.size_loading_canvas = tk.Canvas(
            self.size_loading_win,
            width=self.display_size,
            height=self.display_size,
            bg="magenta",
            highlightthickness=0,
        )
        self.size_loading_canvas.pack()
        self._place_size_loading()
        self._show_wait_hint("请耐心等待…切换尺寸")
        if not self.size_loading_preload_started:
            self.root.after_idle(lambda s=new_size: self._ensure_sprite_cached(s))
            self.size_loading_preload_started = True
        self._animate_size_loading()

    def _finish_size_loading(self) -> None:
        if not self.size_loading_active:
            return
        preset = self.size_loading_preset
        new_size = self.size_loading_target
        if new_size not in self._sprite_cache:
            self._enter_ui_busy("请耐心等待…加载资源")
            try:
                self._sprite_cache[new_size] = SpriteSet(new_size)
            finally:
                self._exit_ui_busy()
        self._hide_size_loading()
        self._apply_size_preset(preset, new_size)

    def _set_size_preset(self, preset: str) -> None:
        new_size = SIZE_PRESETS[preset]
        self._hide_main_menu()
        if new_size == self.display_size:
            self._show_toast(f"当前已是「{preset}」尺寸", PIXEL_COLOR)
            return
        self._interrupt_current_interaction()
        self._show_size_loading(preset, new_size)

    def _apply_size_preset(self, preset: str, new_size: int) -> None:
        if new_size not in self._sprite_cache:
            self._sprite_cache[new_size] = SpriteSet(new_size)
        self.display_size = new_size
        self.sprites = self._sprite_cache[new_size]
        self.drag_handle = self._get_drag_handle()
        preset_key = next((k for k, v in SIZE_PRESETS.items() if v == new_size), "中")
        self.app_config["display_size"] = new_size
        self.app_config["display_preset"] = preset_key
        _save_app_config(self.app_config)
        self._apply_current_sprite()
        self._place_window()
        self._reposition_panel(force=True)
        for entry in self.mini_pets:
            self._mini_pet_follow_tick(entry)
        if self.mode == "quiet" and self.state == "rest":
            self._show_sleep_zzz()
        self._show_toast(f"尺寸已设为「{preset}」", PIXEL_COLOR)
        self._resume_idle()

    def _apply_current_sprite(self) -> None:
        if self.state == "walk":
            self._set_image(self._walk_sprites[self.direction][self.walk_frame % 2])
        elif self.state == "action" and self.action_name in self.sprites.actions:
            frames = self.sprites.actions[self.action_name]
            self._set_image(frames[self.action_frame % len(frames)])
        elif self.state == "sleep":
            idx = 1 if self.sleep_in_deep else 0
            self._set_image(self.sprites.sleep[idx])
        elif self.state == "action" and self.action_name == "angry":
            self._set_image(self.sprites.stand_angry)
        elif self.state == "action" and self.action_name == "question":
            self._set_image(self.sprites.stand_question)
        elif self.state == "action" and self.action_name == "sad":
            if self.sad_phase == "sad1":
                self._set_image(self.sprites.sad1)
            elif self.sad_phase == "sad2":
                self._set_image(self.sprites.sad2)
            else:
                self._set_image(self.sprites.actions["squat"][0])
        elif self.state == "action" and self.action_name == "idea":
            self._set_image(self.sprites.eat2_only)
        elif self.state == "action" and self.action_name == "kick":
            self._set_image(self.sprites.kick)
        elif self.state == "action" and self.action_name == "shy":
            self._set_image(self.sprites.shy[self.shy_frame_idx])
        elif self.state == "action" and self.action_name == "wink":
            self._set_image(self.sprites.wink)
        elif self.state == "action" and self.action_name == "like":
            self._set_image(self.sprites.like)
        elif self.state == "action" and self.action_name == "yesno":
            self._set_image(self.sprites.yes if getattr(self, "yesno_is_yes", True) else self.sprites.no)
        elif self.state == "action" and self.action_name == "yes":
            self._set_image(self.sprites.yes)
        elif self.state == "action" and self.action_name == "no":
            self._set_image(self.sprites.no)
        elif self.state == "action" and self.action_name == "happy":
            self._set_image(
                self.sprites.happy if self.happy_step_idx % 2 == 0 else self.sprites.stand
            )
        elif self.mode == "quiet" and self.state == "rest":
            self._set_image(self.sprites.sleep[1])
        elif self.dragging:
            pass
        elif self.music_sprite_mode and self.state in ("stand", "walk"):
            self._set_image(self._current_stand_sprite() if self.state == "stand" else self._walk_sprites[self.direction][self.walk_frame % 2])
        else:
            self._set_image(self.sprites.stand)

    def _on_root_click(self, event: tk.Event) -> None:
        if event.widget is self.label:
            return
        self._hide_main_menu()
        if self.ai_chat_win and self.ai_chat_win.winfo_exists() and not self._is_ai_chat_widget(event.widget):
            self._check_ai_chat_focus()

    def _hit_drag_handle(self, x: int, y: int) -> bool:
        x1, y1, x2, y2 = self.drag_handle
        return x1 <= x <= x2 and y1 <= y <= y2

    def _play_click_bounce(self) -> None:
        if self.click_bouncing:
            return
        self.click_bouncing = True
        self.click_bounce_offset = -CLICK_BOUNCE_PX
        self._place_window()
        self._place_sleep_zzz()
        self._place_ai_chat()
        self._bounce_mini_pets(up=True)
        self.root.after(CLICK_BOUNCE_MS, self._click_bounce_down)

    def _click_bounce_down(self) -> None:
        self.click_bounce_offset = 0
        self.click_bouncing = False
        self._place_window()
        self._place_sleep_zzz()
        self._place_ai_chat()
        self._bounce_mini_pets(up=False)

    def _bounce_mini_pets(self, *, up: bool) -> None:
        bounce = -CLICK_BOUNCE_PX if up else 0
        for entry in self.mini_pets:
            entry["bounce_offset"] = bounce
            win = entry.get("win")
            if not win or not win.winfo_exists():
                continue
            try:
                win.geometry(f"+{int(entry['x'])}+{int(entry['y']) + bounce}")
            except Exception:
                pass
            self._place_mini_pet_music_wave(entry)
            self._place_mini_pet_bg_fx(entry)

    def _handle_face_double_click(self) -> bool:
        if self.mode == "game" or self.state == "work":
            return False
        if self.state == "action" and self.action_name == "shy":
            return False
        now_ms = int(time.time() * 1000)
        if self.face_click_pending_ms and now_ms - self.face_click_pending_ms <= FACE_DCLICK_MS:
            self.face_click_pending_ms = 0
            if now_ms - self.face_dclick_last_combo_ms > FACE_DCLICK_COMBO_RESET_MS:
                self.face_dclick_combos = 0
            self.face_dclick_combos += 1
            self.face_dclick_last_combo_ms = now_ms
            if self.face_dclick_combos >= FACE_DCLICK_COMBOS_NEEDED:
                self.face_dclick_combos = 0
                self._play_expression_shy()
                return True
            return True
        self.face_click_pending_ms = now_ms
        return False

    def _on_press(self, event: tk.Event) -> None:
        if self._startup_busy():
            return
        self._hide_main_menu()
        if self.mode == "game":
            return
        if self.state == "action" and self.action_name == "shy" and not self._hit_drag_handle(event.x, event.y):
            self._handle_shy_click()
            self._play_click_bounce()
            return
        if self._hit_drag_handle(event.x, event.y):
            if self.state == "sleep":
                self._wake_from_sleep()
            if self.mode == "quiet" and self.state == "rest":
                self._stop_rest_bobble()
            self.dragging = True
            self.drag_x = event.x_root - self.x
            self.drag_y = event.y_root - self.y
            self.drag_track_x = event.x_root
            self.drag_track_y = event.y_root
            self.drag_last_dir = ""
            self.drag_spin_dir = 0
            self.drag_spin_steps = 0
            self.drag_dizzy_extra_spins = 0
            if self.state == "work":
                pass
            else:
                self._start_drag_move()
            return
        if self._handle_face_double_click():
            self._play_click_bounce()
            return
        self._play_click_bounce()
        self._handle_state_multi_click()
        if self.mode == "quiet" and self.state == "rest":
            self._handle_rest_click()

    def _handle_state_multi_click(self) -> None:
        if self.mode == "game" or self.dragging:
            return
        key = self.state
        if self.state == "action" and self.action_name:
            key = f"action:{self.action_name}"
        elif self.mode == "quiet" and self.state == "rest":
            key = "rest"
        elif self.music_sprite_mode and self.state == "stand":
            key = "music"
        lines = STATE_MULTI_CLICK.get(key)
        if not lines:
            return
        now_ms = int(time.time() * 1000)
        if now_ms - self.multi_click_last_ms > MULTI_CLICK_WINDOW_MS or self.multi_click_key != key:
            self.multi_click_count = 0
            self.multi_click_key = key
        self.multi_click_last_ms = now_ms
        self.multi_click_count += 1
        if self.multi_click_count < 2:
            return
        if self.speech_dialog and self.speech_dialog.winfo_exists():
            return
        self._show_speech_dialog(random.choice(lines), auto_hide_ms=2600)
        self.multi_click_count = 0

    def _handle_rest_click(self) -> None:
        now_ms = int(time.time() * 1000)
        if now_ms - self.rest_last_click_ms > REST_CLICK_WINDOW_MS:
            self.rest_click_count = 0
        self.rest_last_click_ms = now_ms
        self.rest_click_count += 1

        if self.rest_click_count >= REST_WAKE_CLICKS:
            self.rest_click_count = 0
            self._enable_free()
            return
        if self.rest_click_count >= REST_PEEK_CLICKS:
            self.rest_click_count = 0
            self._rest_peek_sleep1()

    def _rest_peek_sleep1(self) -> None:
        if self.mode != "quiet" or self.state != "rest":
            return
        if self.rest_peek_job:
            self.root.after_cancel(self.rest_peek_job)
        self._stop_rest_bobble()
        self._set_image(self.sprites.sleep[0])
        self.rest_peek_job = self.root.after(REST_PEEK_MS, self._rest_peek_done)

    def _rest_peek_done(self) -> None:
        self.rest_peek_job = None
        if self.mode != "quiet" or self.state != "rest":
            return
        self._set_image(self.sprites.sleep[1])
        self._schedule_rest_bobble()

    def _start_drag_move(self) -> None:
        self._stop_drag_move()
        self._end_drag_dizzy()
        if self.state == "action" and self.action_name:
            self._cancel_action_end()
            self._cancel_action_defer()
            self._clear_all_action_fx()
            if self.action_name == "wink":
                self._wink_restore_free = False
            self.action_name = ""
        self.state = "drag"
        self.drag_move_start_ms = int(time.time() * 1000)
        self.drag_last_dir = ""
        self.drag_spin_dir = 0
        self.drag_spin_steps = 0
        self.drag_dizzy_extra_spins = 0
        self._drag_move_tick()

    def _drag_move_tick(self) -> None:
        if not self.dragging:
            return

        elapsed = int(time.time() * 1000) - self.drag_move_start_ms
        total_ms = MOVE_CYCLE_MS * MOVE_DRAG_CYCLES
        if elapsed >= total_ms:
            self._set_image(self.sprites.move[0])
        else:
            phase_elapsed = elapsed % MOVE_CYCLE_MS
            if phase_elapsed < MOVE23_DURATION_MS:
                frame_idx = 1 if (phase_elapsed // MOVE23_FRAME_MS) % 2 == 0 else 2
                self._set_image(self.sprites.move[frame_idx])
            else:
                self._set_image(self.sprites.move[0])

        self.drag_move_job = self.root.after(MOVE23_FRAME_MS, self._drag_move_tick)

    def _stop_drag_move(self) -> None:
        if self.drag_move_job:
            self.root.after_cancel(self.drag_move_job)
            self.drag_move_job = None

    def _on_drag(self, event: tk.Event) -> None:
        if not self.dragging:
            return
        dx = event.x_root - self.drag_track_x
        dy = event.y_root - self.drag_track_y
        self.drag_track_x = event.x_root
        self.drag_track_y = event.y_root
        self.x = event.x_root - self.drag_x
        self.y = event.y_root - self.drag_y
        self._clamp_position()
        self._place_window(light=True)
        if self.state == "drag":
            direction = self._drag_move_dir(dx, dy)
            if direction:
                self._track_drag_spin(direction)
        if self.state == "work":
            self._refresh_work_overlay()

    def _on_release(self, _event: tk.Event) -> None:
        if not self.dragging:
            return
        had_move_anim = self.state == "drag"
        self.dragging = False
        self._stop_drag_move()
        self._end_drag_dizzy()
        if self.mode == "game":
            self.state = "game"
            self._set_image(self.sprites.stand)
            self._place_window()
            return
        if self.state == "work":
            self._set_image(self.sprites.work_stand if not self.work_carrying else self._walk_sprites[self.direction][0])
            self._refresh_work_overlay()
            if not self.work_animating:
                self.work_animating = True
                self._work_animate()
            self._work_move_step()
            self._place_window()
            return
        if self.mode == "quiet":
            self.state = "rest"
            self.rest_base_y = self.y
            self._set_image(self.sprites.sleep[1])
            self._show_sleep_zzz()
            self._schedule_rest_bobble()
            self._place_window()
        elif had_move_anim:
            self._play_move_land()
        else:
            self.state = "stand"
            self._set_image(self.sprites.stand)
            delay = random.randint(800, 2000)
            self.idle_job = self.root.after(delay, self._resume_idle)
            self._place_window()

    def _play_move_land(self) -> None:
        self.move_land_base_y = self.y
        land_px = self.display_size // 3
        self.y = self.move_land_base_y + land_px
        self.state = "stand"
        self._set_image(self.sprites.stand)
        self._place_window()
        tok = self.interaction_token
        self.move_land_job = self.root.after(
            MOVE_LAND_MS, lambda t=tok: self._move_land_settle(t)
        )

    def _move_land_settle(self, tok: int | None = None) -> None:
        if tok is not None and tok != self.interaction_token:
            return
        self.move_land_job = None
        self._place_window()
        delay = random.randint(800, 2000)
        self.idle_job = self.root.after(delay, self._resume_idle)

    def _on_close(self, _event=None) -> None:
        if self._closing:
            return
        self._closing = True
        self._hide_main_menu()
        self._hide_wait_hint()
        if self._ui_heartbeat_job:
            try:
                self.root.after_cancel(self._ui_heartbeat_job)
            except Exception:
                pass
            self._ui_heartbeat_job = None
        self._hide_toast()
        self._cancel_expose_qte()
        self._unregister_hotkey()
        self._play_exit_dissolve()

    def _play_exit_dissolve(self) -> None:
        pending = {"count": 0}

        def one_done() -> None:
            pending["count"] -= 1
            if pending["count"] <= 0:
                self._finalize_close()

        pending["count"] += 1
        self._run_exit_dissolve_at(
            self.x,
            self.y + self.click_bounce_offset,
            self.display_size,
            on_hide=lambda: self.label.pack_forget(),
            on_done=one_done,
        )

        if self.companion_bar_enabled and self.mini_pets:
            for entry in list(self.mini_pets):
                follow_job = entry.get("follow_job")
                if follow_job:
                    try:
                        self.root.after_cancel(follow_job)
                    except Exception:
                        pass
                    entry["follow_job"] = None
                self._stop_mini_pet_music_wave(entry)
                lbl = entry.get("label")
                pending["count"] += 1
                self._run_exit_dissolve_at(
                    int(entry["x"]),
                    int(entry["y"]),
                    int(entry.get("size", MINI_PET_SIZE)),
                    on_hide=lambda label=lbl: label.pack_forget() if label else None,
                    on_done=one_done,
                )

    def _run_exit_dissolve_at(
        self,
        x: int,
        y: int,
        size: int,
        *,
        on_hide=None,
        on_done=None,
    ) -> None:
        if on_hide:
            on_hide()
        total_frames = max(EXIT_DISSOLVE_FRAMES, _loading_peak_phase(size))
        dissolve_win = tk.Toplevel(self.root)
        dissolve_win.overrideredirect(True)
        dissolve_win.attributes("-topmost", True)
        dissolve_win.configure(bg="magenta")
        dissolve_win.wm_attributes("-transparentcolor", "magenta")
        canvas = tk.Canvas(dissolve_win, width=size, height=size, bg="magenta", highlightthickness=0)
        canvas.pack()
        dissolve_win.geometry(f"+{x}+{y}")
        frame = {"n": 0}
        tick_job: dict[str, str | None] = {"id": None}

        def tick() -> None:
            if not dissolve_win.winfo_exists():
                if on_done:
                    on_done()
                return
            _draw_size_loading_frame(canvas, size, frame["n"], reverse=True)
            frame["n"] += 1
            if frame["n"] <= total_frames:
                tick_job["id"] = self.root.after(EXIT_DISSOLVE_MS, tick)
            else:
                tick_job["id"] = None
                if dissolve_win.winfo_exists():
                    dissolve_win.destroy()
                if on_done:
                    on_done()

        tick()

    def _finalize_close(self) -> None:
        self._hide_size_loading()
        self._hide_companion_loading()
        self._hide_happy_fx()
        self._hide_food_fx()
        self._hide_rain_fx()
        self._hide_bulb_fx()
        self._hide_sleep_zzz()
        self._stop_game_mode()
        self._stop_work_mode()
        self._close_ai_chat()
        self._cancel_follow_chain()
        if self.schedule_win and self.schedule_win.winfo_exists():
            self.schedule_win.destroy()
        self._stop_drag_move()
        self._stop_rest_bobble()
        self._cancel_action_end()
        if self.rest_peek_job:
            self.root.after_cancel(self.rest_peek_job)
            self.rest_peek_job = None
        self._stop_call_audio()
        self._close_rhyme_fight(resume=False)
        self._destroy_all_mini_pets()
        self._close_panel()
        self._hide_speech_dialog()
        self.root.destroy()

    def _hide_speech_dialog(self) -> None:
        if self.speech_type_job:
            self.root.after_cancel(self.speech_type_job)
            self.speech_type_job = None
        if self.speech_hide_job:
            self.root.after_cancel(self.speech_hide_job)
            self.speech_hide_job = None
        if self.speech_dialog and self.speech_dialog.winfo_exists():
            self.speech_dialog.destroy()
        self.speech_dialog = None
        self.speech_label = None
        self.speech_full_text = ""
        self.speech_on_complete = None

    def _notify_speech_complete(self) -> None:
        if self.speech_on_complete:
            cb = self.speech_on_complete
            self.speech_on_complete = None
            cb()

    def _play_type_sound(self) -> None:
        global _type_sound, _type_sound_channel, _type_sound_last_ms
        now = int(time.time() * 1000)
        if now - _type_sound_last_ms < TYPE_SOUND_MIN_GAP_MS:
            return
        sound = _get_type_sound()
        if not sound or sound is False:
            return
        vol = self._sound_scale("sfx")
        if vol <= 0:
            return
        try:
            import pygame

            # 固定声道：打断上一次，避免 1s 音效叠满通道导致未响应
            ch = pygame.mixer.Channel(0)
            try:
                ch.stop()
            except Exception:
                pass
            ch.set_volume(vol)
            ch.play(sound)
            _type_sound_channel = ch
            _type_sound_last_ms = now
        except Exception:
            try:
                self._play_sound_with_volume(sound, "sfx")
                _type_sound_last_ms = now
            except Exception:
                pass

    def _show_speech_dialog(
        self,
        text: str,
        auto_hide_ms: int | None = None,
        *,
        on_complete=None,
        color: str = PIXEL_COLOR,
        typewriter_ms: int | None = None,
    ) -> None:
        self._hide_speech_dialog()

        self.speech_dialog = tk.Toplevel(self.root)
        self.speech_dialog.overrideredirect(True)
        self.speech_dialog.attributes("-topmost", True)
        self.speech_dialog.configure(bg="#111122")

        border = tk.Frame(self.speech_dialog, bg=color, padx=2, pady=2)
        border.pack()
        inner = tk.Frame(border, bg="#111122", padx=12, pady=10)
        inner.pack()

        self.speech_label = tk.Label(
            inner,
            text="",
            font=PIXEL_FONT,
            fg=color,
            bg="#111122",
            justify=tk.LEFT,
        )
        self.speech_label.pack()

        self.speech_full_text = text
        self.speech_type_idx = 0
        self.speech_type_ms = typewriter_ms if typewriter_ms is not None else TYPEWRITER_MS
        self.speech_on_complete = on_complete
        self._place_pet_attached_popup(
            self.speech_dialog,
            self.x + self.display_size + PET_SPEECH_GAP,
            self.y,
        )
        self._speech_type_next(auto_hide_ms)

    def _speech_type_next(self, auto_hide_ms: int | None) -> None:
        if not self.speech_dialog or not self.speech_dialog.winfo_exists() or not self.speech_label:
            return

        if self.speech_type_idx >= len(self.speech_full_text):
            self._notify_speech_complete()
            if auto_hide_ms is not None:
                self.speech_hide_job = self.root.after(auto_hide_ms, self._hide_speech_dialog)
            return

        char = self.speech_full_text[self.speech_type_idx]
        self.speech_label.config(text=self.speech_full_text[: self.speech_type_idx + 1])
        if char == "\n" or self.speech_type_idx % 12 == 0:
            self._place_pet_attached_popup(
                self.speech_dialog,
                self.x + self.display_size + PET_SPEECH_GAP,
                self.y,
            )
        if char not in (" ", "\n") and self.action_name != "call":
            self._play_type_sound()
        self.speech_type_idx += 1
        delay = self.speech_type_ms * (2 if char == "\n" else 1)
        self.speech_type_job = self.root.after(delay, lambda: self._speech_type_next(auto_hide_ms))

    def _hide_food_fx(self) -> None:
        if self.food_fx_win and self.food_fx_win.winfo_exists():
            self.food_fx_win.destroy()
        self.food_fx_win = None
        self.food_fx_canvas = None
        self.food_fx_id = None
        self._notify_bg_fx_change()

    def _place_food_fx(self) -> None:
        if not self.food_fx_win or not self.food_fx_win.winfo_exists():
            return
        pad = FOOD_FX_PAD
        display_y = self.y + self.click_bounce_offset
        self.food_fx_win.geometry(f"+{self.x - pad}+{display_y - pad}")
        self.root.lift()

    def _show_food_fx(self, food_id: str) -> None:
        self._hide_food_fx()
        self.food_fx_id = food_id
        pad = FOOD_FX_PAD
        size = self.display_size + pad * 2

        self.food_fx_win = tk.Toplevel(self.root)
        self.food_fx_win.overrideredirect(True)
        self.food_fx_win.attributes("-topmost", False)
        self.food_fx_win.configure(bg="magenta")
        self.food_fx_win.wm_attributes("-transparentcolor", "magenta")

        self.food_fx_canvas = tk.Canvas(
            self.food_fx_win, width=size, height=size, bg="magenta", highlightthickness=0
        )
        self.food_fx_canvas.pack()
        self._food_fx_step(0)
        self._notify_bg_fx_change()

    def _food_fx_step(self, elapsed_ms: int) -> None:
        if not self.food_fx_canvas or not self.food_fx_id:
            return

        total_ms = FOOD_APPEAR_MS + FOOD_HOLD_MS + FOOD_VANISH_MS
        if elapsed_ms >= total_ms:
            self._hide_food_fx()
            return

        canvas = self.food_fx_canvas
        canvas.delete("all")
        pad = FOOD_FX_PAD
        size = self.display_size + pad * 2
        px = max(4, self.display_size // FOOD_FX_PIXEL_DIV)
        if elapsed_ms < FOOD_APPEAR_MS:
            progress = elapsed_ms / FOOD_APPEAR_MS
        elif elapsed_ms < FOOD_APPEAR_MS + FOOD_HOLD_MS:
            progress = 1.0
        else:
            vanish = elapsed_ms - FOOD_APPEAR_MS - FOOD_HOLD_MS
            progress = max(0.0, 1.0 - vanish / FOOD_VANISH_MS)
        scale = max(3, int(px * (0.6 + 0.4 * progress)))
        offset_y = int((1.0 - progress) * scale * 2)
        base_x = size - scale * 5
        base_y = size // 2 + scale - offset_y
        _draw_pixel_food(canvas, self.food_fx_id, base_x, base_y, px=scale)
        self._place_food_fx()
        tok = self.interaction_token
        self.food_fx_job = self.root.after(
            50, lambda t=tok, e=elapsed_ms + 50: self._food_fx_step_guarded(t, e)
        )

    def _food_fx_step_guarded(self, tok: int, elapsed_ms: int) -> None:
        if tok != self.interaction_token:
            return
        self.food_fx_job = None
        self._food_fx_step(elapsed_ms)

    def _hide_happy_fx(self) -> None:
        if self.happy_fx_win and self.happy_fx_win.winfo_exists():
            self.happy_fx_win.destroy()
        self.happy_fx_win = None
        self.happy_fx_canvas = None
        self._notify_bg_fx_change()

    def _draw_pixel_flower(self, canvas: tk.Canvas, x: int, y: int, color: str, px: int = 3) -> None:
        petal = px
        canvas.create_rectangle(x, y, x + petal, y + petal, fill=color, outline="")
        canvas.create_rectangle(x - petal, y + petal, x, y + petal * 2, fill=color, outline="")
        canvas.create_rectangle(x + petal, y + petal, x + petal * 2, y + petal * 2, fill=color, outline="")
        canvas.create_rectangle(x, y + petal * 2, x + petal, y + petal * 3, fill=color, outline="")
        canvas.create_rectangle(x + petal // 2, y + petal, x + petal + petal // 2, y + petal * 2, fill="#ffee88", outline="")

    def _show_happy_fx(self) -> None:
        self._hide_happy_fx()
        pad = 24
        size = self.display_size + pad * 2

        self.happy_fx_win = tk.Toplevel(self.root)
        self.happy_fx_win.overrideredirect(True)
        self.happy_fx_win.attributes("-topmost", False)
        self.happy_fx_win.configure(bg="magenta")
        self.happy_fx_win.wm_attributes("-transparentcolor", "magenta")

        self.happy_fx_canvas = tk.Canvas(
            self.happy_fx_win, width=size, height=size, bg="magenta", highlightthickness=0
        )
        self.happy_fx_canvas.pack()

        colors = ("#ff88cc", "#ffcc44", "#88dd88", "#ff6688", "#cc88ff", "#88ccff")
        for _ in range(10):
            fx = random.randint(4, size - 16)
            fy = random.randint(4, size - 20)
            self._draw_pixel_flower(self.happy_fx_canvas, fx, fy, random.choice(colors))

        self._place_happy_fx()
        self._notify_bg_fx_change()

    def _place_happy_fx(self) -> None:
        if not self.happy_fx_win or not self.happy_fx_win.winfo_exists():
            return
        pad = 24
        display_y = self.y + self.click_bounce_offset
        self.happy_fx_win.geometry(f"+{self.x - pad}+{display_y - pad}")
        self.root.lift()

    def _show_call_dialog(self) -> None:
        self._show_speech_dialog(CALL_TEXT)
        self._play_call_audio()

    def _play_call_audio(self) -> None:
        if self.bg_music_playing:
            self.bg_music_paused_for_call = True
            try:
                import pygame

                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
            except Exception:
                pass
            self.bg_music_playing = False
        wav = _ensure_audio_wav(CALL_AUDIO_SRC, CALL_AUDIO_WAV)
        if wav is None:
            self.call_audio_ms = 0
            return
        self.call_audio_ms = _get_wav_duration_ms(wav)
        try:
            import pygame

            if not pygame.mixer.get_init():
                _init_pygame_mixer()
            pygame.mixer.music.load(str(wav))
            pygame.mixer.music.set_volume(self._sound_scale("voice"))
            pygame.mixer.music.play()
        except Exception:
            self.call_audio_ms = 0

    def _stop_call_audio(self) -> None:
        try:
            import pygame

            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass
        if self.bg_music_paused_for_call and self.music_sprite_mode:
            self.bg_music_paused_for_call = False
            self._start_bg_music()
        else:
            self.bg_music_paused_for_call = False

    def _hide_call_dialog(self) -> None:
        self._stop_call_audio()
        self._hide_speech_dialog()

    def _play_action(self, name: str) -> None:
        if self.dragging or self.state == "work":
            return
        if self.music_sprite_mode:
            return
        if name == "happy":
            self._play_happy()
            return
        if name not in SELECT_ACTIONS:
            return
        self._interrupt_current_interaction()

        self._interact_flair(name, banter=name not in ("hi", "call", "squat"))

        self.state = "action"
        self.action_name = name
        self.action_frame = 0
        frames = self.sprites.actions[name]
        self._set_image(frames[0])

        if name == "call":
            self._show_call_dialog()
        elif name == "hi":
            self._show_speech_dialog(HI_TEXT, typewriter_ms=HI_TYPEWRITER_MS)

        if len(frames) > 1:
            self._action_animate()

        if name == "call":
            typing_ms = _typing_duration_ms(CALL_TEXT)
            audio_ms = self.call_audio_ms or typing_ms
            self._schedule_action_end(duration_ms=max(typing_ms, audio_ms))
        elif name == "hi":
            self._schedule_action_end(duration_ms=_typing_duration_ms(HI_TEXT, char_ms=HI_TYPEWRITER_MS))
        else:
            self._schedule_action_end(action=name)

    def _play_happy(self) -> None:
        if self.dragging or self.state == "work" or self.music_sprite_mode:
            return
        self._interrupt_current_interaction()
        self._interact_flair("happy", banter=False, show_fx=False)
        self.state = "action"
        self.action_name = "happy"
        self.happy_step_idx = 0
        self.happy_base_y = self.y
        self._show_happy_fx()
        self._happy_step()
        self._schedule_action_end(action="happy", callback=self._finish_happy)

    def _finish_happy(self) -> None:
        if self.dragging or self.state != "action" or self.action_name != "happy":
            return
        self.y = self.happy_base_y
        self._hide_happy_fx()
        self._place_window()
        self._add_interact_mood()
        if self.mode == "quiet":
            self.state = "rest"
            self._set_image(self.sprites.sleep[1])
            self._show_sleep_zzz()
            self._schedule_rest_bobble()
        else:
            self.state = "stand"
            self._set_image(self.sprites.stand)
        if not self._check_mood_happy():
            self._resume_idle()

    def _happy_step(self) -> None:
        if self.dragging or self.state != "action" or self.action_name != "happy":
            return

        total_steps = HAPPY_CYCLES * 2
        if self.happy_step_idx >= total_steps:
            return

        if self.happy_step_idx % 2 == 0:
            self._set_image(self.sprites.happy)
            self.y = self.happy_base_y - HAPPY_JUMP_PX
        else:
            self._set_image(self.sprites.stand)
            self.y = self.happy_base_y

        self.happy_step_idx += 1
        self._place_window()
        self._place_happy_fx()
        tok = self.interaction_token
        self.happy_job = self.root.after(
            HAPPY_FRAME_MS, lambda t=tok: self._happy_step_guarded(t)
        )

    def _happy_step_guarded(self, tok: int) -> None:
        if tok != self.interaction_token:
            return
        self.happy_job = None
        self._happy_step()

    def _action_animate(self) -> None:
        if self.state != "action" or self.dragging:
            return

        if self.action_name not in self.sprites.actions:
            return
        frames = self.sprites.actions[self.action_name]
        if len(frames) < 2:
            return

        self.action_frame += 1
        self._set_image(frames[self.action_frame % 2])
        tok = self.interaction_token
        self.action_anim_job = self.root.after(
            ACTION_FRAME_MS, lambda t=tok: self._action_animate_guarded(t)
        )

    def _action_animate_guarded(self, tok: int) -> None:
        if tok != self.interaction_token:
            return
        self.action_anim_job = None
        self._action_animate()

    def _after_action(self) -> None:
        if self.dragging or self.state != "action":
            return
        if self.action_name == "call":
            self._hide_call_dialog()
        elif self.action_name == "hi":
            self._hide_speech_dialog()
        elif self.action_name == "eat":
            self._hide_food_fx()
        elif self.action_name == "sad":
            self._hide_rain_fx()
        elif self.action_name == "idea":
            self._hide_bulb_fx()
        elif self.action_name == "happy":
            self._hide_happy_fx()
        self._clear_all_action_fx()
        self._cancel_action_end()
        self._add_interact_mood()
        if self.mode == "quiet":
            self.state = "rest"
            self._set_image(self.sprites.sleep[1])
            self._show_sleep_zzz()
            self._schedule_rest_bobble()
        if not self._check_mood_happy():
            self._resume_idle()

    def _resume_idle_after_activity(self) -> None:
        """小游戏等活动结束后回到自由模式并恢复漫步。"""
        if self.dragging or not self.root.winfo_exists():
            return
        self._cancel_pending_mode_switch()
        self.mode_switch_token += 1
        if self.mode != "free":
            if self.mode in ("work", "game", "quiet"):
                self._apply_free_transition()
                return
            self._interrupt_for_mode_switch()
            self.mode = "free"
            self.follow_animating = False
            self.state = "stand"
            self.action_name = ""
            self._set_image(self._current_stand_sprite())
            self._place_window()
        self.root.after(150, self._resume_idle)

    def _schedule_stand_idle(self, *, min_delay: int = 1200, max_delay: int = 3500) -> None:
        if self.idle_job:
            try:
                self.root.after_cancel(self.idle_job)
            except Exception:
                pass
            self.idle_job = None
        if self.dragging or not self._supports_walk_idle() or self.state == "work":
            return
        delay = random.randint(min_delay, max_delay)
        tok = self.interaction_token
        self.idle_job = self.root.after(delay, lambda t=tok: self._idle_to_walk(t))

    def _start_idle_watchdog(self) -> None:
        if self.idle_watchdog_job:
            try:
                self.root.after_cancel(self.idle_watchdog_job)
            except Exception:
                pass
            self.idle_watchdog_job = None

        def tick() -> None:
            if not self.root.winfo_exists() or self._closing:
                return
            self._idle_watchdog_tick()
            self.idle_watchdog_job = self.root.after(IDLE_WATCHDOG_MS, tick)

        self.idle_watchdog_job = self.root.after(IDLE_WATCHDOG_MS, tick)

    def _idle_watchdog_tick(self) -> None:
        if not self._startup_ready or self.dragging or self._closing:
            return
        if self.mode not in ("free", "stroll"):
            return
        if self.state in ("work", "sleep", "game"):
            return
        # 暴露 / 倒计时 / 进行中的 QTE 会话：不可被看门狗清掉
        if getattr(self, "expose_session_active", False) or self.action_name == "expose":
            return
        if getattr(self, "_countdown_active", False):
            return
        if self.state == "action":
            if self.action_end_job or self.action_defer_job:
                return
            if self.action_name in ("expose", "yesno"):
                return
            self.action_name = ""
            self._clear_all_action_fx()
            self.state = "stand"
            self._set_image(self._current_stand_sprite())
        if self.state == "walk":
            if self.walk_move_job or self.walk_anim_job:
                return
            self.state = "stand"
            self._set_image(self._current_stand_sprite())
        if self.state == "stand" and not self.idle_job:
            self._schedule_stand_idle(min_delay=500, max_delay=1500)

    def _resume_idle(self) -> None:
        if self.dragging:
            return
        if self.state == "sleep" or self.sleep_interact_active:
            return
        if self.mode == "game":
            return
        if getattr(self, "expose_session_active", False) or self.action_name == "expose":
            return
        if getattr(self, "_countdown_active", False):
            return
        if self.mode in ("free", "stroll") and self.state == "action":
            self._cancel_action_end()
            self._clear_all_action_fx()
            self.action_name = ""
            self.state = "stand"
            self._set_image(self._current_stand_sprite())
        if self.mode == "follow":
            self._follow_tick()
        elif self.mode == "quiet":
            if self.state != "rest":
                self.state = "rest"
                self._set_image(self.sprites.sleep[1])
                self._show_sleep_zzz()
            self._schedule_rest_bobble()
        else:
            self._stand_tick()

    def _stop_rest_bobble(self) -> None:
        if self.rest_bobble_job:
            self.root.after_cancel(self.rest_bobble_job)
            self.rest_bobble_job = None

    def _schedule_rest_bobble(self) -> None:
        is_quiet_rest = self.mode == "quiet" and self.state == "rest"
        is_sleep_action = self.sleep_interact_active and self.state == "rest"
        if self.dragging or (not is_quiet_rest and not is_sleep_action):
            return
        self._stop_rest_bobble()
        pause = random.randint(REST_BOBBLE_PAUSE_MIN_MS, REST_BOBBLE_PAUSE_MAX_MS)
        tok = self.interaction_token
        self.rest_bobble_job = self.root.after(
            pause, lambda t=tok: self._rest_bobble_up_guarded(t)
        )

    def _rest_bobble_up_guarded(self, tok: int) -> None:
        if tok != self.interaction_token:
            return
        self._rest_bobble_up()

    def _rest_bobble_up(self) -> None:
        is_quiet_rest = self.mode == "quiet" and self.state == "rest"
        is_sleep_action = self.sleep_interact_active and self.state == "rest"
        if self.dragging or (not is_quiet_rest and not is_sleep_action):
            return
        self.rest_base_y = self.y
        self.y = self.rest_base_y - REST_BOBBLE_PX
        self._place_window()
        self._place_sleep_zzz()
        tok = self.interaction_token
        self.root.after(REST_BOBBLE_MS, lambda t=tok: self._rest_bobble_down_guarded(t))

    def _rest_bobble_down_guarded(self, tok: int) -> None:
        if tok != self.interaction_token:
            return
        self._rest_bobble_down()

    def _rest_bobble_down(self) -> None:
        is_quiet_rest = self.mode == "quiet" and self.state == "rest"
        is_sleep_action = self.sleep_interact_active and self.state == "rest"
        if self.dragging or (not is_quiet_rest and not is_sleep_action):
            return
        self.y = self.rest_base_y
        self._place_window()
        self._place_sleep_zzz()
        self._schedule_rest_bobble()

    def _play_sleep_interact(self) -> None:
        if self.dragging:
            return
        self._interrupt_current_interaction()
        self._interact_flair("sleep", banter=True)
        self.sleep_interact_active = True
        self.rest_base_y = self.y
        self.state = "rest"
        self._set_image(self.sprites.sleep[1])
        self._show_sleep_zzz()
        self._schedule_rest_bobble()
        tok = self.interaction_token
        self.sleep_interact_end_job = self.root.after(
            SLEEP_INTERACT_MS, lambda t=tok: self._finish_sleep_interact(t)
        )

    def _finish_sleep_interact(self, tok: int | None = None) -> None:
        if tok is not None and tok != self.interaction_token:
            return
        if not self.sleep_interact_active:
            return
        self.sleep_interact_active = False
        self.sleep_interact_end_job = None
        self._stop_rest_bobble()
        self._hide_sleep_zzz()
        self.state = "stand"
        self._set_image(self._current_stand_sprite())
        self._place_window()
        self._add_interact_mood()
        if not self._check_mood_happy():
            self._resume_idle()

    def _start_sleep(self, forced: bool = False) -> None:
        if self.dragging or self.state == "sleep" or self.mode == "quiet":
            return
        if not forced and self.state == "action":
            return
        self.sleep_from_interact = False
        self.sleep_forced = forced
        self._begin_sleep_sequence()
        if forced:
            self._show_toast("好累…先睡一会儿", "#8899cc", duration_ms=2000)

    def _begin_sleep_sequence(self) -> None:
        self.state = "sleep"
        self.action_name = "sleep"
        self.sleep_in_deep = False
        self._hide_sleep_zzz()
        self._set_image(self.sprites.sleep[0])
        self.root.after(SLEEP_TRANSITION_MS, self._sleep_enter_deep)

    def _sleep_enter_deep(self) -> None:
        if self.state != "sleep":
            return
        self.sleep_in_deep = True
        self.sleep_deep_end_ms = int(time.time() * 1000) + SLEEP_INTERACT_MS
        self._set_image(self.sprites.sleep[1])
        self._show_sleep_zzz()
        self._sleep_deep_tick()

    def _sleep_deep_tick(self) -> None:
        if self.state != "sleep" or self.dragging:
            return

        if self.sleep_forced or self.sleep_from_interact:
            self.stamina = min(100, self.stamina + SLEEP_STAMINA_RECOVER)
            self._refresh_panel()

        now_ms = int(time.time() * 1000)
        interact_done = self.sleep_from_interact and now_ms >= self.sleep_deep_end_ms
        forced_done = self.sleep_forced and self.stamina >= SLEEP_WAKE_STAMINA
        if interact_done or forced_done:
            self._sleep_exit_sequence()
            return

        self.root.after(SLEEP_RECOVER_MS, self._sleep_deep_tick)

    def _sleep_exit_sequence(self) -> None:
        if self.state != "sleep":
            return
        self._hide_sleep_zzz()
        self.sleep_in_deep = False
        self._set_image(self.sprites.sleep[0])
        self.root.after(SLEEP_TRANSITION_MS, self._sleep_finish)

    def _sleep_finish(self) -> None:
        if self.state != "sleep":
            return
        self.state = "stand"
        self._set_image(self.sprites.stand)
        self._place_window()
        if self.sleep_from_interact:
            self._add_interact_mood()
        self.sleep_from_interact = False
        self.sleep_forced = False
        if not self._check_mood_happy():
            self._resume_idle()

    def _wake_from_sleep(self) -> None:
        if self.state != "sleep":
            return
        self._hide_sleep_zzz()
        self._stop_call_audio()
        self.sleep_in_deep = False
        self.sleep_from_interact = False
        self.sleep_forced = False
        if self.mode == "quiet":
            self.state = "rest"
            self._set_image(self.sprites.sleep[1])
            self._show_sleep_zzz()
            self._schedule_rest_bobble()
        else:
            self.state = "stand"
            self._set_image(self.sprites.stand)
            self._place_window()
            self._resume_idle()

    def _hide_sleep_zzz(self) -> None:
        if self.sleep_zzz_win and self.sleep_zzz_win.winfo_exists():
            self.sleep_zzz_win.destroy()
        self.sleep_zzz_win = None
        self.sleep_zzz_canvas = None

    def _draw_pixel_z(self, canvas: tk.Canvas, x: int, y: int, size: int, color: str) -> None:
        s = size
        canvas.create_rectangle(x, y, x + s * 2, y + s, fill=color, outline="")
        canvas.create_rectangle(x + s, y + s, x + s * 2, y + s * 2, fill=color, outline="")
        canvas.create_rectangle(x, y + s * 2, x + s * 2, y + s * 3, fill=color, outline="")

    def _show_sleep_zzz(self) -> None:
        self._hide_sleep_zzz()
        pad = 20
        size = self.display_size + pad * 2
        self.sleep_zzz_win = tk.Toplevel(self.root)
        self.sleep_zzz_win.overrideredirect(True)
        self.sleep_zzz_win.attributes("-topmost", False)
        self.sleep_zzz_win.configure(bg="magenta")
        self.sleep_zzz_win.wm_attributes("-transparentcolor", "magenta")
        self.sleep_zzz_canvas = tk.Canvas(
            self.sleep_zzz_win, width=size, height=size, bg="magenta", highlightthickness=0
        )
        self.sleep_zzz_canvas.pack()
        self.zzz_phase = 0
        self._place_sleep_zzz()
        self._animate_sleep_zzz()

    def _place_sleep_zzz(self) -> None:
        if not self.sleep_zzz_win or not self.sleep_zzz_win.winfo_exists():
            return
        pad = 20
        display_y = self.y + self.click_bounce_offset
        self.sleep_zzz_win.geometry(f"+{self.x - pad}+{display_y - pad}")
        self.root.lift()

    def _should_show_zzz(self) -> bool:
        photo = getattr(self.label, "image", None)
        if not photo:
            return False
        return photo in (self.sprites.sleep[0], self.sprites.sleep[1])

    def _animate_sleep_zzz(self) -> None:
        if not self.sleep_zzz_canvas or not self._should_show_zzz():
            self._hide_sleep_zzz()
            return
        canvas = self.sleep_zzz_canvas
        canvas.delete("all")
        size = self.display_size + 40
        px = max(2, self.display_size // 40)
        offset = (self.zzz_phase % 3) * 4
        colors = ("#aabbff", "#8899ee", "#6677dd")
        self._draw_pixel_z(canvas, size - px * 8, px * 2 + offset, px, colors[0])
        self._draw_pixel_z(canvas, size - px * 12, px * 6 + offset, px - 1, colors[1])
        self._draw_pixel_z(canvas, size - px * 16, px * 10 + offset, px - 1, colors[2])
        self.zzz_phase += 1
        self._place_sleep_zzz()
        self.root.after(SLEEP_ZZZ_MS, self._animate_sleep_zzz)

    def _mood_tier_actions(self, mood: int) -> list[str]:
        for threshold, actions in MOOD_EXPRESSION_TIERS:
            if mood >= threshold:
                return actions
        return MOOD_EXPRESSION_TIERS[-1][1]

    def _trigger_mood_action(self, action: str) -> None:
        dispatch = {
            "happy": self._play_happy,
            "like": self._play_expression_like,
            "wink": self._play_expression_wink,
            "hi": lambda: self._play_action("hi"),
            "squat": lambda: self._play_action("squat"),
            "idea": self._play_expression_idea,
            "question": lambda: self._play_expression("question"),
            "sad": self._play_expression_sad,
            "angry": self._play_expression_angry,
        }
        handler = dispatch.get(action)
        if handler:
            handler()

    def _try_mood_random_expression(self) -> bool:
        if self.mode != "free" or self.state != "stand" or self.dragging:
            return False
        if self.mood >= MOOD_LOW_THRESHOLD:
            return False
        if random.random() >= MOOD_RANDOM_CHANCE:
            return False
        actions = self._mood_tier_actions(self.mood)
        before = self.action_name
        self._trigger_mood_action(random.choice(actions))
        return self.state == "action" and self.action_name != before

    def _try_free_random_action(self) -> bool:
        if self.mode != "free" or self.state != "stand" or self.dragging:
            return False
        if random.random() >= FREE_RANDOM_ACTION_CHANCE:
            return False
        pool = [
            lambda: self._play_action("hi"),
            lambda: self._play_action("squat"),
            self._play_expression_wink,
            self._play_expression_like,
            lambda: self._play_expression("question"),
        ]
        before = self.action_name
        random.choice(pool)()
        return self.state == "action" and self.action_name != before

    def _stand_tick(self) -> None:
        if self.dragging or not self._supports_walk_idle() or self.state == "work":
            return

        self.state = "stand"
        self._set_image(self._current_stand_sprite())
        if self.mode == "free":
            if self._try_mood_random_expression():
                return
            if self._try_free_random_action():
                return
        self._schedule_stand_idle()

    def _idle_to_walk(self, tok: int) -> None:
        self.idle_job = None
        if tok != self.interaction_token:
            if self._supports_walk_idle() and self.state == "stand" and not self.dragging:
                self._schedule_stand_idle(min_delay=400, max_delay=1000)
            return
        self._start_walk()

    def _start_walk(self) -> None:
        if self.dragging or not self._supports_walk_idle() or self.state != "stand":
            return

        self.state = "walk"
        self.direction = random.choice(self.DIRECTIONS)
        self.walk_frame = 0
        self.walk_steps_left = random.randint(20, 80)
        self._walk_move()
        self._walk_animate()

    def _walk_animate(self) -> None:
        if self.state != "walk" or self.dragging or not self._supports_walk_idle():
            return

        frames = self._walk_sprites[self.direction]
        self._set_image(frames[self.walk_frame % 2])
        self.walk_frame += 1
        tok = self.interaction_token
        self.walk_anim_job = self.root.after(
            WALK_FRAME_MS, lambda t=tok: self._walk_animate_guarded(t)
        )

    def _walk_animate_guarded(self, tok: int) -> None:
        self.walk_anim_job = None
        if tok != self.interaction_token:
            if self.state == "walk" and self._supports_walk_idle() and not self.dragging:
                self._stand_tick()
            return
        self._walk_animate()

    def _walk_move(self) -> None:
        if self.state != "walk" or self.dragging or not self._supports_walk_idle():
            return

        if self.walk_steps_left <= 0:
            self._stand_tick()
            return

        dx, dy = self.DELTAS[self.direction]
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        next_x = self.x + dx
        next_y = self.y + dy

        if (
            next_x < 0
            or next_x + self.display_size > screen_w
            or next_y < 0
            or next_y + self.display_size > screen_h
        ):
            self._stand_tick()
            return

        self.x = next_x
        self.y = next_y
        self.walk_steps_left -= 1
        self._place_window()
        tok = self.interaction_token
        self.walk_move_job = self.root.after(
            MOVE_INTERVAL_MS, lambda t=tok: self._walk_move_guarded(t)
        )

    def _walk_move_guarded(self, tok: int) -> None:
        if tok != self.interaction_token:
            return
        self.walk_move_job = None
        self._walk_move()

    def _setup_game_overlay(self) -> None:
        pass

    def _game_apply_time_delta(self, delta_ms: int) -> None:
        self.game_start_ms += int(delta_ms)
        left = self._game_time_left_ms()
        if left <= 0:
            self._finish_game()
            return
        sign = "+" if delta_ms > 0 else ""
        sec = abs(delta_ms) // 1000
        self._show_toast(f"时间 {sign}{sec}s", "#88ccff" if delta_ms > 0 else "#ff8844", duration_ms=900)
        self._update_game_hud()

    def _game_handle_special_catch(self, kind: str) -> None:
        if kind == "time_plus":
            self._game_apply_time_delta(GAME_TIME_ITEM_DELTA_MS)
        elif kind == "time_minus":
            self._game_apply_time_delta(-GAME_TIME_ITEM_DELTA_MS)
        elif kind == "dizzy":
            self._start_game_dizzy_stun()

    def _game_spawn_box(self) -> None:
        if self.mode != "game" or self._game_time_left_ms() <= 0:
            return
        sw = self.root.winfo_screenwidth()
        margin = GAME_BOX_SIZE
        bx = random.randint(margin, max(margin, sw - margin))
        kind, food_id = _pick_game_drop_kind()
        size = GAME_BOX_SIZE
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg="magenta")
        win.wm_attributes("-transparentcolor", "magenta")
        canvas = tk.Canvas(win, width=size, height=size, bg="magenta", highlightthickness=0)
        canvas.pack()
        if kind == "food" and food_id:
            px = max(4, size // 8)
            draw_x = max(2, (size - px * 4) // 2)
            draw_y = max(2, (size - px * 4) // 2)
            _draw_pixel_food(canvas, food_id, draw_x, draw_y, px=px)
        else:
            _draw_game_special_item(canvas, kind, size)
        win.geometry(f"+{bx}+{-GAME_BOX_SIZE}")
        base = max(2, float(self._game_box_speed))
        speed = base * random.uniform(GAME_BOX_SPEED_MIN_MULT, GAME_BOX_SPEED_MAX_MULT)
        self.game_boxes.append(
            {
                "x": bx,
                "y": -GAME_BOX_SIZE,
                "win": win,
                "kind": kind,
                "food_id": food_id,
                "speed": speed,
            }
        )
        self.game_spawn_job = self.root.after(self._game_spawn_ms, self._game_spawn_box)

    def _game_tick(self) -> None:
        if self.mode != "game":
            return

        if self._game_time_left_ms() <= 0:
            self._finish_game()
            return

        if not self.game_dizzy:
            mx = self.root.winfo_pointerx()
            my = self.root.winfo_pointery()
            self.x = mx - self.display_size // 2
            self.y = my - self.display_size // 2
            self._clamp_position()
            self._place_window()
        self.root.lift()
        self._update_game_hud()

        sh = self.root.winfo_screenheight()
        pet_cx = self.x + self.display_size // 2
        pet_cy = self.y + self.display_size // 2
        remaining: list[dict] = []
        near_food = False

        for box in self.game_boxes:
            win = box.get("win")
            if not win or not win.winfo_exists():
                continue
            box["y"] += float(box.get("speed", self._game_box_speed))
            win.geometry(f"+{int(box['x'])}+{int(box['y'])}")
            box_cx = box["x"] + GAME_BOX_SIZE // 2
            box_cy = box["y"] + GAME_BOX_SIZE // 2
            dist = math.hypot(box_cx - pet_cx, box_cy - pet_cy)
            kind = box.get("kind", "food")
            if kind == "food" and dist < GAME_NEAR_DIST:
                near_food = True
            if dist < self._game_catch_dist:
                if win.winfo_exists():
                    win.destroy()
                if kind == "food":
                    food_id = box.get("food_id") or random.choice(list(FOODS.keys()))
                    self._add_food_to_inventory(food_id)
                    self.game_catches += 1
                    self.game_score += GAME_SCORE_PER_CATCH
                    if self.game_catches % 5 == 0:
                        self.mood = min(100, self.mood + 1)
                        self._refresh_panel()
                else:
                    self._game_handle_special_catch(kind)
                continue
            if box["y"] > sh + GAME_BOX_SIZE:
                win.destroy()
                if kind == "food":
                    self.game_misses += 1
                    self.game_score = max(0, self.game_score - GAME_PENALTY_MISS)
                continue
            remaining.append(box)

        self.game_boxes = remaining
        self.game_near_food = near_food
        if self.game_dizzy:
            self._set_image(self.sprites.stand)
        else:
            self._set_image(self.sprites.happy if near_food else self.sprites.stand)
        self.game_tick_job = self.root.after(GAME_TICK_MS, self._game_tick)

    def _open_work_menu(self) -> None:
        self._show_sub_menu(
            [
                ("自由", self._start_work_free),
                ("自定义", self._open_work_custom_dialog),
            ],
            offset_x=240,
        )

    def _close_work_custom_dialog(self) -> None:
        if self.work_custom_win and self.work_custom_win.winfo_exists():
            self.work_custom_win.destroy()
        self.work_custom_win = None

    def _open_work_custom_dialog(self) -> None:
        self._hide_main_menu()
        if self.dragging or self.state in ("work", "sleep"):
            return
        self._close_work_custom_dialog()
        win = tk.Toplevel(self.root)
        self.work_custom_win = win
        win.title("自定义工作")
        win.attributes("-topmost", True)
        win.configure(bg=MENU_BG)
        win.protocol("WM_DELETE_WINDOW", self._close_work_custom_dialog)

        frame = tk.Frame(win, bg=MENU_BG, padx=12, pady=10)
        frame.pack()
        tk.Label(frame, text="自定义运送货物", font=PIXEL_FONT, fg=PIXEL_COLOR, bg=MENU_BG).pack(anchor=tk.W)
        tk.Label(
            frame,
            text=f"货物数 {WORK_TOTAL_SETTING_MIN}–{WORK_TOTAL_SETTING_MAX}；起点随机，终点可拖动（中途也能改）",
            font=PIXEL_FONT,
            fg="#aaaaaa",
            bg=MENU_BG,
            wraplength=260,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(4, 6))
        entry_row = tk.Frame(frame, bg=MENU_BG)
        entry_row.pack(fill=tk.X, pady=(0, 8))
        tk.Label(entry_row, text="货物数", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG).pack(side=tk.LEFT)
        entry = tk.Entry(entry_row, width=8, font=PIXEL_FONT)
        entry.pack(side=tk.LEFT, padx=(8, 0))
        entry.insert(0, str(WORK_BOX_TOTAL_DEFAULT))

        def confirm() -> None:
            raw = entry.get().strip()
            try:
                total = int(raw)
            except ValueError:
                self._show_toast("请输入有效货物数", "#ff4444")
                return
            total = max(WORK_TOTAL_SETTING_MIN, min(WORK_TOTAL_SETTING_MAX, total))
            self._close_work_custom_dialog()
            self._start_work_impl(total, flag_movable=True)

        tk.Button(frame, text="开始", command=confirm, font=PIXEL_FONT, bg=MENU_ACTIVE, fg=MENU_FG).pack(anchor=tk.E)
        entry.bind("<Return>", lambda _e: confirm())
        entry.focus_set()
        self._place_panel_popup(win)

    def _start_work_free(self) -> None:
        self._hide_main_menu()
        total = random.randint(WORK_TOTAL_MIN, WORK_TOTAL_MAX)
        # 自由：数量/起点/终点均随机，终点固定不可拖
        self._start_work_impl(total, flag_movable=False)

    def _start_work_impl(self, total: int, *, flag_movable: bool, continuous: bool = False) -> None:
        if self.dragging or self.state in ("work", "sleep"):
            return
        self._interrupt_current_interaction()
        if self.mode == "game":
            self._stop_game_mode()
            self.mode = "free"

        self._hide_main_menu()
        if not continuous:
            self._interact_flair("work", banter=True)

        margin = 80
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        max_x = max(margin, sw - self.display_size - margin)
        max_y = max(margin, sh - self.display_size - margin)

        self.work_start_x = random.randint(margin, max_x)
        self.work_start_y = random.randint(margin, max_y)
        start_cx = self.work_start_x + self.display_size // 2
        start_cy = self.work_start_y + self.display_size // 2
        best_end: tuple[float, int, int] | None = None
        for _ in range(50):
            end_x = random.randint(margin, max_x)
            end_y = random.randint(margin, max_y)
            dist = math.hypot(
                end_x + self.display_size // 2 - start_cx,
                end_y + self.display_size // 2 - start_cy,
            )
            if dist >= WORK_MIN_SPAN_DIST and (best_end is None or dist > best_end[0]):
                best_end = (dist, end_x, end_y)
        if best_end is not None:
            self.work_end_x, self.work_end_y = best_end[1], best_end[2]
        else:
            self.work_end_x = margin if self.work_start_x > (margin + max_x) // 2 else max_x
            self.work_end_y = margin if self.work_start_y > (margin + max_y) // 2 else max_y

        self.work_continuous = continuous
        self.work_total = max(WORK_TOTAL_SETTING_MIN, min(WORK_TOTAL_SETTING_MAX, int(total)))
        self.work_flag_movable = bool(flag_movable)
        self.work_delivered = 0
        self.work_stack = 0
        self.work_local_stack = 0
        self._clear_work_anchored_boxes()
        self.work_boxes_since_banter = 0
        self.work_banter_last_ms = 0
        self.work_has_start_box = True
        self.work_carrying = False
        self.work_phase = "to_start"
        self.work_use_work_sprites = False
        self.work_flag_dragging = False

        self.state = "work"
        self.walk_frame = 0
        self.x = self.work_start_x
        self.y = self.work_start_y
        self._set_image(self.sprites.work_stand)
        self._place_window()
        self._sync_work_overlay()
        if continuous:
            self._maybe_work_mode_banter(force=True)
            self._schedule_work_mode_banter()
            tip = "工作模式：持续运送，可拖动终点旗子；点「结束」停止"
            self._show_toast(tip, PIXEL_COLOR, duration_ms=2800)
        elif flag_movable:
            self._show_toast(
                f"自定义运送：{self.work_total} 批（可拖动终点旗子）",
                PIXEL_COLOR,
                duration_ms=2400,
            )
        else:
            self._show_toast(f"自由运送：{self.work_total} 批", PIXEL_COLOR, duration_ms=2400)
        self._work_move_step()
        if not self.work_animating:
            self.work_animating = True
            self._work_animate()

    def _maybe_work_mode_banter(self, *, force: bool = False) -> None:
        if not self.work_continuous and not force:
            return
        if self.state != "work":
            return
        now_ms = int(time.time() * 1000)
        if self.work_banter_last_ms and now_ms - self.work_banter_last_ms < WORK_MODE_BANTER_COOLDOWN_MS:
            return
        if self.speech_dialog and self.speech_dialog.winfo_exists():
            return
        text = random.choice(WORK_MODE_BANTER)
        self._show_speech_dialog(text, auto_hide_ms=4200, typewriter_ms=TYPEWRITER_MS)
        self.work_banter_last_ms = now_ms

    def _schedule_work_mode_banter(self) -> None:
        if self.work_encourage_job:
            try:
                self.root.after_cancel(self.work_encourage_job)
            except Exception:
                pass
            self.work_encourage_job = None
        if not self.work_continuous:
            return
        lo, hi = WORK_MODE_BANTER_INTERVAL_MS
        delay = max(WORK_MODE_BANTER_COOLDOWN_MS, random.randint(lo, hi))

        def tick() -> None:
            self.work_encourage_job = None
            if self.mode == "work" and self.state == "work":
                self._maybe_work_mode_banter(force=True)
                self._schedule_work_mode_banter()

        self.work_encourage_job = self.root.after(delay, tick)

    def _work_overlay_should_show(self) -> bool:
        return self.state == "work"

    @staticmethod
    def _work_stack_ring_positions(ring: int) -> list[tuple[int, int]]:
        positions: list[tuple[int, int]] = []
        for dx in range(-ring, ring + 1):
            for dy in range(-ring, ring + 1):
                if dx == 0 and dy == 0:
                    continue
                if max(abs(dx), abs(dy)) != ring:
                    continue
                positions.append((dx, dy))

        def sort_key(p: tuple[int, int]) -> tuple[int, int]:
            dx, dy = p
            if dy == 0:
                return 0, abs(dx)
            if dx == 0 and dy < 0:
                return 1, abs(dy)
            return 2, abs(dx) + abs(dy)

        positions.sort(key=sort_key)
        return positions

    def _work_stack_offsets(self, count: int) -> list[tuple[int, int]]:
        if count <= 0:
            return []
        positions: list[tuple[int, int]] = []
        ring = 1
        while len(positions) < count:
            for pos in self._work_stack_ring_positions(ring):
                positions.append(pos)
                if len(positions) >= count:
                    return positions
            ring += 1
        return positions

    def _work_stack_canvas_size(self, stack_count: int) -> tuple[int, int]:
        pad = 40
        step = WORK_STACK_OFFSET
        offsets = self._work_stack_offsets(stack_count)
        max_dx = max((abs(dx) for dx, _ in offsets), default=0)
        max_dy_up = max((-dy for _, dy in offsets if dy < 0), default=0)
        max_dy_down = max((dy for _, dy in offsets if dy > 0), default=0)
        width = pad * 2 + WORK_PROP_SIZE + max_dx * step * 2
        height = pad * 2 + WORK_PROP_SIZE + max_dy_up * step + max_dy_down * step
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        width = min(width, max(WORK_PROP_SIZE + pad * 2, sw - 16))
        height = min(height, max(WORK_PROP_SIZE + pad * 2, sh - 16))
        return width, height

    def _work_box_xy(
        self, index: int, offsets: list[tuple[int, int]], pad: int, canvas_w: int, canvas_h: int
    ) -> tuple[int, int]:
        flag_x = canvas_w // 2
        flag_y = canvas_h - pad
        dx, dy = offsets[index]
        step = WORK_STACK_OFFSET
        return flag_x + dx * step, flag_y + dy * step

    def _hide_work_end_button(self) -> None:
        if self.work_end_btn_win and self.work_end_btn_win.winfo_exists():
            self.work_end_btn_win.destroy()
        self.work_end_btn_win = None

    def _end_continuous_work(self) -> None:
        self._enable_free()

    def _sync_work_end_button(self, overlay_x: int, overlay_y: int, flag_x: int, flag_y: int) -> None:
        if not (self.work_continuous and self.state == "work"):
            self._hide_work_end_button()
            return
        if not self.work_end_btn_win or not self.work_end_btn_win.winfo_exists():
            self.work_end_btn_win = tk.Toplevel(self.root)
            self.work_end_btn_win.overrideredirect(True)
            self.work_end_btn_win.attributes("-topmost", True)
            self.work_end_btn_win.configure(bg=MENU_BG)
            tk.Button(
                self.work_end_btn_win,
                text="结束",
                command=self._end_continuous_work,
                font=PIXEL_FONT,
                bg="#664444",
                fg=MENU_FG,
                relief=tk.FLAT,
                padx=6,
                pady=2,
                cursor="hand2",
            ).pack()
        btn_x = overlay_x + flag_x + WORK_PROP_SIZE // 2 + 8
        btn_y = overlay_y + flag_y - 28
        self.work_end_btn_win.geometry(f"+{btn_x}+{btn_y}")

    def _bind_work_flag_drag(self) -> None:
        if not self.work_canvas:
            return
        self.work_canvas.bind("<ButtonPress-1>", self._work_flag_press)
        self.work_canvas.bind("<B1-Motion>", self._work_flag_motion)
        self.work_canvas.bind("<ButtonRelease-1>", self._work_flag_release)

    def _unbind_work_flag_drag(self) -> None:
        if not self.work_canvas:
            return
        try:
            self.work_canvas.unbind("<ButtonPress-1>")
            self.work_canvas.unbind("<B1-Motion>")
            self.work_canvas.unbind("<ButtonRelease-1>")
        except Exception:
            pass
        self.work_flag_dragging = False

    def _work_flag_press(self, event: tk.Event) -> None:
        if self.state != "work" or not self.work_flag_movable:
            return
        self.work_flag_dragging = True
        self.work_flag_drag_origin = (event.x_root, event.y_root, self.work_end_x, self.work_end_y)

    def _work_flag_motion(self, event: tk.Event) -> None:
        if not self.work_flag_dragging or self.state != "work" or not self.work_flag_movable:
            return
        ox, oy, ex, ey = self.work_flag_drag_origin
        dx = event.x_root - ox
        dy = event.y_root - oy
        margin = 80
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        max_x = max(margin, sw - self.display_size - margin)
        max_y = max(margin, sh - self.display_size - margin)
        self.work_end_x = max(margin, min(max_x, ex + dx))
        self.work_end_y = max(margin, min(max_y, ey + dy))
        self._refresh_work_overlay()

    def _work_flag_release(self, _event: tk.Event | None = None) -> None:
        was_dragging = self.work_flag_dragging
        self.work_flag_dragging = False
        if was_dragging and self.state == "work":
            # 旗子挪走后，新送达的箱子从新位置重新堆起；已送达的留在原位
            self.work_local_stack = 0
            self._refresh_work_overlay()

    def _work_flag_button_down(self) -> bool:
        if sys.platform != "win32":
            return self.work_flag_dragging
        try:
            return bool(ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000)
        except Exception:
            return self.work_flag_dragging

    def _sync_work_overlay(self) -> None:
        if not self._work_overlay_should_show():
            if self.work_overlay and self.work_overlay.winfo_exists():
                self._unbind_work_flag_drag()
                self.work_overlay.destroy()
                self.work_overlay = None
                self.work_canvas = None
            self._update_work_start_box()
            self._hide_work_end_button()
            return
        if not self.work_overlay or not self.work_overlay.winfo_exists():
            self._show_work_overlay()
        else:
            self._refresh_work_overlay()

    def _hide_work_overlay(self) -> None:
        self._unbind_work_flag_drag()
        self._hide_work_end_button()
        if self.work_overlay and self.work_overlay.winfo_exists():
            self.work_overlay.destroy()
        self.work_overlay = None
        self.work_canvas = None
        self.work_flag_dragging = False

    def _show_work_overlay(self) -> None:
        movable = self.work_flag_movable
        self._hide_work_overlay()
        self.work_flag_movable = movable
        width, height = self._work_stack_canvas_size(0)
        self.work_overlay = tk.Toplevel(self.root)
        self.work_overlay.overrideredirect(True)
        self.work_overlay.attributes("-topmost", True)
        self.work_overlay.configure(bg="magenta")
        self.work_overlay.wm_attributes("-transparentcolor", "magenta")
        self.work_overlay.geometry(f"{width}x{height}+0+0")
        self.work_canvas = tk.Canvas(
            self.work_overlay, width=width, height=height, bg="magenta", highlightthickness=0
        )
        self.work_canvas.pack()
        if self.work_flag_movable:
            self._bind_work_flag_drag()
        else:
            self._unbind_work_flag_drag()
        self._refresh_work_overlay()

    def _clear_work_anchored_boxes(self) -> None:
        for win in self.work_anchored_box_wins:
            try:
                if win.winfo_exists():
                    win.destroy()
            except Exception:
                pass
        self.work_anchored_box_wins = []
        self.work_local_stack = 0

    def _spawn_work_anchored_box(self) -> None:
        """在当前旗子位置钉住一箱；之后拖旗不会带走。"""
        if not self._work_mode_config().get("show_stack", True):
            return
        idx = self.work_local_stack
        offsets = self._work_stack_offsets(idx + 1)
        dx, dy = offsets[idx]
        step = WORK_STACK_OFFSET
        flag_sx = self.work_end_x + self.display_size // 2
        flag_sy = self.work_end_y
        box_sx = flag_sx + dx * step
        box_sy = flag_sy + dy * step
        pad = 6
        size = WORK_PROP_SIZE + pad * 2
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg="magenta")
        win.wm_attributes("-transparentcolor", "magenta")
        c = tk.Canvas(win, width=size, height=size, bg="magenta", highlightthickness=0)
        c.pack()
        c.create_image(size // 2, size - pad, image=self.sprites.box_img, anchor=tk.S)
        win.geometry(f"{size}x{size}+{box_sx - size // 2}+{box_sy - size + pad}")
        self.work_anchored_box_wins.append(win)
        self.work_local_stack += 1

    def _refresh_work_overlay(self) -> None:
        if not self.work_canvas or not self.work_overlay:
            return
        pad = 40
        # 已送达箱子用独立窗口钉住，旗子 overlay 只画终点旗
        width, height = self._work_stack_canvas_size(0)
        flag_x = width // 2
        flag_y = height - pad

        self.work_canvas.config(width=width, height=height)
        self.work_canvas.delete("all")
        overlay_x = self.work_end_x + self.display_size // 2 - flag_x
        overlay_y = self.work_end_y - height + pad
        self.work_overlay.geometry(f"{width}x{height}+{overlay_x}+{overlay_y}")
        self.work_canvas.create_image(flag_x, flag_y, image=self.sprites.flag_img, anchor=tk.S)
        label = "终点（可拖）" if self.work_flag_movable else "终点"
        self.work_canvas.create_text(
            flag_x,
            flag_y - WORK_PROP_SIZE - 4,
            text=label,
            fill="#ffee88",
            font=PIXEL_FONT,
            anchor=tk.S,
        )

        self._sync_work_end_button(overlay_x, overlay_y, flag_x, flag_y)
        self._update_work_start_box()

    def _update_work_start_box(self) -> None:
        pad = 40
        size = WORK_PROP_SIZE + pad * 2
        half = WORK_PROP_SIZE // 2
        show_props = self._work_mode_config().get("show_props", True)

        if show_props and self.work_has_start_box and not self.work_carrying:
            sx = self.work_start_x + self.display_size // 2 - half
            sy = self.work_start_y - pad
            sx, sy = self._smart_popup_pos(sx, sy, size, size)
            if not self.work_start_box_win or not self.work_start_box_win.winfo_exists():
                self.work_start_box_win = tk.Toplevel(self.root)
                self.work_start_box_win.overrideredirect(True)
                self.work_start_box_win.attributes("-topmost", False)
                self.work_start_box_win.configure(bg="magenta")
                self.work_start_box_win.wm_attributes("-transparentcolor", "magenta")
                c = tk.Canvas(
                    self.work_start_box_win,
                    width=size,
                    height=size,
                    bg="magenta",
                    highlightthickness=0,
                )
                c.pack()
                c.create_image(half, size - pad, image=self.sprites.box_img, anchor=tk.S)
            self.work_start_box_win.geometry(f"{size}x{size}+{sx}+{sy}")
        elif self.work_start_box_win and self.work_start_box_win.winfo_exists():
            self.work_start_box_win.destroy()
            self.work_start_box_win = None

    def _work_animate(self) -> None:
        if self.state != "work":
            self.work_animating = False
            return
        if self.dragging:
            self.root.after(WALK_FRAME_MS, self._work_animate)
            return
        sprite_map = self._work_sprites if self.work_use_work_sprites else self._walk_sprites
        frames = sprite_map[self.direction]
        self._set_image(frames[self.walk_frame % 2])
        self.walk_frame += 1
        self.root.after(WALK_FRAME_MS, self._work_animate)

    def _work_move_step(self) -> None:
        if self.state != "work":
            return
        if self.dragging:
            self.root.after(WORK_MOVE_INTERVAL_MS, self._work_move_step)
            return
        if self.work_flag_dragging:
            if not self._work_flag_button_down():
                self._work_flag_release()
            else:
                self.root.after(WORK_MOVE_INTERVAL_MS, self._work_move_step)
                return

        if self.work_phase == "to_end":
            tx = self.work_end_x + self.display_size // 2
            ty = self.work_end_y + self.display_size // 2
            self.work_use_work_sprites = True
        elif self.work_phase == "to_start":
            tx = self.work_start_x + self.display_size // 2
            ty = self.work_start_y + self.display_size // 2
            self.work_use_work_sprites = False
        elif self.work_phase == "finish":
            self._finish_work()
            return
        else:
            return

        if self._dist_to(tx, ty) <= WORK_ARRIVE_DIST:
            self._work_arrived()
            return

        self.direction = self._direction_to(tx, ty)
        dx, dy = self.DELTAS[self.direction]
        self.x += dx * (WORK_MOVE_STEP // MOVE_STEP)
        self.y += dy * (WORK_MOVE_STEP // MOVE_STEP)
        self._clamp_position()
        self._place_window()
        # 终点旗子不随小人移动，行走中不必每帧重绘 overlay（否则堆箱后会卡死）
        self.root.after(WORK_MOVE_INTERVAL_MS, self._work_move_step)

    def _work_arrived(self) -> None:
        if self.work_phase == "to_start":
            if not self.work_continuous and self.work_delivered >= self.work_total and not self.work_carrying:
                self.work_phase = "finish"
                self._work_move_step()
                return
            if not self.work_carrying:
                self.work_carrying = True
                self.work_has_start_box = False
                self._sync_work_overlay()
            self.work_phase = "to_end"
        elif self.work_phase == "to_end":
            if self.work_carrying:
                self.work_carrying = False
                self.work_delivered += 1
                self.work_stack += 1
                self._spawn_work_anchored_box()
                self.stamina = min(100, self.stamina + 2)
                self.mood = min(100, self.mood + 1)
                self._refresh_panel()
            if self.work_continuous:
                self.work_has_start_box = True
                self.work_phase = "to_start"
                self._sync_work_overlay()
            elif self.work_delivered >= self.work_total:
                self.work_phase = "finish"
                self._sync_work_overlay()
            else:
                self.work_has_start_box = True
                self.work_phase = "to_start"
                self._sync_work_overlay()
        self._work_move_step()

    def _finish_work(self) -> None:
        if self.state != "work" or self.work_continuous:
            return
        if self.mode == "work":
            self.mode = "free"
        self._stop_work_mode()
        self.state = "stand"
        self._play_happy()

    def _hide_rain_fx(self) -> None:
        if self.rain_fx_win and self.rain_fx_win.winfo_exists():
            self.rain_fx_win.destroy()
        self.rain_fx_win = None
        self.rain_fx_canvas = None
        self.rain_drops.clear()

    def _place_rain_fx(self) -> None:
        if not self.rain_fx_win or not self.rain_fx_win.winfo_exists():
            return
        pad = 20
        display_y = self.y + self.click_bounce_offset
        self.rain_fx_win.geometry(f"+{self.x - pad}+{display_y - pad - 30}")
        self.root.lift()

    def _show_rain_fx(self) -> None:
        self._hide_rain_fx()
        pad = 20
        size = self.display_size + pad * 2
        self.rain_fx_win = tk.Toplevel(self.root)
        self.rain_fx_win.overrideredirect(True)
        self.rain_fx_win.attributes("-topmost", False)
        self.rain_fx_win.configure(bg="magenta")
        self.rain_fx_win.wm_attributes("-transparentcolor", "magenta")
        self.rain_fx_canvas = tk.Canvas(
            self.rain_fx_win, width=size, height=size, bg="magenta", highlightthickness=0
        )
        self.rain_fx_canvas.pack()
        px = max(2, self.display_size // 40)
        self.rain_drops = [
            {"x": random.randint(0, size), "y": random.randint(-size, size // 2), "speed": random.randint(2, 5)}
            for _ in range(18)
        ]
        self.rain_phase = 0
        self._place_rain_fx()
        self._animate_rain_fx()

    def _animate_rain_fx(self) -> None:
        if not self.rain_fx_canvas or self.action_name != "sad":
            return
        canvas = self.rain_fx_canvas
        size = canvas.winfo_width() or self.display_size + 40
        canvas.delete("all")
        px = max(2, self.display_size // 40)
        for drop in self.rain_drops:
            drop["y"] += drop["speed"]
            if drop["y"] > size:
                drop["y"] = random.randint(-20, 0)
                drop["x"] = random.randint(0, size)
            canvas.create_rectangle(
                drop["x"], drop["y"], drop["x"] + px, drop["y"] + px * 2, fill="#6699ff", outline=""
            )
        self._place_rain_fx()
        self.root.after(80, self._animate_rain_fx)

    def _hide_bulb_fx(self) -> None:
        if self.bulb_glow_job:
            self.root.after_cancel(self.bulb_glow_job)
            self.bulb_glow_job = None
        if self.bulb_fx_win and self.bulb_fx_win.winfo_exists():
            self.bulb_fx_win.destroy()
        self.bulb_fx_win = None
        self.bulb_fx_canvas = None

    def _bulb_draw_y(self, size: int, px: int) -> int:
        return max(4, size - px * 5 - self.display_size // 8)

    def _place_bulb_fx(self) -> None:
        if not self.bulb_fx_win or not self.bulb_fx_win.winfo_exists():
            return
        pad = 8
        display_y = self.y + self.click_bounce_offset
        px = max(4, BULB_FX_SIZE // 16)
        bulb_y = self._bulb_draw_y(BULB_FX_SIZE, px)
        win_y = max(0, display_y - bulb_y - BULB_HEAD_GAP - BULB_OFFSET_DOWN)
        self.bulb_fx_win.geometry(
            f"+{max(0, self.x + self.display_size // 2 - BULB_FX_SIZE // 2 + pad)}+{win_y}"
        )
        self.root.lift()

    def _animate_bulb_glow(self) -> None:
        if not self.bulb_fx_canvas or self.action_name != "idea":
            return
        size = BULB_FX_SIZE
        px = max(4, size // 16)
        bulb_x = max(4, (size - px * 4) // 2 - px)
        bulb_y = self._bulb_draw_y(size, px)
        glow = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(self.bulb_glow_phase * 0.22))
        self.bulb_fx_canvas.delete("all")
        _draw_pixel_bulb(self.bulb_fx_canvas, bulb_x, bulb_y, px=px, glow=glow)
        self.bulb_glow_phase += 1
        self._place_bulb_fx()
        self.bulb_glow_job = self.root.after(BULB_GLOW_MS, self._animate_bulb_glow)

    def _show_bulb_fx(self) -> None:
        self._hide_bulb_fx()
        size = BULB_FX_SIZE
        self.bulb_fx_win = tk.Toplevel(self.root)
        self.bulb_fx_win.overrideredirect(True)
        self.bulb_fx_win.attributes("-topmost", False)
        self.bulb_fx_win.configure(bg="magenta")
        self.bulb_fx_win.wm_attributes("-transparentcolor", "magenta")
        self.bulb_fx_canvas = tk.Canvas(
            self.bulb_fx_win, width=size, height=size, bg="magenta", highlightthickness=0
        )
        self.bulb_fx_canvas.pack()
        px = max(6, size // 14)
        bulb_x = max(4, (size - px * 4) // 2 - px)
        bulb_y = self._bulb_draw_y(size, px)
        _draw_pixel_bulb(self.bulb_fx_canvas, bulb_x, bulb_y, px=px)
        self._place_bulb_fx()

    def _play_reminder_sound(self) -> None:
        sound = _get_reminder_sound()
        self._play_sound_with_volume(sound, "sfx")

    def _reminder_tick(self) -> None:
        if not self._alive():
            return
        if not self._startup_ready:
            self._safe_after(REMINDER_CHECK_MS, self._reminder_tick)
            return
        today = datetime.now().strftime("%Y-%m-%d")
        if getattr(self, "_reminder_day", "") != today:
            self._reminder_day = today
            self.triggered_reminders_today.clear()
        now_hm = datetime.now().strftime("%H:%M")
        weekday = datetime.now().weekday()
        for item in self.schedules:
            rid = item.get("id", "")
            if item.get("time") != now_hm or rid in self.triggered_reminders_today:
                continue
            if not _schedule_matches_today(item, weekday):
                continue
            self.triggered_reminders_today.add(rid)
            text = item.get("text", "提醒")
            day_label = _format_schedule_weekdays(item)
            self._play_reminder_sound()
            self._show_speech_dialog(
                f"⏰ 日程提醒（{day_label}）\n{text}",
                auto_hide_ms=10000,
                color=REMINDER_COLOR,
            )
        self._safe_after(REMINDER_CHECK_MS, self._reminder_tick)

    def _open_schedule_manager(self) -> None:
        self._hide_main_menu()
        if self.schedule_win and self.schedule_win.winfo_exists():
            self.schedule_win.destroy()
            self.schedule_win = None
            return

        self.schedule_win = tk.Toplevel(self.root)
        self.schedule_win.title("日程提醒")
        self.schedule_win.attributes("-topmost", True)
        self.schedule_win.configure(bg=MENU_BG)

        _, frame = _pack_fixed_scroll_panel(self.schedule_win)

        tk.Label(frame, text="日程提醒", font=PIXEL_FONT, fg=PIXEL_COLOR, bg=MENU_BG).pack(anchor=tk.W)
        row = tk.Frame(frame, bg=MENU_BG)
        row.pack(fill=tk.X, pady=(8, 4))
        tk.Label(row, text="时间", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG).pack(side=tk.LEFT)
        time_entry = tk.Entry(row, width=8, font=PIXEL_FONT)
        time_entry.pack(side=tk.LEFT, padx=4)
        time_entry.insert(0, datetime.now().strftime("%H:%M"))
        tk.Label(row, text="事项", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG).pack(side=tk.LEFT, padx=(8, 0))
        text_entry = tk.Entry(row, width=18, font=PIXEL_FONT)
        text_entry.pack(side=tk.LEFT, padx=4)

        weekday_row = tk.Frame(frame, bg=MENU_BG)
        weekday_row.pack(fill=tk.X, pady=(0, 4))
        tk.Label(weekday_row, text="星期", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG).pack(side=tk.LEFT)
        weekday_vars = [tk.BooleanVar(value=True) for _ in range(7)]
        weekday_box = tk.Frame(weekday_row, bg=MENU_BG)
        weekday_box.pack(side=tk.LEFT, padx=4)
        for idx, label in enumerate(WEEKDAY_LABELS):
            tk.Checkbutton(
                weekday_box,
                text=label[-1],
                variable=weekday_vars[idx],
                font=PIXEL_FONT,
                fg=MENU_FG,
                bg=MENU_BG,
                activebackground=MENU_BG,
                activeforeground=MENU_FG,
                selectcolor=MENU_ACTIVE,
            ).pack(side=tk.LEFT, padx=1)

        def set_all_weekdays(checked: bool) -> None:
            for var in weekday_vars:
                var.set(checked)

        def select_weekdays(indices: tuple[int, ...]) -> None:
            set_all_weekdays(False)
            for i in indices:
                weekday_vars[i].set(True)

        quick_row = tk.Frame(frame, bg=MENU_BG)
        quick_row.pack(fill=tk.X, pady=(0, 4))
        tk.Button(
            quick_row, text="每天", command=lambda: set_all_weekdays(True), font=PIXEL_FONT, bg=MENU_ACTIVE, fg=MENU_FG
        ).pack(side=tk.LEFT, padx=(44, 4))
        tk.Button(
            quick_row, text="工作日", command=lambda: select_weekdays((0, 1, 2, 3, 4)), font=PIXEL_FONT, bg=MENU_ACTIVE, fg=MENU_FG
        ).pack(side=tk.LEFT, padx=4)
        tk.Button(
            quick_row, text="周末", command=lambda: select_weekdays((5, 6)), font=PIXEL_FONT, bg=MENU_ACTIVE, fg=MENU_FG
        ).pack(side=tk.LEFT, padx=4)

        list_frame = tk.Frame(frame, bg=MENU_BG)
        list_frame.pack(fill=tk.BOTH, pady=4)

        def refresh_list() -> None:
            for w in list_frame.winfo_children():
                w.destroy()
            for item in self.schedules:
                line = tk.Frame(list_frame, bg=MENU_BG)
                line.pack(fill=tk.X, pady=1)
                tk.Label(
                    line,
                    text=f"{item.get('time', '??:??')} [{_format_schedule_weekdays(item)}]  {item.get('text', '')}",
                    font=PIXEL_FONT,
                    fg=MENU_FG,
                    bg=MENU_BG,
                ).pack(side=tk.LEFT)
                rid = item.get("id")

                def delete(r=rid) -> None:
                    self.schedules = [s for s in self.schedules if s.get("id") != r]
                    _save_schedules(self.schedules)
                    refresh_list()

                tk.Button(line, text="删", command=delete, font=PIXEL_FONT, bg=MENU_BG, fg="#ff6666").pack(
                    side=tk.RIGHT
                )

        def add_item() -> None:
            t = _normalize_schedule_time(time_entry.get())
            txt = text_entry.get().strip()
            if not t:
                self._show_toast("请填写有效时间，如 09:30", "#ff8844")
                return
            if not txt:
                self._show_toast("请填写提醒事项", "#ff8844")
                return
            selected_days = [i for i, var in enumerate(weekday_vars) if var.get()]
            if not selected_days:
                self._show_toast("请至少选择一个星期", "#ff8844")
                return
            weekdays = None if len(selected_days) >= 7 else selected_days
            entry = {"id": str(uuid4()), "time": t, "text": txt}
            if weekdays is not None:
                entry["weekdays"] = weekdays
            try:
                self.schedules.append(entry)
                _save_schedules(self.schedules)
            except OSError as exc:
                self._show_toast(f"保存失败：{exc}", "#ff6666")
                self.schedules.pop()
                return
            text_entry.delete(0, tk.END)
            refresh_list()
            self._show_toast("日程已添加", PIXEL_COLOR)

        tk.Button(frame, text="添加", command=add_item, font=PIXEL_FONT, bg=MENU_ACTIVE, fg=MENU_FG).pack(pady=4)
        time_entry.bind("<Return>", lambda _e: add_item())
        text_entry.bind("<Return>", lambda _e: add_item())
        refresh_list()
        self._place_panel_popup(self.schedule_win)

    def _place_ai_chat(self) -> None:
        if not self.ai_chat_win or not self.ai_chat_win.winfo_exists():
            return
        self._place_panel_popup(self.ai_chat_win)

    def _is_ai_chat_widget(self, widget: tk.Misc | None) -> bool:
        if widget is None or not self.ai_chat_win:
            return False
        w: tk.Misc | None = widget
        while w is not None:
            if w == self.ai_chat_win:
                return True
            w = w.master
        return False

    def _cancel_ai_chat_close(self) -> None:
        if self.ai_chat_close_job:
            self.root.after_cancel(self.ai_chat_close_job)
            self.ai_chat_close_job = None

    def _close_ai_chat(self) -> None:
        self._cancel_ai_chat_close()
        if self.ai_reply_job:
            self.root.after_cancel(self.ai_reply_job)
            self.ai_reply_job = None
        if self.ai_chat_win and self.ai_chat_win.winfo_exists():
            self.ai_chat_win.destroy()
        self.ai_chat_win = None
        self.ai_input = None
        self._hide_speech_dialog()

    def _schedule_ai_chat_close(self) -> None:
        if not self.ai_chat_win or not self.ai_chat_win.winfo_exists():
            return
        self._cancel_ai_chat_close()
        self.ai_chat_close_job = self.root.after(AI_CHAT_IDLE_MS, self._close_ai_chat_idle)

    def _close_ai_chat_idle(self) -> None:
        self.ai_chat_close_job = None
        if not self.ai_chat_win or not self.ai_chat_win.winfo_exists():
            return
        focus = self.root.focus_get()
        if self._is_ai_chat_widget(focus):
            return
        self._close_ai_chat()

    def _ai_chat_focus_out(self, _event=None) -> None:
        self.root.after(80, self._check_ai_chat_focus)

    def _check_ai_chat_focus(self) -> None:
        if not self.ai_chat_win or not self.ai_chat_win.winfo_exists():
            return
        focus = self.root.focus_get()
        if self._is_ai_chat_widget(focus):
            self._cancel_ai_chat_close()
            return
        self._schedule_ai_chat_close()

    def _ai_chat_focus_in(self, _event=None) -> None:
        self._cancel_ai_chat_close()

    def _toggle_ai_chat(self) -> None:
        self._hide_main_menu()
        if self.ai_chat_win and self.ai_chat_win.winfo_exists():
            self._close_ai_chat()
            return

        self.ai_chat_win = tk.Toplevel(self.root)
        self.ai_chat_win.overrideredirect(True)
        self.ai_chat_win.attributes("-topmost", True)
        self.ai_chat_win.configure(bg="#111122")

        border = tk.Frame(self.ai_chat_win, bg=PIXEL_COLOR, padx=1, pady=1)
        border.pack()
        inner = tk.Frame(border, bg="#111122", padx=6, pady=4)
        inner.pack()

        self.ai_input = tk.Entry(inner, width=22, font=PIXEL_FONT, bg="#222233", fg=PIXEL_COLOR, insertbackground=PIXEL_COLOR)
        self.ai_input.pack(side=tk.LEFT, padx=(0, 4))
        self.ai_input.bind("<Return>", lambda _e: self._send_ai_message())
        self.ai_input.bind("<FocusOut>", self._ai_chat_focus_out, add="+")
        self.ai_input.bind("<FocusIn>", self._ai_chat_focus_in, add="+")

        send_btn = tk.Button(
            inner,
            text="发送",
            command=self._send_ai_message,
            font=PIXEL_FONT,
            bg=MENU_ACTIVE,
            fg=MENU_FG,
            relief=tk.FLAT,
            padx=6,
        )
        send_btn.pack(side=tk.LEFT)
        send_btn.bind("<FocusOut>", self._ai_chat_focus_out, add="+")
        send_btn.bind("<FocusIn>", self._ai_chat_focus_in, add="+")
        self._place_ai_chat()
        self.ai_input.focus_set()

    def _show_ai_reply(self, reply: str) -> None:
        self.ai_reply_job = None
        if not self.ai_chat_win or not self.ai_chat_win.winfo_exists():
            return
        self._show_speech_dialog(reply, auto_hide_ms=AI_DIALOG_HIDE_MS)

    def _send_ai_message(self) -> None:
        if not self.ai_input:
            return
        text = self.ai_input.get().strip()
        if not text:
            return
        self.ai_input.delete(0, tk.END)
        self._cancel_ai_chat_close()
        self._show_speech_dialog(f"你：{text}", auto_hide_ms=AI_DIALOG_HIDE_MS)
        if self.ai_reply_job:
            try:
                self.root.after_cancel(self.ai_reply_job)
            except Exception:
                pass
            self.ai_reply_job = None

        def work() -> None:
            try:
                reply = self._ai_reply(text)
            except Exception as exc:
                err = str(exc).strip() or "未知错误"
                if len(err) > 60:
                    err = err[:57] + "..."
                reply = f"诶…AI 连接失败了：{err}\n请检查 ai_config.json（推荐千问 DashScope）或网络~"

            def show() -> None:
                if not self._alive():
                    return
                self._show_ai_reply(reply)

            if self._alive():
                try:
                    self.root.after(0, show)
                except tk.TclError:
                    pass

        threading.Thread(target=work, daemon=True).start()

    def _ai_reply(self, user_text: str) -> str:
        config = _load_ai_config()
        api_key = config.get("api_key", "")
        if api_key:
            try:
                reply = self._ai_request(user_text, config, api_key)
                self.ai_history.append({"role": "user", "content": user_text})
                self.ai_history.append({"role": "assistant", "content": reply})
                self.ai_history = self.ai_history[-AI_HISTORY_MAX * 2 :]
                return reply
            except Exception as exc:
                err = str(exc).strip() or "未知错误"
                if len(err) > 60:
                    err = err[:57] + "..."
                return f"诶…AI 连接失败了：{err}\n请检查 ai_config.json（推荐千问 DashScope）或网络~"
        return self._ai_fallback(user_text)

    def _ai_request(self, user_text: str, config: dict, api_key: str) -> str:
        base_url = config.get("base_url", AI_DEFAULT_CONFIG["base_url"]).rstrip("/")
        model = config.get("model", AI_DEFAULT_CONFIG["model"])
        temperature = float(config.get("temperature", AI_DEFAULT_CONFIG["temperature"]))
        messages: list[dict[str, str]] = [{"role": "system", "content": AI_SYSTEM_PROMPT}]
        messages.extend(self.ai_history[-AI_HISTORY_MAX * 2 :])
        messages.append({"role": "user", "content": user_text})
        payload = json.dumps(
            {
                "model": model,
                "messages": messages,
                "max_tokens": 220,
                "temperature": temperature,
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if api_key and api_key.lower() != "ollama":
            headers["Authorization"] = f"Bearer {api_key}"
        req = urllib.request.Request(
            f"{base_url}/chat/completions",
            data=payload,
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()

    def _ai_fallback(self, user_text: str) -> str:
        preset = self._match_preset_dialog(user_text)
        if preset:
            return preset
        if any(k in user_text for k in ("你好", "嗨", "hello")):
            return random.choice(
                [
                    "诶，你好呀！今天也要一起加油哦~",
                    "哇，你来啦！有什么想聊的吗？",
                    "嗨嗨~我在呢，随时都可以找我哦！",
                ]
            )
        if any(k in user_text for k in ("累", "困", "睡")):
            return random.choice(
                [
                    "嗯…累了就歇一歇吧，别硬撑哦。",
                    "诶？辛苦啦…要不要睡一会儿？我在这边守着你。",
                    "困了就休息嘛，身体最重要啦！",
                ]
            )
        if any(k in user_text for k in ("吃", "饿", "食物")):
            return random.choice(
                [
                    "饿了呀？先去模式→游戏接食物，再来互动里喂我！",
                    "诶——想吃东西的话，玩游戏能接到各种食物哦！",
                    "哇，说到吃的我就来劲了…不过得先玩游戏接到才行~",
                ]
            )
        if any(k in user_text for k in ("工作", "上班", "任务")):
            return random.choice(
                [
                    "工作啊…互动里的「工作」可以陪我运送货物，一起加油吧！",
                    "诶，要干活了吗？记得也给自己留点休息时间哦。",
                    "嗯嗯，旧货店这边也要忙起来了呢~",
                ]
            )
        if any(k in user_text for k in ("开心", "高兴", "棒")):
            return random.choice(
                [
                    "哇——太好了！看到你开心我也超开心的！",
                    "诶嘿嘿，这种时候最棒啦~",
                    "耶！今天也是好日子呢！",
                ]
            )
        if any(k in user_text for k in ("伤心", "难过", "哭")):
            return random.choice(
                [
                    "诶…别难过啦，我会一直在这陪你的。",
                    "嗯…没关系的，慢慢说，我听着呢。",
                    "呜…看到你难过我也心里揪揪的…抱抱！",
                ]
            )
        if "?" in user_text or "？" in user_text or any(k in user_text for k in ("什么", "怎么", "为什么")):
            return random.choice(
                [
                    "诶？这个问题…让我想想哦！",
                    "嗯——有意思！值得好好琢磨一下呢。",
                    "哇，问到点上了…我也很好奇答案！",
                ]
            )
        if any(k in user_text for k in ("游戏", "玩")):
            return random.choice(
                [
                    "玩游戏接食物超好玩的！Esc 可以随时退出哦~",
                    "诶，要一起玩吗？模式里选游戏就行啦！",
                    "面板→小游戏里还有打字和背单词哦~",
                ]
            )
        if any(k in user_text for k in ("打字", "练习", "键盘")):
            return random.choice(
                [
                    "打字练习在面板→小游戏里！看释义敲单词~",
                    "诶，来练练单词吧！模式→游戏→背单词就行~",
                ]
            )
        if any(k in user_text for k in ("单词", "背词", "词库", "学习")):
            item = self._pick_vocab_word()
            if item:
                return random.choice(
                    [
                        f"来背这个：{item['word']} — {item.get('meaning', '')}",
                        "面板→小游戏→背单词，选对了心情会变好哦~",
                    ]
                )
            return "词库还没准备好，请把 JSON   词库放进 word_banks 文件夹~"
        return random.choice(
            [
                "嗯嗯，我在听呢~",
                "诶，原来如此！",
                "哇——知道了知道了！",
                "好的好的，随时叫我哦~",
                "诶嘿嘿，有意思~",
            ]
        )

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    DesktopPet().run()
