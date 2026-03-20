@echo off
:: ─────────────────────────────────────────────────────────────────
::  start_db.bat — Inicia MariaDB portable
::  Llamado automáticamente por la app al arrancar
:: ─────────────────────────────────────────────────────────────────
setlocal

set BASE_DIR=C:\PuntoDeVentas
set MARIA_DIR=%BASE_DIR%\mariadb
set DATA_DIR=%BASE_DIR%\data
set LOG_DIR=%BASE_DIR%\logs
set PORT=3307

:: Verificar si ya está corriendo
tasklist /FI "IMAGENAME eq mysqld.exe" 2>NUL | find /I /N "mysqld.exe" >NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] MariaDB ya esta corriendo.
    exit /b 0
)

:: Crear carpetas si no existen
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

:: Iniciar MariaDB
echo [INFO] Iniciando MariaDB en puerto %PORT%...
start /B "" "%MARIA_DIR%\bin\mysqld.exe" ^
    --datadir="%DATA_DIR%" ^
    --port=%PORT% ^
    --socket="%BASE_DIR%\mysql.sock" ^
    --log-error="%LOG_DIR%\mariadb.log" ^
    --pid-file="%BASE_DIR%\mariadb.pid" ^
    --skip-networking=0 ^
    --bind-address=127.0.0.1

:: Esperar a que arranque (máx 15 segundos)
echo [INFO] Esperando que MariaDB este listo...
set /A intentos=0
:ESPERAR
timeout /T 1 /NOBREAK >NUL
set /A intentos+=1
"%MARIA_DIR%\bin\mysqladmin.exe" -u root -padmin123 --port=%PORT% ping >NUL 2>&1
if "%ERRORLEVEL%"=="0" (
    echo [OK] MariaDB lista.
    exit /b 0
)
if %intentos% LSS 15 goto ESPERAR

echo [ERROR] MariaDB no respondio en 15 segundos. Revisa %LOG_DIR%\mariadb.log
exit /b 1
