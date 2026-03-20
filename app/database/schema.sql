-- ============================================================
--  BASE DE DATOS: punto_ventas
--  Sistema de Punto de Venta - Desktop
-- ============================================================

CREATE DATABASE IF NOT EXISTS punto_ventas
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE punto_ventas;

-- ------------------------------------------------------------
-- CATEGORÍAS DE PRODUCTOS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categorias (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL,
    descripcion VARCHAR(255),
    activo      TINYINT(1) DEFAULT 1,
    creado_en   DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- PROVEEDORES
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS proveedores (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nombre      VARCHAR(150) NOT NULL,
    contacto    VARCHAR(100),
    telefono    VARCHAR(20),
    email       VARCHAR(100),
    direccion   VARCHAR(255),
    rfc         VARCHAR(20),
    activo      TINYINT(1) DEFAULT 1,
    creado_en   DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- PRODUCTOS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS productos (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    codigo_barras   VARCHAR(50) UNIQUE,
    clave_interna   VARCHAR(30),
    nombre          VARCHAR(150) NOT NULL,
    descripcion     VARCHAR(255),
    categoria_id    INT,
    proveedor_id    INT,
    precio_costo    DECIMAL(10,2) DEFAULT 0.00,
    precio_venta    DECIMAL(10,2) NOT NULL,
    precio_mayoreo  DECIMAL(10,2),
    existencia      DECIMAL(10,2) DEFAULT 0,
    existencia_min  DECIMAL(10,2) DEFAULT 0,
    unidad          VARCHAR(20) DEFAULT 'PZA',
    aplica_iva      TINYINT(1) DEFAULT 0,
    activo          TINYINT(1) DEFAULT 1,
    creado_en       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL,
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id) ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- CLIENTES
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clientes (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nombre      VARCHAR(150) NOT NULL,
    telefono    VARCHAR(20),
    email       VARCHAR(100),
    direccion   VARCHAR(255),
    rfc         VARCHAR(20),
    limite_credito DECIMAL(10,2) DEFAULT 0.00,
    saldo_credito  DECIMAL(10,2) DEFAULT 0.00,
    activo      TINYINT(1) DEFAULT 1,
    creado_en   DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- USUARIOS / EMPLEADOS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL,
    usuario     VARCHAR(50) UNIQUE NOT NULL,
    password    VARCHAR(255) NOT NULL,
    rol         ENUM('admin','cajero','almacen') DEFAULT 'cajero',
    activo      TINYINT(1) DEFAULT 1,
    creado_en   DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- VENTAS (encabezado / ticket)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ventas (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    folio           VARCHAR(20) UNIQUE NOT NULL,
    fecha           DATETIME DEFAULT CURRENT_TIMESTAMP,
    cliente_id      INT,
    usuario_id      INT,
    subtotal        DECIMAL(10,2) DEFAULT 0.00,
    descuento       DECIMAL(10,2) DEFAULT 0.00,
    iva             DECIMAL(10,2) DEFAULT 0.00,
    total           DECIMAL(10,2) NOT NULL,
    forma_pago      ENUM('efectivo','tarjeta','transferencia','credito') DEFAULT 'efectivo',
    monto_pagado    DECIMAL(10,2) DEFAULT 0.00,
    cambio          DECIMAL(10,2) DEFAULT 0.00,
    estado          ENUM('completada','cancelada') DEFAULT 'completada',
    notas           TEXT,
    FOREIGN KEY (cliente_id)  REFERENCES clientes(id)  ON DELETE SET NULL,
    FOREIGN KEY (usuario_id)  REFERENCES usuarios(id)  ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- DETALLE DE VENTAS (renglones del ticket)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS detalle_ventas (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    venta_id    INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad    DECIMAL(10,2) NOT NULL,
    precio_unit DECIMAL(10,2) NOT NULL,
    descuento   DECIMAL(10,2) DEFAULT 0.00,
    subtotal    DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (venta_id)    REFERENCES ventas(id)    ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE RESTRICT
);

-- ------------------------------------------------------------
-- ENTRADAS DE INVENTARIO (compras / recepciones)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS entradas (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    folio           VARCHAR(20) UNIQUE NOT NULL,
    fecha           DATETIME DEFAULT CURRENT_TIMESTAMP,
    proveedor_id    INT,
    usuario_id      INT,
    total           DECIMAL(10,2) DEFAULT 0.00,
    notas           TEXT,
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id) ON DELETE SET NULL,
    FOREIGN KEY (usuario_id)   REFERENCES usuarios(id)   ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- DETALLE DE ENTRADAS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS detalle_entradas (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    entrada_id  INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad    DECIMAL(10,2) NOT NULL,
    costo_unit  DECIMAL(10,2) NOT NULL,
    subtotal    DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (entrada_id)  REFERENCES entradas(id)  ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE RESTRICT
);

-- ------------------------------------------------------------
-- CAJA (cortes y movimientos)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS caja (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    fecha           DATETIME DEFAULT CURRENT_TIMESTAMP,
    tipo            ENUM('apertura','cierre','entrada','salida') NOT NULL,
    monto           DECIMAL(10,2) NOT NULL,
    concepto        VARCHAR(255),
    usuario_id      INT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- CONFIGURACIÓN DEL NEGOCIO
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS configuracion (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    clave       VARCHAR(50) UNIQUE NOT NULL,
    valor       TEXT,
    descripcion VARCHAR(255)
);

-- ------------------------------------------------------------
-- DATOS INICIALES
-- ------------------------------------------------------------
INSERT IGNORE INTO configuracion (clave, valor, descripcion) VALUES
('nombre_negocio',  'Mi Tienda',        'Nombre del negocio'),
('direccion',       '',                 'Dirección del negocio'),
('telefono',        '',                 'Teléfono del negocio'),
('rfc',             '',                 'RFC del negocio'),
('iva_porcentaje',  '16',               'Porcentaje de IVA'),
('moneda',          'MXN',              'Moneda');

INSERT IGNORE INTO categorias (nombre) VALUES
('General'), ('Abarrotes'), ('Bebidas'), ('Limpieza'), ('Lácteos');

-- Usuario admin por defecto (password: admin123)
INSERT IGNORE INTO usuarios (nombre, usuario, password, rol) VALUES
('Administrador', 'admin', SHA2('admin123', 256), 'admin');
