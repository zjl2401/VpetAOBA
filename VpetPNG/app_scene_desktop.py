"""桌面前台窗口场景检测：游戏 / 刷视频 / 音乐 App。

浏览器内：进页/看片后标题经常丢掉站点名 → 调用方按「同进程粘住」短暂保持；
若长期停留在非相关页（软 miss）或超时 / 切到其它应用，再退出。
音乐客户端最小化后进程仍在 → 视为继续听，不立刻退出。
"""
from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes

# 进程名（小写，不含路径）
_MUSIC_EXES = frozenset(
    {
        "cloudmusic.exe",
        "qqmusic.exe",
        "spotify.exe",
        "lyrica.exe",
        "musicbee.exe",
        "aimp.exe",
        "foobar2000.exe",
        "itunes.exe",
        "applemusic.exe",
        "somafm.exe",
        "kugou.exe",
        "kwmusic.exe",
        "kuwomusic.exe",
        "qqmusicbrowser.exe",
    }
)
_VIDEO_EXES = frozenset(
    {
        "bilibili.exe",
        "哔哩哔哩.exe",
        "qyclient.exe",
        "qqlive.exe",
        "youkuclient.exe",
        "douyin.exe",
        "kuaishou.exe",
        "tiktok.exe",
        "vlc.exe",
        "potplayer.exe",
        "mpc-hc64.exe",
        "mpc-hc.exe",
        "wmplayer.exe",
        "iqiyi.exe",
    }
)
_GAME_EXES = frozenset(
    {
        "steam.exe",
        "epicgameslauncher.exe",
        "origin.exe",
        "galaxyclient.exe",
        "battle.net.exe",
        "minecraft.exe",
        "javaw.exe",  # MC 等；靠标题再确认
        "genshinimpact.exe",
        "yuanshen.exe",
        "starrail.exe",
        "zenlesszonezero.exe",
        "deltaforceclient.exe",
        "leagueclient.exe",
        "league of legends.exe",
        "valorant.exe",
        "cs2.exe",
        "dota2.exe",
        "robloxplayerbeta.exe",
    }
)
_CODE_EXES = frozenset(
    {
        "code.exe",
        "code - insiders.exe",
        "cursor.exe",
        "devenv.exe",
        "idea64.exe",
        "idea.exe",
        "pycharm64.exe",
        "pycharm.exe",
        "webstorm64.exe",
        "clion64.exe",
        "goland64.exe",
        "rider64.exe",
        "androidstudio64.exe",
        "sublime_text.exe",
        "notepad++.exe",
        "zed.exe",
        "windsurf.exe",
        "trae.exe",
    }
)
_STUDY_EXES = frozenset(
    {
        "winword.exe",
        "word.exe",
        "acrobat.exe",
        "acrord32.exe",
        "foxitreader.exe",
        "foxitpdfreader.exe",
        "notion.exe",
        "obsidian.exe",
        "anki.exe",
        "anki-console.exe",
        "zotero.exe",
        "caxa.pdf.exe",
    }
)
_OFFICE_EXES = frozenset(
    {
        "winword.exe",
        "word.exe",
        "excel.exe",
        "powerpnt.exe",
        "powerpoint.exe",
        # OneNote 归记事场景（手写/便签感），见 _NOTE_EXES
        "outlook.exe",
        "outlookforwindows.exe",
        "olk.exe",  # 新版 Outlook
        "teams.exe",
        "ms-teams.exe",
        "ms-teams_exe",
        "wps.exe",
        "et.exe",  # WPS 表格
        "wpp.exe",  # WPS 演示
        "wpspdf.exe",
        "wpsoffice.exe",
        "wpscloudsvr.exe",
        "prometheus.exe",  # 部分 WPS 进程
        "kingsoftpresentation.exe",
        "soffice.bin",  # LibreOffice
        "soffice.exe",
        "scalc.exe",
        "simpress.exe",
        "swriter.exe",
        "notion.exe",
        "feishudocs.exe",
    }
)
_CHAT_EXES = frozenset(
    {
        "wechat.exe",
        "weixin.exe",
        "wechatappex.exe",  # 微信内嵌网页/小程序宿主
        "wechatapp.exe",
        "qq.exe",
        "qqnt.exe",
        "tim.exe",
        "discord.exe",
        "telegram.exe",
        "telegram desktop.exe",
        "slack.exe",
        "feishu.exe",
        "lark.exe",
        "dingtalk.exe",
        "dingding.exe",
        "wxwork.exe",
        "wxworkweb.exe",
        "skype.exe",
        "line.exe",
        "whatsapp.exe",
        "signal.exe",
    }
)
# 绘画软件（→ paint 场景：draw + picture）
_PAINT_EXES = frozenset(
    {
        "photoshop.exe",
        "illustrator.exe",
        "clipstudio.exe",
        "clipstudiopaint.exe",
        "csp.exe",
        "sai.exe",
        "sai2.exe",
        "painttoolsaiver2.exe",
        "painttoolsaiver3.exe",
        "krita.exe",
        "medibangpaintpro.exe",
        "firealpaca.exe",
        "mspaint.exe",
        "paint.exe",
        "pbrush.exe",
        "figma.exe",
        "affinityphoto.exe",
        "affinitydesigner.exe",
        "affinityphoto2.exe",
        "affinitydesigner2.exe",
        "coreldraw.exe",
        "gimp.exe",
        "gimp-2.10.exe",
        "aseprite.exe",
        "sketchbook.exe",
        "infinitepainter.exe",
        "procreate.exe",
        "blender.exe",  # 建模画布也常当绘画席
        "opencanvas.exe",
        "opencanvas7.exe",
        "ibispaint.exe",
        "pixilart.exe",
        "pixelorama.exe",
        "azpainter.exe",
        "azpainter2.exe",
        "mypaint.exe",
    }
)
# 记事 / 手写便签（→ note 场景：仅 draw）
_NOTE_EXES = frozenset(
    {
        "stikynot.exe",  # Sticky Notes
        "microsoft.notes.exe",
        "onenote.exe",
        "onenoteim.exe",
        "onnotenm.exe",
        "notepad.exe",
        "write.exe",
        "wordpad.exe",
        "simplenote.exe",
        "joplin.exe",
        "standardnotes.exe",
        "notion calendar.exe",
        "nebo.exe",
        "goodnotes.exe",
        "xournal++.exe",
        "xournalpp.exe",
        "onesnote.exe",
    }
)
# 窗口类名片段（小写）— 微信/QQ 标题常只有联系人名，靠类名补判
_CHAT_CLASS_KEYS = (
    "wechatmainwndforpc",
    "wechat",
    "weixin",
    "chrome_widgetwin_",  # 微信 NT / QQ NT 常为此类；需配合 exe
    "txguifoundation",
    "qqbrowserdoc",
    "oipchat",
)
_OFFICE_CLASS_KEYS = (
    "xlmain",  # Excel
    "pptframeclass",
    "framework::cframewnd",
    "opusapp",  # Word（也可学习）
    "rctrl_renwnd32",  # Outlook
    "netuihwnd",
)
_CODE_TITLE_KEYS = (
    "visual studio code",
    "vscode",
    "- cursor",
    "cursor -",
    "intellij",
    "pycharm",
    "webstorm",
    "goland",
    "clion",
    "android studio",
    "sublime text",
    "github.dev",
    "gitlab",
)
_STUDY_TITLE_KEYS = (
    "作业",
    "论文",
    "课件",
    "复习",
    "考试",
    "课程",
    "textbook",
    "homework",
    "assignment",
    "thesis",
    "lecture",
    "anki",
    "notion",
    "obsidian",
    ".pdf",
    "word",
)
_OFFICE_TITLE_KEYS = (
    "excel",
    "powerpoint",
    "microsoft word",
    "microsoft excel",
    "microsoft powerpoint",
    "microsoft 365",
    "microsoft teams",
    ".xlsx",
    ".xls",
    ".pptx",
    ".ppt",
    ".docx",  # 办公文档常在标题
    "outlook",
    "teams",
    "会议",
    "报表",
    "周报",
    "日报",
    "表格",
    "幻灯片",
    "wps",
    "docs.google",
    "sheets.google",
    "slides.google",
    "office.com",
    "outlook.office",
    "outlook.live",
    "onedrive",
    "sharepoint",
    "飞书文档",
    "钉钉文档",
    "石墨文档",
    "腾讯文档",
    "语雀",
    "notion",
)
_CHAT_TITLE_KEYS = (
    "微信",
    "wechat",
    "weixin",
    "qq",
    "tim",
    "discord",
    "telegram",
    "slack",
    "飞书",
    "lark",
    "钉钉",
    "dingtalk",
    "企业微信",
    "会话",
    "聊天",
    "消息",
    "web.whatsapp",
    "web.telegram",
)
_PAINT_TITLE_KEYS = (
    "photoshop",
    "illustrator",
    "clip studio",
    "clipstudio",
    "paint tool sai",
    "painttool sai",
    "krita",
    "medibang",
    "firealpaca",
    "画图",
    "mspaint",
    "figma",
    "affinity photo",
    "affinity designer",
    "coreldraw",
    "gimp",
    "aseprite",
    "sketchbook",
    "绘画",
    "画板",
    "pixel art",
    "opencanvas",
    "ibispaint",
    "azpainter",
    "mypaint",
)
_NOTE_TITLE_KEYS = (
    "sticky notes",
    "便签",
    "记事本",
    "记事",
    "onenote",
    "one note",
    "notebook",
    "手写",
    "手账",
    "journal",
    "xournal",
    "nebo",
    "goodnotes",
    "simplenote",
    "joplin",
)
# 标题 / 页签里常见片段（小写匹配）；含域名碎片，适配「看片后标题只剩片名」前后仍带站点的情况
_VIDEO_TITLE_KEYS = (
    "youtube",
    "youtu.be",
    "bilibili",
    "b23.tv",
    "哔哩哔哩",
    "哔哩",
    "抖音",
    "tiktok",
    "快手",
    "netflix",
    "优酷",
    "youku",
    "爱奇艺",
    "iqiyi",
    "腾讯视频",
    "v.qq.com",
    "芒果tv",
    "mgtv",
    "prime video",
    "twitch",
    "西瓜视频",
    "ixigua",
    "acfun",
    "nicovideo",
    "niconico",
    "disney+",
    "disneyplus",
    "hulu",
    "vimeo",
    "youtube music",  # 偏音乐，下面音乐会先判；此处作视频兜底无妨
    # 点进正片后标题常只剩片名+站点尾巴 / 播放痕迹
    " - youtube",
    "｜youtube",
    "| youtube",
    "_哔哩哔哩",
    "- 哔哩哔哩",
    "bilibili.com",
    "/video/",
    "watch?",
    "番剧",
    "影视",
    "正在播放",
)
_MUSIC_TITLE_KEYS = (
    "spotify",
    "网易云音乐",
    "网易云",
    "music.163",
    "163.com/song",
    "163.com/playlist",
    "163.com/my",
    "163.com/discover",
    "163.com/artist",
    "163.com/album",
    "163.com/search",
    "music.163.com",
    "qq音乐",
    "qq music",
    "y.qq.com",
    "i.y.qq.com",
    "apple music",
    "music.apple",
    "itunes",
    "酷狗",
    "kugou",
    "酷我",
    "kuwo",
    "lyrics",
    "lyric",
    "youtube music",
    "music.youtube",
    "music.youtube.com",
    "汽水音乐",
    "音悦台",
    "bandcamp",
    "soundcloud",
    "deezer",
    "tidal",
    "listen.tidal",
    "咪咕音乐",
    "migu",
    "千千静听",
    "lyrica",
    "musicbee",
    "foobar2000",
    "aimp",
    # 播放器标题常见后缀（切歌后窗口名里仍可能带客户端名）
    "cloudmusic",
    "qqmusic",
    "正在播放",
    "now playing",
    "播放中",
)
_GAME_TITLE_KEYS = (
    "steam",
    "unity",
    "unreal",
    "minecraft",
    "原神",
    "genshin",
    "崩坏",
    "星穹铁道",
    "绝区零",
    "鸣潮",
    "三角洲",
    "lol",
    "league of legends",
    "valorant",
    "cs2",
    "counter-strike",
    "dota",
    "roblox",
    "honkai",
    "wuthering waves",
)
_BROWSER_EXES = frozenset(
    {
        "chrome.exe",
        "msedge.exe",
        "firefox.exe",
        "brave.exe",
        "opera.exe",
        "vivaldi.exe",
        "qqbrowser.exe",
        "360chrome.exe",
        "360se.exe",
        "sogouexplorer.exe",
        "safari.exe",
        "chromium.exe",
        "arc.exe",
    }
)


