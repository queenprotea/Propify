import re
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validar_correo(v: str) -> str:
    v = (v or "").strip().lower()
    if not EMAIL_RE.match(v):
        raise ValueError("El correo electrónico no tiene un formato válido")
    dominio = v.split("@")[1]
    if dominio in ("tempmail.com", "throwaway.com"):
        raise ValueError("No se permiten correos electrónicos desechables")
    return v


def validar_telefono(v):
    if v is None:
        return v
    solo_digitos = re.sub(r"\D", "", v)
    if not solo_digitos:
        return None
    if len(solo_digitos) != 10:
        raise ValueError("El teléfono debe tener 10 dígitos")
    return solo_digitos


def validar_password(v: str) -> str:
    if len(v) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    if not any(c.isupper() for c in v):
        raise ValueError("La contraseña debe incluir al menos una mayúscula")
    if not any(c.islower() for c in v):
        raise ValueError("La contraseña debe incluir al menos una minúscula")
    if not any(c.isdigit() for c in v):
        raise ValueError("La contraseña debe incluir al menos un número")
    return v


# Base schema for shared attributes
class UserBase(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    correo: str
    telefono: str | None = None
    is_active: bool
    is_admin: bool

    @field_validator("nombre")
    @classmethod
    def _nombre(cls, v):
        v = (v or "").strip()
        if len(v) < 2:
            raise ValueError("El nombre es obligatorio (mínimo 2 caracteres)")
        return v

    @field_validator("correo")
    @classmethod
    def _correo(cls, v):
        return validar_correo(v)

    @field_validator("telefono")
    @classmethod
    def _telefono(cls, v):
        return validar_telefono(v)


class UserLogin(BaseModel):
    identifier: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=30)

# Schema for creating a user (registration). Includes password.
class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def _password(cls, v):
        return validar_password(v)

# Schema for what we return to the client.
class User(UserBase):
    id: int
    correo: str
    nombre: str
    telefono: str | None = None
    is_admin: bool
    is_active: bool

    class Config:
        from_attributes = True  # Allows ORM mode (translates ORM object -> Pydantic model)

# Schema for the login request
class Token(BaseModel):
    access_token: str
    token_type: str

# Schema for the data embedded inside the JWT token
class TokenData(BaseModel):
    sub: int | None = None

#update user fields
class UserUpdate(BaseModel):
    nombre: str | None = None
    correo: str | None = None
    telefono: str | None = None
    password: str | None = None
    is_active: bool | None = None
    is_admin: bool | None = None

    @field_validator("nombre")
    @classmethod
    def _nombre(cls, v):
        if v is None:
            return v
        v = v.strip()
        if len(v) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres")
        return v

    @field_validator("correo")
    @classmethod
    def _correo(cls, v):
        return validar_correo(v) if v is not None else v

    @field_validator("telefono")
    @classmethod
    def _telefono(cls, v):
        return validar_telefono(v)

    @field_validator("password")
    @classmethod
    def _password(cls, v):
        return validar_password(v) if v else v



# =========================
# ESTADO VISITA
# =========================

class EstadoVisitaBase(BaseModel):
    valor: str


class EstadoVisita(EstadoVisitaBase):
    id: int

    model_config = {
        "from_attributes": True
    }

# =========================
# VISITAS
# =========================

class VisitaBase(BaseModel):
    estado_id: int
    inmueble_id: int


class VisitaCreate(VisitaBase):
    usuario_id: int
    fecha: datetime


class VisitaUpdate(BaseModel):
    estado_id: int | None = None
    inmueble_id: int | None = None
    usuario_id: int | None = None
    fecha: datetime | None = None


class Visita(BaseModel):
    id: int

    fecha: datetime

    estado_id: int

    inmueble_id: int

    usuario_id: int

    # Relación opcional
    estado: EstadoVisita | None = None

    model_config = {
        "from_attributes": True
    }

