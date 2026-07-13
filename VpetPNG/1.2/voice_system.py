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

_PREFIX_RE = re.compile(r"^(\d+|[a-zA-Z])\s+(.+)$")
_RING_NAMES = frozenset({"ring", "call-ring", "call_ring", "callring"})
_STARTUP_HINTS = ("启动", "启动音")


def _is_ring_stem(stem: str) -> bool:
    low = stem.lower().strip()
    if low in _RING_NAMES or low.endswith("-ring") or low.endswith("_ring"):
        return True
    compact = re.sub(r"[\s_\-]+", "", low)
    if compact in ("ring", "callring"):
        return True
    return "call" in low and "ring" in low


def _parse_stem(stem: str) -> tuple[str | None, str, bool, bool]:
    if _is_ring_stem(stem):
        return None, "铃响", True, False
    if any(h in stem for h in _STARTUP_HINTS):
        return None, stem, False, True
    m = _PREFIX_RE.match(stem)
    if m:
        prefix = m.group(1).lower() if m.group(1).isalpha() else m.group(1)
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
                    category = rel.parts[0].lower()
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

    def pick_random(self, source: str, category: str, *, exclude_ring: bool = False) -> VoiceClip | None:
        pool = self._pool(source, category)
        if exclude_ring:
            pool = [c for c in pool if not c.is_ring]
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
        ring_pool = [c for c in self.allmate.get("startup", []) if c.is_ring]
        if ring_pool:
            return random.choice(ring_pool)
        startup_pool = [c for c in self.allmate.get("startup", []) if c.is_startup]
        if startup_pool:
            return random.choice(startup_pool)
        misc_pool = [c for c in self.allmate.get("misc", []) if c.is_ring or c.is_startup]
        return random.choice(misc_pool) if misc_pool else None

    def pick_call_sequence(self) -> list[VoiceClip]:
        """打电话语音：必须先 ring，再从 Vpet/call 非 ring 条目随机选一条。"""
        call_clips = self.vpet.get("call", [])
        rings = [c for c in call_clips if c.is_ring]
        body_pool = [c for c in call_clips if not c.is_ring]
        if not rings or not body_pool:
            return []
        ring = sorted(rings, key=lambda c: (0 if _is_ring_stem(c.src_path.stem) else 1, c.src_path.name))[0]
        return [ring, random.choice(body_pool)]

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
        self.catalog = VoiceCatalog.build()
        self._queue: list[VoiceClip] = []
        self._playing = False
        self._current: VoiceClip | None = None
        self._sound = None
        self._channel = None
        self._watch_job: str | None = None
        self._subtitle_cb: Callable[[str, int], None] | None = None
        self._hide_subtitle_cb: Callable[[], None] | None = None
        self._has_companion_cb: Callable[[], bool] | None = None
        self._done_cb: Callable[[], None] | None = None
        self._session_priority = 0
        self._last_session_end_ms = 0

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
        subtitle_cb: Callable[[str, int], None] | None = None,
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
        self._session_priority = priority
        self._done_cb = on_done

    def stop(self) -> None:
        was_busy = self.is_busy()
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
        total = 0
        for clip in clips:
            wav = self._resolve_wav(clip)
            if wav:
                total += max(400, self.get_duration_ms(wav))
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
        if clip.is_ring:
            return
        if self._subtitle_cb:
            self._subtitle_cb(clip.title, duration_ms)

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
            if interrupt_busy or ignore_cooldown:
                self.stop()
            else:
                return False
        if not ignore_cooldown and not self._global_cooldown_ready():
            return False
        if not self._can_start(priority):
            return False
        self._begin_session(priority, on_done)
        self._play_next(clips, chain=chain)
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

    def preload_all_clips(self, *, on_done: Callable[[int, int], None] | None = None) -> None:
        """后台将全部语音转为 wav 缓存，避免播放时临时转换卡顿。"""
        self._preload_clips(self.all_catalog_clips(), on_done=on_done)

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
            for clip in clips:
                if getattr(self, "_preload_token", 0) != token:
                    return
                try:
                    if self._resolve_wav(clip):
                        ok += 1
                except Exception:
                    pass
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
    ) -> bool:
        clip = self.catalog.pick_random("vpet", category)
        if not clip:
            return False
        return self.play_clips(
            [clip], chain=chain, on_done=on_done, priority=priority, ignore_cooldown=ignore_cooldown
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
        seq = clips if clips is not None else self.catalog.pick_call_sequence()
        if len(seq) < 2:
            return False
        return self.play_clips(
            seq,
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
            [clip], chain=False, on_done=on_done, priority=priority, ignore_cooldown=ignore_cooldown
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
            [clip], chain=False, on_done=on_done, priority=priority, ignore_cooldown=ignore_cooldown
        )

    def _play_next(self, clips: list[VoiceClip], *, chain: bool) -> None:
        if not clips:
            self._finish_all()
            return
        clip = clips[0]
        rest = clips[1:]
        if clip.cache_wav and clip.cache_wav.exists():
            self._start_clip(clip, rest, chain=chain)
            return

        def worker() -> None:
            wav = self._resolve_wav(clip)

            def cont() -> None:
                if not self.enabled:
                    return
                if wav is None:
                    self._play_next(rest, chain=chain)
                    return
                self._start_clip(clip, rest, chain=chain)

            try:
                self.root.after(0, cont)
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def _start_clip(self, clip: VoiceClip, rest: list[VoiceClip], *, chain: bool) -> None:
        wav = clip.cache_wav if clip.cache_wav and clip.cache_wav.exists() else self._resolve_wav(clip)
        if wav is None:
            self._hide_subtitle_now()
            self._play_next(rest, chain=chain)
            return
        duration_ms = max(400, self.get_duration_ms(wav))
        min_play_ms = max(500, int(duration_ms * 0.88))
        if duration_ms < 200 and not clip.is_ring:
            self._hide_subtitle_now()
            self._play_next(rest, chain=chain)
            return
        self._stop_sfx_if_needed()
        try:
            import pygame

            if not self.init_mixer():
                self._hide_subtitle_now()
                self._finish_all()
                return
            ch = pygame.mixer.Channel(VOICE_CHANNEL_ID)
            ch.stop()
            self._sound = pygame.mixer.Sound(str(wav))
            ch.set_volume(self.get_volume())
            played = ch.play(self._sound)
            if played is None:
                for i in range(pygame.mixer.get_num_channels()):
                    if i != VOICE_CHANNEL_ID:
                        try:
                            pygame.mixer.Channel(i).stop()
                        except Exception:
                            pass
                ch.stop()
                played = ch.play(self._sound)
            if played is None:
                self._hide_subtitle_now()
                self._play_next(rest, chain=chain)
                return
            self._channel = ch
        except Exception:
            self._hide_subtitle_now()
            self._play_next(rest, chain=chain)
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
        self._schedule_watch(duration_ms, chain=chain)

    def _end_current_clip(self, *, chain: bool, force_stop: bool = False) -> None:
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
        self._hide_subtitle_now()
        if finished and chain:
            self._maybe_chain(finished)
        if self._queue:
            pending = list(self._queue)
            self._queue.clear()
            self._play_next_sync(pending, chain=chain)
        else:
            self._finish_all()

    def _play_next_sync(self, clips: list[VoiceClip], *, chain: bool) -> None:
        """同步解析路径（仅供内部队列衔接）。"""
        if not clips:
            self._finish_all()
            return
        clip = clips[0]
        rest = clips[1:]
        if clip.cache_wav and clip.cache_wav.exists():
            self._start_clip(clip, rest, chain=chain)
            return

        def worker() -> None:
            wav = self._resolve_wav(clip)

            def cont() -> None:
                if not self.enabled:
                    return
                if wav is None:
                    self._play_next_sync(rest, chain=chain)
                    return
                self._start_clip(clip, rest, chain=chain)

            try:
                self.root.after(0, cont)
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def _schedule_watch(self, duration_ms: int, *, chain: bool) -> None:
        if self._watch_job:
            try:
                self.root.after_cancel(self._watch_job)
            except Exception:
                pass

        def tick() -> None:
            self._watch_job = None
            now_ms = int(time.time() * 1000)
            deadline_ms = getattr(self, "_clip_deadline_ms", now_ms)
            started_ms = getattr(self, "_clip_started_ms", now_ms)
            min_play_ms = getattr(self, "_clip_min_play_ms", 500)
            elapsed = now_ms - started_ms
            if now_ms >= deadline_ms:
                self._end_current_clip(chain=chain, force_stop=True)
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
            self._end_current_clip(chain=chain, force_stop=False)

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
        self._hide_subtitle_now()
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
