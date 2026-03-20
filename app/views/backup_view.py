"""
backup_view.py — Exportar e Importar base de datos + logo
Correcciones:
  - Exporta con INSERT IGNORE → al importar nunca falla por duplicados
  - Modo "Reemplazar todo" usa TRUNCATE + INSERT para restauración completa
  - Importador silencia duplicados correctamente
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime
import os
import zipfile
import platform
import threading
import shutil

from app.database.connection import Database
from app.utils.config import COLORES
from app.utils import session

_BASE     = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_LOGO_DIR = os.path.join(_BASE, "assets", "images")


def _ruta_logo_actual():
    for ext in ("png", "jpg", "jpeg", "gif"):
        p = os.path.join(_LOGO_DIR, f"logo.{ext}")
        if os.path.exists(p):
            return p
    return None


class BackupView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.db = Database.get_instance()
        self._build()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=COLORES["bg_dark"], corner_radius=0, height=52)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="🗄️  Base de Datos — Exportar / Importar",
                     font=("Segoe UI", 16, "bold"),
                     text_color=COLORES["text_primary"]).pack(side="left", padx=20, pady=14)
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=10)
        self._seccion(scroll, "📤  Exportar base de datos",  "#065f46", self._build_exportar)
        ctk.CTkFrame(scroll, height=2, fg_color=COLORES["border"]).pack(fill="x", pady=16)
        self._seccion(scroll, "📥  Importar / Restaurar",    "#7f1d1d", self._build_importar)
        ctk.CTkFrame(scroll, height=2, fg_color=COLORES["border"]).pack(fill="x", pady=16)
        self._seccion(scroll, "📋  Backups recientes",       "#1e3a5f", self._build_lista_backups)

    def _seccion(self, parent, titulo, color, fn):
        card = ctk.CTkFrame(parent, fg_color=COLORES["bg_card"], corner_radius=12)
        card.pack(fill="x", pady=4)
        hdr = ctk.CTkFrame(card, fg_color=color, corner_radius=8, height=38)
        hdr.pack(fill="x", padx=2, pady=(2, 0)); hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=titulo, font=("Segoe UI", 13, "bold"),
                     text_color="white").pack(side="left", padx=14, pady=6)
        fn(card)

    # ── EXPORTAR ─────────────────────────────────────────────────────────────
    def _build_exportar(self, parent):
        body = ctk.CTkFrame(parent, fg_color="transparent")
        body.pack(fill="x", padx=16, pady=12)
        ctk.CTkLabel(body,
            text="Genera un archivo .zip con la base de datos completa + logo del negocio.",
            font=("Segoe UI", 11), text_color=COLORES["text_secondary"],
            justify="left").pack(anchor="w", pady=(0, 10))

        # Destino
        ctk.CTkLabel(body, text="Guardar en:", font=("Segoe UI", 11),
                     text_color=COLORES["text_secondary"]).pack(anchor="w")
        dr = ctk.CTkFrame(body, fg_color="transparent"); dr.pack(fill="x", pady=(4, 8))
        dr.columnconfigure(0, weight=1)
        self._entry_destino = ctk.CTkEntry(dr, height=34, font=("Segoe UI", 11))
        self._entry_destino.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ruta_def = os.path.join(os.path.expanduser("~"), "Desktop",
            f"backup_punto_ventas_{datetime.now().strftime('%Y%m%d_%H%M')}.zip")
        self._entry_destino.insert(0, ruta_def)
        ctk.CTkButton(dr, text="📁 Elegir", width=90, height=34,
                      fg_color=COLORES["secondary"],
                      command=self._elegir_destino).grid(row=0, column=1)

        # Opciones
        opt = ctk.CTkFrame(body, fg_color="transparent"); opt.pack(anchor="w", pady=(0, 6))
        self._var_estructura = tk.BooleanVar(value=True)
        self._var_datos      = tk.BooleanVar(value=True)
        self._var_logo       = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(opt, text="Estructura BD",       variable=self._var_estructura,
                        font=("Segoe UI", 11)).pack(side="left", padx=(0, 14))
        ctk.CTkCheckBox(opt, text="Datos BD",            variable=self._var_datos,
                        font=("Segoe UI", 11)).pack(side="left", padx=(0, 14))
        ctk.CTkCheckBox(opt, text="🖼️ Logo del negocio", variable=self._var_logo,
                        font=("Segoe UI", 11)).pack(side="left")

        logo_actual = _ruta_logo_actual()
        ctk.CTkLabel(body,
            text=f"  Logo actual: {os.path.basename(logo_actual)}" if logo_actual
                 else "  Sin logo personalizado configurado",
            font=("Segoe UI", 10),
            text_color=COLORES["success"] if logo_actual else "#475569").pack(anchor="w", pady=(0, 10))

        self._lbl_estado_exp = ctk.CTkLabel(body, text="", font=("Segoe UI", 11),
                                             text_color=COLORES["text_secondary"])
        self._lbl_estado_exp.pack(anchor="w", pady=(0, 4))
        self._prog_exp = ctk.CTkProgressBar(body, height=8)
        self._prog_exp.set(0); self._prog_exp.pack(fill="x", pady=(0, 8))
        self._prog_exp.pack_forget()
        ctk.CTkButton(body, text="📤  Exportar ahora", height=42,
                      fg_color="#059669", hover_color="#047857",
                      font=("Segoe UI", 13, "bold"),
                      command=self._exportar).pack(fill="x")

    # ── IMPORTAR ─────────────────────────────────────────────────────────────
    def _build_importar(self, parent):
        body = ctk.CTkFrame(parent, fg_color="transparent")
        body.pack(fill="x", padx=16, pady=12)

        # Advertencia
        warn = ctk.CTkFrame(body, fg_color="#450a0a", corner_radius=8); warn.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(warn,
            text="⚠️  ADVERTENCIA: Importar reemplazará los datos actuales con los del backup.",
            font=("Segoe UI", 11, "bold"), text_color="#fca5a5",
            justify="left").pack(padx=12, pady=8)

        # Modo de importación
        ctk.CTkLabel(body, text="Modo de restauración:", font=("Segoe UI", 11, "bold"),
                     text_color=COLORES["text_primary"]).pack(anchor="w", pady=(0, 4))
        self._var_modo = tk.StringVar(value="reemplazar")
        modos = ctk.CTkFrame(body, fg_color=COLORES["bg_dark"], corner_radius=8)
        modos.pack(fill="x", pady=(0, 10))

        ctk.CTkRadioButton(modos,
            text="🔄 Reemplazar todo  (borra datos actuales e importa los del backup — RECOMENDADO)",
            variable=self._var_modo, value="reemplazar",
            font=("Segoe UI", 11)).pack(anchor="w", padx=12, pady=(10, 4))
        ctk.CTkLabel(modos,
            text="      Usa TRUNCATE + INSERT. Restauración limpia y sin errores.",
            font=("Segoe UI", 9), text_color="#64748b").pack(anchor="w", padx=12)

        ctk.CTkFrame(modos, height=1, fg_color=COLORES["border"]).pack(fill="x", padx=12, pady=6)

        ctk.CTkRadioButton(modos,
            text="➕ Agregar / Actualizar  (conserva datos actuales, agrega los nuevos del backup)",
            variable=self._var_modo, value="agregar",
            font=("Segoe UI", 11)).pack(anchor="w", padx=12, pady=(0, 4))
        ctk.CTkLabel(modos,
            text="      Usa INSERT IGNORE. No sobreescribe datos existentes.",
            font=("Segoe UI", 9), text_color="#64748b").pack(anchor="w", padx=12, pady=(0, 10))

        # Archivo
        ctk.CTkLabel(body, text="Archivo de backup (.zip o .sql):",
                     font=("Segoe UI", 11), text_color=COLORES["text_secondary"]).pack(anchor="w")
        ir = ctk.CTkFrame(body, fg_color="transparent"); ir.pack(fill="x", pady=(4, 8))
        ir.columnconfigure(0, weight=1)
        self._entry_origen = ctk.CTkEntry(ir, height=34, font=("Segoe UI", 11),
                                          placeholder_text="Selecciona .zip o .sql...")
        self._entry_origen.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(ir, text="📂 Buscar", width=90, height=34,
                      fg_color=COLORES["secondary"],
                      command=self._elegir_origen).grid(row=0, column=1)

        self._lbl_info_sql = ctk.CTkLabel(body, text="", font=("Segoe UI", 10),
                                           text_color="#64748b")
        self._lbl_info_sql.pack(anchor="w", pady=(0, 8))
        self._lbl_estado_imp = ctk.CTkLabel(body, text="", font=("Segoe UI", 11),
                                             text_color=COLORES["text_secondary"])
        self._lbl_estado_imp.pack(anchor="w", pady=(0, 4))
        self._prog_imp = ctk.CTkProgressBar(body, height=8)
        self._prog_imp.set(0); self._prog_imp.pack(fill="x", pady=(0, 8))
        self._prog_imp.pack_forget()
        ctk.CTkButton(body, text="📥  Restaurar ahora", height=42,
                      fg_color="#dc2626", hover_color="#b91c1c",
                      font=("Segoe UI", 13, "bold"),
                      command=self._confirmar_importar).pack(fill="x")

    # ── LISTA BACKUPS ─────────────────────────────────────────────────────────
    def _build_lista_backups(self, parent):
        body = ctk.CTkFrame(parent, fg_color="transparent"); body.pack(fill="x", padx=16, pady=12)
        ctk.CTkLabel(body, text="Backups en el Escritorio (.zip y .sql):",
                     font=("Segoe UI", 11), text_color=COLORES["text_secondary"]
                     ).pack(anchor="w", pady=(0, 6))
        self._frame_lista = ctk.CTkFrame(body, fg_color=COLORES["bg_dark"], corner_radius=8)
        self._frame_lista.pack(fill="x")
        self._refrescar_lista()
        ctk.CTkButton(body, text="🔄 Actualizar lista", height=30, width=160,
                      fg_color=COLORES["secondary"], font=("Segoe UI", 10, "bold"),
                      command=self._refrescar_lista).pack(anchor="w", pady=(8, 0))

    def _refrescar_lista(self):
        for w in self._frame_lista.winfo_children(): w.destroy()
        desktop = os.path.expanduser("~/Desktop")
        try:
            archivos = sorted([f for f in os.listdir(desktop)
                if f.startswith("backup_punto_ventas") and f.endswith((".zip", ".sql"))
            ], reverse=True)[:10]
        except Exception: archivos = []
        if not archivos:
            ctk.CTkLabel(self._frame_lista, text="  Sin backups en el escritorio.",
                         font=("Segoe UI", 11), text_color="#475569").pack(pady=10)
            return
        hrow = ctk.CTkFrame(self._frame_lista, fg_color=COLORES["primary"],
                             corner_radius=4, height=28)
        hrow.pack(fill="x", padx=4, pady=(4, 2))
        for txt, w in [("Archivo", 300), ("Tipo", 60), ("Tamaño", 90), ("", 120)]:
            ctk.CTkLabel(hrow, text=txt, font=("Segoe UI", 10, "bold"),
                         text_color="white", width=w, anchor="w").pack(side="left", padx=8, pady=3)
        for i, nombre in enumerate(archivos):
            ruta = os.path.join(desktop, nombre)
            ext  = "📦 ZIP" if nombre.endswith(".zip") else "📄 SQL"
            try:
                sk = os.path.getsize(ruta) / 1024
                ss = f"{sk:.1f} KB" if sk < 1024 else f"{sk/1024:.1f} MB"
            except Exception: ss = "?"
            bg = COLORES["bg_card"] if i % 2 == 0 else "transparent"
            row = ctk.CTkFrame(self._frame_lista, fg_color=bg, corner_radius=4, height=32)
            row.pack(fill="x", padx=4, pady=1)
            ctk.CTkLabel(row, text=nombre[:42], font=("Segoe UI", 10),
                         text_color=COLORES["text_primary"], width=300, anchor="w").pack(side="left", padx=8)
            ctk.CTkLabel(row, text=ext, font=("Segoe UI", 9),
                         text_color=COLORES["text_secondary"], width=60, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=ss, font=("Segoe UI", 10),
                         text_color=COLORES["text_secondary"], width=90, anchor="w").pack(side="left")
            ctk.CTkButton(row, text="📥 Restaurar", width=110, height=24,
                          fg_color="#7f1d1d", hover_color="#991b1b",
                          font=("Segoe UI", 9, "bold"),
                          command=lambda r=ruta: self._cargar_y_importar(r)
                          ).pack(side="left", padx=4)

    # ── Lógica exportar ───────────────────────────────────────────────────────
    def _elegir_destino(self):
        nombre = f"backup_punto_ventas_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
        ruta = filedialog.asksaveasfilename(
            title="Guardar backup", defaultextension=".zip", initialfile=nombre,
            filetypes=[("ZIP backup", "*.zip"), ("SQL", "*.sql"), ("All", "*.*")])
        if ruta: self._entry_destino.delete(0, "end"); self._entry_destino.insert(0, ruta)

    def _exportar(self):
        ruta = self._entry_destino.get().strip()
        if not ruta: messagebox.showwarning("Error", "Elige un destino."); return
        self._prog_exp.pack(fill="x", pady=(0, 8)); self._prog_exp.set(0)
        self._lbl_estado_exp.configure(text="⏳ Exportando...", text_color=COLORES["warning"])
        threading.Thread(target=self._exportar_hilo, args=(ruta,), daemon=True).start()

    def _exportar_hilo(self, ruta):
        try:
            lineas = _generar_sql(self.db,
                                   self._var_estructura.get(),
                                   self._var_datos.get(),
                                   callback_progreso=lambda v: self._upd_exp(v * 0.85))
            sql_content = "\n".join(lineas)
            logo_ruta   = _ruta_logo_actual() if self._var_logo.get() else None

            if ruta.endswith(".zip"):
                with zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as zf:
                    zf.writestr("datos.sql", sql_content)
                    if logo_ruta and os.path.exists(logo_ruta):
                        ext = os.path.splitext(logo_ruta)[1]
                        zf.write(logo_ruta, f"logo{ext}")
            else:
                with open(ruta, "w", encoding="utf-8") as f: f.write(sql_content)

            self.after(0, lambda: self._prog_exp.set(1))
            sk = os.path.getsize(ruta) / 1024
            ss = f"{sk:.1f} KB" if sk < 1024 else f"{sk/1024:.1f} MB"
            logo_msg = "  +  🖼️ logo incluido" if (ruta.endswith(".zip") and logo_ruta) else ""
            self.after(0, lambda: self._lbl_estado_exp.configure(
                text=f"✅ Exportado  ({ss}){logo_msg}", text_color=COLORES["success"]))
            self.after(0, self._refrescar_lista)
            self.after(0, lambda: messagebox.showinfo("✅ Exportación completada",
                f"Backup guardado en:\n{ruta}\n\nTamaño: {ss}{logo_msg}"))
        except Exception as e:
            self.after(0, lambda: self._lbl_estado_exp.configure(
                text=f"❌ Error: {e}", text_color=COLORES["danger"]))
            self.after(0, lambda: messagebox.showerror("Error al exportar", str(e)))

    def _upd_exp(self, v):
        self.after(0, lambda: self._prog_exp.set(v))

    # ── Lógica importar ───────────────────────────────────────────────────────
    def _elegir_origen(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar backup",
            filetypes=[("Backup ZIP o SQL", "*.zip *.sql"), ("All", "*.*")])
        if ruta: self._cargar_y_importar(ruta)

    def _cargar_y_importar(self, ruta):
        self._entry_origen.delete(0, "end"); self._entry_origen.insert(0, ruta)
        try:
            sk = os.path.getsize(ruta) / 1024
            ss = f"{sk:.1f} KB" if sk < 1024 else f"{sk/1024:.1f} MB"
            if ruta.endswith(".zip"):
                with zipfile.ZipFile(ruta, "r") as zf:
                    nombres = zf.namelist()
                tiene_sql  = any(n.endswith(".sql") for n in nombres)
                tiene_logo = any(n.startswith("logo") for n in nombres)
                self._lbl_info_sql.configure(
                    text=f"📦 ZIP  •  {ss}  •  {'✅ BD' if tiene_sql else '❌ sin BD'}"
                         f"  •  {'✅ Logo incluido' if tiene_logo else '— sin logo'}",
                    text_color=COLORES["success"] if tiene_sql else COLORES["warning"])
            else:
                with open(ruta, "r", encoding="utf-8", errors="ignore") as f: ls = f.readlines()
                ni = sum(1 for l in ls if l.strip().upper().startswith("INSERT"))
                nc = sum(1 for l in ls if l.strip().upper().startswith("CREATE"))
                self._lbl_info_sql.configure(
                    text=f"📄 SQL  •  {ss}  •  {nc} tablas  •  {ni} bloques — sin logo",
                    text_color="#64748b")
        except Exception: self._lbl_info_sql.configure(text="Archivo seleccionado.")

    def _confirmar_importar(self):
        ruta = self._entry_origen.get().strip()
        if not ruta or not os.path.exists(ruta):
            messagebox.showwarning("Error", "Selecciona un archivo .zip o .sql válido."); return
        modo = self._var_modo.get()
        aviso = ("🔄 REEMPLAZAR TODO:\nBorrará los datos actuales y los reemplazará con los del backup."
                 if modo == "reemplazar"
                 else "➕ AGREGAR:\nAgregará registros nuevos sin tocar los existentes.")
        if not messagebox.askyesno("⚠️ Confirmar restauración",
                f"{aviso}\n\n¿Deseas continuar?", icon="warning"): return
        self._prog_imp.pack(fill="x", pady=(0, 8)); self._prog_imp.set(0)
        self._lbl_estado_imp.configure(text="⏳ Restaurando...", text_color=COLORES["warning"])
        threading.Thread(target=self._importar_hilo, args=(ruta, modo), daemon=True).start()

    def _importar_hilo(self, ruta, modo):
        try:
            logo_restaurado = False
            if ruta.endswith(".zip"):
                with zipfile.ZipFile(ruta, "r") as zf:
                    nombres = zf.namelist()
                    sqls = [n for n in nombres if n.endswith(".sql")]
                    if not sqls: raise ValueError("El ZIP no contiene ningún archivo .sql")
                    sql_content = zf.read(sqls[0]).decode("utf-8", errors="ignore")
                    logos = [n for n in nombres if n.startswith("logo")]
                    if logos:
                        for ext in ("png","jpg","jpeg","gif"):
                            viejo = os.path.join(_LOGO_DIR, f"logo.{ext}")
                            if os.path.exists(viejo): os.remove(viejo)
                        logo_ext  = os.path.splitext(logos[0])[1]
                        logo_dest = os.path.join(_LOGO_DIR, f"logo{logo_ext}")
                        os.makedirs(_LOGO_DIR, exist_ok=True)
                        with zf.open(logos[0]) as src, open(logo_dest, "wb") as dst:
                            dst.write(src.read())
                        logo_restaurado = True
            else:
                with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
                    sql_content = f.read()

            errores = _ejecutar_restauracion(self.db, sql_content, modo,
                                              callback_progreso=self._upd_imp)
            self.after(0, lambda: self._prog_imp.set(1))
            logo_msg = "\n🖼️  Logo restaurado correctamente." if logo_restaurado else ""

            if errores:
                msg = "\n".join(errores[:8])
                if len(errores) > 8: msg += f"\n... y {len(errores)-8} más"
                self.after(0, lambda: self._lbl_estado_imp.configure(
                    text=f"⚠️ Restaurado con {len(errores)} advertencia(s)",
                    text_color=COLORES["warning"]))
                self.after(0, lambda: messagebox.showwarning("Advertencias",
                    f"Restaurado con {len(errores)} advertencia(s):{logo_msg}\n\n{msg}"))
            else:
                self.after(0, lambda: self._lbl_estado_imp.configure(
                    text="✅ Restaurado correctamente", text_color=COLORES["success"]))
                self.after(0, lambda: messagebox.showinfo("✅ Restauración completada",
                    f"Base de datos restaurada sin errores.{logo_msg}\n\n"
                    "Reinicia la aplicación para ver los cambios."))
        except Exception as e:
            self.after(0, lambda: self._lbl_estado_imp.configure(
                text=f"❌ Error: {e}", text_color=COLORES["danger"]))
            self.after(0, lambda: messagebox.showerror("Error al restaurar", str(e)))

    def _upd_imp(self, v):
        self.after(0, lambda: self._prog_imp.set(v))


# ── Motor de exportación ──────────────────────────────────────────────────────
def _generar_sql(db, con_estructura=True, con_datos=True, callback_progreso=None):
    ahora  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lineas = [
        "-- ============================================================",
        f"-- Punto de Ventas — Backup generado el {ahora}",
        "-- ============================================================",
        "", "SET FOREIGN_KEY_CHECKS = 0;",
        "SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';", "SET NAMES utf8mb4;", "",
    ]
    tablas = db.fetch_all("SHOW TABLES")
    nombres = [list(t.values())[0] for t in tablas]
    total   = max(len(nombres), 1)

    for idx, tabla in enumerate(nombres):
        lineas += [f"-- Tabla: `{tabla}`", ""]
        if con_estructura:
            lineas.append(f"DROP TABLE IF EXISTS `{tabla}`;")
            try:
                create = db.fetch_one(f"SHOW CREATE TABLE `{tabla}`")
                create_sql = create.get("Create Table") or list(create.values())[1]
                lineas.append(create_sql + ";")
            except Exception as e:
                lineas.append(f"-- ERROR estructura {tabla}: {e}")
            lineas.append("")

        if con_datos:
            try:
                filas = db.fetch_all(f"SELECT * FROM `{tabla}`")
                if filas:
                    cols     = list(filas[0].keys())
                    cols_str = ", ".join(f"`{c}`" for c in cols)
                    for i in range(0, len(filas), 100):
                        bloque = filas[i:i+100]
                        vlist  = []
                        for fila in bloque:
                            vals = []
                            for v in fila.values():
                                if v is None:       vals.append("NULL")
                                elif isinstance(v, (int, float)): vals.append(str(v))
                                else:
                                    s = str(v).replace("\\","\\\\").replace("'","\\'")
                                    vals.append(f"'{s}'")
                            vlist.append(f"({', '.join(vals)})")
                        # INSERT IGNORE → nunca falla por duplicados al importar
                        lineas.append(
                            f"INSERT IGNORE INTO `{tabla}` ({cols_str}) VALUES\n"
                            + ",\n".join(vlist) + ";")
                    lineas.append("")
            except Exception as e:
                lineas.append(f"-- ERROR datos {tabla}: {e}"); lineas.append("")

        if callback_progreso: callback_progreso((idx + 1) / total)

    lineas += ["", "SET FOREIGN_KEY_CHECKS = 1;", f"-- Fin del backup — {ahora}", ""]
    return lineas


# ── Motor de restauración ─────────────────────────────────────────────────────
def _ejecutar_restauracion(db, sql_content, modo="reemplazar", callback_progreso=None):
    """
    modo = "reemplazar": TRUNCATE todas las tablas antes de insertar (restauración limpia)
    modo = "agregar":    INSERT IGNORE (agrega sin sobreescribir)
    """
    sentencias = _separar_sentencias(sql_content)
    total      = max(len(sentencias), 1)
    errores    = []
    conn       = db.get_connection()
    cursor     = conn.cursor()

    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        conn.commit()

        if modo == "reemplazar":
            # Paso 1: obtener tablas existentes y limpiarlas
            cursor.execute("SHOW TABLES")
            tablas_existentes = {row[0] for row in cursor.fetchall()}

            # Extraer tablas del SQL que se va a importar
            import re
            tablas_sql = set(re.findall(
                r'(?:INSERT\s+(?:IGNORE\s+)?INTO|REPLACE\s+INTO)\s+`?(\w+)`?',
                sql_content, re.IGNORECASE))

            for tabla in tablas_sql:
                if tabla in tablas_existentes:
                    try:
                        cursor.execute(f"TRUNCATE TABLE `{tabla}`")
                        conn.commit()
                    except Exception:
                        try:
                            cursor.execute(f"DELETE FROM `{tabla}`")
                            conn.commit()
                        except Exception:
                            pass

        # Paso 2: ejecutar todas las sentencias del backup
        for idx, sent in enumerate(sentencias):
            sent = sent.strip()
            if not sent or sent.startswith("--") or sent.startswith("/*"):
                continue
            # En modo reemplazar, convertir INSERT IGNORE → INSERT para que actualice
            if modo == "reemplazar":
                sent_exec = sent.replace(
                    "INSERT IGNORE INTO", "REPLACE INTO"
                ).replace(
                    "INSERT INTO", "REPLACE INTO"
                )
            else:
                # Modo agregar: forzar INSERT IGNORE para no fallar
                sent_exec = sent.replace(
                    "INSERT INTO", "INSERT IGNORE INTO"
                )
            try:
                cursor.execute(sent_exec)
                conn.commit()
            except Exception as e:
                msg = str(e)
                # Ignorar errores no críticos
                ignorar = ["already exists", "Duplicate column", "Can't drop",
                           "doesn't exist", "Duplicate entry", "FOREIGN KEY",
                           "Unknown table", "Table"]
                if not any(x in msg for x in ignorar):
                    errores.append(f"[{idx+1}] {msg[:120]}")

            if callback_progreso and idx % 10 == 0:
                callback_progreso((idx + 1) / total)

    finally:
        try:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            conn.commit()
        except Exception: pass
        cursor.close()

    if callback_progreso: callback_progreso(1.0)
    return errores


def _separar_sentencias(sql):
    sentencias = []; actual = []; en_string = False; char_str = None
    for i, ch in enumerate(sql):
        if en_string:
            actual.append(ch)
            if ch == char_str and (i == 0 or sql[i-1] != "\\"): en_string = False
        elif ch in ("'", '"', "`"):
            en_string = True; char_str = ch; actual.append(ch)
        elif ch == ";":
            s = "".join(actual).strip()
            if s: sentencias.append(s)
            actual = []
        else:
            actual.append(ch)
    resto = "".join(actual).strip()
    if resto: sentencias.append(resto)
    return sentencias
