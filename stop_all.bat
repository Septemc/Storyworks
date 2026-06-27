@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   Stop Storyworks Unified
echo ========================================
echo.

for %%P in (3000 8000) do (
    echo Checking port %%P...
    for /f "tokens=5" %%A in ('netstat -ano ^| findstr ":%%P " ^| findstr "LISTENING"') do (
        echo Stopping PID %%A on port %%P
        taskkill /F /PID %%A >nul 2>&1
    )
)

echo.
echo Done.
echo.
pause
