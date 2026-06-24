import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_percentage_error
import shap
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.dataset import ASANA_PROJECTS

le_tipo = LabelEncoder()
le_tech = LabelEncoder()

FEATURE_NAMES = ["tipo_sistema","tecnologia","num_modulos","complejidad","tamano_equipo","duracion_real_dias","num_tareas_asana"]

def build_dataframe():
    rows = []
    for p in ASANA_PROJECTS:
        rows.append({
            "tipo_sistema": p["tipo_sistema"], "tecnologia": p["tecnologia_principal"],
            "num_modulos": p["num_modulos"], "complejidad": p["complejidad"],
            "tamano_equipo": p["tamano_equipo"], "duracion_real_dias": p["duracion_real_dias"],
            "num_tareas_asana": p["num_tareas_asana"], "esfuerzo_horas": p["esfuerzo_real_horas"],
            "asana_project_gid": p["asana_project_gid"], "empresa": p["empresa"], "nombre": p["nombre"],
            "desvio_pct": p["desvio_pct"], "fecha_inicio": p["fecha_inicio"], "fecha_fin_real": p["fecha_fin_real"],
        })
    return pd.DataFrame(rows)

def get_trained_model():
    df = build_dataframe()
    df["tipo_enc"] = le_tipo.fit_transform(df["tipo_sistema"])
    df["tech_enc"] = le_tech.fit_transform(df["tecnologia"])
    X = df[["tipo_enc","tech_enc","num_modulos","complejidad","tamano_equipo","duracion_real_dias","num_tareas_asana"]]
    y = df["esfuerzo_horas"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = XGBRegressor(n_estimators=300, learning_rate=0.05, max_depth=4, subsample=0.8, colsample_bytree=0.8, random_state=42, verbosity=0)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    r2 = round(float(r2_score(y_test, y_pred)), 3)
    mmre = round(float(mean_absolute_percentage_error(y_test, y_pred)) * 100, 1)
    explainer = shap.TreeExplainer(model)
    return model, explainer, r2, mmre, df

MODEL, EXPLAINER, R2, MMRE, DF = get_trained_model()

def estimate_duration_dias(tipo, num_modulos, complejidad, tamano_equipo):
    df = DF.copy()
    df["dist"] = abs(df["num_modulos"]-num_modulos)*2 + abs(df["complejidad"]-complejidad)*1.5 + abs(df["tamano_equipo"]-tamano_equipo) + (df["tipo_sistema"]!=tipo).astype(int)
    return int(round(df.nsmallest(3,"dist")["duracion_real_dias"].mean()))

def encode_input(tipo, tecnologia):
    try: tipo_enc = int(le_tipo.transform([tipo])[0])
    except ValueError: tipo_enc = 0
    try: tech_enc = int(le_tech.transform([tecnologia])[0])
    except ValueError: tech_enc = 0
    return tipo_enc, tech_enc

def predict_effort(tipo, tecnologia, num_modulos, complejidad, tamano_equipo, duracion_dias=None, num_tareas=None):
    tipo_enc, tech_enc = encode_input(tipo, tecnologia)
    if duracion_dias is None:
        duracion_dias = estimate_duration_dias(tipo, num_modulos, complejidad, tamano_equipo)
    if num_tareas is None:
        df = DF.copy()
        df["dist"] = abs(df["num_modulos"]-num_modulos) + abs(df["complejidad"]-complejidad)
        num_tareas = int(round(df.nsmallest(3,"dist")["num_tareas_asana"].mean()))
    X = np.array([[tipo_enc, tech_enc, num_modulos, complejidad, tamano_equipo, duracion_dias, num_tareas]], dtype=float)
    pred = float(MODEL.predict(X)[0])
    intervalo = MMRE
    esfuerzo_min = round(pred * (1 - intervalo/100), 0)
    esfuerzo_max = round(pred * (1 + intervalo/100), 0)
    shap_vals = EXPLAINER.shap_values(X)[0]
    total_shap = sum(abs(shap_vals)) or 1
    shap_top3 = sorted(
        [{"variable": FEATURE_NAMES[i], "impacto_pct": round(abs(shap_vals[i])/total_shap*100, 1)} for i in range(len(shap_vals))],
        key=lambda x: x["impacto_pct"], reverse=True
    )[:3]
    df = DF.copy()
    df["distancia"] = abs(df["num_modulos"]-num_modulos)*2 + abs(df["complejidad"]-complejidad)*1.5 + abs(df["duracion_real_dias"]-duracion_dias)*0.05 + (df["tipo_sistema"]!=tipo).astype(int) + (df["tecnologia"]!=tecnologia).astype(int)*0.5
    referencia = []
    for _, row in df.nsmallest(3,"distancia").iterrows():
        similitud = max(0, round(100 - row["distancia"]*7, 1))
        referencia.append({
            "asana_project_gid": row["asana_project_gid"], "empresa": row["empresa"], "nombre": row["nombre"],
            "tipo_sistema": row["tipo_sistema"], "tecnologia_principal": row["tecnologia"],
            "num_modulos": int(row["num_modulos"]), "esfuerzo_real_horas": float(row["esfuerzo_horas"]),
            "duracion_real_dias": int(row["duracion_real_dias"]), "desvio_pct": float(row["desvio_pct"]),
            "similitud_pct": similitud, "fecha_inicio": row["fecha_inicio"], "fecha_fin_real": row["fecha_fin_real"],
        })
    return round(pred,0), round(intervalo,1), esfuerzo_min, esfuerzo_max, shap_top3, referencia, duracion_dias

def calc_confidence(r2, esfuerzo_horas, duracion_semanas_estimada, tarifa_hora=21.875, presupuesto_maximo=None, deadline_semanas=None):
    base = round(min(r2*85, 85), 1)
    pen_presupuesto = 0.0
    pen_tiempo = 0.0
    if presupuesto_maximo:
        costo_estimado = esfuerzo_horas * tarifa_hora
        if costo_estimado > presupuesto_maximo:
            exceso = (costo_estimado - presupuesto_maximo) / presupuesto_maximo
            pen_presupuesto = round(min(exceso*40, 40), 1)
    if deadline_semanas:
        if duracion_semanas_estimada > deadline_semanas:
            exceso = (duracion_semanas_estimada - deadline_semanas) / deadline_semanas
            pen_tiempo = round(min(exceso*30, 30), 1)
    score = round(max(base - pen_presupuesto - pen_tiempo, 5), 1)
    if score >= 75: msg = "Alta confiabilidad. El proyecto es viable dentro de las restricciones indicadas."
    elif score >= 50: msg = "Confiabilidad media. Revisar alcance o negociar presupuesto/plazo con el cliente."
    else: msg = "Confiabilidad baja. Las restricciones son incompatibles con el alcance estimado."
    return {"score_total": score, "base_modelo": base, "penalizacion_presupuesto": pen_presupuesto, "penalizacion_tiempo": pen_tiempo, "mensaje": msg}
