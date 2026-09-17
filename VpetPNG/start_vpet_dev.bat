@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem 默认伊得；苍叶请用 start_aoba.bat
rem 优先 pet.py，避免旧 release\Vpet.exe 挡住源码更新
set VPET_KIND=eiden
if exist "pet.py" (
  start "" pythonw "%~dp0pet.py" --kind eiden
) else if exist "release\Vpet\Vpet.exe" (
  start "" "%~dp0release\Vpet\Vpet.exe" --kind eiden
) else (
  start "" pythonw "%~dp0vpet_app.py" --kind eiden
)
