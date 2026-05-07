from pydantic import BaseModel, field_validator
from datetime import date, datetime
from typing import List, Optional
from decimal import Decimal
from enum import Enum


#  Enums

class TipoContrato(str, Enum):
    venta = "Venta"
    renta = "Renta"

class EstadoContrato(str, Enum):
    activo     = "activo"
    finalizado = "finalizado"
    cancelado  = "cancelado"

class EstadoPago(str, Enum):
    pendiente   = "pendiente"
    completado  = "completado"
    fallido     = "fallido"


#Pago

class PagoBase(BaseModel):
    monto:  Decimal
    metodo: str

class PagoCreate(PagoBase):
    """Payload para registrar un pago manualmente (sin Stripe)."""
    pass

class PagoResponse(PagoBase):
    id:                int
    fecha:             datetime
    estado:            EstadoPago
    stripe_session_id: Optional[str] = None
    contrato_id:       int

    model_config = {"from_attributes": True}


# Contrato

class ContratoBase(BaseModel):
    fecha_inicio: date
    fecha_fin:    Optional[date] = None
    tipo:         TipoContrato
    monto:        Decimal
    estado:       EstadoContrato = EstadoContrato.activo
    url_archivo:  Optional[str]  = None
    usuario_id:   int
    inmueble_id:  int

    @field_validator("monto")
    @classmethod
    def monto_positivo(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("El monto debe ser mayor que cero")
        return v

    @field_validator("fecha_fin")
    @classmethod
    def fecha_fin_posterior(cls, v: Optional[date], info) -> Optional[date]:
        if v and info.data.get("fecha_inicio") and v <= info.data["fecha_inicio"]:
            raise ValueError("fecha_fin debe ser posterior a fecha_inicio")
        return v

class ContratoCreate(ContratoBase):
    pass

class ContratoResponse(ContratoBase):
    id:    int
    pagos: List[PagoResponse] = []

    model_config = {"from_attributes": True}
