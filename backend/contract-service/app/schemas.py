from pydantic import BaseModel, field_validator, Field
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
    """Pago con tarjeta vía Stripe (PaymentIntent real).

    payment_method es el id generado por Stripe Elements en el navegador a
    partir de los datos reales de la tarjeta; es obligatorio (no se simula).
    """
    monto:          Decimal
    payment_method: str

    @field_validator("monto")
    @classmethod
    def _m(cls, v):
        if v <= 0:
            raise ValueError("El monto debe ser mayor que cero")
        return v

    @field_validator("payment_method")
    @classmethod
    def _pm(cls, v):
        if not v or not v.strip():
            raise ValueError("Falta el método de pago de la tarjeta")
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
    condiciones:  Optional[str] = Field(default=None, max_length=2000)
    usuario_id:   int
    inmueble_id:  int

    @field_validator("monto")
    @classmethod
    def monto_positivo(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("El monto debe ser mayor que cero")
        if v > 999999999:
            raise ValueError("El monto excede el máximo permitido")
        return v

    @field_validator("fecha_fin")
    @classmethod
    def fecha_fin_posterior(cls, v: Optional[date], info) -> Optional[date]:
        if v and info.data.get("fecha_inicio") and v <= info.data["fecha_inicio"]:
            raise ValueError("fecha_fin debe ser posterior a fecha_inicio")
        return v

class ClausulaResponse(BaseModel):
    id:          int
    numero:      Optional[str] = None
    titulo:      Optional[str] = None
    descripcion: str

    model_config = {"from_attributes": True}


class ContratoCreate(ContratoBase):
    clausula_ids: List[int] = []   # cláusulas del catálogo a incluir

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
    clausulas:          List[ClausulaResponse] = []

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
    clausula_ids: List[int] = []         # cláusulas del catálogo a incluir

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
    clausula_ids: List[int] = []

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


# Generar contrato de COMPRAVENTA a partir de una solicitud de compra aprobada.
class GenerarContratoVenta(BaseModel):
    monto:       Decimal   # precio de venta (confirmado o modificado)
    condiciones: Optional[str] = None
    clausula_ids: List[int] = []

    @field_validator("monto")
    @classmethod
    def _m(cls, v):
        if v <= 0:
            raise ValueError("El precio debe ser mayor que cero")
        return v


#  Catálogo de cláusulas

class ClausulaCatalogoCreate(BaseModel):
    numero: str
    titulo: str
    texto:  str

    @field_validator("numero")
    @classmethod
    def _num(cls, v):
        v = (v or "").strip()
        if not v:
            raise ValueError("El número de cláusula es obligatorio (p. ej. 2.1)")
        import re
        if not re.fullmatch(r"\d+(\.\d+)*", v):
            raise ValueError("El número debe ser jerárquico: dígitos separados por puntos (2, 2.1, 2.1.1)")
        return v

    @field_validator("titulo", "texto")
    @classmethod
    def _no_vacio(cls, v):
        if not (v or "").strip():
            raise ValueError("Campo obligatorio")
        return v.strip()


class ClausulaCatalogoResponse(BaseModel):
    id:     int
    numero: str
    titulo: str
    texto:  str

    model_config = {"from_attributes": True}
