from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import estimate, assign_team

app = FastAPI(
    title="EstimaIA API",
    description="""
## Sistema Inteligente de Estimación de Esfuerzo y Asignación de Equipo

**EstimaIA** aplica Machine Learning (XGBoost) para predecir el esfuerzo en horas-hombre
de proyectos de software y recomendar el equipo óptimo de desarrollo.

### Dataset
Proyectos históricos de 4 empresas peruanas:
- **ELDO** — Fintech / Lending y Factoring
- **QROMA** — Manufactura / Pinturas
- **NEXO SALUD** — Clínica Privada
- **LOGIPAQ** — Logística / Courier

### Endpoints principales
- `POST /api/v1/estimate` — Estimación de esfuerzo con SHAP
- `POST /api/v1/assign-team` — Recomendación de equipo óptimo

### Desarrollado por
William Franco Chávez Guerrero & Joaquín Cunorana Jimenez  
Universidad Peruana de Ciencias Aplicadas (UPC) — 2026
    """,
    version="1.0.0",
    contact={"name": "EstimaIA Team", "email": "estimaia@upc.edu.pe"},
    license_info={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://estimaia-front-production.up.railway.app",
        "http://localhost:4200",
        "*"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(estimate.router)
app.include_router(assign_team.router)

@app.get("/", tags=["Sistema"])
def root():
    return {
        "sistema": "EstimaIA",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "endpoints": {
            "estimate": "POST /api/v1/estimate",
            "assign_team": "POST /api/v1/assign-team"
        }
    }

@app.get("/health", tags=["Sistema"])
def health():
    from ml.pipeline import R2, MMRE
    return {
        "status": "ok",
        "modelo": "XGBoost",
        "r2": R2,
        "mmre_pct": MMRE,
        "dataset_proyectos": 21
    }
