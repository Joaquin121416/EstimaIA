from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from data.equipo import a_dict, tarifas_promedio, listar_colaboradores
from db.database import get_db
from db.models import Colaborador, Usuario
from models.schemas import ColaboradorIn, ColaboradorOut

router = APIRouter(prefix="/api/v1/colaboradores", tags=["Catalogo de Colaboradores"])


def _get(db: Session, colaborador_id: int) -> Colaborador:
    c = db.query(Colaborador).filter(Colaborador.id == colaborador_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Colaborador no encontrado")
    return c


def _normalizar(data: ColaboradorIn) -> dict:
    d = data.model_dump()
    d["tecnologias"] = [t.strip().lower() for t in d["tecnologias"] if t and t.strip()]
    d["proyectos"] = [p.strip() for p in d["proyectos"] if p and p.strip()]
    return d


@router.get("/", response_model=List[ColaboradorOut], summary="Listar colaboradores")
def listar(db: Session = Depends(get_db), _u: Usuario = Depends(get_current_user)):
    return listar_colaboradores(db)


@router.get("/tarifas-promedio", summary="Costo por hora promedio por rol (colaboradores activos)")
def tarifas(db: Session = Depends(get_db), _u: Usuario = Depends(get_current_user)):
    return tarifas_promedio(listar_colaboradores(db, solo_activos=True))


@router.get("/{colaborador_id}", response_model=ColaboradorOut, summary="Ver un colaborador")
def ver(colaborador_id: int, db: Session = Depends(get_db), _u: Usuario = Depends(get_current_user)):
    return a_dict(_get(db, colaborador_id))


@router.post("/", response_model=ColaboradorOut, status_code=201, summary="Crear colaborador")
def crear(data: ColaboradorIn, db: Session = Depends(get_db), _u: Usuario = Depends(get_current_user)):
    c = Colaborador(**_normalizar(data))
    db.add(c)
    db.commit()
    db.refresh(c)
    return a_dict(c)


@router.put("/{colaborador_id}", response_model=ColaboradorOut, summary="Editar colaborador")
def editar(colaborador_id: int, data: ColaboradorIn, db: Session = Depends(get_db),
           _u: Usuario = Depends(get_current_user)):
    c = _get(db, colaborador_id)
    for k, v in _normalizar(data).items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return a_dict(c)


@router.patch("/{colaborador_id}/activo", response_model=ColaboradorOut, summary="Activar / desactivar")
def toggle_activo(colaborador_id: int, db: Session = Depends(get_db),
                  _u: Usuario = Depends(get_current_user)):
    c = _get(db, colaborador_id)
    c.activo = not c.activo
    db.commit()
    db.refresh(c)
    return a_dict(c)
