#!/usr/bin/env python3
"""
diagnostico_roles.py — compatible python3 (Mac/Win/Linux)
Ejecuta este script para ver el estado completo de roles y permisos en tu BD.

Uso en Mac (desde la carpeta del proyecto):
    bash arrancar.sh diagnostico
        — O —
    source venv/bin/activate && python3 diagnostico_roles.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.database.connection import Database
except ImportError as e:
    print("[ERROR] Faltan dependencias. Ejecuta primero: bash arrancar.sh")
    print(f"   Error: {e}")
    sys.exit(1)

try:
    db = Database.get_instance()
    if not db.connection:
        print("❌ No se pudo conectar a MySQL.")
        print("   Verifica que MySQL esté corriendo y que tu .env sea correcto.")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error de conexión: {e}")
    sys.exit(1)

SEP = "=" * 60

print(f"\n{SEP}")
print("  DIAGNÓSTICO: ROLES Y PERMISOS")
print(SEP)

# ── 1. Tablas existentes ──────────────────────────────────────────────────────
print("\n📋 TABLAS EN LA BASE DE DATOS:")
try:
    tablas = db.fetch_all("SHOW TABLES")
    nombres = [list(t.values())[0] for t in tablas]
    requeridas = ["roles","permisos_catalogo","permisos_roles",
                  "usuarios","caja_sesiones","caja_movimientos","ajustes_inventario"]
    for t in requeridas:
        estado = "✅" if t in nombres else "❌ FALTA"
        print(f"  {estado}  {t}")
    otras = [n for n in nombres if n not in requeridas]
    print(f"\n  Otras tablas: {', '.join(otras)}")
except Exception as e:
    print(f"  ❌ Error: {e}")

# ── 2. Roles ──────────────────────────────────────────────────────────────────
print(f"\n🔐 ROLES:")
try:
    roles = db.fetch_all("SELECT id, nombre, color, activo FROM roles ORDER BY nombre")
    if roles:
        for r in roles:
            n_perms = db.fetch_one(
                "SELECT COUNT(*) AS c FROM permisos_roles WHERE rol_id=%s", (r["id"],))
            estado = "✅ activo" if r["activo"] else "❌ inactivo"
            print(f"  [{r['id']}] {r['nombre']:20} {estado}  "
                  f"permisos:{n_perms['c']:3}  color:{r['color']}")
    else:
        print("  ⚠  No hay roles — reinicia la app para crearlos automáticamente")
except Exception as e:
    print(f"  ❌ No existe tabla roles: {e}")
    print("  → Solución: reinicia la app (bash arrancar.sh)")

# ── 3. Catálogo de permisos ───────────────────────────────────────────────────
print(f"\n📚 CATÁLOGO DE PERMISOS:")
try:
    total = db.fetch_one("SELECT COUNT(*) AS c FROM permisos_catalogo")
    print(f"  Total: {total['c']} permisos")
    modulos = db.fetch_all(
        "SELECT modulo, COUNT(*) AS c FROM permisos_catalogo GROUP BY modulo ORDER BY modulo")
    for m in modulos:
        print(f"    {m['modulo']:20} → {m['c']} permisos")
    if total['c'] < 20:
        print("  ⚠  Faltan permisos — reinicia la app para agregarlos")
except Exception as e:
    print(f"  ❌ Error: {e}")

# ── 4. Usuarios ───────────────────────────────────────────────────────────────
print(f"\n👤 USUARIOS ACTIVOS:")
try:
    # Detectar si existe la columna 'rol' (esquema viejo)
    cols_info = db.fetch_all("SHOW COLUMNS FROM usuarios")
    col_names = [c["Field"] for c in cols_info]
    tiene_rol_viejo = "rol" in col_names
    tiene_rol_id    = "rol_id" in col_names

    if tiene_rol_id:
        usuarios = db.fetch_all("""
            SELECT u.id, u.nombre, u.usuario, u.rol_id,
                   r.nombre AS rol_nombre
            FROM usuarios u
            LEFT JOIN roles r ON u.rol_id = r.id
            WHERE u.activo = 1
            ORDER BY u.nombre
        """)
    else:
        usuarios = db.fetch_all(
            "SELECT id, nombre, usuario FROM usuarios WHERE activo=1 ORDER BY nombre")
        for u in usuarios:
            u["rol_id"] = None
            u["rol_nombre"] = None

    sin_rol = []
    for u in usuarios:
        rol_str = u.get("rol_nombre") or "⚠ sin rol"
        if not u.get("rol_id"):
            sin_rol.append(u)
            estado = "⚠ "
        else:
            estado = "✅"
        print(f"  {estado} [{u['id']}] {u['nombre']:20} "
              f"login:{u['usuario']:15} rol:{rol_str}")

    if sin_rol:
        print(f"\n  ⚠  {len(sin_rol)} usuario(s) sin rol asignado:")
        for u in sin_rol:
            print(f"     → '{u['nombre']}' (login: {u['usuario']})")
        print("  → Ve a 🔐 Roles y Usuarios → tab Usuarios → edita y asigna rol")

except Exception as e:
    print(f"  ❌ Error: {e}")

# ── 5. Permisos del Administrador ─────────────────────────────────────────────
print(f"\n🔑 PERMISOS ROL 'Administrador':")
try:
    admin_rol = db.fetch_one("SELECT id FROM roles WHERE nombre='Administrador'")
    if admin_rol:
        perms_rows = db.fetch_all(
            "SELECT permiso_clave FROM permisos_roles WHERE rol_id=%s ORDER BY permiso_clave",
            (admin_rol["id"],))
        claves = [p["permiso_clave"] for p in perms_rows]

        # Todos los permisos del catálogo — el admin debe tenerlos TODOS
        catalogo = db.fetch_all("SELECT clave FROM permisos_catalogo ORDER BY clave")
        todos = [p["clave"] for p in catalogo]
        faltantes = [p for p in todos if p not in claves]

        print(f"  Total en catálogo : {len(todos)}")
        print(f"  Asignados al Admin: {len(claves)}")

        if faltantes:
            print(f"  ❌ FALTAN {len(faltantes)} permisos:")
            for f in faltantes:
                print(f"     ✗ {f}")
            print("  → Solución: reinicia la app para agregarlos automáticamente")
        else:
            print("  ✅ Administrador tiene todos los permisos del catálogo")
    else:
        print("  ❌ Rol 'Administrador' no existe")
        print("  → Reinicia la app para crearlo")
except Exception as e:
    print(f"  ❌ Error: {e}")

# ── 6. Estado de caja ─────────────────────────────────────────────────────────
print(f"\n💰 SESIONES DE CAJA:")
try:
    abiertas = db.fetch_one(
        "SELECT COUNT(*) AS c FROM caja_sesiones WHERE estado='abierta'")
    total_s  = db.fetch_one("SELECT COUNT(*) AS c FROM caja_sesiones")
    print(f"  Total sesiones: {total_s['c']}")
    print(f"  Sesiones abiertas ahora: {abiertas['c']}")
    if abiertas['c'] > 1:
        print("  ⚠  Hay más de 1 sesión abierta — puede causar problemas")
        print("  → Solución: reinicia la app, cerrará sesiones huérfanas automáticamente")
    elif abiertas['c'] == 0:
        print("  ✅ No hay sesiones abiertas")
    else:
        print("  ✅ Una sesión abierta (normal)")
except Exception as e:
    print(f"  ❌ Error (tabla puede no existir): {e}")

# ── Resumen final ─────────────────────────────────────────────────────────────
print(f"\n{SEP}")
print("  RESUMEN")
print(SEP)
print("""
  Si todo muestra ✅ → el sistema está correcto.

  Si hay ❌ o ⚠:
  1. Cierra la app si está abierta
  2. Ejecuta:  bash arrancar.sh
     (la app se inicia y repara todo automáticamente)
  3. Vuelve a correr:  bash arrancar.sh diagnostico

  Si un usuario no ve módulos:
  → Ve a 🔐 Roles y Usuarios → edita el usuario → asigna un rol
  → Cierra sesión y vuelve a entrar
""")
print(SEP + "\n")
