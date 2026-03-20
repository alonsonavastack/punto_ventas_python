import customtkinter as ctk
import sys
import os
import subprocess
import time

# ── Detectar si corremos como .exe empaquetado (PyInstaller) ──────────────────
if getattr(sys, 'frozen', False):
    APP_BASE = os.path.dirname(sys.executable)   # C:\PuntoDeVentas\
else:
    APP_BASE = os.path.dirname(os.path.abspath(__file__))

# ── Arrancar MariaDB portable si existe (solo Windows instalado) ──────────────
def _arrancar_mariadb_portable():
    if sys.platform != 'win32':
        return True
    mariadb_dir = os.path.join(APP_BASE, 'mariadb')
    start_bat   = os.path.join(APP_BASE, 'installer', 'start_db.bat')
    if not os.path.exists(mariadb_dir):
        return True
    if not os.path.exists(start_bat):
        return True
    # Verificar si ya corre
    result = subprocess.run(
        ['tasklist', '/FI', 'IMAGENAME eq mysqld.exe'],
        capture_output=True, text=True
    )
    if 'mysqld.exe' in result.stdout:
        return True
    # Arrancar
    print('[INFO] Iniciando MariaDB portable...')
    subprocess.Popen([start_bat], creationflags=subprocess.CREATE_NO_WINDOW, shell=True)
    mysqladmin = os.path.join(mariadb_dir, 'bin', 'mysqladmin.exe')
    for _ in range(15):
        time.sleep(1)
        try:
            r = subprocess.run(
                [mysqladmin, '-u', 'root', '-padmin123', '--port=3307', 'ping'],
                capture_output=True, timeout=2
            )
            if r.returncode == 0:
                print('[OK] MariaDB lista.')
                return True
        except Exception:
            pass
    print('[ERROR] MariaDB no respondió.')
    return False

def _configurar_env_portable():
    if not getattr(sys, 'frozen', False):
        return
    if sys.platform != 'win32':
        return
    mariadb_dir = os.path.join(APP_BASE, 'mariadb')
    if os.path.exists(mariadb_dir):
        os.environ['DB_HOST']     = '127.0.0.1'
        os.environ['DB_PORT']     = '3307'
        os.environ['DB_USER']     = 'root'
        os.environ['DB_PASSWORD'] = 'admin123'
        os.environ['DB_NAME']     = 'punto_ventas'

_configurar_env_portable()
_arrancar_mariadb_portable()

# ── Aplicar scroll ANTES de crear cualquier widget ────────────────────────────
from app.utils.scroll_fix import aplicar_scroll_global
aplicar_scroll_global()

# ── Centrar TODAS las CTkToplevel automáticamente ─────────────────────────────
def _aplicar_centrado_global():
    _orig_toplevel_init = ctk.CTkToplevel.__init__

    def _nuevo_toplevel_init(self, *args, **kwargs):
        _orig_toplevel_init(self, *args, **kwargs)
        self.after(10, lambda: _centrar_si_no_posicionada(self))

    ctk.CTkToplevel.__init__ = _nuevo_toplevel_init

