@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Storyworks now uses the unified workspace.
echo Launching unified app instead of the legacy Project Manager module...

call "%~dp0start.bat"
