#!/usr/bin/env python3
"""打包 Vpet 为 Windows 桌面程序。默认不写桌面快捷方式（加 --shortcut 才写）。
加 --zip / --clean-zip 时额外打出桌面干净电脑版 Vpet_update_时间戳.zip。
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
BUILD = ROOT / "build"
DESKTOP = Path.home() / "Desktop"
EXE_NAME = "Vpet.exe"
BUNDLED_SRC = ROOT / "bundled"
LEGACY_VOICE_SRC = DESKTOP / "Vpetvoice"
LEGACY_MUSIC_SRC = DESKTOP / "Vpetmusic"
LEGACY_GAME_SRC = DESKTOP / "Vpetgame"


def _ensure_icon() -> Path:
    """用 stand 立绘生成图标：居中裁剪/等比缩放，禁止非等比拉伸。"""
    try:
        from make_app_icons import main as _make_icons

        _make_icons()
    except Exception as exc:
        print(f"警告：make_app_icons 失败（{exc}），尝试沿用已有 ico")
    icon_ico = ROOT / "app_icon.ico"
    icon_png = ROOT / "app_icon.png"
    if icon_ico.exists():
        return icon_ico
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
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
        try:
            shutil.rmtree(dst)
        except OSError as exc:
            print(f"警告：无法直接清空 {dst}（{exc}），尝试强制清理…")
            shutil.rmtree(dst, ignore_errors=True)
            if dst.exists():
                # 仍占用：改名旁路，避免整包失败
                bak = dst.with_name(f"Vpetgame_old_{datetime.now().strftime('%H%M%S')}")
                try:
                    dst.rename(bak)
                    print(f"  已将旧目录改名为 {bak.name}")
                except OSError as exc2:
                    print(f"警告：跳过 Vpetgame 同步（目录被占用：{exc2}）")
                    return
    dst.mkdir(parents=True, exist_ok=True)
    game_py = src / "game.py"
    if game_py.is_file():
        shutil.copy2(game_py, dst / "game.py")
    for name in ("assets", "maps"):
        folder = src / name
        if folder.is_dir():
            target = dst / name
            if target.exists():
                shutil.rmtree(target, ignore_errors=True)
            try:
                shutil.copytree(folder, target)
            except OSError as exc:
                print(f"警告：复制 {name} 失败（{exc}）")
    for name in ("README.md", "requirements.txt", "process_assets.py"):
        file = src / name
        if file.is_file():
            try:
                shutil.copy2(file, dst / name)
            except OSError:
                pass
    # 可选：桌面有 music 时再拷（失败不阻断）
    for media_name in ("music.mp4", "music.mp3", "bgm.mp3"):
        media = src / media_name
        if media.is_file():
            try:
                shutil.copy2(media, dst / media_name)
            except OSError as exc:
                print(f"警告：跳过 {media_name}（{exc}）")
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


def _scrub_release_data(data_dst: Path) -> None:
    """公开包不附带个人存档与可再生缓存，仅保留可分发的默认资源。"""
    if not data_dst.is_dir():
        return
    drop_names = {
        "pet_profile.json",
        "diary.json",
        "schedules.json",
        "food_inventory.json",
        "leaderboard.json",
        "vocab_notebook.json",
        "pet_id_registry.json",
        "ai_config.json",
        "app_config.json",
        "music_config.json",
        "weather_cache.json",
        "achievements.json",
    }
    for name in drop_names:
        path = data_dst / name
        if path.is_file():
            try:
                path.unlink()
                print(f"发行清理：data/{name}")
            except OSError:
                pass
    audio = data_dst / "audio"
    if audio.is_dir():
        for path in audio.rglob("*"):
            if not path.is_file():
                continue
            n = path.name.lower()
            keep = n == "type_cache.wav"
            if keep:
                continue
            if (
                n.endswith("_cache.wav")
                or n.startswith("music_")
                or "voice_cache" in path.parts
                or n.startswith("rhythm_chart_")
            ):
                try:
                    path.unlink()
                    print(f"发行清理：{path.relative_to(data_dst)}")
                except OSError:
                    pass
        voice_cache = audio / "voice_cache"
        if voice_cache.is_dir():
            shutil.rmtree(voice_cache, ignore_errors=True)
            print("发行清理：data/audio/voice_cache/")


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
    _scrub_release_data(data_dst)

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
    lnk = DESKTOP / "Vpet Aoba.lnk"
    # 优先 exe 同目录 app_icon.ico（随安装包），勿指向桌面散落文件
    beside = exe_path.parent / "app_icon.ico"
    if icon_path and icon_path.exists():
        try:
            shutil.copy2(icon_path, beside)
        except OSError:
            pass
    elif (ROOT / "app_icon.ico").exists():
        try:
            shutil.copy2(ROOT / "app_icon.ico", beside)
        except OSError:
            pass
    if beside.exists():
        icon = beside
        icon_line = f"$Shortcut.IconLocation = '{icon},0'\n"
    elif exe_path.exists():
        icon_line = f"$Shortcut.IconLocation = '{exe_path},0'\n"
    else:
        icon_line = ""
    ps = f"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut('{lnk}')
$Shortcut.TargetPath = '{exe_path}'
$Shortcut.WorkingDirectory = '{exe_path.parent}'
$Shortcut.Description = 'Vpet Aoba'
{icon_line}$Shortcut.Save()
"""
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)

    # 去掉旧名快捷方式，避免桌面残留两个
    for legacy_name in ("Vpet.lnk", "VpetAoba.lnk"):
        legacy = DESKTOP / legacy_name
        if legacy.exists() and legacy.resolve() != lnk.resolve():
            try:
                legacy.unlink()
            except OSError:
                pass

    release_bat = exe_path.parent.parent / "启动桌宠.bat"
    release_bat.write_text(
        "@echo off\nchcp 65001 >nul\n"
        f'start "" "{exe_path}"\n',
        encoding="utf-8",
    )
    local_bat = exe_path.parent / "启动.bat"
    local_bat.write_text(
        "@echo off\nchcp 65001 >nul\n"
        'cd /d "%~dp0"\n'
        'start "" "%~dp0Vpet.exe"\n',
        encoding="utf-8",
    )


