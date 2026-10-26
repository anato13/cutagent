@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto launch
call SETUP.bat
if errorlevel 1 exit /b 1
:launch
if not exist ".venv\Scripts\python.exe" exit /b 1
".venv\Scripts\python.exe" -m anato12_studio
if not errorlevel 1 exit /b 0
echo.
echo Anato12 Studio could not start. Read the error above.
echo Try SETUP.bat again, or see START_HERE.md.
pause
exit /b 1