def _get_foreground_info() -> tuple[str, str, str]:
    """返回 (exe_name_lower, window_title, class_name_lower)。"""
    if sys.platform != "win32":
        return "", "", ""
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return "", "", ""
        length = int(user32.GetWindowTextLengthW(hwnd) or 0)
        buf = ctypes.create_unicode_buffer(length + 2)
        user32.GetWindowTextW(hwnd, buf, length + 2)
        title = (buf.value or "").strip()

        cls_buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls_buf, 256)
        cls = (cls_buf.value or "").strip().lower()

        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not pid.value:
            return "", title, cls
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        hproc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not hproc:
            return "", title, cls
        try:
            size = wintypes.DWORD(512)
            path_buf = ctypes.create_unicode_buffer(512)
            if not kernel32.QueryFullProcessImageNameW(hproc, 0, path_buf, ctypes.byref(size)):
                return "", title, cls
            path = (path_buf.value or "").replace("\\", "/").lower()
            exe = path.rsplit("/", 1)[-1] if path else ""
            return exe, title, cls
        finally:
            kernel32.CloseHandle(hproc)
    except Exception:
        return "", "", ""


def _title_hit(title_l: str, keys: tuple[str, ...]) -> bool:
    return any(k in title_l for k in keys)


def _class_hit(cls_l: str, keys: tuple[str, ...]) -> bool:
    return any(k in cls_l for k in keys)


