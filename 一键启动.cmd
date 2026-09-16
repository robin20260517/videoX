@echo off
chcp 65001 >nul
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-studio.ps1"
if errorlevel 1 (
    if not defined STUDIO_NO_PAUSE pause
    exit /b 1
)
