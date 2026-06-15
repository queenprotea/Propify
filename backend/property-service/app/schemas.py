import re
from pydantic import BaseModel, Field, computed_field, field_validator
from datetime import datetime
from decimal import Decimal

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

#------------------------------------
#         Estado inmueble 
#------------------------------------

class EstadoInmueble(BaseModel):
    id: int
    valor: str

    class Config:
        from_attributes = True


#------------------------------------
#         Tipo inmueble 
#------------------------------------

class TipoInmueble(BaseModel):
    id: int
    valor: str

    class Config:
        from_attributes = True


#------------------------------------
#         Estado republica 
#------------------------------------

class EstadoRepublica(BaseModel):
    id: int
    valor: str

    class Config:
        from_attributes = True


#------------------------------------
#            ubicacion 
#------------------------------------

class UbicacionBase(BaseModel):
    latitud: Decimal | None = None
    longitud: Decimal | None = None
    estado_id: int
    ciudad: str
    colonia: str 
    calle: str 
    numero_exterior: str
    numero_interior: str | None = None
    codigo_postal: str

    

class UbicacionCreate(UbicacionBase):
    pass


class UbicacionUpdate(BaseModel):
    latitud: Decimal | None = None
    longitud: Decimal | None = None
    estado_id: int | None = None
    ciudad: str | None = None
    colonia: str | None = None
    calle: str | None = None
    numero_exterior: str | None = None
    numero_interior: str | None = None
    codigo_postal: str | None = None


class Ubicacion(UbicacionBase):
    id: int

    estado_republica: EstadoRepublica

    @computed_field
    @property
    def direccion_completa(self) -> str:
        partes = [
            f"{self.calle} {self.numero_exterior}".strip(),
            self.colonia,
            self.ciudad,
            self.estado_republica.valor if self.estado_republica else "",
            f"CP {self.codigo_postal}" if self.codigo_postal else "",
        ]
        return ", ".join(p for p in partes if p)

    class Config:
        from_attributes = True


#------------------------------------
#         Inmueble 
#------------------------------------

class InmuebleBase(BaseModel):
    titulo: str = Field(min_length=5, max_length=100)
    descripcion: str | None = Field(default=None, max_length=2000)
    precio: Decimal = Field(gt=0, le=999999999)
    tipo_id: int
    estado_id: int
    area_construccion: Decimal | None = Field(default=None, ge=0, le=1000000)
    area_terreno: Decimal | None = Field(default=None, ge=0, le=1000000)
    num_recamaras: int | None = Field(default=None, ge=0, le=100)
    num_banos: int | None = Field(default=None, ge=0, le=100)
    num_estacionamientos: int | None = Field(default=None, ge=0, le=100)
    niveles: int | None = Field(default=None, ge=0, le=100)
    amueblado: bool = False
    ubicacion_id: int

    

class InmuebleCreate(InmuebleBase):
    pass


class InmuebleUpdate(BaseModel):
    titulo: str | None = None
    descripcion: str | None = None
    precio: Decimal | None = None
    tipo_id: int | None = None
    estado_id: int | None = None
    area_construccion: Decimal | None = None
    area_terreno: Decimal | None = None
    num_recamaras: int | None = None
    num_banos: int | None = None
    num_estacionamientos: int | None = None
    niveles: int | None = None
    amueblado: bool | None = None
    ubicacion_id: int | None = None
    propietario_id: int | None = None


class Inmueble(InmuebleBase):
    id: int

    estado_inmueble: EstadoInmueble
    tipo_inmueble: TipoInmueble

    propietario_id: int | None = None

    class Config:
        from_attributes = True


class InmuebleDetalle(InmuebleBase):
    id: int

    estado_inmueble: EstadoInmueble
    tipo_inmueble: TipoInmueble
    ubicacion: Ubicacion
    imagenes: list["Imagen"] = []

    class Config:
        from_attributes = True

#------------------------------------
#         Historial estado 
#------------------------------------

class HistorialBase(BaseModel):
    fecha_inicio: datetime
    fecha_fin: datetime | None = None
    inmueble_id: int
    estado_id: int
    

class HistorialCreate(BaseModel):
    inmueble_id: int
    estado_id: int


class HistorialUpdate(BaseModel):
    fecha_inicio: datetime | None = None
    fecha_fin: datetime | None = None
    inmueble_id: int | None = None
    estado_id: int | None = None
    

class Historial(HistorialBase):
    id: int

    estado_inmueble: EstadoInmueble

    class Config:
        from_attributes = True

#------------------------------------
#      Historial propietario 
#------------------------------------

class HistorialPropietarioBase(BaseModel):
    fecha_inicio: datetime
    fecha_fin: datetime | None = None
    inmueble_id: int
    propietario_id: int
    

class HistorialPropietarioCreate(BaseModel):
    inmueble_id: int
    propietario_id: int


class HistorialPropietarioUpdate(BaseModel):
    fecha_inicio: datetime | None = None
    fecha_fin: datetime | None = None
    inmueble_id: int | None = None
    propietario_id: int | None = None
    

class HistorialPropietario(HistorialPropietarioBase):
    id: int

    class Config:
        from_attributes = True


#------------------------------------
#          imagen 
#------------------------------------

class ImagenBase(BaseModel):
    url_archivo: str
    descripcion: str
    inmueble_id: int
    

class ImagenCreate(ImagenBase):
    pass


class ImagenUpdate(BaseModel):
    descripcion: str | None = None
    url_archivo: str | None = None
    

class Imagen(ImagenBase):
    id: int

    class Config:
        from_attributes = True


#------------------------------------
#          contacto 
#------------------------------------

class ContactoBase(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    correo: str = Field(max_length=100)
    mensaje: str = Field(min_length=1, max_length=1000)
    inmueble_id: int

    @field_validator("correo")
    @classmethod
    def _correo_valido(cls, v):
        v = (v or "").strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("El correo electrónico no tiene un formato válido")
        return v


class ContactoCreate(ContactoBase):
    pass


class ContactoUpdate(BaseModel):
    nombre: str | None = None
    correo: str | None = None
    mensaje: str | None = None
    

class Contacto(ContactoBase):
    id: int
    fecha: datetime

    class Config:
        from_attributes = True


#usuario
class CurrentUser(BaseModel):
    id: int
    is_admin: bool