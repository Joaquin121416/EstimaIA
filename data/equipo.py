"""
Catalogo de colaboradores de la consultora.

Cada colaborador tiene un ROL:
- dev        : desarrolladores. Ven el proyecto END-TO-END (analisis, diseno,
               desarrollo, integraciones, documentacion, gestion tecnica).
- qa         : apoyo. Pruebas por modulo y pruebas de sistema.
- devops     : apoyo. Entornos, CI/CD, preparacion de produccion y despliegue.
- seguridad  : apoyo. Hardening y pruebas de vulnerabilidades.

costo_hora es el costo por hora del colaborador en soles (S/.).
"""
from typing import Dict, List

ROLES = ["dev", "qa", "devops", "seguridad"]
ROL_LABEL = {"dev": "Desarrollo", "qa": "QA", "devops": "DevOps", "seguridad": "Seguridad"}
# Los devs llevan el proyecto de punta a punta; el resto participa como apoyo.
ROL_TIPO = {"dev": "end_to_end", "qa": "apoyo", "devops": "apoyo", "seguridad": "apoyo"}

# Datos semilla: se cargan a la tabla `colaboradores` la primera vez (seed_colaboradores).
# Despues, la fuente de verdad es la BD (se editan desde el Catalogo).
COLABORADORES: List[Dict] = [
    # --- Desarrolladores (end-to-end) ---
    {"id": 1,  "nombre": "Ana Quispe",       "rol": "dev", "seniority": "senior", "tecnologias": ["react", "node", "postgresql", "docker", "typescript"],   "disponibilidad_pct": 90,  "experiencia_anos": 6, "costo_hora": 34.0, "email": "a.quispe@consultora.pe", "proyectos": ["Portal E-comm Lima Moda", "API Gateway Fintech", "Dashboard Analytics"], "activo": True},
    {"id": 2,  "nombre": "Carlos Mendoza",   "rol": "dev", "seniority": "mid",    "tecnologias": ["node", "postgresql", "rest", "express"],               "disponibilidad_pct": 100, "experiencia_anos": 3, "costo_hora": 23.0, "email": "c.mendoza@consultora.pe", "proyectos": ["API Inventario QROMA", "Microservicio Notif."], "activo": True},
    {"id": 3,  "nombre": "Lucia Torres",     "rol": "dev", "seniority": "mid",    "tecnologias": ["react", "typescript", "tailwind", "vue"],              "disponibilidad_pct": 75,  "experiencia_anos": 3, "costo_hora": 23.0, "email": "l.torres@consultora.pe", "proyectos": ["Catalogo QROMA", "Dashboard KPIs"], "activo": True},
    {"id": 4,  "nombre": "Jorge Ramos",      "rol": "dev", "seniority": "senior", "tecnologias": ["fastapi", "python", "docker", "postgresql", "shap"],    "disponibilidad_pct": 60,  "experiencia_anos": 7, "costo_hora": 36.0, "email": "j.ramos@consultora.pe", "proyectos": ["Motor Scoring ELDO", "API Optimizacion Rutas", "ML Pipeline EstimaIA"], "activo": True},
    {"id": 5,  "nombre": "Maria Paz Flores", "rol": "dev", "seniority": "junior", "tecnologias": ["react", "javascript", "html", "css"],                  "disponibilidad_pct": 100, "experiencia_anos": 1, "costo_hora": 15.0, "email": "m.paz@consultora.pe", "proyectos": ["App Fuerza Ventas"], "activo": True},
    {"id": 6,  "nombre": "Diego Paredes",    "rol": "dev", "seniority": "mid",    "tecnologias": ["angular", "typescript", "net", "csharp"],              "disponibilidad_pct": 80,  "experiencia_anos": 4, "costo_hora": 25.0, "email": "d.paredes@consultora.pe", "proyectos": ["Portal Distribuidores QROMA"], "activo": True},
    {"id": 7,  "nombre": "Valeria Rios",     "rol": "dev", "seniority": "senior", "tecnologias": ["react_native", "react", "typescript", "firebase"],     "disponibilidad_pct": 70,  "experiencia_anos": 5, "costo_hora": 33.0, "email": "v.rios@consultora.pe", "proyectos": ["App Movil ELDO", "App Repartidor LOGIPAQ"], "activo": True},
    {"id": 8,  "nombre": "Andres Castillo",  "rol": "dev", "seniority": "mid",    "tecnologias": ["node", "fastapi", "python", "microservices", "docker"], "disponibilidad_pct": 90,  "experiencia_anos": 4, "costo_hora": 25.0, "email": "a.castillo@consultora.pe", "proyectos": ["Microservicio Facturacion", "API Integracion SAP"], "activo": True},
    {"id": 9,  "nombre": "Camila Vega",      "rol": "dev", "seniority": "junior", "tecnologias": ["vue", "javascript", "node"],                         "disponibilidad_pct": 100, "experiencia_anos": 2, "costo_hora": 16.0, "email": "c.vega@consultora.pe", "proyectos": ["Portal Laboratorio NEXO"], "activo": True},
    {"id": 10, "nombre": "Roberto Salas",    "rol": "dev", "seniority": "senior", "tecnologias": ["angular", "java", "spring", "postgresql"],            "disponibilidad_pct": 50,  "experiencia_anos": 8, "costo_hora": 38.0, "email": "r.salas@consultora.pe", "proyectos": ["HCE NEXO SALUD", "Sistema Pedidos QROMA"], "activo": False},
    # --- QA (apoyo) ---
    {"id": 11, "nombre": "Patricia Huaman",  "rol": "qa", "seniority": "senior", "tecnologias": ["selenium", "cypress", "postman", "jmeter", "react"],    "disponibilidad_pct": 80,  "experiencia_anos": 6, "costo_hora": 26.0, "email": "p.huaman@consultora.pe", "proyectos": ["Portal E-comm Lima Moda", "HCE NEXO SALUD"], "activo": True},
    {"id": 12, "nombre": "Luis Cardenas",    "rol": "qa", "seniority": "mid",    "tecnologias": ["cypress", "playwright", "postman", "jest", "angular"], "disponibilidad_pct": 100, "experiencia_anos": 3, "costo_hora": 20.0, "email": "l.cardenas@consultora.pe", "proyectos": ["Portal Distribuidores QROMA"], "activo": True},
    {"id": 13, "nombre": "Karen Espinoza",   "rol": "qa", "seniority": "junior", "tecnologias": ["pruebas_manuales", "postman", "jira"],               "disponibilidad_pct": 100, "experiencia_anos": 1, "costo_hora": 14.0, "email": "k.espinoza@consultora.pe", "proyectos": ["App Fuerza Ventas"], "activo": True},
    # --- DevOps (apoyo) ---
    {"id": 14, "nombre": "Renzo Villanueva", "rol": "devops", "seniority": "senior", "tecnologias": ["docker", "kubernetes", "aws", "terraform", "github_actions"], "disponibilidad_pct": 60, "experiencia_anos": 7, "costo_hora": 38.0, "email": "r.villanueva@consultora.pe", "proyectos": ["API Gateway Fintech", "Microservicio Facturacion"], "activo": True},
    {"id": 15, "nombre": "Sofia Chavez",     "rol": "devops", "seniority": "mid",    "tecnologias": ["docker", "railway", "azure", "github_actions", "linux"],     "disponibilidad_pct": 90, "experiencia_anos": 4, "costo_hora": 28.0, "email": "s.chavez@consultora.pe", "proyectos": ["ML Pipeline EstimaIA"], "activo": True},
    # --- Seguridad (apoyo) ---
    {"id": 16, "nombre": "Miguel Alarcon",   "rol": "seguridad", "seniority": "senior", "tecnologias": ["owasp", "pentesting", "burp_suite", "iso27001"], "disponibilidad_pct": 50, "experiencia_anos": 8, "costo_hora": 42.0, "email": "m.alarcon@consultora.pe", "proyectos": ["API Gateway Fintech", "HCE NEXO SALUD"], "activo": True},
    {"id": 17, "nombre": "Daniela Rojas",    "rol": "seguridad", "seniority": "mid",    "tecnologias": ["owasp", "sast", "dast", "sonarqube"],          "disponibilidad_pct": 80, "experiencia_anos": 3, "costo_hora": 30.0, "email": "d.rojas@consultora.pe", "proyectos": ["Motor Scoring ELDO"], "activo": True},
]


