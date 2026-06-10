from fastapi import APIRouter
import numpy as np
from models.schemas import TeamInput, TeamOutput, DeveloperScore

router = APIRouter(prefix="/api/v1", tags=["Asignacion de Equipo"])

DEVELOPERS = [
    {"id":1, "nombre":"Ana Quispe",       "seniority":"senior", "tecnologias":["react","node","postgresql","docker","typescript"], "disponibilidad_pct":90,  "experiencia_anos":6},
    {"id":2, "nombre":"Carlos Mendoza",   "seniority":"mid",    "tecnologias":["node","postgresql","rest","express"],              "disponibilidad_pct":100, "experiencia_anos":3},
    {"id":3, "nombre":"Lucia Torres",     "seniority":"mid",    "tecnologias":["react","typescript","tailwind","vue"],             "disponibilidad_pct":75,  "experiencia_anos":3},
    {"id":4, "nombre":"Jorge Ramos",      "seniority":"senior", "tecnologias":["fastapi","python","docker","postgresql","shap"],   "disponibilidad_pct":60,  "experiencia_anos":7},
    {"id":5, "nombre":"Maria Paz Flores", "seniority":"junior", "tecnologias":["react","javascript","html","css"],                 "disponibilidad_pct":100, "experiencia_anos":1},
    {"id":6, "nombre":"Diego Paredes",    "seniority":"mid",    "tecnologias":["angular","typescript","net","csharp"],             "disponibilidad_pct":80,  "experiencia_anos":4},
    {"id":7, "nombre":"Valeria Rios",     "seniority":"senior", "tecnologias":["react_native","react","typescript","firebase"],    "disponibilidad_pct":70,  "experiencia_anos":5},
    {"id":8, "nombre":"Andres Castillo",  "seniority":"mid",    "tecnologias":["node","fastapi","python","microservices","docker"],"disponibilidad_pct":90,  "experiencia_anos":4},
    {"id":9, "nombre":"Camila Vega",      "seniority":"junior", "tecnologias":["vue","javascript","node"],                        "disponibilidad_pct":100, "experiencia_anos":2},
    {"id":10,"nombre":"Roberto Salas",    "seniority":"senior", "tecnologias":["angular","java","spring","postgresql"],           "disponibilidad_pct":50,  "experiencia_anos":8},
]

EXP_MAP = {"junior": 0.3, "mid": 0.65, "senior": 1.0}

def calc_score(dev: dict, tech_requerida: str):
    tech_req = tech_requerida.lower()
    skills_match = 1.0 if tech_req in dev["tecnologias"] else (0.6 if any(tech_req in t for t in dev["tecnologias"]) else 0.3)
    exp_score    = EXP_MAP.get(dev["seniority"], 0.5)
    disp_score   = dev["disponibilidad_pct"] / 100
    score_skills = round(0.40 * skills_match, 3)
    score_exp    = round(0.35 * exp_score, 3)
    score_disp   = round(0.25 * disp_score, 3)
    total        = round(score_skills + score_exp + score_disp, 3)
    return total, score_skills, score_exp, score_disp

@router.post("/assign-team", response_model=TeamOutput,
    summary="Recomendar equipo optimo para un proyecto",
    description="Dado el esfuerzo estimado, tecnologia y duracion, retorna los N desarrolladores optimos ordenados por score multicriterio (Skills 40% + Experiencia 35% + Disponibilidad 25%).")
def assign_team(data: TeamInput):
    horas_semana = 40
    duracion = max(1, round(float(data.duracion_semanas)))
    n_devs = max(1, round(float(data.esfuerzo_estimado_horas) / (horas_semana * duracion)))

    scored = []
    for dev in DEVELOPERS:
        if dev["disponibilidad_pct"] < 20:
            continue
        total, s_skills, s_exp, s_disp = calc_score(dev, data.tecnologia_requerida)
        scored.append(DeveloperScore(
            id=dev["id"], nombre=dev["nombre"], seniority=dev["seniority"],
            score_total=total, score_skills=s_skills,
            score_experiencia=s_exp, score_disponibilidad=s_disp,
            tecnologias=dev["tecnologias"], disponibilidad_pct=dev["disponibilidad_pct"]
        ))

    scored.sort(key=lambda x: x.score_total, reverse=True)
    equipo = scored[:n_devs]

    tech_req_set = {data.tecnologia_requerida.lower()}
    skills_cubiertas = set()
    for d in equipo:
        skills_cubiertas.update(d.tecnologias)
    cobertura = round(len(tech_req_set & skills_cubiertas) / max(len(tech_req_set), 1) * 100, 1)

    disponiblidades = [d.disponibilidad_pct for d in equipo]
    balance_desv = round(float(np.std(disponiblidades)), 1) if len(disponiblidades) > 1 else 0.0

    return TeamOutput(
        num_devs_recomendados=n_devs,
        equipo=equipo,
        cobertura_skills_pct=cobertura,
        balance_carga_desv_pct=balance_desv
    )