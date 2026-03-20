from app.database.connection import Database


class ProveedorModel:
    def __init__(self):
        self.db = Database.get_instance()

    def get_all(self):
        return self.db.fetch_all(
            "SELECT * FROM proveedores WHERE activo=1 ORDER BY nombre")

    def get_by_id(self, id):
        return self.db.fetch_one("SELECT * FROM proveedores WHERE id=%s", (id,))

    def crear(self, data: dict):
        q = """
            INSERT INTO proveedores (nombre, contacto, telefono, email, direccion, rfc)
            VALUES (%s,%s,%s,%s,%s,%s)
        """
        cur = self.db.execute_query(q, (
            data["nombre"], data.get("contacto"), data.get("telefono"),
            data.get("email"), data.get("direccion"), data.get("rfc")
        ))
        new_id = cur.lastrowid
        cur.close()
        return new_id

    def actualizar(self, id, data: dict):
        q = """
            UPDATE proveedores SET nombre=%s, contacto=%s, telefono=%s,
            email=%s, direccion=%s, rfc=%s WHERE id=%s
        """
        self.db.execute_query_safe(q, (
            data["nombre"], data.get("contacto"), data.get("telefono"),
            data.get("email"), data.get("direccion"), data.get("rfc"), id
        ))

    def eliminar(self, id):
        self.db.execute_query_safe("UPDATE proveedores SET activo=0 WHERE id=%s", (id,))

    def registrar_entrada(self, proveedor_id, items: list, usuario_id=None, notas=""):
        from datetime import datetime
        hoy = datetime.now().strftime("%Y%m%d")
        res = self.db.fetch_one("SELECT COUNT(*) AS t FROM entradas WHERE DATE(fecha)=CURDATE()")
        num = (res["t"] if res else 0) + 1
        folio = f"E{hoy}{num:04d}"
        total = sum(i["costo_unit"] * i["cantidad"] for i in items)

        cur = self.db.execute_query("""
            INSERT INTO entradas (folio, proveedor_id, usuario_id, total, notas)
            VALUES (%s,%s,%s,%s,%s)
        """, (folio, proveedor_id, usuario_id, total, notas))
        entrada_id = cur.lastrowid
        cur.close()

        for item in items:
            self.db.execute_query_safe("""
                INSERT INTO detalle_entradas (entrada_id, producto_id, cantidad, costo_unit, subtotal)
                VALUES (%s,%s,%s,%s,%s)
            """, (entrada_id, item["producto_id"], item["cantidad"],
                  item["costo_unit"], item["costo_unit"] * item["cantidad"]))
            self.db.execute_query_safe(
                "UPDATE productos SET existencia = existencia + %s WHERE id=%s",
                (item["cantidad"], item["producto_id"]))

        return {"id": entrada_id, "folio": folio, "total": total}
