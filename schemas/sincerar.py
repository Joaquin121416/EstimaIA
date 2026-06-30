# app/schemas/sincerar.py
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field

class SincerarRequest(BaseModel):
    esfuerzo_real_horas: float = Field(..., gt=0, description="Horas reales que tomó")
    completed_at: date
    tasks_count: Optional[int] = None
    incluir_en_training: bool = True

class ProyectoPendiente(BaseModel):
    id: int
    nombre: str
    empresa: Optional[str]
    tecnologia_principal: str
    num_modulos: int
    esfuerzo_estimado_horas: Optional[float]
    esfuerzo_real_horas: Optional[float]
    estado: str
    sincerado: bool
    # error de la estimación, útil para detectar outliers en la pantalla
    mmre: Optional[float] = None

    class Config:
        from_attributes = True