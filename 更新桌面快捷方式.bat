@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist "VpetPNG\1.0\更新桌面快捷方式.bat" (
  call "VpetPNG\1.0\更新桌面快捷方式.bat"
) else if exist "1.0\更新桌面快捷方式.bat" (
  call "1.0\更新桌面快捷方式.bat"
) else (
  echo 找不到 VpetPNG\1.0\更新桌面快捷方式.bat
  echo 请先 git pull 到分支 cursor/auto-restore-companion-c4c2
  pause
)
