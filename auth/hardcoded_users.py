# auth/hardcoded_users.py
# Usuarios hardcodeados temporalmente mientras se resuelve la conexion a Supabase.
# HU-13 (Autenticacion) + HU-14 (Roles) sin persistencia en BD.

from auth.security import hash_password

# Hashes pre-calculados al importar el modulo (una sola vez)
USERS_DB = [
    {
        "id": 1,
        "nombre": "Joaquin Cunorana",
        "email": "joaquin@consultora.pe",
        "hashed_password": hash_password("estimaIA2026"),
        "rol": "admin",
        "activo": True,
    },
    {
        "id": 2,
        "nombre": "William Chavez",
        "email": "william@consultora.pe",
        "hashed_password": hash_password("estimaIA2026"),
        "rol": "pm",
        "activo": True,
    },
]


def find_user_by_email(email: str):
    return next((u for u in USERS_DB if u["email"] == email), None)


def find_user_by_id(user_id: int):
    return next((u for u in USERS_DB if u["id"] == user_id), None)


def create_user(nombre: str, email: str, password: str, rol: str = "pm"):
    if find_user_by_email(email):
        return None
    new_id = max([u["id"] for u in USERS_DB], default=0) + 1
    user = {
        "id": new_id,
        "nombre": nombre,
        "email": email,
        "hashed_password": hash_password(password),
        "rol": "admin" if rol.lower() == "admin" else "pm",
        "activo": True,
    }
    USERS_DB.append(user)
    return user
