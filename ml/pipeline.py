import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.metrics import r2_score, mean_absolute_percentage_error
import shap
import joblib
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.dataset import ASANA_PROJECTS

le_tipo = LabelEncoder()
le_tech = LabelEncoder()

# Features base + derivadas (feature engineering Sprint 3)
FEATURE_NAMES = [
    "tipo_sistema", "tecnologia", "num_modulos", "complejidad", "tamano_equipo",
    "duracion_real_dias", "num_tareas_asana",
    "tareas_por_modulo", "dias_por_tarea", "equipo_x_complejidad",
    "modulos_x_complejidad", "velocidad_tareas_dia",
]

def build_dataframe():
    rows = []
    for p in ASANA_PROJECTS:
        rows.append({
            "tipo_sistema":       p["tipo_sistema"],
            "tecnologia":         p["tecnologia_principal"],
            "num_modulos":        p["num_modulos"],
            "complejidad":        p["complejidad"],
            "tamano_equipo":      p["tamano_equipo"],
            "duracion_real_dias": p["duracion_real_dias"],
            "num_tareas_asana":   p["num_tareas_asana"],
            "esfuerzo_horas":     p["esfuerzo_real_horas"],
            "asana_project_gid":  p["asana_project_gid"],
            "empresa":            p["empresa"],
            "nombre":             p["nombre"],
            "desvio_pct":         p["desvio_pct"],
            "fecha_inicio":       p["fecha_inicio"],
            "fecha_fin_real":     p["fecha_fin_real"],
        })
    df = pd.DataFrame(rows)

    return add_derived_features(df)

