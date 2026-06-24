# models/auth_schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=6)
    rol: str = Field(default="pm", description="pm | admin")

    model_config = {
        "json_schema_extra": {
            "example": {
                "nombre": "Joaquin Cunorana",
                "email": "joaquin@consultora.pe",
                "password": "estimaIA2026",
                "rol": "admin"
            }
        }
    }

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "joaquin@consultora.pe",
                "password": "estimaIA2026"
            }
        }
    }

class UsuarioOut(BaseModel):
    id: int
    nombre: str
    email: str
    rol: str
    activo: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut

class RolUpdateRequest(BaseModel):
    rol: str = Field(..., description="pm | admin")

    model_config = {
        "json_schema_extra": {"example": {"rol": "admin"}}
    }
