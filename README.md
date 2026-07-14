# EstimaIA — Backend (FastAPI + XGBoost)

Sistema inteligente de estimación de esfuerzo y asignación de recursos para proyectos de TI.
UPC 2026 — William Chávez Guerrero & Joaquín Cunorana Jiménez.

## Stack
FastAPI (Python 3.11) · XGBoost + SHAP · SQLAlchemy 2.0 · Supabase PostgreSQL · Railway

---

## Módulo de reentrenamiento (HU-06) — bucle cerrado

```
/estimate  ──►  guarda el proyecto con TODAS sus features
                y el esfuerzo ESTIMADO (estado = "estimado")
                          │
                          ▼
/admin/sincerar  ──►  el admin carga el esfuerzo REAL al terminar
                      el proyecto (estado = "completado", sincerado = true)
                      y puede excluir outliers del dataset
                          │
                          ▼
/admin/retrain   ──►  reentrena con dataset semilla + proyectos sincerados
                      compara CHALLENGER vs CHAMPION por R² de validación
                      cruzada 5-fold, y SOLO promueve si mejora.
                      Si promueve → hot-reload: /estimate usa el modelo nuevo
                      sin reiniciar el servidor.
```

### Por qué R² de validación cruzada y no holdout
El champion ya vio las filas del dataset durante su entrenamiento. Evaluarlo sobre un
holdout construido a partir del mismo dataset produce **data leakage**: su R² sale inflado
y ningún challenger podría superarlo jamás. La promoción se decide comparando
**R²(CV 5-fold) contra R²(CV 5-fold)** — mismo protocolo para ambos, sin fuga de información.

El R² holdout se sigue reportando en `/health` por continuidad con la documentación de tesis.

---

## Endpoints

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| POST | `/api/v1/auth/register` | — | Registrar usuario |
| POST | `/api/v1/auth/login` | — | Login (JWT, 8 h) |
| GET | `/api/v1/auth/me` | auth | Usuario actual |
| GET | `/api/v1/users/` | admin | Listar usuarios |
| POST | `/api/v1/estimate` | auth | Estimar esfuerzo (persiste el proyecto) |
| POST | `/api/v1/assign-team` | auth | Recomendar equipo |
| GET | `/api/v1/admin/sincerar/pendientes` | admin | Proyectos por sincerar |
| PUT | `/api/v1/admin/sincerar/{id}` | admin | Cargar esfuerzo real |
| PATCH | `/api/v1/admin/sincerar/{id}/toggle-training` | admin | Incluir/excluir del training |
| DELETE | `/api/v1/admin/sincerar/{id}` | admin | Eliminar del dataset |
| GET | `/api/v1/admin/retrain/estado` | admin | Métricas del modelo en producción |
| POST | `/api/v1/admin/retrain` | admin | Reentrenar (champion/challenger) |
| GET | `/health` | — | Estado + métricas del modelo |

---

## Puesta en marcha

### 1. Migración de base de datos (una sola vez)
En Supabase → SQL Editor, ejecutar `migrations/001_projects_reentrenamiento.sql`.

### 2. Variables de entorno en Railway
```
DATABASE_URL=postgresql://postgres.<REF>:<PASS>@aws-0-<region>.pooler.supabase.com:6543/postgres
JWT_SECRET_KEY=<secreto-largo-aleatorio>
```
> Usar el **Connection Pooler** (puerto 6543), no la conexión directa: Railway no soporta
> el IPv6 al que resuelve el connection string directo de Supabase.

### 3. Local
```bash
pip install -r requirements.txt
uvicorn main:app --reload
# sin DATABASE_URL cae a SQLite local (estimaia_local.db)
```

### 4. Pruebas end-to-end
```bash
python tests_e2e.py
```

---

## Persistencia del modelo
El modelo promovido se guarda en `ml/model.joblib` (modelo + encoders + columnas + métricas).
Al arrancar, la app carga ese champion si existe; si no, entrena desde el dataset semilla.

> **Nota sobre Railway:** el filesystem es efímero — al redeploy se pierde `model.joblib` y
> el sistema vuelve al modelo base (comportamiento seguro, no rompe nada). Para persistirlo
> entre despliegues hay que montar un volumen en Railway sobre el directorio `ml/`.
