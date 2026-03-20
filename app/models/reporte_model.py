from app.database.connection import Database


class ReporteModel:
    def __init__(self):
        self.db = Database.get_instance()

    # ── Resumen general (siempre TODOS los usuarios) ──────────────────────────
    def resumen_general(self, fecha_ini, fecha_fin):
        return self.db.fetch_one("""
            SELECT
                COUNT(*)                                                        AS total_ventas,
                COALESCE(SUM(total), 0)                                         AS ingresos_total,
                COALESCE(AVG(total), 0)                                         AS ticket_promedio,
                COALESCE(SUM(CASE forma_pago WHEN 'efectivo'      THEN total ELSE 0 END), 0) AS efectivo,
                COALESCE(SUM(CASE forma_pago WHEN 'tarjeta'       THEN total ELSE 0 END), 0) AS tarjeta,
                COALESCE(SUM(CASE forma_pago WHEN 'transferencia' THEN total ELSE 0 END), 0) AS transferencia
            FROM ventas
            WHERE DATE(fecha) BETWEEN %s AND %s
              AND estado = 'completada'
        """, (fecha_ini, fecha_fin))

    # ── Resumen propio del cajero (solo sus ventas) ───────────────────────────
    def resumen_propio(self, fecha_ini, fecha_fin, usuario_id):
        return self.db.fetch_one("""
            SELECT
                COUNT(*)                                                        AS total_ventas,
                COALESCE(SUM(total), 0)                                         AS ingresos_total,
                COALESCE(AVG(total), 0)                                         AS ticket_promedio,
                COALESCE(SUM(CASE forma_pago WHEN 'efectivo'      THEN total ELSE 0 END), 0) AS efectivo,
                COALESCE(SUM(CASE forma_pago WHEN 'tarjeta'       THEN total ELSE 0 END), 0) AS tarjeta,
                COALESCE(SUM(CASE forma_pago WHEN 'transferencia' THEN total ELSE 0 END), 0) AS transferencia
            FROM ventas
            WHERE DATE(fecha) BETWEEN %s AND %s
              AND estado     = 'completada'
              AND usuario_id = %s
        """, (fecha_ini, fecha_fin, usuario_id))

    # ── Ventas por día (siempre TODOS) ────────────────────────────────────────
    def ventas_por_periodo(self, fecha_ini, fecha_fin):
        return self.db.fetch_all("""
            SELECT DATE(fecha) AS dia,
                   COUNT(*)    AS num_ventas,
                   SUM(total)  AS total
            FROM ventas
            WHERE DATE(fecha) BETWEEN %s AND %s
              AND estado = 'completada'
            GROUP BY DATE(fecha)
            ORDER BY dia
        """, (fecha_ini, fecha_fin))

    # ── Productos más vendidos (siempre TODOS) ────────────────────────────────
    def productos_mas_vendidos(self, fecha_ini, fecha_fin, limite=10):
        return self.db.fetch_all("""
            SELECT p.nombre,
                   p.codigo_barras,
                   SUM(dv.cantidad)  AS total_cantidad,
                   SUM(dv.subtotal)  AS total_importe
            FROM detalle_ventas dv
            JOIN productos p ON dv.producto_id = p.id
            JOIN ventas v    ON dv.venta_id    = v.id
            WHERE DATE(v.fecha) BETWEEN %s AND %s
              AND v.estado = 'completada'
            GROUP BY p.id
            ORDER BY total_cantidad DESC
            LIMIT %s
        """, (fecha_ini, fecha_fin, limite))

    # ── Detalle de ventas (siempre TODOS — incluye cajero en cada fila) ───────
    def detalle_ventas_periodo(self, fecha_ini, fecha_fin):
        return self.db.fetch_all("""
            SELECT v.id,
                   v.folio,
                   DATE(v.fecha)                     AS dia,
                   TIME(v.fecha)                     AS hora,
                   v.total,
                   v.forma_pago,
                   v.descuento,
                   u.nombre                          AS cajero,
                   c.nombre                          AS cliente,
                   COALESCE(SUM(dv.cantidad), 0)     AS total_articulos
            FROM ventas v
            LEFT JOIN usuarios u         ON v.usuario_id  = u.id
            LEFT JOIN clientes c         ON v.cliente_id  = c.id
            LEFT JOIN detalle_ventas dv  ON dv.venta_id   = v.id
            WHERE DATE(v.fecha) BETWEEN %s AND %s
              AND v.estado = 'completada'
            GROUP BY v.id
            ORDER BY v.fecha DESC
        """, (fecha_ini, fecha_fin))

    # ── Resumen por cajero (para la tabla de rendimiento) ────────────────────
    def resumen_por_cajero(self, fecha_ini, fecha_fin):
        return self.db.fetch_all("""
            SELECT u.nombre                          AS cajero,
                   COUNT(v.id)                       AS total_ventas,
                   COALESCE(SUM(v.total), 0)         AS ingresos,
                   COALESCE(AVG(v.total), 0)         AS ticket_promedio
            FROM ventas v
            LEFT JOIN usuarios u ON v.usuario_id = u.id
            WHERE DATE(v.fecha) BETWEEN %s AND %s
              AND v.estado = 'completada'
            GROUP BY v.usuario_id
            ORDER BY ingresos DESC
        """, (fecha_ini, fecha_fin))

    def inventario_valorizado(self):
        return self.db.fetch_all("""
            SELECT p.nombre, p.codigo_barras, c.nombre AS categoria,
                   p.existencia, p.precio_costo, p.precio_venta,
                   (p.existencia * p.precio_costo) AS valor_costo,
                   (p.existencia * p.precio_venta) AS valor_venta
            FROM productos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
            WHERE p.activo = 1
            ORDER BY p.nombre
        """)
