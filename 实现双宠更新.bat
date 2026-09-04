@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在把友情双宠代码同步到桌面 VpetAOBA / VpetEidenPet ...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0VpetPNG\1.0\sync_desktop_dual_pets.ps1"
if errorlevel 1 (
  echo 同步失败。
  pause
  exit /b 1
)
echo.
pause
