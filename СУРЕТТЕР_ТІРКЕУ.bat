@echo off
chcp 65001 >nul
echo ================================================
echo   KazNU — Студент суреттерін тіркеу
echo ================================================
echo.
echo Суреттерді мына папкаға салыңыз:
echo   %~dp0backend\faces\
echo.
echo Файл аты = Студент ID болуы керек:
echo   STU001.jpg
echo   STU002.jpg  ... т.б.
echo.
pause

set PY=C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe
cd /d "%~dp0backend"
%PY% enroll_faces.py

echo.
echo Сервер жаңартылуда...
curl -s -X POST http://localhost:8000/api/reload-faces >nul 2>&1
if %errorlevel%==0 (
    echo [OK] Сервер суреттерді жуктеди — камера дайын!
) else (
    echo [!] Сервер іске косылмаган — START.bat аркылы косыныз
)
echo.
pause
