; ─────────────────────────────────────────────────────────────────
;  setup.nsi — Instalador NSIS para Punto de Ventas
;  Requiere: NSIS 3.x instalado en Windows
;  Compilar: makensis setup.nsi
; ─────────────────────────────────────────────────────────────────

!define APP_NAME        "Punto de Ventas"
!define APP_VERSION     "1.0.0"
!define APP_PUBLISHER   "Tu Empresa"
!define APP_EXE         "PuntoDeVentas.exe"
!define INSTALL_DIR     "C:\PuntoDeVentas"
!define MARIADB_ZIP     "mariadb-portable.zip"
!define UNINSTALLER     "Desinstalar.exe"
!define REG_KEY         "Software\Microsoft\Windows\CurrentVersion\Uninstall\PuntoDeVentas"

; ── Configuración general ─────────────────────────────────────────
Name            "${APP_NAME} ${APP_VERSION}"
OutFile         "PuntoDeVentas_Installer.exe"
InstallDir      "${INSTALL_DIR}"
RequestExecutionLevel admin
SetCompressor   lzma

; ── Includes ──────────────────────────────────────────────────────
!include "MUI2.nsh"
!include "nsDialogs.nsh"
!include "LogicLib.nsh"

; ── Páginas del instalador ────────────────────────────────────────
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\README.md"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "Spanish"

; ── Sección principal de instalación ─────────────────────────────
Section "Instalar ${APP_NAME}" SecMain

    SetOutPath "$INSTDIR"

    ; ── Copiar ejecutable principal
    File "..\dist\${APP_EXE}"

    ; ── Copiar schema SQL
    SetOutPath "$INSTDIR\app\database"
    File "..\app\database\schema.sql"

    ; ── Copiar scripts de BD
    SetOutPath "$INSTDIR\installer"
    File "start_db.bat"
    File "stop_db.bat"
    File "init_portable_db.bat"

    ; ── Copiar assets
    SetOutPath "$INSTDIR\assets"
    File /r "..\assets\*.*"

    ; ── Extraer MariaDB portable
    SetOutPath "$INSTDIR"
    DetailPrint "Extrayendo MariaDB portable..."
    File "${MARIADB_ZIP}"
    ; Descomprimir MariaDB usando script PowerShell auxiliar
    DetailPrint "Descomprimiendo MariaDB (esto puede tardar unos minutos)..."
    File "unzip_mariadb.ps1"
    ExecWait 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\unzip_mariadb.ps1" -ZipPath "$INSTDIR\mariadb-portable.zip" -DestPath "$INSTDIR\mariadb"' $0
    ${If} $0 != 0
        MessageBox MB_ICONEXCLAMATION "Error al descomprimir MariaDB. Codigo: $0"
    ${EndIf}
    Delete "$INSTDIR\unzip_mariadb.ps1"
    Delete "$INSTDIR\${MARIADB_ZIP}"

    ; ── Crear carpetas necesarias
    CreateDirectory "$INSTDIR\data"
    CreateDirectory "$INSTDIR\logs"
    CreateDirectory "$INSTDIR\reports"

    ; ── Crear .env con configuración
    FileOpen  $0 "$INSTDIR\.env" w
    FileWrite $0 "DB_HOST=127.0.0.1$\r$\n"
    FileWrite $0 "DB_PORT=3307$\r$\n"
    FileWrite $0 "DB_USER=root$\r$\n"
    FileWrite $0 "DB_PASSWORD=admin123$\r$\n"
    FileWrite $0 "DB_NAME=punto_ventas$\r$\n"
    FileClose $0

    ; ── Inicializar base de datos (primera vez)
    DetailPrint "Inicializando base de datos..."
    ExecWait '"$INSTDIR\installer\init_portable_db.bat"' $0
    ${If} $0 != 0
        MessageBox MB_ICONEXCLAMATION "Advertencia: No se pudo inicializar la base de datos.$\nPuedes hacerlo manualmente ejecutando init_portable_db.bat"
    ${EndIf}

    ; ── Crear acceso directo en Escritorio
    CreateShortcut "$DESKTOP\${APP_NAME}.lnk" \
        "$INSTDIR\${APP_EXE}" "" \
        "$INSTDIR\assets\images\logo.ico" 0

    ; ── Crear acceso directo en Menú Inicio
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" \
        "$INSTDIR\${APP_EXE}" "" \
        "$INSTDIR\assets\images\logo.ico" 0
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\${UNINSTALLER}.lnk" \
        "$INSTDIR\${UNINSTALLER}"

    ; ── Registrar en Agregar/Quitar programas
    WriteRegStr   HKLM "${REG_KEY}" "DisplayName"     "${APP_NAME}"
    WriteRegStr   HKLM "${REG_KEY}" "DisplayVersion"  "${APP_VERSION}"
    WriteRegStr   HKLM "${REG_KEY}" "Publisher"       "${APP_PUBLISHER}"
    WriteRegStr   HKLM "${REG_KEY}" "InstallLocation" "$INSTDIR"
    WriteRegStr   HKLM "${REG_KEY}" "UninstallString" "$INSTDIR\${UNINSTALLER}"
    WriteRegDWORD HKLM "${REG_KEY}" "NoModify"        1
    WriteRegDWORD HKLM "${REG_KEY}" "NoRepair"        1

    ; ── Crear desinstalador
    WriteUninstaller "$INSTDIR\${UNINSTALLER}"

    DetailPrint "Instalacion completada!"
    MessageBox MB_ICONINFORMATION "${APP_NAME} se instalo correctamente.$\n$\nAcceso directo creado en el Escritorio."

SectionEnd

; ── Sección de desinstalación ─────────────────────────────────────
Section "Uninstall"

    ; Detener MariaDB antes de desinstalar
    ExecWait '"$INSTDIR\installer\stop_db.bat"'

    ; Preguntar si borrar datos
    MessageBox MB_YESNO "¿Deseas eliminar también los datos de la base de datos?$\n$\nSi dices NO, tus datos se conservarán en $INSTDIR\data" IDNO KeepData
        RMDir /r "$INSTDIR\data"
    KeepData:

    ; Borrar archivos
    RMDir /r "$INSTDIR\mariadb"
    RMDir /r "$INSTDIR\app"
    RMDir /r "$INSTDIR\assets"
    RMDir /r "$INSTDIR\installer"
    RMDir /r "$INSTDIR\logs"
    RMDir /r "$INSTDIR\reports"
    Delete   "$INSTDIR\${APP_EXE}"
    Delete   "$INSTDIR\.env"
    Delete   "$INSTDIR\${UNINSTALLER}"
    RMDir    "$INSTDIR"

    ; Borrar accesos directos
    Delete "$DESKTOP\${APP_NAME}.lnk"
    RMDir /r "$SMPROGRAMS\${APP_NAME}"

    ; Borrar registro
    DeleteRegKey HKLM "${REG_KEY}"

    MessageBox MB_ICONINFORMATION "${APP_NAME} ha sido desinstalado."

SectionEnd
