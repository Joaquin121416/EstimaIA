import math

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
import numpy as np
from models.schemas import TeamInput, TeamOutput, DeveloperScore, ResumenRol
from auth.dependencies import get_current_user
from db.models import Usuario
from data.equipo import COLABORADORES, ROLES, ROL_LABEL, ROL_TIPO, listar_colaboradores
from ml.costos import REPARTO_DEFECTO

router = APIRouter(prefix="/api/v1", tags=["Asignacion de Equipo"])

# Se mantiene el nombre por compatibilidad con codigo que lo importe
DEVELOPERS = COLABORADORES

EXP_MAP = {"junior": 0.3, "mid": 0.65, "senior": 1.0}
HORAS_SEMANA = 40


def calc_score(dev: dict, tech_requerida: str):
    tech_req = tech_requerida.lower()
    if dev.get("rol", "dev") == "dev":
        # Los devs construyen el producto: la tecnologia pesa mucho
        skills_match = 1.0 if tech_req in dev["tecnologias"] else (
            0.6 if any(tech_req in t for t in dev["tecnologias"]) else 0.3)
    else:
        # QA / DevOps / Seguridad son especialistas de su rol; conocer la
        # tecnologia del proyecto es un plus, no un requisito
        skills_match = 1.0 if any(tech_req in t for t in dev["tecnologias"]) else 0.75
    exp_score    = EXP_MAP.get(dev["seniority"], 0.5)
    disp_score   = dev["disponibilidad_pct"] / 100
    score_skills = round(0.40 * skills_match, 3)
    score_exp    = round(0.35 * exp_score, 3)
    score_disp   = round(0.25 * disp_score, 3)
    total        = round(score_skills + score_exp + score_disp, 3)
    return total, score_skills, score_exp, score_disp


def _seleccionar(candidatos: list, horas: float, semanas: float) -> list:
    """
    Toma a los mejores candidatos (por score) hasta cubrir las horas del rol y
    reparte esas horas en proporcion a la capacidad de cada uno.
    - Devs: suelen quedar con alta dedicacion (llevan el proyecto end-to-end).
    - Apoyo: normalmente basta 1 persona con dedicacion parcial.
    """
    if horas <= 0 or not candidatos:
        return []
    elegidos, capacidad = [], 0.0
    for c in candidatos:
        elegidos.append(c)
        capacidad += c["_capacidad"]
        if capacidad >= horas:
            break
    asignados = []
    for c in elegidos:
        h = round(horas * c["_capacidad"] / capacidad, 0) if capacidad else 0
        asignados.append((c, h))
    return asignados


@router.post("/assign-team", response_model=TeamOutput,
    summary="Recomendar equipo optimo para un proyecto",
    description="""
Requiere autenticacion. Arma el equipo por ROL:
- **Desarrolladores (end-to-end):** llevan el proyecto de punta a punta.
- **QA, DevOps y Seguridad (apoyo):** participan con dedicacion parcial segun sus horas.

Envia `horas_por_rol` (sale de `costo.por_rol` de /estimate) para usar el reparto
exacto del cronograma. Cada colaborador devuelve sus horas asignadas, dedicacion,
costo por hora y costo; el equipo devuelve el costo total con tarifas reales.
""")
def assign_team(
    data: TeamInput,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    colaboradores = listar_colaboradores(db, solo_activos=True)
    semanas = max(1.0, float(data.duracion_semanas))
    esfuerzo = float(data.esfuerzo_estimado_horas)
    if data.horas_por_rol:
        horas_rol = {r: float(data.horas_por_rol.get(r, 0) or 0) for r in ROLES}
    else:
        horas_rol = {r: round(esfuerzo * REPARTO_DEFECTO[r], 0) for r in ROLES}

    equipo: list = []
    por_rol: list = []
    for rol in ROLES:
        candidatos = []
        for c in colaboradores:
            if c.get("rol", "dev") != rol or c["disponibilidad_pct"] < 20:
                continue
            total, s_skills, s_exp, s_disp = calc_score(c, data.tecnologia_requerida)
            candidatos.append({**c, "_score": (total, s_skills, s_exp, s_disp),
                               "_capacidad": HORAS_SEMANA * semanas * c["disponibilidad_pct"] / 100})
        candidatos.sort(key=lambda x: x["_score"][0], reverse=True)

        asignados = _seleccionar(candidatos, horas_rol[rol], semanas)
        costo_rol = 0.0
        for c, h in asignados:
            total, s_skills, s_exp, s_disp = c["_score"]
            costo = round(h * c["costo_hora"], 2)
            costo_rol += costo
            equipo.append(DeveloperScore(
                id=c["id"], nombre=c["nombre"], rol=rol, tipo_participacion=ROL_TIPO[rol],
                seniority=c["seniority"],
                score_total=total, score_skills=s_skills,
                score_experiencia=s_exp, score_disponibilidad=s_disp,
                tecnologias=c["tecnologias"], disponibilidad_pct=c["disponibilidad_pct"],
                costo_hora=c["costo_hora"], horas_asignadas=h,
                dedicacion_pct=round(h / (HORAS_SEMANA * semanas) * 100, 1),
                costo=costo,
            ))
        if asignados:
            por_rol.append(ResumenRol(
                rol=rol, rol_label=ROL_LABEL[rol], tipo=ROL_TIPO[rol],
                personas=len(asignados), horas=sum(h for _, h in asignados),
                costo=round(costo_rol, 2),
            ))

    devs = [d for d in equipo if d.rol == "dev"]

    tech_req_set = {data.tecnologia_requerida.lower()}
    skills_cubiertas = set()
    for d in devs:
        skills_cubiertas.update(d.tecnologias)
    cobertura = round(len(tech_req_set & skills_cubiertas) / max(len(tech_req_set), 1) * 100, 1)

    # Balance de carga entre los devs (los de apoyo tienen dedicacion parcial por diseno)
    dedicaciones = [d.dedicacion_pct for d in devs]
    balance_desv = round(float(np.std(dedicaciones)), 1) if len(dedicaciones) > 1 else 0.0

    return TeamOutput(
        num_devs_recomendados=len(devs),
        num_colaboradores=len(equipo),
        equipo=equipo,
        por_rol=por_rol,
        costo_total=round(sum(d.costo for d in equipo), 2),
        cobertura_skills_pct=cobertura,
        balance_carga_desv_pct=balance_desv
    )
