import customtkinter as ctk
from tkinter import messagebox
from app.models.auth_model import AuthModel
from app.utils.config import COLORES
from app.utils.window_utils import centrar_ventana


class LoginView(ctk.CTkToplevel):
    def __init__(self, parent, on_success):
        super().__init__(parent)
        self.on_success = on_success
        self.auth = AuthModel()
        self.title("Iniciar sesión")
        self.geometry("420x540")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build()
        self.update_idletasks()
        centrar_ventana(self, 420, 540)
        self.lift()
        self.focus_force()
        self.grab_set()
        self.after(100, lambda: self.entry_usuario.focus())

    def _on_close(self):
        import sys; sys.exit(0)

    def _build(self):
        self.configure(fg_color=COLORES["bg_dark"])

        ctk.CTkLabel(self, text="🛒", font=("Segoe UI", 44)).pack(pady=(24, 2))
        ctk.CTkLabel(self, text="Punto de Ventas",
                     font=("Segoe UI", 20, "bold"),
                     text_color=COLORES["text_primary"]).pack()
        ctk.CTkLabel(self, text="Inicia sesión para continuar",
                     font=("Segoe UI", 12),
                     text_color=COLORES["text_secondary"]).pack(pady=(2, 16))

        frame = ctk.CTkFrame(self, fg_color=COLORES["bg_card"], corner_radius=16)
        frame.pack(fill="x", padx=36)

        ctk.CTkLabel(frame, text="Usuario", font=("Segoe UI", 12),
                     text_color=COLORES["text_secondary"]).pack(anchor="w", padx=20, pady=(20, 2))
        self.entry_usuario = ctk.CTkEntry(frame, placeholder_text="Ingresa tu usuario",
                                           height=40, font=("Segoe UI", 13))
        self.entry_usuario.pack(fill="x", padx=20)

        ctk.CTkLabel(frame, text="Contraseña", font=("Segoe UI", 12),
                     text_color=COLORES["text_secondary"]).pack(anchor="w", padx=20, pady=(14, 2))
        self.entry_pass = ctk.CTkEntry(frame, placeholder_text="Ingresa tu contraseña",
                                        height=40, font=("Segoe UI", 13), show="●")
        self.entry_pass.pack(fill="x", padx=20)
        self.entry_pass.bind("<Return>", lambda e: self._login())

        self.lbl_error = ctk.CTkLabel(frame, text="", font=("Segoe UI", 11),
                                       text_color=COLORES["danger"])
        self.lbl_error.pack(pady=(8, 4))

        ctk.CTkButton(frame, text="Iniciar sesión", height=44,
                      font=("Segoe UI", 14, "bold"),
                      fg_color=COLORES["primary"],
                      hover_color=COLORES["primary_hover"],
                      command=self._login).pack(fill="x", padx=20, pady=(4, 20))

    def _login(self):
        usuario  = self.entry_usuario.get().strip()
        password = self.entry_pass.get()
        if not usuario or not password:
            self.lbl_error.configure(text="⚠ Completa todos los campos")
            return
        user, error = self.auth.login(usuario, password)
        if error:
            self.lbl_error.configure(text=f"❌ {error}")
            self.entry_pass.delete(0, "end")
            return
        try: self.grab_release()
        except Exception: pass
        self.destroy()
        self.on_success(user)
