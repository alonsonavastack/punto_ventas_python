"""
scroll_fix.py  v2.0 — Scroll con trackpad en Mac/Win/Linux para CustomTkinter.

SOLUCIÓN MAC:
  El trackpad de Mac genera eventos <MouseWheel> con delta muy pequeño
  (típicamente ±1 a ±5 por cada gesto). La clave es:
  1. Parchear CTkScrollableFrame para enlazar scroll en su canvas Y en todos sus hijos
  2. Usar bind_all con Enter/Leave para activar/desactivar globalmente
  3. Dividir el delta entre un número pequeño (3-5) para que sea fluido

Llamar UNA sola vez ANTES de crear cualquier widget:
    from app.utils.scroll_fix import aplicar_scroll_global
    aplicar_scroll_global()
"""

import platform
import customtkinter as ctk

_SISTEMA  = platform.system()   # "Darwin" | "Linux" | "Windows"
_aplicado = False

# Rastreo de qué canvas está activo en este momento
_canvas_activo  = None
_bindings_root  = {}   # root -> lista de ids de binding


def _scroll_y(canvas, delta):
    """Desplaza verticalmente el canvas."""
    try:
        canvas.yview_scroll(int(delta), "units")
    except Exception:
        pass


def _scroll_x(canvas, delta):
    """Desplaza horizontalmente el canvas."""
    try:
        canvas.xview_scroll(int(delta), "units")
    except Exception:
        pass


