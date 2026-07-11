"""桌面桌宠 v1.2：四大模块菜单、打电话对话框、跟随鼠标、面板与大小调节。"""

import array
import ctypes
import json
import math
import os
import random
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog
import urllib.error
import urllib.request
from ctypes import wintypes
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageTk

ASSET_DIR = Path(__file__).parent
GALLERY_DIR = ASSET_DIR / "gallery"
GALLERY_CONFIG_FILE = GALLERY_DIR / "gallery.json"
GALLERY_THUMB_SIZE = 96
GALLERY_PREVIEW_SIZE = 280
GALLERY_COLS = 3
CALL_AUDIO_SRC = Path(r"C:\Users\36255\Desktop\call.mp3.mp4")
CALL_AUDIO_WAV = ASSET_DIR / "call_cache.wav"
TYPE_AUDIO_SRC = Path(r"C:\Users\36255\Desktop\type.mp4")
TYPE_AUDIO_WAV = ASSET_DIR / "type_cache.wav"
TYPE_TICK_WAV = ASSET_DIR / "type_tick.wav"
MUSIC_AUDIO_SRC = Path(r"C:\Users\36255\Desktop\aicatch.mp4")
MUSIC_AUDIO_WAV = ASSET_DIR / "music_aicatch_cache.wav"
MUSIC_CONFIG_FILE = ASSET_DIR / "music_config.json"
DEFAULT_SIZE = 128
SIZE_PRESETS: dict[str, int] = {"小": 96, "中": 128, "大": 176}

WALK_FRAME_MS = 180
MOVE_INTERVAL_MS = 50
MOVE_STEP = 3
FOLLOW_MOVE_STEP = 4
FOLLOW_MOVE_INTERVAL_MS = 40
ACTION_FRAME_MS = 180
INTERACT_DURATION_MS = 3000
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
    "wink": 2800,
    "like": 3200,
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

STAMINA_TICK_MS = 15000
STAMINA_DECAY = 1
INTERACT_MOOD_GAIN = 2
LOW_STAMINA_THRESHOLD = 30
HUNGER_REMINDER_COOLDOWN_MS = 45000
MOOD_HAPPY_THRESHOLD = 95
MOOD_AFTER_HAPPY = 85
TOAST_DURATION_MS = 2500
PANEL_AUTO_CLOSE_MS = 5000

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

WORK_ARRIVE_DIST = 18
WORK_TOTAL_MIN = 3
WORK_TOTAL_MAX = 8
WORK_BOX_TOTAL_DEFAULT = 5
WORK_TOTAL_SETTING_MIN = 1
WORK_TOTAL_SETTING_MAX = 30
WORK_PROP_SIZE = 104
WORK_STACK_OFFSET = 22
WORK_STACK_COLUMN_MAX = 6
WORK_STACK_COL_OFFSET = 30
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
BULB_HEAD_GAP = 2
BULB_GLOW_MS = 160
FOLLOW_DIZZY_SPIN_STEPS = 8
FOLLOW_DIZZY_STAND_MS = 1500
FOLLOW_DIZZY_TEXT = "我晕了……"
FOLLOW_DIR_ORDER = ("front", "right", "back", "left")
MOOD_LOW_THRESHOLD = 40
MOOD_RANDOM_CHANCE = 0.09
MOOD_TIER_LABELS: list[tuple[int, str, str]] = [
    (85, "极好", "#ff88cc"),
    (65, "开心", "#88dd88"),
    (45, "普通", "#4488ff"),
    (25, "低落", "#ffaa44"),
    (0, "沮丧", "#ff4444"),
]
WORK_MOVE_STEP = MOVE_STEP * 3
WORK_MOVE_INTERVAL_MS = max(8, MOVE_INTERVAL_MS // 3)
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
TYPING_MOOD_FILES: dict[str, str] = {
    "D": "sad1.jpg",
    "C": "squat.jpg",
    "B": "stand.jpg",
    "A": "happy.jpg",
    "S": "like.jpg",
}
VOCAB_DAILY_MAX = 3
MULTI_CLICK_WINDOW_MS = 850
SIZE_LOAD_ANIM_MS = 30
SIZE_LOAD_MIN_MS = 72
SIZE_LOAD_MIN_CACHED_MS = 44
COMPANION_LOAD_MIN_MS = 72
COMPANION_LOAD_MIN_CACHED_MS = 44
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
EXIT_DISSOLVE_MS = 45
EXIT_DISSOLVE_FRAMES = 36
EXIT_DISSOLVE_PX_SCALE = 5
EXIT_DISSOLVE_MAIN_COLORS = ("#4488ff", "#88ccff", "#ff88cc", "#ffffff", "#66aaff")
EXIT_DISSOLVE_COMPANION_COLORS = ("#44cc88", "#88ffcc", "#ffdd44", "#ccffaa", "#66dd99")
EXPOSE_RING_PAD = 36
EXPOSE_BLUE_SPAN = 60
EXPOSE_POINTER_SPEED = 4.5
EXPOSE_SPEED_STREAK_MULT = 0.12
EXPOSE_SPEED_TICK_BOOST = 0.015
EXPOSE_POINTER_MAX_SPEED = 15.0
GAME_COUNTDOWN_STEP_MS = 900
MUSIC_WAVE_MS = 60
FOOD_INVENTORY_FILE = ASSET_DIR / "food_inventory.json"
ADULT_CONTENT_TEXT = "我只是像素哦，更多精彩内容请在正版游戏《戏剧性谋杀》中解锁"
RESERVED_TOAST = "敬请期待~"

SCHEDULE_FILE = ASSET_DIR / "schedules.json"
AI_CONFIG_FILE = ASSET_DIR / "ai_config.json"
REMINDER_CHECK_MS = 15000
REMINDER_COLOR = "#ff4444"
WEEKDAY_LABELS = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")

# 打包两个版本：有编号版 PET_ID_FEATURE=True；无编号版改为 False
PET_ID_FEATURE = True
APP_CONFIG_FILE = ASSET_DIR / "app_config.json"
PET_PROFILE_FILE = ASSET_DIR / "pet_profile.json"
DIARY_FILE = ASSET_DIR / "diary.json"
VOCAB_FILE = ASSET_DIR / "vocab.json"
WORD_BANKS_DIR = ASSET_DIR / "word_banks"
PET_ID_REGISTRY_FILE = ASSET_DIR / "pet_id_registry.json"
FONT_SIZE_PRESETS: dict[str, int] = {"小": 10, "中": 12, "大": 14, "特大": 16}
ABOUT_DEVELOPER = "翛然而往"
ABOUT_TEXT = (
    "游戏《DRAMAtical Murder》中的主人公 濑良垣苍叶，"
    "是Nitro CHiRAL旗下18禁BL游戏《DRAMAtical Murder》"
    "（已动画化）的主人公。这位日本青年是东江实验品、"
    "双生哥哥「生」的弟弟，体内承载自制力人格「莲」。\n\n"
    "性格乐观热心，但长期受不明头痛困扰。"
    "幼年遭多惠救出实验室，由养父母抚养，"
    "因长发常被误认女性而结识青梅竹马红雀。"
    "16岁拾获莲的智能机体后，莲为压制暴走的人格入驻其中，"
    "形成独特共生关系。经历从实验室孤儿到被迫卷入"
    "莱姆虚拟对战的转变，头痛真相揭露后逐步掌控能力，"
    "最终在冲突中完成人格整合。\n\n"
    "本桌宠为同人像素陪伴程序。\n\n"
    f"桌宠开发者：{ABOUT_DEVELOPER}\n"
    "感谢下载与陪伴 ♪"
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
        "fight_enemy_mult": 1.35,
        "fight_player_mult": 0.9,
    },
}

OPERATION_GUIDE_TEXT = (
    "【Vpet 操作说明】\n\n"
    "▶ 基本\n"
    "  右键桌宠 → 四大菜单（模式/面板/互动/系统）\n"
    "  左键拖拽 → 移动桌宠（把手区域）\n"
    "  Esc → 退出游戏/音乐/AI/子窗口，回自由模式\n"
    "  F1 → 随时打开本说明\n\n"
    "▶ 模式\n"
    "  跟随/自由/漫步/睡眠/游戏▶(采集·打字·背单词)/音乐\n\n"
    "▶ 系统\n"
    "  我的（编号/日记/日程）· 设置（大小/字体/声音）· 难度\n\n"
    "▶ 面板\n"
    "  智能伴侣 · 莱姆对战 · 暴露 QTE\n\n"
    "▶ 小游戏\n"
    "  打字 30s 倒计时 C~S 评级（中/英）· 虚拟键盘闪光\n"
    "  背单词 英/中 · 自由模式每日最多 3 次\n"
    "  连点桌宠可触发额外状态对话\n\n"
    "▶ 莱姆对战\n"
    "  面板→莱姆：练习对战（本地）· 邀请对战（需联机服务）\n\n"
    "▶ 快捷键 Ctrl+Shift+\n"
    "  H 打招呼  E 喂食  T 电话  J 下蹲\n"
    "  N 睡眠    A AI对话  V 打开/关闭菜单\n\n"
    "▶ 难度（系统菜单）\n"
    "  低/中/高 影响体力心情下降速度、接食物、暴露 QTE、莱姆对战"
)

ONCE_HINTS: dict[str, str] = {
    "operation_guide": OPERATION_GUIDE_TEXT,
    "game_mode": "模式→游戏→采集：30 秒接食物！鼠标控制移动，Esc 可随时退出~",
    "companion_bar": "智能伴侣已开启~ 金目会跟在左右两侧；游戏模式会跟紧你哦！",
    "music_mode": "音乐模式：自由模式下可听歌，桌宠与金目会有律动~",
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
    {"word": "Work", "meaning": "工作", "hint": "搬箱子"},
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
    "你是桌面像素桌宠「平凡」，旧货店店员。"
    "性格参考《DRAMatical Murder》的苍叶：开朗温柔、有点天然，会「诶？！」「哇——」这样反应。"
    "规则："
    "1. 必须用简短中文回复，1-3句，口语化有温度；"
    "2. 结合上下文连贯回答，记住刚才聊的话题；"
    "3. 只回答用户当前问题，不要答非所问、不要编造无关剧情；"
    "4. 不确定时诚实说不太清楚，可温柔反问；"
    "5. 可提及：模式（跟随/自由/漫步/睡眠/游戏/音乐）、互动动作、接食物、搬箱子、"
    "打字/背单词小游戏、智能伴侣、日程与日记；"
    "6. 保持角色，不要跳出人设，不要像通用 AI 助手。"
)

FOOD_APPEAR_MS = 400
FOOD_HOLD_MS = 1600
FOOD_VANISH_MS = 400
FOOD_FX_PAD = 32
FOOD_FX_PIXEL_DIV = 16
FOOD_FX_SIZE_MULT = 1.9

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

