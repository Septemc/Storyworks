@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo.
echo ========================================
echo   Storyworks Unified Launcher
echo ========================================
echo.
echo start_all.bat now delegates to the unified workspace launcher.
echo.

call "%~dp0start.bat"
