from fastapi import APIRouter, Depends
from models.schemas import ProjectInput, EstimacionOutput, ConfidenceDetail
from ml.pipeline import predict_effort, R2, MMRE, calc_confidence
from auth.dependencies import get_current_user
from db.models import Usuario
from sqlalchemy.orm import Session
from db.database import get_db
from models.project import Project, EstadoProyecto


router = APIRouter(prefix="/api/v1", tags=["Estimacion"])

@router.post("/estimate", response_model=EstimacionOutput,
    summary="Estimar esfuerzo de un proyecto",
    description="""
Requiere autenticacion (Bearer token). Retorna estimacion en horas-hombre incluyendo:
- Intervalo de confianza basado en MMRE del modelo
- Duracion estimada en dias y semanas
- Top 3 variables SHAP que explican la prediccion
- Proyectos historicos de referencia mas similares
- Confidence Score (1-100)
    """)
def estimate_effort(
    project: ProjectInput,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    esfuerzo, intervalo, esfuerzo_min, esfuerzo_max, shap_top3, referencia, duracion_dias = predict_effort(
        project.tipo_sistema,
        project.tecnologia_principal,
        project.num_modulos,
        project.complejidad,
        project.tamano_equipo_previsto,
        duracion_dias=project.duracion_dias,
        num_tareas=project.num_tareas,
    )

    duracion_semanas = round(duracion_dias / 7, 1)
    horas_semana     = 40 * project.tamano_equipo_previsto
    duracion_por_esfuerzo = round(esfuerzo / horas_semana, 1)

    confidence = calc_confidence(
        r2=R2,
        esfuerzo_horas=esfuerzo,
        duracion_semanas_estimada=duracion_por_esfuerzo,
        presupuesto_maximo=project.presupuesto_maximo_soles,
        deadline_semanas=project.deadline_semanas,
    )

    
    nuevo_proyecto = Project(
        nombre=project.nombre,
        empresa=getattr(project, "empresa", "DIGITAL DYNAMICS"),
        esfuerzo_estimado_horas=esfuerzo,
        estado=EstadoProyecto.estimado,
        sincerado=False,
        created_by=current_user.id  # opcional si tienes relación
    )

    db.add(nuevo_proyecto)
    db.commit()
    db.refresh(nuevo_proyecto)


    return EstimacionOutput(
        esfuerzo_horas=esfuerzo,
        esfuerzo_min=esfuerzo_min,
        esfuerzo_max=esfuerzo_max,
        intervalo_confianza_pct=intervalo,
        duracion_estimada_dias=duracion_dias,
        duracion_estimada_semanas=duracion_semanas,
        modelo_usado="XGBoost",
        mmre_modelo=MMRE,
        r2_modelo=R2,
        shap_top3=shap_top3,
        proyectos_referencia=referencia,
        confidence_score=ConfidenceDetail(**confidence),
    )
