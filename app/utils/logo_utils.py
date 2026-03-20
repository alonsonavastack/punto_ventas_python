"""
logo_utils.py — Utilidades para el logo del negocio.
"""
import os

_BASE     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_LOGO_DIR = os.path.join(_BASE, "assets", "images")


def ruta_logo() -> str | None:
    for ext in ("png", "jpg", "jpeg", "gif"):
        p = os.path.join(_LOGO_DIR, f"logo.{ext}")
        if os.path.exists(p):
            return p
    return None


def eliminar_logos():
    for ext in ("png", "jpg", "jpeg", "gif"):
        p = os.path.join(_LOGO_DIR, f"logo.{ext}")
        if os.path.exists(p):
            try: os.remove(p)
            except Exception: pass


def generar_ascii_logo(*args, **kwargs) -> bool:
    return True


def cargar_logo_widget(parent, size: int = 80) -> bool:
    p = ruta_logo()
    if not p:
        return False
    try:
        from PIL import Image, ImageTk
        img = Image.open(p).convert("RGBA")
        img.thumbnail((size, size), Image.LANCZOS)
        parent._logo_img = ImageTk.PhotoImage(img)
        import tkinter as tk
        tk.Label(parent, image=parent._logo_img, bg="#1a1a2e", bd=0).pack(pady=(12, 2))
        return True
    except Exception as e:
        print(f"⚠ No se pudo cargar logo: {e}")
        return False


def encabezado_ticket(ancho: int = 42) -> list[str]:
    """
    Genera encabezado simple de texto para tickets:
      Nombre del negocio, dirección, teléfono, RFC
    """
    try:
        from app.database.connection import Database
        db  = Database.get_instance()
        cfg = {r["clave"]: r["valor"]
               for r in db.fetch_all("SELECT clave, valor FROM configuracion")}
    except Exception:
        cfg = {}

    nombre    = cfg.get("nombre_negocio") or "Punto de Ventas"
    direccion = cfg.get("direccion") or ""
    telefono  = cfg.get("telefono")  or ""
    rfc       = cfg.get("rfc")       or ""

    W   = ancho
    sep = "=" * W

    lines = [sep, nombre[:W].center(W)]
    if direccion:
        lines.append(direccion[:W].center(W))
    if telefono:
        lines.append(f"Tel: {telefono}".center(W))
    if rfc:
        lines.append(f"RFC: {rfc}".center(W))
    lines.append(sep)
    return lines
