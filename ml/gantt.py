"""
Generador de cronograma Gantt a partir de una estimacion.

1. Reparte el esfuerzo total (horas) entre fases y tareas segun porcentajes de
   referencia de la industria, ajustados por las variables del proyecto.
2. Calcula la duracion de cada tarea en dias habiles segun las personas asignadas.
3. Programa las tareas por dependencias (los modulos de desarrollo se reparten
   en carriles paralelos segun el tamano del equipo).
4. Escala el cronograma para que su duracion total coincida con la duracion
   estimada del proyecto, y calcula la ruta critica.
Solo se consideran dias habiles (lunes a viernes).
"""
from datetime import date, timedelta
from typing import Dict, List, Optional

HORAS_PRODUCTIVAS_DIA = 6.0


# --- Utilidades de calendario --------------------------------------------------

def _siguiente_habil(d: date) -> date:
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def _sumar_habiles(inicio: date, n: int) -> date:
    """Fecha del dia habil numero n (0 = inicio)."""
    d = _siguiente_habil(inicio)
    while n > 0:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


# --- Construccion de tareas ----------------------------------------------------

def _distribucion(tipo_sistema, claridad, num_integraciones, nivel_seguridad,
                  pruebas_automatizadas, documentacion) -> Dict[str, float]:
    p = {
        "gestion": 0.06, "inicio": 0.03, "requisitos": 0.09, "arquitectura": 0.05,
        "uiux": 0.05, "entorno": 0.03, "desarrollo": 0.47, "integraciones": 0.0,
        "seguridad": 0.0, "qa": 0.12, "uat": 0.03, "despliegue": 0.03,
        "documentacion": 0.02, "cierre": 0.01,
    }
    if tipo_sistema == "api":
        p["uiux"] = 0.0
        p["arquitectura"] += 0.02
    if claridad is not None and claridad <= 2:
        p["requisitos"] += 0.03
    if num_integraciones:
        p["integraciones"] = min(0.03 * num_integraciones, 0.12)
    if nivel_seguridad == "medio":
        p["seguridad"] = 0.03
    elif nivel_seguridad == "alto":
        p["seguridad"] = 0.06
    if pruebas_automatizadas:
        p["qa"] += 0.03
    if documentacion == "estandar":
        p["documentacion"] = 0.04
    elif documentacion == "exhaustiva":
        p["documentacion"] = 0.06
    total = sum(p.values())
    return {k: v / total for k, v in p.items()}


