# 📋 CHANGELOG — Punto de Ventas

---

## v1.1.0 — Actualización profesional (18 Mar 2026)

### 🛒 Ventas (ventas_view.py)
- **Colores diferenciados para granel**: filas con fondo verde oscuro para fácil identificación visual
- **Badge ⚖** en nombre del producto cuando es a granel
- **Badge ⭐** cuando se ha aplicado precio de mayoreo
- **Indicador de stock**: verde ✓ / naranja ⚠ bajo / rojo ✗ sin stock en columna Stock
- **F11 Mayoreo reversible**: ahora al presionar F11 de nuevo revierte al precio normal
- **Botón "🔄 Limpiar todo"** con confirmación para borrar todo el ticket
- **Leyenda visual** en barra superior: ⚖ Granel / ⭐ Mayoreo / 🔴 Sin stock
- **Contador de granel** en barra inferior (ej: "⚖ 3 a granel")
- **Auto-foco** al campo de código después de cada operación
- **Ticket mejorado**: línea extra en granel mostrando precio/unidad

### 💰 Cobro (widgets/cobro.py)
- **Botones de billetes rápidos**: $10, $20, $50, $100, $200, $500, $1k
- **Botón "✓ Exacto"** para pago sin cambio con un clic
- **Teclado numérico integrado** en la columna derecha (7-8-9, 4-5-6, 1-2-3, ⌫-0-.)
- **Cambio en tiempo real**: muestra "Cambio" en verde o "Faltan" en rojo
- **Indicador de granel** en el encabezado cuando el ticket incluye productos a granel
- **Tamaño ampliado** (600×560) para mejor espacio de trabajo

### 🔍 Búsqueda de productos (widgets/busqueda_producto.py)
- **Columna Mayoreo**: muestra el precio de mayoreo en morado
- **Columna Unidad**: muestra KG, LT, PZA etc. con color especial para granel
- **Badge ⚖** en nombre para productos a granel
- **Badge 🔴** para productos sin stock
- **Stock con colores**: verde / naranja / rojo según nivel
- **Contador de resultados** ("X productos encontrados")
- **Ventana redimensionable** (700×520 mínimo)
- **Doble clic** para seleccionar y agregar directamente

### 🎨 Colores (utils/config.py)
- Nuevos colores: `granel`, `granel_hover`, `stock_ok`, `stock_bajo`, `stock_cero`, `mayoreo`, `mayoreo_hover`
- Versión actualizada a `1.1.0`

---

## v1.0.0 — Versión inicial
- Sistema base con ventas, inventario, caja, reportes, clientes, proveedores
- Soporte básico para productos a granel (peso por diálogo)
- Cierre de caja con desglose de billetes y monedas MXN
