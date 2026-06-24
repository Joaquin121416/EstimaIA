# routers/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from db.models import Usuario, RolUsuario
from auth.dependencies import get_current_user, require_admin
from models.auth_schemas import UsuarioOut, RolUpdateRequest

router = APIRouter(prefix="/api/v1/users", tags=["Gestion de Roles (HU-14)"])


@router.get(
    "/",
    response_model=List[UsuarioOut],
    summary="Listar usuarios del sistema",
    description="Solo accesible para Administradores. Lista todos los usuarios PM y Admin registrados."
)
def list_users(
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin)  # HU-14: protegido por rol
):
    return db.query(Usuario).all()


@router.put(
    "/{user_id}/rol",
    response_model=UsuarioOut,
    summary="Cambiar el rol de un usuario",
    description="Solo accesible para Administradores. Cambia el rol entre 'pm' y 'admin'."
)
def update_rol(
    user_id: int,
    payload: RolUpdateRequest,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin)
):
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    nuevo_rol = payload.rol.lower()
    if nuevo_rol not in ["pm", "admin"]:
        raise HTTPException(status_code=400, detail="Rol invalido. Use 'pm' o 'admin'.")

    user.rol = RolUsuario.ADMIN if nuevo_rol == "admin" else RolUsuario.PM
    db.commit()
    db.refresh(user)
    return user


@router.put(
    "/{user_id}/desactivar",
    response_model=UsuarioOut,
    summary="Desactivar un usuario",
    description="Solo accesible para Administradores. Revoca el acceso del usuario sin eliminarlo."
)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin)
):
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user.activo = False
    db.commit()
    db.refresh(user)
    return user


@router.get(
    "/me/permisos",
    summary="Ver mis permisos actuales",
    description="Retorna el rol del usuario autenticado y las acciones que tiene permitidas."
)
def my_permissions(current_user: Usuario = Depends(get_current_user)):
    permisos_pm = ["estimate", "assign-team", "view_catalog", "view_history"]
    permisos_admin = permisos_pm + ["manage_users", "manage_roles", "upload_csv", "retrain_model"]

    return {
        "usuario": current_user.email,
        "rol": current_user.rol.value,
        "permisos": permisos_admin if current_user.rol == RolUsuario.ADMIN else permisos_pm
    }
