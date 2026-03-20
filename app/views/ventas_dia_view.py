"""
ventas_dia_view.py  v1.4
- Todos los tickets usan encabezado_ticket de logo_utils
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from app.models.venta_model import VentaModel
from app.utils.config import COLORES
from app.utils import session
from app.utils.logo_utils import encabezado_ticket
import platform

_ES_MAC = platform.system() == "Darwin"


class VentasDiaView(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Ventas del Día y Devoluciones")
        self.geometry("1020x640")
        self.configure(fg_color=COLORES["bg_dark"])
        self.model        = VentaModel()
        self._entry_busq  = None
        self._expandidos  = set()
        self.protocol("WM_DELETE_WINDOW", self._cerrar)
        self._build()
        self.grab_set()
        self.lift()
        self.focus_force()

    def _cerrar(self):
        try: self.grab_release()
        except Exception: pass
        self.destroy()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=COLORES["primary"], corner_radius=0, height=44)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="📋  VENTAS DEL DÍA Y DEVOLUCIONES",
                     font=("Segoe UI", 13, "bold"),
                     text_color="white").pack(side="left", padx=16, pady=10)

        resumen = self.model.resumen_hoy()
        res_frame = ctk.CTkFrame(self, fg_color=COLORES["bg_card"], corner_radius=0)
        res_frame.pack(fill="x")
        for lbl, val, color in [
            ("Total ventas", str(resumen.get("total_ventas", 0) or 0),         COLORES["primary"]),
            ("Ingresos",     f"${float(resumen.get('ingresos', 0) or 0):.2f}", COLORES["success"]),
            ("Efectivo",     f"${float(resumen.get('efectivo', 0) or 0):.2f}", COLORES["text_primary"]),
        ]:
            col = ctk.CTkFrame(res_frame, fg_color="transparent")
            col.pack(side="left", padx=24, pady=8)
            ctk.CTkLabel(col, text=lbl, font=("Segoe UI", 10),
                         text_color=COLORES["text_secondary"]).pack()
            ctk.CTkLabel(col, text=val, font=("Segoe UI", 16, "bold"),
                         text_color=color).pack()

        busq = ctk.CTkFrame(self, fg_color=COLORES["bg_card"], corner_radius=0, height=40)
        busq.pack(fill="x", padx=8, pady=(4, 2))
        ctk.CTkLabel(busq, text="Buscar cliente:", font=("Segoe UI", 11),
                     text_color=COLORES["text_secondary"]).pack(side="left", padx=(10, 4), pady=7)
        self._entry_busq = ctk.CTkEntry(busq, height=26, width=220,
                                        placeholder_text="Nombre del cliente...")
        self._entry_busq.pack(side="left", padx=4)
        self._entry_busq.bind("<KeyRelease>", lambda e: self._cargar_ventas())
        ctk.CTkButton(busq, text="Ver todos", height=26, width=70,
                      fg_color=COLORES["secondary"],
                      command=lambda: [self._entry_busq.delete(0, "end"),
                                       self._cargar_ventas()]
                      ).pack(side="left", padx=4)
        ctk.CTkLabel(busq, text="Clic en venta para ver detalle",
                     font=("Segoe UI", 10),
                     text_color=COLORES["text_secondary"]).pack(side="right", padx=12)

        cols_bg = COLORES["bg_card"]
        cols_hdr = tk.Frame(self, bg=cols_bg, height=28)
        cols_hdr.pack(fill="x", padx=8)
        cols_hdr.pack_propagate(False)
        self._COLS = [24, 150, 150, 160, 55, 95, 120, 90, 180]
        headers    = [" ", "Folio", "Fecha y Hora", "Cliente", "Arts.", "Total",
                      "Cajero", "Estado", "Acciones"]
        x = 8
        for txt, w in zip(headers, self._COLS):
            tk.Label(cols_hdr, text=txt, bg=cols_bg, fg=COLORES["text_secondary"],
                     font=("Segoe UI", 10, "bold"), anchor="w"
                     ).place(x=x, y=6, width=w)
            x += w

        list_outer = tk.Frame(self, bg=COLORES["bg_dark"])
        list_outer.pack(fill="both", expand=True, padx=8, pady=4)
        self._canvas = tk.Canvas(list_outer, bg=COLORES["bg_dark"], highlightthickness=0)
        self._vscroll = tk.Scrollbar(list_outer, orient="vertical",
                                      command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._vscroll.set)
        self._vscroll.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)
        self._inner = tk.Frame(self._canvas, bg=COLORES["bg_dark"])
        self._canvas_win = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")
        self._inner.bind("<Configure>",
                          lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
                           lambda e: self._canvas.itemconfig(self._canvas_win, width=e.width))
        self._canvas.bind("<MouseWheel>", self._on_wheel)
        self._canvas.bind("<Button-4>",   lambda e: self._canvas.yview_scroll(-2, "units"))
        self._canvas.bind("<Button-5>",   lambda e: self._canvas.yview_scroll( 2, "units"))
        self._cargar_ventas()

    def _on_wheel(self, event):
        self._canvas.yview_scroll(int(-event.delta / (10 if _ES_MAC else 120)), "units")

    def _cargar_ventas(self):
        for w in self._inner.winfo_children(): w.destroy()
        ventas = self.model.get_ventas_hoy()
        if self._entry_busq:
            filtro = self._entry_busq.get().strip().lower()
            if filtro:
                ventas = [v for v in ventas
                          if filtro in (v.get("cliente_nombre") or "publico").lower()]
        if not ventas:
            tk.Label(self._inner, text="Sin ventas para mostrar.",
                     bg=COLORES["bg_dark"], fg=COLORES["text_secondary"],
                     font=("Segoe UI", 12)).pack(pady=20)
            return
        for i, v in enumerate(ventas):
            self._render_fila(v, i)

    def _render_fila(self, v, i):
        vid     = v["id"]
        estado  = v.get("estado", "")
        bg_main = COLORES["bg_card"] if i % 2 == 0 else "#111827"
        COLS    = self._COLS
        ROW_H   = 36

        fecha_raw = str(v.get("fecha", ""))
        try:
            dt = datetime.strptime(fecha_raw[:19], "%Y-%m-%d %H:%M:%S")
            DIAS  = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
            MESES = ["ene","feb","mar","abr","may","jun","jul","ago","sep","oct","nov","dic"]
            fecha_str = f"{DIAS[dt.weekday()]} {dt.day} {MESES[dt.month-1]}  {dt.strftime('%H:%M')}"
        except Exception:
            fecha_str = fecha_raw[:16]

        cajero  = v.get("usuario_nombre") or "—"
        cliente = v.get("cliente_nombre") or "Público general"
        arts    = str(int(float(v.get("total_articulos", 0) or 0)))
        total_s = f"${float(v['total']):.2f}"
        estado_color = COLORES["success"] if estado == "completada" else COLORES["danger"]

        bloque = tk.Frame(self._inner, bg=COLORES["bg_dark"])
        bloque.pack(fill="x", pady=1)

        row = tk.Frame(bloque, bg=bg_main, height=ROW_H, cursor="hand2")
        row.pack(fill="x"); row.pack_propagate(False)
        arrow_txt = ["▼" if vid in self._expandidos else "▶"]
        lbl_arrow = tk.Label(row, text=arrow_txt[0], bg=bg_main,
                             fg=COLORES["text_secondary"], font=("Segoe UI", 10))
        lbl_arrow.place(x=4, y=10, width=COLS[0])

        tk.Label(row, text=v["folio"], bg=bg_main, fg=COLORES["text_primary"],
                 font=("Segoe UI", 11), anchor="w").place(x=COLS[0]+4, y=10, width=COLS[1]-4)
        x2 = COLS[0]+COLS[1]
        tk.Label(row, text=fecha_str, bg=bg_main, fg=COLORES["text_primary"],
                 font=("Segoe UI", 11), anchor="w").place(x=x2+4, y=10, width=COLS[2]-4)
        x3 = x2+COLS[2]
        tk.Label(row, text=cliente[:22], bg=bg_main, fg=COLORES["text_primary"],
                 font=("Segoe UI", 11), anchor="w").place(x=x3+4, y=10, width=COLS[3]-4)
        x4 = x3+COLS[3]
        tk.Label(row, text=arts, bg=bg_main, fg=COLORES["text_primary"],
                 font=("Segoe UI", 11), anchor="w").place(x=x4+4, y=10, width=COLS[4]-4)
        x5 = x4+COLS[4]
        tk.Label(row, text=total_s, bg=bg_main, fg=COLORES["success"],
                 font=("Segoe UI", 11, "bold"), anchor="w").place(x=x5+4, y=10, width=COLS[5]-4)
        x6 = x5+COLS[5]
        tk.Label(row, text=cajero[:16], bg=bg_main, fg=COLORES["text_primary"],
                 font=("Segoe UI", 11), anchor="w").place(x=x6+4, y=10, width=COLS[6]-4)
        x7 = x6+COLS[6]
        tk.Label(row, text=estado.capitalize(), bg=bg_main, fg=estado_color,
                 font=("Segoe UI", 11, "bold"), anchor="w").place(x=x7+4, y=10, width=COLS[7]-4)

        if estado == "completada":
            x8 = x7+COLS[7]
            ctk.CTkButton(row, text="🖨 Reimprimir", width=88, height=26,
                          fg_color=COLORES["primary"], font=("Segoe UI", 9, "bold"),
                          command=lambda _v=v, _f=fecha_str, _ca=cajero, _cl=cliente:
                              self._reimprimir(_v, _f, _ca, _cl)
                          ).place(x=x8+2, y=4)
            ctk.CTkButton(row, text="↩ Devolver", width=80, height=26,
                          fg_color=COLORES["warning"], font=("Segoe UI", 9, "bold"),
                          command=lambda _v=v: self._solicitar_clave_supervisor(_v)
                          ).place(x=x8+94, y=4)

        panel_detalle = tk.Frame(bloque, bg="#0d1520")
        if vid in self._expandidos:
            panel_detalle.pack(fill="x")
            self._render_detalle(panel_detalle, v, fecha_str, cajero, cliente)

        def _toggle(event=None, _vid=vid, _panel=panel_detalle,
                    _arr=arrow_txt, _lbl=lbl_arrow,
                    _v=v, _f=fecha_str, _ca=cajero, _cl=cliente):
            if _vid in self._expandidos:
                self._expandidos.discard(_vid); _panel.pack_forget()
                _arr[0]="▶"; _lbl.configure(text="▶")
            else:
                self._expandidos.add(_vid); _panel.pack(fill="x")
                self._render_detalle(_panel, _v, _f, _ca, _cl)
                _arr[0]="▼"; _lbl.configure(text="▼")

        row.bind("<Button-1>", _toggle)
        for child in row.winfo_children():
            if isinstance(child, tk.Label): child.bind("<Button-1>", _toggle)
        for w in (row, bloque):
            w.bind("<MouseWheel>", self._on_wheel)
            w.bind("<Button-4>", lambda e: self._canvas.yview_scroll(-2,"units"))
            w.bind("<Button-5>", lambda e: self._canvas.yview_scroll( 2,"units"))

    def _render_detalle(self, panel, v, fecha_str, cajero, cliente):
        for w in panel.winfo_children(): w.destroy()
        info_frame = ctk.CTkFrame(panel, fg_color="transparent")
        info_frame.pack(fill="x", padx=24, pady=(6, 2))
        for lbl, val in [("Fecha", fecha_str), ("Cajero", cajero),
                          ("Cliente", cliente), ("Folio", v["folio"]),
                          ("Forma pago", (v.get("forma_pago") or "—").capitalize())]:
            chip = ctk.CTkFrame(info_frame, fg_color=COLORES["bg_input"], corner_radius=6)
            chip.pack(side="left", padx=(0, 8), pady=2)
            ctk.CTkLabel(chip, text=lbl, font=("Segoe UI", 9),
                         text_color=COLORES["text_secondary"]).pack(side="left", padx=(6,2), pady=3)
            ctk.CTkLabel(chip, text=val, font=("Segoe UI", 10, "bold"),
                         text_color=COLORES["text_primary"]).pack(side="left", padx=(0,6), pady=3)

        tbl_outer = tk.Frame(panel, bg=COLORES["bg_input"])
        tbl_outer.pack(fill="x", padx=24, pady=(4, 10))
        hdr = tk.Frame(tbl_outer, bg=COLORES["primary"], height=26)
        hdr.pack(fill="x", padx=4, pady=(4, 2)); hdr.pack_propagate(False)
        TW = [110, 300, 80, 100, 100]
        x = 6
        for txt, w in zip(["Código","Descripción","Cantidad","Precio Unit.","Importe"], TW):
            tk.Label(hdr, text=txt, bg=COLORES["primary"], fg="white",
                     font=("Segoe UI", 10, "bold"), anchor="w").place(x=x, y=4, width=w)
            x += w

        try: items = self.model.get_detalle(v["id"])
        except Exception: items = []

        if not items:
            tk.Label(tbl_outer, text="Sin detalle.",
                     bg=COLORES["bg_input"], fg=COLORES["text_secondary"],
                     font=("Segoe UI", 10)).pack(pady=6)
        else:
            for j, item in enumerate(items):
                row_bg = COLORES["bg_card"] if j % 2 == 0 else COLORES["bg_input"]
                r = tk.Frame(tbl_outer, bg=row_bg, height=28)
                r.pack(fill="x", padx=4, pady=1); r.pack_propagate(False)
                cant   = float(item.get("cantidad", 0))
                precio = float(item.get("precio_unit", 0))
                imp    = cant * precio
                cant_s = f"{cant:.3f}" if cant != int(cant) else str(int(cant))
                x = 6
                for txt, w in zip([item.get("codigo_barras") or "—",
                                    item.get("producto_nombre","?")[:38],
                                    cant_s, f"${precio:.2f}", f"${imp:.2f}"], TW):
                    tk.Label(r, text=str(txt), bg=row_bg, fg=COLORES["text_primary"],
                             font=("Segoe UI", 10), anchor="w").place(x=x, y=6, width=w)
                    x += w
            tot_row = tk.Frame(tbl_outer, bg=COLORES["bg_input"], height=28)
            tot_row.pack(fill="x", padx=4, pady=(2, 6)); tot_row.pack_propagate(False)
            tk.Label(tot_row, text=f"TOTAL  ${float(v['total']):.2f}",
                     bg=COLORES["bg_input"], fg=COLORES["success"],
                     font=("Segoe UI", 11, "bold"), anchor="e").pack(side="right", padx=12, pady=4)

    # ── Reimprimir — usa encabezado_ticket ────────────────────────────────────
    def _reimprimir(self, v, fecha_str, cajero, cliente):
        try:    items = self.model.get_detalle(v["id"])
        except: items = []

        W     = 42
        linea = "─" * W

        # ← Aquí se usa encabezado_ticket con todos los datos del negocio
        lines = encabezado_ticket(W)
        lines += [
            f"Fecha : {fecha_str}",
            f"Cajero: {cajero}",
            f"Folio : {v['folio']}",
            f"Cliente: {cliente}",
            linea,
            f"{'Descripcion':<20}{'Cant':>7}{'P.Unit':>7}{'Importe':>8}",
            linea,
        ]
        for item in items:
            cant   = float(item.get("cantidad", 0))
            precio = float(item.get("precio_unit", 0))
            imp    = cant * precio
            desc   = item.get("producto_nombre", "?")[:19]
            cant_s = f"{cant:.3f}" if cant != int(cant) else str(int(cant))
            lines.append(f"{desc:<20}{cant_s:>7}${precio:>6.2f}{imp:>8.2f}")

        total  = float(v.get("total", 0))
        pagado = float(v.get("monto_pagado") or total)
        cambio = float(v.get("cambio") or 0)
        lines += [
            linea,
            f"{'TOTAL':>{W-9}}  ${total:>7.2f}",
            f"{'PAGÓ':>{W-9}}  ${pagado:>7.2f}",
            f"{'CAMBIO':>{W-9}}  ${cambio:>7.2f}",
            linea,
            f"{'*** REIMPRESIÓN ***':^{W}}",
            f"{'¡Gracias por su compra!':^{W}}",
            "", "",
        ]
        contenido = "\n".join(lines)

        prev = ctk.CTkToplevel(self)
        prev.title(f"🖨 Reimprimir — {v['folio']}")
        prev.geometry("420x520"); prev.grab_set()
        prev.configure(fg_color=COLORES["bg_dark"])

        hdr_w = ctk.CTkFrame(prev, fg_color=COLORES["primary"], corner_radius=0, height=40)
        hdr_w.pack(fill="x")
        ctk.CTkLabel(hdr_w, text=f"REIMPRIMIR — {v['folio']}",
                     font=("Segoe UI", 12, "bold"),
                     text_color="white").pack(side="left", padx=14, pady=8)

        papel = ctk.CTkFrame(prev, fg_color="white", corner_radius=8)
        papel.pack(fill="both", expand=True, padx=14, pady=10)
        sb = tk.Scrollbar(papel, orient="vertical"); sb.pack(side="right", fill="y")
        txt_w = tk.Text(papel, font=("Courier New", 10), bg="white", fg="black",
                        relief="flat", padx=8, pady=8, wrap="none", yscrollcommand=sb.set)
        sb.configure(command=txt_w.yview); txt_w.pack(fill="both", expand=True)
        txt_w.insert("1.0", contenido); txt_w.configure(state="disabled")

        br = ctk.CTkFrame(prev, fg_color="transparent")
        br.pack(fill="x", padx=14, pady=(0, 12))

        def _imprimir():
            import tempfile, os
            try:
                with tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                                  delete=False, encoding="utf-8") as f:
                    f.write(contenido); tmp = f.name
                if _ES_MAC: os.system(f'lp "{tmp}"')
                elif platform.system() == "Windows": os.startfile(tmp, "print")
                else: os.system(f'lp "{tmp}"')
                prev.destroy()
                messagebox.showinfo("✅ Enviado", "Ticket enviado a la impresora.")
            except Exception as e:
                messagebox.showwarning("Error", f"No se pudo imprimir:\n{e}")

        ctk.CTkButton(br, text="🖨 Imprimir", height=36,
                      fg_color=COLORES["success"], font=("Segoe UI", 12, "bold"),
                      command=_imprimir).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(br, text="✕ Cerrar", height=36,
                      fg_color=COLORES["secondary"], font=("Segoe UI", 12, "bold"),
                      command=prev.destroy).pack(side="left", fill="x", expand=True)

    # ── Devolución ────────────────────────────────────────────────────────────
    def _solicitar_clave_supervisor(self, venta):
        dialog = ctk.CTkToplevel(self)
        dialog.title("🔐 Autorización de Supervisor")
        dialog.geometry("420x300"); dialog.resizable(False, False)
        dialog.grab_set(); dialog.configure(fg_color=COLORES["bg_dark"])
        dialog.lift(); dialog.after(100, dialog.lift)

        hdr = ctk.CTkFrame(dialog, fg_color=COLORES["warning"], corner_radius=0, height=42)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="🔐  AUTORIZACIÓN REQUERIDA",
                     font=("Segoe UI", 13, "bold"), text_color="white"
                     ).pack(side="left", padx=14, pady=10)

        body = ctk.CTkFrame(dialog, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=14)
        ctk.CTkLabel(body,
                     text=f"Para cancelar {venta['folio']}\n"
                          "se requiere autorización de Supervisor o Administrador.",
                     font=("Segoe UI", 11), text_color=COLORES["text_secondary"],
                     justify="center").pack(pady=(0, 12))

        ctk.CTkLabel(body, text="Usuario:", font=("Segoe UI", 11),
                     text_color=COLORES["text_primary"]).pack(anchor="w")
        entry_user = ctk.CTkEntry(body, height=34, font=("Segoe UI", 12))
        entry_user.pack(fill="x", pady=(2, 8)); entry_user.focus()

        ctk.CTkLabel(body, text="Contraseña:", font=("Segoe UI", 11),
                     text_color=COLORES["text_primary"]).pack(anchor="w")
        entry_pass = ctk.CTkEntry(body, height=34, font=("Segoe UI", 12), show="●")
        entry_pass.pack(fill="x", pady=(2, 12))

        def _verificar(event=None):
            usuario_str = entry_user.get().strip()
            password    = entry_pass.get()
            if not usuario_str or not password:
                messagebox.showwarning("Error", "Ingresa usuario y contraseña.", parent=dialog); return
            try:
                import hashlib
                from app.database.connection import Database
                db   = Database.get_instance()
                hpwd = hashlib.sha256(password.encode()).hexdigest()
                user = db.fetch_one("""
                    SELECT u.*, r.nombre AS rol_nombre FROM usuarios u
                    LEFT JOIN roles r ON u.rol_id = r.id
                    WHERE u.usuario=%s AND u.password=%s AND u.activo=1
                """, (usuario_str, hpwd))
                if not user:
                    messagebox.showwarning("Credenciales incorrectas",
                        "Usuario o contraseña inválidos.", parent=dialog); return
                perms = [p["permiso_clave"] for p in db.fetch_all(
                    "SELECT permiso_clave FROM permisos_roles WHERE rol_id=%s",
                    (user["rol_id"],))]
                rol = (user.get("rol_nombre") or "").strip().lower()
                if not (rol in ("administrador","supervisor")
                        or "ventas_devolucion" in perms
                        or "ventas_cancelar"   in perms):
                    messagebox.showwarning("Sin autorización",
                        f"'{usuario_str}' no tiene permiso.", parent=dialog); return
                dialog.destroy()
                self._ejecutar_devolucion(venta, user["nombre"])
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo verificar:\n{e}", parent=dialog)

        entry_pass.bind("<Return>", _verificar)
        br = ctk.CTkFrame(body, fg_color="transparent"); br.pack(fill="x")
        ctk.CTkButton(br, text="✅ Autorizar devolución", height=36,
                      fg_color=COLORES["warning"], font=("Segoe UI", 12, "bold"),
                      command=_verificar).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(br, text="❌ Cancelar", height=36,
                      fg_color=COLORES["secondary"], font=("Segoe UI", 12, "bold"),
                      command=dialog.destroy).pack(side="left", fill="x", expand=True)

    def _ejecutar_devolucion(self, venta, autorizado_por):
        self.model.cancelar(venta["id"])
        messagebox.showinfo("✅ Devolución realizada",
            f"Venta {venta['folio']} cancelada.\n"
            f"Inventario restaurado.\n"
            f"Autorizado por: {autorizado_por}")
        self._expandidos.discard(venta["id"])
        self._cargar_ventas()
