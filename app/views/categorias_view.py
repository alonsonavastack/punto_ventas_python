import customtkinter as ctk
from tkinter import messagebox
from app.database.connection import Database
from app.utils.config import COLORES

EMOJIS_CATALOGO = {
    "🛒 Tienda y Comercio":   ["🛒","🏪","🏬","🏦","💰","💵","💳","🧾","📦","🎁","🛍️","🏷️","💼","📊","📈","🔑","🗝️","💲","🪙","💹"],
    "🥤 Bebidas":             ["🥤","🧃","🍺","🍻","🍷","🍸","🍹","🧊","☕","🍵","🧋","🥛","🍶","🥂","🫖","🧉","🍾","🫗","🍼","🧴"],
    "🍎 Frutas":              ["🍎","🍊","🍋","🍇","🍓","🍒","🍑","🥝","🍉","🍌","🥭","🍍","🍐","🍈","🍏","🫐","🍅","🍆","🌶️","🥑"],
    "🥦 Verduras":            ["🥦","🥕","🌽","🥬","🫑","🧅","🧄","🥔","🫛","🥒","🥗","🌿","🌱","🌾","🍀","🪴","🫚","🥑","🌰","🧆"],
    "🥩 Carnes y Proteínas":  ["🥩","🍖","🍗","🥚","🍳","🥓","🧀","🥪","🌮","🌯","🫓","🍱","🍣","🍤","🦐","🦞","🦀","🐟","🐠","🦑"],
    "🍞 Panadería y Granos":  ["🍞","🥐","🥖","🥨","🧁","🎂","🍰","🍪","🍩","🥞","🧇","🌾","🫘","🍚","🍜","🍝","🥣","🍛","🥧","🫔"],
    "🍬 Dulces y Botanas":    ["🍬","🍭","🍫","🍿","🍦","🍧","🍨","🍡","🥜","🌰","🍯","🫙","🍪","🎉","🍮","🍰","🍲","🧆","🥮","🎊"],
    "🧹 Limpieza y Hogar":    ["🧹","🧺","🧻","🪣","🧼","🪥","🫧","🧽","🪴","🛁","🚿","🪞","🛏️","🪑","🚪","🪟","🧴","🪠","🧯","🔒"],
    "💊 Salud y Farmacia":    ["💊","💉","🩺","🩹","🩻","🏥","🧬","🩼","🌡️","🫀","🫁","🧠","👁️","🦷","🦴","🔬","🧪","🩸","🏋️","🧘"],
    "👕 Ropa y Accesorios":   ["👕","👗","👔","👖","👟","👠","👡","👒","🎩","👜","👛","💍","⌚","🕶️","🧣","🧤","🧥","👙","🩳","🎀"],
    "📱 Electrónica":         ["📱","💻","🖥️","⌨️","🖱️","📷","📸","🎮","🕹️","🔌","🔋","💡","📺","📻","🎧","📡","🖨️","💾","📀","🔦"],
    "🚗 Transporte":          ["🚗","🚕","🚙","🚌","🚑","🚒","🏎️","🛵","🚲","✈️","🚢","⛽","🔧","🔩","🛻","🚐","🚓","🛺","🚁","🛸"],
    "🐾 Mascotas":            ["🐶","🐱","🐭","🐹","🐰","🦊","🐻","🐼","🐨","🐯","🦁","🐮","🐷","🐸","🐵","🐔","🐧","🐦","🦆","🦴"],
    "📚 Educación y Oficina": ["📚","📖","📝","✏️","🖊️","📐","📏","📌","📎","🗂️","🗃️","📊","📈","📉","🗓️","🖋️","📋","📓","🎓","🏫"],
    "⚽ Deportes":            ["⚽","🏀","🏈","⚾","🏐","🎾","🏸","🏒","🥊","🎽","🛹","⛸️","🏋️","🤸","🧗","🏊","🚴","🤾","🥅","🏆"],
    "🌟 General / Varios":    ["📦","🏷️","⭐","🌟","💫","✨","🔥","💎","🎯","🎲","🎨","🎭","🎬","🎤","🎵","🌈","☀️","🌙","❄️","🌺"],
}

