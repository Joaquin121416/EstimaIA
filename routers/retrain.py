# routers/retrain.py
"""
HU-06 - Reentrenamiento del modelo ML (champion / challenger).

Bucle cerrado:
  1. /estimate guarda el proyecto con sus features y el esfuerzo ESTIMADO.
  2. El admin sincera el proyecto cargando el esfuerzo REAL (routers/sincerar.py).
  3. Este endpoint reentrena con dataset semilla + proyectos sincerados,
     compara el challenger contra el champion en produccion y SOLO promueve
     si el R2 mejora. Si promueve, recarga el modelo en caliente.
"""
import os
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sklearn.metrics import r2_score, mean_absolute_percentage_error
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.preprocessing import LabelEncoder
from sqlalchemy.orm import Session
from xgboost import XGBRegressor

from auth.dependencies import require_admin
from db.database import get_db
from ml import pipeline
from models.project import Project

router = APIRouter(prefix="/api/v1/admin/retrain", tags=["reentrenamiento"])

MIN_PROYECTOS = 30   # restriccion documentada en PI-1 E1

XGB_PARAMS = dict(
    n_estimators=300, learning_rate=0.05, max_depth=4,
    subsample=0.7, colsample_bytree=0.6, min_child_weight=1,
    reg_alpha=1, reg_lambda=3, random_state=42, verbosity=0,
)


def _filas_sinceradas(db: Session) -> list:
    candidatos = db.query(Project).filter(
        Project.sincerado.is_(True),
        Project.incluir_en_training.is_(True),
        Project.esfuerzo_real_horas.isnot(None),
    ).all()
    return [p for p in candidatos if p.apto_para_training]


def _construir_dataset(db: Session):
    """Dataset semilla (proyectos historicos) + proyectos sincerados en BD."""
    df_semilla = pipeline.build_dataframe()[[
        "tipo_sistema", "tecnologia", "num_modulos", "complejidad",
        "tamano_equipo", "duracion_real_dias", "num_tareas_asana", "esfuerzo_horas",
    ]].copy()
    df_semilla["origen"] = "semilla"

    filas = _filas_sinceradas(db)
    df_nuevos = pd.DataFrame([{
        "tipo_sistema":       p.tipo_sistema,
        "tecnologia":         p.tecnologia_principal,
        "num_modulos":        p.num_modulos,
        "complejidad":        p.complejidad,
        "tamano_equipo":      p.tamano_equipo,
        "duracion_real_dias": p.duracion_real_dias,
        "num_tareas_asana":   p.num_tareas_asana,
        "esfuerzo_horas":     p.esfuerzo_real_horas,
        "origen":             "sincerado",
    } for p in filas])

    df = pd.concat([df_semilla, df_nuevos], ignore_index=True) if len(df_nuevos) else df_semilla
    return pipeline.add_derived_features(df), len(filas)


@router.post("", summary="Reentrenar el modelo (champion/challenger)")
def reentrenar(db: Session = Depends(get_db), user=Depends(require_admin)):
    df, n_sincerados = _construir_dataset(db)

    if len(df) < MIN_PROYECTOS:
        raise HTTPException(
            422,
            f"Dataset insuficiente: {len(df)} proyectos "
            f"({n_sincerados} sincerados). Se requieren {MIN_PROYECTOS}.",
        )

    le_tipo, le_tech = LabelEncoder(), LabelEncoder()
    df["tipo_enc"] = le_tipo.fit_transform(df["tipo_sistema"])
    df["tech_enc"] = le_tech.fit_transform(df["tecnologia"])

    X = df[pipeline.X_COLUMNS]
    y = df["esfuerzo_horas"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    challenger = XGBRegressor(**XGB_PARAMS)
    challenger.fit(X_train, y_train)
    pred = challenger.predict(X_test)
    r2_new   = round(float(r2_score(y_test, pred)), 3)
    mmre_new = round(float(mean_absolute_percentage_error(y_test, pred)) * 100, 1)

    # --- Metrica de promocion: R2 por validacion cruzada 5-fold ---
    # No se evalua al champion sobre este test set porque ya vio esas filas
    # durante su entrenamiento (data leakage): su R2 saldria inflado y ningun
    # challenger podria superarlo nunca. En su lugar se compara CV contra CV:
    # mismo protocolo de evaluacion para ambos, sin fuga de informacion.
    r2_cv_new = round(float(cross_val_score(
        XGBRegressor(**XGB_PARAMS), X, y,
        cv=KFold(5, shuffle=True, random_state=42), scoring="r2"
    ).mean()), 3)

    r2_cv_old = pipeline.R2_CV
    promovido = r2_cv_old is None or r2_cv_new >= r2_cv_old

    if promovido:
        pipeline.save_champion(challenger, r2_new, mmre_new, r2_cv_new, len(df), le_tipo, le_tech)
        pipeline.reload_champion()   # hot-reload: /estimate usa ya el modelo nuevo

    return {
        "proyectos_totales":    int(len(df)),
        "proyectos_semilla":    int(len(df) - n_sincerados),
        "proyectos_sincerados": int(n_sincerados),
        "r2_cv_anterior": r2_cv_old,
        "r2_cv_nuevo":    r2_cv_new,
        "r2_holdout_nuevo": r2_new,
        "mmre_nuevo_pct":   mmre_new,
        "modelo_promovido": bool(promovido),
        "metrica_decision": "R2 validacion cruzada 5-fold",
        "mensaje": (
            f"Modelo promovido. R2(CV) {r2_cv_old} -> {r2_cv_new}. Ya activo en /estimate."
            if promovido else
            f"Reentrenamiento descartado: R2(CV) {r2_cv_new} no supera al champion "
            f"({r2_cv_old}). Se mantiene el modelo en produccion."
        ),
        "reentrenado_por": user.email,
        "fecha": datetime.utcnow().isoformat(),
    }


@router.get("/estado", summary="Estado del modelo en produccion")
def estado_modelo(db: Session = Depends(get_db), _=Depends(require_admin)):
    n_sincerados = len(_filas_sinceradas(db))
    return {
        "r2_actual": pipeline.R2,
        "r2_cv_actual": pipeline.R2_CV,
        "mmre_actual_pct": pipeline.MMRE,
        "proyectos_en_modelo": pipeline.N_PROYECTOS,
        "proyectos_sincerados_disponibles": n_sincerados,
        "modelo_persistido": os.path.exists(pipeline.MODEL_PATH),
        "listo_para_reentrenar": (len(pipeline.DF) + n_sincerados) >= MIN_PROYECTOS,
        "minimo_requerido": MIN_PROYECTOS,
    }
