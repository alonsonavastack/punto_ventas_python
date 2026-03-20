"""
reportes_view.py
Lógica de permisos:
  - TODOS ven el reporte completo (todas las ventas de todos los cajeros).
  - Si el usuario NO tiene 'reportes_ver_todos', además se le muestra
    un bloque extra "Mi resumen" con solo sus propias ventas.
  - Nadie pierde información. El cajero siempre puede ver qué vendió
    y qué vendieron sus compañeros en el mismo período.
"""
import customtkinter as ctk
from datetime import date, timedelta, datetime as _dt
from app.models.reporte_model import ReporteModel
from app.models.venta_model import VentaModel
from app.utils.config import COLORES
from app.utils import session

DIAS  = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun",
         "jul", "ago", "sep", "oct", "nov", "dic"]
FORMA_COLOR = {
    "efectivo":      "#16A34A",
    "tarjeta":       "#2563EB",
    "transferencia": "#D97706",
}


def _fmt_fecha(d):
    try:
        if hasattr(d, "weekday"):
            return f"{DIAS[d.weekday()]} {d.day} {MESES[d.month - 1]} {d.year}"
        dt = _dt.strptime(str(d), "%Y-%m-%d")
        return f"{DIAS[dt.weekday()]} {dt.day} {MESES[dt.month - 1]} {dt.year}"
    except Exception:
        return str(d)


