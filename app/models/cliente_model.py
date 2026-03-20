from app.database.connection import Database


class ClienteModel:
    def __init__(self):
        self.db = Database.get_instance()

    def get_all(self):
        return self.db.fetch_all(
            "SELECT * FROM clientes WHERE activo=1 ORDER BY nombre")

    def get_by_id(self, id):
        return self.db.fetch_one("SELECT * FROM clientes WHERE id=%s", (id,))

    def buscar(self, termino):
        t = f"%{termino}%"
        return self.db.fetch_all(
            "SELECT * FROM clientes WHERE activo=1 AND (nombre LIKE %s OR telefono LIKE %s) LIMIT 20",
            (t, t))

    def crear(self, data: dict):
        q = """
            INSERT INTO clientes (nombre, telefono, email, direccion, rfc, limite_credito)
            VALUES (%s,%s,%s,%s,%s,%s)
        """
        cur = self.db.execute_query(q, (
            data["nombre"], data.get("telefono"), data.get("email"),
            data.get("direccion"), data.get("rfc"), data.get("limite_credito", 0)
        ))
        new_id = cur.lastrowid
        cur.close()
        return new_id

    def actualizar(self, id, data: dict):
        q = """
            UPDATE clientes SET nombre=%s, telefono=%s, email=%s,
            direccion=%s, rfc=%s, limite_credito=%s WHERE id=%s
        """
        self.db.execute_query_safe(q, (
            data["nombre"], data.get("telefono"), data.get("email"),
            data.get("direccion"), data.get("rfc"), data.get("limite_credito", 0), id
        ))

    def eliminar(self, id):
        self.db.execute_query_safe("UPDATE clientes SET activo=0 WHERE id=%s", (id,))

    def historial_compras(self, cliente_id):
        return self.db.fetch_all("""
            SELECT v.folio, v.fecha, v.total, v.forma_pago, v.estado
            FROM ventas v WHERE v.cliente_id=%s ORDER BY v.fecha DESC LIMIT 50
        """, (cliente_id,))
