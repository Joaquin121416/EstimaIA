from pydantic import BaseModel, Field
from typing import List, Optional

class ProjectInput(BaseModel):
    nombre: str
    tipo_sistema: str = Field(..., description="web | api | mobile | microservices")
    tecnologia_principal: str = Field(..., description="react | fastapi | node | angular | vue | react_native")
    num_modulos: int = Field(..., ge=1, le=50)
    complejidad: int = Field(..., ge=1, le=5)
    tamano_equipo_previsto: int = Field(..., ge=1, le=20)
    duracion_dias: Optional[int] = Field(None, description="Duracion real en dias")
    num_tareas: Optional[int] = Field(None, description="Numero de tareas en Asana")
    presupuesto_maximo_soles: Optional[float] = Field(None, description="Presupuesto maximo del cliente en S/.")
    deadline_semanas: Optional[int] = Field(None, description="Plazo maximo del cliente en semanas")

class ShapVariable(BaseModel):
    variable: str
    impacto_pct: float

class ProyectoReferencia(BaseModel):
    asana_project_gid: str
    empresa: str
    nombre: str
    tipo_sistema: str
    tecnologia_principal: str
    num_modulos: int
    esfuerzo_real_horas: float
    duracion_real_dias: int
    desvio_pct: float
    similitud_pct: float
    fecha_inicio: str
    fecha_fin_real: str

class ConfidenceDetail(BaseModel):
    score_total: float
    base_modelo: float
    penalizacion_presupuesto: float
    penalizacion_tiempo: float
    mensaje: str

class EstimacionOutput(BaseModel):
    esfuerzo_horas: float
    esfuerzo_min: float
    esfuerzo_max: float
    intervalo_confianza_pct: float
    duracion_estimada_dias: int
    duracion_estimada_semanas: float
    modelo_usado: str
    mmre_modelo: float
    r2_modelo: float
    shap_top3: List[ShapVariable]
    proyectos_referencia: List[ProyectoReferencia]
    confidence_score: ConfidenceDetail

class DeveloperScore(BaseModel):
    id: int
    nombre: str
    seniority: str
    score_total: float
    score_skills: float
    score_experiencia: float
    score_disponibilidad: float
    tecnologias: List[str]
    disponibilidad_pct: float

class TeamInput(BaseModel):
    esfuerzo_estimado_horas: float
    tecnologia_requerida: str
    duracion_semanas: float

class TeamOutput(BaseModel):
    num_devs_recomendados: int
    equipo: List[DeveloperScore]
    cobertura_skills_pct: float
    balance_carga_desv_pct: float
