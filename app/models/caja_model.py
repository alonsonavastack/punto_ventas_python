from app.database.connection import Database
from app.utils import session as sess
from datetime import datetime

class CajaModel:
    def __init__(self):
        self.db = Database.get_instance()

    # ── Reparar ventas sin sesion_caja_id ──────────────────────────────────
    def reparar_sesion_caja_id(self):
        try:
            # Bug #5 corregido: usar execute_query_safe para queries sin retorno
            self.db.execute_query_safe("""
                UPDATE ventas v
                JOIN caja_sesiones cs
                  ON v.fecha >= cs.fecha_apertura
                 AND (v.fecha <= cs.fecha_cierre OR cs.estado = 'abierta')
                SET v.sesion_caja_id = cs.id
                WHERE v.sesion_caja_id IS NULL
                  AND v.estado = 'completada'
            """)
        except Exception as e:
            print(f"⚠ reparar_sesion_caja_id: {e}")

    # ── Cierre automático de sesiones de días anteriores ──────────────────
    def cerrar_sesiones_dia_anterior(self):
        sesiones_viejas = self.db.fetch_all("""
            SELECT * FROM caja_sesiones
            WHERE estado = 'abierta'
              AND DATE(fecha_apertura) < CURDATE()
        """)

        cerradas = 0
        for sesion in sesiones_viejas:
            sid = sesion["id"]
            totales = self.db.fetch_one("""
                SELECT
                    COALESCE(SUM(CASE forma_pago WHEN 'efectivo'      THEN total ELSE 0 END),0) AS ef,
                    COALESCE(SUM(CASE forma_pago WHEN 'tarjeta'       THEN total ELSE 0 END),0) AS tj,
                    COALESCE(SUM(CASE forma_pago WHEN 'transferencia' THEN total ELSE 0 END),0) AS tr,
                    COUNT(*) AS num
                FROM ventas
                WHERE sesion_caja_id = %s AND estado = 'completada'
            """, (sid,))
            # Bug #5 corregido: execute_query_safe para UPDATE sin necesitar cursor
            self.db.execute_query_safe("""
                UPDATE caja_sesiones SET
                    estado          = 'cerrada',
                    fecha_cierre    = CONCAT(DATE(fecha_apertura), ' 23:59:59'),
                    total_efectivo  = %s,
                    total_tarjeta   = %s,
                    total_transferencia = %s,
                    total_ventas    = %s,
                    notas_cierre    = 'Cierre automático — sesión de día anterior'
                WHERE id = %s
            """, (totales["ef"], totales["tj"], totales["tr"], totales["num"], sid))
            cerradas += 1
            print(f"✅ Sesión {sid} cerrada automáticamente (día anterior)")

        return cerradas

    def get_sesion_activa(self, usuario_id=None):
        if usuario_id:
            return self.db.fetch_one(
                "SELECT * FROM caja_sesiones WHERE usuario_id=%s AND estado='abierta' ORDER BY fecha_apertura DESC LIMIT 1",
                (usuario_id,))
        return self.db.fetch_one(
            "SELECT * FROM caja_sesiones WHERE estado='abierta' ORDER BY fecha_apertura DESC LIMIT 1")

    def abrir(self, fondo_inicial: float, usuario_id: int):
        # execute_query devuelve el cursor para poder usar lastrowid
        cur = self.db.execute_query(
            "INSERT INTO caja_sesiones(usuario_id,fondo_inicial) VALUES(%s,%s)",
            (usuario_id, fondo_inicial))
        new_id = cur.lastrowid
        try:
            cur.close()
        except Exception:
            pass
        sesion = self.db.fetch_one("SELECT * FROM caja_sesiones WHERE id=%s", (new_id,))
        sess.set_sesion_caja(sesion)
        return sesion

    def cerrar(self, sesion_id: int, notas: str = ""):
        totales = self.db.fetch_one("""
            SELECT
                COALESCE(SUM(CASE forma_pago WHEN 'efectivo'      THEN total ELSE 0 END),0) AS ef,
                COALESCE(SUM(CASE forma_pago WHEN 'tarjeta'       THEN total ELSE 0 END),0) AS tj,
                COALESCE(SUM(CASE forma_pago WHEN 'transferencia' THEN total ELSE 0 END),0) AS tr,
                COUNT(*) AS num
            FROM ventas WHERE sesion_caja_id=%s AND estado='completada'
        """, (sesion_id,))
        # Bug #5 corregido: execute_query_safe para UPDATE sin necesitar cursor
        self.db.execute_query_safe("""
            UPDATE caja_sesiones SET
                estado='cerrada', fecha_cierre=NOW(),
                total_efectivo=%s, total_tarjeta=%s, total_transferencia=%s,
                total_ventas=%s, notas_cierre=%s
            WHERE id=%s
        """, (totales["ef"], totales["tj"], totales["tr"], totales["num"], notas, sesion_id))
        sess.set_sesion_caja(None)

    def registrar_movimiento(self, sesion_id, tipo, monto, concepto, usuario_id):
        # Bug #5 corregido: execute_query_safe para INSERT sin necesitar cursor
        self.db.execute_query_safe(
            "INSERT INTO caja_movimientos(sesion_id,tipo,monto,concepto,usuario_id) VALUES(%s,%s,%s,%s,%s)",
            (sesion_id, tipo, monto, concepto, usuario_id))

    def get_movimientos(self, sesion_id):
        return self.db.fetch_all("""
            SELECT cm.*, u.nombre AS usuario_nombre
            FROM caja_movimientos cm
            LEFT JOIN usuarios u ON cm.usuario_id = u.id
            WHERE cm.sesion_id = %s
            ORDER BY cm.fecha
        """, (sesion_id,))

    def get_sesiones_historico(self, fecha_ini=None, fecha_fin=None, usuario_id=None):
        filtros = ["cs.estado = 'cerrada'"]
        params  = []
        if fecha_ini:
            filtros.append("DATE(cs.fecha_apertura) >= %s")
            params.append(fecha_ini)
        if fecha_fin:
            filtros.append("DATE(cs.fecha_apertura) <= %s")
            params.append(fecha_fin)
        if usuario_id:
            filtros.append("cs.usuario_id = %s")
            params.append(usuario_id)
        where = " AND ".join(filtros)
        return self.db.fetch_all(f"""
            SELECT cs.*,
                   u.nombre AS cajero_nombre,
                   COALESCE((
                       SELECT SUM(total) FROM ventas
                       WHERE sesion_caja_id = cs.id AND estado = 'completada'
                   ), 0) AS ventas_total,
                   COALESCE((
                       SELECT COUNT(*) FROM ventas
                       WHERE sesion_caja_id = cs.id AND estado = 'completada'
                   ), 0) AS ventas_num
            FROM caja_sesiones cs
            LEFT JOIN usuarios u ON cs.usuario_id = u.id
            WHERE {where}
            ORDER BY cs.fecha_apertura DESC
        """, tuple(params))

    def get_cajeros(self):
        return self.db.fetch_all("""
            SELECT DISTINCT u.id, u.nombre
            FROM caja_sesiones cs
            JOIN usuarios u ON cs.usuario_id = u.id
            ORDER BY u.nombre
        """)

    def get_resumen_sesion(self, sesion_id):
        return self.db.fetch_one("""
            SELECT cs.*,
                COALESCE((
                    SELECT SUM(CASE forma_pago WHEN 'efectivo' THEN total ELSE 0 END)
                    FROM ventas
                    WHERE sesion_caja_id = cs.id AND estado = 'completada'
                ), 0) AS total_efectivo,
                COALESCE((
                    SELECT SUM(CASE forma_pago WHEN 'tarjeta' THEN total ELSE 0 END)
                    FROM ventas
                    WHERE sesion_caja_id = cs.id AND estado = 'completada'
                ), 0) AS total_tarjeta,
                COALESCE((
                    SELECT SUM(CASE forma_pago WHEN 'transferencia' THEN total ELSE 0 END)
                    FROM ventas
                    WHERE sesion_caja_id = cs.id AND estado = 'completada'
                ), 0) AS total_transferencia,
                COALESCE((
                    SELECT COUNT(*)
                    FROM ventas
                    WHERE sesion_caja_id = cs.id AND estado = 'completada'
                ), 0) AS total_ventas,
                COALESCE((
                    SELECT SUM(monto) FROM caja_movimientos
                    WHERE sesion_id = cs.id AND tipo = 'entrada' AND monto > 0
                ), 0) AS entradas_extra,
                COALESCE((
                    SELECT SUM(monto) FROM caja_movimientos
                    WHERE sesion_id = cs.id AND tipo = 'salida'
                ), 0) AS salidas_extra
            FROM caja_sesiones cs
            WHERE cs.id = %s
        """, (sesion_id,))
