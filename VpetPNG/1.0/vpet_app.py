"""Vpet 桌面程序入口：默认打开托盘启动器；--pet 直接运行桌宠；--rpg 打开 RPG。"""

from __future__ import annotations

import os
import sys
import traceback
from datetime import datetime
from pathlib import Path


def _pet_log_path() -> Path:
    if sys.platform == "win32":
        base = Path.home() / "AppData" / "Local" / "Vpet"
    else:
        base = Path.home() / ".vpet"
    base.mkdir(parents=True, exist_ok=True)
    return base / "pet.log"


def _log_pet_error(exc: BaseException) -> None:
    try:
        log_path = _pet_log_path()
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(f"\n--- {datetime.now().isoformat(timespec='seconds')} ---\n")
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=fh)
    except Exception:
        pass


def _show_pet_error(exc: BaseException) -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Vpet 启动失败",
            f"{exc}\n\n详情已写入：{_pet_log_path()}",
            parent=root,
        )
        root.destroy()
    except Exception:
        pass


def _run_rpg() -> None:
    """独立进程打开 Silent Oath（模式→游戏→RPG）。"""
    from bundled_paths import LEGACY_GAME_ROOT, resolve_bundled

    root = resolve_bundled("Vpetgame", legacy=LEGACY_GAME_ROOT)
    game_py = root / "game.py"
    if not game_py.is_file():
        raise FileNotFoundError(f"未找到 RPG：{game_py}")
    os.chdir(root)
    import runpy

    runpy.run_path(str(game_py), run_name="__main__")


def main() -> None:
    # 顶层侧显式引用，避免 PyInstaller 漏打进 pet / 启动器（二者原先在分支内 import）
    import pet  # noqa: F401
    import vpet_launcher  # noqa: F401

    if "--rpg" in sys.argv:
        try:
            _run_rpg()
        except Exception as exc:
            _log_pet_error(exc)
            _show_pet_error(exc)
            raise SystemExit(1) from exc
        return
    if "--pet" in sys.argv:
        try:
            from pet import DesktopPet

            DesktopPet().run()
        except Exception as exc:
            _log_pet_error(exc)
            _show_pet_error(exc)
            raise SystemExit(1) from exc
        return
    from vpet_launcher import main as run_launcher

    run_launcher()


if __name__ == "__main__":
    main()
