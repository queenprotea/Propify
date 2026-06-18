import re
from pydantic import BaseModel, Field, computed_field, field_validator
from datetime import datetime
from decimal import Decimal

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Caracteres que nunca deben aparecer en texto capturado por el usuario.
_CARS_INVALIDOS = re.compile(r"[<>{}\[\]\\|^~`]")
# Secuencias de símbolos repetidos (spam) como ¿¿??, ???, !!!, ***.
_SIMBOLOS_SPAM = re.compile(r"[¿?¡!*#]{2,}")


def validar_texto(v, campo="El texto"):
    """Rechaza caracteres especiales inválidos y secuencias de símbolos sin sentido."""
    if v is None:
        return v
    if _CARS_INVALIDOS.search(v):
        raise ValueError(f"{campo} contiene caracteres no permitidos (< > {{ }} [ ] \\ | ^ ~ `)")
    if _SIMBOLOS_SPAM.search(v):
        raise ValueError(f"{campo} contiene una secuencia de símbolos no válida")
    return v

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
    ciudad: str = Field(min_length=2, max_length=100)
    colonia: str = Field(min_length=2, max_length=100)
    calle: str = Field(min_length=1, max_length=100)
    numero_exterior: str = Field(min_length=1, max_length=20)
    numero_interior: str | None = Field(default=None, max_length=20)
    codigo_postal: str

    @field_validator("ciudad", "colonia", "calle", "numero_exterior", "numero_interior")
    @classmethod
    def _texto_dir(cls, v):
        return validar_texto(v, "El campo de dirección")

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

# Límites realistas del dominio inmobiliario. Un "Inmueble" puede ser un edificio
# completo, por eso los topes son generosos pero acotados para evitar capturas absurdas.
# Topes derivados del número de caracteres esperado (no valores de negocio arbitrarios).
# precio/area se almacenan como DECIMAL(12,2) → máximo 10 dígitos enteros.
PRECIO_MAX = 9_999_999_999          # hasta 10 dígitos enteros
AREA_MAX = 9_999_999                # hasta 7 dígitos (m²)
RECAMARAS_MAX = 999                 # hasta 3 dígitos
BANOS_MAX = 999
ESTACIONAMIENTOS_MAX = 999
NIVELES_MAX = 999


class InmuebleBase(BaseModel):
    titulo: str = Field(min_length=5, max_length=100)
    descripcion: str | None = Field(default=None, max_length=2000)
    precio: Decimal = Field(gt=0, le=PRECIO_MAX)
    tipo_id: int
    estado_id: int
    area_construccion: Decimal | None = Field(default=None, ge=0, le=AREA_MAX)
    area_terreno: Decimal | None = Field(default=None, ge=0, le=AREA_MAX)
    # Sin tope superior en el modelo base: los topes son de validación de ENTRADA
    # (ver InmuebleCreate/InmuebleUpdate). En lectura toleramos datos preexistentes
    # para no romper el serializado de toda la lista por un registro fuera de rango.
    num_recamaras: int | None = Field(default=None, ge=0)
    num_banos: int | None = Field(default=None, ge=0)
    num_estacionamientos: int | None = Field(default=None, ge=0)
    niveles: int | None = Field(default=None, ge=0)
    amueblado: bool = False
    ubicacion_id: int

    @field_validator("titulo")
    @classmethod
    def _titulo(cls, v):
        return validar_texto(v, "El título")

    @field_validator("descripcion")
    @classmethod
    def _descripcion(cls, v):
        return validar_texto(v, "La descripción")


class InmuebleCreate(InmuebleBase):
    # Topes superiores SOLO en la entrada (evitan capturas absurdas).
    num_recamaras: int | None = Field(default=None, ge=0, le=RECAMARAS_MAX)
    num_banos: int | None = Field(default=None, ge=0, le=BANOS_MAX)
    num_estacionamientos: int | None = Field(default=None, ge=0, le=ESTACIONAMIENTOS_MAX)
    niveles: int | None = Field(default=None, ge=0, le=NIVELES_MAX)


class InmuebleUpdate(BaseModel):
    titulo: str | None = Field(default=None, min_length=5, max_length=100)
    descripcion: str | None = Field(default=None, max_length=2000)
    precio: Decimal | None = Field(default=None, gt=0, le=PRECIO_MAX)
    tipo_id: int | None = None
    estado_id: int | None = None
    area_construccion: Decimal | None = Field(default=None, ge=0, le=AREA_MAX)
    area_terreno: Decimal | None = Field(default=None, ge=0, le=AREA_MAX)
    num_recamaras: int | None = Field(default=None, ge=0, le=RECAMARAS_MAX)
    num_banos: int | None = Field(default=None, ge=0, le=BANOS_MAX)
    num_estacionamientos: int | None = Field(default=None, ge=0, le=ESTACIONAMIENTOS_MAX)
    niveles: int | None = Field(default=None, ge=0, le=NIVELES_MAX)
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

    @field_validator("nombre", "mensaje")
    @classmethod
    def _texto_contacto(cls, v):
        return validar_texto(v, "El campo")


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