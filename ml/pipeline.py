import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_percentage_error
import shap
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.dataset import ASANA_PROJECTS

le_tipo = LabelEncoder()
le_tech = LabelEncoder()

FEATURE_NAMES = ["tipo_sistema", "tecnologia", "num_modulos", "complejidad", "tamano_equipo"]

def build_dataframe():
    rows = []
    for p in ASANA_PROJECTS:
        rows.append({
            "tipo_sistema":       p["tipo_sistema"],
            "tecnologia":         p["tecnologia_principal"],
            "num_modulos":        p["num_modulos"],
            "complejidad":        p["complejidad"],
            "tamano_equipo":      p["tamano_equipo"],
            "esfuerzo_horas":     p["esfuerzo_real_horas"],
            # campos extra para proyectos de referencia
            "asana_project_gid":  p["asana_project_gid"],
            "empresa":            p["empresa"],
            "nombre":             p["nombre"],
            "desvio_pct":         p["desvio_pct"],
        })
    return pd.DataFrame(rows)

def get_trained_model():
    df = build_dataframe()

    df["tipo_enc"] = le_tipo.fit_transform(df["tipo_sistema"])
    df["tech_enc"] = le_tech.fit_transform(df["tecnologia"])

    X = df[["tipo_enc", "tech_enc", "num_modulos", "complejidad", "tamano_equipo"]]
    y = df["esfuerzo_horas"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = XGBRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=4,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=0
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    r2   = round(float(r2_score(y_test, y_pred)), 3)
    mmre = round(float(mean_absolute_percentage_error(y_test, y_pred)) * 100, 1)

    explainer = shap.TreeExplainer(model)

    return model, explainer, r2, mmre, df

MODEL, EXPLAINER, R2, MMRE, DF = get_trained_model()


def encode_input(tipo: str, tecnologia: str):
    try:
        tipo_enc = int(le_tipo.transform([tipo])[0])
    except ValueError:
        tipo_enc = 0
    try:
        tech_enc = int(le_tech.transform([tecnologia])[0])
    except ValueError:
        tech_enc = 0
    return tipo_enc, tech_enc


def predict_effort(tipo, tecnologia, num_modulos, complejidad, tamano_equipo):
    tipo_enc, tech_enc = encode_input(tipo, tecnologia)

    X = np.array([[tipo_enc, tech_enc, num_modulos, complejidad, tamano_equipo]], dtype=float)
    pred = float(MODEL.predict(X)[0])

    # Intervalo de confianza basado en MMRE del modelo
    intervalo = MMRE
    esfuerzo_min = round(pred * (1 - intervalo / 100), 0)
    esfuerzo_max = round(pred * (1 + intervalo / 100), 0)

    # SHAP — top 3 variables
    shap_vals = EXPLAINER.shap_values(X)[0]
    total_shap = sum(abs(shap_vals)) or 1
    shap_top3 = sorted(
        [
            {"variable": FEATURE_NAMES[i], "impacto_pct": round(abs(shap_vals[i]) / total_shap * 100, 1)}
            for i in range(len(shap_vals))
        ],
        key=lambda x: x["impacto_pct"],
        reverse=True
    )[:3]

    # Proyectos de referencia — top 3 más similares (distancia Manhattan)
    df = DF.copy()
    df["distancia"] = (
        abs(df["num_modulos"] - num_modulos) * 2
        + abs(df["complejidad"] - complejidad) * 1.5
        + (df["tipo_sistema"] != tipo).astype(int) * 1
        + (df["tecnologia"] != tecnologia).astype(int) * 0.5
    )
    top3 = df.nsmallest(3, "distancia")

    referencia = []
    for _, row in top3.iterrows():
        similitud = max(0, round(100 - row["distancia"] * 8, 1))
        referencia.append({
            "asana_project_gid": row["asana_project_gid"],
            "empresa":           row["empresa"],
            "nombre":            row["nombre"],
            "tipo_sistema":      row["tipo_sistema"],
            "tecnologia_principal": row["tecnologia"],
            "num_modulos":       int(row["num_modulos"]),
            "esfuerzo_real_horas": float(row["esfuerzo_horas"]),
            "desvio_pct":        float(row["desvio_pct"]),
            "similitud_pct":     similitud,
        })

    return round(pred, 0), round(intervalo, 1), esfuerzo_min, esfuerzo_max, shap_top3, referencia
