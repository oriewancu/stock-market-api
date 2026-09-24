@echo off
title Stock API - Setup

echo ==========================================
echo       STOCK API - FIRST TIME SETUP
echo ==========================================
echo.

where py >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python tidak ditemukan.
    echo.
    echo Silakan install Python terlebih dahulu.
    echo Download:
    echo https://www.python.org/downloads/
    echo.
    echo Pastikan opsi "Add Python to PATH" dicentang.
    pause
    exit /b 1
)

echo [OK] Python ditemukan:
py --version
echo.

echo [1/2] Upgrade pip...
py -m pip install --upgrade pip

echo.
echo [2/2] Install dependencies...
py -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Instalasi dependency gagal.
    echo Coba jalankan:
    echo.
    echo     py -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo       SETUP SELESAI
echo ==========================================
echo.
echo Jalankan server dengan:
echo     py server.py
echo.
pause
