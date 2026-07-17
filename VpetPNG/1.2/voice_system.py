"""Vpet 语音模式：扫描 Vpetvoice 目录，按场景播放语音并支持链式触发。"""
from __future__ import annotations

import random
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from bundled_paths import LEGACY_VOICE_ROOT, resolve_bundled
from media_bundled import is_audio_media
from voice_audio import ensure_voice_wav, voice_cache_path

VOICE_ROOT = resolve_bundled("Vpetvoice", legacy=LEGACY_VOICE_ROOT)
VOICE_CHANNEL_ID = 1

VOICE_PRIORITY_AMBIENT = 1
VOICE_PRIORITY_SCENE = 2
VOICE_GLOBAL_COOLDOWN_MS = 10_000
VOICE_HI_CATEGORY = "你好"

# 去掉文件名开头的序号/字母前缀，如「1 文本」「a 文本」「11.文本」
_PREFIX_RE = re.compile(r"^((?:\d+)|(?:[a-zA-Z]))(?:[\s._\-]+)(.+)$")
_RING_NAMES = frozenset({"ring", "call-ring", "call_ring", "callring"})
_RING_STEM_PRIORITY = ("call-ring", "call_ring", "ring", "callring")
_STARTUP_HINTS = ("启动", "启动音")


def _is_ring_stem(stem: str) -> bool:
    low = stem.lower().strip()
    if low in _RING_NAMES or low.endswith("-ring") or low.endswith("_ring"):
        return True
    compact = re.sub(r"[\s_\-]+", "", low)
    if compact in ("ring", "callring"):
        return True
    return "call" in low and "ring" in low


def _suppress_voice_subtitle(clip: VoiceClip) -> bool:
    """纯音效：只播声音，不弹标题框（智能伴侣启动音 / ring / 碰撞音）。"""
    if getattr(clip, "is_ring", False) or getattr(clip, "is_startup", False):
        return True
    cat = str(getattr(clip, "category", "") or "").lower()
    if cat in ("collision", "startup"):
        return True
    stem = ""
    try:
        stem = clip.src_path.stem
    except Exception:
        stem = ""
    title = str(getattr(clip, "title", "") or "")
    text = f"{stem} {title}"
    if "碰撞" in text:
        return True
    if title.strip() in ("铃响", "ring"):
        return True
    return False


def _strip_title_prefix(title: str) -> str:
    """显示用：再次去掉可能残留的数字/字母前缀。"""
    text = (title or "").strip()
    if not text:
        return ""
    m = _PREFIX_RE.match(text)
    return m.group(2).strip() if m else text


def _parse_stem(stem: str) -> tuple[str | None, str, bool, bool]:
    if _is_ring_stem(stem):
        return None, "铃响", True, False
    if any(h in stem for h in _STARTUP_HINTS):
        return None, stem, False, True
    m = _PREFIX_RE.match(stem)
    if m:
        raw_prefix = m.group(1)
        prefix = raw_prefix.lower() if raw_prefix.isalpha() else raw_prefix
        return prefix, m.group(2).strip(), False, False
    return None, stem.strip(), False, False


@dataclass
class VoiceClip:
    source: str
    category: str
    src_path: Path
    title: str
    prefix: str | None = None
    is_ring: bool = False
    is_startup: bool = False
    cache_wav: Path | None = None


