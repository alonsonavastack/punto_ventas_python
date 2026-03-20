"""
utils/window_utils.py
Utilidades para centrar ventanas y aplicar comportamiento estándar.

Uso simple en cualquier CTkToplevel:
    from app.utils.window_utils import centrar, setup_ventana

    class MiVentana(ctk.CTkToplevel):
        def __init__(self):
            super().__init__()
            self.geometry("400x300")
            centrar(self)           # ← centrar después de geometry()
"""

def centrar(win, ancho: int = None, alto: int = None):
    """
    Centra la ventana en la pantalla.
    Llamar DESPUÉS de geometry(). También funciona antes — usa los valores dados.
    """
    win.update_idletasks()

    # Determinar tamaño
    if ancho and alto:
        w, h = ancho, alto
    else:
        w = win.winfo_width()
        h = win.winfo_height()
        if w <= 1 or h <= 1:
            try:
                geo  = win.geometry()
                dims = geo.split("+")[0]
                w, h = map(int, dims.split("x"))
            except Exception:
                w, h = 800, 600

    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x  = max(0, (sw - w) // 2)
    y  = max(0, (sh - h) // 2)

    win.geometry(f"{w}x{h}+{x}+{y}")


# Alias corto
centrar_ventana = centrar
