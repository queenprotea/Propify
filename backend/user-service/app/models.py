from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base

class Visita(Base):
    __tablename__ = "Visita"

    id = Column(Integer, primary_key=True)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    estado = Column(String(100), nullable=False)#registrada, cancelada
    inmueble_id = Column(Integer)
    usuario_id = Column(Integer, ForeignKey("Usuario.id"), nullable=False)
    
    usuario = relationship("Usuario", back_populates="visitas")
    
    

class Usuario(Base):
    __tablename__ = "Usuario"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), nullable=False) 
    correo = Column(String(100), nullable=False, unique=True)
    telefono = Column(String(20), nullable=True)
    password = Column(String(255), nullable=False)
    rol = Column(String(100), nullable=False)#admin, cliente
    estado = Column(String(100), nullable=False)#inactivo, activo
    
    visitas = relationship("Visita", back_populates="usuario")
