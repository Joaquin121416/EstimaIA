# db/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, JSON, Enum as SAEnum
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
    rol = Column(
        SAEnum(RolUsuario, name="rol_usuario", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=RolUsuario.PM
    )
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

class Colaborador(Base):
    """
    Colaborador de la consultora. rol: dev (end-to-end) | qa | devops | seguridad (apoyo).
    costo_hora en soles. Se siembra desde data/equipo.py la primera vez.
    """
    __tablename__ = "colaboradores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    email = Column(String(150), nullable=True)
    rol = Column(String(20), nullable=False, default="dev")
    seniority = Column(String(20), nullable=False, default="mid")
    tecnologias = Column(JSON, nullable=False, default=list)
    disponibilidad_pct = Column(Float, nullable=False, default=100)
    experiencia_anos = Column(Integer, nullable=False, default=0)
    costo_hora = Column(Float, nullable=False, default=0)
    proyectos = Column(JSON, nullable=False, default=list)
    activo = Column(Boolean, nullable=False, default=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