def _looks_like_chat(exe: str, title_l: str, cls_l: str) -> bool:
    if exe in _CHAT_EXES:
        return True
    if _title_hit(title_l, _CHAT_TITLE_KEYS):
        return True
    # 微信/QQ 等主窗类名（标题常只有联系人名）
    if _class_hit(
        cls_l,
        (
            "wechatmainwndforpc",
            "wechatmainwnd",
            "wechat",
            "weixin",
            "txguifoundation",
            "qqbrowserdoc",
            "oipchat",
        ),
    ):
        return True
    # Electron 壳（Chrome_WidgetWin）：必须配合聊天 exe，避免误伤其它 Electron 应用
    if "chrome_widgetwin" in cls_l and exe in _CHAT_EXES:
        return True
    if exe in _BROWSER_EXES and _title_hit(
        title_l,
        (
            "web.whatsapp",
            "web.telegram",
            "discord.com",
            "feishu.cn/messenger",
            "dingtalk.com",
            "teams.microsoft",
            "web.qq",
            "slack.com",
        ),
    ):
        return True
    return False


def _looks_like_office(exe: str, title_l: str, cls_l: str) -> bool:
    if exe in _OFFICE_EXES:
        return True
    if _class_hit(cls_l, _OFFICE_CLASS_KEYS) and exe not in _CHAT_EXES:
        # Word 类名也算办公（与学习重叠时办公优先于 none）
        return True
    if _title_hit(title_l, _OFFICE_TITLE_KEYS):
        # 浏览器网页办公
        if exe in _BROWSER_EXES or exe in _OFFICE_EXES or not exe:
            return True
        # 非浏览器也允许标题命中（如本地文件名带 xlsx）
        if any(k in title_l for k in (".xlsx", ".xls", ".pptx", ".ppt", "excel", "powerpoint", "wps", "outlook", "teams")):
            return True
    return False


