# app/routers/retrain.py
import os, joblib, shutil
from datetime import datetime
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_percentage_error
from xgboost import XGBRegressor
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from models.project import Project, EstadoProyecto
from auth import require_admin

router = APIRouter(prefix="/api/v1/admin/retrain", tags=["reentrenamiento"])

MODEL_PATH      = "app/ml/model.joblib"          # champion en producción
MIN_PROYECTOS   = 30                              # tu restricción de tesis

FEATURES_NUM = ["num_modulos", "tasks_count"]
FEATURES_CAT = ["tecnologia_principal"]
TARGET       = "esfuerzo_real_horas"

@router.post("")
def reentrenar(db: Session = Depends(get_db), user=Depends(require_admin)):
    # 1) Solo filas sincdas y marcadas para training
    filas = db.query(Project).filter(
        Project.sincerado == True,
        Project.incluir_en_training == True,
        Project.estado == EstadoProyecto.completado,
        Project.esfuerzo_real_horas.isnot(None),
    ).all()

    if len(filas) < MIN_PROYECTOS:
        raise HTTPException(
            422,
            f"Dataset insuficiente: {len(filas)} proyectos sincerados, "
            f"se requieren {MIN_PROYECTOS}."
        )

    df = pd.DataFrame([{
        "num_modulos": f.num_modulos,
        "tasks_count": f.tasks_count or 0,
        "tecnologia_principal": f.tecnologia_principal,
        "esfuerzo_real_horas": f.esfuerzo_real_horas,
    } for f in filas])

    # 2) Preprocesamiento (mismo que tu pipeline original)
    df = pd.get_dummies(df, columns=FEATURES_CAT)
    X = df.drop(columns=[TARGET])
    y = df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # 3) Entrenar el challenger (mismos hiperparámetros que tu modelo actual)
    challenger = XGBRegressor(
        n_estimators=300, learning_rate=0.05, max_depth=6, random_state=42
    )
    challenger.fit(X_train, y_train)
    pred = challenger.predict(X_test)
    r2_new   = r2_score(y_test, pred)
    mmre_new = mean_absolute_percentage_error(y_test, pred)

    # 4) Comparar contra el champion en producción
    r2_old = None
    if os.path.exists(MODEL_PATH):
        try:
            champ = joblib.load(MODEL_PATH)
            # realinear columnas por si cambió el one-hot
            X_test_c = X_test.reindex(columns=champ.get_booster().feature_names, fill_value=0)
            r2_old = r2_score(y_test, champ.predict(X_test_c))
        except Exception:
            r2_old = None

    promovido = r2_old is None or r2_new >= r2_old
    if promovido:
        if os.path.exists(MODEL_PATH):
            shutil.copy(MODEL_PATH, MODEL_PATH.replace(".joblib", f".bak_{datetime.utcnow():%Y%m%d%H%M}.joblib"))
        joblib.dump(challenger, MODEL_PATH)

    return {
        "proyectos_usados": len(filas),
        "r2_anterior": round(r2_old, 4) if r2_old is not None else None,
        "r2_nuevo": round(r2_new, 4),
        "mmre_nuevo": round(mmre_new, 4),
        "modelo_promovido": promovido,
        "mensaje": "Modelo actualizado ✓" if promovido
                   else "Reentrenamiento descartado: el R² no mejoró. Se mantiene el champion.",
        "reentrenado_por": user.email,
        "fecha": datetime.utcnow().isoformat(),
    }