class ReportesView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.model      = ReporteModel()
        self.venta_model = VentaModel()
        usuario = session.get_usuario()
        self._usuario_id     = usuario["id"]     if usuario else None
        self._usuario_nombre = usuario["nombre"] if usuario else ""
        # True = solo ver sus propias ventas en el resumen personal
        self._mostrar_mi_resumen = not session.tiene_permiso("reportes_ver_todos")
        self._expandidos = set()
        self._build()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build(self):
        # Encabezado
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 4))
        ctk.CTkLabel(hdr, text="📊  Reportes",
                     font=("Segoe UI", 20, "bold"),
                     text_color=COLORES["text_primary"]).pack(side="left")
        # Badge informativo (NO restrictivo)
        badge_txt = "Vista completa — todos los cajeros"
        badge_fg  = COLORES["success"]
        if self._mostrar_mi_resumen:
            badge_txt = "Vista completa + tu resumen personal"
            badge_fg  = COLORES["primary"]
        ctk.CTkLabel(hdr, text=f"  {badge_txt}  ",
                     font=("Segoe UI", 10, "bold"),
                     fg_color=badge_fg, text_color="white",
                     corner_radius=6).pack(side="left", padx=10)

        # Filtro de fechas
        filtro = ctk.CTkFrame(self, fg_color=COLORES["bg_dark"], corner_radius=10)
        filtro.pack(fill="x", padx=20, pady=4)
        hoy = date.today()
        ini = hoy - timedelta(days=30)

        ctk.CTkLabel(filtro, text="Desde:", font=("Segoe UI", 12),
                     text_color=COLORES["text_secondary"]).pack(side="left", padx=(14, 4), pady=10)
        self.entry_ini = ctk.CTkEntry(filtro, width=110, height=34)
        self.entry_ini.insert(0, str(ini))
        self.entry_ini.pack(side="left", padx=4)

        ctk.CTkLabel(filtro, text="Hasta:", font=("Segoe UI", 12),
                     text_color=COLORES["text_secondary"]).pack(side="left", padx=(12, 4))
        self.entry_fin = ctk.CTkEntry(filtro, width=110, height=34)
        self.entry_fin.insert(0, str(hoy))
        self.entry_fin.pack(side="left", padx=4)

        ctk.CTkButton(filtro, text="🔍 Generar", width=110, height=34,
                      command=self._generar).pack(side="left", padx=12)
        ctk.CTkButton(filtro, text="📥 Exportar CSV", width=130, height=34,
                      fg_color=COLORES["success"],
                      command=self._exportar_csv).pack(side="left", padx=4)

        self.resultado = ctk.CTkScrollableFrame(
            self, fg_color=COLORES["bg_dark"], corner_radius=12)
        self.resultado.pack(fill="both", expand=True, padx=20, pady=8)

        self._generar()

    # ── Generar reporte ───────────────────────────────────────────────────────
    def _generar(self):
        for w in self.resultado.winfo_children():
            w.destroy()
        self._expandidos.clear()

        fi = self.entry_ini.get().strip()
        ff = self.entry_fin.get().strip()

        # ── 1. Resumen general (TODOS los cajeros) ────────────────────────────
        self._seccion("📈  Resumen general del período")
        resumen = self.model.resumen_general(fi, ff)
        if resumen:
            self._tarjetas_resumen(resumen)

        # ── 2. Mi resumen personal (solo si no tiene permiso total) ───────────
        if self._mostrar_mi_resumen and self._usuario_id:
            self._seccion(f"👤  Mi resumen — {self._usuario_nombre}")
            mi_res = self.model.resumen_propio(fi, ff, self._usuario_id)
            if mi_res:
                self._tarjetas_resumen(mi_res, color_acento=COLORES["primary"])
            else:
                self._sin_datos("Sin ventas propias en el período.")

        # ── 3. Rendimiento por cajero (solo admins lo ven) ───────────────────
        if not self._mostrar_mi_resumen:
            self._seccion("🏅  Rendimiento por cajero")
            cajeros = self.model.resumen_por_cajero(fi, ff)
            self._tabla_cajeros(cajeros)

        # ── 4. Productos más vendidos (TODOS) ─────────────────────────────────
        self._seccion("🏆  Productos más vendidos")
        top = self.model.productos_mas_vendidos(fi, ff)
        self._tabla_simple(
            top, ["nombre", "total_cantidad", "total_importe"],
            ["Producto", "Cantidad", "Importe"])

        # ── 5. Ventas por día (TODOS) ──────────────────────────────────────────
        self._seccion("📅  Ventas por día")
        dias = self.model.ventas_por_periodo(fi, ff)
        self._tabla_simple(
            dias, ["dia", "num_ventas", "total"],
            ["Fecha", "Ventas", "Total"])

        # ── 6. Detalle de ventas (TODOS — con cajero visible en cada fila) ────
        self._seccion("🧾  Detalle de ventas (todos los cajeros)")
        detalle = self.model.detalle_ventas_periodo(fi, ff)
        self._tabla_detalle_ventas(detalle)

    # ── Widgets de resumen ────────────────────────────────────────────────────
    def _tarjetas_resumen(self, r, color_acento=None):
        row = ctk.CTkFrame(self.resultado, fg_color="transparent")
        row.pack(fill="x", pady=6)
        datos = [
            ("Total ventas",  str(r.get("total_ventas", 0)),
             color_acento or COLORES["primary"]),
            ("Ingresos",      f"${float(r.get('ingresos_total', 0)):.2f}",
             COLORES["success"]),
            ("Ticket prom.",  f"${float(r.get('ticket_promedio', 0)):.2f}",
             COLORES["warning"]),
            ("Efectivo",      f"${float(r.get('efectivo', 0)):.2f}",
             COLORES["text_primary"]),
            ("Tarjeta",       f"${float(r.get('tarjeta', 0)):.2f}",
             COLORES["text_primary"]),
            ("Transferencia", f"${float(r.get('transferencia', 0)):.2f}",
             COLORES["text_primary"]),
        ]
        for lbl, val, color in datos:
            card = ctk.CTkFrame(row, fg_color=COLORES["bg_card"],
                                corner_radius=10, width=130)
            card.pack(side="left", padx=5)
            ctk.CTkLabel(card, text=val, font=("Segoe UI", 15, "bold"),
                         text_color=color).pack(padx=10, pady=(10, 2))
            ctk.CTkLabel(card, text=lbl, font=("Segoe UI", 9),
                         text_color=COLORES["text_secondary"]).pack(padx=10, pady=(0, 10))

    def _tabla_cajeros(self, cajeros):
        if not cajeros:
            self._sin_datos("Sin ventas en el período.")
            return
        tabla = ctk.CTkFrame(self.resultado, fg_color=COLORES["bg_card"], corner_radius=8)
        tabla.pack(fill="x", padx=8, pady=4)
        hdr = ctk.CTkFrame(tabla, fg_color=COLORES["primary"], corner_radius=6, height=30)
        hdr.pack(fill="x", padx=4, pady=4)
        for txt, w in [("Cajero", 200), ("Ventas", 100),
                       ("Ingresos", 130), ("Ticket prom.", 130)]:
            ctk.CTkLabel(hdr, text=txt, font=("Segoe UI", 10, "bold"),
                         text_color="white", width=w, anchor="w"
                         ).pack(side="left", padx=6, pady=2)
        for i, c in enumerate(cajeros):
            bg = COLORES["bg_input"] if i % 2 == 0 else "transparent"
            row = ctk.CTkFrame(tabla, fg_color=bg, corner_radius=4, height=30)
            row.pack(fill="x", padx=4, pady=1)
            for txt, w, color in [
                (c.get("cajero") or "—",                      200, COLORES["text_primary"]),
                (str(c.get("total_ventas", 0)),                100, COLORES["text_primary"]),
                (f"${float(c.get('ingresos', 0)):.2f}",        130, COLORES["success"]),
                (f"${float(c.get('ticket_promedio', 0)):.2f}", 130, COLORES["warning"]),
            ]:
                ctk.CTkLabel(row, text=txt, font=("Segoe UI", 11),
                             text_color=color, width=w, anchor="w"
                             ).pack(side="left", padx=6)

    # ── Tabla detalle de ventas expandible ────────────────────────────────────
    def _tabla_detalle_ventas(self, ventas):
        if not ventas:
            self._sin_datos("Sin ventas en el período.")
            return

        contenedor = ctk.CTkFrame(self.resultado, fg_color=COLORES["bg_card"],
                                  corner_radius=8)
        contenedor.pack(fill="x", padx=8, pady=4)

        # Cabecera
        hdr = ctk.CTkFrame(contenedor, fg_color=COLORES["primary"],
                           corner_radius=6, height=30)
        hdr.pack(fill="x", padx=4, pady=4)
        ctk.CTkLabel(hdr, text="", width=24, text_color="white",
                     font=("Segoe UI", 10)).pack(side="left", padx=2)
        for txt, w in [("Folio", 140), ("Fecha", 120), ("Hora", 65),
                       ("Cajero", 130), ("Cliente", 130),
                       ("Arts.", 50), ("Forma pago", 110), ("Total", 90)]:
            ctk.CTkLabel(hdr, text=txt, font=("Segoe UI", 10, "bold"),
                         text_color="white", width=w, anchor="w"
                         ).pack(side="left", padx=4, pady=2)

        for i, v in enumerate(ventas):
            vid      = v.get("id") or v.get("folio", i)
            bg_fila  = COLORES["bg_input"] if i % 2 == 0 else "#111827"
            forma    = v.get("forma_pago", "efectivo") or "efectivo"
            fc       = FORMA_COLOR.get(forma, COLORES["text_primary"])
            arts     = str(int(float(v.get("total_articulos", 0) or 0)))
            arrow    = ctk.StringVar(value="▶")

            bloque = ctk.CTkFrame(contenedor, fg_color="transparent")
            bloque.pack(fill="x", padx=4, pady=1)

            row = ctk.CTkFrame(bloque, fg_color=bg_fila, corner_radius=4,
                               height=32, cursor="hand2")
            row.pack(fill="x")

            ctk.CTkLabel(row, textvariable=arrow, font=("Segoe UI", 9),
                         text_color=COLORES["text_secondary"],
                         width=24).pack(side="left", padx=(4, 0))

            for txt, w, color in [
                (v.get("folio", ""),           140, COLORES["text_primary"]),
                (_fmt_fecha(v.get("dia")),      120, COLORES["text_secondary"]),
                (str(v.get("hora", ""))[:5],     65, COLORES["text_secondary"]),
                (v.get("cajero") or "—",        130, COLORES["text_primary"]),
                (v.get("cliente") or "Público", 130, COLORES["text_secondary"]),
                (arts,                           50, COLORES["text_primary"]),
                (forma.capitalize(),            110, fc),
                (f"${float(v.get('total',0)):.2f}", 90, COLORES["success"]),
            ]:
                ctk.CTkLabel(row, text=str(txt), font=("Segoe UI", 10),
                             text_color=color, width=w, anchor="w"
                             ).pack(side="left", padx=4)

            panel = ctk.CTkFrame(bloque, fg_color="#0d1520", corner_radius=0)

            def _toggle(event=None, _vid=vid, _panel=panel, _arr=arrow):
                if _vid in self._expandidos:
                    self._expandidos.discard(_vid)
                    _panel.pack_forget()
                    _arr.set("▶")
                else:
                    self._expandidos.add(_vid)
                    _panel.pack(fill="x")
                    self._render_productos(_panel, _vid)
                    _arr.set("▼")

            row.bind("<Button-1>", _toggle)
            for child in row.winfo_children():
                child.bind("<Button-1>", _toggle)

    def _render_productos(self, panel, venta_id):
        for w in panel.winfo_children():
            w.destroy()
        try:
            items = self.venta_model.get_detalle(venta_id)
        except Exception:
            items = []

        sub_hdr = ctk.CTkFrame(panel, fg_color="#1a2a3a",
                               corner_radius=4, height=26)
        sub_hdr.pack(fill="x", padx=32, pady=(4, 2))
        for txt, w in [("Código", 120), ("Producto", 310),
                       ("Cant.", 65), ("Precio", 90), ("Importe", 90)]:
            ctk.CTkLabel(sub_hdr, text=txt, font=("Segoe UI", 9, "bold"),
                         text_color=COLORES["text_secondary"],
                         width=w, anchor="w").pack(side="left", padx=4, pady=2)

        if not items:
            ctk.CTkLabel(panel, text="Sin detalle disponible.",
                         font=("Segoe UI", 10),
                         text_color=COLORES["text_secondary"]
                         ).pack(padx=40, pady=6)
            return

        total_calc = 0.0
        for j, item in enumerate(items):
            bg_r    = COLORES["bg_input"] if j % 2 == 0 else "transparent"
            r       = ctk.CTkFrame(panel, fg_color=bg_r, corner_radius=2, height=26)
            r.pack(fill="x", padx=32, pady=1)
            cant    = float(item.get("cantidad", 0))
            precio  = float(item.get("precio_unit", 0))
            importe = cant * precio
            total_calc += importe
            for txt, w in [
                (item.get("codigo_barras") or "—", 120),
                (item.get("producto_nombre", "?")[:40], 310),
                (str(int(cant)), 65),
                (f"${precio:.2f}", 90),
                (f"${importe:.2f}", 90),
            ]:
                ctk.CTkLabel(r, text=str(txt), font=("Segoe UI", 10),
                             text_color=COLORES["text_primary"],
                             width=w, anchor="w").pack(side="left", padx=4)

        tot = ctk.CTkFrame(panel, fg_color="transparent", height=26)
        tot.pack(fill="x", padx=32, pady=(2, 8))
        ctk.CTkLabel(tot, text=f"TOTAL  ${total_calc:.2f}",
                     font=("Segoe UI", 10, "bold"),
                     text_color=COLORES["success"]
                     ).pack(side="right", padx=10)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _seccion(self, titulo):
        ctk.CTkLabel(self.resultado, text=titulo,
                     font=("Segoe UI", 13, "bold"),
                     text_color=COLORES["text_primary"]
                     ).pack(anchor="w", padx=8, pady=(14, 4))

    def _sin_datos(self, msg="Sin datos."):
        ctk.CTkLabel(self.resultado, text=msg,
                     font=("Segoe UI", 11),
                     text_color=COLORES["text_secondary"]
                     ).pack(anchor="w", padx=16, pady=4)

    def _tabla_simple(self, filas, keys, headers):
        if not filas:
            self._sin_datos("Sin datos para el período.")
            return
        tabla = ctk.CTkFrame(self.resultado, fg_color=COLORES["bg_card"],
                             corner_radius=8)
        tabla.pack(fill="x", padx=8, pady=4)
        hdr = ctk.CTkFrame(tabla, fg_color=COLORES["primary"],
                           corner_radius=6, height=30)
        hdr.pack(fill="x", padx=4, pady=4)
        for h in headers:
            ctk.CTkLabel(hdr, text=h, font=("Segoe UI", 11, "bold"),
                         text_color="white", width=180
                         ).pack(side="left", padx=4)
        for i, fila in enumerate(filas):
            bg  = COLORES["bg_input"] if i % 2 == 0 else "transparent"
            row = ctk.CTkFrame(tabla, fg_color=bg, corner_radius=4, height=30)
            row.pack(fill="x", padx=4, pady=1)
            for k in keys:
                val = fila.get(k, "")
                if isinstance(val, float):
                    val = f"${val:.2f}"
                ctk.CTkLabel(row, text=str(val), font=("Segoe UI", 11),
                             text_color=COLORES["text_primary"],
                             width=180, anchor="w").pack(side="left", padx=4)

    # ── Exportar CSV ──────────────────────────────────────────────────────────
    def _exportar_csv(self):
        import csv, os, platform
        from tkinter import filedialog, messagebox

        fi = self.entry_ini.get().strip()
        ff = self.entry_fin.get().strip()

        ruta = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
            initialfile=f"reporte_{fi}_a_{ff}.csv",
            title="Guardar reporte como"
        )
        if not ruta:
            return

        # Cargar todos los datos (siempre completos)
        resumen  = self.model.resumen_general(fi, ff)
        cajeros  = self.model.resumen_por_cajero(fi, ff)
        top      = self.model.productos_mas_vendidos(fi, ff)
        dias     = self.model.ventas_por_periodo(fi, ff)
        detalle  = self.model.detalle_ventas_periodo(fi, ff)

        try:
            with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)

                # ── Resumen general ──────────────────────────────────────────
                w.writerow(["=== RESUMEN GENERAL ==="])
                w.writerow(["Total ventas", "Ingresos", "Ticket prom.",
                             "Efectivo", "Tarjeta", "Transferencia"])
                if resumen:
                    w.writerow([
                        resumen.get("total_ventas", 0),
                        f"${float(resumen.get('ingresos_total', 0)):.2f}",
                        f"${float(resumen.get('ticket_promedio', 0)):.2f}",
                        f"${float(resumen.get('efectivo', 0)):.2f}",
                        f"${float(resumen.get('tarjeta', 0)):.2f}",
                        f"${float(resumen.get('transferencia', 0)):.2f}",
                    ])

                # ── Rendimiento por cajero ───────────────────────────────────
                w.writerow([])
                w.writerow(["=== RENDIMIENTO POR CAJERO ==="])
                w.writerow(["Cajero", "Ventas", "Ingresos", "Ticket prom."])
                for c in cajeros:
                    w.writerow([
                        c.get("cajero") or "—",
                        c.get("total_ventas", 0),
                        f"${float(c.get('ingresos', 0)):.2f}",
                        f"${float(c.get('ticket_promedio', 0)):.2f}",
                    ])

                # ── Ventas por día ───────────────────────────────────────────
                w.writerow([])
                w.writerow(["=== VENTAS POR DÍA ==="])
                w.writerow(["Fecha", "Num. ventas", "Total"])
                for r in dias:
                    w.writerow([str(r.get("dia", "")),
                                r.get("num_ventas", 0),
                                f"${float(r.get('total', 0)):.2f}"])

                # ── Productos más vendidos ───────────────────────────────────
                w.writerow([])
                w.writerow(["=== PRODUCTOS MÁS VENDIDOS ==="])
                w.writerow(["Producto", "Cantidad vendida", "Importe"])
                for r in top:
                    w.writerow([r.get("nombre", ""),
                                r.get("total_cantidad", 0),
                                f"${float(r.get('total_importe', 0)):.2f}"])

                # ── Detalle de ventas con productos ──────────────────────────
                w.writerow([])
                w.writerow(["=== DETALLE DE VENTAS CON PRODUCTOS ==="])
                w.writerow([
                    "Folio", "Fecha", "Hora", "Cajero", "Cliente",
                    "Forma pago", "Total venta", "",
                    "Código producto", "Producto", "Cantidad",
                    "Precio unit.", "Importe línea"
                ])

                for r in detalle:
                    folio   = r.get("folio", "")
                    fecha   = str(r.get("dia", ""))
                    hora    = str(r.get("hora", ""))[:5]
                    cajero  = r.get("cajero") or "—"
                    cliente = r.get("cliente") or "Público general"
                    forma   = r.get("forma_pago", "")
                    total   = f"${float(r.get('total', 0)):.2f}"
                    vid     = r.get("id")

                    try:
                        items = self.venta_model.get_detalle(vid) if vid else []
                    except Exception:
                        items = []

                    if items:
                        for idx, item in enumerate(items):
                            cant    = float(item.get("cantidad", 0))
                            precio  = float(item.get("precio_unit", 0))
                            importe = cant * precio
                            cabecera = ([folio, fecha, hora, cajero,
                                         cliente, forma, total, ""]
                                        if idx == 0
                                        else ["", "", "", "", "", "", "", ""])
                            w.writerow(cabecera + [
                                item.get("codigo_barras") or "—",
                                item.get("producto_nombre", "?"),
                                int(cant),
                                f"${precio:.2f}",
                                f"${importe:.2f}",
                            ])
                    else:
                        w.writerow([folio, fecha, hora, cajero,
                                    cliente, forma, total, "",
                                    "—", "Sin detalle", "", "", ""])

                    w.writerow([])   # línea vacía entre ventas

            messagebox.showinfo("✅ Exportado", f"Reporte guardado en:\n{ruta}")
            if platform.system() == "Darwin":
                os.system(f'open -R "{ruta}"')
            elif platform.system() == "Windows":
                os.startfile(os.path.dirname(ruta))

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")
