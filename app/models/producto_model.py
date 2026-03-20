from app.database.connection import Database


class ProductoModel:
    def __init__(self):
        self.db = Database.get_instance()

    def get_all(self, solo_activos=True):
        q = """
            SELECT p.*, c.nombre AS categoria_nombre
            FROM productos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE p.activo = %s
            ORDER BY p.nombre
        """
        return self.db.fetch_all(q, (1 if solo_activos else 0,))

    def get_by_id(self, id):
        return self.db.fetch_one("SELECT * FROM productos WHERE id = %s", (id,))

    def get_by_codigo(self, codigo):
        return self.db.fetch_one(
            "SELECT * FROM productos WHERE codigo_barras = %s AND activo = 1", (codigo,))

    def buscar(self, termino):
        t = f"%{termino}%"
        q = """
            SELECT p.*, c.nombre AS categoria_nombre
            FROM productos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE p.activo = 1 AND (p.nombre LIKE %s OR p.codigo_barras LIKE %s OR p.clave_interna LIKE %s)
            ORDER BY p.nombre LIMIT 50
        """
        return self.db.fetch_all(q, (t, t, t))

    def crear(self, data: dict):
        q = """
            INSERT INTO productos
            (codigo_barras, clave_interna, nombre, descripcion, categoria_id,
             proveedor_id, precio_costo, precio_venta, precio_mayoreo,
             existencia, existencia_min, unidad, aplica_iva)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        cur = self.db.execute_query(q, (
            data.get("codigo_barras"), data.get("clave_interna"), data["nombre"],
            data.get("descripcion"), data.get("categoria_id"), data.get("proveedor_id"),
            data.get("precio_costo", 0), data["precio_venta"], data.get("precio_mayoreo"),
            data.get("existencia", 0), data.get("existencia_min", 0),
            data.get("unidad", "PZA"), data.get("aplica_iva", 0)
        ))
        new_id = cur.lastrowid
        cur.close()
        return new_id

    def actualizar(self, id, data: dict):
        q = """
            UPDATE productos SET
                codigo_barras=%s, clave_interna=%s, nombre=%s, descripcion=%s,
                categoria_id=%s, proveedor_id=%s, precio_costo=%s, precio_venta=%s,
                precio_mayoreo=%s, existencia_min=%s, unidad=%s, aplica_iva=%s
            WHERE id=%s
        """
        self.db.execute_query_safe(q, (
            data.get("codigo_barras"), data.get("clave_interna"), data["nombre"],
            data.get("descripcion"), data.get("categoria_id"), data.get("proveedor_id"),
            data.get("precio_costo", 0), data["precio_venta"], data.get("precio_mayoreo"),
            data.get("existencia_min", 0), data.get("unidad", "PZA"), data.get("aplica_iva", 0),
            id
        ))

    def actualizar_existencia(self, id, cantidad):
        self.db.execute_query_safe(
            "UPDATE productos SET existencia = existencia + %s WHERE id = %s", (cantidad, id))

    def eliminar(self, id):
        self.db.execute_query_safe("UPDATE productos SET activo = 0 WHERE id = %s", (id,))

    def get_categorias(self):
        return self.db.fetch_all("SELECT * FROM categorias WHERE activo=1 ORDER BY nombre")

    def stock_bajo(self):
        return self.db.fetch_all(
            "SELECT * FROM productos WHERE activo=1 AND existencia <= existencia_min ORDER BY existencia")
