#!/usr/bin/env python3
"""打包 Vpet 为 Windows 桌面程序，并创建桌面快捷方式。"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
BUILD = ROOT / "build"
DESKTOP = Path.home() / "Desktop"
EXE_NAME = "Vpet.exe"


def _ensure_icon() -> Path:
    from PIL import Image

    icon_png = ROOT / "gallery" / "stand.png"
    icon_ico = ROOT / "app_icon.ico"
    if icon_png.exists():
        img = Image.open(icon_png).convert("RGBA")
        img.save(icon_ico, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
    elif not icon_ico.exists():
        img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        from PIL import ImageDraw

        draw = ImageDraw.Draw(img)
        draw.rectangle((48, 40, 208, 216), fill="#4488ff")
        draw.rectangle((88, 72, 168, 112), fill="#ffffff")
        img.save(icon_ico, format="ICO", sizes=[(256, 256), (64, 64), (32, 32)])
    return icon_ico


def _collect_data_args() -> list[str]:
    args: list[str] = []
    sep = ";" if sys.platform == "win32" else ":"
    assets = ROOT / "assets"
    if assets.is_dir():
        args.extend(["--add-data", f"{assets}{sep}assets"])
    for folder in ("gallery", "word_banks"):
        src = ROOT / folder
        if src.is_dir():
            args.extend(["--add-data", f"{src}{sep}{folder}"])
    return args


def _create_shortcut(exe_path: Path) -> None:
    if sys.platform != "win32":
        return
    lnk = DESKTOP / "Vpet 桌宠.lnk"
    ps = f"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut('{lnk}')
$Shortcut.TargetPath = '{exe_path}'
$Shortcut.WorkingDirectory = '{exe_path.parent}'
$Shortcut.Description = 'Vpet 桌宠 - 点击托盘图标生成桌宠'
$Shortcut.Save()
"""
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)


def main() -> None:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("正在安装 PyInstaller …")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "pystray"])

    icon = _ensure_icon()
    if DIST.exists():
        shutil.rmtree(DIST, ignore_errors=True)
    if BUILD.exists():
        shutil.rmtree(BUILD, ignore_errors=True)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        EXE_NAME.removesuffix(".exe"),
        "--icon",
        str(icon),
        *_collect_data_args(),
        "--hidden-import",
        "pystray",
        "--hidden-import",
        "PIL.ImageTk",
        "--hidden-import",
        "pygame",
        "--hidden-import",
        "imageio_ffmpeg",
        str(ROOT / "vpet_app.py"),
    ]
    print("执行打包命令：")
    print(" ".join(f'"{part}"' if " " in part else part for part in cmd))
    subprocess.check_call(cmd, cwd=ROOT)

    exe_path = DIST / EXE_NAME.removesuffix(".exe") / EXE_NAME
    if not exe_path.exists():
        exe_path = DIST / EXE_NAME
    if not exe_path.exists():
        raise SystemExit(f"未找到输出文件：{DIST / EXE_NAME}")

    release_dir = ROOT / "release" / EXE_NAME.removesuffix(".exe")
    if release_dir.exists():
        shutil.rmtree(release_dir, ignore_errors=True)
    shutil.copytree(exe_path.parent, release_dir)
    release_exe = release_dir / EXE_NAME

    data_src = ROOT / "data"
    data_dst = release_dir / "data"
    if data_src.is_dir():
        if data_dst.exists():
            shutil.rmtree(data_dst, ignore_errors=True)
        shutil.copytree(data_src, data_dst)
    else:
        data_dst.mkdir(parents=True, exist_ok=True)

    _create_shortcut(release_exe)
    print(f"\n打包完成：{release_exe}")
    print(f"发布目录：{release_dir}")
    print(f"桌面快捷方式：{DESKTOP / 'Vpet 桌宠.lnk'}")
    print("双击快捷方式 → 托盘出现图标 → 左键点击即可生成桌宠")


if __name__ == "__main__":
    main()
