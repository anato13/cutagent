@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto install
call SETUP.bat
if errorlevel 1 exit /b 1
:install
if not exist ".venv\Scripts\python.exe" exit /b 1
echo Installing optional local speech tools...
".venv\Scripts\python.exe" -m pip install -r requirements-speech.txt
if errorlevel 1 goto failed
echo.
echo Speech tools are installed. Reopen Anato12 Studio.
echo In Dialogue and captions, choose a model and click Transcribe locally.
echo First use downloads that free model. Your recording is not uploaded.
pause
exit /b 0
:failed
echo.
echo Optional speech installation failed. Import, preview and export still work.
echo Check the error above and see START_HERE.md.
pause
exit /b 1
