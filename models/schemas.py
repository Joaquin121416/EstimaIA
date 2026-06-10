from pydantic import BaseModel, Field, computed_field
from typing import List, Optional

class ProjectInput(BaseModel):
    nombre: str
    tipo_sistema: str = Field(..., description="web | api | mobile | microservices")
    tecnologia_principal: str = Field(..., description="react | fastapi | node | angular | vue | react_native")
    num_modulos: int = Field(..., ge=1, le=50)
    complejidad: int = Field(..., ge=1, le=5)
    tamano_equipo_previsto: int = Field(..., ge=1, le=20)
    # Campos opcionales de Asana / restricciones cliente
    duracion_dias: Optional[int] = Field(None, description="Duración real en días (de Asana start_on → completed_at). Si no se provee, se infiere del histórico.")
    num_tareas: Optional[int] = Field(None, description="Número de tareas en Asana. Si no se provee, se infiere del histórico.")
    presupuesto_maximo_soles: Optional[float] = Field(None, description="Presupuesto máximo del cliente en S/.")
    deadline_semanas: Optional[int] = Field(None, description="Plazo máximo del cliente en semanas.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "nombre": "Portal E-Commerce Retail SA",
                "tipo_sistema": "web",
                "tecnologia_principal": "react",
                "num_modulos": 7,
                "complejidad": 3,
                "tamano_equipo_previsto": 3,
                "duracion_dias": 56,
                "num_tareas": 110,
                "presupuesto_maximo_soles": 8000,
                "deadline_semanas": 10
            }
        }
    }

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

    @computed_field
    @property
    def duracion_semanas_int(self) -> int:
        return max(1, round(self.duracion_semanas))

    model_config = {
        "json_schema_extra": {
            "example": {
                "esfuerzo_estimado_horas": 248,
                "tecnologia_requerida": "react",
                "duracion_semanas": 8
            }
        }
    }

class TeamOutput(BaseModel):
    num_devs_recomendados: int
    equipo: List[DeveloperScore]
    cobertura_skills_pct: float
    balance_carga_desv_pct: float
