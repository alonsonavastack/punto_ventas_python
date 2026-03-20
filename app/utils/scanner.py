"""
scanner.py — Escáner de código de barras con cámara
Usa OpenCV para captura de video y pyzbar para decodificación.
Si las librerías no están disponibles, el botón de cámara se deshabilita
silenciosamente sin mostrar ninguna ventana de aviso.
"""
import threading
import customtkinter as ctk
from tkinter import messagebox

# ── Imports opcionales ────────────────────────────────────────────────────────
try:
    import cv2
    OPENCV_OK = True
except ImportError:
    OPENCV_OK = False

try:
    from pyzbar import pyzbar
    PYZBAR_OK = True
except Exception as e:
    PYZBAR_OK = False
    print(f"⚠ No se pudo cargar pyzbar (zbar DLL ausente?): {e}")

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

# True si todas las dependencias están disponibles
ESCANER_DISPONIBLE = OPENCV_OK and PYZBAR_OK and PIL_OK


def abrir_escaner(parent, callback_codigo):
    """
    Abre la ventana del escáner de cámara.
    Si las dependencias no están, muestra un mensaje informativo
    SOLO cuando el usuario presiona el botón, sin bloquear el flujo.
    """
    if not ESCANER_DISPONIBLE:
        _mostrar_aviso_simple(parent)
        return
    _EscanerWindow(parent, callback_codigo)


def crear_boton_escaner(parent, callback_codigo, **kwargs):
    """
    Crea el botón 📷 de escáner listo para usar.
    - Si las dependencias están OK: botón activo que abre la cámara.
    - Si faltan dependencias: botón deshabilitado con tooltip informativo,
      sin mostrar ninguna ventana de aviso al usuario.

    Uso:
        btn = crear_boton_escaner(frame, lambda cod: entry.insert(0, cod))
        btn.grid(row=0, column=1)
    """
    defaults = dict(
        text="📷", width=36, height=34,
        fg_color="#0369a1", hover_color="#0284c7",
        font=("Segoe UI", 15),
    )
    defaults.update(kwargs)

    if ESCANER_DISPONIBLE:
        btn = ctk.CTkButton(
            parent,
            command=lambda: abrir_escaner(parent.winfo_toplevel(), callback_codigo),
            **defaults
        )
    else:
        # Botón deshabilitado visualmente (gris) — no abre ninguna ventana
        defaults["fg_color"]    = "#374151"
        defaults["hover_color"] = "#374151"
        defaults["text_color"]  = "#6b7280"
        defaults["text"]        = "📷"
        btn = ctk.CTkButton(
            parent,
            command=lambda: None,   # no hace nada
            state="disabled",
            **defaults
        )
        # Tooltip simple al pasar el mouse
        _agregar_tooltip(btn, "Escáner no disponible.\nInstala: pip install opencv-python pyzbar")

    return btn


