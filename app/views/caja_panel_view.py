"""
caja_panel_view.py
Panel de caja con:
  - Tarjetas de resumen
  - Botones entrada / salida / ticket de corte / cerrar caja
  - Tabla de movimientos con Hora, Tipo, Monto, Concepto y Usuario
  - Ticket de corte del día que se registra como movimiento
"""
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from app.models.caja_model import CajaModel
from app.utils import session
from app.utils.config import COLORES, APP_NOMBRE, APP_VERSION


class CajaPanelView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.model = CajaModel()
        self._build()

    # ── Layout principal ──────────────────────────────────────────────────────
    def _build(self):
        sesion  = session.get_sesion_caja()
        resumen = self.model.get_resumen_sesion(sesion["id"])

        ef  = float(resumen.get("total_efectivo", 0) or 0)
        tj  = float(resumen.get("total_tarjeta", 0) or 0)
        tr_ = float(resumen.get("total_transferencia", 0) or 0)
        fi  = float(sesion.get("fondo_inicial", 0) or 0)
        en  = float(resumen.get("entradas_extra", 0) or 0)
        sa  = float(resumen.get("salidas_extra", 0) or 0)
        total_caja = fi + ef + en - sa

        # Título
        ctk.CTkLabel(self, text="💰  Panel de Caja",
                     font=("Segoe UI", 20, "bold"),
                     text_color=COLORES["text_primary"]
                     ).pack(padx=20, pady=(16, 8), anchor="w")

        # Tarjetas resumen
        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.pack(fill="x", padx=20, pady=4)
        for lbl, val, color in [
            ("💵 Fondo inicial",    f"${fi:.2f}",         COLORES["text_secondary"]),
            ("🛒 Ventas efectivo",  f"${ef:.2f}",         COLORES["success"]),
            ("💳 Tarjeta",          f"${tj:.2f}",         COLORES["primary"]),
            ("📲 Transferencia",    f"${tr_:.2f}",        COLORES["warning"]),
            ("📦 Total en caja",    f"${total_caja:.2f}", COLORES["success"]),
        ]:
            card = ctk.CTkFrame(cards, fg_color=COLORES["bg_dark"],
                                corner_radius=10, width=150)
            card.pack(side="left", padx=6, pady=4)
            ctk.CTkLabel(card, text=val, font=("Segoe UI", 16, "bold"),
                         text_color=color).pack(padx=14, pady=(10, 2))
            ctk.CTkLabel(card, text=lbl, font=("Segoe UI", 10),
                         text_color=COLORES["text_secondary"]).pack(padx=14, pady=(0, 10))

        # Botones de acción
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=8)

        ctk.CTkButton(btn_row, text="➕ Entrada de efectivo", height=36,
                      fg_color=COLORES["success"],
                      command=lambda: self._movimiento("entrada")
                      ).pack(side="left", padx=4)

        ctk.CTkButton(btn_row, text="➖ Salida de efectivo", height=36,
                      fg_color=COLORES["danger"],
                      command=lambda: self._movimiento("salida")
                      ).pack(side="left", padx=4)

        ctk.CTkButton(btn_row, text="🧾 Ticket de corte", height=36,
                      fg_color=COLORES["secondary"],
                      font=("Segoe UI", 11, "bold"),
                      command=self._ticket_corte
                      ).pack(side="left", padx=4)

        ctk.CTkButton(btn_row, text="🔒 Cerrar Caja", height=36,
                      fg_color=COLORES["warning"], hover_color="#B45309",
                      command=self._cerrar_caja
                      ).pack(side="right", padx=4)

        # Tabla de movimientos
        ctk.CTkLabel(self, text="Movimientos del turno",
                     font=("Segoe UI", 13, "bold"),
                     text_color=COLORES["text_primary"]
                     ).pack(padx=20, anchor="w")

        tabla = ctk.CTkFrame(self, fg_color=COLORES["bg_dark"], corner_radius=12)
        tabla.pack(fill="both", expand=True, padx=20, pady=8)
        tabla.rowconfigure(1, weight=1)
        tabla.columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(tabla, fg_color=COLORES["primary"],
                           corner_radius=6, height=32)
        hdr.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        for txt, w in [("Fecha y Hora", 160), ("Tipo", 110),
                       ("Monto", 100), ("Concepto", 280), ("Usuario", 140)]:
            ctk.CTkLabel(hdr, text=txt, font=("Segoe UI", 11, "bold"),
                         text_color="white", width=w, anchor="w"
                         ).pack(side="left", padx=6)

        scroll = ctk.CTkScrollableFrame(tabla, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)

        movs = self.model.get_movimientos(sesion["id"])

        if not movs:
            ctk.CTkLabel(scroll, text="Sin movimientos en este turno.",
                         font=("Segoe UI", 11),
                         text_color=COLORES["text_secondary"]).pack(pady=16)
        else:
            for i, m in enumerate(movs):
                bg  = COLORES["bg_card"] if i % 2 == 0 else "transparent"
                row = ctk.CTkFrame(scroll, fg_color=bg, corner_radius=4, height=30)
                row.pack(fill="x", pady=1)

                # Fecha y hora completa
                fecha_raw = str(m.get("fecha", ""))
                try:
                    dt = datetime.strptime(fecha_raw[:19], "%Y-%m-%d %H:%M:%S")
                    DIAS  = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
                    MESES = ["ene","feb","mar","abr","may","jun",
                             "jul","ago","sep","oct","nov","dic"]
                    fecha_str = (f"{DIAS[dt.weekday()]} {dt.day} {MESES[dt.month-1]}"
                                 f"  {dt.strftime('%H:%M:%S')}")
                except Exception:
                    fecha_str = fecha_raw[:19]

                tipo  = m["tipo"]
                color = COLORES["success"] if tipo == "entrada" else COLORES["danger"]
                usuario_nombre = m.get("usuario_nombre") or "—"

                for txt, w, tc in [
                    (fecha_str,            160, COLORES["text_secondary"]),
                    (tipo.capitalize(),    110, color),
                    (f"${float(m['monto']):.2f}", 100, color),
                    (m.get("concepto","") or "—", 280, COLORES["text_primary"]),
                    (usuario_nombre,       140, COLORES["text_secondary"]),
                ]:
                    ctk.CTkLabel(row, text=str(txt), font=("Segoe UI", 11),
                                 text_color=tc, width=w, anchor="w"
                                 ).pack(side="left", padx=6)

    # ── Movimiento de caja (entrada / salida) ─────────────────────────────────
    def _movimiento(self, tipo):
        win = ctk.CTkToplevel(self)
        win.title("Movimiento de caja")
        win.geometry("380x280")
        win.configure(fg_color=COLORES["bg_dark"])
        win.protocol("WM_DELETE_WINDOW", lambda: [win.grab_release(), win.destroy()])

        titulo = "➕ Entrada de efectivo" if tipo == "entrada" else "➖ Salida de efectivo"
        color  = COLORES["success"] if tipo == "entrada" else COLORES["danger"]

        ctk.CTkLabel(win, text=titulo, font=("Segoe UI", 16, "bold"),
                     text_color=color).pack(pady=(20, 12), padx=20, anchor="w")

        frame = ctk.CTkFrame(win, fg_color=COLORES["bg_card"], corner_radius=12)
        frame.pack(fill="x", padx=20)

        ctk.CTkLabel(frame, text="Monto ($)", font=("Segoe UI", 11),
                     text_color=COLORES["text_secondary"]
                     ).pack(anchor="w", padx=16, pady=(16, 2))
        entry_monto = ctk.CTkEntry(frame, height=36)
        entry_monto.pack(fill="x", padx=16)

        ctk.CTkLabel(frame, text="Concepto", font=("Segoe UI", 11),
                     text_color=COLORES["text_secondary"]
                     ).pack(anchor="w", padx=16, pady=(10, 2))
        entry_concepto = ctk.CTkEntry(frame, height=36)
        entry_concepto.pack(fill="x", padx=16, pady=(0, 16))

        def guardar():
            try:
                monto = float(entry_monto.get())
            except ValueError:
                messagebox.showwarning("Error", "Monto inválido")
                return
            concepto = entry_concepto.get().strip()
            if not concepto:
                messagebox.showwarning("Error", "Escribe un concepto.")
                return
            sesion  = session.get_sesion_caja()
            usuario = session.get_usuario()
            self.model.registrar_movimiento(
                sesion["id"], tipo, monto, concepto, usuario["id"])
            win.grab_release()
            win.destroy()
            for w in self.winfo_children():
                w.destroy()
            self._build()

        win.grab_set()
        ctk.CTkButton(win, text="✅ Registrar", height=40,
                      fg_color=color, command=guardar
                      ).pack(fill="x", padx=20, pady=12)

    # ── Ticket de corte del día ───────────────────────────────────────────────
    def _ticket_corte(self):
        """Genera, muestra e imprime el ticket de corte de caja del día."""
        sesion   = session.get_sesion_caja()
        resumen  = self.model.get_resumen_sesion(sesion["id"])
        usuario  = session.get_usuario()
        movs     = self.model.get_movimientos(sesion["id"])
        ahora    = datetime.now()

        # Leer nombre del negocio
        try:
            from app.database.connection import Database
            db  = Database.get_instance()
            cfg = {r["clave"]: r["valor"]
                   for r in db.fetch_all("SELECT clave, valor FROM configuracion")}
            nombre_negocio = cfg.get("nombre_negocio") or APP_NOMBRE
            telefono       = cfg.get("telefono") or ""
        except Exception:
            nombre_negocio = APP_NOMBRE
            telefono       = ""

        ef  = float(resumen.get("total_efectivo", 0) or 0)
        tj  = float(resumen.get("total_tarjeta", 0) or 0)
        tr_ = float(resumen.get("total_transferencia", 0) or 0)
        fi  = float(sesion.get("fondo_inicial", 0) or 0)
        en  = float(resumen.get("entradas_extra", 0) or 0)
        sa  = float(resumen.get("salidas_extra", 0) or 0)
        total_caja = fi + ef + en - sa
        num_ventas = int(resumen.get("total_ventas", 0) or 0)

        fecha_apertura = str(sesion.get("fecha_apertura", ""))[:16]
        fecha_corte    = ahora.strftime("%d/%m/%Y  %H:%M:%S")

        DIAS  = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
        MESES = ["ene","feb","mar","abr","may","jun",
                 "jul","ago","sep","oct","nov","dic"]
        dia_semana = (f"{DIAS[ahora.weekday()]} {ahora.day} de "
                      f"{MESES[ahora.month - 1]} {ahora.year}")

        linea = "=" * 42
        sep   = "-" * 42

        lines = [
            f"{nombre_negocio:^42}",
            f"{('Tel: ' + telefono) if telefono else ('v' + APP_VERSION):^42}",
            linea,
            f"{'*** CORTE DE CAJA ***':^42}",
            linea,
            f"Fecha    : {dia_semana}",
            f"Hora     : {ahora.strftime('%H:%M:%S')}",
            f"Cajero   : {usuario['nombre'] if usuario else '—'}",
            f"Apertura : {fecha_apertura}",
            sep,
            f"{'VENTAS DEL TURNO':^42}",
            sep,
            f"Num. ventas      : {num_ventas}",
            f"Efectivo ventas  : ${ef:>10.2f}",
            f"Tarjeta          : ${tj:>10.2f}",
            f"Transferencia    : ${tr_:>10.2f}",
            sep,
            f"{'MOVIMIENTOS DE EFECTIVO':^42}",
            sep,
            f"Fondo inicial    : ${fi:>10.2f}",
            f"Entradas extra   : ${en:>10.2f}",
            f"Salidas extra    : ${sa:>10.2f}",
            sep,
            f"{'TOTAL EN CAJA':^42}",
            f"${total_caja:>40.2f}",
            sep,
        ]

        # Detalle de movimientos
        if movs:
            lines.append(f"{'DETALLE MOVIMIENTOS':^42}")
            lines.append(sep)
            for m in movs:
                h   = str(m.get("fecha", ""))
                try:
                    h = datetime.strptime(h[:19], "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
                except Exception:
                    h = h[-8:][:5]
                tipo    = "ENT" if m["tipo"] == "entrada" else "SAL"
                monto   = float(m.get("monto", 0))
                usuario_mov = (m.get("usuario_nombre") or "—")[:12]
                concepto = (m.get("concepto") or "—")[:20]
                lines.append(
                    f"{h}  {tipo}  ${monto:>8.2f}  {concepto:<20}  {usuario_mov}"
                )
            lines.append(sep)

        lines += [
            f"{'Impreso: ' + fecha_corte:^42}",
            f"{'Por: ' + (usuario['nombre'] if usuario else '—'):^42}",
            "",
            "",
        ]

        contenido = "\n".join(lines)

        # ── Vista previa del ticket ──────────────────────────────────────────
        win = ctk.CTkToplevel(self)
        win.title("🧾 Ticket de Corte")
        win.geometry("460x600")
        win.configure(fg_color=COLORES["bg_dark"])
        win.protocol("WM_DELETE_WINDOW", lambda: [win.grab_release(), win.destroy()])

        hdr = ctk.CTkFrame(win, fg_color=COLORES["primary"], corner_radius=0, height=44)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="TICKET DE CORTE DE CAJA",
                     font=("Segoe UI", 13, "bold"),
                     text_color="white").pack(side="left", padx=16, pady=10)

        # Área de texto tipo papel
        ticket_frame = ctk.CTkFrame(win, fg_color="white", corner_radius=8)
        ticket_frame.pack(fill="both", expand=True, padx=16, pady=12)
        import tkinter as tk
        txt = tk.Text(ticket_frame, font=("Courier New", 10),
                      bg="white", fg="black",
                      relief="flat", padx=8, pady=8,
                      wrap="none", state="normal")
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", contenido)
        txt.configure(state="disabled")

        def _imprimir():
            import tempfile, os, platform
            try:
                with tempfile.NamedTemporaryFile(
                        mode="w", suffix=".txt",
                        delete=False, encoding="utf-8") as f:
                    f.write(contenido)
                    tmp = f.name
                if platform.system() == "Darwin":
                    os.system(f'lp "{tmp}"')
                elif platform.system() == "Windows":
                    os.startfile(tmp, "print")
                else:
                    os.system(f'lp "{tmp}"')

                # Registrar en movimientos
                sesion_act = session.get_sesion_caja()
                usr        = session.get_usuario()
                if sesion_act and usr:
                    self.model.registrar_movimiento(
                        sesion_act["id"],
                        "entrada",          # tipo neutro para que no afecte el saldo
                        0.0,
                        f"Ticket de corte impreso — {fecha_corte} — por {usr['nombre']}",
                        usr["id"]
                    )
                messagebox.showinfo("✅ Impreso",
                                    "Ticket enviado a la impresora y\n"
                                    "registrado en movimientos.")
                win.grab_release()
                win.destroy()
                # Refrescar el panel para mostrar el nuevo movimiento
                for w in self.winfo_children():
                    w.destroy()
                self._build()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo imprimir:\n{e}")

        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(btn_row, text="🖨 Imprimir y registrar", height=38,
                      fg_color=COLORES["success"], font=("Segoe UI", 12, "bold"),
                      command=_imprimir
                      ).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(btn_row, text="✕ Cerrar", height=38,
                      fg_color=COLORES["danger"], font=("Segoe UI", 12, "bold"),
                      command=lambda: [win.grab_release(), win.destroy()]
                      ).pack(side="left", fill="x", expand=True)

        win.grab_set()
        win.lift()
        win.focus_force()

    # ── Cerrar caja ───────────────────────────────────────────────────────────
    def _cerrar_caja(self):
        from app.views.caja_view import CierreCajaView

        def _on_cierre():
            widget = self
            while widget is not None:
                if hasattr(widget, "_rebuild"):
                    widget._rebuild()
                    return
                try:
                    widget = widget.master
                except Exception:
                    break

        CierreCajaView(on_success=_on_cierre)