# ── Mac ───────────────────────────────────────────────────────────────────────
def _activar_mac(canvas):
    global _canvas_activo
    _canvas_activo = canvas

    root = canvas.winfo_toplevel()

    def _on_wheel(event):
        if _canvas_activo is None:
            return
        # Shift + scroll = horizontal
        if event.state & 0x0001:
            _scroll_x(_canvas_activo, -event.delta // 4)
        else:
            _scroll_y(_canvas_activo, -event.delta // 4)

    # Limpiar bindings anteriores de esta raíz
    _limpiar_bindings_root(root)

    b1 = root.bind("<MouseWheel>", _on_wheel, add="+")
    b2 = root.bind("<Shift-MouseWheel>",
                   lambda e: _scroll_x(_canvas_activo, -e.delta // 4), add="+")
    _bindings_root[id(root)] = (root, [b1, b2])


def _desactivar_mac(canvas):
    global _canvas_activo
    if _canvas_activo is canvas:
        _canvas_activo = None


def _limpiar_bindings_root(root):
    key = id(root)
    if key in _bindings_root:
        _, ids = _bindings_root.pop(key)
        for bid in ids:
            try:
                root.unbind("<MouseWheel>", bid)
            except Exception:
                pass
            try:
                root.unbind("<Shift-MouseWheel>", bid)
            except Exception:
                pass


def _bind_widget_mac(widget, canvas):
    """Enlaza Enter/Leave en cada widget hijo para activar el scroll correcto."""
    try:
        widget.bind("<Enter>", lambda e: _activar_mac(canvas), add="+")
        widget.bind("<Leave>", lambda e: _desactivar_mac(canvas), add="+")
    except Exception:
        pass
    try:
        for child in widget.winfo_children():
            _bind_widget_mac(child, canvas)
    except Exception:
        pass


# ── Linux ─────────────────────────────────────────────────────────────────────
def _bind_linux(canvas):
    def _up(e):   _scroll_y(canvas, -2)
    def _dn(e):   _scroll_y(canvas,  2)
    def _lt(e):   _scroll_x(canvas, -2)
    def _rt(e):   _scroll_x(canvas,  2)

    canvas.bind("<Button-4>",       _up, add="+")
    canvas.bind("<Button-5>",       _dn, add="+")
    canvas.bind("<Shift-Button-4>", _lt, add="+")
    canvas.bind("<Shift-Button-5>", _rt, add="+")

    canvas.bind("<Enter>", lambda e: _activar_linux(canvas, _up, _dn, _lt, _rt))
    canvas.bind("<Leave>", lambda e: _desactivar_linux(canvas))


def _activar_linux(canvas, up, dn, lt, rt):
    try:
        root = canvas.winfo_toplevel()
        root.bind_all("<Button-4>",       up, add="+")
        root.bind_all("<Button-5>",       dn, add="+")
        root.bind_all("<Shift-Button-4>", lt, add="+")
        root.bind_all("<Shift-Button-5>", rt, add="+")
    except Exception:
        pass


def _desactivar_linux(canvas):
    try:
        root = canvas.winfo_toplevel()
        for ev in ("<Button-4>", "<Button-5>",
                   "<Shift-Button-4>", "<Shift-Button-5>"):
            root.unbind_all(ev)
    except Exception:
        pass


# ── Windows ───────────────────────────────────────────────────────────────────
def _bind_windows(canvas):
    def _on_scroll(event):
        if event.state & 0x0001:
            _scroll_x(canvas, int(-event.delta / 120))
        else:
            _scroll_y(canvas, int(-event.delta / 120))

    canvas.bind("<MouseWheel>",       _on_scroll, add="+")
    canvas.bind("<Shift-MouseWheel>", _on_scroll, add="+")
    canvas.bind("<Enter>", lambda e: _activar_windows(canvas, _on_scroll))
    canvas.bind("<Leave>", lambda e: _desactivar_windows(canvas))


def _activar_windows(canvas, fn):
    try:
        root = canvas.winfo_toplevel()
        root.bind_all("<MouseWheel>", fn, add="+")
    except Exception:
        pass


def _desactivar_windows(canvas):
    try:
        root = canvas.winfo_toplevel()
        root.unbind_all("<MouseWheel>")
    except Exception:
        pass


# ── Parche central ────────────────────────────────────────────────────────────
def _setup_scroll_en_frame(sf):
    """Configura scroll en un CTkScrollableFrame ya construido."""
    try:
        canvas = sf._parent_canvas
    except AttributeError:
        return

    if _SISTEMA == "Darwin":
        # Enlazar el canvas directamente
        canvas.bind("<Enter>", lambda e: _activar_mac(canvas), add="+")
        canvas.bind("<Leave>", lambda e: _desactivar_mac(canvas), add="+")
        # Enlazar todos los hijos actuales
        _bind_widget_mac(sf, canvas)

        # Observar nuevos hijos que se agreguen al frame
        _instalar_observer_hijos(sf, canvas)

    elif _SISTEMA == "Linux":
        _bind_linux(canvas)

    else:
        _bind_windows(canvas)


def _instalar_observer_hijos(sf, canvas):
    """
    En Mac: cuando se agrega un nuevo hijo al scrollable frame,
    también enlazarle Enter/Leave para activar el scroll.
    """
    orig_pack   = getattr(sf, "_orig_pack",   None)
    orig_grid   = getattr(sf, "_orig_grid",   None)
    orig_place  = getattr(sf, "_orig_place",  None)

    # Usamos after_idle para capturar widgets recién empaquetados
    def _check_nuevos_hijos():
        try:
            _bind_widget_mac(sf, canvas)
        except Exception:
            pass
        sf.after(300, _check_nuevos_hijos)

    sf.after(300, _check_nuevos_hijos)


# ── API pública ───────────────────────────────────────────────────────────────
def aplicar_scroll_global():
    """
    Llama esto UNA vez al inicio del programa, ANTES de crear cualquier widget.
    Parchea CTkScrollableFrame.__init__ para que cada instancia registre
    automáticamente el scroll correcto según el sistema operativo.
    """
    global _aplicado
    if _aplicado:
        return
    _aplicado = True

    _orig_init = ctk.CTkScrollableFrame.__init__

    def _nuevo_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        # Esperar a que el canvas esté completamente construido
        self.after(50, lambda: _setup_scroll_en_frame(self))

    ctk.CTkScrollableFrame.__init__ = _nuevo_init


# ── Función auxiliar para enlazar scroll a un frame específico (uso manual) ──
def bind_scroll(frame: ctk.CTkScrollableFrame):
    """
    Llama esto si necesitas forzar el scroll en un frame específico
    que ya fue creado antes de aplicar_scroll_global().
    """
    _setup_scroll_en_frame(frame)
