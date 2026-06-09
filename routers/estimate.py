from fastapi import APIRouter
from models.schemas import ProjectInput, EstimacionOutput, ConfidenceDetail
from ml.pipeline import predict_effort, R2, MMRE, calc_confidence

router = APIRouter(prefix="/api/v1", tags=["Estimacion"])

VELOCIDAD_PROMEDIO_HORAS_SEMANA = 40  # horas por dev por semana

@router.post(
    "/estimate",
    response_model=EstimacionOutput,
    summary="Estimar esfuerzo de un proyecto",
    description="""
Retorna estimación en horas-hombre con:
- Intervalo de confianza basado en MMRE del modelo
- Top 3 variables SHAP que explican la predicción
- Proyectos históricos de referencia más similares
- **Confidence Score (1-100)** considerando R² del modelo y restricciones de presupuesto y tiempo del cliente
    """
)
def estimate_effort(project: ProjectInput):
    esfuerzo, intervalo, esfuerzo_min, esfuerzo_max, shap_top3, referencia = predict_effort(
        project.tipo_sistema,
        project.tecnologia_principal,
        project.num_modulos,
        project.complejidad,
        project.tamano_equipo_previsto
    )

    # Duración estimada en semanas
    horas_semana = VELOCIDAD_PROMEDIO_HORAS_SEMANA * project.tamano_equipo_previsto
    duracion_estimada_semanas = round(esfuerzo / horas_semana, 1)

    # Confidence score
    confidence = calc_confidence(
        r2=R2,
        esfuerzo_horas=esfuerzo,
        duracion_semanas_estimada=duracion_estimada_semanas,
        presupuesto_maximo=project.presupuesto_maximo_soles,
        deadline_semanas=project.deadline_semanas
    )

    return EstimacionOutput(
        esfuerzo_horas=esfuerzo,
        esfuerzo_min=esfuerzo_min,
        esfuerzo_max=esfuerzo_max,
        intervalo_confianza_pct=intervalo,
        modelo_usado="XGBoost",
        mmre_modelo=MMRE,
        r2_modelo=R2,
        shap_top3=shap_top3,
        proyectos_referencia=referencia,
        confidence_score=ConfidenceDetail(**confidence)
    )