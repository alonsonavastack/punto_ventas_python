"""
widgets/cobro.py  v1.1
Ventana de cobro — efectivo, tarjeta o transferencia + descuento.
Mejoras v1.1:
  - Botones de billetes rápidos ($10, $20, $50, $100, $200, $500, $1000)
  - Cálculo automático de cambio en tiempo real
  - Botón "Monto exacto" para ahorrar tiempo
  - Soporte visual para granel (muestra artículos con decimales)
  - Teclas F1/F2/ESC funcionan desde cualquier widget
"""
import customtkinter as ctk
from tkinter import messagebox
from app.utils.config import COLORES

# Billetes rápidos MXN
BILLETES_RAPIDOS = [10, 20, 50, 100, 200, 500, 1000]


class CobroWidget(ctk.CTkToplevel):
    def __init__(self, parent, total: float, num_articulos: int, on_cobrar,
                 tiene_granel: bool = False):
        super().__init__(parent)
        self.title("💰 Cobrar")
        self.geometry("600x560")
        self.resizable(False, False)
        self.configure(fg_color=COLORES["bg_dark"])
        self.protocol("WM_DELETE_WINDOW", self._cerrar_seguro)
        self._total_original = total
        self._total          = total
        self._num            = num_articulos
        self._on_cobrar      = on_cobrar
        self._tiene_granel   = tiene_granel
        self._forma_pago     = ctk.StringVar(value="efectivo")
        self._build()
        self.grab_set()
        self.lift()
        self.focus_force()
        self.after(120, lambda: self.entry_pago.focus())

    def _cerrar_seguro(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color=COLORES["primary"], corner_radius=0, height=50)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="💰  COBRAR",
                     font=("Segoe UI", 17, "bold"),
                     text_color="white").pack(side="left", padx=16, pady=12)
        if self._tiene_granel:
            ctk.CTkLabel(hdr, text="⚖ Incluye productos a granel",
                         font=("Segoe UI", 10),
                         text_color="#93c5fd").pack(side="right", padx=14)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=14, pady=10)
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=1)

        # ── Columna izquierda ─────────────────────────────────────────────────
        left = ctk.CTkFrame(body, fg_color=COLORES["bg_card"], corner_radius=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Total
        ctk.CTkLabel(left, text="Total a Cobrar",
                     font=("Segoe UI", 12),
                     text_color=COLORES["text_secondary"]).pack(pady=(14, 2))
        self.lbl_total = ctk.CTkLabel(left, text=f"${self._total:.2f}",
                                       font=("Segoe UI", 34, "bold"),
                                       text_color=COLORES["primary"])
        self.lbl_total.pack(pady=(0, 6))
        ctk.CTkFrame(left, height=1, fg_color=COLORES["border"]).pack(fill="x", padx=16)

        # ── Descuento ─────────────────────────────────────────────────────────
        desc_row = ctk.CTkFrame(left, fg_color="transparent")
        desc_row.pack(fill="x", padx=16, pady=(10, 4))
        ctk.CTkLabel(desc_row, text="Descuento:",
                     font=("Segoe UI", 11),
                     text_color=COLORES["text_secondary"]).pack(side="left")
        self._tipo_desc = ctk.StringVar(value="%")
        ctk.CTkRadioButton(desc_row, text="%", variable=self._tipo_desc, value="%",
                           font=("Segoe UI", 11),
                           command=self._calcular).pack(side="left", padx=(10, 4))
        ctk.CTkRadioButton(desc_row, text="$", variable=self._tipo_desc, value="$",
                           font=("Segoe UI", 11),
                           command=self._calcular).pack(side="left", padx=(0, 8))
        self.entry_desc = ctk.CTkEntry(left, height=30, width=90, font=("Segoe UI", 12),
                                        placeholder_text="0")
        self.entry_desc.pack(anchor="w", padx=16)
        self.entry_desc.bind("<KeyRelease>", self._calcular)
        ctk.CTkFrame(left, height=1, fg_color=COLORES["border"]).pack(fill="x", padx=16, pady=8)

        # ── Forma de pago ─────────────────────────────────────────────────────
        ctk.CTkLabel(left, text="Forma de pago:",
                     font=("Segoe UI", 11),
                     text_color=COLORES["text_secondary"]).pack(anchor="w", padx=16)
        forma_row = ctk.CTkFrame(left, fg_color="transparent")
        forma_row.pack(fill="x", padx=16, pady=4)
        for txt, val in [
            ("💵 Efectivo",      "efectivo"),
            ("💳 Tarjeta",       "tarjeta"),
            ("📲 Transferencia", "transferencia"),
        ]:
            ctk.CTkRadioButton(forma_row, text=txt, variable=self._forma_pago, value=val,
                               font=("Segoe UI", 11),
                               command=self._forma_cambiada).pack(anchor="w", pady=2)
        ctk.CTkFrame(left, height=1, fg_color=COLORES["border"]).pack(fill="x", padx=16, pady=6)

        # ── Pagó con ──────────────────────────────────────────────────────────
        self.lbl_pago_titulo = ctk.CTkLabel(left, text="Pagó con:",
                                             font=("Segoe UI", 12),
                                             text_color=COLORES["text_secondary"])
        self.lbl_pago_titulo.pack(pady=(0, 4))
        self.entry_pago = ctk.CTkEntry(left, height=44, font=("Segoe UI", 22, "bold"),
                                        justify="center")
        self.entry_pago.pack(fill="x", padx=16)
        self.entry_pago.bind("<KeyRelease>", self._calcular_cambio)
        self.entry_pago.bind("<Return>", lambda e: self._cobrar_registrar())

        # ── Cambio ────────────────────────────────────────────────────────────
        self.lbl_cambio = ctk.CTkLabel(left, text="Cambio: $0.00",
                                        font=("Segoe UI", 15, "bold"),
                                        text_color=COLORES["success"])
        self.lbl_cambio.pack(pady=(6, 4))

        # ── Billetes rápidos ──────────────────────────────────────────────────
        self.frame_billetes = ctk.CTkFrame(left, fg_color="transparent")
        self.frame_billetes.pack(fill="x", padx=12, pady=(2, 10))

        ctk.CTkLabel(self.frame_billetes, text="Billetes rápidos:",
                     font=("Segoe UI", 9, "bold"),
                     text_color=COLORES["text_secondary"]).pack(anchor="w", padx=4)

        btn_row = ctk.CTkFrame(self.frame_billetes, fg_color="transparent")
        btn_row.pack(fill="x")

        # Botón de exacto
        ctk.CTkButton(btn_row, text="✓ Exacto", width=60, height=26,
                      fg_color=COLORES["success"], hover_color=COLORES["stock_ok"],
                      font=("Segoe UI", 9, "bold"),
                      command=self._pago_exacto).pack(side="left", padx=2)

        for billete in BILLETES_RAPIDOS:
            b = billete  # closure
            ctk.CTkButton(btn_row,
                          text=f"${billete}" if billete < 1000 else "$1k",
                          width=44, height=26,
                          fg_color=COLORES["bg_input"],
                          hover_color=COLORES["primary"],
                          font=("Segoe UI", 9, "bold"),
                          command=lambda x=b: self._pago_billete(x)
                          ).pack(side="left", padx=2)

        # ── Columna derecha — botones ─────────────────────────────────────────
        right = ctk.CTkFrame(body, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")

        ctk.CTkButton(right, text="F1 — Cobrar e\nImprimir Ticket",
                      height=60, font=("Segoe UI", 11, "bold"),
                      fg_color=COLORES["success"],
                      command=lambda: self._cobrar_registrar(imprimir=True)
                      ).pack(fill="x", pady=4)
        ctk.CTkButton(right, text="F2 — Cobrar sin\nImprimir",
                      height=60, font=("Segoe UI", 11, "bold"),
                      fg_color=COLORES["primary"],
                      command=self._cobrar_registrar
                      ).pack(fill="x", pady=4)
        ctk.CTkButton(right, text="ESC — Cancelar",
                      height=40, font=("Segoe UI", 11),
                      fg_color=COLORES["danger"],
                      command=self._cerrar_seguro
                      ).pack(fill="x", pady=4)

        ctk.CTkFrame(right, height=1, fg_color=COLORES["border"]).pack(fill="x", pady=8)

        arts_label = f"Artículos: {self._num}"
        ctk.CTkLabel(right, text=arts_label,
                     font=("Segoe UI", 12, "bold"),
                     text_color=COLORES["text_primary"],
                     justify="center").pack(pady=4)

        if self._tiene_granel:
            ctk.CTkLabel(right, text="⚖ Incluye\nproductos\na granel",
                         font=("Segoe UI", 9),
                         text_color=COLORES["granel"],
                         justify="center").pack(pady=4)

        # ── Teclado numérico rápido ───────────────────────────────────────────
        teclado = ctk.CTkFrame(right, fg_color=COLORES["bg_card"], corner_radius=8)
        teclado.pack(fill="x", pady=6)
        nums = [["7","8","9"],["4","5","6"],["1","2","3"],["⌫","0","."]]
        for fila in nums:
            r = ctk.CTkFrame(teclado, fg_color="transparent")
            r.pack(fill="x", padx=4, pady=2)
            for d in fila:
                d_ = d
                color = COLORES["danger"] if d == "⌫" else COLORES["bg_input"]
                ctk.CTkButton(r, text=d, width=42, height=34,
                              fg_color=color, font=("Segoe UI", 13, "bold"),
                              command=lambda x=d_: self._teclado(x)
                              ).pack(side="left", padx=2)

        self.bind("<F1>", lambda e: self._cobrar_registrar(imprimir=True))
        self.bind("<F2>", lambda e: self._cobrar_registrar())
        self.bind("<Escape>", lambda e: self._cerrar_seguro())

        self._forma_cambiada()

    # ── Teclado numérico ──────────────────────────────────────────────────────
    def _teclado(self, char):
        if char == "⌫":
            val = self.entry_pago.get()
            self.entry_pago.delete(0, "end")
            self.entry_pago.insert(0, val[:-1])
        else:
            current = self.entry_pago.get()
            # Evitar doble punto
            if char == "." and "." in current:
                return
            self.entry_pago.insert("end", char)
        self._calcular_cambio()

    # ── Billetes rápidos ──────────────────────────────────────────────────────
    def _pago_exacto(self):
        self.entry_pago.delete(0, "end")
        self.entry_pago.insert(0, f"{self._total:.2f}")
        self._calcular_cambio()
        self.entry_pago.focus()

    def _pago_billete(self, valor):
        """Establece el billete como monto pagado (si es >= total) o acumula."""
        try:
            actual = float(self.entry_pago.get() or 0)
        except ValueError:
            actual = 0
        # Si el campo está vacío o tiene el valor exacto del total, usa el billete directo
        if actual == 0 or abs(actual - self._total) < 0.01:
            nuevo = float(valor)
        else:
            nuevo = actual + float(valor)
        self.entry_pago.delete(0, "end")
        self.entry_pago.insert(0, f"{nuevo:.2f}")
        self._calcular_cambio()
        self.entry_pago.focus()

    # ── Descuento ─────────────────────────────────────────────────────────────
    def _calcular(self, event=None):
        try:
            val = float(self.entry_desc.get() or 0)
        except ValueError:
            val = 0
        if self._tipo_desc.get() == "%":
            desc = self._total_original * val / 100
        else:
            desc = val
        desc = max(0, min(desc, self._total_original))
        self._total = round(self._total_original - desc, 2)
        self.lbl_total.configure(text=f"${self._total:.2f}")
        self._resetear_pago()
        self._calcular_cambio()

    def _resetear_pago(self):
        self.entry_pago.delete(0, "end")
        self.entry_pago.insert(0, f"{self._total:.2f}")

    # ── Forma de pago ─────────────────────────────────────────────────────────
    def _forma_cambiada(self):
        forma = self._forma_pago.get()
        self._resetear_pago()
        if forma == "efectivo":
            self.lbl_pago_titulo.configure(text="Pagó con:")
            self.entry_pago.configure(state="normal")
            self.lbl_cambio.pack()
            self.frame_billetes.pack(fill="x", padx=12, pady=(2, 10))
        else:
            self.lbl_pago_titulo.configure(text="No. de referencia / autorización (opcional):")
            self.entry_pago.configure(state="normal")
            self.entry_pago.delete(0, "end")
            self.lbl_cambio.configure(text="")
            self.frame_billetes.pack_forget()
        self._calcular_cambio()

    # ── Cambio en tiempo real ─────────────────────────────────────────────────
    def _calcular_cambio(self, event=None):
        if self._forma_pago.get() != "efectivo":
            self.lbl_cambio.configure(text="")
            return
        try:
            pagado = float(self.entry_pago.get())
            cambio = round(pagado - self._total, 2)
            if cambio >= 0:
                self.lbl_cambio.configure(
                    text=f"Cambio: ${cambio:.2f}",
                    text_color=COLORES["success"])
            else:
                self.lbl_cambio.configure(
                    text=f"Faltan: ${abs(cambio):.2f}",
                    text_color=COLORES["danger"])
        except ValueError:
            self.lbl_cambio.configure(text="Cambio: $0.00",
                                       text_color=COLORES["text_secondary"])

    # ── Registrar cobro ───────────────────────────────────────────────────────
    def _cobrar_registrar(self, imprimir=False):
        forma = self._forma_pago.get()
        if forma == "efectivo":
            try:
                pagado = float(self.entry_pago.get())
            except ValueError:
                messagebox.showwarning("Error", "Ingresa un monto válido.")
                return
            if pagado < self._total:
                messagebox.showwarning(
                    "Pago insuficiente",
                    f"El monto (${pagado:.2f}) es menor al total (${self._total:.2f}).")
                return
        else:
            pagado = self._total

        try:
            val_desc = float(self.entry_desc.get() or 0)
        except ValueError:
            val_desc = 0
        if self._tipo_desc.get() == "%":
            descuento = round(self._total_original * val_desc / 100, 2)
        else:
            descuento = round(val_desc, 2)
        descuento = max(0, min(descuento, self._total_original))

        self._cerrar_seguro()
        self._on_cobrar(pagado, imprimir, forma, descuento)
