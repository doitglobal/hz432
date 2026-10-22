@echo off
rem Creates .venv next to this file (if missing) and installs requirements.txt into it.
rem Safe to run repeatedly - with an existing .venv it only installs missing packages.
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" goto install

where py >nul 2>nul
if %errorlevel%==0 (
    set "PY=py -3"
) else (
    where python >nul 2>nul || (
        echo Python not found. Install Python 3.10+ from https://www.python.org/ and run this script again.
        exit /b 1
    )
    set "PY=python"
)

echo Creating .venv ...
%PY% -m venv .venv || (echo Failed to create .venv & exit /b 1)

:install
echo Installing requirements.txt ...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt || (
    echo Installing dependencies failed.
    exit /b 1
)

echo Done. Usage: .venv\Scripts\python hz432.py "C:\Music"
exit /b 0
