@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem 以苍叶身份直接开一只桌宠（--pet：不经启动器单实例，不关已有宠）
set VPET_KIND=aoba
if exist "pet.py" (
  start "" pythonw "%~dp0pet.py" --kind aoba
) else if exist "release\Vpet\Vpet.exe" (
  start "" "%~dp0release\Vpet\Vpet.exe" --pet --kind aoba
) else (
  start "" pythonw "%~dp0vpet_app.py" --pet --kind aoba
)
