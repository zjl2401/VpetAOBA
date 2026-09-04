@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem 兼容旧快捷方式：默认启动伊得；苍叶请用桌面「苍叶桌宠」或 start_aoba.bat
call "%~dp0start_eiden.bat"