def _looks_like_paint(exe: str, title_l: str) -> bool:
    if exe in _PAINT_EXES:
        return True
    if _title_hit(title_l, _PAINT_TITLE_KEYS):
        if exe in _BROWSER_EXES or exe in _PAINT_EXES or not exe:
            return True
        # 本地绘画文件名常见后缀
        if any(k in title_l for k in (".psd", ".clip", ".kra", ".ora", ".xcf", ".sai", "figma")):
            return True
    return False


def _looks_like_note(exe: str, title_l: str) -> bool:
    if exe in _NOTE_EXES:
        return True
    if _title_hit(title_l, _NOTE_TITLE_KEYS):
        return True
    return False


# 进程名缓存：避免每 tick 枚举全表（听音乐最小化检测用）
_process_name_cache: frozenset[str] = frozenset()
_process_name_cache_ms: float = 0.0
_PROCESS_CACHE_TTL_MS = 5000.0


def _snapshot_running_exes() -> frozenset[str]:
    """当前运行中的 exe 小写名集合（Win32 Toolhelp）。"""
    if sys.platform != "win32":
        return frozenset()
    try:
        TH32CS_SNAPPROCESS = 0x00000002
        kernel32 = ctypes.windll.kernel32

        class PROCESSENTRY32W(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD),
                ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", wintypes.DWORD),
                ("szExeFile", wintypes.WCHAR * 260),
            ]

        snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snap in (-1, 0, None):
            return frozenset()
        names: set[str] = set()
        try:
            pe = PROCESSENTRY32W()
            pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
            if not kernel32.Process32FirstW(snap, ctypes.byref(pe)):
                return frozenset()
            while True:
                name = (pe.szExeFile or "").strip().lower()
                if name:
                    names.add(name)
                if not kernel32.Process32NextW(snap, ctypes.byref(pe)):
                    break
        finally:
            kernel32.CloseHandle(snap)
        return frozenset(names)
    except Exception:
        return frozenset()


