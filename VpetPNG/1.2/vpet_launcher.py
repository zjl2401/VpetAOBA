"""Vpet 托盘启动器：点击图标即可生成一只桌宠，无需重复打开终端。"""

from __future__ import annotations

import socket
import subprocess
import sys
import threading
from pathlib import Path

LAUNCHER_PORT = 52847
APP_ROOT = Path(__file__).resolve().parent


def _resource_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return APP_ROOT


def _data_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return APP_ROOT


def _pet_spawn_command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, "--pet"]
    return [sys.executable, str(APP_ROOT / "vpet_app.py"), "--pet"]


def spawn_pet() -> None:
    cmd = _pet_spawn_command()
    cwd = str(_data_root())
    kwargs: dict = {
        "cwd": cwd,
        "close_fds": True,
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW
    subprocess.Popen(cmd, **kwargs)


def _notify_running_launcher() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", LAUNCHER_PORT), timeout=0.35) as sock:
            sock.sendall(b"spawn")
        return True
    except OSError:
        return False


def _hold_launcher_lock() -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", LAUNCHER_PORT))
    sock.listen(5)
    return sock


def _load_tray_icon():
    from PIL import Image, ImageDraw

    root = _resource_root()
    for rel in ("gallery/stand.png", "app_icon.png"):
        path = root / rel
        if path.exists():
            img = Image.open(path).convert("RGBA")
            return img.resize((64, 64), Image.Resampling.LANCZOS)
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
                    client.recv(16)
                except OSError:
                    pass
            on_spawn()

    threading.Thread(target=accept_loop, daemon=True).start()

    menu = pystray.Menu(
        pystray.MenuItem("新建桌宠", on_spawn, default=True),
        pystray.MenuItem("退出启动器", on_quit),
    )
    icon = pystray.Icon(
        "Vpet",
        _load_tray_icon(),
        "Vpet 桌宠\n点击「新建桌宠」生成一只",
        menu,
    )
    try:
        icon.run()
    finally:
        stop_event.set()
        try:
            lock_sock.close()
        except OSError:
            pass


def main() -> None:
    if _notify_running_launcher():
        return
    run_tray(spawn_on_start=False)


if __name__ == "__main__":
    main()
