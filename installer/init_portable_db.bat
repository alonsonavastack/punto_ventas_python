@echo off
:: ─────────────────────────────────────────────────────────────────
::  init_portable_db.bat — Inicializa MariaDB por primera vez
::  y crea la base de datos punto_ventas
::  Se ejecuta UNA SOLA VEZ durante la instalación
:: ─────────────────────────────────────────────────────────────────
setlocal

set BASE_DIR=C:\PuntoDeVentas
set MARIA_DIR=%BASE_DIR%\mariadb
set DATA_DIR=%BASE_DIR%\data
set LOG_DIR=%BASE_DIR%\logs
set SCHEMA=%BASE_DIR%\app\database\schema.sql
set PORT=3307

echo.
echo ============================================
echo   Inicializando base de datos...
echo ============================================
echo.

:: Crear carpetas
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
if not exist "%LOG_DIR%"  mkdir "%LOG_DIR%"

:: Inicializar data directory de MariaDB (solo primera vez)
if not exist "%DATA_DIR%\mysql" (
    echo [1/4] Inicializando directorio de datos MariaDB...
    "%MARIA_DIR%\bin\mysql_install_db.exe" ^
        --datadir="%DATA_DIR%" ^
        --password=admin123 ^
        --default-user=root
    if errorlevel 1 (
        echo [ERROR] Fallo al inicializar MariaDB.
        pause
        exit /b 1
    )
    echo [OK] Directorio inicializado.
) else (
    echo [OK] Directorio de datos ya existe, omitiendo inicializacion.
)

:: Iniciar MariaDB
echo [2/4] Iniciando MariaDB...
call "%BASE_DIR%\installer\start_db.bat"
if errorlevel 1 (
    echo [ERROR] No se pudo iniciar MariaDB.
    pause
    exit /b 1
)

:: Crear base de datos
echo [3/4] Creando base de datos punto_ventas...
"%MARIA_DIR%\bin\mysql.exe" -u root -padmin123 --port=%PORT% -e "CREATE DATABASE IF NOT EXISTS punto_ventas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>NUL
if errorlevel 1 (
    echo [ERROR] No se pudo crear la base de datos.
    pause
    exit /b 1
)
echo [OK] Base de datos creada.

:: Importar schema
echo [4/4] Importando estructura de tablas...
if exist "%SCHEMA%" (
    "%MARIA_DIR%\bin\mysql.exe" -u root -padmin123 --port=%PORT% punto_ventas < "%SCHEMA%"
    if errorlevel 1 (
        echo [ERROR] Fallo al importar schema.
        pause
        exit /b 1
    )
    echo [OK] Schema importado correctamente.
) else (
    echo [ERROR] No se encontro el archivo schema.sql en: %SCHEMA%
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Base de datos lista correctamente!
echo ============================================
echo.
exit /b 0
