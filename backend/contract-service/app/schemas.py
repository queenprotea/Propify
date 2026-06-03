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
    borrador            = "borrador"
    pendiente_de_firma  = "pendiente_de_firma"
    firmado             = "firmado"
    activo              = "activo"
    finalizado          = "finalizado"
    cancelado           = "cancelado"
    liquidado           = "liquidado"

class EstadoDocumento(str, Enum):
    pendiente = "pendiente"
    aprobado  = "aprobado"
    rechazado = "rechazado"

class EstadoPago(str, Enum):
    pendiente   = "pendiente"
    pagado      = "pagado"
    vencido     = "vencido"
    cancelado   = "cancelado"
    reembolsado = "reembolsado"


#  Pago

class PagoBase(BaseModel):
    monto:  Decimal
    metodo: str

class PagoCreate(PagoBase):
    """Payload para registrar/realizar un pago."""
    pass

class PagoStripeCreate(BaseModel):
    """Pago con tarjeta vía Stripe (PaymentIntent real)."""
    monto:          Decimal
    payment_method: str = "pm_card_visa"   # método de prueba de Stripe

    @field_validator("monto")
    @classmethod
    def _m(cls, v):
        if v <= 0:
            raise ValueError("El monto debe ser mayor que cero")
        return v

class PagoResponse(BaseModel):
    id:                int
    monto:             Decimal
    fecha:             Optional[datetime] = None
    fecha_vencimiento: Optional[date] = None
    numero_cuota:      Optional[int] = None
    metodo:            Optional[str] = None
    estado:            EstadoPago
    contrato_id:       int
    usuario_id:        Optional[int] = None
    ip:                Optional[str] = None
    stripe_session_id: Optional[str] = None
    stripe_payment_intent: Optional[str] = None

    model_config = {"from_attributes": True}


#  Contrato

class ContratoBase(BaseModel):
    fecha_inicio: date
    fecha_fin:    Optional[date] = None
    tipo:         TipoContrato
    monto:        Decimal
    condiciones:  Optional[str] = None
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
    id:                 int
    estado:             EstadoContrato
    folio:              Optional[str] = None
    estado_documento:   EstadoDocumento = EstadoDocumento.pendiente
    motivo_rechazo:     Optional[str] = None
    contrato_padre_id:  Optional[int] = None
    url_archivo:        Optional[str] = None
    url_firmado:        Optional[str] = None
    fecha_generacion:   Optional[datetime] = None
    fecha_descarga:     Optional[datetime] = None
    fecha_firma_subida: Optional[datetime] = None
    pagos:              List[PagoResponse] = []

    model_config = {"from_attributes": True}


class ContratoEstadoUpdate(BaseModel):
    estado: EstadoContrato

class DocumentoValidacion(BaseModel):
    aprobado: bool
    motivo:   Optional[str] = None   # requerido si se rechaza


class RenovarContrato(BaseModel):
    fecha_inicio: date
    fecha_fin:    date
    monto:        Decimal

    @field_validator("monto")
    @classmethod
    def _m(cls, v):
        if v <= 0:
            raise ValueError("El monto debe ser mayor que cero")
        return v


# Resumen económico genérico (sirve para venta y renta)
class ResumenContrato(BaseModel):
    contrato_id:         int
    tipo:                str
    monto_total:         Decimal
    total_pagado:        Decimal
    saldo_pendiente:     Decimal
    porcentaje_cubierto: float
    liquidado:           bool
    cuotas_pendientes:   int = 0
    proximo_vencimiento: Optional[date] = None


#  Resumen de pagos de un contrato de Venta

class ResumenVenta(BaseModel):
    contrato_id:        int
    monto_total:        Decimal
    total_pagado:       Decimal
    saldo_pendiente:    Decimal
    porcentaje_cubierto: float
    liquidado:          bool


#  Solicitud de renta

class EstadoSolicitud(str, Enum):
    pendiente    = "pendiente"
    en_revision  = "en revision"
    aprobada     = "aprobada"
    rechazada    = "rechazada"
    cancelada    = "cancelada"

