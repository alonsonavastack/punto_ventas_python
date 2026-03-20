# 🛠️ Cómo construir el instalador .exe para Windows

## Requisitos (hacer esto UNA SOLA VEZ en Windows)

1. **Python 3.10+** — https://python.org/downloads
2. **NSIS 3.x** — https://nsis.sourceforge.io/Download
3. **MariaDB portable** (ZIP) — https://mariadb.org/download/
   - Seleccionar: Windows → ZIP portable → descargar
   - Renombrar el ZIP a `mariadb-portable.zip`
   - Colocarlo en esta carpeta `installer/`

---

## Pasos para construir

### Paso 1 — Instalar dependencias Python
```cmd
cd "punto de ventas"
pip install -r requirements.txt
pip install pyinstaller
```

### Paso 2 — Generar el .exe de la app
```cmd
python build_windows.py
```
Esto genera `dist/PuntoDeVentas.exe`

### Paso 3 — Compilar el instalador con NSIS
```cmd
cd installer
makensis setup.nsi
```
Esto genera `installer/PuntoDeVentas_Installer.exe`

---

## Resultado final

Un solo archivo: **`PuntoDeVentas_Installer.exe`** (~150MB)

El usuario solo da doble clic y:
1. Se instala en `C:\PuntoDeVentas\`
2. MariaDB se extrae y configura automáticamente
3. La base de datos se crea e importa sola
4. Se crea acceso directo en el Escritorio
5. Listo para usar

---

## Credenciales por defecto

- **Usuario:** admin
- **Contraseña:** admin123

---

## Estructura después de instalar en Windows

```
C:\PuntoDeVentas\
├── PuntoDeVentas.exe       ← La app
├── mariadb\                ← MariaDB portable
├── data\                   ← Datos de la BD (NO borrar)
├── logs\                   ← Logs de MariaDB
├── reports\                ← PDFs generados
├── app\database\schema.sql
├── installer\
│   ├── start_db.bat
│   ├── stop_db.bat
│   └── init_portable_db.bat
└── .env
```
