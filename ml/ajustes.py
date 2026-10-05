"""
Factores de ajuste de la estimacion (estilo multiplicadores de esfuerzo COCOMO II).

El modelo XGBoost fue entrenado con el dataset historico de Asana, que NO contiene
estas variables. Por eso no entran como features del modelo: se aplican como
multiplicadores sobre la prediccion base. Cada variable es opcional; si no se envia,
su factor es 1.0 (neutral) y la estimacion queda igual a la del modelo.

Cuando el dataset sincerado tenga suficientes proyectos con estas variables,
podran promoverse a features del modelo en el reentrenamiento.
"""
from typing import Dict, List, Optional

# --- Tablas de multiplicadores -------------------------------------------------

EXPERIENCIA_EQUIPO = {1: 1.25, 2: 1.12, 3: 1.00, 4: 0.92, 5: 0.85}
EXPERIENCIA_LABEL = {1: "Muy baja", 2: "Baja", 3: "Media", 4: "Alta", 5: "Muy alta"}

CLARIDAD_REQUISITOS = {1: 1.20, 2: 1.10, 3: 1.00, 4: 0.95, 5: 0.90}
CLARIDAD_LABEL = {1: "Muy baja", 2: "Baja", 3: "Media", 4: "Alta", 5: "Muy alta"}

METODOLOGIA = {"scrum": 1.00, "kanban": 1.00, "hibrido": 1.03, "cascada": 1.08}
METODOLOGIA_LABEL = {"scrum": "Scrum", "kanban": "Kanban", "hibrido": "Hibrida", "cascada": "Cascada"}

NIVEL_SEGURIDAD = {"bajo": 1.00, "medio": 1.07, "alto": 1.18}

DOCUMENTACION = {"basica": 1.00, "estandar": 1.05, "exhaustiva": 1.12}

FACTOR_MIN, FACTOR_MAX = 0.5, 2.5


def _ajuste(variable: str, valor: str, factor: float, base: float) -> Dict:
    return {
        "variable": variable,
        "valor": valor,
        "factor": round(factor, 3),
        "impacto_pct": round((factor - 1) * 100, 1),
        "impacto_horas": round(base * (factor - 1), 0),
    }


def calcular_ajustes(
    esfuerzo_base: float,
    experiencia_equipo: Optional[int] = None,
    claridad_requisitos: Optional[int] = None,
    metodologia: Optional[str] = None,
    num_integraciones: Optional[int] = None,
    nivel_seguridad: Optional[str] = None,
    reutilizacion_pct: Optional[float] = None,
    documentacion: Optional[str] = None,
    pruebas_automatizadas: Optional[bool] = None,
    plataformas_destino: Optional[int] = None,
) -> (float, List[Dict]):
    """
    Devuelve (factor_total, detalle). impacto_horas de cada variable se calcula
    de forma aislada sobre el esfuerzo base, para que el usuario vea el peso de
    cada una; el factor total es el producto de todos los factores.
    """
    detalle: List[Dict] = []

    if experiencia_equipo is not None:
        f = EXPERIENCIA_EQUIPO[experiencia_equipo]
        detalle.append(_ajuste("Experiencia del equipo", EXPERIENCIA_LABEL[experiencia_equipo], f, esfuerzo_base))

    if claridad_requisitos is not None:
        f = CLARIDAD_REQUISITOS[claridad_requisitos]
        detalle.append(_ajuste("Claridad de requisitos", CLARIDAD_LABEL[claridad_requisitos], f, esfuerzo_base))

    if metodologia is not None:
        f = METODOLOGIA[metodologia]
        detalle.append(_ajuste("Metodologia", METODOLOGIA_LABEL[metodologia], f, esfuerzo_base))

    if num_integraciones:
        f = min(1 + 0.04 * num_integraciones, 1.5)
        detalle.append(_ajuste("Integraciones externas", str(num_integraciones), f, esfuerzo_base))

    if nivel_seguridad is not None:
        f = NIVEL_SEGURIDAD[nivel_seguridad]
        detalle.append(_ajuste("Requisitos de seguridad", nivel_seguridad.capitalize(), f, esfuerzo_base))

    if reutilizacion_pct:
        # Reutilizar codigo no ahorra el 100%: hay que adaptarlo e integrarlo.
        f = 1 - 0.5 * reutilizacion_pct / 100
        detalle.append(_ajuste("Reutilizacion de codigo", f"{reutilizacion_pct:.0f}%", f, esfuerzo_base))

    if documentacion is not None:
        f = DOCUMENTACION[documentacion]
        detalle.append(_ajuste("Documentacion requerida", documentacion.capitalize(), f, esfuerzo_base))

    if pruebas_automatizadas:
        f = 1.06
        detalle.append(_ajuste("Pruebas automatizadas", "Si", f, esfuerzo_base))

    if plataformas_destino and plataformas_destino > 1:
        f = 1 + 0.15 * (plataformas_destino - 1)
        detalle.append(_ajuste("Plataformas destino", str(plataformas_destino), f, esfuerzo_base))

    total = 1.0
    for d in detalle:
        total *= d["factor"]
    total = max(FACTOR_MIN, min(total, FACTOR_MAX))
    return round(total, 3), detalle
