
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Numeric, String, Text, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Contrato(Base):

    __tablename__ = "Contrato"

    id           = Column(Integer, primary_key=True, index=True)
    tipo         = Column(String(50), nullable=False)   
    monto        = Column(Numeric(12, 2), nullable=False)
    estado       = Column(String(50), nullable=False)
    usuario_id   = Column(Integer, nullable=False)
    inmueble_id  = Column(Integer, nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin    = Column(Date, nullable=True)

    pagos = relationship("Pago", back_populates="contrato")


class Pago(Base):

    __tablename__ = "Pago"

    id                = Column(Integer, primary_key=True, index=True)
    monto             = Column(Numeric(12, 2), nullable=False)
    fecha             = Column(DateTime, nullable=False, default=datetime.utcnow)
    metodo            = Column(String(50), nullable=False, default="stripe")
    estado            = Column(String(50), nullable=False, default="pendiente")
    stripe_session_id = Column(String(255), nullable=True, index=True)
    contrato_id       = Column(Integer, ForeignKey("Contrato.id"), nullable=False)

    contrato = relationship("Contrato", back_populates="pagos")
