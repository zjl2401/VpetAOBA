@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem 兼容旧快捷方式：优先 pet.py（伊得）；苍叶请用「苍叶桌宠」
set VPET_KIND=eiden
if exist "pet.py" (
  start "" pythonw "%~dp0pet.py" --kind eiden
) else (
  call "%~dp0start_eiden.bat"
)
