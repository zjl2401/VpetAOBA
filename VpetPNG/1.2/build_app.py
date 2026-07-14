#!/usr/bin/env python3
"""打包 Vpet 为 Windows 桌面程序，并创建桌面快捷方式。"""

from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
BUILD = ROOT / "build"
DESKTOP = Path.home() / "Desktop"
EXE_NAME = "Vpet.exe"
BUNDLED_SRC = ROOT / "bundled"
LEGACY_VOICE_SRC = Path(r"C:\Users\36255\Desktop\Vpetvoice")
LEGACY_MUSIC_SRC = Path(r"C:\Users\36255\Desktop\Vpetmusic")
LEGACY_GAME_SRC = Path(r"C:\Users\36255\Desktop\Vpetgame")


def _ensure_icon() -> Path:
    from PIL import Image

    icon_ico = ROOT / "app_icon.ico"
    icon_png = ROOT / "app_icon.png"
    # 优先使用 app_icon1（用户指定的新图标）
    sources = (
        ROOT / "app_icon1.jpg",
        ROOT / "app_icon1.png",
        ROOT / "app_icon1.ico",
        ROOT / "gallery" / "stand.png",
    )
    src = next((p for p in sources if p.exists()), None)
    if src is not None:
        img = Image.open(src).convert("RGBA")
        # 居中裁成正方形再缩放，避免 JPG 比例拉伸变形
        w, h = img.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        img = img.crop((left, top, left + side, top + side))
        img_png = img.resize((256, 256), Image.Resampling.LANCZOS)
        img_png.save(icon_png, format="PNG")
        img_png.save(
            icon_ico,
            format="ICO",
            sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)],
        )
    elif not icon_ico.exists():
        img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        from PIL import ImageDraw

        draw = ImageDraw.Draw(img)
        draw.rectangle((48, 40, 208, 216), fill="#4488ff")
        draw.rectangle((88, 72, 168, 112), fill="#ffffff")
        img.save(icon_png, format="PNG")
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
    for name in ("app_icon.png", "app_icon1.jpg", "app_icon1.png", "border1.jpg", "border5.jpg"):
        src = ROOT / name
        if src.is_file():
            args.extend(["--add-data", f"{src}{sep}."])
    type_cache = ROOT / "data" / "audio" / "type_cache.wav"
    if type_cache.is_file():
        args.extend(["--add-data", f"{type_cache}{sep}data/audio"])
    return args



def _sync_vpetgame() -> None:
    """打包前：桌面 Vpetgame → bundled/Vpetgame（game.py + assets + maps）。"""
    src = LEGACY_GAME_SRC
    dst = BUNDLED_SRC / "Vpetgame"
    if not src.is_dir():
        print(f"警告：未找到 {src}，无法同步 bundled/Vpetgame")
        return
    print(f"同步 RPG {src} → {dst} …")
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    game_py = src / "game.py"
    if game_py.is_file():
        shutil.copy2(game_py, dst / "game.py")
    for name in ("assets", "maps"):
        folder = src / name
        if folder.is_dir():
            shutil.copytree(folder, dst / name)
    for name in ("README.md", "requirements.txt", "process_assets.py"):
        file = src / name
        if file.is_file():
            shutil.copy2(file, dst / name)
    has_game = (dst / "game.py").is_file()
    asset_n = sum(1 for _ in (dst / "assets").rglob("*") if _.is_file()) if (dst / "assets").is_dir() else 0
    map_n = sum(1 for _ in (dst / "maps").rglob("*") if _.is_file()) if (dst / "maps").is_dir() else 0
    print(f"  bundled/Vpetgame: game.py={'有' if has_game else '无'}，assets {asset_n}，maps {map_n}")


def _sync_bundled_media(*, force: bool = True) -> None:
    """打包前：桌面 Vpetvoice/Vpetmusic → bundled/（仅音频，视频容器转为 wav）；同步 Vpetgame。"""
    from media_bundled import count_media_files, sync_bundled_audio_only

    BUNDLED_SRC.mkdir(parents=True, exist_ok=True)
    for name, src in (("Vpetvoice", LEGACY_VOICE_SRC), ("Vpetmusic", LEGACY_MUSIC_SRC)):
        dst = BUNDLED_SRC / name
        if not src.is_dir():
            print(f"警告：未找到 {src}，无法同步 bundled/{name}")
            continue
        print(f"同步音频 {src} → {dst} …")
        copied, converted, removed = sync_bundled_audio_only(src, dst, force=force)
        audio_n, video_n = count_media_files(dst)
        print(f"  bundled/{name}: 复制 {copied}，转换 {converted}，剔除视频 {removed}；现有音频 {audio_n}，残留视频 {video_n}")
    _sync_vpetgame()


def _clean_workspace() -> None:
    """清理可再生的构建产物与重复发布目录。"""
    for rel in ("build", "dist"):
        path = ROOT / rel
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
            print(f"已清理 {rel}/")
    release = ROOT / "release"
    for name in ("Vpet_old", "Vpet_new"):
        path = release / name
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
            print(f"已清理 release/{name}/")
    # 过期节奏谱缓存
    audio_dir = ROOT / "data" / "audio"
    if audio_dir.is_dir():
        for pattern in ("rhythm_chart_*_v3.json", "rhythm_chart_*_v4.json", "rhythm_chart_aicatch_*"):
            for path in audio_dir.glob(pattern):
                try:
                    path.unlink()
                    print(f"已删除过期缓存 {path.name}")
                except OSError:
                    pass


