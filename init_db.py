#!/usr/bin/env python3
"""
init_db.py — Crea e inicializa la base de datos punto_ventas
Ejecutar: python3 init_db.py
"""

import sys
try:
    import mysql.connector
except ImportError:
    print("[ERROR] Ejecuta: python3 -m pip install mysql-connector-python --user")
    sys.exit(1)

from mysql.connector import Error
import hashlib, os

def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()
def out(msg): print(msg)

CONFIGS = [
    {"host":"127.0.0.1","port":3306,"user":"root","password":"admin123","label":"3306/admin123"},
    {"host":"127.0.0.1","port":3306,"user":"root","password":"root",    "label":"3306/root"},
    {"host":"127.0.0.1","port":3306,"user":"root","password":"",        "label":"3306/sin-pass"},
    {"host":"127.0.0.1","port":8889,"user":"root","password":"root",    "label":"8889/root"},
    {"host":"127.0.0.1","port":8889,"user":"root","password":"admin123","label":"8889/admin123"},
]

out("\n🔍 Detectando MySQL...\n")
cfg_ok = None
for cfg in CONFIGS:
    try:
        c = mysql.connector.connect(host=cfg["host"],port=cfg["port"],
            user=cfg["user"],password=cfg["password"],connection_timeout=2)
        c.close()
        out(f"✅ Conectado → {cfg['label']}")
        cfg_ok = cfg
        break
    except: out(f"  ✗ {cfg['label']}")

if not cfg_ok:
    out("❌ No se pudo conectar. Verifica que MySQL esté activo.")
    sys.exit(1)

with open(os.path.join(os.path.dirname(__file__),".env"),"w") as f:
    f.write(f"DB_HOST={cfg_ok['host']}\nDB_PORT={cfg_ok['port']}\nDB_USER={cfg_ok['user']}\nDB_PASSWORD={cfg_ok['password']}\nDB_NAME=punto_ventas\n")
out("✅ .env actualizado\n")

conn = mysql.connector.connect(host=cfg_ok["host"],port=cfg_ok["port"],
    user=cfg_ok["user"],password=cfg_ok["password"],charset="utf8mb4")
cur = conn.cursor()