def running_exe_names(*, force: bool = False) -> frozenset[str]:
    """带短缓存的运行中 exe 名。"""
    global _process_name_cache, _process_name_cache_ms
    now = time.time() * 1000.0
    if (
        not force
        and _process_name_cache
        and (now - _process_name_cache_ms) < _PROCESS_CACHE_TTL_MS
    ):
        return _process_name_cache
    _process_name_cache = _snapshot_running_exes()
    _process_name_cache_ms = now
    return _process_name_cache


def process_exe_running(exe: str) -> bool:
    name = str(exe or "").strip().lower()
    if not name:
        return False
    return name in running_exe_names()


def any_exe_running(exes: frozenset[str] | set[str] | tuple[str, ...]) -> bool:
    if not exes:
        return False
    running = running_exe_names()
    return any(str(e).strip().lower() in running for e in exes)


def music_source_still_alive(sticky_exe: str) -> bool:
    """最小化后：专用音乐客户端或浏览器进程仍在，视为音乐可能仍在播。"""
    sticky = str(sticky_exe or "").strip().lower()
    if sticky and sticky in _MUSIC_EXES and process_exe_running(sticky):
        return True
    if sticky and sticky in _BROWSER_EXES and any_exe_running(_BROWSER_EXES):
        return True
    # sticky 丢了也兜底：任一音乐客户端还在
    if any_exe_running(_MUSIC_EXES):
        return True
    return False


def video_source_still_alive(sticky_exe: str) -> bool:
    sticky = str(sticky_exe or "").strip().lower()
    if sticky and sticky in _VIDEO_EXES and process_exe_running(sticky):
        return True
    if sticky and sticky in _BROWSER_EXES and any_exe_running(_BROWSER_EXES):
        return True
    if any_exe_running(_VIDEO_EXES):
        return True
    return False


def classify_foreground() -> tuple[str, str]:
    """
    返回 (scene, signature)
    scene: none | hold | music | video | game | code | study | office | chat | paint | note
    hold = 前台是桌宠自身，保持上一场景（避免点宠后立刻退出）
    signature: 始终带 exe（含 none），供「同进程粘住」；格式 exe|title前缀
    """
    exe, title, cls = _get_foreground_info()
    t = (title or "").lower()
    cls_l = (cls or "").lower()
    sig = f"{exe}|{(title or '')[:64]}"
    # 本桌宠抢到前台时保持场景，不要当成「已离开」
    # Tk 浮层（提示、侧栏）标题不一定带 Vpet，拖动时前台会在宠和软件间跳
    if exe in ("python.exe", "pythonw.exe", "vpet.exe") and (
        "vpet" in t or not t or "tk" in cls_l
    ):
        return "hold", sig
    video_title = _title_hit(t, _VIDEO_TITLE_KEYS)
    music_title = _title_hit(t, _MUSIC_TITLE_KEYS)
    # 音乐标题优先（避免 youtube music 被视频抢）
    if music_title or (exe in _MUSIC_EXES and not video_title):
        if exe in _BROWSER_EXES and not music_title:
            pass
        else:
            return "music", sig
    if video_title or (exe in _VIDEO_EXES and not music_title):
        if exe in _BROWSER_EXES and not video_title:
            pass
        else:
            return "video", sig
    if exe in _GAME_EXES or _title_hit(t, _GAME_TITLE_KEYS):
        if exe == "javaw.exe" and not _title_hit(t, _GAME_TITLE_KEYS):
            pass
        elif exe == "steam.exe" and not _title_hit(t, _GAME_TITLE_KEYS) and t.strip() in ("", "steam"):
            pass
        else:
            return "game", sig
    if exe.endswith("-win64-shipping.exe") or exe.endswith("_data.exe"):
        return "game", sig
    if "unity" in exe or exe.endswith("game.exe"):
        return "game", sig
    # 聊天优先于办公（飞书/钉钉既开会又聊天时，前台会话窗更像 chat）
    if _looks_like_chat(exe, t, cls_l):
        return "chat", sig
    if exe in _CODE_EXES or _title_hit(t, _CODE_TITLE_KEYS):
        return "code", sig
    if exe in _BROWSER_EXES and _title_hit(t, _CODE_TITLE_KEYS):
        return "code", sig
    # 绘画 / 记事：在办公之前，避免 Word 类名等误伤
    if _looks_like_paint(exe, t):
        return "paint", sig
    if _looks_like_note(exe, t):
        return "note", sig
    if _looks_like_office(exe, t, cls_l):
        return "office", sig
    if exe in _STUDY_EXES or (exe in _BROWSER_EXES and _title_hit(t, _STUDY_TITLE_KEYS)):
        return "study", sig
    return "none", sig
