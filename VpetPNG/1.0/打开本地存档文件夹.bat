@echo off
chcp 65001 >nul
set "SAVE=%LOCALAPPDATA%\Vpet"
echo.
echo ========================================
echo   Vpet 本地存档位置
echo ========================================
echo.
echo 路径：
echo   %SAVE%
echo.
echo （所属人、日记、家园、成就、金币、RPG 等都在这里）
echo  不是解压出来的程序文件夹！
echo.
if not exist "%SAVE%" (
  echo 目前还没有本地存档文件夹（等于已经是第一次打开状态）。
  echo.
  pause
  exit /b 0
)
echo 正在打开该文件夹…
start "" explorer.exe "%SAVE%"
echo.
echo 若要「第一次打开」效果：
echo   1. 先退出桌宠托盘（右键托盘图标 → 退出启动器）
echo   2. 回到这个窗口，可改运行「清空本地存档.bat」
echo   3. 或在已打开的文件夹里，把整个 Vpet 文件夹删掉/改名
echo.
pause
