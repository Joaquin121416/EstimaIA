# routers/users.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from auth.dependencies import get_current_user, require_admin
from auth.hardcoded_users import USERS_DB, find_user_by_id
from models.auth_schemas import UsuarioOut, RolUpdateRequest

router = APIRouter(prefix="/api/v1/users", tags=["Gestion de Roles (HU-14)"])


@router.get(
    "/",
    response_model=List[UsuarioOut],
    summary="Listar usuarios del sistema",
    description="Solo accesible para Administradores."
)
def list_users(_admin: dict = Depends(require_admin)):
    return USERS_DB


@router.put(
    "/{user_id}/rol",
    response_model=UsuarioOut,
    summary="Cambiar el rol de un usuario",
    description="Solo accesible para Administradores. Cambia el rol entre 'pm' y 'admin'."
)
def update_rol(user_id: int, payload: RolUpdateRequest, _admin: dict = Depends(require_admin)):
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    nuevo_rol = payload.rol.lower()
    if nuevo_rol not in ["pm", "admin"]:
        raise HTTPException(status_code=400, detail="Rol invalido. Use 'pm' o 'admin'.")

    user["rol"] = nuevo_rol
    return user


@router.put(
    "/{user_id}/desactivar",
    response_model=UsuarioOut,
    summary="Desactivar un usuario",
    description="Solo accesible para Administradores."
)
def deactivate_user(user_id: int, _admin: dict = Depends(require_admin)):
    user = find_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user["activo"] = False
    return user


@router.get(
    "/me/permisos",
    summary="Ver mis permisos actuales",
    description="Retorna el rol del usuario autenticado y las acciones que tiene permitidas."
)
def my_permissions(current_user: dict = Depends(get_current_user)):
    permisos_pm = ["estimate", "assign-team", "view_catalog", "view_history"]
    permisos_admin = permisos_pm + ["manage_users", "manage_roles", "upload_csv", "retrain_model"]

    return {
        "usuario": current_user["email"],
        "rol": current_user["rol"],
        "permisos": permisos_admin if current_user["rol"] == "admin" else permisos_pm
    }
