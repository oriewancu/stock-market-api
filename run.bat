@echo off
title Stock API Server

echo ==========================================
echo          STOCK API SERVER
echo ==========================================
echo.

where py >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python tidak ditemukan.
    echo Jalankan setup.bat terlebih dahulu.
    pause
    exit /b 1
)

if not exist "server.py" (
    echo [ERROR] server.py tidak ditemukan.
    pause
    exit /b 1
)

if not exist "Daftar Saham  - 20260924.xlsx" (
    echo [WARNING] File Excel tidak ditemukan:
    echo Daftar Saham  - 20260924.xlsx
    echo.
    echo API /api/get_idx_tickers tidak akan bekerja.
    echo.
)

echo Starting server...
echo.

py server.py

pause
