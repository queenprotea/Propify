from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal

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
    latitud: Decimal
    longitud: Decimal
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

    class Config:
        from_attributes = True


#------------------------------------
#         Inmueble 
#------------------------------------

class InmuebleBase(BaseModel):
    titulo: str = Field(min_length=5, max_length=100)
    descripcion: str | None = None
    precio: Decimal
    tipo_id: int
    estado_id: int
    area_construccion: Decimal | None = None
    area_terreno: Decimal | None = None
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


#usuario
class CurrentUser(BaseModel):
    id: int
    is_admin: bool