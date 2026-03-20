# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\Pc\\Desktop\\punto_ventas\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\Pc\\Desktop\\punto_ventas\\assets', 'assets'), ('C:\\Users\\Pc\\Desktop\\punto_ventas\\app', 'app'), ('C:\\Users\\Pc\\Desktop\\punto_ventas\\.env.example', '.'), ('C:\\Users\\Pc\\Desktop\\punto_ventas\\venv\\Lib\\site-packages\\mysql\\connector\\locales', 'mysql/connector/locales')],
    hiddenimports=['customtkinter', 'mysql.connector', 'PIL._tkinter_finder', 'reportlab', 'dotenv', 'tkinter', 'tkinter.ttk', 'mysql.connector.locales', 'mysql.connector.locales.eng', 'mysql.connector.plugins', 'mysql.connector.plugins.mysql_native_password', 'cv2', 'pyzbar', 'pyzbar.pyzbar'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'scipy', 'pandas'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PuntoDeVentas',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
