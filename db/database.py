# db/database.py
import logging
import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

log = logging.getLogger("estimaia.db")

# Supabase Connection Pooler (IPv4) -> variable de entorno en Railway
# postgresql://postgres.<REF>:<PASS>@aws-<N>-<region>.pooler.supabase.com:6543/postgres
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./estimaia_local.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

IS_SQLITE = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if IS_SQLITE else {"connect_timeout": 10}

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,          # descarta conexiones muertas antes de usarlas
    pool_recycle=1800,           # el pooler de Supabase corta conexiones ociosas
    connect_args=connect_args,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Estado de la conexion, expuesto en /health para diagnosticar sin leer logs
DB_STATUS = {"conectada": False, "error": None, "motor": "sqlite" if IS_SQLITE else "postgresql"}


def _diagnostico(msg: str) -> str:
    """Traduce el error crudo de psycopg2 a una causa accionable."""
    m = msg.lower()
    if "tenant or user not found" in m or "enotfound" in m:
        return ("El pooler no reconoce el proyecto. Causas: (1) el proyecto esta PAUSADO "
                "en Supabase -> restaurarlo; (2) el project ref no coincide; "
                "(3) el host aws-0/aws-1 o la region son incorrectos -> copiar el string "
                "textual desde Supabase > Connect > Transaction pooler.")
    if "password authentication failed" in m:
        return ("El tenant existe pero la contrasena es incorrecta. Revisar DATABASE_URL "
                "(los caracteres especiales deben ir URL-encodeados: # -> %23).")
    if "timeout" in m or "unreachable" in m:
        return "No hay ruta de red al pooler. Verificar host y puerto 6543."
    return "Revisar DATABASE_URL en las variables de Railway."


def init_db() -> bool:
    """
    Crea las tablas si no existen. NO lanza excepcion si la BD no responde:
    la API debe levantar igual para poder diagnosticar y para que el modulo
    de estimacion ML (que no depende de la BD) siga operativo.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        Base.metadata.create_all(bind=engine)
        DB_STATUS.update(conectada=True, error=None)
        log.info("Base de datos conectada correctamente.")
        return True
    except Exception as e:
        detalle = str(e).split("\n")[0][:300]
        DB_STATUS.update(conectada=False, error=detalle, diagnostico=_diagnostico(detalle))
        log.error("FALLO DE CONEXION A LA BD: %s", detalle)
        log.error("Diagnostico: %s", _diagnostico(detalle))
        return False


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
