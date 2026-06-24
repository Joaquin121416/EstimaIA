# auth/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Usuario, RolUsuario
from auth.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Usuario:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales invalidas o token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    email = payload.get("sub")
    if email is None:
        raise credentials_exception

    user = db.query(Usuario).filter(Usuario.email == email).first()
    if user is None or not user.activo:
        raise credentials_exception

    return user


def require_admin(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """HU-14: Restringe el endpoint solo a usuarios con rol ADMIN."""
    if current_user.rol != RolUsuario.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta accion requiere permisos de Administrador"
        )
    return current_user
