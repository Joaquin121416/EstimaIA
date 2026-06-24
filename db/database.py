# db/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Supabase connection string - viene de variable de entorno en Railway
# Formato: postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:JoaNicolas1212%23@db.unpjifazbvexaexdlcbd.supabase.co:5432/postgres")

# Railway/Supabase usan postgres:// pero SQLAlchemy 2.x requiere postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
