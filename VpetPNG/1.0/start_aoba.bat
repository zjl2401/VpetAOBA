@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem 以苍叶身份启动（可与伊得双开，靠近涨友情）
set VPET_KIND=aoba
if exist "release\Vpet\Vpet.exe" (
  start "" "%~dp0release\Vpet\Vpet.exe" --kind aoba
) else if exist "pet.py" (
  start "" pythonw "%~dp0pet.py" --kind aoba
) else (
  start "" pythonw "%~dp0vpet_app.py" --kind aoba
)
