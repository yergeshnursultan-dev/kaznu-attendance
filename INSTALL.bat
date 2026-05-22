@echo off
chcp 65001 >nul
title KazNU — Орнату / Installation

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║     KazNU Smart Attendance — Орнату              ║
echo  ║     Бір рет іске қосыңыз / Run once only         ║
echo  ╚══════════════════════════════════════════════════╝
echo.

:: ── Python тексеру ─────────────────────────────────────
echo [1/5] Python тексерілуде...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ҚАТЕ: Python орнатылмаған!
    echo  https://www.python.org/downloads/ сайтынан жүктеп алыңыз
    echo  Орнату кезінде "Add Python to PATH" белгісін қойыңыз!
    echo.
    pause
    exit /b 1
)
python --version
echo  [OK] Python табылды
echo.

:: ── Node.js тексеру ────────────────────────────────────
echo [2/5] Node.js тексерілуде...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ҚАТЕ: Node.js орнатылмаған!
    echo  https://nodejs.org сайтынан LTS нұсқасын жүктеп алыңыз
    echo.
    pause
    exit /b 1
)
node --version
echo  [OK] Node.js табылды
echo.

:: ── Python библиотекалары ──────────────────────────────
echo [3/5] Python библиотекалары орнатылуда...
echo  (бірінші рет 2-3 минут кетуі мүмкін)
echo.
python -m pip install --upgrade pip --quiet
python -m pip install fastapi uvicorn[standard] sqlalchemy opencv-python numpy Pillow python-multipart aiofiles onnxruntime --quiet
if %errorlevel% neq 0 (
    echo  ҚАТЕ: Python библиотекалары орнатылмады!
    pause
    exit /b 1
)
echo  [OK] Python библиотекалары дайын
echo.

:: ── ONNX модельдері ────────────────────────────────────
echo [4/5] AI модельдері тексерілуде...
if not exist "%~dp0backend\face_detection_yunet_2023mar.onnx" (
    echo  YuNet детектор жүктелуде...
    python -c "import urllib.request; urllib.request.urlretrieve('https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx', r'%~dp0backend\face_detection_yunet_2023mar.onnx'); print('[OK] YuNet')"
) else (
    echo  [OK] YuNet модель бар
)
if not exist "%~dp0backend\face_recognition_sface_2021dec.onnx" (
    echo  SFace recognizer жүктелуде...
    python -c "import urllib.request; urllib.request.urlretrieve('https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx', r'%~dp0backend\face_recognition_sface_2021dec.onnx'); print('[OK] SFace')"
) else (
    echo  [OK] SFace модель бар
)
echo.

:: ── npm пакеттері ──────────────────────────────────────
echo [5/5] Frontend пакеттері орнатылуда...
cd /d "%~dp0frontend"
call npm install --silent
if %errorlevel% neq 0 (
    echo  ҚАТЕ: npm install сәтсіз!
    pause
    exit /b 1
)
echo  [OK] Frontend пакеттері дайын
echo.

:: ── faces папкасы ──────────────────────────────────────
if not exist "%~dp0backend\faces\" mkdir "%~dp0backend\faces"

:: ── Дайын ─────────────────────────────────────────────
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║  Орнату аяқталды!                                ║
echo  ║                                                  ║
echo  ║  Енді START.bat іске қосыңыз                     ║
echo  ╚══════════════════════════════════════════════════╝
echo.
pause
