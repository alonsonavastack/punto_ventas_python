"""
widgets/busqueda_producto.py  v1.2
Búsqueda de productos — compatible Mac/Win/Linux.
Fix v1.2: eliminado nombre_frame con pack_propagate(False) que causaba
  que las filas tuvieran height 0 en Mac. Ahora se usa grid() para el
  layout interno de cada fila, lo que es más robusto.
"""
import customtkinter as ctk
from app.utils.config import COLORES


class BusquedaProductoWidget(ctk.CTkToplevel):
    UNIDADES_GRANEL = {"KG", "GR", "G", "LB", "LT", "L", "ML"}

    def __init__(self, parent, on_seleccionar, productos=None):
        super().__init__(parent)
        self.title("🔍 Búsqueda de Productos")
        self.geometry("680x500")
        self.resizable(True, True)
        self.minsize(580, 380)
        self.grab_set()
        self.configure(fg_color=COLORES["bg_dark"])
        self._on_sel  = on_seleccionar
        self._todos   = productos or []
        self._sel     = None
        self._filas   = []
        self._idx_sel = -1
        self._build()
        self.after(20, self._centrar_ventana)
        self.after(120, lambda: self.entry_buscar.focus())

    def _centrar_ventana(self):
        try:
            self.update_idletasks()
            w = self.winfo_width()
            h = self.winfo_height()
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            x = max(0, (sw - w) // 2)
            y = max(0, (sh - h) // 2)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

    def _es_granel(self, prod) -> bool:
        return (prod.get("unidad") or "PZA").strip().upper() in self.UNIDADES_GRANEL

    def _build(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color=COLORES["primary"], corner_radius=0, height=48)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="🔍  BÚSQUEDA DE PRODUCTOS",
                     font=("Segoe UI", 14, "bold"),
                     text_color="white").pack(side="left", padx=16, pady=12)
        ctk.CTkLabel(hdr, text="↑↓ navegar   Enter seleccionar   Esc cerrar",
                     font=("Segoe UI", 9), text_color="#93c5fd").pack(side="right", padx=14)

        # ── Barra de búsqueda ─────────────────────────────────────────────────
        busq = ctk.CTkFrame(self, fg_color="transparent")
        busq.pack(fill="x", padx=14, pady=(10, 4))
        busq.columnconfigure(0, weight=1)
        self.entry_buscar = ctk.CTkEntry(busq, height=38,
                                          font=("Segoe UI", 13),
                                          placeholder_text="Nombre, código de barras o clave...")
        self.entry_buscar.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.entry_buscar.bind("<KeyRelease>", self._filtrar)
        self.entry_buscar.bind("<Return>",     self._aceptar)
        self.entry_buscar.bind("<Down>",       lambda e: self._mover_sel(1))
        self.entry_buscar.bind("<Up>",         lambda e: self._mover_sel(-1))
        ctk.CTkButton(busq, text="Buscar", width=80, height=38,
                      fg_color=COLORES["primary"], font=("Segoe UI", 11, "bold"),
                      command=self._filtrar).grid(row=0, column=1)

        # Contador
        self.lbl_count = ctk.CTkLabel(self, text="", font=("Segoe UI", 10),
                                       text_color=COLORES["text_secondary"])
        self.lbl_count.pack(anchor="w", padx=16)

        # ── Cabecera de tabla ─────────────────────────────────────────────────
        hdr_t = ctk.CTkFrame(self, fg_color=COLORES["bg_card"], corner_radius=0, height=28)
        hdr_t.pack(fill="x", padx=14)
        # Anchos de columna
        self._CW = (260, 80, 76, 64, 74, 100)
        for txt, w in zip(["Descripción", "Precio V.", "Mayoreo", "Unidad", "Exist.", "Categoría"],
                           self._CW):
            ctk.CTkLabel(hdr_t, text=txt, font=("Segoe UI", 10, "bold"),
                         text_color=COLORES["text_secondary"],
                         width=w, anchor="w").pack(side="left", padx=6, pady=3)

        # ── Lista con scroll — usamos tk.Canvas+Frame para Mac ────────────────
        import tkinter as tk

        list_container = ctk.CTkFrame(self, fg_color=COLORES["bg_dark"], corner_radius=0)
        list_container.pack(fill="both", expand=True, padx=14, pady=4)

        self._canvas = tk.Canvas(list_container,
                                  bg=COLORES["bg_dark"],
                                  highlightthickness=0)
        self._scrollbar = tk.Scrollbar(list_container, orient="vertical",
                                        command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self._scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self.lista = tk.Frame(self._canvas, bg=COLORES["bg_dark"])
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self.lista, anchor="nw")

        self.lista.bind("<Configure>", self._on_lista_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # Scroll con trackpad/rueda en Mac
        self._canvas.bind("<MouseWheel>", self._on_wheel)
        self._canvas.bind("<Button-4>",   lambda e: self._canvas.yview_scroll(-2, "units"))
        self._canvas.bind("<Button-5>",   lambda e: self._canvas.yview_scroll( 2, "units"))

        # Botones inferiores
        bot = ctk.CTkFrame(self, fg_color=COLORES["bg_card"], corner_radius=0, height=46)
        bot.pack(fill="x", padx=14, pady=(0, 6))
        bot.pack_propagate(False)
        ctk.CTkButton(bot, text="✅  ENTER — Agregar al ticket",
                      height=34, fg_color=COLORES["success"],
                      font=("Segoe UI", 11, "bold"),
                      command=self._aceptar).pack(side="left", padx=8, pady=6)
        ctk.CTkButton(bot, text="❌  ESC — Cerrar",
                      height=34, fg_color=COLORES["danger"],
                      font=("Segoe UI", 11, "bold"),
                      command=self.destroy).pack(side="right", padx=8)

        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Return>", self._aceptar)
        self._filtrar()

    def _on_lista_configure(self, event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_wheel(self, event):
        import platform
        if platform.system() == "Darwin":
            self._canvas.yview_scroll(int(-event.delta / 10), "units")
        else:
            self._canvas.yview_scroll(int(-event.delta / 120), "units")

    # ── Filtrar lista ─────────────────────────────────────────────────────────
    def _filtrar(self, event=None):
        import tkinter as tk
        termino = self.entry_buscar.get().strip().lower()

        # Limpiar lista anterior
        for w in self.lista.winfo_children():
            w.destroy()
        self._filas   = []
        self._idx_sel = -1

        if termino:
            filtrados = [p for p in self._todos
                         if termino in p.get("nombre","").lower()
                         or termino in (p.get("codigo_barras","") or "").lower()
                         or termino in (p.get("clave_interna","") or "").lower()
                         or termino == "%"]
        else:
            filtrados = self._todos[:100]

        mostrados = filtrados[:100]
        n = len(filtrados)
        self.lbl_count.configure(
            text=f"{n} producto{'s' if n != 1 else ''} encontrado{'s' if n != 1 else ''}"
                 + ("  (mostrando primeros 100)" if n > 100 else ""))

        CW = self._CW

        for i, p in enumerate(mostrados):
            granel     = self._es_granel(p)
            existencia = float(p.get("existencia", 0) or 0)
            sin_stock  = existencia <= 0
            mayoreo    = float(p.get("precio_mayoreo") or 0)

            bg = COLORES["bg_card"] if i % 2 == 0 else COLORES["bg_dark"]

            row = tk.Frame(self.lista, bg=bg, cursor="hand2", height=30)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)  # fijar altura de la fila

            # Columna nombre
            nombre_txt = ("⚖ " if granel else "") + p.get("nombre","")[:36]
            nc = COLORES["text_secondary"] if sin_stock else (
                 COLORES["granel"] if granel else COLORES["text_primary"])
            lbl_n = tk.Label(row, text=nombre_txt, bg=bg, fg=nc,
                             font=("Segoe UI", 11), width=0, anchor="w")
            lbl_n.place(x=6, y=5, width=CW[0]-6)

            # Precio venta
            lbl_p = tk.Label(row, text=f"${float(p.get('precio_venta',0)):.2f}",
                             bg=bg, fg=COLORES["success"],
                             font=("Segoe UI", 11), anchor="w")
            lbl_p.place(x=CW[0]+6, y=5, width=CW[1]-6)

            # Mayoreo
            m_txt   = f"${mayoreo:.2f}" if mayoreo > 0 else "—"
            m_color = COLORES["mayoreo"] if mayoreo > 0 else COLORES["text_secondary"]
            lbl_m = tk.Label(row, text=m_txt, bg=bg, fg=m_color,
                             font=("Segoe UI", 11), anchor="w")
            lbl_m.place(x=CW[0]+CW[1]+6, y=5, width=CW[2]-6)

            # Unidad
            unidad  = (p.get("unidad") or "PZA").strip().upper()
            uc      = COLORES["granel"] if granel else COLORES["text_secondary"]
            lbl_u = tk.Label(row, text=unidad, bg=bg, fg=uc,
                             font=("Segoe UI", 10, "bold"), anchor="w")
            lbl_u.place(x=CW[0]+CW[1]+CW[2]+6, y=5, width=CW[3]-6)

            # Existencia
            exist_txt = f"{existencia:.2f}" if granel else str(int(existencia))
            ec = (COLORES["stock_cero"] if sin_stock
                  else COLORES["stock_bajo"] if existencia <= float(p.get("existencia_min",0) or 0)
                  else COLORES["stock_ok"])
            lbl_e = tk.Label(row, text=exist_txt, bg=bg, fg=ec,
                             font=("Segoe UI", 11, "bold"), anchor="w")
            lbl_e.place(x=CW[0]+CW[1]+CW[2]+CW[3]+6, y=5, width=CW[4]-6)

            # Categoría
            cat = (p.get("categoria_nombre") or "—")[:14]
            lbl_c = tk.Label(row, text=cat, bg=bg, fg=COLORES["text_secondary"],
                             font=("Segoe UI", 10), anchor="w")
            lbl_c.place(x=CW[0]+CW[1]+CW[2]+CW[3]+CW[4]+6, y=5, width=CW[5]-6)

            # Scroll wheel en cada fila
            row.bind("<MouseWheel>", self._on_wheel)
            row.bind("<Button-4>",   lambda e: self._canvas.yview_scroll(-2, "units"))
            row.bind("<Button-5>",   lambda e: self._canvas.yview_scroll( 2, "units"))
            for lbl in (lbl_n, lbl_p, lbl_m, lbl_u, lbl_e, lbl_c):
                lbl.bind("<MouseWheel>", self._on_wheel)
                lbl.bind("<Button-4>",   lambda e: self._canvas.yview_scroll(-2, "units"))
                lbl.bind("<Button-5>",   lambda e: self._canvas.yview_scroll( 2, "units"))

            # Clicks
            for widget in (row, lbl_n, lbl_p, lbl_m, lbl_u, lbl_e, lbl_c):
                widget.bind("<Button-1>",        lambda e, x=p, r=row: self._click_fila(x, r))
                widget.bind("<Double-Button-1>",  lambda e, x=p: self._seleccionar(x))

            self._filas.append((row, p))

        if self._filas:
            self._idx_sel = 0
            self._sel     = self._filas[0][1]
            self._filas[0][0].configure(bg=COLORES["primary"])
            for lbl in self._filas[0][0].winfo_children():
                try: lbl.configure(bg=COLORES["primary"])
                except Exception: pass

        # Resetear scroll al inicio
        self._canvas.yview_moveto(0)

    # ── Selección ─────────────────────────────────────────────────────────────
    def _color_fila(self, fila_idx, seleccionado=False):
        if fila_idx < 0 or fila_idx >= len(self._filas):
            return
        row, _ = self._filas[fila_idx]
        bg = COLORES["primary"] if seleccionado else (
             COLORES["bg_card"] if fila_idx % 2 == 0 else COLORES["bg_dark"])
        try:
            row.configure(bg=bg)
            for lbl in row.winfo_children():
                try: lbl.configure(bg=bg)
                except Exception: pass
        except Exception:
            pass

    def _click_fila(self, prod, row):
        # Desseleccionar anterior
        if self._idx_sel >= 0:
            self._color_fila(self._idx_sel, False)
        # Seleccionar nueva
        idx = next((i for i, (r, p) in enumerate(self._filas) if r is row), -1)
        self._idx_sel = idx
        self._sel     = prod
        self._color_fila(idx, True)

    def _mover_sel(self, delta):
        if not self._filas:
            return
        self._color_fila(self._idx_sel, False)
        self._idx_sel = max(0, min(len(self._filas)-1, self._idx_sel + delta))
        self._color_fila(self._idx_sel, True)
        self._sel = self._filas[self._idx_sel][1]

    def _seleccionar(self, prod):
        self._on_sel(prod)
        self.destroy()

    def _aceptar(self, event=None):
        if self._sel:
            self._seleccionar(self._sel)
            return "break"
        elif self._filas:
            self._seleccionar(self._filas[0][1])
            return "break"
