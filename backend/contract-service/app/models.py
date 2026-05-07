from sqlalchemy import Column, Integer, ForeignKey, Date, DateTime, Numeric, String, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Contrato(Base):
    __tablename__ = "Contrato"

    id            = Column(Integer, primary_key=True, index=True)
    fecha_inicio  = Column(Date, nullable=False)
    fecha_fin     = Column(Date, nullable=True)
    tipo          = Column(String(50), nullable=False)
    monto         = Column(Numeric(12, 2), nullable=False)
    estado        = Column(String(50), nullable=False, default="activo")
    url_archivo   = Column(Text, nullable=True)
    usuario_id    = Column(Integer, ForeignKey("Usuario.id"), nullable=False)
    inmueble_id   = Column(Integer, ForeignKey("Inmueble.id"), nullable=False)

    pagos = relationship("Pago", back_populates="contrato", cascade="all, delete-orphan")


class Pago(Base):
    __tablename__ = "Pago"

    id                = Column(Integer, primary_key=True, index=True)
    monto             = Column(Numeric(12, 2), nullable=False)
    fecha             = Column(DateTime, nullable=False, default=datetime.utcnow)
    metodo            = Column(String(50), nullable=False)
    estado            = Column(String(50), nullable=False, default="pendiente")
    stripe_session_id = Column(String(255), nullable=True)
    contrato_id       = Column(Integer, ForeignKey("Contrato.id"), nullable=False)

    contrato = relationship("Contrato", back_populates="pagos")
