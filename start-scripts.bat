@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Storyworks now uses the unified workspace.
echo Launching unified app instead of the legacy Scripts module...

call "%~dp0start.bat"
