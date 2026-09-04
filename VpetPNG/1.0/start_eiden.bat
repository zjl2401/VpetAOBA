@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem 以伊得身份启动（可与苍叶双开，靠近涨友情）
set VPET_KIND=eiden
if exist "release\Vpet\Vpet.exe" (
  start "" "%~dp0release\Vpet\Vpet.exe" --kind eiden
) else if exist "pet.py" (
  start "" pythonw "%~dp0pet.py" --kind eiden
) else (
  start "" pythonw "%~dp0vpet_app.py" --kind eiden
)
