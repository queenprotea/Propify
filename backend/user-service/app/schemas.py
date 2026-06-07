from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime

# Base schema for shared attributes
class UserBase(BaseModel):
    nombre: str
    correo: str 
    telefono: str | None = None
    is_active: bool
    

class UserLogin(BaseModel):
    identifier: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=30)

# Schema for creating a user (registration). Includes password.

class UserCreate(UserBase):
    password: str 
    
    @field_validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @field_validator('correo')
    def validate_email_domain(cls, v):
        disposable_domains = ['tempmail.com', 'throwaway.com']
        domain = v.split('@')[1]
        if domain in disposable_domains:
            raise ValueError('Disposable email addresses are not allowed')
        return v
    
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

