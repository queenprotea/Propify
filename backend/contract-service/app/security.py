from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

security = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not set")


def verify_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not payload.get("sub"):
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def system_token() -> str:
    """JWT interno con rol admin para llamadas servicio-a-servicio (p. ej. liberar/marcar inmueble)."""
    tok = jwt.encode({"sub": "0", "is_admin": True}, SECRET_KEY, algorithm=ALGORITHM)
    return f"Bearer {tok}"


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    return verify_jwt(credentials.credentials)


def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    payload = verify_jwt(credentials.credentials)
    if not payload.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Se requieren permisos de administrador")
    return payload


def require_owner_or_admin(payload: dict, usuario_id: int):
    """El recurso solo es accesible por su dueño o por un administrador."""
    if payload.get("is_admin"):
        return
    if int(payload.get("sub")) != int(usuario_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="No autorizado para este contrato")