@dataclass
class VoiceCatalog:
    vpet: dict[str, list[VoiceClip]] = field(default_factory=dict)
    allmate: dict[str, list[VoiceClip]] = field(default_factory=dict)
    laimu: dict[str, list[VoiceClip]] = field(default_factory=dict)
    vpet_by_prefix: dict[str, list[VoiceClip]] = field(default_factory=dict)
    allmate_by_prefix: dict[str, list[VoiceClip]] = field(default_factory=dict)

    @classmethod
    def build(cls, root: Path = VOICE_ROOT) -> VoiceCatalog:
        cat = cls()
        if not root.exists():
            return cat
        vpet_dir = root / "Vpet"
        if vpet_dir.is_dir():
            for item in sorted(vpet_dir.rglob("*")):
                if not item.is_file() or not is_audio_media(item):
                    continue
                rel = item.relative_to(vpet_dir)
                if rel.parent == Path("."):
                    if "碰撞" in item.stem:
                        category = "collision"
                    else:
                        category = "misc"
                else:
                    # ASCII 目录名统一小写；中文目录名（如「你好」）保持原样
                    raw_cat = rel.parts[0]
                    category = raw_cat.lower() if raw_cat.isascii() else raw_cat
                prefix, title, is_ring, is_startup = _parse_stem(item.stem)
                clip = VoiceClip(
                    source="vpet",
                    category=category,
                    src_path=item,
                    title=title,
                    prefix=prefix,
                    is_ring=is_ring,
                    is_startup=is_startup,
                )
                cat._add_vpet(clip)
        allmate_dir = root / "Allmate"
        if allmate_dir.is_dir():
            for item in sorted(allmate_dir.iterdir()):
                if not item.is_file() or not is_audio_media(item):
                    continue
                prefix, title, is_ring, is_startup = _parse_stem(item.stem)
                category = "startup" if (is_ring or is_startup) else "misc"
                clip = VoiceClip(
                    source="allmate",
                    category=category,
                    src_path=item,
                    title=title,
                    prefix=prefix,
                    is_ring=is_ring,
                    is_startup=is_startup,
                )
                cat._add_allmate(clip)
        laimu_dir = root / "laimu"
        if laimu_dir.is_dir():
            for item in sorted(laimu_dir.iterdir()):
                if not item.is_file() or not is_audio_media(item):
                    continue
                low = item.stem.lower()
                if low in ("openness", "openning", "opening"):
                    category = "open"
                elif "得分" in item.stem or low.startswith("得"):
                    category = "score"
                elif low in ("莱", "莱姆") or "莱姆" in item.stem:
                    category = "laimu"
                else:
                    category = "misc"
                clip = VoiceClip(
                    source="laimu",
                    category=category,
                    src_path=item,
                    title=item.stem.strip(),
                )
                cat.laimu.setdefault(category, []).append(clip)
        return cat

    def _add_vpet(self, clip: VoiceClip) -> None:
        self.vpet.setdefault(clip.category, []).append(clip)
        if clip.prefix:
            self.vpet_by_prefix.setdefault(clip.prefix, []).append(clip)

    def _add_allmate(self, clip: VoiceClip) -> None:
        self.allmate.setdefault(clip.category, []).append(clip)
        if clip.prefix:
            self.allmate_by_prefix.setdefault(clip.prefix, []).append(clip)

    def pick_random(
        self,
        source: str,
        category: str,
        *,
        exclude_ring: bool = False,
        avoid_path: Path | None = None,
    ) -> VoiceClip | None:
        pool = self._pool(source, category)
        if exclude_ring:
            pool = [c for c in pool if not c.is_ring]
        if avoid_path is not None and len(pool) > 1:
            narrowed = [c for c in pool if c.src_path.resolve() != avoid_path.resolve()]
            if narrowed:
                pool = narrowed
        return random.choice(pool) if pool else None

    def pick_open_laimu(self) -> VoiceClip | None:
        pool = list(self.laimu.get("open", []))
        return random.choice(pool) if pool else None

    def pick_by_prefix(self, source: str, prefix: str, *, category: str | None = None) -> VoiceClip | None:
        key = prefix.lower() if prefix.isalpha() else prefix
        if source == "vpet":
            pool = self.vpet_by_prefix.get(key, [])
            if category:
                pool = [c for c in pool if c.category == category]
        elif source == "allmate":
            pool = self.allmate_by_prefix.get(key, [])
        else:
            return None
        return random.choice(pool) if pool else None

    def pick_companion_startup(self) -> VoiceClip | None:
        """点击/开启智能伴侣：ring 与启动音随机二选一。"""
        startup_clips = list(self.allmate.get("startup", []))
        ring_pool = [c for c in startup_clips if c.is_ring]
        boot_pool = [c for c in startup_clips if c.is_startup and not c.is_ring]
        candidates: list[VoiceClip] = []
        if ring_pool:
            candidates.append(random.choice(ring_pool))
        if boot_pool:
            candidates.append(random.choice(boot_pool))
        if candidates:
            return random.choice(candidates)
        # 兜底：startup 目录其它条目 / misc
        if startup_clips:
            return random.choice(startup_clips)
        misc_pool = [c for c in self.allmate.get("misc", []) if c.is_ring or c.is_startup]
        return random.choice(misc_pool) if misc_pool else None

    def pick_call_sequence(self) -> list[VoiceClip]:
        """打电话语音：必须先 call/ring，再从 call 目录非 ring 条目随机选一条（紧跟）。"""
        call_clips = self.vpet.get("call", [])
        rings = [c for c in call_clips if c.is_ring]
        body_pool = [c for c in call_clips if not c.is_ring]
        if not rings or not body_pool:
            return []

        def _ring_rank(clip: VoiceClip) -> tuple[int, str]:
            stem = clip.src_path.stem.lower().strip()
            compact = re.sub(r"[\s_\-]+", "", stem)
            for i, name in enumerate(_RING_STEM_PRIORITY):
                if stem == name or compact == name.replace("-", "").replace("_", ""):
                    return (i, clip.src_path.name)
            return (len(_RING_STEM_PRIORITY), clip.src_path.name)

        ring = sorted(rings, key=_ring_rank)[0]
        body = random.choice(body_pool)
        # 强制顺序：ring → 非 ring；调用方不得颠倒或拆开只播其一
        return [ring, body]

    def pick_hi_clip(self) -> VoiceClip | None:
        """打招呼：从 Vpet/你好 目录随机选一条。"""
        pool = list(self.vpet.get(VOICE_HI_CATEGORY, []))
        if not pool:
            pool = [
                c
                for items in self.vpet.values()
                for c in items
                if VOICE_HI_CATEGORY in c.title or VOICE_HI_CATEGORY in c.src_path.stem
            ]
        return random.choice(pool) if pool else None

    def pick_interjection(self, part: str) -> VoiceClip | None:
        groups = self._interjection_part_groups()
        pool = groups.get(part) or list(self.vpet.get("interjection", []))
        if not pool:
            pool = list(self.vpet.get("interjection", []))
        return random.choice(pool) if pool else None

    def _interjection_part_groups(self) -> dict[str, list[VoiceClip]]:
        pool = sorted(self.vpet.get("interjection", []), key=lambda c: c.src_path.name)
        parts = ("face", "body", "legs")
        groups: dict[str, list[VoiceClip]] = {p: [] for p in parts}
        if not pool:
            return groups
        n = len(pool)
        for i, clip in enumerate(pool):
            idx = min(i * len(parts) // n, len(parts) - 1)
            groups[parts[idx]].append(clip)
        return groups

    def _pool(self, source: str, category: str) -> list[VoiceClip]:
        if source == "vpet":
            return list(self.vpet.get(category, []))
        if source == "allmate":
            return list(self.allmate.get(category, []))
        if source == "laimu":
            return list(self.laimu.get(category, []))
        return []


def clip_cache_stem(clip: VoiceClip) -> str:
    safe = f"{clip.source}_{clip.category}_{clip.src_path.stem}"
    return re.sub(r'[<>:"/\\|?*]', "_", safe)[:120]


def iter_all_clips(root: Path = VOICE_ROOT) -> list[VoiceClip]:
    cat = VoiceCatalog.build(root)
    clips: list[VoiceClip] = []
    for pool in (cat.vpet, cat.allmate, cat.laimu):
        for items in pool.values():
            clips.extend(items)
    return sorted(clips, key=lambda c: (c.source, c.category, c.title))


def phonograph_id(clip: VoiceClip) -> str:
    return f"voice:{clip.source}:{clip.category}:{clip_cache_stem(clip)}"


_PHONOGRAPH_SOURCE_LABEL = {"vpet": "Vpet", "allmate": "Allmate", "laimu": "莱姆"}


def phonograph_title(clip: VoiceClip) -> str:
    label = _PHONOGRAPH_SOURCE_LABEL.get(clip.source, clip.source)
    return f"{label}·{clip.title}"


class VoicePlayer:
    def __init__(
        self,
        root,
        *,
        cache_dir: Path,
        ensure_wav: Callable[..., Path | None],
        get_duration_ms: Callable[[Path], int],
        get_volume: Callable[[], float],
        init_mixer: Callable[[], bool],
        stop_sfx: Callable[[], None] | None = None,
    ) -> None:
        self.root = root
        self.cache_dir = cache_dir
        self.ensure_wav = ensure_wav
        self.get_duration_ms = get_duration_ms
        self.get_volume = get_volume
        self.init_mixer = init_mixer
        self.stop_sfx = stop_sfx
        self.enabled = False
        self.catalog = VoiceCatalog()  # 启动时空目录，后台异步扫描
        self._catalog_building = False
        self._catalog_on_done: Callable[[], None] | None = None
        self._queue: list[VoiceClip] = []
        self._playing = False
        self._current: VoiceClip | None = None
        self._sound = None
        self._channel = None
        self._watch_job: str | None = None
        self._subtitle_cb: Callable[..., None] | None = None
        self._hide_subtitle_cb: Callable[[], None] | None = None
        self._has_companion_cb: Callable[[], bool] | None = None
        self._done_cb: Callable[[], None] | None = None
        self._session_priority = 0
        self._last_session_end_ms = 0
        self._last_pick_path: dict[tuple[str, str], Path] = {}
        self._play_gen = 0
        self.reload_catalog_async()

    def reload_catalog_async(self, *, on_done: Callable[[], None] | None = None) -> None:
        if on_done:
            self._catalog_on_done = on_done
        if self._catalog_building:
            return
        self._catalog_building = True

        def worker() -> None:
            cat = VoiceCatalog.build()

            def apply() -> None:
                self.catalog = cat
                self._catalog_building = False
                cb = self._catalog_on_done
                self._catalog_on_done = None
                if cb:
                    try:
                        cb()
                    except Exception:
                        pass

            try:
                self.root.after(0, apply)
            except Exception:
                self.catalog = cat
                self._catalog_building = False
                cb = self._catalog_on_done
                self._catalog_on_done = None
                if cb:
                    try:
                        cb()
                    except Exception:
                        pass

        threading.Thread(target=worker, daemon=True).start()

    def _global_cooldown_ready(self) -> bool:
        if self._last_session_end_ms <= 0:
            return True
        return int(time.time() * 1000) - self._last_session_end_ms >= VOICE_GLOBAL_COOLDOWN_MS

    def _mark_session_end(self) -> None:
        self._last_session_end_ms = int(time.time() * 1000)

    def configure(
        self,
        *,
        enabled: bool,
        subtitle_cb: Callable[..., None] | None = None,
        hide_subtitle_cb: Callable[[], None] | None = None,
        has_companion_cb: Callable[[], bool] | None = None,
    ) -> None:
        self.enabled = enabled
        self._subtitle_cb = subtitle_cb
        self._hide_subtitle_cb = hide_subtitle_cb
        self._has_companion_cb = has_companion_cb
        if not enabled:
            self._preload_token = getattr(self, "_preload_token", 0) + 1
            self.stop()

    def is_busy(self) -> bool:
        return self._playing or bool(self._queue)

    def _can_start(self, priority: int) -> bool:
        if not self._playing and not self._queue:
            return True
        return priority > self._session_priority

    def _begin_session(self, priority: int, on_done: Callable[[], None] | None) -> None:
        if self._playing or self._queue:
            self._done_cb = None
            self.stop()
        self._play_gen = int(getattr(self, "_play_gen", 0)) + 1
        self._session_priority = priority
        self._done_cb = on_done

    def stop(self) -> None:
        was_busy = self.is_busy()
        # 作废进行中的后台转码/after 回调，避免 stop 后旧 worker 把语音又拉回来
        self._play_gen = int(getattr(self, "_play_gen", 0)) + 1
        self._queue.clear()
        self._playing = False
        self._current = None
        self._session_priority = 0
        if self._watch_job:
            try:
                self.root.after_cancel(self._watch_job)
            except Exception:
                pass
            self._watch_job = None
        try:
            import pygame

            if pygame.mixer.get_init():
                ch = pygame.mixer.Channel(VOICE_CHANNEL_ID)
                ch.stop()
        except Exception:
            pass
        if was_busy:
            self._mark_session_end()
            self._hide_subtitle_now()

    def resolve_wav(self, clip: VoiceClip) -> Path | None:
        return self._resolve_wav(clip)

    def estimate_sequence_ms(self, clips: list[VoiceClip]) -> int:
        """只读已有 wav 头；缺缓存时用默认估值，避免主线程触发 ffmpeg。"""
        total = 0
        for clip in clips:
            wav: Path | None = None
            if clip.cache_wav and clip.cache_wav.exists():
                wav = clip.cache_wav
            else:
                # 已有转换产物可直接量时长；勿调用 ensure_voice_wav
                safe = f"{clip.source}_{clip.category}_{clip.src_path.stem}"
                safe = re.sub(r'[<>:"/\\|?*]', "_", safe)[:120]
                candidate = voice_cache_path(self.cache_dir, safe)
                if candidate.exists():
                    wav = candidate
                    clip.cache_wav = candidate
                elif clip.src_path.suffix.lower() == ".wav" and clip.src_path.exists():
                    wav = clip.src_path
            if wav:
                total += max(400, self.get_duration_ms(wav))
            else:
                total += 1600
        return total

    def _resolve_wav(self, clip: VoiceClip) -> Path | None:
        if clip.cache_wav and clip.cache_wav.exists():
            return clip.cache_wav
        safe = f"{clip.source}_{clip.category}_{clip.src_path.stem}"
        safe = re.sub(r'[<>:"/\\|?*]', "_", safe)[:120]
        dst = voice_cache_path(self.cache_dir, safe)
        wav = ensure_voice_wav(clip.src_path, dst)
        if wav:
            clip.cache_wav = wav
        return wav

    def _hide_subtitle_now(self) -> None:
        hide_cb = self._hide_subtitle_cb
        if hide_cb:
            try:
                hide_cb()
            except Exception:
                pass

    def _show_subtitle(self, clip: VoiceClip, duration_ms: int) -> None:
        # 启动音 / ring / 碰撞：只播声音，不弹标题框
        if _suppress_voice_subtitle(clip):
            self._hide_subtitle_now()
            return
        title = _strip_title_prefix(clip.title)
        if not title:
            title = (clip.title or "").strip() or "……"
        if not title:
            title = "……"
        cb = self._subtitle_cb
        if not cb:
            return
        source = getattr(clip, "source", "vpet") or "vpet"
        # 主线程直接弹；失败则 after 再试，保证有台词则有标题框
        try:
            cb(title, int(duration_ms), source)
            return
        except TypeError:
            # 兼容旧签名 (title, duration_ms)
            try:
                cb(title, int(duration_ms))
                return
            except Exception:
                pass
        except Exception:
            pass
        try:
            self.root.after(0, lambda t=title, d=int(duration_ms), s=source: cb(t, d, s))
        except Exception:
            try:
                self.root.after(40, lambda t=title, d=int(duration_ms), s=source: cb(t, d, s))
            except Exception:
                pass

    def _stop_sfx_if_needed(self) -> None:
        if self.stop_sfx:
            self.stop_sfx()

    def play_clips(
        self,
        clips: list[VoiceClip],
        *,
        chain: bool = True,
        on_done: Callable[[], None] | None = None,
        priority: int = VOICE_PRIORITY_SCENE,
        ignore_cooldown: bool = False,
        interrupt_busy: bool = False,
    ) -> bool:
        if not self.enabled or not clips:
            return False
        if self.is_busy():
            # 仅 interrupt_busy 可打断；ignore_cooldown 只跳过全局冷却，不得误掐正在播的场景语音
            if interrupt_busy:
                self.stop()
            else:
                return False
        if not ignore_cooldown and not self._global_cooldown_ready():
            return False
        if not self._can_start(priority):
            return False
        # 绝不在主线程跑 ffmpeg：直接入队，由 _play_next 后台解析。
        # 仅快速剔掉「已缓存路径不存在且无法同步换绑」的失败仍异步重试。
        self._begin_session(priority, on_done)
        play_gen = self._play_gen
        self._play_next(list(clips), chain=chain, play_gen=play_gen)
        return True

    def all_catalog_clips(self) -> list[VoiceClip]:
        clips: list[VoiceClip] = []
        for pool in (self.catalog.vpet, self.catalog.allmate, self.catalog.laimu):
            for items in pool.values():
                clips.extend(items)
        return clips

    def preload_vpet_categories(self, categories: tuple[str, ...]) -> None:
        clips: list[VoiceClip] = []
        for cat in categories:
            clip = self.catalog.pick_random("vpet", cat)
            if clip:
                clips.append(clip)
        self._preload_clips(clips)

    def preload_priority_clips(self, *, on_done: Callable[[int, int], None] | None = None) -> None:
        """预热高频 + 特定触发场景（与 normal 一并提前缓存，避免首次点播卡转码）。"""
        # 特定触发 / 场景专用：整组进缓存；normal 也整组预热
        want = (
            "call",
            "你好",
            "eat",
            "kick",
            "hurt",
            "hungry",
            "end",
            "sleep",
            "work",
            "yuqi",
            "walk",
            "dizzy",
            "normal",
            "interjection",
        )
        full_preload = frozenset(
            {
                "yuqi",
                "eat",
                "kick",
                "hurt",
                "hungry",
                "sleep",
                "work",
                "walk",
                "dizzy",
                "end",
                "你好",
                "normal",
                "call",
            }
        )
        clips: list[VoiceClip] = []
        for cat in want:
            pool = list(self.catalog.vpet.get(cat, []))
            if not pool and cat == "你好":
                for c in self.all_catalog_clips():
                    if c.source == "vpet" and ("你好" in c.title or "你好" in c.src_path.stem):
                        pool.append(c)
            rings = [c for c in pool if c.is_ring]
            bodies = [c for c in pool if not c.is_ring]
            if rings:
                # call：ring 全部预热，保证打电话必响
                if cat == "call":
                    clips.extend(rings)
                else:
                    clips.append(rings[0])
            limit = len(bodies) if cat in full_preload else 2
            for c in bodies[:limit]:
                clips.append(c)
        # 伴侣启动音少量
        for c in list(self.catalog.allmate.get("startup", []))[:2]:
            clips.append(c)
        # 去重
        seen: set[str] = set()
        uniq: list[VoiceClip] = []
        for c in clips:
            key = str(c.src_path)
            if key in seen:
                continue
            seen.add(key)
            uniq.append(c)
        self._preload_clips(uniq, on_done=on_done)

    def _preload_clips(
        self,
        clips: list[VoiceClip],
        *,
        on_done: Callable[[int, int], None] | None = None,
    ) -> None:
        if not clips:
            if on_done:
                try:
                    self.root.after(0, lambda: on_done(0, 0))
                except Exception:
                    pass
            return

        token = getattr(self, "_preload_token", 0) + 1
        self._preload_token = token

        def worker() -> None:
            ok = 0
            total = len(clips)
            for i, clip in enumerate(clips):
                if getattr(self, "_preload_token", 0) != token:
                    return
                try:
                    if self._resolve_wav(clip):
                        ok += 1
                except Exception:
                    pass
                # 节流：避免上百条连续 ffmpeg 把磁盘/CPU 打满导致启动卡死
                if i and i % 2 == 0:
                    time.sleep(0.035)
            if on_done:

                def done() -> None:
                    if getattr(self, "_preload_token", 0) != token:
                        return
                    on_done(ok, total)

                try:
                    self.root.after(0, done)
                except Exception:
                    pass

        threading.Thread(target=worker, daemon=True).start()

    def play_interjection(self, part: str, *, on_done=None, priority: int = VOICE_PRIORITY_SCENE) -> bool:
        clip = self.catalog.pick_interjection(part)
        if not clip:
            return False
        return self.play_clips([clip], chain=False, on_done=on_done, priority=priority)

    def play_vpet(
        self,
        category: str,
        *,
        chain: bool = True,
        on_done=None,
        priority: int = VOICE_PRIORITY_SCENE,
        ignore_cooldown: bool = False,
        interrupt_busy: bool = False,
    ) -> bool:
        key = ("vpet", category)
        avoid = self._last_pick_path.get(key)
        clip = self.catalog.pick_random("vpet", category, avoid_path=avoid)
        if not clip:
            return False
        self._last_pick_path[key] = clip.src_path
        return self.play_clips(
            [clip],
            chain=chain,
            on_done=on_done,
            priority=priority,
            ignore_cooldown=ignore_cooldown,
            interrupt_busy=interrupt_busy,
        )

    def play_laimu_open(self, *, on_done=None, priority: int = VOICE_PRIORITY_SCENE, ignore_cooldown: bool = False) -> bool:
        clip = self.catalog.pick_open_laimu()
        if not clip:
            return False
        return self.play_clips(
            [clip], chain=False, on_done=on_done, priority=priority, ignore_cooldown=ignore_cooldown
        )

    def play_call(
        self,
        *,
        clips: list[VoiceClip] | None = None,
        on_done=None,
        priority: int = VOICE_PRIORITY_SCENE,
        ignore_cooldown: bool = False,
    ) -> bool:
        """打电话：必须 ring（无字幕）→ 紧跟一条非 ring call 台词（有字幕）。缺一不可。"""
        seq = list(clips) if clips is not None else self.catalog.pick_call_sequence()
        if len(seq) < 2 or not seq[0].is_ring or seq[1].is_ring:
            seq = self.catalog.pick_call_sequence()
        if len(seq) < 2 or not seq[0].is_ring or any(c.is_ring for c in seq[1:]):
            return False
        # 不在主线程转码；交由 _play_next 后台解析。
        # ring 失败时 _play_next 会整段终止，不会跳到随机台词。
        body = [c for c in seq[1:] if not c.is_ring]
        if not body:
            return False
        play_seq = [seq[0], body[0]]
        return self.play_clips(
            play_seq,
            chain=False,
            on_done=on_done,
            priority=priority,
            ignore_cooldown=ignore_cooldown,
            interrupt_busy=True,
        )

    def play_hi(self, *, on_done=None, priority: int = VOICE_PRIORITY_SCENE, ignore_cooldown: bool = False) -> bool:
        clip = self.catalog.pick_hi_clip()
        if not clip:
            return False
        return self.play_clips(
            [clip],
            chain=False,
            on_done=on_done,
            priority=priority,
            ignore_cooldown=ignore_cooldown,
            interrupt_busy=True,
        )

    def play_companion_startup(self, *, on_done=None, priority: int = VOICE_PRIORITY_SCENE, ignore_cooldown: bool = False) -> bool:
        clip = self.catalog.pick_companion_startup()
        if not clip:
            return False
        return self.play_clips(
            [clip], chain=False, on_done=on_done, priority=priority, ignore_cooldown=ignore_cooldown
        )

    def play_collision(self, *, on_done=None, priority: int = VOICE_PRIORITY_SCENE, ignore_cooldown: bool = False) -> bool:
        clip = self.catalog.pick_random("vpet", "collision")
        if not clip:
            return False
        return self.play_clips(
            [clip],
            chain=False,
            on_done=on_done,
            priority=priority,
            ignore_cooldown=ignore_cooldown,
            interrupt_busy=True,
        )

    def _play_next(self, clips: list[VoiceClip], *, chain: bool, play_gen: int | None = None) -> None:
        if play_gen is None:
            play_gen = self._play_gen
        if play_gen != self._play_gen:
            return
        if not clips:
            self._finish_all()
            return
        clip = clips[0]
        rest = clips[1:]
        # 快速路径：已有内存/磁盘缓存则立刻播，绝不主线程转码
        if clip.cache_wav and clip.cache_wav.exists():
            self._start_clip(clip, rest, chain=chain, play_gen=play_gen)
            return
        safe = f"{clip.source}_{clip.category}_{clip.src_path.stem}"
        safe = re.sub(r'[<>:"/\\|?*]', "_", safe)[:120]
        candidate = voice_cache_path(self.cache_dir, safe)
        if candidate.exists():
            clip.cache_wav = candidate
            self._start_clip(clip, rest, chain=chain, play_gen=play_gen)
            return
        if clip.src_path.suffix.lower() == ".wav" and clip.src_path.exists():
            clip.cache_wav = clip.src_path
            self._start_clip(clip, rest, chain=chain, play_gen=play_gen)
            return

        def worker() -> None:
            wav = self._resolve_wav(clip)

            def cont() -> None:
                if play_gen != self._play_gen or not self.enabled:
                    return
                if wav is None:
                    # ring 解析失败绝不跳过到后续随机台词
                    if clip.is_ring:
                        self._finish_all()
                        return
                    self._play_next(rest, chain=chain, play_gen=play_gen)
                    return
                self._start_clip(clip, rest, chain=chain, play_gen=play_gen)

            try:
                self.root.after(0, cont)
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def _start_clip(
        self,
        clip: VoiceClip,
        rest: list[VoiceClip],
        *,
        chain: bool,
        play_gen: int | None = None,
    ) -> None:
        if play_gen is None:
            play_gen = self._play_gen
        if play_gen != self._play_gen:
            return
        # 调用方已保证 cache 就绪，或经由 worker 解析；此处禁止再触发主线程 ffmpeg
        wav = clip.cache_wav if clip.cache_wav and clip.cache_wav.exists() else None
        if wav is None:
            if clip.is_ring:
                self._finish_all()
                return
            self._play_next(rest, chain=chain, play_gen=play_gen)
            return
        duration_ms = max(400, self.get_duration_ms(wav))
        min_play_ms = max(500, int(duration_ms * 0.88))
        if duration_ms < 200 and not clip.is_ring:
            self._play_next(rest, chain=chain, play_gen=play_gen)
            return
        self._stop_sfx_if_needed()
        try:
            import pygame

            if not self.init_mixer():
                self._finish_all()
                return
            ch = pygame.mixer.Channel(VOICE_CHANNEL_ID)
            ch.stop()
            self._sound = pygame.mixer.Sound(str(wav))
            ch.set_volume(self.get_volume())
            # 注意：pygame.mixer.Channel.play() 成功时也返回 None（与 Sound.play 不同）
            # 原先用 `if played is None` 会误判失败 → 掐掉队列 → 有声音无字幕
            ch.play(self._sound)
            if not ch.get_busy():
                for i in range(pygame.mixer.get_num_channels()):
                    if i != VOICE_CHANNEL_ID:
                        try:
                            pygame.mixer.Channel(i).stop()
                        except Exception:
                            pass
                ch.stop()
                ch.play(self._sound)
            if not ch.get_busy():
                if clip.is_ring:
                    self._finish_all()
                    return
                self._play_next(rest, chain=chain, play_gen=play_gen)
                return
            self._channel = ch
        except Exception:
            if clip.is_ring:
                self._finish_all()
                return
            self._play_next(rest, chain=chain, play_gen=play_gen)
            return
        if play_gen != self._play_gen:
            try:
                ch.stop()
            except Exception:
                pass
            return
        self._playing = True
        self._current = clip
        self._clip_started_ms = int(time.time() * 1000)
        self._clip_deadline_ms = self._clip_started_ms + duration_ms + 500
        self._clip_min_play_ms = min_play_ms
        self._show_subtitle(clip, duration_ms)
        if rest:
            self._queue = rest
        else:
            self._queue = []
        self._schedule_watch(duration_ms, chain=chain, play_gen=play_gen)

    def _end_current_clip(self, *, chain: bool, force_stop: bool = False, play_gen: int | None = None) -> None:
        if play_gen is not None and play_gen != self._play_gen:
            return
        if force_stop:
            try:
                import pygame

                if pygame.mixer.get_init():
                    pygame.mixer.Channel(VOICE_CHANNEL_ID).stop()
            except Exception:
                pass
        finished = self._current
        self._current = None
        self._playing = False
        # 不在片段结束时立刻关字幕：字幕框由桌宠侧按时长+1s 自行关闭
        if finished and chain:
            self._maybe_chain(finished)
        if self._queue:
            pending = list(self._queue)
            self._queue.clear()
            self._play_next_sync(pending, chain=chain, play_gen=self._play_gen)
        else:
            self._finish_all()

    def _play_next_sync(self, clips: list[VoiceClip], *, chain: bool, play_gen: int | None = None) -> None:
        """同步解析路径（仅供内部队列衔接）。"""
        if play_gen is None:
            play_gen = self._play_gen
        if play_gen != self._play_gen:
            return
        if not clips:
            self._finish_all()
            return
        clip = clips[0]
        rest = clips[1:]
        if clip.cache_wav and clip.cache_wav.exists():
            self._start_clip(clip, rest, chain=chain, play_gen=play_gen)
            return

        def worker() -> None:
            wav = self._resolve_wav(clip)

            def cont() -> None:
                if play_gen != self._play_gen or not self.enabled:
                    return
                if wav is None:
                    if clip.is_ring:
                        self._finish_all()
                        return
                    self._play_next_sync(rest, chain=chain, play_gen=play_gen)
                    return
                self._start_clip(clip, rest, chain=chain, play_gen=play_gen)

            try:
                self.root.after(0, cont)
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def _schedule_watch(self, duration_ms: int, *, chain: bool, play_gen: int | None = None) -> None:
        if play_gen is None:
            play_gen = self._play_gen
        if self._watch_job:
            try:
                self.root.after_cancel(self._watch_job)
            except Exception:
                pass

        def tick() -> None:
            self._watch_job = None
            if play_gen != self._play_gen:
                return
            now_ms = int(time.time() * 1000)
            deadline_ms = getattr(self, "_clip_deadline_ms", now_ms)
            started_ms = getattr(self, "_clip_started_ms", now_ms)
            min_play_ms = getattr(self, "_clip_min_play_ms", 500)
            elapsed = now_ms - started_ms
            if now_ms >= deadline_ms:
                self._end_current_clip(chain=chain, force_stop=True, play_gen=play_gen)
                return
            busy = False
            try:
                import pygame

                if pygame.mixer.get_init():
                    busy = pygame.mixer.Channel(VOICE_CHANNEL_ID).get_busy()
            except Exception:
                busy = False
            if busy or elapsed < min_play_ms:
                self._watch_job = self.root.after(80, tick)
                return
            self._end_current_clip(chain=chain, force_stop=False, play_gen=play_gen)

        self._watch_job = self.root.after(80, tick)

    def _maybe_chain(self, clip: VoiceClip) -> None:
        has_mate = self._has_companion_cb() if self._has_companion_cb else False
        if clip.source == "vpet" and clip.prefix and clip.prefix.isdigit() and has_mate:
            mate = self.catalog.pick_by_prefix("allmate", clip.prefix)
            if mate:
                self._queue.append(mate)
        elif clip.source == "allmate" and clip.prefix and clip.prefix.isalpha():
            vpet = self.catalog.pick_by_prefix("vpet", clip.prefix, category="normal")
            if vpet:
                self._queue.append(vpet)

    def _finish_all(self) -> None:
        self._playing = False
        self._current = None
        self._session_priority = 0
        self._mark_session_end()
        # 会话结束也不强行关字幕，保留「语音时长 + 1s」显示窗口
        cb = self._done_cb
        self._done_cb = None
        if cb:
            try:
                cb()
            except Exception:
                pass

    def apply_volume(self) -> None:
        try:
            import pygame

            if pygame.mixer.get_init():
                pygame.mixer.Channel(VOICE_CHANNEL_ID).set_volume(self.get_volume())
        except Exception:
            pass
