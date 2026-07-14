from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from db.database import get_db
from db.models import Usuario
from ml import pipeline
from ml.pipeline import predict_effort, calc_confidence
from models.project import EstadoProyecto, Project
from models.schemas import ConfidenceDetail, EstimacionOutput, ProjectInput

router = APIRouter(prefix="/api/v1", tags=["Estimacion"])


@router.post("/estimate", response_model=EstimacionOutput,
    summary="Estimar esfuerzo de un proyecto",
    description="""
Requiere autenticacion (Bearer token). Retorna la estimacion en horas-hombre incluyendo:
- Intervalo de confianza basado en el MMRE del modelo
- Duracion estimada en dias y semanas
- Top 3 variables SHAP que explican la prediccion
- Proyectos historicos de referencia mas similares
- Confidence Score (1-100)

El proyecto queda persistido en BD con estado `estimado`, listo para ser
sincerado luego con su esfuerzo real y alimentar el reentrenamiento (HU-06).
    """)
def estimate_effort(
    project: ProjectInput,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    (esfuerzo, intervalo, esfuerzo_min, esfuerzo_max,
     shap_top3, referencia, duracion_dias) = predict_effort(
        project.tipo_sistema,
        project.tecnologia_principal,
        project.num_modulos,
        project.complejidad,
        project.tamano_equipo_previsto,
        duracion_dias=project.duracion_dias,
        num_tareas=project.num_tareas,
    )

    duracion_semanas = round(duracion_dias / 7, 1)
    horas_semana = 40 * project.tamano_equipo_previsto
    duracion_por_esfuerzo = round(esfuerzo / horas_semana, 1)

    confidence = calc_confidence(
        r2=pipeline.R2,
        esfuerzo_horas=esfuerzo,
        duracion_semanas_estimada=duracion_por_esfuerzo,
        presupuesto_maximo=project.presupuesto_maximo_soles,
        deadline_semanas=project.deadline_semanas,
    )

    # Nro de tareas usado por el modelo (el del input, o el inferido por vecinos)
    num_tareas_usado = project.num_tareas or pipeline.estimate_num_tareas(
        project.num_modulos, project.complejidad
    )

    # Persistir el proyecto con TODAS sus features -> habilita el reentrenamiento
    nuevo = Project(
        nombre=project.nombre,
        empresa=getattr(project, "empresa", None) or "DIGITAL DYNAMICS",
        tipo_sistema=project.tipo_sistema,
        tecnologia_principal=project.tecnologia_principal,
        num_modulos=project.num_modulos,
        complejidad=project.complejidad,
        tamano_equipo=project.tamano_equipo_previsto,
        num_tareas_asana=num_tareas_usado,
        duracion_estimada_dias=duracion_dias,
        start_on=date.today(),
        esfuerzo_estimado_horas=esfuerzo,
        estado=EstadoProyecto.estimado,
        sincerado=False,
        incluir_en_training=True,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return EstimacionOutput(
        proyecto_id=nuevo.id,
        esfuerzo_horas=esfuerzo,
        esfuerzo_min=esfuerzo_min,
        esfuerzo_max=esfuerzo_max,
        intervalo_confianza_pct=intervalo,
        duracion_estimada_dias=duracion_dias,
        duracion_estimada_semanas=duracion_semanas,
        modelo_usado="XGBoost",
        mmre_modelo=pipeline.MMRE,
        r2_modelo=pipeline.R2,
        shap_top3=shap_top3,
        proyectos_referencia=referencia,
        confidence_score=ConfidenceDetail(**confidence),
    )
