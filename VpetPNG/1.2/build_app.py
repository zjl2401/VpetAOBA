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


_RELEASE_LOCK_HINT = (
    "release/Vpet 仍被旧程序占用：已把完整新版放到 release/Vpet_new，"
    "桌面快捷方式会指向该目录。退出托盘后可删除旧的 release/Vpet。"
)


def _try_clear_dir(target: Path) -> bool:
    if not target.exists():
        return True
    try:
        shutil.rmtree(target)
        return True
    except OSError:
        pass
    backup = target.with_name(f"{target.name}_old")
    if backup.exists():
        shutil.rmtree(backup, ignore_errors=True)
    try:
        target.rename(backup)
        return True
    except OSError:
        return False


def _deploy_tree(src_dir: Path, dst_dir: Path) -> None:
    if not _try_clear_dir(dst_dir):
        raise OSError(f"无法清空目录：{dst_dir}")
    shutil.copytree(src_dir, dst_dir)


def _publish_release(build_dir: Path, data_src: Path) -> tuple[Path, Path]:
    release_root = ROOT / "release"
    release_root.mkdir(parents=True, exist_ok=True)
    app_name = EXE_NAME.removesuffix(".exe")
    primary = release_root / app_name
    staging = release_root / f"{app_name}_new"

    _deploy_tree(build_dir, staging)
    data_dst = staging / "data"
    if data_src.is_dir():
        _deploy_tree(data_src, data_dst)
    else:
        data_dst.mkdir(parents=True, exist_ok=True)

    if _try_clear_dir(primary):
        try:
            staging.rename(primary)
            return primary, primary / EXE_NAME
        except OSError:
            pass

    print(_RELEASE_LOCK_HINT)
    return staging, staging / EXE_NAME


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

    bat = DESKTOP / "启动 Vpet 桌宠.bat"
    bat.write_text(f'@echo off\nchcp 65001 >nul\nstart "" "{exe_path}"\n', encoding="utf-8")
    release_bat = exe_path.parent.parent / "启动桌宠.bat"
    release_bat.write_text(
        "@echo off\nchcp 65001 >nul\n"
        f'start "" "{exe_path}"\n',
        encoding="utf-8",
    )


def main() -> None:
    deploy_only = len(sys.argv) > 1 and sys.argv[1] in ("--deploy-only", "--publish-only")

    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("正在安装 PyInstaller …")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "pystray"])

    if not deploy_only:
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
    else:
        print("跳过 PyInstaller，仅发布 dist 到 release …")

    exe_path = DIST / EXE_NAME.removesuffix(".exe") / EXE_NAME
    if not exe_path.exists():
        exe_path = DIST / EXE_NAME
    if not exe_path.exists():
        raise SystemExit(f"未找到输出文件：{DIST / EXE_NAME}")

    release_dir, release_exe = _publish_release(exe_path.parent, ROOT / "data")

    _create_shortcut(release_exe)
    print(f"\n打包完成：{release_exe}")
    print(f"发布目录：{release_dir}")
    print(f"桌面快捷方式：{DESKTOP / 'Vpet 桌宠.lnk'}")
    print("双击快捷方式 → 托盘出现图标 → 左键点击即可生成桌宠")


if __name__ == "__main__":
    main()
