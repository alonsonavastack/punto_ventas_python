@echo off
REM ─────────────────────────────────────────────────────────
REM  Punto de Ventas — Setup completo (Windows)
REM ─────────────────────────────────────────────────────────

cd /d "%~dp0"

echo.
echo  Punto de Ventas
echo.

REM ── Verificar Python ─────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python no encontrado.
    echo  Descarga Python 3.11 de: https://www.python.org/downloads/
    echo  Asegurate de marcar "Add Python to PATH" al instalar.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo  Python encontrado: %PYVER%

REM ── Crear entorno virtual si no existe ───────────────────
if not exist "venv" (
    echo  Creando entorno virtual...
    python -m venv venv
    echo  Entorno virtual creado
)

REM ── Activar entorno virtual ───────────────────────────────
call venv\Scripts\activate.bat
echo  Entorno virtual activado

REM ── Instalar dependencias ─────────────────────────────────
echo  Instalando dependencias...
pip install --upgrade pip --quiet
pip install customtkinter mysql-connector-python Pillow reportlab python-dotenv --quiet

REM ── Dependencias para escaner de camara ──────────────────
echo  Verificando dependencias de camara...
pip install opencv-python pyzbar --quiet 2>nul
echo  Dependencias instaladas

REM ── Modo: arrancar normal o diagnostico ──────────────────
if "%1"=="diagnostico" (
    echo.
    echo  Ejecutando diagnostico de roles...
    echo.
    python diagnostico_roles.py
    call venv\Scripts\deactivate.bat
    pause
    exit /b 0
)

REM ── Verificar/crear BD ────────────────────────────────────
python -c "
import mysql.connector, os
from dotenv import load_dotenv
load_dotenv()
try:
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST','127.0.0.1'),
        port=int(os.getenv('DB_PORT',3306)),
        user=os.getenv('DB_USER','root'),
        password=os.getenv('DB_PASSWORD','admin123'))
    cur = conn.cursor()
    cur.execute(\"SHOW DATABASES LIKE 'punto_ventas'\")
    print('SI' if cur.fetchone() else 'NO')
    conn.close()
except:
    print('NO')
" > tmp_bd.txt 2>nul

set /p BD_EXISTE=<tmp_bd.txt
del tmp_bd.txt 2>nul

if "%BD_EXISTE%"=="NO" (
    echo  Creando base de datos...
    python init_db.py
)

REM ── Lanzar app ────────────────────────────────────────────
echo.
echo  Iniciando aplicacion...
echo.
python main.py

call venv\Scripts\deactivate.bat
