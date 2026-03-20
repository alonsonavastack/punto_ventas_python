"""
widgets/tabla.py
Tabla reutilizable con cabecera, scroll y filas alternas.
Uso:
    t = TablaWidget(parent, cols=[("Nombre",200),("Precio",90)], height=400)
    t.pack(fill="both", expand=True)
    t.cargar(lista_de_dicts, keys=["nombre","precio"])
"""
import customtkinter as ctk
from app.utils.config import COLORES

class TablaWidget(ctk.CTkFrame):
    def __init__(self, parent, cols: list, height=None, **kwargs):
        super().__init__(parent, fg_color=COLORES["bg_dark"],
                         corner_radius=12, **kwargs)
        self.cols = cols   # [(titulo, ancho), ...]
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self._build_header()
        kw = {"height": height} if height else {}
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", **kw)
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0,8))

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=COLORES["primary"],
                           corner_radius=6, height=34)
        hdr.grid(row=0, column=0, sticky="ew", padx=8, pady=(8,4))
        for titulo, ancho in self.cols:
            ctk.CTkLabel(hdr, text=titulo, font=("Segoe UI",11,"bold"),
                         text_color="white", width=ancho).pack(side="left", padx=4)

    def limpiar(self):
        for w in self.scroll.winfo_children():
            w.destroy()

    def agregar_fila(self, valores: list, acciones=None, alterna=0):
        """
        valores: lista de strings (mismo orden que cols)
        acciones: lista de (texto, color, comando)
        alterna: índice de la fila para color alterno
        """
        bg = COLORES["bg_card"] if alterna % 2 == 0 else "transparent"
        row = ctk.CTkFrame(self.scroll, fg_color=bg, corner_radius=4, height=34)
        row.pack(fill="x", pady=1)

        for (_, ancho), val in zip(self.cols, valores):
            color = COLORES["text_primary"]
            if isinstance(val, tuple):  # (texto, color)
                val, color = val
            ctk.CTkLabel(row, text=str(val)[:30], font=("Segoe UI",11),
                         text_color=color, width=ancho, anchor="w").pack(side="left", padx=4)

        if acciones:
            for txt, color, cmd in acciones:
                ctk.CTkButton(row, text=txt, width=36, height=26,
                              fg_color=color, hover_color="#1e293b",
                              command=cmd).pack(side="left", padx=2)
        return row

    def cargar(self, filas: list, keys: list, col_colors: dict = None,
               acciones_fn=None):
        """
        filas: lista de dicts
        keys: claves a mostrar (mismo orden que cols, sin contar columna acciones)
        col_colors: {key: fn(valor)->color} para colorear celdas
        acciones_fn: fn(fila) -> [(txt, color, cmd)]
        """
        self.limpiar()
        for i, fila in enumerate(filas):
            vals = []
            for k in keys:
                v = fila.get(k, "")
                if col_colors and k in col_colors:
                    c = col_colors[k](v, fila)
                    vals.append((str(v), c))
                else:
                    vals.append(str(v) if v is not None else "")
            acciones = acciones_fn(fila) if acciones_fn else None
            self.agregar_fila(vals, acciones=acciones, alterna=i)
