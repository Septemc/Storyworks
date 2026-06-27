@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "BACKEND_HOST=127.0.0.1"
if "%BACKEND_PORT%"=="" set "BACKEND_PORT=8000"
if "%FRONTEND_PORT%"=="" set "FRONTEND_PORT=3000"

set "BACKEND_CANDIDATES=%BACKEND_PORT% 8022 8021 8020 8023 8024 8001 8002 8010 8011"
set "SELECTED_BACKEND_PORT="
set "SELECTED_BACKEND_MODE="
set "FIRST_FREE_PORT="

echo.
echo ========================================
echo   Storyworks Unified startup
echo ========================================
echo.

for %%P in (%BACKEND_CANDIDATES%) do (
  call :CheckBackend %%P
  if "!BACKEND_STATUS!"=="compatible" (
    set "SELECTED_BACKEND_PORT=%%P"
    set "SELECTED_BACKEND_MODE=existing"
    goto BackendSelected
  )
  if "!BACKEND_STATUS!"=="free" if "!FIRST_FREE_PORT!"=="" set "FIRST_FREE_PORT=%%P"
)

if not "%FIRST_FREE_PORT%"=="" (
  set "SELECTED_BACKEND_PORT=%FIRST_FREE_PORT%"
  set "SELECTED_BACKEND_MODE=start"
  goto BackendSelected
)

echo ERROR: no compatible or free backend port was found.
echo Close stale Storyworks backend windows and run start.bat again.
pause
exit /b 1

:BackendSelected
set "BACKEND_URL=http://%BACKEND_HOST%:%SELECTED_BACKEND_PORT%"
set "STORYWORKS_API_TARGET=%BACKEND_URL%"

if "%SELECTED_BACKEND_MODE%"=="existing" (
  echo Backend ready: %BACKEND_URL%
) else (
  echo Starting backend: %BACKEND_URL%
  start "Storyworks Backend" cmd /k "cd /d %~dp0apps\backend && python run.py --host %BACKEND_HOST% --port %SELECTED_BACKEND_PORT%"
)

echo Checking frontend port: http://localhost:%FRONTEND_PORT%
powershell -NoProfile -ExecutionPolicy Bypass -Command "$c = New-Object Net.Sockets.TcpClient; try { $c.Connect('127.0.0.1', %FRONTEND_PORT%); $c.Close(); exit 1 } catch { exit 0 }"
if "%ERRORLEVEL%"=="1" (
  echo Frontend already running: http://localhost:%FRONTEND_PORT%
  echo Refresh the page if it was opened before this startup.
) else (
  echo Starting frontend: http://localhost:%FRONTEND_PORT%
  start "Storyworks Frontend" cmd /k "cd /d %~dp0apps\frontend && set STORYWORKS_API_TARGET=%BACKEND_URL%&& npm run dev -- --host 127.0.0.1 --port %FRONTEND_PORT%"
)

echo.
echo Frontend: http://localhost:%FRONTEND_PORT%
echo Backend:  %BACKEND_URL%
echo.
pause
exit /b 0

:CheckBackend
set "BACKEND_STATUS=occupied"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$base='http://%BACKEND_HOST%:%1'; try { $h=Invoke-RestMethod -TimeoutSec 2 -Uri ($base + '/api/health'); $s=Invoke-RestMethod -TimeoutSec 2 -Uri ($base + '/api/settings/ai'); if ($h.code -eq 200 -and $h.data.status -eq 'ok' -and $s.code -eq 200) { exit 2 } } catch {}; $c=New-Object Net.Sockets.TcpClient; try { $c.Connect('%BACKEND_HOST%', %1); $c.Close(); exit 1 } catch { exit 0 }"
if "%ERRORLEVEL%"=="2" set "BACKEND_STATUS=compatible"
if "%ERRORLEVEL%"=="0" set "BACKEND_STATUS=free"
exit /b 0