def _construir_tareas(esfuerzo, num_modulos, tamano_equipo, tipo_sistema, metodologia,
                      claridad, num_integraciones, nivel_seguridad,
                      pruebas_automatizadas, documentacion, nombres_modulos):
    dist = _distribucion(tipo_sistema, claridad, num_integraciones, nivel_seguridad,
                         pruebas_automatizadas, documentacion)
    h = {k: esfuerzo * v for k, v in dist.items()}
    n = tamano_equipo
    agil = metodologia in (None, "scrum", "kanban", "hibrido")
    tareas: List[Dict] = []

    def add(id_, nombre, fase, horas, personas, rol, deps, tipo="tarea"):
        tareas.append({
            "id": id_, "nombre": nombre, "fase": fase, "tipo": tipo,
            "horas": round(horas, 0), "personas": round(personas, 1), "rol": rol,
            "dependencias": deps,
        })

    # 1. Inicio y planificacion
    add("1.1", "Kick-off y plan del proyecto", "Inicio", h["inicio"], min(2, n),
        "Jefe de proyecto", [])
    add("H1", "Plan aprobado", "Inicio", 0, 0, "Jefe de proyecto", ["1.1"], "hito")

    # 2. Analisis
    add("2.1", "Levantamiento de requisitos", "Analisis", h["requisitos"] * 0.6, min(2, n),
        "Analista funcional", ["H1"])
    add("2.2", "Historias de usuario y criterios de aceptacion", "Analisis",
        h["requisitos"] * 0.4, min(2, n), "Analista funcional", ["2.1"])
    add("H2", "Requisitos aprobados", "Analisis", 0, 0, "Cliente", ["2.2"], "hito")

    # 3. Diseno
    diseno = []
    add("3.1", "Arquitectura y modelo de datos", "Diseno", h["arquitectura"], 1,
        "Arquitecto / Tech Lead", ["H2"])
    diseno.append("3.1")
    if h["uiux"] > 0:
        add("3.2", "Diseno UI/UX y prototipos", "Diseno", h["uiux"], 1,
            "Disenador UI/UX", ["H2"])
        diseno.append("3.2")
    add("H3", "Diseno aprobado", "Diseno", 0, 0, "Cliente", diseno, "hito")

    # 4. Desarrollo
    add("4.0", "Configuracion de entornos y CI/CD", "Desarrollo", h["entorno"], 1,
        "DevOps", ["3.1"])
    carriles = max(1, min(num_modulos, n))
    personas_modulo = max(1.0, n / carriles)
    horas_modulo = h["desarrollo"] / num_modulos
    qa_modulo_total = h["qa"] * 0.4 if agil else 0.0
    ultimo_carril: List[Optional[str]] = [None] * carriles
    fin_qa_modulos: List[str] = []
    qa_previa = None
    for i in range(num_modulos):
        nombre_mod = (nombres_modulos[i] if nombres_modulos and i < len(nombres_modulos)
                      and nombres_modulos[i].strip() else f"Modulo {i + 1}")
        carril = i % carriles
        id_ = f"4.{i + 1}"
        deps = ["H3", "4.0"]
        if ultimo_carril[carril]:
            deps.append(ultimo_carril[carril])
        etiqueta = f"Sprint {i // carriles + 1} - " if metodologia == "scrum" else ""
        add(id_, f"{etiqueta}Desarrollo: {nombre_mod}", "Desarrollo", horas_modulo,
            personas_modulo, "Desarrolladores", deps)
        ultimo_carril[carril] = id_
        if agil:
            qid = f"4.{i + 1}.q"
            qdeps = [id_] + ([qa_previa] if qa_previa else [])
            add(qid, f"Pruebas: {nombre_mod}", "Desarrollo", qa_modulo_total / num_modulos,
                1, "QA", qdeps)
            qa_previa = qid
            fin_qa_modulos.append(qid)
    fin_desarrollo = [c for c in ultimo_carril if c]
    add("H4", "Desarrollo completado", "Desarrollo", 0, 0, "Tech Lead",
        fin_desarrollo, "hito")

    # 5. Pruebas e integracion
    previas_qa = ["H4"] + fin_qa_modulos[-1:]
    if h["integraciones"] > 0:
        add("5.1", f"Integracion con sistemas externos ({num_integraciones})", "Pruebas",
            h["integraciones"], min(2, n), "Desarrolladores", ["H4"])
        previas_qa.append("5.1")
    if h["seguridad"] > 0:
        add("5.2", "Seguridad: hardening y pruebas de vulnerabilidades", "Pruebas",
            h["seguridad"], 1, "Especialista de seguridad", ["H4"])
        previas_qa.append("5.2")
    nombre_qa = "Pruebas de sistema e integracion"
    if pruebas_automatizadas:
        nombre_qa += " (suite automatizada)"
    add("5.3", nombre_qa, "Pruebas", h["qa"] - qa_modulo_total, max(1, min(2, n)),
        "QA", previas_qa)
    add("5.4", "Pruebas de aceptacion (UAT) con el cliente", "Pruebas", h["uat"], 1,
        "Analista funcional", ["5.3"])
    add("H5", "Conformidad del cliente", "Pruebas", 0, 0, "Cliente", ["5.4"], "hito")

    # 6. Despliegue
    add("6.1", "Preparacion de produccion y migracion de datos", "Despliegue",
        h["despliegue"] * 0.5, 1, "DevOps", ["5.3"])
    add("6.2", "Despliegue y puesta en marcha", "Despliegue", h["despliegue"] * 0.5, 1,
        "DevOps", ["6.1", "H5"])
    add("H6", "Go-live", "Despliegue", 0, 0, "Jefe de proyecto", ["6.2"], "hito")

    # 7. Cierre
    add("7.1", "Documentacion tecnica, manuales y capacitacion", "Cierre",
        h["documentacion"], 1, "Analista funcional", ["5.4"])
    add("7.2", "Cierre del proyecto y lecciones aprendidas", "Cierre", h["cierre"], 1,
        "Jefe de proyecto", ["H6", "7.1"])
    add("H7", "Proyecto cerrado", "Cierre", 0, 0, "Jefe de proyecto", ["7.2"], "hito")

    gestion_horas = h["gestion"]
    return tareas, gestion_horas


# --- Programacion --------------------------------------------------------------

def _programar(tareas: List[Dict], duraciones: Dict[str, int]) -> int:
    por_id = {t["id"]: t for t in tareas}
    for t in tareas:  # las tareas ya vienen en orden topologico
        t["_es"] = max((por_id[d]["_ef"] for d in t["dependencias"]), default=0)
        t["_ef"] = t["_es"] + duraciones[t["id"]]
    return max(t["_ef"] for t in tareas)


