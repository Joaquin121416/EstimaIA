from fastapi import APIRouter
from models.schemas import ProjectInput, EstimacionOutput
from ml.pipeline import predict_effort, R2, MMRE

router = APIRouter(prefix="/api/v1", tags=["Estimacion"])

@router.post(
    "/estimate",
    response_model=EstimacionOutput,
    summary="Estimar esfuerzo de un proyecto",
    description="Recibe los parámetros del proyecto y retorna la estimación en horas-hombre con intervalo de confianza, explicabilidad SHAP y proyectos históricos de referencia."
)
def estimate_effort(project: ProjectInput):
    esfuerzo, intervalo, esfuerzo_min, esfuerzo_max, shap_top3, referencia = predict_effort(
        project.tipo_sistema,
        project.tecnologia_principal,
        project.num_modulos,
        project.complejidad,
        project.tamano_equipo_previsto
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
        proyectos_referencia=referencia
    )
