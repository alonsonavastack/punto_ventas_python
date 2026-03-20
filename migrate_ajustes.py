#!/usr/bin/env python3
"""
migrate_ajustes.py
Agrega la tabla ajustes_inventario a la BD existente sin perder datos.
Ejecutar: python3 migrate_ajustes.py
"""
import sys
try:
    import mysql.connector
except ImportError:
    print("[ERROR] pip install mysql-connector-python --user"); sys.exit(1)

import os
from dotenv import load_dotenv
load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST","127.0.0.1"),
    port=int(os.getenv("DB_PORT",3306)),
    user=os.getenv("DB_USER","root"),
    password=os.getenv("DB_PASSWORD","admin123"),
    database=os.getenv("DB_NAME","punto_ventas"),
    charset="utf8mb4"
)
cur = conn.cursor()

print("🔧 Aplicando migración...")

cur.execute("""
    CREATE TABLE IF NOT EXISTS ajustes_inventario (
        id          INT AUTO_INCREMENT PRIMARY KEY,
        producto_id INT NOT NULL,
        usuario_id  INT,
        fecha       DATETIME DEFAULT CURRENT_TIMESTAMP,
        tipo        ENUM('entrada','salida','ajuste','merma','devolucion') NOT NULL,
        cantidad_anterior DECIMAL(10,2) NOT NULL,
        cantidad_nueva    DECIMAL(10,2) NOT NULL,
        diferencia        DECIMAL(10,2) NOT NULL,
        motivo      VARCHAR(100),
        notas       TEXT,
        FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE,
        FOREIGN KEY (usuario_id)  REFERENCES usuarios(id)  ON DELETE SET NULL
    )
""")
conn.commit()
print("✅ Tabla ajustes_inventario creada")

cur.close()
conn.close()
print("✅ Migración completada. Ya puedes usar el historial de ajustes.")