# ── Ventana del escáner ───────────────────────────────────────────────────────
class _EscanerWindow(ctk.CTkToplevel):
    ANCHO   = 540
    ALTO    = 480
    FPS_MS  = 33   # ~30 fps
    VERDE   = (0, 220, 80)
    ROJO    = (60, 60, 220)

    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback   = callback
        self._cap       = None
        self._activo    = True
        self._detectado = False
        self._ultimo_codigo = ""

        self.title("📷 Escáner de Código de Barras")
        self.geometry(f"{self.ANCHO}x{self.ALTO}")
        self.resizable(False, False)
        self.grab_set()
        self.configure(fg_color="#0f172a")
        self.protocol("WM_DELETE_WINDOW", self._cerrar)

        self._build_ui()
        self._iniciar_camara()

    def _build_ui(self):
        hdr = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=0, height=40)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="📷  Apunta la cámara al código de barras",
                     font=("Segoe UI", 12, "bold"),
                     text_color="#94a3b8").pack(side="left", padx=14, pady=8)

        self._canvas = ctk.CTkCanvas(self, width=self.ANCHO, height=360,
                                      bg="#0f172a", highlightthickness=0)
        self._canvas.pack(padx=0, pady=0)

        self._lbl_estado = ctk.CTkLabel(self,
            text="🔍 Buscando código...",
            font=("Segoe UI", 13, "bold"),
            text_color="#64748b",
            fg_color="#1e293b",
            corner_radius=0,
            height=34)
        self._lbl_estado.pack(fill="x")

        bot = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=0, height=48)
        bot.pack(fill="x")
        ctk.CTkButton(bot, text="✕ Cancelar", height=36, width=160,
                      fg_color="#dc2626", hover_color="#b91c1c",
                      font=("Segoe UI", 11, "bold"),
                      command=self._cerrar).pack(side="right", padx=12, pady=6)
        ctk.CTkButton(bot, text="🔄 Reintentar", height=36, width=140,
                      fg_color="#475569", hover_color="#334155",
                      font=("Segoe UI", 11, "bold"),
                      command=self._reiniciar_deteccion).pack(side="right", padx=4, pady=6)

    def _iniciar_camara(self):
        threading.Thread(target=self._abrir_camara_hilo, daemon=True).start()

    def _abrir_camara_hilo(self):
        for idx in range(3):
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                self._cap = cap
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.after(0, self._loop_video)
                return
        self.after(0, lambda: self._lbl_estado.configure(
            text="❌ No se encontró cámara disponible",
            text_color="#ef4444"))

    def _loop_video(self):
        if not self._activo or self._cap is None:
            return

        ret, frame = self._cap.read()
        if not ret:
            self.after(self.FPS_MS, self._loop_video)
            return

        codigos = []
        if not self._detectado:
            codigos = pyzbar.decode(frame)

        for barcode in codigos:
            pts = barcode.polygon
            if len(pts) == 4:
                import numpy as np
                hull = cv2.convexHull(
                    np.array([[p.x, p.y] for p in pts], dtype=np.int32))
                cv2.polylines(frame, [hull], True, self.VERDE, 3)
            x, y, w, h = barcode.rect
            cv2.rectangle(frame, (x, y), (x+w, y+h), self.VERDE, 2)
            texto = barcode.data.decode("utf-8", errors="ignore")
            cv2.putText(frame, texto, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.VERDE, 2)

        cx = frame.shape[1] // 2
        cy = frame.shape[0] // 2
        color_guia = self.VERDE if codigos else (80, 80, 80)
        cv2.line(frame, (cx - 80, cy), (cx + 80, cy), color_guia, 1)
        cv2.line(frame, (cx, cy - 40), (cx, cy + 40), color_guia, 1)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img = img.resize((self.ANCHO, 360), Image.LANCZOS)
        self._foto = ImageTk.PhotoImage(img)
        self._canvas.create_image(0, 0, anchor="nw", image=self._foto)

        if codigos and not self._detectado:
            self._detectado = True
            codigo_str = codigos[0].data.decode("utf-8", errors="ignore").strip()
            self._ultimo_codigo = codigo_str
            self._lbl_estado.configure(
                text=f"✅  Código detectado: {codigo_str}",
                text_color="#22c55e")
            self.after(500, lambda: self._confirmar(codigo_str))

        self.after(self.FPS_MS, self._loop_video)

    def _confirmar(self, codigo):
        self._cerrar()
        self.callback(codigo)

    def _reiniciar_deteccion(self):
        self._detectado = False
        self._ultimo_codigo = ""
        self._lbl_estado.configure(text="🔍 Buscando código...", text_color="#64748b")

    def _cerrar(self):
        self._activo = False
        if self._cap:
            self._cap.release()
        self.destroy()


# ── Aviso simplificado (solo si el usuario presiona el botón) ─────────────────
def _mostrar_aviso_simple(parent):
    """
    Muestra un aviso compacto con la instrucción de instalación.
    Se muestra ÚNICAMENTE cuando el usuario presiona el botón 📷.
    """
    messagebox.showinfo(
        "Escáner no disponible",
        "Para usar el escáner de cámara instala las dependencias:\n\n"
        "  pip install opencv-python pyzbar\n\n"
        "Después reinicia la aplicación.",
        parent=parent
    )


# ── Tooltip simple ────────────────────────────────────────────────────────────
def _agregar_tooltip(widget, texto):
    """Muestra un label flotante al pasar el mouse sobre el widget."""
    import tkinter as tk

    tip = None

    def _mostrar(event):
        nonlocal tip
        if tip:
            return
        x = widget.winfo_rootx() + 20
        y = widget.winfo_rooty() + widget.winfo_height() + 4
        tip = tk.Toplevel(widget)
        tip.wm_overrideredirect(True)
        tip.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(tip, text=texto, justify="left",
                       background="#1e293b", foreground="#94a3b8",
                       relief="flat", font=("Segoe UI", 9),
                       padx=8, pady=4)
        lbl.pack()

    def _ocultar(event):
        nonlocal tip
        if tip:
            tip.destroy()
            tip = None

    widget.bind("<Enter>", _mostrar)
    widget.bind("<Leave>", _ocultar)
