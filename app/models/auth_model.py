from app.database.connection import Database
from app.utils import session
import hashlib
import os


class AuthModel:
    def __init__(self):
        self.db = Database.get_instance()

    def _hash(self, password: str, salt: str = "") -> str:
        """
        Bug #9 corregido: si hay salt almacenado se usa; si no (passwords antiguos
        sin salt) se sigue usando SHA-256 puro para compatibilidad hacia atrás.
        Para nuevos usuarios o cambios de contraseña se debe llamar _hash_con_salt.
        """
        if salt:
            return hashlib.sha256((salt + password).encode()).hexdigest()
        return hashlib.sha256(password.encode()).hexdigest()

    def _hash_con_salt(self, password: str) -> tuple[str, str]:
        """Genera un salt aleatorio y devuelve (hash, salt)."""
        salt = os.urandom(16).hex()
        h = hashlib.sha256((salt + password).encode()).hexdigest()
        return h, salt

    def login(self, usuario_str: str, password: str):
        user = self.db.fetch_one("""
            SELECT u.*,
                   r.nombre AS rol_nombre,
                   r.color  AS rol_color
            FROM usuarios u
            LEFT JOIN roles r ON u.rol_id = r.id
            WHERE u.usuario = %s AND u.activo = 1
        """, (usuario_str,))

        if not user:
            return None, "Usuario no encontrado"

        # Soporte para passwords con salt (campo password_salt) y sin salt (legacy)
        salt = user.get("password_salt") or ""
        if user["password"] != self._hash(password, salt):
            return None, "Contraseña incorrecta"

        perms = []
        if user.get("rol_id"):
            rows = self.db.fetch_all(
                "SELECT permiso_clave FROM permisos_roles WHERE rol_id = %s",
                (user["rol_id"],))
            perms = [p["permiso_clave"] for p in rows]

        if not perms and user.get("rol"):
            rol_viejo = (user.get("rol") or "").lower()
            if rol_viejo == "admin":
                perms = _permisos_admin_legacy()
            elif rol_viejo == "cajero":
                perms = _permisos_cajero_legacy()
            elif rol_viejo == "almacen":
                perms = _permisos_almacen_legacy()

        user["permisos"] = perms
        session.login(user)
        return user, None


# ── Permisos de compatibilidad para el esquema viejo (campo rol ENUM) ─────────
def _permisos_admin_legacy():
    return [
        "ventas_ver","ventas_cobrar","ventas_descuento","ventas_devolucion","ventas_cancelar",
        "caja_abrir","caja_cerrar","caja_movimientos","caja_historial",
        "inventario_ver","inventario_editar","inventario_ajuste",
        "categorias_ver","categorias_editar",
        "clientes_ver","clientes_editar",
        "proveedores_ver","proveedores_editar",
        "reportes_ver","reportes_ver_todos","reportes_exportar",
        "roles_gestionar","usuarios_gestionar",
        "config_ver","config_editar",
    ]

def _permisos_cajero_legacy():
    return [
        "ventas_ver","ventas_cobrar","ventas_descuento",
        "caja_abrir","caja_cerrar","caja_movimientos",
        "inventario_ver",
        "clientes_ver",
        "reportes_ver",
    ]

def _permisos_almacen_legacy():
    return [
        "ventas_ver",
        "inventario_ver","inventario_editar","inventario_ajuste",
        "categorias_ver","categorias_editar",
        "proveedores_ver","proveedores_editar",
        "reportes_ver",
    ]
