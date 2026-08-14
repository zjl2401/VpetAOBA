@echo off
chcp 65001 >nul
setlocal EnableExtensions
set "SAVE=%LOCALAPPDATA%\Vpet"
echo.
echo ========================================
echo   清空 Vpet 本地存档（恢复第一次打开）
echo ========================================
echo.
echo 将处理：
echo   %SAVE%
echo.
echo 会清空：所属人、日记、家园、成就、金币、设置、RPG 等
echo 不会删除：你解压的程序文件夹（Vpet.exe 所在目录）
echo.
echo 请先完全退出桌宠（托盘右键 → 退出启动器，或 Ctrl+Shift+Q）
echo.
set /p CONFIRM=确认清空？输入 YES 后回车： 
if /I not "%CONFIRM%"=="YES" (
  echo 已取消。
  pause
  exit /b 0
)

if not exist "%SAVE%" (
  echo 本地存档本来就不存在，已是第一次打开状态。
  pause
  exit /b 0
)

for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "TS=%%I"
set "BACKUP=%LOCALAPPDATA%\Vpet_backup_%TS%"
echo.
echo 正在改名备份（可恢复）…
echo   原：%SAVE%
echo   备：%BACKUP%
move "%SAVE%" "%BACKUP%" >nul
if exist "%SAVE%" (
  echo.
  echo 失败：文件夹可能被占用。请退出托盘后重试。
  echo 或按 Win+R，粘贴下面路径回车，手动把 Vpet 文件夹改名/删除：
  echo   %%LOCALAPPDATA%%\Vpet
  echo   实际：%SAVE%
  start "" explorer.exe "%LOCALAPPDATA%"
  pause
  exit /b 1
)

echo.
echo 完成。下次启动 Vpet 会像第一次打开一样。
echo 若要找回旧存档：把备份文件夹改回名称为 Vpet
echo   %BACKUP%
echo.
start "" explorer.exe "%LOCALAPPDATA%"
pause
