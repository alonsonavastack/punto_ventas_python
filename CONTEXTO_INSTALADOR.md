# PROMPT DE CONTEXTO — Punto de Ventas Desktop (Windows Installer)

## Contexto del proyecto

Estás ayudando a crear un instalador `.exe` para Windows de una aplicación de **Punto de Ventas Desktop**.

### Stack tecnológico
- **Lenguaje:** Python 3.x
- **GUI:** CustomTkinter
- **Base de datos:** MySQL / MariaDB
- **Dependencias:** `customtkinter`, `mysql-connector-python`, `Pillow`, `reportlab`, `python-dotenv`

### Ubicación del proyecto
```
/Users/codfull-stack/Desktop/punto de ventas/
```

### Estructura del proyecto
```
punto de ventas/
├── main.py                      # Punto de entrada principal
├── requirements.txt             # Dependencias Python
├── arrancar.sh                  # Script de arranque Mac
├── arrancar.bat                 # Script de arranque Windows
├── init_db.py                   # Script que crea la BD
├── .env                         # Credenciales BD (no subir a git)
├── .env.example                 # Plantilla de credenciales
├── .gitignore
├── README.md
├── app/
│   ├── database/
│   │   ├── connection.py        # Conexión MySQL singleton
│   │   └── schema.sql           # Estructura completa de la BD
│   ├── models/                  # Lógica CRUD
│   ├── views/                   # Pantallas CustomTkinter
│   ├── controllers/
│   └── utils/
├── assets/
├── reports/
└── venv/
```

### Credenciales BD (.env)
```
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=admin123
DB_NAME=punto_ventas
```

### Credenciales de acceso al sistema
- Usuario: `admin`
- Contraseña: `admin123`

---

## Lo que se quiere lograr

Crear un **instalador `.exe` para Windows** que:

1. El usuario final solo da doble clic
2. **No requiere** instalar Python, MySQL, XAMPP ni nada manualmente
3. Instala **MariaDB portable** de forma silenciosa
4. Crea la base de datos `punto_ventas` automáticamente
5. Importa el schema (`app/database/schema.sql`)
6. Genera el `.exe` de la app con **PyInstaller**
7. Crea acceso directo en el Escritorio y menú de inicio
8. Incluye opción de desinstalar

### Herramientas a usar
- **PyInstaller** — empaquetar Python a .exe
- **MariaDB portable** — BD sin instalación del usuario
- **NSIS** (Nullsoft Scriptable Install System) — crear el instalador .exe final
- **HeidiSQL** — opcional, para que el admin gestione la BD visualmente

---

## Archivos a crear

### 1. `build_windows.py`
Script que ejecuta PyInstaller para generar `dist/PuntoDeVentas.exe`

### 2. `installer/setup.nsi`
Script NSIS que:
- Extrae MariaDB portable
- Inicia MariaDB
- Importa el schema SQL
- Copia la app
- Crea accesos directos
- Registra desinstalador en Windows

### 3. `installer/start_db.bat`
Arranca MariaDB al iniciar la app

### 4. `installer/stop_db.bat`
Detiene MariaDB al cerrar

### 5. Modificación de `main.py`
Agregar lógica para que al iniciar la app:
- Verifique si MariaDB está corriendo
- Si no, la arranque automáticamente desde la ruta portable

---

## Notas importantes

- MariaDB portable se descarga desde: https://mariadb.org/download/ (ZIP portable para Windows)
- El instalador final debe ser un solo `.exe` de ~100-150MB
- La app debe funcionar sin conexión a internet una vez instalada
- Puerto MySQL: 3307 (para no conflictar con otras instalaciones de MySQL)
- Los datos se guardan en `C:\PuntoDeVentas\data\`
- Logs en `C:\PuntoDeVentas\logs\`

---

## Estado actual

- [ ] `build_windows.py` — por crear
- [ ] `installer/setup.nsi` — por crear  
- [ ] `installer/start_db.bat` — por crear
- [ ] `installer/stop_db.bat` — por crear
- [ ] `installer/init_portable_db.bat` — por crear
- [ ] Modificar `main.py` para detectar MariaDB portable
- [ ] Probar en Windows

## Comando para continuar

Una vez en nueva sesión, lee este archivo y los archivos del proyecto, luego procede a crear todos los archivos listados en "Estado actual".
