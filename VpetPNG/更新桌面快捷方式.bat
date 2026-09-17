@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在更新桌面快捷方式（苍叶 / 伊得）...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0update_desktop_shortcuts.ps1"
if errorlevel 1 (
  echo.
  echo 更新失败。可手动把 start_aoba.bat / start_eiden.bat 发送到桌面。
  pause
  exit /b 1
)
echo.
pause
