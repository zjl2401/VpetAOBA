"""Vpet 托盘启动器：点击图标即可生成一只桌宠；可选开机自启并自动显示桌宠。"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

# 苍叶 / 伊得分端口，双开互不抢锁、也不会因「stale」去关对方
LAUNCHER_PORT_AOBA = 52847
LAUNCHER_PORT_EIDEN = 52848
APP_ROOT = Path(__file__).resolve().parent
STARTUP_LNK_NAME = "Vpet Aoba.lnk"


def _resolve_launcher_kind() -> str:
    """启动器身份：--kind > VPET_KIND > KIND.txt > 默认 aoba。"""
    args = [str(a).strip().lower() for a in sys.argv[1:]]
    for i, a in enumerate(args):
        if a == "--kind" and i + 1 < len(args):
            k = args[i + 1].lstrip("-")
            if k in ("aoba", "eiden"):
                return k
        if a.startswith("--kind="):
            k = a.split("=", 1)[-1].strip().lower()
            if k in ("aoba", "eiden"):
                return k
    env = str(os.environ.get("VPET_KIND") or "").strip().lower()
    if env in ("aoba", "eiden"):
        return env
    bases: list[Path] = []
    if getattr(sys, "frozen", False):
        try:
            bases.append(Path(sys._MEIPASS))  # type: ignore[attr-defined]
        except Exception:
            pass
        try:
            bases.append(Path(sys.executable).resolve().parent)
        except Exception:
            pass
    bases.append(APP_ROOT)
    for base in bases:
        try:
            p = base / "KIND.txt"
            if p.is_file():
                k = p.read_text(encoding="utf-8").strip().lower()
                if k in ("aoba", "eiden"):
                    return k
        except Exception:
            continue
    return "aoba"


LAUNCHER_KIND = _resolve_launcher_kind()
# 本仓库发布包只有苍叶立绘：禁止以 eiden 身份写「Vpet Eiden」开机项（会把用户骗到假伊得）。
if LAUNCHER_KIND == "eiden":
    LAUNCHER_KIND = "aoba"
LAUNCHER_PORT = LAUNCHER_PORT_AOBA
STARTUP_LNK_NAME = "Vpet Aoba.lnk"


def _resource_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return APP_ROOT


def _data_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return APP_ROOT


def _userdata_dir() -> Path:
    """与 pet._resolve_app_paths 对齐：便携包用 exe 旁 data，否则 LOCALAPPDATA\\Vpet\\userdata。"""
    if getattr(sys, "frozen", False):
        app_dir = Path(sys.executable).resolve().parent
        if (app_dir / "PORTABLE").is_file() or (app_dir / "PORTABLE.txt").is_file():
            d = app_dir / "data"
            d.mkdir(parents=True, exist_ok=True)
            return d
        d = Path(os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or str(Path.home())) / "Vpet" / "userdata"
        d.mkdir(parents=True, exist_ok=True)
        return d
    # 开发态：与 pet 同目录 data
    d = APP_ROOT / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _app_config_path() -> Path:
    return _userdata_dir() / "app_config.json"


def _load_app_config_light() -> dict:
    path = _app_config_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_app_config_light(patch: dict) -> None:
    path = _app_config_path()
    cfg = _load_app_config_light()
    cfg.update(patch)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def launch_at_login_enabled() -> bool:
    """默认开启：开机启动托盘并自动显示桌宠。"""
    cfg = _load_app_config_light()
    if "launch_at_login" not in cfg:
        return True
    return bool(cfg.get("launch_at_login"))


def spawn_on_launcher_start() -> bool:
    """启动器起来时是否自动新建一只桌宠（默认与开机自启一致）。"""
    cfg = _load_app_config_light()
    if "spawn_on_launcher_start" in cfg:
        return bool(cfg.get("spawn_on_launcher_start"))
    return launch_at_login_enabled()


def _windows_startup_dir() -> Path | None:
    if sys.platform != "win32":
        return None
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def _startup_lnk_path() -> Path | None:
    folder = _windows_startup_dir()
    if folder is None:
        return None
    return folder / STARTUP_LNK_NAME


def _launcher_target() -> tuple[str, str]:
    """返回 (TargetPath, WorkingDirectory)。"""
    if getattr(sys, "frozen", False):
        exe = str(Path(sys.executable).resolve())
        return exe, str(Path(sys.executable).resolve().parent)
    # 开发：用当前解释器跑 vpet_app.py（进托盘）
    script = str((APP_ROOT / "vpet_app.py").resolve())
    return sys.executable, str(APP_ROOT), script  # type: ignore[return-value]


def sync_windows_startup(enabled: bool, *, force: bool = False) -> bool:
    """写入或删除「启动」文件夹快捷方式。成功返回 True。

    默认若快捷方式已存在则跳过 PowerShell（避免每次出宠都卡几百毫秒～数秒）。
    设置里改开机自启时应传 force=True。
    """
    if sys.platform != "win32":
        return False
    lnk = _startup_lnk_path()
    if lnk is None:
        return False
    if not enabled:
        try:
            if lnk.is_file():
                lnk.unlink()
            return True
        except OSError:
            return False
    try:
        lnk.parent.mkdir(parents=True, exist_ok=True)
        # 已有快捷方式：跳过重建（出宠路径高频调用）
        if not force and lnk.is_file():
            return True
        kind = LAUNCHER_KIND
        if getattr(sys, "frozen", False):
            target = str(Path(sys.executable).resolve())
            workdir = str(Path(sys.executable).resolve().parent)
            # 开机只起托盘；出宠由 spawn_on_launcher_start 控制，勿用 --pet（否则无托盘）
            args = f"--kind {kind}"
        else:
            target = sys.executable
            workdir = str(APP_ROOT)
            args = f'"{(APP_ROOT / "vpet_app.py").resolve()}" --kind {kind}'
        desc = "Vpet Eiden 开机自启" if kind == "eiden" else "Vpet Aoba 开机自启"
        # PowerShell 创建 .lnk，避免依赖 pywin32
        ps = (
            "$ws = New-Object -ComObject WScript.Shell; "
            f"$s = $ws.CreateShortcut('{str(lnk).replace(chr(39), chr(39)+chr(39))}'); "
            f"$s.TargetPath = '{target.replace(chr(39), chr(39)+chr(39))}'; "
            f"$s.WorkingDirectory = '{workdir.replace(chr(39), chr(39)+chr(39))}'; "
            f"$s.Arguments = '{args.replace(chr(39), chr(39)+chr(39))}'; "
            "$s.WindowStyle = 7; "
            f"$s.Description = '{desc}'; "
            "$s.Save()"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
        return lnk.is_file()
    except Exception:
        return False


def set_launch_at_login(enabled: bool) -> None:
    """设置开机自启，并同步 Windows 启动项；开启时启动器也会自动出宠。"""
    enabled = bool(enabled)
    _save_app_config_light(
        {
            "launch_at_login": enabled,
            "spawn_on_launcher_start": enabled,
        }
    )
    sync_windows_startup(enabled, force=True)


def ensure_launch_prefs_defaults() -> None:
    """首次无配置时写入默认：开机自启 + 启动器自动出宠。"""
    cfg = _load_app_config_light()
    changed = False
    if "launch_at_login" not in cfg:
        cfg["launch_at_login"] = True
        changed = True
    if "spawn_on_launcher_start" not in cfg:
        cfg["spawn_on_launcher_start"] = True
        changed = True
    if changed:
        _save_app_config_light(cfg)
    if cfg.get("launch_at_login", True):
        sync_windows_startup(True)


def _my_exe() -> str:
    return str(Path(sys.executable).resolve())


def _normalize_kind(raw: str | None) -> str:
    k = str(raw or "").strip().lower()
    return k if k in ("aoba", "eiden") else LAUNCHER_KIND


def _pet_spawn_command(*, kind: str | None = None) -> list[str]:
    k = _normalize_kind(kind)
    if getattr(sys, "frozen", False):
        return [sys.executable, "--pet", "--kind", k]
    return [sys.executable, str(APP_ROOT / "vpet_app.py"), "--pet", "--kind", k]


def _pet_log_path() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Vpet"
    else:
        base = Path.home() / ".vpet"
    base.mkdir(parents=True, exist_ok=True)
    return base / "pet.log"


_last_spawn_ts = 0.0
_spawn_lock = threading.Lock()


def _show_spawn_feedback(ms: int = 1600) -> None:
    """点击快捷方式/托盘后立刻给反馈，避免 exe 冷启期间像没反应。"""

    def _run() -> None:
        try:
            import tkinter as tk
        except Exception:
            return
        try:
            root = tk.Tk()
            root.overrideredirect(True)
            root.attributes("-topmost", True)
            root.configure(bg="#1a2233")
            label = tk.Label(
                root,
                text="正在打开桌宠…",
                fg="#ffe08a",
                bg="#1a2233",
                font=("Segoe UI", 12),
                padx=18,
                pady=12,
            )
            label.pack()
            root.update_idletasks()
            w = max(root.winfo_reqwidth(), 160)
            h = max(root.winfo_reqheight(), 40)
            sw = root.winfo_screenwidth()
            sh = root.winfo_screenheight()
            root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
            root.after(max(800, int(ms)), root.destroy)
            root.mainloop()
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()


def spawn_pet(*, show_feedback: bool = True, kind: str | None = None) -> None:
    """新建一只桌宠（独立进程）；绝不关闭已有桌宠。连点时自动错开。"""
    if show_feedback:
        _show_spawn_feedback()
    spawn_kind = _normalize_kind(kind)

    def _do_spawn() -> None:
        global _last_spawn_ts
        with _spawn_lock:
            now = time.time()
            # 仅连点错开；首次 spawn 不要空等 1.4s（_last_spawn_ts==0 时旧逻辑会白等）
            if _last_spawn_ts > 0:
                wait = 1.4 - (now - _last_spawn_ts)
                if wait > 0.05:
                    time.sleep(wait)
            _last_spawn_ts = time.time()
        cmd = _pet_spawn_command(kind=spawn_kind)
        cwd = str(_data_root())
        log_path = _pet_log_path()
        try:
            log_file = log_path.open("a", encoding="utf-8")
            log_file.write(
                f"\n--- spawn {time.strftime('%Y-%m-%d %H:%M:%S')} kind={spawn_kind} ---\n"
            )
            log_file.flush()
        except OSError:
            log_file = subprocess.DEVNULL
        kwargs: dict = {
            "cwd": cwd,
            "close_fds": True,
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.DEVNULL,
            "stderr": log_file,
        }
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
        subprocess.Popen(cmd, **kwargs)

    threading.Thread(target=_do_spawn, daemon=True).start()


def _launcher_exchange(payload: str, *, timeout: float = 0.5) -> str | None:
    try:
        with socket.create_connection(("127.0.0.1", LAUNCHER_PORT), timeout=timeout) as sock:
            sock.sendall(payload.encode("utf-8"))
            sock.shutdown(socket.SHUT_WR)
            sock.settimeout(timeout)
            data = sock.recv(512)
            return data.decode("utf-8", errors="ignore").strip() or None
    except OSError:
        return None


def _hold_launcher_lock() -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", LAUNCHER_PORT))
    sock.listen(5)
    return sock


def _load_tray_icon():
    from PIL import Image, ImageDraw
    from collections import deque

    def _is_chroma_green(r: int, g: int, b: int, a: int = 255) -> bool:
        if a < 8:
            return False
        if g > 200 and r < 90 and b < 90:
            return True
        return g > 100 and g >= r + 15 and g >= b + 25

    def _key_and_fit(im: Image.Image, size: int) -> Image.Image:
        rgba = im.convert("RGBA")
        w, h = rgba.size
        px = rgba.load()
        visited = [[False] * w for _ in range(h)]
        q: deque[tuple[int, int]] = deque()
        for x in range(w):
            q.append((x, 0))
            q.append((x, h - 1))
        for y in range(h):
            q.append((0, y))
            q.append((w - 1, y))
        while q:
            x, y = q.popleft()
            if x < 0 or y < 0 or x >= w or y >= h or visited[y][x]:
                continue
            r, g, b, a = px[x, y]
            if not _is_chroma_green(r, g, b, a):
                continue
            visited[y][x] = True
            px[x, y] = (r, g, b, 0)
            q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
        bbox = rgba.getbbox()
        if bbox:
            rgba = rgba.crop(bbox)
        # 等比装入，不拉伸
        iw, ih = rgba.size
        scale = min(size / max(iw, 1), size / max(ih, 1))
        nw = max(1, int(round(iw * scale)))
        nh = max(1, int(round(ih * scale)))
        scaled = rgba.resize((nw, nh), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        canvas.paste(scaled, ((size - nw) // 2, (size - nh) // 2), scaled)
        return canvas

    root = _resource_root()
    for rel in (
        "app_icon.png",
        "assets/sprites/stand.jpg",
        "assets/sprites/stand.png",
        "gallery/stand.png",
        "app_icon1.png",
        "app_icon1.jpg",
    ):
        path = root / rel
        if path.exists():
            # 已生成的 app_icon 直接等比缩放；源 stand 则抠绿再装入
            img = Image.open(path).convert("RGBA")
            if path.name == "app_icon.png":
                return img.resize((64, 64), Image.Resampling.LANCZOS)
            return _key_and_fit(img, 64)
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle((12, 10, 52, 54), fill="#4488ff")
    draw.rectangle((22, 18, 42, 28), fill="#ffffff")
    return img


def run_tray(*, spawn_on_start: bool = True) -> None:
    import pystray

    if spawn_on_start:
        spawn_pet()

    lock_sock = _hold_launcher_lock()
    stop_event = threading.Event()
    tray_icon: pystray.Icon | None = None

    def on_spawn(_icon=None, _item=None) -> None:
        spawn_pet()

    def on_quit(icon, _item) -> None:
        stop_event.set()
        icon.stop()

    def accept_loop() -> None:
        while not stop_event.is_set():
            try:
                lock_sock.settimeout(1.0)
                client, _addr = lock_sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            with client:
                try:
                    data = client.recv(512).decode("utf-8", errors="ignore").strip()
                except OSError:
                    data = ""
                if data.startswith("hello:"):
                    remote = data[6:]
                    local = _my_exe()
                    try:
                        client.sendall(b"same" if remote == local else b"stale")
                    except OSError:
                        pass
                    continue
                if data == "quit":
                    # 仅退出本启动器托盘，不杀任何已打开的桌宠进程
                    stop_event.set()
                    if tray_icon is not None:
                        try:
                            tray_icon.stop()
                        except Exception:
                            pass
                    return
                if data == "spawn" or data.startswith("spawn"):
                    kind = None
                    if data.startswith("spawn:"):
                        kind = data.split(":", 1)[-1]
                    spawn_pet(show_feedback=True, kind=kind)

    threading.Thread(target=accept_loop, daemon=True).start()

    menu = pystray.Menu(
        pystray.MenuItem("新建桌宠", on_spawn, default=True),
        pystray.MenuItem("退出启动器", on_quit),
    )
    tip = "Vpet Eiden" if LAUNCHER_KIND == "eiden" else "Vpet Aoba"
    if spawn_on_start:
        tip += "\n已自动显示桌宠；托盘可再新建"
    else:
        tip += "\n点击「新建桌宠」生成一只"
    tray_icon = pystray.Icon(
        tip.split("\n", 1)[0],
        _load_tray_icon(),
        tip,
        menu,
    )
    try:
        tray_icon.run()
    finally:
        stop_event.set()
        try:
            lock_sock.close()
        except OSError:
            pass


def main() -> None:
    ensure_launch_prefs_defaults()
    exe = _my_exe()
    reply = _launcher_exchange(f"hello:{exe}")
    spawn_payload = f"spawn:{LAUNCHER_KIND}"
    if reply == "same":
        # 同一启动器已在：只加一只宠，绝不关闭已有桌宠
        _launcher_exchange(spawn_payload)
        return
    if reply == "stale":
        # 端口上已有其它路径的启动器：请它再生成一只，绝不 quit / 绝不杀进程
        _launcher_exchange(spawn_payload)
        return
    run_tray(spawn_on_start=spawn_on_launcher_start())


if __name__ == "__main__":
    main()
