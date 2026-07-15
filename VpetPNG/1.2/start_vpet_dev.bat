@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist "release\Vpet\Vpet.exe" (
  start "" "%~dp0release\Vpet\Vpet.exe"
) else (
  start "" pythonw "%~dp0vpet_app.py"
)
