"""Vpet 桌面程序入口：默认打开托盘启动器；--pet 直接运行桌宠；--rpg 打开 RPG。"""

from __future__ import annotations

import importlib.util
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


def _runtime_module_dirs() -> list[Path]:
    """打包后优先找 _internal / exe 旁的 sidecar .py，便于热更新 pet.py。"""
    dirs: list[Path] = []
    # 开发热更新：源码目录 / 安装根优先于冻结包
    for key in ("VPET_AOBA_SRC", "VPET_APP_DIR"):
        raw = str(os.environ.get(key) or "").strip()
        if raw:
            dirs.append(Path(raw))
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        # 若 executable 是 pythonw，则用 VPET_APP_DIR；否则用 exe 旁
        app = str(os.environ.get("VPET_APP_DIR") or "").strip()
        if app:
            app_p = Path(app)
            dirs.append(app_p)
            dirs.append(app_p / "_internal")
        dirs.append(exe_dir)
        dirs.append(exe_dir / "_internal")
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            dirs.append(Path(meipass))
    dirs.append(Path(__file__).resolve().parent)
    out: list[Path] = []
    seen: set[str] = set()
    for d in dirs:
        key = str(d).lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(d)
    return out


def _load_sidecar_module(name: str) -> bool:
    """若磁盘上有同名 .py，则覆盖冻结包内模块。成功返回 True。"""
    if name in sys.modules and not getattr(sys, "frozen", False):
        return False
    for base in _runtime_module_dirs():
        path = base / f"{name}.py"
        if not path.is_file():
            continue
        try:
            spec = importlib.util.spec_from_file_location(name, path)
            if spec is None or spec.loader is None:
                continue
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
            return True
        except Exception:
            sys.modules.pop(name, None)
            continue
    return False


def _bootstrap_sidecars() -> None:
    # 先 peer / 依赖，再 pet（pet 会 import 它们）
    for name in (
        "peer_friendship",
        "pet_outfit",
        "home_cottage",
        "panel_decor",
        "bundled_paths",
        "media_bundled",
        "voice_audio",
        "voice_system",
        "pet_id_cloud",
        "app_scene_desktop",
        "rhythm_chart_editor",
        "vpet_launcher",
        "pet",
    ):
        _load_sidecar_module(name)


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
    _bootstrap_sidecars()
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