class TipoOperacion(str, Enum):
    renta = "renta"
    venta = "venta"

class SolicitudCreate(BaseModel):
    inmueble_id:    int
    tipo_operacion: TipoOperacion = TipoOperacion.renta
    fecha_inicio:   Optional[date] = None   # requeridas solo para renta
    fecha_fin:      Optional[date] = None
    duracion_meses: Optional[int] = None
    mensaje:        Optional[str] = None

    @field_validator("fecha_fin")
    @classmethod
    def _fin_posterior(cls, v, info):
        if v and info.data.get("fecha_inicio") and v <= info.data["fecha_inicio"]:
            raise ValueError("La fecha de fin debe ser posterior a la de inicio")
        return v

    @field_validator("tipo_operacion")
    @classmethod
    def _req_fechas_renta(cls, v, info):
        # (la validación dura de fechas en renta se hace en el endpoint, donde
        #  ya están disponibles todos los campos)
        return v

class SolicitudEstadoUpdate(BaseModel):
    estado: EstadoSolicitud

class SolicitudResponse(BaseModel):
    id:              int
    usuario_id:      int
    inmueble_id:     int
    fecha_solicitud: datetime
    estado:          EstadoSolicitud
    tipo_operacion:  str = "renta"
    fecha_inicio:    Optional[date] = None
    fecha_fin:       Optional[date] = None
    duracion_meses:  Optional[int] = None
    mensaje:         Optional[str] = None
    contrato_id:     Optional[int] = None

    model_config = {"from_attributes": True}

# Datos para generar el contrato a partir de una solicitud aprobada.
# El administrador puede modificar la duración propuesta; si omite las fechas,
# se usan las de la solicitud.
class GenerarContratoRenta(BaseModel):
    fecha_inicio: Optional[date] = None
    fecha_fin:    Optional[date] = None
    monto:        Decimal   # renta mensual (confirmada o modificada)
    condiciones:  Optional[str] = None   # observaciones del administrador

    @field_validator("monto")
    @classmethod
    def _monto(cls, v):
        if v <= 0:
            raise ValueError("El monto debe ser mayor que cero")
        return v


# Registro manual de renta por el administrador (sin solicitud del cliente).
class RentaManualCreate(BaseModel):
    usuario_id:   int
    inmueble_id:  int
    fecha_inicio: date
    fecha_fin:    date
    monto:        Decimal
    condiciones:  Optional[str] = None
    estado:       EstadoContrato = EstadoContrato.activo

    @field_validator("monto")
    @classmethod
    def _m(cls, v):
        if v <= 0:
            raise ValueError("El monto debe ser mayor que cero")
        return v

    @field_validator("fecha_fin")
    @classmethod
    def _ff(cls, v, info):
        if v and info.data.get("fecha_inicio") and v <= info.data["fecha_inicio"]:
            raise ValueError("La fecha de fin debe ser posterior a la de inicio")
        return v


#  Comprobante de pago

class ComprobanteResponse(BaseModel):
    id:          int
    contrato_id: int
    pago_id:     Optional[int] = None
    url_archivo: str
    usuario_id:  int
    fecha_carga: datetime

    model_config = {"from_attributes": True}


#  Auditoría

class AuditoriaResponse(BaseModel):
    id:             int
    usuario_id:     Optional[int] = None
    accion:         str
    entidad:        Optional[str] = None
    entidad_id:     Optional[int] = None
    valor_anterior: Optional[str] = None
    valor_nuevo:    Optional[str] = None
    detalle:        Optional[str] = None
    fecha:          datetime

    model_config = {"from_attributes": True}


# Generar contrato de COMPRAVENTA a partir de una solicitud de compra aprobada.
class GenerarContratoVenta(BaseModel):
    monto:       Decimal   # precio de venta (confirmado o modificado)
    condiciones: Optional[str] = None

    @field_validator("monto")
    @classmethod
    def _m(cls, v):
        if v <= 0:
            raise ValueError("El precio debe ser mayor que cero")
        return v