out("🗄️  Creando base de datos...")
cur.execute("DROP DATABASE IF EXISTS `punto_ventas`")
cur.execute("CREATE DATABASE `punto_ventas` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
cur.execute("USE `punto_ventas`")
out("✅ BD creada\n")

out("📋 Creando tablas...")

TABLAS = [
("configuracion","""CREATE TABLE configuracion(
    id INT AUTO_INCREMENT PRIMARY KEY,
    clave VARCHAR(50) UNIQUE NOT NULL,
    valor TEXT, descripcion VARCHAR(255))"""),
("permisos_catalogo","""CREATE TABLE permisos_catalogo(
    id INT AUTO_INCREMENT PRIMARY KEY,
    clave VARCHAR(60) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    modulo VARCHAR(60) NOT NULL,
    descripcion VARCHAR(255))"""),
("roles","""CREATE TABLE roles(
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(80) UNIQUE NOT NULL,
    descripcion VARCHAR(255),
    color VARCHAR(20) DEFAULT '#3b82f6',
    activo TINYINT(1) DEFAULT 1,
    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP)"""),
("permisos_roles","""CREATE TABLE permisos_roles(
    id INT AUTO_INCREMENT PRIMARY KEY,
    rol_id INT NOT NULL,
    permiso_clave VARCHAR(60) NOT NULL,
    FOREIGN KEY(rol_id) REFERENCES roles(id) ON DELETE CASCADE,
    UNIQUE KEY uq_rol_perm(rol_id,permiso_clave))"""),
("usuarios","""CREATE TABLE usuarios(
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    usuario VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    rol_id INT,
    activo TINYINT(1) DEFAULT 1,
    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(rol_id) REFERENCES roles(id) ON DELETE SET NULL)"""),
("categorias","""CREATE TABLE categorias(
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(255),
    color VARCHAR(20) DEFAULT '#64748b',
    icono VARCHAR(10) DEFAULT '📦',
    activo TINYINT(1) DEFAULT 1,
    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP)"""),
("proveedores","""CREATE TABLE proveedores(
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    contacto VARCHAR(100), telefono VARCHAR(20),
    email VARCHAR(100), direccion VARCHAR(255), rfc VARCHAR(20),
    activo TINYINT(1) DEFAULT 1,
    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP)"""),
("productos","""CREATE TABLE productos(
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo_barras VARCHAR(50) UNIQUE,
    clave_interna VARCHAR(30),
    nombre VARCHAR(150) NOT NULL,
    descripcion VARCHAR(255),
    categoria_id INT, proveedor_id INT,
    precio_costo DECIMAL(10,2) DEFAULT 0,
    precio_venta DECIMAL(10,2) NOT NULL,
    precio_mayoreo DECIMAL(10,2),
    existencia DECIMAL(10,2) DEFAULT 0,
    existencia_min DECIMAL(10,2) DEFAULT 0,
    unidad VARCHAR(20) DEFAULT 'PZA',
    aplica_iva TINYINT(1) DEFAULT 0,
    activo TINYINT(1) DEFAULT 1,
    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(categoria_id) REFERENCES categorias(id) ON DELETE SET NULL,
    FOREIGN KEY(proveedor_id) REFERENCES proveedores(id) ON DELETE SET NULL)"""),
("clientes","""CREATE TABLE clientes(
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    telefono VARCHAR(20), email VARCHAR(100),
    direccion VARCHAR(255), rfc VARCHAR(20),
    limite_credito DECIMAL(10,2) DEFAULT 0,
    saldo_credito DECIMAL(10,2) DEFAULT 0,
    activo TINYINT(1) DEFAULT 1,
    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP)"""),
("caja_sesiones","""CREATE TABLE caja_sesiones(
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT,
    fecha_apertura DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_cierre DATETIME,
    fondo_inicial DECIMAL(10,2) DEFAULT 0,
    total_efectivo DECIMAL(10,2) DEFAULT 0,
    total_tarjeta DECIMAL(10,2) DEFAULT 0,
    total_transferencia DECIMAL(10,2) DEFAULT 0,
    total_ventas INT DEFAULT 0,
    estado ENUM('abierta','cerrada') DEFAULT 'abierta',
    notas_cierre TEXT,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL)"""),
("caja_movimientos","""CREATE TABLE caja_movimientos(
    id INT AUTO_INCREMENT PRIMARY KEY,
    sesion_id INT NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    tipo ENUM('entrada','salida') NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    concepto VARCHAR(255),
    usuario_id INT,
    FOREIGN KEY(sesion_id) REFERENCES caja_sesiones(id) ON DELETE CASCADE,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL)"""),
("ventas","""CREATE TABLE ventas(
    id INT AUTO_INCREMENT PRIMARY KEY,
    folio VARCHAR(20) UNIQUE NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    cliente_id INT, usuario_id INT, sesion_caja_id INT,
    subtotal DECIMAL(10,2) DEFAULT 0,
    descuento DECIMAL(10,2) DEFAULT 0,
    iva DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(10,2) NOT NULL,
    forma_pago ENUM('efectivo','tarjeta','transferencia','credito') DEFAULT 'efectivo',
    monto_pagado DECIMAL(10,2) DEFAULT 0,
    cambio DECIMAL(10,2) DEFAULT 0,
    estado ENUM('completada','cancelada') DEFAULT 'completada',
    notas TEXT,
    FOREIGN KEY(cliente_id) REFERENCES clientes(id) ON DELETE SET NULL,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL,
    FOREIGN KEY(sesion_caja_id) REFERENCES caja_sesiones(id) ON DELETE SET NULL)"""),
("detalle_ventas","""CREATE TABLE detalle_ventas(
    id INT AUTO_INCREMENT PRIMARY KEY,
    venta_id INT NOT NULL, producto_id INT NOT NULL,
    cantidad DECIMAL(10,2) NOT NULL,
    precio_unit DECIMAL(10,2) NOT NULL,
    descuento DECIMAL(10,2) DEFAULT 0,
    subtotal DECIMAL(10,2) NOT NULL,
    FOREIGN KEY(venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
    FOREIGN KEY(producto_id) REFERENCES productos(id) ON DELETE RESTRICT)"""),
("entradas","""CREATE TABLE entradas(
    id INT AUTO_INCREMENT PRIMARY KEY,
    folio VARCHAR(20) UNIQUE NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    proveedor_id INT, usuario_id INT,
    total DECIMAL(10,2) DEFAULT 0, notas TEXT,
    FOREIGN KEY(proveedor_id) REFERENCES proveedores(id) ON DELETE SET NULL,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL)"""),
("detalle_entradas","""CREATE TABLE detalle_entradas(
    id INT AUTO_INCREMENT PRIMARY KEY,
    entrada_id INT NOT NULL, producto_id INT NOT NULL,
    cantidad DECIMAL(10,2) NOT NULL,
    costo_unit DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    FOREIGN KEY(entrada_id) REFERENCES entradas(id) ON DELETE CASCADE,
    FOREIGN KEY(producto_id) REFERENCES productos(id) ON DELETE RESTRICT)"""),
]

for nombre, sql in TABLAS:
    try:
        cur.execute(sql)
        out(f"  ✔ {nombre}")
    except Error as e:
        out(f"  ⚠ {nombre}: {e}")
conn.commit()

# ── Datos iniciales ───────────────────────────────────────────────────────────
out("\n📦 Insertando datos iniciales...")

# Configuración
for clave,valor,desc in [
    ("nombre_negocio","Mi Tienda","Nombre del negocio"),
    ("direccion","","Dirección"),("telefono","","Teléfono"),
    ("rfc","","RFC"),("iva_porcentaje","16","IVA %"),("moneda","MXN","Moneda"),
    ("requiere_login","1","Requerir login al iniciar"),
    ("solicitar_fondo_caja","1","Pedir fondo al abrir caja"),
]:
    cur.execute("INSERT IGNORE INTO configuracion(clave,valor,descripcion) VALUES(%s,%s,%s)",(clave,valor,desc))

# Catálogo de permisos
PERMISOS = [
    ("ventas_ver",      "Ver ventas",           "Ventas",       "Ver el módulo de ventas"),
    ("ventas_crear",    "Realizar ventas",       "Ventas",       "Crear nuevas ventas"),
    ("ventas_cancelar", "Cancelar ventas",       "Ventas",       "Cancelar ventas realizadas"),
    ("ventas_descuento","Aplicar descuentos",    "Ventas",       "Aplicar descuentos en venta"),
    ("caja_abrir",      "Abrir caja",            "Caja",         "Abrir sesión de caja"),
    ("caja_cerrar",     "Cerrar caja",           "Caja",         "Cerrar sesión de caja"),
    ("caja_movimientos","Movimientos de caja",   "Caja",         "Entradas y salidas de efectivo"),
    ("inventario_ver",  "Ver inventario",        "Inventario",   "Ver productos e inventario"),
    ("inventario_crear","Agregar productos",     "Inventario",   "Crear nuevos productos"),
    ("inventario_editar","Editar productos",     "Inventario",   "Modificar productos existentes"),
    ("inventario_eliminar","Eliminar productos", "Inventario",   "Dar de baja productos"),
    ("entradas_ver",    "Ver entradas",          "Inventario",   "Ver entradas de mercancía"),
    ("entradas_crear",  "Registrar entradas",    "Inventario",   "Registrar entradas de mercancía"),
    ("clientes_ver",    "Ver clientes",          "Clientes",     "Ver lista de clientes"),
    ("clientes_crear",  "Agregar clientes",      "Clientes",     "Crear nuevos clientes"),
    ("clientes_editar", "Editar clientes",       "Clientes",     "Modificar clientes"),
    ("clientes_eliminar","Eliminar clientes",    "Clientes",     "Dar de baja clientes"),
    ("proveedores_ver", "Ver proveedores",       "Proveedores",  "Ver lista de proveedores"),
    ("proveedores_gestionar","Gestionar proveedores","Proveedores","CRUD de proveedores"),
    ("categorias_ver",  "Ver categorías",        "Catálogos",    "Ver categorías"),
    ("categorias_gestionar","Gestionar categorías","Catálogos",  "CRUD de categorías"),
    ("reportes_ver",    "Ver reportes",          "Reportes",     "Acceder a reportes"),
    ("reportes_exportar","Exportar reportes",    "Reportes",     "Exportar reportes a PDF"),
    ("usuarios_ver",    "Ver usuarios",          "Administración","Ver lista de usuarios"),
    ("usuarios_gestionar","Gestionar usuarios",  "Administración","CRUD de usuarios"),
    ("roles_gestionar", "Gestionar roles",       "Administración","CRUD de roles y permisos"),
    ("config_ver",      "Ver configuración",     "Administración","Ver configuración del sistema"),
    ("config_editar",   "Editar configuración",  "Administración","Modificar configuración"),
]
for clave,nombre,modulo,desc in PERMISOS:
    cur.execute("INSERT IGNORE INTO permisos_catalogo(clave,nombre,modulo,descripcion) VALUES(%s,%s,%s,%s)",
                (clave,nombre,modulo,desc))
out("  ✔ catálogo de permisos (28 permisos)")

# Roles
cur.execute("INSERT IGNORE INTO roles(nombre,descripcion,color) VALUES('Administrador','Acceso total al sistema','#dc2626')")
cur.execute("INSERT IGNORE INTO roles(nombre,descripcion,color) VALUES('Cajero','Solo ventas y caja','#16a34a')")
cur.execute("INSERT IGNORE INTO roles(nombre,descripcion,color) VALUES('Almacenista','Inventario y entradas','#d97706')")
cur.execute("INSERT IGNORE INTO roles(nombre,descripcion,color) VALUES('Supervisor','Todo menos administración','#2563eb')")

cur.execute("SELECT id FROM roles WHERE nombre='Administrador'"); admin_rol = cur.fetchone()[0]
cur.execute("SELECT id FROM roles WHERE nombre='Cajero'");        cajero_rol = cur.fetchone()[0]
cur.execute("SELECT id FROM roles WHERE nombre='Almacenista'");   almacen_rol = cur.fetchone()[0]
cur.execute("SELECT id FROM roles WHERE nombre='Supervisor'");    supervisor_rol = cur.fetchone()[0]

# Permisos por rol
todos = [p[0] for p in PERMISOS]
cajero_perms = ["ventas_ver","ventas_crear","ventas_descuento","caja_abrir","caja_cerrar","caja_movimientos","clientes_ver","clientes_crear"]
almacen_perms = ["inventario_ver","inventario_crear","inventario_editar","entradas_ver","entradas_crear","proveedores_ver","categorias_ver"]
supervisor_perms = [p for p in todos if not p.startswith(("usuarios_","roles_","config_"))]

for rol_id, perms in [(admin_rol,todos),(cajero_rol,cajero_perms),(almacen_rol,almacen_perms),(supervisor_rol,supervisor_perms)]:
    for p in perms:
        cur.execute("INSERT IGNORE INTO permisos_roles(rol_id,permiso_clave) VALUES(%s,%s)",(rol_id,p))
out("  ✔ roles y permisos asignados")

# Usuario admin
cur.execute("SELECT id FROM roles WHERE nombre='Administrador'"); rid = cur.fetchone()[0]
cur.execute("INSERT IGNORE INTO usuarios(nombre,usuario,password,rol_id) VALUES(%s,%s,%s,%s)",
            ("Administrador","admin",hash_password("admin123"),rid))
out("  ✔ usuario admin/admin123")

# Categorías
for nombre,color,icono in [
    ("Abarrotes","#f59e0b","🛒"),("Bebidas","#3b82f6","🥤"),("Lácteos","#ffffff","🥛"),
    ("Limpieza","#10b981","🧹"),("Botanas","#f97316","🍿"),("Dulces","#ec4899","🍬"),
    ("Panadería","#92400e","🍞"),("Frutas y Verduras","#84cc16","🥦"),
    ("Carnes","#dc2626","🥩"),("General","#64748b","📦"),
]:
    cur.execute("INSERT IGNORE INTO categorias(nombre,color,icono) VALUES(%s,%s,%s)",(nombre,color,icono))
out("  ✔ categorías (10)")

for n,c,t in [("Distribuidora ABC","Juan Pérez","55-1234-5678"),
               ("Proveedor XYZ","María López","55-8765-4321"),
               ("Mayoreo del Norte","Carlos Ruiz","81-9000-1111")]:
    cur.execute("INSERT IGNORE INTO proveedores(nombre,contacto,telefono) VALUES(%s,%s,%s)",(n,c,t))

cur.execute("SELECT id FROM categorias WHERE nombre='Abarrotes' LIMIT 1"); cat_ab=cur.fetchone()[0]
cur.execute("SELECT id FROM categorias WHERE nombre='Bebidas' LIMIT 1");   cat_be=cur.fetchone()[0]
cur.execute("SELECT id FROM categorias WHERE nombre='Lácteos' LIMIT 1");   cat_la=cur.fetchone()[0]
cur.execute("SELECT id FROM categorias WHERE nombre='Limpieza' LIMIT 1");  cat_li=cur.fetchone()[0]

for cod,nom,cat,pv,pc,ex in [
    ("7501055300782","Coca-Cola 600ml",cat_be,18.00,12.00,50),
    ("7501055300783","Agua Natural 1L",cat_be,10.00,7.00,40),
    ("7501055300784","Leche Entera 1L",cat_la,22.00,16.00,60),
    ("7501003130228","Arroz 1kg",cat_ab,25.00,18.00,100),
    ("7501003130229","Frijol Negro 1kg",cat_ab,30.00,22.00,80),
    ("7501055300788","Azúcar 1kg",cat_ab,28.00,20.00,90),
    ("7501055300789","Sal 1kg",cat_ab,12.00,8.00,70),
    ("7501055300790","Aceite Vegetal 1L",cat_ab,48.00,35.00,50),
    ("7501055300786","Jabón en Polvo 1kg",cat_li,45.00,32.00,40),
    ("7501055300787","Papel de Baño x4",cat_li,55.00,38.00,30),
]:
    cur.execute("""INSERT IGNORE INTO productos
        (codigo_barras,nombre,categoria_id,precio_venta,precio_costo,existencia,existencia_min,unidad)
        VALUES(%s,%s,%s,%s,%s,%s,5,'PZA')""",(cod,nom,cat,pv,pc,ex))
out("  ✔ productos (10)")

for nom,tel in [("Público General",""),("Ana García","55-1111-2222"),("Roberto Martínez","55-3333-4444")]:
    cur.execute("INSERT IGNORE INTO clientes(nombre,telefono) VALUES(%s,%s)",(nom,tel))
out("  ✔ clientes (3)")

conn.commit()
cur.close()
conn.close()

out(f"""
══════════════════════════════════════════
🎉  BASE DE DATOS LISTA
══════════════════════════════════════════
  Servidor : {cfg_ok['host']}:{cfg_ok['port']}
  BD       : punto_ventas

  👤 admin / admin123  (Administrador)

  Roles creados:
    🔴 Administrador — acceso total
    🟢 Cajero        — ventas y caja
    🟡 Almacenista   — inventario
    🔵 Supervisor    — todo menos admin

▶  python3 main.py
══════════════════════════════════════════
""")
