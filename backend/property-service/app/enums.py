from enum import Enum


class TipoInmueble(str, Enum):
    CASA = "casa"
    DEPARTAMENTO = "departamento"
    TERRENO = "terreno"
    LOCAL = "local"


class EstadoInmueble(str, Enum):
    ENVENTA = "en venta"
    ENRENTA = "en renta"
    VENDIDO = "vendido"
    RENTADO = "rentado"
    APARTADO = "apartado"
    NODISPONIBLE = "no disponible"