def get_trained_model():
    df = build_dataframe()
    df["tipo_enc"] = le_tipo.fit_transform(df["tipo_sistema"])
    df["tech_enc"] = le_tech.fit_transform(df["tecnologia"])

    X = df[["tipo_enc","tech_enc","num_modulos","complejidad","tamano_equipo",
            "duracion_real_dias","num_tareas_asana","tareas_por_modulo",
            "dias_por_tarea","equipo_x_complejidad","modulos_x_complejidad",
            "velocidad_tareas_dia"]]
    y = df["esfuerzo_horas"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Hiperparametros optimizados via RandomizedSearchCV (Sprint 3)
    model = XGBRegressor(
        n_estimators=300, learning_rate=0.05, max_depth=4,
        subsample=0.7, colsample_bytree=0.6, min_child_weight=1,
        reg_alpha=1, reg_lambda=3,
        random_state=42, verbosity=0
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    r2   = round(float(r2_score(y_test, y_pred)), 3)
    mmre = round(float(mean_absolute_percentage_error(y_test, y_pred)) * 100, 1)

    # R2 por validacion cruzada 5-fold: metrica robusta usada para decidir
    # la promocion de modelos en el reentrenamiento (evita el sesgo de un
    # unico split con pocos datos de test).
    r2_cv = round(float(cross_val_score(
        XGBRegressor(**dict(n_estimators=300, learning_rate=0.05, max_depth=4,
                            subsample=0.7, colsample_bytree=0.6, min_child_weight=1,
                            reg_alpha=1, reg_lambda=3, random_state=42, verbosity=0)),
        X, y, cv=KFold(5, shuffle=True, random_state=42), scoring="r2"
    ).mean()), 3)

    explainer = shap.TreeExplainer(model)
    return model, explainer, r2, mmre, r2_cv, df

# ---------------------------------------------------------------------------
# Persistencia del modelo campeon (HU-06)
# ---------------------------------------------------------------------------
MODEL_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(MODEL_DIR, "model.joblib")

# Columnas de entrada del modelo, en orden. Unica fuente de verdad.
X_COLUMNS = [
    "tipo_enc", "tech_enc", "num_modulos", "complejidad", "tamano_equipo",
    "duracion_real_dias", "num_tareas_asana", "tareas_por_modulo",
    "dias_por_tarea", "equipo_x_complejidad", "modulos_x_complejidad",
    "velocidad_tareas_dia",
]


def add_derived_features(df):
    """Feature engineering compartido por entrenamiento y reentrenamiento."""
    df["tareas_por_modulo"]     = df["num_tareas_asana"] / df["num_modulos"]
    df["dias_por_tarea"]        = df["duracion_real_dias"] / df["num_tareas_asana"]
    df["equipo_x_complejidad"]  = df["tamano_equipo"] * df["complejidad"]
    df["modulos_x_complejidad"] = df["num_modulos"] * df["complejidad"]
    df["velocidad_tareas_dia"]  = df["num_tareas_asana"] / df["duracion_real_dias"]
    return df


def _load_champion():
    """Carga el modelo campeon persistido. None si no existe o es invalido."""
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        bundle = joblib.load(MODEL_PATH)
        if bundle.get("columns") != X_COLUMNS:
            return None  # esquema de features incompatible -> ignorar
        return bundle
    except Exception:
        return None


def save_champion(model, r2, mmre, r2_cv, n_proyectos, le_tipo_, le_tech_):
    """Persiste el modelo promovido para que sobreviva a reinicios de Railway."""
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump({
        "model": model, "columns": X_COLUMNS,
        "r2": r2, "mmre": mmre, "r2_cv": r2_cv, "n_proyectos": n_proyectos,
        "le_tipo": le_tipo_, "le_tech": le_tech_,
    }, MODEL_PATH)


def _init():
    """Al arrancar: usa el campeon persistido si existe; si no, entrena del dataset semilla."""
    global MODEL, EXPLAINER, R2, MMRE, R2_CV, DF, le_tipo, le_tech, N_PROYECTOS

    model_s, explainer_s, r2_s, mmre_s, r2cv_s, df_s = get_trained_model()
    DF = df_s
    N_PROYECTOS = len(df_s)

    bundle = _load_champion()
    if bundle is not None:
        MODEL       = bundle["model"]
        le_tipo     = bundle["le_tipo"]
        le_tech     = bundle["le_tech"]
        R2          = bundle["r2"]
        MMRE        = bundle["mmre"]
        R2_CV       = bundle.get("r2_cv", bundle["r2"])
        N_PROYECTOS = bundle.get("n_proyectos", len(df_s))
        EXPLAINER   = shap.TreeExplainer(MODEL)
    else:
        MODEL, EXPLAINER, R2, MMRE, R2_CV = model_s, explainer_s, r2_s, mmre_s, r2cv_s


def reload_champion():
    """
    Recarga en caliente el modelo campeon tras un reentrenamiento exitoso.
    Sin esto, /estimate seguiria usando el modelo viejo hasta reiniciar el server.
    """
    global MODEL, EXPLAINER, R2, MMRE, R2_CV, le_tipo, le_tech, N_PROYECTOS
    bundle = _load_champion()
    if bundle is None:
        return False
    MODEL       = bundle["model"]
    le_tipo     = bundle["le_tipo"]
    le_tech     = bundle["le_tech"]
    R2          = bundle["r2"]
    MMRE        = bundle["mmre"]
    R2_CV       = bundle.get("r2_cv", bundle["r2"])
    N_PROYECTOS = bundle.get("n_proyectos", N_PROYECTOS)
    EXPLAINER   = shap.TreeExplainer(MODEL)
    return True


MODEL = EXPLAINER = R2 = MMRE = R2_CV = DF = None
N_PROYECTOS = 0
_init()

def estimate_duration_dias(tipo, num_modulos, complejidad, tamano_equipo):
    df = DF.copy()
    df["dist"] = (
        abs(df["num_modulos"] - num_modulos) * 2
        + abs(df["complejidad"] - complejidad) * 1.5
        + abs(df["tamano_equipo"] - tamano_equipo)
        + (df["tipo_sistema"] != tipo).astype(int)
    )
    return int(round(df.nsmallest(3, "dist")["duracion_real_dias"].mean()))

def estimate_num_tareas(num_modulos, complejidad):
    df = DF.copy()
    df["dist"] = abs(df["num_modulos"] - num_modulos) + abs(df["complejidad"] - complejidad)
    return int(round(df.nsmallest(3, "dist")["num_tareas_asana"].mean()))

def encode_input(tipo, tecnologia):
    try: tipo_enc = int(le_tipo.transform([tipo])[0])
    except ValueError: tipo_enc = 0
    try: tech_enc = int(le_tech.transform([tecnologia])[0])
    except ValueError: tech_enc = 0
    return tipo_enc, tech_enc

def predict_effort(tipo, tecnologia, num_modulos, complejidad, tamano_equipo,
                   duracion_dias=None, num_tareas=None):

    tipo_enc, tech_enc = encode_input(tipo, tecnologia)

    if duracion_dias is None:
        duracion_dias = estimate_duration_dias(tipo, num_modulos, complejidad, tamano_equipo)
    if num_tareas is None:
        num_tareas = estimate_num_tareas(num_modulos, complejidad)

    # Calcular features derivadas para el input
    tareas_por_modulo     = num_tareas / num_modulos
    dias_por_tarea         = duracion_dias / num_tareas
    equipo_x_complejidad   = tamano_equipo * complejidad
    modulos_x_complejidad  = num_modulos * complejidad
    velocidad_tareas_dia   = num_tareas / duracion_dias

    X = np.array([[
        tipo_enc, tech_enc, num_modulos, complejidad, tamano_equipo,
        duracion_dias, num_tareas, tareas_por_modulo, dias_por_tarea,
        equipo_x_complejidad, modulos_x_complejidad, velocidad_tareas_dia
    ]], dtype=float)

    pred = float(MODEL.predict(X)[0])
    intervalo = MMRE
    esfuerzo_min = round(pred * (1 - intervalo / 100), 0)
    esfuerzo_max = round(pred * (1 + intervalo / 100), 0)

    shap_vals = EXPLAINER.shap_values(X)[0]
    total_shap = sum(abs(shap_vals)) or 1
    shap_top3 = sorted(
        [{"variable": FEATURE_NAMES[i], "impacto_pct": round(abs(shap_vals[i]) / total_shap * 100, 1)}
         for i in range(len(shap_vals))],
        key=lambda x: x["impacto_pct"], reverse=True
    )[:3]

    df = DF.copy()
    df["distancia"] = (
        abs(df["num_modulos"] - num_modulos) * 2
        + abs(df["complejidad"] - complejidad) * 1.5
        + abs(df["duracion_real_dias"] - duracion_dias) * 0.05
        + (df["tipo_sistema"] != tipo).astype(int)
        + (df["tecnologia"] != tecnologia).astype(int) * 0.5
    )
    top3 = df.nsmallest(3, "distancia")

    referencia = []
    for _, row in top3.iterrows():
        similitud = max(0, round(100 - row["distancia"] * 7, 1))
        referencia.append({
            "asana_project_gid":    row["asana_project_gid"],
            "empresa":              row["empresa"],
            "nombre":               row["nombre"],
            "tipo_sistema":         row["tipo_sistema"],
            "tecnologia_principal": row["tecnologia"],
            "num_modulos":          int(row["num_modulos"]),
            "esfuerzo_real_horas":  float(row["esfuerzo_horas"]),
            "duracion_real_dias":   int(row["duracion_real_dias"]),
            "desvio_pct":           float(row["desvio_pct"]),
            "similitud_pct":        similitud,
            "fecha_inicio":         row["fecha_inicio"],
            "fecha_fin_real":       row["fecha_fin_real"],
        })

    return round(pred, 0), round(intervalo, 1), esfuerzo_min, esfuerzo_max, shap_top3, referencia, duracion_dias

def calc_confidence(r2, esfuerzo_horas, duracion_semanas_estimada,
                    tarifa_hora=21.875, presupuesto_maximo=None, deadline_semanas=None):
    base = round(min(r2 * 85, 85), 1)
    pen_presupuesto = 0.0
    pen_tiempo = 0.0

    if presupuesto_maximo:
        costo_estimado = esfuerzo_horas * tarifa_hora
        if costo_estimado > presupuesto_maximo:
            exceso = (costo_estimado - presupuesto_maximo) / presupuesto_maximo
            pen_presupuesto = round(min(exceso * 40, 40), 1)

    if deadline_semanas:
        if duracion_semanas_estimada > deadline_semanas:
            exceso = (duracion_semanas_estimada - deadline_semanas) / deadline_semanas
            pen_tiempo = round(min(exceso * 30, 30), 1)

    score = round(max(base - pen_presupuesto - pen_tiempo, 5), 1)

    if score >= 75:
        msg = "Alta confiabilidad. El proyecto es viable dentro de las restricciones indicadas."
    elif score >= 50:
        msg = "Confiabilidad media. Revisar alcance o negociar presupuesto/plazo con el cliente."
    else:
        msg = "Confiabilidad baja. Las restricciones son incompatibles con el alcance estimado."

    return {
        "score_total": score, "base_modelo": base,
        "penalizacion_presupuesto": pen_presupuesto,
        "penalizacion_tiempo": pen_tiempo, "mensaje": msg,
    }
