from sqlalchemy import Column, Integer, ForeignKey, Date, DateTime, Numeric, String, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Contrato(Base):
    __tablename__ = "Contrato"

    id                 = Column(Integer, primary_key=True, index=True)
    fecha_inicio       = Column(Date, nullable=False)
    fecha_fin          = Column(Date, nullable=True)
    tipo               = Column(String(50), nullable=False)   # Venta | Renta (operación)
    monto              = Column(Numeric(12, 2), nullable=False)
    estado             = Column(String(50), nullable=False, default="activo")
    folio              = Column(String(30), nullable=True, unique=True)
    estado_documento   = Column(String(20), nullable=False, default="pendiente")
    motivo_rechazo     = Column(Text, nullable=True)
    condiciones        = Column(Text, nullable=True)
    contrato_padre_id  = Column(Integer, nullable=True)
    url_archivo        = Column(Text, nullable=True)          # documento ORIGINAL
    url_firmado        = Column(Text, nullable=True)          # documento FIRMADO
    fecha_generacion   = Column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_descarga     = Column(DateTime, nullable=True)
    fecha_firma_subida = Column(DateTime, nullable=True)
    # FK cross-service: la integridad la garantiza la BD (init.sql), no este ORM.
    usuario_id         = Column(Integer, nullable=False)
    inmueble_id        = Column(Integer, nullable=False)

    pagos = relationship(
        "Pago", back_populates="contrato",
        cascade="all, delete-orphan", order_by="Pago.numero_cuota",
    )


class Pago(Base):
    __tablename__ = "Pago"

    id                = Column(Integer, primary_key=True, index=True)
    monto             = Column(Numeric(12, 2), nullable=False)
    fecha             = Column(DateTime, nullable=True)          # fecha real de pago
    fecha_vencimiento = Column(Date, nullable=True)             # para calendario de renta
    numero_cuota      = Column(Integer, nullable=True)          # nº de mensualidad
    metodo            = Column(String(50), nullable=True)
    estado            = Column(String(50), nullable=False, default="pendiente")
    contrato_id       = Column(Integer, ForeignKey("Contrato.id"), nullable=False)
    usuario_id        = Column(Integer, nullable=True)
    ip                = Column(String(45), nullable=True)
    stripe_session_id = Column(String(255), nullable=True)
    stripe_payment_intent = Column(String(255), nullable=True)

    contrato = relationship("Contrato", back_populates="pagos")


class SolicitudRenta(Base):
    __tablename__ = "SolicitudRenta"

    id              = Column(Integer, primary_key=True, index=True)
    usuario_id      = Column(Integer, nullable=False)   # cross-service
    inmueble_id     = Column(Integer, nullable=False)   # cross-service
    fecha_solicitud = Column(DateTime, nullable=False, default=datetime.utcnow)
    estado          = Column(String(20), nullable=False, default="pendiente")
    tipo_operacion  = Column(String(10), nullable=False, default="renta")  # renta | venta
    fecha_inicio    = Column(Date, nullable=True)    # duración propuesta por el cliente
    fecha_fin       = Column(Date, nullable=True)
    duracion_meses  = Column(Integer, nullable=True)
    mensaje         = Column(Text, nullable=True)
    contrato_id     = Column(Integer, nullable=True)


class Comprobante(Base):
    __tablename__ = "Comprobante"

    id          = Column(Integer, primary_key=True, index=True)
    contrato_id = Column(Integer, nullable=False)
    pago_id     = Column(Integer, nullable=True)
    url_archivo = Column(Text, nullable=False)
    usuario_id  = Column(Integer, nullable=False)
    fecha_carga = Column(DateTime, nullable=False, default=datetime.utcnow)


class Auditoria(Base):
    __tablename__ = "Auditoria"

    id         = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, nullable=True)
    accion     = Column(String(100), nullable=False)
    entidad    = Column(String(50), nullable=True)
    entidad_id = Column(Integer, nullable=True)
    valor_anterior = Column(Text, nullable=True)
    valor_nuevo    = Column(Text, nullable=True)
    detalle    = Column(Text, nullable=True)
    fecha      = Column(DateTime, nullable=False, default=datetime.utcnow)
