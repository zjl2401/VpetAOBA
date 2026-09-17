# -*- coding: utf-8 -*-
"""Copy latest Aoba sources onto Desktop\\Vpet and point the shortcut at pythonw launcher."""
from __future__ import annotations

import py_compile
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESKTOP = Path.home() / "Desktop"
DST = DESKTOP / "Vpet"
LNK = DESKTOP / "Vpet Aoba.lnk"
PYTHONW = Path(sys.executable).with_name("pythonw.exe")
if not PYTHONW.is_file():
    PYTHONW = Path(sys.executable)

# 新 pet.py 依赖的同目录模块；旧安装包里往往缺/旧，必须一并同步
SIDE_MODULES = (
    "pet.py",
    "peer_friendship.py",
    "vpet_app.py",
    "vpet_launcher.py",
    "aoba_launch.py",
    "bundled_paths.py",
    "app_scene_desktop.py",
    "desktop_clock.py",
    "home_cottage.py",
    "home_farm.py",
    "pet_outfit.py",
    "rhythm_chart_editor.py",
    "media_bundled.py",
    "pet_id_cloud.py",
    "panel_decor.py",
    "friend_talk_anim.py",
    "friend_crossover.py",
    "voice_audio.py",
    "voice_system.py",
    "system_media_control.py",
)


def _copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print("copied", dst)


def _sync_friend_assets() -> None:
    src = ROOT / "assets" / "friend"
    if not src.is_dir():
        print("skip friend assets (missing)", src)
        return
    for dst in (DST / "assets" / "friend", DST / "_internal" / "assets" / "friend"):
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst, dirs_exist_ok=True)
        print("synced", dst)


def main() -> None:
    for name in ("pet.py", "peer_friendship.py", "aoba_launch.py", "bundled_paths.py", "friend_crossover.py"):
        py_compile.compile(str(ROOT / name), doraise=True)
    if not (DST / "Vpet.exe").is_file():
        raise SystemExit(f"missing {DST / 'Vpet.exe'}")

    for name in SIDE_MODULES:
        src = ROOT / name
        if not src.is_file():
            print("skip missing", name)
            continue
        _copy(src, DST / name)
        _copy(src, DST / "_internal" / name)

    _sync_friend_assets()

    (DST / "KIND.txt").write_text("aoba\n", encoding="utf-8")
    print("wrote", DST / "KIND.txt")

    pyw = str(PYTHONW)
    launch = str(DST / "aoba_launch.py")
    bat = DST / "start_aoba.bat"
    src_posix = str(ROOT).replace("/", "\\")
    copy_lines = [
        "@echo off",
        "chcp 65001 >nul",
        'cd /d "%~dp0"',
        f'set "SRC={src_posix}"',
        'set "VPET_AOBA_SRC=%SRC%"',
        'set "VPET_KIND=aoba"',
    ]
    for name in SIDE_MODULES:
        copy_lines.append(
            f'if exist "%SRC%\\{name}" copy /Y "%SRC%\\{name}" "%~dp0_internal\\{name}" >nul'
        )
        copy_lines.append(
            f'if exist "%SRC%\\{name}" copy /Y "%SRC%\\{name}" "%~dp0{name}" >nul'
        )
    copy_lines.extend(
        [
            'if exist "%SRC%\\assets\\friend" (',
            '  if not exist "%~dp0assets\\friend" mkdir "%~dp0assets\\friend" >nul',
            '  if not exist "%~dp0_internal\\assets\\friend" mkdir "%~dp0_internal\\assets\\friend" >nul',
            '  xcopy /E /Y /Q "%SRC%\\assets\\friend\\*" "%~dp0assets\\friend\\" >nul',
            '  xcopy /E /Y /Q "%SRC%\\assets\\friend\\*" "%~dp0_internal\\assets\\friend\\" >nul',
            ")",
            f'start "" "{pyw}" "%~dp0aoba_launch.py"',
            "",
        ]
    )
    bat.write_text("\r\n".join(copy_lines), encoding="utf-8")
    print("wrote", bat)

    ico = DST / "app_icon.ico"
    icon_loc = f"{ico},0" if ico.is_file() else f"{DST / 'Vpet.exe'},0"
    # 快捷方式走 bat：可先同步源码再启动，也避免 pythonw 参数引号问题
    ps = f"""
$wsh = New-Object -ComObject WScript.Shell
$lnk = $wsh.CreateShortcut('{str(LNK).replace(chr(39), chr(39)+chr(39))}')
$lnk.TargetPath = '{str(bat).replace(chr(39), chr(39)+chr(39))}'
$lnk.Arguments = ''
$lnk.WorkingDirectory = '{str(DST).replace(chr(39), chr(39)+chr(39))}'
$lnk.IconLocation = '{icon_loc.replace(chr(39), chr(39)+chr(39))}'
$lnk.WindowStyle = 7
$lnk.Description = 'Aoba - start_aoba.bat loads disk pet.py'
$lnk.Save()
Write-Output ('OK ' + $lnk.TargetPath + ' ' + $lnk.Arguments)
"""
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
        check=True,
    )

    kill = r"""
Get-CimInstance Win32_Process | ForEach-Object {
  $cl = [string]$_.CommandLine
  if (-not $cl) { return }
  $ok = ($cl -match 'aoba_launch\.py') -or ($cl -match '--kind aoba') -or ($cl -match '\\Desktop\\Vpet\\Vpet\.exe')
  if ($ok -and $_.Name -match 'Vpet|pythonw|python') {
    Write-Output ('stop ' + $_.ProcessId + ' ' + $cl)
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
  }
}
"""
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", kill],
        check=False,
    )
    print("deployed")
    _ = launch


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("FAIL", exc, file=sys.stderr)
        raise SystemExit(1) from exc
