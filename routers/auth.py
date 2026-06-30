# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Usuario, RolUsuario
from auth.security import hash_password, verify_password, create_access_token
from auth.dependencies import get_current_user
from models.auth_schemas import UsuarioCreate, LoginRequest, TokenResponse, UsuarioOut

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticacion (HU-13)"])


@router.post("/register", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
    description="Crea un nuevo usuario PM o Admin, persistido en Supabase PostgreSQL.")
def register(payload: UsuarioCreate, db: Session = Depends(get_db)):
    existente = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if existente:
        raise HTTPException(status_code=400, detail="El email ya esta registrado")

    rol_valido = RolUsuario.ADMIN if payload.rol.lower() == "admin" else RolUsuario.PM

    nuevo = Usuario(
        nombre=payload.nombre,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        rol=rol_valido,
        activo=True
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.post("/login", response_model=TokenResponse,
    summary="Iniciar sesion",
    description="Autentica al usuario con email y password, retorna un JWT valido por 8 horas.")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == payload.email).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email o contrasena incorrectos")

    if not user.activo:
        raise HTTPException(status_code=403, detail="Usuario inactivo. Contacte al administrador.")

    token = create_access_token(data={"sub": user.email, "rol": user.rol.value})
    return TokenResponse(access_token=token, usuario=user)


@router.get("/me", response_model=UsuarioOut,
    summary="Obtener usuario autenticado",
    description="Retorna los datos del usuario actual segun el token JWT enviado.")
def get_me(current_user: Usuario = Depends(get_current_user)):
    return current_user
