"""
historial_cortes_view.py
Vista de historial de sesiones de caja para Administrador / Supervisor.
Permite filtrar por fecha y cajero, ver el detalle de cada sesión,
reimprimir el corte y exportar a CSV.
Solo visible para roles con permiso 'reportes_ver_todos'.
"""
import customtkinter as ctk
from tkinter import messagebox
from datetime import date, timedelta, datetime
from app.models.caja_model import CajaModel
from app.utils.config import COLORES, APP_NOMBRE, APP_VERSION
from app.utils import session


DIAS  = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
MESES = ["ene","feb","mar","abr","may","jun",
         "jul","ago","sep","oct","nov","dic"]

def _fmt(d):
    try:
        if hasattr(d, "weekday"):
            return f"{DIAS[d.weekday()]} {d.day} {MESES[d.month-1]} {d.year}"
        dt = datetime.strptime(str(d)[:10], "%Y-%m-%d")
        return f"{DIAS[dt.weekday()]} {dt.day} {MESES[dt.month-1]} {dt.year}"
    except Exception:
        return str(d)[:10]

def _fmt_hora(dt_str):
    try:
        return datetime.strptime(str(dt_str)[:19], "%Y-%m-%d %H:%M:%S").strftime("%H:%M:%S")
    except Exception:
        return str(dt_str)[11:19]


