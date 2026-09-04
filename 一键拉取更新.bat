@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   Vpet 一键拉取友情双宠分支
echo ========================================
echo 当前目录: %CD%
echo.

where git >nul 2>nul
if errorlevel 1 (
  echo [错误] 没找到 git。请改用浏览器下载 ZIP：
  echo https://github.com/zjl2401/VpetAOBA/archive/refs/heads/cursor/auto-restore-companion-c4c2.zip
  echo 解压后覆盖到本目录，再双击「实现双宠更新.bat」
  echo.
  pause
  exit /b 1
)

echo [1/3] git fetch origin ...
git fetch origin
if errorlevel 1 (
  echo fetch 失败，请检查网络或是否已 git clone 本仓库。
  pause
  exit /b 1
)

echo [2/3] git checkout cursor/auto-restore-companion-c4c2 ...
git checkout cursor/auto-restore-companion-c4c2
if errorlevel 1 (
  echo checkout 失败，尝试创建本地跟踪分支...
  git checkout -B cursor/auto-restore-companion-c4c2 origin/cursor/auto-restore-companion-c4c2
  if errorlevel 1 (
    echo 仍失败。可用 ZIP 下载覆盖：见上方链接。
    pause
    exit /b 1
  )
)

echo [3/3] git pull origin cursor/auto-restore-companion-c4c2 ...
git pull origin cursor/auto-restore-companion-c4c2
if errorlevel 1 (
  echo pull 失败。
  pause
  exit /b 1
)

echo.
echo 拉取完成。
echo.
if exist "实现双宠更新.bat" (
  echo 接着同步到桌面 VpetAOBA / VpetEidenPet ...
  call "%~dp0实现双宠更新.bat"
) else if exist "VpetPNG\1.0\实现双宠更新.bat" (
  call "%~dp0VpetPNG\1.0\实现双宠更新.bat"
) else (
  echo 请再双击「实现双宠更新.bat」完成同步。
  pause
)
