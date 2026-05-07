from pydantic import BaseModel, Field
from datetime import datetime
from app.enums import TipoInmueble, EstadoInmueble


class InmuebleBase(BaseModel):
    titulo: str = Field(min_length=5, max_length=100)
    descripcion: str | None = None
    precio: float
    tipo: TipoInmueble
    estado: EstadoInmueble
    propietario_id: int | None = None
    area_construccion: float | None = None
    area_terreno: float | None = None
    num_recamaras: int | None = None
    num_banos: int | None = None
    num_estacionamientos: int | None = None
    niveles: int | None = None
    amueblado: bool = False
    ubicacion_id: int 

    

class InmuebleCreate(InmuebleBase):
    pass


class InmuebleUpdate(BaseModel):
    titulo: str | None = None
    descripcion: str | None = None
    precio: float | None = None
    tipo: TipoInmueble | None = None
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
    direccion_completa: str 
    latitud: float
    longitud: float
    estado: str
    ciudad: str
    colonia: str 
    calle: str 
    numero_exterior: str
    numero_interior: str | None = None
    codigo_postal: str

    

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
    id_inmueble: int
    estado: EstadoInmueble
    

class HistorialCreate(BaseModel):
    id_inmueble: int
    estado: EstadoInmueble


class HistorialUpdate(BaseModel):
    fecha_inicio: datetime | None = None
    fecha_fin: datetime | None = None
    id_inmueble: int | None = None
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
    inmueble_id: int
    

class ImagenCreate(ImagenBase):
    pass


class ImagenUpdate(BaseModel):
    url_archivo: str | None = None
    

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
    id_inmueble: int
    

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
