from datetime import date
from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional

Rol = Literal["dev", "qa", "devops", "seguridad"]

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
    # --- Variables de ajuste (opcionales; ver ml/ajustes.py) ---
    experiencia_equipo: Optional[int] = Field(None, ge=1, le=5, description="1 muy baja ... 5 muy alta")
    claridad_requisitos: Optional[int] = Field(None, ge=1, le=5, description="1 muy baja ... 5 muy alta")
    metodologia: Optional[Literal["scrum", "kanban", "hibrido", "cascada"]] = None
    num_integraciones: Optional[int] = Field(None, ge=0, le=20, description="Sistemas externos a integrar")
    nivel_seguridad: Optional[Literal["bajo", "medio", "alto"]] = None
    reutilizacion_pct: Optional[float] = Field(None, ge=0, le=80, description="% de codigo reutilizable")
    documentacion: Optional[Literal["basica", "estandar", "exhaustiva"]] = None
    pruebas_automatizadas: Optional[bool] = None
    plataformas_destino: Optional[int] = Field(None, ge=1, le=5, description="Web, Android, iOS, escritorio...")
    disponibilidad_equipo_pct: Optional[float] = Field(None, ge=25, le=100, description="Dedicacion del equipo al proyecto")
    # --- Cronograma ---
    fecha_inicio: Optional[date] = Field(None, description="Inicio del proyecto (por defecto hoy)")
    nombres_modulos: Optional[List[str]] = Field(None, description="Nombres de los modulos para el Gantt")
    # --- Costos ---
    tarifas_hora: Optional[Dict[Rol, float]] = Field(
        None, description="Costo por hora (S/.) por rol: dev, qa, devops, seguridad. "
                          "Si falta un rol se usa el promedio del catalogo de colaboradores.")

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

class AjusteVariable(BaseModel):
    variable: str
    valor: str
    factor: float
    impacto_pct: float
    impacto_horas: float

class GanttTarea(BaseModel):
    id: str
    nombre: str
    fase: str
    tipo: str  # tarea | hito
    horas: float
    personas: float
    rol: str
    dependencias: List[str]
    inicio: str
    fin: str
    dia_inicio: int
    duracion_dias: int
    holgura_dias: int
    critica: bool

class GanttFase(BaseModel):
    nombre: str
    inicio: str
    fin: str
    horas: float

class GanttOutput(BaseModel):
    fecha_inicio: str
    fecha_fin: str
    dias_habiles: int
    dias_calendario: int
    carriles_desarrollo: int
    fases: List[GanttFase]
    tareas: List[GanttTarea]
    ruta_critica: List[str]

class CostoRol(BaseModel):
    rol: str                 # dev | qa | devops | seguridad
    rol_label: str
    tipo: str                # end_to_end | apoyo
    horas: float
    pct: float
    tarifa_hora: float
    costo: float
    tarifa_personalizada: bool = False

class CostoProyecto(BaseModel):
    moneda: str = "PEN"
    costo_total: float
    costo_min: float
    costo_max: float
    tarifa_promedio_hora: float
    por_rol: List[CostoRol]

class EstimacionOutput(BaseModel):
    proyecto_id: Optional[int] = None
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
    esfuerzo_base_modelo: Optional[float] = None
    factor_ajuste_total: float = 1.0
    ajustes: List[AjusteVariable] = []
    gantt: Optional[GanttOutput] = None
    costo: Optional[CostoProyecto] = None

class DeveloperScore(BaseModel):
    id: int
    nombre: str
    rol: str = "dev"                  # dev | qa | devops | seguridad
    tipo_participacion: str = "end_to_end"   # end_to_end | apoyo
    seniority: str
    score_total: float
    score_skills: float
    score_experiencia: float
    score_disponibilidad: float
    tecnologias: List[str]
    disponibilidad_pct: float
    costo_hora: float = 0.0
    horas_asignadas: float = 0.0
    dedicacion_pct: float = 0.0       # % de su jornada dedicada a este proyecto
    costo: float = 0.0

class TeamInput(BaseModel):
    esfuerzo_estimado_horas: float
    tecnologia_requerida: str
    duracion_semanas: float
    horas_por_rol: Optional[Dict[Rol, float]] = Field(
        None, description="Horas-hombre por rol (sale de costo.por_rol de /estimate). "
                          "Si no se envia, se reparte con proporciones por defecto.")

class ResumenRol(BaseModel):
    rol: str
    rol_label: str
    tipo: str
    personas: int
    horas: float
    costo: float

class TeamOutput(BaseModel):
    num_devs_recomendados: int
    num_colaboradores: int = 0
    equipo: List[DeveloperScore]
    por_rol: List[ResumenRol] = []
    costo_total: float = 0.0
    cobertura_skills_pct: float
    balance_carga_desv_pct: float


class ColaboradorIn(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    email: Optional[str] = None
    rol: Rol = "dev"
    seniority: Literal["junior", "mid", "senior"] = "mid"
    tecnologias: List[str] = []
    disponibilidad_pct: float = Field(100, ge=0, le=100)
    experiencia_anos: int = Field(0, ge=0, le=50)
    costo_hora: float = Field(..., ge=0, description="Costo por hora en S/.")
    proyectos: List[str] = []
    activo: bool = True

class ColaboradorOut(ColaboradorIn):
    id: int
