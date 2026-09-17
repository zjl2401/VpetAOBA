# -*- coding: utf-8 -*-
"""Refresh Desktop Vpet Aoba.lnk -> Desktop\\Vpet\\Vpet.exe --pet --kind aoba"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release" / "Vpet"
DESKTOP = Path.home() / "Desktop"
DESK_VPET = DESKTOP / "Vpet"
LNK = DESKTOP / "Vpet Aoba.lnk"


def main() -> None:
    DESK_VPET.mkdir(parents=True, exist_ok=True)
    src = RELEASE if (RELEASE / "Vpet.exe").is_file() else None
    if src is None:
        # fallback: keep existing Desktop\\Vpet if present
        print("no release\\Vpet\\Vpet.exe; will still rewrite shortcut if Desktop\\Vpet\\Vpet.exe exists")
    else:
        # sync without wiping userdata: copy exe + key py modules if present in release
        for name in ("Vpet.exe", "app_icon.ico", "qidong.bat", "start_aoba.bat"):
            s = src / name
            if s.is_file():
                shutil.copy2(s, DESK_VPET / name)
                print("copied", name)
        # also sync _internal / bundled if folders exist (robocopy via subprocess)
        for folder in ("_internal", "bundled"):
            sdir = src / folder
            ddir = DESK_VPET / folder
            if sdir.is_dir():
                subprocess.run(
                    ["robocopy", str(sdir), str(ddir), "/E", "/NFL", "/NDL", "/NJH", "/NJS", "/nc", "/ns", "/np"],
                    check=False,
                )
                print("synced", folder)

    exe = DESK_VPET / "Vpet.exe"
    if not exe.is_file():
        exe = RELEASE / "Vpet.exe"
    if not exe.is_file():
        raise SystemExit("missing Vpet.exe")

    ico = DESK_VPET / "app_icon.ico"
    if not ico.is_file():
        ico = ROOT / "app_icon.ico"
    icon_loc = f"{ico},0" if ico.is_file() else f"{exe},0"

    ps = f"""
$wsh = New-Object -ComObject WScript.Shell
$lnk = $wsh.CreateShortcut('{str(LNK).replace("'", "''")}')
$lnk.TargetPath = '{str(exe).replace("'", "''")}'
$lnk.Arguments = '--pet --kind aoba'
$lnk.WorkingDirectory = '{str(exe.parent).replace("'", "''")}'
$lnk.IconLocation = '{icon_loc.replace("'", "''")}'
$lnk.Description = '苍叶 · Ctrl+Shift+V 开菜单'
$lnk.Save()
Write-Host ('OK ' + $lnk.TargetPath + ' ' + $lnk.Arguments)
"""
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], check=True)
    print("shortcut", LNK)


if __name__ == "__main__":
    main()
