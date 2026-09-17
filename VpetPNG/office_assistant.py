"""桌宠办公助手：待办 / 剪贴板历史 / 常用语 / 健康提醒 / 快捷启动（离线）。"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

MAX_TODOS = 50
MAX_CLIPBOARD = 30
MAX_CLIP_CHARS = 2000
MAX_PHRASES = 40
MAX_LAUNCHERS = 20

DEFAULT_PHRASES: list[dict[str, str]] = [
    {"id": "p_daily", "title": "日报开头", "body": "【今日工作】\n1. \n2. \n【明日计划】\n1. \n"},
    {"id": "p_mail", "title": "邮件开头", "body": "您好，\n\n麻烦您看一下：\n\n谢谢。\n"},
    {"id": "p_meet", "title": "会议纪要壳", "body": "【会议纪要】\n时间：\n参与人：\n决议：\n待办：\n"},
    {"id": "p_ok", "title": "收到确认", "body": "收到，我这边会处理，有进展同步您。"},
]


def _read_json(path: Path, default: Any) -> Any:
    try:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def _write_json(path: Path, data: Any) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


# —— 待办 ——

def load_todos(path: Path) -> list[dict]:
    raw = _read_json(path, [])
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for item in raw[:MAX_TODOS]:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()[:120]
        if not text:
            continue
        out.append(
            {
                "id": str(item.get("id") or uuid.uuid4()),
                "text": text,
                "done": bool(item.get("done")),
                "created_ms": int(item.get("created_ms") or time.time() * 1000),
            }
        )
    return out


def save_todos(path: Path, items: list[dict]) -> None:
    _write_json(path, items[:MAX_TODOS])


def add_todo(path: Path, text: str) -> list[dict]:
    items = load_todos(path)
    t = text.strip()[:120]
    if not t:
        return items
    items.insert(
        0,
        {"id": str(uuid.uuid4()), "text": t, "done": False, "created_ms": int(time.time() * 1000)},
    )
    save_todos(path, items)
    return items


def toggle_todo(path: Path, todo_id: str) -> list[dict]:
    items = load_todos(path)
    for it in items:
        if it["id"] == todo_id:
            it["done"] = not it["done"]
            break
    save_todos(path, items)
    return items


def remove_todo(path: Path, todo_id: str) -> list[dict]:
    items = [it for it in load_todos(path) if it["id"] != todo_id]
    save_todos(path, items)
    return items


def open_todos_preview(path: Path, *, limit: int = 3) -> list[dict]:
    """未完成优先，最多 limit 条（给悬浮条）。"""
    items = load_todos(path)
    open_ = [it for it in items if not it.get("done")]
    return open_[:limit]


# —— 剪贴板历史 ——

def load_clipboard(path: Path) -> list[dict]:
    raw = _read_json(path, [])
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for item in raw[:MAX_CLIPBOARD]:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "")[:MAX_CLIP_CHARS]
        if not text.strip():
            continue
        out.append(
            {
                "id": str(item.get("id") or uuid.uuid4()),
                "text": text,
                "ts_ms": int(item.get("ts_ms") or 0),
            }
        )
    return out


def save_clipboard(path: Path, items: list[dict]) -> None:
    _write_json(path, items[:MAX_CLIPBOARD])


def push_clipboard(path: Path, text: str) -> list[dict]:
    t = (text or "").strip("\x00")
    if not t or len(t) > MAX_CLIP_CHARS:
        t = t[:MAX_CLIP_CHARS]
    if not t.strip():
        return load_clipboard(path)
    items = load_clipboard(path)
    if items and items[0].get("text") == t:
        return items
    items = [it for it in items if it.get("text") != t]
    items.insert(0, {"id": str(uuid.uuid4()), "text": t, "ts_ms": int(time.time() * 1000)})
    save_clipboard(path, items)
    return items


# —— 常用语 ——

def load_phrases(path: Path) -> list[dict]:
    raw = _read_json(path, None)
    if raw is None:
        save_phrases(path, list(DEFAULT_PHRASES))
        return list(DEFAULT_PHRASES)
    if not isinstance(raw, list):
        return list(DEFAULT_PHRASES)
    out: list[dict] = []
    for item in raw[:MAX_PHRASES]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()[:40]
        body = str(item.get("body") or "").strip()[:2000]
        if not title or not body:
            continue
        out.append({"id": str(item.get("id") or uuid.uuid4()), "title": title, "body": body})
    return out or list(DEFAULT_PHRASES)


def save_phrases(path: Path, items: list[dict]) -> None:
    _write_json(path, items[:MAX_PHRASES])


def add_phrase(path: Path, title: str, body: str) -> list[dict]:
    items = load_phrases(path)
    items.insert(
        0,
        {
            "id": str(uuid.uuid4()),
            "title": title.strip()[:40],
            "body": body.strip()[:2000],
        },
    )
    save_phrases(path, items)
    return items


def remove_phrase(path: Path, phrase_id: str) -> list[dict]:
    items = [it for it in load_phrases(path) if it["id"] != phrase_id]
    save_phrases(path, items)
    return items


# —— 快捷启动 ——

def load_launchers(path: Path) -> list[dict]:
    raw = _read_json(path, [])
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for item in raw[:MAX_LAUNCHERS]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()[:40]
        target = str(item.get("target") or "").strip()
        kind = str(item.get("kind") or "auto").strip().lower()
        if not title or not target:
            continue
        if kind not in ("file", "folder", "url", "auto"):
            kind = "auto"
        out.append({"id": str(item.get("id") or uuid.uuid4()), "title": title, "target": target, "kind": kind})
    return out


def save_launchers(path: Path, items: list[dict]) -> None:
    _write_json(path, items[:MAX_LAUNCHERS])


def add_launcher(path: Path, title: str, target: str, kind: str = "auto") -> list[dict]:
    items = load_launchers(path)
    items.insert(
        0,
        {
            "id": str(uuid.uuid4()),
            "title": title.strip()[:40],
            "target": target.strip(),
            "kind": kind if kind in ("file", "folder", "url", "auto") else "auto",
        },
    )
    save_launchers(path, items)
    return items


def remove_launcher(path: Path, launcher_id: str) -> list[dict]:
    items = [it for it in load_launchers(path) if it["id"] != launcher_id]
    save_launchers(path, items)
    return items


def infer_launcher_kind(target: str) -> str:
    t = (target or "").strip()
    low = t.lower()
    if low.startswith("http://") or low.startswith("https://"):
        return "url"
    p = Path(t)
    if p.is_dir():
        return "folder"
    if p.is_file():
        return "file"
    return "auto"


# —— 健康提醒配置 ——

HEALTH_DEFAULTS = {
    "sit_enabled": True,
    "sit_minutes": 50,
    "water_enabled": True,
    "water_minutes": 60,
    "eye_enabled": True,
    "eye_minutes": 20,
}


def normalize_health(cfg: dict | None) -> dict:
    base = dict(HEALTH_DEFAULTS)
    if isinstance(cfg, dict):
        for k, v in HEALTH_DEFAULTS.items():
            if k in cfg:
                base[k] = cfg[k]
    base["sit_minutes"] = max(5, min(180, int(base.get("sit_minutes") or 50)))
    base["water_minutes"] = max(5, min(240, int(base.get("water_minutes") or 60)))
    base["eye_minutes"] = max(5, min(60, int(base.get("eye_minutes") or 20)))
    base["sit_enabled"] = bool(base.get("sit_enabled"))
    base["water_enabled"] = bool(base.get("water_enabled"))
    base["eye_enabled"] = bool(base.get("eye_enabled"))
    return base


# —— 桌面整理建议（只扫描、只建议，绝不自动删除）——

TIDY_LARGE_MB = 80
TIDY_OLD_DAYS = 90
TIDY_MAX_ITEMS = 10


def _human_size(n: int) -> str:
    v = float(max(0, int(n)))
    for unit in ("B", "KB", "MB", "GB"):
        if v < 1024 or unit == "GB":
            if unit == "B":
                return f"{int(v)}{unit}"
            return f"{v:.1f}{unit}"
        v /= 1024.0
    return f"{int(n)}B"


def scan_desk_tidy_suggestions(
    *,
    desktop: Path | None = None,
    downloads: Path | None = None,
    now_ms: int | None = None,
    limit: int = TIDY_MAX_ITEMS,
) -> list[dict[str, str]]:
    """扫描桌面/下载顶层，给出可人工确认的整理建议（不删文件）。"""
    home = Path.home()
    desk = desktop or (home / "Desktop")
    down = downloads or (home / "Downloads")
    # 中文系统常见别名
    if not desk.is_dir():
        alt = home / "桌面"
        if alt.is_dir():
            desk = alt
    if not down.is_dir():
        alt = home / "下载"
        if alt.is_dir():
            down = alt
    t_now = int(now_ms if now_ms is not None else time.time() * 1000)
    old_before = t_now - TIDY_OLD_DAYS * 24 * 3600 * 1000
    large_bytes = TIDY_LARGE_MB * 1024 * 1024

    files: list[tuple[Path, int, float]] = []
    name_map: dict[str, list[Path]] = {}

    def _collect(root: Path) -> None:
        if not root.is_dir():
            return
        try:
            entries = list(root.iterdir())
        except Exception:
            return
        for p in entries:
            try:
                if not p.is_file():
                    continue
                st = p.stat()
                files.append((p, int(st.st_size), float(st.st_mtime)))
                key = p.name.lower()
                name_map.setdefault(key, []).append(p)
            except Exception:
                continue

    _collect(desk)
    _collect(down)

    out: list[dict[str, str]] = []
    seen: set[str] = set()

    def _add(kind: str, title: str, path: Path, detail: str) -> None:
        key = f"{kind}:{path}"
        if key in seen or len(out) >= max(1, int(limit)):
            return
        seen.add(key)
        out.append(
            {
                "kind": kind,
                "title": title[:60],
                "path": str(path),
                "detail": detail[:80],
            }
        )

    for p, size, _mtime in sorted(files, key=lambda x: -x[1]):
        if size >= large_bytes:
            where = "桌面" if desk in p.parents or p.parent == desk else "下载"
            _add("large", f"大文件 · {where}", p, f"{_human_size(size)} · 可挪到硬盘或云盘")

    for _name, paths in name_map.items():
        if len(paths) < 2:
            continue
        # 同名出现在桌面+下载等
        parents = {str(p.parent) for p in paths}
        if len(parents) >= 2:
            _add("dup", "可能重复", paths[0], f"另有 {len(paths) - 1} 处同名 · 请人工核对")

    for p, size, mtime in files:
        mtime_ms = int(mtime * 1000)
        if mtime_ms < old_before and size > 2 * 1024 * 1024:
            if down in p.parents or p.parent == down:
                _add("old", "下载区旧文件", p, f"超过 {TIDY_OLD_DAYS} 天 · {_human_size(size)}")

    return out[: max(1, int(limit))]


def reveal_in_explorer(path: str) -> tuple[bool, str]:
    """在资源管理器中显示文件（不删除）。"""
    import os
    import subprocess
    import sys

    p = Path(str(path or ""))
    if not p.exists():
        return False, "文件已不存在"
    try:
        if sys.platform.startswith("win"):
            subprocess.Popen(["explorer", "/select,", str(p.resolve())], shell=False)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", str(p.resolve())])
        else:
            subprocess.Popen(["xdg-open", str(p.parent)])
        return True, "已打开所在位置"
    except Exception as exc:
        try:
            os.startfile(str(p.parent))  # type: ignore[attr-defined]
            return True, "已打开所在文件夹"
        except Exception:
            return False, f"无法打开：{type(exc).__name__}"
