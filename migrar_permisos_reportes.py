#!/usr/bin/env python3
"""
migrar_permisos_reportes.py
Agrega el permiso 'reportes_ver_todos' al catalogo y lo asigna
a Administrador y Supervisor. Cajero y Almacenista solo veran sus propias ventas.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.database.connection import Database

db = Database.get_instance()
if not db.connection:
    print("❌ No se pudo conectar a MySQL.")
    sys.exit(1)

# 1. Agregar al catalogo si no existe
db.execute_query("""
    INSERT IGNORE INTO permisos_catalogo(clave, nombre, modulo, descripcion)
    VALUES('reportes_ver_todos',
           'Ver reportes de todos los usuarios',
           'Reportes',
           'Permite ver ventas de todos los cajeros. Sin este permiso, solo ve sus propias ventas.')
""")
print("✅ Permiso 'reportes_ver_todos' registrado en catalogo.")

# 2. Asignar a Administrador y Supervisor
for rol_nombre in ("Administrador", "Supervisor"):
    rol = db.fetch_one("SELECT id FROM roles WHERE nombre = %s", (rol_nombre,))
    if rol:
        db.execute_query(
            "INSERT IGNORE INTO permisos_roles(rol_id, permiso_clave) VALUES(%s, 'reportes_ver_todos')",
            (rol["id"],)
        )
        print(f"✅ Asignado a rol '{rol_nombre}'.")
    else:
        print(f"⚠  Rol '{rol_nombre}' no encontrado.")

print("\n🎉 Listo. Reinicia la app para aplicar los cambios.")
print("   Cajero y Almacenista verán solo sus propias ventas en Reportes.")
print("   Administrador y Supervisor ven todo.")