CAMPOS = ["id", "nombre", "email", "rol", "seniority", "tecnologias", "disponibilidad_pct",
          "experiencia_anos", "costo_hora", "proyectos", "activo"]


def seed_colaboradores(db) -> int:
    """Carga los colaboradores semilla si la tabla esta vacia. Devuelve cuantos inserto."""
    from db.models import Colaborador
    if db.query(Colaborador).count():
        return 0
    for c in COLABORADORES:
        db.add(Colaborador(**{k: c[k] for k in CAMPOS}))
    db.commit()
    # En PostgreSQL, alinear la secuencia del id con los ids insertados a mano
    if db.bind.dialect.name == "postgresql":
        from sqlalchemy import text
        db.execute(text("SELECT setval(pg_get_serial_sequence('colaboradores','id'), "
                        "(SELECT MAX(id) FROM colaboradores))"))
        db.commit()
    return len(COLABORADORES)


def a_dict(c) -> Dict:
    return {k: getattr(c, k) for k in CAMPOS}


def listar_colaboradores(db=None, solo_activos: bool = False) -> List[Dict]:
    """Colaboradores desde la BD; si la BD no responde, usa la lista semilla."""
    datos = None
    if db is not None:
        try:
            from db.models import Colaborador
            datos = [a_dict(c) for c in db.query(Colaborador).order_by(Colaborador.id).all()]
        except Exception:
            # Deja la sesion usable para el resto del request
            try:
                db.rollback()
            except Exception:
                pass
            datos = None
    if not datos:
        datos = [dict(c) for c in COLABORADORES]
    return [c for c in datos if c.get("activo", True)] if solo_activos else datos


def tarifas_promedio(colaboradores: List[Dict] = None) -> Dict[str, float]:
    """Costo por hora promedio de cada rol (S/.), sobre los colaboradores activos."""
    lista = colaboradores if colaboradores is not None else [c for c in COLABORADORES if c.get("activo", True)]
    out = {}
    for rol in ROLES:
        costos = [c["costo_hora"] for c in lista if c["rol"] == rol]
        out[rol] = round(sum(costos) / len(costos), 2) if costos else 0.0
    return out
