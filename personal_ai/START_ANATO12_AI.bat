@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 -m anato12_ai
) else (
    python -m anato12_ai
)
if errorlevel 1 (
    echo.
    echo ANATO12 AI could not start. See README.md for setup help.
    pause
)
