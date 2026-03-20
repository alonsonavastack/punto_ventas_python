import customtkinter as ctk
from tkinter import messagebox
from app.models.proveedor_model import ProveedorModel
from app.utils.config import COLORES

class ProveedoresView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.model = ProveedorModel()
        self._build()
        self._cargar()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16,8))
        ctk.CTkLabel(hdr, text="🏭  Proveedores",
                     font=("Segoe UI",20,"bold"),
                     text_color=COLORES["text_primary"]).pack(side="left")
        ctk.CTkButton(hdr, text="➕ Nuevo proveedor", width=160,
                      command=self._form).pack(side="right")

        tabla = ctk.CTkFrame(self, fg_color=COLORES["bg_dark"], corner_radius=12)
        tabla.pack(fill="both", expand=True, padx=20, pady=8)
        tabla.rowconfigure(1, weight=1)
        tabla.columnconfigure(0, weight=1)

        hdr_row = ctk.CTkFrame(tabla, fg_color=COLORES["primary"], corner_radius=6, height=36)
        hdr_row.grid(row=0, column=0, sticky="ew", padx=8, pady=(8,4))
        for txt, w in [("Nombre",200),("Contacto",140),("Teléfono",120),
                       ("RFC",120),("Acciones",100)]:
            ctk.CTkLabel(hdr_row, text=txt, font=("Segoe UI",11,"bold"),
                         text_color="white", width=w).pack(side="left", padx=4)

        self.scroll = ctk.CTkScrollableFrame(tabla, fg_color="transparent")
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)

    def _cargar(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        for i, p in enumerate(self.model.get_all()):
            bg = COLORES["bg_card"] if i % 2 == 0 else "transparent"
            row = ctk.CTkFrame(self.scroll, fg_color=bg, corner_radius=4, height=36)
            row.pack(fill="x", pady=1)
            for v, w in [(p["nombre"][:26],200),(p.get("contacto","") or "—",140),
                         (p.get("telefono","") or "—",120),(p.get("rfc","") or "—",120)]:
                ctk.CTkLabel(row, text=v, font=("Segoe UI",11),
                             text_color=COLORES["text_primary"], width=w, anchor="w").pack(side="left", padx=4)
            ctk.CTkButton(row, text="✏️", width=36, height=28,
                          fg_color=COLORES["primary"],
                          command=lambda x=p: self._form(x)).pack(side="left", padx=2)
            ctk.CTkButton(row, text="🗑", width=36, height=28,
                          fg_color=COLORES["danger"],
                          command=lambda x=p: self._eliminar(x)).pack(side="left", padx=2)

    def _eliminar(self, p):
        if messagebox.askyesno("Eliminar", f"¿Eliminar '{p['nombre']}'?"):
            self.model.eliminar(p["id"])
            self._cargar()

    def _form(self, prov=None):
        win = ctk.CTkToplevel(self)
        win.title("Proveedor")
        win.geometry("420x420")
        win.grab_set()
        campos = [("Nombre *","nombre"),("Contacto","contacto"),
                  ("Teléfono","telefono"),("Email","email"),
                  ("Dirección","direccion"),("RFC","rfc")]
        entries = {}
        scroll = ctk.CTkScrollableFrame(win)
        scroll.pack(fill="both", expand=True, padx=16, pady=10)
        for lbl, key in campos:
            ctk.CTkLabel(scroll, text=lbl, font=("Segoe UI",11),
                         text_color=COLORES["text_secondary"]).pack(anchor="w")
            e = ctk.CTkEntry(scroll, height=34)
            e.pack(fill="x", pady=(0,8))
            if prov and prov.get(key):
                e.insert(0, str(prov[key]))
            entries[key] = e

        def guardar():
            data = {k: e.get().strip() for k, e in entries.items()}
            if not data["nombre"]:
                messagebox.showwarning("Error", "El nombre es obligatorio.")
                return
            if prov:
                self.model.actualizar(prov["id"], data)
            else:
                self.model.crear(data)
            win.destroy()
            self._cargar()

        ctk.CTkButton(win, text="💾  Guardar", height=40,
                      fg_color=COLORES["success"], command=guardar).pack(
                          fill="x", padx=16, pady=8)
