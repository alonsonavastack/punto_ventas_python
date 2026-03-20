"""
caja_view.py - Banco de México MXN completo
Flujo: desglose billetes/monedas → vista previa corte → imprimir → cerrar caja
"""
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from app.models.caja_model import CajaModel
from app.utils import session
from app.utils.config import COLORES, APP_NOMBRE, APP_VERSION
from app.utils.logo_utils import encabezado_ticket
from app.utils.window_utils import centrar
import tkinter as tk
import platform
import tempfile
import os

_ES_MAC = platform.system() == "Darwin"
_ES_WIN = platform.system() == "Windows"

DENOMINACIONES = [
    (1000,'b'),(500,'b'),(200,'b'),(100,'b'),(50,'b'),(20,'b'),
    (20,'m'),(10,'m'),(5,'m'),(2,'m'),(1,'m'),
    (0.50,'m'),(0.20,'m'),(0.10,'m'),
]
DEN_INFO = {
    (1000,'b'): ("$1,000 billete","🟣","#c084fc"),
    ( 500,'b'): ("$500   billete","🔵","#60a5fa"),
    ( 200,'b'): ("$200   billete","🟤","#fb923c"),
    ( 100,'b'): ("$100   billete","🟢","#4ade80"),
    (  50,'b'): ("$50    billete","🟠","#fbbf24"),
    (  20,'b'): ("$20    billete","🔴","#f87171"),
    (  20,'m'): ("$20    moneda", "🪙","#e5c44a"),
    (  10,'m'): ("$10    moneda", "🪙","#e5e5e5"),
    (   5,'m'): ("$5     moneda", "🪙","#d4d4d4"),
    (   2,'m'): ("$2     moneda", "🪙","#d4d4d4"),
    (   1,'m'): ("$1     moneda", "🪙","#d4d4d4"),
    (0.50,'m'): ("50¢    moneda", "🪙","#a3a3a3"),
    (0.20,'m'): ("20¢    moneda", "🪙","#a3a3a3"),
    (0.10,'m'): ("10¢    moneda", "🪙","#737373"),
}

def _sugerir_conteo(monto_total):
    orden = sorted(DENOMINACIONES, key=lambda x: -x[0])
    restante = round(monto_total, 2)
    sugerido = {}
    for key in orden:
        den = key[0]
        if restante <= 0.009: break
        cantidad = int(restante // den)
        if cantidad > 0:
            sugerido[key] = cantidad
            restante = round(restante - cantidad * den, 2)
    return sugerido


# ─────────────────────────────────────────────────────────────────────────────
class AperturaCajaView(ctk.CTkToplevel):
    def __init__(self, parent, on_success):
        super().__init__(parent)
        self.on_success = on_success
        self.model = CajaModel()
        self.title("Apertura de Caja")
        self.geometry("420x400")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._salir)
        self._build()
        centrar(self, 420, 400)
        self.lift(); self.focus_force(); self.grab_set()

    def _salir(self):
        if messagebox.askyesno(
            "Salir",
            "¿Salir de la aplicación?\n\nSin abrir la caja no podrá registrar ventas.",
            parent=self
        ):
            try:
                self.grab_release()
            except Exception:
                pass
            import sys
            sys.exit(0)

    def _build(self):
        self.configure(fg_color=COLORES["bg_dark"])
        hdr = ctk.CTkFrame(self, fg_color=COLORES["success"], corner_radius=0, height=52)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="💰  Apertura de Caja",
                     font=("Segoe UI",16,"bold"), text_color="white").pack(side="left", padx=16, pady=12)
        ctk.CTkLabel(self, text="💰", font=("Segoe UI",44)).pack(pady=(20,2))
        usuario = session.get_usuario()
        ctk.CTkLabel(self, text=f"Cajero: {usuario['nombre']}",
                     font=("Segoe UI",13,"bold"), text_color=COLORES["text_primary"]).pack()
        ctk.CTkLabel(self, text=datetime.now().strftime("%A %d de %B %Y  %H:%M"),
                     font=("Segoe UI",11), text_color=COLORES["text_secondary"]).pack(pady=(2,16))
        frame = ctk.CTkFrame(self, fg_color=COLORES["bg_card"], corner_radius=14)
        frame.pack(fill="x", padx=30)
        ctk.CTkLabel(frame, text="Fondo inicial en caja ($)",
                     font=("Segoe UI",13), text_color=COLORES["text_secondary"]
                     ).pack(anchor="w", padx=20, pady=(20,4))
        self.entry_fondo = ctk.CTkEntry(frame, placeholder_text="0.00",
                                        height=44, font=("Segoe UI",18,"bold"), justify="center")
        self.entry_fondo.pack(fill="x", padx=20)
        self.entry_fondo.insert(0, "0.00")
        self.entry_fondo.bind("<Return>", lambda e: self._abrir())
        ctk.CTkButton(frame, text="✅  Abrir Caja", height=46,
                      font=("Segoe UI",14,"bold"),
                      fg_color=COLORES["success"], hover_color="#15803D",
                      command=self._abrir).pack(fill="x", padx=20, pady=(16,20))
        self.after(150, lambda: [self.entry_fondo.focus(), self.entry_fondo.select_range(0,"end")])

    def _abrir(self):
        try: fondo = float(self.entry_fondo.get())
        except ValueError: messagebox.showwarning("Error","Ingresa un monto válido"); return
        usuario = session.get_usuario()
        try: self.grab_release()
        except Exception: pass
        self.destroy()
        self.on_success(self.model.abrir(fondo, usuario["id"]))


