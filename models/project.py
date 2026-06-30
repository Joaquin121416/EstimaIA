# app/models/project.py
import enum
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, Enum
from app.database import Base

class EstadoProyecto(str, enum.Enum):
    estimado   = "estimado"     # solo tiene predicción
    en_curso   = "en_curso"     # arrancó, aún sin datos reales
    completado = "completado"   # terminó, listo para sincerar

class Project(Base):
    __tablename__ = "projects"

    id                    = Column(Integer, primary_key=True, index=True)
    nombre                = Column(String, nullable=False)
    empresa               = Column(String, nullable=True)

    # --- Features de entrada (las que ya usas en el modelo) ---
    tecnologia_principal  = Column(String, nullable=False)
    num_modulos           = Column(Integer, nullable=False)
    tasks_count           = Column(Integer, nullable=True)   # Asana
    start_on              = Column(Date, nullable=True)       # Asana
    completed_at          = Column(Date, nullable=True)       # Asana

    # --- Target: estimado vs real ---
    esfuerzo_estimado_horas = Column(Float, nullable=True)   # lo que predijo el modelo
    esfuerzo_real_horas     = Column(Float, nullable=True)   # se llena al SINCERAR

    # --- Control del bucle de reentrenamiento ---
    estado              = Column(
        Enum(EstadoProyecto, values_callable=lambda x: [e.value for e in x]),
        default=EstadoProyecto.estimado, nullable=False
    )
    sincerado           = Column(Boolean, default=False, nullable=False)  # validado para training
    incluir_en_training = Column(Boolean, default=True, nullable=False)   # toggle de limpieza
    fecha_sincerado     = Column(DateTime, nullable=True)
    sincerado_por       = Column(String, nullable=True)