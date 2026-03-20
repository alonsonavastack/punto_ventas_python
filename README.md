# 🛒 Punto de Ventas — Desktop
**Python + CustomTkinter + MySQL**

---

## 📋 Requisitos previos

- Python 3.10 o superior
- MySQL 8.0 o superior
- MySQL Workbench (para gestión visual de la BD)

---

## 🗂️ Estructura del proyecto

```
punto de ventas/
├── main.py                      # Punto de entrada
├── requirements.txt             # Dependencias Python
├── .env                         # Configuración BD (no subir a git)
│
├── app/
│   ├── database/
│   │   ├── connection.py        # Conexión MySQL singleton
│   │   └── schema.sql           # Script para crear la BD y tablas
│   │
│   ├── models/                  # Lógica de datos (CRUD)
│   │   ├── producto_model.py
│   │   ├── venta_model.py
│   │   ├── cliente_model.py
│   │   └── ...
│   │
│   ├── views/                   # Pantallas de la aplicación
│   │   ├── main_window.py       # Ventana principal + navegación
│   │   ├── ventas_view.py       # Caja / Punto de venta
│   │   ├── inventario_view.py   # Productos e inventario
│   │   ├── clientes_view.py     # Gestión de clientes
│   │   ├── proveedores_view.py  # Gestión de proveedores
│   │   ├── reportes_view.py     # Reportes y estadísticas
│   │   └── config_view.py       # Configuración del negocio
│   │
│   ├── controllers/             # Lógica entre vistas y modelos
│   └── utils/
│       └── config.py            # Colores, fuentes, constantes
│
├── assets/
│   ├── images/
│   └── fonts/
│
└── reports/                     # PDFs generados (tickets, reportes)
```

---

## ⚙️ Instalación paso a paso

### 1. Instalar dependencias Python

```bash
cd "punto de ventas"
pip install -r requirements.txt
```

### 2. Crear la base de datos con MySQL Workbench

1. Abre **MySQL Workbench**
2. Conéctate a tu servidor local (`127.0.0.1`, puerto `3306`)
3. En el menú: **File → Open SQL Script**
4. Selecciona el archivo: `app/database/schema.sql`
5. Presiona **⚡ Execute** (o Ctrl+Shift+Enter)
6. Verifica en el panel izquierdo que aparece la base de datos `punto_ventas` con todas sus tablas

### 3. Configurar la conexión en .env

Abre el archivo `.env` y coloca tu contraseña de MySQL:

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=tu_password_aqui
DB_NAME=punto_ventas
```

### 4. Ejecutar la aplicación

```bash
python main.py
```

**Usuario por defecto:**
- Usuario: `admin`
- Contraseña: `admin123`

---

## 🗄️ Tablas de la base de datos

| Tabla              | Descripción                              |
|--------------------|------------------------------------------|
| `productos`        | Catálogo de productos con precios        |
| `categorias`       | Clasificación de productos               |
| `proveedores`      | Datos de proveedores                     |
| `clientes`         | Clientes (crédito y facturación)         |
| `usuarios`         | Empleados con roles y contraseñas        |
| `ventas`           | Encabezado de cada ticket de venta       |
| `detalle_ventas`   | Renglones de cada venta                  |
| `entradas`         | Recepciones de mercancía / compras       |
| `detalle_entradas` | Renglones de cada entrada de inventario  |
| `caja`             | Movimientos y cortes de caja             |
| `configuracion`    | Parámetros generales del negocio         |

---

## 🔧 MySQL Workbench — Uso diario

| Tarea                        | Cómo hacerlo en Workbench                        |
|------------------------------|--------------------------------------------------|
| Ver productos                | Click en tabla `productos` → icono de tabla      |
| Corregir un precio           | Doble click en la celda → editar → Apply         |
| Respaldar la BD              | Server → Data Export → seleccionar `punto_ventas`|
| Restaurar respaldo           | Server → Data Import                             |
| Ver ventas del día           | Nueva query: `SELECT * FROM ventas WHERE DATE(fecha) = CURDATE();` |

---

## 📦 Dependencias

| Paquete                  | Uso                          |
|--------------------------|------------------------------|
| `customtkinter`          | Interfaz gráfica moderna     |
| `mysql-connector-python` | Conexión a MySQL             |
| `Pillow`                 | Manejo de imágenes           |
| `reportlab`              | Generación de tickets en PDF |
| `python-dotenv`          | Variables de entorno (.env)  |

---

## 🚀 Módulos del sistema

- [x] Estructura base del proyecto
- [x] Conexión a MySQL
- [x] Esquema completo de base de datos
- [x] Ventana principal con navegación
- [ ] Módulo de Ventas / Caja
- [ ] Módulo de Inventario y Productos
- [ ] Módulo de Clientes
- [ ] Módulo de Proveedores
- [ ] Módulo de Reportes
- [ ] Configuración del negocio
- [ ] Impresión de tickets
