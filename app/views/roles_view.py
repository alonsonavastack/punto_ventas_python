import customtkinter as ctk
from tkinter import messagebox
from app.models.roles_model import RolModel, UsuarioModel
from app.utils.config import COLORES
from app.utils import session

class RolesView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.rol_model = RolModel()
        self.usuario_model = UsuarioModel()
        self._build()

    def _build(self):
        # Tabs: Roles | Usuarios
        self.tab = ctk.CTkTabview(self, fg_color=COLORES["bg_card"], corner_radius=12)
        self.tab.pack(fill="both", expand=True, padx=20, pady=16)
        self.tab.add("👥  Roles")
        self.tab.add("👤  Usuarios")

        self._tab_roles(self.tab.tab("👥  Roles"))
        self._tab_usuarios(self.tab.tab("👤  Usuarios"))

    # ── TAB ROLES ─────────────────────────────────────────────────────────────
    def _tab_roles(self, parent):
        hdr = ctk.CTkFrame(parent, fg_color="transparent")
        hdr.pack(fill="x", pady=(8,6))
        ctk.CTkLabel(hdr, text="Gestión de Roles",
                     font=("Segoe UI",18,"bold"),
                     text_color=COLORES["text_primary"]).pack(side="left")
        ctk.CTkButton(hdr, text="➕ Nuevo Rol", width=140,
                      command=self._form_rol).pack(side="right")

        self.scroll_roles = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.scroll_roles.pack(fill="both", expand=True)
        self._cargar_roles()

    def _cargar_roles(self):
        for w in self.scroll_roles.winfo_children():
            w.destroy()
        for rol in self.rol_model.get_all():
            card = ctk.CTkFrame(self.scroll_roles, fg_color=COLORES["bg_dark"], corner_radius=10)
            card.pack(fill="x", pady=4)

            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True, padx=14, pady=10)

            # Badge de color
            badge = ctk.CTkFrame(left, fg_color=rol.get("color","#3b82f6"),
                                  corner_radius=6, width=12, height=12)
            badge.pack(side="left", padx=(0,8))

            ctk.CTkLabel(left, text=rol["nombre"], font=("Segoe UI",14,"bold"),
                         text_color=COLORES["text_primary"]).pack(side="left")
            ctk.CTkLabel(left, text=f"  —  {rol.get('descripcion','') or ''}",
                         font=("Segoe UI",11),
                         text_color=COLORES["text_secondary"]).pack(side="left")

            right = ctk.CTkFrame(card, fg_color="transparent")
            right.pack(side="right", padx=10)
            ctk.CTkButton(right, text="✏️ Editar", width=90, height=30,
                          fg_color=COLORES["primary"],
                          command=lambda r=rol: self._form_rol(r)).pack(side="left", padx=4)
            ctk.CTkButton(right, text="🗑", width=36, height=30,
                          fg_color=COLORES["danger"],
                          command=lambda r=rol: self._eliminar_rol(r)).pack(side="left")

    def _eliminar_rol(self, rol):
        if messagebox.askyesno("Eliminar", f"¿Eliminar rol '{rol['nombre']}'?"):
            self.rol_model.eliminar(rol["id"])
            self._cargar_roles()

    def _form_rol(self, rol=None):
        win = ctk.CTkToplevel(self)
        win.title("Nuevo Rol" if not rol else f"Editar: {rol['nombre']}")
        win.geometry("820x620")
        win.grab_set()
        win.configure(fg_color=COLORES["bg_dark"])

        ctk.CTkLabel(win, text="🔐 Configurar Rol",
                     font=("Segoe UI",18,"bold"),
                     text_color=COLORES["text_primary"]).pack(pady=(16,4), padx=20, anchor="w")

        # Datos básicos
        datos_frame = ctk.CTkFrame(win, fg_color=COLORES["bg_card"], corner_radius=10)
        datos_frame.pack(fill="x", padx=20, pady=8)
        datos_frame.columnconfigure((0,1,2), weight=1)

        ctk.CTkLabel(datos_frame, text="Nombre del rol",
                     text_color=COLORES["text_secondary"], font=("Segoe UI",11)).grid(
                         row=0, column=0, padx=14, pady=(12,2), sticky="w")
        entry_nombre = ctk.CTkEntry(datos_frame, height=36)
        entry_nombre.grid(row=1, column=0, padx=14, pady=(0,12), sticky="ew")

        ctk.CTkLabel(datos_frame, text="Descripción",
                     text_color=COLORES["text_secondary"], font=("Segoe UI",11)).grid(
                         row=0, column=1, padx=14, pady=(12,2), sticky="w")
        entry_desc = ctk.CTkEntry(datos_frame, height=36)
        entry_desc.grid(row=1, column=1, padx=14, pady=(0,12), sticky="ew")

        ctk.CTkLabel(datos_frame, text="Color (hex)",
                     text_color=COLORES["text_secondary"], font=("Segoe UI",11)).grid(
                         row=0, column=2, padx=14, pady=(12,2), sticky="w")
        entry_color = ctk.CTkEntry(datos_frame, height=36, width=120)
        entry_color.grid(row=1, column=2, padx=14, pady=(0,12), sticky="w")

        if rol:
            entry_nombre.insert(0, rol["nombre"])
            entry_desc.insert(0, rol.get("descripcion","") or "")
            entry_color.insert(0, rol.get("color","#3b82f6") or "#3b82f6")
        else:
            entry_color.insert(0, "#3b82f6")

        # Permisos en dos columnas
        ctk.CTkLabel(win, text="Asignar Permisos",
                     font=("Segoe UI",13,"bold"),
                     text_color=COLORES["text_primary"]).pack(padx=20, anchor="w", pady=(4,2))
        ctk.CTkLabel(win, text="Selecciona permisos de la izquierda y pásalos a la derecha con los botones ➡",
                     font=("Segoe UI",10),
                     text_color=COLORES["text_secondary"]).pack(padx=20, anchor="w")

        perm_frame = ctk.CTkFrame(win, fg_color=COLORES["bg_card"], corner_radius=10)
        perm_frame.pack(fill="both", expand=True, padx=20, pady=8)
        perm_frame.columnconfigure(0, weight=1)
        perm_frame.columnconfigure(2, weight=1)

        # ── Columna izquierda: disponibles
        ctk.CTkLabel(perm_frame, text="📋  Permisos disponibles",
                     font=("Segoe UI",12,"bold"),
                     text_color=COLORES["text_secondary"]).grid(row=0,column=0,pady=(10,4),padx=10,sticky="w")
        scroll_dis = ctk.CTkScrollableFrame(perm_frame, fg_color=COLORES["bg_dark"],
                                             corner_radius=8, height=280)
        scroll_dis.grid(row=1, column=0, sticky="nsew", padx=(10,4), pady=(0,10))

        # ── Botones centrales
        btn_frame = ctk.CTkFrame(perm_frame, fg_color="transparent")
        btn_frame.grid(row=1, column=1, padx=4)
        btn_add = ctk.CTkButton(btn_frame, text="➡", width=44, height=36,
                                 fg_color=COLORES["success"])
        btn_add.pack(pady=4)
        btn_add_all = ctk.CTkButton(btn_frame, text="⇒", width=44, height=36,
                                     fg_color=COLORES["primary"])
        btn_add_all.pack(pady=4)
        btn_rem = ctk.CTkButton(btn_frame, text="⬅", width=44, height=36,
                                 fg_color=COLORES["warning"])
        btn_rem.pack(pady=4)
        btn_rem_all = ctk.CTkButton(btn_frame, text="⇐", width=44, height=36,
                                     fg_color=COLORES["danger"])
        btn_rem_all.pack(pady=4)

        # ── Columna derecha: asignados
        ctk.CTkLabel(perm_frame, text="✅  Permisos asignados",
                     font=("Segoe UI",12,"bold"),
                     text_color=COLORES["success"]).grid(row=0,column=2,pady=(10,4),padx=10,sticky="w")
        scroll_asi = ctk.CTkScrollableFrame(perm_frame, fg_color=COLORES["bg_dark"],
                                             corner_radius=8, height=280)
        scroll_asi.grid(row=1, column=2, sticky="nsew", padx=(4,10), pady=(0,10))

        # Cargar catálogo
        todos_perms = self.rol_model.get_permisos_catalogo()
        rol_perms = set(self.rol_model.get_by_id(rol["id"])["permisos"]) if rol else set()

        disponibles = [p for p in todos_perms if p["clave"] not in rol_perms]
        asignados   = [p for p in todos_perms if p["clave"] in rol_perms]

        sel_dis = []
        sel_asi = []

        def render_lista(scroll, items, sel_list, color_sel):
            for w in scroll.winfo_children():
                w.destroy()
            modulo_actual = None
            for p in items:
                if p["modulo"] != modulo_actual:
                    modulo_actual = p["modulo"]
                    ctk.CTkLabel(scroll, text=f"— {modulo_actual} —",
                                 font=("Segoe UI",10,"bold"),
                                 text_color=COLORES["primary"]).pack(anchor="w", padx=4, pady=(6,2))
                selected = p["clave"] in sel_list
                bg = color_sel if selected else "transparent"
                btn = ctk.CTkButton(scroll, text=f"  {p['nombre']}",
                                    anchor="w", height=28,
                                    font=("Segoe UI",11),
                                    fg_color=bg,
                                    hover_color=COLORES["bg_input"],
                                    text_color=COLORES["text_primary"],
                                    corner_radius=4,
                                    command=lambda c=p["clave"]: toggle(c, sel_list, color_sel, scroll, items))
                btn.pack(fill="x", pady=1, padx=4)

        def toggle(clave, sel_list, color, scroll, items):
            if clave in sel_list:
                sel_list.remove(clave)
            else:
                sel_list.append(clave)
            render_lista(scroll, items, sel_list, color)

        def mover(de_lista, a_lista, de_scroll, a_scroll, sel, todo=False):
            if todo:
                claves = [p["clave"] for p in de_lista]
            else:
                claves = list(sel)
            mover_items = [p for p in de_lista if p["clave"] in claves]
            for p in mover_items:
                de_lista.remove(p)
                a_lista.append(p)
            sel.clear()
            render_lista(de_scroll, de_lista, sel_dis if de_scroll==scroll_dis else sel_asi, COLORES["primary"])
            render_lista(a_scroll, a_lista, sel_asi if a_scroll==scroll_asi else sel_dis, COLORES["success"])

        btn_add.configure(command=lambda: mover(disponibles, asignados, scroll_dis, scroll_asi, sel_dis))
        btn_add_all.configure(command=lambda: mover(disponibles, asignados, scroll_dis, scroll_asi, sel_dis, todo=True))
        btn_rem.configure(command=lambda: mover(asignados, disponibles, scroll_asi, scroll_dis, sel_asi))
        btn_rem_all.configure(command=lambda: mover(asignados, disponibles, scroll_asi, scroll_dis, sel_asi, todo=True))

        render_lista(scroll_dis, disponibles, sel_dis, COLORES["primary"])
        render_lista(scroll_asi, asignados, sel_asi, COLORES["success"])

        def guardar():
            nombre = entry_nombre.get().strip()
            desc   = entry_desc.get().strip()
            color  = entry_color.get().strip() or "#3b82f6"
            if not nombre:
                messagebox.showwarning("Error", "El nombre es obligatorio.")
                return
            perms = [p["clave"] for p in asignados]
            if rol:
                self.rol_model.actualizar(rol["id"], nombre, desc, color, perms)
            else:
                self.rol_model.crear(nombre, desc, color, perms)
            win.destroy()
            self._cargar_roles()

        ctk.CTkButton(win, text="💾  Guardar Rol", height=42,
                      font=("Segoe UI",13,"bold"),
                      fg_color=COLORES["success"],
                      command=guardar).pack(fill="x", padx=20, pady=(4,14))

    # ── TAB USUARIOS ──────────────────────────────────────────────────────────
    def _tab_usuarios(self, parent):
        hdr = ctk.CTkFrame(parent, fg_color="transparent")
        hdr.pack(fill="x", pady=(8,6))
        ctk.CTkLabel(hdr, text="Gestión de Usuarios",
                     font=("Segoe UI",18,"bold"),
                     text_color=COLORES["text_primary"]).pack(side="left")
        ctk.CTkButton(hdr, text="➕ Nuevo Usuario", width=150,
                      command=self._form_usuario).pack(side="right")

        # Cabecera tabla
        tabla = ctk.CTkFrame(parent, fg_color=COLORES["bg_dark"], corner_radius=12)
        tabla.pack(fill="both", expand=True)
        tabla.rowconfigure(1, weight=1)
        tabla.columnconfigure(0, weight=1)

        hdr_row = ctk.CTkFrame(tabla, fg_color=COLORES["primary"], corner_radius=6, height=34)
        hdr_row.grid(row=0, column=0, sticky="ew", padx=8, pady=(8,4))
        for txt, w in [("Nombre",200),("Usuario",140),("Rol",160),("Estado",80),("Acciones",120)]:
            ctk.CTkLabel(hdr_row, text=txt, font=("Segoe UI",11,"bold"),
                         text_color="white", width=w).pack(side="left", padx=4)

        self.scroll_usuarios = ctk.CTkScrollableFrame(tabla, fg_color="transparent")
        self.scroll_usuarios.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        self._cargar_usuarios()

    def _cargar_usuarios(self):
        for w in self.scroll_usuarios.winfo_children():
            w.destroy()
        for i, u in enumerate(self.usuario_model.get_all()):
            bg = COLORES["bg_card"] if i%2==0 else "transparent"
            row = ctk.CTkFrame(self.scroll_usuarios, fg_color=bg, corner_radius=4, height=36)
            row.pack(fill="x", pady=1)

            color_rol = u.get("rol_color","#64748b") or "#64748b"
            for v, w in [(u["nombre"][:24],200),(u["usuario"],140)]:
                ctk.CTkLabel(row, text=v, font=("Segoe UI",11),
                             text_color=COLORES["text_primary"], width=w, anchor="w").pack(side="left", padx=4)

            # Badge rol
            badge_frame = ctk.CTkFrame(row, fg_color=color_rol, corner_radius=6, width=140, height=22)
            badge_frame.pack(side="left", padx=4)
            badge_frame.pack_propagate(False)
            ctk.CTkLabel(badge_frame, text=u.get("rol_nombre","Sin rol") or "Sin rol",
                         font=("Segoe UI",10,"bold"), text_color="white").pack(expand=True)

            estado = "✅ Activo" if u.get("activo") else "❌ Inactivo"
            ctk.CTkLabel(row, text=estado, font=("Segoe UI",10),
                         text_color=COLORES["success"], width=80).pack(side="left", padx=4)

            ctk.CTkButton(row, text="✏️", width=36, height=28,
                          fg_color=COLORES["primary"],
                          command=lambda x=u: self._form_usuario(x)).pack(side="left", padx=2)
            ctk.CTkButton(row, text="🗑", width=36, height=28,
                          fg_color=COLORES["danger"],
                          command=lambda x=u: self._eliminar_usuario(x)).pack(side="left", padx=2)

    def _eliminar_usuario(self, u):
        if session.get_usuario()["id"] == u["id"]:
            messagebox.showwarning("Error", "No puedes eliminar tu propio usuario.")
            return
        if messagebox.askyesno("Eliminar", f"¿Eliminar usuario '{u['nombre']}'?"):
            self.usuario_model.eliminar(u["id"])
            self._cargar_usuarios()

    def _form_usuario(self, usuario=None):
        win = ctk.CTkToplevel(self)
        win.title("Usuario")
        win.geometry("420x460")
        win.grab_set()
        win.configure(fg_color=COLORES["bg_dark"])

        ctk.CTkLabel(win, text="👤 Usuario",
                     font=("Segoe UI",18,"bold"),
                     text_color=COLORES["text_primary"]).pack(pady=(20,12), padx=20, anchor="w")

        frame = ctk.CTkFrame(win, fg_color=COLORES["bg_card"], corner_radius=12)
        frame.pack(fill="x", padx=20)

        campos = [("Nombre completo *","nombre"),("Usuario *","usuario"),
                  ("Contraseña" + (" (dejar vacío = no cambiar)" if usuario else " *"),"password")]
        entries = {}
        for lbl, key in campos:
            ctk.CTkLabel(frame, text=lbl, font=("Segoe UI",11),
                         text_color=COLORES["text_secondary"]).pack(anchor="w", padx=16, pady=(12,2))
            e = ctk.CTkEntry(frame, height=36, show="●" if key=="password" else "")
            e.pack(fill="x", padx=16, pady=(0,4))
            if usuario and key != "password" and usuario.get(key):
                e.insert(0, str(usuario[key]))
            entries[key] = e

        ctk.CTkLabel(frame, text="Rol", font=("Segoe UI",11),
                     text_color=COLORES["text_secondary"]).pack(anchor="w", padx=16, pady=(12,2))
        roles = self.rol_model.get_all()
        rol_nombres = [r["nombre"] for r in roles]
        rol_ids     = [r["id"]     for r in roles]
        combo_rol = ctk.CTkComboBox(frame, values=rol_nombres, height=36)
        combo_rol.pack(fill="x", padx=16, pady=(0,16))
        if usuario and usuario.get("rol_id"):
            try:
                idx = rol_ids.index(usuario["rol_id"])
                combo_rol.set(rol_nombres[idx])
            except ValueError:
                pass

        def guardar():
            nombre   = entries["nombre"].get().strip()
            usuario_ = entries["usuario"].get().strip()
            password = entries["password"].get().strip()
            if not nombre or not usuario_:
                messagebox.showwarning("Error", "Nombre y usuario son obligatorios."); return
            if not usuario and not password:
                messagebox.showwarning("Error", "La contraseña es obligatoria."); return
            sel = combo_rol.get()
            rol_id = rol_ids[rol_nombres.index(sel)] if sel in rol_nombres else None
            if usuario:
                self.usuario_model.actualizar(usuario["id"], nombre, usuario_, rol_id, password or None)
            else:
                self.usuario_model.crear(nombre, usuario_, password, rol_id)
            win.destroy()
            self._cargar_usuarios()

        ctk.CTkButton(win, text="💾  Guardar", height=42,
                      font=("Segoe UI",13,"bold"),
                      fg_color=COLORES["success"],
                      command=guardar).pack(fill="x", padx=20, pady=14)
