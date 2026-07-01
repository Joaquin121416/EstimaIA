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
    nombre: str | None = None
    esfuerzo_estimado_horas: float | None = None
    esfuerzo_real_horas: float | None = None
    estado: str | None = None
    sincerado: bool | None = None
    incluir_en_training: bool | None = None
    completed_at: str | None = None

    mmre: float | None = None

    class Config:
        from_attributes = True   # 🔥 ESTO ES LA CLAVE