def _centrar_si_no_posicionada(win):
    try:
        if not win.winfo_exists():
            return
        win.update_idletasks()
        geo    = win.geometry()
        partes = geo.split("+")
        if len(partes) < 3 or (partes[1] == "0" and partes[2] == "0"):
            dims = partes[0]
            try:
                w, h = map(int, dims.split("x"))
            except Exception:
                return
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()
            x  = max(0, (sw - w) // 2)
            y  = max(0, (sh - h) // 2)
            win.geometry(f"{w}x{h}+{x}+{y}")
    except Exception:
        pass

_aplicar_centrado_global()

# ── Importaciones ─────────────────────────────────────────────────────────────
from app.database.connection import Database
from app.views.main_window import _iniciar_app


def _columna_existe(db, tabla, columna):
    try:
        r = db.fetch_all(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s AND COLUMN_NAME=%s",
            (tabla, columna))
        return len(r) > 0
    except Exception:
        return False


def _migrar_sistema():
    try:
        db = Database.get_instance()
        if not _columna_existe(db, "usuarios", "rol_id"):
            db.execute_query("ALTER TABLE usuarios ADD COLUMN rol_id INT NULL")
        for col, defn in [("icono","VARCHAR(10) DEFAULT '📦'"),
                           ("color","VARCHAR(20) DEFAULT '#64748b'")]:
            if not _columna_existe(db, "categorias", col):
                db.execute_query(f"ALTER TABLE categorias ADD COLUMN {col} {defn}")
        if not _columna_existe(db, "ventas", "sesion_caja_id"):
            db.execute_query("ALTER TABLE ventas ADD COLUMN sesion_caja_id INT NULL")

        for sql in [
            """CREATE TABLE IF NOT EXISTS roles (id INT AUTO_INCREMENT PRIMARY KEY,
               nombre VARCHAR(80) NOT NULL UNIQUE, descripcion VARCHAR(255),
               color VARCHAR(20) DEFAULT '#3b82f6', activo TINYINT(1) DEFAULT 1,
               creado_en DATETIME DEFAULT CURRENT_TIMESTAMP)""",
            """CREATE TABLE IF NOT EXISTS permisos_catalogo (clave VARCHAR(80) PRIMARY KEY,
               nombre VARCHAR(120) NOT NULL, modulo VARCHAR(60) NOT NULL, descripcion VARCHAR(255))""",
            """CREATE TABLE IF NOT EXISTS permisos_roles (rol_id INT NOT NULL,
               permiso_clave VARCHAR(80) NOT NULL, PRIMARY KEY (rol_id, permiso_clave),
               FOREIGN KEY (rol_id) REFERENCES roles(id) ON DELETE CASCADE)""",
            """CREATE TABLE IF NOT EXISTS caja_sesiones (id INT AUTO_INCREMENT PRIMARY KEY,
               usuario_id INT, fondo_inicial DECIMAL(10,2) DEFAULT 0,
               fecha_apertura DATETIME DEFAULT CURRENT_TIMESTAMP, fecha_cierre DATETIME,
               total_efectivo DECIMAL(10,2) DEFAULT 0, total_tarjeta DECIMAL(10,2) DEFAULT 0,
               total_transferencia DECIMAL(10,2) DEFAULT 0, total_ventas INT DEFAULT 0,
               estado ENUM('abierta','cerrada') DEFAULT 'abierta', notas_cierre TEXT,
               FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL)""",
            """CREATE TABLE IF NOT EXISTS caja_movimientos (id INT AUTO_INCREMENT PRIMARY KEY,
               sesion_id INT NOT NULL, tipo ENUM('entrada','salida') NOT NULL,
               monto DECIMAL(10,2) NOT NULL, concepto VARCHAR(255), usuario_id INT,
               fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
               FOREIGN KEY (sesion_id) REFERENCES caja_sesiones(id) ON DELETE CASCADE,
               FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL)""",
            """CREATE TABLE IF NOT EXISTS ajustes_inventario (id INT AUTO_INCREMENT PRIMARY KEY,
               producto_id INT NOT NULL, usuario_id INT,
               tipo ENUM('entrada','salida','ajuste','merma','devolucion') NOT NULL,
               cantidad_anterior DECIMAL(10,2), cantidad_nueva DECIMAL(10,2),
               diferencia DECIMAL(10,2), motivo VARCHAR(255), notas TEXT,
               fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
               FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE,
               FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL)""",
        ]:
            db.execute_query(sql)

        print("✅ Tablas verificadas/creadas.")

        PERMISOS = [
            ("ventas_ver","Ver ventas","Ventas",""),("ventas_cobrar","Cobrar","Ventas",""),
            ("ventas_descuento","Descuentos","Ventas",""),("ventas_devolucion","Devoluciones","Ventas",""),
            ("ventas_cancelar","Cancelar ventas","Ventas",""),
            ("caja_abrir","Abrir caja","Caja",""),("caja_cerrar","Cerrar caja","Caja",""),
            ("caja_movimientos","Movimientos","Caja",""),("caja_historial","Historial","Caja",""),
            ("inventario_ver","Ver inventario","Inventario",""),
            ("inventario_editar","Editar inventario","Inventario",""),
            ("inventario_ajuste","Ajustes","Inventario",""),
            ("entradas_ver","Ver entradas","Inventario",""),
            ("entradas_editar","Registrar entradas","Inventario",""),
            ("categorias_ver","Ver categorías","Catálogos",""),
            ("categorias_editar","Editar categorías","Catálogos",""),
            ("clientes_ver","Ver clientes","Clientes",""),
            ("clientes_editar","Editar clientes","Clientes",""),
            ("clientes_credito","Crédito","Clientes",""),
            ("clientes_estado_cuenta","Estado de cuenta","Clientes",""),
            ("proveedores_ver","Ver proveedores","Proveedores",""),
            ("proveedores_editar","Editar proveedores","Proveedores",""),
            ("reportes_ver","Ver reportes","Reportes",""),
            ("reportes_ver_todos","Todos los reportes","Reportes",""),
            ("reportes_exportar","Exportar","Reportes",""),
            ("roles_gestionar","Gestionar roles","Administración",""),
            ("usuarios_gestionar","Gestionar usuarios","Administración",""),
            ("config_ver","Ver configuración","Administración",""),
            ("config_editar","Editar configuración","Administración",""),
        ]
        for clave, nombre, modulo, desc in PERMISOS:
            db.execute_query(
                "INSERT IGNORE INTO permisos_catalogo(clave,nombre,modulo,descripcion) VALUES(%s,%s,%s,%s)",
                (clave, nombre, modulo, desc))
        print(f"✅ {len(PERMISOS)} permisos verificados en catálogo.")

        ROLES = {
            "Administrador": {"color":"#dc2626","perms": None},
            "Supervisor":    {"color":"#7c3aed","perms":[
                "ventas_ver","ventas_cobrar","ventas_descuento","ventas_devolucion","ventas_cancelar",
                "caja_abrir","caja_cerrar","caja_movimientos","caja_historial",
                "inventario_ver","inventario_editar","inventario_ajuste",
                "categorias_ver","clientes_ver","clientes_editar","proveedores_ver",
                "reportes_ver","reportes_ver_todos","reportes_exportar"]},
            "Cajero":        {"color":"#2563eb","perms":[
                "ventas_ver","ventas_cobrar","ventas_descuento",
                "caja_abrir","caja_cerrar","caja_movimientos",
                "inventario_ver","clientes_ver","reportes_ver"]},
            "Almacenista":   {"color":"#059669","perms":[
                "ventas_ver","inventario_ver","inventario_editar","inventario_ajuste",
                "categorias_ver","categorias_editar","proveedores_ver","proveedores_editar",
                "entradas_ver","entradas_editar","reportes_ver"]},
        }

        for rol_nombre, datos in ROLES.items():
            existente = db.fetch_one("SELECT id FROM roles WHERE nombre=%s", (rol_nombre,))
            if not existente:
                cur = db.execute_query(
                    "INSERT INTO roles(nombre,color) VALUES(%s,%s)",
                    (rol_nombre, datos["color"]))
                rol_id = cur.lastrowid
            else:
                rol_id = existente["id"]
            if datos["perms"] is None:
                todos = db.fetch_all("SELECT clave FROM permisos_catalogo")
                perms = [p["clave"] for p in todos]
            else:
                perms = datos["perms"]
            for p in perms:
                db.execute_query(
                    "INSERT IGNORE INTO permisos_roles(rol_id,permiso_clave) VALUES(%s,%s)",
                    (rol_id, p))
        print("✅ Roles base verificados.")

        admin_user = db.fetch_one("SELECT id,rol_id FROM usuarios WHERE usuario='admin'")
        admin_rol  = db.fetch_one("SELECT id FROM roles WHERE nombre='Administrador'")
        if admin_user and admin_rol and not admin_user.get("rol_id"):
            db.execute_query("UPDATE usuarios SET rol_id=%s WHERE usuario='admin'",
                             (admin_rol["id"],))
        print("✅ Sistema de roles verificado completamente.\n")

    except Exception as e:
        import traceback
        print(f"[ERROR] Error en _migrar_sistema: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    db = Database.get_instance()
    if db.connection is None:
        print("[ERROR] No se pudo conectar a MySQL. Verifica que MySQL este activo.")
        exit(1)

    from app.models.caja_model import CajaModel
    _caja = CajaModel()

    print("🔧 Verificando estructura del sistema...")
    _migrar_sistema()

    _caja.reparar_sesion_caja_id()

    _n = _caja.cerrar_sesiones_dia_anterior()
    if _n:
        print(f"🔒 {_n} sesión(es) de caja cerradas automáticamente.")

    _iniciar_app()
