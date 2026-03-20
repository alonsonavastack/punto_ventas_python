from app.database.connection import Database
import hashlib


class RolModel:
    def __init__(self):
        self.db = Database.get_instance()

    def get_all(self):
        return self.db.fetch_all("SELECT * FROM roles WHERE activo=1 ORDER BY nombre")

    def get_by_id(self, id):
        rol = self.db.fetch_one("SELECT * FROM roles WHERE id=%s", (id,))
        if rol:
            perms = self.db.fetch_all(
                "SELECT permiso_clave FROM permisos_roles WHERE rol_id=%s", (id,))
            rol["permisos"] = [p["permiso_clave"] for p in perms]
        return rol

    def get_permisos_catalogo(self):
        return self.db.fetch_all("SELECT * FROM permisos_catalogo ORDER BY modulo, nombre")

    def get_permisos_by_modulo(self):
        perms = self.get_permisos_catalogo()
        modulos = {}
        for p in perms:
            modulos.setdefault(p["modulo"], []).append(p)
        return modulos

    def crear(self, nombre, descripcion, color, permisos: list):
        cur = self.db.execute_query(
            "INSERT INTO roles(nombre,descripcion,color) VALUES(%s,%s,%s)",
            (nombre, descripcion, color))
        rol_id = cur.lastrowid
        cur.close()
        for p in permisos:
            self.db.execute_query_safe(
                "INSERT IGNORE INTO permisos_roles(rol_id,permiso_clave) VALUES(%s,%s)",
                (rol_id, p))
        return rol_id

    def actualizar(self, id, nombre, descripcion, color, permisos: list):
        self.db.execute_query_safe(
            "UPDATE roles SET nombre=%s,descripcion=%s,color=%s WHERE id=%s",
            (nombre, descripcion, color, id))
        self.db.execute_query_safe(
            "DELETE FROM permisos_roles WHERE rol_id=%s", (id,))
        for p in permisos:
            self.db.execute_query_safe(
                "INSERT IGNORE INTO permisos_roles(rol_id,permiso_clave) VALUES(%s,%s)",
                (id, p))

    def eliminar(self, id):
        self.db.execute_query_safe("UPDATE roles SET activo=0 WHERE id=%s", (id,))


class UsuarioModel:
    def __init__(self):
        self.db = Database.get_instance()

    def _hash(self, p):
        return hashlib.sha256(p.encode()).hexdigest()

    def get_all(self):
        return self.db.fetch_all("""
            SELECT u.*, r.nombre AS rol_nombre, r.color AS rol_color
            FROM usuarios u LEFT JOIN roles r ON u.rol_id=r.id
            WHERE u.activo=1 ORDER BY u.nombre
        """)

    def get_by_id(self, id):
        return self.db.fetch_one("""
            SELECT u.*, r.nombre AS rol_nombre
            FROM usuarios u LEFT JOIN roles r ON u.rol_id=r.id WHERE u.id=%s
        """, (id,))

    def crear(self, nombre, usuario, password, rol_id):
        self.db.execute_query_safe(
            "INSERT INTO usuarios(nombre,usuario,password,rol_id) VALUES(%s,%s,%s,%s)",
            (nombre, usuario, self._hash(password), rol_id))

    def actualizar(self, id, nombre, usuario, rol_id, password=None):
        if password:
            self.db.execute_query_safe(
                "UPDATE usuarios SET nombre=%s,usuario=%s,rol_id=%s,password=%s WHERE id=%s",
                (nombre, usuario, rol_id, self._hash(password), id))
        else:
            self.db.execute_query_safe(
                "UPDATE usuarios SET nombre=%s,usuario=%s,rol_id=%s WHERE id=%s",
                (nombre, usuario, rol_id, id))

    def eliminar(self, id):
        self.db.execute_query_safe("UPDATE usuarios SET activo=0 WHERE id=%s", (id,))
