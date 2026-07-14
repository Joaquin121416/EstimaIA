import os
os.environ["DATABASE_URL"] = "sqlite:///./smoke.db"
for f in ("smoke.db", "ml/model.joblib"):
    if os.path.exists(f): os.remove(f)

from fastapi.testclient import TestClient
import main
c = TestClient(main.app, raise_server_exceptions=False)

def show(l, r):
    print(f"[{r.status_code}] {l} -> {r.text[:160]}")
    return r

c.post("/api/v1/auth/register", json={"nombre":"Admin","email":"admin@estimaia.com","password":"admin1234","rol":"admin"})
tok = c.post("/api/v1/auth/login", json={"email":"admin@estimaia.com","password":"admin1234"}).json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}

print("=== 1. /estimate (antes rompia con 500) ===")
r = show("estimate", c.post("/api/v1/estimate", headers=H, json={
    "nombre":"Portal Clientes","tipo_sistema":"web","tecnologia_principal":"react",
    "num_modulos":8,"complejidad":4,"tamano_equipo_previsto":3}))
pid = r.json().get("proyecto_id")
pred_antes = r.json().get("esfuerzo_horas")
print(f"    -> proyecto_id={pid}  esfuerzo={pred_antes}h")

print("\n=== 2. Estado del modelo ===")
show("retrain/estado", c.get("/api/v1/admin/retrain/estado", headers=H))

print("\n=== 3. Pendientes de sincerar ===")
r = show("pendientes", c.get("/api/v1/admin/sincerar/pendientes", headers=H))
print(f"    -> {len(r.json())} pendiente(s)")

print("\n=== 4. Sincerar el proyecto (esfuerzo real 520h) ===")
show(f"PUT sincerar/{pid}", c.put(f"/api/v1/admin/sincerar/{pid}", headers=H, json={
    "esfuerzo_real_horas": 520, "completed_at": "2026-11-20",
    "start_on": "2026-07-14", "num_tareas_asana": 150, "incluir_en_training": True}))

print("\n=== 5. Toggle training (limpieza outlier) ===")
show("toggle", c.patch(f"/api/v1/admin/sincerar/{pid}/toggle-training", headers=H))
show("toggle back", c.patch(f"/api/v1/admin/sincerar/{pid}/toggle-training", headers=H))

print("\n=== 6. REENTRENAR ===")
show("retrain", c.post("/api/v1/admin/retrain", headers=H))

print("\n=== 7. /estimate DESPUES del retrain (mismo input) ===")
r2 = c.post("/api/v1/estimate", headers=H, json={
    "nombre":"Portal Clientes 2","tipo_sistema":"web","tecnologia_principal":"react",
    "num_modulos":8,"complejidad":4,"tamano_equipo_previsto":3})
pred_desp = r2.json().get("esfuerzo_horas")
print(f"    esfuerzo ANTES={pred_antes}h  |  DESPUES={pred_desp}h")
print(f"    >>> El modelo reentrenado {'SI' if pred_antes != pred_desp else 'NO'} afecta la prediccion")

print("\n=== 8. Health ===")
show("health", c.get("/health"))
