import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routers import estimate, assign_team, auth, users, retrain, sincerar
from db.database import init_db, DB_STATUS

# Crea las tablas si la BD responde. Si no, la API levanta igual:
# /health y /docs siguen vivos para diagnosticar, y el modulo ML sigue operativo.
init_db()

app = FastAPI(
    title="EstimaIA API",
    description="""
## Sistema Inteligente de Estimacion de Esfuerzo y Asignacion de Equipo

**EstimaIA** aplica Machine Learning (XGBoost) para predecir el esfuerzo en horas-hombre
de proyectos de software y recomendar el equipo optimo de desarrollo.

### Autenticacion (persistida en Supabase PostgreSQL)
- POST /api/v1/auth/register
- POST /api/v1/auth/login
- GET /api/v1/auth/me

### Gestion de Roles (Solo Admin)
- GET /api/v1/users/
- PUT /api/v1/users/{id}/rol
- PUT /api/v1/users/{id}/desactivar

### Reentrenamiento (Solo Admin)
- POST /api/v1/admin/retrain
- GET  /api/v1/admin/retrain/estado

### sinceracion de Proyectos (Solo Admin)
- GET /api/v1/admin/sincerar/pendientes
- PUT /api/v1/admin/sincerar/project_id


### Dataset
Proyectos historicos de 4 empresas peruanas: ELDO, QROMA, NEXO SALUD, LOGIPAQ

### Desarrollado por
William Franco Chavez Guerrero & Joaquin Cunorana Jimenez
Universidad Peruana de Ciencias Aplicadas (UPC) - 2026
    """,
    version="1.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://estimaia-front-production.up.railway.app",
        "http://localhost:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(auth.router)
app.include_router(users.router)
app.include_router(estimate.router)
app.include_router(assign_team.router)
app.include_router(sincerar.router)
app.include_router(retrain.router)

@app.get("/", tags=["Sistema"])
def root():
    return {
        "sistema": "EstimaIA",
        "version": "1.2.0",
        "status": "online",
        "docs": "/docs",
    }

@app.get("/health", tags=["Sistema"])
def health():
    from ml import pipeline
    return {
        "status": "ok" if DB_STATUS["conectada"] else "degradado",
        "modelo": "XGBoost",
        "r2": pipeline.R2,
        "r2_cv": pipeline.R2_CV,
        "mmre_pct": pipeline.MMRE,
        "dataset_proyectos": pipeline.N_PROYECTOS,
        "modelo_reentrenado": os.path.exists(pipeline.MODEL_PATH),
        "base_datos": {
            "conectada": DB_STATUS["conectada"],
            "motor": DB_STATUS["motor"],
            "error": DB_STATUS.get("error"),
            "diagnostico": DB_STATUS.get("diagnostico"),
        },
    }


@app.post("/health/db/reconectar", tags=["Sistema"])
def reconectar_db():
    """Reintenta la conexion a la BD sin redesplegar (util tras restaurar Supabase)."""
    ok = init_db()
    return {
        "conectada": ok,
        "error": DB_STATUS.get("error"),
        "diagnostico": DB_STATUS.get("diagnostico"),
    }
