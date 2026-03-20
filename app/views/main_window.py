import customtkinter as ctk
import traceback
import os
import platform
from app.utils.config import COLORES, APP_NOMBRE, APP_VERSION, VENTANA_W, VENTANA_H
from app.utils import session
from app.utils.logo_utils import ruta_logo

_ES_MAC = platform.system() == "Darwin"


class MainWindow(ctk.CTk):
    """
    Ventana principal — es la ÚNICA instancia de ctk.CTk en todo el programa.
    El login y la apertura de caja usan CTkToplevel, no ctk.CTk.
    """
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title(f"{APP_NOMBRE} v{APP_VERSION}")
        self.geometry(f"{VENTANA_W}x{VENTANA_H}")
        self.minsize(1100, 680)
        self._seccion_activa = "ventas"
        self._logo_img = None       # referencia global al CTkImage del sidebar

        # Ocultar hasta que termine el login
        self.withdraw()

        # Iniciar flujo: login → caja → mostrar ventana
        self.after(10, self._iniciar_flujo)

    # ── Flujo de inicio ───────────────────────────────────────────────────────
    def _iniciar_flujo(self):
        from app.views.login_view import LoginView
        LoginView(self, on_success=self._post_login)

    def _post_login(self, user):
        from app.models.caja_model import CajaModel
        caja_model    = CajaModel()
        sesion_activa = caja_model.get_sesion_activa(user["id"])
        if sesion_activa:
            session.set_sesion_caja(sesion_activa)
            self._mostrar_app()
        elif session.tiene_permiso("caja_abrir"):
            from app.views.caja_view import AperturaCajaView
            AperturaCajaView(self, on_success=lambda s: self._mostrar_app())
        else:
            self._mostrar_app()

    def _mostrar_app(self):
        self._build_layout()
        self._show_section("ventas")
        self.deiconify()
        self.state('zoomed')  # Maximizar la ventana
        self.lift()
        self.focus_force()
        self.after(1000, self._alertar_stock_bajo)

    # ── Stock bajo ────────────────────────────────────────────────────────────
    def _alertar_stock_bajo(self):
        try:
            from app.models.producto_model import ProductoModel
            bajos = ProductoModel().stock_bajo()
            if bajos:
                from tkinter import messagebox
                lista = "\n".join(
                    f"  • {p['nombre']} — existencia: {int(float(p.get('existencia',0)))}"
                    for p in bajos[:10])
                if len(bajos) > 10:
                    lista += f"\n  ... y {len(bajos)-10} más"
                messagebox.showwarning(
                    f"⚠️ Stock bajo — {len(bajos)} producto(s)",
                    f"Los siguientes productos están por agotarse:\n\n{lista}\n\n"
                    "Ve a Inventario → Productos bajos para más detalles.")
        except Exception as e:
            print(f"⚠ No se pudo verificar stock: {e}")

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_layout(self):
        usuario = session.get_usuario()

        # ── Sidebar exterior ──────────────────────────────────────────────────
        self.sidebar_outer = ctk.CTkFrame(
            self, width=224, corner_radius=0, fg_color=COLORES["bg_dark"])
        self.sidebar_outer.pack(side="left", fill="y")
        self.sidebar_outer.pack_propagate(False)

        # ── Top fijo: logo + nombre + usuario ─────────────────────────────────
        top_fixed = ctk.CTkFrame(
            self.sidebar_outer, fg_color=COLORES["bg_dark"], corner_radius=0)
        top_fixed.pack(fill="x")

        # Cargar logo usando PIL directamente con ImageTk para evitar pyimage error
        logo_ok = self._cargar_logo_sidebar(top_fixed, size=80)
        if not logo_ok:
            ctk.CTkLabel(top_fixed, text="🛒",
                         font=("Segoe UI", 32)).pack(pady=(14, 0))

        ctk.CTkLabel(top_fixed, text=APP_NOMBRE,
                     font=("Segoe UI", 14, "bold"),
                     text_color=COLORES["text_primary"]).pack(pady=(2, 0))
        ctk.CTkLabel(top_fixed, text=f"v{APP_VERSION}",
                     font=("Segoe UI", 9),
                     text_color=COLORES["text_secondary"]).pack()

        if not logo_ok:
            ctk.CTkLabel(top_fixed,
                         text="Ir a Configuración → Logo",
                         font=("Segoe UI", 8),
                         text_color="#374151",
                         wraplength=180).pack(pady=(0, 2))

        ctk.CTkFrame(top_fixed, height=1,
                     fg_color=COLORES["border"]).pack(fill="x", padx=16, pady=4)

        if usuario:
            rol_color = usuario.get("rol_color", "#3b82f6") or "#3b82f6"
            info = ctk.CTkFrame(top_fixed, fg_color=COLORES["bg_card"], corner_radius=8)
            info.pack(fill="x", padx=10, pady=(0, 6))
            ctk.CTkLabel(info, text=f"👤  {usuario['nombre']}",
                         font=("Segoe UI", 11, "bold"),
                         text_color=COLORES["text_primary"]).pack(
                             anchor="w", padx=10, pady=(6, 2))
            badge = ctk.CTkFrame(info, fg_color=rol_color, corner_radius=6)
            badge.pack(anchor="w", padx=10, pady=(0, 6))
            ctk.CTkLabel(badge,
                         text=f"  {usuario.get('rol_nombre','Usuario')}  ",
                         font=("Segoe UI", 9, "bold"),
                         text_color="white").pack()

        ctk.CTkFrame(top_fixed, height=1,
                     fg_color=COLORES["border"]).pack(fill="x", padx=16, pady=2)

        # ── Bot fijo: caja + cerrar sesión ────────────────────────────────────
        bot_fixed = ctk.CTkFrame(
            self.sidebar_outer, fg_color=COLORES["bg_dark"], corner_radius=0)
        bot_fixed.pack(side="bottom", fill="x", padx=10, pady=10)

        from app.utils import session as sess
        if sess.caja_abierta():
            ctk.CTkLabel(bot_fixed, text="🟢 Caja abierta",
                         font=("Segoe UI", 10),
                         text_color=COLORES["success"]).pack(pady=(0, 3))
            ctk.CTkButton(bot_fixed, text="🔒 Cerrar caja", height=32,
                          fg_color=COLORES["warning"], hover_color="#B45309",
                          font=("Segoe UI", 10),
                          command=self._cerrar_caja).pack(fill="x")
        else:
            ctk.CTkLabel(bot_fixed, text="🔴 Caja cerrada",
                         font=("Segoe UI", 10),
                         text_color=COLORES["danger"]).pack(pady=(0, 3))

        ctk.CTkButton(bot_fixed, text="🚪 Cerrar sesión", height=32,
                      fg_color=COLORES["secondary"], hover_color="#475569",
                      font=("Segoe UI", 10),
                      command=self._logout).pack(fill="x", pady=(4, 0))

        # ── Nav scrollable ────────────────────────────────────────────────────
        self._nav_scroll = ctk.CTkScrollableFrame(
            self.sidebar_outer,
            fg_color=COLORES["bg_dark"],
            corner_radius=0,
            scrollbar_button_color=COLORES["bg_card"],
            scrollbar_button_hover_color=COLORES["primary"])
        self._nav_scroll.pack(fill="both", expand=True)
        self._setup_sidebar_scroll()

        self._nav_buttons = {}
        for label, key, permiso in [
            ("🛒  Ventas",         "ventas",         "ventas_ver"),
            ("💰  Caja",           "caja",           "caja_abrir"),
            ("📦  Inventario",     "inventario",     "inventario_ver"),
            ("🏷️   Categorías",   "categorias",     "categorias_ver"),
            ("👥  Clientes",       "clientes",       "clientes_ver"),
            ("🏭  Proveedores",    "proveedores",    "proveedores_ver"),
            ("📊  Reportes",       "reportes",       "reportes_ver"),
            ("🏦  Historial Caja", "historial_caja", "reportes_ver_todos"),
        ]:
            if session.tiene_permiso(permiso):
                self._agregar_btn_nav(label, key)

        ctk.CTkFrame(self._nav_scroll, height=1,
                     fg_color=COLORES["border"]).pack(fill="x", padx=16, pady=6)

        if session.tiene_permiso("roles_gestionar") or \
                session.tiene_permiso("usuarios_gestionar"):
            self._agregar_btn_nav("🔐  Roles y Usuarios", "roles")
        if session.tiene_permiso("config_ver"):
            self._agregar_btn_nav("⚙️   Configuración", "config")
        if session.tiene_permiso("config_editar"):
            self._agregar_btn_nav("🗄️   Base de Datos", "backup")

        # ── Área principal ────────────────────────────────────────────────────
        self.main_area = ctk.CTkFrame(
            self, corner_radius=0, fg_color=COLORES["bg_card"])
        self.main_area.pack(side="left", fill="both", expand=True)

    def _cargar_logo_sidebar(self, parent, size=80) -> bool:
        """
        Carga el logo usando PIL + ImageTk directamente (sin CTkImage)
        para evitar el error 'pyimage does not exist' que ocurre cuando
        hay múltiples ventanas Tk o imágenes creadas antes de que el
        mainloop esté activo.
        """
        p = ruta_logo()
        if not p:
            return False
        try:
            from PIL import Image, ImageTk
            img = Image.open(p).convert("RGBA")
            img.thumbnail((size, size), Image.LANCZOS)

            # Guardar en self para que no la borre el GC
            self._logo_img = ImageTk.PhotoImage(img)

            import tkinter as tk
            lbl = tk.Label(parent,
                           image=self._logo_img,
                           bg=COLORES["bg_dark"],
                           bd=0)
            lbl.pack(pady=(12, 2))
            return True
        except Exception as e:
            print(f"⚠ No se pudo cargar logo: {e}")
            return False

    def _agregar_btn_nav(self, label, key):
        btn = ctk.CTkButton(
            self._nav_scroll, text=label, anchor="w", height=38,
            font=("Segoe UI", 12), fg_color="transparent",
            hover_color=COLORES["bg_card"],
            text_color=COLORES["text_secondary"], corner_radius=8,
            command=lambda k=key: self._show_section(k))
        btn.pack(fill="x", padx=6, pady=1)
        self._nav_buttons[key] = btn

    def _setup_sidebar_scroll(self):
        try:
            canvas = self._nav_scroll._parent_canvas
        except AttributeError:
            return
        if _ES_MAC:
            def _on(e):
                self.bind_all("<MouseWheel>",
                              lambda ev: canvas.yview_scroll(
                                  int(-ev.delta / 4), "units"), add="+")
            def _off(e):
                self.unbind_all("<MouseWheel>")
            canvas.bind("<Enter>", _on,  add="+")
            canvas.bind("<Leave>", _off, add="+")
            self._nav_scroll.bind("<Enter>", _on,  add="+")
            self._nav_scroll.bind("<Leave>", _off, add="+")
        else:
            def _wh(e):
                canvas.yview_scroll(int(-e.delta / 120), "units")
            canvas.bind("<MouseWheel>", _wh, add="+")
            canvas.bind("<Button-4>",
                        lambda e: canvas.yview_scroll(-2, "units"), add="+")
            canvas.bind("<Button-5>",
                        lambda e: canvas.yview_scroll(2,  "units"), add="+")

    # ── Navegación ────────────────────────────────────────────────────────────
    def _show_section(self, section: str):
        self._seccion_activa = section
        for w in self.main_area.winfo_children():
            w.destroy()
        for key, btn in self._nav_buttons.items():
            btn.configure(
                fg_color=COLORES["primary"] if key == section else "transparent",
                text_color=COLORES["text_primary"] if key == section
                else COLORES["text_secondary"])
        try:
            self._cargar_seccion(section)
        except Exception as e:
            print(f"❌ Error en '{section}':\n{traceback.format_exc()}")
            self._mostrar_error(section, str(e))

    def _cargar_seccion(self, section):
        if section == "ventas":
            from app.views.ventas_view import VentasView
            VentasView(self.main_area).pack(fill="both", expand=True)
        elif section == "caja":
            self._show_caja()
        elif section == "inventario":
            from app.views.inventario_view import InventarioView
            InventarioView(self.main_area).pack(fill="both", expand=True)
        elif section == "categorias":
            from app.views.categorias_view import CategoriasView
            CategoriasView(self.main_area).pack(fill="both", expand=True)
        elif section == "clientes":
            from app.views.clientes_view import ClientesView
            ClientesView(self.main_area).pack(fill="both", expand=True)
        elif section == "proveedores":
            from app.views.proveedores_view import ProveedoresView
            ProveedoresView(self.main_area).pack(fill="both", expand=True)
        elif section == "reportes":
            from app.views.reportes_view import ReportesView
            ReportesView(self.main_area).pack(fill="both", expand=True)
        elif section == "roles":
            from app.views.roles_view import RolesView
            RolesView(self.main_area).pack(fill="both", expand=True)
        elif section == "config":
            from app.views.config_view import ConfigView
            ConfigView(self.main_area).pack(fill="both", expand=True)
        elif section == "historial_caja":
            from app.views.historial_cortes_view import HistorialCortesView
            HistorialCortesView(self.main_area).pack(fill="both", expand=True)
        elif section == "backup":
            from app.views.backup_view import BackupView
            BackupView(self.main_area).pack(fill="both", expand=True)

    def _mostrar_error(self, section, error):
        ctk.CTkLabel(self.main_area, text="⚠️  Error al cargar el módulo",
                     font=("Segoe UI", 18, "bold"),
                     text_color=COLORES["danger"]).pack(pady=(60, 8))
        ctk.CTkLabel(self.main_area, text=f"Módulo: {section}",
                     font=("Segoe UI", 13),
                     text_color=COLORES["text_secondary"]).pack()
        ctk.CTkLabel(self.main_area, text=error,
                     font=("Segoe UI", 11),
                     text_color=COLORES["warning"],
                     wraplength=700).pack(pady=8)
        ctk.CTkButton(self.main_area, text="🔄 Reintentar", height=40,
                      fg_color=COLORES["primary"],
                      command=lambda: self._show_section(section)).pack(pady=12)

    def _show_caja(self):
        from app.utils import session as sess
        if sess.caja_abierta():
            from app.views.caja_panel_view import CajaPanelView
            CajaPanelView(self.main_area).pack(fill="both", expand=True)
        else:
            ctk.CTkLabel(self.main_area, text="💰  Caja",
                         font=("Segoe UI", 20, "bold"),
                         text_color=COLORES["text_primary"]).pack(pady=40)
            ctk.CTkLabel(self.main_area, text="La caja está cerrada.",
                         font=("Segoe UI", 13),
                         text_color=COLORES["text_secondary"]).pack()
            ctk.CTkButton(self.main_area, text="✅ Abrir Caja",
                          font=("Segoe UI", 13, "bold"), height=44, width=200,
                          fg_color=COLORES["success"],
                          command=self._abrir_caja).pack(pady=16)

    def _abrir_caja(self):
        from app.views.caja_view import AperturaCajaView
        AperturaCajaView(self, on_success=self._on_caja_abierta)

    def _on_caja_abierta(self, _):
        self._rebuild()

    def _cerrar_caja(self):
        from app.views.caja_view import CierreCajaView
        CierreCajaView(self, on_success=self._rebuild)

    def _logout(self):
        from tkinter import messagebox
        if not messagebox.askyesno("Cerrar sesión", "¿Deseas cerrar sesión?"):
            return
        session.logout()
        # Limpiar layout actual
        for w in self.winfo_children():
            w.destroy()
        self._logo_img = None
        self.withdraw()
        # Volver al login
        self.after(10, self._iniciar_flujo)

    def _rebuild(self, volver_a=None):
        """Reconstruye el layout y vuelve a la sección activa."""
        seccion = volver_a or self._seccion_activa or "ventas"
        self._logo_img = None
        for w in self.winfo_children():
            w.destroy()
        self._build_layout()
        self._show_section(seccion)


# ── login_view necesita parent ahora ─────────────────────────────────────────
# Actualizar LoginView para aceptar parent opcional
def _iniciar_app():
    win = MainWindow()
    win.mainloop()
