# models/project.py
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, Enum
from db.database import Base


class EstadoProyecto(str, enum.Enum):
    estimado   = "estimado"     # solo tiene prediccion del modelo
    en_curso   = "en_curso"     # arranco, aun sin datos reales
    completado = "completado"   # termino y fue sincerado


class Project(Base):
    """
    Proyecto estimado por el sistema. Guarda TODAS las features de entrada
    para que, al sincerar el esfuerzo real, la fila pueda alimentar el
    reentrenamiento del modelo (HU-06) con el mismo esquema de features
    que el dataset semilla de ml/pipeline.py.
    """
    __tablename__ = "projects"

    id      = Column(Integer, primary_key=True, index=True)
    nombre  = Column(String, nullable=False)
    empresa = Column(String, nullable=True)

    # --- Features de entrada (paridad 1:1 con el dataset semilla) ---
    tipo_sistema         = Column(String,  nullable=True)
    tecnologia_principal = Column(String,  nullable=True)
    num_modulos          = Column(Integer, nullable=True)
    complejidad          = Column(Integer, nullable=True)
    tamano_equipo        = Column(Integer, nullable=True)
    num_tareas_asana     = Column(Integer, nullable=True)

    # --- Fechas / duracion ---
    duracion_estimada_dias = Column(Integer, nullable=True)
    duracion_real_dias     = Column(Integer, nullable=True)   # se llena al SINCERAR
    start_on               = Column(Date,    nullable=True)
    completed_at           = Column(Date,    nullable=True)   # se llena al SINCERAR

    # --- Target: estimado vs real ---
    esfuerzo_estimado_horas = Column(Float, nullable=True)    # lo que predijo el modelo
    esfuerzo_real_horas     = Column(Float, nullable=True)    # se llena al SINCERAR

    # --- Control del bucle de reentrenamiento ---
    estado = Column(
        Enum(EstadoProyecto, name="estado_proyecto",
             values_callable=lambda x: [e.value for e in x]),
        default=EstadoProyecto.estimado, nullable=False,
    )
    sincerado           = Column(Boolean, default=False, nullable=False)
    incluir_en_training = Column(Boolean, default=True,  nullable=False)
    fecha_sincerado     = Column(DateTime, nullable=True)
    sincerado_por       = Column(String,   nullable=True)

    # ------------------------------------------------------------------
    @property
    def mmre(self) -> float | None:
        """Error relativo de la estimacion. Sirve para detectar outliers."""
        if self.esfuerzo_real_horas and self.esfuerzo_estimado_horas:
            return abs(self.esfuerzo_real_horas - self.esfuerzo_estimado_horas) / self.esfuerzo_real_horas
        return None

    @property
    def apto_para_training(self) -> bool:
        """True si la fila tiene todas las features que exige el modelo."""
        return all([
            self.tipo_sistema, self.tecnologia_principal, self.num_modulos,
            self.complejidad, self.tamano_equipo, self.num_tareas_asana,
            self.duracion_real_dias, self.esfuerzo_real_horas,
        ])
