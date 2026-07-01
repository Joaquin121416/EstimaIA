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
    nombre: Optional[str] = None
    tecnologia_principal: Optional[str] = None
    num_modulos: Optional[int] = None
    esfuerzo_estimado_horas: Optional[float] = None
    esfuerzo_real_horas: Optional[float] = None
    estado: Optional[str] = None
    sincerado: Optional[bool] = None
    incluir_en_training: Optional[bool] = None
    completed_at: Optional[str] = None

    mmre: Optional[float] = None

class Config:
    from_attributes = True
