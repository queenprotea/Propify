from enum import Enum


# Tipo físico del inmueble (criterio de búsqueda "Tipo de propiedad")
class TipoInmueble(str, Enum):
    CASA = "casa"
    DEPARTAMENTO = "departamento"
    TERRENO = "terreno"
    LOCAL = "local"
    EDIFICIO = "edificio"
    OFICINA = "oficina"


# Operación comercial (parte de la "categorización": Venta / Renta)
class OperacionInmueble(str, Enum):
    VENTA = "venta"
    RENTA = "renta"


# Uso del inmueble (parte de la "categorización": Comercial / Residencial)
class UsoInmueble(str, Enum):
    RESIDENCIAL = "residencial"
    COMERCIAL = "comercial"


# Estado del inmueble (requisito: Disponible, Reservado, Vendido, Rentado)
class EstadoInmueble(str, Enum):
    DISPONIBLE = "disponible"
    RESERVADO = "reservado"
    VENDIDO = "vendido"
    RENTADO = "rentado"
