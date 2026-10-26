@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run SETUP.bat first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m anato12_studio.evaluate_model --interactive
set "STUDIO_RESULT=%ERRORLEVEL%"
pause
exit /b %STUDIO_RESULT%
