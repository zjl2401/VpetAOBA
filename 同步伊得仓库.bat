@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo   同步双宠代码 → 桌面伊得目录
echo   然后请用 GitHub Desktop 推到 VpetEidenPet
echo ========================================
echo.
if not exist "%~dp0同步到伊得仓库-GitHubDesktop步骤.txt" (
  echo 缺少说明文件。
  pause
  exit /b 1
)
echo 详细步骤见：同步到伊得仓库-GitHubDesktop步骤.txt
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0VpetPNG\1.0\sync_desktop_dual_pets.ps1"
if errorlevel 1 (
  echo 同步失败。
  pause
  exit /b 1
)
echo.
echo 下一步：打开 GitHub Desktop → 仓库 VpetEidenPet → Commit → Push origin
echo 若还没有该远程仓库，请先按说明文件「一」创建。
echo.
start "" notepad "%~dp0同步到伊得仓库-GitHubDesktop步骤.txt"
pause
