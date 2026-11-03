"""
Costo del proyecto en horas-hombre, por rol.

1. Reparte el esfuerzo estimado entre roles a partir de las tareas del Gantt:
   - QA, DevOps y Seguridad solo cuentan las horas de SUS tareas (son apoyo).
   - Todo lo demas (analisis, diseno, desarrollo, integraciones, UAT,
     documentacion, gestion) lo ven los devs, que llevan el proyecto end-to-end.
2. Costo = horas de cada rol x costo por hora del rol (S/.).
   Si el usuario no envia tarifas, se usa el promedio del catalogo de colaboradores.
"""
from typing import Dict, List, Optional

from data.equipo import ROLES, ROL_LABEL, ROL_TIPO, tarifas_promedio

# Rol del Gantt -> rol de colaborador. Lo que no aparece aqui lo hacen los devs.
ROL_GANTT = {
    "QA": "qa",
    "DevOps": "devops",
    "Especialista de seguridad": "seguridad",
}

# Reparto por defecto cuando no hay Gantt (no deberia pasar en /estimate).
REPARTO_DEFECTO = {"dev": 0.82, "qa": 0.13, "devops": 0.05, "seguridad": 0.0}


def rol_de_tarea(rol_gantt: str) -> str:
    return ROL_GANTT.get(rol_gantt, "dev")


def horas_por_rol(esfuerzo_horas: float, gantt: Optional[Dict]) -> Dict[str, float]:
    """Horas-hombre de cada rol. Siempre suman el esfuerzo total."""
    bruto = {r: 0.0 for r in ROLES}
    if gantt and gantt.get("tareas"):
        for t in gantt["tareas"]:
            if t["tipo"] == "hito":
                continue
            bruto[rol_de_tarea(t["rol"])] += t["horas"]
    total = sum(bruto.values())
    reparto = {r: bruto[r] / total for r in ROLES} if total else REPARTO_DEFECTO
    horas = {r: round(esfuerzo_horas * reparto[r], 0) for r in ROLES}
    # El redondeo se lo lleva dev para que la suma cuadre exacto
    horas["dev"] += round(esfuerzo_horas - sum(horas.values()), 0)
    return horas


def calcular_costo(
    esfuerzo_horas: float,
    esfuerzo_min: float,
    esfuerzo_max: float,
    gantt: Optional[Dict],
    tarifas: Optional[Dict[str, float]] = None,
) -> Dict:
    base = tarifas_promedio()
    tarifas_usadas = {r: float((tarifas or {}).get(r) or base[r]) for r in ROLES}
    horas = horas_por_rol(esfuerzo_horas, gantt)

    por_rol: List[Dict] = []
    total = 0.0
    for r in ROLES:
        if horas[r] <= 0:
            continue
        costo = round(horas[r] * tarifas_usadas[r], 2)
        total += costo
        por_rol.append({
            "rol": r,
            "rol_label": ROL_LABEL[r],
            "tipo": ROL_TIPO[r],
            "horas": horas[r],
            "pct": round(horas[r] / esfuerzo_horas * 100, 1) if esfuerzo_horas else 0.0,
            "tarifa_hora": tarifas_usadas[r],
            "costo": costo,
            "tarifa_personalizada": bool(tarifas and tarifas.get(r)),
        })

    total = round(total, 2)
    tarifa_prom = round(total / esfuerzo_horas, 2) if esfuerzo_horas else 0.0
    return {
        "moneda": "PEN",
        "costo_total": total,
        "costo_min": round(esfuerzo_min * tarifa_prom, 2),
        "costo_max": round(esfuerzo_max * tarifa_prom, 2),
        "tarifa_promedio_hora": tarifa_prom,
        "por_rol": por_rol,
    }