def _copy_release_to_desktop(release_dir: Path) -> Path:
    """把完整发布包（含 bundled 素材）拷到桌面 Vpet，方便用户找到。"""
    desktop_dst = DESKTOP / "Vpet"
    print(f"拷贝完整包到桌面：{release_dir} → {desktop_dst}")
    try:
        _deploy_tree(release_dir, desktop_dst)
    except OSError as exc:
        # 桌面旧包被占用时改放到带时间戳的新文件夹
        alt = DESKTOP / f"Vpet_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"警告：无法覆盖桌面 Vpet（{exc}），改为 {alt.name}")
        shutil.copytree(release_dir, alt)
        desktop_dst = alt
    bat = desktop_dst / "启动.bat"
    bat.write_text(
        "@echo off\nchcp 65001 >nul\n"
        'cd /d "%~dp0"\n'
        'start "" "%~dp0Vpet.exe"\n',
        encoding="utf-8",
    )
    readme = desktop_dst / "请从这里打开.txt"
    readme.write_text(
        "Vpet 完整包已放在本文件夹。\n\n"
        "打开方式：\n"
        "1. 双击「启动.bat」或 Vpet.exe\n"
        "2. 托盘出现图标后，左键点击即可生成桌宠\n\n"
        "语音 / 音乐 / RPG 等素材在 bundled 子目录中。\n",
        encoding="utf-8",
    )
    return desktop_dst


def _zip_clean_pc_release(release_dir: Path) -> Path:
    """干净电脑版压缩包：无个人存档（发布时已 scrub），zip 到桌面。"""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = DESKTOP / f"Vpet_update_{stamp}.zip"
    if zip_path.exists():
        zip_path.unlink()
    skip_names = {".DS_Store", "Thumbs.db", "desktop.ini"}
    skip_parts = {"__pycache__", ".git"}
    print(f"打包干净电脑版 zip：{zip_path}")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for path in sorted(release_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.name in skip_names:
                continue
            if any(part in skip_parts for part in path.parts):
                continue
            arc = Path("Vpet") / path.relative_to(release_dir)
            zf.write(path, arc.as_posix())
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"干净包大小：{size_mb:.1f} MB")
    return zip_path


def main() -> None:
    args = set(sys.argv[1:])
    deploy_only = bool(args & {"--deploy-only", "--publish-only"})
    make_shortcut = "--shortcut" in args or "--with-shortcut" in args
    make_zip = "--zip" in args or "--clean-zip" in args

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

        # 使用现有 Vpet.spec，避免 PyInstaller 重写 .spec 时 Errno 22
        spec = ROOT / "Vpet.spec"
        if not spec.is_file():
            raise SystemExit(f"缺少打包配置：{spec}")
        cmd = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            str(spec),
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

    # 完整包（含 bundled 素材）拷到桌面，方便用户找到
    desktop_dir: Path | None
    try:
        desktop_dir = _copy_release_to_desktop(release_dir)
        desktop_exe = desktop_dir / EXE_NAME
    except Exception as exc:
        print(f"警告：拷贝到桌面失败（{exc}），仍保留 release 目录")
        desktop_dir = None
        desktop_exe = release_exe

    shortcut_exe = desktop_exe if desktop_dir and desktop_exe.exists() else release_exe
    _create_shortcut(shortcut_exe, icon if icon.exists() else None)
    local_bat = release_dir / "启动.bat"
    local_bat.write_text(
        "@echo off\nchcp 65001 >nul\n"
        'cd /d "%~dp0"\n'
        'start "" "%~dp0Vpet.exe"\n',
        encoding="utf-8",
    )
    release_bat = release_dir.parent / "启动桌宠.bat"
    release_bat.write_text(
        "@echo off\nchcp 65001 >nul\n"
        f'start "" "{shortcut_exe}"\n',
        encoding="utf-8",
    )
    print(f"\n打包完成：{release_exe}")
    print(f"发布目录：{release_dir}")
    if desktop_dir is not None:
        print(f"桌面完整包：{desktop_dir}")
    if make_zip:
        try:
            zip_path = _zip_clean_pc_release(release_dir)
            print(f"干净电脑版压缩包：{zip_path}")
        except Exception as exc:
            print(f"警告：打 zip 失败（{exc}）")
    print(f"构建版本：{stamp}")
    print(f"桌面快捷方式：{DESKTOP / 'Vpet Aoba.lnk'}")
    print("请打开桌面「Vpet Aoba」或发布目录，双击 启动.bat 或 Vpet.exe")
    print("若更新后改动未生效：请先托盘右键「退出启动器」，再重新打开。")


if __name__ == "__main__":
    main()
