from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import estimate, assign_team, auth, users, retrain, sincerar
from db.database import Base, engine

# Crear tablas en Supabase si no existen
Base.metadata.create_all(bind=engine)

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
        "http://localhost:4200"
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
    from ml.pipeline import R2, MMRE
    return {
        "status": "ok",
        "modelo": "XGBoost",
        "r2": R2,
        "mmre_pct": MMRE,
        "dataset_proyectos": 26
    }
