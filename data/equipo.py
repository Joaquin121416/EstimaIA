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

COLABORADORES: List[Dict] = [
    # --- Desarrolladores (end-to-end) ---
    {"id": 1,  "nombre": "Ana Quispe",       "rol": "dev", "seniority": "senior", "tecnologias": ["react", "node", "postgresql", "docker", "typescript"],   "disponibilidad_pct": 90,  "experiencia_anos": 6, "costo_hora": 34.0},
    {"id": 2,  "nombre": "Carlos Mendoza",   "rol": "dev", "seniority": "mid",    "tecnologias": ["node", "postgresql", "rest", "express"],               "disponibilidad_pct": 100, "experiencia_anos": 3, "costo_hora": 23.0},
    {"id": 3,  "nombre": "Lucia Torres",     "rol": "dev", "seniority": "mid",    "tecnologias": ["react", "typescript", "tailwind", "vue"],              "disponibilidad_pct": 75,  "experiencia_anos": 3, "costo_hora": 23.0},
    {"id": 4,  "nombre": "Jorge Ramos",      "rol": "dev", "seniority": "senior", "tecnologias": ["fastapi", "python", "docker", "postgresql", "shap"],    "disponibilidad_pct": 60,  "experiencia_anos": 7, "costo_hora": 36.0},
    {"id": 5,  "nombre": "Maria Paz Flores", "rol": "dev", "seniority": "junior", "tecnologias": ["react", "javascript", "html", "css"],                  "disponibilidad_pct": 100, "experiencia_anos": 1, "costo_hora": 15.0},
    {"id": 6,  "nombre": "Diego Paredes",    "rol": "dev", "seniority": "mid",    "tecnologias": ["angular", "typescript", "net", "csharp"],              "disponibilidad_pct": 80,  "experiencia_anos": 4, "costo_hora": 25.0},
    {"id": 7,  "nombre": "Valeria Rios",     "rol": "dev", "seniority": "senior", "tecnologias": ["react_native", "react", "typescript", "firebase"],     "disponibilidad_pct": 70,  "experiencia_anos": 5, "costo_hora": 33.0},
    {"id": 8,  "nombre": "Andres Castillo",  "rol": "dev", "seniority": "mid",    "tecnologias": ["node", "fastapi", "python", "microservices", "docker"], "disponibilidad_pct": 90,  "experiencia_anos": 4, "costo_hora": 25.0},
    {"id": 9,  "nombre": "Camila Vega",      "rol": "dev", "seniority": "junior", "tecnologias": ["vue", "javascript", "node"],                         "disponibilidad_pct": 100, "experiencia_anos": 2, "costo_hora": 16.0},
    {"id": 10, "nombre": "Roberto Salas",    "rol": "dev", "seniority": "senior", "tecnologias": ["angular", "java", "spring", "postgresql"],            "disponibilidad_pct": 50,  "experiencia_anos": 8, "costo_hora": 38.0},
    # --- QA (apoyo) ---
    {"id": 11, "nombre": "Patricia Huaman",  "rol": "qa", "seniority": "senior", "tecnologias": ["selenium", "cypress", "postman", "jmeter", "react"],    "disponibilidad_pct": 80,  "experiencia_anos": 6, "costo_hora": 26.0},
    {"id": 12, "nombre": "Luis Cardenas",    "rol": "qa", "seniority": "mid",    "tecnologias": ["cypress", "playwright", "postman", "jest", "angular"], "disponibilidad_pct": 100, "experiencia_anos": 3, "costo_hora": 20.0},
    {"id": 13, "nombre": "Karen Espinoza",   "rol": "qa", "seniority": "junior", "tecnologias": ["pruebas_manuales", "postman", "jira"],               "disponibilidad_pct": 100, "experiencia_anos": 1, "costo_hora": 14.0},
    # --- DevOps (apoyo) ---
    {"id": 14, "nombre": "Renzo Villanueva", "rol": "devops", "seniority": "senior", "tecnologias": ["docker", "kubernetes", "aws", "terraform", "github_actions"], "disponibilidad_pct": 60, "experiencia_anos": 7, "costo_hora": 38.0},
    {"id": 15, "nombre": "Sofia Chavez",     "rol": "devops", "seniority": "mid",    "tecnologias": ["docker", "railway", "azure", "github_actions", "linux"],     "disponibilidad_pct": 90, "experiencia_anos": 4, "costo_hora": 28.0},
    # --- Seguridad (apoyo) ---
    {"id": 16, "nombre": "Miguel Alarcon",   "rol": "seguridad", "seniority": "senior", "tecnologias": ["owasp", "pentesting", "burp_suite", "iso27001"], "disponibilidad_pct": 50, "experiencia_anos": 8, "costo_hora": 42.0},
    {"id": 17, "nombre": "Daniela Rojas",    "rol": "seguridad", "seniority": "mid",    "tecnologias": ["owasp", "sast", "dast", "sonarqube"],          "disponibilidad_pct": 80, "experiencia_anos": 3, "costo_hora": 30.0},
]


def tarifas_promedio() -> Dict[str, float]:
    """Costo por hora promedio de cada rol segun el catalogo (S/.)."""
    out = {}
    for rol in ROLES:
        costos = [c["costo_hora"] for c in COLABORADORES if c["rol"] == rol]
        out[rol] = round(sum(costos) / len(costos), 2) if costos else 0.0
    return out
