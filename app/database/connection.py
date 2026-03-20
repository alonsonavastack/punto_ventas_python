import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
import sys
import threading

# Cargar .env desde la carpeta del .exe (instalado) o del script (dev)
if getattr(sys, 'frozen', False):
    _base = os.path.dirname(sys.executable)
else:
    _base = os.path.dirname(os.path.abspath(__file__))
    _base = os.path.join(_base, '..', '..')  # subir a raiz del proyecto

_env_path = os.path.join(_base, '.env')
load_dotenv(dotenv_path=_env_path)


class Database:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.connection = None
        self._conn_lock = threading.Lock()
        self.connect()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = Database()
        return cls._instance

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv("DB_HOST", "127.0.0.1"),
                port=int(os.getenv("DB_PORT", 3306)),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", "admin123"),
                database=os.getenv("DB_NAME", "punto_ventas"),
                charset="utf8mb4",
                # ─── CLAVE: autocommit=True ───────────────────────────────
                # Con autocommit activado cada query se confirma sola.
                # Cuando necesitemos una transacción explícita simplemente
                # llamamos conn.start_transaction(), hacemos las queries y
                # finalizamos con commit() o rollback(). MySQL Connector no
                # lanza "Transaction already in progress" en este modo.
                autocommit=True,
            )
            if self.connection.is_connected():
                print("[OK] Conexion a MySQL exitosa")
        except Error as e:
            print(f"[ERROR] Conexion a MySQL: {e}")
            self.connection = None

    def get_connection(self):
        with self._conn_lock:
            if self.connection is None or not self.connection.is_connected():
                self.connect()
            return self.connection

    # ── Helpers de uso general ────────────────────────────────────────────

    def execute_query(self, query, params=None):
        """
        Ejecuta un INSERT/UPDATE/DELETE simple (autocommit).
        Devuelve el cursor abierto para que el llamador pueda leer lastrowid.
        El llamador es responsable de cerrar el cursor cuando ya no lo necesite.
        """
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            return cursor
        except Error as e:
            print(f"[ERROR] execute_query: {e}")
            raise e

    def execute_query_safe(self, query, params=None):
        """
        Igual que execute_query pero cierra el cursor automáticamente.
        Usar cuando NO se necesita el cursor de retorno (UPDATE/DELETE simples).
        """
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
        except Error as e:
            print(f"[ERROR] execute_query_safe: {e}")
            raise e
        finally:
            cursor.close()

    def fetch_all(self, query, params=None):
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Error as e:
            print(f"[ERROR] fetch_all: {e}")
            raise e
        finally:
            cursor.close()

    def fetch_one(self, query, params=None):
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchone()
        except Error as e:
            print(f"[ERROR] fetch_one: {e}")
            raise e
        finally:
            cursor.close()

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("[INFO] Conexion cerrada")
