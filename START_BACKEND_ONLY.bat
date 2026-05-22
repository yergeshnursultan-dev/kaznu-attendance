@echo off
chcp 65001 >nul
echo ================================================
echo   KazNU Smart Attendance AI - Backend
echo ================================================
echo.
echo Backend: http://localhost:8000
echo.
set PYTHONIOENCODING=utf-8
set PY=C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe
cd /d "%~dp0backend"
%PY% -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
