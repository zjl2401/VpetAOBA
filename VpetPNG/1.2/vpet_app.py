"""Vpet 桌面程序入口：默认打开托盘启动器；--pet 直接运行桌宠。"""

from __future__ import annotations

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


def main() -> None:
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
