@echo off
chcp 65001 >nul

rem Always run from the folder this .bat lives in, so the project's own
rem .venv is used no matter where the script is launched from
rem (Explorer double-click, Run as administrator, or a foreign terminal cwd).
cd /d "%~dp0"

echo ========================================
echo       AI Arena - Launcher
echo ========================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Project virtual environment not found in "%CD%".
    echo         Create it with:   python -m venv .venv
    echo         Then install with: .venv\Scripts\python -m pip install -e .
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"
echo [OK] Using project venv: %VIRTUAL_ENV%
echo [INFO] Starting AI Arena on http://localhost:8085 ...
echo.

rem Explicit .venv interpreter: guarantees the project's own environment,
rem independent of what "python" or "streamlit" is on the system PATH.
".venv\Scripts\python.exe" -m streamlit run run.py --server.port 8085

pause
