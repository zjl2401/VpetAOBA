@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PATCH=%~dp0eiden-forcequit-cosmetics.patch
set EIDEN=%USERPROFILE%\Desktop\VpetEidenPet
if not exist "%PATCH%" (
  echo 找不到补丁: %PATCH%
  pause
  exit /b 1
)
if not exist "%EIDEN%\.git" (
  echo 找不到伊得 git 仓库: %EIDEN%
  echo 请先用 GitHub Desktop 打开并 Publish 桌面 VpetEidenPet
  pause
  exit /b 1
)
pushd "%EIDEN%"
git apply --3way "%PATCH%"
if errorlevel 1 (
  echo 自动打补丁失败，请把报错发我；或授权云端推送伊得仓库。
  popd
  pause
  exit /b 1
)
echo 补丁已打上。请打开 GitHub Desktop → VpetEidenPet → Commit → Push
popd
pause
