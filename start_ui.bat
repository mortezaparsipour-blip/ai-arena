@echo off
chcp 65001 >nul
echo ========================================
echo       AI Arena - Launcher
echo ========================================
echo.

if not exist .venv\Scripts\activate.bat (
    echo [ERROR] Virtual environment not found. Run: python -m venv .venv && .venv\Scripts\activate
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
echo [OK] Virtual environment activated.
echo [INFO] Starting AI Arena...
echo.

streamlit run run.py

pause
