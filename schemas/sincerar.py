# schemas/sincerar.py
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class SincerarRequest(BaseModel):
    """Datos reales de un proyecto terminado."""
    esfuerzo_real_horas: float = Field(..., gt=0, description="Horas-hombre reales")
    completed_at: date = Field(..., description="Fecha real de fin")
    start_on: Optional[date] = Field(None, description="Fecha real de inicio (si cambio)")
    num_tareas_asana: Optional[int] = Field(None, ge=1, description="Tareas reales en Asana")
    incluir_en_training: bool = True


class ProyectoPendiente(BaseModel):
    id: int
    nombre: Optional[str] = None
    empresa: Optional[str] = None
    tipo_sistema: Optional[str] = None
    tecnologia_principal: Optional[str] = None
    num_modulos: Optional[int] = None
    complejidad: Optional[int] = None
    tamano_equipo: Optional[int] = None
    num_tareas_asana: Optional[int] = None
    duracion_estimada_dias: Optional[int] = None
    duracion_real_dias: Optional[int] = None
    start_on: Optional[date] = None
    completed_at: Optional[date] = None
    esfuerzo_estimado_horas: Optional[float] = None
    esfuerzo_real_horas: Optional[float] = None
    estado: Optional[str] = None
    sincerado: Optional[bool] = None
    incluir_en_training: Optional[bool] = None
    fecha_sincerado: Optional[datetime] = None
    sincerado_por: Optional[str] = None
    mmre: Optional[float] = None
    apto_para_training: Optional[bool] = None

    class Config:
        from_attributes = True
