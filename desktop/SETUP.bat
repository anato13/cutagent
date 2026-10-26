@echo off
setlocal
cd /d "%~dp0"
echo.
echo Anato12 Studio - first-time setup
echo.
set "STUDIO_PYTHON="
py -3.12 -c "import sys; assert sys.version_info[:2] == (3,12)" >nul 2>&1
if not errorlevel 1 set "STUDIO_PYTHON=py -3.12"
if defined STUDIO_PYTHON goto python_ready
py -3.13 -c "import sys; assert sys.version_info[:2] == (3,13)" >nul 2>&1
if not errorlevel 1 set "STUDIO_PYTHON=py -3.13"
if defined STUDIO_PYTHON goto python_ready
python -c "import sys; assert (3,10) <= sys.version_info[:2] < (3,14)" >nul 2>&1
if not errorlevel 1 set "STUDIO_PYTHON=python"
if defined STUDIO_PYTHON goto python_ready
echo Python was not found, or the version is unsupported.
echo Install Python 3.12 or 3.13 for Windows from https://www.python.org/downloads/windows/
echo During installation, check "Add python.exe to PATH".
echo Then double-click SETUP.bat again.
pause
exit /b 1
:python_ready
if exist ".venv\Scripts\python.exe" goto install_packages
echo Creating a private Python environment in this folder...
%STUDIO_PYTHON% -m venv .venv
if errorlevel 1 goto failed
:install_packages
echo Installing the free desktop components. This can take several minutes.
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -c "from anato12_studio.video import find_tool; print(find_tool('ffmpeg')); print(find_tool('ffprobe'))" >nul 2>&1
if not errorlevel 1 goto complete
echo.
echo FFmpeg is needed to import and export videos.
where winget >nul 2>&1
if errorlevel 1 goto manual_ffmpeg
choice /C YN /N /M "Install the free Gyan FFmpeg package with winget? [Y/N] "
if errorlevel 2 goto manual_ffmpeg
winget install --id Gyan.FFmpeg --exact --accept-package-agreements --accept-source-agreements
if errorlevel 1 goto manual_ffmpeg
goto complete
:manual_ffmpeg
echo.
echo Desktop components are installed, but FFmpeg still needs setup.
echo Read START_HERE.md, section "FFmpeg", before importing a recording.
pause
exit /b 0
:complete
echo.
echo Setup finished. Double-click START_ANATO12.bat to open the editor.
echo Optional transcription can be added later with INSTALL_SPEECH.bat.
pause
exit /b 0
:failed
echo.
echo Setup did not finish. Keep this window open and check the error above.
echo Verify your internet connection and retry SETUP.bat.
echo Do not disable certificate verification.
pause
exit /b 1
