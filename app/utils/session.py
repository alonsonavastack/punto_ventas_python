# app/utils/session.py
# Sesión global del usuario logueado

_usuario_actual = None
_sesion_caja = None

def login(usuario: dict):
    global _usuario_actual
    _usuario_actual = usuario

def logout():
    global _usuario_actual, _sesion_caja
    _usuario_actual = None
    _sesion_caja = None

def get_usuario():
    return _usuario_actual

def esta_logueado():
    return _usuario_actual is not None

def tiene_permiso(clave: str) -> bool:
    if not _usuario_actual:
        return False
    permisos = _usuario_actual.get("permisos", [])
    return clave in permisos

def set_sesion_caja(sesion: dict):
    global _sesion_caja
    _sesion_caja = sesion

def get_sesion_caja():
    return _sesion_caja

def caja_abierta():
    return _sesion_caja is not None and _sesion_caja.get("estado") == "abierta"
