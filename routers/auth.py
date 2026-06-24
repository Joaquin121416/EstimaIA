# routers/auth.py
from fastapi import APIRouter, HTTPException, status, Depends
from auth.security import verify_password, create_access_token
from auth.dependencies import get_current_user
from auth.hardcoded_users import find_user_by_email, create_user
from models.auth_schemas import UsuarioCreate, LoginRequest, TokenResponse, UsuarioOut

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticacion (HU-13)"])


@router.post(
    "/register",
    response_model=UsuarioOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
    description="Crea un nuevo usuario PM o Admin. Almacenamiento temporal en memoria (hardcoded) mientras se conecta Supabase."
)
def register(payload: UsuarioCreate):
    user = create_user(payload.nombre, payload.email, payload.password, payload.rol)
    if user is None:
        raise HTTPException(status_code=400, detail="El email ya esta registrado")
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesion",
    description="Autentica al usuario con email y password, retorna un JWT valido por 8 horas."
)
def login(payload: LoginRequest):
    user = find_user_by_email(payload.email)

    if not user or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contrasena incorrectos"
        )

    if not user["activo"]:
        raise HTTPException(status_code=403, detail="Usuario inactivo. Contacte al administrador.")

    token = create_access_token(data={"sub": user["email"], "rol": user["rol"]})

    return TokenResponse(access_token=token, usuario=user)


@router.get(
    "/me",
    response_model=UsuarioOut,
    summary="Obtener usuario autenticado",
    description="Retorna los datos del usuario actual segun el token JWT enviado."
)
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
