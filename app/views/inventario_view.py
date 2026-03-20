import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, date, timedelta
from app.models.producto_model import ProductoModel
from app.database.connection import Database
from app.utils.config import COLORES
from app.utils import session
from app.views.widgets.tabla import TablaWidget
from app.utils.scanner import crear_boton_escaner

class InventarioView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.model = ProductoModel()
        self.db    = Database.get_instance()
        self._prod_agregar = None
        self._prod_ajuste  = None
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=COLORES["bg_dark"], corner_radius=0, height=44)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="INVENTARIO", font=("Segoe UI",14,"bold"),
                     text_color=COLORES["text_primary"]).pack(side="left", padx=16, pady=10)

        acc = ctk.CTkFrame(self, fg_color=COLORES["bg_card"], corner_radius=0, height=42)
        acc.pack(fill="x")
        self._btn_tab = {}
        for txt, key in [
            ("➕ Agregar a Inv.",       "agregar"),
            ("✏️  Ajustes",             "ajustes"),
            ("⚠️  Productos bajos",     "bajos"),
            ("📊 Reporte Inventario",   "reporte"),
            ("📋 Historial Movimientos","historial"),
        ]:
            btn = ctk.CTkButton(acc, text=txt, height=32, width=170,
                                font=("Segoe UI",10,"bold"),
                                fg_color=COLORES["bg_input"],
                                hover_color=COLORES["primary"], corner_radius=4,
                                command=lambda k=key: self._mostrar_tab(k))
            btn.pack(side="left", padx=4, pady=5)
            self._btn_tab[key] = btn

        self.contenido = ctk.CTkFrame(self, fg_color="transparent")
        self.contenido.pack(fill="both", expand=True)
        self._mostrar_tab("reporte")

    def _limpiar_contenido(self):
        for w in self.contenido.winfo_children():
            w.destroy()
        for btn in self._btn_tab.values():
            btn.configure(fg_color=COLORES["bg_input"])

    def _mostrar_tab(self, key):
        self._limpiar_contenido()
        self._btn_tab[key].configure(fg_color=COLORES["primary"])
        if   key == "reporte":   self._tab_reporte()
        elif key == "bajos":     self._tab_bajos()
        elif key == "historial": self._tab_historial()
        elif key == "agregar":   self._tab_agregar_inventario()
        elif key == "ajustes":   self._tab_ajustes()

    # ── Tabla de productos ────────────────────────────────────────────────────
    def _build_tabla_productos(self, parent, productos=None):
        tools = ctk.CTkFrame(parent, fg_color=COLORES["bg_card"], corner_radius=0, height=40)
        tools.pack(fill="x")
        self.entry_buscar = ctk.CTkEntry(tools, placeholder_text="🔍 Buscar...",
                                          height=30, width=260)
        self.entry_buscar.pack(side="left", padx=8, pady=5)
        self.entry_buscar.bind("<KeyRelease>", self._filtrar_productos)
        for txt, color, cmd in [
            ("➕ Nuevo",    COLORES["success"], lambda: self._form_producto()),
            ("✏️  Modificar", COLORES["primary"], self._tip_modificar),
            ("🗑 Eliminar",  COLORES["danger"],  self._tip_eliminar),
        ]:
            ctk.CTkButton(tools, text=txt, height=30, width=110,
                          fg_color=color, font=("Segoe UI",10,"bold"),
                          command=cmd).pack(side="left", padx=4)

        self._tabla_prods = TablaWidget(parent, cols=[
            ("Código",120),("Descripción del Producto",220),
            ("Costo",80),("Precio Venta",90),
            ("Existencia",90),("Mínimo",80),
            ("Categoría",110),("",80)
        ])
        self._tabla_prods.pack(fill="both", expand=True, padx=8, pady=4)
        self._cargar_tabla_productos(productos)

    def _cargar_tabla_productos(self, productos=None):
        if productos is None:
            productos = self.model.get_all()
        self._productos_actuales = productos

        def color_exist(val, fila):
            ex = float(fila.get("existencia",0) or 0)
            mi = float(fila.get("existencia_min",0) or 0)
            return COLORES["danger"] if ex <= mi else COLORES["success"]

        self._tabla_prods.cargar(
            productos,
            keys=["codigo_barras","nombre","precio_costo","precio_venta",
                  "existencia","existencia_min","categoria_nombre"],
            col_colors={"existencia": color_exist},
            acciones_fn=lambda f: [
                ("✏️", COLORES["primary"], lambda x=f: self._form_producto(x)),
                ("🗑", COLORES["danger"],  lambda x=f: self._eliminar(x)),
            ]
        )

    def _filtrar_productos(self, event=None):
        t = self.entry_buscar.get().strip()
        if len(t) >= 2: self._cargar_tabla_productos(self.model.buscar(t))
        elif t == "":   self._cargar_tabla_productos()

    def _tip_modificar(self):
        messagebox.showinfo("Tip","Haz clic en ✏️ en la fila del producto a modificar.")
    def _tip_eliminar(self):
        messagebox.showinfo("Tip","Haz clic en 🗑 en la fila del producto a eliminar.")

    # ── TABS ──────────────────────────────────────────────────────────────────
    def _tab_reporte(self):
        todos = self.model.get_all()
        val_costo = sum(float(p.get("precio_costo",0) or 0)*float(p.get("existencia",0) or 0) for p in todos)
        total_u   = sum(float(p.get("existencia",0) or 0) for p in todos)

        top = ctk.CTkFrame(self.contenido, fg_color=COLORES["bg_card"], corner_radius=0)
        top.pack(fill="x", padx=8, pady=4)
        for lbl, val, color in [
            ("Costo del inventario",   f"${val_costo:.2f}", COLORES["text_secondary"]),
            ("Cantidad en inventario", f"{total_u:.0f}",    COLORES["primary"]),
            ("Productos distintos",    str(len(todos)),      COLORES["success"]),
        ]:
            col = ctk.CTkFrame(top, fg_color="transparent")
            col.pack(side="left", padx=24, pady=10)
            ctk.CTkLabel(col, text=lbl, font=("Segoe UI",10),
                         text_color=COLORES["text_secondary"]).pack()
            ctk.CTkLabel(col, text=val, font=("Segoe UI",18,"bold"),
                         text_color=color).pack()

        fil = ctk.CTkFrame(self.contenido, fg_color="transparent")
        fil.pack(fill="x", padx=8)
        ctk.CTkLabel(fil, text="Categoría:", font=("Segoe UI",11),
                     text_color=COLORES["text_secondary"]).pack(side="left", padx=8)
        cats = ["— Todos —"] + [c["nombre"] for c in self.model.get_categorias()]
        combo = ctk.CTkComboBox(fil, values=cats, height=30, width=200,
                                 command=self._filtrar_por_cat)
        combo.pack(side="left", padx=4)
        self._build_tabla_productos(self.contenido)

    def _filtrar_por_cat(self, valor):
        if valor == "— Todos —": self._cargar_tabla_productos()
        else:
            self._cargar_tabla_productos(
                [p for p in self.model.get_all() if p.get("categoria_nombre","") == valor])

    def _tab_bajos(self):
        ctk.CTkLabel(self.contenido, text="⚠️  PRODUCTOS BAJOS EN INVENTARIO",
                     font=("Segoe UI",15,"bold"),
                     text_color=COLORES["warning"]).pack(padx=16, pady=(12,4), anchor="w")
        ctk.CTkLabel(self.contenido,
                     text="Productos con existencia igual o por debajo del mínimo:",
                     font=("Segoe UI",11),
                     text_color=COLORES["text_secondary"]).pack(padx=16, anchor="w")

        tabla = TablaWidget(self.contenido, cols=[
            ("Código",120),("Descripción",220),("Precio Venta",100),
            ("Existencia",100),("Mínimo",100),("Categoría",140)])
        tabla.pack(fill="both", expand=True, padx=8, pady=8)

        bajos = self.model.stock_bajo()
        for i, p in enumerate(bajos):
            tabla.agregar_fila([
                p.get("codigo_barras","") or "",
                p["nombre"],
                f"${float(p['precio_venta']):.2f}",
                (str(int(p.get("existencia",0))), COLORES["danger"]),
                str(int(p.get("existencia_min",0))),
                p.get("categoria_nombre","") or "—"
            ], alterna=i)

        if not bajos:
            ctk.CTkLabel(self.contenido,
                         text="✅ Todo el inventario está en niveles correctos.",
                         font=("Segoe UI",13), text_color=COLORES["success"]).pack(pady=30)

    # ── HISTORIAL ─────────────────────────────────────────────────────────────
    def _tab_historial(self):
        hoy = date.today()

        ctk.CTkLabel(self.contenido, text="📋  HISTORIAL DE MOVIMIENTOS",
                     font=("Segoe UI",15,"bold"),
                     text_color=COLORES["text_primary"]).pack(padx=16, pady=(12,4), anchor="w")

        fil = ctk.CTkFrame(self.contenido, fg_color=COLORES["bg_card"], corner_radius=8)
        fil.pack(fill="x", padx=8, pady=(0,6))

        ctk.CTkLabel(fil, text="📅 Desde:", font=("Segoe UI",11),
                     text_color=COLORES["text_secondary"]).pack(side="left", padx=(12,4), pady=8)
        self._hist_fecha_ini = ctk.CTkEntry(fil, width=100, height=30)
        self._hist_fecha_ini.pack(side="left", padx=(0,8))
        self._hist_fecha_ini.insert(0, str(hoy))

        ctk.CTkLabel(fil, text="Hasta:", font=("Segoe UI",11),
                     text_color=COLORES["text_secondary"]).pack(side="left", padx=(0,4))
        self._hist_fecha_fin = ctk.CTkEntry(fil, width=100, height=30)
        self._hist_fecha_fin.pack(side="left", padx=(0,12))
        self._hist_fecha_fin.insert(0, str(hoy))

        for lbl, delta in [("Hoy",0),("7 días",7),("30 días",30)]:
            d = delta
            ctk.CTkButton(fil, text=lbl, width=60, height=28,
                          fg_color=COLORES["bg_input"],
                          font=("Segoe UI",9,"bold"),
                          command=lambda d=d: self._set_rango(d)
                          ).pack(side="left", padx=2)

        ctk.CTkFrame(fil, width=1, fg_color=COLORES["border"]).pack(
            side="left", fill="y", padx=8, pady=6)

        ctk.CTkLabel(fil, text="Producto:", font=("Segoe UI",11),
                     text_color=COLORES["text_secondary"]).pack(side="left", padx=(0,4))
        self._hist_buscar = ctk.CTkEntry(fil, height=30, width=160,
                                          placeholder_text="Nombre o código...")
        self._hist_buscar.pack(side="left", padx=(0,8))

        ctk.CTkLabel(fil, text="Tipo:", font=("Segoe UI",11),
                     text_color=COLORES["text_secondary"]).pack(side="left", padx=(0,4))
        self._hist_tipo = ctk.CTkComboBox(
            fil, height=30, width=150,
            values=["— Todos —","Venta","Entrada manual","Ajuste",
                    "Merma","Devolución","Salida manual"])
        self._hist_tipo.set("— Todos —")
        self._hist_tipo.pack(side="left", padx=(0,8))

        ctk.CTkButton(fil, text="🔍 Filtrar", height=30, width=90,
                      fg_color=COLORES["primary"],
                      font=("Segoe UI",10,"bold"),
                      command=self._cargar_historial).pack(side="left", padx=4)

        self._hist_tabla = TablaWidget(self.contenido, cols=[
            ("Fecha",100),("Hora",65),("Producto",190),("Tipo",120),
            ("Antes",65),("Cambio",70),("Después",70),
            ("Motivo",150),("Usuario",110)])
        self._hist_tabla.pack(fill="both", expand=True, padx=8, pady=4)

        self._cargar_historial()

    def _set_rango(self, dias):
        hoy = date.today()
        ini = hoy - timedelta(days=dias)
        self._hist_fecha_ini.delete(0,"end")
        self._hist_fecha_ini.insert(0, str(ini))
        self._hist_fecha_fin.delete(0,"end")
        self._hist_fecha_fin.insert(0, str(hoy))
        self._cargar_historial()

    def _cargar_historial(self):
        fecha_ini = self._hist_fecha_ini.get().strip() if hasattr(self,"_hist_fecha_ini") else str(date.today())
        fecha_fin = self._hist_fecha_fin.get().strip() if hasattr(self,"_hist_fecha_fin") else str(date.today())
        buscar    = self._hist_buscar.get().strip()    if hasattr(self,"_hist_buscar")    else ""
        tipo      = self._hist_tipo.get()              if hasattr(self,"_hist_tipo")      else "— Todos —"

        rows = []

        if tipo in ("— Todos —","Venta"):
            q = """
                SELECT DATE(v.fecha) AS fecha_mov,
                       TIME(v.fecha) AS hora_mov,
                       p.nombre AS producto,
                       p.codigo_barras,
                       'Venta' AS tipo,
                       NULL AS cant_antes,
                       -dv.cantidad AS diferencia,
                       NULL AS cant_despues,
                       'Venta al cliente' AS motivo,
                       u.nombre AS usuario
                FROM detalle_ventas dv
                JOIN ventas v    ON dv.venta_id    = v.id
                JOIN productos p ON dv.producto_id = p.id
                LEFT JOIN usuarios u ON v.usuario_id = u.id
                WHERE DATE(v.fecha) BETWEEN %s AND %s
                  AND v.estado = 'completada'
            """
            params = [fecha_ini, fecha_fin]
            if buscar:
                q += " AND (p.nombre LIKE %s OR p.codigo_barras LIKE %s)"
                params += [f"%{buscar}%", f"%{buscar}%"]
            q += " ORDER BY v.fecha DESC"
            rows += self.db.fetch_all(q, tuple(params))

        tipos_map = {
            "Entrada manual": "entrada",
            "Ajuste":         "ajuste",
            "Merma":          "merma",
            "Devolución":     "devolucion",
            "Salida manual":  "salida",
        }
        tipo_filtro = tipos_map.get(tipo)

        if tipo in ("— Todos —",) or tipo_filtro:
            q2 = """
                SELECT DATE(a.fecha) AS fecha_mov,
                       TIME(a.fecha) AS hora_mov,
                       p.nombre AS producto,
                       p.codigo_barras,
                       CASE a.tipo
                           WHEN 'entrada'    THEN 'Entrada manual'
                           WHEN 'salida'     THEN 'Salida manual'
                           WHEN 'ajuste'     THEN 'Ajuste'
                           WHEN 'merma'      THEN 'Merma'
                           WHEN 'devolucion' THEN 'Devolución'
                           ELSE a.tipo
                       END AS tipo,
                       a.cantidad_anterior AS cant_antes,
                       a.diferencia,
                       a.cantidad_nueva    AS cant_despues,
                       COALESCE(a.motivo,'—') AS motivo,
                       u.nombre AS usuario
                FROM ajustes_inventario a
                JOIN productos p ON a.producto_id = p.id
                LEFT JOIN usuarios u ON a.usuario_id = u.id
                WHERE DATE(a.fecha) BETWEEN %s AND %s
            """
            params2 = [fecha_ini, fecha_fin]
            if tipo_filtro:
                q2 += " AND a.tipo = %s"
                params2.append(tipo_filtro)
            if buscar:
                q2 += " AND (p.nombre LIKE %s OR p.codigo_barras LIKE %s)"
                params2 += [f"%{buscar}%", f"%{buscar}%"]
            q2 += " ORDER BY a.fecha DESC"
            try:
                rows += self.db.fetch_all(q2, tuple(params2))
            except Exception:
                pass

        def sort_key(r):
            try:
                return (str(r.get("fecha_mov","0")), str(r.get("hora_mov","0")))
            except:
                return ("0","0")
        rows.sort(key=sort_key, reverse=True)

        self._hist_tabla.limpiar()

        if not rows:
            ctk.CTkLabel(self._hist_tabla.scroll,
                         text="No hay movimientos para los filtros seleccionados.",
                         font=("Segoe UI",12),
                         text_color=COLORES["text_secondary"]).pack(pady=20)
            return

        tipo_colores = {
            "Venta":          COLORES["danger"],
            "Entrada manual": COLORES["success"],
            "Ajuste":         COLORES["warning"],
            "Merma":          "#f97316",
            "Devolución":     COLORES["primary"],
            "Salida manual":  "#dc2626",
        }

        for i, r in enumerate(rows):
            try:
                fd = r.get("fecha_mov")
                if hasattr(fd, "strftime"):
                    fecha_str = fd.strftime("%d/%m/%Y")
                else:
                    fd_obj = datetime.strptime(str(fd), "%Y-%m-%d").date()
                    fecha_str = fd_obj.strftime("%d/%m/%Y")
            except:
                fecha_str = str(r.get("fecha_mov",""))

            hora_str = str(r.get("hora_mov",""))[:5]
            tipo_str = r.get("tipo","")
            color    = tipo_colores.get(tipo_str, COLORES["text_primary"])

            antes   = f"{float(r['cant_antes']):.0f}"   if r.get("cant_antes")   is not None else "—"
            despues = f"{float(r['cant_despues']):.0f}" if r.get("cant_despues") is not None else "—"
            dif     = float(r.get("diferencia", 0) or 0)
            dif_str = f"+{dif:.0f}" if dif >= 0 else f"{dif:.0f}"
            dif_col = COLORES["success"] if dif >= 0 else COLORES["danger"]

            self._hist_tabla.agregar_fila([
                (fecha_str, COLORES["text_secondary"]),
                hora_str,
                r.get("producto","")[:22],
                (tipo_str, color),
                antes,
                (dif_str, dif_col),
                despues,
                r.get("motivo","—") or "—",
                r.get("usuario","—") or "—",
            ], alterna=i)

    # ── Agregar inventario ────────────────────────────────────────────────────
    def _tab_agregar_inventario(self):
        ctk.CTkLabel(self.contenido, text="➕  AGREGAR CANTIDAD A INVENTARIO",
                     font=("Segoe UI",15,"bold"),
                     text_color=COLORES["text_primary"]).pack(padx=16, pady=(20,4), anchor="w")

        frame = ctk.CTkFrame(self.contenido, fg_color=COLORES["bg_card"], corner_radius=12)
        frame.pack(padx=20, pady=8, fill="x")

        ctk.CTkLabel(frame, text="Código del Producto:",
                     font=("Segoe UI",12),
                     text_color=COLORES["text_secondary"]).pack(anchor="w", padx=20, pady=(16,2))

        cod_row = ctk.CTkFrame(frame, fg_color="transparent")
        cod_row.pack(fill="x", padx=20)
        cod_row.columnconfigure(0, weight=1)
        entry_cod = ctk.CTkEntry(cod_row, height=36, font=("Segoe UI",13))
        entry_cod.grid(row=0, column=0, sticky="ew", padx=(0,8))
        ctk.CTkButton(cod_row, text="🔍 Buscar", width=100, height=36,
                      fg_color=COLORES["primary"],
                      command=lambda: _buscar()).grid(row=0, column=1)

        lbl_nombre = ctk.CTkLabel(frame, text="— Escribe el código y presiona Enter",
                                   font=("Segoe UI",12), text_color=COLORES["primary"])
        lbl_nombre.pack(anchor="w", padx=20, pady=(6,0))
        lbl_actual = ctk.CTkLabel(frame, text="", font=("Segoe UI",11),
                                   text_color=COLORES["text_secondary"])
        lbl_actual.pack(anchor="w", padx=20)

        ctk.CTkLabel(frame, text="Cantidad a agregar:",
                     font=("Segoe UI",12),
                     text_color=COLORES["text_secondary"]).pack(anchor="w", padx=20, pady=(14,2))
        entry_cant = ctk.CTkEntry(frame, height=38, font=("Segoe UI",14))
        entry_cant.pack(fill="x", padx=20)
        entry_cant.insert(0, "1")

        def _buscar(event=None):
            cod = entry_cod.get().strip()
            if not cod: return
            p = self.model.get_by_codigo(cod)
            if not p:
                res = self.model.buscar(cod)
                p = res[0] if res else None
            if p:
                self._prod_agregar = p
                lbl_nombre.configure(text=f"✅  {p['nombre']}")
                unidad = p.get("unidad","PZA")
                unidad_lbl = {"PZA":"piezas", "KG":"kg", "KIT":"kits"}.get(unidad, unidad)
                lbl_actual.configure(
                    text=f"Cantidad actual: {float(p.get('existencia',0)):.2f} {unidad_lbl}")
            else:
                lbl_nombre.configure(text="❌ Producto no encontrado")
                lbl_actual.configure(text="")
                self._prod_agregar = None

        entry_cod.bind("<Return>", _buscar)

        ctk.CTkLabel(frame, text="Últimas entradas de hoy:",
                     font=("Segoe UI",11),
                     text_color=COLORES["text_secondary"]).pack(anchor="w", padx=20, pady=(14,4))

        hist_frame = ctk.CTkFrame(frame, fg_color=COLORES["bg_dark"], corner_radius=8)
        hist_frame.pack(fill="x", padx=20, pady=(0,16))

        hdr_h = ctk.CTkFrame(hist_frame, fg_color=COLORES["primary"], corner_radius=4, height=28)
        hdr_h.pack(fill="x", padx=4, pady=4)
        for txt, w in [("Hora",80),("Producto",220),("Cantidad agregada",140)]:
            ctk.CTkLabel(hdr_h, text=txt, font=("Segoe UI",10,"bold"),
                         text_color="white", width=w, anchor="w").pack(side="left", padx=6, pady=2)

        self._hist_agregar_scroll = ctk.CTkScrollableFrame(hist_frame,
                                                            fg_color="transparent", height=100)
        self._hist_agregar_scroll.pack(fill="x", padx=4, pady=(0,4))
        self._refrescar_hist_agregar()

        def agregar():
            if not self._prod_agregar:
                messagebox.showwarning("Error","Busca un producto primero."); return
            try: cant = float(entry_cant.get())
            except: messagebox.showwarning("Error","Cantidad inválida."); return
            if cant <= 0: messagebox.showwarning("Error","La cantidad debe ser mayor a 0."); return

            ant  = float(self._prod_agregar.get("existencia",0) or 0)
            nueva = ant + cant
            usuario = session.get_usuario()
            uid = usuario["id"] if usuario else None

            self.model.actualizar_existencia(self._prod_agregar["id"], cant)
            self._registrar_ajuste(self._prod_agregar["id"], "entrada", ant, nueva, cant,
                                   "Entrada manual", uid)
            unidad = self._prod_agregar.get("unidad","PZA")
            unidad_lbl = {"PZA":"piezas", "KG":"kg", "KIT":"kits"}.get(unidad, unidad)
            messagebox.showinfo("✅ Listo",
                f"Se agregaron {cant:.2f} {unidad_lbl} a '{self._prod_agregar['nombre']}'.\n"
                f"Nueva existencia: {nueva:.2f} {unidad_lbl}")
            entry_cod.delete(0,"end")
            entry_cant.delete(0,"end")
            entry_cant.insert(0,"1")
            lbl_nombre.configure(text="— Escribe el código y presiona Enter")
            lbl_actual.configure(text="")
            self._prod_agregar = None
            self._refrescar_hist_agregar()

        ctk.CTkButton(frame, text="✅  Agregar cantidad a Inventario",
                      height=42, fg_color=COLORES["success"],
                      font=("Segoe UI",12,"bold"),
                      command=agregar).pack(fill="x", padx=20, pady=(0,8))

    def _refrescar_hist_agregar(self):
        if not hasattr(self,"_hist_agregar_scroll"): return
        for w in self._hist_agregar_scroll.winfo_children():
            w.destroy()
        try:
            movs = self.db.fetch_all("""
                SELECT TIME(a.fecha) AS hora, p.nombre, a.diferencia
                FROM ajustes_inventario a
                JOIN productos p ON a.producto_id = p.id
                WHERE DATE(a.fecha)=CURDATE() AND a.tipo='entrada'
                ORDER BY a.fecha DESC LIMIT 10
            """)
            for i, m in enumerate(movs):
                bg = COLORES["bg_card"] if i%2==0 else "transparent"
                row = ctk.CTkFrame(self._hist_agregar_scroll, fg_color=bg, height=26)
                row.pack(fill="x", pady=1)
                for txt, w in [(str(m["hora"])[:5],80),(m["nombre"][:26],220),
                                (f"+{float(m['diferencia']):.2f}",140)]:
                    ctk.CTkLabel(row, text=txt, font=("Segoe UI",10),
                                 text_color=COLORES["text_primary"], width=w,
                                 anchor="w").pack(side="left", padx=6)
            if not movs:
                ctk.CTkLabel(self._hist_agregar_scroll, text="Sin entradas hoy.",
                             font=("Segoe UI",10),
                             text_color=COLORES["text_secondary"]).pack(pady=4)
        except Exception:
            ctk.CTkLabel(self._hist_agregar_scroll, text="Sin entradas registradas.",
                         font=("Segoe UI",10),
                         text_color=COLORES["text_secondary"]).pack(pady=4)

    # ── Ajustes ───────────────────────────────────────────────────────────────
    def _tab_ajustes(self):
        ctk.CTkLabel(self.contenido, text="✏️  AJUSTES DE INVENTARIO",
                     font=("Segoe UI",15,"bold"),
                     text_color=COLORES["text_primary"]).pack(padx=16, pady=(16,2), anchor="w")
        ctk.CTkLabel(self.contenido,
                     text="Corrige existencias por merma, conteo físico, errores, devoluciones, etc.",
                     font=("Segoe UI",11),
                     text_color=COLORES["text_secondary"]).pack(padx=16, anchor="w")

        frame = ctk.CTkFrame(self.contenido, fg_color=COLORES["bg_card"], corner_radius=12)
        frame.pack(padx=20, pady=12, fill="x")

        ctk.CTkLabel(frame, text="Código del Producto:",
                     font=("Segoe UI",12),
                     text_color=COLORES["text_secondary"]).pack(anchor="w", padx=20, pady=(16,2))
        cod_row = ctk.CTkFrame(frame, fg_color="transparent")
        cod_row.pack(fill="x", padx=20)
        cod_row.columnconfigure(0, weight=1)
        entry_cod = ctk.CTkEntry(cod_row, height=36)
        entry_cod.grid(row=0, column=0, sticky="ew", padx=(0,8))
        ctk.CTkButton(cod_row, text="🔍 Buscar", width=100, height=36,
                      fg_color=COLORES["primary"],
                      command=lambda: _buscar()).grid(row=0, column=1)

        lbl_info  = ctk.CTkLabel(frame, text="— Escribe el código y busca el producto",
                                  font=("Segoe UI",12), text_color=COLORES["primary"])
        lbl_info.pack(anchor="w", padx=20, pady=(6,0))
        lbl_exist = ctk.CTkLabel(frame, text="", font=("Segoe UI",11),
                                  text_color=COLORES["text_secondary"])
        lbl_exist.pack(anchor="w", padx=20)

        def _buscar(event=None):
            cod = entry_cod.get().strip()
            p = self.model.get_by_codigo(cod)
            if not p:
                res = self.model.buscar(cod)
                p = res[0] if res else None
            if p:
                self._prod_ajuste = p
                lbl_info.configure(text=f"✅  {p['nombre']}")
                unidad = p.get("unidad","PZA")
                unidad_lbl = {"PZA":"piezas", "KG":"kg", "KIT":"kits"}.get(unidad, unidad)
                lbl_exist.configure(
                    text=f"Existencia actual: {float(p.get('existencia',0)):.2f} {unidad_lbl}")
                entry_nueva.delete(0,"end")
                entry_nueva.insert(0, f"{float(p.get('existencia',0)):.2f}")
            else:
                self._prod_ajuste = None
                lbl_info.configure(text="❌ Producto no encontrado")
                lbl_exist.configure(text="")

        entry_cod.bind("<Return>", _buscar)

        ctk.CTkLabel(frame, text="Tipo de ajuste:",
                     font=("Segoe UI",12),
                     text_color=COLORES["text_secondary"]).pack(anchor="w", padx=20, pady=(14,2))
        TIPOS = [("🔴 Merma","merma"),("📦 Entrada manual","entrada"),
                 ("➖ Salida manual","salida"),("🔄 Corrección conteo","ajuste"),
                 ("↩️  Devolución","devolucion")]
        tipo_var = ctk.StringVar(value="merma")
        tf = ctk.CTkFrame(frame, fg_color="transparent")
        tf.pack(fill="x", padx=20, pady=(0,4))
        for txt, val in TIPOS:
            ctk.CTkRadioButton(tf, text=txt, variable=tipo_var, value=val,
                               font=("Segoe UI",11)).pack(side="left", padx=10, pady=4)

        modo_var = ctk.StringVar(value="nueva")
        mf = ctk.CTkFrame(frame, fg_color="transparent")
        mf.pack(fill="x", padx=20, pady=(4,2))
        ctk.CTkRadioButton(mf, text="Establecer cantidad nueva",
                           variable=modo_var, value="nueva",
                           font=("Segoe UI",11)).pack(side="left", padx=4)
        ctk.CTkRadioButton(mf, text="Restar cantidad (merma/salida)",
                           variable=modo_var, value="restar",
                           font=("Segoe UI",11)).pack(side="left", padx=16)

        ctk.CTkLabel(frame, text="Cantidad:",
                     font=("Segoe UI",12),
                     text_color=COLORES["text_secondary"]).pack(anchor="w", padx=20, pady=(10,2))
        entry_nueva = ctk.CTkEntry(frame, height=36, font=("Segoe UI",13))
        entry_nueva.pack(fill="x", padx=20)
        entry_nueva.insert(0,"0")

        ctk.CTkLabel(frame, text="Motivo:",
                     font=("Segoe UI",12),
                     text_color=COLORES["text_secondary"]).pack(anchor="w", padx=20, pady=(10,2))
        combo_motivo = ctk.CTkComboBox(frame, height=34, values=[
            "Merma por caducidad","Merma por daño","Conteo físico",
            "Error de captura","Devolución a proveedor",
            "Devolución de cliente","Robo/pérdida","Otro"])
        combo_motivo.set("Merma por caducidad")
        combo_motivo.pack(fill="x", padx=20, pady=(0,4))

        ctk.CTkLabel(frame, text="Notas (opcional):",
                     font=("Segoe UI",11),
                     text_color=COLORES["text_secondary"]).pack(anchor="w", padx=20, pady=(4,2))
        entry_notas = ctk.CTkEntry(frame, height=34)
        entry_notas.pack(fill="x", padx=20, pady=(0,16))

        def aplicar():
            if not self._prod_ajuste:
                messagebox.showwarning("Error","Busca un producto primero."); return
            try: cant = float(entry_nueva.get())
            except: messagebox.showwarning("Error","Cantidad inválida."); return
            if cant < 0: messagebox.showwarning("Error","No puede ser negativo."); return

            ant  = float(self._prod_ajuste.get("existencia",0) or 0)
            if modo_var.get() == "nueva":
                nueva = cant
                dif   = nueva - ant
            else:
                if cant > ant:
                    messagebox.showwarning("Error",
                        f"Solo hay {ant:.2f} disponibles, no puedes restar {cant:.2f}."); return
                nueva = ant - cant
                dif   = -cant

            usuario = session.get_usuario()
            uid = usuario["id"] if usuario else None
            self.db.execute_query_safe(
                "UPDATE productos SET existencia=%s WHERE id=%s",
                (nueva, self._prod_ajuste["id"]))
            self._registrar_ajuste(self._prod_ajuste["id"], tipo_var.get(),
                                   ant, nueva, dif, combo_motivo.get(), uid,
                                   entry_notas.get().strip())
            unidad = self._prod_ajuste.get("unidad","PZA")
            unidad_lbl = {"PZA":"pzas", "KG":"kg", "KIT":"kits"}.get(unidad, unidad)
            signo = "+" if dif >= 0 else ""
            messagebox.showinfo("✅ Ajuste aplicado",
                f"Producto: {self._prod_ajuste['nombre']}\n"
                f"Antes: {ant:.2f} {unidad_lbl}  →  Después: {nueva:.2f} {unidad_lbl}  ({signo}{dif:.2f})\n"
                f"Tipo: {tipo_var.get()}  |  Motivo: {combo_motivo.get()}")
            entry_cod.delete(0,"end")
            entry_nueva.delete(0,"end")
            entry_nueva.insert(0,"0")
            entry_notas.delete(0,"end")
            lbl_info.configure(text="— Escribe el código y busca el producto")
            lbl_exist.configure(text="")
            self._prod_ajuste = None

        ctk.CTkButton(self.contenido, text="✅  Aplicar Ajuste", height=42,
                      fg_color=COLORES["warning"], hover_color="#B45309",
                      font=("Segoe UI",12,"bold"),
                      command=aplicar).pack(fill="x", padx=20, pady=8)

    def _registrar_ajuste(self, producto_id, tipo, cant_antes, cant_nueva,
                           diferencia, motivo, usuario_id, notas=""):
        try:
            self.db.execute_query_safe("""
                INSERT INTO ajustes_inventario
                (producto_id, usuario_id, tipo, cantidad_anterior,
                 cantidad_nueva, diferencia, motivo, notas)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (producto_id, usuario_id, tipo, cant_antes,
                  cant_nueva, diferencia, motivo, notas))
        except Exception as e:
            print(f"⚠ No se pudo registrar ajuste: {e}")

    # ── Formulario producto ───────────────────────────────────────────────────
    def _eliminar(self, prod):
        if messagebox.askyesno("Eliminar", f"¿Eliminar '{prod['nombre']}'?"):
            self.model.eliminar(prod["id"])
            self._cargar_tabla_productos()

    def _form_producto(self, prod=None):
        win = ctk.CTkToplevel(self)
        win.title("Nuevo Producto" if not prod else "Modificar Producto")
        win.geometry("540x640")
        win.grab_set()
        win.configure(fg_color=COLORES["bg_dark"])

        hdr = ctk.CTkFrame(win, fg_color="#f59e0b", corner_radius=0, height=36)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="NUEVO PRODUCTO" if not prod else "MODIFICAR PRODUCTO",
                     font=("Segoe UI",13,"bold"), text_color="white").pack(
                         side="left", padx=14, pady=6)

        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=8)
        entries = {}

        def campo(lbl, key):
            ctk.CTkLabel(scroll, text=lbl, font=("Segoe UI",11),
                         text_color=COLORES["text_secondary"]).pack(anchor="w", pady=(8,2))
            e = ctk.CTkEntry(scroll, height=34)
            e.pack(fill="x")
            if prod and prod.get(key) is not None:
                e.insert(0, str(prod[key]))
            entries[key] = e

        # ── Código de barras + botón cámara ──────────────────────────────────
        ctk.CTkLabel(scroll, text="Código de Barras", font=("Segoe UI",11),
                     text_color=COLORES["text_secondary"]).pack(anchor="w", pady=(8,2))
        cr = ctk.CTkFrame(scroll, fg_color="transparent")
        cr.pack(fill="x")
        cr.columnconfigure(0, weight=1)
        e_cod = ctk.CTkEntry(cr, height=34)
        e_cod.grid(row=0, column=0, sticky="ew", padx=(0,6))
        if prod and prod.get("codigo_barras"):
            e_cod.insert(0, prod["codigo_barras"])

        def _on_codigo_escaneado(codigo):
            e_cod.delete(0, "end")
            e_cod.insert(0, codigo)

        # Botón 📷: activo si pyzbar está disponible, deshabilitado si no
        btn_cam = crear_boton_escaner(cr, _on_codigo_escaneado)
        btn_cam.grid(row=0, column=1)
        entries["codigo_barras"] = e_cod

        campo("Descripción *", "nombre")

        # ── Tipo de venta (radio) ─────────────────────────────────────────────
        ctk.CTkLabel(scroll, text="Se vende", font=("Segoe UI",11),
                     text_color=COLORES["text_secondary"]).pack(anchor="w", pady=(8,2))
        vf = ctk.CTkFrame(scroll, fg_color="transparent")
        vf.pack(anchor="w")
        vende_var = ctk.StringVar(value=prod.get("unidad","PZA") if prod else "PZA")

        for txt, val in [("Por Unidad/Pza","PZA"),("A Granel (KG)","KG"),("Paquete/Kit","KIT")]:
            ctk.CTkRadioButton(vf, text=txt, variable=vende_var, value=val,
                               command=lambda: _actualizar_labels_inventario()
                               ).pack(side="left", padx=8)
        entries["unidad_radio"] = vende_var

        campo("Precio Costo $",   "precio_costo")
        campo("Precio Venta $",   "precio_venta")
        campo("Precio Mayoreo $", "precio_mayoreo")

        ctk.CTkLabel(scroll, text="Categoría / Departamento", font=("Segoe UI",11),
                     text_color=COLORES["text_secondary"]).pack(anchor="w", pady=(8,2))
        cats = self.model.get_categorias()
        cat_nombres = ["— Sin categoría —"] + [c["nombre"] for c in cats]
        cat_ids     = [None] + [c["id"] for c in cats]
        combo_cat = ctk.CTkComboBox(scroll, values=cat_nombres, height=34)
        combo_cat.pack(fill="x")
        if prod and prod.get("categoria_id"):
            try: combo_cat.set(cat_nombres[cat_ids.index(prod["categoria_id"])])
            except ValueError: pass
        entries["_combo_cat"] = combo_cat
        entries["_cat_ids"]   = cat_ids
        entries["_cat_names"] = cat_nombres

        # ── Sección inventario con etiquetas dinámicas ────────────────────────
        ctk.CTkFrame(scroll, height=1, fg_color=COLORES["border"]).pack(fill="x", pady=10)

        inv_hdr = ctk.CTkFrame(scroll, fg_color="transparent")
        inv_hdr.pack(fill="x")
        ctk.CTkLabel(inv_hdr, text="── Inventario",
                     font=("Segoe UI",11,"bold"), text_color="#f59e0b").pack(side="left")
        lbl_unidad_chip = ctk.CTkLabel(
            inv_hdr,
            text="  📦 en Piezas  ",
            font=("Segoe UI",10,"bold"),
            fg_color="#1e3a5f",
            corner_radius=6,
            text_color="#60a5fa")
        lbl_unidad_chip.pack(side="left", padx=10)

        lbl_existencia = ctk.CTkLabel(scroll, text="Cantidad Actual (pzas)",
                                       font=("Segoe UI",11),
                                       text_color=COLORES["text_secondary"])
        lbl_existencia.pack(anchor="w", pady=(8,2))
        e_exist = ctk.CTkEntry(scroll, height=34)
        e_exist.pack(fill="x")
        if prod and prod.get("existencia") is not None:
            e_exist.insert(0, str(prod["existencia"]))
        entries["existencia"] = e_exist

        lbl_minimo = ctk.CTkLabel(scroll, text="Mínimo en inventario (pzas)",
                                   font=("Segoe UI",11),
                                   text_color=COLORES["text_secondary"])
        lbl_minimo.pack(anchor="w", pady=(8,2))
        e_min = ctk.CTkEntry(scroll, height=34)
        e_min.pack(fill="x")
        if prod and prod.get("existencia_min") is not None:
            e_min.insert(0, str(prod["existencia_min"]))
        entries["existencia_min"] = e_min

        lbl_ayuda = ctk.CTkLabel(scroll, text="",
                                  font=("Segoe UI",10),
                                  text_color="#64748b",
                                  justify="left",
                                  wraplength=460)
        lbl_ayuda.pack(anchor="w", padx=2, pady=(2,4))

        def _actualizar_labels_inventario():
            unidad = vende_var.get()
            if unidad == "KG":
                chip_txt  = "  ⚖️  en Kilogramos  "
                chip_bg   = "#3b2a00"
                chip_fg   = "#fbbf24"
                lbl_exist_txt = "Cantidad Actual (kg)"
                lbl_min_txt   = "Mínimo en inventario (kg)"
                ayuda_txt = (
                    "💡 Granel: ingresa el peso en kilogramos.\n"
                    "   Ejemplo: 5.500 = 5 kg con 500 gramos.\n"
                    "   Puedes usar decimales (ej. 0.250 para 250 g)."
                )
            elif unidad == "KIT":
                chip_txt  = "  📦 en Kits/Paquetes  "
                chip_bg   = "#1a2e1a"
                chip_fg   = "#4ade80"
                lbl_exist_txt = "Cantidad Actual (kits)"
                lbl_min_txt   = "Mínimo en inventario (kits)"
                ayuda_txt = (
                    "💡 Paquete/Kit: cada unidad representa un kit completo.\n"
                    "   Ejemplo: 10 = 10 kits disponibles."
                )
            else:
                chip_txt  = "  📦 en Piezas  "
                chip_bg   = "#1e3a5f"
                chip_fg   = "#60a5fa"
                lbl_exist_txt = "Cantidad Actual (pzas)"
                lbl_min_txt   = "Mínimo en inventario (pzas)"
                ayuda_txt = (
                    "💡 Por pieza/unidad: ingresa la cantidad entera.\n"
                    "   Ejemplo: 24 = 24 piezas en inventario."
                )
            lbl_unidad_chip.configure(text=chip_txt, fg_color=chip_bg, text_color=chip_fg)
            lbl_existencia.configure(text=lbl_exist_txt)
            lbl_minimo.configure(text=lbl_min_txt)
            lbl_ayuda.configure(text=ayuda_txt)

        _actualizar_labels_inventario()

        # ── Guardar ───────────────────────────────────────────────────────────
        def guardar():
            data = {k: entries[k].get().strip()
                    for k in ["codigo_barras","nombre","precio_costo",
                              "precio_venta","precio_mayoreo","existencia","existencia_min"]}
            data["unidad"] = entries["unidad_radio"].get()
            if not data["nombre"] or not data["precio_venta"]:
                messagebox.showwarning("Error","Nombre y precio venta son obligatorios."); return
            try:
                for k in ["precio_costo","precio_venta","precio_mayoreo",
                           "existencia","existencia_min"]:
                    data[k] = float(data[k] or 0)
            except ValueError:
                messagebox.showwarning("Error","Revisa los valores numéricos."); return
            sel = combo_cat.get()
            if sel in entries["_cat_names"]:
                data["categoria_id"] = entries["_cat_ids"][entries["_cat_names"].index(sel)]
            if prod: self.model.actualizar(prod["id"], data)
            else:    self.model.crear(data)
            win.destroy()
            self._cargar_tabla_productos()

        bot = ctk.CTkFrame(win, fg_color="transparent")
        bot.pack(fill="x", padx=16, pady=8)
        ctk.CTkButton(bot, text="✅ Guardar Producto", height=40,
                      fg_color=COLORES["success"], font=("Segoe UI",12,"bold"),
                      command=guardar).pack(side="left", fill="x", expand=True, padx=(0,8))
        ctk.CTkButton(bot, text="✕ Cancelar", height=40,
                      fg_color=COLORES["danger"], font=("Segoe UI",12,"bold"),
                      command=win.destroy).pack(side="left", fill="x", expand=True)
