from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base

class Visita(Base):
    __tablename__ = "Visita"

    id = Column(Integer, primary_key=True)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    estado_id = Column(Integer, ForeignKey("EstadoVisita.id"), nullable=False)
    inmueble_id = Column(Integer)
    usuario_id = Column(Integer, ForeignKey("Usuario.id"), nullable=False)
    
    usuario = relationship("Usuario", back_populates="visitas")
    estado = relationship("EstadoVisita", back_populates="visitas")

class EstadoVisita(Base):
    __tablename__ = "EstadoVisita"
    id = Column(Integer, primary_key=True)
    valor = Column(String(50), nullable=False, unique=True)

    visitas = relationship("Visita", back_populates="estado")

class Usuario(Base):
    __tablename__ = "Usuario"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False) 
    correo = Column(String(100), nullable=False, unique=True)
    telefono = Column(String(20), nullable=True)
    password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    visitas = relationship("Visita", back_populates="usuario")
