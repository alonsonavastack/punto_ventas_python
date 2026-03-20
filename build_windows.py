# ─────────────────────────────────────────────────────────────────
#  build_windows.py — Empaqueta la app con PyInstaller
#  Ejecutar desde Windows en la carpeta del proyecto:
#  python build_windows.py
# ─────────────────────────────────────────────────────────────────
import subprocess
import sys
import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")
APP_NAME = "PuntoDeVentas"

def limpiar():
    print("[1/4] Limpiando builds anteriores...")
    for d in [DIST_DIR, BUILD_DIR]:
        if os.path.exists(d):
            shutil.rmtree(d)
    spec = os.path.join(BASE_DIR, f"{APP_NAME}.spec")
    if os.path.exists(spec):
        os.remove(spec)
    print("      OK")

def instalar_pyinstaller():
    print("[2/4] Verificando PyInstaller...")
    try:
        import PyInstaller
        print(f"      PyInstaller {PyInstaller.__version__} OK")
    except ImportError:
        print("      Instalando PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def construir():
    print("[3/4] Construyendo ejecutable...")

    # Rutas de datos adicionales a incluir
    datas = [
        ("assets",          "assets"),
        ("app",             "app"),
        (".env.example",    "."),
    ]

    # Incluir archivos de localizacion de mysql-connector-python
    import mysql.connector
    mysql_pkg_dir = os.path.dirname(mysql.connector.__file__)
    # charsets y localization
    for share_name in ["charsets.xml", "errmsg.sys"]:
        share_path = os.path.join(mysql_pkg_dir, share_name)
        if os.path.exists(share_path):
            datas.append((share_path, "mysql/connector"))
    # Carpeta localization completa si existe
    localization_dir = os.path.join(mysql_pkg_dir, "locales")
    if os.path.exists(localization_dir):
        datas.append((localization_dir, "mysql/connector/locales"))

    # Construir argumento --add-data
    add_data_args = []
    sep = ";" if sys.platform == "win32" else ":"
    for src, dst in datas:
        src_path = os.path.join(BASE_DIR, src)
        if os.path.exists(src_path):
            add_data_args += ["--add-data", f"{src_path}{sep}{dst}"]

    # Icono (si existe)
    icon_path = os.path.join(BASE_DIR, "assets", "images", "logo.png")
    icon_args = []
    if os.path.exists(icon_path):
        # PyInstaller en Windows necesita .ico
        ico_path = os.path.join(BASE_DIR, "assets", "images", "logo.ico")
        if os.path.exists(ico_path):
            icon_args = ["--icon", ico_path]

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name",        APP_NAME,
        "--onefile",                        # Un solo .exe
        "--windowed",                       # Sin ventana de consola
        "--clean",
        "--noconfirm",
        # Imports ocultos necesarios
        "--hidden-import", "customtkinter",
        "--hidden-import", "mysql.connector",
        "--hidden-import", "PIL._tkinter_finder",
        "--hidden-import", "reportlab",
        "--hidden-import", "dotenv",
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.ttk",
        "--hidden-import", "mysql.connector.locales",
        "--hidden-import", "mysql.connector.locales.eng",
        "--hidden-import", "mysql.connector.plugins",
        "--hidden-import", "mysql.connector.plugins.mysql_native_password",
        "--hidden-import", "cv2",
        "--hidden-import", "pyzbar",
        "--hidden-import", "pyzbar.pyzbar",
        # Excluir cosas innecesarias para reducir tamaño
        "--exclude-module", "matplotlib",
        "--exclude-module", "numpy",
        "--exclude-module", "scipy",
        "--exclude-module", "pandas",
    ] + add_data_args + icon_args + [
        os.path.join(BASE_DIR, "main.py"),
    ]

    print("      Ejecutando PyInstaller (puede tardar 2-5 minutos)...")
    result = subprocess.run(cmd, cwd=BASE_DIR)

    if result.returncode != 0:
        print("[ERROR] PyInstaller falló.")
        sys.exit(1)

    exe_path = os.path.join(DIST_DIR, f"{APP_NAME}.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / 1024 / 1024
        print(f"      OK — {exe_path} ({size_mb:.1f} MB)")
    else:
        print("[ERROR] No se generó el .exe")
        sys.exit(1)

def copiar_archivos_extra():
    print("[4/4] Copiando archivos adicionales al dist/...")

    # Copiar schema.sql al dist para que el instalador lo encuentre
    schema_src = os.path.join(BASE_DIR, "app", "database", "schema.sql")
    schema_dst_dir = os.path.join(DIST_DIR, "app", "database")
    os.makedirs(schema_dst_dir, exist_ok=True)
    if os.path.exists(schema_src):
        shutil.copy2(schema_src, schema_dst_dir)
        print(f"      Copiado: schema.sql")

    # Copiar scripts del instalador
    installer_src = os.path.join(BASE_DIR, "installer")
    installer_dst = os.path.join(DIST_DIR, "installer")
    if os.path.exists(installer_src):
        shutil.copytree(installer_src, installer_dst, dirs_exist_ok=True)
        print(f"      Copiado: installer/")

    print("\n✅ Build completado.")
    print(f"   Ejecutable: dist/{APP_NAME}.exe")
    print(f"   Siguiente paso: compilar installer/setup.nsi con NSIS")

if __name__ == "__main__":
    print()
    print("=" * 50)
    print("  Punto de Ventas — Build para Windows")
    print("=" * 50)
    print()
    limpiar()
    instalar_pyinstaller()
    construir()
    copiar_archivos_extra()
    print()
