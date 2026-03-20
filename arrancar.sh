#!/bin/bash
# ─────────────────────────────────────────────────────────
#  Punto de Ventas — Setup completo (Mac)
# ─────────────────────────────────────────────────────────

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo ""
echo "🚀 Punto de Ventas"
echo ""

# ── Verificar Python ──────────────────────────────────────
PYTHON=""
for cmd in python3.12 python3.11 python3.10 python3.9 python3; do
    if command -v $cmd &>/dev/null; then
        PYTHON=$cmd
        echo "✅ Python encontrado: $cmd ($($cmd --version 2>&1))"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "❌ No se encontró Python."
    echo "   Descarga Python 3.11 de: https://www.python.org/downloads/"
    exit 1
fi

# ── Crear entorno virtual si no existe ───────────────────
if [ ! -d "$DIR/venv" ]; then
    echo "📦 Creando entorno virtual..."
    $PYTHON -m venv venv
    echo "✅ Entorno virtual creado"
fi

# ── Activar entorno virtual ───────────────────────────────
source "$DIR/venv/bin/activate"
echo "✅ Entorno virtual activado"

# ── Instalar dependencias ─────────────────────────────────
echo "📦 Instalando dependencias..."
pip install --upgrade pip --quiet
pip install customtkinter mysql-connector-python Pillow reportlab python-dotenv --quiet

# ── Dependencias para escáner de cámara ──────────────────
echo "📷 Verificando dependencias de cámara..."
pip install opencv-python pyzbar --quiet 2>/dev/null
if ! python3 -c "from pyzbar import pyzbar" 2>/dev/null; then
    if command -v brew &>/dev/null; then
        brew install zbar --quiet
        pip install pyzbar --quiet
    fi
fi

echo "✅ Dependencias instaladas"

# ── Modo: arrancar normal o diagnóstico ───────────────────
if [ "$1" = "diagnostico" ]; then
    echo ""
    echo "🔍 Ejecutando diagnóstico de roles..."
    echo ""
    python3 diagnostico_roles.py
    deactivate
    exit 0
fi

# ── Verificar/crear BD ────────────────────────────────────
BD_EXISTE=$(python3 -c "
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
except Exception as e:
    print('NO')
" 2>/dev/null)

if [ "$BD_EXISTE" = "NO" ]; then
    echo "📋 Creando base de datos..."
    python3 init_db.py
fi

# ── Lanzar app ────────────────────────────────────────────
echo ""
echo "✅ Iniciando aplicación..."
echo ""
python3 main.py

deactivate
