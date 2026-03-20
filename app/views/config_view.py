import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import os
import shutil
from app.database.connection import Database
from app.utils.config import COLORES
from app.utils.logo_utils import ruta_logo, eliminar_logos


def _recargar_sidebar(widget):
    try:
        w = widget
        while w is not None:
            if hasattr(w, "_rebuild"):
                w._rebuild()
                return
            w = getattr(w, "master", None)
    except Exception as e:
        print(f"⚠ No se pudo recargar sidebar: {e}")


class ConfigView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.db = Database.get_instance()
        self._logo_img = None
        self._build()
        self._cargar()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=COLORES["bg_dark"], corner_radius=0, height=52)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="⚙️  Configuración del Negocio",
                     font=("Segoe UI", 16, "bold"),
                     text_color=COLORES["text_primary"]).pack(side="left", padx=20, pady=14)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=10)

        # ── Logo ──────────────────────────────────────────────────────────────
        logo_card = ctk.CTkFrame(scroll, fg_color=COLORES["bg_card"], corner_radius=12)
        logo_card.pack(fill="x", pady=(0, 12))
        lh = ctk.CTkFrame(logo_card, fg_color="#1e3a5f", corner_radius=8, height=36)
        lh.pack(fill="x", padx=2, pady=(2, 0)); lh.pack_propagate(False)
        ctk.CTkLabel(lh, text="🖼️  Logo del negocio",
                     font=("Segoe UI", 12, "bold"), text_color="white"
                     ).pack(side="left", padx=14, pady=6)

        lb = ctk.CTkFrame(logo_card, fg_color="transparent")
        lb.pack(fill="x", padx=16, pady=12)
        lr = ctk.CTkFrame(lb, fg_color="transparent"); lr.pack(fill="x")

        self._preview_box = ctk.CTkFrame(lr, fg_color=COLORES["bg_dark"],
                                          corner_radius=10, width=110, height=110)
        self._preview_box.pack(side="left", padx=(0, 16))
        self._preview_box.pack_propagate(False)
        self._lbl_preview = ctk.CTkLabel(self._preview_box, text="🛒", font=("Segoe UI", 40))
        self._lbl_preview.pack(expand=True)

        ctrl = ctk.CTkFrame(lr, fg_color="transparent")
        ctrl.pack(side="left", fill="x", expand=True)
        self._lbl_ruta = ctk.CTkLabel(ctrl,
            text="Sin logo personalizado — se muestra 🛒",
            font=("Segoe UI", 11), text_color=COLORES["text_secondary"],
            wraplength=420, justify="left")
        self._lbl_ruta.pack(anchor="w", pady=(0, 8))

        br = ctk.CTkFrame(ctrl, fg_color="transparent"); br.pack(anchor="w")
        ctk.CTkButton(br, text="📂 Elegir imagen",
                      height=36, width=150, fg_color=COLORES["primary"],
                      font=("Segoe UI", 11, "bold"),
                      command=self._elegir_logo).pack(side="left", padx=(0, 8))
        ctk.CTkButton(br, text="🗑 Quitar logo",
                      height=36, width=120, fg_color=COLORES["danger"],
                      font=("Segoe UI", 11, "bold"),
                      command=self._quitar_logo).pack(side="left")

        ctk.CTkLabel(ctrl,
            text="PNG, JPG, GIF  •  Recomendado: 200×200 px  •  Aparece en el menú lateral",
            font=("Segoe UI", 9), text_color="#475569").pack(anchor="w", pady=(6, 0))

        ctk.CTkFrame(scroll, height=1, fg_color=COLORES["border"]).pack(fill="x", pady=4)

        # ── Datos del negocio ─────────────────────────────────────────────────
        dc = ctk.CTkFrame(scroll, fg_color=COLORES["bg_card"], corner_radius=12)
        dc.pack(fill="x", pady=(0, 12))
        dh = ctk.CTkFrame(dc, fg_color="#065f46", corner_radius=8, height=36)
        dh.pack(fill="x", padx=2, pady=(2, 0)); dh.pack_propagate(False)
        ctk.CTkLabel(dh, text="🏪  Datos del negocio",
                     font=("Segoe UI", 12, "bold"), text_color="white"
                     ).pack(side="left", padx=14, pady=6)

        db_body = ctk.CTkFrame(dc, fg_color="transparent")
        db_body.pack(fill="x", padx=16, pady=12)

        self.entries = {}
        self._campos_config = [
            ("nombre_negocio", "Nombre del negocio *"),
            ("direccion",      "Dirección"),
            ("telefono",       "Teléfono"),
            ("rfc",            "RFC"),
            ("iva_porcentaje", "IVA (%)"),
            ("moneda",         "Moneda (MXN, USD...)"),
        ]
        col_izq = ctk.CTkFrame(db_body, fg_color="transparent")
        col_der = ctk.CTkFrame(db_body, fg_color="transparent")
        col_izq.pack(side="left", fill="x", expand=True, padx=(0, 8))
        col_der.pack(side="left", fill="x", expand=True)
        for i, (key, lbl) in enumerate(self._campos_config):
            col = col_izq if i % 2 == 0 else col_der
            ctk.CTkLabel(col, text=lbl, font=("Segoe UI", 11),
                         text_color=COLORES["text_secondary"]).pack(anchor="w", pady=(10, 2))
            e = ctk.CTkEntry(col, height=36, font=("Segoe UI", 12))
            e.pack(fill="x"); self.entries[key] = e

        ctk.CTkButton(self, text="💾  Guardar cambios", height=44,
                      font=("Segoe UI", 13, "bold"), fg_color=COLORES["success"],
                      command=self._guardar).pack(fill="x", padx=20, pady=(4, 12))

        self._actualizar_preview()

    # ── Logo ──────────────────────────────────────────────────────────────────
    def _elegir_logo(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar logo",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.gif"), ("All", "*.*")])
        if not ruta: return
        try:
            from app.utils.logo_utils import _LOGO_DIR
            os.makedirs(_LOGO_DIR, exist_ok=True)
            eliminar_logos()
            ext     = os.path.splitext(ruta)[1].lower()
            destino = os.path.join(_LOGO_DIR, f"logo{ext}")
            shutil.copy2(ruta, destino)
            if not os.path.exists(destino):
                raise FileNotFoundError(f"No se copió: {destino}")
            self._actualizar_preview()
            self.after(150, lambda: _recargar_sidebar(self))
        except Exception as e:
            messagebox.showerror("Error al guardar logo", str(e))

    def _quitar_logo(self):
        if not ruta_logo():
            messagebox.showinfo("Sin logo", "No hay logo personalizado."); return
        if messagebox.askyesno("Quitar logo", "¿Eliminar el logo?\nSe volverá al ícono 🛒."):
            eliminar_logos()
            self._actualizar_preview()
            self.after(150, lambda: _recargar_sidebar(self))

    def _actualizar_preview(self):
        for w in self._preview_box.winfo_children(): w.destroy()
        p = ruta_logo()
        if p:
            try:
                from PIL import Image
                img = Image.open(p).convert("RGBA")
                img.thumbnail((90, 90), Image.LANCZOS)
                self._logo_img = ctk.CTkImage(light_image=img, dark_image=img, size=(90, 90))
                ctk.CTkLabel(self._preview_box, image=self._logo_img, text="").pack(expand=True)
                nombre  = os.path.basename(p)
                size_kb = os.path.getsize(p) / 1024
                self._lbl_ruta.configure(
                    text=f"✅  {nombre}  ({size_kb:.1f} KB)\n📂 {p}",
                    text_color=COLORES["success"])
                return
            except Exception as e:
                print(f"⚠ preview error: {e}")
        ctk.CTkLabel(self._preview_box, text="🛒", font=("Segoe UI", 40)).pack(expand=True)
        self._logo_img = None
        self._lbl_ruta.configure(
            text="Sin logo personalizado — se muestra 🛒",
            text_color=COLORES["text_secondary"])

    # ── Datos ─────────────────────────────────────────────────────────────────
    def _cargar(self):
        rows  = self.db.fetch_all("SELECT clave, valor FROM configuracion")
        datos = {r["clave"]: r["valor"] for r in rows}
        for key, _ in self._campos_config:
            if key in datos:
                self.entries[key].delete(0, "end")
                self.entries[key].insert(0, datos[key] or "")

    def _guardar(self):
        for key, _ in self._campos_config:
            val = self.entries[key].get().strip()
            self.db.execute_query(
                "INSERT INTO configuracion (clave, valor) VALUES (%s, %s) "
                "ON DUPLICATE KEY UPDATE valor=%s", (key, val, val))
        messagebox.showinfo("✅ Guardado", "Configuración guardada correctamente.")