class HistorialCortesView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.model      = CajaModel()
        self._expandidos = set()
        self._sesiones   = []
        self._build()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build(self):
        # Encabezado
        hdr_row = ctk.CTkFrame(self, fg_color="transparent")
        hdr_row.pack(fill="x", padx=20, pady=(16, 4))
        ctk.CTkLabel(hdr_row, text="🏦  Historial de Cortes de Caja",
                     font=("Segoe UI", 20, "bold"),
                     text_color=COLORES["text_primary"]).pack(side="left")
        ctk.CTkLabel(hdr_row,
                     text="  Solo admins y supervisores  ",
                     font=("Segoe UI", 10, "bold"),
                     fg_color=COLORES["primary"], text_color="white",
                     corner_radius=6).pack(side="left", padx=10)

        # ── Filtros ───────────────────────────────────────────────────────
        filtros = ctk.CTkFrame(self, fg_color=COLORES["bg_dark"], corner_radius=10)
        filtros.pack(fill="x", padx=20, pady=4)

        hoy = date.today()
        ini = hoy - timedelta(days=30)

        ctk.CTkLabel(filtros, text="Desde:", font=("Segoe UI", 11),
                     text_color=COLORES["text_secondary"]).pack(side="left", padx=(14,4), pady=10)
        self.entry_ini = ctk.CTkEntry(filtros, width=110, height=32)
        self.entry_ini.insert(0, str(ini))
        self.entry_ini.pack(side="left", padx=4)

        ctk.CTkLabel(filtros, text="Hasta:", font=("Segoe UI", 11),
                     text_color=COLORES["text_secondary"]).pack(side="left", padx=(8,4))
        self.entry_fin = ctk.CTkEntry(filtros, width=110, height=32)
        self.entry_fin.insert(0, str(hoy))
        self.entry_fin.pack(side="left", padx=4)

        # Filtro por cajero
        ctk.CTkLabel(filtros, text="Cajero:", font=("Segoe UI", 11),
                     text_color=COLORES["text_secondary"]).pack(side="left", padx=(12,4))
        cajeros = self.model.get_cajeros()
        self._cajero_ids   = [None] + [c["id"] for c in cajeros]
        self._cajero_names = ["— Todos —"] + [c["nombre"] for c in cajeros]
        self.combo_cajero  = ctk.CTkComboBox(filtros, width=160, height=32,
                                              values=self._cajero_names)
        self.combo_cajero.set("— Todos —")
        self.combo_cajero.pack(side="left", padx=4)

        ctk.CTkButton(filtros, text="🔍 Buscar", width=100, height=32,
                      fg_color=COLORES["primary"],
                      command=self._cargar).pack(side="left", padx=10)

        ctk.CTkButton(filtros, text="📥 CSV", width=80, height=32,
                      fg_color=COLORES["success"],
                      command=self._exportar_csv).pack(side="left", padx=4)

        # Accesos rápidos de rango
        for lbl, dias in [("Hoy", 0), ("7d", 7), ("30d", 30)]:
            d = dias
            ctk.CTkButton(filtros, text=lbl, width=46, height=28,
                          fg_color=COLORES["bg_input"],
                          font=("Segoe UI", 9, "bold"),
                          command=lambda d=d: self._set_rango(d)
                          ).pack(side="right", padx=2, pady=6)

        # ── Cabecera de la tabla ──────────────────────────────────────────
        col_hdr = ctk.CTkFrame(self, fg_color=COLORES["primary"], corner_radius=6, height=30)
        col_hdr.pack(fill="x", padx=20, pady=(6, 0))
        ctk.CTkLabel(col_hdr, text="", width=24, text_color="white",
                     font=("Segoe UI", 10)).pack(side="left", padx=4)
        for txt, w in [("Fecha apertura", 160), ("Hora apertura", 100),
                       ("Fecha cierre", 140), ("Hora cierre", 100),
                       ("Cajero", 140), ("Ventas", 60),
                       ("Total ventas", 110), ("Total caja", 110),
                       ("Estado", 80)]:
            ctk.CTkLabel(col_hdr, text=txt, font=("Segoe UI", 10, "bold"),
                         text_color="white", width=w, anchor="w"
                         ).pack(side="left", padx=4, pady=4)

        # ── Área scrollable ───────────────────────────────────────────────
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=4)

        self._cargar()

    # ── Cargar sesiones ───────────────────────────────────────────────────────
    def _set_rango(self, dias):
        hoy = date.today()
        ini = hoy - timedelta(days=dias)
        self.entry_ini.delete(0, "end"); self.entry_ini.insert(0, str(ini))
        self.entry_fin.delete(0, "end"); self.entry_fin.insert(0, str(hoy))
        self._cargar()

    def _cargar(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self._expandidos.clear()

        fi  = self.entry_ini.get().strip()
        ff  = self.entry_fin.get().strip()
        sel = self.combo_cajero.get()
        uid = None
        if sel in self._cajero_names and sel != "— Todos —":
            uid = self._cajero_ids[self._cajero_names.index(sel)]

        self._sesiones = self.model.get_sesiones_historico(fi, ff, uid)

        if not self._sesiones:
            ctk.CTkLabel(self.scroll,
                         text="Sin cortes en el período seleccionado.",
                         font=("Segoe UI", 12),
                         text_color=COLORES["text_secondary"]).pack(pady=30)
            return

        for i, s in enumerate(self._sesiones):
            self._render_fila(s, i)

    def _render_fila(self, s, i):
        sid     = s["id"]
        bg_fila = COLORES["bg_card"] if i % 2 == 0 else "#111827"

        fi_dt  = s.get("fecha_apertura")
        fc_dt  = s.get("fecha_cierre")
        cajero = s.get("cajero_nombre") or "—"
        num_v  = int(s.get("ventas_num", 0) or 0)
        tot_v  = float(s.get("ventas_total", 0) or 0)
        ef     = float(s.get("total_efectivo", 0) or 0)
        tj     = float(s.get("total_tarjeta", 0) or 0)
        tr_    = float(s.get("total_transferencia", 0) or 0)
        fi_num = float(s.get("fondo_inicial", 0) or 0)
        # Total efectivo en caja = fondo + ventas efectivo
        # (entradas/salidas no las tenemos aquí; mostramos lo registrado)
        total_caja = fi_num + ef

        fecha_ap  = _fmt(fi_dt)  if fi_dt else "—"
        hora_ap   = _fmt_hora(fi_dt) if fi_dt else "—"
        fecha_ci  = _fmt(fc_dt)  if fc_dt else "—"
        hora_ci   = _fmt_hora(fc_dt) if fc_dt else "Abierta"
        estado    = s.get("estado", "cerrada")
        arrow     = ctk.StringVar(value="▶")

        bloque = ctk.CTkFrame(self.scroll, fg_color="transparent")
        bloque.pack(fill="x", pady=1)

        row = ctk.CTkFrame(bloque, fg_color=bg_fila, corner_radius=4,
                           height=34, cursor="hand2")
        row.pack(fill="x")

        ctk.CTkLabel(row, textvariable=arrow, font=("Segoe UI", 9),
                     text_color=COLORES["text_secondary"],
                     width=24).pack(side="left", padx=(4, 0))

        estado_color = COLORES["success"] if estado == "cerrada" else COLORES["warning"]
        for txt, w, color in [
            (fecha_ap,      160, COLORES["text_primary"]),
            (hora_ap,       100, COLORES["text_secondary"]),
            (fecha_ci,      140, COLORES["text_secondary"]),
            (hora_ci,       100, COLORES["text_secondary"]),
            (cajero,        140, COLORES["text_primary"]),
            (str(num_v),     60, COLORES["text_primary"]),
            (f"${tot_v:,.2f}", 110, COLORES["success"]),
            (f"${total_caja:,.2f}", 110, COLORES["success"]),
            (estado.capitalize(), 80, estado_color),
        ]:
            ctk.CTkLabel(row, text=str(txt), font=("Segoe UI", 10),
                         text_color=color, width=w, anchor="w"
                         ).pack(side="left", padx=4)

        panel = ctk.CTkFrame(bloque, fg_color="#0d1520", corner_radius=0)

        def _toggle(event=None, _sid=sid, _panel=panel, _arr=arrow, _s=s):
            if _sid in self._expandidos:
                self._expandidos.discard(_sid)
                _panel.pack_forget()
                _arr.set("▶")
            else:
                self._expandidos.add(_sid)
                _panel.pack(fill="x")
                self._render_detalle(_panel, _s)
                _arr.set("▼")

        row.bind("<Button-1>", _toggle)
        for child in row.winfo_children():
            child.bind("<Button-1>", _toggle)

    # ── Detalle expandido de una sesión ───────────────────────────────────────
    def _render_detalle(self, panel, s):
        for w in panel.winfo_children():
            w.destroy()

        resumen = self.model.get_resumen_sesion(s["id"])
        movs    = self.model.get_movimientos(s["id"])

        ef  = float(resumen.get("total_efectivo",      0) or 0)
        tj  = float(resumen.get("total_tarjeta",       0) or 0)
        tr_ = float(resumen.get("total_transferencia", 0) or 0)
        fi  = float(s.get("fondo_inicial",             0) or 0)
        en  = float(resumen.get("entradas_extra",      0) or 0)
        sa  = float(resumen.get("salidas_extra",       0) or 0)
        nv  = int(resumen.get("total_ventas",          0) or 0)
        total_caja = fi + ef + en - sa

        # Chips informativos
        chips = ctk.CTkFrame(panel, fg_color="transparent")
        chips.pack(fill="x", padx=24, pady=(8, 4))
        for lbl, val, color in [
            ("Fondo inicial",    f"${fi:,.2f}",         COLORES["text_secondary"]),
            ("Ventas efectivo",  f"${ef:,.2f}",         COLORES["success"]),
            ("Tarjeta",          f"${tj:,.2f}",         COLORES["primary"]),
            ("Transferencia",    f"${tr_:,.2f}",        COLORES["warning"]),
            ("Entradas extra",   f"+${en:,.2f}",        COLORES["success"]),
            ("Salidas extra",    f"-${sa:,.2f}",        COLORES["danger"]),
            ("Num. ventas",      str(nv),               COLORES["text_primary"]),
            ("Total en caja",    f"${total_caja:,.2f}", COLORES["success"]),
        ]:
            chip = ctk.CTkFrame(chips, fg_color=COLORES["bg_input"], corner_radius=6)
            chip.pack(side="left", padx=(0, 8), pady=2)
            ctk.CTkLabel(chip, text=lbl, font=("Segoe UI", 9),
                         text_color=COLORES["text_secondary"]
                         ).pack(side="left", padx=(6, 2), pady=3)
            ctk.CTkLabel(chip, text=val, font=("Segoe UI", 10, "bold"),
                         text_color=color
                         ).pack(side="left", padx=(0, 6), pady=3)

        # Notas de cierre
        notas = s.get("notas_cierre") or ""
        if notas:
            ctk.CTkLabel(panel, text=f"📝 Notas: {notas}",
                         font=("Segoe UI", 10),
                         text_color=COLORES["text_secondary"]
                         ).pack(anchor="w", padx=28, pady=(0, 4))

        # Movimientos de la sesión
        if movs:
            mov_tbl = ctk.CTkFrame(panel, fg_color=COLORES["bg_input"], corner_radius=6)
            mov_tbl.pack(fill="x", padx=24, pady=(2, 6))
            mov_hdr = ctk.CTkFrame(mov_tbl, fg_color=COLORES["primary"],
                                   corner_radius=4, height=24)
            mov_hdr.pack(fill="x", padx=4, pady=(4, 2))
            for txt, w in [("Hora", 80), ("Tipo", 90), ("Monto", 100),
                           ("Concepto", 300), ("Usuario", 140)]:
                ctk.CTkLabel(mov_hdr, text=txt, font=("Segoe UI", 9, "bold"),
                             text_color="white", width=w, anchor="w"
                             ).pack(side="left", padx=4, pady=2)

            for j, m in enumerate(movs):
                bg_r   = COLORES["bg_card"] if j % 2 == 0 else "transparent"
                r      = ctk.CTkFrame(mov_tbl, fg_color=bg_r, corner_radius=2, height=26)
                r.pack(fill="x", padx=4, pady=1)
                color  = COLORES["success"] if m["tipo"] == "entrada" else COLORES["danger"]
                hora_m = _fmt_hora(m.get("fecha", ""))[:5]
                for txt, w, tc in [
                    (hora_m,               80, COLORES["text_secondary"]),
                    (m["tipo"].capitalize(), 90, color),
                    (f"${float(m.get('monto',0)):.2f}", 100, color),
                    ((m.get("concepto") or "—")[:42], 300, COLORES["text_primary"]),
                    (m.get("usuario_nombre") or "—",   140, COLORES["text_secondary"]),
                ]:
                    ctk.CTkLabel(r, text=str(txt), font=("Segoe UI", 10),
                                 text_color=tc, width=w, anchor="w"
                                 ).pack(side="left", padx=4)

            ctk.CTkFrame(mov_tbl, height=4, fg_color="transparent").pack()

        # Botón reimprimir corte
        btn_reimp = ctk.CTkFrame(panel, fg_color="transparent")
        btn_reimp.pack(fill="x", padx=24, pady=(2, 10))
        ctk.CTkButton(btn_reimp, text="🖨  Reimprimir corte de esta sesión",
                      height=34, width=260,
                      font=("Segoe UI", 11, "bold"),
                      fg_color=COLORES["secondary"],
                      command=lambda _s=s, _r=resumen, _m=movs: self._reimprimir(_s, _r, _m)
                      ).pack(side="left")

    # ── Reimprimir corte histórico ────────────────────────────────────────────
    def _reimprimir(self, s, resumen, movs):
        try:
            from app.database.connection import Database
            db  = Database.get_instance()
            cfg = {r["clave"]: r["valor"]
                   for r in db.fetch_all("SELECT clave, valor FROM configuracion")}
            nombre_negocio = cfg.get("nombre_negocio") or APP_NOMBRE
            telefono       = cfg.get("telefono") or ""
        except Exception:
            nombre_negocio = APP_NOMBRE; telefono = ""

        ef  = float(resumen.get("total_efectivo",      0) or 0)
        tj  = float(resumen.get("total_tarjeta",       0) or 0)
        tr_ = float(resumen.get("total_transferencia", 0) or 0)
        fi  = float(s.get("fondo_inicial",             0) or 0)
        en  = float(resumen.get("entradas_extra",      0) or 0)
        sa  = float(resumen.get("salidas_extra",       0) or 0)
        nv  = int(resumen.get("total_ventas",          0) or 0)
        total_caja = fi + ef + en - sa

        ahora    = datetime.now()
        fi_str   = str(s.get("fecha_apertura", ""))[:16]
        fc_str   = str(s.get("fecha_cierre", ""))[:16]
        cajero   = s.get("cajero_nombre") or "—"
        notas    = s.get("notas_cierre") or ""
        reimp_por = (session.get_usuario() or {}).get("nombre", "—")

        W = 46; sep = "=" * W; lin = "-" * W
        def c(t): return t.center(W)
        def lr(l, r): return f"{l:<28}{r:>18}"

        L = [c(nombre_negocio)]
        if telefono: L.append(c("Tel: " + telefono))
        L += [sep, c("*** CORTE DE CAJA (REIMPRESION) ***"), sep,
              f"Apertura : {fi_str}",
              f"Cierre   : {fc_str}",
              f"Cajero   : {cajero}",
              lin, c("RESUMEN DE VENTAS"), lin,
              lr("Número de ventas", str(nv)),
              lr("Efectivo",  f"${ef:,.2f}"),
              lr("Tarjeta",   f"${tj:,.2f}"),
              lr("Transf.",   f"${tr_:,.2f}"),
              lr("Total vendido", f"${ef+tj+tr_:,.2f}"),
              lin, c("EFECTIVO EN CAJA"), lin,
              lr("Fondo inicial",   f"${fi:,.2f}"),
              lr("+ Ventas efect.", f"${ef:,.2f}"),
              ]
        if en > 0: L.append(lr("+ Entradas extra", f"${en:,.2f}"))
        if sa > 0: L.append(lr("- Salidas extra",  f"${sa:,.2f}"))
        L += [lin, lr("TOTAL EN CAJA", f"${total_caja:,.2f}"), sep]

        if movs:
            L.append(c("MOVIMIENTOS"))
            L.append(lin)
            for m in movs:
                h    = _fmt_hora(m.get("fecha",""))[:5]
                tipo = "ENT" if m["tipo"] == "entrada" else "SAL"
                mto  = float(m.get("monto", 0))
                conc = (m.get("concepto") or "—")[:22]
                L.append(f"{h}  {tipo}  ${mto:>8.2f}  {conc}")
            L.append(sep)

        if notas:
            L += [f"Notas: {notas}", lin]
        L += [c(f"Reimpreso: {ahora.strftime('%d/%m/%Y %H:%M:%S')}"),
              c(f"Por: {reimp_por}"), "", ""]

        contenido = "\n".join(L)

        # Vista previa
        win = ctk.CTkToplevel(self)
        win.title("🖨 Reimprimir Corte")
        win.geometry("500x640")
        win.configure(fg_color=COLORES["bg_dark"])
        win.protocol("WM_DELETE_WINDOW", lambda: [win.grab_release(), win.destroy()])

        hdr = ctk.CTkFrame(win, fg_color=COLORES["secondary"], corner_radius=0, height=44)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="REIMPRESIÓN DE CORTE — Vista previa",
                     font=("Segoe UI", 13, "bold"), text_color="white"
                     ).pack(side="left", padx=16, pady=10)

        import tkinter as tk
        papel = ctk.CTkFrame(win, fg_color="white", corner_radius=8)
        papel.pack(fill="both", expand=True, padx=14, pady=10)
        sb  = tk.Scrollbar(papel, orient="vertical")
        sb.pack(side="right", fill="y")
        txt = tk.Text(papel, font=("Courier New", 10), bg="white", fg="black",
                      relief="flat", padx=8, pady=8, wrap="none",
                      yscrollcommand=sb.set)
        sb.configure(command=txt.yview)
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", contenido)
        txt.configure(state="disabled")

        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=(0, 12))

        def _imprimir():
            import tempfile, os, platform
            try:
                with tempfile.NamedTemporaryFile(
                        mode="w", suffix=".txt",
                        delete=False, encoding="utf-8") as f:
                    f.write(contenido); tmp = f.name
                if   platform.system() == "Darwin":  os.system(f'lp "{tmp}"')
                elif platform.system() == "Windows": os.startfile(tmp, "print")
                else:                                os.system(f'lp "{tmp}"')
                messagebox.showinfo("✅ Enviado", "Corte enviado a la impresora.")
                win.grab_release(); win.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo imprimir:\n{e}")

        ctk.CTkButton(btn_row, text="🖨  Imprimir",
                      height=42, font=("Segoe UI", 13, "bold"),
                      fg_color=COLORES["primary"], command=_imprimir
                      ).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(btn_row, text="✕  Cerrar",
                      height=42, font=("Segoe UI", 12),
                      fg_color=COLORES["danger"],
                      command=lambda: [win.grab_release(), win.destroy()]
                      ).pack(side="left", fill="x", expand=True)

        win.lift(); win.focus_force(); win.grab_set()

    # ── Exportar CSV ──────────────────────────────────────────────────────────
    def _exportar_csv(self):
        import csv, os, platform
        from tkinter import filedialog

        if not self._sesiones:
            messagebox.showwarning("Sin datos", "No hay sesiones para exportar.")
            return

        fi = self.entry_ini.get().strip()
        ff = self.entry_fin.get().strip()

        ruta = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
            initialfile=f"cortes_caja_{fi}_a_{ff}.csv",
            title="Guardar historial de cortes"
        )
        if not ruta:
            return

        try:
            with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["=== HISTORIAL DE CORTES DE CAJA ==="])
                w.writerow(["ID sesion", "Cajero",
                            "Fecha apertura", "Hora apertura",
                            "Fecha cierre",   "Hora cierre",
                            "Fondo inicial",
                            "Ventas efectivo", "Tarjeta", "Transferencia",
                            "Num. ventas", "Total vendido",
                            "Notas cierre"])
                for s in self._sesiones:
                    res = self.model.get_resumen_sesion(s["id"])
                    ef  = float(res.get("total_efectivo",      0) or 0)
                    tj  = float(res.get("total_tarjeta",       0) or 0)
                    tr_ = float(res.get("total_transferencia", 0) or 0)
                    nv  = int(res.get("total_ventas",          0) or 0)
                    fi_dt = str(s.get("fecha_apertura", ""))
                    fc_dt = str(s.get("fecha_cierre", ""))
                    w.writerow([
                        s["id"],
                        s.get("cajero_nombre") or "—",
                        fi_dt[:10], fi_dt[11:19],
                        fc_dt[:10], fc_dt[11:19],
                        f"${float(s.get('fondo_inicial',0)):.2f}",
                        f"${ef:.2f}", f"${tj:.2f}", f"${tr_:.2f}",
                        nv, f"${ef+tj+tr_:.2f}",
                        s.get("notas_cierre") or "",
                    ])

            messagebox.showinfo("✅ Exportado", f"Guardado en:\n{ruta}")
            if platform.system() == "Darwin":
                os.system(f'open -R "{ruta}"')
            elif platform.system() == "Windows":
                os.startfile(os.path.dirname(ruta))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")
