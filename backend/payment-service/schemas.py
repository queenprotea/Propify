from pydantic import BaseModel, field_validator
from decimal import Decimal
from typing import Optional
from enum import Enum


class TipoContrato(str, Enum):
    venta = "Venta"
    renta = "Renta"


class IniciarPago(BaseModel):
    contrato_id:    int
    monto:          Decimal
    moneda:         str = "mxn"
    success_url:    str = "https://tu-sitio.com/pago-exitoso"
    cancel_url:     str = "https://tu-sitio.com/pago-cancelado"

    @field_validator("monto")
    @classmethod
    def monto_positivo(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("El monto debe ser mayor que cero")
        return v


class RespuestaSesion(BaseModel):
    """Devuelve la URL de Stripe a la que debe redirigirse el usuario."""
    checkout_url:     str
    stripe_session_id: str
    tipo_contrato:    TipoContrato
    pago_id:          int


class EstadoPago(BaseModel):
    pago_id:   int
    estado:    str
    contrato_id: int
