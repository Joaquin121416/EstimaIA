from pydantic import BaseModel, Field
from typing import List, Optional

class ProjectInput(BaseModel):
    nombre: str
    tipo_sistema: str = Field(..., description="web | api | mobile | microservices")
    tecnologia_principal: str = Field(..., description="react | fastapi | node | angular | vue | react_native")
    num_modulos: int = Field(..., ge=1, le=50)
    complejidad: int = Field(..., ge=1, le=5)
    tamano_equipo_previsto: int = Field(..., ge=1, le=20)

    model_config = {
        "json_schema_extra": {
            "example": {
                "nombre": "Portal E-Commerce Retail SA",
                "tipo_sistema": "web",
                "tecnologia_principal": "react",
                "num_modulos": 7,
                "complejidad": 3,
                "tamano_equipo_previsto": 3
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
    desvio_pct: float
    similitud_pct: float

class EstimacionOutput(BaseModel):
    esfuerzo_horas: float
    esfuerzo_min: float
    esfuerzo_max: float
    intervalo_confianza_pct: float
    modelo_usado: str
    mmre_modelo: float
    r2_modelo: float
    shap_top3: List[ShapVariable]
    proyectos_referencia: List[ProyectoReferencia]

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
    duracion_semanas: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "esfuerzo_estimado_horas": 248,
                "tecnologia_requerida": "react",
                "duracion_semanas": 6
            }
        }
    }

class TeamOutput(BaseModel):
    num_devs_recomendados: int
    equipo: List[DeveloperScore]
    cobertura_skills_pct: float
    balance_carga_desv_pct: float
