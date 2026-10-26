@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto build
call SETUP.bat
if errorlevel 1 exit /b 1
:build
echo Building a Windows desktop application on this Windows PC...
echo If you want speech support in the EXE, run INSTALL_SPEECH.bat before building.
".venv\Scripts\python.exe" -m pip install "pyinstaller>=6,<7"
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean Anato12Studio.spec
if errorlevel 1 goto failed
echo.
echo Ready: dist\Anato12Studio\Anato12Studio.exe
echo Keep the entire Anato12Studio folder together. FFmpeg is installed separately.
pause
exit /b 0
:failed
echo Build failed. Read the error above.
pause
exit /b 1