def _publish_bundled_media(staging: Path) -> None:
    from media_bundled import count_media_files, prune_video_files

    if not BUNDLED_SRC.is_dir():
        return
    dst = staging / "bundled"
    print(f"发布 bundled 资源：{BUNDLED_SRC} → {dst}")
    _deploy_tree(BUNDLED_SRC, dst)
    removed = prune_video_files(dst)
    if removed:
        print(f"  发布包剔除残留视频 {removed} 个")
    for name in ("Vpetvoice", "Vpetmusic"):
        sub = dst / name
        audio_n, video_n = count_media_files(sub)
        print(f"  发布 bundled/{name}: 音频 {audio_n}，视频 {video_n}")
    game = dst / "Vpetgame"
    if game.is_dir():
        print(f"  发布 bundled/Vpetgame: game.py={'有' if (game / 'game.py').is_file() else '无'}")


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


def _publish_release(build_dir: Path, data_src: Path) -> tuple[Path, Path, str]:
    release_root = ROOT / "release"
    release_root.mkdir(parents=True, exist_ok=True)
    app_name = EXE_NAME.removesuffix(".exe")
    primary = release_root / app_name
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stamp_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    staging_candidates = (
        release_root / f"{app_name}_new",
        release_root / f"{app_name}_build_{stamp_tag}",
    )

    staging: Path | None = None
    for candidate in staging_candidates:
        if _try_clear_dir(candidate):
            staging = candidate
            break
    if staging is None:
        raise OSError(f"无法创建发布暂存目录：{staging_candidates[-1]}")

    _deploy_tree(build_dir, staging)
    data_dst = staging / "data"
    if data_src.is_dir():
        _deploy_tree(data_src, data_dst)
    else:
        data_dst.mkdir(parents=True, exist_ok=True)

    (staging / "BUILD_STAMP.txt").write_text(stamp, encoding="utf-8")
    _publish_bundled_media(staging)

    if _try_clear_dir(primary):
        try:
            staging.rename(primary)
            return primary, primary / EXE_NAME, stamp
        except OSError:
            pass

    print(_RELEASE_LOCK_HINT)
    return staging, staging / EXE_NAME, stamp


def _prune_old_builds(*, keep: int = 2) -> None:
    """只保留最近若干份 Vpet_build_*，避免 release 堆积上百 GB。"""
    release_root = ROOT / "release"
    if not release_root.is_dir() or keep < 1:
        return
    builds = sorted(
        (p for p in release_root.glob("Vpet_build_*") if p.is_dir()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for old in builds[keep:]:
        print(f"清理旧包：{old.name}")
        shutil.rmtree(old, ignore_errors=True)
    for name in ("Vpet_old", "Vpet_new_old"):
        path = release_root / name
        if path.is_dir():
            print(f"清理残留：{name}")
            shutil.rmtree(path, ignore_errors=True)


def _create_shortcut(exe_path: Path, icon_path: Path | None = None) -> None:
    if sys.platform != "win32":
        return
    lnk = DESKTOP / "Vpet 桌宠.lnk"
    icon = icon_path if icon_path and icon_path.exists() else (ROOT / "app_icon.ico")
    icon_line = f"$Shortcut.IconLocation = '{icon},0'\n" if icon.exists() else ""
    ps = f"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut('{lnk}')
$Shortcut.TargetPath = '{exe_path}'
$Shortcut.WorkingDirectory = '{exe_path.parent}'
$Shortcut.Description = 'Vpet 桌宠 - 点击托盘图标生成桌宠'
{icon_line}$Shortcut.Save()
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

    _sync_bundled_media()
    _clean_workspace()

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
            "--hidden-import",
            "panel_decor",
            "--hidden-import",
            "voice_audio",
            "--hidden-import",
            "voice_system",
            "--hidden-import",
            "bundled_paths",
            "--hidden-import",
            "media_bundled",
            "--hidden-import",
            "pet_id_cloud",
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

    release_dir, release_exe, stamp = _publish_release(exe_path.parent, ROOT / "data")
    _prune_old_builds(keep=2)

    icon = ROOT / "app_icon.ico"
    if icon.exists():
        try:
            shutil.copy2(icon, release_dir / "app_icon.ico")
        except OSError:
            pass
    _create_shortcut(release_exe, icon if icon.exists() else None)
    print(f"\n打包完成：{release_exe}")
    print(f"发布目录：{release_dir}")
    print(f"构建版本：{stamp}")
    print(f"桌面快捷方式：{DESKTOP / 'Vpet 桌宠.lnk'}")
    print("双击快捷方式 → 托盘出现图标 → 左键点击即可生成桌宠")
    print("若更新后改动未生效：请先托盘右键「退出启动器」，再重新打开快捷方式。")


if __name__ == "__main__":
    main()