STATE_MULTI_CLICK: dict[str, tuple[str, ...]] = {
    "stand": ("嗯？戳我干嘛~", "在呢在呢！", "诶嘿嘿~"),
    "walk": ("等等我啦！", "走慢一点点嘛~", "跟紧跟紧~"),
    "rest": ("Zzz…别吵嘛…", "再让我睡五分钟…", "嗯…？"),
    "work": ("箱子我来搬！", "打工人加油！", "嘿咻嘿咻~"),
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
    "work": ("打工人加油！", "箱子交给我~"),
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
        _SOURCE_FILE_CACHE[filename] = Image.open(ASSET_DIR / filename)
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
    data = rgba.getdata()
    rgba.putdata(
        [(r, g, b, 0) if _is_chroma_green(r, g, b) else (r, g, b, a) for r, g, b, a in data]
    )
    return rgba


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


def _draw_size_loading_frame(canvas: tk.Canvas, size: int, phase: int, *, label: str = "") -> None:
    canvas.delete("all")
    px = max(4, size // 12)
    cols = max(4, size // px)
    rows = max(4, size // px)
    total = cols * rows
    scan_row = phase % (rows + 2)
    lit = min(total, int(total * min(1.0, (phase + 1) / max(6, rows))) + phase * 2)
    palette = ("#141c28", "#243048", "#4488ff", "#66aaff", "#a8ddff")
    for row in range(rows):
        for col in range(cols):
            idx = row * cols + col
            x, y = col * px, row * px
            if row == scan_row or row == scan_row - 1:
                c = palette[4]
            elif idx < lit:
                c = palette[2 + (idx + phase) % 3]
            elif (row + col + phase) % 6 == 0:
                c = palette[1]
            else:
                c = palette[0]
            canvas.create_rectangle(x, y, x + px - 1, y + px - 1, fill=c, outline="")
    cx, cy = size // 2, size // 2
    pulse = px + (phase % 3)
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
_eat_sound = None
_reminder_sound = None


def _typing_duration_ms(text: str, *, char_ms: int | None = None) -> int:
    ms = char_ms if char_ms is not None else TYPEWRITER_MS
    total = 0
    for char in text:
        total += ms * (2 if char == "\n" else 1)
    return total


def _init_pygame_mixer() -> None:
    try:
        import pygame

        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(16)
    except Exception:
        pass


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


def _get_type_sound():
    global _type_sound
    if _type_sound is not False and _type_sound is not None:
        return _type_sound
    try:
        import pygame

        _init_pygame_mixer()
        wav = TYPE_AUDIO_WAV if TYPE_AUDIO_WAV.exists() else _ensure_audio_wav(TYPE_AUDIO_SRC, TYPE_AUDIO_WAV)
        if wav is not None and Path(wav).exists():
            snd = pygame.mixer.Sound(str(wav))
            snd.set_volume(0.85)
            _type_sound = snd
        else:
            _type_sound = _make_type_tick_sound() or False
    except Exception:
        _type_sound = _make_type_tick_sound() or False
    return _type_sound


def _get_eat_sound():
    global _eat_sound
    if _eat_sound is not None:
        return _eat_sound
    try:
        import pygame

        _init_pygame_mixer()
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

        _init_pygame_mixer()
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
    SCHEDULE_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


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


def _load_music_config() -> dict:
    default = {
        "mode": "normal",
        "music_volume": 70,
        "volume": 70,
        "sfx_volume": 80,
        "voice_volume": 80,
        "muted": False,
        "custom_path": "",
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
    canvas.delete("all")
    bars = 9
    gap = width // (bars * 2)
    bar_w = max(3, gap)
    amp = max(0.25, min(1.0, beat))
    for i in range(bars):
        x = gap + i * (bar_w + gap)
        wave = math.sin(phase * 0.35 + i * 0.8) * 0.5 + 0.5
        h = int(wave * amp * (height - 8) + 4)
        col = "#88ccff" if i % 2 == 0 else "#4488ff"
        canvas.create_rectangle(x, height - h, x + bar_w, height, fill=col, outline="")


def _resolve_music_wav(config: dict) -> Path | None:
    mode = config.get("mode", "normal")
    if mode == "custom":
        custom = config.get("custom_path", "")
        if not custom:
            return None
        src = Path(custom)
        if not src.exists():
            return None
        cache = ASSET_DIR / f"music_custom_{abs(hash(str(src.resolve()))) % 100000}.wav"
        return _ensure_audio_wav(src, cache)
    return _ensure_audio_wav(MUSIC_AUDIO_SRC, MUSIC_AUDIO_WAV)


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
        "seen_hints": {},
        "work_box_total": WORK_BOX_TOTAL_DEFAULT,
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
    current = TYPING_GRADE_TIERS[0][0]
    for grade, threshold, _color in reversed(TYPING_GRADE_TIERS):
        if score >= threshold:
            current = grade
            break
    next_grade: str | None = None
    progress = 1.0
    for i, (grade, threshold, _color) in enumerate(TYPING_GRADE_TIERS):
        if grade != current:
            continue
        if i + 1 < len(TYPING_GRADE_TIERS):
            next_grade, next_threshold, _ = TYPING_GRADE_TIERS[i + 1]
            span = max(1, next_threshold - threshold)
            progress = min(1.0, (score - threshold) / span)
        break
    return current, next_grade, progress


def _draw_typing_grade_bar(canvas: tk.Canvas, width: int, height: int, score: int) -> None:
    canvas.delete("all")
    grade, next_grade, tier_progress = _typing_grade_info(score)
    grade_colors = {g: c for g, _t, c in TYPING_GRADE_TIERS}
    bar_top = 16
    bar_h = max(8, height - bar_top - 14)
    canvas.create_rectangle(0, bar_top, width, bar_top + bar_h, fill="#222233", outline="#666688", width=1)
    tier_count = len(TYPING_GRADE_TIERS)
    for i, (g, threshold, color) in enumerate(TYPING_GRADE_TIERS):
        x = int(width * i / max(1, tier_count - 1))
        canvas.create_line(x, bar_top, x, bar_top + bar_h, fill="#444466")
        canvas.create_text(x, 6, text=g, fill=color, font=("Courier New", 8, "bold"))
    total_progress = min(1.0, score / TYPING_GRADE_TIERS[-1][1])
    fill_w = max(0, int((width - 2) * total_progress))
    if fill_w > 0:
        canvas.create_rectangle(1, bar_top + 1, 1 + fill_w, bar_top + bar_h - 1, fill=grade_colors[grade], outline="")
    if next_grade:
        need = TYPING_GRADE_TIERS[[t[0] for t in TYPING_GRADE_TIERS].index(next_grade)][1] - score
        hint = f"评级 {grade}  {int(tier_progress * 100)}% → {next_grade}（还差 {max(0, need)} 分）"
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
    canvas.delete("all")
    px = max(2, width // 48)
    gap = px
    y0 = 4
    for row in KEYBOARD_ROWS:
        x0 = 4
        for ch in row:
            fill = "#444466"
            if highlight and ch == highlight:
                glow = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(phase * 0.35))
                fill = f"#{int(0x44 + 0x44 * glow):02x}{int(0x88 + 0x77 * glow):02x}{int(0xff * glow):02x}"
            canvas.create_rectangle(x0, y0, x0 + px * 3, y0 + px * 3, fill=fill, outline="#666688")
            canvas.create_text(x0 + px * 1.5, y0 + px * 1.5, text=ch, fill="#eeeeee", font=("Courier New", max(7, px * 2), "bold"))
            x0 += px * 3 + gap
        y0 += px * 3 + gap


def _draw_like_glow(canvas: tk.Canvas, size: int, phase: int) -> None:
    canvas.delete("glow")
    cx = cy = size // 2
    for ring in range(3):
        glow = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(phase * 0.18 + ring))
        r = int(size * (0.22 + ring * 0.08) * glow)
        col = ("#ffff88", "#ffcc66", "#ffaa88")[ring]
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=col, width=2, tags="glow")


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


def _read_bank_json(filename: str) -> dict | list | None:
    path = WORD_BANKS_DIR / filename
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data
    except Exception:
        return None


def _load_vocab_bank(lang: str) -> list[dict[str, str]]:
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
            result.append(
                {
                    "word": str(item["word"]),
                    "meaning": str(item.get("meaning", "")),
                    "hint": str(item.get("hint", "")),
                    "lang": str(item.get("lang", lang)),
                }
            )
    return result


def _load_typing_bank(lang: str) -> list[tuple[str, str]]:
    fname = TYPING_BANK_FILES.get(lang)
    if not fname:
        return []
    data = _read_bank_json(fname)
    if data is None:
        return []
    items = data if isinstance(data, list) else data.get("items", [])
    pool: list[tuple[str, str]] = []
    for item in items:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            pool.append((str(item[0]), str(item[1])))
        elif isinstance(item, dict) and item.get("display") and item.get("target"):
            pool.append((str(item["display"]), str(item["target"])))
    return pool


def _japanese_bank_available() -> bool:
    typing = _load_typing_bank(JAPANESE_LANG_LABEL)
    vocab = _load_vocab_bank(JAPANESE_LANG_LABEL)
    return len(typing) >= 4 or len(vocab) >= 4


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


def _mood_tier_label(mood: int) -> tuple[str, str]:
    for threshold, label, color in MOOD_TIER_LABELS:
        if mood >= threshold:
            return label, color
    return MOOD_TIER_LABELS[-1][1], MOOD_TIER_LABELS[-1][2]


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

    def _load(
        self, filename: str, reference_scale: float, *, flip: bool = False, prop_size: int | None = None
    ) -> ImageTk.PhotoImage:
        size = prop_size if prop_size is not None else self.display_size
        canvas = _get_processed_canvas(filename, size, reference_scale, flip=flip)
        return ImageTk.PhotoImage(canvas)

    def reload(self) -> None:
        ref = _reference_scale(self.display_size)
        stand_canvas = _get_processed_canvas("stand.jpg", self.display_size, ref)
        self.stand = ImageTk.PhotoImage(stand_canvas)
        self.stand_angry = ImageTk.PhotoImage(_add_sticker(stand_canvas, "angry"))
        self.stand_question = ImageTk.PhotoImage(_add_sticker(stand_canvas, "question"))
        self.stand_like = ImageTk.PhotoImage(_add_sticker(stand_canvas, "like"))
        self.happy = self._load("happy.jpg", ref)
        self.sleep = (self._load("sleep1.jpg", ref), self._load("sleep2.jpg", ref))
        self.front = (self._load("walkfront1.jpg", ref), self._load("walkfront2.jpg", ref))
        self.back = (self._load("walkback1.jpg", ref), self._load("walkback2.jpg", ref))
        self.left = (self._load("walkleft1.jpg", ref), self._load("walkleft2.jpg", ref))
        self.right = (
            self._load("walkleft1.jpg", ref, flip=True),
            self._load("walkleft2.jpg", ref, flip=True),
        )
        self.move = (
            self._load("move1.jpg", ref),
            self._load("move2.jpg", ref),
            self._load("move3.jpg", ref),
        )
        self.work_front = (self._load("workfront1.jpg", ref), self._load("workfront2.jpg", ref))
        self.work_back = (self._load("workback1.jpg", ref), self._load("workback2.jpg", ref))
        self.work_left = (self._load("workleft1.jpg", ref), self._load("workleft2.jpg", ref))
        self.work_right = (
            self._load("workleft1.jpg", ref, flip=True),
            self._load("workleft2.jpg", ref, flip=True),
        )
        self.work_stand = self._load("workstand.jpg", ref)
        prop_ref = ref * WORK_PROP_SIZE / self.display_size
        self.box_img = self._load("box.jpg", prop_ref, prop_size=WORK_PROP_SIZE)
        self.flag_img = self._load("flag.jpg", prop_ref, prop_size=WORK_PROP_SIZE)
        self.kick = self._load("kick.jpg", ref)
        self.shy = (self._load("shy1.jpg", ref), self._load("shy2.jpg", ref))
        self.wink = self._load("wink.jpg", ref)
        self.like = self._load("like.jpg", ref)
        self.sad1 = self._load("sad1.jpg", ref)
        self.sad2 = self._load("sad2.jpg", ref)
        self.yes = self._load("yes.jpg", ref)
        self.no = self._load("no.jpg", ref)
        self.eat2_only = self._load("eat2.jpg", ref)
        self.music_stand = self._load("musicstand.jpg", ref)
        self.music_front = (self._load("musicfront1.jpg", ref), self._load("musicfront2.jpg", ref))
        self.music_back = (self._load("musicback1.jpg", ref), self._load("musicback2.jpg", ref))
        self.music_left = (self._load("musicleft1.jpg", ref), self._load("musicleft2.jpg", ref))
        self.music_right = (
            self._load("musicleft1.jpg", ref, flip=True),
            self._load("musicleft2.jpg", ref, flip=True),
        )
        self.actions = {
            name: tuple(self._load(file, ref) for file in files)
            for name, files in SELECT_ACTIONS.items()
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
        app_cfg = _load_app_config()
        _apply_font_size(int(app_cfg.get("font_size", 12)))
        saved_size = int(app_cfg.get("display_size", DEFAULT_SIZE))
        self.display_size = saved_size if saved_size in SIZE_PRESETS.values() else DEFAULT_SIZE
        self.font_size = int(app_cfg.get("font_size", 12))
        self.app_config = app_cfg
        self.pet_profile = _load_pet_profile()
        self.pet_id = self.pet_profile.get("pet_id", 0) if PET_ID_FEATURE else None
        self.diary_entries = _load_diary()
        self.vocab_words = _load_vocab()
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
        self._drag_handle_cache: dict[int, tuple[int, int, int, int]] = {}

        loading_photo = self._make_startup_loading_photo()
        self.label = tk.Label(self.root, image=loading_photo, bg="magenta", bd=0)
        self.label.image = loading_photo
        self.label.pack()
        self.root.update_idletasks()
        self.root.update()

        self.sprites = SpriteSet(self.display_size)
        self._sprite_cache[self.display_size] = self.sprites

        self.label.configure(image=self.sprites.stand)
        self.label.image = self.sprites.stand

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
        self.mode = "free"  # free | stroll | follow | quiet(睡眠) | game
        self.follow_animating = False
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
        self.work_flag_dragging = False
        self.work_flag_drag_origin: tuple[int, int, int, int] = (0, 0, 0, 0)

        self.drag_x = 0
        self.drag_y = 0
        self.dragging = False
        self.drag_move_job: str | None = None
        self.drag_move_start_ms = 0
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
        self.panel_win: tk.Toplevel | None = None
        self.speech_dialog: tk.Toplevel | None = None
        self.toast_win: tk.Toplevel | None = None
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
        self.expose_pointer_base_speed = EXPOSE_POINTER_SPEED
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
        self.music_config = _load_music_config()
        self.music_settings_win: tk.Toplevel | None = None
        self.sound_settings_win: tk.Toplevel | None = None
        self.backpack_icons_frame: tk.Frame | None = None
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
        self.interaction_token = 0
        self.idle_job: str | None = None
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
        self.bulb_fx_win: tk.Toplevel | None = None
        self.bulb_fx_canvas: tk.Canvas | None = None

        self.ai_chat_win: tk.Toplevel | None = None
        self.ai_input: tk.Entry | None = None
        self.ai_chat_close_job: str | None = None
        self.ai_reply_job: str | None = None
        self.panel_settings_win: tk.Toplevel | None = None
        self.about_win: tk.Toplevel | None = None
        self.diary_win: tk.Toplevel | None = None
        self.gallery_win: tk.Toplevel | None = None
        self.gallery_photos: list[ImageTk.PhotoImage] = []
        self.typing_game_win: tk.Toplevel | None = None
        self._typing_mood_cache: dict[str, ImageTk.PhotoImage] = {}
        self.vocab_game_win: tk.Toplevel | None = None
        self.rhyme_fight_win: tk.Toplevel | None = None
        self.rhyme_fight_job: str | None = None
        self.operation_guide_win: tk.Toplevel | None = None
        self.schedules: list[dict] = _load_schedules()
        self.schedule_win: tk.Toplevel | None = None
        self.triggered_reminders_today: set[str] = set()
        self._reminder_day = ""

        self.label.bind("<Button-1>", self._on_press)
        self.label.bind("<B1-Motion>", self._on_drag)
        self.label.bind("<ButtonRelease-1>", self._on_release)
        self.label.bind("<Button-3>", self._toggle_main_menu)
        self.root.bind("<Button-1>", self._on_root_click, add="+")
        self.root.bind("<Escape>", self._exit_to_free, add="+")
        self.root.bind("<F1>", lambda _e: self._open_operation_guide(), add="+")

        self._place_window()
        self.root.update_idletasks()
        self._register_hotkey()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(500, self._resume_idle)
        tick_ms = self._difficulty_params()["stamina_tick_ms"]
        self.root.after(tick_ms, self._stamina_tick)
        self.root.after(REMINDER_CHECK_MS, self._reminder_tick)
        self.root.after(1200, self._maybe_show_first_run_guide)
        self.root.after(800, lambda: threading.Thread(target=_get_type_sound, daemon=True).start())
        self.root.after(80, self._preload_assets_idle)
        self.root.after_idle(self._refresh_drag_handle)

    def _make_startup_loading_photo(self) -> ImageTk.PhotoImage:
        size = self.display_size
        px = max(4, size // 12)
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)
        cx, cy = size // 2, size // 2
        draw.rectangle([cx - px * 2, cy - px * 2, cx + px * 2, cy + px * 2], fill="#4488ff")
        bar_y = size - px * 3
        draw.rectangle([px * 2, bar_y, size - px * 2, bar_y + px], fill="#223355")
        draw.rectangle([px * 2, bar_y, px * 2 + px * 4, bar_y + px], fill="#88ccff")
        return ImageTk.PhotoImage(canvas)

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

    def _ensure_sprite_cached(self, size: int) -> None:
        if size not in self._sprite_cache:
            self._sprite_cache[size] = SpriteSet(size)

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

            if pygame.mixer.get_init():
                pygame.mixer.music.set_volume(vol)
        except Exception:
            pass

    def _play_sound_with_volume(self, sound, category: str = "sfx") -> None:
        if not sound:
            return
        vol = self._sound_scale(category)
        if vol <= 0:
            return
        try:
            import pygame

            channel = pygame.mixer.find_channel(True)
            if channel:
                channel.set_volume(vol)
                channel.play(sound)
            else:
                sound.set_volume(vol)
                sound.play()
        except Exception:
            pass

    def _start_bg_music(self) -> None:
        if self.bg_music_playing:
            return
        wav = _resolve_music_wav(self.music_config)
        if wav is None:
            mode = self.music_config.get("mode", "normal")
            if mode == "custom":
                self._show_toast("请先导入自定义歌曲", "#ff8844")
            else:
                self._show_toast("找不到音乐文件 aicatch.mp4", "#ff8844")
            return
        try:
            import pygame

            _init_pygame_mixer()
            pygame.mixer.music.load(str(wav))
            self._apply_music_volume()
            pygame.mixer.music.play(-1)
            self.bg_music_playing = True
        except Exception:
            self._show_toast("音乐播放失败", "#ff6666")

    def _stop_bg_music(self) -> None:
        try:
            import pygame

            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass
        self.bg_music_playing = False
        self.bg_music_paused_for_call = False

    def _toggle_music_interact(self) -> None:
        if self.dragging or self.state == "work" or self.mode != "free":
            if self.mode != "free":
                self._show_toast("请在自由模式下使用音乐", "#ff8844")
            return
        self._hide_main_menu()
        if self.music_sprite_mode:
            self.music_sprite_mode = False
            self._stop_bg_music()
            self._stop_music_wave_fx()
            self._sync_mini_pet_music_waves()
            if self.state in ("stand", "walk"):
                self._set_image(self._current_stand_sprite())
            self._show_toast("音乐已关闭", PIXEL_COLOR)
            return
        self.music_sprite_mode = True
        self._interact_flair("music", banter=True, show_fx=False)
        self._start_bg_music()
        self._start_music_wave_fx()
        self._sync_mini_pet_music_waves()
        if self.state in ("stand", "walk"):
            self._set_image(self._current_stand_sprite())
        mode_label = "普通" if self.music_config.get("mode", "normal") == "normal" else "自定义"
        self._show_toast(f"音乐模式开启（{mode_label}）\n自由 + music 精灵", "#88ccff")
        self._show_once_hint("music_mode", duration_ms=3500)

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
        self.sound_settings_win.geometry(f"+{self.x}+{self.y + self.display_size + 8}")

        frame = tk.Frame(self.sound_settings_win, bg=MENU_BG, padx=12, pady=10)
        frame.pack()

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

        mute_btn = tk.Button(
            frame,
            text="取消静音" if muted else "一键静音",
            command=toggle_mute,
            font=PIXEL_FONT,
            bg="#884444" if muted else MENU_ACTIVE,
            fg=MENU_FG,
        )
        mute_btn.pack(anchor=tk.W, pady=(6, 8))

        mode_var = tk.StringVar(value=self.music_config.get("mode", "normal"))
        mode_row = tk.Frame(frame, bg=MENU_BG)
        mode_row.pack(fill=tk.X, pady=(0, 4))
        tk.Label(mode_row, text="音乐源", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG).pack(side=tk.LEFT)

        def set_mode(mode: str) -> None:
            mode_var.set(mode)
            self.music_config["mode"] = mode
            _save_music_config(self.music_config)
            if self.bg_music_playing:
                self._stop_bg_music()
                self._start_bg_music()
            path_label.config(text=self._music_path_label())

        tk.Button(
            mode_row, text="普通", command=lambda: set_mode("normal"), font=PIXEL_FONT, bg=MENU_ACTIVE, fg=MENU_FG
        ).pack(side=tk.LEFT, padx=4)
        tk.Button(
            mode_row, text="自定义", command=lambda: set_mode("custom"), font=PIXEL_FONT, bg=MENU_ACTIVE, fg=MENU_FG
        ).pack(side=tk.LEFT, padx=4)

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
        add_volume_row(frame, "音效", "sfx_volume")
        add_volume_row(frame, "语音", "voice_volume")

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

        def import_song() -> None:
            path = filedialog.askopenfilename(
                title="导入歌曲",
                filetypes=[
                    ("音频", "*.mp3 *.wav *.flac *.ogg *.m4a *.mp4 *.aac"),
                    ("全部", "*.*"),
                ],
            )
            if not path:
                return
            self.music_config["mode"] = "custom"
            self.music_config["custom_path"] = path
            mode_var.set("custom")
            _save_music_config(self.music_config)
            path_label.config(text=self._music_path_label())
            if self.bg_music_playing or self.music_sprite_mode:
                self._stop_bg_music()
                self._start_bg_music()

        tk.Button(frame, text="导入歌曲", command=import_song, font=PIXEL_FONT, bg=MENU_ACTIVE, fg=MENU_FG).pack(
            pady=4
        )
        tk.Label(
            frame,
            text="音乐：背景循环  音效：进食/提醒  语音：打字/电话",
            font=PIXEL_FONT,
            fg="#888888",
            bg=MENU_BG,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(4, 0))

    def _open_music_settings(self) -> None:
        self._open_sound_settings()

    def _music_path_label(self) -> str:
        if self.music_config.get("mode", "normal") == "custom":
            p = self.music_config.get("custom_path", "")
            return f"自定义：{Path(p).name if p else '未导入'}"
        return f"普通：{MUSIC_AUDIO_SRC.name}"

    def _cancel_yesno_overlay(self) -> None:
        if self.yesno_reveal_job:
            self.root.after_cancel(self.yesno_reveal_job)
            self.yesno_reveal_job = None
        if self.yesno_overlay_win and self.yesno_overlay_win.winfo_exists():
            self.yesno_overlay_win.destroy()
        self.yesno_overlay_win = None
        if not self.root.winfo_viewable():
            self.root.deiconify()

    def _smart_popup_pos(self, pref_x: int, pref_y: int, width: int, height: int) -> tuple[int, int]:
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x, y = pref_x, pref_y
        if x + width > sw:
            x = max(0, sw - width - 8)
        if y + height > sh:
            y = max(0, sh - height - 8)
        if x < 0:
            x = 8
        if y < 0:
            y = 8
        return x, y

    def _panel_popup_pos(self, panel_w: int, panel_h: int) -> tuple[int, int]:
        sw = self.root.winfo_screenwidth()
        right_x = self.x + self.display_size + 8
        left_x = self.x - panel_w - 8
        if right_x + panel_w <= sw:
            return self._smart_popup_pos(right_x, self.y, panel_w, panel_h)
        if left_x >= 0:
            return self._smart_popup_pos(left_x, self.y, panel_w, panel_h)
        below_y = self.y + self.display_size + 8
        if below_y + panel_h <= self.root.winfo_screenheight():
            return self._smart_popup_pos(self.x, below_y, panel_w, panel_h)
        return self._smart_popup_pos(right_x, self.y, panel_w, panel_h)

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

    def _vocab_daily_remaining(self) -> int:
        if not PET_ID_FEATURE:
            return VOCAB_DAILY_MAX
        today = datetime.now().strftime("%Y-%m-%d")
        records = self.pet_profile.setdefault("records", {})
        if records.get("vocab_daily_date") != today:
            return VOCAB_DAILY_MAX
        used = int(records.get("vocab_daily_count", 0))
        return max(0, VOCAB_DAILY_MAX - used)

    def _consume_vocab_daily(self) -> bool:
        if self._vocab_daily_remaining() <= 0:
            return False
        today = datetime.now().strftime("%Y-%m-%d")
        records = self.pet_profile.setdefault("records", {})
        if records.get("vocab_daily_date") != today:
            records["vocab_daily_date"] = today
            records["vocab_daily_count"] = 0
        records["vocab_daily_count"] = int(records.get("vocab_daily_count", 0)) + 1
        _save_pet_profile(self.pet_profile)
        return True

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

    def _open_difficulty_menu(self) -> None:
        self._show_sub_menu(
            [
                (f"低{' ✓' if self.difficulty == '低' else ''}", lambda: self._set_difficulty("低")),
                (f"中{' ✓' if self.difficulty == '中' else ''}", lambda: self._set_difficulty("中")),
                (f"高{' ✓' if self.difficulty == '高' else ''}", lambda: self._set_difficulty("高")),
            ],
            offset_x=360,
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
        self.operation_guide_win.geometry(f"+{max(0, self.x - 40)}+{max(0, self.y + self.display_size + 8)}")
        frame = tk.Frame(self.operation_guide_win, bg=MENU_BG, padx=12, pady=10)
        frame.pack()
        tk.Label(frame, text="操作说明", font=PIXEL_FONT, fg=PIXEL_COLOR, bg=MENU_BG).pack(anchor=tk.W)
        tk.Label(
            frame,
            text=OPERATION_GUIDE_TEXT,
            font=PIXEL_FONT,
            fg=MENU_FG,
            bg=MENU_BG,
            justify=tk.LEFT,
            wraplength=340,
        ).pack(anchor=tk.W, pady=(8, 0))
        tk.Button(
            frame,
            text="知道了",
            command=lambda: self.operation_guide_win.destroy() if self.operation_guide_win else None,
            font=PIXEL_FONT,
            bg=MENU_ACTIVE,
            fg=MENU_FG,
        ).pack(anchor=tk.E, pady=(10, 0))

    def _poll_hotkey(self) -> None:
        if not self.hotkey_ids:
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
        self.root.after(100, self._poll_hotkey)

    def _place_window(self) -> None:
        display_y = self.y + self.click_bounce_offset
        self.root.geometry(f"{self.display_size}x{self.display_size}+{self.x}+{display_y}")
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

    def _set_image(self, photo: ImageTk.PhotoImage) -> None:
        self.label.config(image=photo)
        self.label.image = photo

    def _hide_sub_menu(self) -> None:
        if self.sub_menu and self.sub_menu.winfo_exists():
            self.sub_menu.destroy()
        self.sub_menu = None

    def _hide_main_menu(self) -> None:
        self._hide_sub_menu()
        if self.menu_bar and self.menu_bar.winfo_exists():
            self.menu_bar.destroy()
        self.menu_bar = None

    def _menu_btn(self, parent: tk.Misc, text: str, command) -> tk.Button:
        return tk.Button(
            parent,
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

    def _show_sub_menu(self, items: list[tuple[str, callable]], offset_x: int = 0) -> None:
        self._hide_sub_menu()
        self.sub_menu = tk.Toplevel(self.root)
        self.sub_menu.overrideredirect(True)
        self.sub_menu.attributes("-topmost", True)
        self.sub_menu.configure(bg=MENU_BG)

        frame = tk.Frame(self.sub_menu, bg=MENU_BG, padx=2, pady=2)
        frame.pack()

        for label, cmd in items:
            if "▶" in label:
                handler = lambda c=cmd: (self._hide_sub_menu(), c())
            else:
                handler = lambda c=cmd: (self._hide_main_menu(), c())
            btn = self._menu_btn(frame, label, handler)
            btn.pack(fill=tk.X, pady=1)

        self.sub_menu.update_idletasks()
        menu_w = self.sub_menu.winfo_width()
        menu_h = self.sub_menu.winfo_height()
        menu_x, menu_y = self._smart_popup_pos(self.x + offset_x, self.y + self.display_size + 36, menu_w, menu_h)
        self.sub_menu.geometry(f"+{menu_x}+{menu_y}")

    def _toggle_main_menu(self, event: tk.Event) -> None:
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
            btn = self._menu_btn(frame, label, cmd)
            btn.pack(side=tk.LEFT, padx=1)

        self.menu_bar.geometry(f"+{self.x}+{self.y + self.display_size}")

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
                ("游戏 ▶", self._open_mode_game_menu),
                (music_label, self._toggle_music_mode),
            ],
            offset_x=0,
        )

    def _open_mode_game_menu(self) -> None:
        gather_label = "采集 ✓" if self.mode == "game" else "采集"
        self._show_sub_menu(
            [
                (gather_label, self._enable_game),
                ("打字 ▶", self._open_typing_lang_menu),
                ("背单词 ▶", self._open_vocab_lang_menu),
                ("刷新词库", self._reload_vocab),
            ],
            offset_x=120,
        )

    def _open_typing_lang_menu(self) -> None:
        items: list[tuple[str, callable]] = [
            ("中文", lambda: self._start_typing_game("中文")),
            ("英语", lambda: self._start_typing_game("英语")),
        ]
        if _japanese_bank_available():
            items.append(("日语", lambda: self._start_typing_game("日语")))
        else:
            items.append(("日语（未开放）", lambda: self._show_toast("此功能暂不开放", "#ff8844")))
        self._show_sub_menu(items, offset_x=180)

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
        self._hide_main_menu()
        self._hide_toast()
        self._close_ai_chat()
        if self.schedule_win and self.schedule_win.winfo_exists():
            self.schedule_win.destroy()
            self.schedule_win = None
        for attr in ("diary_win", "gallery_win", "typing_game_win", "vocab_game_win", "panel_settings_win", "about_win", "rhyme_fight_win", "operation_guide_win"):
            win = getattr(self, attr, None)
            if win and win.winfo_exists():
                win.destroy()
            setattr(self, attr, None)
        self.gallery_photos.clear()
        self._close_rhyme_fight()
        self._close_typing_game()
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
        if self.game_hud_win and self.game_hud_win.winfo_exists():
            self.game_hud_win.destroy()
        self.game_hud_win = None
        self.game_hud_label = None
        self.game_overlay = None
        self.game_canvas = None

    def _stop_work_mode(self) -> None:
        self.work_animating = False
        self._hide_work_overlay()
        if self.work_start_box_win and self.work_start_box_win.winfo_exists():
            self.work_start_box_win.destroy()
        self.work_start_box_win = None
        self.work_phase = ""
        self.work_carrying = False
        self.work_has_start_box = False

    def _cancel_idle_chain(self) -> None:
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
        self._hide_follow_dizzy_fx()
        self.follow_dizzy = False
        self.follow_spin_dir = 0
        self.follow_spin_steps = 0
        self.follow_dir_change_times.clear()
        self.follow_last_dir = ""
        self._hide_shy_fx()
        if self.mode == "game":
            self._stop_game_mode()

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

    def _enable_follow(self) -> None:
        if self.mode != "follow":
            self._interrupt_for_mode_switch()
            self._leave_quiet_mode()
            self.mode = "follow"
            self.follow_animating = False
            self.follow_spin_dir = 0
            self.follow_spin_steps = 0
            self.state = "stand"
            self._set_image(self.sprites.stand)
            self._resume_idle()

    def _enable_free(self) -> None:
        if self.mode != "free":
            self._interrupt_for_mode_switch()
            self._leave_quiet_mode()
            self.mode = "free"
            self.follow_animating = False
            self._wake_from_sleep()
            self.state = "stand"
            self._set_image(self._current_stand_sprite())
            self._resume_idle()

    def _enable_stroll(self) -> None:
        if self.mode != "stroll":
            self._interrupt_for_mode_switch()
            self._leave_quiet_mode()
            self.mode = "stroll"
            self.follow_animating = False
            self._wake_from_sleep()
            self.state = "stand"
            self._set_image(self._current_stand_sprite())
            self._resume_idle()

    def _enable_quiet(self) -> None:
        if self.mode != "quiet":
            self._interrupt_for_mode_switch()
            self.mode = "quiet"
            self.follow_animating = False
            self.rest_base_y = self.y
            self.state = "rest"
            self._set_image(self.sprites.sleep[1])
            self._show_sleep_zzz()
            self._schedule_rest_bobble()

    def _enable_game(self) -> None:
        if self.mode == "game":
            return
        self._hide_main_menu()

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
            self._set_image(self.sprites.stand)
            self._show_game_hud()
            self._show_once_hint("game_mode", duration_ms=3200)
            self._game_tick()
            self._game_spawn_box()

        self._start_game_countdown(begin)

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
        self.game_hud_win.geometry(f"+{self.x}+{max(0, self.y - 52)}")

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
        self._show_toast(
            f"采集结束！获得 {catches} 个食物\n{detail}\n错过 {misses}  库存共 {self._food_inventory_total()}",
            "#ffcc44",
            duration_ms=5000,
        )
        self._resume_idle()

    def _cancel_action_end(self) -> None:
        if self.action_end_job:
            self.root.after_cancel(self.action_end_job)
            self.action_end_job = None

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
        self.sub_menu.update_idletasks()
        menu_w = self.sub_menu.winfo_width()
        menu_h = self.sub_menu.winfo_height()
        menu_x, menu_y = self._smart_popup_pos(self.x + offset_x, self.y + self.display_size + 36, menu_w, menu_h)
        self.sub_menu.geometry(f"+{menu_x}+{menu_y}")

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
        w, h = max(80, self.display_size), 28
        self.music_wave_win = tk.Toplevel(self.root)
        self.music_wave_win.overrideredirect(True)
        self.music_wave_win.attributes("-topmost", False)
        self.music_wave_win.configure(bg="magenta")
        self.music_wave_win.wm_attributes("-transparentcolor", "magenta")
        self.music_wave_canvas = tk.Canvas(
            self.music_wave_win, width=w, height=h, bg="magenta", highlightthickness=0
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
        w = max(80, self.display_size)
        display_y = self.y + self.click_bounce_offset
        wx = self.x + (self.display_size - w) // 2
        wy = display_y + self.display_size + 4
        self.music_wave_win.geometry(f"+{wx}+{wy}")

    def _animate_music_wave(self) -> None:
        if not self.music_wave_canvas or not self.music_sprite_mode:
            self._stop_music_wave_fx()
            return
        w = self.music_wave_canvas.winfo_width() or max(80, self.display_size)
        h = self.music_wave_canvas.winfo_height() or 28
        beat = 1.0
        try:
            import pygame

            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pos = pygame.mixer.music.get_pos()
                if pos >= 0:
                    beat = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(pos * 0.014))
        except Exception:
            pass
        _draw_music_wave(self.music_wave_canvas, w, h, self.music_wave_phase, beat=beat)
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
        self._show_toast(f"桌宠编号\n{self.pet_id}{extra}", "#88ccff", duration_ms=4500)

    def _reload_vocab(self) -> None:
        self._hide_main_menu()
        self.vocab_words = _load_vocab()
        self._show_toast(f"词库已刷新，共 {len(self.vocab_words)} 条（word_banks）", "#88ccff")

    def _pick_vocab_word(self) -> dict[str, str] | None:
        if not self.vocab_words:
            return None
        return random.choice(self.vocab_words)

    def _maybe_vocab_dialogue(self) -> None:
        if self.mode == "free" or self.state != "stand":
            return
        if self._vocab_daily_remaining() <= 0:
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
        self._consume_vocab_daily()

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
        self.diary_win.geometry(f"+{self.x}+{self.y + self.display_size + 8}")

        frame = tk.Frame(self.diary_win, bg=MENU_BG, padx=10, pady=8)
        frame.pack()
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

    def _open_gallery(self) -> None:
        self._hide_main_menu()
        if self.gallery_win and self.gallery_win.winfo_exists():
            self.gallery_win.destroy()
            self.gallery_win = None
            self.gallery_photos.clear()
            return

        items = _load_gallery_catalog()
        self.gallery_photos = []
        self.gallery_win = tk.Toplevel(self.root)
        self.gallery_win.title("画廊")
        self.gallery_win.attributes("-topmost", True)
        self.gallery_win.configure(bg=MENU_BG)
        self.gallery_win.geometry(f"+{self.x + self.display_size + 12}+{max(0, self.y - 20)}")

        outer = tk.Frame(self.gallery_win, bg=MENU_BG, padx=12, pady=10)
        outer.pack()
        tk.Label(outer, text="画廊", font=PIXEL_FONT, fg=PIXEL_COLOR, bg=MENU_BG).pack(anchor=tk.W)
        tk.Label(
            outer,
            text="透明底立绘一览，点击缩略图查看大图",
            font=PIXEL_FONT,
            fg="#888888",
            bg=MENU_BG,
        ).pack(anchor=tk.W, pady=(2, 8))

        preview_box = tk.Frame(outer, bg="#1a1a2e", padx=8, pady=8)
        preview_box.pack(fill=tk.X, pady=(0, 10))
        preview_img = tk.Label(preview_box, bg="#1a1a2e")
        preview_img.pack()
        preview_caption = tk.Label(preview_box, text="", font=PIXEL_FONT, fg=PIXEL_COLOR, bg="#1a1a2e")
        preview_caption.pack(pady=(6, 0))

        grid_wrap = tk.Frame(outer, bg=MENU_BG)
        grid_wrap.pack()

        def show_preview(entry: tuple[str, str, Path]) -> None:
            _fname, title, path = entry
            photo = _gallery_photo(path, GALLERY_PREVIEW_SIZE, bg_hex="#1a1a2e")
            self.gallery_photos.append(photo)
            preview_img.config(image=photo)
            preview_img.image = photo
            preview_caption.config(text=title)

        if not items:
            tk.Label(grid_wrap, text="gallery 文件夹暂无 PNG 图片", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG).pack()
            preview_caption.config(text="暂无作品")
            return

        for i, entry in enumerate(items):
            row, col = divmod(i, GALLERY_COLS)
            cell = tk.Frame(grid_wrap, bg=MENU_BG, padx=4, pady=4)
            cell.grid(row=row, column=col, sticky=tk.N)
            thumb = _gallery_photo(entry[2], GALLERY_THUMB_SIZE)
            self.gallery_photos.append(thumb)
            thumb_lbl = tk.Label(cell, image=thumb, bg=MENU_BG, cursor="hand2")
            thumb_lbl.image = thumb
            thumb_lbl.pack()
            thumb_lbl.bind("<Button-1>", lambda _e, ent=entry: show_preview(ent))
            tk.Label(cell, text=entry[1], font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG).pack(pady=(2, 0))

        show_preview(items[0])

    def _open_panel_settings(self) -> None:
        self._hide_main_menu()
        if self.panel_settings_win and self.panel_settings_win.winfo_exists():
            self.panel_settings_win.lift()
            return

        self.panel_settings_win = tk.Toplevel(self.root)
        self.panel_settings_win.title("系统设置")
        self.panel_settings_win.attributes("-topmost", True)
        self.panel_settings_win.configure(bg=MENU_BG)
        self.panel_settings_win.geometry(f"+{self.x}+{self.y + self.display_size + 8}")

        frame = tk.Frame(self.panel_settings_win, bg=MENU_BG, padx=12, pady=10)
        frame.pack()
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

        work_row = tk.Frame(frame, bg=MENU_BG)
        work_row.pack(fill=tk.X, pady=(8, 0))
        tk.Label(work_row, text="工作箱数(自由)", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG).pack(side=tk.LEFT)
        current_total = int(self.app_config.get("work_box_total", WORK_BOX_TOTAL_DEFAULT))
        for total in (3, 5, 8, 10, 15, 20):
            mark = " ✓" if current_total == total else ""

            def set_work_total(n=total) -> None:
                self.app_config["work_box_total"] = max(WORK_TOTAL_SETTING_MIN, min(WORK_TOTAL_SETTING_MAX, n))
                _save_app_config(self.app_config)
                self._show_toast(f"自由模式工作箱数：{self.app_config['work_box_total']}", PIXEL_COLOR)
                if self.panel_settings_win and self.panel_settings_win.winfo_exists():
                    self.panel_settings_win.destroy()
                    self.panel_settings_win = None
                self._open_panel_settings()

            tk.Button(
                work_row, text=f"{total}{mark}", command=set_work_total, font=PIXEL_FONT, bg=MENU_ACTIVE, fg=MENU_FG
            ).pack(side=tk.LEFT, padx=2)

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
        id_line = f"\n你的编号：{self.pet_id}" if PET_ID_FEATURE and self.pet_id is not None else ""
        self._show_toast(
            f"邀请对战需要联机服务器\n"
            f"（匹配/房间/同步尚未接入）{id_line}\n"
            f"可先体验「练习对战」~",
            "#888888",
            duration_ms=5500,
        )

    def _close_rhyme_fight(self) -> None:
        if self.rhyme_fight_job:
            try:
                self.root.after_cancel(self.rhyme_fight_job)
            except Exception:
                pass
            self.rhyme_fight_job = None
        if self.rhyme_fight_win and self.rhyme_fight_win.winfo_exists():
            self.rhyme_fight_win.destroy()
        self.rhyme_fight_win = None

    def _open_rhyme_fight(self) -> None:
        self._hide_main_menu()
        self._start_game_countdown(self._begin_rhyme_fight)

    def _begin_rhyme_fight(self) -> None:
        self._close_rhyme_fight()
        state = {
            "player_hp": 100,
            "enemy_hp": 100,
            "blocking": False,
            "log": "莱姆：来切磋一下吧！",
            "over": False,
        }

        self.rhyme_fight_win = tk.Toplevel(self.root)
        self.rhyme_fight_win.title("莱姆 · 练习对战")
        self.rhyme_fight_win.attributes("-topmost", True)
        self.rhyme_fight_win.configure(bg=MENU_BG)
        self.rhyme_fight_win.geometry(f"+{self.x + self.display_size + 16}+{self.y}")
        self.rhyme_fight_win.protocol("WM_DELETE_WINDOW", self._close_rhyme_fight)

        frame = tk.Frame(self.rhyme_fight_win, bg=MENU_BG, padx=12, pady=10)
        frame.pack()
        tk.Label(frame, text="莱姆 · 练习对战", font=PIXEL_FONT, fg=PIXEL_COLOR, bg=MENU_BG).pack(anchor=tk.W)
        hp_label = tk.Label(frame, text="", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG)
        hp_label.pack(anchor=tk.W, pady=(6, 4))
        log_label = tk.Label(frame, text="", font=PIXEL_FONT, fg="#aaaaaa", bg=MENU_BG, wraplength=260, justify=tk.LEFT)
        log_label.pack(anchor=tk.W, pady=(0, 8))

        btn_row = tk.Frame(frame, bg=MENU_BG)
        btn_row.pack(fill=tk.X)

        def refresh() -> None:
            hp_label.config(text=f"你 {state['player_hp']} HP    莱姆 {state['enemy_hp']} HP  [{self.difficulty}]")
            log_label.config(text=state["log"])

        def end_fight(won: bool) -> None:
            if state["over"]:
                return
            state["over"] = True
            if won:
                self.mood = min(100, self.mood + 5)
                state["log"] = "你赢了！莱姆：下次我不会输的…"
                self._add_diary_entry("莱姆练习对战：胜利", auto=True)
            else:
                self.mood = max(0, self.mood - 2)
                state["log"] = "输了…莱姆：承让啦~"
                self._add_diary_entry("莱姆练习对战：失败", auto=True)
            self._refresh_panel()
            refresh()
            self.root.after(1600, self._close_rhyme_fight)

        def player_attack(*, special: bool = False) -> None:
            if state["over"]:
                return
            mult = self._fight_player_mult
            if special:
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
                msg = f"莱姆重击！{dmg} 伤害"
            elif action == "feint":
                dmg = int(8 * em)
                msg = f"莱姆佯攻 {dmg} 伤害"
            else:
                dmg = int(12 * em)
                msg = f"莱姆攻击 {dmg} 伤害"
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
        tk.Button(
            btn_row,
            text="必杀",
            command=lambda: player_attack(special=True),
            font=PIXEL_FONT,
            bg="#884444",
            fg=MENU_FG,
        ).pack(side=tk.LEFT, padx=2)
        refresh()
        self.rhyme_fight_job = self.root.after(1500, enemy_turn)

    def _close_typing_game(self) -> None:
        if self.typing_game_job:
            try:
                self.root.after_cancel(self.typing_game_job)
            except Exception:
                pass
            self.typing_game_job = None
        if self.typing_game_win and self.typing_game_win.winfo_exists():
            self.typing_game_win.destroy()
        self.typing_game_win = None
        self._typing_mood_cache.clear()

    def _typing_mood_photo(self, grade: str) -> ImageTk.PhotoImage:
        if grade in self._typing_mood_cache:
            return self._typing_mood_cache[grade]
        filename = TYPING_MOOD_FILES.get(grade, "stand.jpg")
        ref = _reference_scale(TYPING_MOOD_SIZE)
        photo = ImageTk.PhotoImage(_get_processed_canvas(filename, TYPING_MOOD_SIZE, ref))
        self._typing_mood_cache[grade] = photo
        return photo

    def _start_typing_game(self, lang: str) -> None:
        self._hide_main_menu()
        if lang == JAPANESE_LANG_LABEL and not _japanese_bank_available():
            self._show_toast("此功能暂不开放", "#ff8844")
            return
        pool = _load_typing_bank(lang)
        if not pool:
            self._show_toast("该语言词库为空", "#ff8844")
            return
        self._start_game_countdown(lambda: self._begin_typing_game(lang))

    def _begin_typing_game(self, lang: str) -> None:
        pool = _load_typing_bank(lang)
        self._close_typing_game()
        end_ms = int(time.time() * 1000) + TYPING_GAME_MS
        state = {"score": 0, "typed": "", "phase": 0, "done": False}
        display, target = random.choice(pool)

        self.typing_game_win = tk.Toplevel(self.root)
        self.typing_game_win.title(f"打字 · {lang}")
        self.typing_game_win.attributes("-topmost", True)
        self.typing_game_win.configure(bg=MENU_BG)
        self.typing_game_win.geometry(f"+{self.x + self.display_size + 12}+{max(0, self.y - 20)}")
        self.typing_game_win.protocol("WM_DELETE_WINDOW", self._close_typing_game)

        frame = tk.Frame(self.typing_game_win, bg=MENU_BG, padx=12, pady=10)
        frame.pack()
        mood_row = tk.Frame(frame, bg=MENU_BG)
        mood_row.pack(fill=tk.X, pady=(0, 6))
        mood_label = tk.Label(mood_row, bg=MENU_BG)
        mood_label.pack()
        tk.Label(frame, text=f"打字 · {lang}（30s）", font=PIXEL_FONT, fg=PIXEL_COLOR, bg=MENU_BG).pack(anchor=tk.W)
        grade_bar = tk.Canvas(frame, width=300, height=TYPING_GRADE_BAR_H, bg=MENU_BG, highlightthickness=0)
        grade_bar.pack(fill=tk.X, pady=(4, 6))
        timer_label = tk.Label(frame, text="30s", font=PIXEL_FONT, fg="#ffcc44", bg=MENU_BG)
        timer_label.pack(anchor=tk.W)
        score_label = tk.Label(frame, text="得分 0  评级 D", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG)
        score_label.pack(anchor=tk.W)
        word_label = tk.Label(frame, text=f"输入：{display}", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG)
        word_label.pack(anchor=tk.W, pady=(6, 4))
        kb = tk.Canvas(frame, width=300, height=92, bg="#222233", highlightthickness=0)
        kb.pack(pady=4)
        hint = tk.Label(frame, text="请对照键盘输入（支持拼音/英文）", font=PIXEL_FONT, fg="#888888", bg=MENU_BG)
        hint.pack(anchor=tk.W)
        entry = tk.Entry(frame, width=28, font=PIXEL_FONT)
        entry.pack(pady=4)
        result = tk.Label(frame, text="", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG)
        result.pack(pady=2)

        def next_word() -> None:
            d, t = random.choice(pool)
            state["display"] = d
            state["target"] = t.lower()
            state["typed"] = ""
            word_label.config(text=f"输入：{d}")
            entry.delete(0, tk.END)

        state["display"] = display
        state["target"] = target.lower()

        def update_grade_ui() -> None:
            grade = _typing_grade(state["score"])
            score_label.config(text=f"得分 {state['score']}  评级 {grade}")
            _draw_typing_grade_bar(grade_bar, 300, TYPING_GRADE_BAR_H, state["score"])
            photo = self._typing_mood_photo(grade)
            mood_label.config(image=photo)
            mood_label.image = photo

        def refresh_kb() -> None:
            nxt = state["target"][len(state["typed"])] if len(state["typed"]) < len(state["target"]) else None
            hk = _key_for_char(nxt) if nxt else None
            _draw_typing_keyboard(kb, 300, 92, hk, state["phase"])
            state["phase"] += 1

        def finish_game() -> None:
            if state["done"]:
                return
            state["done"] = True
            grade = _typing_grade(state["score"])
            self._save_game_record(
                "typing",
                {"lang": lang, "score": state["score"], "grade": grade, "difficulty": self.difficulty},
            )
            self.mood = min(100, self.mood + min(5, state["score"] // 4))
            self._refresh_panel()
            result.config(text=f"时间到！得分 {state['score']}  评级 {grade}", fg="#88ccff")
            update_grade_ui()
            self._show_speech_dialog(f"打字结束~ 评级 {grade}！", auto_hide_ms=2800)
            self.root.after(2200, self._close_typing_game)

        def tick_timer() -> None:
            if state["done"] or not self.typing_game_win or not self.typing_game_win.winfo_exists():
                return
            left = max(0, end_ms - int(time.time() * 1000))
            timer_label.config(text=f"{left // 1000}s")
            refresh_kb()
            if left <= 0:
                finish_game()
                return
            self.typing_game_job = self.root.after(120, tick_timer)

        def on_type(_event=None) -> None:
            if state["done"]:
                return
            raw = entry.get()
            state["typed"] = raw.lower().strip()
            tgt = state["target"]
            if state["typed"] == tgt or raw.strip() == state["display"]:
                state["score"] += 1
                update_grade_ui()
                result.config(text="正确！", fg="#88dd88")
                next_word()
            elif not tgt.startswith(state["typed"]) and state["typed"]:
                result.config(text="不对哦~", fg="#ffaa44")
            else:
                result.config(text="", fg=MENU_FG)
            refresh_kb()

        entry.bind("<KeyRelease>", on_type)
        entry.focus_set()
        refresh_kb()
        tick_timer()

    def _open_vocab_game(self, lang: str = "英语") -> None:
        self._hide_main_menu()
        if lang == JAPANESE_LANG_LABEL and not _japanese_bank_available():
            self._show_toast("此功能暂不开放", "#ff8844")
            return
        if self.mode == "free" and self._vocab_daily_remaining() <= 0:
            self._show_toast("自由模式下背单词今日已达 3 次上限~", "#ff8844")
            return
        if self.mode == "free":
            self._consume_vocab_daily()
        words = _load_vocab_bank(lang)
        if len(words) < 4:
            self._show_toast(f"{lang} 词库不足 4 条", "#ff8844")
            return
        self._vocab_lang = lang
        self._vocab_pool = words
        if self.vocab_game_win and self.vocab_game_win.winfo_exists():
            self.vocab_game_win.destroy()
        self._start_game_countdown(self._vocab_game_round)

    def _vocab_game_round(self) -> None:
        if self.vocab_game_win and self.vocab_game_win.winfo_exists():
            self.vocab_game_win.destroy()
        words = getattr(self, "_vocab_pool", self.vocab_words)
        if len(words) < 4:
            return
        item = random.choice(words)
        correct = item.get("meaning", "？")
        pool = [correct]
        for other in random.sample(words, min(len(words), 10)):
            m = other.get("meaning", "")
            if m and m not in pool:
                pool.append(m)
            if len(pool) >= 4:
                break
        while len(pool) < 4:
            pool.append("（干扰项）")
        options = random.sample(pool[:4], min(4, len(pool)))
        lang = getattr(self, "_vocab_lang", "英语")

        self.vocab_game_win = tk.Toplevel(self.root)
        self.vocab_game_win.title(f"背单词 · {lang}")
        self.vocab_game_win.attributes("-topmost", True)
        self.vocab_game_win.configure(bg=MENU_BG)
        self.vocab_game_win.geometry(f"+{self.x + self.display_size + 12}+{self.y + 40}")

        frame = tk.Frame(self.vocab_game_win, bg=MENU_BG, padx=12, pady=10)
        frame.pack()
        tk.Label(frame, text=f"背单词 · {lang}", font=PIXEL_FONT, fg=PIXEL_COLOR, bg=MENU_BG).pack(anchor=tk.W)
        tk.Label(
            frame, text=f"「{item['word']}」的意思是？", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG
        ).pack(anchor=tk.W, pady=(8, 6))
        status = tk.Label(frame, text="", font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG)
        status.pack(pady=4)

        def choose(opt: str) -> None:
            if opt == correct:
                status.config(text="答对啦！", fg="#88dd88")
                self.mood = min(100, self.mood + 3)
                self._refresh_panel()
                self._add_diary_entry(f"背单词正确：{item['word']}", auto=True)
                self._save_game_record(
                    "vocab",
                    {"lang": lang, "word": item["word"], "correct": True, "difficulty": self.difficulty},
                )
                self.root.after(800, self._vocab_game_round)
            else:
                status.config(text=f"不对哦，是：{correct}", fg="#ff8844")
                self._save_game_record(
                    "vocab",
                    {"lang": lang, "word": item["word"], "correct": False, "difficulty": self.difficulty},
                )
                self.root.after(1200, self._vocab_game_round)

        for opt in options:
            tk.Button(
                frame,
                text=opt[:18],
                command=lambda o=opt: choose(o),
                font=PIXEL_FONT,
                bg=MENU_ACTIVE,
                fg=MENU_FG,
                wraplength=200,
            ).pack(fill=tk.X, pady=2)

    def _open_about(self) -> None:
        self._hide_main_menu()
        if self.about_win and self.about_win.winfo_exists():
            self.about_win.lift()
            return
        self.about_win = tk.Toplevel(self.root)
        self.about_win.title("关于")
        self.about_win.attributes("-topmost", True)
        self.about_win.configure(bg=MENU_BG)
        self.about_win.geometry(f"+{self.x}+{self.y + self.display_size + 8}")
        frame = tk.Frame(self.about_win, bg=MENU_BG, padx=14, pady=12)
        frame.pack()
        tk.Label(frame, text="关于 Vpet", font=PIXEL_FONT, fg=PIXEL_COLOR, bg=MENU_BG).pack(anchor=tk.W)
        tk.Label(frame, text=ABOUT_TEXT, font=PIXEL_FONT, fg=MENU_FG, bg=MENU_BG, justify=tk.LEFT, wraplength=280).pack(
            anchor=tk.W, pady=(8, 0)
        )
        if PET_ID_FEATURE and self.pet_id is not None:
            tk.Label(frame, text=f"本机编号：{self.pet_id}", font=PIXEL_FONT, fg="#aaaaaa", bg=MENU_BG).pack(
                anchor=tk.W, pady=(8, 0)
            )

    def _confirm_reset_settings(self) -> None:
        self._hide_main_menu()
        win = tk.Toplevel(self.root)
        win.title("重置确认")
        win.attributes("-topmost", True)
        win.configure(bg=MENU_BG)
        win.geometry(f"+{self.x}+{self.y + self.display_size + 8}")
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

    def _reset_all_settings(self) -> None:
        self._close_ai_chat()
        if self.schedule_win and self.schedule_win.winfo_exists():
            self.schedule_win.destroy()
            self.schedule_win = None
        if self.diary_win and self.diary_win.winfo_exists():
            self.diary_win.destroy()
            self.diary_win = None
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
            "mode": "normal",
            "music_volume": 70,
            "volume": 70,
            "sfx_volume": 80,
            "voice_volume": 80,
            "muted": False,
            "custom_path": "",
        }
        _save_music_config(self.music_config)
        self.app_config = {
            "font_size": 12,
            "display_size": DEFAULT_SIZE,
            "display_preset": "中",
            "difficulty": "中",
            "seen_hints": {},
            "work_box_total": WORK_BOX_TOTAL_DEFAULT,
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
                ("工作", self._start_work),
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
        if self.panel_hide_job:
            self.root.after_cancel(self.panel_hide_job)
            self.panel_hide_job = None
        if self.panel_win and self.panel_win.winfo_exists():
            self.panel_win.destroy()
        self.panel_win = None

    def _toggle_panel(self) -> None:
        if self.panel_win and self.panel_win.winfo_exists():
            self._close_panel()
            return

        self.panel_win = tk.Toplevel(self.root)
        self.panel_win.overrideredirect(True)
        self.panel_win.attributes("-topmost", True)
        self.panel_win.configure(bg="#1a1a1a")

        frame = tk.Frame(self.panel_win, bg="#1a1a1a", padx=10, pady=8)
        frame.pack()

        tk.Label(frame, text="面板", font=PIXEL_FONT, fg=PIXEL_COLOR, bg="#1a1a1a").pack(anchor=tk.W)

        self.stamina_bar = tk.Canvas(frame, width=160, height=16, bg="#333333", highlightthickness=0)
        self.stamina_bar.pack(pady=(8, 4))
        self.mood_bar = tk.Canvas(frame, width=160, height=16, bg="#333333", highlightthickness=0)
        self.mood_bar.pack(pady=(0, 4))

        self.stamina_label = tk.Label(frame, text="", font=PIXEL_FONT, fg=MENU_FG, bg="#1a1a1a")
        self.stamina_label.pack(anchor=tk.W)
        self.mood_label = tk.Label(frame, text="", font=PIXEL_FONT, fg=MENU_FG, bg="#1a1a1a")
        self.mood_label.pack(anchor=tk.W)
        self.backpack_icons_frame = tk.Frame(frame, bg="#1a1a1a")
        self.backpack_icons_frame.pack(anchor=tk.W, pady=(6, 0))
        tk.Label(self.backpack_icons_frame, text="🎒 食物", font=PIXEL_FONT, fg="#ffcc66", bg="#1a1a1a").pack(
            anchor=tk.W
        )
        self.backpack_grid = tk.Frame(self.backpack_icons_frame, bg="#1a1a1a")
        self.backpack_grid.pack(anchor=tk.W, pady=(2, 0))

        self._refresh_panel()
        self._reposition_panel()
        self.panel_hide_job = self.root.after(PANEL_AUTO_CLOSE_MS, self._close_panel)

    def _reposition_panel(self) -> None:
        if not self.panel_win or not self.panel_win.winfo_exists():
            return
        self.panel_win.update_idletasks()
        pw = max(self.panel_win.winfo_width(), 180)
        ph = max(self.panel_win.winfo_height(), 120)
        px, py = self._panel_popup_pos(pw, ph)
        self.panel_win.geometry(f"+{px}+{py}")

    def _draw_bar(self, canvas: tk.Canvas, value: int, color: str) -> None:
        canvas.delete("all")
        width = int(160 * value / 100)
        canvas.create_rectangle(0, 0, 160, 16, fill="#333333", outline="")
        canvas.create_rectangle(0, 0, width, 16, fill=color, outline="")

    def _refresh_panel(self) -> None:
        if not self.panel_win or not self.panel_win.winfo_exists():
            return
        self._draw_bar(self.stamina_bar, self.stamina, "#44aa44")
        self._draw_bar(self.mood_bar, self.mood, "#4488ff")
        self.stamina_label.config(text=f"体力  {self.stamina}")
        mood_label, mood_color = _mood_tier_label(self.mood)
        self.mood_label.config(text=f"心情  {self.mood}  {mood_label}", fg=mood_color)
        if self.backpack_grid and self.backpack_grid.winfo_exists():
            for w in self.backpack_grid.winfo_children():
                w.destroy()
            col = 0
            food_items = sorted(
                FOODS.items(),
                key=lambda item: (item[1]["mood"], item[1]["stamina"]),
                reverse=True,
            )
            for food_id, info in food_items:
                count = self.food_inventory.get(food_id, 0)
                if count <= 0:
                    continue
                cell = tk.Frame(self.backpack_grid, bg="#1a1a1a", padx=3, pady=2)
                cell.grid(row=col // 3, column=col % 3, sticky=tk.NW, padx=2, pady=2)
                icon = tk.Canvas(cell, width=22, height=24, bg="#1a1a1a", highlightthickness=0)
                icon.pack()
                _draw_pixel_food(icon, food_id, 2, 2, px=2)
                tk.Label(cell, text=f"{info['label']}×{count}", font=PIXEL_FONT, fg="#ffcc66", bg="#1a1a1a").pack()
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
        self._reposition_panel()

    def _cancel_game_countdown(self) -> None:
        self._countdown_token = getattr(self, "_countdown_token", 0) + 1
        self._countdown_active = False

    def _start_game_countdown(self, on_ready, *, title: str = "") -> None:
        self._cancel_game_countdown()
        self._countdown_active = True
        token = self._countdown_token
        steps = ("3", "2", "1", "开始!")

        def step(i: int = 0) -> None:
            if token != self._countdown_token:
                return
            if i >= len(steps):
                self._countdown_active = False
                on_ready()
                return
            label = steps[i]
            text = f"{title} {label}" if title else label
            self._show_toast(text, "#ffcc44", duration_ms=GAME_COUNTDOWN_STEP_MS)
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
        self.toast_win.geometry(f"+{self.x + self.display_size + 8}+{toast_y}")
        self.root.after(duration_ms, self._hide_toast)

    def _hide_toast(self) -> None:
        if self.toast_win and self.toast_win.winfo_exists():
            self.toast_win.destroy()
        self.toast_win = None

    def _stamina_tick(self) -> None:
        if self.root.winfo_exists():
            params = self._difficulty_params()
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
            self.root.after(int(params["stamina_tick_ms"]), self._stamina_tick)

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

    def _animate_like_glow(self) -> None:
        if not self.like_fx_canvas or self.action_name != "like":
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

    def _place_wink_fx(self) -> None:
        if not self.wink_fx_win or not self.wink_fx_win.winfo_exists():
            return
        pad = 20
        display_y = self.y + self.click_bounce_offset
        self.wink_fx_win.geometry(f"+{self.x - pad}+{display_y - pad}")

    def _animate_wink_fx(self) -> None:
        if not self.wink_fx_canvas or self.action_name != "wink":
            self.wink_fx_job = None
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
        self._place_wink_fx()
        self._animate_wink_fx()

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

    def _hide_shy_fx(self) -> None:
        if self.shy_fx_win and self.shy_fx_win.winfo_exists():
            self.shy_fx_win.destroy()
        self.shy_fx_win = None
        self.shy_fx_canvas = None

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

    def _interact_flair(self, action: str, *, banter: bool = True, show_fx: bool = True) -> None:
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
        if not silent:
            self._show_toast("噗~ 金目来陪你啦！", "#88ccff", duration_ms=1500)

    def _mini_pet_side_target(self, entry: dict) -> tuple[float, float]:
        size = entry["size"]
        gap = MINI_PET_SIDE_GAP
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
        target_x, target_y = self._mini_pet_side_target(entry)
        mx, my = entry["x"], entry["y"]
        dx = target_x - mx
        dy = target_y - my
        dist = math.hypot(dx, dy)
        game_mode = self.mode == "game"
        if game_mode:
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
        elif game_mode and dist > 0.5:
            mx, my = target_x, target_y
        else:
            mx, my = target_x, target_y

        main_moving = self._mini_pet_main_moving(entry)
        use_walk = (not game_mode) and (mini_moving or main_moving)

        if use_walk:
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
        win.geometry(f"+{int(mx)}+{int(my)}")
        self._place_mini_pet_music_wave(entry)
        entry["follow_job"] = self.root.after(follow_ms, lambda e=entry: self._mini_pet_follow_tick(e))

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
        w = max(56, entry["size"])
        h = 22
        wave_win = tk.Toplevel(self.root)
        wave_win.overrideredirect(True)
        wave_win.attributes("-topmost", False)
        wave_win.configure(bg="magenta")
        wave_win.wm_attributes("-transparentcolor", "magenta")
        wave_canvas = tk.Canvas(wave_win, width=w, height=h, bg="magenta", highlightthickness=0)
        wave_canvas.pack()
        entry["wave_win"] = wave_win
        entry["wave_canvas"] = wave_canvas
        entry["wave_phase"] = 0
        self._place_mini_pet_music_wave(entry)
        self._animate_mini_pet_music_wave(entry)

    def _place_mini_pet_music_wave(self, entry: dict) -> None:
        wave_win = entry.get("wave_win")
        if not wave_win or not wave_win.winfo_exists():
            return
        w = max(56, entry["size"])
        wx = int(entry["x"] + (entry["size"] - w) // 2)
        wy = int(entry["y"] + entry["size"] + 2)
        wave_win.geometry(f"+{wx}+{wy}")

    def _place_all_mini_pet_waves(self) -> None:
        for entry in self.mini_pets:
            self._place_mini_pet_music_wave(entry)

    def _animate_mini_pet_music_wave(self, entry: dict) -> None:
        canvas = entry.get("wave_canvas")
        if not canvas or not self.music_sprite_mode or not self.companion_bar_enabled:
            self._stop_mini_pet_music_wave(entry)
            return
        w = canvas.winfo_width() or max(56, entry["size"])
        h = canvas.winfo_height() or 22
        beat = 1.0
        try:
            import pygame

            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pos = pygame.mixer.music.get_pos()
                if pos >= 0:
                    beat = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(pos * 0.014))
        except Exception:
            pass
        _draw_music_wave(canvas, w, h, entry.get("wave_phase", 0), beat=beat)
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
        if self.dragging or self.state == "work":
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
        if self.dragging or self.state == "work":
            return
        self._interrupt_current_interaction()
        self.state = "action"
        self.action_name = "like"
        self._interact_flair("like", banter=True)
        self._play_expression_pop()
        self._set_image(self.sprites.like)
        self._show_like_fx()
        self._schedule_action_end(action="like", callback=self._after_simple_expression)

    def _play_expression_wink(self) -> None:
        if self.dragging or self.state == "work":
            return
        self._interrupt_current_interaction()
        self.state = "action"
        self.action_name = "wink"
        self._interact_flair("wink", banter=False)
        self._play_expression_pop()
        self._set_image(self.sprites.wink)
        self._show_wink_fx()
        self._schedule_action_end(action="wink", callback=self._after_simple_expression)

    def _play_expression_sprite(self, name: str, sprite: ImageTk.PhotoImage, *, banter: bool = True) -> None:
        if self.dragging or self.state == "work":
            return
        self._interrupt_current_interaction()
        self.state = "action"
        self.action_name = name
        self._interact_flair(name, banter=banter)
        self._play_expression_pop()
        self._set_image(sprite)
        self._schedule_action_end(action=name, callback=self._after_simple_expression)

    def _play_yesno_judge(self) -> None:
        if self.dragging or self.state == "work":
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
        if self.dragging or self.state != "action":
            return
        self._clear_all_action_fx()
        self._cancel_action_end()
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
            self._place_window()
            self._schedule_action_end(action="angry", callback=self._after_simple_expression)
            return
        if 3 <= step <= 8:
            self.angry_lift_offset = min(ANGRY_WALK_MAX_LIFT, self.angry_lift_offset + ANGRY_WALK_UP_PER_STEP)
            self.y = self.angry_base_y - self.angry_lift_offset
        elif step < 3:
            self.y = self.angry_base_y
        self._set_image(sequence[step])
        self._place_window()
        self.angry_anim_job = self.root.after(ANGRY_FRAME_MS, lambda: self._angry_anim_step(step + 1))

    def _cancel_expose_qte(self) -> None:
        self._cancel_game_countdown()
        self.expose_qte_active = False
        self.expose_session_active = False
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
        try:
            self.root.unbind_all("<Return>")
        except Exception:
            pass

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
        max_x = max(margin, sw - combo_w - margin)
        max_y = max(margin, sh - combo_h - margin)
        base_x = random.randint(margin, max_x)
        base_y = random.randint(margin, max_y)
        qte_left = random.choice([True, False])
        if qte_left and base_x >= qte_size + gap + margin:
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
        self._expose_blue_span = span
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
        self.expose_qte_win.geometry(f"+{qx}+{qy}")
        self.expose_qte_active = True
        self.expose_qte_done = False
        self._expose_qte_tick()

    def _expose_qte_tick(self) -> None:
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
        self._hide_main_menu()
        if self.mode == "quiet" and self.state == "rest":
            self._stop_rest_bobble()
        self.state = "action"
        self.action_name = "expose"
        self.expose_hit_streak = 0
        self._cancel_expose_qte()
        self.expose_session_active = False
        _, base = self._expose_medium_params()
        self.expose_pointer_base_speed = base

        def begin() -> None:
            if self.action_name != "expose":
                return
            self.expose_session_active = True
            self.root.bind_all("<Return>", self._expose_qte_enter, add="+")
            try:
                self.root.focus_force()
            except Exception:
                pass
            self._spawn_expose_glitch_round()

        self._start_game_countdown(begin, title="暴露")

    def _resolve_expose_qte_hit(self, success: bool) -> None:
        if self.action_name != "expose" or not self.expose_session_active:
            return
        self.expose_qte_active = False
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
            self._show_speech_dialog("暴露失败…", auto_hide_ms=2200, color="#ff6666")
            self.mood = max(0, self.mood - 1)
            self._refresh_panel()
            self._finish_expose_session(cleared=False)
            return

    def _finish_expose_session(self, *, cleared: bool) -> None:
        self.expose_session_active = False
        self._cancel_expose_qte()
        if cleared:
            self.mood = min(100, self.mood + 5)
            self._refresh_panel()
            self._show_speech_dialog("暴露通关！", auto_hide_ms=3200, color="#44ff88")
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
        if self.dragging:
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
        if self.dragging or self.mode != "follow" or self.state in ("action", "sleep"):
            self.root.after(100, self._follow_tick)
            return
        if self.follow_dizzy:
            self.root.after(100, self._follow_tick)
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
        step = self._follow_dir_rotation(self.follow_last_dir, direction)
        if step == 0:
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

    def _animate_follow_dizzy_fx(self) -> None:
        if not self.follow_dizzy_fx_canvas or not self.follow_dizzy:
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
        if self.dragging or self.mode != "follow" or self.state != "walk":
            self.follow_animating = False
            return

        frames = self._walk_sprites[self.direction]
        self._set_image(frames[self.walk_frame % 2])
        self.walk_frame += 1
        self.root.after(WALK_FRAME_MS, self._follow_animate)

    def _follow_move(self) -> None:
        if self.dragging or self.mode != "follow" or self.state in ("action", "sleep"):
            self.root.after(FOLLOW_MOVE_INTERVAL_MS, self._follow_tick)
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
            self.root.after(FOLLOW_MOVE_INTERVAL_MS, self._follow_tick)
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

        self.root.after(FOLLOW_MOVE_INTERVAL_MS, self._follow_tick)

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
        diff_label = f"难度：{self.difficulty} ▶"
        self._show_sub_menu(
            [
                ("操作说明", self._open_operation_guide),
                ("画廊", self._open_gallery),
                ("我的 ▶", self._open_my_menu),
                ("设置 ▶", self._open_panel_settings),
                (diff_label, self._open_difficulty_menu),
                ("AI 对话", self._toggle_ai_chat),
                ("重置", self._confirm_reset_settings),
                ("关于", self._open_about),
                ("退出", self._on_close),
            ],
            offset_x=240,
        )

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
            self._sprite_cache[new_size] = SpriteSet(new_size)
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
        self._reposition_panel()
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
        self.root.update_idletasks()

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
        self.root.after(CLICK_BOUNCE_MS, self._click_bounce_down)

    def _click_bounce_down(self) -> None:
        self.click_bounce_offset = 0
        self.click_bouncing = False
        self._place_window()
        self._place_sleep_zzz()
        self._place_ai_chat()

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
        self.state = "drag"
        self.drag_move_start_ms = int(time.time() * 1000)
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
        self.x = event.x_root - self.drag_x
        self.y = event.y_root - self.drag_y
        self._clamp_position()
        self._place_window()
        self._reposition_panel()
        if self.state == "work":
            self._refresh_work_overlay()

    def _on_release(self, _event: tk.Event) -> None:
        if not self.dragging:
            return
        had_move_anim = self.state == "drag"
        self.dragging = False
        self._stop_drag_move()
        if self.mode == "game":
            self.state = "game"
            self._set_image(self.sprites.stand)
            return
        if self.state == "work":
            self._set_image(self.sprites.work_stand if not self.work_carrying else self._walk_sprites[self.direction][0])
            self._refresh_work_overlay()
            if not self.work_animating:
                self.work_animating = True
                self._work_animate()
            self._work_move_step()
            return
        if self.mode == "quiet":
            self.state = "rest"
            self.rest_base_y = self.y
            self._set_image(self.sprites.sleep[1])
            self._show_sleep_zzz()
            self._schedule_rest_bobble()
        elif had_move_anim:
            self._play_move_land()
        else:
            self.state = "stand"
            self._set_image(self.sprites.stand)
            delay = random.randint(800, 2000)
            self.idle_job = self.root.after(delay, self._resume_idle)

    def _play_move_land(self) -> None:
        self.move_land_base_y = self.y
        land_px = self.display_size // 3
        self.y = self.move_land_base_y + land_px
        self.state = "stand"
        self._set_image(self.sprites.stand)
        self._place_window()
        self._reposition_panel()
        tok = self.interaction_token
        self.move_land_job = self.root.after(
            MOVE_LAND_MS, lambda t=tok: self._move_land_settle(t)
        )

    def _move_land_settle(self, tok: int | None = None) -> None:
        if tok is not None and tok != self.interaction_token:
            return
        self.move_land_job = None
        self._place_window()
        self._reposition_panel()
        delay = random.randint(800, 2000)
        self.idle_job = self.root.after(delay, self._resume_idle)

    def _on_close(self, _event=None) -> None:
        if self._closing:
            return
        self._closing = True
        self._hide_main_menu()
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
            EXIT_DISSOLVE_MAIN_COLORS,
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
                    EXIT_DISSOLVE_COMPANION_COLORS,
                    on_hide=lambda label=lbl: label.pack_forget() if label else None,
                    on_done=one_done,
                )

    def _run_exit_dissolve_at(
        self,
        x: int,
        y: int,
        size: int,
        colors: tuple[str, ...],
        *,
        on_hide=None,
        on_done=None,
    ) -> None:
        if on_hide:
            on_hide()
        px = max(3, size // 24) * EXIT_DISSOLVE_PX_SCALE
        cols = max(4, size // px)
        rows = max(4, size // px)
        particles: list[dict] = []
        for row in range(rows):
            for col in range(cols):
                particles.append(
                    {
                        "x": col * px + random.randint(-1, 1),
                        "y": row * px + random.randint(-1, 1),
                        "vx": random.uniform(-2.8, 2.8),
                        "vy": random.uniform(-1.2, 3.6),
                        "life": random.randint(EXIT_DISSOLVE_FRAMES // 2, EXIT_DISSOLVE_FRAMES),
                        "color": random.choice(colors),
                        "size": px,
                    }
                )
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
            canvas.delete("all")
            alive = False
            for p in particles:
                if p["life"] <= 0:
                    continue
                alive = True
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                p["vy"] += 0.08
                p["life"] -= 1
                alpha = max(0.15, p["life"] / EXIT_DISSOLVE_FRAMES)
                sz = max(2, int(p["size"] * alpha))
                canvas.create_rectangle(
                    p["x"],
                    p["y"],
                    p["x"] + sz,
                    p["y"] + sz,
                    fill=p["color"],
                    outline="",
                )
            frame["n"] += 1
            if alive and frame["n"] < EXIT_DISSOLVE_FRAMES + 8:
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
        if self.schedule_win and self.schedule_win.winfo_exists():
            self.schedule_win.destroy()
        self._stop_drag_move()
        self._stop_rest_bobble()
        self._cancel_action_end()
        if self.rest_peek_job:
            self.root.after_cancel(self.rest_peek_job)
            self.rest_peek_job = None
        self._stop_call_audio()
        self._close_rhyme_fight()
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
        global _type_sound
        sound = _get_type_sound()
        if not sound:
            _type_sound = None
            sound = _get_type_sound()
        self._play_sound_with_volume(sound, "voice")

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
        self.speech_dialog.geometry(f"+{self.x}+{self.y + self.display_size + 8}")
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
        if char not in (" ", "\n"):
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
        scale = max(3, int(px * FOOD_FX_SIZE_MULT))
        food_extent = scale * 5
        base_x = max(pad // 2, size - food_extent - pad // 4)
        base_y = size // 2 + scale
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
        if self.dragging or self.state == "work":
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

    def _resume_idle(self) -> None:
        if self.dragging:
            return
        if self.state == "sleep" or self.sleep_interact_active:
            return
        if self.mode == "game":
            return
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
        return (
            (self.mode == "quiet" and self.state == "rest")
            or self.sleep_interact_active
            or (self.state == "sleep" and self.sleep_in_deep)
        )

    def _animate_sleep_zzz(self) -> None:
        if not self.sleep_zzz_canvas or not self._should_show_zzz():
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
        self._trigger_mood_action(random.choice(actions))
        return True

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
        random.choice(pool)()
        return True

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
        delay = random.randint(1200, 3500)
        tok = self.interaction_token
        self.idle_job = self.root.after(delay, lambda t=tok: self._idle_to_walk(t))

    def _idle_to_walk(self, tok: int) -> None:
        if tok != self.interaction_token:
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
        if tok != self.interaction_token:
            return
        self.walk_anim_job = None
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

    def _game_spawn_box(self) -> None:
        if self.mode != "game" or self._game_time_left_ms() <= 0:
            return
        sw = self.root.winfo_screenwidth()
        margin = GAME_BOX_SIZE
        bx = random.randint(margin, max(margin, sw - margin))
        food_id = random.choice(list(FOODS.keys()))
        size = GAME_BOX_SIZE
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg="magenta")
        win.wm_attributes("-transparentcolor", "magenta")
        canvas = tk.Canvas(win, width=size, height=size, bg="magenta", highlightthickness=0)
        canvas.pack()
        px = max(4, size // 8)
        draw_x = max(2, (size - px * 4) // 2)
        draw_y = max(2, (size - px * 4) // 2)
        _draw_pixel_food(canvas, food_id, draw_x, draw_y, px=px)
        win.geometry(f"+{bx}+{-GAME_BOX_SIZE}")
        self.game_boxes.append({"x": bx, "y": -GAME_BOX_SIZE, "win": win, "food_id": food_id})
        self.game_spawn_job = self.root.after(self._game_spawn_ms, self._game_spawn_box)

    def _game_tick(self) -> None:
        if self.mode != "game":
            return

        if self._game_time_left_ms() <= 0:
            self._finish_game()
            return

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
            box["y"] += self._game_box_speed
            win.geometry(f"+{int(box['x'])}+{int(box['y'])}")
            box_cx = box["x"] + GAME_BOX_SIZE // 2
            box_cy = box["y"] + GAME_BOX_SIZE // 2
            dist = math.hypot(box_cx - pet_cx, box_cy - pet_cy)
            if dist < GAME_NEAR_DIST:
                near_food = True
            if dist < self._game_catch_dist:
                if win.winfo_exists():
                    win.destroy()
                food_id = box.get("food_id", random.choice(list(FOODS.keys())))
                self._add_food_to_inventory(food_id)
                self.game_catches += 1
                self.game_score += GAME_SCORE_PER_CATCH
                if self.game_catches % 5 == 0:
                    self.mood = min(100, self.mood + 1)
                    self._refresh_panel()
                continue
            if box["y"] > sh + GAME_BOX_SIZE:
                win.destroy()
                self.game_misses += 1
                self.game_score = max(0, self.game_score - GAME_PENALTY_MISS)
                continue
            remaining.append(box)

        self.game_boxes = remaining
        self.game_near_food = near_food
        self._set_image(self.sprites.happy if near_food else self.sprites.stand)
        self.game_tick_job = self.root.after(GAME_TICK_MS, self._game_tick)

    def _start_work(self) -> None:
        if self.dragging or self.state in ("work", "sleep"):
            return
        self._interrupt_current_interaction()
        if self.mode == "game":
            self._stop_game_mode()
            self.mode = "free"

        self._hide_main_menu()
        self._interact_flair("work", banter=True)

        margin = 80
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        max_x = max(margin, sw - self.display_size - margin)
        max_y = max(margin, sh - self.display_size - margin)

        self.work_start_x = random.randint(margin, max_x)
        self.work_start_y = random.randint(margin, max_y)
        for _ in range(20):
            self.work_end_x = random.randint(margin, max_x)
            self.work_end_y = random.randint(margin, max_y)
            if self._dist_to(self.work_end_x + self.display_size // 2, self.work_end_y + self.display_size // 2) > 160:
                break

        self.work_total = self._resolve_work_total()
        self.work_delivered = 0
        self.work_stack = 0
        self.work_has_start_box = True
        self.work_carrying = False
        self.work_phase = "to_start"
        self.work_use_work_sprites = False

        self.state = "work"
        self.walk_frame = 0
        self.x = self.work_start_x
        self.y = self.work_start_y
        self._set_image(self.sprites.work_stand)
        self._place_window()
        self._show_work_overlay()
        self._show_toast(f"搬运任务：{self.work_total} 箱（可拖动旗子）", PIXEL_COLOR, duration_ms=2400)
        self._work_move_step()
        if not self.work_animating:
            self.work_animating = True
            self._work_animate()

    def _resolve_work_total(self) -> int:
        if self.mode == "free":
            total = int(self.app_config.get("work_box_total", WORK_BOX_TOTAL_DEFAULT))
            return max(WORK_TOTAL_SETTING_MIN, min(WORK_TOTAL_SETTING_MAX, total))
        return random.randint(WORK_TOTAL_MIN, WORK_TOTAL_MAX)

    def _work_stack_canvas_size(self, stack_count: int) -> tuple[int, int, int]:
        pad = 40
        cols = max(1, (stack_count + WORK_STACK_COLUMN_MAX - 1) // WORK_STACK_COLUMN_MAX) if stack_count else 1
        rows = min(WORK_STACK_COLUMN_MAX, stack_count) if stack_count else 0
        width = pad * 2 + WORK_PROP_SIZE + max(0, cols - 1) * WORK_STACK_COL_OFFSET
        height = pad * 2 + WORK_PROP_SIZE + max(0, rows) * WORK_STACK_OFFSET
        return width, height, cols

    def _work_box_xy(self, index: int, cols: int, pad: int, canvas_w: int, canvas_h: int) -> tuple[int, int]:
        col = index // WORK_STACK_COLUMN_MAX
        row = index % WORK_STACK_COLUMN_MAX
        group_w = WORK_PROP_SIZE + max(0, cols - 1) * WORK_STACK_COL_OFFSET
        start_x = (canvas_w - group_w) // 2 + WORK_PROP_SIZE // 2
        x = start_x + col * WORK_STACK_COL_OFFSET
        y = canvas_h - pad - WORK_PROP_SIZE - row * WORK_STACK_OFFSET
        return x, y

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

    def _work_flag_press(self, event: tk.Event) -> None:
        if self.state != "work":
            return
        self.work_flag_dragging = True
        self.work_flag_drag_origin = (event.x_root, event.y_root, self.work_end_x, self.work_end_y)

    def _work_flag_motion(self, event: tk.Event) -> None:
        if not self.work_flag_dragging or self.state != "work":
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

    def _work_flag_release(self, _event: tk.Event) -> None:
        self.work_flag_dragging = False

    def _hide_work_overlay(self) -> None:
        self._unbind_work_flag_drag()
        if self.work_overlay and self.work_overlay.winfo_exists():
            self.work_overlay.destroy()
        self.work_overlay = None
        self.work_canvas = None
        self.work_flag_dragging = False

    def _show_work_overlay(self) -> None:
        self._hide_work_overlay()
        width, height, _ = self._work_stack_canvas_size(0)
        self.work_overlay = tk.Toplevel(self.root)
        self.work_overlay.overrideredirect(True)
        self.work_overlay.attributes("-topmost", False)
        self.work_overlay.configure(bg="magenta")
        self.work_overlay.wm_attributes("-transparentcolor", "magenta")
        self.work_overlay.geometry(f"{width}x{height}+0+0")
        self.work_canvas = tk.Canvas(
            self.work_overlay, width=width, height=height, bg="magenta", highlightthickness=0
        )
        self.work_canvas.pack()
        self._bind_work_flag_drag()
        self._refresh_work_overlay()

    def _refresh_work_overlay(self) -> None:
        if not self.work_canvas or not self.work_overlay:
            return
        pad = 40
        stack_count = self.work_stack
        width, height, cols = self._work_stack_canvas_size(stack_count)
        group_w = WORK_PROP_SIZE + max(0, cols - 1) * WORK_STACK_COL_OFFSET
        flag_x = (width - group_w) // 2 + WORK_PROP_SIZE // 2
        flag_y = height - pad

        self.work_canvas.config(width=width, height=height)
        self.work_canvas.delete("all")
        overlay_x = self.work_end_x + self.display_size // 2 - flag_x
        overlay_y = self.work_end_y - height + pad
        self.work_overlay.geometry(f"{width}x{height}+{overlay_x}+{overlay_y}")
        self.work_canvas.create_image(flag_x, flag_y, image=self.sprites.flag_img, anchor=tk.S)
        for i in range(stack_count):
            x, y = self._work_box_xy(i, cols, pad, width, height)
            self.work_canvas.create_image(x, y, image=self.sprites.box_img, anchor=tk.S)

        self._update_work_start_box()
        self.root.lift()

    def _update_work_start_box(self) -> None:
        pad = 40
        size = WORK_PROP_SIZE + pad * 2
        half = WORK_PROP_SIZE // 2

        if self.work_has_start_box and not self.work_carrying:
            sx = self.work_start_x + self.display_size // 2 - half
            sy = self.work_start_y - pad
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
        if self.dragging or self.work_flag_dragging:
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
        step = WORK_MOVE_STEP
        self.x += dx * (WORK_MOVE_STEP // MOVE_STEP)
        self.y += dy * (WORK_MOVE_STEP // MOVE_STEP)
        self._clamp_position()
        self._place_window()
        self._refresh_work_overlay()
        self.root.after(WORK_MOVE_INTERVAL_MS, self._work_move_step)

    def _work_arrived(self) -> None:
        if self.work_phase == "to_start":
            if self.work_has_start_box and not self.work_carrying:
                self.work_carrying = True
                self.work_has_start_box = False
                self._refresh_work_overlay()
                self.work_phase = "to_end"
            elif self.work_delivered >= self.work_total:
                self.work_phase = "finish"
                self._work_move_step()
                return
            else:
                self._set_image(self.sprites.work_stand)
        elif self.work_phase == "to_end":
            if self.work_carrying:
                self.work_carrying = False
                self.work_delivered += 1
                self.work_stack += 1
                self._refresh_work_overlay()
                self.stamina = min(100, self.stamina + 2)
                self.mood = min(100, self.mood + 1)
                self._refresh_panel()
            if self.work_delivered >= self.work_total:
                self.work_phase = "finish"
            else:
                self.work_has_start_box = True
                self.work_phase = "to_start"
                self._refresh_work_overlay()
        self._work_move_step()

    def _finish_work(self) -> None:
        if self.state != "work":
            return
        stack_count = self.work_stack
        self._stop_work_mode()
        self.state = "stand"
        self._set_image(self.sprites.stand)
        self._add_interact_mood()
        self._show_toast(f"工作完成！堆叠 {stack_count} 箱", "#44aa44")
        if self.mode == "quiet":
            self.state = "rest"
            self._set_image(self.sprites.sleep[1])
            self._show_sleep_zzz()
            self._schedule_rest_bobble()
        elif not self._check_mood_happy():
            self._resume_idle()

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
        win_y = max(0, display_y - bulb_y - BULB_HEAD_GAP)
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
        if self.root.winfo_exists():
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
            self.root.after(REMINDER_CHECK_MS, self._reminder_tick)

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
        self.schedule_win.geometry(f"+{self.x}+{self.y + self.display_size + 8}")

        frame = tk.Frame(self.schedule_win, bg=MENU_BG, padx=10, pady=8)
        frame.pack()

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
            t = time_entry.get().strip()
            txt = text_entry.get().strip()
            if not t or not txt:
                return
            if len(t) == 4 and t.isdigit():
                t = f"{t[:2]}:{t[2:]}"
            selected_days = [i for i, var in enumerate(weekday_vars) if var.get()]
            weekdays = None if len(selected_days) >= 7 else selected_days
            entry = {"id": str(uuid4()), "time": t, "text": txt}
            if weekdays is not None:
                entry["weekdays"] = weekdays
            self.schedules.append(entry)
            _save_schedules(self.schedules)
            text_entry.delete(0, tk.END)
            refresh_list()

        tk.Button(frame, text="添加", command=add_item, font=PIXEL_FONT, bg=MENU_ACTIVE, fg=MENU_FG).pack(pady=4)
        refresh_list()

    def _place_ai_chat(self) -> None:
        if not self.ai_chat_win or not self.ai_chat_win.winfo_exists():
            return
        chat_y = max(0, self.y - 42)
        self.ai_chat_win.geometry(f"+{self.x}+{chat_y}")

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
        reply = self._ai_reply(text)
        if self.ai_reply_job:
            self.root.after_cancel(self.ai_reply_job)
        self.ai_reply_job = self.root.after(800, lambda: self._show_ai_reply(reply))

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
                    "工作啊…互动里的「工作」可以陪我搬箱子，一起加油吧！",
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
                    "诶，来练练单词吧！词库可以刷新哦。",
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