COLORES_PRESET = [
    ("#f59e0b","Ámbar"),   ("#f97316","Naranja"), ("#dc2626","Rojo"),    ("#ec4899","Rosa"),
    ("#7c3aed","Morado"),  ("#3b82f6","Azul"),    ("#0891b2","Cian"),    ("#16a34a","Verde"),
    ("#059669","Esmeralda"),("#92400e","Café"),   ("#64748b","Gris"),    ("#0f172a","Negro"),
]

class CategoriasView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.db = Database.get_instance()
        self._build()
        self._cargar()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16,8))
        ctk.CTkLabel(hdr, text="🏷️  Categorías",
                     font=("Segoe UI",20,"bold"),
                     text_color=COLORES["text_primary"]).pack(side="left")
        ctk.CTkButton(hdr, text="➕ Nueva Categoría", width=160,
                      command=self._form).pack(side="right")

        self.grid_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True, padx=20, pady=4)

    def _cargar(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        cats = self.db.fetch_all("SELECT * FROM categorias WHERE activo=1 ORDER BY nombre")
        cols = 4
        for i, cat in enumerate(cats):
            row_i = i // cols
            col_i = i % cols
            self.grid_frame.columnconfigure(col_i, weight=1)
            card = ctk.CTkFrame(self.grid_frame, fg_color=COLORES["bg_dark"],
                                corner_radius=12, width=160, height=115)
            card.grid(row=row_i, column=col_i, padx=6, pady=6, sticky="ew")
            card.grid_propagate(False)

            color = cat.get("color","#64748b") or "#64748b"
            ctk.CTkFrame(card, fg_color=color, corner_radius=8, height=6).pack(fill="x")
            ctk.CTkLabel(card, text=cat.get("icono","📦") or "📦",
                         font=("Segoe UI",28)).pack(pady=(6,2))
            ctk.CTkLabel(card, text=cat["nombre"],
                         font=("Segoe UI",12,"bold"),
                         text_color=COLORES["text_primary"]).pack()
            cnt = self.db.fetch_one(
                "SELECT COUNT(*) AS c FROM productos WHERE categoria_id=%s AND activo=1",
                (cat["id"],))
            ctk.CTkLabel(card, text=f"{cnt['c']} productos",
                         font=("Segoe UI",10),
                         text_color=COLORES["text_secondary"]).pack()
            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(pady=4)
            ctk.CTkButton(btn_row, text="✏️", width=32, height=26,
                          fg_color=COLORES["primary"],
                          command=lambda c=cat: self._form(c)).pack(side="left", padx=2)
            ctk.CTkButton(btn_row, text="🗑", width=32, height=26,
                          fg_color=COLORES["danger"],
                          command=lambda c=cat: self._eliminar(c)).pack(side="left", padx=2)

    def _eliminar(self, cat):
        cnt = self.db.fetch_one(
            "SELECT COUNT(*) AS c FROM productos WHERE categoria_id=%s AND activo=1",
            (cat["id"],))
        if cnt["c"] > 0:
            messagebox.showwarning("No permitido",
                f"La categoría tiene {cnt['c']} producto(s). Reasígnalos antes de eliminar.")
            return
        if messagebox.askyesno("Eliminar", f"¿Eliminar '{cat['nombre']}'?"):
            self.db.execute_query("UPDATE categorias SET activo=0 WHERE id=%s", (cat["id"],))
            self._cargar()

    def _form(self, cat=None):
        win = ctk.CTkToplevel(self)
        win.title("Nueva Categoría" if not cat else "Editar Categoría")
        win.geometry("480x660")
        win.resizable(False, True)
        win.grab_set()
        win.configure(fg_color=COLORES["bg_dark"])

        ctk.CTkLabel(win, text="🏷️  Categoría",
                     font=("Segoe UI",18,"bold"),
                     text_color=COLORES["text_primary"]).pack(pady=(16,6), padx=20, anchor="w")

        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20)

        # ── Nombre y descripción ──────────────────────────────────────────
        b1 = ctk.CTkFrame(scroll, fg_color=COLORES["bg_card"], corner_radius=12)
        b1.pack(fill="x", pady=(0,10))

        ctk.CTkLabel(b1, text="Nombre *", font=("Segoe UI",11),
                     text_color=COLORES["text_secondary"]).pack(anchor="w", padx=16, pady=(14,2))
        entry_nombre = ctk.CTkEntry(b1, height=36)
        entry_nombre.pack(fill="x", padx=16, pady=(0,10))

        ctk.CTkLabel(b1, text="Descripción (opcional)", font=("Segoe UI",11),
                     text_color=COLORES["text_secondary"]).pack(anchor="w", padx=16, pady=(0,2))
        entry_desc = ctk.CTkEntry(b1, height=36)
        entry_desc.pack(fill="x", padx=16, pady=(0,14))

        if cat:
            entry_nombre.insert(0, cat["nombre"])
            entry_desc.insert(0, cat.get("descripcion","") or "")

        # ── Selector de ícono ─────────────────────────────────────────────
        icono_var = ctk.StringVar(value=(cat.get("icono","📦") if cat else "📦"))

        b2 = ctk.CTkFrame(scroll, fg_color=COLORES["bg_card"], corner_radius=12)
        b2.pack(fill="x", pady=(0,10))

        # Título + preview
        top_row = ctk.CTkFrame(b2, fg_color="transparent")
        top_row.pack(fill="x", padx=16, pady=(14,6))
        ctk.CTkLabel(top_row, text="Ícono",
                     font=("Segoe UI",12,"bold"),
                     text_color=COLORES["text_primary"]).pack(side="left")
        preview_box = ctk.CTkFrame(top_row, fg_color=COLORES["bg_input"],
                                    corner_radius=10, width=52, height=42)
        preview_box.pack(side="right")
        preview_box.pack_propagate(False)
        lbl_preview = ctk.CTkLabel(preview_box, text=icono_var.get(),
                                    font=("Segoe UI",24))
        lbl_preview.pack(expand=True)

        # ComboBox de grupo
        ctk.CTkLabel(b2, text="Grupo de emojis:",
                     font=("Segoe UI",11),
                     text_color=COLORES["text_secondary"]).pack(anchor="w", padx=16, pady=(0,4))

        grupos = list(EMOJIS_CATALOGO.keys())
        combo_grupo = ctk.CTkComboBox(b2, values=grupos, height=34,
                                       font=("Segoe UI",12))
        combo_grupo.pack(fill="x", padx=16, pady=(0,8))

        # Cuadrícula de emojis — 8 por fila, todo visible sin scroll horizontal
        emoji_grid = ctk.CTkFrame(b2, fg_color=COLORES["bg_dark"], corner_radius=8)
        emoji_grid.pack(fill="x", padx=16, pady=(0,14))

        botones_emojis = []

        def renderizar_emojis(grupo):
            for w in emoji_grid.winfo_children():
                w.destroy()
            botones_emojis.clear()
            emojis = EMOJIS_CATALOGO.get(grupo, [])
            fila = None
            for j, em in enumerate(emojis):
                if j % 8 == 0:          # ← 8 por fila (antes 10, se cortaban)
                    fila = ctk.CTkFrame(emoji_grid, fg_color="transparent")
                    fila.pack(fill="x", pady=2, padx=4)
                selec = (em == icono_var.get())
                btn = ctk.CTkButton(
                    fila, text=em, width=44, height=40,
                    font=("Segoe UI",20),
                    fg_color=COLORES["primary"] if selec else "transparent",
                    hover_color=COLORES["bg_input"],
                    corner_radius=6,
                    command=lambda e=em: _sel_emoji(e))
                btn.pack(side="left", padx=2, pady=1)
                botones_emojis.append((btn, em))

        def _sel_emoji(emoji):
            icono_var.set(emoji)
            lbl_preview.configure(text=emoji)
            for btn, em in botones_emojis:
                btn.configure(
                    fg_color=COLORES["primary"] if em == emoji else "transparent")

        combo_grupo.configure(command=lambda v: renderizar_emojis(v))

        # Posicionar en el grupo del ícono actual
        grupo_inicial = grupos[0]
        for g, ems in EMOJIS_CATALOGO.items():
            if (cat.get("icono","") if cat else "") in ems:
                grupo_inicial = g
                break
        combo_grupo.set(grupo_inicial)
        renderizar_emojis(grupo_inicial)

        # ── Selector de color ─────────────────────────────────────────────
        color_var = ctk.StringVar(value=(cat.get("color","#64748b") if cat else "#64748b"))

        b3 = ctk.CTkFrame(scroll, fg_color=COLORES["bg_card"], corner_radius=12)
        b3.pack(fill="x", pady=(0,10))

        top_c = ctk.CTkFrame(b3, fg_color="transparent")
        top_c.pack(fill="x", padx=16, pady=(14,6))
        ctk.CTkLabel(top_c, text="Color",
                     font=("Segoe UI",12,"bold"),
                     text_color=COLORES["text_primary"]).pack(side="left")
        lbl_hex = ctk.CTkLabel(top_c, text=color_var.get(),
                                font=("Segoe UI",11),
                                text_color=COLORES["text_secondary"])
        lbl_hex.pack(side="right")

        # 4 colores por fila → todo cabe sin scroll horizontal
        color_grid = ctk.CTkFrame(b3, fg_color="transparent")
        color_grid.pack(padx=16, pady=(0,8), fill="x")

        btns_color = []

        def set_color(hex_c, btn_sel):
            color_var.set(hex_c)
            lbl_hex.configure(text=hex_c)
            for b in btns_color:
                b.configure(border_width=0)
            btn_sel.configure(border_width=3)

        for i, (hex_c, nombre_c) in enumerate(COLORES_PRESET):
            col_i = i % 4          # ← 4 por fila (antes 6, se cortaban)
            row_i = i // 4
            selec = (hex_c == color_var.get())
            tc = "white" if hex_c != "#ffffff" else "#000000"
            btn_c = ctk.CTkButton(
                color_grid, text=nombre_c, width=90, height=36,
                fg_color=hex_c, text_color=tc,
                font=("Segoe UI",10,"bold"), corner_radius=8,
                border_width=3 if selec else 0,
                border_color=COLORES["text_primary"])
            btn_c.grid(row=row_i, column=col_i, padx=4, pady=4, sticky="ew")
            btn_c.configure(command=lambda h=hex_c, b=btn_c: set_color(h, b))
            btns_color.append(btn_c)

        for col in range(4):
            color_grid.columnconfigure(col, weight=1)

        ctk.CTkLabel(b3, text="Color hex personalizado (opcional):",
                     font=("Segoe UI",10),
                     text_color=COLORES["text_secondary"]).pack(
                         anchor="w", padx=16, pady=(4,2))
        entry_hex = ctk.CTkEntry(b3, height=32, placeholder_text="#f59e0b")
        entry_hex.pack(fill="x", padx=16, pady=(0,14))

        # ── Guardar ───────────────────────────────────────────────────────
        def guardar():
            nombre = entry_nombre.get().strip()
            if not nombre:
                messagebox.showwarning("Error", "El nombre es obligatorio.")
                return
            color_final = entry_hex.get().strip() or color_var.get()
            datos = (nombre, entry_desc.get().strip(),
                     icono_var.get() or "📦", color_final)
            if cat:
                self.db.execute_query(
                    "UPDATE categorias SET nombre=%s,descripcion=%s,icono=%s,color=%s WHERE id=%s",
                    datos + (cat["id"],))
            else:
                self.db.execute_query(
                    "INSERT INTO categorias(nombre,descripcion,icono,color) VALUES(%s,%s,%s,%s)",
                    datos)
            win.destroy()
            self._cargar()

        ctk.CTkButton(win, text="💾  Guardar Categoría", height=44,
                      font=("Segoe UI",13,"bold"),
                      fg_color=COLORES["success"],
                      command=guardar).pack(fill="x", padx=20, pady=12)
