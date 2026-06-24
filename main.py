from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import estimate, assign_team, auth, users

app = FastAPI(
    title="EstimaIA API",
    description="""
## Sistema Inteligente de Estimacion de Esfuerzo y Asignacion de Equipo

**EstimaIA** aplica Machine Learning (XGBoost) para predecir el esfuerzo en horas-hombre
de proyectos de software y recomendar el equipo optimo de desarrollo.

### Autenticacion (Sprint 2) - Usuarios hardcodeados temporalmente
- `POST /api/v1/auth/register` - Crear usuario
- `POST /api/v1/auth/login` - Iniciar sesion (retorna JWT)
- `GET /api/v1/auth/me` - Usuario autenticado

Usuarios de prueba:
- Admin: joaquin@consultora.pe / estimaIA2026
- PM: william@consultora.pe / estimaIA2026

### Gestion de Roles (Sprint 2 - Solo Admin)
- `GET /api/v1/users/` - Listar usuarios
- `PUT /api/v1/users/{id}/rol` - Cambiar rol
- `PUT /api/v1/users/{id}/desactivar` - Desactivar usuario

### Dataset
Proyectos historicos de 4 empresas peruanas: ELDO, QROMA, NEXO SALUD, LOGIPAQ

### Desarrollado por
William Franco Chavez Guerrero & Joaquin Cunorana Jimenez
Universidad Peruana de Ciencias Aplicadas (UPC) - 2026
    """,
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(estimate.router)
app.include_router(assign_team.router)

@app.get("/", tags=["Sistema"])
def root():
    return {
        "sistema": "EstimaIA",
        "version": "1.1.0",
        "status": "online",
        "docs": "/docs",
        "endpoints": {
            "auth_login": "POST /api/v1/auth/login",
            "auth_register": "POST /api/v1/auth/register",
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
        "dataset_proyectos": 26
    }
