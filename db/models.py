# db/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.sql import func
from db.database import Base
import enum

class RolUsuario(str, enum.Enum):
    PM = "pm"
    ADMIN = "admin"

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    rol = Column(SAEnum(RolUsuario, name="rol_usuario"), nullable=False, default=RolUsuario.PM)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
