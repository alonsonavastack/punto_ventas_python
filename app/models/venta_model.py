from app.database.connection import Database
from datetime import datetime
import secrets


class VentaModel:
    def __init__(self):
        self.db = Database.get_instance()

    def _generar_folio(self, cursor):
        """
        Genera el folio dentro de la transacción activa usando el cursor
        ya abierto, para evitar conflictos con start_transaction.
        """
        hoy = datetime.now().strftime("%Y%m%d")
        cursor.execute(
            "SELECT COUNT(*) AS total FROM ventas WHERE DATE(fecha) = CURDATE()")
        res = cursor.fetchone()
        num = (res["total"] if res else 0) + 1
        # sufijo 4 chars hex → 65 536 combinaciones
        sufijo = secrets.token_hex(2).upper()
        return f"V{hoy}{num:04d}{sufijo}"

    def _calcular_iva(self, items):
        """IVA desglosado 16 % solo de productos con aplica_iva=1."""
        iva = 0.0
        for item in items:
            if item.get("aplica_iva"):
                subtotal_item = item["precio_unit"] * item["cantidad"]
                iva += round(subtotal_item * 16 / 116, 4)
        return round(iva, 2)

    def crear_venta(self, items: list, forma_pago: str, monto_pagado: float,
                    cliente_id=None, usuario_id=None, descuento=0.0,
                    sesion_caja_id=None):
        from app.utils import session
        if not usuario_id:
            u = session.get_usuario()
            if u:
                usuario_id = u["id"]

        subtotal = sum(i["precio_unit"] * i["cantidad"] for i in items)
        subtotal -= descuento
        iva    = self._calcular_iva(items)
        total  = round(subtotal, 2)
        cambio = round(monto_pagado - total, 2)

        conn   = self.db.get_connection()
        cursor = None
        try:
            # Con autocommit=True, start_transaction() desactiva el autocommit
            # solo para este bloque y nunca lanza "Transaction already in progress"
            conn.start_transaction()
            cursor = conn.cursor(dictionary=True)

            folio = self._generar_folio(cursor)

            cursor.execute("""
                INSERT INTO ventas
                (folio, cliente_id, usuario_id, sesion_caja_id,
                 subtotal, descuento, iva, total, forma_pago, monto_pagado, cambio)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (folio, cliente_id, usuario_id, sesion_caja_id,
                  subtotal, descuento, iva, total, forma_pago, monto_pagado, cambio))
            venta_id = cursor.lastrowid

            for item in items:
                cursor.execute("""
                    INSERT INTO detalle_ventas
                    (venta_id, producto_id, cantidad, precio_unit, subtotal)
                    VALUES (%s,%s,%s,%s,%s)
                """, (venta_id, item["producto_id"], item["cantidad"],
                      item["precio_unit"],
                      round(item["precio_unit"] * item["cantidad"], 2)))
                cursor.execute(
                    "UPDATE productos SET existencia = existencia - %s WHERE id = %s",
                    (item["cantidad"], item["producto_id"]))

            conn.commit()
            return {"id": venta_id, "folio": folio, "total": total, "cambio": cambio}

        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            print(f"[ERROR] crear_venta: {e}")
            raise e

        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass

    def cancelar(self, venta_id):
        """Cancelación atómica: restaura stock y cambia estado en una sola transacción."""
        conn   = self.db.get_connection()
        cursor = None
        try:
            conn.start_transaction()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                "SELECT * FROM detalle_ventas WHERE venta_id = %s", (venta_id,))
            detalles = cursor.fetchall()

            for d in detalles:
                cursor.execute(
                    "UPDATE productos SET existencia = existencia + %s WHERE id = %s",
                    (d["cantidad"], d["producto_id"]))

            cursor.execute(
                "UPDATE ventas SET estado='cancelada' WHERE id=%s", (venta_id,))

            conn.commit()

        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            print(f"[ERROR] cancelar venta: {e}")
            raise e

        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    pass

    def get_ventas_hoy(self):
        return self.db.fetch_all("""
            SELECT v.*,
                   c.nombre AS cliente_nombre,
                   u.nombre AS usuario_nombre,
                   COALESCE(SUM(dv.cantidad),0) AS total_articulos
            FROM ventas v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            LEFT JOIN usuarios u ON v.usuario_id = u.id
            LEFT JOIN detalle_ventas dv ON dv.venta_id = v.id
            WHERE DATE(v.fecha) = CURDATE()
            GROUP BY v.id
            ORDER BY v.fecha DESC
        """)

    def get_detalle(self, venta_id):
        return self.db.fetch_all("""
            SELECT dv.*, p.nombre AS producto_nombre, p.codigo_barras
            FROM detalle_ventas dv
            JOIN productos p ON dv.producto_id = p.id
            WHERE dv.venta_id = %s
        """, (venta_id,))

    def get_venta(self, venta_id):
        return self.db.fetch_one("SELECT * FROM ventas WHERE id=%s", (venta_id,))

    def resumen_hoy(self):
        return self.db.fetch_one("""
            SELECT
                COUNT(*) AS total_ventas,
                COALESCE(SUM(total),0) AS ingresos,
                COALESCE(SUM(CASE forma_pago WHEN 'efectivo' THEN total ELSE 0 END),0) AS efectivo,
                COALESCE(SUM(CASE forma_pago WHEN 'tarjeta'  THEN total ELSE 0 END),0) AS tarjeta
            FROM ventas
            WHERE DATE(fecha) = CURDATE() AND estado='completada'
        """)
