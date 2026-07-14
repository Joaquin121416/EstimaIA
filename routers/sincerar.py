# routers/sincerar.py
"""
HU-06 (parte 1) - Sinceracion de proyectos.
Carga los valores REALES de proyectos terminados y permite limpiar el dataset
marcando outliers para excluirlos del reentrenamiento.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth.dependencies import require_admin
from db.database import get_db
from models.project import EstadoProyecto, Project
from schemas.sincerar import ProyectoPendiente, SincerarRequest

router = APIRouter(prefix="/api/v1/admin/sincerar", tags=["sinceracion"])


def _a_salida(p: Project) -> ProyectoPendiente:
    item = ProyectoPendiente.model_validate(p)
    item.mmre = round(p.mmre, 3) if p.mmre is not None else None
    item.apto_para_training = p.apto_para_training
    return item


@router.get("/pendientes", response_model=list[ProyectoPendiente],
            summary="Listar proyectos para sincerar")
def listar_pendientes(
    incluir_sincerados: bool = Query(False, description="Incluir los ya sincerados"),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    q = db.query(Project)
    if not incluir_sincerados:
        q = q.filter(Project.sincerado.is_(False))
    proyectos = q.order_by(Project.id.desc()).all()
    return [_a_salida(p) for p in proyectos]


@router.put("/{project_id}", response_model=ProyectoPendiente,
            summary="Cargar los datos reales de un proyecto")
def sincerar_proyecto(
    project_id: int,
    datos: SincerarRequest,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    p = db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")

    p.esfuerzo_real_horas = datos.esfuerzo_real_horas
    p.completed_at = datos.completed_at
    if datos.start_on:
        p.start_on = datos.start_on
    if datos.num_tareas_asana is not None:
        p.num_tareas_asana = datos.num_tareas_asana

    # Duracion real derivada de las fechas; si no hay start_on, cae a la estimada
    if p.start_on and p.completed_at:
        dias = (p.completed_at - p.start_on).days
        p.duracion_real_dias = dias if dias > 0 else (p.duracion_estimada_dias or 1)
    else:
        p.duracion_real_dias = p.duracion_estimada_dias

    p.incluir_en_training = datos.incluir_en_training
    p.estado = EstadoProyecto.completado
    p.sincerado = True
    p.fecha_sincerado = datetime.utcnow()
    p.sincerado_por = user.email

    db.commit()
    db.refresh(p)
    return _a_salida(p)


@router.patch("/{project_id}/toggle-training",
              summary="Incluir/excluir del reentrenamiento (limpieza de outliers)")
def toggle_training(project_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    p = db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")
    p.incluir_en_training = not p.incluir_en_training
    db.commit()
    return {"id": p.id, "incluir_en_training": p.incluir_en_training}


@router.delete("/{project_id}", summary="Eliminar un proyecto del dataset")
def eliminar_proyecto(project_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    p = db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")
    db.delete(p)
    db.commit()
    return {"eliminado": project_id}
