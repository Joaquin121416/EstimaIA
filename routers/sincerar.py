# app/routers/sincerar.py
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from models.project import Project, EstadoProyecto
from schemas.sincerar import SincerarRequest, ProyectoPendiente
from auth.dependencies import require_admin   # tu dependencia RBAC existente

router = APIRouter(prefix="/api/v1/admin/sincerar", tags=["sinceracion"])

@router.get("/pendientes", response_model=list[ProyectoPendiente])
def listar_pendientes(db: Session = Depends(get_db), _=Depends(require_admin)):
    """Proyectos completados aún no sincerados + ya sincerados (para revisión)."""
    proyectos = db.query(Project).filter(
        Project.estado.in_([EstadoProyecto.completado, EstadoProyecto.en_curso])
    ).all()

    salida = []
    for p in proyectos:
        mmre = None
        if p.esfuerzo_real_horas and p.esfuerzo_estimado_horas:
            mmre = abs(p.esfuerzo_real_horas - p.esfuerzo_estimado_horas) / p.esfuerzo_real_horas
        item = ProyectoPendiente.model_validate(p)
        item.mmre = round(mmre, 3) if mmre is not None else None
        salida.append(item)
    return salida


@router.put("/{project_id}", response_model=ProyectoPendiente)
def sincerar_proyecto(
    project_id: int,
    datos: SincerarRequest,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    """Carga los valores reales de un proyecto terminado."""
    p = db.query(Project).get(project_id)
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")

    p.esfuerzo_real_horas  = datos.esfuerzo_real_horas
    p.completed_at         = datos.completed_at
    if datos.tasks_count is not None:
        p.tasks_count = datos.tasks_count
    p.incluir_en_training  = datos.incluir_en_training
    p.estado               = EstadoProyecto.completado
    p.sincerado            = True
    p.fecha_sincerado      = datetime.utcnow()
    p.sincerado_por        = user.email   # ajusta al campo de tu user
    db.commit(); db.refresh(p)

    item = ProyectoPendiente.model_validate(p)
    if p.esfuerzo_real_horas and p.esfuerzo_estimado_horas:
        item.mmre = round(abs(p.esfuerzo_real_horas - p.esfuerzo_estimado_horas) / p.esfuerzo_real_horas, 3)
    return item


@router.patch("/{project_id}/toggle-training")
def toggle_training(project_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Marca/desmarca un proyecto como outlier (excluir de limpieza)."""
    p = db.query(Project).get(project_id)
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")
    p.incluir_en_training = not p.incluir_en_training
    db.commit()
    return {"id": p.id, "incluir_en_training": p.incluir_en_training}