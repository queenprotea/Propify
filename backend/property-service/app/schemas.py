import re
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from app.enums import TipoInmueble, OperacionInmueble, UsoInmueble, EstadoInmueble


class InmuebleBase(BaseModel):
    titulo: str = Field(min_length=5, max_length=150)
    descripcion: str | None = None
    precio: float
    tipo: TipoInmueble
    operacion: OperacionInmueble
    uso: UsoInmueble
    estado: EstadoInmueble = EstadoInmueble.DISPONIBLE
    propietario_id: int | None = None
    area_construccion: float | None = None
    area_terreno: float | None = None
    num_recamaras: int | None = None
    num_banos: int | None = None
    num_estacionamientos: int | None = None
    niveles: int | None = None
    amueblado: bool = False
    ubicacion_id: int

    @field_validator("titulo")
    @classmethod
    def _titulo(cls, v):
        v = (v or "").strip()
        if len(v) < 5:
            raise ValueError("El título debe tener al menos 5 caracteres")
        return v

    @field_validator("precio")
    @classmethod
    def _precio(cls, v):
        if v is None or v <= 0:
            raise ValueError("El precio debe ser mayor que cero")
        return v

    @field_validator("num_recamaras", "num_banos", "num_estacionamientos", "niveles")
    @classmethod
    def _no_negativos(cls, v):
        if v is not None and v < 0:
            raise ValueError("El valor no puede ser negativo")
        return v


class InmuebleCreate(InmuebleBase):
    pass


class InmuebleUpdate(BaseModel):
    titulo: str | None = None
    descripcion: str | None = None
    precio: float | None = None
    tipo: TipoInmueble | None = None
    operacion: OperacionInmueble | None = None
    uso: UsoInmueble | None = None
    estado: EstadoInmueble | None = None
    area_construccion: float | None = None
    area_terreno: float | None = None
    num_recamaras: int | None = None
    num_banos: int | None = None
    num_estacionamientos: int | None = None
    niveles: int | None = None
    amueblado: bool | None = None
    ubicacion_id: int | None = None
    propietario_id: int | None = None


class Inmueble(InmuebleBase):
    id: int

    propietario_id: int | None = None

    class Config:
        from_attributes = True


#------------------------------------
#            ubicacion
#------------------------------------

class UbicacionBase(BaseModel):
    # direccion_completa se autogenera en el servidor a partir de las partes;
    # el cliente no necesita enviarla (en la UI aparece como "autogenerada").
    direccion_completa: str | None = None
    latitud: float | None = None
    longitud: float | None = None
    estado: str
    ciudad: str
    colonia: str
    calle: str
    numero_exterior: str
    numero_interior: str | None = None
    codigo_postal: str

    @field_validator("codigo_postal")
    @classmethod
    def _cp(cls, v):
        v = (v or "").strip()
        if not re.fullmatch(r"\d{4,6}", v):
            raise ValueError("El código postal debe tener entre 4 y 6 dígitos")
        return v


class UbicacionCreate(UbicacionBase):
    pass


class UbicacionUpdate(BaseModel):
    direccion_completa: str | None = None
    latitud: float | None = None
    longitud: float | None = None
    estado: str | None = None
    ciudad: str | None = None
    colonia: str | None = None
    calle: str | None = None
    numero_exterior: str | None = None
    numero_interior: str | None = None
    codigo_postal: str | None = None


class Ubicacion(UbicacionBase):
    id: int

    class Config:
        from_attributes = True

#------------------------------------
#         Historial estado
#------------------------------------

class HistorialBase(BaseModel):
    fecha_inicio: datetime
    fecha_fin: datetime | None = None
    inmueble_id: int
    estado: EstadoInmueble


class HistorialCreate(BaseModel):
    inmueble_id: int
    estado: EstadoInmueble


class HistorialUpdate(BaseModel):
    fecha_inicio: datetime | None = None
    fecha_fin: datetime | None = None
    inmueble_id: int | None = None
    estado: EstadoInmueble | None = None


class Historial(HistorialBase):
    id: int

    class Config:
        from_attributes = True


#------------------------------------
#          imagen
#------------------------------------

class ImagenBase(BaseModel):
    url_archivo: str
    # WCAG 1.1.1: texto alternativo descriptivo obligatorio
    texto_alternativo: str = Field(min_length=1, max_length=255)
    inmueble_id: int


class ImagenCreate(ImagenBase):
    pass


class ImagenUpdate(BaseModel):
    url_archivo: str | None = None
    texto_alternativo: str | None = Field(default=None, max_length=255)


class Imagen(ImagenBase):
    id: int

    class Config:
        from_attributes = True


#------------------------------------
#          contacto
#------------------------------------

class ContactoBase(BaseModel):
    nombre: str
    correo: str
    mensaje: str
    inmueble_id: int


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
