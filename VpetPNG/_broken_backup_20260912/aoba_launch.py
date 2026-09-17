# -*- coding: utf-8 -*-
"""桌面快捷方式入口：跑磁盘上的 pet.py，并优先用源码目录依赖。"""
from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path


def _here() -> Path:
    return Path(__file__).resolve().parent


def _source_dir() -> Path | None:
    env = str(os.environ.get("VPET_AOBA_SRC") or "").strip()
    if env:
        p = Path(env)
        if (p / "pet.py").is_file():
            return p
    for cand in (
        Path.home() / "Desktop" / "VpetAOBA" / "VpetPNG",
        _here().parent / "VpetAOBA" / "VpetPNG",
    ):
        if (cand / "pet.py").is_file():
            return cand
    return None


def _log(msg: str) -> None:
    try:
        p = _here() / "launch.log"
        with p.open("a", encoding="utf-8") as fh:
            fh.write(msg.rstrip() + "\n")
    except Exception:
        pass


def _fail(exc: BaseException) -> None:
    _log(traceback.format_exc())
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "苍叶启动失败",
            f"{exc}\n\n详情：{_here() / 'launch.log'}",
            parent=root,
        )
        root.destroy()
    except Exception:
        pass
    raise SystemExit(1) from exc


def _setup_tcl(internal: Path) -> None:
    """PyInstaller 的 _tcl_data/_tk_data，或本机 Python 的 Tcl。"""
    tcl = internal / "_tcl_data"
    tk = internal / "_tk_data"
    if tcl.is_dir() and not os.environ.get("TCL_LIBRARY"):
        os.environ["TCL_LIBRARY"] = str(tcl)
    if tk.is_dir() and not os.environ.get("TK_LIBRARY"):
        os.environ["TK_LIBRARY"] = str(tk)
    # conda/python 自带
    py_root = Path(sys.base_prefix)
    for cand in (
        py_root / "tcl" / "tcl8.6",
        py_root / "Library" / "lib" / "tcl8.6",
    ):
        if cand.is_dir() and not os.environ.get("TCL_LIBRARY"):
            os.environ["TCL_LIBRARY"] = str(cand)
            break
    for cand in (
        py_root / "tcl" / "tk8.6",
        py_root / "Library" / "lib" / "tk8.6",
    ):
        if cand.is_dir() and not os.environ.get("TK_LIBRARY"):
            os.environ["TK_LIBRARY"] = str(cand)
            break


def main() -> None:
    here = _here()
    internal = here / "_internal"
    src = _source_dir()
    exe = here / "Vpet.exe"
    real_py = Path(sys.executable).resolve()
    _log(f"--- launch {os.getpid()} ---")
    _log(f"here={here}")
    _log(f"src={src}")
    _log(f"py={real_py}")

    # 切到安装根目录，切勿 chdir 到 _internal（里面有打包的 numpy，会炸）
    os.chdir(str(here))
    _setup_tcl(internal)

    try:
        import pygame  # noqa: F401
        from PIL import Image  # noqa: F401
    except Exception as exc:
        _fail(exc)

    os.environ["VPET_KIND"] = "aoba"
    os.environ["VPET_APP_DIR"] = str(here)
    if src is not None:
        os.environ["VPET_AOBA_SRC"] = str(src)

    # 路径优先：源码 > 安装根 > _internal
    for p in (internal, here, src):
        if p is None:
            continue
        s = str(p)
        while s in sys.path:
            sys.path.remove(s)
        sys.path.insert(0, s)

    # 立绘走 _internal；不要改 sys.executable，否则 tkinter 找不到 Tcl
    sys.frozen = True  # type: ignore[attr-defined]
    sys._MEIPASS = str(internal if internal.is_dir() else here)  # type: ignore[attr-defined]

    argv = [str(real_py), "--pet", "--kind", "aoba"]
    sys.argv = argv + [a for a in sys.argv[1:] if a not in ("--pet", "--kind", "aoba")]

    try:
        # app_dir：优先读环境变量，避免 sys.executable 指向 pythonw
        import bundled_paths

        _orig_app_dir = bundled_paths.app_dir

        def _app_dir() -> Path:
            override = str(os.environ.get("VPET_APP_DIR") or "").strip()
            if override:
                return Path(override)
            return _orig_app_dir()

        bundled_paths.app_dir = _app_dir  # type: ignore[assignment]

        import vpet_app
        from pet import CODE_REV

        _log(f"CODE_REV={CODE_REV}")
        _log(f"TCL_LIBRARY={os.environ.get('TCL_LIBRARY')}")
        _log(f"TK_LIBRARY={os.environ.get('TK_LIBRARY')}")
        stamp = here / "LOADED_REV.txt"
        stamp.write_text(str(CODE_REV), encoding="utf-8")
        if internal.is_dir():
            (internal / "LOADED_REV.txt").write_text(str(CODE_REV), encoding="utf-8")
        vpet_app.main()
    except Exception as exc:
        _fail(exc)


if __name__ == "__main__":
    main()
