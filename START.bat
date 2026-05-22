@echo off
chcp 65001 >nul
title KazNU Smart Attendance AI
set PATH=C:\Program Files\nodejs;%PATH%
set PYTHONIOENCODING=utf-8

:: ── Орнатылу тексеру ───────────────────────────────────
python -m pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [!] Алдымен INSTALL.bat іске қосыңыз!
    echo.
    pause
    exit /b 1
)
if not exist "%~dp0frontend\node_modules\" (
    echo.
    echo  [!] Алдымен INSTALL.bat іске қосыңыз!
    echo.
    pause
    exit /b 1
)

echo.
echo  ══════════════════════════════════════════
echo    KazNU Smart Attendance AI
echo    Backend:   http://localhost:8000
echo    Frontend:  http://localhost:5173
echo  ══════════════════════════════════════════
echo.

:: Ескі процестерді тоқтату
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING 2^>nul') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING 2^>nul') do taskkill /F /PID %%a >nul 2>&1
timeout /t 1 /nobreak >nul

start "KazNU-Backend"  cmd /k "chcp 65001 >nul && set PYTHONIOENCODING=utf-8 && cd /d "%~dp0backend" && python -m uvicorn main:app --host 0.0.0.0 --port 8000"
timeout /t 4 /nobreak >nul
start "KazNU-Frontend" cmd /k "set PATH=C:\Program Files\nodejs;%%PATH%% && cd /d "%~dp0frontend" && npm run dev -- --port 5173"
timeout /t 6 /nobreak >nul
start "" "http://localhost:5173"
echo  Жүйе іске қосылды!
