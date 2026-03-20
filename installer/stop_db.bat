@echo off
:: ─────────────────────────────────────────────────────────────────
::  stop_db.bat — Detiene MariaDB portable
:: ─────────────────────────────────────────────────────────────────
setlocal

set BASE_DIR=C:\PuntoDeVentas
set MARIA_DIR=%BASE_DIR%\mariadb
set PORT=3307

echo [INFO] Deteniendo MariaDB...
"%MARIA_DIR%\bin\mysqladmin.exe" -u root -padmin123 --port=%PORT% shutdown >NUL 2>&1

:: Esperar cierre
timeout /T 3 /NOBREAK >NUL

tasklist /FI "IMAGENAME eq mysqld.exe" 2>NUL | find /I /N "mysqld.exe" >NUL
if "%ERRORLEVEL%"=="0" (
    echo [WARN] Forzando cierre...
    taskkill /F /IM mysqld.exe >NUL 2>&1
)

echo [OK] MariaDB detenida.
exit /b 0