# ─────────────────────────────────────────────────────────────────────────────
class CierreCajaView(ctk.CTkToplevel):
    def __init__(self, parent, on_success=None):
        super().__init__(parent)
        self.on_success = on_success
        self.model      = CajaModel()
        self.title("Cierre de Caja")

        self.update_idletasks()
        sh    = self.winfo_screenheight()
        alto  = min(760, sh - 60)
        ancho = 720
        self.geometry(f"{ancho}x{alto}")
        self.minsize(660, min(580, alto))
        self.resizable(True, True)

        self.protocol("WM_DELETE_WINDOW", self._cerrar_ventana)
        self._vars    = {}
        self._lbl_sub = {}
        self._sesion  = None
        self._resumen = None
        self._esperado = 0.0
        self._build()

        centrar(self, ancho, alto)
        self.lift(); self.focus_force(); self.grab_set()

    def _cerrar_ventana(self):
        try: self.grab_release()
        except Exception: pass
        self.destroy()

    def _build(self):
        self.configure(fg_color=COLORES["bg_dark"])
        hdr = ctk.CTkFrame(self, fg_color=COLORES["danger"], corner_radius=0, height=52)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="🔒  Cierre de Caja — Desglose de efectivo",
                     font=("Segoe UI",15,"bold"), text_color="white").pack(side="left", padx=16, pady=12)

        sesion = session.get_sesion_caja() or self.model.get_sesion_activa()
        if not sesion:
            ctk.CTkLabel(self, text="No hay caja abierta.",
                         font=("Segoe UI",14), text_color=COLORES["danger"]).pack(pady=40)
            return

        self._sesion  = sesion
        resumen       = self.model.get_resumen_sesion(sesion["id"])
        self._resumen = resumen
        ef = float(resumen.get("total_efectivo",0) or 0)
        fi = float(sesion.get("fondo_inicial",  0) or 0)
        en = float(resumen.get("entradas_extra",0) or 0)
        sa = float(resumen.get("salidas_extra", 0) or 0)
        self._esperado = round(fi + ef + en - sa, 2)

        # ── Resumen de totales ────────────────────────────────────────────
        info = ctk.CTkFrame(self, fg_color=COLORES["bg_card"], corner_radius=10)
        info.pack(fill="x", padx=14, pady=(10,2))
        for lbl, val, color in [
            ("Fondo inicial",    f"${fi:.2f}",             COLORES["text_secondary"]),
            ("Ventas efectivo",  f"${ef:.2f}",             COLORES["success"]),
            ("Entradas extra",   f"+${en:.2f}",            COLORES["success"]),
            ("Salidas extra",    f"-${sa:.2f}",            COLORES["danger"]),
            ("ESPERADO EN CAJA", f"${self._esperado:.2f}", "#fbbf24"),
        ]:
            r = ctk.CTkFrame(info, fg_color="transparent")
            r.pack(fill="x", padx=14, pady=2)
            ctk.CTkLabel(r, text=lbl, font=("Segoe UI",11),
                         text_color=COLORES["text_secondary"]).pack(side="left")
            ctk.CTkLabel(r, text=val, font=("Segoe UI",11,"bold"),
                         text_color=color).pack(side="right")

        # ── Barra instrucciones + botón autocompletar ─────────────────────
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=14, pady=(6,2))
        ctk.CTkLabel(bar, text="Ingresa cuántas piezas hay de cada denominación:",
                     font=("Segoe UI",11), text_color=COLORES["text_secondary"]).pack(side="left")
        ctk.CTkButton(bar, text="⚡ Autocompletar", height=28, width=160,
                      font=("Segoe UI",10,"bold"), fg_color=COLORES["primary"],
                      command=self._autocompletar).pack(side="right")

        # ── Cabecera de columnas ──────────────────────────────────────────
        col_hdr = ctk.CTkFrame(self, fg_color=COLORES["bg_card"], corner_radius=6, height=28)
        col_hdr.pack(fill="x", padx=14, pady=(4,0))
        for txt, w in [("  Denominación",200),("Tipo",80),("Piezas",90),("Subtotal",150)]:
            ctk.CTkLabel(col_hdr, text=txt, font=("Segoe UI",10,"bold"),
                         text_color=COLORES["text_secondary"],
                         width=w, anchor="w").pack(side="left", padx=6, pady=3)

        # ── Tabla scrollable de denominaciones (expand=True) ──────────────
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=14, pady=2)

        b_hdr = ctk.CTkFrame(scroll, fg_color="#1c1008", corner_radius=6, height=28)
        b_hdr.pack(fill="x", pady=(4,3))
        ctk.CTkLabel(b_hdr, text="  💵  BILLETES",
                     font=("Segoe UI",10,"bold"), text_color="#fbbf24").pack(side="left", padx=8, pady=3)
        for den in [1000,500,200,100,50,20]:
            self._fila(scroll, (den,'b'))

        ctk.CTkFrame(scroll, height=2, fg_color=COLORES["border"]).pack(fill="x", pady=6)

        m_hdr = ctk.CTkFrame(scroll, fg_color="#08101c", corner_radius=6, height=28)
        m_hdr.pack(fill="x", pady=(0,3))
        ctk.CTkLabel(m_hdr, text="  🪙  MONEDAS",
                     font=("Segoe UI",10,"bold"), text_color="#60a5fa").pack(side="left", padx=8, pady=3)
        for den in [20,10,5,2,1,0.50,0.20,0.10]:
            self._fila(scroll, (den,'m'))

        # ── Total contado + diferencia ────────────────────────────────────
        tot = ctk.CTkFrame(self, fg_color=COLORES["bg_card"], corner_radius=8)
        tot.pack(fill="x", padx=14, pady=(4,2))
        lt = ctk.CTkFrame(tot, fg_color="transparent")
        lt.pack(side="left", padx=14, pady=8)
        ctk.CTkLabel(lt, text="💰 Total contado:", font=("Segoe UI",13,"bold"),
                     text_color=COLORES["text_primary"]).pack(side="left")
        self._lbl_contado = ctk.CTkLabel(lt, text="$0.00", font=("Segoe UI",18,"bold"),
                                          text_color=COLORES["success"])
        self._lbl_contado.pack(side="left", padx=10)
        self._lbl_dif = ctk.CTkLabel(tot, text="", font=("Segoe UI",12,"bold"),
                                      text_color=COLORES["warning"])
        self._lbl_dif.pack(side="right", padx=14)

        # ── Notas ─────────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Notas del cierre (opcional):",
                     font=("Segoe UI",11), text_color=COLORES["text_secondary"]
                     ).pack(anchor="w", padx=14, pady=(2,0))
        self.entry_notas = ctk.CTkEntry(self, height=34, font=("Segoe UI",12),
                                        placeholder_text="Ej: Sin novedades")
        self.entry_notas.pack(fill="x", padx=14, pady=(2,0))

        # ── Botones de acción (fila con dos botones) ──────────────────────
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=(6,10))

        ctk.CTkButton(btn_row,
                      text="📋  Ver Corte e Imprimir",
                      height=46, font=("Segoe UI",13,"bold"),
                      fg_color=COLORES["danger"], hover_color="#B91C1C",
                      command=self._ir_a_corte
                      ).pack(side="left", fill="x", expand=True, padx=(0,5))

        ctk.CTkButton(btn_row,
                      text="✅  Cerrar sin imprimir",
                      height=46, font=("Segoe UI",13,"bold"),
                      fg_color="#374151", hover_color="#1f2937",
                      command=self._cerrar_sin_imprimir
                      ).pack(side="left", fill="x", expand=True)

    # ── Helpers de denominaciones ──────────────────────────────────────────
    def _fila(self, parent, key):
        den=key[0]; tipo=key[1]
        etq, emoji, color = DEN_INFO.get(key,(str(den),"💲","#fff"))
        es_billete = (tipo=='b')
        bg = COLORES["bg_card"] if es_billete else "transparent"
        row = ctk.CTkFrame(parent, fg_color=bg, corner_radius=6, height=40)
        row.pack(fill="x", pady=2, padx=2)
        ctk.CTkLabel(row, text=emoji, font=("Segoe UI",20), width=30).pack(side="left", padx=(8,2))
        ctk.CTkLabel(row, text=etq, font=("Segoe UI",13,"bold"),
                     text_color=color, width=160, anchor="w").pack(side="left", padx=(2,4))
        ctk.CTkLabel(row, text="billete" if es_billete else "moneda",
                     font=("Segoe UI",10), text_color=COLORES["text_secondary"],
                     width=58, anchor="w").pack(side="left", padx=2)
        var = ctk.StringVar(value="0")
        ctk.CTkEntry(row, textvariable=var, width=76, height=30,
                     justify="center", font=("Segoe UI",13,"bold")).pack(side="left", padx=8)
        lbl = ctk.CTkLabel(row, text="$0.00", font=("Segoe UI",12,"bold"),
                           text_color=color, width=140, anchor="e")
        lbl.pack(side="left", padx=6)
        def _upd(*_):
            try: cant=float(var.get() or 0)
            except (ValueError, TypeError): cant=0
            sub=round(cant*den,2)
            lbl.configure(text=f"${sub:,.2f}" if sub>0 else "$0.00")
            self._recalcular()
        var.trace_add("write", _upd)
        self._vars[key]=var; self._lbl_sub[key]=lbl

    def _autocompletar(self):
        s = _sugerir_conteo(self._esperado)
        for k, v in self._vars.items(): v.set(str(s.get(k,0)))

    def _recalcular(self):
        total=0.0
        for k,v in self._vars.items():
            try: cant=float(v.get() or 0)
            except (ValueError, TypeError): cant=0
            total += cant*k[0]
        total=round(total,2)
        self._lbl_contado.configure(text=f"${total:,.2f}")
        dif=round(total-self._esperado,2)
        if abs(dif)<0.01:
            self._lbl_dif.configure(text="✅ Cuadra exacto", text_color=COLORES["success"])
        elif dif>0:
            self._lbl_dif.configure(text=f"▲ Sobrante  ${dif:,.2f}", text_color=COLORES["warning"])
        else:
            self._lbl_dif.configure(text=f"▼ Faltante  ${abs(dif):,.2f}", text_color=COLORES["danger"])

    # ── Acciones principales ───────────────────────────────────────────────
    def _ir_a_corte(self):
        desglose={}; total_contado=0.0
        for k,v in self._vars.items():
            try: cant=int(float(v.get() or 0))
            except (ValueError, TypeError): cant=0
            if cant>0:
                desglose[k]=cant
                total_contado+=cant*k[0]
        total_contado=round(total_contado,2)
        notas=self.entry_notas.get().strip()
        contenido=self._generar_ticket(desglose,total_contado,notas)

        prev=ctk.CTkToplevel(self)
        prev.title("🧾 Vista Previa — Corte de Caja")
        prev.update_idletasks()
        sh = prev.winfo_screenheight()
        prev_h = min(720, sh - 60)
        prev_w = 540
        prev.geometry(f"{prev_w}x{prev_h}")
        prev.configure(fg_color=COLORES["bg_dark"])
        prev.protocol("WM_DELETE_WINDOW", lambda:[prev.grab_release(),prev.destroy()])

        hdr=ctk.CTkFrame(prev,fg_color=COLORES["primary"],corner_radius=0,height=44)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr,text="CORTE DE CAJA",font=("Segoe UI",13,"bold"),text_color="white").pack(side="left",padx=16,pady=10)

        papel=ctk.CTkFrame(prev,fg_color="white",corner_radius=8)
        papel.pack(fill="both",expand=True,padx=14,pady=10)
        sb=tk.Scrollbar(papel,orient="vertical"); sb.pack(side="right",fill="y")
        txt=tk.Text(papel,font=("Courier New",10),bg="white",fg="black",
                    relief="flat",padx=8,pady=8,wrap="none",yscrollcommand=sb.set)
        sb.configure(command=txt.yview); txt.pack(fill="both",expand=True)
        txt.insert("1.0",contenido); txt.configure(state="disabled")

        br=ctk.CTkFrame(prev,fg_color="transparent"); br.pack(fill="x",padx=14,pady=(0,12))
        def _conf(): prev.grab_release(); prev.destroy(); self._imprimir_y_cerrar(contenido,notas)
        ctk.CTkButton(br,text="🖨  Imprimir y Cerrar Caja",height=44,
                      font=("Segoe UI",13,"bold"),fg_color=COLORES["danger"],
                      command=_conf).pack(side="left",fill="x",expand=True,padx=(0,6))
        ctk.CTkButton(br,text="←  Regresar",height=44,font=("Segoe UI",12),
                      fg_color=COLORES["secondary"],
                      command=lambda:[prev.grab_release(),prev.destroy()]
                      ).pack(side="left",fill="x",expand=True)

        centrar(prev, prev_w, prev_h)
        prev.lift(); prev.focus_force(); prev.grab_set()

    def _cerrar_sin_imprimir(self):
        """Cierra la caja directamente sin pasar por la vista previa ni imprimir."""
        notas = self.entry_notas.get().strip()
        if not messagebox.askyesno(
            "Cerrar caja sin imprimir",
            "¿Cerrar la caja sin generar el corte impreso?\n\n"
            "La caja quedará registrada como cerrada en el sistema.",
            parent=self
        ):
            return
        sesion  = self._sesion
        usuario = session.get_usuario()
        ahora   = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        try:
            self.model.registrar_movimiento(
                sesion["id"], "salida", 0.0,
                f"Cierre sin impresión — {ahora} — {usuario['nombre'] if usuario else '—'}",
                usuario["id"] if usuario else None)
        except Exception:
            pass
        self.model.cerrar(sesion["id"], notas)
        messagebox.showinfo("✅ Caja cerrada", "La caja quedó cerrada correctamente.")
        try: self.grab_release()
        except Exception: pass
        self.destroy()
        if self.on_success: self.on_success()

    # ── Generación del ticket ──────────────────────────────────────────────
    def _generar_ticket(self, desglose, total_contado, notas):
        sesion=self._sesion; resumen=self._resumen
        usuario=session.get_usuario(); ahora=datetime.now()
        ef=float(resumen.get("total_efectivo",0) or 0)
        tj=float(resumen.get("total_tarjeta",0) or 0)
        tr_=float(resumen.get("total_transferencia",0) or 0)
        fi=float(sesion.get("fondo_inicial",0) or 0)
        en=float(resumen.get("entradas_extra",0) or 0)
        sa=float(resumen.get("salidas_extra",0) or 0)
        nv=int(resumen.get("total_ventas",0) or 0)
        esperado=self._esperado; diferencia=round(total_contado-esperado,2)
        DIAS=["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
        MESES=["enero","febrero","marzo","abril","mayo","junio","julio","agosto",
               "septiembre","octubre","noviembre","diciembre"]
        dia_str=f"{DIAS[ahora.weekday()]} {ahora.day} de {MESES[ahora.month-1]} de {ahora.year}"
        W=46; lin="-"*W
        def lr(l,r): return f"{l:<28}{r:>18}"
        L=encabezado_ticket(W)
        L+=["*** CORTE DE CAJA ***".center(W),"="*W,
            f"Fecha    : {dia_str}",f"Hora     : {ahora.strftime('%H:%M:%S')}",
            f"Cajero   : {usuario['nombre'] if usuario else '—'}",
            f"Apertura : {str(sesion.get('fecha_apertura',''))[:16]}",
            lin,"RESUMEN DE VENTAS".center(W),lin,
            lr("Número de ventas",str(nv)),lr("Efectivo",f"${ef:,.2f}"),
            lr("Tarjeta",f"${tj:,.2f}"),lr("Transferencia",f"${tr_:,.2f}"),
            lr("Total vendido",f"${ef+tj+tr_:,.2f}"),
            lin,"EFECTIVO EN CAJA".center(W),lin,
            lr("Fondo inicial",f"${fi:,.2f}"),lr("+ Ventas efectivo",f"${ef:,.2f}")]
        if en>0: L.append(lr("+ Entradas extra",f"${en:,.2f}"))
        if sa>0: L.append(lr("- Salidas extra",f"${sa:,.2f}"))
        L+=[lin,lr("ESPERADO EN CAJA",f"${esperado:,.2f}"),"="*W,
            "DESGLOSE CONTADO".center(W),lin,
            f"  {'Denominación':<18}{'Tipo':<8}{'Piezas':>6}{'Subtotal':>12}",lin]
        bil_tot=0.0; L.append("  -- BILLETES --")
        for den in [1000,500,200,100,50,20]:
            k=(den,'b'); cant=desglose.get(k,0); sub=round(cant*den,2); bil_tot+=sub
            etq=f"${den:,}" if den>=1 else f"${den:.2f}"
            L.append(f"  {etq:<18}{'billete':<8}{cant:>6}  ${sub:>10,.2f}")
        mon_tot=0.0; L.append(lin+"\n  -- MONEDAS --")
        for den in [20,10,5,2,1,0.50,0.20,0.10]:
            k=(den,'m'); cant=desglose.get(k,0); sub=round(cant*den,2); mon_tot+=sub
            etq=f"${int(den)}" if den>=1 else f"{int(den*100)}¢"
            L.append(f"  {etq:<18}{'moneda':<8}{cant:>6}  ${sub:>10,.2f}")
        L+=[lin,lr("  Subtotal billetes",f"${bil_tot:,.2f}"),
            lr("  Subtotal monedas",f"${mon_tot:,.2f}"),"="*W,
            lr("TOTAL CONTADO",f"${total_contado:,.2f}"),"="*W]
        if abs(diferencia)<0.01: L.append("✅  CAJA CUADRADA".center(W))
        elif diferencia>0: L.append(lr("SOBRANTE (+)",f"${diferencia:,.2f}"))
        else: L.append(lr("FALTANTE (-)",f"${abs(diferencia):,.2f}"))
        L.append("="*W)
        if notas: L+=[f"Notas: {notas}",lin]
        L+=[f"Impreso: {ahora.strftime('%d/%m/%Y %H:%M:%S')}".center(W),
            f"Por: {usuario['nombre'] if usuario else '—'}".center(W),"",""]
        return "\n".join(L)

    def _imprimir_y_cerrar(self, contenido, notas):
        try:
            with tempfile.NamedTemporaryFile(mode="w",suffix=".txt",delete=False,encoding="utf-8") as f:
                f.write(contenido); tmp=f.name
            if _ES_MAC:   os.system(f'lp "{tmp}"')
            elif _ES_WIN: os.startfile(tmp,"print")
            else:         os.system(f'lp "{tmp}"')
        except Exception as e:
            messagebox.showwarning("Impresión",f"No se pudo imprimir:\n{e}\n\nLa caja se cerrará de todas formas.")
        sesion=self._sesion; usuario=session.get_usuario()
        ahora=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        try:
            self.model.registrar_movimiento(sesion["id"],"salida",0.0,
                f"Corte impreso — {ahora} — {usuario['nombre'] if usuario else '—'}",
                usuario["id"] if usuario else None)
        except Exception: pass
        self.model.cerrar(sesion["id"],notas)
        messagebox.showinfo("✅ Caja cerrada","Corte enviado.\nLa caja quedó cerrada correctamente.")
        try: self.grab_release()
        except Exception: pass
        self.destroy()
        if self.on_success: self.on_success()
