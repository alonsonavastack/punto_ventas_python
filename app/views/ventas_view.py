"""
ventas_view.py  v1.6 — bugs corregidos (folio, IVA, cursor, búsqueda, bindings)
"""
import platform
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from app.models.producto_model import ProductoModel
from app.models.venta_model import VentaModel
from app.utils.config import COLORES
from app.utils import session
from app.utils.logo_utils import encabezado_ticket

_SISTEMA = platform.system()
_ES_MAC  = _SISTEMA == "Darwin"
_ES_WIN  = _SISTEMA == "Windows"


class VentasView(ctk.CTkFrame):
    UNIDADES_GRANEL = {"KG", "GR", "G", "LB", "LT", "L", "ML"}

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.producto_model   = ProductoModel()
        self.venta_model      = VentaModel()
        self.carrito          = []
        self._total           = 0.0
        self._fila_sel        = None
        self._todos_productos = []
        self._entry_codigo    = None
        self._canvas          = None
        try:
            self._todos_productos = self.producto_model.get_all()
        except Exception as e:
            print(f"⚠ No se pudo cargar productos: {e}")
        self._build()
        # Registrar bindings después de UI completamente lista
        self.after(10, self._registrar_bindings)

    def _es_granel(self, prod):
        return (prod.get("unidad") or "PZA").strip().upper() in self.UNIDADES_GRANEL

    def _tiene_granel_en_carrito(self):
        return any(i.get("granel") for i in self.carrito)

    def _actualizar_fecha(self):
        DIAS  = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
        MESES = ["enero","febrero","marzo","abril","mayo","junio",
                 "julio","agosto","septiembre","octubre","noviembre","diciembre"]
        ahora = datetime.now()
        self._lbl_fecha.configure(
            text=f"{DIAS[ahora.weekday()]} {ahora.day} de {MESES[ahora.month-1]} "
                 f"{ahora.year}   {ahora.strftime('%H:%M:%S')}")
        self.after(1000, self._actualizar_fecha)

    def _registrar_bindings(self):
        try:
            root = self.winfo_toplevel()
            
            # Bindings locales al frame
            self.bind("<Delete>",    self._borrar_seleccionado, add="+")
            self.bind("<BackSpace>", self._borrar_seleccionado, add="+")
            self.bind("<F10>", self._abrir_busqueda_con_event, add="+")
            self.bind("<F11>", lambda e: self._aplicar_mayoreo(), add="+")
            self.bind("<F12>", lambda e: self._abrir_cobro(), add="+")
            
            # Bindings globales a la ventana root
            if _ES_MAC:
                root.bind_all("<Command-b>", self._abrir_busqueda, add="+")
                root.bind_all("<Command-p>", lambda e: self._abrir_cobro(), add="+")
                root.bind_all("<Command-m>", lambda e: self._aplicar_mayoreo(), add="+")
            else:
                root.bind_all("<Control-b>", self._abrir_busqueda, add="+")
                root.bind_all("<Control-p>", lambda e: self._abrir_cobro(), add="+")
                root.bind_all("<Control-m>", lambda e: self._aplicar_mayoreo(), add="+")
            
            root.bind_all("<F10>", self._abrir_busqueda_con_event, add="+")
            root.bind_all("<F11>", lambda e: self._aplicar_mayoreo(), add="+")
            root.bind_all("<F12>", lambda e: self._abrir_cobro(), add="+")
            
            # Bindings directos al entry para máxima responsividad
            if self._entry_codigo:
                self._entry_codigo.bind("<F10>", self._abrir_busqueda_con_event, add="+")
                self._entry_codigo.bind("<F11>", lambda e: self._aplicar_mayoreo(), add="+")
                self._entry_codigo.bind("<F12>", lambda e: self._abrir_cobro(), add="+")
        except Exception as e:
            print(f"⚠ Error registrando bindings: {e}")
        
        self._focus_codigo()

    def _focus_codigo(self):
        if self._entry_codigo:
            try: self._entry_codigo.focus()
            except Exception: pass

    def _abrir_busqueda_con_event(self, event=None):
        self._abrir_busqueda(event)
        return "break"

    @staticmethod
    def _lbl_atajo(accion):
        mod = "⌘" if _ES_MAC else "Ctrl+"
        return {"buscar":  f"🔍 {mod}B / F10 Buscar",
                "mayoreo": f"💲 {mod}M / F11 Mayoreo",
                "cobrar":  f"💳 {mod}P / F12 Cobrar"}.get(accion, "")

    def _build(self):
        usuario  = session.get_usuario()
        nombre_u = usuario["nombre"] if usuario else "—"

        top = ctk.CTkFrame(self, fg_color=COLORES["bg_dark"], corner_radius=0, height=44)
        top.pack(fill="x"); top.pack_propagate(False)
        ctk.CTkLabel(top, text="VENTA DE PRODUCTOS",
                     font=("Segoe UI", 14, "bold"),
                     text_color=COLORES["text_primary"]).pack(side="left", padx=16, pady=8)
        ctk.CTkLabel(top, text=f"Le atiende: {nombre_u}",
                     font=("Segoe UI", 11),
                     text_color=COLORES["text_secondary"]).pack(side="right", padx=16)
        self._lbl_fecha = ctk.CTkLabel(top, text="", font=("Segoe UI", 11),
                                        text_color=COLORES["text_secondary"])
        self._lbl_fecha.pack(side="right", padx=20)
        self._actualizar_fecha()

        cod_bar = ctk.CTkFrame(self, fg_color=COLORES["bg_card"], corner_radius=0, height=52)
        cod_bar.pack(fill="x"); cod_bar.pack_propagate(False)
        ctk.CTkLabel(cod_bar, text="Código / Nombre del Producto:",
                     font=("Segoe UI", 12, "bold"),
                     text_color=COLORES["text_primary"]).pack(side="left", padx=(16, 8), pady=10)
        self._entry_codigo = ctk.CTkEntry(cod_bar, height=34, width=340, font=("Segoe UI", 13))
        self._entry_codigo.pack(side="left", padx=(0, 8))
        self._entry_codigo.bind("<Return>", self._enter_agregar)
        ctk.CTkButton(cod_bar, text="✅ ENTER - Agregar", height=34,
                      fg_color=COLORES["success"], font=("Segoe UI", 11, "bold"),
                      command=self._enter_agregar).pack(side="left", padx=4)
        leyenda = ctk.CTkFrame(cod_bar, fg_color="transparent")
        leyenda.pack(side="right", padx=12)
        for txt, color in [("⚖ Granel", COLORES["granel"]),
                            ("⭐ Mayoreo", COLORES["mayoreo"]),
                            ("🔴 Sin stock", COLORES["stock_cero"])]:
            ctk.CTkLabel(leyenda, text=txt, font=("Segoe UI", 9),
                         text_color=color).pack(side="left", padx=6)

        acc = ctk.CTkFrame(self, fg_color=COLORES["bg_dark"], corner_radius=0, height=40)
        acc.pack(fill="x"); acc.pack_propagate(False)
        for txt, color, cmd in [
            (self._lbl_atajo("buscar"),  COLORES["primary"],   self._abrir_busqueda),
            (self._lbl_atajo("mayoreo"), "#7c3aed",            self._aplicar_mayoreo),
            ("🗑 DEL Borrar Art.",       COLORES["danger"],    self._borrar_seleccionado),
            ("🔄 Limpiar todo",          COLORES["secondary"], self._confirmar_limpiar),
        ]:
            ctk.CTkButton(acc, text=txt, height=30, width=165,
                          fg_color=color, font=("Segoe UI", 10, "bold"),
                          corner_radius=4, command=cmd).pack(side="left", padx=4, pady=5)

        hdr_cols = ctk.CTkFrame(self, fg_color=COLORES["bg_card"], corner_radius=0, height=30)
        hdr_cols.pack(fill="x")
        for txt, w in [("Código",120),("Descripción del Producto",260),
                       ("Precio/Unidad",110),("Cant/Peso",110),("Importe",110),("Existencia",90)]:
            ctk.CTkLabel(hdr_cols, text=txt, font=("Segoe UI", 10, "bold"),
                         text_color=COLORES["text_secondary"],
                         width=w, anchor="w").pack(side="left", padx=6, pady=4)

        ticket_outer = ctk.CTkFrame(self, fg_color=COLORES["bg_dark"], corner_radius=0)
        ticket_outer.pack(fill="both", expand=True)
        self._canvas = tk.Canvas(ticket_outer, bg=COLORES["bg_dark"], highlightthickness=0)
        vscroll = tk.Scrollbar(ticket_outer, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vscroll.set)
        vscroll.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)
        self._ticket_frame = tk.Frame(self._canvas, bg=COLORES["bg_dark"])
        self._canvas_win   = self._canvas.create_window((0,0), window=self._ticket_frame, anchor="nw")
        self._ticket_frame.bind("<Configure>", lambda e: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(
            self._canvas_win, width=e.width))
        self._canvas.bind("<MouseWheel>", self._on_wheel)
        self._canvas.bind("<Button-4>",   lambda e: self._canvas.yview_scroll(-2, "units"))
        self._canvas.bind("<Button-5>",   lambda e: self._canvas.yview_scroll(2,  "units"))
        self._build_barra_inferior()

    def _on_wheel(self, event):
        if not self._canvas: return
        self._canvas.yview_scroll(
            int(-event.delta / (10 if _ES_MAC else 120)), "units")

    def _build_barra_inferior(self):
        bot = ctk.CTkFrame(self, fg_color=COLORES["bg_card"], corner_radius=0, height=60)
        bot.pack(fill="x", side="bottom"); bot.pack_propagate(False)
        self._lbl_num = ctk.CTkLabel(bot, text="0  Productos en la venta actual.",
                                      font=("Segoe UI", 12, "bold"),
                                      text_color=COLORES["text_secondary"])
        self._lbl_num.pack(side="left", padx=16)
        self._lbl_granel_info = ctk.CTkLabel(bot, text="", font=("Segoe UI", 10),
                                              text_color=COLORES["granel"])
        self._lbl_granel_info.pack(side="left", padx=8)
        right = ctk.CTkFrame(bot, fg_color="transparent")
        right.pack(side="right", padx=10)
        ctk.CTkButton(right, text=self._lbl_atajo("cobrar"), height=44, width=180,
                      font=("Segoe UI", 12, "bold"), fg_color=COLORES["primary"],
                      command=self._abrir_cobro).pack(side="left", padx=8)
        self._lbl_total = ctk.CTkLabel(right, text="$0.00",
                                        font=("Segoe UI", 28, "bold"),
                                        text_color=COLORES["primary"])
        self._lbl_total.pack(side="left")
        info = ctk.CTkFrame(bot, fg_color="transparent")
        info.pack(side="left", padx=16)
        for attr, lbl in [("_lbl_tot","Total:"),("_lbl_pago","Pagó:"),("_lbl_cambio","Cambio:")]:
            col = ctk.CTkFrame(info, fg_color="transparent")
            col.pack(side="left", padx=8)
            ctk.CTkLabel(col, text=lbl, font=("Segoe UI", 10),
                         text_color=COLORES["text_secondary"]).pack()
            w = ctk.CTkLabel(col, text="$0.00", font=("Segoe UI", 11, "bold"),
                             text_color=COLORES["text_primary"])
            w.pack()
            setattr(self, attr, w)
        ctk.CTkButton(bot, text="📋 Ventas del día", height=44, width=130,
                      font=("Segoe UI", 10), fg_color=COLORES["secondary"],
                      command=self._ver_ventas_dia).pack(side="right", padx=4)

    def _renderizar(self):
        for w in self._ticket_frame.winfo_children():
            w.destroy()
        self._total = 0.0
        ANCHO = [120, 260, 110, 110, 110, 90]
        for i, item in enumerate(self.carrito):
            sub = item["cantidad"] * item["precio_unit"]
            self._total += sub
            es_granel  = item.get("granel", False)
            unidad     = item.get("unidad", "PZA")
            es_mayoreo = item.get("es_mayoreo", False)
            existencia = float(item.get("existencia", 0))
            stock_bajo = existencia <= item["cantidad"]
            if self._fila_sel == i:   bg = "#1e40af"
            elif es_granel:           bg = "#042f2e" if i%2==0 else "#064e3b"
            else:                     bg = COLORES["bg_input"] if i%2==0 else COLORES["bg_dark"]
            row = tk.Frame(self._ticket_frame, bg=bg, height=36, cursor="hand2")
            row.pack(fill="x", pady=1); row.pack_propagate(False)
            tk.Label(row, text=item["codigo"][:14], bg=bg, fg=COLORES["text_primary"],
                     font=("Segoe UI",11), anchor="w").place(x=6, y=8, width=ANCHO[0]-6)
            nombre_display = ("⚖ " if es_granel else "") + item["nombre"][:32]
            tk.Label(row, text=nombre_display, bg=bg,
                     fg=COLORES["granel"] if es_granel else COLORES["text_primary"],
                     font=("Segoe UI",11), anchor="w").place(x=ANCHO[0]+6, y=8, width=ANCHO[1]-6)
            precio_txt = (f"${item['precio_unit']:.2f}/{unidad}" if es_granel
                          else f"${item['precio_unit']:.2f}")
            tk.Label(row, text=precio_txt, bg=bg,
                     fg=COLORES["mayoreo"] if es_mayoreo else COLORES["text_primary"],
                     font=("Segoe UI",11), anchor="w").place(
                         x=ANCHO[0]+ANCHO[1]+6, y=8, width=ANCHO[2]-6)
            x_cant = ANCHO[0]+ANCHO[1]+ANCHO[2]
            if es_granel:
                ctk.CTkButton(row, text=f"{item['cantidad']:.3f} {unidad}",
                              width=100, height=26,
                              fg_color=COLORES["granel"],
                              hover_color=COLORES["granel_hover"],
                              font=("Segoe UI",10,"bold"),
                              command=lambda x=item: self._editar_peso(x)
                              ).place(x=x_cant+4, y=4)
            else:
                ctk.CTkButton(row, text="−", width=26, height=26,
                              fg_color=COLORES["warning"], hover_color="#b45309",
                              font=("Segoe UI",13,"bold"),
                              command=lambda x=item: self._cambiar_cant(x,-1)
                              ).place(x=x_cant+2, y=4)
                ent = ctk.CTkEntry(row, width=42, height=26, justify="center",
                                    font=("Segoe UI",11,"bold"))
                ent.insert(0, str(int(item["cantidad"])))
                ent.place(x=x_cant+30, y=4)
                ent.bind("<Return>",   lambda e, x=item, en=ent: self._set_cant_manual(x,en))
                ent.bind("<FocusOut>", lambda e, x=item, en=ent: self._set_cant_manual(x,en))
                ctk.CTkButton(row, text="+", width=26, height=26,
                              fg_color=COLORES["success"], hover_color="#15803d",
                              font=("Segoe UI",13,"bold"),
                              command=lambda x=item: self._cambiar_cant(x,1)
                              ).place(x=x_cant+74, y=4)
            x_imp = x_cant + ANCHO[3]
            tk.Label(row, text=f"${sub:.2f}", bg=bg, fg=COLORES["success"],
                     font=("Segoe UI",11,"bold"), anchor="w").place(x=x_imp+6, y=8, width=ANCHO[4]-6)
            x_exist = x_imp + ANCHO[4]
            exist_txt = f"{existencia:.3f}" if es_granel else str(int(existencia))
            sc = (COLORES["stock_cero"] if existencia<=0
                  else COLORES["stock_bajo"] if stock_bajo
                  else COLORES["stock_ok"])
            tk.Label(row, text=exist_txt, bg=bg, fg=sc,
                     font=("Segoe UI",11), anchor="w").place(x=x_exist+6, y=8, width=ANCHO[5]-6)
            if es_mayoreo:
                tk.Label(row, text="⭐", bg=bg, font=("Segoe UI",13),
                         anchor="w").place(x=x_exist+ANCHO[5]+4, y=8)
            row.bind("<Button-1>", lambda e, idx=i: self._sel_fila(idx))
            row.bind("<MouseWheel>", self._on_wheel)
            row.bind("<Button-4>", lambda e: self._canvas.yview_scroll(-2,"units") if self._canvas else None)
            row.bind("<Button-5>", lambda e: self._canvas.yview_scroll(2,"units")  if self._canvas else None)
            for child in row.winfo_children():
                if isinstance(child, tk.Label):
                    child.bind("<Button-1>", lambda e, idx=i: self._sel_fila(idx))
        self._actualizar_totales()
        if self._canvas:
            self._canvas.update_idletasks()
            self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _editar_peso(self, item):
        unidad=item.get("unidad","KG"); precio=item["precio_unit"]; existencia=item["existencia"]
        dialog=ctk.CTkToplevel(self)
        dialog.title(f"Editar peso — {item['nombre']}")
        dialog.geometry("380x260"); dialog.resizable(False,False)
        dialog.grab_set(); dialog.configure(fg_color=COLORES["bg_dark"])
        dialog.lift(); dialog.after(100,dialog.lift)
        hdr=ctk.CTkFrame(dialog,fg_color=COLORES["granel"],corner_radius=0,height=42); hdr.pack(fill="x")
        ctk.CTkLabel(hdr,text="⚖  EDITAR PESO",font=("Segoe UI",13,"bold"),text_color="white").pack(side="left",padx=14,pady=10)
        body=ctk.CTkFrame(dialog,fg_color="transparent"); body.pack(fill="both",expand=True,padx=20,pady=10)
        ctk.CTkLabel(body,text=item["nombre"],font=("Segoe UI",12,"bold"),text_color=COLORES["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(body,text=f"${precio:.2f}/{unidad}  |  Stock: {existencia:.3f} {unidad}",
                     font=("Segoe UI",11),text_color=COLORES["text_secondary"]).pack(anchor="w",pady=(2,10))
        rp=ctk.CTkFrame(body,fg_color="transparent"); rp.pack(fill="x")
        ctk.CTkLabel(rp,text=f"Nuevo peso ({unidad}):",font=("Segoe UI",11,"bold"),text_color=COLORES["text_primary"]).pack(side="left")
        ep=ctk.CTkEntry(rp,width=120,height=38,font=("Segoe UI",15,"bold"),justify="center")
        ep.insert(0,f"{item['cantidad']:.3f}"); ep.pack(side="left",padx=(10,0))
        ep.focus(); ep.select_range(0,"end")
        lbl_t=ctk.CTkLabel(body,text=f"Total: ${item['cantidad']*precio:.2f}",
                            font=("Segoe UI",17,"bold"),text_color=COLORES["success"]); lbl_t.pack(pady=(10,0))
        def _act(*_):
            try: lbl_t.configure(text=f"Total: ${float(ep.get().replace(',','.'))*precio:.2f}")
            except: lbl_t.configure(text="Total: $0.00")
        ep.bind("<KeyRelease>",_act)
        br=ctk.CTkFrame(body,fg_color="transparent"); br.pack(fill="x",pady=(12,0))
        def _ok(event=None):
            try: peso=float(ep.get().strip().replace(",","."))
            except: messagebox.showwarning("Error","Ingresa un número.",parent=dialog); return
            if peso<=0: self.carrito.remove(item); self._fila_sel=None; dialog.destroy(); self._renderizar(); return
            if peso>existencia: messagebox.showwarning("Stock",f"Solo hay {existencia:.3f} {unidad}.",parent=dialog); return
            item["cantidad"]=peso; dialog.destroy(); self._renderizar()
        ep.bind("<Return>",_ok)
        ctk.CTkButton(br,text="✅ Actualizar",height=36,fg_color=COLORES["success"],
                      font=("Segoe UI",12,"bold"),command=_ok).pack(side="left",fill="x",expand=True,padx=(0,6))
        ctk.CTkButton(br,text="❌ Cancelar",height=36,fg_color=COLORES["danger"],
                      font=("Segoe UI",12,"bold"),command=dialog.destroy).pack(side="left",fill="x",expand=True)

    def _set_cant_manual(self,item,entry):
        try: nueva=float(entry.get().strip())
        except: entry.delete(0,"end"); entry.insert(0,str(int(item["cantidad"]))); return
        if nueva<=0: self.carrito.remove(item); self._fila_sel=None; self._renderizar(); return
        if nueva>item["existencia"]:
            messagebox.showwarning("Stock",f"Solo hay {int(item['existencia'])} unidades.")
            entry.delete(0,"end"); entry.insert(0,str(int(item["cantidad"]))); return
        item["cantidad"]=nueva; self._renderizar()

    def _sel_fila(self,idx): self._fila_sel=idx; self._renderizar()

    def _cambiar_cant(self,item,delta):
        nueva=item["cantidad"]+delta
        if nueva<=0: self.carrito.remove(item); self._fila_sel=None
        elif nueva>item["existencia"]: messagebox.showwarning("Stock",f"Máximo: {int(item['existencia'])}"); return
        else: item["cantidad"]=nueva
        self._renderizar()

    def _borrar_seleccionado(self,event=None):
        if self._fila_sel is not None and 0<=self._fila_sel<len(self.carrito):
            self.carrito.pop(self._fila_sel); self._fila_sel=None; self._renderizar()

    def _confirmar_limpiar(self):
        if self.carrito and messagebox.askyesno("Limpiar ticket","¿Eliminar todos los productos?"):
            self._limpiar()

    def _aplicar_mayoreo(self,event=None):
        if self._fila_sel is None or self._fila_sel>=len(self.carrito):
            messagebox.showinfo("Mayoreo","Selecciona un producto primero."); return
        item=self.carrito[self._fila_sel]
        if not item.get("precio_mayoreo"):
            messagebox.showinfo("Sin precio mayoreo","Este producto no tiene precio de mayoreo."); return
        if item.get("es_mayoreo"):
            item["precio_unit"]=item["precio_original"]; item["es_mayoreo"]=False
            messagebox.showinfo("Precio normal",f"Revertido a ${item['precio_unit']:.2f}")
        else:
            item["precio_original"]=item["precio_unit"]
            item["precio_unit"]=item["precio_mayoreo"]; item["es_mayoreo"]=True
            messagebox.showinfo("⭐ Mayoreo aplicado",f"Precio: ${item['precio_mayoreo']:.2f}")
        self._renderizar()

    def _actualizar_totales(self):
        self._lbl_total.configure(text=f"${self._total:.2f}")
        self._lbl_tot.configure(text=f"${self._total:.2f}")
        n=len(self.carrito); ng=sum(1 for i in self.carrito if i.get("granel"))
        self._lbl_num.configure(text=f"{n}  {'Producto' if n==1 else 'Productos'} en la venta actual.")
        self._lbl_granel_info.configure(text=f"⚖ {ng} a granel" if ng>0 else "")

    def _enter_agregar(self,event=None):
        if not self._entry_codigo: return
        cod=self._entry_codigo.get().strip()
        if not cod: self._abrir_busqueda(); return
        prod=self.producto_model.get_by_codigo(cod)
        if not prod:
            res=self.producto_model.buscar(cod)
            if len(res)==1: prod=res[0]
            elif len(res)>1: self._abrir_busqueda_con(res); self._entry_codigo.delete(0,"end"); return
            else: messagebox.showwarning("No encontrado",f"'{cod}' no encontrado."); self._entry_codigo.delete(0,"end"); return
        self._entry_codigo.delete(0,"end")
        self._agregar_al_carrito(prod)
        if not self._es_granel(prod): self.after(50,self._focus_codigo)

    def _beep(self):
        try:
            if _ES_MAC:
                import subprocess
                subprocess.Popen(["afplay","/System/Library/Sounds/Tink.aiff"],
                                 stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            elif _ES_WIN:
                import winsound; winsound.Beep(1000,80)
            else: self.bell()
        except Exception: self.bell()

    def _agregar_al_carrito(self,prod):
        existencia=float(prod.get("existencia",0) or 0)
        if existencia<=0: messagebox.showwarning("Sin stock",f"'{prod['nombre']}' sin existencia."); return
        if self._es_granel(prod): self._pedir_peso(prod,existencia); return
        for item in self.carrito:
            if item["producto_id"]==prod["id"] and not item.get("granel"):
                if item["cantidad"]+1>existencia:
                    messagebox.showwarning("Stock",f"Solo hay {int(existencia)}."); return
                item["cantidad"]+=1; self._beep(); self._renderizar(); return
        self.carrito.append({
            "producto_id": prod["id"], "nombre": prod["nombre"],
            "codigo": prod.get("codigo_barras","") or "",
            "cantidad": 1, "precio_unit": float(prod["precio_venta"]),
            "precio_original": float(prod["precio_venta"]),
            "precio_mayoreo": float(prod.get("precio_mayoreo") or 0),
            "existencia": existencia, "granel": False, "es_mayoreo": False,
            "unidad": (prod.get("unidad") or "PZA").strip().upper(),
            "aplica_iva": int(prod.get("aplica_iva") or 0),
        })
        self._beep(); self._renderizar()

    def _pedir_peso(self,prod,existencia):
        unidad=(prod.get("unidad") or "KG").strip().upper(); precio=float(prod["precio_venta"])
        dialog=ctk.CTkToplevel(self); dialog.title(f"⚖ Granel — {prod['nombre']}")
        dialog.geometry("400x300"); dialog.resizable(False,False)
        dialog.grab_set(); dialog.configure(fg_color=COLORES["bg_dark"])
        dialog.lift(); dialog.after(100,dialog.lift)
        hdr=ctk.CTkFrame(dialog,fg_color=COLORES["granel"],corner_radius=0,height=46); hdr.pack(fill="x")
        ctk.CTkLabel(hdr,text="⚖  PRODUCTO A GRANEL",font=("Segoe UI",14,"bold"),text_color="white").pack(side="left",padx=14,pady=12)
        body=ctk.CTkFrame(dialog,fg_color="transparent"); body.pack(fill="both",expand=True,padx=20,pady=10)
        ctk.CTkLabel(body,text=prod["nombre"],font=("Segoe UI",13,"bold"),text_color=COLORES["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(body,text=f"${precio:.2f}/{unidad}  |  Stock: {existencia:.3f} {unidad}",
                     font=("Segoe UI",11),text_color=COLORES["text_secondary"]).pack(anchor="w",pady=(2,12))
        rp=ctk.CTkFrame(body,fg_color="transparent"); rp.pack(fill="x")
        ctk.CTkLabel(rp,text=f"Peso ({unidad}):",font=("Segoe UI",12,"bold"),text_color=COLORES["text_primary"]).pack(side="left")
        ep=ctk.CTkEntry(rp,width=130,height=42,font=("Segoe UI",17,"bold"),justify="center"); ep.pack(side="left",padx=(10,0)); ep.focus()
        lbl_t=ctk.CTkLabel(body,text="Total: $0.00",font=("Segoe UI",20,"bold"),text_color=COLORES["success"]); lbl_t.pack(pady=(14,0))
        def _act(*_):
            try: lbl_t.configure(text=f"Total: ${float(ep.get().replace(',','.'))*precio:.2f}")
            except: lbl_t.configure(text="Total: $0.00")
        ep.bind("<KeyRelease>",_act)
        br=ctk.CTkFrame(body,fg_color="transparent"); br.pack(fill="x",pady=(16,0))
        def _ok(event=None):
            try: peso=float(ep.get().strip().replace(",","."))
            except: messagebox.showwarning("Error","Ingresa un número.",parent=dialog); return
            if peso<=0: messagebox.showwarning("Error","Debe ser mayor que cero.",parent=dialog); return
            if peso>existencia: messagebox.showwarning("Stock",f"Solo hay {existencia:.3f} {unidad}.",parent=dialog); return
            dialog.destroy(); self._agregar_granel_carrito(prod,peso,existencia); self.after(60,self._focus_codigo)
        ep.bind("<Return>",_ok)
        ctk.CTkButton(br,text="✅ Agregar al ticket",height=38,fg_color=COLORES["success"],
                      font=("Segoe UI",12,"bold"),command=_ok).pack(side="left",fill="x",expand=True,padx=(0,6))
        ctk.CTkButton(br,text="❌ Cancelar",height=38,fg_color=COLORES["danger"],
                      font=("Segoe UI",12,"bold"),command=dialog.destroy).pack(side="left",fill="x",expand=True)

    def _agregar_granel_carrito(self,prod,peso,existencia):
        unidad=(prod.get("unidad") or "KG").strip().upper()
        for item in self.carrito:
            if item["producto_id"]==prod["id"] and item.get("granel"):
                nv=item["cantidad"]+peso
                if nv>existencia: messagebox.showwarning("Stock",f"Solo hay {existencia:.3f} {unidad}."); return
                item["cantidad"]=nv; self._beep(); self._renderizar(); return
        self.carrito.append({
            "producto_id": prod["id"], "nombre": prod["nombre"],
            "codigo": prod.get("codigo_barras","") or "",
            "cantidad": peso, "precio_unit": float(prod["precio_venta"]),
            "precio_original": float(prod["precio_venta"]),
            "precio_mayoreo": float(prod.get("precio_mayoreo") or 0),
            "existencia": existencia, "granel": True, "es_mayoreo": False, "unidad": unidad,
            "aplica_iva": int(prod.get("aplica_iva") or 0),
        })
        self._beep(); self._renderizar()

    def _refrescar_productos(self):
        """
        Bug #8 corregido: refresca el catálogo completo de productos desde la BD.
        Se llama antes de abrir el buscador para que siempre muestre datos actuales.
        """
        try:
            self._todos_productos = self.producto_model.get_all()
        except Exception as e:
            print(f"⚠ No se pudo refrescar productos: {e}")

    def _abrir_busqueda(self,event=None):
        # Bug #8 corregido: se refresca el catálogo antes de abrir la búsqueda
        self._refrescar_productos()
        try:
            from app.views.widgets.busqueda_producto import BusquedaProductoWidget
            BusquedaProductoWidget(self,on_seleccionar=self._agregar_al_carrito,
                                   productos=self._todos_productos)
        except Exception as e: print(f"Error búsqueda: {e}")

    def _abrir_busqueda_con(self,productos):
        try:
            from app.views.widgets.busqueda_producto import BusquedaProductoWidget
            BusquedaProductoWidget(self,on_seleccionar=self._agregar_al_carrito,productos=productos)
        except Exception as e: print(f"Error: {e}")

    def _abrir_cobro(self):
        if not self.carrito: messagebox.showwarning("Carrito vacío","Agrega productos primero."); return
        try:
            from app.views.widgets.cobro import CobroWidget
            CobroWidget(self,total=self._total,num_articulos=len(self.carrito),
                        on_cobrar=self._procesar_cobro,
                        tiene_granel=self._tiene_granel_en_carrito())
        except Exception as e: print(f"Error cobro: {e}")

    def _procesar_cobro(self,monto_pagado,imprimir,forma_pago="efectivo",descuento=0.0):
        cambio=round(monto_pagado-self._total,2)
        try:
            ses=session.get_sesion_caja()
            resultado=self.venta_model.crear_venta(
                items=self.carrito,forma_pago=forma_pago,
                monto_pagado=monto_pagado,descuento=descuento,
                sesion_caja_id=ses["id"] if ses else None)
            self._lbl_pago.configure(text=f"${monto_pagado:.2f}")
            self._lbl_cambio.configure(text=f"${cambio:.2f}")
            if imprimir: self._preview_ticket(resultado,monto_pagado,cambio)
            else: messagebox.showinfo("✅ Venta",
                    f"Folio: {resultado['folio']}\nTotal: ${resultado['total']:.2f}\nCambio: ${cambio:.2f}")
            self._limpiar(); self._todos_productos=self.producto_model.get_all()
        except Exception as e: messagebox.showerror("Error",f"No se pudo registrar:\n{e}")

    def _generar_contenido_ticket(self, resultado, monto_pagado, cambio):
        """Genera el texto del ticket usando encabezado_ticket de logo_utils."""
        ahora  = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        usuario = session.get_usuario()
        cajero  = usuario["nombre"] if usuario else "—"
        folio   = resultado.get("folio", "")
        total   = resultado.get("total", self._total)
        W       = 42
        linea   = "─" * W

        lines = encabezado_ticket(W)
        lines += [
            f"Fecha : {ahora}",
            f"Cajero: {cajero}",
            f"Folio : {folio}",
            linea,
            f"{'Descripcion':<20}{'Cant':>7}{'P.Unit':>7}{'Importe':>8}",
            linea,
        ]
        for item in self.carrito:
            desc    = item["nombre"][:19]
            precio  = item["precio_unit"]
            importe = item["cantidad"] * precio
            unidad  = item.get("unidad", "PZA")
            cant_str = (f"{item['cantidad']:.3f}{unidad}" if item.get("granel")
                        else str(int(item["cantidad"])))
            sfx = " ⭐" if item.get("es_mayoreo") else ""
            lines.append(f"{desc:<20}{cant_str:>7}${precio:>6.2f}{importe:>8.2f}{sfx}")
            if item.get("granel"):
                lines.append(f"  (${precio:.2f}/{unidad})")

        lines += [
            linea,
            f"{'TOTAL':>{W-9}}  ${total:>7.2f}",
            f"{'PAGÓ':>{W-9}}  ${monto_pagado:>7.2f}",
            f"{'CAMBIO':>{W-9}}  ${cambio:>7.2f}",
            linea,
            f"{'¡Gracias por su compra!':^{W}}",
            "", "",
        ]
        return "\n".join(lines)

    def _preview_ticket(self,resultado,monto_pagado,cambio):
        contenido=self._generar_contenido_ticket(resultado,monto_pagado,cambio)
        win=ctk.CTkToplevel(self); win.title("🖨 Vista previa del ticket")
        win.geometry("420x560"); win.grab_set(); win.configure(fg_color=COLORES["bg_dark"])
        hdr=ctk.CTkFrame(win,fg_color=COLORES["primary"],corner_radius=0,height=40); hdr.pack(fill="x")
        ctk.CTkLabel(hdr,text="VISTA PREVIA DEL TICKET",font=("Segoe UI",13,"bold"),text_color="white").pack(side="left",padx=14,pady=8)
        tf=ctk.CTkFrame(win,fg_color="white",corner_radius=8); tf.pack(fill="both",expand=True,padx=16,pady=12)
        sb=tk.Scrollbar(tf,orient="vertical"); sb.pack(side="right",fill="y")
        txt_w=tk.Text(tf,font=("Courier New",10),bg="white",fg="black",relief="flat",
                      padx=8,pady=8,wrap="none",yscrollcommand=sb.set)
        sb.configure(command=txt_w.yview); txt_w.pack(fill="both",expand=True)
        txt_w.insert("1.0",contenido); txt_w.configure(state="disabled")
        br=ctk.CTkFrame(win,fg_color="transparent"); br.pack(fill="x",padx=16,pady=(0,12))
        ctk.CTkButton(br,text="🖨 Imprimir",height=38,fg_color=COLORES["success"],
                      font=("Segoe UI",12,"bold"),
                      command=lambda:[win.destroy(),
                                      self._imprimir_ticket(resultado,monto_pagado,cambio)]
                      ).pack(side="left",fill="x",expand=True,padx=(0,6))
        ctk.CTkButton(br,text="❌ Cancelar",height=38,fg_color=COLORES["danger"],
                      font=("Segoe UI",12,"bold"),command=win.destroy
                      ).pack(side="left",fill="x",expand=True)

    def _imprimir_ticket(self,resultado,monto_pagado,cambio):
        import tempfile, os
        contenido=self._generar_contenido_ticket(resultado,monto_pagado,cambio)
        folio=resultado.get("folio",""); total=resultado.get("total",self._total)
        try:
            with tempfile.NamedTemporaryFile(mode="w",suffix=".txt",
                                             delete=False,encoding="utf-8") as f:
                f.write(contenido); tmp=f.name
            if _ES_MAC:   os.system(f'lp "{tmp}"')
            elif _ES_WIN: os.startfile(tmp,"print")
            else:         os.system(f'lp "{tmp}"')
            messagebox.showinfo("✅ Impresión",
                f"Folio: {folio}\nTotal: ${total:.2f}\nCambio: ${cambio:.2f}\n\n🖨 Enviado.")
        except Exception as e:
            messagebox.showwarning("Impresión",f"Venta registrada. No se pudo imprimir:\n{e}")

    def _limpiar(self):
        self.carrito.clear(); self._fila_sel=None
        if self._entry_codigo: self._entry_codigo.delete(0,"end")
        self._renderizar(); self.after(60,self._focus_codigo)

    def _ver_ventas_dia(self):
        try:
            from app.views.ventas_dia_view import VentasDiaView; VentasDiaView(self)
        except Exception as e: print(f"Error: {e}")
