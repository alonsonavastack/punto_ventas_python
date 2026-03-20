"""
widgets/formulario.py
Formulario reutilizable en ventana modal.
"""
import customtkinter as ctk
from tkinter import messagebox
from app.utils.config import COLORES

class FormularioModal(ctk.CTkToplevel):
    def __init__(self, parent, titulo: str, campos: list,
                 on_guardar, datos=None, ancho=460, alto=None):
        """
        campos: [{"key":"nombre","label":"Nombre *","tipo":"entry|combo|check",
                  "opciones":[],"requerido":True}, ...]
        on_guardar: fn(data_dict)
        datos: dict con valores existentes (para editar)
        """
        super().__init__(parent)
        self.title(titulo)
        self.resizable(False, False)
        self.grab_set()
        self.configure(fg_color=COLORES["bg_dark"])
        self._campos_def = campos
        self._on_guardar = on_guardar
        self._datos = datos or {}
        self._widgets = {}

        ctk.CTkLabel(self, text=titulo, font=("Segoe UI",17,"bold"),
                     text_color=COLORES["text_primary"]).pack(
                         padx=20, pady=(20,10), anchor="w")

        frame = ctk.CTkScrollableFrame(self, fg_color=COLORES["bg_card"],
                                        corner_radius=12)
        frame.pack(fill="both", expand=True, padx=20, pady=4)

        for campo in campos:
            lbl = campo.get("label", campo["key"])
            tipo = campo.get("tipo", "entry")
            ctk.CTkLabel(frame, text=lbl, font=("Segoe UI",11),
                         text_color=COLORES["text_secondary"]).pack(
                             anchor="w", padx=16, pady=(10,2))
            if tipo == "combo":
                opts = campo.get("opciones", [])
                w = ctk.CTkComboBox(frame, values=opts, height=34)
                w.pack(fill="x", padx=16, pady=(0,4))
                val = self._datos.get(campo["key"])
                if val and val in opts:
                    w.set(val)
                elif opts:
                    w.set(opts[0])
            elif tipo == "check":
                var = ctk.BooleanVar(value=bool(self._datos.get(campo["key"], False)))
                w = ctk.CTkCheckBox(frame, text="", variable=var)
                w.pack(anchor="w", padx=16, pady=(0,4))
                w._var = var
            else:
                show = "●" if campo.get("password") else ""
                w = ctk.CTkEntry(frame, height=34, show=show)
                w.pack(fill="x", padx=16, pady=(0,4))
                val = self._datos.get(campo["key"])
                if val is not None:
                    w.insert(0, str(val))
            self._widgets[campo["key"]] = w

        ctk.CTkButton(self, text="💾  Guardar", height=42,
                      font=("Segoe UI",13,"bold"),
                      fg_color=COLORES["success"],
                      command=self._guardar).pack(fill="x", padx=20, pady=14)

        if alto:
            self.geometry(f"{ancho}x{alto}")
        else:
            self.geometry(f"{ancho}x{min(100 + len(campos)*70, 700)}")

    def _guardar(self):
        data = {}
        for campo in self._campos_def:
            w = self._widgets[campo["key"]]
            tipo = campo.get("tipo","entry")
            if tipo == "check":
                data[campo["key"]] = w._var.get()
            elif tipo == "combo":
                data[campo["key"]] = w.get()
            else:
                data[campo["key"]] = w.get().strip()
            if campo.get("requerido") and not data[campo["key"]]:
                messagebox.showwarning("Requerido", f"'{campo['label']}' es obligatorio.")
                return
        self._on_guardar(data)
        self.destroy()