def _ruta_critica(tareas: List[Dict], duraciones: Dict[str, int], fin: int) -> None:
    sucesores: Dict[str, List[str]] = {t["id"]: [] for t in tareas}
    for t in tareas:
        for d in t["dependencias"]:
            sucesores[d].append(t["id"])
    por_id = {t["id"]: t for t in tareas}
    for t in reversed(tareas):
        t["_lf"] = min((por_id[s]["_lf"] - duraciones[s] for s in sucesores[t["id"]]),
                       default=fin)
    for t in tareas:
        holgura = t["_lf"] - t["_ef"]
        t["holgura_dias"] = holgura
        t["critica"] = holgura == 0


def generar_gantt(
    esfuerzo_horas: float,
    duracion_dias: int,
    num_modulos: int,
    tamano_equipo: int,
    tipo_sistema: str,
    metodologia: Optional[str] = None,
    claridad_requisitos: Optional[int] = None,
    num_integraciones: Optional[int] = None,
    nivel_seguridad: Optional[str] = None,
    pruebas_automatizadas: Optional[bool] = None,
    documentacion: Optional[str] = None,
    nombres_modulos: Optional[List[str]] = None,
    fecha_inicio: Optional[date] = None,
) -> Dict:
    inicio = _siguiente_habil(fecha_inicio or date.today())
    tareas, gestion_horas = _construir_tareas(
        esfuerzo_horas, num_modulos, tamano_equipo, tipo_sistema, metodologia,
        claridad_requisitos, num_integraciones, nivel_seguridad,
        pruebas_automatizadas, documentacion, nombres_modulos,
    )

    # Duracion "natural" segun esfuerzo y personas asignadas
    natural = {
        t["id"]: (0.0 if t["tipo"] == "hito"
                  else t["horas"] / (HORAS_PRODUCTIVAS_DIA * max(t["personas"], 1)))
        for t in tareas
    }
    dur = {k: (0 if v == 0 and k.startswith("H") else max(1, round(v))) for k, v in natural.items()}
    fin_natural = _programar(tareas, dur)

    # Escalar a la duracion estimada (dias calendario -> dias habiles)
    objetivo = max(5, round(duracion_dias * 5 / 7))
    escala = objetivo / fin_natural if fin_natural else 1
    dur = {k: (0 if dur[k] == 0 else max(1, round(natural[k] * escala))) for k in natural}
    fin = _programar(tareas, dur)
    _ruta_critica(tareas, dur, fin)

    salida = []
    # Gestion del proyecto: transversal a todo el cronograma
    salida.append({
        "id": "0", "nombre": "Gestion y seguimiento del proyecto", "fase": "Gestion",
        "tipo": "tarea", "horas": round(gestion_horas, 0), "personas": 1,
        "rol": "Jefe de proyecto", "dependencias": [],
        "inicio": inicio.isoformat(), "fin": _sumar_habiles(inicio, fin - 1).isoformat(),
        "dia_inicio": 0, "duracion_dias": fin, "holgura_dias": 0, "critica": False,
    })
    for t in tareas:
        dias = dur[t["id"]]
        f_ini = _sumar_habiles(inicio, t["_es"])
        if dias:
            f_fin = _sumar_habiles(inicio, t["_es"] + dias - 1)
        else:
            # Un hito ocurre el mismo dia en que termina su ultima tarea previa
            f_ini = f_fin = _sumar_habiles(inicio, max(t["_es"] - 1, 0))
        salida.append({
            "id": t["id"], "nombre": t["nombre"], "fase": t["fase"], "tipo": t["tipo"],
            "horas": t["horas"], "personas": t["personas"], "rol": t["rol"],
            "dependencias": t["dependencias"],
            "inicio": f_ini.isoformat(), "fin": f_fin.isoformat(),
            "dia_inicio": t["_es"], "duracion_dias": dias,
            "holgura_dias": t["holgura_dias"], "critica": t["critica"],
        })

    fecha_fin = _sumar_habiles(inicio, fin - 1)
    fases = []
    for fase in ["Inicio", "Analisis", "Diseno", "Desarrollo", "Pruebas", "Despliegue", "Cierre"]:
        items = [s for s in salida if s["fase"] == fase]
        if not items:
            continue
        fases.append({
            "nombre": fase,
            "inicio": min(s["inicio"] for s in items),
            "fin": max(s["fin"] for s in items),
            "horas": round(sum(s["horas"] for s in items), 0),
        })

    return {
        "fecha_inicio": inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat(),
        "dias_habiles": fin,
        "dias_calendario": (fecha_fin - inicio).days + 1,
        "carriles_desarrollo": max(1, min(num_modulos, tamano_equipo)),
        "fases": fases,
        "tareas": salida,
        "ruta_critica": [s["id"] for s in salida if s["critica"]],
    }
